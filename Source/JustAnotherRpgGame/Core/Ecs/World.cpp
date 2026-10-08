// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Ecs/World.h"

#include <string>
#include <utility>

#include "Core/Ecs/EcsLog.h"

namespace core {

// Crée une nouvelle entité vivante.
// Un handle valide.
Entity World::createEntity() {
    return _entities.create();
}

// Détruit une entité et retire ses composants de toutes les pools.
void World::destroyEntity(Entity entity) {
    if (!_entities.isAlive(entity)) {
        // Handle déjà détruit ou périmé : rien à faire.
        return;
    }

    // Retire le composant de cette entité dans chaque pool avant de recycler
    // l'index, pour qu'aucune pool ne référence encore l'entité détruite.
    for (auto& entry : _pools) {
        entry.second->removeIfPresent(entity);
    }
    _entities.destroy(entity);
}

// Indique si une entité est vivante.
// `true` si l'entité est vivante.
bool World::isAlive(Entity entity) const {
    return _entities.isAlive(entity);
}

// Enregistre un système ; l'ordre d'enregistrement fixe l'ordre d'exécution.
void World::addSystem(std::unique_ptr<ISystem> system) {
    _systems.push_back(std::move(system));
    ECS_LOG_TRACE("Systeme enregistre (total : " + std::to_string(_systems.size()) + ")");
}

// Exécute tous les systèmes enregistrés, dans l'ordre, pour un pas fixe.
void World::update(float fixedDelta) {
    // Ordre d'exécution déterministe : l'ordre d'enregistrement des systèmes.
    for (const std::unique_ptr<ISystem>& system : _systems) {
        system->update(*this, fixedDelta);
    }
}

// Nombre de systèmes enregistrés.
// Le décompte des systèmes.
std::size_t World::systemCount() const {
    return _systems.size();
}

}  // namespace core
