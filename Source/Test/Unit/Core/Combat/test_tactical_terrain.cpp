// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_tactical_terrain.cpp
 * @brief Tests de l'avertissement d'une rencontre mal posée (`LOT-11`, `EX-CBT-001`).
 *
 * Le combat se joue sur la carte d'exploration : toute carte doit être un terrain tactique valide.
 * Les cartes sont écrites ici, à la case près, pour qu'un seuil déplacé se voie au premier test
 * qui le franchit.
 */

#include <cstddef>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/Encounter.h"
#include "Core/Combat/TacticalTerrain.h"
#include "Core/Levels/GridPosition.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"
#include "Core/Rpg/Bestiary.h"

namespace {

/// Un catalogue d'une rencontre de deux combattants : un rat devant, un rat à droite.
[[nodiscard]] core::EncounterCatalog catalogue() {
    core::Encounter combat;
    combat.id = "rats";
    combat.combatants = {
        {.creatureId = "rat", .columnOffset = 0, .rowOffset = -1},
        {.creatureId = "rat", .columnOffset = 1, .rowOffset = 0},
    };
    core::EncounterCatalog rencontres;
    rencontres.encounters.push_back(combat);
    return rencontres;
}

/// Une entité de rencontre nommant @p rencontre, posée en @p case_.
[[nodiscard]] core::MapEntity declencheur(core::GridPosition case_,
                                          const std::string& rencontre = "rats") {
    core::MapEntity entite;
    entite.type = "encounter";
    entite.position = case_;
    entite.properties["encounterId"] = rencontre;
    return entite;
}

/// Un champ ouvert de 20 × 20 cases.
[[nodiscard]] core::TileMap champ() {
    return core::TileMap(20, 20);
}

}  // namespace

/**
 * @brief Une rencontre posée au milieu d'un champ ouvert est valide.
 * \castest{<b>Une rencontre en champ ouvert est un terrain tactique valide.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Poser une rencontre de deux rats au centre d'une carte vide de 20 x 20.<br/>
 * 2. Analyser le terrain.<br/>
 * \tattendu Un verdict valide ; la zone est le carre de 13 x 13 autour du declencheur, triee, et
 * en exige 24.
 * }
 */
TEST(TacticalTerrainTest, UneRencontreEnChampOuvertEstValide) {
    const std::vector<core::MapEntity> entites{declencheur({.column = 10, .row = 10})};

    const auto verdicts = core::analyzeEncounterTerrain(champ(), entites, catalogue());

    ASSERT_EQ(verdicts.size(), 1U);
    const core::EncounterTerrain& verdict = verdicts.front();
    EXPECT_TRUE(verdict.valid());
    EXPECT_EQ(verdict.entityIndex, 0U);
    EXPECT_EQ(verdict.encounterId, "rats");
    EXPECT_EQ(verdict.placements.size(), 2U);
    EXPECT_EQ(verdict.requiredCells, (2 + core::TACTICAL_PARTY_SIZE) * 4);
    // Diagonales à 1 : six cases de rayon font un carré de 13 de côté.
    EXPECT_EQ(verdict.area.size(), 13U * 13U);
    EXPECT_EQ(verdict.area.front(), (core::GridPosition{.column = 4, .row = 4}));
    EXPECT_EQ(verdict.area.back(), (core::GridPosition{.column = 16, .row = 16}));
}

/**
 * @brief Un combattant dont la case voulue tombe dans un mur est signalé.
 * \castest{<b>Un combattant pose dans un mur est signale.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Murer la case devant le declencheur.<br/>2. Analyser le terrain.<br/>
 * \tattendu Un seul probleme, CombatantObstructed, sur le premier rat et sa case.
 * }
 */
TEST(TacticalTerrainTest, UnCombattantDansUnMurEstSignale) {
    core::TileMap collision = champ();
    collision.setTile(10, 9, core::TileType::Wall);
    const std::vector<core::MapEntity> entites{declencheur({.column = 10, .row = 10})};

    const auto verdicts = core::analyzeEncounterTerrain(collision, entites, catalogue());

    ASSERT_EQ(verdicts.size(), 1U);
    const std::vector<core::TacticalIssue> attendus{
        {.code = core::TacticalIssueCode::CombatantObstructed,
         .creatureId = "rat",
         .cell = {.column = 10, .row = 9}}};
    EXPECT_EQ(verdicts.front().issues, attendus);
}

/**
 * @brief Une formation qui sort de la carte est signalée.
 * \castest{<b>Un combattant hors de la carte est signale.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Poser le declencheur sur la premiere ligne : le premier rat tombe en ligne -1.<br/>
 * 2. Analyser le terrain.<br/>
 * \tattendu CombatantOutOfBounds pour le premier rat, et aucun autre probleme.
 * }
 */
