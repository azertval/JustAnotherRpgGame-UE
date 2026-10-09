// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_map_interactions.cpp
 * @brief Les lieux cliquables de l'écran Carte (LOT-1020) : le fichier du dépôt, ses niveaux, ses
 *        voisins, et une entrée fautive.
 */

#include <filesystem>

#include <gtest/gtest.h>

#include "Core/Ui/MapInteractions.h"

/**
 * @brief Le fichier du dépôt se lit, du monde jusqu'aux bâtiments d'un quartier.
 * \castest{<b>Les lieux de la carte se lisent du monde aux bâtiments.</b><br/>
 * \tcat Unitaire · Interface · Carte<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Lire Source/Elements/Maps/map-interactions.json.<br/>2. Descendre du monde à
 *          l'Empire central, à la Capitale, à Arenarea.<br/>
 * \tattendu Aucune erreur ; le monde a ses régions sur Maps/world.png, dont l'Empire central ;
 *           Arenarea s'ouvre sur son illustration et porte l'Arena of Fate, dont le parent est
 *           Arenarea ; un lieu déborde au moins une fois sur une illustration voisine.
 * }
 */
TEST(MapInteractionsTest, LesLieuxSeLisentDuMondeAuxBatiments) {
    const core::MapInteractions read = core::loadMapInteractions(
        std::filesystem::path(JADG_ELEMENTS_DIR) / "Maps" / "map-interactions.json");
    ASSERT_TRUE(read.errors.empty()) << read.errors.front();
    EXPECT_EQ(read.imageOf("world"), "Maps/world.png");
    bool empire = false;
    for (const core::MapZone* zone : read.childrenOf("world")) {
        empire = empire || zone->id == "central-empire";
    }
    EXPECT_TRUE(empire);
    EXPECT_EQ(read.imageOf("central-empire-the-capital-city-arenarea"),
              "Maps/capital/images/arenarea.png");
    EXPECT_EQ(read.parentOf("arena-of-fate"), "central-empire-the-capital-city-arenarea");
    EXPECT_TRUE(read.imageOf("hippodrome").empty() || !read.childrenOf("hippodrome").empty());
    bool neighbour = false;
    for (const core::MapZone& zone : read.zones) {
        neighbour = neighbour || zone.neighbour;
    }
    EXPECT_TRUE(neighbour);
}

/**
 * @brief Une entrée sans parent ou à la bannière fausse est nommée ; les autres se lisent.
 * \castest{<b>Un lieu fautif de la carte est nommé, les autres se lisent.</b><br/>
 * \tcat Unitaire · Interface · Carte<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire trois entrées : une juste, une sans parent, une à la bannière de trois
 * nombres.<br/>
 * \tattendu Deux erreurs ; la juste est lue.
 * }
 */
TEST(MapInteractionsTest, UnLieuFautifEstNomme) {
    const core::MapInteractions read = core::readMapInteractions(R"({"version": 1, "entries": {
        "a": {"image": "Maps/world.png", "parent": "world", "label": [0.1, 0.2, 0.3, 0.04]},
        "b": {"image": "Maps/world.png"},
        "c": {"image": "Maps/world.png", "parent": "world", "label": [0.1, 0.2, 0.3]}}})");
    EXPECT_EQ(read.errors.size(), 2U);
    ASSERT_EQ(read.zones.size(), 1U);
    EXPECT_FLOAT_EQ(read.zones[0].label[2], 0.3F);
}
