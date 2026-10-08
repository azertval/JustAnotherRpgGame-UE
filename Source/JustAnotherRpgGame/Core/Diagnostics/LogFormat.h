// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <string>
#include <string_view>

#include "Core/Diagnostics/LogLevel.h"

/**
 * @file Core/Diagnostics/LogFormat.h
 * @brief Formatage des lignes de journalisation.
 */

namespace core {

/**
 * @brief Réduit un chemin source à son seul nom de fichier.
 * @param path Chemin complet (tel que fourni par `__FILE__`).
 * @return La portion après le dernier séparateur, ou le chemin entier s'il n'y en a pas.
 */
[[nodiscard]] std::string_view fileName(std::string_view path);

/**
 * @brief Compose une ligne de journalisation.
 * @param timestamp Horodatage déjà formaté (injecté, pour rester testable).
 * @param level     Niveau du message.
 * @param category  Catégorie / sous-système émetteur (ex. "HMI").
 * @param file      Fichier source (le nom seul est conservé dans la ligne).
 * @param line      Ligne source à l'origine du message.
 * @param message   Texte du message.
 * @return Ligne de la forme "[timestamp][NIVEAU][catégorie][fichier:ligne] message".
 */
[[nodiscard]] std::string formatLogLine(std::string_view timestamp, LogLevel level,
                                        std::string_view category, std::string_view file, int line,
                                        std::string_view message);

/**
 * @brief Horodatage courant local, au format "HH:MM:SS".
 * @return La chaîne d'horodatage.
 */
[[nodiscard]] std::string currentTimestamp();

}  // namespace core
