// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_appearance.cpp
 * @brief La fiche d'apparence d'un personnage (LOT-1015, D-63) : ce que Core en lit, ce qu'il
 * refuse.
 */

#include <filesystem>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Data/JsonDocument.h"
#include "Core/Rpg/Appearance.h"

namespace {

const std::filesystem::path RPG{JADG_RPG_DIR};

constexpr const char* FICHE = R"({
  "id": "essai", "name": "Essai", "source": "original",
  "creator": "humanoid", "body": "metahuman", "head": "metahuman", "height": 1.8,
  "colors": {"skin": [0.5, 0.4, 0.3], "eyes": [0.1, 0.2, 0.3, 1.0]},
  "pieces": {"torso": "tunic", "hair": "none"},
  "weapons": {"main-hand": "Weapons/brawler-axe"},
  "clips": {"attack": {"key": 0.4}, "idle": {}}
})";

TEST(ApparenceTest, UneFicheSeLitChampParChamp) {
    const core::AppearanceReadResult lue = core::parseAppearance(FICHE, "essai.json");
    ASSERT_TRUE(lue.ok()) << lue.message;
    const core::Appearance& fiche = lue.appearance;
    EXPECT_EQ(fiche.id, "essai");
    EXPECT_EQ(fiche.creator, "humanoid");
    EXPECT_EQ(fiche.body, "metahuman");
    EXPECT_FLOAT_EQ(fiche.height, 1.8F);
    ASSERT_EQ(fiche.colors.size(), 2U);
    EXPECT_FLOAT_EQ(fiche.colors.at("skin").r, 0.5F);
    EXPECT_FLOAT_EQ(fiche.colors.at("skin").a, 1.0F);
    EXPECT_FLOAT_EQ(fiche.colors.at("eyes").b, 0.3F);
    EXPECT_EQ(fiche.pieces.at("torso"), "tunic");
    EXPECT_EQ(fiche.weapons.at("main-hand"), "Weapons/brawler-axe");
    ASSERT_EQ(fiche.clipKeys.size(), 1U);
    EXPECT_FLOAT_EQ(fiche.clipKeys.at("attack"), 0.4F);
}

TEST(ApparenceTest, CeQuEllRefuseEstNommeAvecSonChamp) {
    struct Cas {
        const char* json;
        const char* champ;
    };
    const std::vector<Cas> cas = {
        {R"({"id":"a","name":"a","source":"original","body":"b","head":"h","height":1})",
         "creator"},
        {R"({"id":"a","name":"a","source":"original","creator":"c","body":"b","head":"h","height":0})",
         "height"},
        {R"({"id":"a","name":"a","source":"original","creator":"c","body":"b","head":"h","height":1,
             "colors":{"skin":[1,2,0]}})",
         "colors/skin"},
        {R"({"id":"a","name":"a","source":"original","creator":"c","body":"b","head":"h","height":1,
             "weapons":{"tail":"x"}})",
         "weapons/tail"},
        {R"({"id":"a","name":"a","source":"original","creator":"c","body":"b","head":"h","height":1,
             "clips":{"attack":{"key":-1}}})",
         "clips/attack/key"},
    };
    for (const Cas& c : cas) {
        const core::AppearanceReadResult lue = core::parseAppearance(c.json, "essai.json");
        EXPECT_EQ(lue.error, core::JsonReadError::MalformedStructure) << c.champ;
        EXPECT_NE(lue.message.find(c.champ), std::string::npos) << lue.message;
    }
    const core::AppearanceReadResult malforme = core::parseAppearance("{", "essai.json");
    EXPECT_EQ(malforme.error, core::JsonReadError::ParseError);
}

TEST(ApparenceTest, LesFichesLivreesSeLisentEtPortentLeurNomDeFichier) {
    std::vector<std::string> erreurs;
    const auto fiches = core::loadAppearances(RPG / "appearances", erreurs);
    EXPECT_TRUE(erreurs.empty()) << erreurs.front();
    // Les quatre héros de la démo (D-28) et le pantin qui tient la place des autres.
    for (const char* id :
         {"heros-brawler", "heros-mage", "heros-priest", "heros-scoundrel", "pantin"}) {
        ASSERT_TRUE(fiches.count(id)) << id;
        EXPECT_GT(fiches.at(id).height, 0.0F);
    }
    // Chaque héros tient son arme de la main principale, comme sa fiche de règles l'équipe.
    for (const char* id : {"heros-brawler", "heros-mage", "heros-priest", "heros-scoundrel"}) {
        EXPECT_TRUE(fiches.at(id).weapons.count("main-hand")) << id;
        EXPECT_FLOAT_EQ(fiches.at(id).clipKeys.at("attack"), 0.4F) << id;
    }
    // Une fiche de règles de héros a sa fiche d'apparence.
    for (const auto& entree : std::filesystem::directory_iterator(RPG / "characters")) {
        EXPECT_TRUE(fiches.count(entree.path().stem().string())) << entree.path();
    }
}

TEST(ApparenceTest, UnFichierAbsentEstUnEchecNomme) {
    const core::AppearanceReadResult lue =
        core::readAppearance(RPG / "appearances" / "nulle-part.json");
    EXPECT_EQ(lue.error, core::JsonReadError::FileNotFound);
}

}  // namespace
