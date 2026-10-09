// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_enemy_ai.cpp
 * @brief Tests unitaires de l'IA tactique (`LOT-23`) : la prise en tenaille du *Guide du Maître*,
 *        le jet requis et l'espérance de dégâts, les profils en données, ce que l'IA sait, le
 *        suicide, le blocage et le rejeu.
 *
 * L'espace est en mètres (`LOT-1017`) : les combattants se posent au centre de leurs cases
 * (`test_support::tile`), l'allonge et la portée se mesurent entre les bords des volumes.
 */

#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/Arena.h"
#include "Core/Combat/Attack.h"
#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/EnemyAi.h"
#include "Core/Combat/Flanking.h"
#include "Core/Levels/Level.h"
#include "Core/Levels/TileMap.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/Ability.h"
#include "Core/Rpg/Bestiary.h"
#include "Test/Support/CombatSpaceSupport.h"

namespace {

using core::CombatantId;
using core::CombatSide;
using core::GridPosition;
using core::Meters3;
using test_support::tile;

/// Une salle ouverte ceinte de murs, et des piliers aux cases données.
core::Level salle(int largeur, int hauteur, const std::vector<GridPosition>& piliers = {}) {
    core::TileMap carte(largeur, hauteur);
    for (int x = 0; x < largeur; ++x) {
        carte.setTile(x, 0, core::TileType::Wall);
        carte.setTile(x, hauteur - 1, core::TileType::Wall);
    }
    for (int y = 0; y < hauteur; ++y) {
        carte.setTile(0, y, core::TileType::Wall);
        carte.setTile(largeur - 1, y, core::TileType::Wall);
    }
    for (const GridPosition p : piliers) {
        carte.setTile(p.column, p.row, core::TileType::Wall);
    }
    return core::Level(core::LevelData{
        .name = "salle", .tileMap = std::move(carte), .entities = {}, .entry = {1, 1}});
}

core::ArenaContestant combattant(const std::string& nom, CombatSide camp, GridPosition case_,
                                 const std::string& comportement = {}, int pv = 20, int ca = 12,
                                 int bonus = 4, const char* degats = "1d6+2") {
    core::CombatantProfile profil{.name = nom,
                                  .side = camp,
                                  .maximumHitPoints = pv,
                                  .currentHitPoints = pv,
                                  .dexterity = 12,
                                  .initiativeModifier = 1,
                                  .movement = 6};
    profil.armorClass = ca;
    core::AttackProfile coup;
    coup.label = nom;
    coup.modifiers = {{.source = "bonus d'attaque", .value = bonus}};
    coup.damage = {
        {.dice = *core::parseDice(degats), .type = core::DamageType::Slashing, .flags = 0}};
    return {.profile = profil,
            .attacks = {coup},
            .position = case_,
            .markId = {},
            .behavior = comportement};
}

core::ArenaContestant archer(const std::string& nom, CombatSide camp, GridPosition case_,
                             const std::string& comportement) {
    core::ArenaContestant a = combattant(nom, camp, case_, comportement, 14, 13, 5, "1d8+3");
    a.attacks[0].kind = core::AttackKind::Ranged;
    a.attacks[0].range = core::AttackRange{.normal = 16, .maximum = 64};
    return a;
}

core::BehaviorCatalog catalogue() {
    return core::loadBehaviors(std::filesystem::path(JADG_RPG_RULES_DIR) / "behaviors.json");
}

/// L'ecart entre les bords de deux combattants, en metres (-1 si l'un n'est pas pose).
float ecart(const core::ArenaSession& session, CombatantId a, CombatantId b) {
    return core::gapBetween(session.combat(), a, b).value_or(-1.0f);
}

/// Joue le combat jusqu'à son issue, chaque tour par l'IA. @return Le nombre de tours joués, ou
/// -1 si la garde est atteinte.
int jouerParLIa(core::ArenaSession& session, const core::BehaviorCatalog& profils,
                int garde = 600) {
    for (int tours = 0; tours < garde; ++tours) {
        if (session.combat().phase() == core::CombatPhase::Ended) {
            return tours;
        }
        if (!core::playTurn(session, profils)) {
            return -1;
        }
    }
    return -1;
}

}  // namespace

/**
 * @brief La tenaille se lit a l'angle au centre de la cible (Guide du Maitre, chapitre 8 ;
 *        LOT-1017).
 * \castest{<b>Deux allies prennent un ennemi en tenaille si leurs centres forment au centre de la
 * cible un angle d'au moins 135 degres, s'ils sont a une case de lui (ecart entre les bords d'au
 * plus 1,5 m), debout, et le voient.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un ennemi au centre de la case (5,5) ; tester, aux centres des cases voisines, des
 * cotes opposes, des angles opposes, un cote et l'angle oppose, une position en L et deux cases du
 * meme cote.<br/>2. Un ennemi de taille G sur (5,5)-(6,6).<br/>3. Dans un combat : l'allie a
 * terre, une autre place de l'attaquant, puis un allie a une case de l'ennemi mais derriere un
 * mur.<br/>
 * \tattendu Opposes et angles opposes (180 degres) : oui ; un cote et l'angle oppose (135
 * degres) : oui ; L et meme cote (90 degres) : non ; la grande creature se prend en tenaille par
 * ses cotes et ses angles opposes, pas en L ; un allie a terre, a angle droit ou qui ne voit pas
 * l'ennemi ne compte pas.
 * }
 */
