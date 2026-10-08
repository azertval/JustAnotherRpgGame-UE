// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_turn_order.cpp
 * @brief Tests de l'ordre d'initiative : départage, repères fixes, places après un départ
 *        (`LOT-20`, `EX-CBT-010`).
 */

#include <algorithm>
#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/TurnOrder.h"

namespace {

using core::CombatSide;

/// Cinq places, chacune ne se distinguant de sa voisine que par **un** critère de départage.
[[nodiscard]] std::array<core::InitiativeEntry, 5> placesAEgalite() {
    return {{
        // Le plus haut total.
        {.combatant = core::CombatantId{5}, .total = 18, .modifier = 0, .dexterity = 10},
        // 15 partout ensuite : le modificateur départage...
        {.combatant = core::CombatantId{4}, .total = 15, .modifier = 3, .dexterity = 10},
        // ...puis la Dextérité...
        {.combatant = core::CombatantId{3},
         .total = 15,
         .modifier = 2,
         .dexterity = 15,
         .side = CombatSide::Enemies},
        // ...puis le camp : l'allié avant l'ennemi...
        {.combatant = core::CombatantId{2},
         .total = 15,
         .modifier = 2,
         .dexterity = 14,
         .side = CombatSide::Allies},
        // ...enfin l'identifiant, à tout le reste égal.
        {.combatant = core::CombatantId{1},
         .total = 15,
         .modifier = 2,
         .dexterity = 14,
         .side = CombatSide::Enemies},
    }};
}

[[nodiscard]] std::vector<core::CombatantId> ordreDe(const core::TurnOrder& ordre) {
    std::vector<core::CombatantId> ids;
    for (const core::InitiativeEntry& place : ordre.entries()) {
        ids.push_back(place.combatant);
    }
    return ids;
}

[[nodiscard]] core::InitiativeEntry combattant(std::uint32_t id, int total) {
    return {.combatant = core::CombatantId{id}, .total = total};
}

}  // namespace

/**
 * @brief Les egalites se departagent par une regle, jamais par l'ordre d'insertion.
 * \castest{<b>L'ordre d'initiative ne depend pas de l'ordre dans lequel on range les
 * combattants.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Cinq places qui ne se distinguent chacune de la suivante que par un critere : total,
 * modificateur, Dexterite, camp, identifiant.<br/>2. Les ranger dans les 120 ordres possibles.<br/>
 * \tattendu Les 120 ordres donnent la meme sequence 5, 4, 3, 2, 1 ; un combattant deja range est
 * refuse.
 * }
 */
TEST(TurnOrderTest, LOrdreNeDependPasDeLInsertion) {
    std::array<core::InitiativeEntry, 5> places = placesAEgalite();
    const std::vector<core::CombatantId> attendu{core::CombatantId{5}, core::CombatantId{4},
                                                 core::CombatantId{3}, core::CombatantId{2},
                                                 core::CombatantId{1}};
    std::sort(places.begin(), places.end(),
              [](const auto& a, const auto& b) { return a.combatant < b.combatant; });
    int permutations = 0;
    do {
        core::TurnOrder ordre;
        for (const core::InitiativeEntry& place : places) {
            ASSERT_TRUE(ordre.add(place));
        }
        EXPECT_EQ(ordreDe(ordre), attendu);
        ++permutations;
    } while (std::next_permutation(places.begin(), places.end(), [](const auto& a, const auto& b) {
        return a.combatant < b.combatant;
    }));
    EXPECT_EQ(permutations, 120);

    core::TurnOrder ordre;
    EXPECT_TRUE(ordre.add(places[0]));
    EXPECT_FALSE(ordre.add(places[0]));
    EXPECT_EQ(ordre.entries().size(), 1U);
}

/**
 * @brief Un repere d'initiative fixe perd les egalites, et se parcourt comme une place.
 * \castest{<b>Les actions de repaire au rang 20 jouent apres un combattant a 20, les renforts au
 * rang 0 en dernier.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Ranger un combattant a 20, un a 12 et un a 0, un repere « repaire » a 20 et un
 * « renforts » a 0.<br/>2. Parcourir le round de place en place.<br/>3. Ranger deux fois le meme
 * repere.<br/>
 * \tattendu Sequence : combattant 20, repaire, combattant 12, combattant 0, renforts ; le doublon
 * est refuse.
 * }
 */
TEST(TurnOrderTest, UnRepereFixePerdLesEgalites) {
    core::TurnOrder ordre;
    ASSERT_TRUE(ordre.addMarker({.count = 0, .name = "renforts"}));
    ASSERT_TRUE(ordre.addMarker({.count = 20, .name = "repaire"}));
    ASSERT_TRUE(ordre.add(combattant(1, 0)));
    ASSERT_TRUE(ordre.add(combattant(2, 12)));
    ASSERT_TRUE(ordre.add(combattant(3, 20)));
    EXPECT_FALSE(ordre.addMarker({.count = 20, .name = "repaire"}));

    std::vector<std::string> parcours;
    for (std::optional<core::TurnSlot> place = ordre.firstSlot(); place.has_value();
         place = ordre.slotAfter(*place)) {
        parcours.push_back(place->entry.has_value()
                               ? "C" + std::to_string(static_cast<int>(*place->combatant()))
                               : place->marker.name);
    }
    EXPECT_EQ(parcours, (std::vector<std::string>{"C3", "repaire", "C2", "C1", "renforts"}));
}

/**
 * @brief La place suivante se calcule par la regle, meme apres un depart ou une arrivee.
 * \castest{<b>Un combattant qui sort ne fait sauter aucun tour ; un renfort joue ce round-ci s'il
 * est range apres la place en cours.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Ordre 18, 12, 6 ; la place en cours est celle de 12.<br/>2. Retirer le combattant a
 * 12.<br/>3. Ranger un renfort a 9, puis un a 15.<br/>
 * \tattendu Apres la place de 12 vient le renfort a 9, puis 6 ; le renfort a 15 n'est pas atteint
 * ce round-ci.
 * }
 */
TEST(TurnOrderTest, UnePlaceSeCalculeApresUnDepart) {
    core::TurnOrder ordre;
    ASSERT_TRUE(ordre.add(combattant(1, 18)));
    ASSERT_TRUE(ordre.add(combattant(2, 12)));
    ASSERT_TRUE(ordre.add(combattant(3, 6)));

    std::optional<core::TurnSlot> enCours = ordre.slotAfter(*ordre.firstSlot());
    ASSERT_TRUE(enCours.has_value());
    ASSERT_EQ(enCours->combatant(), core::CombatantId{2});

    ASSERT_TRUE(ordre.remove(core::CombatantId{2}));
    EXPECT_FALSE(ordre.remove(core::CombatantId{2}));
    EXPECT_FALSE(ordre.contains(core::CombatantId{2}));
    ASSERT_TRUE(ordre.add(combattant(4, 9)));
    ASSERT_TRUE(ordre.add(combattant(5, 15)));

    std::optional<core::TurnSlot> suivante = ordre.slotAfter(*enCours);
    ASSERT_TRUE(suivante.has_value());
    EXPECT_EQ(suivante->combatant(), core::CombatantId{4});
    suivante = ordre.slotAfter(*suivante);
    ASSERT_TRUE(suivante.has_value());
    EXPECT_EQ(suivante->combatant(), core::CombatantId{3});
    EXPECT_FALSE(ordre.slotAfter(*suivante).has_value());
    EXPECT_EQ(ordre.firstSlot()->combatant(), core::CombatantId{1});
}
