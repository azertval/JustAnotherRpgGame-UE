// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_assert.cpp
 * @brief Tests unitaires des assertions du projet.
 */

#include <string>

#include <gtest/gtest.h>

#include "Core/Diagnostics/Assert.h"

/**
 * @brief Une condition vraie n'invoque pas le gestionnaire d'assertion.
 * \castest{<b>Une condition vraie n'invoque pas le gestionnaire d'assertion.</b><br/>
 * \tcat Unitaire · Assert<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Une condition vraie n'invoque pas le gestionnaire d'assertion.
 * }
 */
TEST(AssertTest, ConditionVraieNInvoquePasLeHandler) {
    bool invoked = false;
    core::setAssertionHandler([&](const char*, const char*, const char*, int) { invoked = true; });

    // Condition évaluée à l'exécution (évite l'avertissement de condition constante).
    // [[maybe_unused]] : en Release l'assertion est un no-op, la variable n'est pas lue.
    [[maybe_unused]] volatile bool condition = true;
    JADG_ASSERT(condition, "ne doit pas echouer");

    EXPECT_FALSE(invoked);
    core::setAssertionHandler(nullptr);
}

/**
 * @brief Une condition fausse invoque le gestionnaire une fois, avec le message (Debug uniquement).
 * \castest{<b>Une condition fausse invoque le gestionnaire une fois, avec le message (Debug
 * uniquement).</b><br/>
 * \tcat Unitaire · Assert<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Une condition fausse invoque le gestionnaire une fois, avec le message (Debug
 * uniquement).
 * }
 */
TEST(AssertTest, ConditionFausseInvoqueLeHandler) {
#ifdef NDEBUG
    GTEST_SKIP() << "Assertions desactivees en Release";
#else
    int count = 0;
    std::string capturedMessage;
    core::setAssertionHandler([&](const char*, const char* message, const char*, int) {
        ++count;
        capturedMessage = message;
    });

    // Condition évaluée à l'exécution (évite l'avertissement de condition constante).
    volatile bool condition = false;
    JADG_ASSERT(condition, "echec attendu");

    EXPECT_EQ(count, 1);
    EXPECT_EQ(capturedMessage, "echec attendu");
    core::setAssertionHandler(nullptr);
#endif
}
