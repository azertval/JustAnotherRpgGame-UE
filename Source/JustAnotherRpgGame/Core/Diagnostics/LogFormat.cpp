// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Diagnostics/LogFormat.h"

#include <array>
#include <ctime>

namespace core {

std::string_view fileName(std::string_view path) {
    // Conserve la portion après le dernier séparateur de chemin (Windows ou POSIX).
    const std::size_t separator = path.find_last_of("/\\");
    if (separator == std::string_view::npos) {
        return path;
    }
    return path.substr(separator + 1);
}

// Compose une ligne de journalisation.
// Ligne de la forme "[timestamp][NIVEAU][catégorie][fichier:ligne] message".
std::string formatLogLine(std::string_view timestamp, LogLevel level, std::string_view category,
                          std::string_view file, int line, std::string_view message) {
    const std::string_view name = fileName(file);

    std::string result;
    result.reserve(timestamp.size() + category.size() + name.size() + message.size() + 32);
    result += '[';
    result += timestamp;
    result += "][";
    result += toString(level);
    result += "][";
    result += category;
    result += "][";
    result += name;
    result += ':';
    result += std::to_string(line);
    result += "] ";
    result += message;
    return result;
}

// Horodatage courant local, au format "HH:MM:SS".
// La chaîne d'horodatage.
std::string currentTimestamp() {
    const std::time_t now = std::time(nullptr);
    std::tm localTime{};
#ifdef _WIN32
    localtime_s(&localTime, &now);
#else
    localtime_r(&now, &localTime);
#endif
    std::array<char, 16> buffer{};
    std::strftime(buffer.data(), buffer.size(), "%H:%M:%S", &localTime);
    return buffer.data();
}

}  // namespace core
