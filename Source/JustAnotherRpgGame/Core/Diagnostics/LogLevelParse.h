// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <cctype>
#include <optional>
#include <string>
#include <string_view>

#include "Core/Diagnostics/LogLevel.h"

/**
 * @file Core/Diagnostics/LogLevelParse.h
 * @brief Analyse d'un niveau de log depuis une chaîne (configuration au lancement).
 */

namespace core {

/**
 * @brief Convertit une chaîne en niveau de log (insensible à la casse).
 * @param text Nom du niveau : « trace », « info », « warning » (ou « warn »), « error ».
 * @return Le niveau correspondant, ou `std::nullopt` si la chaîne n'est pas reconnue.
 */
[[nodiscard]] inline std::optional<LogLevel> parseLogLevel(std::string_view text) {
    std::string lowered;
    lowered.reserve(text.size());
    for (const char character : text) {
        lowered.push_back(static_cast<char>(std::tolower(static_cast<unsigned char>(character))));
    }

    if (lowered == "trace") {
        return LogLevel::Trace;
    }
    if (lowered == "info") {
        return LogLevel::Info;
    }
    if (lowered == "warning" || lowered == "warn") {
        return LogLevel::Warning;
    }
    if (lowered == "error") {
        return LogLevel::Error;
    }
    return std::nullopt;
}

}  // namespace core
