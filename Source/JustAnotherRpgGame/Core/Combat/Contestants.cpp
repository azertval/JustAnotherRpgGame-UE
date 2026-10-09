// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/Contestants.h"

#include <utility>
#include <variant>

#include "Core/Combat/Attack.h"
#include "Core/Combat/CombatState.h"
#include "Core/Combat/CombatTransition.h"

namespace core {

HeroContestantSource heroContestantSource(const LoadedCharacterSheet& member,
                                          const HeroCatalogs& catalogs) {
    HeroContestantSource hero{
        .sheet = member.sheet,
        .proficiency = catalogs.experience != nullptr
                           ? proficiencyBonus(member.sheet, *catalogs.experience)
                           : 2,
        .armorClass = 10,
        .weapon = std::nullopt,
        .spells = {}};
    if (catalogs.items != nullptr && catalogs.equipment != nullptr && catalogs.rules != nullptr &&
        catalogs.encumbrance != nullptr) {
        const ItemLookup lookup{.items = catalogs.items, .equipment = catalogs.equipment};
        hero.armorClass = derivedStatsFor(member.sheet, member.inventory, lookup, *catalogs.rules,
                                          *catalogs.encumbrance)
                              .armorClass;
    }
    if (catalogs.equipment != nullptr) {
        if (const Weapon* weapon =
                catalogs.equipment->findWeapon(member.inventory.at(EquipmentSlot::MainHand))) {
            hero.weapon = *weapon;
        }
    }
    if (catalogs.options != nullptr) {
        if (const PlayableClass* playableClass =
                catalogs.options->findClass(member.sheet.classId)) {
            std::vector<std::string> skipped;
            hero.spells = arenaSpellsFor(member.sheet, *playableClass, catalogs.options->spells,
                                         hero.proficiency, skipped);
        }
    }
    return hero;
}

ArenaContestant heroContestant(const HeroContestantSource& hero, CombatSide side) {
    // Le profil lit la fiche : vitesse et resistances des capacites comprises (LOT-131) ; la CA
    // vient de l'equipement porte (EX-CBT-030) ; les sauvegardes maitrisees prennent la maitrise.
    CombatantProfile profile = profileFor(hero.sheet, side, hero.proficiency);
    profile.armorClass = hero.armorClass;
    std::vector<AttackProfile> attacks;
    if (hero.weapon.has_value()) {
        const bool proficient = isProficientWith(hero.sheet, *hero.weapon);
        attacks.push_back(weaponAttackFor(hero.sheet, &*hero.weapon, hero.proficiency, proficient));
        if (std::optional<AttackProfile> thrown =
                thrownAttackFor(hero.sheet, *hero.weapon, hero.proficiency, proficient)) {
            attacks.push_back(std::move(*thrown));
        }
    }
    attacks.push_back(weaponAttackFor(hero.sheet, nullptr, hero.proficiency));
    return ArenaContestant{.profile = std::move(profile),
                           .attacks = std::move(attacks),
                           .position = std::nullopt,
                           .markId = {},
                           .behavior = {},
                           .capacities = hero.sheet.capacities,
                           .spells = hero.spells};
}

ArenaContestant creatureContestant(const Creature& creature, CombatSide side,
                                   const BehaviorCatalog* behaviors) {
    // Les attaques multiples du bloc (LOT-142) : le meme mecanisme que l'Extra Attack d'un heros.
    std::vector<Capacity> capacites;
    if (creature.multiattack > 1) {
        Capacity attaques{.id = "multiattack", .name = "Attaques multiples"};
        attaques.effects.push_back(
            {.kind = CapacityEffectKind::ExtraAttack, .value = creature.multiattack - 1});
        capacites.push_back(std::move(attaques));
    }
    return ArenaContestant{.profile = profileFor(creature, side),
                           .attacks = attacksFor(creature).attacks,
                           .position = std::nullopt,
                           .markId = {},
                           .behavior = behaviors != nullptr && !behaviors->profiles.empty()
                                           ? behaviorFor(creature, *behaviors)
                                           : std::string{},
                           .capacities = std::move(capacites),
                           .spells = {}};
}

const char* behaviorOfClass(std::string_view classId) noexcept {
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

std::optional<GridPosition> encounterTriggerOn(const Level& map, std::string_view encounterId) {
    std::optional<GridPosition> premier;
    for (const MapEntity& entity : map.entities()) {
        if (entity.type != ENCOUNTER_ENTITY_TYPE) {
            continue;
        }
        if (!premier.has_value()) {
            premier = entity.position;
        }
        const auto id = entity.properties.find("encounterId");
        if (id == entity.properties.end()) {
            continue;
        }
        if (const auto* text = std::get_if<std::string>(&id->second);
            text != nullptr && *text == encounterId) {
            return entity.position;
        }
    }
    return premier;
}

std::vector<GridPosition> partyDeploymentOn(const Level& map) {
    std::vector<GridPosition> cases;
    for (const ArenaEntryPoint& entree : arenaEntryPoints(map)) {
        if (entree.side == CombatSide::Allies) {
            cases.push_back(entree.position);
        }
    }
    return cases;
}

EncounterBout boutForEncounter(const MapEncounterSetup& setup,
                               std::span<const HeroContestantSource> party,
                               const Bestiary& bestiary, const BehaviorCatalog& behaviors,
                               std::uint64_t seed) {
    ArenaBout bout{.contestants = {},
                   .seed = seed,
                   .lethal = true,
                   .heroicMark = false,
                   .flanking = true,
                   .escapable = setup.run.escapable};
    for (std::size_t rang = 0; rang < party.size() && rang < setup.partyCells.size(); ++rang) {
        ArenaContestant membre = heroContestant(party[rang], CombatSide::Allies);
        membre.position = setup.partyCells[rang];
        bout.contestants.push_back(std::move(membre));
    }
    for (const CombatantPlacement& placement : setup.run.placements) {
        const Creature* const creature = bestiary.find(placement.creatureId);
        if (creature == nullptr) {
            return {.bout = std::nullopt, .issue = "creature inconnue : " + placement.creatureId};
        }
        ArenaContestant enemy = creatureContestant(*creature, CombatSide::Enemies, &behaviors);
        enemy.position = placement.position;
        bout.contestants.push_back(std::move(enemy));
    }
    return {.bout = std::move(bout), .issue = {}};
}

}  // namespace core
