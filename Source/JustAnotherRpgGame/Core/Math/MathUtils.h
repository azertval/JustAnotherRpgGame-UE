// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <cmath>

/**
 * @file Core/Math/MathUtils.h
 * @brief Utilitaires mathématiques minimaux de `Core` (comparaisons flottantes).
 */

namespace core {

/// Tolérance par défaut pour les comparaisons de flottants issus de calculs.
inline constexpr float EPSILON = 1e-5f;

/**
 * @brief Compare deux flottants à une tolérance relative-absolue près.
 *
 * Évite les faux négatifs des comparaisons `==` brutes sur des résultats
 * calculés, tout en restant robuste pour les grandes magnitudes (tolérance
 * mise à l'échelle par le plus grand opérande).
 *
 * @param lhs       Premier opérande.
 * @param rhs       Second opérande.
 * @param tolerance Tolérance de base (défaut : ::core::EPSILON).
 * @return `true` si les deux valeurs sont égales à la tolérance près.
 */
[[nodiscard]] inline bool approximatelyEqual(float lhs, float rhs, float tolerance = EPSILON) {
    const float difference = std::fabs(lhs - rhs);
    const float scale = std::fmax(std::fabs(lhs), std::fabs(rhs));
    return difference <= tolerance * std::fmax(1.0f, scale);
}

}  // namespace core
