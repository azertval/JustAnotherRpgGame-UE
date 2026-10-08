// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_combat_zone.cpp
 * @brief Tests de la zone de combat (LOT-09) : la session joue sur la zone declaree, et les cases
 *        du dehors lui sont inconnues.
 */

#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/Arena.h"
#include "Core/Levels/GridPosition.h"
#include "Core/Levels/Level.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"
#include "Core/Rpg/Dialogue.h"
#include "Core/World/CombatZone.h"
#include "Core/World/WorldTravel.h"

namespace {

core::MapEntity zone(std::string nom, core::GridPosition origine, int largeur, int hauteur) {
    return core::MapEntity{
        .type = std::string{core::COMBAT_ZONE_ENTITY_TYPE},
        .position = origine,
        .properties = {
            {std::string{core::COMBAT_ZONE_NAME_PROPERTY}, std::move(nom)},
            {std::string{core::COMBAT_ZONE_WIDTH_PROPERTY}, static_cast<std::int64_t>(largeur)},
            {std::string{core::COMBAT_ZONE_HEIGHT_PROPERTY}, static_cast<std::int64_t>(hauteur)}}};
}

// Une carte de 12 x 10, murs au pourtour, une zone « sable » de 4 x 3 en (4, 4), un PNJ dedans et
// un autre dehors, et une couche de decor pour verifier qu'elle se decoupe aussi.
core::Level carte(std::vector<core::MapEntity> entites) {
    core::TileMap collision{12, 10};
    for (int colonne = 0; colonne < 12; ++colonne) {
        collision.setTile(colonne, 0, core::TileType::Wall);
        collision.setTile(colonne, 9, core::TileType::Wall);
    }
    core::TileMap decor{12, 10};
    decor.setTile(4, 4, core::TileType::Wall);

    core::LevelData donnees{.name = "colisee", .tileMap = std::move(collision)};
    donnees.entry = {1, 1};
    donnees.layers.push_back(core::TileLayer{.name = "relief",
                                             .kind = core::LayerKind::Decor,
                                             .tiles = std::move(decor),
                                             .properties = {}});
    donnees.layers.back().setPiece(5, 5, "torch-left");
    donnees.layers.back().setPiece(1, 1, "wall-left");
    donnees.forcedCollision = {{1, 1}, {6, 5}};
    donnees.entities = std::move(entites);
    return core::Level{std::move(donnees)};
}

}  // namespace

/**
 * @brief La zone declaree se lit, et la carte reduite n'est qu'elle.
 * \castest{<b>La carte reduite a la zone ne porte que la zone, entites translatees.</b><br/>
 * \tcat Unitaire · Zone de combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Declarer une zone « sable » de 4 x 3 en (4, 4) sur une carte de 12 x 10.<br/>
 * 2. Reduire la carte a la zone.<br/>
 * \tattendu Une grille de 4 x 3 ; les entites du dedans translatees a l'origine de la zone, celles
 * du dehors absentes ; le decor, ses pieces et les cases forcees decoupes de meme.
 * }
 */
TEST(CombatZoneTest, LaCarteReduiteNEstQueLaZone) {
    const core::Level complete = carte(
        {zone("sable", {4, 4}, 4, 3),
         core::MapEntity{.type = std::string{core::NPC_ENTITY_TYPE}, .position = {5, 5}},
         core::MapEntity{.type = std::string{core::NPC_ENTITY_TYPE}, .position = {1, 1}},
         core::MapEntity{
             .type = std::string{core::ARENA_ENTRY_ENTITY_TYPE},
             .position = {4, 6},
             .properties = {{std::string{core::ARENA_SIDE_PROPERTY}, std::string{"allies"}}}}});

    const std::vector<core::CombatZone> zones = core::combatZonesOf(complete);
    ASSERT_EQ(zones.size(), 1U);
    EXPECT_EQ(zones.front(),
              (core::CombatZone{.name = "sable", .origin = {4, 4}, .columns = 4, .rows = 3}));
    EXPECT_TRUE(zones.front().contains({4, 4}));
    EXPECT_TRUE(zones.front().contains({7, 6}));
    EXPECT_FALSE(zones.front().contains({8, 6}));
    EXPECT_EQ(core::findCombatZone(zones, "sable"), &zones.front());
    EXPECT_EQ(core::findCombatZone(zones, ""), &zones.front())
        << "une seule zone se trouve sans nom";
    EXPECT_EQ(core::findCombatZone(zones, "tribunes"), nullptr);

    const core::Level reduite = core::cropLevelToZone(complete, zones.front());
    EXPECT_EQ(reduite.tileMap().width(), 4);
    EXPECT_EQ(reduite.tileMap().height(), 3);

    // Deux entites sur trois sont dans la zone, et elles y sont translatees.
    ASSERT_EQ(reduite.entities().size(), 3U);  // la zone elle-meme compte : elle est dans la zone
    int pnj = 0;
    for (const core::MapEntity& entite : reduite.entities()) {
        if (entite.type == core::NPC_ENTITY_TYPE) {
            ++pnj;
            EXPECT_EQ(entite.position, (core::GridPosition{1, 1}));
        }
        if (entite.type == core::ARENA_ENTRY_ENTITY_TYPE) {
            EXPECT_EQ(entite.position, (core::GridPosition{0, 2}));
        }
    }
    EXPECT_EQ(pnj, 1) << "le PNJ du dehors n'entre pas dans la grille de combat";

    // Le decor et ses pieces suivent : une seule couche visible, decoupee, et la torche de la zone
    // translatee ; le mur du dehors est parti. Les cases forcees suivent de meme.
    ASSERT_EQ(reduite.layers().size(), 1U);
    EXPECT_EQ(reduite.layers().front().tiles.width(), 4);
    EXPECT_EQ(reduite.layers().front().tiles.tile(0, 0), core::TileType::Wall);
    EXPECT_EQ(reduite.layers().front().pieceAt(1, 1), "torch-left");
    EXPECT_EQ(reduite.layers().front().pieces.size(), 12U) << "une piece par case de la zone";
    EXPECT_EQ(reduite.forcedCollision(), (std::vector<core::GridPosition>{{2, 1}}));
}

