// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Core/Diagnostics/LogLevel.h"
#include "Core/Diagnostics/Logger.h"

/**
 * @file Core/Diagnostics/ScopedLogLevel.h
 * @brief Élévation temporaire (RAII) du niveau minimal d'un `Logger`.
 */

namespace core {

/**
 * @brief Relève le niveau minimal de @p logger à au moins @p floor pour la durée de vie de
 * l'objet, et restaure le niveau précédent à la destruction.
 *
 * N'assouplit jamais un niveau déjà plus strict que @p floor : un utilisateur qui a explicitement
 * demandé `--log-level=error` reste à `error` même à l'intérieur d'une portée qui ne demande que
 * `warning`. Sert à faire taire les traces de cycle de vie (chargement de carte, ouverture d'un
 * catalogue…) pendant un traitement répété sans joueur — un volume de journalisation sans rapport
 * avec une partie réelle, qui ralentit le traitement pour rien.
 *
 * **Réentrant et sûr entre fils** : la comptabilité vit dans le `Logger`
 * (`beginLevelElevation`/`endLevelElevation`), pas dans chaque objet de portée. Deux portées qui se
 * chevauchent — deux traitements lancés chacun sur son fil — restauraient sinon le niveau que la
 * première avait relevé, laissant le journal muet pour le reste de la session.
 */
class ScopedLogLevel {
public:
    ScopedLogLevel(Logger& logger, LogLevel floor) : _logger(logger) {
        _logger.beginLevelElevation(floor);
    }

    ~ScopedLogLevel() {
        _logger.endLevelElevation();
    }

    ScopedLogLevel(const ScopedLogLevel&) = delete;
    ScopedLogLevel& operator=(const ScopedLogLevel&) = delete;

private:
    Logger& _logger;
};

}  // namespace core
