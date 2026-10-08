// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/AreaOfEffect.h
 * @brief Les zones d'effet sur la grille tactique (`LOT-22`) : cône, cube, cylindre, ligne,
 *        sphère.
 *
 * ## Ce que dit le Manuel
 *
 * Chapitre 10, « Zones d'effet » : chaque zone a un **point d'origine**, et l'effet « s'étend en
 * lignes droites » depuis ce point — un emplacement qu'aucune ligne droite ne relie à l'origine
 * n'est pas dans la zone, et seul un abri total bloque ces lignes. Puis les cinq formes :
 *
 * - **cône** — sa largeur en un point égale la distance à l'origine ; l'origine n'est pas incluse ;
 * - **cube** — l'origine est sur une face ; la taille est l'arête ; l'origine n'est pas incluse ;
 * - **cylindre** — l'origine est le centre du disque de base ; incluse ;
 * - **ligne** — une longueur et une largeur ; l'origine n'est pas incluse ;
 * - **sphère** — un rayon depuis l'origine ; incluse.
 *
 * ## Sur la grille : la moitié d'une case
 *
 * Le Manuel ne dit pas quelles cases une forme couvre. Une case est **dans la zone si la forme en
 * couvre au moins la moitié** — la règle du *Guide du Maître* pour les zones circulaires, étendue
 * aux autres formes plutôt que d'en inventer une par forme. La surface se calcule exactement : un
 * cône, un cube et une ligne sont des polygones découpés par la case ; un disque s'intègre.
 *
 * Le point d'origine est un `core::GridPoint`, en demi-cases : un coin de case pour une boule de
 * feu lancée sur une intersection, le milieu de l'arête d'une créature pour un souffle en ligne,
 * son centre pour une aura. « L'origine n'est pas incluse » tombe alors de la géométrie : un cône
 * qui part du bord d'une créature ne couvre rien de sa case.
 *
 * ## L'altitude
 *
 * Le jeu n'a pas de hauteur (`core::Locomotion`) : un cylindre est son disque, une sphère le sien.
 * Les deux formes restent distinctes parce que le Manuel les distingue, et qu'un sort les nomme.
 *
 * ## Hors de ce fichier
 *
 * Le déplacement de l'origine derrière un obstacle quand l'incantateur vise un point qu'il ne voit
 * pas, et les sorts qui emploient ces zones : avec les classes, qui les apportent.
 */

#include <cstdint>
#include <optional>
#include <vector>

#include "Core/Combat/BattleGrid.h"
#include "Core/Combat/LineOfSight.h"
#include "Core/Levels/GridPosition.h"

namespace core {

class CombatState;

/// @brief Les cinq formes du Manuel.
enum class AreaShape : std::uint8_t {
    Cone,
    Cube,
    Cylinder,
    Line,
    Sphere,
};

/**
 * @brief Une zone posée sur la grille.
 *
 * Les tailles sont en **cases** (`core::areaTilesFromMeters` pour celles du corpus, en mètres).
 */
struct AreaOfEffect {
    AreaShape shape = AreaShape::Sphere;
    /// Le point d'origine, en demi-cases.
    GridPoint origin;
    /// Un point vers lequel s'étendent le cône, le cube et la ligne ; ignoré par la sphère et le
    /// cylindre. Confondu avec l'origine, la zone est vide : sans direction, rien ne s'étend.
    GridPoint toward;
    /// Rayon (sphère, cylindre), longueur (cône, ligne) ou arête (cube), en cases.
    int size = 1;
    /// Largeur d'une ligne, en cases. Ignorée par les autres formes.
    int width = 1;
};

/**
 * @brief Une taille de zone du corpus, en cases : 6 m font 4 cases, 4,50 m en font 3.
 *
 * Arrondie **vers le bas** : une zone ne déborde jamais de ce que le texte promet. Vide pour une
 * taille nulle ou négative.
 */
[[nodiscard]] std::optional<int> areaTilesFromMeters(float meters);

/**
 * @brief Les cases qu'une forme couvre au moins à moitié, dans une grille de @p columns ×
 *        @p rows, **sans** obstacle : le gabarit seul.
 *
 * Ordonnées par ligne puis par colonne.
 */
[[nodiscard]] std::vector<GridPosition> areaTemplate(const AreaOfEffect& area, int columns,
                                                     int rows);

/**
 * @brief Les cases réellement atteintes : le gabarit, moins celles qu'aucune ligne droite ne relie
 *        à l'origine sans traverser ce qui arrête la vue.
 *
 * Une case est atteinte si un segment dégagé (`core::isSightClear`) relie l'origine à l'un de ses
 * quatre coins : c'est le même compte que l'abri total, et une cible qu'il protège entièrement de
 * l'origine est hors de la zone. Une case qui arrête elle-même la vue — le mur — n'est pas un
 * emplacement de la zone : l'effet s'y heurte.
 */
[[nodiscard]] std::vector<GridPosition> affectedCells(const BattleGrid& grid,
                                                      const AreaOfEffect& area);

/// @brief Les combattants dont une case au moins est atteinte, par identifiant croissant.
[[nodiscard]] std::vector<CombatantId> combatantsInArea(const CombatState& combat,
                                                        const AreaOfEffect& area);

}  // namespace core
