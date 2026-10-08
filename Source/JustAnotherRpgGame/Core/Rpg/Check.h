// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Rpg/Check.h
 * @brief Le jet de d20 : avantage, désavantage, seuil, restitution (`EX-REG-002`, `EX-REG-003`).
 */

#include <filesystem>
#include <span>
#include <string>
#include <string_view>
#include <vector>

#include "Core/Math/DeterministicRandom.h"

namespace core {

/// @brief Nombre de faces du dé de résolution. Le d20 est la mécanique centrale du jeu.
inline constexpr int D20_FACES = 20;

/**
 * @brief Comment le d20 est lancé.
 *
 * `Advantage` et `Disadvantage` **ne se cumulent pas** (`EX-REG-002`) : plusieurs sources
 * d'avantage donnent un avantage, et une source de chaque s'annule entièrement. C'est
 * `rollStance` qui applique cette règle, à partir du décompte des sources — jamais l'appelant, qui
 * aurait à arbitrer une pile de bonus contre toutes les autres à chaque capacité ajoutée.
 */
enum class RollStance {
    Normal,
    Advantage,
    Disadvantage,
};

/**
 * @brief Détermine la posture depuis le **nombre de sources** de chaque type (`EX-REG-002`).
 *
 * Deux avantages et un désavantage donnent `Normal`, pas `Advantage` : la règle annule, elle ne
 * compte pas. C'est contre-intuitif la première fois, et c'est précisément pour cela que la
 * décision vit ici, à un seul endroit.
 */
[[nodiscard]] constexpr RollStance rollStance(int advantageSources,
                                              int disadvantageSources) noexcept {
    const bool avantage = advantageSources > 0;
    const bool desavantage = disadvantageSources > 0;
    if (avantage == desavantage) {
        return RollStance::Normal;  // aucun des deux, ou les deux : ils s'annulent.
    }
    return avantage ? RollStance::Advantage : RollStance::Disadvantage;
}

/// @brief Un modificateur, avec **son origine** — sans quoi le jet n'est pas restituable.
struct Modifier {
    std::string source;
    int value = 0;
};

/**
 * @brief Le résultat complet d'un jet, et de quoi le reconstituer (`EX-REG-003`).
 *
 * Tout y est : les dés obtenus (deux si avantage ou désavantage), celui qui a été **retenu**, les
 * modificateurs avec leur origine, le seuil visé et l'issue. « Vous échouez » n'apprend rien ;
 * « 7 au dé, +3 de Dextérité, +2 de maîtrise = 12 contre 15 » se comprend, se discute, et se
 * diagnostique.
 */
struct CheckResult {
    /// Les dés lancés : un, ou deux en cas d'avantage ou de désavantage.
    std::vector<int> dice;
    /// Le dé retenu — le meilleur, le pire, ou le seul.
    int keptDie = 0;
    /// Les modificateurs appliqués, avec leur origine.
    std::vector<Modifier> modifiers;
    /// `keptDie` plus la somme des modificateurs.
    int total = 0;
    /// Le seuil visé (degré de difficulté, ou classe d'armure).
    int target = 0;
    /// La posture effectivement appliquée, après annulation.
    RollStance stance = RollStance::Normal;

    /**
     * @brief Vrai si le **dé retenu** vaut 20, indépendamment du total.
     *
     * À ne pas confondre avec « un total de 20 » : un 20 naturel déclenche le coup critique et
     * réussit quoi qu'il arrive, un total de 20 obtenu avec un 8 et huit points de bonus n'est
     * qu'un total. Les confondre rendrait critique un jet sur deux à haut niveau.
     */
    [[nodiscard]] constexpr bool isNaturalTwenty() const noexcept {
        return keptDie == D20_FACES;
    }

    /// @brief Vrai si le **dé retenu** vaut 1, indépendamment du total.
    [[nodiscard]] constexpr bool isNaturalOne() const noexcept {
        return keptDie == 1;
    }

    /// @brief Vrai si le total atteint ou dépasse le seuil.
    [[nodiscard]] constexpr bool succeeded() const noexcept {
        return total >= target;
    }

    /// @brief Restitution lisible du jet, modificateurs et origines compris (`EX-REG-003`).
    [[nodiscard]] std::string describe() const;
};

/**
 * @brief Lance un d20 contre un seuil.
 *
 * @param target Seuil visé : un degré de difficulté (`Source/Elements/Rpg/rules/difficulty.json`)
 *               ou une classe d'armure. **Jamais un littéral dans le code appelant**
 *               (`EX-REG-021`) : un nombre nu dans un `if` ne dit pas ce qu'il représente, et
 *               régler l'équilibre du jeu ne doit pas demander de recompiler.
 * @param modifiers Les modificateurs, **avec leur origine**.
 * @param stance Avantage, désavantage, ou ni l'un ni l'autre — voir `rollStance`.
 * @param random Générateur déterministe (`EX-NFR-002`).
 * @return Le résultat complet, restituable.
 */
[[nodiscard]] CheckResult rollCheck(int target, std::span<const Modifier> modifiers,
                                    RollStance stance, DeterministicRandom& random);

/// @brief Nom textuel d'une posture, pour les journaux et la restitution.
[[nodiscard]] std::string_view rollStanceName(RollStance stance) noexcept;

/// @brief Un degré de difficulté nommé : « moyenne », 15.
struct DifficultyTier {
    std::string id;
    std::string name;
    int dc = 0;
};

/**
 * @brief L'échelle des degrés de difficulté, telle que `rules/difficulty.json` la déclare
 *        (`EX-REG-021`, `LOT-15`).
 *
 * Un contenu écrit « Persuasion, difficulté **moyenne** » et non « Persuasion 15 » : le nombre est
 * une règle, et régler l'équilibre du jeu ne doit toucher qu'un fichier. C'est la lecture qui
 * manquait à `rollCheck` depuis le `LOT-12`, et que le premier contenu à jeter un d20 hors combat
 * — le dialogue — rend nécessaire.
 */
struct DifficultyScale {
    std::vector<DifficultyTier> tiers;
    std::vector<std::string> errors;

    /// @brief Le degré portant cet identifiant, ou `nullptr`.
    [[nodiscard]] const DifficultyTier* find(std::string_view id) const;
};

/**
 * @brief Charge l'échelle des degrés de difficulté.
 *
 * @param path `Source/Elements/Rpg/rules/difficulty.json`.
 * @return L'échelle et ses erreurs, un degré sans identifiant ou sans nombre étant écarté en le
 *         nommant. Ne lève jamais (`EX-NFR-040`).
 */
[[nodiscard]] DifficultyScale loadDifficultyScale(const std::filesystem::path& path);

}  // namespace core
