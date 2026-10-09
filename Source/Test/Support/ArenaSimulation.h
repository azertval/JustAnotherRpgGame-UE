// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file ArenaSimulation.h
 * @brief Le banc des combats simulés sur le sable de l'Arena of Fate (`LOT-139`, `LOT-142`) :
 *        le groupe de « Nouvelle partie » monté à un niveau, une rencontre du contenu livré, les
 *        deux camps joués par l'IA, à une graine.
 *
 * C'est le montage que faisait l'écran de rencontre de l'ancien moteur, sans fenêtre (le
 * `LOT-1017` le reprend sans rien de Qt, D-58) : la zone de combat qui contient
 * le déclencheur, le groupe en file devant le maître d'arène, un combat létal dont on ne
 * s'échappe pas, la prise en tenaille en jeu. Chaque héros est joué par l'IA, sorts et soins
 * compris (`core::playTurn`), avec le profil de son rôle (`profileOfClass`).
 */

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/Arena.h"
#include "Core/Combat/Contestants.h"
#include "Core/Combat/Encounter.h"
#include "Core/Combat/EnemyAi.h"
#include "Core/Combat/MapEncounter.h"
#include "Core/Levels/GridPosition.h"
#include "Core/Levels/Level.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/CharacterOptions.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Equipment.h"
#include "Core/Rpg/Inventory.h"
#include "Core/Rpg/Skill.h"

namespace test_support {

/// Les sources de combattant et le montage d'une rencontre sont dans Core
/// (`Core/Combat/Contestants.h`) : le combat joué dans le moteur les lit aussi (LOT-1017).
using HeroContestantSource = core::HeroContestantSource;

/// La carte du sable, telle que le jeu la nomme.
inline constexpr std::string_view SABLE = "central-empire/capital/arenarea/arena-of-fate";
/// Le maître d'arène sur le sable, et la case d'où on lui parle.
inline constexpr core::GridPosition MAITRE{8, 10};
inline constexpr core::GridPosition DEVANT_LE_MAITRE{9, 10};

/// Le profil de comportement qui joue un héros dans les simulations (`core::behaviorOfClass`).
[[nodiscard]] inline const char* profileOfClass(std::string_view classId) {
    return core::behaviorOfClass(classId);
}

/// Le groupe de « Nouvelle partie », dans l'ordre de marche (celui de l'ancien écran du monde).
inline const std::vector<std::string>& startingParty() {
    static const std::vector<std::string> groupe{"heros-brawler", "heros-priest", "heros-scoundrel",
                                                 "heros-mage"};
    return groupe;
}

/// Les fiches d'un groupe et les catalogues qui les montent en combat.
struct Heros {
    core::CharacterOptions options;
    core::SkillCatalog skills;
    core::ExperienceTable experience;
    core::CharacterCreationRules rules;
    /// Les fiches, le meneur en tête.
    std::vector<core::LoadedCharacterSheet> members;
    core::ItemCatalog items;
    core::EquipmentCatalog equipment;
    core::EncumbranceRules encumbrance;

    /// La fiche du meneur.
    [[nodiscard]] const core::LoadedCharacterSheet& loaded() const {
        return members.front();
    }

    /// La source de combattant de @p member : sa fiche, son arme, ses sorts.
    [[nodiscard]] HeroContestantSource sourceOf(const core::LoadedCharacterSheet& member) const {
        return core::heroContestantSource(member, {.options = &options,
                                                   .experience = &experience,
                                                   .rules = &rules,
                                                   .items = &items,
                                                   .equipment = &equipment,
                                                   .encumbrance = &encumbrance});
    }

    /// Les sources de tous, dans l'ordre de marche.
    [[nodiscard]] std::vector<HeroContestantSource> sources() const {
        std::vector<HeroContestantSource> result;
        for (const core::LoadedCharacterSheet& member : members) {
            result.push_back(sourceOf(member));
        }
        return result;
    }
};

/**
 * @brief Charge @p members depuis le contenu livré (@p elements), montés au niveau @p level comme
 *        la partie les monte (`core::levelUpTo`, `LOT-141`).
 */
[[nodiscard]] inline Heros loadHeroes(const std::filesystem::path& elements,
                                      const std::vector<std::string>& members, int level = 1) {
    const std::filesystem::path rpg = elements / "Rpg";
    Heros heros;
    heros.options = core::loadCharacterOptions(rpg);
    heros.skills = core::loadSkills(rpg / "skills");
    heros.experience = core::loadExperienceTable(rpg / "rules" / "experience.json");
    heros.rules = core::loadCharacterCreationRules(rpg / "rules" / "character-creation.json");
    for (const std::string& membre : members) {
        core::LoadedCharacterSheet charge = core::loadCharacterSheet(
            rpg / "characters" / (membre + ".json"), heros.options, heros.rules, heros.experience);
        if (level > charge.sheet.level) {
            if (const core::PlayableClass* classe = heros.options.findClass(charge.sheet.classId)) {
                std::vector<std::string> manquants;
                static_cast<void>(core::levelUpTo(charge.sheet, level, *classe, heros.options,
                                                  heros.rules, heros.experience, manquants));
            }
        }
        heros.members.push_back(std::move(charge));
    }
    heros.items = core::loadItems(rpg / "items");
    heros.equipment = core::loadEquipment(rpg / "weapons", rpg / "armors");
    heros.encumbrance = core::loadEncumbranceRules(rpg / "rules" / "encumbrance.json");
    return heros;
}

/// Ce que le combat de l'arène demande au contenu livré.
struct ArenaContent {
    explicit ArenaContent(const std::filesystem::path& elements)
        : encounters(core::loadEncounters(elements / "Rpg" / "encounters")),
          bestiary(core::loadBestiary(elements / "Rpg" / "creatures")),
          behaviors(core::loadBehaviors(elements / "Rpg" / "rules" / "behaviors.json")) {}

