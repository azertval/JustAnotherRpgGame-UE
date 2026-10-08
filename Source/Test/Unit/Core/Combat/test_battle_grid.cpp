// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_battle_grid.cpp
 * @brief Tests de la grille de combat : obstacles, zones, occupation et objets (`LOT-19`,
 *        `EX-CBT-020`).
 *
 * Toutes les grilles sont écrites ici, case par case : un test qui lirait une carte livrée
 * vérifierait deux choses à la fois, et échouerait pour la mauvaise raison le jour où la carte
 * bouge.
 */

#include <string>
#include <utility>
#include <variant>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/BattleGrid.h"
#include "Core/Levels/Level.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"

namespace {

constexpr core::CombatantId HEROS{1};
constexpr core::CombatantId RAT{2};
constexpr core::CombatantId OURS{3};

/// Une carte 6 × 4 dont la couche de décor, marquée difficile, couvre deux cases, et dont une
/// seconde couche porte une règle de zone que la grille ne connaît pas.
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
    // Une coquille : `1` n'est pas `true`, et une faute de saisie ne doit pas devenir une règle.
    couches.push_back({.name = "coquille",
                       .kind = core::LayerKind::Decor,
                       .tiles = std::move(mal),
                       .properties = {{"difficultTerrain", std::int64_t{1}}}});
    return core::Level(core::LevelData{
        .name = "zones", .tileMap = std::move(collision), .layers = std::move(couches)});
}

}  // namespace

/**
 * @brief Les obstacles viennent de la grille de collision, et d'elle seule.
 * \castest{<b>Les obstacles de la grille de combat sont ceux de la couche collision.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Construire une grille sur une collision portant un mur, de l'eau peu profonde et de
 * l'eau profonde.<br/>2. Interroger chaque case, au sol puis en vol.<br/>
 * \tattendu Le mur arrete tout le monde, l'eau profonde n'arrete que la marche, l'eau peu profonde
 * n'arrete personne, et le hors-carte compte pour plein.
 * }
 */
TEST(BattleGridTest, LesObstaclesSontCeuxDeLaCollision) {
    core::TileMap collision(4, 1);
    collision.setTile(0, 0, core::TileType::Wall);
    collision.setTile(1, 0, core::TileType::Water);
    collision.setTile(2, 0, core::TileType::DeepWater);
    const core::BattleGrid grille(collision);

    EXPECT_TRUE(grille.isObstructed({0, 0}));
    EXPECT_TRUE(grille.isObstructed({0, 0}, core::Locomotion::Fly))
        << "un mur monte jusqu'a la voute : un volant ne le traverse pas";
    EXPECT_FALSE(grille.isObstructed({1, 0})) << "on patauge dans l'eau peu profonde";
    EXPECT_TRUE(grille.isObstructed({2, 0}));
    EXPECT_FALSE(grille.isObstructed({2, 0}, core::Locomotion::Fly))
        << "l'eau profonde est un obstacle de sol, et un volant la survole";
    EXPECT_FALSE(grille.isObstructed({3, 0}));
    EXPECT_TRUE(grille.isObstructed({4, 0}));
    EXPECT_TRUE(grille.isObstructed({-1, 0}));
}

/**
 * @brief Deux combattants ne partagent jamais une case, quelle que soit leur taille.
 * \castest{<b>Deux creatures ne partagent jamais une case.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Placer un combattant.<br/>2. Tenter d'en placer un second sur sa case, puis d'y
 * deplacer un troisieme.<br/>3. Tenter de poser une creature 2x2 dont l'emprise mord sur la
 * case.<br/>
 * \tattendu Chaque tentative est refusee comme Occupied, et la case reste tenue par le premier.
 * }
 */
TEST(BattleGridTest, DeuxCreaturesNePartagentJamaisUneCase) {
    const core::TileMap collision(8, 8);
    core::BattleGrid grille(collision);

    ASSERT_EQ(grille.place(HEROS, {3, 3}), core::PlacementResult::Placed);
    EXPECT_EQ(grille.place(RAT, {3, 3}), core::PlacementResult::Occupied);
    ASSERT_EQ(grille.place(RAT, {5, 5}), core::PlacementResult::Placed);
    EXPECT_EQ(grille.moveTo(RAT, {3, 3}), core::PlacementResult::Occupied);
    EXPECT_EQ(grille.place(OURS, {2, 2}, 2), core::PlacementResult::Occupied)
        << "l'emprise 2x2 d'un ours ancree en (2,2) couvre la case (3,3)";

    EXPECT_EQ(grille.occupantAt({3, 3}), HEROS);
    EXPECT_EQ(grille.positionOf(RAT), (core::GridPosition{5, 5}));
    EXPECT_FALSE(grille.positionOf(OURS).has_value());
}

