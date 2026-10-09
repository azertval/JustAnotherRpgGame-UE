// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/Contestants.h
 * @brief Monter une rencontre en affrontement : les héros et les créatures en combattants, la
 *        rencontre sur une carte, la composition prête pour `core::ArenaSession` (`LOT-1017`).
 *
 * ## D'où ça vient
 *
 * L'écran de rencontre de l'ancien moteur (`hmi::EncounterModel`, `LOT-118`, `LOT-139`) montait
 * le combat : la fiche d'un héros devenait un combattant, la rencontre se posait sur la zone de
 * combat qui contient son déclencheur, et la composition jouait **létale**, sans Marque Héroïque,
 * tenaille en jeu, sans fuite si la rencontre le dit. Le banc de la série de l'arène
 * (`Source/Test/Support/ArenaSimulation.h`) en avait repris une copie sans Qt ; le combat joué
 * dans le moteur (`LOT-1017`, sous-lot 3) en a besoin à son tour. La règle est donc ici, une
 * fois, et les deux la lisent.
 *
 * ## Le déclencheur et le déploiement
 *
 * Une rencontre engagée par un dialogue n'a pas de case : son lieu est la carte d'arène. Le
 * déclencheur est le marqueur `encounter` qui la nomme ; à défaut, le **premier** marqueur
 * `encounter` de la carte — le sable n'en a qu'un, et chaque rencontre de la série s'y dresse
 * (décision du `LOT-1017`). Le groupe se déploie sur les points d'entrée `arenaEntry` de son camp,
 * par rang (`core::arenaEntryPoints`) : c'est la carte qui dit où il entre, pas le code.
 */

#include <cstdint>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include "Core/Combat/Arena.h"
#include "Core/Combat/EnemyAi.h"
#include "Core/Combat/MapEncounter.h"
#include "Core/Levels/GridPosition.h"
#include "Core/Levels/Level.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/CharacterOptions.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Equipment.h"
#include "Core/Rpg/Inventory.h"

namespace core {

/// @brief Ce qu'il faut d'un héros pour le monter en combattant : sa fiche, sa maîtrise, sa CA,
/// son arme et ses sorts.
struct HeroContestantSource {
    CharacterSheet sheet;
    /// Bonus de maîtrise, d'après son expérience.
    int proficiency = 2;
    /// Classe d'armure recalculée depuis l'équipement porté.
    int armorClass = 10;
    /// L'arme en main directrice, ou rien : il frappe alors à mains nues.
    std::optional<Weapon> weapon;
    /// Les sorts qu'il sait lancer en combat, lancers du jour compris (`core::arenaSpellsFor`).
    std::vector<ArenaSpell> spells;
};

/// @brief Les catalogues qui font d'une fiche chargée une source de combattant.
struct HeroCatalogs {
    const CharacterOptions* options = nullptr;
    const ExperienceTable* experience = nullptr;
    const CharacterCreationRules* rules = nullptr;
    const ItemCatalog* items = nullptr;
    const EquipmentCatalog* equipment = nullptr;
    const EncumbranceRules* encumbrance = nullptr;
};

/**
 * @brief La source de combattant d'un membre : sa fiche, sa maîtrise, la CA de ce qu'il porte,
 *        l'arme de sa main directrice, ses sorts de combat.
 */
[[nodiscard]] HeroContestantSource heroContestantSource(const LoadedCharacterSheet& member,
                                                        const HeroCatalogs& catalogs);

/// @brief Le héros comme combattant du camp @p side : son arme, son arme lancée, ses mains nues.
[[nodiscard]] ArenaContestant heroContestant(const HeroContestantSource& hero, CombatSide side);

/// @brief Une créature du bestiaire comme combattant du camp @p side, avec le profil de
/// comportement que ses règles lui donnent (`LOT-23`) ; ses attaques multiples deviennent des
/// attaques supplémentaires, comme l'*Extra Attack* d'un héros (`LOT-142`).
[[nodiscard]] ArenaContestant creatureContestant(const Creature& creature, CombatSide side,
                                                 const BehaviorCatalog* behaviors);

/**
 * @brief Le profil de comportement qui joue un héros de la classe @p classId quand ce n'est pas le
 *        joueur (`LOT-142`, décision nommée) : son rôle, comme un joueur le tiendrait. Le Brawler
 * va au contact (`aggressive`), le Scoundrel frappe là où un allié tient déjà la cible (`pack`,
 *        l'attaque sournoise), le Priest reste près des blessés (`support`), le Mage tire et
 *        recule (`archer`).
 */
[[nodiscard]] const char* behaviorOfClass(std::string_view classId) noexcept;

/// @brief Le déclencheur de @p encounterId sur @p map : son marqueur `encounter`, sinon le premier
/// marqueur `encounter` de la carte ; rien si la carte n'en a aucun.
[[nodiscard]] std::optional<GridPosition> encounterTriggerOn(const Level& map,
                                                             std::string_view encounterId);

/// @brief Les cases où le groupe se déploie : les points d'entrée alliés de la carte, par rang.
[[nodiscard]] std::vector<GridPosition> partyDeploymentOn(const Level& map);

/// @brief La composition d'une rencontre préparée, ou ce qui l'en empêche.
struct EncounterBout {
    std::optional<ArenaBout> bout;
    /// Vide si `bout` est là.
    std::string issue;
};

/**
 * @brief La composition de @p setup : le groupe à ses places (`partyCells`, meneur d'abord), les
 *        créatures de la rencontre aux leurs, à la graine @p seed.
 *
 * Les règles de l'écran de rencontre (`LOT-118`, `LOT-139`) : un combat **létal**, sans Marque
 * Héroïque, la prise en tenaille en jeu, la fuite si la rencontre la permet. Les héros sont joués
 * par le joueur (`behavior` vide) ; les créatures, par le profil de leurs règles.
 */
[[nodiscard]] EncounterBout boutForEncounter(const MapEncounterSetup& setup,
                                             std::span<const HeroContestantSource> party,
                                             const Bestiary& bestiary,
                                             const BehaviorCatalog& behaviors, std::uint64_t seed);

}  // namespace core