TEST(FlankingTest, LAngleAuCentreTranche) {
    const Meters3 moyen = tile(5, 5);
    EXPECT_TRUE(core::flanksByAngle(tile(4, 5), tile(6, 5), moyen));
    EXPECT_TRUE(core::flanksByAngle(tile(5, 4), tile(5, 6), moyen));
    EXPECT_TRUE(core::flanksByAngle(tile(4, 4), tile(6, 6), moyen));
    EXPECT_TRUE(core::flanksByAngle(tile(6, 4), tile(4, 6), moyen));
    // Un cote et l'angle oppose : 135 degres. La ligne des centres de la grille ne les prenait pas
    // (elle sortait par un cote voisin) ; l'angle du LOT-1017 les prend.
    EXPECT_TRUE(core::flanksByAngle(tile(4, 5), tile(6, 6), moyen));
    EXPECT_TRUE(core::flanksByAngle(tile(4, 4), tile(6, 5), moyen));
    EXPECT_FALSE(core::flanksByAngle(tile(4, 4), tile(4, 6), moyen));
    EXPECT_FALSE(core::flanksByAngle(tile(4, 5), tile(5, 4), moyen));

    const Meters3 grand = tile(5, 5, core::CreatureSize::Large);
    EXPECT_TRUE(core::flanksByAngle(tile(4, 5), tile(7, 6), grand));
    EXPECT_TRUE(core::flanksByAngle(tile(4, 4), tile(7, 7), grand));
    EXPECT_FALSE(core::flanksByAngle(tile(4, 5), tile(5, 7), grand));

    core::ArenaBout bout{.seed = 1, .lethal = false, .heroicMark = false, .flanking = true};
    bout.contestants = {combattant("A", CombatSide::Allies, {4, 3}),
                        combattant("B", CombatSide::Allies, {6, 3}),
                        combattant("Cible", CombatSide::Enemies, {5, 3})};
    core::ArenaSession session(salle(10, 8));
    session.mount(bout);
    EXPECT_TRUE(core::isFlanked(session.combat(), CombatantId{1}, CombatantId{3}));
    EXPECT_TRUE(core::isFlanked(session.combat(), CombatantId{2}, CombatantId{3}));
    // A au nord de la cible, B a l'est : un angle droit.
    EXPECT_FALSE(core::isFlankedFrom(session.combat(), CombatantId{1}, tile(5, 2), CombatantId{3}));
    EXPECT_FALSE(core::isFlanked(session.combat(), CombatantId{3}, CombatantId{1}));
    session.combat().applyDamage(CombatantId{2}, 100);
    EXPECT_FALSE(core::isFlanked(session.combat(), CombatantId{1}, CombatantId{3}));

    // Un allie a une case de la cible mais derriere un mur ne la voit pas : pas de tenaille. Le
    // centre de (7,3) est a 3 m de celui de (5,3) : 1,5 m entre les bords, a une case, en face de
    // A ; le mur de la colonne 6 est entre eux. (Sur la grille, deux coins de mur en diagonale
    // suffisaient ; dans l'espace, des lignes passent entre eux, et l'allie voit la cible.)
    core::ArenaBout coin{.seed = 1, .lethal = false, .heroicMark = false, .flanking = true};
    coin.contestants = {combattant("A", CombatSide::Allies, {4, 3}),
                        combattant("B", CombatSide::Allies, {7, 3}),
                        combattant("Cible", CombatSide::Enemies, {5, 3})};
    core::ArenaSession murs(salle(10, 8, {{6, 2}, {6, 3}, {6, 4}}));
    murs.mount(coin);
    EXPECT_TRUE(core::flanksByAngle(tile(4, 3), tile(7, 3), tile(5, 3)));
    ASSERT_TRUE(core::adjacentGap(ecart(murs, CombatantId{2}, CombatantId{3})));
    ASSERT_FALSE(core::hasLineOfSight(murs.combat(), CombatantId{2}, CombatantId{3}));
    EXPECT_FALSE(core::isFlanked(murs.combat(), CombatantId{1}, CombatantId{3}));
}

/**
 * @brief La tenaille donne l'avantage au corps a corps, et seulement dans une arene qui la joue.
 * \castest{<b>Dans une arene a prise en tenaille, une attaque au corps a corps contre un ennemi
 * pris en tenaille est jetee avec avantage, et le journal le dit ; ailleurs, non.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Deux allies de part et d'autre d'un ennemi, le premier joue.<br/>2. Il attaque, dans
 * une arene avec tenaille puis sans.<br/>
 * \tattendu Avantage et « prise en tenaille » au journal avec la regle ; posture normale sans.
 * }
 */
