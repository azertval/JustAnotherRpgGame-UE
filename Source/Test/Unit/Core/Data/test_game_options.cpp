// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_game_options.cpp
 * @brief Les options du jeu en fichier texte (LOT-1014) : lecture sur une base, bornes, champs
 *        refusés, fichier d'usine du dépôt.
 */

#include <filesystem>
#include <string>

#include <gtest/gtest.h>

#include "Core/Data/GameOptions.h"

namespace {

const std::filesystem::path OPTIONS =
    std::filesystem::path(JADG_ELEMENTS_DIR) / core::GAME_OPTIONS_FILE;

}  // namespace

/**
 * @brief Le fichier d'usine du dépôt se lit sans erreur et porte les valeurs par défaut.
 * \castest{<b>Le fichier d'options du dépôt se lit sans erreur.</b><br/>
 * \tcat Unitaire · Données · Options<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Lire Source/Elements/Options/options.json.<br/>
 * \tattendu Le fichier est trouvé, aucune erreur ; 1920 × 1080 en plein écran, rendu à 100 %,
 *           ombres au palier 3, volume à 100 : les valeurs par défaut de `core::GameOptions`.
 * }
 */
TEST(GameOptionsTest, LeFichierDUsineSeLitSansErreur) {
    const core::GameOptionsResult lu = core::loadGameOptions(OPTIONS);
    EXPECT_TRUE(lu.found) << OPTIONS.string();
    for (const std::string& erreur : lu.errors) {
        ADD_FAILURE() << erreur;
    }
    EXPECT_EQ(lu.options, core::GameOptions{});
    EXPECT_EQ(lu.options.width, 1920);
    EXPECT_EQ(lu.options.height, 1080);
    EXPECT_TRUE(lu.options.fullscreen);
    EXPECT_EQ(lu.options.renderScalePercent, 100);
    EXPECT_EQ(lu.options.shadowQuality, 3);
    EXPECT_EQ(lu.options.volumePercent, 100);
}

/**
 * @brief Un fichier se lit sur une base : un champ présent la remplace, un champ absent la garde.
 * \castest{<b>Les réglages du joueur se lisent sur ceux d'usine.</b><br/>
 * \tcat Unitaire · Données · Options<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Prendre une base à 2560 × 1440, volume 40.<br/>2. Lire dessus un document qui ne
 *          porte que la qualité des ombres et le plein écran.<br/>
 * \tattendu Les ombres et le plein écran sont ceux du document ; la définition et le volume ceux
 *           de la base ; aucune erreur.
 * }
 */
TEST(GameOptionsTest, UnChampAbsentGardeLaBase) {
    core::GameOptions base;
    base.width = 2560;
    base.height = 1440;
    base.volumePercent = 40;

    const core::GameOptionsResult lu = core::readGameOptions(
        R"({"version": 1, "display": {"fullscreen": false}, "rendering": {"shadowQuality": 1}})",
        base);

    EXPECT_TRUE(lu.ok());
    EXPECT_TRUE(lu.found);
    EXPECT_EQ(lu.options.width, 2560);
    EXPECT_EQ(lu.options.height, 1440);
    EXPECT_FALSE(lu.options.fullscreen);
    EXPECT_EQ(lu.options.shadowQuality, 1);
    EXPECT_EQ(lu.options.renderScalePercent, 100);
    EXPECT_EQ(lu.options.volumePercent, 40);
}

/**
 * @brief Un champ faux est nommé et garde la base ; les autres se lisent.
 * \castest{<b>Une valeur hors bornes, du mauvais type ou inconnue est refusée, seule.</b><br/>
 * \tcat Unitaire · Données · Options<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire un document dont l'échelle de rendu vaut 400, le volume est un texte, la
 *          largeur un nombre à virgule, et qui porte un champ et une section inconnus.<br/>
 * \tattendu Cinq erreurs, chacune nommant son champ ; l'échelle, le volume et la largeur restent
 *           ceux de la base ; la hauteur et les ombres, justes, sont lues.
 * }
 */
TEST(GameOptionsTest, UnChampFauxEstRefuseSeul) {
    const core::GameOptionsResult lu = core::readGameOptions(
        R"({"version": 1,
            "display": {"width": 1280.5, "height": 720, "plein": true},
            "rendering": {"renderScalePercent": 400, "shadowQuality": 4},
            "audio": {"volumePercent": "fort"},
            "reseau": {}})",
        core::GameOptions{}, "options.json");

    ASSERT_EQ(lu.errors.size(), 5U);
    const auto nomme = [&lu](const std::string& fragment) {
        for (const std::string& erreur : lu.errors) {
            if (erreur.find(fragment) != std::string::npos &&
                erreur.find("options.json") != std::string::npos) {
                return true;
            }
        }
        return false;
    };
    EXPECT_TRUE(nomme("display.width is not an integer"));
    EXPECT_TRUE(nomme("display.plein is not a known option"));
    EXPECT_TRUE(nomme("rendering.renderScalePercent out of range [50, 200]"));
    EXPECT_TRUE(nomme("audio.volumePercent is not an integer"));
    EXPECT_TRUE(nomme("reseau is not a known section"));

    EXPECT_EQ(lu.options.width, 1920);
    EXPECT_EQ(lu.options.height, 720);
    EXPECT_EQ(lu.options.renderScalePercent, 100);
    EXPECT_EQ(lu.options.shadowQuality, 4);
    EXPECT_EQ(lu.options.volumePercent, 100);
}

