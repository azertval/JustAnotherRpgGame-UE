// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_combat_state.cpp
 * @brief Tests de la machine à états du combat : initiative, tour, crochets, entrées et sorties,
 *        les trois fins (`LOT-20`, `EX-CBT-010`, `EX-CBT-011`, `EX-CBT-012`, `EX-VIS-004`) ; et
 *        le déplacement d'un tour dans l'espace en mètres (`LOT-19`, `LOT-1017`, `EX-CBT-020`,
 *        `EX-REG-051`) : budget, terrain difficile, vol, droit de passage, placement.
 *
 * **Aucune fenêtre** : un combat se déroule ici du premier round à sa fin, au rythme des appels du
 * test. Les combattants sont écrits dans le test, jamais lus d'un catalogue livré.
 *
 * L'espace est la simulation de Core lue d'une grille de collision (`test_support::spaceOf`) : un
 * réseau à la demi-case, où les centres et les coins des cases sont des nœuds. Les combattants se
 * posent au centre de leurs cases (`test_support::tile`) ; les longueurs se lisent en mètres, à
 * 0,01 m près.
 */

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <map>
#include <memory>
#include <optional>
#include <random>
#include <string>
#include <utility>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/ActionEconomy.h"
#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/CombatState.h"
#include "Core/Combat/CombatTransition.h"
#include "Core/Combat/Encounter.h"
#include "Core/Combat/SimulatedSpace.h"
#include "Core/Gameplay/WorldFlags.h"
#include "Core/Levels/GridPosition.h"
#include "Core/Levels/Level.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Check.h"
#include "Core/Rpg/Dice.h"
#include "Test/Support/CombatSpaceSupport.h"

namespace {

using core::CombatantId;
using core::CombatHook;
using core::CombatSide;
using core::Meters3;
using test_support::tile;

/// La tolérance d'une longueur : le centimètre.
constexpr float CM = 0.01f;

/// Un modificateur d'initiative qu'aucun d20 ne rattrape : l'ordre du test ne dépend plus des dés.
constexpr int PREMIER = 100;
constexpr int SECOND = 50;
constexpr int DERNIER = -100;

[[nodiscard]] core::CombatantProfile profil(const std::string& nom, CombatSide camp, int pv,
                                            int initiative = 0, int mouvement = 6) {
    return {.name = nom,
            .side = camp,
            .maximumHitPoints = pv,
            .currentHitPoints = pv,
            .dexterity = 10,
            .initiativeModifier = initiative,
            .movement = mouvement};
}

/// Une salle de 12 × 8 cases, sans mur.
[[nodiscard]] std::shared_ptr<core::SimulatedSpace> ouverte() {
    return test_support::openSpace(12, 8);
}

/// Le rectangle au sol de la case (@p colonne, @p ligne).
[[nodiscard]] core::GroundRect caseAuSol(int colonne, int ligne) {
    const float x = static_cast<float>(colonne) * core::METERS_PER_TILE;
    const float y = static_cast<float>(ligne) * core::METERS_PER_TILE;
    return {x, y, x + core::METERS_PER_TILE, y + core::METERS_PER_TILE};
}

[[nodiscard]] bool proche(Meters3 a, Meters3 b) {
    return std::fabs(a.x - b.x) < CM && std::fabs(a.y - b.y) < CM;
}

/// Les places de fin d'un déplacement, la place de départ (en tête) exclue.
[[nodiscard]] std::vector<Meters3> fins(const std::vector<core::Destination>& destinations) {
    std::vector<Meters3> points;
    for (std::size_t i = 1; i < destinations.size(); ++i) {
        points.push_back(destinations[i].point);
    }
    return points;
}

[[nodiscard]] bool parmi(const std::vector<Meters3>& points, Meters3 point) {
    return std::any_of(points.begin(), points.end(),
                       [&](Meters3 autre) { return proche(autre, point); });
}

[[nodiscard]] std::string texte(Meters3 point) {
    std::array<char, 32> tampon{};
    std::snprintf(tampon.data(), tampon.size(), "%.2f,%.2f", static_cast<double>(point.x),
                  static_cast<double>(point.y));
    return tampon.data();
}

[[nodiscard]] std::string idTexte(std::optional<CombatantId> id) {
    return id.has_value() ? std::to_string(static_cast<int>(*id)) : "?";
}

[[nodiscard]] std::string decrire(const core::CombatEvent& evenement) {
    switch (evenement.hook) {
        case CombatHook::BeforeFirstTurn:
            return "avant";
        case CombatHook::RoundStart:
            return "round " + std::to_string(evenement.round);
        case CombatHook::InitiativeCount:
            return "rang " + evenement.marker;
        case CombatHook::TurnStart:
            return "debut " + idTexte(evenement.combatant);
        case CombatHook::TurnEnd:
            return "fin " + idTexte(evenement.combatant);
        case CombatHook::AttackDeclared:
            return "attaque " + idTexte(evenement.combatant) + ">" + idTexte(evenement.target);
        case CombatHook::DamageTaken:
            return "degats " + idTexte(evenement.combatant);
        case CombatHook::CombatantDowned:
            return "a terre " + idTexte(evenement.combatant);
        case CombatHook::CombatantJoined:
            return "entree " + idTexte(evenement.combatant);
        case CombatHook::CombatantLeft:
            return "sortie " + idTexte(evenement.combatant);
        case CombatHook::CombatEnded:
            return "issue";
    }
    return "?";
}

/// Abonne un journal à **tous** les crochets.
void ecouter(core::CombatState& combat, std::vector<std::string>& journal) {
    constexpr std::array<CombatHook, 9> CROCHETS{
        CombatHook::BeforeFirstTurn, CombatHook::RoundStart,    CombatHook::InitiativeCount,
        CombatHook::TurnStart,       CombatHook::TurnEnd,       CombatHook::AttackDeclared,
        CombatHook::CombatantJoined, CombatHook::CombatantLeft, CombatHook::CombatEnded};
    for (const CombatHook crochet : CROCHETS) {
        combat.subscribe(crochet, [&journal](core::CombatState&, const core::CombatEvent& e) {
            journal.push_back(decrire(e));
        });
    }
}

[[nodiscard]] CombatantId enrole(core::CombatState& combat, const core::CombatantProfile& p,
                                 std::optional<Meters3> base = std::nullopt) {
    const core::EnlistResult enrolement = combat.enlist(p, base);
    EXPECT_TRUE(enrolement.combatant.has_value()) << p.name;
    return enrolement.combatant.value_or(CombatantId{});
}

/// L'écart entre les bords de @p mobile posé en @p base et de @p cible à sa place.
[[nodiscard]] float ecart(const core::CombatState& combat, CombatantId mobile, Meters3 base,
                          CombatantId cible) {
    return core::edgeDistance(*combat.volumeAt(mobile, base), *combat.volumeOf(cible));
}

/// Ce qu'un combattant de l'escarmouche sait frapper : le reste du combat est au `LOT-21`.
struct Arme {
    int bonus = 0;
    core::Dice degats;
    int classeArmure = 10;
};

/**
 * Une escarmouche à cinq, jouée sans fenêtre par une tactique élémentaire : marcher vers l'ennemi
 * debout le plus proche, le frapper s'il est à l'allonge, terminer son tour.
 */
[[nodiscard]] std::vector<std::string> escarmouche(std::uint64_t graine,
                                                   std::optional<core::CombatOutcome>& issue,
                                                   int& rounds) {
    core::TileMap carte(10, 8);
    carte.setTile(4, 3, core::TileType::Wall);
    carte.setTile(4, 4, core::TileType::Wall);
    core::CombatState combat{test_support::spaceOf(carte)};
    std::vector<std::string> journal;
    ecouter(combat, journal);

    std::map<CombatantId, Arme> armes;
    const auto ajouter = [&](const std::string& nom, CombatSide camp, int pv, int dexterite,
                             Meters3 base, Arme arme) {
        core::CombatantProfile p = profil(nom, camp, pv);
        p.dexterity = dexterite;
        p.initiativeModifier = (dexterite - 10) / 2;
        const CombatantId id = enrole(combat, p, base);
        armes[id] = arme;
    };
    ajouter("Guerriere", CombatSide::Allies, 20, 12, tile(1, 3),
            {.bonus = 5, .degats = *core::parseDice("1d8+3"), .classeArmure = 16});
    ajouter("Pretre", CombatSide::Allies, 14, 10, tile(1, 5),
            {.bonus = 4, .degats = *core::parseDice("1d6+2"), .classeArmure = 15});
    for (int rang = 0; rang < 3; ++rang) {
        ajouter("Gobelin", CombatSide::Enemies, 7, 14, tile(8, 2 + 2 * rang),
                {.bonus = 4, .degats = *core::parseDice("1d6+2"), .classeArmure = 15});
    }

    core::DeterministicRandom des(graine);
    EXPECT_TRUE(combat.start(des));
    for (int garde = 0; garde < 500 && combat.phase() != core::CombatPhase::Ended; ++garde) {
        const CombatantId actif = *combat.activeCombatant();
        const CombatSide camp = combat.find(actif)->profile.side;
        const Meters3 depart = *combat.positionOf(actif);

        std::optional<CombatantId> cible;
        float distance = 0.0f;
        for (const CombatantId autre : combat.combatants()) {
            const core::Combatant* c = combat.find(autre);
            if (c->profile.side == camp || c->status != core::CombatantStatus::Standing) {
                continue;
            }
            const float d = ecart(combat, actif, depart, autre);
            if (!cible.has_value() || d < distance) {
                cible = autre;
                distance = d;
            }
        }

        if (distance > core::MELEE_REACH_METERS) {
            std::optional<Meters3> meilleure;
            for (const core::Destination& destination : combat.destinations()) {
                const float d = ecart(combat, actif, destination.point, *cible);
                if (d < distance - CM) {
                    distance = d;
                    meilleure = destination.point;
                }
            }
            if (meilleure.has_value()) {
                EXPECT_EQ(combat.move(*meilleure).result, core::MoveResult::Moved);
                journal.push_back("pas " + idTexte(actif) + " " + texte(*meilleure));
            }
        }
        if (core::inReach(*combat.volumeOf(actif), *combat.volumeOf(*cible))) {
            EXPECT_TRUE(combat.declareAttack(actif, *cible));
            EXPECT_TRUE(combat.spend(core::ACTION_RESOURCE));
            const Arme& arme = armes[actif];
            const std::array<core::Modifier, 1> bonus{
                core::Modifier{.source = "attaque", .value = arme.bonus}};
            const core::CheckResult jet =
                core::rollCheck(armes[*cible].classeArmure, bonus, core::RollStance::Normal, des);
            journal.push_back(jet.describe());
            if (jet.succeeded()) {
                combat.applyDamage(*cible, core::rollDice(arme.degats, des).total);
            }
        }
        if (combat.phase() != core::CombatPhase::Ended) {
            EXPECT_TRUE(combat.endTurn());
        }
    }
    issue = combat.outcome();
    rounds = combat.round();
    return journal;
}

}  // namespace

/**
 * @brief L'initiative est jetee une fois, et l'ordre tient jusqu'a la fin.
 * \castest{<b>L'ordre d'initiative est jete au debut et reste stable de round en round.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Engager trois combattants, graine 7.<br/>2. Jouer trois rounds en terminant chaque
 * tour.<br/>3. Rejouer le meme combat a la meme graine.<br/>
 * \tattendu Chaque jet est restituable (de + modificateur = total) ; les neuf tours suivent trois
 * fois l'ordre initial ; l'ordre n'a pas bouge ; le rejeu donne les memes des.
 * }
 */