TEST(FlankingTest, LaTenailleDonneLAvantageDansLArene) {
    for (const bool tenaille : {true, false}) {
        core::ArenaBout bout{.seed = 4, .lethal = false, .heroicMark = false, .flanking = tenaille};
        core::ArenaContestant a = combattant("A", CombatSide::Allies, {4, 3});
        a.profile.initiativeModifier = 100;
        bout.contestants = {a, combattant("B", CombatSide::Allies, {6, 3}),
                            combattant("Cible", CombatSide::Enemies, {5, 3})};
        core::ArenaSession session(salle(10, 8));
        session.mount(bout);
        ASSERT_TRUE(session.start());
        ASSERT_EQ(session.combat().activeCombatant(), CombatantId{1});
        const core::ArenaAttack attaque = session.attack(CombatantId{3});
        ASSERT_TRUE(attaque.outcome.has_value());
        EXPECT_EQ(attaque.outcome->roll.check.stance,
                  tenaille ? core::RollStance::Advantage : core::RollStance::Normal);
        EXPECT_EQ(attaque.outcome->describe().find("prise en tenaille") != std::string::npos,
                  tenaille);
    }
}

/**
 * @brief Le jet requis et l'esperance de degats suivent le Guide du Maitre.
 * \castest{<b>Le jet requis est la CA moins le bonus d'attaque ; la chance de toucher et
 * l'esperance de degats en decoulent, en entiers.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. L'exemple du Guide : des orcs a +5 contre un guerrier a CA 19.<br/>2. La chance d'un
 * jet requis de 14, normal, avec avantage, avec desavantage ; d'un jet requis de 1 et de 25.<br/>3.
 * L'esperance d'un gobelin (+4, 1d6+2) contre CA 15, et contre CA 15 avec un seuil critique a 19.
 * \tattendu Jet requis 14 ; 140, 231 et 49 quatre-centiemes ; 380 et 20 ; 2340 huit-centiemes
 * (0,5 x 5,5 + 0,05 x 3,5 = 2,925 points), puis 2480 avec le seuil a 19.
 * }
 */
TEST(EnemyAiTest, LeJetRequisEtLEsperanceSuiventLeGuide) {
    EXPECT_EQ(core::requiredRoll(19, 5), 14);
    EXPECT_EQ(core::hitChance(14, core::RollStance::Normal), 140);
    EXPECT_EQ(core::hitChance(14, core::RollStance::Advantage), 231);
    EXPECT_EQ(core::hitChance(14, core::RollStance::Disadvantage), 49);
    EXPECT_EQ(core::hitChance(1, core::RollStance::Normal), 380);
    EXPECT_EQ(core::hitChance(25, core::RollStance::Normal), 20);
    EXPECT_EQ(core::criticalChance(20, core::RollStance::Normal), 20);
    EXPECT_EQ(core::criticalChance(19, core::RollStance::Advantage), 400 - 18 * 18);

    core::AttackProfile gobelin;
    gobelin.modifiers = {{.source = "bonus d'attaque", .value = 4}};
    gobelin.damage = {
        {.dice = *core::parseDice("1d6+2"), .type = core::DamageType::Slashing, .flags = 0}};
    EXPECT_EQ(core::attackBonusOf(gobelin), 4);
    EXPECT_EQ(core::expectedDamage(gobelin, 15, core::RollStance::Normal), 2340);
    gobelin.criticalThreshold = 19;
    // Le seuil a 19 n'ajoute aucune face qui touche (il en fallait 11), mais double le critique.
    EXPECT_EQ(core::expectedDamage(gobelin, 15, core::RollStance::Normal), 11 * 200 + 7 * 40);
}

/**
 * @brief Les profils se chargent de la donnee et s'attribuent par regle.
 * \castest{<b>Les profils de comportement livres se chargent sans erreur, ne tolerent jamais trois
 * menaces, et s'attribuent aux creatures par leurs regles.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Charger behaviors.json.<br/>2. Charger le bestiaire, lire le profil du loup (Tactique
 * de groupe), du sanglier et du singe.<br/>3. Un sanglier synthetique qui tire plus fort qu'il ne
 * mord.<br/>
 * \tattendu Agressif, prudent, soutien, archer et meute ; aucun ne tolere plus de deux menaces ; le
 * loup est « pack », le sanglier « aggressive », le singe, dont le rocher frappe plus fort que le
 * poing, « archer », comme le tireur synthetique.
 * }
 */
