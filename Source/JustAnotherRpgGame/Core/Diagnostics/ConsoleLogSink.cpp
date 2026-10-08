// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Diagnostics/ConsoleLogSink.h"

#include <iostream>
#include <string>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <Windows.h>
#endif

namespace core {

// Restitue un message sur la console.
void ConsoleLogSink::write(LogLevel level, std::string_view message) {
    // Les avertissements et erreurs partent sur la sortie d'erreur, le reste sur
    // la sortie standard.
    std::ostream& stream = (level >= LogLevel::Warning) ? std::cerr : std::cout;
    // Flush immédiat : les journaux restent visibles même en cas d'arrêt brutal.
    stream << message << '\n';

#ifdef _WIN32
    // Double la sortie vers la fenêtre de débogage de Visual Studio.
    const std::string line = std::string(message) + '\n';
    OutputDebugStringA(line.c_str());
#endif
}

}  // namespace core