TEST(TacticalTerrainTest, UnCombattantHorsDeLaCarteEstSignale) {
    const std::vector<core::MapEntity> entites{declencheur({.column = 10, .row = 0})};

    const auto verdicts = core::analyzeEncounterTerrain(champ(), entites, catalogue());

    ASSERT_EQ(verdicts.size(), 1U);
    const std::vector<core::TacticalIssue> attendus{
        {.code = core::TacticalIssueCode::CombatantOutOfBounds,
         .creatureId = "rat",
         .cell = {.column = 10, .row = -1}}};
    EXPECT_EQ(verdicts.front().issues, attendus);
}

/**
 * @brief Deux combattants sur la même case : c'est le second qui est signalé.
 * \castest{<b>Deux combattants superposes sont signales.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Ecrire une rencontre dont deux combattants partagent un decalage.<br/>
 * 2. Analyser le terrain.<br/>
 * \tattendu Un seul CombatantsOverlap, sur le second combattant.
 * }
 */
TEST(TacticalTerrainTest, DeuxCombattantsSuperposesSontSignales) {
    core::EncounterCatalog rencontres = catalogue();
    rencontres.encounters.front().combatants = {
        {.creatureId = "rat", .columnOffset = 1, .rowOffset = 1},
        {.creatureId = "chef-rat", .columnOffset = 1, .rowOffset = 1},
    };
    const std::vector<core::MapEntity> entites{declencheur({.column = 10, .row = 10})};

    const auto verdicts = core::analyzeEncounterTerrain(champ(), entites, rencontres);

    ASSERT_EQ(verdicts.size(), 1U);
    const std::vector<core::TacticalIssue> attendus{
        {.code = core::TacticalIssueCode::CombatantsOverlap,
         .creatureId = "chef-rat",
         .cell = {.column = 11, .row = 11}}};
    EXPECT_EQ(verdicts.front().issues, attendus);
}

/**
 * @brief Une rencontre posée dans un couloir d'une case de large est trop à l'étroit.
 * \castest{<b>Un couloir trop etroit est signale.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Murer une carte de 30 x 3 sauf sa ligne du milieu.<br/>2. Y poser une rencontre de
 * deux combattants alignes.<br/>3. Analyser le terrain.<br/>
 * \tattendu 13 cases atteignables pour 24 exigees : un seul AreaTooNarrow, sur le declencheur.
 * }
 */
TEST(TacticalTerrainTest, UnCouloirTropEtroitEstSignale) {
    core::TileMap collision(30, 3);
    for (int column = 0; column < 30; ++column) {
        collision.setTile(column, 0, core::TileType::Wall);
        collision.setTile(column, 2, core::TileType::Wall);
    }
    core::EncounterCatalog rencontres = catalogue();
    rencontres.encounters.front().combatants = {
        {.creatureId = "rat", .columnOffset = 1, .rowOffset = 0},
        {.creatureId = "rat", .columnOffset = 2, .rowOffset = 0},
    };
    const std::vector<core::MapEntity> entites{declencheur({.column = 15, .row = 1})};

    const auto verdicts = core::analyzeEncounterTerrain(collision, entites, rencontres);

    ASSERT_EQ(verdicts.size(), 1U);
    const core::EncounterTerrain& verdict = verdicts.front();
    EXPECT_EQ(verdict.area.size(), 13U);
    EXPECT_EQ(verdict.requiredCells, 24);
    const std::vector<core::TacticalIssue> attendus{{.code = core::TacticalIssueCode::AreaTooNarrow,
                                                     .creatureId = {},
                                                     .cell = {.column = 15, .row = 1}}};
    EXPECT_EQ(verdict.issues, attendus);
}

/**
 * @brief Un déclencheur posé dans un mur n'a aucune zone.
 * \castest{<b>Un declencheur dans un mur n'a aucune zone.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Murer la case du declencheur d'un champ ouvert.<br/>2. Analyser le terrain.<br/>
 * \tattendu Zone vide, et AreaTooNarrow en dernier probleme.
 * }
 */
TEST(TacticalTerrainTest, UnDeclencheurDansUnMurNAAucuneZone) {
    core::TileMap collision = champ();
    collision.setTile(10, 10, core::TileType::Wall);
    const std::vector<core::MapEntity> entites{declencheur({.column = 10, .row = 10})};

    const auto verdicts = core::analyzeEncounterTerrain(collision, entites, catalogue());

    ASSERT_EQ(verdicts.size(), 1U);
    EXPECT_TRUE(verdicts.front().area.empty());
    ASSERT_FALSE(verdicts.front().issues.empty());
    EXPECT_EQ(verdicts.front().issues.back().code, core::TacticalIssueCode::AreaTooNarrow);
}

/**
 * @brief Une rencontre absente du catalogue n'a pas de verdict : un autre validateur la signale.
 * \castest{<b>Une rencontre inconnue est ignoree.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser une rencontre inconnue, puis une connue.<br/>2. Analyser le terrain.<br/>
 * \tattendu Un seul verdict, celui de la seconde entite, au rang 1.
 * }
 */