TEST(EnemyAiTest, LesProfilsSontDesDonnees) {
    const core::BehaviorCatalog profils = catalogue();
    EXPECT_TRUE(profils.errors.empty()) << profils.errors.front();
    for (const char* id : {"aggressive", "cautious", "support", "archer", "pack"}) {
        const core::BehaviorProfile* profil = profils.find(id);
        ASSERT_NE(profil, nullptr) << id;
        EXPECT_LE(profil->toleratedThreats, 2) << id;
        EXPECT_GT(profil->approachPerTile, 0) << id;
    }
    EXPECT_EQ(profils.defaultBehavior, "aggressive");

    const core::Bestiary bestiaire =
        core::loadBestiary(std::filesystem::path(JADG_RPG_CREATURES_DIR));
    const auto trouver = [&](std::string_view id) {
        return std::ranges::find(bestiaire.creatures, id, &core::Creature::id);
    };
    ASSERT_NE(trouver("wolf"), bestiaire.creatures.end());
    ASSERT_NE(trouver("boar"), bestiaire.creatures.end());
    ASSERT_NE(trouver("ape"), bestiaire.creatures.end());
    EXPECT_EQ(core::behaviorFor(*trouver("wolf"), profils), "pack");
    EXPECT_EQ(core::behaviorFor(*trouver("boar"), profils), "aggressive");
    // Le singe lance un rocher plus fort qu'il ne frappe du poing : il tire.
    EXPECT_EQ(core::behaviorFor(*trouver("ape"), profils), "archer");

    core::Creature tireur = *trouver("boar");
    tireur.traits.clear();
    tireur.actions = {{.name = "Morsure",
                       .text = "",
                       .attackBonus = 3,
                       .reach = 1.5F,
                       .damage = *core::parseDice("1d4"),
                       .damageType = core::DamageType::Piercing},
                      {.name = "Arc",
                       .text = "",
                       .attackBonus = 4,
                       .reach = std::nullopt,
                       .damage = *core::parseDice("1d8+2"),
                       .damageType = core::DamageType::Piercing,
                       .rangeNormal = 24.0F,
                       .rangeLong = 96.0F}};
    EXPECT_EQ(core::behaviorFor(tireur, profils), "archer");
}

/**
 * @brief L'IA lit l'etat ensanglante, jamais les points de vie (EX-CBT-050).
 * \castest{<b>Les points de vie d'un adversaire restent secrets : deux cibles qui ne different que
 * par des points de vie au-dessus de la moitie sont indiscernables ; une cible ensanglantee est
 * preferee.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un gobelin agressif au contact de deux heros identiques, a 20/20 et 11/20.<br/>2.
 * Planifier son tour.<br/>3. Le second passe a 9/20, planifier encore.<br/>
 * \tattendu Meme score et premiere cible (le plus petit identifiant) tant que 11/20 n'est pas
 * ensanglante ; a 9/20, il vise le second.
 * }
 */
TEST(EnemyAiTest, LIaNeLitQueLEtatEnsanglante) {
    const core::BehaviorCatalog profils = catalogue();
    const auto planifier = [&](int pvDuSecond) {
        core::ArenaBout bout{.seed = 8, .lethal = false, .heroicMark = false};
        core::ArenaContestant gobelin =
            combattant("Gobelin", CombatSide::Enemies, {5, 3}, "aggressive");
        gobelin.profile.initiativeModifier = 100;
        core::ArenaContestant second = combattant("Heros2", CombatSide::Allies, {6, 3});
        second.profile.currentHitPoints = pvDuSecond;
        bout.contestants = {combattant("Heros1", CombatSide::Allies, {4, 3}), second, gobelin};
        core::ArenaSession session(salle(10, 8));
        session.mount(bout);
        EXPECT_TRUE(session.start());
        EXPECT_EQ(session.combat().activeCombatant(), CombatantId{3});
        return core::planTurn(session, CombatantId{3}, *profils.find("aggressive"));
    };
    const core::TurnPlan plein = planifier(20);
    const core::TurnPlan entame = planifier(11);
    const core::TurnPlan ensanglante = planifier(9);
    EXPECT_EQ(plein.action, core::TurnAction::Attack);
    EXPECT_EQ(plein.target, CombatantId{1});
    EXPECT_EQ(entame.target, CombatantId{1});
    EXPECT_EQ(entame.score, plein.score);
    EXPECT_EQ(ensanglante.target, CombatantId{2});
    EXPECT_GT(ensanglante.score, plein.score);
}

/**
 * @brief L'IA ne finit pas son tour a portee de trois ennemis quand une place sure existait.
 * \castest{<b>Aucun profil ne finit son tour a portee immediate de trois ennemis quand une place
 * moins exposee etait atteignable.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Trois heros inoffensifs aux centres des cases (6,2), (6,4) et (7,3), le dernier
 * ensanglante ; le centre de (6,3) les touche tous, et les places d'ou le gobelin prend le heros
 * ensanglante en tenaille avec son complice en (8,3) -- les plus rentables -- sont a une case des
 * trois. D'autres places frappent au plus deux heros.<br/>2. Pour chaque profil livre, jouer le
 * tour du gobelin.<br/>
 * \tattendu Le tour se termine sur une place a une case (ecart entre les bords d'au plus 1,5 m)
 * d'au plus deux heros, jamais au centre de (6,3). **Reintroduit a la main**, un classement au
 * seul score y envoie le gobelin.
 * }
 */
