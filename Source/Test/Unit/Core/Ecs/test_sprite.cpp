// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_sprite.cpp
 * @brief Tests unitaires du composant d'apparence `Sprite` (données pures).
 */

#include <gtest/gtest.h>

#include "Core/Ecs/Components/Sprite.h"

/**
 * @brief Un sprite par défaut a une teinte blanche opaque, la couche 0 et une région nulle.
 * \castest{<b>Un sprite par défaut a une teinte blanche opaque, la couche 0 et une région
 * nulle.</b><br/>
 * \tcat Unitaire · Sprite<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un sprite par défaut a une teinte blanche opaque, la couche 0 et une région nulle.
 * }
 */
TEST(SpriteTest, ValeursParDefaut) {
    const core::Sprite sprite;

    EXPECT_EQ(sprite.layer, 0);
    EXPECT_EQ(sprite.region.x, 0);
    EXPECT_EQ(sprite.region.y, 0);
    EXPECT_EQ(sprite.region.width, 0);
    EXPECT_EQ(sprite.region.height, 0);
    EXPECT_FLOAT_EQ(sprite.tint.r, 1.0f);
    EXPECT_FLOAT_EQ(sprite.tint.g, 1.0f);
    EXPECT_FLOAT_EQ(sprite.tint.b, 1.0f);
    EXPECT_FLOAT_EQ(sprite.tint.a, 1.0f);
}

/**
 * @brief Les champs sont librement assignables (donnée pure).
 * \castest{<b>Les champs sont librement assignables (donnée pure).</b><br/>
 * \tcat Unitaire · Sprite<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Les champs sont librement assignables (donnée pure).
 * }
 */
TEST(SpriteTest, ChampsAssignables) {
    core::Sprite sprite;
    sprite.region = core::AtlasRegion{16, 32, 16, 16};
    sprite.layer = 2;
    sprite.tint = core::Color{1.0f, 0.5f, 0.0f, 0.8f};

    EXPECT_EQ(sprite.region.x, 16);
    EXPECT_EQ(sprite.region.y, 32);
    EXPECT_EQ(sprite.region.width, 16);
    EXPECT_EQ(sprite.region.height, 16);
    EXPECT_EQ(sprite.layer, 2);
    EXPECT_FLOAT_EQ(sprite.tint.g, 0.5f);
    EXPECT_FLOAT_EQ(sprite.tint.a, 0.8f);
}

/**
 * @brief Le composant est utilisable comme un composant d'ECS (stockage/copie de données pures).
 * \castest{<b>Le composant est utilisable comme un composant d'ECS (stockage/copie de données
 * pures).</b><br/>
 * \tcat Unitaire · Sprite<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Le composant est utilisable comme un composant d'ECS (stockage/copie de données pures).
 * }
 */
TEST(SpriteTest, CopieValeur) {
    const core::Sprite source{core::AtlasRegion{0, 0, 16, 16}, 5,
                              core::Color{0.2f, 0.2f, 0.2f, 1.0f}};
    const core::Sprite copy = source;

    EXPECT_EQ(copy.layer, 5);
    EXPECT_EQ(copy.region.width, 16);
    EXPECT_FLOAT_EQ(copy.tint.r, 0.2f);
}
