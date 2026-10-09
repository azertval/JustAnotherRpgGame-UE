// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/AreaOfEffect.h
 * @brief Les zones d'effet dans le combat (`LOT-22`, `LOT-1017`) : qui une forme posée dans
 *        l'espace prend.
 *
 * ## Ce que dit le Manuel
 *
 * Chapitre 10, « Zones d'effet » : chaque zone a un **point d'origine**, et l'effet « s'étend en
 * lignes droites » depuis ce point — un emplacement qu'aucune ligne droite ne relie à l'origine
 * n'est pas dans la zone, et seul un abri total bloque ces lignes. Les cinq formes et leur
 * géométrie en mètres sont dans `core::Effect` et `core::shapeHits` (`Core/Combat/CombatSpace.h`).
 *
 * ## En distance
 *
 * Une créature est prise si son **volume croise** la forme — un bord suffit — et si l'origine ne
 * la tient pas sous abri total (`core::coverFromPoint`) : un mur entre l'origine et elle l'en
 * protège, un corps ne la protège pas. Plus de demi-case couverte : la forme est exacte.
 *
 * ## Hors de ce fichier
 *
 * Le déplacement de l'origine derrière un obstacle quand l'incantateur vise un point qu'il ne voit
 * pas, et les sorts qui emploient ces zones : avec les classes, qui les apportent.
 */

#include <vector>

#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/CombatTypes.h"

namespace core {

class CombatState;

/**
 * @brief Les combattants posés que la zone prend — volume croisé, pas d'abri total depuis
 *        l'origine —, par identifiant croissant, corps à terre compris.
 */
[[nodiscard]] std::vector<CombatantId> combatantsInArea(const CombatState& combat,
                                                        const Effect& area);

}  // namespace core
