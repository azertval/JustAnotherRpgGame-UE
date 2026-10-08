// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Rpg/Dice.h
 * @brief Notation de dés `NdF+M` : analyse, évaluation, bornes (`EX-NFR-002`).
 */

#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "Core/Math/DeterministicRandom.h"

namespace core {

/**
 * @brief Une expression de dés analysée : `2d6+3`, `1d8`, `4`.
 *
 * La **notation est une donnée** : elle vient des catalogues (`"damage": "2d4+2"`), jamais du
 * code. Ce type en est la forme analysée, et `parseDice` la seule porte d'entrée — un catalogue
 * qui écrirait `ld8` au lieu de `1d8`, faute d'OCR que le `LOT-30` a documentée, est refusé ici
 * comme il l'est au schéma.
 */
struct Dice {
    /// Nombre de dés. `0` pour une valeur fixe (`"4"`).
    int count = 0;
    /// Nombre de faces. `0` pour une valeur fixe.
    int faces = 0;
    /// Modificateur additionnel, éventuellement négatif.
    int modifier = 0;

    /// @brief Plus petit total possible.
    [[nodiscard]] constexpr int minimum() const noexcept {
        return count + modifier;
    }

    /// @brief Plus grand total possible.
    [[nodiscard]] constexpr int maximum() const noexcept {
        return count * faces + modifier;
    }

    [[nodiscard]] bool operator==(const Dice&) const = default;
};

/**
 * @brief Le détail d'un lancer, pour que le joueur puisse le reconstituer (`EX-REG-003`).
 *
 * Chaque dé est conservé, pas seulement le total. Un jeu de rôle au dé dont le joueur ne peut pas
 * reconstituer pourquoi il a échoué se joue comme une machine à sous — et c'est aussi le seul
 * outil de diagnostic praticable quand une capacité ne s'applique pas.
 */
struct DiceRoll {
    /// L'expression lancée.
    Dice dice;
    /// Chaque dé, dans l'ordre du tirage.
    std::vector<int> faces;
    /// Somme des dés **et** du modificateur.
    int total = 0;

    /// @brief Restitution lisible : `« 2d6+3 : 4 + 5 + 3 = 12 »`.
    [[nodiscard]] std::string describe() const;
};

/**
 * @brief Analyse une notation `NdF`, `NdF+M`, `NdF-M` ou une valeur fixe.
 *
 * @param notation La notation, sans espace. La casse du `d` est indifférente.
 * @return L'expression, ou `std::nullopt` si la notation est mal formée — jamais une expression
 *         devinée : une notation illisible est une donnée invalide à signaler.
 */
[[nodiscard]] std::optional<Dice> parseDice(std::string_view notation);

/// @brief Réécrit une expression en notation canonique (`2d6+3`, `1d8`, `4`).
[[nodiscard]] std::string formatDice(const Dice& dice);

/**
 * @brief Lance une expression avec un générateur **déterministe**.
 *
 * Le déterminisme n'est pas un confort : sans lui, **aucun test de combat n'est écrivable**
 * (`EX-NFR-002`). Le générateur est passé par référence et jamais créé ici, pour que l'appelant
 * reste maître de la graine et de la position dans la suite.
 */
[[nodiscard]] DiceRoll rollDice(const Dice& dice, DeterministicRandom& random);

}  // namespace core