TEST(CombatStateTest, LInitiativeEstJeteeUneFoisEtLOrdreTient) {
    const auto jouer = [](std::vector<int>& des, std::vector<CombatantId>& tours) {
        core::CombatState combat(ouverte());
        static_cast<void>(enrole(combat, profil("Heroine", CombatSide::Allies, 10, 2)));
        static_cast<void>(enrole(combat, profil("Loup", CombatSide::Enemies, 10, 2)));
        static_cast<void>(enrole(combat, profil("Compagnon", CombatSide::Allies, 10, 1)));
        core::DeterministicRandom hasard(7);
        EXPECT_TRUE(combat.start(hasard));
        const std::vector<core::InitiativeEntry> initial = combat.turnOrder().entries();
        for (const core::InitiativeEntry& place : initial) {
            const core::Combatant* c = combat.find(place.combatant);
            ASSERT_TRUE(c->initiativeRoll.has_value());
            EXPECT_EQ(c->initiativeRoll->total, c->initiativeRoll->keptDie + place.modifier);
            EXPECT_EQ(place.total, c->initiativeRoll->total);
            des.push_back(c->initiativeRoll->keptDie);
        }
        for (int tour = 0; tour < 9; ++tour) {
            tours.push_back(*combat.activeCombatant());
            ASSERT_TRUE(combat.endTurn());
        }
        EXPECT_EQ(combat.round(), 4);
        ASSERT_EQ(combat.turnOrder().entries().size(), initial.size());
        for (std::size_t rang = 0; rang < initial.size(); ++rang) {
            EXPECT_EQ(combat.turnOrder().entries()[rang].combatant, initial[rang].combatant);
            EXPECT_EQ(combat.turnOrder().entries()[rang].total, initial[rang].total);
            EXPECT_EQ(tours[rang], initial[rang].combatant);
            EXPECT_EQ(tours[rang + 3], initial[rang].combatant);
            EXPECT_EQ(tours[rang + 6], initial[rang].combatant);
        }
    };
    std::vector<int> des;
    std::vector<CombatantId> tours;
    jouer(des, tours);
    std::vector<int> desRejeu;
    std::vector<CombatantId> toursRejeu;
    jouer(desRejeu, toursRejeu);
    EXPECT_EQ(des, desRejeu);
    EXPECT_EQ(tours, toursRejeu);
}

/**
 * @brief Un tour ne se termine que sur demande, meme ressources epuisees.
 * \castest{<b>La fin d'un tour est explicite : epuiser ses ressources ne la declenche pas.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Heroine puis loup.<br/>2. Depenser action, action bonus, reaction et les six cases
 * de l'heroine.<br/>3. Terminer le tour, puis celui du loup.<br/>4. Tenter de terminer un tour
 * depuis un abonne au debut de tour.<br/>
 * \tattendu Ressources epuisees, le tour reste celui de l'heroine ; endTurn passe au loup, puis au
 * round 2 ou l'heroine retrouve ses ressources ; endTurn depuis un abonne est refuse.
 * }
 */
TEST(CombatStateTest, LeTourNeFinitQueSurDemande) {
    core::CombatState combat(ouverte());
    const CombatantId heroine = enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER));
    const CombatantId loup = enrole(combat, profil("Loup", CombatSide::Enemies, 10, DERNIER));
    std::vector<bool> finsDepuisUnAbonne;
    combat.subscribe(CombatHook::TurnStart, [&](core::CombatState& etat, const core::CombatEvent&) {
        finsDepuisUnAbonne.push_back(etat.endTurn());
    });
    EXPECT_FALSE(combat.endTurn());

    core::DeterministicRandom des(3);
    ASSERT_TRUE(combat.start(des));
    EXPECT_FALSE(combat.start(des));
    ASSERT_EQ(combat.activeCombatant(), heroine);
    EXPECT_TRUE(combat.spend(core::ACTION_RESOURCE));
    EXPECT_TRUE(combat.spend(core::BONUS_ACTION_RESOURCE));
    EXPECT_TRUE(combat.spend(core::REACTION_RESOURCE));
    EXPECT_TRUE(combat.spend(core::MOVEMENT_RESOURCE, 6));
    EXPECT_FALSE(combat.spend(core::ACTION_RESOURCE));
    EXPECT_EQ(combat.phase(), core::CombatPhase::TurnActive);
    EXPECT_EQ(combat.activeCombatant(), heroine);

    ASSERT_TRUE(combat.endTurn());
    EXPECT_EQ(combat.activeCombatant(), loup);
    EXPECT_EQ(combat.round(), 1);
    ASSERT_TRUE(combat.endTurn());
    EXPECT_EQ(combat.activeCombatant(), heroine);
    EXPECT_EQ(combat.round(), 2);
    EXPECT_EQ(combat.economy(heroine)->remaining(core::ACTION_RESOURCE), 1);
    EXPECT_EQ(combat.economy(heroine)->remaining(core::MOVEMENT_RESOURCE), 6);

    EXPECT_EQ(finsDepuisUnAbonne, (std::vector<bool>{false, false, false}));
}

/**
 * @brief La reaction revient au debut du tour de son porteur, pas a la fin du tour courant.
 * \castest{<b>Une reaction depensee hors de son tour ne revient qu'au debut du tour de son
 * porteur.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Ordre : heroine, loup, compagnon.<br/>2. Pendant le tour de l'heroine, le compagnon
 * depense sa reaction.<br/>3. Terminer le tour de l'heroine, puis celui du loup.<br/>
 * \tattendu Pendant le tour du loup, la reaction du compagnon est toujours a 0 ; elle revient a 1
 * quand son tour commence.
 * }
 */
TEST(CombatStateTest, LaReactionRevientAuDebutDuTourDeSonPorteur) {
    core::CombatState combat(ouverte());
    static_cast<void>(enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER)));
    const CombatantId loup = enrole(combat, profil("Loup", CombatSide::Enemies, 10, SECOND));
    const CombatantId compagnon =
        enrole(combat, profil("Compagnon", CombatSide::Allies, 10, DERNIER));
    core::DeterministicRandom des(5);
    ASSERT_TRUE(combat.start(des));

    ASSERT_TRUE(combat.economy(compagnon)->spend(core::REACTION_RESOURCE));
    ASSERT_TRUE(combat.endTurn());
    ASSERT_EQ(combat.activeCombatant(), loup);
    EXPECT_EQ(combat.economy(compagnon)->remaining(core::REACTION_RESOURCE), 0);
    ASSERT_TRUE(combat.endTurn());
    ASSERT_EQ(combat.activeCombatant(), compagnon);
    EXPECT_EQ(combat.economy(compagnon)->remaining(core::REACTION_RESOURCE), 1);
}

/**
 * @brief Premiere fin : la victoire.
 * \castest{<b>Un combat se termine par une victoire quand plus aucun ennemi n'est debout.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Deux allies contre deux gobelins.<br/>2. Abattre un gobelin, puis faire fuir
 * l'autre... non : abattre le second.<br/>3. Tenter de jouer apres la fin.<br/>
 * \tattendu Le combat continue apres le premier ; au second, issue Victoire annoncee une seule
 * fois, plus de tour actif, endTurn refuse.
 * }
 */
TEST(CombatStateTest, UneVictoireQuandPlusAucunEnnemiNEstDebout) {
    core::CombatState combat(ouverte());
    std::vector<std::string> journal;
    ecouter(combat, journal);
    static_cast<void>(enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER)));
    static_cast<void>(enrole(combat, profil("Compagnon", CombatSide::Allies, 10)));
    const CombatantId premier = enrole(combat, profil("Gobelin", CombatSide::Enemies, 5));
    const CombatantId second = enrole(combat, profil("Gobelin", CombatSide::Enemies, 5));
    core::DeterministicRandom des(9);
    ASSERT_TRUE(combat.start(des));

    combat.applyDamage(premier, 5);
    EXPECT_EQ(combat.find(premier)->status, core::CombatantStatus::Down);
    EXPECT_NE(combat.phase(), core::CombatPhase::Ended);
    combat.applyDamage(second, 9);
    EXPECT_EQ(combat.find(second)->profile.currentHitPoints, 0);

    EXPECT_EQ(combat.phase(), core::CombatPhase::Ended);
    EXPECT_EQ(combat.outcome(), core::CombatOutcome::Victory);
    EXPECT_FALSE(combat.activeCombatant().has_value());
    EXPECT_FALSE(combat.endTurn());
    combat.applyDamage(premier, 1);
    EXPECT_EQ(std::count(journal.begin(), journal.end(), "issue"), 1);
}

/**
 * @brief Deuxieme fin : la defaite.
 * \castest{<b>Un combat se termine par une defaite quand tous les allies sont a terre ; si les deux
 * camps tombent ensemble, c'est une defaite.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Deux allies contre un ogre ; abattre un allie, puis l'autre.<br/>2. Second combat :
 * une meme salve abat le premier allie, l'ogre et le second allie.<br/>
 * \tattendu Premier combat : il continue apres le premier allie, puis Defaite. Second : Defaite,
 * pas Victoire.
 * }
 */
TEST(CombatStateTest, UneDefaiteQuandTousLesAlliesSontATerre) {
    {
        core::CombatState combat(ouverte());
        const CombatantId heroine = enrole(combat, profil("Heroine", CombatSide::Allies, 4));
        const CombatantId compagnon = enrole(combat, profil("Compagnon", CombatSide::Allies, 4));
        static_cast<void>(enrole(combat, profil("Ogre", CombatSide::Enemies, 30)));
        core::DeterministicRandom des(1);
        ASSERT_TRUE(combat.start(des));
        combat.applyDamage(heroine, 4);
        EXPECT_FALSE(combat.outcome().has_value());
        combat.applyDamage(compagnon, 6);
        EXPECT_EQ(combat.outcome(), core::CombatOutcome::Defeat);
    }
    {
        core::CombatState combat(ouverte());
        const CombatantId heroine = enrole(combat, profil("Heroine", CombatSide::Allies, 4));
        const CombatantId compagnon = enrole(combat, profil("Compagnon", CombatSide::Allies, 4));
        const CombatantId ogre = enrole(combat, profil("Ogre", CombatSide::Enemies, 30));
        core::DeterministicRandom des(1);
        ASSERT_TRUE(combat.start(des));
        const std::array<core::HitPointChange, 3> salve{{
            {.target = heroine, .amount = 4},
            {.target = ogre, .amount = 30},
            {.target = compagnon, .amount = 4},
        }};
        combat.applyDamage(salve);
        EXPECT_EQ(combat.outcome(), core::CombatOutcome::Defeat);
    }
}

/**
 * @brief Troisieme fin : la fuite.
 * \castest{<b>Un combat se termine par une fuite quand plus aucun allie n'est debout et que l'un
 * d'eux est parti.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Rencontre dont on ne fuit pas : l'heroine tente de sortir.<br/>2. La rendre fuyable ;
 * l'heroine sort pendant son tour ; un gobelin sort aussi.<br/>3. Le compagnon tombe.<br/>
 * \tattendu Sortie refusee (NotEscapable) ; puis l'heroine quitte l'espace et l'ordre, son tour se
 * termine et le suivant commence ; la sortie d'un ennemi ne termine rien ; la chute du compagnon
 * donne Fuite.
 * }
 */
