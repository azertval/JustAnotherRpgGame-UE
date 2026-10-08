// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <filesystem>
#include <optional>
#include <string_view>

#include "Core/Levels/Level.h"

/**
 * @file Core/Levels/LevelVariant.h
 * @brief La **variante** d'une carte : la même carte, sous une autre planche et avec d'autres
 *        entités (`LOT-EDITOR-12`, décision D12, `EX-LVL-023`).
 *
 * L'Arène du Destin du `LOT-27` est le Colisée ; le plan pénombral du `LOT-90` est la même ville
 * sous une autre lumière. Recopier leurs cases ferait deux cartes à tenir d'accord à chaque
 * retouche. Une variante déclare donc sa `base`, sa planche (`scene`) et ses propres entités, et ne
 * porte **aucune case** : elle les reprend de sa base au chargement.
 */

namespace core {

/// @brief Propriété de couche qui nomme le lieu dont la carte porte les planches (`scene`).
inline constexpr std::string_view SCENE_LAYER_PROPERTY = "scene";

/**
 * @brief La carte que joue une variante : les cases, couches, collision et entrée de @p base, les
 *        entités et le nom de @p variant, et sa planche si elle en change.
 *
 * La carte rendue garde `base` et `scene` : l'écrivain la réécrit en variante, sans ses cases.
 * @param base    La carte de base, chargée.
 * @param variant Ce que le fichier de la variante déclare.
 */
[[nodiscard]] Level applyVariant(const Level& base, LevelData variant);

/**
 * @brief Cherche le fichier de la base @p baseId d'une variante rangée en @p variantPath.
 * @return `<dossier>/<baseId>.json` pour le premier dossier, de celui de la variante vers la
 *         racine, où ce fichier existe ; `std::nullopt` si aucun.
 */
[[nodiscard]] std::optional<std::filesystem::path> findVariantBase(
    const std::filesystem::path& variantPath, std::string_view baseId);

}  // namespace core
