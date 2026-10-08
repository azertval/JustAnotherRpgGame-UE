// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/CombatTypes.h
 * @brief Les types que tout le combat partage — l'identifiant d'un combattant, sa locomotion,
 *        l'abri, les formes de zone — sans la grille (`LOT-1017`, D-50).
 *
 * Ils vivaient dans `BattleGrid.h`. Ce fichier-ci ne déclare rien qui porte le nom d'une macro du
 * moteur : il se consomme depuis le module du jeu, ce que `BattleGrid.h` ne peut pas (sa méthode
 * `check`).
 */

#include <cstdint>

#include "Core/Rpg/RpgEnums.h"

namespace core {

/**
 * @brief Identifiant d'un combattant.
 *
 * Un type **fort**, et non un `int` : l'espace de combat ne sait rien de ce qu'est un combattant —
 * fiche, créature, camp —, il ne retient que sa place. C'est le combat (`core::CombatState`,
 * `LOT-20`) qui attribue les identifiants.
 */
enum class CombatantId : std::uint32_t {};

/**
 * @brief Côté, en cases, de l'emprise d'une créature de taille @p size.
 *
 * Manuel des Joueurs, « Taille des créatures » : TP, P et M tiennent dans une case de 1,50 m, G
 * dans 2 × 2, TG dans 3 × 3, Gig dans 4 × 4. Une très petite créature occupe **une case entière**
 * ici, là où le livre en tolère quatre dans la même : décision du `LOT-19`, gardée en distance.
 */
[[nodiscard]] constexpr int footprintSide(CreatureSize size) noexcept {
    switch (size) {
        case CreatureSize::Tiny:
        case CreatureSize::Small:
        case CreatureSize::Medium:
            return 1;
        case CreatureSize::Large:
            return 2;
        case CreatureSize::Huge:
            return 3;
        case CreatureSize::Gargantuan:
            return 4;
    }
    return 1;
}

/**
 * @brief Comment un combattant se déplace : au sol, ou en vol.
 *
 * Le vol est une **manière de traverser** le même espace : un volant franchit les obstacles au sol
 * (l'eau profonde, la falaise) et ignore le terrain difficile ; il ne traverse pas la matière
 * pleine ; il tient sa place comme tout autre combattant.
 */
enum class Locomotion {
    Walk,
    Fly,
};

/**
 * @brief Les trois abris du Manuel des Joueurs (chapitre 9, « Abri »), et l'absence d'abri.
 *
 * Ordonnés du moins au plus protecteur : « si une cible se positionne derrière plusieurs types
 * d'abri, seul celui qui la protège le plus est pris en compte ».
 */
enum class Cover : std::uint8_t {
    None,
    /// Au moins la moitié du corps : +2 à la CA et aux sauvegardes de Dextérité.
    Half,
    /// Au moins les trois quarts : +5.
    ThreeQuarters,
    /// Complètement dissimulée : ne peut pas être ciblée directement.
    Total,
};

/// @brief Le bonus d'un abri à la CA et aux sauvegardes de Dextérité : 0, +2, +5 ; 0 pour l'abri
/// total, qui n'est pas un bonus mais une interdiction.
[[nodiscard]] constexpr int coverBonus(Cover cover) noexcept {
    switch (cover) {
        case Cover::Half:
            return 2;
        case Cover::ThreeQuarters:
            return 5;
        case Cover::None:
        case Cover::Total:
            return 0;
    }
    return 0;
}

/// @brief Les cinq formes de zone d'effet du Manuel (chapitre 10, « Zones d'effet »).
enum class AreaShape : std::uint8_t {
    Cone,
    Cube,
    Cylinder,
    Line,
    Sphere,
};

}  // namespace core
