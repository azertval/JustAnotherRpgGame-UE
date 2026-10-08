// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <string_view>

#include "Core/Diagnostics/ILogSink.h"
#include "Core/Diagnostics/LogLevel.h"

/**
 * @file Core/Diagnostics/ConsoleLogSink.h
 * @brief Sink écrivant sur la console (et le débogueur sous Windows).
 */

namespace core {

/// Sink qui écrit les messages sur la sortie standard et, sous Windows, vers le débogueur.
class ConsoleLogSink : public ILogSink {
public:
    void write(LogLevel level, std::string_view message) override;
};

}  // namespace core
