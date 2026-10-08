// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Time/FixedTimestep.h
 * @brief Cadenceur à pas de temps fixe pour une simulation déterministe.
 */

namespace core {

/**
 * @brief Convertit un temps réel écoulé variable en un nombre de pas de simulation fixes.
 *
 * Accumule le temps réel fourni par l'appelant et le découpe en pas de durée
 * constante, garantissant une simulation déterministe indépendante du framerate.
 * Un plafond du nombre de pas par appel évite la « spirale de la mort » lorsque
 * le temps écoulé devient très grand (fenêtre gelée, point d'arrêt…).
 *
 * La classe ne mesure pas le temps elle-même (aucune dépendance système) : le
 * temps réel écoulé lui est passé en paramètre, ce qui la rend testable en isolation.
 */
class FixedTimestep {
public:
    /**
     * @brief Construit un cadenceur.
     * @param fixedDeltaSeconds   Durée d'un pas de simulation, en secondes (défaut : 1/60).
     * @param maximumStepsPerCall Nombre maximal de pas restitués par appel à advance()
     * (anti-spirale).
     */
    explicit FixedTimestep(float fixedDeltaSeconds = 1.0f / 60.0f, int maximumStepsPerCall = 5);

    /**
     * @brief Accumule le temps écoulé et renvoie le nombre de pas fixes à exécuter.
     * @param elapsedSeconds Temps réel écoulé depuis le dernier appel, en secondes.
     * @return Nombre de pas de simulation à exécuter (0 si le seuil n'est pas atteint).
     */
    [[nodiscard]] int advance(float elapsedSeconds);

    /**
     * @brief Durée d'un pas de simulation.
     * @return Le pas fixe, en secondes.
     */
    [[nodiscard]] float fixedDeltaSeconds() const;

    /**
     * @brief Fraction de pas restant dans l'accumulateur, pour l'interpolation du rendu.
     * @return Un facteur dans l'intervalle [0, 1[.
     */
    [[nodiscard]] float interpolationAlpha() const;

private:
    float _fixedDeltaSeconds;
    int _maximumStepsPerCall;
    float _accumulator;
};

}  // namespace core
