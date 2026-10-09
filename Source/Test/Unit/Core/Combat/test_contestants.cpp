// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_contestants.cpp
 * @brief Le montage d'une rencontre sur la carte d'arène du combat joué dans le moteur
 *        (`LOT-1017`, sous-lot 3) : le déclencheur, le déploiement, la composition.
 *
 * La carte est celle de l'essai du combat (`Source/Test/Fixtures/Exploration/Levels/essai/arene`,
 * écrite par `scripts/maps/build_essai_maps.py`) ; le contenu est celui qui est livré.
 */

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/Arena.h"
#include "Core/Combat/Contestants.h"
#include "Core/Combat/Encounter.h"
#include "Core/Combat/MapEncounter.h"
#include "Core/World/WorldTravel.h"
#include "Test/Support/ArenaSimulation.h"

namespace {

const std::filesystem::path ELEMENTS{JADG_ELEMENTS_DIR};
const std::filesystem::path FIXTURES{JADG_TEST_FIXTURES_DIR};

[[nodiscard]] core::LevelLoadResult arene() {
    return core::WorldTravel::directoriesLoader({FIXTURES / "Exploration" / "Levels"})(
        "essai/arene");
}

/**
 * \castest{<b>L'arene d'essai dit ou la rencontre se dresse et ou le groupe entre.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire la carte d'arene d'essai.<br/>2. Chercher le declencheur de arene-bandits, puis
 * d'une rencontre que la carte ne nomme pas.<br/>3. Lire le deploiement du groupe.<br/>
 * \tattendu Le marqueur (15, 7) pour les deux ; quatre cases alliees, par rang, colonne 3, lignes
 * 5 a 8.}
 */
TEST(ContestantsTest, LArenaDitOuLaRencontreSeDresseEtOuLeGroupeEntre) {
    const core::LevelLoadResult charge = arene();
    ASSERT_TRUE(charge.ok()) << charge.error;
    const core::Level& carte = *charge.level;
    const core::GridPosition marqueur{15, 7};
    EXPECT_EQ(core::encounterTriggerOn(carte, "arene-bandits"), marqueur);
    // Une rencontre que la carte ne nomme pas se dresse au premier marqueur : la serie entiere.
    EXPECT_EQ(core::encounterTriggerOn(carte, "arene-champion"), marqueur);
    const std::vector<core::GridPosition> groupe = core::partyDeploymentOn(carte);
    ASSERT_EQ(groupe.size(), 4u);
    for (int rang = 0; rang < 4; ++rang) {
        EXPECT_EQ(groupe[static_cast<std::size_t>(rang)], (core::GridPosition{3, 5 + rang}));
    }
}

/**
 * \castest{<b>La composition d'une rencontre suit les regles de l'ecran de rencontre.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Preparer arene-bandits sur l'arene d'essai, le groupe a ses points d'entree.<br/>2.
 * Composer l'affrontement a la graine 7, puis le monter et le lancer.<br/>
 * \tattendu Letal, sans Marque Heroique, tenaille en jeu, sans fuite ; quatre heros sans
 * comportement, six bandits avec le leur ; tous poses, le combat commence.}
 */
TEST(ContestantsTest, LaCompositionSuitLesReglesDeLEcranDeRencontre) {
    const core::LevelLoadResult charge = arene();
    ASSERT_TRUE(charge.ok()) << charge.error;
    const core::Level& carte = *charge.level;
    const test_support::ArenaContent contenu(ELEMENTS);
    const test_support::Heros heros =
        test_support::loadHeroes(ELEMENTS, test_support::startingParty());
    const core::Encounter* rencontre = contenu.encounters.find("arene-bandits");
    ASSERT_NE(rencontre, nullptr);
    const std::vector<core::GridPosition> groupe = core::partyDeploymentOn(carte);
    const core::MapEncounterResult prepare = core::prepareMapEncounter(
        carte, "essai/arene", *rencontre, *core::encounterTriggerOn(carte, rencontre->id), groupe,
        core::ExplorationSnapshot{}, "");
    ASSERT_TRUE(prepare.ok()) << prepare.issue;

    const std::vector<core::HeroContestantSource> sources = heros.sources();
    core::EncounterBout monte =
        core::boutForEncounter(*prepare.setup, sources, contenu.bestiary, contenu.behaviors, 7);
    ASSERT_TRUE(monte.bout.has_value()) << monte.issue;
    const core::ArenaBout& bout = *monte.bout;
    EXPECT_TRUE(bout.lethal);
    EXPECT_FALSE(bout.heroicMark);
    EXPECT_TRUE(bout.flanking);
    EXPECT_FALSE(bout.escapable);
    EXPECT_EQ(bout.seed, 7u);
    ASSERT_EQ(bout.contestants.size(), 10u);
    for (std::size_t i = 0; i < bout.contestants.size(); ++i) {
        EXPECT_EQ(bout.contestants[i].behavior.empty(), i < 4) << i;
    }

    core::ArenaSession session(prepare.setup->battlefield);
    const core::ArenaMount mount = session.mount(bout);
    EXPECT_EQ(mount.allies.size(), 4u);
    EXPECT_EQ(mount.enemies.size(), 6u);
    EXPECT_TRUE(mount.refusals.empty());
    EXPECT_TRUE(session.start());
}

/**
 * \castest{<b>Une creature inconnue empeche la composition, et la raison est dite.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Mineure<br/>
 * \tetapes 1. Une mise en place dont un placement nomme une creature absente du bestiaire.<br/>
 * \tattendu Aucune composition ; la raison nomme la creature.}
 */
TEST(ContestantsTest, UneCreatureInconnueEmpecheLaComposition) {
    const core::LevelLoadResult charge = arene();
    ASSERT_TRUE(charge.ok()) << charge.error;
    const core::Level& carte = *charge.level;
    const core::Encounter rencontre{
        .id = "chimeres",
        .name = "Chimeres",
        .source = "original",
        .combatants = {{.creatureId = "chimere-de-papier", .columnOffset = -1, .rowOffset = 0}},
        .escapable = true};
    const core::MapEncounterResult prepare =
        core::prepareMapEncounter(carte, "essai/arene", rencontre, core::GridPosition{15, 7},
                                  core::partyDeploymentOn(carte), core::ExplorationSnapshot{}, "");
    ASSERT_TRUE(prepare.ok()) << prepare.issue;
    const core::EncounterBout monte =
        core::boutForEncounter(*prepare.setup, {}, core::Bestiary{}, core::BehaviorCatalog{}, 1);
    EXPECT_FALSE(monte.bout.has_value());
    EXPECT_NE(monte.issue.find("chimere-de-papier"), std::string::npos);
}

/**
 * \castest{<b>Chaque classe a son role quand ce n'est pas le joueur qui la joue.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Mineure<br/>
 * \tetapes 1. Lire le profil des quatre classes et d'une classe inconnue.<br/>
 * \tattendu brawler aggressive, scoundrel pack, priest support, mage archer, inconnue
 * aggressive.}
 */
TEST(ContestantsTest, ChaqueClasseASonRole) {
    EXPECT_STREQ(core::behaviorOfClass("brawler"), "aggressive");
    EXPECT_STREQ(core::behaviorOfClass("scoundrel"), "pack");
    EXPECT_STREQ(core::behaviorOfClass("priest"), "support");
    EXPECT_STREQ(core::behaviorOfClass("mage"), "archer");
    EXPECT_STREQ(core::behaviorOfClass("barde"), "aggressive");
}

}  // namespace
