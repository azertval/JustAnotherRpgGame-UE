// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_ui_style.cpp
 * @brief Le style des écrans en fichier texte (LOT-1020) : couleurs, pièces 9-patch, erreurs
 *        nommées, et le fichier du dépôt.
 */

#include <filesystem>

#include <gtest/gtest.h>

#include "Core/Ui/UiStyle.h"

namespace {

const std::filesystem::path STYLE = std::filesystem::path(JADG_ASSETS_DIR) / "UI" / "style.json";

}  // namespace

/**
 * @brief Le style du dépôt se lit sans erreur et porte la charte v2.
 * \castest{<b>Le style des écrans du dépôt se lit sans erreur.</b><br/>
 * \tcat Unitaire · Interface · Style<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Lire Source/Elements/Assets/UI/style.json.<br/>
 * \tattendu Aucune erreur ; conception à 1920 × 1080 ; le filet d'or `panelEdge` à #e4a43c ; le
 *           panneau sombre a ses marges 9-patch de 112 ; le bouton par défaut ses quatre états ;
 *           le titre en Cinzel, le corps en IM Fell English ; le titre d'écran à 36 pixels.
 * }
 */
TEST(UiStyleTest, LeStyleDuDepotSeLit) {
    const core::UiStyleResult read = core::loadUiStyle(STYLE);
    ASSERT_TRUE(read.ok()) << read.errors.front();
    const core::UiStyle& style = read.style;
    EXPECT_EQ(style.designWidth, 1920);
    EXPECT_EQ(style.designHeight, 1080);
    EXPECT_EQ(style.colours.at("panelEdge"), *core::parseUiColour("#e4a43c"));
    const core::UiPiece& panel = style.pieces.at("frame/panel-dark");
    ASSERT_TRUE(panel.margins.has_value());
    EXPECT_EQ(*panel.margins, (core::UiMargins{112, 112, 112, 112}));
    EXPECT_EQ(panel.file(), "frame/panel-dark.png");
    const core::UiPiece& button = style.pieces.at("button/default");
    EXPECT_EQ(button.states.size(), 4U);
    EXPECT_EQ(button.file("hover"), "button/default/hover.png");
    EXPECT_EQ(style.fonts.at("title"), "Fonts/Cinzel-SemiBold.ttf");
    EXPECT_EQ(style.fonts.at("body"), "Fonts/IMFellEnglish-Regular.ttf");
    for (const auto& [role, file] : style.fonts) {
        EXPECT_TRUE(std::filesystem::exists(std::filesystem::path(JADG_ASSETS_DIR) / file)) << role;
    }
    EXPECT_EQ(style.sizes.at("screenTitle"), 36);
}

/**
 * @brief Une valeur fausse est une erreur nommée ; le reste se lit.
 * \castest{<b>Une valeur fausse du style est nommée, le reste se lit.</b><br/>
 * \tcat Unitaire · Interface · Style<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire un style à une couleur fausse, une pièce aux marges plus larges qu'elle, une
 *          taille négative et une section inconnue, à côté de valeurs justes.<br/>
 * \tattendu Quatre erreurs, chacune nommant son champ ; la couleur et la pièce justes sont lues.
 * }
 */
TEST(UiStyleTest, UneValeurFausseEstNommee) {
    const core::UiStyleResult read = core::readUiStyle(R"({"version": 1,
        "colours": {"ink": "#302000", "faux": "rouge"},
        "sizes": {"body": -3},
        "pieces": {"plate/ok": {"size": [64, 32], "margins": [8, 0, 8, 0]},
                   "plate/faux": {"size": [64, 32], "margins": [40, 0, 40, 0]}},
        "palette": {}})");
    ASSERT_EQ(read.errors.size(), 4U);
    EXPECT_NE(read.errors[0].find("colours.faux"), std::string::npos);
    EXPECT_TRUE(read.style.colours.contains("ink"));
    EXPECT_TRUE(read.style.pieces.contains("plate/ok"));
    EXPECT_FALSE(read.style.pieces.contains("plate/faux"));
    EXPECT_FALSE(core::parseUiColour("#12345").has_value());
    EXPECT_FLOAT_EQ(core::parseUiColour("#000000a0")->alpha, 160.0F / 255.0F);
}