/**
 * @brief Une grande creature occupe toute son emprise, et ne se gene pas elle-meme en avancant.
 * \castest{<b>Une creature 2x2 occupe quatre cases et avance sur sa propre emprise.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Placer une creature de taille G (2x2).<br/>2. La deplacer d'une case vers la
 * droite.<br/>
 * \tattendu Les quatre cases sont tenues ; le deplacement, qui recouvre la moitie de l'ancienne
 * emprise, est accepte et libere la colonne quittee.
 * }
 */
TEST(BattleGridTest, UneGrandeCreatureOccupeToutSonEmprise) {
    const core::TileMap collision(6, 6);
    core::BattleGrid grille(collision);

    EXPECT_EQ(core::footprintSide(core::CreatureSize::Tiny), 1);
    EXPECT_EQ(core::footprintSide(core::CreatureSize::Large), 2);
    EXPECT_EQ(core::footprintSide(core::CreatureSize::Gargantuan), 4);

    ASSERT_EQ(grille.place(OURS, {1, 1}, core::footprintSide(core::CreatureSize::Large)),
              core::PlacementResult::Placed);
    for (const core::GridPosition case_ : {core::GridPosition{1, 1}, core::GridPosition{2, 1},
                                           core::GridPosition{1, 2}, core::GridPosition{2, 2}}) {
        EXPECT_EQ(grille.occupantAt(case_), OURS);
    }
    EXPECT_EQ(grille.sideOf(OURS), 2);

    ASSERT_EQ(grille.moveTo(OURS, {2, 1}), core::PlacementResult::Placed);
    EXPECT_FALSE(grille.occupantAt({1, 1}).has_value());
    EXPECT_EQ(grille.occupantAt({3, 2}), OURS);
}

/**
 * @brief Un placement impossible est refuse avec sa raison, jamais corrige d'office.
 * \castest{<b>Un placement impossible est refuse avec sa raison.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Placer hors de la carte, dans un mur, a cheval sur le bord.<br/>2. Placer deux fois
 * le meme combattant, deplacer un combattant absent.<br/>3. Retirer un combattant et reprendre sa
 * case.<br/>
 * \tattendu OutOfBounds, Obstructed, OutOfBounds, InvalidCombatant, InvalidCombatant ; la case
 * liberee se reprend.
 * }
 */
TEST(BattleGridTest, UnPlacementImpossibleEstRefuseAvecSaRaison) {
    core::TileMap collision(4, 4);
    collision.setTile(1, 1, core::TileType::Wall);
    core::BattleGrid grille(collision);

    EXPECT_EQ(grille.place(HEROS, {4, 0}), core::PlacementResult::OutOfBounds);
    EXPECT_EQ(grille.place(HEROS, {1, 1}), core::PlacementResult::Obstructed);
    EXPECT_EQ(grille.place(OURS, {3, 3}, 2), core::PlacementResult::OutOfBounds);
    ASSERT_EQ(grille.place(HEROS, {0, 0}), core::PlacementResult::Placed);
    EXPECT_EQ(grille.place(HEROS, {2, 2}), core::PlacementResult::InvalidCombatant);
    EXPECT_EQ(grille.moveTo(RAT, {2, 2}), core::PlacementResult::InvalidCombatant);
    EXPECT_EQ(grille.place(RAT, {2, 2}, 0), core::PlacementResult::InvalidCombatant);

    EXPECT_TRUE(grille.remove(HEROS));
    EXPECT_FALSE(grille.remove(HEROS));
    EXPECT_EQ(grille.place(RAT, {0, 0}), core::PlacementResult::Placed);
    EXPECT_EQ(grille.combatants(), (std::vector<core::CombatantId>{RAT}));
}

/**
 * @brief Les couches a proprietes declarent des zones ; seul difficultTerrain est interprete.
 * \castest{<b>Les proprietes de zone de la carte sont relevees par la grille.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Construire la grille d'une carte dont une couche porte difficultTerrain, une autre
 * une regle inconnue, une troisieme une coquille (difficultTerrain: 1).<br/>2. Interroger les
 * cases.<br/>
 * \tattendu Les cases de la premiere couche sont difficiles ; la regle inconnue se lit par zonesAt
 * sans rien changer au terrain ; la coquille ne rend rien difficile.
 * }
 */
