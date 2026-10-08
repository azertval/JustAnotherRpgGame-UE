// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Levels/TileMap.h"

#include <cstddef>

#include "Core/Diagnostics/Assert.h"

namespace core {

// Construit une grille de dimensions données, entièrement Empty.
TileMap::TileMap(int width, int height)
    : _width(width),
      _height(height),
      _tiles(static_cast<std::size_t>(width) * static_cast<std::size_t>(height), TileType::Empty) {
    JADG_ASSERT(width > 0 && height > 0, "Dimensions de TileMap invalides");
}

// Indique si une case est dans les bornes de la grille.
bool TileMap::inBounds(int column, int row) const noexcept {
    return column >= 0 && column < _width && row >= 0 && row < _height;
}

// Type de la tuile a une case (precondition : case dans les bornes).
TileType TileMap::tile(int column, int row) const {
    JADG_ASSERT(inBounds(column, row), "Acces hors bornes de TileMap");
    return _tiles[(static_cast<std::size_t>(row) * static_cast<std::size_t>(_width)) +
                  static_cast<std::size_t>(column)];
}

// Change le type de la tuile a une case (precondition : case dans les bornes).
void TileMap::setTile(int column, int row, TileType type) {
    JADG_ASSERT(inBounds(column, row), "Ecriture hors bornes de TileMap");
    _tiles[(static_cast<std::size_t>(row) * static_cast<std::size_t>(_width)) +
           static_cast<std::size_t>(column)] = type;
}

// Indique si la tuile a une case est statiquement solide.
bool TileMap::isSolid(int column, int row) const {
    return core::isSolid(tile(column, row));
}

}  // namespace core