TEST(CombatStateTest, UneFuiteQuandLesAlliesQuittentLaZone) {
    core::CombatState combat(ouverte());
    std::vector<std::string> journal;
    ecouter(combat, journal);
    const CombatantId heroine =
        enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER), tile(1, 1));
    const CombatantId gobelin =
        enrole(combat, profil("Gobelin", CombatSide::Enemies, 7, SECOND), tile(5, 1));
    const CombatantId compagnon =
        enrole(combat, profil("Compagnon", CombatSide::Allies, 10, 0), tile(1, 2));
    static_cast<void>(enrole(combat, profil("Chef", CombatSide::Enemies, 12, DERNIER), tile(6, 1)));
    combat.setEscapable(false);
    EXPECT_EQ(combat.withdraw(heroine), core::WithdrawResult::NotInCombat);

    core::DeterministicRandom des(4);
    ASSERT_TRUE(combat.start(des));
    ASSERT_EQ(combat.activeCombatant(), heroine);
    EXPECT_EQ(combat.withdraw(heroine), core::WithdrawResult::NotEscapable);

    combat.setEscapable(true);
    journal.clear();
    EXPECT_EQ(combat.withdraw(heroine), core::WithdrawResult::Withdrawn);
    EXPECT_EQ(journal, (std::vector<std::string>{"sortie 1", "fin 1", "debut 2"}));
    EXPECT_FALSE(combat.positionOf(heroine).has_value());
    EXPECT_FALSE(combat.turnOrder().contains(heroine));
    EXPECT_EQ(combat.withdraw(heroine), core::WithdrawResult::NotInCombat);

    EXPECT_EQ(combat.withdraw(gobelin), core::WithdrawResult::Withdrawn);
    EXPECT_FALSE(combat.outcome().has_value());
    EXPECT_EQ(combat.activeCombatant(), compagnon);

    combat.applyDamage(compagnon, 10);
    EXPECT_EQ(combat.outcome(), core::CombatOutcome::Flight);
}

/**
 * @brief Quatre allies : rien ne suppose un heros unique.
 * \castest{<b>Un combat a quatre allies se deroule sans qu'aucun ne soit traite a part.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Quatre allies contre deux ennemis, graine 11.<br/>2. Jouer trois rounds.<br/>3.
 * Abattre trois allies, jouer un round, puis abattre les ennemis.<br/>
 * \tattendu Chacun des six joue exactement trois tours ; trois allies a terre ne terminent pas le
 * combat et leurs tours sont passes ; la fin est une Victoire.
 * }
 */
TEST(CombatStateTest, QuatreAlliesSansHerosUnique) {
    core::CombatState combat(ouverte());
    std::vector<CombatantId> allies;
    for (const char* nom : {"Heroine", "Guerrier", "Magicienne", "Pretre"}) {
        allies.push_back(enrole(combat, profil(nom, CombatSide::Allies, 10, 1)));
    }
    const CombatantId loup = enrole(combat, profil("Loup", CombatSide::Enemies, 10, 2));
    const CombatantId ours = enrole(combat, profil("Ours", CombatSide::Enemies, 10, 0));
    core::DeterministicRandom des(11);
    ASSERT_TRUE(combat.start(des));
    EXPECT_EQ(combat.turnOrder().entries().size(), 6U);

    std::map<CombatantId, int> tours;
    while (combat.round() <= 3) {
        ++tours[*combat.activeCombatant()];
        ASSERT_TRUE(combat.endTurn());
    }
    EXPECT_EQ(tours.size(), 6U);
    for (const auto& [id, nombre] : tours) {
        EXPECT_EQ(nombre, 3) << static_cast<int>(id);
    }

    combat.applyDamage(allies[0], 10);
    combat.applyDamage(allies[1], 10);
    combat.applyDamage(allies[2], 10);
    EXPECT_FALSE(combat.outcome().has_value());
    const int round = combat.round();
    std::vector<CombatantId> joueurs;
    while (combat.round() == round) {
        joueurs.push_back(*combat.activeCombatant());
        ASSERT_TRUE(combat.endTurn());
    }
    std::sort(joueurs.begin(), joueurs.end());
    EXPECT_EQ(joueurs, (std::vector<CombatantId>{allies[3], loup, ours}));

    combat.applyDamage(loup, 10);
    combat.applyDamage(ours, 10);
    EXPECT_EQ(combat.outcome(), core::CombatOutcome::Victory);
}

/**
 * @brief Un combat a cinq se deroule sans fenetre jusqu'a sa fin, et se rejoue a l'identique.
 * \castest{<b>Une escarmouche a cinq combattants va du premier round a une fin, et le rejeu a
 * graine fixe est exact.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Deux allies contre trois gobelins, sur une carte a pilier, dans l'espace en
 * metres.<br/>2. Chaque combattant marche vers la place qui le rapproche le plus de l'ennemi le
 * plus proche, frappe a l'allonge (1,5 m entre les bords), termine son tour.<br/>3. Rejouer a la
 * meme graine, puis a une autre.<br/>
 * \tattendu Le combat se termine sur une issue ; les cinq ont joue ; meme graine, meme journal,
 * initiative, pas et jets compris ; une autre graine donne un autre journal.
 * }
 */
TEST(CombatStateTest, UnCombatACinqSeDerouleSansFenetreEtSeRejoue) {
    std::optional<core::CombatOutcome> issue;
    int rounds = 0;
    const std::vector<std::string> journal = escarmouche(2026, issue, rounds);
    ASSERT_TRUE(issue.has_value());
    EXPECT_GE(rounds, 2);
    for (const char* debut : {"debut 1", "debut 2", "debut 3", "debut 4", "debut 5"}) {
        EXPECT_NE(std::find(journal.begin(), journal.end(), debut), journal.end()) << debut;
    }
    EXPECT_EQ(std::count(journal.begin(), journal.end(), "issue"), 1);

    std::optional<core::CombatOutcome> issueRejeu;
    int roundsRejeu = 0;
    EXPECT_EQ(escarmouche(2026, issueRejeu, roundsRejeu), journal);
    EXPECT_EQ(issueRejeu, issue);
    EXPECT_EQ(roundsRejeu, rounds);

    std::optional<core::CombatOutcome> autreIssue;
    int autresRounds = 0;
    EXPECT_NE(escarmouche(7, autreIssue, autresRounds), journal);
}

/**
 * @brief Un renfort entre en cours de combat et prend sa place par la regle d'ordre.
 * \castest{<b>Un renfort appele au rang 0 joue au round suivant ; un combattant qui entre apres la
 * place en cours joue ce round-ci.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Heroine (tres haute initiative), repere « renforts » au rang 0, chef (tres
 * basse).<br/>
 * 2. Au repere du round 1, faire entrer un gobelin a l'initiative 0.<br/>3. Au round 2, pendant le
 * tour de l'heroine, faire entrer un loup d'initiative plus basse que tout, puis un combattant a
 * la place du loup.<br/>
 * \tattendu Round 1 : heroine, renforts, entree, chef ; round 2 : heroine, gobelin, renforts, loup,
 * chef ; l'entree sur une place prise est refusee (Occupied) sans consommer d'identifiant.
 * }
 */
TEST(CombatStateTest, UnRenfortEntreEnCoursDeCombat) {
    core::CombatState combat(ouverte());
    std::vector<std::string> journal;
    ecouter(combat, journal);
    static_cast<void>(
        enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER), tile(1, 1)));
    static_cast<void>(
        enrole(combat, profil("Chef", CombatSide::Enemies, 10, DERNIER * 2), tile(8, 1)));
    ASSERT_TRUE(combat.addInitiativeMarker({.count = 0, .name = "renforts"}));
    combat.subscribe(CombatHook::InitiativeCount,
                     [](core::CombatState& etat, const core::CombatEvent& e) {
                         if (e.marker == "renforts" && e.round == 1) {
                             static_cast<void>(etat.joinAtInitiative(
                                 profil("Gobelin", CombatSide::Enemies, 7), tile(8, 2), 0));
                         }
                     });
    core::DeterministicRandom des(21);
    ASSERT_TRUE(combat.start(des));
    ASSERT_TRUE(combat.endTurn());  // heroine
    ASSERT_TRUE(combat.endTurn());  // chef
    ASSERT_EQ(combat.round(), 2);

    const core::EnlistResult loup =
        combat.join(profil("Loup", CombatSide::Enemies, 9, DERNIER), tile(8, 3), des);
    ASSERT_EQ(loup.combatant, CombatantId{4});
    const core::EnlistResult refuse =
        combat.join(profil("Rat", CombatSide::Enemies, 2), tile(8, 3), des);
    EXPECT_FALSE(refuse.combatant.has_value());
    EXPECT_EQ(refuse.placement, core::PlacementResult::Occupied);
    for (int tour = 0; tour < 4; ++tour) {
        ASSERT_TRUE(combat.endTurn());
    }

    const std::vector<std::string> attendu{
        "avant",         "round 1", "debut 1", "fin 1",    "rang renforts", "entree 3", "debut 2",
        "fin 2",         "round 2", "debut 1", "entree 4", "fin 1",         "debut 3",  "fin 3",
        "rang renforts", "debut 4", "fin 4",   "debut 2",  "fin 2",         "round 3",  "debut 1"};
    EXPECT_EQ(journal, attendu);
    EXPECT_EQ(combat.combatants().size(), 4U);
}

/**
 * @brief Les points d'insertion s'annoncent dans l'ordre, et l'acteur flottant joue quand il veut.
 * \castest{<b>Les crochets du combat s'annoncent dans un ordre fixe, repere fixe et acteur flottant
 * compris.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Heroine (haute initiative), acteur flottant, gobelin (basse), repere « repaire » au
 * rang 20.<br/>2. Round 1 : l'acteur flottant demande a jouer pendant le tour de l'heroine ; une
 * attaque est declaree.<br/>3. Round 2 : il ne demande rien.<br/>
 * \tattendu Avant le premier tour, puis round 1 : heroine, flottant, repaire, gobelin ; round 2 :
 * heroine, repaire, gobelin, flottant ; une seconde demande et une demande avant le round 1 sont
 * refusees ; le flottant n'a pas de place dans l'ordre.
 * }
 */
TEST(CombatStateTest, LesCrochetsSAnnoncentDansLOrdre) {
    core::CombatState combat(ouverte());
    std::vector<std::string> journal;
    ecouter(combat, journal);
    const CombatantId heroine = enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER));
    core::CombatantProfile gardien = profil("Gardien du temps", CombatSide::Allies, 10);
    gardien.floating = true;
    const CombatantId flottant = enrole(combat, gardien);
    const CombatantId gobelin = enrole(combat, profil("Gobelin", CombatSide::Enemies, 7, DERNIER));
    ASSERT_TRUE(combat.addInitiativeMarker({.count = 20, .name = "repaire"}));
    std::optional<bool> demandeAvantLePremierTour;
    combat.subscribe(CombatHook::BeforeFirstTurn,
                     [&](core::CombatState& etat, const core::CombatEvent&) {
                         demandeAvantLePremierTour = etat.interject(flottant);
                     });

    core::DeterministicRandom des(8);
    ASSERT_TRUE(combat.start(des));
    EXPECT_EQ(demandeAvantLePremierTour, false);
    EXPECT_FALSE(combat.turnOrder().contains(flottant));
    EXPECT_FALSE(combat.find(flottant)->initiativeRoll.has_value());
    EXPECT_FALSE(combat.interject(heroine));
    EXPECT_TRUE(combat.interject(flottant));
    EXPECT_FALSE(combat.interject(flottant));
    EXPECT_TRUE(combat.declareAttack(heroine, gobelin));
    for (int tour = 0; tour < 6; ++tour) {
        ASSERT_TRUE(combat.endTurn());
    }

    const std::vector<std::string> attendu{
        "avant",        "round 1", "debut 1", "attaque 1>3", "fin 1",   "debut 2", "fin 2",
        "rang repaire", "debut 3", "fin 3",   "round 2",     "debut 1", "fin 1",   "rang repaire",
        "debut 3",      "fin 3",   "debut 2", "fin 2",       "round 3", "debut 1"};
    EXPECT_EQ(journal, attendu);
}