TEST(EnemyAiTest, PasDeSuicideQuandUneCaseSureExiste) {
    const core::BehaviorCatalog profils = catalogue();
    for (const core::BehaviorProfile& profil : profils.profiles) {
        core::ArenaBout bout{.seed = 12, .lethal = false, .heroicMark = false, .flanking = true};
        core::ArenaContestant gobelin =
            combattant("Gobelin", CombatSide::Enemies, {2, 3}, profil.id, 30);
        gobelin.profile.initiativeModifier = 100;
        const auto inoffensif = [](const std::string& nom, GridPosition case_) {
            return combattant(nom, CombatSide::Allies, case_, {}, 20, 12, 0, "1");
        };
        core::ArenaContestant est = inoffensif("Est", {7, 3});
        est.profile.currentHitPoints = 6;
        core::ArenaContestant complice = combattant("Complice", CombatSide::Enemies, {8, 3});
        complice.profile.initiativeModifier = -100;
        bout.contestants = {inoffensif("Nord", {6, 2}), inoffensif("Sud", {6, 4}), est, gobelin,
                            complice};
        core::ArenaSession session(salle(12, 8));
        session.mount(bout);
        ASSERT_TRUE(session.start());
        ASSERT_EQ(session.combat().activeCombatant(), CombatantId{4});
        ASSERT_TRUE(core::playTurn(session, profils));

        const Meters3 fin = *session.combat().positionOf(CombatantId{4});
        int aPortee = 0;
        for (const CombatantId heros : {CombatantId{1}, CombatantId{2}, CombatantId{3}}) {
            aPortee += core::adjacentGap(ecart(session, heros, CombatantId{4})) ? 1 : 0;
        }
        EXPECT_LE(aPortee, 2) << profil.id << " finit en " << fin.x << "," << fin.y;
        EXPECT_GT(core::groundDistance(fin, tile(6, 3)), 0.01f) << profil.id;
    }
}

/**
 * @brief Un tireur ne compte pas dans la cle anti-suicide : sa portee couvre l'arene.
 * \castest{<b>Deux archers allies qui couvrent toute la salle n'empechent pas un prudent d'aller
 * frapper le heros au contact.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Salle 12x8 : un heros de contact en (7,3), deux archers allies en (2,2) et (2,5)
 * dont la portee couvre la salle, un gobelin prudent (tolere une menace) en (5,3).<br/>2. Planifier
 * le tour du gobelin.<br/>
 * \tattendu Une attaque contre le heros depuis une place au contact. Avant la correction, toute
 * place etait a portee des deux archers, la place de contact en depassait le seuil, et le gobelin
 * fuyait.
 * }
 */
TEST(EnemyAiTest, UnTireurNeComptePasDansLAntiSuicide) {
    const core::BehaviorCatalog profils = catalogue();
    core::ArenaBout bout{.seed = 4, .lethal = false, .heroicMark = false};
    core::ArenaContestant gobelin = combattant("Gobelin", CombatSide::Enemies, {5, 3}, "cautious");
    gobelin.profile.initiativeModifier = 100;
    bout.contestants = {combattant("Contact", CombatSide::Allies, {7, 3}),
                        archer("Nord", CombatSide::Allies, {2, 2}, {}),
                        archer("Sud", CombatSide::Allies, {2, 5}, {}), gobelin};
    core::ArenaSession session(salle(12, 8));
    session.mount(bout);
    ASSERT_TRUE(session.start());
    ASSERT_EQ(session.combat().activeCombatant(), CombatantId{4});

    const core::TurnPlan plan = core::planTurn(session, CombatantId{4}, *profils.find("cautious"));
    EXPECT_EQ(plan.action, core::TurnAction::Attack) << plan.summary;
    EXPECT_EQ(plan.target, CombatantId{1}) << plan.summary;
    EXPECT_EQ(plan.immediateThreats, 1) << "seul le heros de contact menace la place de fin";
}

/**
 * @brief Sans attaque possible, chaque profil avance : la menace ne le tient pas a distance.
 * \castest{<b>Dans une salle aux dimensions de l'arene, un ennemi de chaque profil qui ne peut pas
 * encore frapper se rapproche a chaque tour, jusqu'a attaquer.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Salle 20x14, heros en (3,6) (+4, 1d8+2), ennemi de contact en (16,6) : treize cases
 * entre les centres, 18 m entre les bords. Pour chacun des profils livres.<br/>2. Le heros passe
 * son tour ; jouer l'ennemi par l'IA, jusqu'a six tours.<br/>
 * \tattendu Tant qu'il n'a pas attaque, l'ecart au heros diminue strictement a chaque tour de
 * l'ennemi ; il attaque au plus tard au quatrieme. Avant la correction, un prudent s'arretait au
 * bord de la zone de menace et reculait quand le heros avancait. (Sur la grille, au troisieme :
 * dans l'espace, la zone que le heros atteint n'est pas un cercle -- les chemins du reseau hors
 * des axes sont un peu plus longs --, et un prudent gagne encore quelques metres hors de sa
 * portee avant de se precipiter.)
 * }
 */
