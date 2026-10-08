// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <vector>

#include "Core/Levels/GridPosition.h"

/**
 * @file Core/Levels/PieceFootprint.h
 * @brief L'**emprise** d'une pièce posée sur une carte : les cases qu'elle occupe, et la case d'où
 *        elle se trie (`LOT-EDITOR-12`, constat A4).
 *
 * Avant ce lot, le manifeste d'un lieu déclarait l'emprise des pièces larges (étal 2 × 1, façade,
 * gradin), mais personne ne la lisait : ni l'occupation, ni le tri de profondeur, ni la collision
 * de la deuxième case n'étaient définis. La règle est ici, **une seule fois**, et lue par la
 * composition du jeu (`hmi::composeWorldScene`), la déduction de collision
 * (`core::deriveCollision`) et le contrôle de l'éditeur.
 *
 * ## La règle
 *
 * Une pièce est **ancrée** sur la case que la carte lui donne. Son image se pose par le sommet haut
 * du losange de cette case — c'est l'ancre que l'atelier des textures (`LOT-92`) mesure. Son
 * emprise de `columns` × `rows` cases s'étend donc vers les indices croissants,
 * `[colonne, colonne + columns[ × [ligne, ligne + rows[`. Elle se trie au **pied** de son emprise,
 * le sommet bas du losange de la case opposée à l'ancre — ce qui la garde derrière tout ce qui se
 * tient devant n'importe laquelle de ses cases.
 */

namespace core {

/// @brief Emprise d'une pièce, en cases : colonnes, puis lignes. Au moins 1 × 1.
struct PieceFootprint {
    int columns = 1;
    int rows = 1;

    [[nodiscard]] bool operator==(const PieceFootprint&) const = default;
};

/// @return Les cases qu'occupe une pièce d'emprise @p footprint ancrée en @p anchor, ligne par
///         ligne. Une emprise dégénérée compte pour 1 × 1.
[[nodiscard]] inline std::vector<GridPosition> footprintCells(GridPosition anchor,
                                                              PieceFootprint footprint) {
    const int columns = footprint.columns < 1 ? 1 : footprint.columns;
    const int rows = footprint.rows < 1 ? 1 : footprint.rows;
    std::vector<GridPosition> cells;
    cells.reserve(static_cast<std::size_t>(columns) * static_cast<std::size_t>(rows));
    for (int row = 0; row < rows; ++row) {
        for (int column = 0; column < columns; ++column) {
            cells.push_back(
                GridPosition{.column = anchor.column + column, .row = anchor.row + row});
        }
    }
    return cells;
}

/**
 * @return Le coin de grille (en cases, continu) dont la projection donne le **pied** de la pièce :
 *         `(colonne + columns, ligne + rows)`, le sommet bas de la case opposée à l'ancre. Pour une
 *         pièce 1 × 1, le pied de sa case.
 */
[[nodiscard]] constexpr GridPosition footprintFootCorner(GridPosition anchor,
                                                         PieceFootprint footprint) noexcept {
    return GridPosition{.column = anchor.column + (footprint.columns < 1 ? 1 : footprint.columns),
                        .row = anchor.row + (footprint.rows < 1 ? 1 : footprint.rows)};
}

}  // namespace core
