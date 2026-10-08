// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Levels/GridPosition.h
 * @brief Position entière dans la grille d'un niveau (colonne, ligne).
 */

namespace core {

/**
 * @brief Position d'une case dans la grille d'un niveau, en **coordonnées entières**.
 *
 * Repère de la grille : origine **haut-gauche**, `column` vers la droite, `row` vers le bas
 * (convention du projet, `EX-ARCH-020`). Distincte de `Vector2` (flottant, unités monde) :
 * une `GridPosition` désigne une case, pas une position continue.
 */
struct GridPosition {
    int column = 0;
    int row = 0;
};

/// @return true si les deux positions désignent la même case.
[[nodiscard]] constexpr bool operator==(GridPosition left, GridPosition right) noexcept {
    return left.column == right.column && left.row == right.row;
}

/// @return true si les deux positions désignent des cases différentes.
[[nodiscard]] constexpr bool operator!=(GridPosition left, GridPosition right) noexcept {
    return !(left == right);
}

}  // namespace core
