// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Ecs/ISystem.h
 * @brief Interface d'un système de l'ECS : logique exécutée au pas de temps fixe.
 */

namespace core {

class World;

/**
 * @brief Interface d'un système : porte la logique itérant sur les composants.
 *
 * Un système ne détient aucun état de simulation (celui-ci vit dans les
 * composants du ::core::World) : il lit et met à jour les composants via les
 * vues du monde. Les systèmes sont enregistrés dans le `World` et exécutés
 * **dans l'ordre** à chaque pas de temps fixe (`EX-ARCH-030`).
 */
class ISystem {
public:
    virtual ~ISystem() = default;

    /**
     * @brief Exécute un pas de simulation du système.
     * @param world      Monde sur lequel opérer (accès aux entités, composants, vues).
     * @param fixedDelta Durée du pas de simulation, en secondes (constante).
     */
    virtual void update(World& world, float fixedDelta) = 0;
};

}  // namespace core
