// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Rpg/Multiclassing.h
 * @brief Cumul des emplacements de sorts d'un personnage multiclassé (`EX-RPG-041`).
 */

#include <optional>
#include <span>
#include <string_view>

namespace core {

/**
 * @brief Rythme auquel une classe fait progresser le niveau de lanceur.
 *
 * Les valeurs viennent d'une phrase du *Manuel des Joueurs* (p. 166), citée mot pour mot dans
 * `scripts/sourcebook/options.py` : *« additionnez tous les niveaux dans vos classes de barde, de
 * druide, de clerc, d'ensorceleur et de magicien, la moitié de vos niveaux (arrondis à l'entier
 * inférieur) dans les classes de paladin et rôdeur, et un tiers de vos niveaux de guerrier et de
 * roublard (arrondis à l'entier inférieur) si vous avez choisi l'archétype de chevalier occulte ou
 * d'arnaqueur arcanique. »*
 *
 * La correspondance classe → progression est une **donnée**
 * (`Source/Elements/Rpg/rules/multiclassing.json`) ; ce type n'en porte que le vocabulaire.
 */
enum class CasterProgression {
    /// La classe n'apporte rien au niveau de lanceur — barbare, moine.
    None,
    /// Un tiers des niveaux, arrondi à l'inférieur — guerrier et roublard, sous archétype.
    Third,
    /// La moitié des niveaux, arrondie à l'inférieur — paladin, rôdeur.
    Half,
    /// La totalité des niveaux — barde, clerc, druide, ensorceleur, magicien.
    Full,
    /// **Magie de pacte** : n'entre pas dans la somme (`EX-RPG-052`).
    Pact,
};

/// @brief Un niveau pris dans une classe, et ce que cette classe apporte au niveau de lanceur.
struct ClassLevel {
    int level = 0;
    CasterProgression progression = CasterProgression::None;
};

/**
 * @brief Niveau de lanceur cumulé d'un personnage multiclassé.
 *
 * **La règle qu'il est le plus facile d'implémenter de travers** (`EX-RPG-041`), pour deux raisons
 * qui se cumulent :
 *
 * 1. **L'arrondi se fait par classe, jamais sur le total.** Un paladin 3/rôdeur 3 donne
 *    `1 + 1 = 2`, et non `⌊6/2⌋ = 3`. Sommer d'abord et diviser ensuite donne un emplacement de
 *    trop, à un niveau où c'en est un tiers de plus.
 * 2. **La magie de pacte est exclue.** Le sorcier (occultiste) obtient ses emplacements par une
 *    voie distincte — peu nombreux, toujours au niveau maximal, récupérés au repos **court**. Les
 *    additionner double la puissance du personnage sans que rien ne le signale.
 *
 * Un lanceur multiclassé mal calculé **reste jouable, simplement faux** : c'est pourquoi cette
 * fonction est vérifiée contre l'exemple travaillé du livre lui-même — un rôdeur 4/magicien 3 est
 * « considéré comme un personnage de niveau 5 ».
 *
 * @param classes Les niveaux pris dans chaque classe. Une classe absente n'apporte rien.
 * @return Le niveau de lanceur, dans `[0, 20]`. `0` signifie qu'aucun emplacement n'est accordé
 *         par cette voie — ce qui n'interdit pas la magie de pacte, comptée à part.
 */
[[nodiscard]] int multiclassCasterLevel(std::span<const ClassLevel> classes);

/**
 * @brief Convertit le nom d'une progression, tel que la donnée l'écrit, en valeur.
 *
 * Inverse de `casterProgressionName`. Un nom inconnu renvoie `std::nullopt` : c'est une donnée
 * invalide à signaler, jamais une progression devinée — deviner `None` ferait taire un lanceur.
 */
[[nodiscard]] std::optional<CasterProgression> parseCasterProgression(std::string_view name);

/// @brief Nom textuel d'une progression, tel que `multiclassing.json` l'écrit.
[[nodiscard]] std::string_view casterProgressionName(CasterProgression progression);

}  // namespace core
