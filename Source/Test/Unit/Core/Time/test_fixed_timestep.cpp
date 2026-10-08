// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_fixed_timestep.cpp
 * @brief Tests unitaires du cadenceur à pas de temps fixe.
 */

#include <gtest/gtest.h>

#include "Core/Time/FixedTimestep.h"

namespace {
constexpr float STEP = 1.0f / 60.0f;
}

/**
 * @brief Un temps écoulé égal au pas fixe produit exactement un pas.
 * \castest{<b>Un temps écoulé égal au pas fixe produit exactement un pas.</b><br/>
 * \tcat Unitaire · Fixed Timestep<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un temps écoulé égal au pas fixe produit exactement un pas.
 * }
 */
TEST(FixedTimestepTest, UnPasExact) {
    core::FixedTimestep timestep(STEP);
    EXPECT_EQ(timestep.advance(STEP), 1);
}

/**
 * @brief Un temps écoulé inférieur au pas ne produit aucun pas.
 * \castest{<b>Un temps écoulé inférieur au pas ne produit aucun pas.</b><br/>
 * \tcat Unitaire · Fixed Timestep<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un temps écoulé inférieur au pas ne produit aucun pas.
 * }
 */
TEST(FixedTimestepTest, TempsInsuffisant) {
    core::FixedTimestep timestep(STEP);
    EXPECT_EQ(timestep.advance(STEP * 0.5f), 0);
}

/**
 * @brief Un temps écoulé nul ou négatif ne produit aucun pas.
 * \castest{<b>Un temps écoulé nul ou négatif ne produit aucun pas.</b><br/>
 * \tcat Unitaire · Fixed Timestep<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un temps écoulé nul ou négatif ne produit aucun pas.
 * }
 */
TEST(FixedTimestepTest, TempsNulOuNegatif) {
    core::FixedTimestep timestep(STEP);
    EXPECT_EQ(timestep.advance(0.0f), 0);
    EXPECT_EQ(timestep.advance(-1.0f), 0);
}

/**
 * @brief 2,5 pas donnent 2 pas, et le reste (0,5 pas) est conservé puis complété.
 * \castest{<b>2,5 pas donnent 2 pas, et le reste (0,5 pas) est conservé puis complété.</b><br/>
 * \tcat Unitaire · Fixed Timestep<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu 2,5 pas donnent 2 pas, et le reste (0,5 pas) est conservé puis complété.
 * }
 */
TEST(FixedTimestepTest, ResteConserve) {
    core::FixedTimestep timestep(STEP);
    EXPECT_EQ(timestep.advance(STEP * 2.5f), 2);
    // Le reste vaut 0,5 pas : l'interpolation doit refléter cette fraction.
    EXPECT_NEAR(timestep.interpolationAlpha(), 0.5f, 1e-4f);
    // Un apport supplémentaire qui, cumulé au reste conservé, dépasse un pas
    // complet déclenche exactement un pas de plus (le reste n'a pas été perdu).
    EXPECT_EQ(timestep.advance(STEP * 0.6f), 1);
}

/**
 * @brief Un temps écoulé énorme est plafonné (anti-spirale de la mort).
 * \castest{<b>Un temps écoulé énorme est plafonné (anti-spirale de la mort).</b><br/>
 * \tcat Unitaire · Fixed Timestep<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un temps écoulé énorme est plafonné (anti-spirale de la mort).
 * }
 */
TEST(FixedTimestepTest, PlafondAntiSpirale) {
    const int maximum = 5;
    core::FixedTimestep timestep(STEP, maximum);
    EXPECT_EQ(timestep.advance(STEP * 1000.0f), maximum);
    // Le retard a été abandonné : l'appel suivant repart de zéro.
    EXPECT_EQ(timestep.advance(0.0f), 0);
}

/**
 * @brief Le pas fixe exposé correspond à la configuration.
 * \castest{<b>Le pas fixe exposé correspond à la configuration.</b><br/>
 * \tcat Unitaire · Fixed Timestep<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Le pas fixe exposé correspond à la configuration.
 * }
 */
TEST(FixedTimestepTest, PasFixeExpose) {
    core::FixedTimestep timestep(STEP);
    EXPECT_NEAR(timestep.fixedDeltaSeconds(), STEP, 1e-6f);
}

/**
 * @brief Ne pas appeler advance() pendant une pause n'accumule rien : le
 *        cadenceur n'a aucune horloge propre, seuls ses appels comptent -- une pause de durée
 *        réelle arbitraire, simulée en n'appelant simplement pas advance(), suivie d'un appel
 *        avec un petit delta (l'horloge de référence réarmée à la reprise, EX-GP-041) ne rend
 *        qu'un seul pas, jamais une rafale de rattrapage.
 * \castest{<b>Une pause simulée (aucun appel à advance()) n'accumule aucun pas.</b><br/>
 * \tcat Unitaire · Fixed Timestep<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Avancer normalement de quelques pas.<br/>2. Simuler une pause de longue durée en
 * n'appelant PAS advance() (aucun appel, pas un appel à zéro).<br/>3. Reprendre avec un petit
 * delta, comme après réarmement de l'horloge de référence.<br/>
 * \tattendu Le pas suivant la « pause » ne rend qu'un seul pas, jamais une rafale.
 * }
 */
TEST(FixedTimestepTest, PauseSansAppelNAccumuleAucunPas) {
    core::FixedTimestep timestep(STEP);
    EXPECT_EQ(timestep.advance(STEP * 3.0f), 3);

    // « Pause » : aucun appel à advance() ici, quelle que soit la durée réelle qu'elle
    // représenterait -- c'est l'absence d'appel qui est le test.

    // Reprise : l'appelant réarme son horloge de référence avant le prochain appel, donc le delta
    // suivant est petit -- pas la durée totale de la pause.
    EXPECT_EQ(timestep.advance(STEP), 1);
}