    core::EncounterCatalog encounters;
    core::Bestiary bestiary;
    core::BehaviorCatalog behaviors;
};

/**
 * @brief Le déclencheur de @p encounterId sur @p map : son marqueur `encounter`, sinon le maître
 *        d'arène — c'est ce que faisait l'écran de rencontre.
 */
[[nodiscard]] inline core::GridPosition triggerOf(const core::Level& map,
                                                  std::string_view encounterId) {
    for (const core::MapEntity& entity : map.entities()) {
        if (entity.type != "encounter") {
            continue;
        }
        const auto id = entity.properties.find("encounterId");
        if (id != entity.properties.end()) {
            if (const auto* text = std::get_if<std::string>(&id->second);
                text != nullptr && *text == encounterId) {
                return entity.position;
            }
        }
    }
    return MAITRE;
}

/**
 * @brief Joue @p encounterId sur @p map, les deux camps par l'IA, à la graine @p seed.
 * @return L'issue, ou rien si le combat n'a pas pu se monter ou ne s'est pas terminé.
 */
[[nodiscard]] inline std::optional<core::CombatOutcome> playEncounter(
    const core::Level& map, const ArenaContent& arena, std::string_view encounterId,
    const std::vector<HeroContestantSource>& party, std::uint64_t seed,
    core::EncounterRun* engaged = nullptr) {
    const core::Encounter* const rencontre = arena.encounters.find(encounterId);
    if (rencontre == nullptr) {
        ADD_FAILURE() << "rencontre inconnue : " << encounterId;
        return std::nullopt;
    }
    // Le meneur devant le maitre, ses suiveurs dans son dos, vers l'est.
    std::vector<core::GridPosition> cases;
    for (std::size_t rang = 0; rang < party.size(); ++rang) {
        cases.push_back({.column = DEVANT_LE_MAITRE.column + static_cast<int>(rang),
                         .row = DEVANT_LE_MAITRE.row});
    }
    const core::MapEncounterResult prepared =
        core::prepareMapEncounter(map, SABLE, *rencontre, triggerOf(map, encounterId), cases,
                                  core::ExplorationSnapshot{}, "");
    if (!prepared.ok()) {
        ADD_FAILURE() << prepared.issue;
        return std::nullopt;
    }
    const core::MapEncounterSetup& setup = *prepared.setup;
    if (engaged != nullptr) {
        *engaged = setup.run;
    }
    core::ArenaSession session(setup.battlefield);
    session.setOpportunityPolicy(core::aiOpportunityPolicy(arena.behaviors));
    core::EncounterBout monte =
        core::boutForEncounter(setup, party, arena.bestiary, arena.behaviors, seed);
    if (!monte.bout.has_value()) {
        ADD_FAILURE() << monte.issue;
        return std::nullopt;
    }
    core::ArenaBout& bout = *monte.bout;
    // Le joueur ne joue pas : l'IA tient la place de chacun, sorts et soins compris.
    for (std::size_t rang = 0; rang < party.size() && rang < bout.contestants.size(); ++rang) {
        bout.contestants[rang].behavior = profileOfClass(party[rang].sheet.classId);
    }
    const core::ArenaMount mount = session.mount(bout);
    if (mount.allies.empty() || mount.enemies.empty() || !session.start()) {
        ADD_FAILURE() << "montage refuse a la graine " << seed;
        return std::nullopt;
    }
    for (int tours = 0; tours < 600; ++tours) {
        if (session.combat().phase() == core::CombatPhase::Ended) {
            return session.outcome();
        }
        if (!core::playTurn(session, arena.behaviors)) {
            return std::nullopt;
        }
    }
    return std::nullopt;
}

}  // namespace test_support