/**
 * @brief Un combattant a terre passe ses tours, et celui qui tombe pendant son tour le termine.
 * \castest{<b>Les tours d'un combattant a terre sont passes ; tomber pendant son tour le
 * termine.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Ordre : heroine, loup, compagnon, ours.<br/>2. Abattre le compagnon pendant le tour
 * de l'heroine, puis terminer les tours.<br/>3. Le relever ; au round 2, abattre le loup pendant
 * son propre tour.<br/>
 * \tattendu Le compagnon est saute au round 1 et rejoue au round 2 ; le tour du loup se termine
 * aussitot et le compagnon prend la main.
 * }
 */
TEST(CombatStateTest, UnCombattantATerrePasseSonTour) {
    core::CombatState combat(ouverte());
    std::vector<std::string> journal;
    ecouter(combat, journal);
    const CombatantId heroine = enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER));
    const CombatantId loup = enrole(combat, profil("Loup", CombatSide::Enemies, 10, SECOND));
    const CombatantId compagnon = enrole(combat, profil("Compagnon", CombatSide::Allies, 10, 0));
    const CombatantId ours = enrole(combat, profil("Ours", CombatSide::Enemies, 10, DERNIER));
    core::DeterministicRandom des(2);
    ASSERT_TRUE(combat.start(des));

    combat.applyDamage(compagnon, 10);
    ASSERT_TRUE(combat.endTurn());
    EXPECT_EQ(combat.activeCombatant(), loup);
    ASSERT_TRUE(combat.endTurn());
    EXPECT_EQ(combat.activeCombatant(), ours);

    combat.heal(compagnon, 3);
    EXPECT_EQ(combat.find(compagnon)->status, core::CombatantStatus::Standing);
    ASSERT_TRUE(combat.endTurn());
    EXPECT_EQ(combat.activeCombatant(), heroine);
    ASSERT_TRUE(combat.endTurn());
    ASSERT_EQ(combat.activeCombatant(), loup);

    journal.clear();
    combat.applyDamage(loup, 10);
    EXPECT_EQ(journal, (std::vector<std::string>{"fin 2", "debut 3"}));
    EXPECT_EQ(combat.activeCombatant(), compagnon);
}

/**
 * @brief Le deplacement du tour paie son chemin, et le camp dit qui l'on traverse.
 * \castest{<b>Le deplacement se paie sur le budget restant ; on traverse un allie, un ennemi a deux
 * tailles d'ecart, en terrain difficile, sans finir dans leur espace ; jamais un ennemi de taille
 * voisine.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Couloir de 7 cases sur 1 (10,5 m sur 1,5 m) : heroine (8 cases, 12 m) au centre de la
 * case 0, compagnon en 1, rat tres petit ennemi en 3.<br/>2. Aller en 1, en 5, en 2, puis
 * en 4.<br/>
 * 3. Meme couloir avec un gobelin de taille M a la place du rat.<br/>
 * \tattendu Places de fin : les centres des cases 2 et 4, rien entre ; finir sur le compagnon et
 * aller en 5 (12,75 m) est refuse ; aller en 2 coute 6 m (les 3 m ou l'on chevauche le compagnon
 * comptent double), soit 4 cases ; de 2, aller en 4 coute les 6 m restants ; avec le gobelin,
 * seule la case 2 est une place de fin, et le gobelin ne se traverse pas.
 * }
 */
TEST(CombatStateTest, LeDeplacementPaieLeCheminEtLesCampsDisentQuiSeTraverse) {
    const auto couloir = [](core::CreatureSize tailleEnnemi) {
        auto combat = std::make_unique<core::CombatState>(test_support::openSpace(7, 1));
        static_cast<void>(
            enrole(*combat, profil("Heroine", CombatSide::Allies, 10, PREMIER, 8), tile(0, 0)));
        static_cast<void>(enrole(*combat, profil("Compagnon", CombatSide::Allies, 10), tile(1, 0)));
        core::CombatantProfile ennemi = profil("Ennemi", CombatSide::Enemies, 3, DERNIER);
        ennemi.size = tailleEnnemi;
        static_cast<void>(enrole(*combat, ennemi, tile(3, 0)));
        return combat;
    };

    {
        const auto combat = couloir(core::CreatureSize::Tiny);
        EXPECT_EQ(combat->move(tile(2, 0)).result, core::MoveResult::NoActiveTurn);
        core::DeterministicRandom des(6);
        ASSERT_TRUE(combat->start(des));
        EXPECT_NEAR(combat->movementLeft(), 12.0f, CM);
        const std::vector<core::Destination> places = combat->destinations();
        ASSERT_FALSE(places.empty());
        EXPECT_TRUE(proche(places.front().point, tile(0, 0))) << "la place de depart en tete";
        const std::vector<Meters3> finales = fins(places);
        ASSERT_EQ(finales.size(), 2U);
        EXPECT_TRUE(proche(finales[0], tile(2, 0)));
        EXPECT_TRUE(proche(finales[1], tile(4, 0)));

        EXPECT_FALSE(combat->routeTo(tile(1, 0)).has_value()) << "on ne finit pas sur un allie";
        EXPECT_EQ(combat->move(tile(1, 0)).result, core::MoveResult::Unreachable);
        EXPECT_EQ(combat->move(tile(5, 0)).result, core::MoveResult::Unreachable);

        const core::MoveOutcome premier = combat->move(tile(2, 0));
        ASSERT_EQ(premier.result, core::MoveResult::Moved);
        EXPECT_NEAR(premier.path.length, 6.0f, CM);
        ASSERT_FALSE(premier.path.points.empty());
        EXPECT_TRUE(proche(premier.path.points.back(), tile(2, 0)));
        EXPECT_EQ(combat->economy(CombatantId{1})->remaining(core::MOVEMENT_RESOURCE), 4);
        EXPECT_NEAR(combat->movementLeft(), 6.0f, CM);

        const core::MoveOutcome second = combat->move(tile(4, 0));
        ASSERT_EQ(second.result, core::MoveResult::Moved);
        EXPECT_NEAR(second.path.length, 6.0f, CM);
        EXPECT_TRUE(proche(*combat->positionOf(CombatantId{1}), tile(4, 0)));
        EXPECT_EQ(combat->economy(CombatantId{1})->remaining(core::MOVEMENT_RESOURCE), 0);
        EXPECT_NEAR(combat->movementLeft(), 0.0f, CM);
        EXPECT_TRUE(fins(combat->destinations()).empty());
    }
    {
        const auto combat = couloir(core::CreatureSize::Medium);
        core::DeterministicRandom des(6);
        ASSERT_TRUE(combat->start(des));
        const std::vector<Meters3> finales = fins(combat->destinations());
        ASSERT_EQ(finales.size(), 1U);
        EXPECT_TRUE(proche(finales[0], tile(2, 0)));
        EXPECT_FALSE(combat->routeFor(CombatantId{1}, tile(4, 0), -1.0f).has_value())
            << "un ennemi de taille voisine ferme le couloir";
    }
}

/**
 * @brief Le montage d'une rencontre attribue les identifiants, place, et dit ce qu'il refuse.
 * \castest{<b>Le montage pose le groupe puis les creatures de la rencontre, et nomme chaque refus
 * avec sa raison.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Carte a un mur ; rencontre de cinq entrees : un gobelin libre, un dans le mur, une
 * creature inconnue, une chauve-souris, un gobelin sur la case de l'heroine.<br/>2. Monter la
 * rencontre avec l'heroine au declencheur.<br/>3. Gagner le combat et le terminer.<br/>
 * \tattendu Allie 1, ennemis 2 et 3, chacun au centre de sa case ; trois refus : mur (Obstructed),
 * inconnue (sans raison d'espace), place prise (Occupied) ; la chauve-souris vole ; la fiche donne
 * +3 et 6 cases ; la fuite est interdite comme dans la donnee ; la victoire pose le drapeau de la
 * rencontre.
 * }
 */
TEST(CombatStateTest, LeMontageDUneRencontrePlaceEtRefuseEnLeDisant) {
    core::Bestiary bestiaire;
    core::Creature chauveSouris;
    chauveSouris.id = "chauve-souris";
    chauveSouris.name = "Chauve-souris";
    chauveSouris.size = core::CreatureSize::Tiny;
    chauveSouris.hitPoints = 1;
    chauveSouris.abilities = {2, 15, 8, 2, 12, 4};
    chauveSouris.speed.walk = 1.5F;
    chauveSouris.speed.fly = 9.0F;
    core::Creature gobelin;
    gobelin.id = "gobelin";
    gobelin.name = "Gobelin";
    gobelin.size = core::CreatureSize::Small;
    gobelin.hitPoints = 7;
    gobelin.abilities = {8, 14, 10, 10, 8, 8};
    gobelin.speed.walk = 9.0F;
    bestiaire.creatures = {chauveSouris, gobelin};

    core::Encounter rencontre;
    rencontre.id = "embuscade";
    rencontre.escapable = false;
    rencontre.combatants = {
        {.creatureId = "gobelin", .columnOffset = 2, .rowOffset = 0},
        {.creatureId = "gobelin", .columnOffset = 3, .rowOffset = 0},
        {.creatureId = "fantome", .columnOffset = 0, .rowOffset = -1},
        {.creatureId = "chauve-souris", .columnOffset = 1, .rowOffset = 1},
        {.creatureId = "gobelin", .columnOffset = 0, .rowOffset = 0},
    };
    const core::GridPosition declencheur{3, 3};
    const core::EncounterRun engagee =
        core::beginEncounter(rencontre, {.captured = true}, declencheur, "carte/embuscade/3/3");

    core::CharacterSheet heroine;
    heroine.name = "Heroine";
    heroine.abilities = {10, 16, 12, 10, 10, 10};
    heroine.maximumHitPoints = 12;
    heroine.currentHitPoints = 12;
    heroine.speedMeters = 9.0F;
    const std::array<core::PartyMember, 1> groupe{
        core::PartyMember{.profile = core::profileFor(heroine), .position = declencheur}};

    core::TileMap carte(10, 6);
    carte.setTile(6, 3, core::TileType::Wall);
    core::CombatState combat{test_support::spaceOf(carte)};
    const core::EncounterMount montage = core::mountEncounter(combat, engagee, bestiaire, groupe);

    EXPECT_EQ(montage.allies, (std::vector<CombatantId>{CombatantId{1}}));
    EXPECT_EQ(montage.enemies, (std::vector<CombatantId>{CombatantId{2}, CombatantId{3}}));
    ASSERT_EQ(montage.refusals.size(), 3U);
    EXPECT_EQ(montage.refusals[0].who, "gobelin");
    EXPECT_EQ(montage.refusals[0].position, (core::GridPosition{6, 3}));
    EXPECT_EQ(montage.refusals[0].placement, core::PlacementResult::Obstructed);
    EXPECT_EQ(montage.refusals[1].who, "fantome");
    EXPECT_FALSE(montage.refusals[1].placement.has_value());
    EXPECT_EQ(montage.refusals[2].placement, core::PlacementResult::Occupied);

    EXPECT_EQ(combat.find(CombatantId{1})->profile.initiativeModifier, 3);
    EXPECT_EQ(combat.find(CombatantId{1})->profile.movement, 6);
    ASSERT_TRUE(combat.positionOf(CombatantId{2}).has_value());
    EXPECT_TRUE(proche(*combat.positionOf(CombatantId{2}), tile(5, 3)))
        << "pose au centre de sa case, contre le mur";
    EXPECT_EQ(combat.find(CombatantId{3})->profile.locomotion, core::Locomotion::Fly);
    EXPECT_EQ(combat.find(CombatantId{3})->profile.movement, 6);
    EXPECT_FALSE(combat.escapable());

    core::DeterministicRandom des(12);
    ASSERT_TRUE(combat.start(des));
    EXPECT_EQ(combat.withdraw(CombatantId{1}), core::WithdrawResult::NotEscapable);
    combat.applyDamage(CombatantId{2}, 7);
    combat.applyDamage(CombatantId{3}, 1);
    ASSERT_EQ(combat.outcome(), core::CombatOutcome::Victory);

    core::WorldFlags drapeaux;
    static_cast<void>(core::endEncounter(engagee, *combat.outcome(), drapeaux));
    EXPECT_TRUE(drapeaux.isSet("carte/embuscade/3/3"));
}

