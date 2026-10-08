// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_vector2.cpp
 * @brief Tests unitaires du vecteur 2D de `Core`.
 */

#include <gtest/gtest.h>

#include "Core/Math/Vector2.h"

namespace {
constexpr float TOLERANCE = 1e-5f;
}

/**
 * @brief L'addition et la soustraction agissent composante à composante.
 * \castest{<b>Vector2 : addition et soustraction</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser deux vecteurs.<br/>2. Calculer a+b et a-b.<br/>
 * \tattendu Opérations composante à composante correctes.}
 */
TEST(Vector2Test, AdditionSoustraction) {
    const core::Vector2 a{1.0f, 2.0f};
    const core::Vector2 b{3.0f, -4.0f};
    EXPECT_EQ(a + b, core::Vector2(4.0f, -2.0f));
    EXPECT_EQ(a - b, core::Vector2(-2.0f, 6.0f));
}

/**
 * @brief La multiplication et la division par un scalaire mettent le vecteur à l'échelle.
 * \castest{<b>Vector2 : échelle par un scalaire</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser un vecteur.<br/>2. Multiplier/diviser par un scalaire, prendre l'opposé.<br/>
 * \tattendu Chaque composante est mise à l'échelle ; l'opposé inverse les signes.}
 */
TEST(Vector2Test, EchelleScalaire) {
    const core::Vector2 v{2.0f, -3.0f};
    EXPECT_EQ(v * 2.0f, core::Vector2(4.0f, -6.0f));
    EXPECT_EQ(2.0f * v, core::Vector2(4.0f, -6.0f));
    EXPECT_EQ(v / 2.0f, core::Vector2(1.0f, -1.5f));
    EXPECT_EQ(-v, core::Vector2(-2.0f, 3.0f));
}

/**
 * @brief Les opérateurs composés modifient le vecteur en place.
 * \castest{<b>Vector2 : opérateurs composés</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Appliquer +=, -=, *=, /= à un vecteur.<br/>
 * \tattendu Le vecteur est modifié en place, résultats corrects.}
 */
TEST(Vector2Test, OperateursComposes) {
    core::Vector2 v{1.0f, 1.0f};
    v += core::Vector2{2.0f, 3.0f};
    EXPECT_EQ(v, core::Vector2(3.0f, 4.0f));
    v -= core::Vector2{1.0f, 1.0f};
    EXPECT_EQ(v, core::Vector2(2.0f, 3.0f));
    v *= 2.0f;
    EXPECT_EQ(v, core::Vector2(4.0f, 6.0f));
    v /= 2.0f;
    EXPECT_EQ(v, core::Vector2(2.0f, 3.0f));
}

/**
 * @brief Le produit scalaire renvoie la somme des produits composante à composante.
 * \castest{<b>Vector2 : produit scalaire</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Calculer a·b.<br/>2. Calculer le produit de deux vecteurs orthogonaux.<br/>
 * \tattendu Somme des produits (11) ; produit nul pour des vecteurs orthogonaux.}
 */
TEST(Vector2Test, ProduitScalaire) {
    const core::Vector2 a{1.0f, 2.0f};
    const core::Vector2 b{3.0f, 4.0f};
    EXPECT_NEAR(a.dot(b), 11.0f, TOLERANCE);
    // Deux vecteurs orthogonaux ont un produit scalaire nul.
    EXPECT_NEAR(core::Vector2(1.0f, 0.0f).dot(core::Vector2(0.0f, 1.0f)), 0.0f, TOLERANCE);
}

/**
 * @brief La longueur d'un (3,4) vaut 5 (triangle 3-4-5).
 * \castest{<b>Vector2 : longueur</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Calculer `lengthSquared` et `length` de (3, 4).<br/>
 * \tattendu 25 et 5 (théorème de Pythagore).}
 */
TEST(Vector2Test, Longueur) {
    const core::Vector2 v{3.0f, 4.0f};
    EXPECT_NEAR(v.lengthSquared(), 25.0f, TOLERANCE);
    EXPECT_NEAR(v.length(), 5.0f, TOLERANCE);
}

/**
 * @brief La normalisation d'un vecteur non nul produit un vecteur de longueur 1.
 * \castest{<b>Vector2 : normalisation (non nul)</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Normaliser (3, 4).<br/>
 * \tattendu Longueur 1 ; vecteur (0,6 ; 0,8).}
 */
TEST(Vector2Test, NormalisationNonNulle) {
    const core::Vector2 normalized = core::Vector2{3.0f, 4.0f}.normalized();
    EXPECT_NEAR(normalized.length(), 1.0f, TOLERANCE);
    EXPECT_EQ(normalized, core::Vector2(0.6f, 0.8f));
}

/**
 * @brief La normalisation du vecteur nul renvoie le vecteur nul (aucune direction).
 * \castest{<b>Vector2 : normalisation (vecteur nul)</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Normaliser le vecteur nul.<br/>
 * \tattendu Le vecteur nul (pas de division par zéro).}
 */
TEST(Vector2Test, NormalisationVecteurNul) {
    EXPECT_EQ(core::Vector2{}.normalized(), core::Vector2(0.0f, 0.0f));
}

/**
 * @brief L'égalité est approchée : de petites erreurs de calcul restent égales.
 * \castest{<b>Vector2 : égalité approchée</b><br/>
 * \tcat Unitaire · Mathématiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Comparer (0,1+0,2 ; 1) à (0,3 ; 1).<br/>2. Comparer deux vecteurs distincts.<br/>
 * \tattendu Égal malgré l'erreur flottante ; différent pour des vecteurs distincts.}
 */
TEST(Vector2Test, EgaliteApprochee) {
    const core::Vector2 a{0.1f + 0.2f, 1.0f};
    EXPECT_EQ(a, core::Vector2(0.3f, 1.0f));
    EXPECT_NE(core::Vector2(0.0f, 0.0f), core::Vector2(1.0f, 0.0f));
}
