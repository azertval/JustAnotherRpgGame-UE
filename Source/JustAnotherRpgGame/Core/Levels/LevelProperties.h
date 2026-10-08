// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <cstdint>
#include <map>
#include <string>
#include <variant>

/**
 * @file Core/Levels/LevelProperties.h
 * @brief Propriétés libres d'une couche ou d'une entité de carte.
 */

namespace core {

/**
 * @brief Valeur d'une propriété libre : booléen, entier, réel ou chaîne.
 *
 * Volontairement **un type de `Core`**, jamais un `nlohmann::json` : `Core` ne connaît pas le
 * format de fichier (`EX-ARCH-001`), et la bibliothèque JSON lui est liée en `PRIVATE` — l'exposer
 * dans un en-tête la propagerait à tous ses consommateurs.
 */
using PropertyValue = std::variant<bool, std::int64_t, double, std::string>;

/**
 * @brief Propriétés libres, indexées par nom.
 *
 * **C'est le mécanisme qui évite un `version: 4`.** Un besoin découvert plus tard — terrain
 * difficile, couverture, hauteur, dialogue d'un PNJ — s'exprime comme une propriété, jamais comme
 * un nouveau champ du format. Le chargeur y range en outre **toute clé qu'il ne reconnaît pas**,
 * et l'écrivain les réémet : un fichier produit par une version ultérieure de l'éditeur traverse
 * donc une version antérieure sans rien perdre.
 *
 * `std::map` (ordonné) et non `unordered_map` : l'écriture doit être **déterministe**, faute de
 * quoi deux enregistrements du même niveau produiraient des fichiers différents et pollueraient
 * chaque diff.
 *
 * @note Limite assumée : une valeur **composite** (objet ou tableau JSON) ne rentre pas dans
 *       `PropertyValue` et n'est donc pas préservée. Le format n'en produit aucune aujourd'hui ;
 *       le jour où il en faudra une, ce sera un champ à part entière, pas une propriété libre.
 */
using PropertyMap = std::map<std::string, PropertyValue>;

}  // namespace core