// --- Le deplacement dans l'espace (LOT-19, LOT-1017) -----------------------------------------
//
// Les regles du Manuel que la grille de combat et son chemin verifiaient (`test_battle_grid.cpp`,
// `test_pathfinding.cpp`, retires au LOT-1017), rejouees en metres sur le combat.

namespace {

/// Une carte 6 x 4 dont la couche de decor, marquee difficile, couvre deux cases, dont une seconde
/// couche porte une regle de zone que l'espace ne connait pas, et une troisieme une coquille.
[[nodiscard]] core::Level carteAZones() {
    core::TileMap collision(6, 4);
    collision.setTile(5, 0, core::TileType::Wall);

    core::TileMap boue(6, 4);
    boue.setTile(1, 1, core::TileType::Water);
    boue.setTile(2, 1, core::TileType::Water);

    core::TileMap cercle(6, 4);
    cercle.setTile(2, 1, core::TileType::Grass);
    cercle.setTile(3, 1, core::TileType::Grass);

    core::TileMap mal(6, 4);
    mal.setTile(0, 3, core::TileType::Grass);

    std::vector<core::TileLayer> couches;
    couches.push_back(
        {.name = "collision", .kind = core::LayerKind::Collision, .tiles = collision});
    couches.push_back({.name = "boue",
                       .kind = core::LayerKind::Decor,
                       .tiles = std::move(boue),
                       .properties = {{"difficultTerrain", true}}});
    couches.push_back({.name = "cercle",
                       .kind = core::LayerKind::Decor,
                       .tiles = std::move(cercle),
                       .properties = {{"noHealing", true}}});
    // Une coquille : `1` n'est pas `true`, et une faute de saisie ne doit pas devenir une regle.
    couches.push_back({.name = "coquille",
                       .kind = core::LayerKind::Decor,
                       .tiles = std::move(mal),
                       .properties = {{"difficultTerrain", std::int64_t{1}}}});
    return core::Level(core::LevelData{
        .name = "zones", .tileMap = std::move(collision), .layers = std::move(couches)});
}

/// Une carte 9 x 7 avec un mur en L et trois cases de boue, le heros (#1) en (1, 3) et un ennemi
/// (#2) au coin oppose : de quoi rendre les egalites de cout nombreuses.
[[nodiscard]] std::unique_ptr<core::CombatState> combatAccidente() {
    core::TileMap collision(9, 7);
    for (int row = 1; row <= 4; ++row) {
        collision.setTile(4, row, core::TileType::Wall);
    }
    collision.setTile(5, 4, core::TileType::Wall);
    collision.setTile(6, 4, core::TileType::Wall);
    const std::shared_ptr<core::SimulatedSpace> espace = test_support::spaceOf(collision);
    espace->addDifficult(caseAuSol(2, 5));
    espace->addDifficult(caseAuSol(3, 5));
    espace->addDifficult(caseAuSol(2, 2));
    auto combat = std::make_unique<core::CombatState>(espace);
    static_cast<void>(
        enrole(*combat, profil("Heros", CombatSide::Allies, 10, PREMIER, 12), tile(1, 3)));
    static_cast<void>(
        enrole(*combat, profil("Loup", CombatSide::Enemies, 10, DERNIER), tile(8, 6)));
    return combat;
}

constexpr CombatantId HEROS{1};

}  // namespace

/**
 * @brief Le budget se deduit de la vitesse en metres, a raison d'une case pour 1,5 m.
 * \castest{<b>Le budget de deplacement vaut la vitesse divisee par 1,5, arrondie en
 * dessous.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Convertir 9 m, 7,5 m, 10 m, 0 m et -3 m.<br/>2. Lire le budget d'une fiche a 9
 * m.<br/>
 * 3. Lire le budget de marche et de vol d'une creature qui ne vole pas, puis d'une qui vole.<br/>
 * \tattendu 6, 5, 6, 0, 0 ; 6 pour la fiche ; la creature sans vol a un budget de vol nul.
 * }
 */
TEST(CombatStateTest, LeBudgetSeDeduitDeLaVitesse) {
    EXPECT_EQ(core::movementBudget(9.0F), 6) << "Manuel des Joueurs : 9 metres, 6 cases";
    EXPECT_EQ(core::movementBudget(7.5F), 5);
    EXPECT_EQ(core::movementBudget(10.0F), 6) << "un segment de 1,50 m entame n'en est pas un";
    EXPECT_EQ(core::movementBudget(13.5F - 4.5F), 6);
    EXPECT_EQ(core::movementBudget(0.0F), 0);
    EXPECT_EQ(core::movementBudget(-3.0F), 0);

    core::CharacterSheet fiche;
    fiche.speedMeters = 9.0F;
    EXPECT_EQ(core::movementBudget(fiche), 6);

    core::Creature loup;
    loup.speed.walk = 12.0F;
    EXPECT_EQ(core::movementBudget(loup, core::Locomotion::Walk), 8);
    EXPECT_EQ(core::movementBudget(loup, core::Locomotion::Fly), 0);
    core::Creature chouette;
    chouette.speed.walk = 1.5F;
    chouette.speed.fly = 18.0F;
    EXPECT_EQ(core::movementBudget(chouette, core::Locomotion::Fly), 12);
}

/**
 * @brief Les places atteignables sont celles du budget, a vol d'oiseau sur un sol libre.
 * \castest{<b>Sur un sol libre, une place est atteignable si et seulement si sa distance tient
 * dans le budget, diagonale comprise : la diagonale n'est plus une case.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Salle ouverte de 11 x 11 cases, heros au centre de la case (5,5).<br/>2. Pour un
 * budget de 0 a 4 cases (0 a 6 m), lire les places de fin et les chemins vers les centres des
 * cases sur la ligne et sur la diagonale.<br/>
 * \tattendu Chaque place de fin a un chemin dans le budget, et le heros peut s'y tenir ; le
 * centre de la case a k cases sur la ligne est atteint pour 1,5 k m si k tient dans le budget, et
 * seulement alors ; sur la diagonale, il faut 2,12 k m : (8,8) n'est pas atteint avec 4 cases.
 * }
 */
TEST(CombatStateTest, LesPlacesAtteignablesSontCellesDuBudget) {
    core::CombatState combat(test_support::openSpace(11, 11));
    const CombatantId heros = enrole(combat, profil("Heros", CombatSide::Allies, 10), tile(5, 5));
    const Meters3 centre = tile(5, 5);

    for (int budget = 0; budget <= 4; ++budget) {
        const float metres = core::metersFromTiles(static_cast<float>(budget));
        const std::vector<core::Destination> places = combat.destinationsFor(heros, metres);
        ASSERT_FALSE(places.empty());
        EXPECT_TRUE(proche(places.front().point, centre));
        for (std::size_t i = 1; i < places.size(); ++i) {
            EXPECT_LE(places[i].route.length, metres + CM) << "budget " << budget;
            EXPECT_LE(core::groundDistance(centre, places[i].point), metres + CM);
            EXPECT_TRUE(combat.canStandAt(heros, places[i].point));
        }
        const std::vector<Meters3> finales = fins(places);
        for (int k = 1; k <= 5; ++k) {
            const Meters3 ligne = tile(5 + k, 5);
            EXPECT_EQ(parmi(finales, ligne), k <= budget) << "budget " << budget << ", k " << k;
            const std::optional<core::Route> droit = combat.routeFor(heros, ligne, metres);
            ASSERT_EQ(droit.has_value(), k <= budget) << "budget " << budget << ", k " << k;
            if (droit.has_value()) {
                EXPECT_NEAR(droit->length, 1.5f * static_cast<float>(k), CM);
            }
        }
        for (int k = 1; k <= 3; ++k) {
            const float longueur = 1.5f * std::sqrt(2.0f) * static_cast<float>(k);
            const std::optional<core::Route> diagonale =
                combat.routeFor(heros, tile(5 + k, 5 + k), metres);
            ASSERT_EQ(diagonale.has_value(), longueur <= metres)
                << "budget " << budget << ", diagonale " << k;
            if (diagonale.has_value()) {
                EXPECT_NEAR(diagonale->length, longueur, CM);
            }
        }
    }
}

/**
 * @brief Un mur coute le detour : la portee se compte sur le chemin, pas a vol d'oiseau.
 * \castest{<b>Un mur entre deux places voisines coute le detour.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Carte de 7 x 5 cases, mur en colonne 3 des lignes 0 a 2.<br/>2. Heros au centre de
 * (2,1), cible au centre de (4,1), a 3 m de l'autre cote du mur.<br/>
 * \tattendu Le chemin fait 9 m (6 cases) : il descend sous le mur, le longe a une demi-case et
 * remonte, sans en couper le coin. Un budget de 7,5 m ne l'atteint pas, un budget de 9 m si.
 * }
 */
TEST(CombatStateTest, UnMurCouteLeDetour) {
    core::TileMap collision(7, 5);
    for (int row = 0; row <= 2; ++row) {
        collision.setTile(3, row, core::TileType::Wall);
    }
    core::CombatState combat(test_support::spaceOf(collision));
    const CombatantId heros = enrole(combat, profil("Heros", CombatSide::Allies, 10), tile(2, 1));

    EXPECT_NEAR(core::groundDistance(tile(2, 1), tile(4, 1)), 3.0f, CM);
    EXPECT_FALSE(combat.routeFor(heros, tile(4, 1), 7.5f).has_value())
        << "a vol d'oiseau, la cible n'est qu'a 3 m";
    const std::optional<core::Route> chemin = combat.routeFor(heros, tile(4, 1), 9.0f);
    ASSERT_TRUE(chemin.has_value());
    EXPECT_NEAR(chemin->length, 9.0f, CM);
    ASSERT_FALSE(chemin->points.empty());
    EXPECT_TRUE(proche(chemin->points.back(), tile(4, 1)));
    for (const Meters3 pas : chemin->points) {
        EXPECT_TRUE(combat.canStandAt(heros, pas)) << texte(pas);
    }
}

