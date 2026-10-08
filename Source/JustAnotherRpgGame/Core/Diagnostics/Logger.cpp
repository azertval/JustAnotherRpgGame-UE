// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Diagnostics/Logger.h"

#include <mutex>
#include <utility>

namespace core {

void Logger::setMinimumLevel(LogLevel level) {
    _minimumLevel.store(level, std::memory_order_relaxed);
}

bool Logger::isEnabled(LogLevel level) const {
    return level >= _minimumLevel.load(std::memory_order_relaxed);
}

void Logger::beginLevelElevation(LogLevel floor) {
    const std::lock_guard<std::mutex> guard(_elevationMutex);
    if (_elevationDepth == 0) {
        _levelBeforeElevation = minimumLevel();
    }
    ++_elevationDepth;
    // N'assouplit jamais un niveau deja plus strict : un utilisateur qui a demande `error` reste a
    // `error` meme dans une portee qui ne demande que `warning`.
    if (minimumLevel() < floor) {
        setMinimumLevel(floor);
    }
}

void Logger::endLevelElevation() {
    const std::lock_guard<std::mutex> guard(_elevationMutex);
    if (_elevationDepth == 0) {
        return;
    }
    --_elevationDepth;
    if (_elevationDepth == 0) {
        setMinimumLevel(_levelBeforeElevation);
    }
}

void Logger::addSink(std::unique_ptr<ILogSink> sink) {
    _sinks.push_back(std::move(sink));
}

void Logger::clearSinks() {
    _sinks.clear();
}

// Diffuse un message aux sinks s'il passe le filtre de niveau.
void Logger::log(LogLevel level, std::string_view message) {
    // Filtrage en amont : un message moins grave que le seuil n'est pas diffusé.
    if (!isEnabled(level)) {
        return;
    }
    for (const std::unique_ptr<ILogSink>& sink : _sinks) {
        sink->write(level, message);
    }
}

Logger& defaultLogger() {
    // Instance à durée de vie statique : construite au premier appel, partagée
    // par l'ensemble du programme via les macros de log.
    static Logger instance;
    return instance;
}

}  // namespace core
