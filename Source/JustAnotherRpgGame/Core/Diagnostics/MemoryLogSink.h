// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <string>
#include <string_view>
#include <vector>

#include "Core/Diagnostics/ILogSink.h"
#include "Core/Diagnostics/LogLevel.h"

/**
 * @file Core/Diagnostics/MemoryLogSink.h
 * @brief Sink qui conserve les messages en mémoire, destiné aux tests.
 */

namespace core {

/// Sink de test : mémorise les messages reçus pour inspection.
class MemoryLogSink : public ILogSink {
public:
    /// Un message reçu (niveau + texte).
    struct Entry {
        LogLevel level;
        std::string message;
    };

    void write(LogLevel level, std::string_view message) override {
        _entries.push_back(Entry{level, std::string(message)});
    }

    /// @return Les messages reçus, dans l'ordre d'arrivée.
    [[nodiscard]] const std::vector<Entry>& entries() const {
        return _entries;
    }

    /// Vide les messages mémorisés.
    void clear() {
        _entries.clear();
    }

private:
    std::vector<Entry> _entries;
};

}  // namespace core
