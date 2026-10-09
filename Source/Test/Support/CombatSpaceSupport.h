// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Test/Support/CombatSpaceSupport.h
 * @brief Les espaces de combat des tests (`LOT-1017`) : une salle lue d'une grille de collision,
 *        et les places des cases.
 *
 * Les tests écrits sur la grille posent leurs combattants sur des cases : ils se rejouent en
 * mètres au centre de ces cases (`core::tileCenter`), dans l'espace simulé que la grille de
 * collision donne (`core::SimulatedSpace::fromTileMap`).
 */

#include <memory>

#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/SimulatedSpace.h"
#include "Core/Levels/TileMap.h"
#include "Core/Rpg/RpgEnums.h"

namespace test_support {

/// @return L'espace simulé de @p collision, partagé comme le combat le tient.
inline std::shared_ptr<core::SimulatedSpace> spaceOf(const core::TileMap& collision) {
    return std::make_shared<core::SimulatedSpace>(core::SimulatedSpace::fromTileMap(collision));
}

/// @return Une salle de @p columns × @p rows cases, sans mur.
inline std::shared_ptr<core::SimulatedSpace> openSpace(int columns, int rows) {
    return spaceOf(core::TileMap(columns, rows));
}

/// @return Le centre, au sol, de l'emprise de taille @p size dont la case haut-gauche est
/// (@p column, @p row).
inline core::Meters3 tile(int column, int row,
                          core::CreatureSize size = core::CreatureSize::Medium) {
    return core::tileCenter({column, row}, size);
}

}  // namespace test_support