/**
 * @brief Le terrain difficile double le cout, et reduit la portee en consequence.
 * \castest{<b>Le terrain difficile double le cout des metres qu'on y marche, et reduit la
 * portee.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Salle ouverte de 11 x 11 cases, heros au centre de (5,5).<br/>2. Rendre difficile la
 * case voisine (6,5) ; chemins vers son centre et vers (7,5), au-dela.<br/>3. Rendre toute la
 * salle difficile, budget de 4 cases (6 m).<br/>
 * \tattendu Le centre de (6,5) coute 2,25 m (0,75 m hors de la boue, 0,75 m dedans compte double),
 * hors d'un budget d'une case ; (7,5) se rejoint en contournant la boue (4,24 m) plutot qu'en la
 * traversant (4,5 m) ; toute la salle difficile, le centre a deux cases coute 6 m et celui a trois
 * cases est hors de portee.
 * }
 */
TEST(CombatStateTest, LeTerrainDifficileDoubleLeCoutEtReduitLaPortee) {
    const std::shared_ptr<core::SimulatedSpace> espace = test_support::openSpace(11, 11);
    core::CombatState combat(espace);
    const CombatantId heros = enrole(combat, profil("Heros", CombatSide::Allies, 10), tile(5, 5));

    espace->addDifficult(caseAuSol(6, 5));
    const std::optional<core::Route> boue = combat.routeFor(heros, tile(6, 5), -1.0f);
    ASSERT_TRUE(boue.has_value());
    EXPECT_NEAR(boue->length, 2.25f, CM);
    EXPECT_FALSE(combat.routeFor(heros, tile(6, 5), 1.5f).has_value())
        << "il faut pouvoir payer l'entree";
    const std::optional<core::Route> auDela = combat.routeFor(heros, tile(7, 5), -1.0f);
    ASSERT_TRUE(auDela.has_value());
    EXPECT_NEAR(auDela->length, 3.0f * std::sqrt(2.0f), CM)
        << "le detour par les diagonales evite la boue";

    espace->addDifficult({0.0f, 0.0f, 16.5f, 16.5f});
    const std::optional<core::Route> deux = combat.routeFor(heros, tile(7, 5), 6.0f);
    ASSERT_TRUE(deux.has_value());
    EXPECT_NEAR(deux->length, 6.0f, CM);
    EXPECT_FALSE(combat.routeFor(heros, tile(8, 5), 6.0f).has_value());
    const std::vector<core::Destination> places = combat.destinationsFor(heros, 6.0f);
    ASSERT_GT(places.size(), 1U);
    for (std::size_t i = 1; i < places.size(); ++i) {
        EXPECT_LE(core::groundDistance(tile(5, 5), places[i].point), 3.0f + CM)
            << "la portee est divisee par deux";
    }
}

/**
 * @brief Le deplacement se paie en cases entamees ; ce qui reste de la case sert au pas suivant.
 * \castest{<b>Un pas se paie en cases de 1,5 m entamees, et le reste de la case entamee sert au
 * pas suivant du meme tour : deux pas de 0,75 m coutent une case, pas deux.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Heros (6 cases) au centre de (2,2), un ennemi au loin.<br/>2. Faire un pas de 0,75 m,
 * puis un second de 0,75 m, puis un de 2,25 m.<br/>3. Finir le tour, et celui de l'ennemi.<br/>
 * \tattendu Apres le premier pas, 5 cases et 0,75 m de reste (8,25 m) ; apres le second, 5 cases
 * et rien (7,5 m) ; apres le troisieme, 3 cases et 0,75 m (5,25 m) ; au tour suivant, 6 cases et
 * pas de reste.
 * }
 */
TEST(CombatStateTest, LeDeplacementSePaieEnCasesEntamees) {
    core::CombatState combat(ouverte());
    const CombatantId heros =
        enrole(combat, profil("Heros", CombatSide::Allies, 10, PREMIER), tile(2, 2));
    static_cast<void>(
        enrole(combat, profil("Loup", CombatSide::Enemies, 10, DERNIER), tile(10, 6)));
    core::DeterministicRandom des(4);
    ASSERT_TRUE(combat.start(des));
    ASSERT_EQ(combat.activeCombatant(), heros);
    EXPECT_NEAR(combat.movementLeft(), 9.0f, CM);

    const auto pas = [&](float x, float longueur, int cases, float reste) {
        const core::MoveOutcome issue = combat.move({x, 3.75f, 0.0f});
        ASSERT_EQ(issue.result, core::MoveResult::Moved) << x;
        EXPECT_NEAR(issue.path.length, longueur, CM) << x;
        EXPECT_EQ(combat.economy(heros)->remaining(core::MOVEMENT_RESOURCE), cases) << x;
        EXPECT_NEAR(combat.find(heros)->movementSlack, reste, CM) << x;
        EXPECT_NEAR(combat.movementLeft(), 1.5f * static_cast<float>(cases) + reste, CM) << x;
    };
    pas(4.5f, 0.75f, 5, 0.75f);
    pas(5.25f, 0.75f, 5, 0.0f);
    pas(7.5f, 2.25f, 3, 0.75f);

    ASSERT_TRUE(combat.endTurn());
    ASSERT_TRUE(combat.endTurn());
    ASSERT_EQ(combat.activeCombatant(), heros);
    EXPECT_EQ(combat.economy(heros)->remaining(core::MOVEMENT_RESOURCE), 6);
    EXPECT_NEAR(combat.find(heros)->movementSlack, 0.0f, CM);
    EXPECT_NEAR(combat.movementLeft(), 9.0f, CM);
}

/**
 * @brief Le terrain difficile peut naitre en cours de combat.
 * \castest{<b>Du terrain difficile pose en cours de combat (un seisme) compte des la question
 * suivante.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Heros au centre de (2,2), combat commence.<br/>2. Rendre la case (3,2)
 * difficile.<br/>
 * 3. Y aller.<br/>
 * \tattendu Avant : 1,5 m ; apres : 2,25 m ; le pas coute 2 cases entamees, et il reste 0,75 m de
 * la seconde (6,75 m en tout).
 * }
 */
TEST(CombatStateTest, LeTerrainDifficileSeCreeEnCombat) {
    const std::shared_ptr<core::SimulatedSpace> espace = ouverte();
    core::CombatState combat(espace);
    const CombatantId heros =
        enrole(combat, profil("Heros", CombatSide::Allies, 10, PREMIER), tile(2, 2));
    static_cast<void>(
        enrole(combat, profil("Loup", CombatSide::Enemies, 10, DERNIER), tile(10, 6)));
    core::DeterministicRandom des(4);
    ASSERT_TRUE(combat.start(des));
    ASSERT_EQ(combat.activeCombatant(), heros);

    ASSERT_TRUE(combat.routeTo(tile(3, 2)).has_value());
    EXPECT_NEAR(combat.routeTo(tile(3, 2))->length, 1.5f, CM);
    espace->addDifficult(caseAuSol(3, 2));
    ASSERT_TRUE(combat.routeTo(tile(3, 2)).has_value());
    EXPECT_NEAR(combat.routeTo(tile(3, 2))->length, 2.25f, CM);

    ASSERT_EQ(combat.move(tile(3, 2)).result, core::MoveResult::Moved);
    EXPECT_EQ(combat.economy(heros)->remaining(core::MOVEMENT_RESOURCE), 4);
    EXPECT_NEAR(combat.movementLeft(), 6.75f, CM);
}

/**
 * @brief Les zones de la carte declarent le terrain difficile ; seul difficultTerrain: true compte.
 * \castest{<b>Les proprietes de zone de la carte font le terrain difficile de l'espace.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Construire l'espace d'une carte dont une couche porte difficultTerrain, une autre une
 * regle inconnue, une troisieme une coquille (difficultTerrain: 1).<br/>2. Interroger les cases ;
 * marcher vers chacune depuis sa voisine.<br/>
 * \tattendu Les cases de la premiere couche sont difficiles (2,25 m pour en gagner le centre) ;
 * la regle inconnue ne change rien au terrain (1,5 m) ; la coquille ne rend rien difficile
 * (1,5 m) ; le mur de la collision refuse un placement.
 * }
 */
TEST(CombatStateTest, LeTerrainDifficileVientDesZonesDeLaCarte) {
    const core::Level carte = carteAZones();
    const auto espace = std::make_shared<core::SimulatedSpace>(
        core::SimulatedSpace::fromLevel(carte, carte.tileMap()));

    struct Attendu {
        int colonne;
        int ligne;
        bool difficile;
    };
    for (const Attendu attendu :
         {Attendu{1, 1, true}, Attendu{2, 1, true}, Attendu{3, 1, false}, Attendu{0, 3, false}}) {
        const Meters3 centre = tile(attendu.colonne, attendu.ligne);
        EXPECT_EQ(espace->isDifficult(centre.x, centre.y), attendu.difficile)
            << "(" << attendu.colonne << "," << attendu.ligne << ")";
    }

    core::CombatState combat(espace);
    const CombatantId heros = enrole(combat, profil("Heros", CombatSide::Allies, 10), tile(0, 1));
    const CombatantId compagne =
        enrole(combat, profil("Compagne", CombatSide::Allies, 10), tile(4, 1));
    const CombatantId compagnon =
        enrole(combat, profil("Compagnon", CombatSide::Allies, 10), tile(1, 3));
    const std::optional<core::Route> boue = combat.routeFor(heros, tile(1, 1), -1.0f);
    const std::optional<core::Route> cercle = combat.routeFor(compagne, tile(3, 1), -1.0f);
    const std::optional<core::Route> coquille = combat.routeFor(compagnon, tile(0, 3), -1.0f);
    ASSERT_TRUE(boue.has_value());
    ASSERT_TRUE(cercle.has_value());
    ASSERT_TRUE(coquille.has_value());
    EXPECT_NEAR(boue->length, 2.25f, CM);
    EXPECT_NEAR(cercle->length, 1.5f, CM) << "le cercle porte une regle, pas une gene";
    EXPECT_NEAR(coquille->length, 1.5f, CM) << "difficultTerrain: 1 est une coquille";
    EXPECT_EQ(combat.placementAt(profil("Rat", CombatSide::Enemies, 2), tile(5, 0)),
              core::PlacementResult::Obstructed);
}

/**
 * @brief On traverse un allie, jamais un ennemi de taille voisine ; et l'on ne finit sur personne.
 * \castest{<b>Un allie se traverse en terrain difficile, un ennemi de meme taille non, et aucun
 * n'est une place de fin.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Couloir de 5 cases sur 1 : heros en 0, allie en 1, ennemi en 3.<br/>2. Chemins vers
 * les centres des cases 1, 2 et 4.<br/>3. Meme couloir, l'ennemi a la place de l'allie.<br/>
 * \tattendu La case 2 coute 6 m (l'espace de l'allie compte double) ; la case de l'allie et la
 * case 4, derriere l'ennemi, n'ont pas de chemin ; l'ennemi en 1, rien n'est atteignable.
 * }
 */
