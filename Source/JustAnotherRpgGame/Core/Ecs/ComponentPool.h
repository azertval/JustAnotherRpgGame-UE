// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <cstddef>
#include <vector>

#include "Core/Diagnostics/Assert.h"
#include "Core/Ecs/Entity.h"

/**
 * @file Core/Ecs/ComponentPool.h
 * @brief Stockage typé des composants d'un ECS sous forme de sparse set.
 */

namespace core {

/**
 * @brief Interface type-effacée d'une pool de composants.
 *
 * Permet au ::core::World de détenir des pools de types hétérogènes dans un même
 * conteneur et d'agir dessus sans connaître le type concret — notamment pour
 * retirer les composants d'une entité détruite dans **toutes** les pools.
 */
class IComponentPool {
public:
    virtual ~IComponentPool() = default;

    /**
     * @brief Retire le composant d'une entité s'il existe.
     * @param entity Entité éventuellement porteuse d'un composant.
     * @return `true` si un composant a été retiré, `false` sinon.
     */
    virtual bool removeIfPresent(Entity entity) = 0;
};

/**
 * @brief Stockage dense des composants d'un type `T`, indexé par entité (sparse set).
 *
 * Combine deux structures pour concilier itération rapide et accès direct :
 * - un tableau **dense** de composants, contigu en mémoire (itération
 *   cache-friendly par les systèmes) et son tableau parallèle des entités
 *   propriétaires ;
 * - un tableau **creux** indexé par ::core::Entity::index, associant chaque
 *   entité à la position de son composant dans le tableau dense (accès en temps
 *   constant).
 *
 * La suppression se fait par *swap-and-pop* : le composant retiré est échangé
 * avec le dernier avant d'être retranché, ce qui maintient la densité sans
 * décaler tout le tableau.
 *
 * @warning Les références renvoyées par get() sont invalidées par tout add()
 *          (réallocation possible) ou remove() (déplacement du dernier élément).
 *          Ne pas conserver une référence à un composant au-delà de telles
 *          opérations sur la même pool.
 *
 * @tparam T Type de composant stocké. Doit être une donnée pure (`EX-ARCH-011`).
 */
template <typename T>
class ComponentPool : public IComponentPool {
public:
    /// Position dense réservée signifiant « aucun composant pour cette entité ».
    static constexpr std::size_t INVALID_POSITION = ~std::size_t{0};

    /**
     * @brief Attache un composant à une entité.
     * @param entity    Entité destinataire ; ne doit pas déjà posséder ce composant.
     * @param component Valeur du composant à copier dans le tableau dense.
     * @pre L'entité ne possède pas encore de composant de ce type (has() == false).
     */
    void add(Entity entity, const T& component) {
        JADG_ASSERT(!has(entity), "L'entite possede deja ce composant.");

        ensureSparseSize(entity.index);
        _sparse[entity.index] = _components.size();
        _components.push_back(component);
        _entities.push_back(entity);
    }

    /**
     * @brief Retire le composant d'une entité (swap-and-pop).
     * @param entity Entité dont le composant est retiré.
     * @pre L'entité possède ce composant (has() == true).
     */
    void remove(Entity entity) {
        JADG_ASSERT(has(entity), "L'entite ne possede pas ce composant.");

        const std::size_t removed = _sparse[entity.index];
        const std::size_t last = _components.size() - 1;

        // Swap-and-pop : on remonte le dernier élément à la place du supprimé
        // pour garder le tableau dense contigu, puis on met à jour le creux de
        // l'entité déplacée pour qu'il pointe vers sa nouvelle position.
        _components[removed] = _components[last];
        _entities[removed] = _entities[last];
        _sparse[_entities[removed].index] = removed;

        _components.pop_back();
        _entities.pop_back();
        _sparse[entity.index] = INVALID_POSITION;
    }

    /**
     * @brief Retire le composant d'une entité s'il existe (sans précondition).
     * @param entity Entité éventuellement porteuse du composant.
     * @return `true` si un composant a été retiré, `false` s'il n'y en avait pas.
     */
    bool removeIfPresent(Entity entity) override {
        if (!has(entity)) {
            return false;
        }
        remove(entity);
        return true;
    }

    /**
     * @brief Indique si une entité possède un composant de ce type.
     * @param entity Entité testée.
     * @return `true` si un composant est associé à cette entité (génération incluse).
     */
    [[nodiscard]] bool has(Entity entity) const {
        if (entity.index >= _sparse.size()) {
            return false;
        }
        const std::size_t position = _sparse[entity.index];
        // Position valide et pointant une entrée dont l'entité correspond
        // exactement (l'égalité inclut la génération : un handle périmé échoue).
        return position != INVALID_POSITION && _entities[position] == entity;
    }

    /**
     * @brief Accède au composant d'une entité (lecture-écriture).
     * @param entity Entité porteuse du composant.
     * @return Une référence sur le composant stocké.
     * @pre L'entité possède ce composant (has() == true).
     */
    [[nodiscard]] T& get(Entity entity) {
        JADG_ASSERT(has(entity), "L'entite ne possede pas ce composant.");
        return _components[_sparse[entity.index]];
    }

    /**
     * @brief Accède au composant d'une entité (lecture seule).
     * @param entity Entité porteuse du composant.
     * @return Une référence constante sur le composant stocké.
     * @pre L'entité possède ce composant (has() == true).
     */
    [[nodiscard]] const T& get(Entity entity) const {
        JADG_ASSERT(has(entity), "L'entite ne possede pas ce composant.");
        return _components[_sparse[entity.index]];
    }

    /// @return Nombre de composants actuellement stockés.
    [[nodiscard]] std::size_t size() const {
        return _components.size();
    }

    /// @return `true` si la pool ne contient aucun composant.
    [[nodiscard]] bool empty() const {
        return _components.empty();
    }

    /**
     * @brief Entités possédant un composant, dans l'ordre du tableau dense.
     * @return Une référence constante sur le tableau dense des entités.
     */
    [[nodiscard]] const std::vector<Entity>& entities() const {
        return _entities;
    }

    /**
     * @brief Composants stockés, dans l'ordre du tableau dense.
     * @return Une référence constante sur le tableau dense des composants.
     */
    [[nodiscard]] const std::vector<T>& components() const {
        return _components;
    }

private:
    /**
     * @brief Agrandit le tableau creux pour qu'il couvre un index d'entité donné.
     * @param index Index d'entité à rendre adressable dans le tableau creux.
     */
    void ensureSparseSize(Entity::Index index) {
        if (index >= _sparse.size()) {
            _sparse.resize(static_cast<std::size_t>(index) + 1, INVALID_POSITION);
        }
    }

    /// Tableau dense des composants (contigu, cache-friendly).
    std::vector<T> _components;
    /// Entités propriétaires, parallèle à `_components`.
    std::vector<Entity> _entities;
    /// Position dense de chaque entité, indexé par Entity::index (INVALID_POSITION si absente).
    std::vector<std::size_t> _sparse;
};

}  // namespace core
