// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_math_utils.cpp
 * @brief Tests unitaires des utilitaires mathématiques (comparaison flottante).
 */

#include <gtest/gtest.h>

#include "Core/Math/MathUtils.h"

/**
 * @brief Deux valeurs identiques sont approximativement égales.
 * \castest{<b>approximatelyEqual : égalité exacte</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Comparer des valeurs identiques (1, 0, -2,5).<br/>
 * \tattendu `approximatelyEqual` renvoie vrai.}
 */
TEST(MathUtilsTest, EgaliteExacte) {
    EXPECT_TRUE(core::approximatelyEqual(1.0f, 1.0f));
    EXPECT_TRUE(core::approximatelyEqual(0.0f, 0.0f));
    EXPECT_TRUE(core::approximatelyEqual(-2.5f, -2.5f));
}

/**
 * @brief Un écart en deçà de la tolérance est considéré comme égal, au-delà comme différent.
 * \castest{<b>approximatelyEqual : tolérance par défaut</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Comparer 1 et 1+1e-6.<br/>2. Comparer 1 et 1,1.<br/>
 * \tattendu Égal sous la tolérance ; différent au-delà.}
 */
TEST(MathUtilsTest, ToleranceParDefaut) {
    EXPECT_TRUE(core::approximatelyEqual(1.0f, 1.0f + 1e-6f));
    EXPECT_FALSE(core::approximatelyEqual(1.0f, 1.1f));
}

/**
 * @brief La tolérance est mise à l'échelle des grandes magnitudes (robustesse relative).
 * \castest{<b>approximatelyEqual : mise à l'échelle des grandes magnitudes</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Comparer 1e6 et 1e6+1.<br/>2. Comparer 1e6 et 1e6+1000.<br/>
 * \tattendu Égal pour un petit écart relatif ; différent pour un grand.}
 */
TEST(MathUtilsTest, MiseALEchelleGrandesMagnitudes) {
    EXPECT_TRUE(core::approximatelyEqual(1.0e6f, 1.0e6f + 1.0f));
    EXPECT_FALSE(core::approximatelyEqual(1.0e6f, 1.0e6f + 1000.0f));
}

/**
 * @brief Des signes opposés ne sont pas égaux.
 * \castest{<b>approximatelyEqual : signes opposés</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Comparer 2 et -2.<br/>
 * \tattendu Non égaux.}
 */
TEST(MathUtilsTest, SignesOpposes) {
    EXPECT_FALSE(core::approximatelyEqual(2.0f, -2.0f));
}

/**
 * @brief Une tolérance explicite élargit l'égalité.
 * \castest{<b>approximatelyEqual : tolérance explicite</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Comparer 1 et 1,5 sans tolérance.<br/>2. Recomparer avec une tolérance de 1.<br/>
 * \tattendu Différent par défaut ; égal avec la tolérance élargie.}
 */
TEST(MathUtilsTest, ToleranceExplicite) {
    EXPECT_FALSE(core::approximatelyEqual(1.0f, 1.5f));
    EXPECT_TRUE(core::approximatelyEqual(1.0f, 1.5f, 1.0f));
}
