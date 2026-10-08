// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <atomic>
#include <memory>
#include <mutex>
#include <string_view>
#include <vector>

#include "Core/Diagnostics/ILogSink.h"
#include "Core/Diagnostics/LogLevel.h"

/**
 * @file Core/Diagnostics/Logger.h
 * @brief Journaliseur : filtrage par niveau et diffusion vers des sinks.
 */

namespace core {

/**
 * @brief Filtre les messages par niveau minimal et les diffuse aux sinks enregistrés.
 *
 * Le journaliseur **possède** ses sinks (RAII). Il n'effectue aucune entrée-sortie
 * lui-même : celle-ci est déléguée aux sinks.
 */
class Logger {
public:
    Logger() = default;

    Logger(const Logger&) = delete;
    Logger& operator=(const Logger&) = delete;

    /// Définit le niveau minimal ; les messages moins graves sont ignorés.
    void setMinimumLevel(LogLevel level);

    /// @return Le niveau minimal courant.
    [[nodiscard]] LogLevel minimumLevel() const noexcept {
        return _minimumLevel.load(std::memory_order_relaxed);
    }

    /**
     * @brief Ouvre une **élévation temporaire** du niveau minimal à au moins @p floor.
     *
     * Compte les élévations au lieu de mémoriser un niveau par appelant : l'écran Mode IA peut
     * faire tourner un entraînement et une évaluation **en même temps**, chacun sur son fil, et
     * deux portées qui se chevauchent restauraient alors le niveau que la première avait relevé —
     * laissant le journal muet pour le reste de la session. Le niveau d'origine n'est mémorisé
     * qu'à la première élévation, et restauré à la dernière sortie.
     * @param floor Niveau minimal souhaité ; un niveau déjà plus strict n'est jamais assoupli.
     */
    void beginLevelElevation(LogLevel floor);

    /// Ferme une élévation ouverte par `beginLevelElevation` ; restaure le niveau d'origine
    /// lorsque la dernière élévation en cours se ferme.
    void endLevelElevation();

    /**
     * @brief Indique si un niveau passe le filtre courant.
     * @param level Niveau à tester.
     * @return true si un message de ce niveau serait diffusé.
     */
    [[nodiscard]] bool isEnabled(LogLevel level) const;

    /// Ajoute un sink (le journaliseur en prend la propriété).
    void addSink(std::unique_ptr<ILogSink> sink);

    /// Retire tous les sinks.
    void clearSinks();

    /**
     * @brief Diffuse un message aux sinks s'il passe le filtre de niveau.
     * @param level   Niveau du message.
     * @param message Texte du message.
     */
    void log(LogLevel level, std::string_view message);

private:
    /// Lu à chaque message depuis n'importe quel fil, écrit par les élévations temporaires : le
    /// type atomique n'est pas cosmétique, un `LogLevel` nu était une course de données.
    std::atomic<LogLevel> _minimumLevel = LogLevel::Trace;
    /// Protège le compteur d'élévations et le niveau mémorisé (voir `beginLevelElevation`).
    std::mutex _elevationMutex;
    int _elevationDepth = 0;
    LogLevel _levelBeforeElevation = LogLevel::Trace;
    std::vector<std::unique_ptr<ILogSink>> _sinks;
};

/**
 * @brief Journaliseur global de l'application (utilisé par les macros de log).
 * @return Référence vers l'instance unique.
 */
[[nodiscard]] Logger& defaultLogger();

}  // namespace core
