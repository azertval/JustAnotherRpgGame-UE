// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_asset_keys.cpp
 * @brief Tests des clés d'assets d'entité et de leurs marqueurs (`LOT-39`, `EX-CNT-040`,
 *        `EX-CNT-041`).
 *
 * Ces tests lisent la **donnée livrée** — la table des familles et les catalogues réels — parce que
 * c'est elle que le jeu chargera, et que le manifeste est dérivé : une fixture serait une seconde
 * source, qui divergerait au premier ajout de créature.
 */

#include <algorithm>
#include <filesystem>
#include <set>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Resources/AssetKey.h"
#include "Core/Resources/AssetMarker.h"

namespace {

[[nodiscard]] std::filesystem::path fichierDesFamilles() {
    return std::filesystem::path(JADG_ASSETS_DIR) / "Entities" / "families.json";
}

[[nodiscard]] const core::AssetFamilyTable& familles() {
    static const core::AssetFamilyTable table = core::loadAssetFamilies(fichierDesFamilles());
    return table;
}

}  // namespace

/**
 * @brief Une clé d'asset n'est **jamais** un chemin de fichier.
 * \castest{<b>Une cle d'asset n'est jamais un chemin de fichier.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Valider des cles bien formees.<br/>2. Valider des chemins et des cles
 * malformees.<br/>
 * \tattendu Seules les cles `famille/identifiant` sont acceptees ; tout ce qui ressemble a un
 * chemin est refuse.
 * }
 */
TEST(AssetKeyTest, UneCleNEstJamaisUnCheminDeFichier) {
    EXPECT_TRUE(core::isValidAssetKey("beast/wolf"));
    EXPECT_TRUE(core::isValidAssetKey("item/corde-en-chanvre-15-m"));
    EXPECT_TRUE(core::isValidAssetKey("weapon/epee-longue"));

    // Ce qui ressemble a un chemin, et qui lierait le catalogue a l'arborescence du disque.
    EXPECT_FALSE(core::isValidAssetKey("Assets/Entities/wolf.png"));
    EXPECT_FALSE(core::isValidAssetKey("beast/wolf/token")) << "trois segments : un chemin deguise";
    EXPECT_FALSE(core::isValidAssetKey("beast/wolf.png"));
    EXPECT_FALSE(core::isValidAssetKey("../beast/wolf"));

    // Syntaxe.
    EXPECT_FALSE(core::isValidAssetKey("wolf")) << "pas de famille";
    EXPECT_FALSE(core::isValidAssetKey("Beast/wolf")) << "majuscule";
    EXPECT_FALSE(core::isValidAssetKey("beast/")) << "identifiant vide";
    EXPECT_FALSE(core::isValidAssetKey("beast/-wolf")) << "tiret en tete";
    EXPECT_FALSE(core::isValidAssetKey("beast/wolf-")) << "tiret en fin";
    EXPECT_FALSE(core::isValidAssetKey("beast/gris--loup")) << "tirets doubles";
    EXPECT_FALSE(core::isValidAssetKey(""));
}

/**
 * @brief Une clé se décompose et se recompose sans perte.
 * \castest{<b>Une cle se decompose et se recompose sans perte.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Decomposer une cle valide.<br/>2. La reformer depuis ses deux morceaux.<br/>
 * \tattendu L'aller-retour redonne la cle de depart ; une cle malformee ne se devine pas.
 * }
 */
TEST(AssetKeyTest, UneCleSeDecomposeEtSeRecompose) {
    const auto decomposee = core::parseAssetKey("beast/giant-rat");
    ASSERT_TRUE(decomposee.has_value());
    EXPECT_EQ(decomposee->family, "beast");
    EXPECT_EQ(decomposee->id, "giant-rat");
    EXPECT_EQ(core::defaultAssetKeyFor(decomposee->family, decomposee->id), "beast/giant-rat");

    EXPECT_FALSE(core::parseAssetKey("pas une cle").has_value());
    EXPECT_TRUE(core::defaultAssetKeyFor("beast", "Loup").empty()) << "jamais devinee";
}

/**
 * @brief La table des familles LIVRÉE se charge, et chaque famille porte ses dimensions.
 * \castest{<b>La table des familles livree se charge.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger Assets/Entities/families.json.<br/>
 * \tattendu La table est valide, chaque famille a un nom conforme, des dimensions positives et au
 * moins un dossier de catalogue.
 * }
 */
