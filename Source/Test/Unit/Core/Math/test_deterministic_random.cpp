// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_deterministic_random.cpp
 * @brief Tests unitaires de `core::DeterministicRandom`, `splitMix64` et `deriveSeed`
 * (`EX-NFR-002`).
 *
 * Ce fichier fige des **vecteurs de référence** : les valeurs attendues y sont écrites en dur,
 * calculées indépendamment de l'implémentation. C'est le seul moyen de détecter qu'une refonte a
 * silencieusement changé la suite produite — auquel cas toutes les séquences de particules déjà
 * observées changeraient sans qu'aucun autre test ne s'en aperçoive : elles resteraient
 * *reproductibles*, simplement plus les mêmes.
 */

#include <cstdint>

#include <gtest/gtest.h>

#include "Core/Math/DeterministicRandom.h"

/**
 * @brief `splitMix64` rend, pour des entrées de référence, exactement les valeurs attendues du
 * mélangeur SplitMix64.
 * \castest{<b>splitMix64 : vecteurs de référence.</b><br/>
 * \tcat Unitaire · Core Math<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. `splitMix64` sur `0`, `1` et `0x0123456789ABCDEF`.<br/>
 * \tattendu Les trois valeurs figées du mélangeur de référence ; `0` est un point fixe du
 * finaliseur.}
 */
TEST(DeterministicRandomTest, SplitMix64VecteursDeReference) {
    // Point fixe du finaliseur SplitMix64 : xor-shift et multiplications laissent zero inchange.
    // Consequence a connaitre, pas un defaut -- DeterministicRandom n'en souffre pas, il ajoute la
    // constante du nombre d'or a son etat AVANT de melanger.
    EXPECT_EQ(core::splitMix64(0x0000000000000000ULL), 0x0000000000000000ULL);
    EXPECT_EQ(core::splitMix64(0x0000000000000001ULL), 0x5692161D100B05E5ULL);
    EXPECT_EQ(core::splitMix64(0x0123456789ABCDEFULL), 0xB2C058E4EBB5112CULL);
}

/**
 * @brief `deriveSeed` rend des vecteurs de référence figés, et sépare les trois composantes du
 * triplet : changer le pas ou l'identité produit une graine différente.
 * \castest{<b>deriveSeed : vecteurs de référence et séparation du triplet.</b><br/>
 * \tcat Unitaire · Core Math<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. `deriveSeed` sur `(1,0,0)`, `(1,0,1)` et `(1,1,0)`.<br/>2. Comparer les trois entre
 * eux.<br/>
 * \tattendu Les trois valeurs figées, toutes distinctes : le pas et l'identifiant ne se
 * confondent pas.}
 */
TEST(DeterministicRandomTest, DeriveSeedVecteursDeReference) {
    EXPECT_EQ(core::deriveSeed(1, 0, 0), 0x71CAC37448049CE4ULL);
    EXPECT_EQ(core::deriveSeed(1, 0, 1), 0xC14BF009DE212E89ULL);
    EXPECT_EQ(core::deriveSeed(1, 1, 0), 0x98DCCAA31A8BAF69ULL);

    // Le pas et l'identifiant occupent des positions distinctes : les intervertir ne doit pas
    // rendre la meme graine, sans quoi deux entites d'un meme pas partageraient leurs tirages.
    EXPECT_NE(core::deriveSeed(1, 0, 1), core::deriveSeed(1, 1, 0));
}

/**
 * @brief La suite produite depuis une graine donnée est figée : cinq valeurs de référence.
 * \castest{<b>DeterministicRandom : suite de référence depuis une graine fixée.</b><br/>
 * \tcat Unitaire · Core Math<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. `DeterministicRandom(42)`.<br/>2. Cinq appels à `nextUInt32()`.<br/>
 * \tattendu Exactement les cinq valeurs figées, dans l'ordre.}
 */
TEST(DeterministicRandomTest, SuiteDeReferenceDepuisUneGraineFixee) {
    core::DeterministicRandom random(42);
    EXPECT_EQ(random.nextUInt32(), 0xBDD73226U);
    EXPECT_EQ(random.nextUInt32(), 0x28EFE333U);
    EXPECT_EQ(random.nextUInt32(), 0x47526757U);
    EXPECT_EQ(random.nextUInt32(), 0x581CE1FFU);
    EXPECT_EQ(random.nextUInt32(), 0x09BC585AU);
}

/**
 * @brief Deux instances de même graine produisent la même suite ; deux graines différentes
 * divergent dès le premier tirage.
 * \castest{<b>DeterministicRandom : même graine, même suite ; graines différentes,
 * suites différentes.</b><br/>
 * \tcat Unitaire · Core Math<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Deux instances de graine `7`, 16 tirages chacune.<br/>2. Une instance de graine
 * `8`, premier tirage.<br/>
 * \tattendu Les deux premières suites coïncident terme à terme ; la troisième diverge dès le
 * premier tirage.}
 */
TEST(DeterministicRandomTest, MemeGraineMemeSuite) {
    core::DeterministicRandom first(7);
    core::DeterministicRandom second(7);
    for (int draw = 0; draw < 16; ++draw) {
        EXPECT_EQ(first.nextUInt32(), second.nextUInt32()) << "tirage " << draw;
    }

    core::DeterministicRandom other(8);
    core::DeterministicRandom reference(7);
    EXPECT_NE(other.nextUInt32(), reference.nextUInt32());
}

/**
 * @brief `nextFloat01` reste dans `[0, 1[` sur un grand nombre de tirages, borne haute **exclue**.
 * \castest{<b>nextFloat01 : borne haute exclue.</b><br/>
 * \tcat Unitaire · Core Math<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. 10 000 tirages depuis une graine fixée.<br/>
 * \tattendu Toutes les valeurs sont dans `[0, 1[` ; `1.0f` n'est jamais atteint.}
 */
TEST(DeterministicRandomTest, NextFloat01ExclutLaBorneHaute) {
    core::DeterministicRandom random(1234);
    for (int draw = 0; draw < 10000; ++draw) {
        const float value = random.nextFloat01();
        ASSERT_GE(value, 0.0f) << "tirage " << draw;
        ASSERT_LT(value, 1.0f) << "tirage " << draw;
    }
}

/**
 * @brief `nextRange` reste dans `[min, max]`, et rend exactement `min` quand les deux bornes
 * coïncident — cas d'une durée de vie ou d'une vitesse fixe, où aucun tirage ne discrimine.
 * \castest{<b>nextRange : bornes respectées, intervalle dégénéré rendu exactement.</b><br/>
 * \tcat Unitaire · Core Math<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. 1 000 tirages dans `[-2, 5]`.<br/>2. Un tirage dans `[3, 3]`.<br/>
 * \tattendu Toutes les valeurs sont dans `[-2, 5]` ; l'intervalle dégénéré rend exactement `3`.}
 */
TEST(DeterministicRandomTest, NextRangeRespecteLesBornes) {
    core::DeterministicRandom random(99);
    for (int draw = 0; draw < 1000; ++draw) {
        const float value = random.nextRange(-2.0f, 5.0f);
        ASSERT_GE(value, -2.0f) << "tirage " << draw;
        ASSERT_LE(value, 5.0f) << "tirage " << draw;
    }

    // Intervalle degenere : min + t * 0 == min, quel que soit le tirage.
    EXPECT_FLOAT_EQ(random.nextRange(3.0f, 3.0f), 3.0f);
}