TEST(CombatStateTest, UnAllieSeTraverseUnEnnemiNon) {
    const auto couloir = [](CombatSide campDuVoisin) {
        auto combat = std::make_unique<core::CombatState>(test_support::openSpace(5, 1));
        static_cast<void>(enrole(*combat, profil("Heros", CombatSide::Allies, 10), tile(0, 0)));
        static_cast<void>(enrole(*combat, profil("Voisin", campDuVoisin, 10), tile(1, 0)));
        static_cast<void>(enrole(*combat, profil("Ennemi", CombatSide::Enemies, 10), tile(3, 0)));
        return combat;
    };
    const auto passage = couloir(CombatSide::Allies);
    const std::optional<core::Route> derriere = passage->routeFor(HEROS, tile(2, 0), 9.0f);
    ASSERT_TRUE(derriere.has_value());
    EXPECT_NEAR(derriere->length, 6.0f, CM);
    EXPECT_FALSE(passage->routeFor(HEROS, tile(1, 0), 9.0f).has_value());
    EXPECT_FALSE(passage->routeFor(HEROS, tile(4, 0), -1.0f).has_value());
    const std::vector<Meters3> finales = fins(passage->destinationsFor(HEROS, 9.0f));
    ASSERT_EQ(finales.size(), 1U);
    EXPECT_TRUE(proche(finales[0], tile(2, 0)));

    const auto bloque = couloir(CombatSide::Enemies);
    EXPECT_TRUE(fins(bloque->destinationsFor(HEROS, 9.0f)).empty());
    EXPECT_FALSE(bloque->routeFor(HEROS, tile(2, 0), -1.0f).has_value());
}

/**
 * @brief Un chemin impossible est refuse.
 * \castest{<b>Un chemin impossible est refuse.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Carte de 5 x 5 cases coupee en deux par un mur plein.<br/>2. Demander un chemin de
 * l'autre cote, un chemin dans le mur, un chemin pour un combattant inconnu, un chemin pour un
 * combattant sans place.<br/>
 * \tattendu Aucun chemin ; les places de fin restent du bon cote du mur ; un combattant inconnu
 * ou sans place n'en a aucune.
 * }
 */
TEST(CombatStateTest, UnCheminImpossibleEstRefuse) {
    core::TileMap collision(5, 5);
    for (int row = 0; row < 5; ++row) {
        collision.setTile(2, row, core::TileType::Wall);
    }
    core::CombatState combat(test_support::spaceOf(collision));
    const CombatantId heros = enrole(combat, profil("Heros", CombatSide::Allies, 10), tile(0, 2));
    const CombatantId absent = enrole(combat, profil("Absent", CombatSide::Allies, 10));

    EXPECT_FALSE(combat.routeFor(heros, tile(4, 2), -1.0f).has_value());
    EXPECT_FALSE(combat.routeFor(heros, tile(2, 2), -1.0f).has_value());
    EXPECT_FALSE(combat.routeFor(CombatantId{9}, tile(1, 2), -1.0f).has_value());
    EXPECT_FALSE(combat.routeFor(absent, tile(1, 2), -1.0f).has_value());

    const std::vector<core::Destination> places = combat.destinationsFor(heros, 30.0f);
    ASSERT_GT(places.size(), 1U);
    for (const core::Destination& place : places) {
        EXPECT_LE(place.point.x, 3.0f - 0.75f + CM) << texte(place.point);
    }
    EXPECT_TRUE(combat.destinationsFor(CombatantId{9}, 30.0f).empty());
    EXPECT_TRUE(combat.destinationsFor(absent, 30.0f).empty());
}

/**
 * @brief Un volant survole l'eau profonde et la falaise, ignore la boue, mais pas les murs.
 * \castest{<b>Un volant survole les obstacles de sol, pas les murs.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Carte de 5 x 3 cases : la case (2,1) en eau profonde, la case (2,2) en falaise, la
 * case (1,1) en boue, la ligne 0 muree.<br/>2. Chemins du meme combattant au sol, puis en vol,
 * depuis le centre de (0,1).<br/>
 * \tattendu Au sol, l'autre rive est inaccessible, l'eau n'est pas une place, et la boue coute
 * 2,25 m ; en vol, l'autre rive est a 4,5 m, la boue coute 1,5 m, on se tient au-dessus de l'eau
 * et du gouffre ; la ligne muree reste hors d'atteinte dans les deux cas.
 * }
 */
TEST(CombatStateTest, UnVolantSurvoleLesObstaclesDeSol) {
    core::TileMap collision(5, 3);
    for (int column = 0; column < 5; ++column) {
        collision.setTile(column, 0, core::TileType::Wall);
    }
    collision.setTile(2, 1, core::TileType::DeepWater);
    collision.setTile(2, 2, core::TileType::Cliff);
    const auto monter = [&](core::Locomotion locomotion) {
        const std::shared_ptr<core::SimulatedSpace> espace = test_support::spaceOf(collision);
        espace->addDifficult(caseAuSol(1, 1));
        auto combat = std::make_unique<core::CombatState>(espace);
        core::CombatantProfile p = profil("Heros", CombatSide::Allies, 10);
        p.locomotion = locomotion;
        static_cast<void>(enrole(*combat, p, tile(0, 1)));
        return combat;
    };

    const auto marche = monter(core::Locomotion::Walk);
    EXPECT_FALSE(marche->routeFor(HEROS, tile(3, 1), 9.0f).has_value());
    EXPECT_FALSE(marche->routeFor(HEROS, tile(3, 2), 9.0f).has_value());
    EXPECT_FALSE(marche->canStandAt(HEROS, tile(2, 1)));
    const std::optional<core::Route> boueAPied = marche->routeFor(HEROS, tile(1, 1), 9.0f);
    ASSERT_TRUE(boueAPied.has_value());
    EXPECT_NEAR(boueAPied->length, 2.25f, CM);

    const auto vol = monter(core::Locomotion::Fly);
    const std::optional<core::Route> rive = vol->routeFor(HEROS, tile(3, 1), 9.0f);
    ASSERT_TRUE(rive.has_value());
    EXPECT_NEAR(rive->length, 4.5f, CM);
    const std::optional<core::Route> boueEnVol = vol->routeFor(HEROS, tile(1, 1), 9.0f);
    ASSERT_TRUE(boueEnVol.has_value());
    EXPECT_NEAR(boueEnVol->length, 1.5f, CM);
    EXPECT_TRUE(vol->canStandAt(HEROS, tile(2, 1)))
        << "un volant se tient en vol stationnaire au-dessus de l'eau";
    EXPECT_TRUE(vol->routeFor(HEROS, tile(2, 2), 9.0f).has_value()) << "et au-dessus du gouffre";

    for (const core::CombatState* combat : {marche.get(), vol.get()}) {
        EXPECT_FALSE(combat->routeFor(HEROS, tile(1, 0), -1.0f).has_value());
        EXPECT_FALSE(combat->canStandAt(HEROS, tile(1, 0)));
    }
}

/**
 * @brief Une grande creature ne passe pas par un passage d'une case.
 * \castest{<b>Une creature G (3 m de diametre) ne passe pas par un passage de 1,5 m.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Salle de 6 x 6 cases coupee par un mur en colonne 3, percee d'une seule case en
 * (3,2).<br/>2. Chemins et places de fin d'un combattant M, puis d'un G, avec 15 m.<br/>
 * \tattendu Le M passe de l'autre cote ; le G n'y parvient pas, et ses places de fin sont toutes
 * des places ou il tient, de son cote du mur.
 * }
 */
TEST(CombatStateTest, UneGrandeCreatureNePassePasParUnPassageEtroit) {
    core::TileMap collision(6, 6);
    for (int row = 0; row < 6; ++row) {
        if (row != 2) {
            collision.setTile(3, row, core::TileType::Wall);
        }
    }
    core::CombatState combat(test_support::spaceOf(collision));
    const CombatantId heros = enrole(combat, profil("Heros", CombatSide::Allies, 10), tile(0, 0));
    core::CombatantProfile grand = profil("Ours", CombatSide::Enemies, 30);
    grand.size = core::CreatureSize::Large;
    const CombatantId ours = enrole(combat, grand, tile(0, 3, core::CreatureSize::Large));

    EXPECT_TRUE(combat.routeFor(heros, tile(5, 2), 15.0f).has_value());
    EXPECT_FALSE(combat.routeFor(ours, tile(4, 1, core::CreatureSize::Large), 15.0f).has_value());
    const std::vector<core::Destination> places = combat.destinationsFor(ours, 15.0f);
    ASSERT_GT(places.size(), 1U);
    for (const core::Destination& place : places) {
        EXPECT_LE(place.point.x + core::creatureRadius(core::CreatureSize::Large), 4.5f + CM)
            << "le G est passe de l'autre cote du mur : " << texte(place.point);
        EXPECT_TRUE(combat.canStandAt(ours, place.point)) << texte(place.point);
    }
}

/**
 * @brief Les obstacles viennent de la grille de collision, et d'elle seule.
 * \castest{<b>Les obstacles de l'espace sont ceux de la couche collision.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un espace lu d'une collision portant un mur, de l'eau peu profonde, de l'eau
 * profonde et une falaise.<br/>2. Demander un placement au centre de chaque case, au sol puis en
 * vol, et hors de la carte.<br/>
 * \tattendu Le mur arrete tout le monde, l'eau profonde et la falaise n'arretent que la marche,
 * l'eau peu profonde n'arrete personne, et le hors-carte est refuse (Obstructed).
 * }
 */
TEST(CombatStateTest, LesObstaclesSontCeuxDeLaCollision) {
    core::TileMap collision(5, 1);
    collision.setTile(0, 0, core::TileType::Wall);
    collision.setTile(1, 0, core::TileType::Water);
    collision.setTile(2, 0, core::TileType::DeepWater);
    collision.setTile(3, 0, core::TileType::Cliff);
    const core::CombatState combat(test_support::spaceOf(collision));
    const core::CombatantProfile marcheur = profil("Marcheur", CombatSide::Allies, 10);
    core::CombatantProfile volant = profil("Volant", CombatSide::Allies, 10);
    volant.locomotion = core::Locomotion::Fly;
    const auto place = [&](const core::CombatantProfile& p, int colonne) {
        return combat.placementAt(p, tile(colonne, 0));
    };

    EXPECT_EQ(place(marcheur, 0), core::PlacementResult::Obstructed);
    EXPECT_EQ(place(volant, 0), core::PlacementResult::Obstructed)
        << "un mur monte jusqu'a la voute : un volant ne le traverse pas";
    EXPECT_EQ(place(marcheur, 1), core::PlacementResult::Placed) << "on patauge";
    EXPECT_EQ(place(marcheur, 2), core::PlacementResult::Obstructed);
    EXPECT_EQ(place(volant, 2), core::PlacementResult::Placed)
        << "l'eau profonde est un obstacle de sol, et un volant la survole";
    EXPECT_EQ(place(marcheur, 3), core::PlacementResult::Obstructed);
    EXPECT_EQ(place(volant, 3), core::PlacementResult::Placed);
    EXPECT_EQ(place(marcheur, 4), core::PlacementResult::Placed);
    EXPECT_EQ(place(marcheur, 5), core::PlacementResult::Obstructed);
    EXPECT_EQ(place(volant, -1), core::PlacementResult::Obstructed);
}

/**
 * @brief Un placement impossible est refuse avec sa raison, jamais corrige d'office ; deux
 *        combattants ne se recouvrent jamais.
 * \castest{<b>Un placement impossible est refuse avec sa raison, et la place d'un combattant
 * sorti se reprend.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Carte de 8 x 8 cases, mur en (1,1) : enroler hors de la carte, dans le mur, un G a
 * cheval sur le bord.<br/>2. Poser le heros en (3,3), puis tenter un rat sur sa place, a 0,75 m de
 * lui, et un G dont l'emprise le couvre ; poser le rat au contact.<br/>3. Pendant son tour, le
 * heros tente d'aller sur le rat ; il sort ; un renfort entre a sa place.<br/>
 * \tattendu Obstructed, Obstructed, Obstructed, sans enroler personne ; puis Occupied trois fois,
 * le rat recoit l'identifiant 2 ; le deplacement sur le rat est refuse ; la place liberee se
 * reprend.
 * }
 */