TEST(EnemyAiTest, SansAttaquePossibleChaqueProfilAvance) {
    const core::BehaviorCatalog profils = catalogue();
    for (const core::BehaviorProfile& profil : profils.profiles) {
        core::ArenaBout bout{.seed = 21, .lethal = false, .heroicMark = false};
        core::ArenaContestant heros =
            combattant("Heros", CombatSide::Allies, {3, 6}, {}, 30, 12, 4, "1d8+2");
        heros.profile.initiativeModifier = -100;
        core::ArenaContestant ennemi =
            combattant("Ennemi", CombatSide::Enemies, {16, 6}, profil.id, 30);
        ennemi.profile.initiativeModifier = 100;
        bout.contestants = {heros, ennemi};
        core::ArenaSession session(salle(20, 14));
        session.mount(bout);
        ASSERT_TRUE(session.start());

        const auto aAttaque = [&] {
            return std::ranges::any_of(session.journal(), [](const std::string& l) {
                return l.starts_with("attaque Ennemi");
            });
        };
        float distance = ecart(session, CombatantId{2}, CombatantId{1});
        ASSERT_NEAR(distance, 18.0f, 0.01f);
        int toursEnnemi = 0;
        for (int tour = 0; tour < 12 && !aAttaque(); ++tour) {
            if (session.combat().activeCombatant() == CombatantId{1}) {
                ASSERT_TRUE(session.endTurn());
                continue;
            }
            ASSERT_TRUE(core::playTurn(session, profils)) << profil.id;
            ++toursEnnemi;
            if (aAttaque()) {
                break;
            }
            const float apres = ecart(session, CombatantId{2}, CombatantId{1});
            EXPECT_LT(apres, distance - 0.01f)
                << profil.id << ", tour " << toursEnnemi << " : " << session.journal().back();
            distance = apres;
        }
        std::string journal;
        for (const std::string& ligne : session.journal()) {
            journal += ligne + "\n";
        }
        EXPECT_TRUE(aAttaque()) << profil.id << "\n" << journal;
        EXPECT_LE(toursEnnemi, 4) << profil.id << "\n" << journal;
    }
}

/**
 * @brief Le repli apres l'attaque va a la place sure la plus proche, pas au coin de la salle.
 * \castest{<b>Une archere prudente tire puis recule juste hors de portee du heros, vers la place la
 * plus proche de lui.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Salle 20x8, heros de contact en (16,3) (6 cases : 9 m), archere prudente en (10,3)
 * a 7 cases de portee (10,5 m entre les bords) : le heros atteint en un tour toute place a moins
 * de 12 m de son centre, et elle tire de la ou elle est.<br/>2. Jouer le tour de l'archere.<br/>
 * \tattendu Un tir au journal, puis un repli : hors de portee de toute place que le heros atteint,
 * et a moins d'une case de cette limite (moins de 13,5 m du centre du heros). Avant la correction,
 * a menace egale le premier examine l'emportait, et elle filait au fond de la salle.
 * }
 */
TEST(EnemyAiTest, LeRepliVaALaCaseSureLaPlusProche) {
    const core::BehaviorCatalog profils = catalogue();
    core::ArenaBout bout{.seed = 8, .lethal = false, .heroicMark = false};
    core::ArenaContestant heros = combattant("Heros", CombatSide::Allies, {16, 3}, {}, 30);
    heros.profile.initiativeModifier = -100;
    core::ArenaContestant tireuse = archer("Archere", CombatSide::Enemies, {10, 3}, "cautious");
    tireuse.attacks[0].range = core::AttackRange{.normal = 7, .maximum = 7};
    tireuse.profile.initiativeModifier = 100;
    bout.contestants = {heros, tireuse};
    core::ArenaSession session(salle(20, 8));
    session.mount(bout);
    ASSERT_TRUE(session.start());
    ASSERT_EQ(session.combat().activeCombatant(), CombatantId{2});
    ASSERT_TRUE(core::playTurn(session, profils));

    const std::vector<std::string>& journal = session.journal();
    EXPECT_TRUE(std::ranges::any_of(
        journal, [](const std::string& l) { return l.starts_with("attaque Archere -> Heros"); }));
    EXPECT_TRUE(std::ranges::any_of(
        journal, [](const std::string& l) { return l.find(": recule en") != std::string::npos; }));

    // Hors de portee : aucune place que le heros atteint en un tour ne la touche.
    const core::CombatState& combat = session.combat();
    const Meters3 fin = *combat.positionOf(CombatantId{2});
    const core::Volume elle = *combat.volumeOf(CombatantId{2});
    for (const core::Destination& d :
         combat.destinationsFor(CombatantId{1}, core::metersFromTiles(6.0f))) {
        ASSERT_FALSE(core::adjacentGap(
            core::edgeDistance(core::volumeOf(d.point, core::CreatureSize::Medium), elle)))
            << "le heros l'atteint depuis " << d.point.x << "," << d.point.y;
    }
    // Et pas plus loin qu'il ne faut : a moins d'une case de la limite de 12 m.
    const float auHeros = core::groundDistance(fin, tile(16, 3));
    EXPECT_GT(auHeros, 12.0f) << "en " << fin.x << "," << fin.y;
    EXPECT_LT(auHeros, 13.5f) << "en " << fin.x << "," << fin.y;
}

