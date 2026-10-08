// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <filesystem>
#include <fstream>
#include <string_view>

#include "Core/Diagnostics/ILogSink.h"
#include "Core/Diagnostics/LogLevel.h"

/**
 * @file Core/Diagnostics/FileLogSink.h
 * @brief Sink écrivant les messages dans un fichier, avec flush immédiat.
 */

namespace core {

/**
 * @brief Sink qui écrit chaque message dans un fichier, ligne par ligne.
 *
 * Flush immédiat à chaque message (comme `ConsoleLogSink`) : un arrêt brutal du processus
 * (crash, `std::abort()` déclenché par `JADG_ASSERT`) ne perd pas les dernières lignes
 * écrites avant l'incident — c'est la raison d'être principale de ce sink par rapport à
 * `MemoryLogSink` (perdu à la fermeture) ou à un export manuel.
 */
class FileLogSink : public ILogSink {
public:
    /**
     * @brief Ouvre (ou crée) le fichier de destination en écriture.
     * @param path   Chemin du fichier ; les dossiers parents sont créés au besoin.
     * @param append Si vrai, ajoute à la suite d'un fichier existant plutôt que de l'écraser.
     */
    explicit FileLogSink(const std::filesystem::path& path, bool append = false);

    void write(LogLevel level, std::string_view message) override;

    /// @return true si le fichier a pu être ouvert (sinon, `write()` est un no-op silencieux :
    /// journaliser ne doit jamais faire échouer l'appelant).
    [[nodiscard]] bool isOpen() const;

private:
    std::ofstream _stream;
};

}  // namespace core
