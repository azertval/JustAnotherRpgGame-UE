// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <memory>
#include <typeindex>
#include <unordered_map>
#include <vector>

#include "Core/Diagnostics/Assert.h"
#include "Core/Ecs/ComponentPool.h"
#include "Core/Ecs/Entity.h"
#include "Core/Ecs/EntityManager.h"
#include "Core/Ecs/ISystem.h"
#include "Core/Ecs/View.h"

/**
 * @file Core/Ecs/World.h
 * @brief Façade de l'ECS : entités, composants, vues et orchestration des systèmes.
 */

namespace core {

/**
 * @brief Point d'entrée unique de la simulation : possède les entités, les
 *        composants et les systèmes.
 *
 * Le `World` délègue le cycle de vie des entités à un ::core::EntityManager,
 * détient une ::core::ComponentPool par type de composant (créée à la demande)
 * et exécute les systèmes enregistrés **dans l'ordre**, à chaque pas de temps
 * fixe (`EX-ARCH-030`). Il **possède** toutes ses ressources (RAII) : aucun état
 * global, aucune connaissance du rendu (dépendance `HMI → Core` respectée).
 */
class World {
public:
    /**
     * @brief Crée une nouvelle entité vivante.
     * @return Un handle valide.
     */
    [[nodiscard]] Entity createEntity();

    /**
     * @brief Détruit une entité et retire ses composants de toutes les pools.
     * @param entity Entité à détruire ; sans effet si elle n'est pas vivante.
     */
    void destroyEntity(Entity entity);

    /**
     * @brief Indique si une entité est vivante.
     * @param entity Handle à tester.
     * @return `true` si l'entité est vivante.
     */
    [[nodiscard]] bool isAlive(Entity entity) const;

    /**
     * @brief Attache un composant à une entité.
     * @tparam T        Type de composant (donnée pure).
     * @param entity    Entité destinataire (supposée vivante, sans ce composant).
     * @param component Valeur du composant.
     */
    template <typename T>
    void addComponent(Entity entity, const T& component) {
        JADG_ASSERT(isAlive(entity), "Ajout d'un composant sur une entite morte.");
        poolFor<T>().add(entity, component);
    }

    /**
     * @brief Indique si une entité possède un composant d'un type donné.
     * @tparam T     Type de composant.
     * @param entity Entité testée.
     * @return `true` si le composant est présent.
     */
    template <typename T>
    [[nodiscard]] bool hasComponent(Entity entity) const {
        const ComponentPool<T>* pool = findPool<T>();
        return pool != nullptr && pool->has(entity);
    }

    /**
     * @brief Accède au composant d'une entité (lecture-écriture).
     * @tparam T     Type de composant.
     * @param entity Entité porteuse du composant.
     * @return Une référence sur le composant.
     * @pre L'entité possède ce composant (hasComponent<T>() == true).
     */
    template <typename T>
    [[nodiscard]] T& getComponent(Entity entity) {
        JADG_ASSERT(hasComponent<T>(entity), "L'entite ne possede pas ce composant.");
        return poolFor<T>().get(entity);
    }

    /**
     * @brief Retire le composant d'un type donné d'une entité.
     * @tparam T     Type de composant.
     * @param entity Entité dont le composant est retiré.
     * @pre L'entité possède ce composant (hasComponent<T>() == true).
     */
    template <typename T>
    void removeComponent(Entity entity) {
        JADG_ASSERT(hasComponent<T>(entity), "L'entite ne possede pas ce composant.");
        poolFor<T>().remove(entity);
    }

    /**
     * @brief Construit une vue sur les entités possédant tous les composants demandés.
     * @tparam Components Types de composants requis (distincts).
     * @return Une ::core::View joignant les pools correspondantes.
     */
    template <typename... Components>
    [[nodiscard]] View<Components...> view() {
        return View<Components...>(poolFor<Components>()...);
    }

    /**
     * @brief Enregistre un système ; l'ordre d'enregistrement fixe l'ordre d'exécution.
     * @param system Système à ajouter (le `World` en prend possession).
     */
    void addSystem(std::unique_ptr<ISystem> system);

    /**
     * @brief Exécute tous les systèmes enregistrés, dans l'ordre, pour un pas fixe.
     * @param fixedDelta Durée du pas de simulation, en secondes.
     */
    void update(float fixedDelta);

    /// @return Nombre de systèmes enregistrés.
    [[nodiscard]] std::size_t systemCount() const;

private:
    /**
     * @brief Récupère la pool du type `T`, en la créant à la première demande.
     * @tparam T Type de composant.
     * @return Une référence sur la pool typée.
     */
    template <typename T>
    ComponentPool<T>& poolFor() {
        const std::type_index key(typeid(T));
        auto iterator = _pools.find(key);
        if (iterator == _pools.end()) {
            iterator = _pools.emplace(key, std::make_unique<ComponentPool<T>>()).first;
        }
        return *static_cast<ComponentPool<T>*>(iterator->second.get());
    }

    /**
     * @brief Récupère la pool du type `T` sans la créer.
     * @tparam T Type de composant.
     * @return Un pointeur sur la pool, ou `nullptr` si aucune pool de ce type n'existe.
     */
    template <typename T>
    const ComponentPool<T>* findPool() const {
        const auto iterator = _pools.find(std::type_index(typeid(T)));
        if (iterator == _pools.end()) {
            return nullptr;
        }
        return static_cast<const ComponentPool<T>*>(iterator->second.get());
    }

    /// Cycle de vie des entités.
    EntityManager _entities;
    /// Pools de composants, une par type (clé = type du composant).
    std::unordered_map<std::type_index, std::unique_ptr<IComponentPool>> _pools;
    /// Systèmes enregistrés, exécutés dans l'ordre d'insertion.
    std::vector<std::unique_ptr<ISystem>> _systems;
};

}  // namespace core