/**
 * @brief Chaque borne est tenue des deux côtés.
 * \castest{<b>Les bornes de chaque option sont incluses, et rien au-delà n'entre.</b><br/>
 * \tcat Unitaire · Données · Options<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire les valeurs aux deux bornes de chaque champ entier.<br/>2. Lire les valeurs
 *          juste au-delà.<br/>
 * \tattendu Les bornes sont lues sans erreur ; chaque valeur au-delà est refusée.
 * }
 */
TEST(GameOptionsTest, LesBornesSontIncluses) {
    const core::GameOptionsResult bas = core::readGameOptions(
        R"({"display": {"width": 640, "height": 360},
            "rendering": {"renderScalePercent": 50, "shadowQuality": 0},
            "audio": {"volumePercent": 0}})");
    EXPECT_TRUE(bas.ok());
    EXPECT_EQ(bas.options.width, 640);
    EXPECT_EQ(bas.options.height, 360);
    EXPECT_EQ(bas.options.renderScalePercent, 50);
    EXPECT_EQ(bas.options.shadowQuality, 0);
    EXPECT_EQ(bas.options.volumePercent, 0);

    const core::GameOptionsResult haut = core::readGameOptions(
        R"({"display": {"width": 7680, "height": 4320},
            "rendering": {"renderScalePercent": 200, "shadowQuality": 4},
            "audio": {"volumePercent": 100}})");
    EXPECT_TRUE(haut.ok());
    EXPECT_EQ(haut.options.width, 7680);
    EXPECT_EQ(haut.options.height, 4320);
    EXPECT_EQ(haut.options.renderScalePercent, 200);
    EXPECT_EQ(haut.options.shadowQuality, 4);

    const core::GameOptionsResult dehors = core::readGameOptions(
        R"({"display": {"width": 639, "height": 4321},
            "rendering": {"renderScalePercent": 49, "shadowQuality": 5},
            "audio": {"volumePercent": -1}})");
    EXPECT_EQ(dehors.errors.size(), 5U);
    EXPECT_EQ(dehors.options, core::GameOptions{});
}

/**
 * @brief Un fichier absent n'est pas une erreur ; un fichier illisible ou trop récent en est une.
 * \castest{<b>Sans fichier, les options sont la base ; un document illisible le dit.</b><br/>
 * \tcat Unitaire · Données · Options<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Charger un fichier qui n'existe pas, sur une base au volume 25.<br/>2. Lire un JSON
 *          malformé.<br/>3. Lire un document de version 2.<br/>
 * \tattendu Le fichier absent rend la base, `found` faux, sans erreur ; les deux autres rendent
 *           la base et une erreur.
 * }
 */
TEST(GameOptionsTest, UnFichierAbsentRendLaBase) {
    core::GameOptions base;
    base.volumePercent = 25;
    const core::GameOptionsResult absent =
        core::loadGameOptions(OPTIONS.parent_path() / "absent.json", base);
    EXPECT_FALSE(absent.found);
    EXPECT_TRUE(absent.ok());
    EXPECT_EQ(absent.options, base);

    const core::GameOptionsResult malforme = core::readGameOptions(R"({"display": )", base);
    EXPECT_EQ(malforme.errors.size(), 1U);
    EXPECT_EQ(malforme.options, base);

    const core::GameOptionsResult recent =
        core::readGameOptions(R"({"version": 2, "audio": {"volumePercent": 90}})", base);
    EXPECT_EQ(recent.errors.size(), 1U);
    EXPECT_EQ(recent.options, base);
}

/**
 * @brief La langue se lit, se refuse si elle n'est pas un code, et l'écriture se relit à
 * l'identique.
 * \castest{<b>Les options écrites par l'écran Options se relisent à l'identique.</b><br/>
 * \tcat Unitaire · Données · Options<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire `interface.language` à « en », puis à « English ».<br/>2. Écrire des options
 *          réglées (2560 × 1440, fenêtré, anglais) puis les relire sur la base par défaut.<br/>
 * \tattendu « en » est lu ; « English » est une erreur qui garde « fr » ; les options relues sont
 *           celles écrites, sans erreur.
 * }
 */
TEST(GameOptionsTest, LaLangueSeLitEtLEcritureSeRelit) {
    EXPECT_EQ(core::readGameOptions(R"({"version": 1, "interface": {"language": "en"}})")
                  .options.language,
              "en");
    const core::GameOptionsResult refused =
        core::readGameOptions(R"({"version": 1, "interface": {"language": "English"}})");
    EXPECT_EQ(refused.errors.size(), 1U);
    EXPECT_EQ(refused.options.language, "fr");

    core::GameOptions written;
    written.width = 2560;
    written.height = 1440;
    written.fullscreen = false;
    written.language = "en";
    const core::GameOptionsResult read = core::readGameOptions(core::writeGameOptions(written));
    EXPECT_TRUE(read.ok());
    EXPECT_EQ(read.options, written);
}
