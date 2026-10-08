// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Levels/MapEntity.h"

#include <algorithm>
#include <cstdint>
#include <string>
#include <variant>

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

}  // namespace core
