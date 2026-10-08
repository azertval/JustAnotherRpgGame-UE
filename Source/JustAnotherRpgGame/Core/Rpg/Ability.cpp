// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Rpg/Ability.h"

#include <array>

namespace core {

namespace {

constexpr std::array ABILITIES = {
    Ability::Strength,     Ability::Dexterity, Ability::Constitution,
    Ability::Intelligence, Ability::Wisdom,    Ability::Charisma,
};

}  // namespace

std::string_view abilityName(Ability ability) noexcept {
    // switch exhaustif sans default : une caracteristique ajoutee sans nom casse la compilation.
    switch (ability) {
        case Ability::Strength:
            return "strength";
        case Ability::Dexterity:
            return "dexterity";
        case Ability::Constitution:
            return "constitution";
        case Ability::Intelligence:
            return "intelligence";
        case Ability::Wisdom:
            return "wisdom";
        case Ability::Charisma:
            return "charisma";
    }
    return {};
}

std::optional<Ability> parseAbility(std::string_view name) noexcept {
    for (const Ability ability : ABILITIES) {
        if (abilityName(ability) == name) {
            return ability;
        }
    }
    return std::nullopt;
}

std::span<const Ability> allAbilities() noexcept {
    return ABILITIES;
}

}  // namespace core
