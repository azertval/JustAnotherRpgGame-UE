// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Diagnostics/Assert.h"

#include <cstdlib>
#include <string>
#include <utility>

#include "Core/Diagnostics/LogFormat.h"
#include "Core/Diagnostics/LogLevel.h"
#include "Core/Diagnostics/Logger.h"

namespace core {

namespace {
// Gestionnaire courant, avec un comportement par défaut : journaliser puis abandonner.
AssertionHandler& currentHandler() {
    static AssertionHandler handler = [](const char* condition, const char* message,
                                         const char* file, int line) {
        const std::string text = std::string("Assertion echouee (") + condition + ") : " + message;
        defaultLogger().log(LogLevel::Error, formatLogLine(currentTimestamp(), LogLevel::Error,
                                                           "Assert", file, line, text));
        std::abort();
    };
    return handler;
}
}  // namespace

void setAssertionHandler(AssertionHandler handler) {
    currentHandler() = std::move(handler);
}

void handleAssertionFailure(const char* condition, const char* message, const char* file,
                            int line) {
    // Un gestionnaire nul rend l'échec silencieux (utile pour certains tests).
    if (currentHandler()) {
        currentHandler()(condition, message, file, line);
    }
}

}  // namespace core
