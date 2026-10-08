// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <string>
#include <string_view>
#include <vector>

#include "Core/Levels/GridPosition.h"

namespace core {
class Level;
}

/**
 * @file Core/World/CityBlock.h
 * @brief L'**îlot** d'un quartier : un rectangle nommé de sa carte, que le plan de la ville montre
 *        (`LOT-96`).
 *
 * Le plan descend de la ville au quartier, puis à l'îlot. L'îlot n'a pas d'image à lui (*décision
 * de l'auteur*, 18 septembre 2026) : l'écran « Carte » montre la carte du quartier telle que le jeu
 * la dessine, cadrée sur ce rectangle. Il se déclare donc **sur la carte**, comme la zone de
 * combat (`core::CombatZone`) : une entité dont la case est le coin haut-gauche et dont les
 * propriétés donnent le nom et la taille. L'éditeur le pose et le déplace avec la carte ; aucun
 * fichier à part ne peut diverger du terrain.
 */

namespace core {

/// @brief Type d'entité d'un îlot.
inline constexpr std::string_view CITY_BLOCK_ENTITY_TYPE = "cityBlock";
/// @brief Propriété d'un îlot : son nom, qui est aussi la clé de son libellé (`city_block.<nom>`).
inline constexpr std::string_view CITY_BLOCK_NAME_PROPERTY = "name";
/// @brief Propriété d'un îlot : sa largeur, en cases.
inline constexpr std::string_view CITY_BLOCK_WIDTH_PROPERTY = "width";
/// @brief Propriété d'un îlot : sa hauteur, en cases.
inline constexpr std::string_view CITY_BLOCK_HEIGHT_PROPERTY = "height";

/// @brief Un îlot : un nom, et un rectangle de cases.
struct CityBlock {
    std::string name;
    GridPosition origin{};
    int columns = 0;
    int rows = 0;

    /// @return Vrai si @p cell est dans l'îlot.
    [[nodiscard]] bool contains(GridPosition cell) const noexcept;

    [[nodiscard]] bool operator==(const CityBlock&) const = default;
};

/**
 * @return Les îlots de @p level, dans l'ordre des entités. Un îlot sans nom ou de taille nulle est
 *         une saisie fautive : il est écarté plutôt que montré vide.
 */
[[nodiscard]] std::vector<CityBlock> cityBlocksOf(const Level& level);

}  // namespace core
