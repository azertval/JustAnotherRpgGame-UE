// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_text_catalog.cpp
 * @brief Le catalogue des textes (LOT-1020) : lecture d'un `.lang`, trous, écriture du moteur, et
 *        les deux catalogues du dépôt, clé pour clé.
 */

#include <set>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Ui/TextCatalog.h"

/**
 * @brief Un `.lang` se lit : commentaires et lignes vides ignorés, premier `=` seul séparateur.
 * \castest{<b>Un catalogue de textes se lit clé par clé.</b><br/>
 * \tcat Unitaire · Interface · Textes<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Lire un contenu avec une marque d'ordre des octets, un commentaire, une ligne vide,
 *          une valeur qui contient « = », des fins de ligne Windows.<br/>
 * \tattendu Deux clés ; la valeur garde son « = » ; ni espace de bord ni retour chariot.
 * }
 */
TEST(TextCatalogTest, UnCatalogueSeLitCleParCle) {
    const core::TextTable table = core::parseTextCatalog(
        "\xEF\xBB\xBF# titre\r\n\r\nmenu.quit = Quitter\r\nmath.eq =  a = b \r\nsans-signe\r\n");
    ASSERT_EQ(table.size(), 2U);
    EXPECT_EQ(table.at("menu.quit"), "Quitter");
    EXPECT_EQ(table.at("math.eq"), "a = b");
}

/**
 * @brief Les trous se remplissent dans l'ordre, et se traduisent pour le moteur.
 * \castest{<b>Les trous d'un texte se remplissent et s'écrivent pour le moteur.</b><br/>
 * \tcat Unitaire · Interface · Textes<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Remplir « %1 · DD %2 » avec deux arguments, puis avec un seul.<br/>2. Traduire un
 *          texte à trous et à accolades dans l'écriture du moteur.<br/>
 * \tattendu « Persuasion · DD 12 » ; un trou sans argument reste visible ; « {0} · `{x`} ».
 * }
 */
TEST(TextCatalogTest, LesTrousSeRemplissentEtSeTraduisent) {
    EXPECT_EQ(core::formatText("%1 · DD %2", {"Persuasion", "12"}), "Persuasion · DD 12");
    EXPECT_EQ(core::formatText("%1 · DD %2", {"Persuasion"}), "Persuasion · DD %2");
    EXPECT_EQ(core::toEngineFormat("%1 · {x}"), "{0} · `{x`}");
    EXPECT_EQ(core::textPlaceholders("%2 puis %1 puis %2"), (std::vector<int>{1, 2}));
}

/**
 * @brief Les catalogues français et anglais du dépôt portent les mêmes clés et les mêmes trous.
 * \castest{<b>Le français et l'anglais ont les mêmes clés et les mêmes trous.</b><br/>
 * \tcat Unitaire · Interface · Textes<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Lire Source/Elements/Localization/fr.lang et en.lang.<br/>2. Comparer leurs clés,
 *          puis les trous de chaque valeur.<br/>
 * \tattendu Aucune clé d'un seul côté ; aucune valeur vide ; mêmes trous des deux côtés.
 * }
 */
TEST(TextCatalogTest, LesDeuxCataloguesDuDepotSeRepondent) {
    const core::TextTable french = core::loadTextCatalog(JADG_FR_LANG_PATH);
    const core::TextTable english = core::loadTextCatalog(JADG_EN_LANG_PATH);
    ASSERT_FALSE(french.empty());
    for (const auto& [key, value] : french) {
        ASSERT_TRUE(english.contains(key)) << key << " manque en anglais";
        EXPECT_FALSE(value.empty()) << key;
        EXPECT_EQ(core::textPlaceholders(value), core::textPlaceholders(english.at(key))) << key;
    }
    for (const auto& [key, value] : english) {
        EXPECT_TRUE(french.contains(key)) << key << " manque en français";
    }
}
