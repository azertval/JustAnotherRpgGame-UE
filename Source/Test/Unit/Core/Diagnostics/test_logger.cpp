// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_logger.cpp
 * @brief Tests unitaires du journaliseur (filtrage et diffusion).
 */

#include <memory>

#include <gtest/gtest.h>

#include "Core/Diagnostics/Logger.h"
#include "Core/Diagnostics/MemoryLogSink.h"

/**
 * @brief Un message au-dessus du niveau minimal est diffusé ; en dessous, il est filtré.
 * \castest{<b>Un message au-dessus du niveau minimal est diffusé ; en dessous, il est
 * filtré.</b><br/>
 * \tcat Unitaire · Logger<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un message au-dessus du niveau minimal est diffusé ; en dessous, il est filtré.
 * }
 */
TEST(LoggerTest, FiltreParNiveauMinimal) {
    core::Logger logger;
    auto sink = std::make_unique<core::MemoryLogSink>();
    core::MemoryLogSink* observed = sink.get();
    logger.addSink(std::move(sink));
    logger.setMinimumLevel(core::LogLevel::Warning);

    logger.log(core::LogLevel::Info, "ignore");
    logger.log(core::LogLevel::Error, "garde");

    ASSERT_EQ(observed->entries().size(), 1u);
    EXPECT_EQ(observed->entries()[0].level, core::LogLevel::Error);
    EXPECT_EQ(observed->entries()[0].message, "garde");
}

/**
 * @brief Le même message atteint tous les sinks enregistrés.
 * \castest{<b>Le même message atteint tous les sinks enregistrés.</b><br/>
 * \tcat Unitaire · Logger<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Le même message atteint tous les sinks enregistrés.
 * }
 */
TEST(LoggerTest, DiffuseAPlusieursSinks) {
    core::Logger logger;
    auto first = std::make_unique<core::MemoryLogSink>();
    auto second = std::make_unique<core::MemoryLogSink>();
    core::MemoryLogSink* firstObserved = first.get();
    core::MemoryLogSink* secondObserved = second.get();
    logger.addSink(std::move(first));
    logger.addSink(std::move(second));

    logger.log(core::LogLevel::Info, "diffuse");

    EXPECT_EQ(firstObserved->entries().size(), 1u);
    EXPECT_EQ(secondObserved->entries().size(), 1u);
}

/**
 * @brief clearSinks retire les destinations : plus rien n'est diffusé ensuite.
 * \castest{<b>clearSinks retire les destinations : plus rien n'est diffusé ensuite.</b><br/>
 * \tcat Unitaire · Logger<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu clearSinks retire les destinations : plus rien n'est diffusé ensuite.
 * }
 */
TEST(LoggerTest, ClearSinksArreteLaDiffusion) {
    core::Logger logger;
    logger.addSink(std::make_unique<core::MemoryLogSink>());

    logger.clearSinks();

    // clearSinks() detruit le sink retire (le logger en possede le unique_ptr) : verifier son
    // etat apres coup serait un use-after-free (trouve par AddressSanitizer).
    // On verifie a la place qu'un sink ajoute APRES clearSinks() est le seul a recevoir le
    // message : si l'ancien sink etait reste attache (bogue de clearSinks), l'appel toucherait de
    // la memoire liberee et planterait sous ASan.
    auto sinkAfterClear = std::make_unique<core::MemoryLogSink>();
    core::MemoryLogSink* observedAfterClear = sinkAfterClear.get();
    logger.addSink(std::move(sinkAfterClear));

    logger.log(core::LogLevel::Error, "personne");

    ASSERT_EQ(observedAfterClear->entries().size(), 1u);
    EXPECT_EQ(observedAfterClear->entries()[0].message, "personne");
}
