// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/Flanking.h
 * @brief La prise en tenaille, règle optionnelle du *Guide du Maître* (`LOT-23`).
 *
 * ## Ce que dit le Guide
 *
 * Chapitre 8, « Règle optionnelle : la prise en tenaille » (PDF p. 251) : « Quand une créature et
 * au moins un de ses alliés sont adjacents à un ennemi et placés sur des côtés ou des angles
 * opposés de son emplacement, ils le prennent en tenaille et ils bénéficient tous deux d'un
 * avantage lors de leurs jets d'attaque au corps à corps contre cet ennemi. » Pour trancher un
 * doute, « tracez une ligne imaginaire entre les centres des emplacements de chacune de ces deux
 * créatures. Si la ligne passe par des côtés ou des angles opposés de l'emplacement de
 * l'adversaire, alors ce dernier est bien pris en tenaille. »
 *
 * Deux restrictions : on ne prend pas en tenaille un ennemi **qu'on ne voit pas**, ni quand on est
 * **neutralisé** ; et une créature de Grande taille ou plus prend en tenaille « tant que l'une des
 * cases qu'elle occupe remplit les conditions ».
 *
 * ## Comment l'espace le mesure (`LOT-1017`)
 *
 * Sans grille, la ligne des centres devient un **angle** : les deux attaquants prennent la cible
 * en tenaille si l'angle qu'ils forment au centre de la cible atteint 135° (`core::flanksByAngle`).
 * C'est la valeur exacte où la ligne des centres du Guide bascule sur les huit cases adjacentes
 * (`test_combat_space.cpp`, `LaTenailleParAngleRejoueLaLigneDesCentresDuGuide`). « Adjacent »
 * devient « à l'allonge de 1,50 m » : l'écart entre les bords des volumes
 * (`core::adjacentGap`).
 *
 * La règle est **optionnelle** : c'est la donnée de l'arène qui l'active
 * (`core::ArenaBout::flanking`), pas le moteur.
 */

#include "Core/Combat/Attack.h"
#include "Core/Combat/CombatState.h"

namespace core {

/**
 * @brief Vrai si @p attacker, posé en @p attackerBase, prend @p target en tenaille avec au moins
 *        un allié debout.
 *
 * Chacun des deux doit être debout, à une case de la cible (`core::adjacentGap`) et la voir
 * (`core::hasLineOfSight`) ; leurs deux positions doivent former au centre de la cible un angle
 * d'au moins 135° (`core::flanksByAngle`). La position supposée sert l'IA (`LOT-23`), qui juge une
 * place avant d'y aller.
 */
[[nodiscard]] bool isFlankedFrom(const CombatState& combat, CombatantId attacker,
                                 Meters3 attackerBase, CombatantId target);

/// @brief La même règle, l'attaquant à sa place. Faux s'il n'est pas posé.
[[nodiscard]] bool isFlanked(const CombatState& combat, CombatantId attacker, CombatantId target);

/**
 * @brief Vrai si @p target est à une case (`core::adjacentGap`) d'un allié **debout** de
 *        @p attacker, autre que lui (`LOT-135`).
 *
 * La moitié de la tenaille — l'allié au contact —, sans l'angle ni la vue : ce que *Sneak Attack
 * Simplified* demande (*Player's Guide*, p. 204).
 */
[[nodiscard]] bool isAdjacentToAllyOf(const CombatState& combat, CombatantId attacker,
                                      CombatantId target);

}  // namespace core
