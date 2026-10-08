// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_rect.cpp
 * @brief Tests unitaires du rectangle aligné sur les axes de `Core`.
 */

#include <gtest/gtest.h>

#include "Core/Math/Rect.h"
#include "Core/Math/Vector2.h"

namespace {
constexpr float TOLERANCE = 1e-5f;
}

/**
 * @brief Les bords exposés découlent de la position et de la taille.
 * \castest{<b>Les bords exposés découlent de la position et de la taille.</b><br/>
 * \tcat Unitaire · Rect<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Les bords exposés découlent de la position et de la taille.
 * }
 */
TEST(RectTest, Bords) {
    const core::Rect rect{{10.0f, 20.0f}, {30.0f, 40.0f}};
    EXPECT_NEAR(rect.left(), 10.0f, TOLERANCE);
    EXPECT_NEAR(rect.top(), 20.0f, TOLERANCE);
    EXPECT_NEAR(rect.right(), 40.0f, TOLERANCE);
    EXPECT_NEAR(rect.bottom(), 60.0f, TOLERANCE);
}

/**
 * @brief Un point strictement intérieur est contenu.
 * \castest{<b>Un point strictement intérieur est contenu.</b><br/>
 * \tcat Unitaire · Rect<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un point strictement intérieur est contenu.
 * }
 */
TEST(RectTest, ContientPointInterieur) {
    const core::Rect rect{{0.0f, 0.0f}, {10.0f, 10.0f}};
    EXPECT_TRUE(rect.contains(core::Vector2{5.0f, 5.0f}));
}

/**
 * @brief Contenance inclusive haut/gauche, exclusive bas/droit.
 * \castest{<b>Contenance inclusive haut/gauche, exclusive bas/droit.</b><br/>
 * \tcat Unitaire · Rect<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Contenance inclusive haut/gauche, exclusive bas/droit.
 * }
 */
TEST(RectTest, ContientBords) {
    const core::Rect rect{{0.0f, 0.0f}, {10.0f, 10.0f}};
    EXPECT_TRUE(rect.contains(core::Vector2{0.0f, 0.0f}));    // coin haut-gauche inclus
    EXPECT_FALSE(rect.contains(core::Vector2{10.0f, 5.0f}));  // bord droit exclu
    EXPECT_FALSE(rect.contains(core::Vector2{5.0f, 10.0f}));  // bord bas exclu
}

/**
 * @brief Un point extérieur n'est pas contenu.
 * \castest{<b>Un point extérieur n'est pas contenu.</b><br/>
 * \tcat Unitaire · Rect<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un point extérieur n'est pas contenu.
 * }
 */
TEST(RectTest, NeContientPasExterieur) {
    const core::Rect rect{{0.0f, 0.0f}, {10.0f, 10.0f}};
    EXPECT_FALSE(rect.contains(core::Vector2{-1.0f, 5.0f}));
    EXPECT_FALSE(rect.contains(core::Vector2{5.0f, 100.0f}));
}

/**
 * @brief Deux rectangles qui se recouvrent s'intersectent (relation symétrique).
 * \castest{<b>Deux rectangles qui se recouvrent s'intersectent (relation symétrique).</b><br/>
 * \tcat Unitaire · Rect<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Deux rectangles qui se recouvrent s'intersectent (relation symétrique).
 * }
 */
TEST(RectTest, IntersectionRecouvrement) {
    const core::Rect a{{0.0f, 0.0f}, {10.0f, 10.0f}};
    const core::Rect b{{5.0f, 5.0f}, {10.0f, 10.0f}};
    EXPECT_TRUE(a.intersects(b));
    EXPECT_TRUE(b.intersects(a));
}

/**
 * @brief Un simple contact par un bord ne compte pas comme intersection.
 * \castest{<b>Un simple contact par un bord ne compte pas comme intersection.</b><br/>
 * \tcat Unitaire · Rect<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un simple contact par un bord ne compte pas comme intersection.
 * }
 */
TEST(RectTest, ContactBordSansIntersection) {
    const core::Rect a{{0.0f, 0.0f}, {10.0f, 10.0f}};
    const core::Rect b{{10.0f, 0.0f}, {10.0f, 10.0f}};  // colle le bord droit de a
    EXPECT_FALSE(a.intersects(b));
}

/**
 * @brief Deux rectangles disjoints ne s'intersectent pas.
 * \castest{<b>Deux rectangles disjoints ne s'intersectent pas.</b><br/>
 * \tcat Unitaire · Rect<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Deux rectangles disjoints ne s'intersectent pas.
 * }
 */
TEST(RectTest, Disjonction) {
    const core::Rect a{{0.0f, 0.0f}, {10.0f, 10.0f}};
    const core::Rect b{{20.0f, 20.0f}, {5.0f, 5.0f}};
    EXPECT_FALSE(a.intersects(b));
}
