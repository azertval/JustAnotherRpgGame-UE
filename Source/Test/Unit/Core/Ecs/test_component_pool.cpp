// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_component_pool.cpp
 * @brief Tests unitaires du stockage de composants en sparse set.
 */

#include <stdexcept>

#include <gtest/gtest.h>

#include "Core/Diagnostics/Assert.h"
#include "Core/Ecs/ComponentPool.h"
#include "Core/Ecs/Entity.h"
#include "Core/Ecs/EntityManager.h"

namespace {
/// Composant de test : donnée pure minimale.
struct Position {
    int x = 0;
    int y = 0;
};
}  // namespace

/**
 * @brief `add` puis `get` renvoie la valeur stockée ; `has` est cohérent.
 * \castest{<b>`add` puis `get` renvoie la valeur stockée ; `has` est cohérent.</b><br/>
 * \tcat Unitaire · Component Pool<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `add` puis `get` renvoie la valeur stockée ; `has` est cohérent.
 * }
 */
TEST(ComponentPoolTest, AjoutPuisAcces) {
    core::EntityManager manager;
    const core::Entity entity = manager.create();
    core::ComponentPool<Position> pool;

    EXPECT_FALSE(pool.has(entity));
    pool.add(entity, Position{3, 4});

    EXPECT_TRUE(pool.has(entity));
    EXPECT_EQ(pool.get(entity).x, 3);
    EXPECT_EQ(pool.get(entity).y, 4);
    EXPECT_EQ(pool.size(), 1u);
}

/**
 * @brief `get` renvoie une référence modifiable sur le composant stocké.
 * \castest{<b>`get` renvoie une référence modifiable sur le composant stocké.</b><br/>
 * \tcat Unitaire · Component Pool<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `get` renvoie une référence modifiable sur le composant stocké.
 * }
 */
TEST(ComponentPoolTest, GetRenvoieReferenceModifiable) {
    core::EntityManager manager;
    const core::Entity entity = manager.create();
    core::ComponentPool<Position> pool;
    pool.add(entity, Position{1, 1});

    pool.get(entity).x = 42;

    EXPECT_EQ(pool.get(entity).x, 42);
}

/**
 * @brief `remove` d'un élément au milieu (swap-and-pop) laisse les autres composants accessibles et
 * corrects, et le stockage dense reste contigu.
 * \castest{<b>`remove` d'un élément au milieu (swap-and-pop) laisse les autres composants
 * accessibles et corrects, et le stockage dense reste contigu.</b><br/>
 * \tcat Unitaire · Component Pool<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `remove` d'un élément au milieu (swap-and-pop) laisse les autres composants accessibles
 * et corrects, et le stockage dense reste contigu.
 * }
 */
TEST(ComponentPoolTest, RemoveAuMilieuSwapAndPop) {
    core::EntityManager manager;
    const core::Entity first = manager.create();
    const core::Entity middle = manager.create();
    const core::Entity last = manager.create();

    core::ComponentPool<int> pool;
    pool.add(first, 10);
    pool.add(middle, 20);
    pool.add(last, 30);

    pool.remove(middle);

    EXPECT_FALSE(pool.has(middle));
    EXPECT_TRUE(pool.has(first));
    EXPECT_TRUE(pool.has(last));
    EXPECT_EQ(pool.get(first), 10);
    EXPECT_EQ(pool.get(last), 30);
    // Densité maintenue : deux composants contigus, sans trou.
    EXPECT_EQ(pool.size(), 2u);
    EXPECT_EQ(pool.components().size(), 2u);
    EXPECT_EQ(pool.entities().size(), 2u);
}

/**
 * @brief Retirer le dernier élément ne perturbe pas les précédents.
 * \castest{<b>Retirer le dernier élément ne perturbe pas les précédents.</b><br/>
 * \tcat Unitaire · Component Pool<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Retirer le dernier élément ne perturbe pas les précédents.
 * }
 */
TEST(ComponentPoolTest, RemoveDernierElement) {
    core::EntityManager manager;
    const core::Entity a = manager.create();
    const core::Entity b = manager.create();
    core::ComponentPool<int> pool;
    pool.add(a, 1);
    pool.add(b, 2);

    pool.remove(b);

    EXPECT_TRUE(pool.has(a));
    EXPECT_FALSE(pool.has(b));
    EXPECT_EQ(pool.get(a), 1);
    EXPECT_EQ(pool.size(), 1u);
}

/**
 * @brief Un handle périmé (index recyclé, génération différente) ne possède pas le composant de
 * l'ancienne entité.
 * \castest{<b>Un handle périmé (index recyclé, génération différente) ne possède pas le composant
 * de l'ancienne entité.</b><br/>
 * \tcat Unitaire · Component Pool<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un handle périmé (index recyclé, génération différente) ne possède pas le composant de
 * l'ancienne entité.
 * }
 */
TEST(ComponentPoolTest, HandlePerimeNePossedePasLeComposant) {
    core::EntityManager manager;
    const core::Entity original = manager.create();
    core::ComponentPool<int> pool;
    pool.add(original, 7);

    manager.destroy(original);
    const core::Entity recycled = manager.create();  // même index, génération distincte

    // Le composant reste rattaché à l'ancien handle (données pures : la pool ne
    // sait pas que l'entité a été détruite), mais pas au nouveau handle.
    EXPECT_TRUE(pool.has(original));
    EXPECT_FALSE(pool.has(recycled));
}

/**
 * @brief `removeIfPresent` retire si le composant existe, sinon ne fait rien.
 * \castest{<b>`removeIfPresent` retire si le composant existe, sinon ne fait rien.</b><br/>
 * \tcat Unitaire · Component Pool<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `removeIfPresent` retire si le composant existe, sinon ne fait rien.
 * }
 */
TEST(ComponentPoolTest, RemoveIfPresent) {
    core::EntityManager manager;
    const core::Entity entity = manager.create();
    core::ComponentPool<int> pool;

    EXPECT_FALSE(pool.removeIfPresent(entity));  // rien à retirer
    pool.add(entity, 5);
    EXPECT_TRUE(pool.removeIfPresent(entity));
    EXPECT_FALSE(pool.has(entity));
}

/**
 * @brief `get` sur une entité absente viole une précondition (assertion en Debug).
 * \castest{<b>`get` sur une entité absente viole une précondition (assertion en Debug).</b><br/>
 * \tcat Unitaire · Component Pool<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu `get` sur une entité absente viole une précondition (assertion en Debug).
 * }
 */
TEST(ComponentPoolTest, GetSurEntiteAbsenteViolePrecondition) {
#ifdef NDEBUG
    GTEST_SKIP() << "Assertions desactivees en Release";
#else
    // Le gestionnaire lève pour interrompre avant tout accès hors-borne.
    core::setAssertionHandler([](const char*, const char*, const char*, int) {
        throw std::runtime_error("precondition");
    });

    core::EntityManager manager;
    const core::Entity absent = manager.create();
    core::ComponentPool<int> pool;

    EXPECT_THROW(
        {
            const int value = pool.get(absent);
            (void)value;
        },
        std::runtime_error);

    core::setAssertionHandler(nullptr);
#endif
}
