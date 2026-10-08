// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Core/Diagnostics/Log.h"

/**
 * @file Core/Ecs/EcsLog.h
 * @brief Macros de journalisation de la catégorie « Ecs ».
 *
 * Sous-catégorie de log de l'ECS (voir `HMI/HmiLog.h` pour le modèle). L'ECS s'exécute à
 * chaque frame : réserver la journalisation aux événements rares (enregistrement de systèmes,
 * mise en place d'un monde), jamais aux opérations par entité ou par frame.
 */

#define ECS_LOG_TRACE(message) JADG_LOG_TRACE("Ecs", message)
#define ECS_LOG_INFO(message) JADG_LOG_INFO("Ecs", message)
#define ECS_LOG_WARNING(message) JADG_LOG_WARNING("Ecs", message)
#define ECS_LOG_ERROR(message) JADG_LOG_ERROR("Ecs", message)
