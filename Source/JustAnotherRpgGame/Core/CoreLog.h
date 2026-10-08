// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Core/Diagnostics/Log.h"

/**
 * @file Core/CoreLog.h
 * @brief Macros de journalisation de la catégorie « Core ».
 *
 * Sous-catégorie de log du module `Core` (voir `HMI/HmiLog.h` pour le modèle). À réserver aux
 * événements de cycle de vie ; ne jamais journaliser dans les chemins exécutés à chaque frame.
 */

#define CORE_LOG_TRACE(message) JADG_LOG_TRACE("Core", message)
#define CORE_LOG_INFO(message) JADG_LOG_INFO("Core", message)
#define CORE_LOG_WARNING(message) JADG_LOG_WARNING("Core", message)
#define CORE_LOG_ERROR(message) JADG_LOG_ERROR("Core", message)
