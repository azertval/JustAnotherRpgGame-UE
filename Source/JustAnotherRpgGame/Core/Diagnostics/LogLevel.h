// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Diagnostics/LogLevel.h
 * @brief Niveaux de journalisation, par gravité croissante.
 */

namespace core {

/// Niveau d'un message de journalisation (ordre croissant de gravité).
enum class LogLevel {
    Trace,    ///< Détails fins de débogage.
    Info,     ///< Information de fonctionnement normal.
    Warning,  ///< Anomalie non bloquante.
    Error     ///< Erreur nécessitant attention.
};

/**
 * @brief Convertit un niveau en libellé lisible.
 * @param level Niveau à convertir.
 * @return Libellé constant ("TRACE", "INFO", "WARNING", "ERROR").
 */
[[nodiscard]] constexpr const char* toString(LogLevel level) {
    switch (level) {
        case LogLevel::Trace:
            return "TRACE";
        case LogLevel::Info:
            return "INFO";
        case LogLevel::Warning:
            return "WARNING";
        case LogLevel::Error:
            return "ERROR";
    }
    return "UNKNOWN";
}

}  // namespace core