/**
 * @brief Une session d'arene montee sur la zone ignore les cases du dehors.
 * \castest{<b>La grille de combat de la carte reduite ne connait que la zone.</b><br/>
 * \tcat Unitaire · Zone de combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Monter une `core::ArenaSession` sur la carte reduite a la zone.<br/>
 * \tattendu La grille a la taille de la zone : une case de tribune est hors grille, et la session
 * ne peut donc pas y poser un combattant.
 * }
 */
TEST(CombatZoneTest, LaSessionIgnoreLesCasesHorsZone) {
    const core::Level complete = carte({zone("sable", {4, 4}, 4, 3)});
    const std::vector<core::CombatZone> zones = core::combatZonesOf(complete);
    ASSERT_EQ(zones.size(), 1U);

    const core::ArenaSession session{core::cropLevelToZone(complete, zones.front())};
    EXPECT_EQ(session.combat().grid().width(), 4);
    EXPECT_EQ(session.combat().grid().height(), 3);
    EXPECT_FALSE(session.combat().grid().inBounds({4, 0}))
        << "la premiere case hors zone doit etre inconnue de la grille";
}

/**
 * @brief Chaque defaut de zone est releve au chargement.
 * \castest{<b>Une zone degeneree, debordante ou entierement pleine est refusee, avec son
 * code.</b><br/>
 * \tcat Unitaire · Zone de combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Declarer une zone de largeur nulle, une zone qui sort de la carte, une zone
 * entierement muree.<br/>
 * 2. Valider la carte.<br/>
 * \tattendu Un defaut par zone fautive, situe et nomme (EX-NFR-040) : le refus a lieu au
 * chargement, pas au moment ou le heraut lance le combat.
 * }
 */
TEST(CombatZoneTest, ChaqueDefautDeZoneEstReleveAuChargement) {
    using core::WorldIssueCode;

    const core::Level degeneree = carte({zone("plate", {4, 4}, 0, 3)});
    ASSERT_EQ(core::validateCombatZones("colisee", degeneree).size(), 1U);
    EXPECT_EQ(core::validateCombatZones("colisee", degeneree).front().code,
              WorldIssueCode::CombatZoneDegenerate);

    const core::Level debordante = carte({zone("large", {9, 4}, 6, 3)});
    ASSERT_EQ(core::validateCombatZones("colisee", debordante).size(), 1U);
    EXPECT_EQ(core::validateCombatZones("colisee", debordante).front().code,
              WorldIssueCode::CombatZoneOutOfBounds);

    // Une zone posee sur le mur du pourtour : aucune case libre, personne ne peut s'y poser.
    const core::Level muree = carte({zone("mur", {2, 0}, 3, 1)});
    ASSERT_EQ(core::validateCombatZones("colisee", muree).size(), 1U);
    const core::WorldIssue defaut = core::validateCombatZones("colisee", muree).front();
    EXPECT_EQ(defaut.code, WorldIssueCode::CombatZoneBlocked);
    EXPECT_EQ(defaut.value, "mur");
    EXPECT_EQ(defaut.position, (core::GridPosition{2, 0}));

    // Et la validation de carte les releve avec les autres defauts.
    EXPECT_FALSE(core::validateWorldMap("colisee", muree).empty());
    EXPECT_TRUE(core::validateWorldMap("colisee", carte({zone("sable", {4, 4}, 4, 3)})).empty());
}
