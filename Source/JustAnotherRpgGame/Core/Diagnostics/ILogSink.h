// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <string_view>

#include "Core/Diagnostics/LogLevel.h"

/**
 * @file Core/Diagnostics/ILogSink.h
 * @brief Interface d'une destination de journalisation.
 */

namespace core {

/// Destination vers laquelle un `Logger` diffuse ses messages.
class ILogSink {
public:
    virtual ~ILogSink() = default;

    /**
     * @brief Restitue un message.
     * @param level   Niveau du message.
     * @param message Texte du message (déjà formaté par l'appelant le cas échéant).
     */
    virtual void write(LogLevel level, std::string_view message) = 0;
};

}  // namespace core