TEST(BattleGridTest, LesProprietesDeZoneSontRelevees) {
    const core::Level carte = carteAZones();
    const core::BattleGrid grille(carte);

    EXPECT_TRUE(grille.isObstructed({5, 0}));
    EXPECT_TRUE(grille.isDifficult({1, 1}));
    EXPECT_TRUE(grille.isDifficult({2, 1}));
    EXPECT_FALSE(grille.isDifficult({3, 1})) << "le cercle porte une regle, pas une gene";
    EXPECT_FALSE(grille.isDifficult({0, 3})) << "difficultTerrain: 1 est une coquille";

    const std::vector<const core::PropertyMap*> zones = grille.zonesAt({2, 1});
    ASSERT_EQ(zones.size(), 2U);
    EXPECT_TRUE(zones[0]->contains("difficultTerrain"));
    EXPECT_TRUE(std::get<bool>(zones[1]->at("noHealing")));
    EXPECT_TRUE(grille.zonesAt({4, 3}).empty());
    EXPECT_TRUE(grille.zonesAt({-1, 0}).empty());
}

/**
 * @brief Le terrain difficile peut naitre et disparaitre en cours de combat.
 * \castest{<b>Le terrain difficile se cree et s'efface en combat.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Rendre une case difficile (un seisme).<br/>2. L'effacer.<br/>3. Viser une case hors
 * de la carte.<br/>
 * \tattendu La case suit chaque changement ; la case hors carte est ignoree sans erreur.
 * }
 */
TEST(BattleGridTest, LeTerrainDifficileSeCreeEnCombat) {
    const core::TileMap collision(3, 3);
    core::BattleGrid grille(collision);

    grille.setDifficult({1, 1}, true);
    EXPECT_TRUE(grille.isDifficult({1, 1}));
    grille.setDifficult({1, 1}, false);
    EXPECT_FALSE(grille.isDifficult({1, 1}));
    grille.setDifficult({9, 9}, true);
    EXPECT_FALSE(grille.isDifficult({9, 9}));
}

/**
 * @brief Un objet de grille a des points de vie, bloque tant qu'il tient, et se detruit.
 * \castest{<b>Un objet de grille bloque tant qu'il tient, puis se detruit.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser une barricade de 10 PV et une toile non bloquante.<br/>2. Infliger 4 puis 6
 * degats a la barricade.<br/>3. Placer un combattant sur la toile, puis tenter une barricade sur
 * lui.<br/>
 * \tattendu La barricade bloque jusqu'au coup qui la detruit, puis la case se libere ; la toile
 * accueille un combattant ; une barricade ne se pose pas sur un combattant.
 * }
 */
TEST(BattleGridTest, UnObjetDeGrilleBloqueEtSeDetruit) {
    const core::TileMap collision(4, 4);
    core::BattleGrid grille(collision);

    ASSERT_EQ(grille.placeObject({1, 1}, {.kind = "barricade", .hitPoints = 10}),
              core::PlacementResult::Placed);
    ASSERT_EQ(grille.placeObject({2, 2}, {.kind = "web", .hitPoints = 10, .blocksMovement = false}),
              core::PlacementResult::Placed);
    EXPECT_EQ(grille.placeObject({1, 1}, {.kind = "tonneau"}), core::PlacementResult::Occupied);

    EXPECT_TRUE(grille.isObstructed({1, 1}));
    EXPECT_EQ(grille.place(HEROS, {1, 1}), core::PlacementResult::Obstructed);
    EXPECT_FALSE(grille.damageObject({1, 1}, 4));
    ASSERT_NE(grille.objectAt({1, 1}), nullptr);
    EXPECT_EQ(grille.objectAt({1, 1})->hitPoints, 6);
    EXPECT_TRUE(grille.damageObject({1, 1}, 6));
    EXPECT_EQ(grille.objectAt({1, 1}), nullptr);
    EXPECT_FALSE(grille.isObstructed({1, 1}));

    EXPECT_FALSE(grille.isObstructed({2, 2})) << "une toile se traverse";
    ASSERT_EQ(grille.place(HEROS, {3, 3}), core::PlacementResult::Placed);
    EXPECT_EQ(grille.placeObject({3, 3}, {.kind = "barricade"}), core::PlacementResult::Occupied);
}
