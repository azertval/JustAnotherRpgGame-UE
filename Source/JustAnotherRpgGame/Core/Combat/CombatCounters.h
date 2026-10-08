// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/CombatCounters.h
 * @brief « Une fois par tour », « une fois par rencontre », « immunisé pendant 24 heures » : les
 *        mémoires à portée que les capacités des livres supposent (`LOT-20`).
 */

#include <cstdint>
#include <functional>
#include <map>
#include <string>
#include <string_view>
#include <tuple>

namespace core {

/**
 * @brief Jusqu'à quand un compteur vit.
 *
 * - `Turn` — jusqu'à la fin du tour **en cours**, quel qu'en soit le porteur : « une fois par
 *   tour » se compte aussi pendant le tour d'un autre (une attaque sournoise portée par une
 *   réaction) ;
 * - `Round` — jusqu'au début du round suivant : la cadence « un pouvoir par round » de la
 *   Dragonblade ;
 * - `Encounter` — jusqu'à la fin du combat ;
 * - `Day` — jusqu'à ce que l'horloge de jeu (`LOT-70`) tourne la journée. Le combat ne la vide
 *   jamais.
 */
enum class CounterScope : std::uint8_t {
    Turn,
    Round,
    Encounter,
    Day,
};

/**
 * @brief Des compteurs nommés, par porteur et par portée.
 *
 * Le porteur est une **chaîne**, pas un `core::CombatantId` : un compteur « par jour » survit au
 * combat, et l'identifiant d'un combattant ne vit que le temps d'une rencontre.
 */
class ScopedCounters {
public:
    /// @brief Ajoute @p amount au compteur, et rend sa nouvelle valeur.
    int increment(CounterScope scope, std::string_view owner, std::string_view key, int amount = 1);
    /// @brief La valeur du compteur, 0 s'il n'a jamais été touché.
    [[nodiscard]] int value(CounterScope scope, std::string_view owner, std::string_view key) const;
    /// @brief Remet à zéro tous les compteurs de @p scope.
    void clear(CounterScope scope);

private:
    std::map<std::tuple<CounterScope, std::string, std::string>, int, std::less<>> _values;
};

/// @brief Durée d'une immunité « de 24 heures », en secondes de jeu.
inline constexpr std::int64_t IMMUNITY_DAY_SECONDS = 24 * 60 * 60;

/**
 * @brief La mémoire des immunités temporaires, par couple (créature, source).
 *
 * « Une créature qui réussit son jet de sauvegarde est immunisée contre la Présence terrifiante
 * du dragon pendant 24 heures » : l'immunité tient à un **couple**, pas à la créature seule — la
 * même créature reste sensible à la présence d'un autre dragon —, et elle a une **échéance**, pas
 * une durée en rounds. Le temps est compté en secondes de jeu, que l'horloge du `LOT-70` fournira ;
 * ce registre ne lit aucune horloge lui-même.
 */
class ImmunityLedger {
public:
    /// @brief Rend @p creature immunisée contre @p source jusqu'à @p untilSecond. Une échéance plus
    /// proche que celle déjà connue ne raccourcit pas l'immunité.
    void grant(std::string_view creature, std::string_view source, std::int64_t untilSecond);
    /// @brief Vrai si l'immunité court encore à @p nowSecond.
    [[nodiscard]] bool isImmune(std::string_view creature, std::string_view source,
                                std::int64_t nowSecond) const;
    /// @brief Oublie les immunités échues à @p nowSecond.
    void expire(std::int64_t nowSecond);

private:
    std::map<std::tuple<std::string, std::string>, std::int64_t, std::less<>> _until;
};

}  // namespace core
