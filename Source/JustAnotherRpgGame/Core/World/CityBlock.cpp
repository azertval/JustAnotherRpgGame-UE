// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/World/CityBlock.h"

#include <cstdint>
#include <utility>
#include <variant>

#include "Core/Levels/Level.h"

namespace core {

namespace {

[[nodiscard]] std::string texteDe(const MapEntity& entite, std::string_view cle) {
    const auto trouvee = entite.properties.find(std::string{cle});
    if (trouvee == entite.properties.end()) {
        return {};
    }
    const std::string* texte = std::get_if<std::string>(&trouvee->second);
    return texte != nullptr ? *texte : std::string{};
}

// Un entier de propriete, ou 0 : meme regle que la zone de combat.
[[nodiscard]] int entierDe(const MapEntity& entite, std::string_view cle) {
    const auto trouvee = entite.properties.find(std::string{cle});
    if (trouvee == entite.properties.end()) {
        return 0;
    }
    const std::int64_t* entier = std::get_if<std::int64_t>(&trouvee->second);
    return entier != nullptr ? static_cast<int>(*entier) : 0;
}

}  // namespace

bool CityBlock::contains(GridPosition cell) const noexcept {
    return cell.column >= origin.column && cell.row >= origin.row &&
           cell.column < origin.column + columns && cell.row < origin.row + rows;
}

std::vector<CityBlock> cityBlocksOf(const Level& level) {
    std::vector<CityBlock> ilots;
    for (const MapEntity& entite : level.entities()) {
        if (entite.type != CITY_BLOCK_ENTITY_TYPE) {
            continue;
        }
        CityBlock ilot{.name = texteDe(entite, CITY_BLOCK_NAME_PROPERTY),
                       .origin = entite.position,
                       .columns = entierDe(entite, CITY_BLOCK_WIDTH_PROPERTY),
                       .rows = entierDe(entite, CITY_BLOCK_HEIGHT_PROPERTY)};
        if (ilot.name.empty() || ilot.columns <= 0 || ilot.rows <= 0) {
            continue;
        }
        ilots.push_back(std::move(ilot));
    }
    return ilots;
}

}  // namespace core
