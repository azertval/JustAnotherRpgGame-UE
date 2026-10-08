// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Rpg/Scale.h
 * @brief L'échelle du monde : une case vaut 1,5 mètre. Seule source de vérité.
 */

namespace core {

/**
 * @brief Côté d'une case de la grille tactique, en mètres.
 *
 * **Décision de cadrage, figée ici et nulle part ailleurs.** Toutes les portées et vitesses du
 * corpus sont exprimées en mètres — « allonge 1,50 m », « vitesse 9 m », « portée 6 m/18 m » — et
 * la grille tactique du `LOT-19` compte en cases. La conversion se fait donc *quelque part*, et le
 * seul choix ouvert est : à un endroit, ou à trente.
 *
 * À trente endroits, il suffit qu'un seul emploie 1,5 quand un autre emploie 1,52 (les cinq pieds
 * d'origine) pour qu'une portée de six cases devienne cinq à un endroit du jeu et six ailleurs —
 * et c'est le genre d'écart qu'on ne diagnostique qu'après l'avoir cherché longtemps.
 *
 * Consommée par les `LOT-19` (déplacement) et `LOT-22` (portée, ligne de vue, zones d'effet).
 */
inline constexpr float METERS_PER_TILE = 1.5f;

/// @brief Convertit une distance en mètres — telle que le corpus l'écrit — en nombre de cases.
[[nodiscard]] constexpr float tilesFromMeters(float meters) noexcept {
    return meters / METERS_PER_TILE;
}

/// @brief Convertit un nombre de cases en mètres, pour l'affichage et les infobulles.
[[nodiscard]] constexpr float metersFromTiles(float tiles) noexcept {
    return tiles * METERS_PER_TILE;
}

}  // namespace core
