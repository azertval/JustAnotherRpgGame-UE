// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Levels/TileLayer.h"

#include <algorithm>
#include <cstddef>
#include <utility>

namespace core {

namespace {

// Rang de (column, row) dans un tableau dense ligne par ligne, ou cellCount si hors grille.
[[nodiscard]] std::size_t cellIndex(const TileMap& tiles, int column, int row) noexcept {
    return (static_cast<std::size_t>(row) * static_cast<std::size_t>(tiles.width())) +
           static_cast<std::size_t>(column);
}

[[nodiscard]] std::size_t cellCount(const TileMap& tiles) noexcept {
    return static_cast<std::size_t>(tiles.width()) * static_cast<std::size_t>(tiles.height());
}

}  // namespace

std::string_view TileLayer::pieceAt(int column, int row) const noexcept {
    if (pieces.empty() || !tiles.inBounds(column, row)) {
        return {};
    }
    const std::size_t index = cellIndex(tiles, column, row);
    return index < pieces.size() ? std::string_view{pieces[index]} : std::string_view{};
}

void TileLayer::setPiece(int column, int row, std::string piece) {
    if (!tiles.inBounds(column, row)) {
        return;
    }
    if (pieces.empty()) {
        if (piece.empty()) {
            return;
        }
        pieces.assign(cellCount(tiles), std::string{});
    }
    const bool clearing = piece.empty();
    pieces[cellIndex(tiles, column, row)] = std::move(piece);
    if (clearing && !hasPieces()) {
        pieces.clear();  // de nouveau vide : une couche sans pièce ne paie rien
    }
}

bool TileLayer::hasPieces() const noexcept {
    return std::ranges::any_of(pieces, [](const std::string& piece) { return !piece.empty(); });
}

int TileLayer::elevationAt(int column, int row) const noexcept {
    if (elevations.empty() || !tiles.inBounds(column, row)) {
        return 0;
    }
    const std::size_t index = cellIndex(tiles, column, row);
    return index < elevations.size() ? elevations[index] : 0;
}

void TileLayer::setElevation(int column, int row, int elevation) {
    if (!tiles.inBounds(column, row)) {
        return;
    }
    if (elevations.empty()) {
        if (elevation == 0) {
            return;
        }
        elevations.assign(cellCount(tiles), 0);
    }
    elevations[cellIndex(tiles, column, row)] = elevation;
    if (elevation == 0 && !hasElevation()) {
        elevations.clear();
    }
}

bool TileLayer::hasElevation() const noexcept {
    return std::ranges::any_of(elevations, [](int elevation) { return elevation != 0; });
}

TileLayer resizedLayer(const TileLayer& layer, int width, int height) {
    TileLayer resized{.name = layer.name,
                      .kind = layer.kind,
                      .tiles = TileMap(width, height),
                      .properties = layer.properties,
                      .floor = layer.floor};
    const int copyWidth = (std::min)(width, layer.tiles.width());
    const int copyHeight = (std::min)(height, layer.tiles.height());
    for (int row = 0; row < copyHeight; ++row) {
        for (int column = 0; column < copyWidth; ++column) {
            resized.tiles.setTile(column, row, layer.tiles.tile(column, row));
            resized.setPiece(column, row, std::string{layer.pieceAt(column, row)});
            resized.setElevation(column, row, layer.elevationAt(column, row));
        }
    }
    return resized;
}

}  // namespace core