TEST(AssetKeyTest, LaTableDesFamillesLivreeSeCharge) {
    ASSERT_TRUE(familles().ok()) << (familles().errors.empty() ? "" : familles().errors.front());
    for (const core::AssetFamilyDefinition& famille : familles().families) {
        EXPECT_FALSE(famille.name.empty());
        EXPECT_GT(famille.width, 0) << famille.name;
        EXPECT_GT(famille.height, 0) << famille.name;
        EXPECT_FALSE(famille.catalogues.empty()) << famille.name;
        // Le nom de famille doit lui-meme pouvoir former une cle.
        EXPECT_TRUE(core::isValidAssetKey(famille.name + "/essai")) << famille.name;
    }
    EXPECT_NE(familles().find("beast"), nullptr);
    EXPECT_EQ(familles().find("famille-inexistante"), nullptr);
}

/**
 * @brief **Aucune clé orpheline** dans les catalogues livrés — c'est le critère d'acceptation.
 * \castest{<b>Aucune cle d'asset orpheline dans les catalogues livres.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Deriver le manifeste des catalogues reels.<br/>2. Relever les erreurs.<br/>
 * \tattendu Aucune erreur : toute derogation ecrite dans une donnee est bien formee et nomme une
 * famille connue.
 * }
 */
TEST(AssetKeyTest, AucuneCleOrphelineDansLesCataloguesLivres) {
    std::vector<std::string> erreurs;
    const std::vector<core::ExpectedAssetKey> attendues =
        core::expectedAssetKeys(std::filesystem::path(JADG_RPG_DIR), familles(), erreurs);

    EXPECT_TRUE(erreurs.empty()) << (erreurs.empty() ? "" : erreurs.front());
    EXPECT_GT(attendues.size(), 300U) << "les catalogues livres en attendent plus de trois cents";
}

/**
 * @brief Le manifeste dérivé ne porte **aucun doublon**, et chaque clé est bien formée.
 * \castest{<b>Le manifeste derive n'a aucun doublon et chaque cle est bien formee.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Deriver le manifeste.<br/>2. Verifier l'unicite et la syntaxe de chaque cle.<br/>
 * \tattendu Chaque cle est unique, valide, et nomme une famille de la table.
 * }
 */
TEST(AssetKeyTest, LeManifesteDeriveNAPasDeDoublon) {
    std::vector<std::string> erreurs;
    const std::vector<core::ExpectedAssetKey> attendues =
        core::expectedAssetKeys(std::filesystem::path(JADG_RPG_DIR), familles(), erreurs);
    ASSERT_FALSE(attendues.empty());

    std::set<std::string> vues;
    for (const core::ExpectedAssetKey& attendue : attendues) {
        EXPECT_TRUE(core::isValidAssetKey(attendue.key)) << attendue.sourceFile;
        EXPECT_NE(familles().find(attendue.family), nullptr) << attendue.key;
        // Deux entrees peuvent DEROGER vers la meme illustration ; deux cles DERIVEES identiques,
        // en revanche, signalent deux entrees de meme identifiant dans un meme catalogue.
        if (!attendue.explicitKey) {
            EXPECT_TRUE(vues.insert(attendue.key).second)
                << "cle derivee en double : " << attendue.key << " (" << attendue.sourceFile << ")";
        }
    }
}

/**
 * @brief Un marqueur est **déterministe** : la même clé donne toujours le même.
 * \castest{<b>Un marqueur est deterministe.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Peindre deux fois le marqueur d'une meme cle.<br/>2. Peindre celui d'une autre
 * cle.<br/>
 * \tattendu Les deux premiers sont identiques pixel a pixel ; le troisieme differe.
 * }
 */
