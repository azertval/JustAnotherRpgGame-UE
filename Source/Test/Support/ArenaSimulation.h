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

/// @brief Ce qu'il faut d'un héros pour le monter en combattant : sa fiche, sa maîtrise, sa CA,
/// son arme et ses sorts.
struct HeroContestantSource {
    core::CharacterSheet sheet;
    /// Bonus de maîtrise, d'après son expérience.
    int proficiency = 2;
    /// Classe d'armure recalculée depuis l'équipement porté.
    int armorClass = 10;
    /// L'arme en main directrice, ou rien : il frappe alors à mains nues.
    std::optional<core::Weapon> weapon;
    /// Les sorts qu'il sait lancer en combat, lancers du jour compris (`core::arenaSpellsFor`).
    std::vector<core::ArenaSpell> spells;
};

/// @brief Le héros comme combattant du camp @p side : son arme, son arme lancée, ses mains nues.
inline core::ArenaContestant heroContestant(const HeroContestantSource& hero,
                                            core::CombatSide side) {
    // Le profil lit la fiche : vitesse et resistances des capacites comprises (LOT-131) ; la CA
    // vient de l'equipement porte (EX-CBT-030) ; les sauvegardes maitrisees prennent la maitrise.
    core::CombatantProfile profile = core::profileFor(hero.sheet, side, hero.proficiency);
    profile.armorClass = hero.armorClass;
    std::vector<core::AttackProfile> attacks;
    if (hero.weapon.has_value()) {
        const bool proficient = core::isProficientWith(hero.sheet, *hero.weapon);
        attacks.push_back(
            core::weaponAttackFor(hero.sheet, &*hero.weapon, hero.proficiency, proficient));
        if (std::optional<core::AttackProfile> thrown =
                core::thrownAttackFor(hero.sheet, *hero.weapon, hero.proficiency, proficient)) {
            attacks.push_back(std::move(*thrown));
        }
    }
    attacks.push_back(core::weaponAttackFor(hero.sheet, nullptr, hero.proficiency));
    return core::ArenaContestant{.profile = std::move(profile),
                                 .attacks = std::move(attacks),
                                 .position = std::nullopt,
                                 .markId = {},
                                 .behavior = {},
                                 .capacities = hero.sheet.capacities,
                                 .spells = hero.spells};
}

/// @brief Une créature du bestiaire comme combattant du camp @p side, avec le profil de
/// comportement que ses règles lui donnent (`LOT-23`).
inline core::ArenaContestant creatureContestant(const core::Creature& creature,
                                                core::CombatSide side,
                                                const core::BehaviorCatalog* behaviors) {
    // Les attaques multiples du bloc (LOT-142) : le meme mecanisme que l'Extra Attack d'un heros.
    std::vector<core::Capacity> capacites;
    if (creature.multiattack > 1) {
        core::Capacity attaques{.id = "multiattack", .name = "Attaques multiples"};
        attaques.effects.push_back(
            {.kind = core::CapacityEffectKind::ExtraAttack, .value = creature.multiattack - 1});
        capacites.push_back(std::move(attaques));
    }
    return core::ArenaContestant{.profile = core::profileFor(creature, side),
                                 .attacks = core::attacksFor(creature).attacks,
                                 .position = std::nullopt,
                                 .markId = {},
                                 .behavior = behaviors != nullptr && !behaviors->profiles.empty()
                                                 ? core::behaviorFor(creature, *behaviors)
                                                 : std::string{},
                                 .capacities = std::move(capacites),
                                 .spells = {}};
}

/// La carte du sable, telle que le jeu la nomme.
inline constexpr std::string_view SABLE = "central-empire/capital/arenarea/arena-of-fate";
/// Le maître d'arène sur le sable, et la case d'où on lui parle.
inline constexpr core::GridPosition MAITRE{8, 10};
inline constexpr core::GridPosition DEVANT_LE_MAITRE{9, 10};

/**
 * @brief Le profil de comportement qui joue un héros de la classe @p classId dans les simulations
 *        (`LOT-142`, décision nommée) : son rôle, comme un joueur le tiendrait. Le Brawler va au
 *        contact (`aggressive`), le Scoundrel frappe là où un allié tient déjà la cible (`pack`,
 *        l'attaque sournoise), le Priest reste près des blessés (`support`), le Mage tire et
 *        recule (`archer`).
 */
[[nodiscard]] inline const char* profileOfClass(std::string_view classId) {
    if (classId == "scoundrel") {
        return "pack";
    }
    if (classId == "priest") {
        return "support";
    }
    if (classId == "mage") {
        return "archer";
    }
    return "aggressive";
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
        const core::ItemLookup lookup{.items = &items, .equipment = &equipment};
        HeroContestantSource hero{
            .sheet = member.sheet,
            .proficiency = core::proficiencyBonus(member.sheet, experience),
            .armorClass =
                core::derivedStatsFor(member.sheet, member.inventory, lookup, rules, encumbrance)
                    .armorClass,
            .weapon = std::nullopt,
            .spells = {}};
        if (const core::Weapon* weapon =
                equipment.findWeapon(member.inventory.at(core::EquipmentSlot::MainHand))) {
            hero.weapon = *weapon;
        }
        if (const core::PlayableClass* playableClass = options.findClass(member.sheet.classId)) {
            std::vector<std::string> skipped;
            hero.spells = core::arenaSpellsFor(member.sheet, *playableClass, options.spells,
                                               hero.proficiency, skipped);
        }
        return hero;
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
    core::ArenaBout bout{.contestants = {},
                         .seed = seed,
                         .lethal = true,
                         .heroicMark = false,
                         .flanking = true,
                         .escapable = setup.run.escapable};
    for (std::size_t rang = 0; rang < party.size() && rang < setup.partyCells.size(); ++rang) {
        core::ArenaContestant membre = heroContestant(party[rang], core::CombatSide::Allies);
        membre.position = setup.partyCells[rang];
        // Le joueur ne joue pas : l'IA tient la place de chacun, sorts et soins compris.
        membre.behavior = profileOfClass(party[rang].sheet.classId);
        bout.contestants.push_back(std::move(membre));
    }
    for (const core::CombatantPlacement& placement : setup.run.placements) {
        const core::Creature* const creature = arena.bestiary.find(placement.creatureId);
        if (creature == nullptr) {
            ADD_FAILURE() << "creature inconnue : " << placement.creatureId;
            return std::nullopt;
        }
        core::ArenaContestant enemy =
            creatureContestant(*creature, core::CombatSide::Enemies, &arena.behaviors);
        enemy.position = placement.position;
        bout.contestants.push_back(std::move(enemy));
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
