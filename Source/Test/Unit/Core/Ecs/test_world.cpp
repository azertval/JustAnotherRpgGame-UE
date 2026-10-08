// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_world.cpp
 * @brief Tests unitaires de la façade `World` de l'ECS.
 */

#include <memory>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Ecs/ISystem.h"
#include "Core/Ecs/World.h"

namespace {
/// Composants de test : données pures minimales.
struct Health {
    int value = 0;
};
struct Position {
    int value = 0;
};

/// Système de test consignant son identifiant à chaque exécution (ordre/décompte).
class RecordingSystem : public core::ISystem {
public:
    RecordingSystem(int identifier, std::vector<int>& log) : _identifier(identifier), _log(&log) {}

    void update(core::World&, float) override {
        _log->push_back(_identifier);
    }

private:
    int _identifier;
    std::vector<int>* _log;
};

/// Système de test mémorisant le dernier `fixedDelta` reçu.
class DeltaProbeSystem : public core::ISystem {
public:
    explicit DeltaProbeSystem(float& lastDelta) : _lastDelta(&lastDelta) {}

    void update(core::World&, float fixedDelta) override {
        *_lastDelta = fixedDelta;
    }

private:
    float* _lastDelta;
};
}  // namespace

/**
 * @brief Le cycle add/has/get/remove d'un composant est cohérent via le `World`.
 * \castest{<b>Le cycle add/has/get/remove d'un composant est cohérent via le `World`.</b><br/>
 * \tcat Unitaire · World<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Le cycle add/has/get/remove d'un composant est cohérent via le `World`.
 * }
 */
TEST(WorldTest, CycleComposant) {
    core::World world;
    const core::Entity entity = world.createEntity();

    EXPECT_FALSE(world.hasComponent<Health>(entity));
    world.addComponent(entity, Health{100});

    EXPECT_TRUE(world.hasComponent<Health>(entity));
    EXPECT_EQ(world.getComponent<Health>(entity).value, 100);

    world.getComponent<Health>(entity).value = 60;
    EXPECT_EQ(world.getComponent<Health>(entity).value, 60);

    world.removeComponent<Health>(entity);
    EXPECT_FALSE(world.hasComponent<Health>(entity));
}

/**
 * @brief `hasComponent` est faux quand aucune pool du type n'existe encore.
 * \castest{<b>`hasComponent` est faux quand aucune pool du type n'existe encore.</b><br/>
 * \tcat Unitaire · World<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `hasComponent` est faux quand aucune pool du type n'existe encore.
 * }
 */
TEST(WorldTest, HasComponentSansPool) {
    core::World world;
    const core::Entity entity = world.createEntity();
    EXPECT_FALSE(world.hasComponent<Health>(entity));
}

/**
 * @brief `destroyEntity` retire l'entité de toutes les pools et la rend non vivante.
 * \castest{<b>`destroyEntity` retire l'entité de toutes les pools et la rend non vivante.</b><br/>
 * \tcat Unitaire · World<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `destroyEntity` retire l'entité de toutes les pools et la rend non vivante.
 * }
 */
TEST(WorldTest, DestroyEntityRetireTousLesComposants) {
    core::World world;
    const core::Entity entity = world.createEntity();
    world.addComponent(entity, Health{50});
    world.addComponent(entity, Position{7});

    world.destroyEntity(entity);

    EXPECT_FALSE(world.isAlive(entity));
    EXPECT_FALSE(world.hasComponent<Health>(entity));
    EXPECT_FALSE(world.hasComponent<Position>(entity));
}

/**
 * @brief Les systèmes enregistrés s'exécutent dans l'ordre d'enregistrement.
 * \castest{<b>Les systèmes enregistrés s'exécutent dans l'ordre d'enregistrement.</b><br/>
 * \tcat Unitaire · World<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Les systèmes enregistrés s'exécutent dans l'ordre d'enregistrement.
 * }
 */
TEST(WorldTest, SystemesExecutesDansLOrdre) {
    core::World world;
    std::vector<int> log;
    world.addSystem(std::make_unique<RecordingSystem>(1, log));
    world.addSystem(std::make_unique<RecordingSystem>(2, log));
    world.addSystem(std::make_unique<RecordingSystem>(3, log));
    EXPECT_EQ(world.systemCount(), 3u);

    world.update(1.0f / 60.0f);

    EXPECT_EQ(log, (std::vector<int>{1, 2, 3}));
}

/**
 * @brief `update` appelé N fois exécute chaque système N fois (cadencement déterministe).
 * \castest{<b>`update` appelé N fois exécute chaque système N fois (cadencement
 * déterministe).</b><br/>
 * \tcat Unitaire · World<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `update` appelé N fois exécute chaque système N fois (cadencement déterministe).
 * }
 */
TEST(WorldTest, UpdateNFoisExecuteNFois) {
    core::World world;
    std::vector<int> log;
    world.addSystem(std::make_unique<RecordingSystem>(42, log));

    const int calls = 5;
    for (int i = 0; i < calls; ++i) {
        world.update(1.0f / 60.0f);
    }

    EXPECT_EQ(log.size(), static_cast<std::size_t>(calls));
}

/**
 * @brief Le `fixedDelta` passé à `update` est transmis tel quel aux systèmes.
 * \castest{<b>Le `fixedDelta` passé à `update` est transmis tel quel aux systèmes.</b><br/>
 * \tcat Unitaire · World<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Le `fixedDelta` passé à `update` est transmis tel quel aux systèmes.
 * }
 */
TEST(WorldTest, FixedDeltaTransmisAuxSystemes) {
    core::World world;
    float observed = 0.0f;
    world.addSystem(std::make_unique<DeltaProbeSystem>(observed));

    world.update(0.25f);

    EXPECT_FLOAT_EQ(observed, 0.25f);
}

/**
 * @brief La vue exposée par le `World` itère l'intersection des composants.
 * \castest{<b>La vue exposée par le `World` itère l'intersection des composants.</b><br/>
 * \tcat Unitaire · World<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu La vue exposée par le `World` itère l'intersection des composants.
 * }
 */
TEST(WorldTest, ViewViaWorld) {
    core::World world;
    const core::Entity both = world.createEntity();
    const core::Entity healthOnly = world.createEntity();
    world.addComponent(both, Health{10});
    world.addComponent(both, Position{1});
    world.addComponent(healthOnly, Health{20});

    std::vector<core::Entity> visited;
    world.view<Health, Position>().each(
        [&](core::Entity entity, Health&, Position&) { visited.push_back(entity); });

    ASSERT_EQ(visited.size(), 1u);
    EXPECT_EQ(visited.front(), both);
}
