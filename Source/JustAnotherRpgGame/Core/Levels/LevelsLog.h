// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Core/Diagnostics/Log.h"

/**
 * @file Core/Levels/LevelsLog.h
 * @brief Macros de journalisation de la catégorie « Levels ».
 *
 * Sous-catégorie de log du module `Levels` (voir `HMI/HmiLog.h` pour le modèle). Réservée aux
 * événements de cycle de vie (chargement, échec de validation), jamais aux opérations exécutées
 * à chaque pas fixe ou par tuile.
 */

#define LEVELS_LOG_TRACE(message) JADG_LOG_TRACE("Levels", message)
#define LEVELS_LOG_INFO(message) JADG_LOG_INFO("Levels", message)
#define LEVELS_LOG_WARNING(message) JADG_LOG_WARNING("Levels", message)
#define LEVELS_LOG_ERROR(message) JADG_LOG_ERROR("Levels", message)
