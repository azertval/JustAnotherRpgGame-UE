// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_action_economy.cpp
 * @brief Tests de l'économie d'action et des mémoires à portée (`LOT-20`, `EX-CBT-011`).
 */

#include <cstdint>
#include <initializer_list>
#include <string>
#include <string_view>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/ActionEconomy.h"
#include "Core/Combat/CombatCounters.h"

/**
 * @brief Chaque ressource du tour se consomme une fois ; le deplacement se fractionne.
 * \castest{<b>Action, action bonus et reaction se depensent une fois ; le deplacement se depense
 * en plusieurs fois sans jamais revenir dans le tour.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Economie standard a 6 cases.<br/>2. Depenser deux fois l'action, l'action bonus et
 * la reaction.<br/>3. Depenser 2 puis 4 cases, puis 1.<br/>4. Depenser 0, une ressource inconnue,
 * puis restaurer.<br/>
 * \tattendu Seconde depense refusee pour chacune ; 2 et 4 cases acceptees, la septieme refusee ;
 * rien n'est depense par un refus ; la restauration rend tout.
 * }
 */
TEST(ActionEconomyTest, ChaqueRessourceUneFoisParTour) {
    core::ActionEconomy economie = core::ActionEconomy::standard(6);
    for (const std::string_view ressource :
         {core::ACTION_RESOURCE, core::BONUS_ACTION_RESOURCE, core::REACTION_RESOURCE}) {
        EXPECT_TRUE(economie.spend(ressource)) << ressource;
        EXPECT_FALSE(economie.spend(ressource)) << ressource;
        EXPECT_EQ(economie.remaining(ressource), 0) << ressource;
    }

    EXPECT_TRUE(economie.spend(core::MOVEMENT_RESOURCE, 2));
    EXPECT_FALSE(economie.spend(core::MOVEMENT_RESOURCE, 5));
    EXPECT_EQ(economie.remaining(core::MOVEMENT_RESOURCE), 4);
    EXPECT_TRUE(economie.spend(core::MOVEMENT_RESOURCE, 4));
    EXPECT_FALSE(economie.spend(core::MOVEMENT_RESOURCE, 1));

    EXPECT_FALSE(economie.spend(core::MOVEMENT_RESOURCE, 0));
    EXPECT_FALSE(economie.spend("inconnue"));
    EXPECT_FALSE(economie.has("inconnue"));

    economie.refresh();
    EXPECT_EQ(economie.remaining(core::ACTION_RESOURCE), 1);
    EXPECT_EQ(economie.remaining(core::BONUS_ACTION_RESOURCE), 1);
    EXPECT_EQ(economie.remaining(core::REACTION_RESOURCE), 1);
    EXPECT_EQ(economie.remaining(core::MOVEMENT_RESOURCE), 6);
}

/**
 * @brief L'economie est une liste : une troisieme economie se declare, une reaction s'octroie.
 * \castest{<b>Une ressource nouvelle se declare sans rien casser, et un octroi ne dure que jusqu'au
 * prochain debut de tour.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Declarer « heroicAction » a 1 par tour.<br/>2. Octroyer une reaction, puis une
 * ressource inconnue.<br/>3. Restaurer.<br/>
 * \tattendu Les ressources gardent l'ordre de leur declaration ; la reaction monte a 2 puis
 * revient a 1 ; la ressource octroyee disparait a 0.
 * }
 */
TEST(ActionEconomyTest, UneRessourceSeDeclareEtSOctroie) {
    core::ActionEconomy economie = core::ActionEconomy::standard(6);
    economie.declare("heroicAction", 1);
    std::vector<std::string> noms;
    for (const core::ActionResource& ressource : economie.resources()) {
        noms.push_back(ressource.id);
    }
    EXPECT_EQ(noms, (std::vector<std::string>{"action", "bonusAction", "reaction", "movement",
                                              "heroicAction"}));
    EXPECT_TRUE(economie.spend("heroicAction"));

    economie.grant(core::REACTION_RESOURCE);
    EXPECT_EQ(economie.remaining(core::REACTION_RESOURCE), 2);
    economie.grant("sursis", 2);
    EXPECT_EQ(economie.remaining("sursis"), 2);

    economie.refresh();
    EXPECT_EQ(economie.remaining(core::REACTION_RESOURCE), 1);
    EXPECT_EQ(economie.remaining("heroicAction"), 1);
    EXPECT_EQ(economie.remaining("sursis"), 0);
}

/**
 * @brief Les compteurs vivent a leur portee, et une immunite tient a un couple.
 * \castest{<b>« Une fois par tour », « une fois par rencontre » et « immunise 24 heures » se
 * comptent separement.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Incrementer un meme compteur aux portees tour, rencontre et jour.<br/>2. Vider la
 * portee tour.<br/>3. Immuniser un gobelin contre la presence d'un dragon pendant 24 h.<br/>
 * \tattendu Seul le compteur de tour retombe a 0 ; l'immunite vaut contre ce dragon seulement, et
 * jusqu'a son echeance.
 * }
 */
TEST(CombatCountersTest, LesPorteesSontSeparees) {
    core::ScopedCounters compteurs;
    EXPECT_EQ(compteurs.increment(core::CounterScope::Turn, "moine", "posture"), 1);
    EXPECT_EQ(compteurs.increment(core::CounterScope::Turn, "moine", "posture"), 2);
    compteurs.increment(core::CounterScope::Encounter, "moine", "posture");
    compteurs.increment(core::CounterScope::Day, "moine", "posture", 3);

    compteurs.clear(core::CounterScope::Turn);
    EXPECT_EQ(compteurs.value(core::CounterScope::Turn, "moine", "posture"), 0);
    EXPECT_EQ(compteurs.value(core::CounterScope::Encounter, "moine", "posture"), 1);
    EXPECT_EQ(compteurs.value(core::CounterScope::Day, "moine", "posture"), 3);
    EXPECT_EQ(compteurs.value(core::CounterScope::Day, "gobelin", "posture"), 0);

    core::ImmunityLedger immunites;
    const std::int64_t maintenant = 1000;
    immunites.grant("gobelin", "dragon-rouge", maintenant + core::IMMUNITY_DAY_SECONDS);
    immunites.grant("gobelin", "dragon-rouge", maintenant + 10);  // ne raccourcit pas
    EXPECT_TRUE(immunites.isImmune("gobelin", "dragon-rouge", maintenant));
    EXPECT_FALSE(immunites.isImmune("gobelin", "dragon-bleu", maintenant));
    EXPECT_FALSE(immunites.isImmune("ogre", "dragon-rouge", maintenant));
    EXPECT_TRUE(
        immunites.isImmune("gobelin", "dragon-rouge", maintenant + core::IMMUNITY_DAY_SECONDS - 1));
    immunites.expire(maintenant + core::IMMUNITY_DAY_SECONDS);
    EXPECT_FALSE(
        immunites.isImmune("gobelin", "dragon-rouge", maintenant + core::IMMUNITY_DAY_SECONDS - 1));
}
