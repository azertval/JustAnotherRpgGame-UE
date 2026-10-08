// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_log_format.cpp
 * @brief Tests unitaires du formatage des lignes de log.
 */

#include <string>

#include <gtest/gtest.h>

#include "Core/Diagnostics/LogFormat.h"

/**
 * @brief La ligne formatée contient horodatage, niveau, catégorie, position source et message.
 * \castest{<b>La ligne formatée contient horodatage, niveau, catégorie, position source et
 * message.</b><br/>
 * \tcat Unitaire · Log Format<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu La ligne formatée contient horodatage, niveau, catégorie, position source et message.
 * }
 */
TEST(LogFormatTest, LigneContientTousLesChamps) {
    // L'horodatage est injecté pour rendre le test déterministe.
    const std::string line = core::formatLogLine("12:34:56", core::LogLevel::Warning, "HMI",
                                                 "Foo.cpp", 42, "message test");

    EXPECT_NE(line.find("12:34:56"), std::string::npos);
    EXPECT_NE(line.find("WARNING"), std::string::npos);
    EXPECT_NE(line.find("HMI"), std::string::npos);
    EXPECT_NE(line.find("Foo.cpp:42"), std::string::npos);
    EXPECT_NE(line.find("message test"), std::string::npos);
}

/**
 * @brief Le chemin source est réduit à son nom de fichier dans la ligne.
 * \castest{<b>Le chemin source est réduit à son nom de fichier dans la ligne.</b><br/>
 * \tcat Unitaire · Log Format<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Le chemin source est réduit à son nom de fichier dans la ligne.
 * }
 */
TEST(LogFormatTest, CheminReduitAuNomDeFichier) {
    const std::string line =
        core::formatLogLine("00:00:00", core::LogLevel::Info, "Core",
                            "D:\\JustAnotherRpgGame\\Source\\Core\\Foo.cpp", 7, "x");

    EXPECT_NE(line.find("Foo.cpp:7"), std::string::npos);
    EXPECT_EQ(line.find("JustAnotherRpgGame"), std::string::npos);
    EXPECT_EQ(line.find("Source"), std::string::npos);
}

/**
 * @brief fileName isole le nom de fichier des chemins Windows et POSIX, ou renvoie l'entrée.
 * \castest{<b>fileName isole le nom de fichier des chemins Windows et POSIX, ou renvoie
 * l'entrée.</b><br/>
 * \tcat Unitaire · Log Format<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu fileName isole le nom de fichier des chemins Windows et POSIX, ou renvoie l'entrée.
 * }
 */
TEST(LogFormatTest, FileNameIsoleLeNom) {
    EXPECT_EQ(core::fileName("a/b/c/File.cpp"), "File.cpp");
    EXPECT_EQ(core::fileName("a\\b\\File.cpp"), "File.cpp");
    EXPECT_EQ(core::fileName("File.cpp"), "File.cpp");
}

/**
 * @brief L'horodatage courant respecte le format HH:MM:SS (longueur 8).
 * \castest{<b>L'horodatage courant respecte le format HH:MM:SS (longueur 8).</b><br/>
 * \tcat Unitaire · Log Format<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu L'horodatage courant respecte le format HH:MM:SS (longueur 8).
 * }
 */
TEST(LogFormatTest, HorodatageFormatHeure) {
    const std::string timestamp = core::currentTimestamp();
    EXPECT_EQ(timestamp.size(), 8u);
    EXPECT_EQ(timestamp[2], ':');
    EXPECT_EQ(timestamp[5], ':');
}
