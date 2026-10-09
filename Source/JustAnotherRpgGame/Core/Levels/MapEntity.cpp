// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Levels/MapEntity.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>
#include <variant>

#include "Core/Rpg/Scale.h"

namespace core {

namespace {

// Côté d'un rectangle de zone : entier positif, 1 sinon. Même borne que le rectangle d'une zone de
// combat, lue par ailleurs (`core::CombatZone`) : une zone dégénérée couvre au moins sa case.
[[nodiscard]] int sideOf(const PropertyMap& properties, std::string_view key) {
    const auto found = properties.find(std::string{key});
    if (found == properties.end()) {
        return 1;
    }
    const auto* const value = std::get_if<std::int64_t>(&found->second);
    return value == nullptr ? 1 : static_cast<int>(std::clamp<std::int64_t>(*value, 1, 1 << 16));
}

}  // namespace

std::string entityIdFor(int number) {
    return "e" + std::to_string(number);
}

std::optional<int> entityIdNumber(std::string_view id) noexcept {
    if (id.size() < 2 || id.size() > 10 || id.front() != 'e') {
        return std::nullopt;
    }
    int number = 0;
    for (const char digit : id.substr(1)) {
        if (digit < '0' || digit > '9') {
            return std::nullopt;
        }
        number = (number * 10) + (digit - '0');
    }
    return number;
}

std::vector<GridPosition> zoneCells(const MapEntity& entity) {
    if (!entity.cells.empty()) {
        return entity.cells;
    }
    const int columns = sideOf(entity.properties, ZONE_WIDTH_PROPERTY);
    const int rows = sideOf(entity.properties, ZONE_HEIGHT_PROPERTY);
    std::vector<GridPosition> cells;
    cells.reserve(static_cast<std::size_t>(columns) * static_cast<std::size_t>(rows));
    for (int row = 0; row < rows; ++row) {
        for (int column = 0; column < columns; ++column) {
            cells.push_back(GridPosition{.column = entity.position.column + column,
                                         .row = entity.position.row + row});
        }
    }
    return cells;
}

VolumeCells volumeCells(const MapVolume& volume) noexcept {
    // Les cases dont le centre tombe dans l'emprise : de la premiere colonne dont le centre est a
    // droite du bord ouest a la derniere dont le centre est a gauche du bord est.
    const auto first = [](float low) {
        return static_cast<int>(std::ceil((low / METERS_PER_TILE) - 0.5F));
    };
    const auto last = [](float high) {
        return static_cast<int>(std::floor((high / METERS_PER_TILE) - 0.5F));
    };
    int column0 = first(volume.minX);
    int column1 = last(volume.maxX);
    int row0 = first(volume.minY);
    int row1 = last(volume.maxY);
    // Un volume plus etroit qu'une case garde la case de son centre.
    if (column1 < column0) {
        column0 = column1 =
            static_cast<int>(std::floor(((volume.minX + volume.maxX) / 2.0F) / METERS_PER_TILE));
    }
    if (row1 < row0) {
        row0 = row1 =
            static_cast<int>(std::floor(((volume.minY + volume.maxY) / 2.0F) / METERS_PER_TILE));
    }
    return VolumeCells{.origin = GridPosition{.column = column0, .row = row0},
                       .columns = column1 - column0 + 1,
                       .rows = row1 - row0 + 1};
}

}  // namespace core
