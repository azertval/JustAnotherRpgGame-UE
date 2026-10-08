// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Rpg/RpgEnumNames.h
 * @brief Correspondance entre les énumérations RPG et leurs noms textuels (`EX-CNT-011`).
 */

#include <optional>
#include <span>
#include <string>
#include <string_view>

#include "Core/Rpg/RpgEnums.h"

namespace core {

/**
 * @name Noms textuels
 *
 * Point unique de vérité de la correspondance valeur ↔ nom, partagé par les catalogues de données
 * (`Source/Elements/Rpg/`), leurs schémas JSON et le moteur. Deux tables distinctes divergeraient
 * au premier type ajouté — et le scénario qu'`EX-CNT-011` décrit se produirait : la donnée déclare
 * un type que le moteur ne connaît pas, la valeur tombe dans un cas par défaut, et le sort cesse
 * de faire des dégâts sans que rien ne l'annonce.
 *
 * Chaque `switch` est **exhaustif et sans `default`** : ajouter une valeur à une énumération sans
 * lui donner de nom devient une erreur de compilation (`/W4 /WX`), jamais un nom faux.
 *
 * Les noms sont ceux du **lexique de traduction** (`LOT-30`) : ce sont les termes anglais que la
 * table d'autorité porte sous les catégories *type de dégâts*, *état* et *école de magie*.
 * @{
 */
[[nodiscard]] std::string damageTypeName(DamageType type);
[[nodiscard]] std::string conditionName(Condition condition);
[[nodiscard]] std::string magicSchoolName(MagicSchool school);
[[nodiscard]] std::string creatureSizeName(CreatureSize size);
/** @} */

/**
 * @name Analyse d'un nom
 *
 * Inverses exacts des fonctions ci-dessus : tout nom qu'elles produisent est accepté ici, et
 * réciproquement. Un nom inconnu renvoie `std::nullopt` — c'est une donnée invalide à signaler,
 * jamais une valeur devinée.
 * @{
 */
[[nodiscard]] std::optional<DamageType> parseDamageType(std::string_view name);
[[nodiscard]] std::optional<Condition> parseCondition(std::string_view name);
[[nodiscard]] std::optional<MagicSchool> parseMagicSchool(std::string_view name);
[[nodiscard]] std::optional<CreatureSize> parseCreatureSize(std::string_view name);
/** @} */

/**
 * @name Énumération complète
 *
 * Les valeurs de chaque énumération, dans l'ordre de déclaration. Ce sont ces vues qui permettent
 * à un test de **balayer** une énumération sans coder en dur sa dernière valeur : la borne d'un
 * parcours écrite à la main est la première chose qui vieillit, et un type ajouté après elle
 * échapperait en silence à tous les contrôles.
 * @{
 */
[[nodiscard]] std::span<const DamageType> allDamageTypes();
[[nodiscard]] std::span<const Condition> allConditions();
[[nodiscard]] std::span<const MagicSchool> allMagicSchools();
[[nodiscard]] std::span<const CreatureSize> allCreatureSizes();
/** @} */

}  // namespace core
