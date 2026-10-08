// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <vector>

#include "Core/Levels/TileType.h"

/**
 * @file Core/Levels/TileMap.h
 * @brief Grille de tuiles typées d'un niveau.
 */

namespace core {

/**
 * @brief Grille dense de tuiles typées (`EX-GP-001`), origine haut-gauche.
 *
 * Toutes les cases sont initialisées à `TileType::Empty`. C'est la représentation en mémoire du
 * décor d'un niveau : le chargeur la remplit à partir du fichier, le gameplay (à venir)
 * l'interroge pour les collisions (`EX-GP-002`). Donnée pure, sans dépendance rendu ni fichier
 * (`EX-ARCH-011`), testable sans fenêtre ni GPU.
 */
class TileMap {
public:
    /**
     * @brief Construit une grille de dimensions données, entièrement `Empty`.
     * @param width  Largeur en cases (> 0).
     * @param height Hauteur en cases (> 0).
     */
    TileMap(int width, int height);

    /// @return Largeur de la grille, en cases.
    [[nodiscard]] int width() const noexcept {
        return _width;
    }

    /// @return Hauteur de la grille, en cases.
    [[nodiscard]] int height() const noexcept {
        return _height;
    }

    /**
     * @brief Indique si une case est dans les bornes de la grille.
     * @param column Colonne visée.
     * @param row    Ligne visée.
     * @return true si `0 ≤ column < width` et `0 ≤ row < height`.
     */
    [[nodiscard]] bool inBounds(int column, int row) const noexcept;

    /**
     * @brief Type de la tuile à une case.
     * @param column Colonne (doit être dans les bornes).
     * @param row    Ligne (doit être dans les bornes).
     * @return Le type de la tuile.
     */
    [[nodiscard]] TileType tile(int column, int row) const;

    /**
     * @brief Change le type de la tuile à une case.
     * @param column Colonne (doit être dans les bornes).
     * @param row    Ligne (doit être dans les bornes).
     * @param type   Nouveau type de tuile.
     */
    void setTile(int column, int row, TileType type);

    /**
     * @brief Indique si la tuile à une case est **statiquement solide**.
     * @param column Colonne (doit être dans les bornes).
     * @param row    Ligne (doit être dans les bornes).
     * @return true si la tuile bloque le déplacement (cf. `isSolid(TileType)`).
     */
    [[nodiscard]] bool isSolid(int column, int row) const;

private:
    int _width;
    int _height;
    std::vector<TileType> _tiles;
};

}  // namespace core
