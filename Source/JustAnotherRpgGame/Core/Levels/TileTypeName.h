// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Levels/TileTypeName.h
 * @brief Correspondance entre `core::TileType` et son nom textuel (`EX-LVL-003`).
 */

#include <optional>
#include <string>
#include <string_view>

#include "Core/Levels/TileType.h"

namespace core {

/**
 * @brief Convertit un type de tuile en son nom textuel.
 *
 * Point unique de vérité de la correspondance type ↔ nom, partagé par le format de niveau
 * (`core::LevelWriter`, `core::LevelLoader`) et par les messages qui nomment un type de tuile.
 * Deux tables distinctes divergeraient au premier type ajouté : un niveau écrit avec un nom qu'un
 * autre lecteur ne reconnaîtrait pas.
 *
 * Le `switch` est **exhaustif et sans `default`** : ajouter une valeur à `core::TileType` sans
 * lui donner de nom devient une erreur de compilation (`/W4 /WX`), et non un nom silencieusement
 * faux.
 * @param type Type de tuile.
 * @return Le nom textuel du type (`"solid"`, `"slopeUpRight"`…).
 */
[[nodiscard]] std::string tileTypeName(TileType type);

/**
 * @brief Convertit un nom textuel en type de tuile.
 *
 * Inverse exact de `core::tileTypeName` : tout nom qu'il produit est accepté ici, et
 * réciproquement (propriété vérifiée par test sur les trente types).
 * @param name Nom textuel, tel qu'écrit dans un fichier.
 * @return Le type correspondant, ou `std::nullopt` si le nom est inconnu — un nom inconnu est une
 *         donnée invalide à signaler, jamais un type deviné.
 */
[[nodiscard]] std::optional<TileType> parseTileType(std::string_view name);

}  // namespace core
