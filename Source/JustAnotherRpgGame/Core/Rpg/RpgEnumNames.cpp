// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Rpg/RpgEnumNames.h"

#include <array>
#include <cstddef>
#include <functional>
#include <unordered_map>

namespace core {

namespace {

// Hacheur transparent : permet d'interroger une table a cles std::string avec un std::string_view
// sans construire de chaine temporaire a chaque appel (C++20, heterogeneous lookup). Meme patron
// que Core/Levels/TileTypeName.cpp.
struct TransparentStringHash {
    using is_transparent = void;

    [[nodiscard]] std::size_t operator()(std::string_view text) const noexcept {
        return std::hash<std::string_view>{}(text);
    }
};

// Les tables inverses sont construites A PARTIR des fonctions de nommage, jamais saisies a la
// main : c'est ce qui garantit que l'aller-retour est exact par construction, et non par
// vigilance. Une seconde table ecrite en dur divergerait de la premiere au premier ajout.
template <typename Enum, typename Nommer>
[[nodiscard]] std::optional<Enum> parseAvec(std::span<const Enum> valeurs, Nommer nommer,
                                            std::string_view name) {
    // Construite une seule fois, a la premiere analyse (initialisation locale statique, sure vis
    // a vis des threads depuis C++11). La table est propre a l'instanciation du modele, donc une
    // par enumeration.
    static const std::unordered_map<std::string, Enum, TransparentStringHash, std::equal_to<>>
        table = [valeurs, nommer] {
            std::unordered_map<std::string, Enum, TransparentStringHash, std::equal_to<>>
                construite;
            construite.reserve(valeurs.size());
            for (const Enum valeur : valeurs) {
                construite.emplace(nommer(valeur), valeur);
            }
            return construite;
        }();

    const auto trouve = table.find(name);
    return trouve == table.end() ? std::nullopt : std::optional<Enum>{trouve->second};
}

constexpr std::array DAMAGE_TYPES = {
    DamageType::Acid,    DamageType::Bludgeoning, DamageType::Cold,     DamageType::Fire,
    DamageType::Force,   DamageType::Lightning,   DamageType::Necrotic, DamageType::Piercing,
    DamageType::Poison,  DamageType::Psychic,     DamageType::Radiant,  DamageType::Slashing,
    DamageType::Thunder,
};

constexpr std::array CONDITIONS = {
    Condition::Blinded,    Condition::Charmed,   Condition::Deafened,      Condition::Exhaustion,
    Condition::Frightened, Condition::Grappled,  Condition::Incapacitated, Condition::Invisible,
    Condition::Paralyzed,  Condition::Petrified, Condition::Poisoned,      Condition::Prone,
    Condition::Restrained, Condition::Stunned,   Condition::Unconscious,
};

constexpr std::array MAGIC_SCHOOLS = {
    MagicSchool::Abjuration,  MagicSchool::Conjuration,   MagicSchool::Divination,
    MagicSchool::Enchantment, MagicSchool::Evocation,     MagicSchool::Illusion,
    MagicSchool::Necromancy,  MagicSchool::Transmutation,
};

constexpr std::array CREATURE_SIZES = {
    CreatureSize::Tiny,  CreatureSize::Small, CreatureSize::Medium,
    CreatureSize::Large, CreatureSize::Huge,  CreatureSize::Gargantuan,
};

}  // namespace

std::string damageTypeName(DamageType type) {
    // switch exhaustif sans default : un DamageType ajoute sans nom casse la compilation au lieu
    // de retomber sur un nom arbitraire (EX-CNT-011).
    switch (type) {
        case DamageType::Acid:
            return "acid";
        case DamageType::Bludgeoning:
            return "bludgeoning";
        case DamageType::Cold:
            return "cold";
        case DamageType::Fire:
            return "fire";
        case DamageType::Force:
            return "force";
        case DamageType::Lightning:
            return "lightning";
        case DamageType::Necrotic:
            return "necrotic";
        case DamageType::Piercing:
            return "piercing";
        case DamageType::Poison:
            return "poison";
        case DamageType::Psychic:
            return "psychic";
        case DamageType::Radiant:
            return "radiant";
        case DamageType::Slashing:
            return "slashing";
        case DamageType::Thunder:
            return "thunder";
    }
    return {};  // inatteignable : le switch ci-dessus est exhaustif.
}

std::string conditionName(Condition condition) {
    switch (condition) {
        case Condition::Blinded:
            return "blinded";
        case Condition::Charmed:
            return "charmed";
        case Condition::Deafened:
            return "deafened";
        case Condition::Exhaustion:
            return "exhaustion";
        case Condition::Frightened:
            return "frightened";
        case Condition::Grappled:
            return "grappled";
        case Condition::Incapacitated:
            return "incapacitated";
        case Condition::Invisible:
            return "invisible";
        case Condition::Paralyzed:
            return "paralyzed";
        case Condition::Petrified:
            return "petrified";
        case Condition::Poisoned:
            return "poisoned";
        case Condition::Prone:
            return "prone";
        case Condition::Restrained:
            return "restrained";
        case Condition::Stunned:
            return "stunned";
        case Condition::Unconscious:
            return "unconscious";
    }
    return {};
}

std::string magicSchoolName(MagicSchool school) {
    switch (school) {
        case MagicSchool::Abjuration:
            return "abjuration";
        case MagicSchool::Conjuration:
            return "conjuration";
        case MagicSchool::Divination:
            return "divination";
        case MagicSchool::Enchantment:
            return "enchantment";
        case MagicSchool::Evocation:
            return "evocation";
        case MagicSchool::Illusion:
            return "illusion";
        case MagicSchool::Necromancy:
            return "necromancy";
        case MagicSchool::Transmutation:
            return "transmutation";
    }
    return {};
}

std::string creatureSizeName(CreatureSize size) {
    switch (size) {
        case CreatureSize::Tiny:
            return "tiny";
        case CreatureSize::Small:
            return "small";
        case CreatureSize::Medium:
            return "medium";
        case CreatureSize::Large:
            return "large";
        case CreatureSize::Huge:
            return "huge";
        case CreatureSize::Gargantuan:
            return "gargantuan";
    }
    return {};
}

std::optional<DamageType> parseDamageType(std::string_view name) {
    return parseAvec<DamageType>(allDamageTypes(), damageTypeName, name);
}

std::optional<Condition> parseCondition(std::string_view name) {
    return parseAvec<Condition>(allConditions(), conditionName, name);
}

std::optional<MagicSchool> parseMagicSchool(std::string_view name) {
    return parseAvec<MagicSchool>(allMagicSchools(), magicSchoolName, name);
}

std::optional<CreatureSize> parseCreatureSize(std::string_view name) {
    return parseAvec<CreatureSize>(allCreatureSizes(), creatureSizeName, name);
}

std::span<const DamageType> allDamageTypes() {
    return DAMAGE_TYPES;
}

std::span<const Condition> allConditions() {
    return CONDITIONS;
}

std::span<const MagicSchool> allMagicSchools() {
    return MAGIC_SCHOOLS;
}

std::span<const CreatureSize> allCreatureSizes() {
    return CREATURE_SIZES;
}

}  // namespace core
