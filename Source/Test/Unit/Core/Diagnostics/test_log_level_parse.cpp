// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_log_level_parse.cpp
 * @brief Tests unitaires de l'analyse d'un niveau de log depuis une chaîne.
 */

#include <gtest/gtest.h>

#include "Core/Diagnostics/LogLevelParse.h"

/**
 * @brief Les noms de niveaux reconnus sont convertis (y compris l'alias « warn »).
 * \castest{<b>Les noms de niveaux reconnus sont convertis (y compris l'alias « warn »).</b><br/>
 * \tcat Unitaire · Log Level Parse<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Les noms de niveaux reconnus sont convertis (y compris l'alias « warn »).
 * }
 */
TEST(LogLevelParseTest, NiveauxReconnus) {
    EXPECT_EQ(core::parseLogLevel("trace"), core::LogLevel::Trace);
    EXPECT_EQ(core::parseLogLevel("info"), core::LogLevel::Info);
    EXPECT_EQ(core::parseLogLevel("warning"), core::LogLevel::Warning);
    EXPECT_EQ(core::parseLogLevel("warn"), core::LogLevel::Warning);
    EXPECT_EQ(core::parseLogLevel("error"), core::LogLevel::Error);
}

/**
 * @brief L'analyse est insensible à la casse.
 * \castest{<b>L'analyse est insensible à la casse.</b><br/>
 * \tcat Unitaire · Log Level Parse<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu L'analyse est insensible à la casse.
 * }
 */
TEST(LogLevelParseTest, InsensibleALaCasse) {
    EXPECT_EQ(core::parseLogLevel("INFO"), core::LogLevel::Info);
    EXPECT_EQ(core::parseLogLevel("Warning"), core::LogLevel::Warning);
    EXPECT_EQ(core::parseLogLevel("Error"), core::LogLevel::Error);
}

/**
 * @brief Une valeur inconnue ou vide n'est pas convertie.
 * \castest{<b>Une valeur inconnue ou vide n'est pas convertie.</b><br/>
 * \tcat Unitaire · Log Level Parse<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Une valeur inconnue ou vide n'est pas convertie.
 * }
 */
TEST(LogLevelParseTest, ValeurInconnue) {
    EXPECT_FALSE(core::parseLogLevel("verbose").has_value());
    EXPECT_FALSE(core::parseLogLevel("").has_value());
}