TEST(CombatStateTest, UnPlacementImpossibleEstRefuseAvecSaRaison) {
    core::TileMap collision(8, 8);
    collision.setTile(1, 1, core::TileType::Wall);
    core::CombatState combat(test_support::spaceOf(collision));
    core::CombatantProfile grand = profil("Ours", CombatSide::Enemies, 30);
    grand.size = core::CreatureSize::Large;

    EXPECT_EQ(combat.enlist(profil("Heros", CombatSide::Allies, 10), tile(8, 0)).placement,
              core::PlacementResult::Obstructed);
    EXPECT_EQ(combat.enlist(profil("Heros", CombatSide::Allies, 10), tile(1, 1)).placement,
              core::PlacementResult::Obstructed);
    EXPECT_EQ(combat.enlist(grand, tile(7, 7, core::CreatureSize::Large)).placement,
              core::PlacementResult::Obstructed);
    EXPECT_TRUE(combat.combatants().empty());

    const CombatantId heros =
        enrole(combat, profil("Heros", CombatSide::Allies, 10, PREMIER), tile(3, 3));
    EXPECT_EQ(heros, CombatantId{1});
    const core::CombatantProfile rat = profil("Rat", CombatSide::Enemies, 2, SECOND);
    EXPECT_EQ(combat.enlist(rat, tile(3, 3)).placement, core::PlacementResult::Occupied);
    EXPECT_EQ(combat.enlist(rat, Meters3{tile(3, 3).x + 0.75f, tile(3, 3).y, 0.0f}).placement,
              core::PlacementResult::Occupied);
    EXPECT_EQ(combat.enlist(grand, tile(2, 2, core::CreatureSize::Large)).placement,
              core::PlacementResult::Occupied)
        << "l'emprise d'un ours posee en (2,2) couvre la case (3,3)";
    const CombatantId leRat = enrole(combat, rat, tile(4, 3));
    EXPECT_EQ(leRat, CombatantId{2});
    static_cast<void>(enrole(combat, profil("Compagnon", CombatSide::Allies, 10), tile(6, 6)));

    EXPECT_EQ(combat.occupantAt(tile(3, 3)), heros);
    EXPECT_EQ(combat.occupantAt(tile(4, 3)), leRat);
    EXPECT_FALSE(combat.occupantAt(tile(5, 5)).has_value());

    core::DeterministicRandom des(3);
    ASSERT_TRUE(combat.start(des));
    ASSERT_EQ(combat.activeCombatant(), heros);
    EXPECT_EQ(combat.move(tile(4, 3)).result, core::MoveResult::Unreachable);
    EXPECT_TRUE(proche(*combat.positionOf(heros), tile(3, 3)));
    ASSERT_EQ(combat.withdraw(heros), core::WithdrawResult::Withdrawn);
    EXPECT_FALSE(combat.occupantAt(tile(3, 3)).has_value());
    const core::EnlistResult renfort =
        combat.join(profil("Renfort", CombatSide::Allies, 10), tile(3, 3), des);
    EXPECT_EQ(renfort.placement, core::PlacementResult::Placed);
    EXPECT_EQ(renfort.combatant, CombatantId{4});
}

/**
 * @brief Une grande creature occupe toute son emprise, et ne se gene pas elle-meme en avancant.
 * \castest{<b>Une creature G couvre ses quatre cases et avance en recouvrant sa propre
 * place.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser une creature G sur les cases (1,1) a (2,2).<br/>2. A son tour, la deplacer
 * d'une case vers la droite.<br/>
 * \tattendu Les centres des quatre cases sont a elle ; le deplacement, qui recouvre la moitie de
 * l'ancienne place, coute 1,5 m et libere la colonne quittee.
 * }
 */
TEST(CombatStateTest, UneGrandeCreatureOccupeToutSonEmprise) {
    EXPECT_EQ(core::footprintSide(core::CreatureSize::Tiny), 1);
    EXPECT_EQ(core::footprintSide(core::CreatureSize::Large), 2);
    EXPECT_EQ(core::footprintSide(core::CreatureSize::Gargantuan), 4);

    core::CombatState combat(test_support::openSpace(6, 6));
    core::CombatantProfile grand = profil("Ours", CombatSide::Allies, 30, PREMIER);
    grand.size = core::CreatureSize::Large;
    const CombatantId ours = enrole(combat, grand, tile(1, 1, core::CreatureSize::Large));
    static_cast<void>(enrole(combat, profil("Rat", CombatSide::Enemies, 2, DERNIER), tile(5, 5)));
    for (const Meters3 centre : {tile(1, 1), tile(2, 1), tile(1, 2), tile(2, 2)}) {
        EXPECT_EQ(combat.occupantAt(centre), ours) << texte(centre);
    }
    EXPECT_FALSE(combat.occupantAt(tile(3, 1)).has_value());

    core::DeterministicRandom des(2);
    ASSERT_TRUE(combat.start(des));
    ASSERT_EQ(combat.activeCombatant(), ours);
    const core::MoveOutcome pas = combat.move(tile(2, 1, core::CreatureSize::Large));
    ASSERT_EQ(pas.result, core::MoveResult::Moved);
    EXPECT_NEAR(pas.path.length, 1.5f, CM);
    EXPECT_FALSE(combat.occupantAt(tile(1, 1)).has_value());
    EXPECT_EQ(combat.occupantAt(tile(3, 2)), ours);
}

/**
 * @brief Meme entree, meme chemin ; et le chemin annonce est celui que l'on suit et paie.
 * \castest{<b>Le chemin est deterministe, et la place de fin annoncee porte le chemin que le
 * deplacement suivra.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Carte accidentee (mur en L, boue), heros au centre de (1,3).<br/>2. Monter cinquante
 * fois le meme combat et demander le chemin vers (7,2) et les places de fin a 18 m.<br/>3. Pour
 * chaque place de fin, redemander son chemin ; puis, le combat commence, aller a l'une
 * d'elles.<br/>
 * \tattendu Cinquante fois les memes points et la meme longueur ; chaque chemin redemande est
 * celui de la place ; le deplacement suit ce chemin.
 * }
 */
TEST(CombatStateTest, MemeEntreeMemeChemin) {
    const std::unique_ptr<core::CombatState> reference = combatAccidente();
    const std::optional<core::Route> chemin = reference->routeFor(HEROS, tile(7, 2), -1.0f);
    ASSERT_TRUE(chemin.has_value());
    const std::vector<core::Destination> places = reference->destinationsFor(HEROS, 18.0f);
    ASSERT_GT(places.size(), 10U);
    for (int essai = 0; essai < 50; ++essai) {
        const std::unique_ptr<core::CombatState> copie = combatAccidente();
        const std::optional<core::Route> autre = copie->routeFor(HEROS, tile(7, 2), -1.0f);
        ASSERT_TRUE(autre.has_value());
        EXPECT_EQ(autre->points, chemin->points);
        EXPECT_EQ(autre->length, chemin->length);
        const std::vector<core::Destination> autres = copie->destinationsFor(HEROS, 18.0f);
        ASSERT_EQ(autres.size(), places.size());
        for (std::size_t i = 0; i < places.size(); ++i) {
            EXPECT_EQ(autres[i].point, places[i].point);
        }
    }

    for (std::size_t i = 1; i < places.size(); ++i) {
        const std::optional<core::Route> redemande =
            reference->routeFor(HEROS, places[i].point, 18.0f);
        ASSERT_TRUE(redemande.has_value()) << texte(places[i].point);
        EXPECT_EQ(redemande->points, places[i].route.points) << texte(places[i].point);
        EXPECT_NEAR(redemande->length, places[i].route.length, 1e-4f);
        EXPECT_LE(places[i].route.length, 18.0f + CM);
    }

    core::DeterministicRandom des(1);
    ASSERT_TRUE(reference->start(des));
    ASSERT_EQ(reference->activeCombatant(), HEROS);
    const std::vector<core::Destination> duTour = reference->destinations();
    ASSERT_GT(duTour.size(), 1U);
    const core::Destination& visee = duTour.back();
    const core::MoveOutcome pas = reference->move(visee.point);
    ASSERT_EQ(pas.result, core::MoveResult::Moved);
    EXPECT_EQ(pas.path.points, visee.route.points);
    EXPECT_NEAR(pas.path.length, visee.route.length, 1e-4f);
}

/**
 * @brief Sur des cartes tirees d'une graine fixe, le chemin annonce et le chemin demande
 *        s'accordent toujours.
 * \castest{<b>Sur douze cartes aleatoires a graine fixe, la place de fin et le chemin demande
 * vers elle s'accordent.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Tirer douze cartes de 12 x 9 cases (graine fixe) : murs, eau profonde, boue, un
 * allie a traverser ; une carte sur trois en vol.<br/>2. Pour chaque place de fin a 21 m, comparer
 * son chemin au chemin demande.<br/>
 * \tattendu Points et longueurs identiques partout, dans le budget.
 * }
 */
TEST(CombatStateTest, SurDesCartesAleatoiresLeCheminAnnonceSAccorde) {
    std::mt19937 tirage(19);
    std::uniform_int_distribution<int> de(0, 99);
    int comparaisons = 0;
    for (int carte = 0; carte < 12; ++carte) {
        core::TileMap collision(12, 9);
        for (int row = 0; row < 9; ++row) {
            for (int column = 0; column < 12; ++column) {
                const int valeur = de(tirage);
                if (valeur < 18) {
                    collision.setTile(column, row, core::TileType::Wall);
                } else if (valeur < 24) {
                    collision.setTile(column, row, core::TileType::DeepWater);
                }
            }
        }
        collision.setTile(1, 1, core::TileType::Grass);
        collision.setTile(2, 1, core::TileType::Grass);
        const std::shared_ptr<core::SimulatedSpace> espace = test_support::spaceOf(collision);
        for (int row = 0; row < 9; ++row) {
            for (int column = 0; column < 12; ++column) {
                if (de(tirage) < 20) {
                    espace->addDifficult(caseAuSol(column, row));
                }
            }
        }
        core::CombatState combat(espace);
        core::CombatantProfile p = profil("Heros", CombatSide::Allies, 10);
        p.locomotion = carte % 3 == 0 ? core::Locomotion::Fly : core::Locomotion::Walk;
        const CombatantId heros = enrole(combat, p, tile(1, 1));
        static_cast<void>(enrole(combat, profil("Allie", CombatSide::Allies, 10), tile(2, 1)));

        const std::vector<core::Destination> places = combat.destinationsFor(heros, 21.0f);
        for (std::size_t i = 1; i < places.size(); ++i) {
            const std::optional<core::Route> demande =
                combat.routeFor(heros, places[i].point, 21.0f);
            ASSERT_TRUE(demande.has_value())
                << "carte " << carte << ", place " << texte(places[i].point);
            EXPECT_EQ(demande->points, places[i].route.points)
                << "carte " << carte << ", place " << texte(places[i].point);
            EXPECT_NEAR(demande->length, places[i].route.length, 1e-4f);
            EXPECT_LE(demande->length, 21.0f + CM);
            ++comparaisons;
        }
    }
    EXPECT_GT(comparaisons, 600) << "les cartes tirees doivent laisser de la place ou aller";
}
