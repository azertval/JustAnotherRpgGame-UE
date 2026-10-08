// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_level.cpp
 * @brief Tests unitaires du modèle de niveau : TileMap et Level.
 */

#include <gtest/gtest.h>

#include "Core/Levels/Level.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"

/**
 * @brief Une grille neuve a les bonnes dimensions et n'est composée que de cases Empty.
 * \castest{<b>Une grille neuve a les bonnes dimensions et n'est composée que de cases
 * Empty.</b><br/>
 * \tcat Unitaire · Tile Map<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Une grille neuve a les bonnes dimensions et n'est composée que de cases Empty.
 * }
 */
TEST(TileMapTest, GrilleNeuveVideAuxBonnesDimensions) {
    const core::TileMap map(4, 3);

    EXPECT_EQ(map.width(), 4);
    EXPECT_EQ(map.height(), 3);
    for (int row = 0; row < map.height(); ++row) {
        for (int column = 0; column < map.width(); ++column) {
            EXPECT_EQ(map.tile(column, row), core::TileType::Empty);
        }
    }
}

/**
 * @brief Écrire puis lire une tuile restitue le type posé.
 * \castest{<b>Écrire puis lire une tuile restitue le type posé.</b><br/>
 * \tcat Unitaire · Tile Map<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Écrire puis lire une tuile restitue le type posé.
 * }
 */
TEST(TileMapTest, EcritureLectureDUneTuile) {
    core::TileMap map(4, 3);
    map.setTile(2, 1, core::TileType::Solid);

    EXPECT_EQ(map.tile(2, 1), core::TileType::Solid);
    EXPECT_EQ(map.tile(0, 0), core::TileType::Empty);  // les autres restent vides
}

/**
 * @brief Les bornes de la grille sont correctement détectées.
 * \castest{<b>Les bornes de la grille sont correctement détectées.</b><br/>
 * \tcat Unitaire · Tile Map<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Les bornes de la grille sont correctement détectées.
 * }
 */
TEST(TileMapTest, Bornes) {
    const core::TileMap map(4, 3);

    EXPECT_TRUE(map.inBounds(0, 0));
    EXPECT_TRUE(map.inBounds(3, 2));
    EXPECT_FALSE(map.inBounds(4, 2));
    EXPECT_FALSE(map.inBounds(3, 3));
    EXPECT_FALSE(map.inBounds(-1, 0));
}

/**
 * @brief Seules les tuiles solides bloquent statiquement.
 * \castest{<b>Seules les tuiles solides bloquent statiquement.</b><br/>
 * \tcat Unitaire · Tile Map<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Seules les tuiles solides bloquent statiquement.
 * }
 */
TEST(TileMapTest, Solidite) {
    core::TileMap map(3, 1);
    map.setTile(0, 0, core::TileType::Solid);
    map.setTile(1, 0, core::TileType::Grass);
    // (2, 0) reste Empty

    EXPECT_TRUE(map.isSolid(0, 0));
    EXPECT_FALSE(map.isSolid(1, 0));
    EXPECT_FALSE(map.isSolid(2, 0));
}

/**
 * @brief `isSolid(TileType)` : vrai seulement pour Solid.
 * \castest{<b>`isSolid(TileType)` : vrai seulement pour Solid.</b><br/>
 * \tcat Unitaire · Tile Map<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `isSolid(TileType)` : vrai seulement pour Solid.
 * }
 */
TEST(TileMapTest, IsSolidParType) {
    EXPECT_TRUE(core::isSolid(core::TileType::Solid));
    EXPECT_FALSE(core::isSolid(core::TileType::Empty));
    EXPECT_FALSE(core::isSolid(core::TileType::Entry));
    EXPECT_FALSE(core::isSolid(core::TileType::Grass));
}

/**
 * @brief Un Level restitue ses composantes (nom, grille, entrée).
 * \castest{<b>Un Level restitue ses composantes (nom, grille, entrée).</b><br/>
 * \tcat Unitaire · Level<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un Level restitue ses composantes (nom, grille, entrée).
 * }
 */
TEST(LevelTest, RestitueSesComposantes) {
    core::TileMap map(5, 4);
    map.setTile(1, 1, core::TileType::Entry);

    const core::Level level(core::LevelData{
        .name = "Tutoriel", .tileMap = std::move(map), .entry = core::GridPosition{1, 1}});

    EXPECT_EQ(level.name(), "Tutoriel");
    EXPECT_EQ(level.tileMap().width(), 5);
    EXPECT_EQ(level.entry(), (core::GridPosition{1, 1}));
}
