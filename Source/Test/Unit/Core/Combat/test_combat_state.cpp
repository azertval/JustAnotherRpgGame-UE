// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_combat_state.cpp
 * @brief Tests de la machine à états du combat : initiative, tour, crochets, entrées et sorties,
 *        les trois fins (`LOT-20`, `EX-CBT-010`, `EX-CBT-011`, `EX-CBT-012`, `EX-VIS-004`).
 *
 * **Aucune fenêtre** : un combat se déroule ici du premier round à sa fin, au rythme des appels du
 * test. Les combattants sont écrits dans le test, jamais lus d'un catalogue livré.
 */

#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/ActionEconomy.h"
#include "Core/Combat/BattleGrid.h"
#include "Core/Combat/CombatState.h"
#include "Core/Combat/CombatTransition.h"
#include "Core/Combat/Encounter.h"
#include "Core/Gameplay/WorldFlags.h"
#include "Core/Levels/GridPosition.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Check.h"
#include "Core/Rpg/Dice.h"

namespace {

using core::CombatantId;
using core::CombatHook;
using core::CombatSide;

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

[[nodiscard]] core::BattleGrid ouverte() {
    return core::BattleGrid(core::TileMap(12, 8));
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
                                 std::optional<core::GridPosition> ancre = std::nullopt) {
    const core::EnlistResult enrolement = combat.enlist(p, ancre);
    EXPECT_TRUE(enrolement.combatant.has_value()) << p.name;
    return enrolement.combatant.value_or(CombatantId{});
}

[[nodiscard]] int chebyshev(core::GridPosition a, core::GridPosition b) {
    return std::max(std::abs(a.column - b.column), std::abs(a.row - b.row));
}

/// Ce qu'un combattant de l'escarmouche sait frapper : le reste du combat est au `LOT-21`.
struct Arme {
    int bonus = 0;
    core::Dice degats;
    int classeArmure = 10;
};

/**
 * Une escarmouche à cinq, jouée sans fenêtre par une tactique élémentaire : marcher vers l'ennemi
 * debout le plus proche, le frapper s'il est au contact, terminer son tour.
 */
[[nodiscard]] std::vector<std::string> escarmouche(std::uint64_t graine,
                                                   std::optional<core::CombatOutcome>& issue,
                                                   int& rounds) {
    core::TileMap carte(10, 8);
    carte.setTile(4, 3, core::TileType::Wall);
    carte.setTile(4, 4, core::TileType::Wall);
    core::CombatState combat{core::BattleGrid(carte)};
    std::vector<std::string> journal;
    ecouter(combat, journal);

    std::map<CombatantId, Arme> armes;
    const auto ajouter = [&](const std::string& nom, CombatSide camp, int pv, int dexterite,
                             core::GridPosition case_, Arme arme) {
        core::CombatantProfile p = profil(nom, camp, pv);
        p.dexterity = dexterite;
        p.initiativeModifier = (dexterite - 10) / 2;
        const CombatantId id = enrole(combat, p, case_);
        armes[id] = arme;
    };
    ajouter("Guerriere", CombatSide::Allies, 20, 12, {1, 3},
            {.bonus = 5, .degats = *core::parseDice("1d8+3"), .classeArmure = 16});
    ajouter("Pretre", CombatSide::Allies, 14, 10, {1, 5},
            {.bonus = 4, .degats = *core::parseDice("1d6+2"), .classeArmure = 15});
    for (int rang = 0; rang < 3; ++rang) {
        ajouter("Gobelin", CombatSide::Enemies, 7, 14, {8, 2 + 2 * rang},
                {.bonus = 4, .degats = *core::parseDice("1d6+2"), .classeArmure = 15});
    }

    core::DeterministicRandom des(graine);
    EXPECT_TRUE(combat.start(des));
    for (int garde = 0; garde < 500 && combat.phase() != core::CombatPhase::Ended; ++garde) {
        const CombatantId actif = *combat.activeCombatant();
        const CombatSide camp = combat.find(actif)->profile.side;
        const core::GridPosition depart = *combat.grid().positionOf(actif);

        std::optional<CombatantId> cible;
        int distance = 0;
        for (const CombatantId autre : combat.combatants()) {
            const core::Combatant* c = combat.find(autre);
            if (c->profile.side == camp || c->status != core::CombatantStatus::Standing) {
                continue;
            }
            const int d = chebyshev(depart, *combat.grid().positionOf(autre));
            if (!cible.has_value() || d < distance) {
                cible = autre;
                distance = d;
            }
        }
        const core::GridPosition visee = *combat.grid().positionOf(*cible);

        if (distance > 1) {
            const std::optional<core::ReachableArea> aire = combat.reachableArea();
            std::optional<core::GridPosition> meilleure;
            for (const core::GridPosition destination : aire->destinations()) {
                if (chebyshev(destination, visee) < distance) {
                    distance = chebyshev(destination, visee);
                    meilleure = destination;
                }
            }
            if (meilleure.has_value()) {
                EXPECT_EQ(combat.move(*meilleure).result, core::MoveResult::Moved);
                journal.push_back("pas " + idTexte(actif) + " " +
                                  std::to_string(meilleure->column) + "," +
                                  std::to_string(meilleure->row));
            }
        }
        if (distance == 1) {
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
 * \tattendu Sortie refusee (NotEscapable) ; puis l'heroine quitte grille et ordre, son tour se
 * termine et le suivant commence ; la sortie d'un ennemi ne termine rien ; la chute du compagnon
 * donne Fuite.
 * }
 */
TEST(CombatStateTest, UneFuiteQuandLesAlliesQuittentLaZone) {
    core::CombatState combat(ouverte());
    std::vector<std::string> journal;
    ecouter(combat, journal);
    const CombatantId heroine = enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER),
                                       core::GridPosition{1, 1});
    const CombatantId gobelin =
        enrole(combat, profil("Gobelin", CombatSide::Enemies, 7, SECOND), core::GridPosition{5, 1});
    const CombatantId compagnon =
        enrole(combat, profil("Compagnon", CombatSide::Allies, 10, 0), core::GridPosition{1, 2});
    static_cast<void>(
        enrole(combat, profil("Chef", CombatSide::Enemies, 12, DERNIER), core::GridPosition{6, 1}));
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
    EXPECT_FALSE(combat.grid().positionOf(heroine).has_value());
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
 * \tetapes 1. Deux allies contre trois gobelins, sur une carte a pilier.<br/>2. Chaque combattant
 * marche vers l'ennemi le plus proche, frappe au contact, termine son tour.<br/>3. Rejouer a la
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
 * tour de l'heroine, faire entrer un loup d'initiative plus basse que tout, puis un combattant sur
 * une case prise.<br/>
 * \tattendu Round 1 : heroine, renforts, entree, chef ; round 2 : heroine, gobelin, renforts, loup,
 * chef ; l'entree sur une case prise est refusee sans consommer d'identifiant.
 * }
 */
TEST(CombatStateTest, UnRenfortEntreEnCoursDeCombat) {
    core::CombatState combat(ouverte());
    std::vector<std::string> journal;
    ecouter(combat, journal);
    static_cast<void>(enrole(combat, profil("Heroine", CombatSide::Allies, 10, PREMIER),
                             core::GridPosition{1, 1}));
    static_cast<void>(enrole(combat, profil("Chef", CombatSide::Enemies, 10, DERNIER * 2),
                             core::GridPosition{8, 1}));
    ASSERT_TRUE(combat.addInitiativeMarker({.count = 0, .name = "renforts"}));
    combat.subscribe(
        CombatHook::InitiativeCount, [](core::CombatState& etat, const core::CombatEvent& e) {
            if (e.marker == "renforts" && e.round == 1) {
                static_cast<void>(
                    etat.joinAtInitiative(profil("Gobelin", CombatSide::Enemies, 7), {8, 2}, 0));
            }
        });
    core::DeterministicRandom des(21);
    ASSERT_TRUE(combat.start(des));
    ASSERT_TRUE(combat.endTurn());  // heroine
    ASSERT_TRUE(combat.endTurn());  // chef
    ASSERT_EQ(combat.round(), 2);

    const core::EnlistResult loup =
        combat.join(profil("Loup", CombatSide::Enemies, 9, DERNIER), {8, 3}, des);
    ASSERT_EQ(loup.combatant, CombatantId{4});
    const core::EnlistResult refuse =
        combat.join(profil("Rat", CombatSide::Enemies, 2), {8, 3}, des);
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
 * \castest{<b>Le deplacement se paie sur le budget restant ; on traverse un allie, un ennemi tres
 * petit, jamais un ennemi de taille voisine.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Couloir 7x1 : heroine (6 cases) en 0, compagnon en 1, rat tres petit ennemi
 * en 3.<br/>
 * 2. Aller en 2, puis en 4.<br/>3. Meme couloir avec un gobelin de taille M a la place du rat.<br/>
 * \tattendu Destinations 2 et 4 ; aller en 2 coute 3 (la case du compagnon compte double) ; de 2,
 * aller en 4 coute les 3 restantes ; avec le gobelin, seule la case 2 est une destination.
 * }
 */
TEST(CombatStateTest, LeDeplacementPaieLeCheminEtLesCampsDisentQuiSeTraverse) {
    const auto couloir = [](core::CreatureSize tailleEnnemi) {
        auto combat = std::make_unique<core::CombatState>(core::BattleGrid(core::TileMap(7, 1)));
        static_cast<void>(enrole(*combat, profil("Heroine", CombatSide::Allies, 10, PREMIER),
                                 core::GridPosition{0, 0}));
        static_cast<void>(
            enrole(*combat, profil("Compagnon", CombatSide::Allies, 10), core::GridPosition{1, 0}));
        core::CombatantProfile ennemi = profil("Ennemi", CombatSide::Enemies, 3, DERNIER);
        ennemi.size = tailleEnnemi;
        static_cast<void>(enrole(*combat, ennemi, core::GridPosition{3, 0}));
        return combat;
    };

    {
        const auto combat = couloir(core::CreatureSize::Tiny);
        EXPECT_EQ(combat->move({2, 0}).result, core::MoveResult::NoActiveTurn);
        core::DeterministicRandom des(6);
        ASSERT_TRUE(combat->start(des));
        EXPECT_EQ(combat->reachableArea()->destinations(),
                  (std::vector<core::GridPosition>{{2, 0}, {4, 0}}));
        EXPECT_EQ(combat->move({5, 0}).result, core::MoveResult::Unreachable);

        const core::MoveOutcome premier = combat->move({2, 0});
        ASSERT_EQ(premier.result, core::MoveResult::Moved);
        EXPECT_EQ(premier.path.cost, 3);
        EXPECT_EQ(premier.path.steps, (std::vector<core::GridPosition>{{1, 0}, {2, 0}}));
        EXPECT_EQ(combat->economy(CombatantId{1})->remaining(core::MOVEMENT_RESOURCE), 3);

        const core::MoveOutcome second = combat->move({4, 0});
        ASSERT_EQ(second.result, core::MoveResult::Moved);
        EXPECT_EQ(second.path.cost, 3);
        EXPECT_EQ(combat->grid().positionOf(CombatantId{1}), (core::GridPosition{4, 0}));
        EXPECT_EQ(combat->economy(CombatantId{1})->remaining(core::MOVEMENT_RESOURCE), 0);
        EXPECT_TRUE(combat->reachableArea()->destinations().empty());
    }
    {
        const auto combat = couloir(core::CreatureSize::Medium);
        core::DeterministicRandom des(6);
        ASSERT_TRUE(combat->start(des));
        EXPECT_EQ(combat->reachableArea()->destinations(),
                  (std::vector<core::GridPosition>{{2, 0}}));
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
 * \tattendu Allie 1, ennemis 2 et 3 ; trois refus : mur (Obstructed), inconnue (sans raison de
 * grille), case prise (Occupied) ; la chauve-souris vole ; la fiche donne +3 et 6 cases ; la fuite
 * est interdite comme dans la donnee ; la victoire pose le drapeau de la rencontre.
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
    core::CombatState combat{core::BattleGrid(carte)};
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
    EXPECT_EQ(combat.grid().positionOf(CombatantId{2}), (core::GridPosition{5, 3}));
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
