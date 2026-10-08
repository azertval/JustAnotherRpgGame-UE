// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_view.cpp
 * @brief Tests unitaires de la vue multi-composants de l'ECS.
 */

#include <vector>

#include <gtest/gtest.h>

#include "Core/Ecs/ComponentPool.h"
#include "Core/Ecs/Entity.h"
#include "Core/Ecs/EntityManager.h"
#include "Core/Ecs/View.h"

namespace {
/// Composants de test : données pures minimales.
struct Position {
    int value = 0;
};
struct Velocity {
    int value = 0;
};
}  // namespace

/**
 * @brief Une vue <A, B> itère exactement les entités possédant A et B.
 * \castest{<b>Une vue <A, B> itère exactement les entités possédant A et B.</b><br/>
 * \tcat Unitaire · View<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Une vue <A, B> itère exactement les entités possédant A et B.
 * }
 */
TEST(ViewTest, SelectionneUniquementLIntersection) {
    core::EntityManager manager;
    const core::Entity both = manager.create();  // Position + Velocity
    const core::Entity positionOnly = manager.create();
    const core::Entity velocityOnly = manager.create();

    core::ComponentPool<Position> positions;
    core::ComponentPool<Velocity> velocities;
    positions.add(both, Position{1});
    positions.add(positionOnly, Position{2});
    velocities.add(both, Velocity{10});
    velocities.add(velocityOnly, Velocity{20});

    std::vector<core::Entity> visited;
    core::View<Position, Velocity> view(positions, velocities);
    view.each([&](core::Entity entity, Position&, Velocity&) { visited.push_back(entity); });

    ASSERT_EQ(visited.size(), 1u);
    EXPECT_EQ(visited.front(), both);
}

/**
 * @brief Les composants fournis par la vue correspondent bien à l'entité itérée.
 * \castest{<b>Les composants fournis par la vue correspondent bien à l'entité itérée.</b><br/>
 * \tcat Unitaire · View<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Les composants fournis par la vue correspondent bien à l'entité itérée.
 * }
 */
TEST(ViewTest, ComposantsCorrespondentALEntite) {
    core::EntityManager manager;
    const core::Entity first = manager.create();
    const core::Entity second = manager.create();

    core::ComponentPool<Position> positions;
    core::ComponentPool<Velocity> velocities;
    positions.add(first, Position{1});
    positions.add(second, Position{2});
    velocities.add(first, Velocity{10});
    velocities.add(second, Velocity{20});

    core::View<Position, Velocity> view(positions, velocities);
    view.each([&](core::Entity entity, Position& position, Velocity& velocity) {
        // La vitesse vaut dix fois la position pour chaque entité construite ci-dessus.
        EXPECT_EQ(velocity.value, position.value * 10);
        if (entity == first) {
            EXPECT_EQ(position.value, 1);
        } else {
            EXPECT_EQ(position.value, 2);
        }
    });
}

/**
 * @brief La modification d'un composant via la vue est visible ensuite (référence).
 * \castest{<b>La modification d'un composant via la vue est visible ensuite (référence).</b><br/>
 * \tcat Unitaire · View<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu La modification d'un composant via la vue est visible ensuite (référence).
 * }
 */
TEST(ViewTest, ModificationViaVueEstVisible) {
    core::EntityManager manager;
    const core::Entity entity = manager.create();
    core::ComponentPool<Position> positions;
    core::ComponentPool<Velocity> velocities;
    positions.add(entity, Position{5});
    velocities.add(entity, Velocity{3});

    core::View<Position, Velocity> view(positions, velocities);
    for (auto [visited, position, velocity] : view) {
        position.value += velocity.value;  // 5 + 3
    }

    EXPECT_EQ(positions.get(entity).value, 8);
}

/**
 * @brief Une vue sans entité correspondante s'itère sans erreur (aucune visite).
 * \castest{<b>Une vue sans entité correspondante s'itère sans erreur (aucune visite).</b><br/>
 * \tcat Unitaire · View<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Une vue sans entité correspondante s'itère sans erreur (aucune visite).
 * }
 */
TEST(ViewTest, VueVideNIterePas) {
    core::ComponentPool<Position> positions;
    core::ComponentPool<Velocity> velocities;

    int visits = 0;
    core::View<Position, Velocity> view(positions, velocities);
    view.each([&](core::Entity, Position&, Velocity&) { ++visits; });
    for (auto [entity, position, velocity] : view) {
        (void)entity;
        (void)position;
        (void)velocity;
        ++visits;
    }

    EXPECT_EQ(visits, 0);
}

/**
 * @brief L'itération par `for` visite les mêmes entités que `each`.
 * \castest{<b>L'itération par `for` visite les mêmes entités que `each`.</b><br/>
 * \tcat Unitaire · View<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu L'itération par `for` visite les mêmes entités que `each`.
 * }
 */
TEST(ViewTest, IterationForEtEachCoherentes) {
    core::EntityManager manager;
    const core::Entity a = manager.create();
    const core::Entity b = manager.create();
    const core::Entity aloneWithPosition = manager.create();

    core::ComponentPool<Position> positions;
    core::ComponentPool<Velocity> velocities;
    positions.add(a, Position{1});
    positions.add(b, Position{2});
    positions.add(aloneWithPosition, Position{3});
    velocities.add(a, Velocity{1});
    velocities.add(b, Velocity{2});

    core::View<Position, Velocity> view(positions, velocities);

    std::vector<core::Entity> fromEach;
    view.each([&](core::Entity entity, Position&, Velocity&) { fromEach.push_back(entity); });

    std::vector<core::Entity> fromFor;
    for (auto [entity, position, velocity] : view) {
        (void)position;
        (void)velocity;
        fromFor.push_back(entity);
    }

    EXPECT_EQ(fromEach.size(), 2u);
    EXPECT_EQ(fromFor, fromEach);
}