TEST(AssetMarkerTest, UnMarqueurEstDeterministe) {
    const core::MarkerImage premier = core::assetMarker("beast/wolf", 96, 96);
    const core::MarkerImage second = core::assetMarker("beast/wolf", 96, 96);
    ASSERT_FALSE(premier.isEmpty());
    EXPECT_EQ(premier.pixels, second.pixels)
        << "un marqueur tire au hasard changerait a chaque lancement";

    const core::MarkerImage autre = core::assetMarker("beast/giant-rat", 96, 96);
    ASSERT_FALSE(autre.isEmpty());
    EXPECT_NE(premier.pixels, autre.pixels) << "deux creatures ne se confondent pas";

    // Le hachage est ecrit dans le projet, et non emprunte a std::hash : sa valeur doit etre la
    // meme partout, sans quoi le marqueur d'un loup changerait de teinte au changement de
    // compilateur.
    EXPECT_EQ(core::stableAssetHash("beast/wolf"), core::stableAssetHash("beast/wolf"));
    EXPECT_NE(core::stableAssetHash("beast/wolf"), core::stableAssetHash("beast/wolt"));
}

/**
 * @brief Un marqueur respecte les dimensions demandées, et se voit **comme** un marqueur.
 * \castest{<b>Un marqueur respecte ses dimensions et se voit comme un marqueur.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Peindre un marqueur aux dimensions d'une famille.<br/>2. Comparer un pixel de la
 * diagonale a un pixel de coin.<br/>
 * \tattendu Les dimensions sont celles demandees, et les diagonales tranchent sur le fond.
 * }
 */
TEST(AssetMarkerTest, UnMarqueurRespecteSesDimensionsEtSeVoit) {
    const core::MarkerImage marqueur = core::assetMarker("species/demi-elfe", 128, 128);
    ASSERT_FALSE(marqueur.isEmpty());
    EXPECT_EQ(marqueur.width, 128);
    EXPECT_EQ(marqueur.height, 128);
    EXPECT_EQ(marqueur.pixels.size(), 128U * 128U);

    // Le centre est sur les deux diagonales ; un point du bord haut, entre elles, ne l'est pas.
    const core::MarkerColor centre = marqueur.at(64, 64);
    const core::MarkerColor bord = marqueur.at(64, 4);
    EXPECT_NE(centre, bord) << "sans diagonales, le marqueur passerait pour une illustration";
    EXPECT_EQ(centre.a, 255) << "un marqueur est opaque : un trou reste un trou";
}

/**
 * @brief Une clé malformée ne reçoit **pas** de marqueur.
 * \castest{<b>Une cle malformee ne recoit pas de marqueur.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Demander le marqueur d'une cle malformee, puis de dimensions nulles.<br/>
 * \tattendu L'image est vide dans les deux cas.
 * }
 */
TEST(AssetMarkerTest, UneCleMalformeeNeRecoitPasDeMarqueur) {
    EXPECT_TRUE(core::assetMarker("Assets/wolf.png", 96, 96).isEmpty())
        << "lui donner un marqueur la ferait passer pour une entree en attente d'illustration";
    EXPECT_TRUE(core::assetMarker("beast/wolf", 0, 96).isEmpty());
    EXPECT_TRUE(core::assetMarker("beast/wolf", 96, -1).isEmpty());
}

/**
 * @brief **Toute** clé attendue par les catalogues obtient un marqueur : le jeu tourne complet.
 * \castest{<b>Toute cle attendue obtient un marqueur.</b><br/>
 * \tcat Unitaire · Assets<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Deriver le manifeste des catalogues reels.<br/>2. Peindre le marqueur de chaque cle
 * aux dimensions de sa famille.<br/>
 * \tattendu Aucune image vide : les trois cents entrees sont affichables avant qu'aucune
 * illustration n'existe (EX-CNT-041).
 * }
 */
TEST(AssetMarkerTest, TouteCleAttendueObtientUnMarqueur) {
    std::vector<std::string> erreurs;
    const std::vector<core::ExpectedAssetKey> attendues =
        core::expectedAssetKeys(std::filesystem::path(JADG_RPG_DIR), familles(), erreurs);
    ASSERT_FALSE(attendues.empty());

    int peints = 0;
    for (const core::ExpectedAssetKey& attendue : attendues) {
        const core::AssetFamilyDefinition* const famille = familles().find(attendue.family);
        ASSERT_NE(famille, nullptr) << attendue.key;
        const core::MarkerImage marqueur =
            core::assetMarker(attendue.key, famille->width, famille->height);
        ASSERT_FALSE(marqueur.isEmpty()) << "clé sans marqueur : " << attendue.key;
        EXPECT_EQ(marqueur.width, famille->width) << attendue.key;
        ++peints;
    }
    EXPECT_EQ(peints, static_cast<int>(attendues.size()));
}
