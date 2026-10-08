// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_file_log_sink.cpp
 * @brief Tests unitaires de `core::FileLogSink`.
 */

#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <system_error>

#include <gtest/gtest.h>

#include "Core/Diagnostics/FileLogSink.h"

namespace {

// Fournit un dossier temporaire vierge par test (créé/supprimé automatiquement).
class FileLogSinkTest : public ::testing::Test {
protected:
    std::filesystem::path dir;

    void SetUp() override {
        dir = std::filesystem::temp_directory_path() /
              ("pg_filelogsink_" + std::to_string(reinterpret_cast<std::uintptr_t>(this)));
        std::filesystem::create_directories(dir);
    }
    void TearDown() override {
        std::error_code error;
        std::filesystem::remove_all(dir, error);
    }

    [[nodiscard]] std::string readFile(const std::filesystem::path& path) const {
        std::ifstream stream(path);
        std::ostringstream buffer;
        buffer << stream.rdbuf();
        return buffer.str();
    }
};

}  // namespace

/**
 * @brief Écrire un message via `FileLogSink::write` le persiste immédiatement dans le fichier,
 * lisible sans fermer le sink au préalable (flush immédiat).
 * \castest{<b>FileLogSink : écriture persistée immédiatement (flush).</b><br/>
 * \tcat Unitaire · Diagnostics<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Construire un `FileLogSink` sur un chemin dans un dossier temporaire.<br/>2. Écrire
 * un message.<br/>3. Relire le fichier sans détruire le sink.<br/>
 * \tattendu Le fichier contient le message écrit.}
 */
TEST_F(FileLogSinkTest, EcritureEstPersisteeImmediatement) {
    const std::filesystem::path path = dir / "session.log";
    core::FileLogSink sink(path);

    ASSERT_TRUE(sink.isOpen());
    sink.write(core::LogLevel::Info, "message de test");

    const std::string content = readFile(path);
    EXPECT_NE(content.find("message de test"), std::string::npos);
}

/**
 * @brief Plusieurs messages écrits successivement apparaissent dans le fichier, une ligne
 * chacun, dans l'ordre d'écriture.
 * \castest{<b>FileLogSink : plusieurs messages, une ligne chacun, ordre préservé.</b><br/>
 * \tcat Unitaire · Diagnostics<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Construire un `FileLogSink`.<br/>2. Écrire trois messages successifs.<br/>3. Relire
 * le fichier.<br/>
 * \tattendu Trois lignes, dans l'ordre d'écriture.}
 */
TEST_F(FileLogSinkTest, MessagesSuccessifsUneLigneChacunOrdrePreserve) {
    const std::filesystem::path path = dir / "session.log";
    core::FileLogSink sink(path);

    sink.write(core::LogLevel::Info, "premier");
    sink.write(core::LogLevel::Warning, "deuxieme");
    sink.write(core::LogLevel::Error, "troisieme");

    std::ifstream stream(path);
    std::string line;
    ASSERT_TRUE(std::getline(stream, line));
    EXPECT_EQ(line, "premier");
    ASSERT_TRUE(std::getline(stream, line));
    EXPECT_EQ(line, "deuxieme");
    ASSERT_TRUE(std::getline(stream, line));
    EXPECT_EQ(line, "troisieme");
}

/**
 * @brief Construire un `FileLogSink` sur un chemin dont les dossiers parents n'existent pas
 * encore les crée, plutôt que d'échouer.
 * \castest{<b>FileLogSink : crée les dossiers parents manquants.</b><br/>
 * \tcat Unitaire · Diagnostics<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Construire un `FileLogSink` sur `dir/sous/dossier/session.log` (dossiers
 * inexistants).<br/>2. Écrire un message.<br/>
 * \tattendu Le sink s'ouvre correctement et le fichier contient le message.}
 */
TEST_F(FileLogSinkTest, CreeLesDossiersParentsManquants) {
    const std::filesystem::path path = dir / "sous" / "dossier" / "session.log";
    core::FileLogSink sink(path);

    ASSERT_TRUE(sink.isOpen());
    sink.write(core::LogLevel::Info, "message");

    EXPECT_TRUE(std::filesystem::exists(path));
    EXPECT_NE(readFile(path).find("message"), std::string::npos);
}

/**
 * @brief Par défaut, construire un `FileLogSink` sur un fichier déjà existant l'écrase (pas
 * d'ajout à la suite) ; avec `append = true`, il complète le fichier existant.
 * \castest{<b>FileLogSink : écrase par défaut, complète avec `append = true`.</b><br/>
 * \tcat Unitaire · Diagnostics<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Écrire un fichier avec un premier sink.<br/>2. Rouvrir sur le même chemin sans
 * `append`, puis avec `append = true`.<br/>
 * \tattendu Sans `append`, l'ancien contenu disparaît ; avec `append`, il est conservé et
 * complété.}
 */
TEST_F(FileLogSinkTest, EcraseParDefautCompleteAvecAppend) {
    const std::filesystem::path path = dir / "session.log";

    {
        core::FileLogSink first(path);
        first.write(core::LogLevel::Info, "premiere ouverture");
    }
    {
        core::FileLogSink truncated(path);
        truncated.write(core::LogLevel::Info, "seconde ouverture");
    }
    const std::string afterTruncate = readFile(path);
    EXPECT_EQ(afterTruncate.find("premiere ouverture"), std::string::npos);
    EXPECT_NE(afterTruncate.find("seconde ouverture"), std::string::npos);

    {
        core::FileLogSink appended(path, /*append=*/true);
        appended.write(core::LogLevel::Info, "troisieme ouverture");
    }
    const std::string afterAppend = readFile(path);
    EXPECT_NE(afterAppend.find("seconde ouverture"), std::string::npos);
    EXPECT_NE(afterAppend.find("troisieme ouverture"), std::string::npos);
}

/**
 * @brief Un chemin impossible à ouvrir (dossier parent qui ne peut pas être créé) laisse le sink
 * fermé (`isOpen() == false`) sans lever d'exception ; `write()` devient alors un no-op silencieux
 * — journaliser ne doit jamais faire échouer l'appelant.
 * \castest{<b>FileLogSink : chemin invalide, sink fermé, write() silencieux.</b><br/>
 * \tcat Unitaire · Diagnostics<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Construire un `FileLogSink` dont un segment du chemin est en réalité un
 * fichier existant (impossible à traverser comme dossier).<br/>2. Appeler `write()`.<br/>
 * \tattendu `isOpen() == false` ; `write()` ne lève rien et ne crée aucun fichier.}
 */
TEST_F(FileLogSinkTest, CheminInvalideSinkFermeEtWriteSilencieux) {
    const std::filesystem::path blockingFile = dir / "pas_un_dossier";
    {
        std::ofstream blocker(blockingFile);
        blocker << "je suis un fichier, pas un dossier";
    }
    const std::filesystem::path impossiblePath = blockingFile / "session.log";

    core::FileLogSink sink(impossiblePath);

    EXPECT_FALSE(sink.isOpen());
    EXPECT_NO_THROW(sink.write(core::LogLevel::Error, "ne doit rien faire"));
}