/**
 * @brief L'archere cherche la place d'ou elle voit, tire, et n'attaque jamais a travers un mur.
 * \castest{<b>Une IA archere cachee de sa cible par un pan de mur se deplace jusqu'a une place qui
 * la voit et tire ; elle n'essaie jamais un tir que la ligne de vue refuse.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Une archere en (3,3), un heros en (8,3) derriere un pan de mur en (6,2)-(6,4) ; elle
 * ne le voit pas.<br/>2. Jouer son tour par l'IA.<br/>
 * \tattendu Une attaque jetee au journal, sans refus d'abri total, depuis une place qui voit le
 * heros.
 * }
 */
TEST(EnemyAiTest, LArchereChercheLaVue) {
    const core::BehaviorCatalog profils = catalogue();
    core::ArenaBout bout{.seed = 5, .lethal = false, .heroicMark = false};
    core::ArenaContestant tireuse = archer("Archere", CombatSide::Enemies, {3, 3}, "archer");
    tireuse.profile.initiativeModifier = 100;
    bout.contestants = {combattant("Heros", CombatSide::Allies, {8, 3}, {}, 30), tireuse};
    core::ArenaSession session(salle(12, 8, {{6, 2}, {6, 3}, {6, 4}}));
    session.mount(bout);
    ASSERT_TRUE(session.start());
    ASSERT_EQ(session.combat().activeCombatant(), CombatantId{2});
    ASSERT_FALSE(core::hasLineOfSight(session.combat(), CombatantId{2}, CombatantId{1}));
    const core::TurnPlan plan = core::planTurn(session, CombatantId{2}, *profils.find("archer"));
    EXPECT_EQ(plan.action, core::TurnAction::Attack) << plan.summary;
    ASSERT_TRUE(plan.moveTo.has_value()) << plan.summary;
    EXPECT_TRUE(
        core::hasLineOfSightFrom(session.combat(), CombatantId{2}, *plan.moveTo, CombatantId{1}));

    ASSERT_TRUE(core::playTurn(session, profils));
    const std::vector<std::string>& journal = session.journal();
    EXPECT_TRUE(std::ranges::any_of(
        journal, [](const std::string& l) { return l.starts_with("attaque Archere -> Heros"); }));
}

/**
 * @brief Loin de tout, l'IA se precipite ; la prudente refuse une opportunite trop difficile.
 * \castest{<b>Une IA qui ne peut attaquer se precipite vers l'ennemi le plus proche ; une IA
 * prudente laisse passer une attaque d'opportunite dont le jet requis depasse son seuil, une
 * agressive la prend.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un gobelin agressif a seize cases d'un heros ; jouer son tour.<br/>2. Un ogre au
 * contact d'un heros a CA 20 (+4 : jet requis 16) ; le heros s'eloigne au centre de (2,5), hors de
 * l'allonge, l'ogre prudent puis agressif.<br/>
 * \tattendu « precipitation » au journal et le gobelin a plus de six cases (9 m) de son depart ;
 * aucune opportunite prise par le prudent, une par l'agressif.
 * }
 */
TEST(EnemyAiTest, SePrecipiterEtChoisirSesOpportunites) {
    const core::BehaviorCatalog profils = catalogue();
    {
        core::ArenaBout bout{.seed = 3, .lethal = false, .heroicMark = false};
        core::ArenaContestant gobelin =
            combattant("Gobelin", CombatSide::Enemies, {1, 1}, "aggressive");
        gobelin.profile.initiativeModifier = 100;
        bout.contestants = {combattant("Heros", CombatSide::Allies, {17, 6}), gobelin};
        core::ArenaSession session(salle(19, 8));
        session.mount(bout);
        ASSERT_TRUE(session.start());
        ASSERT_TRUE(core::playTurn(session, profils));
        EXPECT_TRUE(std::ranges::any_of(session.journal(), [](const std::string& l) {
            return l.starts_with("precipitation Gobelin");
        }));
        EXPECT_GT(core::groundDistance(*session.combat().positionOf(CombatantId{2}), tile(1, 1)),
                  core::metersFromTiles(6.0f));
    }
    for (const char* profil : {"cautious", "aggressive"}) {
        core::ArenaBout bout{.seed = 9, .lethal = false, .heroicMark = false};
        core::ArenaContestant heros = combattant("Heros", CombatSide::Allies, {2, 3}, {}, 50, 20);
        heros.profile.initiativeModifier = 100;
        bout.contestants = {heros, combattant("Ogre", CombatSide::Enemies, {3, 3}, profil, 50)};
        core::ArenaSession session(salle(10, 8));
        session.setOpportunityPolicy(core::aiOpportunityPolicy(profils));
        session.mount(bout);
        ASSERT_TRUE(session.start());
        ASSERT_EQ(session.combat().activeCombatant(), CombatantId{1});
        ASSERT_EQ(session.move(tile(2, 5)).result, core::MoveResult::Moved);
        ASSERT_FALSE(core::adjacentGap(ecart(session, CombatantId{1}, CombatantId{2})));
        const auto prises = std::ranges::count_if(session.journal(), [](const std::string& l) {
            return l.starts_with("opportunite : ");
        });
        EXPECT_EQ(prises, std::string(profil) == "aggressive" ? 1 : 0) << profil;
    }
}

