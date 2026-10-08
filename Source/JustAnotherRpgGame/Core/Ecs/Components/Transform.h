// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Core/Math/Vector2.h"

/**
 * @file Core/Ecs/Components/Transform.h
 * @brief Composant de placement d'une entité dans le monde (données pures).
 */

namespace core {

/**
 * @brief Position, échelle et rotation d'une entité, en unités monde (`EX-ARCH-020`).
 *
 * Donnée pure sans logique (`EX-ARCH-011`) : les systèmes la lisent et la
 * modifient, le rendu la lit. La rotation est exprimée en **radians**. Les
 * valeurs par défaut décrivent une entité à l'origine, non tournée, à l'échelle 1.
 */
struct Transform {
    /// Position du repère de l'entité, en unités monde (origine haut-gauche, Y-bas).
    Vector2 position{};
    /// Facteurs d'échelle horizontal et vertical (1 = taille nominale).
    Vector2 scale{1.0f, 1.0f};
    /// Rotation autour de l'origine de l'entité, en radians.
    float rotation = 0.0f;
};

}  // namespace core
