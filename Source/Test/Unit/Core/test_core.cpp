// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_core.cpp
 * @brief Tests unitaires de la bibliothèque Core (amorçage).
 */

#include <gtest/gtest.h>

#include "Core/Core.h"

/**
 * @brief Vérifie que la version du moteur n'est pas vide.
 * \castest{<b>Vérifie que la version du moteur n'est pas vide.</b><br/>
 * \tcat Unitaire · Engine<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Vérifie que la version du moteur n'est pas vide.
 * }
 */
TEST(EngineTest, VersionNonVide) {
    const core::Engine engine;
    EXPECT_FALSE(engine.version().empty());
}