/**
 * @brief Un combat IA contre IA se termine toujours, et se rejoue a l'identique.
 * \castest{<b>Sur des configurations generees -- salles, piliers, compositions, profils, tireurs,
 * tenaille ou non --, un combat joue par l'IA des deux cotes atteint son issue ; a graine fixee,
 * deux parties donnent le meme journal.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Pour trente graines, generer une salle de 10 a 16 cases sur 8 a 10 avec des
 * piliers, deux a quatre combattants par camp poses aux centres de leurs cases, chacun avec un
 * profil livre, un tiers de tireurs, la tenaille une fois sur deux.<br/>2. Jouer par l'IA jusqu'a
 * l'issue, avec une garde de 600 tours.<br/>3. Une graine sur trois, rejouer par `replay`.<br/>
 * \tattendu Chaque combat a une issue avant la garde ; le rejeu donne le meme journal et le meme
 * nombre de tours.
 * }
 */
TEST(EnemyAiTest, UnCombatIaContreIaSeTermineToujoursEtSeRejoue) {
    const core::BehaviorCatalog profils = catalogue();
    ASSERT_TRUE(profils.errors.empty());
    int longest = 0;
    for (std::uint64_t graine = 1; graine <= 30; ++graine) {
        core::DeterministicRandom des(graine * 7919);
        const int largeur = des.nextInt(10, 16);
        const int hauteur = des.nextInt(8, 10);
        std::vector<GridPosition> piliers;
        const int nombre = des.nextInt(0, (largeur * hauteur) / 12);
        for (int i = 0; i < nombre; ++i) {
            // Les colonnes 1-2 et les deux dernieres restent libres : les camps y entrent.
            piliers.push_back({des.nextInt(3, largeur - 4), des.nextInt(1, hauteur - 2)});
        }
        core::ArenaBout bout{.seed = graine,
                             .lethal = false,
                             .heroicMark = true,
                             .flanking = des.nextInt(0, 1) == 1};
        for (const CombatSide camp : {CombatSide::Allies, CombatSide::Enemies}) {
            const int effectif = des.nextInt(2, 4);
            for (int i = 0; i < effectif; ++i) {
                const std::string& profil =
                    profils
                        .profiles[static_cast<std::size_t>(
                            des.nextInt(0, static_cast<int>(profils.profiles.size()) - 1))]
                        .id;
                const GridPosition case_{
                    camp == CombatSide::Allies ? 1 + (i % 2) : largeur - 2 - (i % 2), 1 + i};
                const std::string nom =
                    std::string(camp == CombatSide::Allies ? "A" : "E") + std::to_string(i);
                core::ArenaContestant c =
                    des.nextInt(0, 2) == 0
                        ? archer(nom, camp, case_, profil)
                        : combattant(nom, camp, case_, profil, des.nextInt(8, 24),
                                     des.nextInt(11, 17), des.nextInt(2, 6),
                                     des.nextInt(0, 1) == 0 ? "1d6+2" : "2d4+1");
                c.profile.initiativeModifier = des.nextInt(-1, 3);
                bout.contestants.push_back(std::move(c));
            }
        }
        core::ArenaSession session(salle(largeur, hauteur, piliers));
        session.setOpportunityPolicy(core::aiOpportunityPolicy(profils));
        const core::ArenaMount montage = session.mount(bout);
        ASSERT_TRUE(montage.refusals.empty()) << "graine " << graine;
        ASSERT_TRUE(session.start());
        const int tours = jouerParLIa(session, profils);
        ASSERT_GE(tours, 0) << "graine " << graine << " : pas d'issue en 600 tours";
        ASSERT_TRUE(session.outcome().has_value());
        longest = std::max(longest, tours);

        // Le rejeu d'une graine sur trois : chaque partie coute, et une divergence se voit vite.
        if (graine % 3 != 0) {
            continue;
        }
        const std::vector<std::string> journal = session.journal();
        session.replay();
        ASSERT_EQ(jouerParLIa(session, profils), tours) << "graine " << graine;
        EXPECT_EQ(session.journal(), journal) << "graine " << graine;
    }
    EXPECT_GT(longest, 0);
}
