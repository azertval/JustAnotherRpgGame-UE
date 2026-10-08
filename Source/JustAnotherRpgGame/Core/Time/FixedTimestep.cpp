// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Time/FixedTimestep.h"

#include <string>

#include "Core/CoreLog.h"

namespace core {

// Construit un cadenceur.
FixedTimestep::FixedTimestep(float fixedDeltaSeconds, int maximumStepsPerCall)
    : _fixedDeltaSeconds(fixedDeltaSeconds),
      _maximumStepsPerCall(maximumStepsPerCall),
      _accumulator(0.0F) {
    CORE_LOG_TRACE("Cadenceur a pas fixe : " + std::to_string(fixedDeltaSeconds) + " s/pas (max " +
                   std::to_string(maximumStepsPerCall) + " pas/appel)");
}

// Accumule le temps écoulé et renvoie le nombre de pas fixes à exécuter.
// Nombre de pas de simulation à exécuter (0 si le seuil n'est pas atteint).
int FixedTimestep::advance(float elapsedSeconds) {
    // Un temps écoulé négatif ou nul n'apporte aucun pas : on ignore les valeurs
    // aberrantes (horloge non monotone) plutôt que de reculer l'accumulateur.
    if (elapsedSeconds > 0.0F) {
        _accumulator += elapsedSeconds;
    }

    // Découpe l'accumulateur en pas fixes, en s'arrêtant au plafond pour ne pas
    // bloquer l'appelant sur une rafale de rattrapage.
    int steps = 0;
    while (_accumulator >= _fixedDeltaSeconds && steps < _maximumStepsPerCall) {
        _accumulator -= _fixedDeltaSeconds;
        ++steps;
    }

    // Plafond atteint : il reste plus de temps que ce que l'on peut rattraper.
    // On abandonne ce retard (reset de l'accumulateur) pour éviter la spirale de
    // la mort, où chaque frame accumulerait davantage qu'elle ne consomme.
    if (steps == _maximumStepsPerCall && _accumulator >= _fixedDeltaSeconds) {
        _accumulator = 0.0F;
    }

    return steps;
}

// Durée d'un pas de simulation.
// Le pas fixe, en secondes.
float FixedTimestep::fixedDeltaSeconds() const {
    return _fixedDeltaSeconds;
}

// Fraction de pas restant dans l'accumulateur, pour l'interpolation du rendu.
// Un facteur dans l'intervalle [0, 1[.
float FixedTimestep::interpolationAlpha() const {
    return _accumulator / _fixedDeltaSeconds;
}

}  // namespace core
