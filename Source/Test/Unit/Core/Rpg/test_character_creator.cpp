// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_character_creator.cpp
 * @brief La description du créateur de personnage (LOT-1015, D-63) : ce que Core en lit, ce qu'il
 * refuse.
 */

#include <filesystem>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Data/JsonDocument.h"
#include "Core/Rpg/Appearance.h"
#include "Core/Rpg/CharacterCreator.h"

namespace {

const std::filesystem::path ELEMENTS{std::filesystem::path{JADG_RPG_DIR}.parent_path()};

TEST(CreateurDePersonnageTest, LaDescriptionLivreeSeLit) {
    const core::CharacterCreatorReadResult lue =
        core::readCharacterCreator(ELEMENTS / "Assets" / "Characters" / "humanoid.json");
    ASSERT_TRUE(lue.ok()) << lue.message;
    const core::CharacterCreator& creator = lue.creator;
    EXPECT_EQ(creator.id, "humanoid");
    EXPECT_EQ(creator.component, "Body");
    EXPECT_GT(creator.referenceHeight, 0.0F);
    EXPECT_GE(creator.bodies.size(), 2U);
    // Les six clips du jeu, et les deux sockets des mains.
    for (const char* clip : {"idle", "walk", "attack", "cast", "hit", "death"}) {
        EXPECT_TRUE(creator.clips.count(clip)) << clip;
    }
    EXPECT_TRUE(creator.sockets.count("main-hand"));
    EXPECT_TRUE(creator.sockets.count("off-hand"));
}

TEST(CreateurDePersonnageTest, ChaqueFicheLivreeNommeUnCorpsDuCreateur) {
    const core::CharacterCreator creator =
        core::readCharacterCreator(ELEMENTS / "Assets" / "Characters" / "humanoid.json").creator;
    std::vector<std::string> erreurs;
    const auto fiches = core::loadAppearances(ELEMENTS / "Rpg" / "appearances", erreurs);
    ASSERT_TRUE(erreurs.empty());
    for (const auto& [id, fiche] : fiches) {
        EXPECT_EQ(fiche.creator, creator.id) << id;
        EXPECT_TRUE(creator.bodies.count(fiche.body)) << id << " : corps " << fiche.body;
        for (const auto& [main, piece] : fiche.weapons) {
            EXPECT_TRUE(creator.sockets.count(main)) << id << " : " << main;
            EXPECT_EQ(piece.rfind("Weapons/", 0), 0U) << id << " : " << piece;
        }
    }
}

TEST(CreateurDePersonnageTest, CeQuIlRefuse) {
    struct Cas {
        const char* json;
        const char* champ;
    };
    const char* ok =
        R"({"id":"h","asset":"/Game/C/CO","component":"Body","skeleton":"/Game/S","weapons":"/Game/W",
            "referenceHeight":1.8,"bodies":{"a":"/Game/A"},"clips":{"idle":"/Game/I","walk":"/Game/M"},
            "sockets":{"main-hand":"hand_r"}})";
    ASSERT_TRUE(core::parseCharacterCreator(ok, "ok").ok());
    const std::vector<Cas> cas = {
        {R"({"id":"h","asset":"Content/CO","component":"Body","skeleton":"/Game/S","weapons":"/Game/W",
            "referenceHeight":1.8,"bodies":{"a":"/Game/A"},"clips":{"idle":"/Game/I","walk":"/Game/M"},
            "sockets":{"main-hand":"hand_r"}})",
         "asset"},
        {R"({"id":"h","asset":"/Game/C/CO","component":"Body","skeleton":"/Game/S","weapons":"/Game/W",
            "referenceHeight":0,"bodies":{"a":"/Game/A"},"clips":{"idle":"/Game/I","walk":"/Game/M"},
            "sockets":{"main-hand":"hand_r"}})",
         "referenceHeight"},
        {R"({"id":"h","asset":"/Game/C/CO","component":"Body","skeleton":"/Game/S","weapons":"/Game/W",
            "referenceHeight":1.8,"bodies":{"a":"A"},"clips":{"idle":"/Game/I","walk":"/Game/M"},
            "sockets":{"main-hand":"hand_r"}})",
         "bodies/a"},
        {R"({"id":"h","asset":"/Game/C/CO","component":"Body","skeleton":"/Game/S","weapons":"/Game/W",
            "referenceHeight":1.8,"bodies":{"a":"/Game/A"},"clips":{"idle":"/Game/I"},
            "sockets":{"main-hand":"hand_r"}})",
         "clips/walk"},
    };
    for (const Cas& c : cas) {
        const core::CharacterCreatorReadResult lue = core::parseCharacterCreator(c.json, "essai");
        EXPECT_EQ(lue.error, core::JsonReadError::MalformedStructure) << c.champ;
        EXPECT_NE(lue.message.find(c.champ), std::string::npos) << lue.message;
    }
}

}  // namespace
