// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <string>

/**
 * @file Core/Core.h
 * @brief Interface publique de la bibliothèque Core (moteur / logique de jeu).
 */

/// Espace de noms du moteur et de la logique de jeu.
namespace core {

/**
 * @brief Fournit les informations globales du moteur.
 *
 * Sans état : une seule fonction statique, qui expose le numéro de version du moteur. Elle existe
 * pour que ce numéro ait **un** point d'accès depuis le code, alimenté par le système de build
 * plutôt que recopié — voir `version()` ci-dessous.
 */
class Engine {
public:
    /**
     * @brief Retourne la version du moteur, telle que déclarée par le système de build.
     *
     * La chaîne provient de `project(... VERSION ...)` (CMakeLists.txt racine), transmise à la
     * compilation : elle **ne peut pas** diverger du numéro que porte la release, contrairement
     * à une constante recopiée dans le code.
     *
     * @return Chaîne de version sémantique (par exemple "0.0.5").
     */
    static std::string version();
};

}  // namespace core