TEST(TacticalTerrainTest, UneRencontreInconnueEstIgnoree) {
    const std::vector<core::MapEntity> entites{
        declencheur({.column = 5, .row = 5}, "fantome"),
        declencheur({.column = 10, .row = 10}),
    };

    const auto verdicts = core::analyzeEncounterTerrain(champ(), entites, catalogue());

    ASSERT_EQ(verdicts.size(), 1U);
    EXPECT_EQ(verdicts.front().entityIndex, 1U);
    EXPECT_EQ(verdicts.front().encounterId, "rats");
}

/**
 * @brief Ce qui n'est pas un déclencheur de rencontre n'est pas analysé.
 * \castest{<b>Les entites qui ne sont pas des rencontres sont ignorees.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser un coffre portant un encounterId, et une rencontre sans encounterId, tous deux
 * dans un mur.<br/>2. Analyser le terrain.<br/>
 * \tattendu Aucun verdict.
 * }
 */
TEST(TacticalTerrainTest, LesAutresEntitesSontIgnorees) {
    core::TileMap collision = champ();
    collision.setTile(3, 3, core::TileType::Wall);
    core::MapEntity coffre = declencheur({.column = 3, .row = 3});
    coffre.type = "chest";
    core::MapEntity sansRencontre;
    sansRencontre.type = "encounter";
    sansRencontre.position = {.column = 3, .row = 3};
    const std::vector<core::MapEntity> entites{coffre, sansRencontre};

    EXPECT_TRUE(core::analyzeEncounterTerrain(collision, entites, catalogue()).empty());
}

/**
 * @brief Une grande créature occupe 2 x 2 cases, et le mur qu'elle touche se voit avec le
 *        bestiaire.
 * \castest{<b>L'emprise d'une grande creature vient du bestiaire.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser un ogre (taille G) dont seule la case diagonale de son emprise est
 * muree.<br/>2. Analyser sans bestiaire, puis avec.<br/>
 * \tattendu Sans bestiaire, taille M : valide. Avec : CombatantObstructed sur l'ogre.
 * }
 */
TEST(TacticalTerrainTest, LEmpriseDUneGrandeCreatureVientDuBestiaire) {
    core::TileMap collision = champ();
    collision.setTile(11, 9, core::TileType::Wall);
    core::EncounterCatalog rencontres = catalogue();
    rencontres.encounters.front().combatants = {
        {.creatureId = "ogre", .columnOffset = 0, .rowOffset = -2},
    };
    core::Creature ogre;
    ogre.id = "ogre";
    ogre.size = core::CreatureSize::Large;
    core::Bestiary bestiaire;
    bestiaire.creatures.push_back(ogre);
    const std::vector<core::MapEntity> entites{declencheur({.column = 10, .row = 10})};

    const auto sansBestiaire = core::analyzeEncounterTerrain(collision, entites, rencontres);
    const auto avecBestiaire =
        core::analyzeEncounterTerrain(collision, entites, rencontres, &bestiaire);

    ASSERT_EQ(sansBestiaire.size(), 1U);
    EXPECT_TRUE(sansBestiaire.front().valid()) << "sans bestiaire, l'ogre compte pour une case";
    ASSERT_EQ(avecBestiaire.size(), 1U);
    const std::vector<core::TacticalIssue> attendus{
        {.code = core::TacticalIssueCode::CombatantObstructed,
         .creatureId = "ogre",
         .cell = {.column = 10, .row = 8}}};
    EXPECT_EQ(avecBestiaire.front().issues, attendus);
}

/**
 * @brief La même carte donne toujours le même verdict, dans l'ordre des entités.
 * \castest{<b>L'analyse est deterministe.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser trois rencontres, dont une mal posee.<br/>2. Analyser deux fois.<br/>
 * \tattendu Les verdicts sont dans l'ordre des entites, et identiques d'un appel a l'autre.
 * }
 */
TEST(TacticalTerrainTest, LAnalyseEstDeterministe) {
    core::TileMap collision = champ();
    collision.setTile(4, 3, core::TileType::Wall);
    const std::vector<core::MapEntity> entites{
        declencheur({.column = 15, .row = 15}),
        declencheur({.column = 4, .row = 4}),
        declencheur({.column = 10, .row = 0}),
    };

    const auto premier = core::analyzeEncounterTerrain(collision, entites, catalogue());
    const auto second = core::analyzeEncounterTerrain(collision, entites, catalogue());

    ASSERT_EQ(premier.size(), 3U);
    ASSERT_EQ(second.size(), 3U);
    for (std::size_t i = 0; i < premier.size(); ++i) {
        EXPECT_EQ(premier[i].entityIndex, i);
        EXPECT_EQ(premier[i].area, second[i].area);
        EXPECT_EQ(premier[i].issues, second[i].issues);
    }
    EXPECT_TRUE(premier[0].valid());
    EXPECT_FALSE(premier[1].valid());
    EXPECT_FALSE(premier[2].valid());
}
