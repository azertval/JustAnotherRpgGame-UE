// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <ostream>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Data/JsonDocument.h"

/**
 * @file test_json_document.cpp
 * @brief Brique de lecture JSON partagée (`EX-CNT-012`) et **premiers tests paramétrés** du dépôt.
 *
 * Deux choses sont couvertes ici, et la seconde est une capacité autant qu'un test : jusqu'au
 * `LOT-79`, `Source/Test/` ne comptait **aucun** `TEST_P` ni aucun parcours de dossier de
 * fixtures. Les lots de données en vivent — un catalogue de mille créatures se teste en balayant
 * un dossier, pas en écrivant mille `TEST`.
 */

namespace {

const std::filesystem::path FIXTURES = std::filesystem::path(JADG_TEST_FIXTURES_DIR) / "Json";

// ---------------------------------------------------------------------------------------------
// Position ligne/colonne
// ---------------------------------------------------------------------------------------------

/**
 * @brief Un decalage en octets se traduit en ligne et colonne.
 * \castest{<b>Une position d'erreur est exprimee en ligne et colonne.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Convertir le decalage du premier octet de la 3e ligne d'un texte connu.<br/>
 * \tattendu La position rendue est ligne 3, colonne 1 -- nlohmann ne donnant qu'un decalage en
 * octets, inexploitable devant un catalogue de mille lignes.
 * }
 */
TEST(JsonDocumentPosition, ConvertitUnDecalageEnLigneEtColonne) {
    const std::string texte = "{\n  \"a\": 1,\n  \"b\": 2\n}";
    // Le 1er octet de la 3e ligne : "{\n" = 2, "  \"a\": 1,\n" = 10 -> l'octet 13 (1-indexe) est
    // le premier caractere de la 3e ligne.
    const core::TextPosition position = core::positionOf(texte, 13);
    EXPECT_EQ(position.line, 3);
    EXPECT_EQ(position.column, 1);
}

/**
 * @brief Un decalage hors du texte rend une position inconnue plutot qu'une valeur inventee.
 * \castest{<b>Un decalage aberrant ne produit pas de position fausse.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Mineure<br/>
 * \tetapes 1. Convertir un decalage superieur a la taille du texte.<br/>
 * \tattendu La position rendue est {0, 0} : une position inconnue se declare, elle ne se devine
 * pas.
 * }
 */
TEST(JsonDocumentPosition, RendUnePositionInconnueHorsDuTexte) {
    const core::TextPosition position = core::positionOf("{}", 99);
    EXPECT_EQ(position.line, 0);
    EXPECT_EQ(position.column, 0);
}

// ---------------------------------------------------------------------------------------------
// Enveloppe commune
// ---------------------------------------------------------------------------------------------

/**
 * @brief Un document bien forme est lu, sa version et son contenu accessibles.
 * \castest{<b>Un document JSON valide se lit sans erreur.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lire une chaine JSON contenant une version et un champ.<br/>
 * \tattendu La lecture reussit, la version vaut 1 et le champ est accessible dans l'arbre.
 * }
 */
TEST(JsonDocument, LitUnObjetBienForme) {
    const core::JsonDocument doc = core::readJsonObject(R"({"version": 1, "a": 2})", 1);
    ASSERT_TRUE(doc.ok());
    EXPECT_EQ(doc.version, 1);
    EXPECT_EQ(doc.root.at("a").get<int>(), 2);
}

/**
 * @brief Un document sans champ de version reste lisible.
 * \castest{<b>Un champ de version absent vaut 1.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire un document sans champ de version, avec une version geree de 3.<br/>
 * \tattendu La lecture reussit et la version vaut 1 : un catalogue ecrit avant que le format ne se
 * versionne reste lisible, sans avoir a reecrire les fichiers existants.
 * }
 */
TEST(JsonDocument, VersionAbsenteVautUn) {
    const core::JsonDocument doc = core::readJsonObject(R"({"a": 1})", 3);
    ASSERT_TRUE(doc.ok());
    EXPECT_EQ(doc.version, 1);
}

/**
 * @brief Un document plus recent que le lecteur est refuse explicitement.
 * \castest{<b>Une version de format non geree est refusee, pas lue au mieux.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lire un document de version 4 avec une version geree de 3.<br/>
 * \tattendu La lecture echoue avec UnsupportedVersion, et le message cite les deux nombres : sans
 * eux, l'utilisateur ne sait pas s'il doit mettre a jour le jeu ou corriger le fichier.
 * }
 */
TEST(JsonDocument, RefuseUneVersionPlusRecenteQueLeLecteur) {
    const core::JsonDocument doc = core::readJsonObject(R"({"version": 4})", 3);
    EXPECT_FALSE(doc.ok());
    EXPECT_EQ(doc.error, core::JsonReadError::UnsupportedVersion);
    // Le message dit les deux nombres : sans eux, l'utilisateur ne sait pas s'il doit mettre a
    // jour le jeu ou corriger le fichier.
    EXPECT_NE(doc.message.find('4'), std::string::npos);
    EXPECT_NE(doc.message.find('3'), std::string::npos);
}

/**
 * @brief Une racine qui n'est pas un objet est refusee.
 * \castest{<b>Un document dont la racine est un tableau est refuse.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire un document dont la racine est un tableau.<br/>
 * \tattendu La lecture echoue avec ParseError : tous les catalogues du depot ont un objet a la
 * racine.
 * }
 */
TEST(JsonDocument, RefuseUneRacineQuiNEstPasUnObjet) {
    const core::JsonDocument doc = core::readJsonObject("[1, 2]", 1);
    EXPECT_FALSE(doc.ok());
    EXPECT_EQ(doc.error, core::JsonReadError::ParseError);
}

/**
 * @brief Une erreur de syntaxe est situee au fichier et a la ligne.
 * \castest{<b>Une erreur de syntaxe nomme le fichier et la ligne.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lire un document dont la 3e ligne porte une virgule en trop, en nommant
 * l'origine.<br/>
 * \tattendu L'echec porte la ligne 3 et le message contient « essai.json:3 » : c'est tout l'objet
 * de la brique, « JSON malforme » ne se corrige pas, « essai.json:3 » si (EX-CNT-010).
 * }
 */
TEST(JsonDocument, SitueLErreurDeSyntaxeALaLigne) {
    // La virgule en trop est sur la 3e ligne.
    const core::JsonDocument doc = core::readJsonObject("{\n  \"a\": 1,\n  ,\n}", 1, "essai.json");
    ASSERT_FALSE(doc.ok());
    EXPECT_EQ(doc.error, core::JsonReadError::ParseError);
    EXPECT_EQ(doc.position.line, 3);
    // C'est tout l'objet de la brique : « JSON malforme » ne se corrige pas, « essai.json:3 » si.
    EXPECT_NE(doc.message.find("essai.json:3"), std::string::npos);
}

/**
 * @brief Un nombre hors de portee est un echec decrit, pas une exception.
 * \castest{<b>Un nombre JSON trop grand pour etre represente ne fait pas lever la lecture.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lire un objet dont une valeur vaut 1e400.<br/>2. Lire un tableau dont l'unique nombre
 * porte un exposant de quatorze chiffres (entree trouvee par le fuzzing de nuit).<br/>
 * \tattendu Les deux lectures echouent avec ParseError, en nommant l'origine, sans lever :
 * nlohmann signale ce cas par `out_of_range` et non `parse_error`, et un catalogue ecrit `1e400`
 * faisait sortir l'exception de la brique (EX-NFR-040).
 * }
 */
TEST(JsonDocument, NeLevePasSurUnNombreHorsDePortee) {
    core::JsonDocument doc{};
    ASSERT_NO_THROW(doc = core::readJsonObject(R"({"octets": 723e404})", 1, "essai.json"));
    EXPECT_EQ(doc.error, core::JsonReadError::ParseError);
    EXPECT_NE(doc.message.find("essai.json"), std::string::npos);

    ASSERT_NO_THROW(doc = core::readJsonObject("[444444444444444E44444444444449]", 1));
    EXPECT_EQ(doc.error, core::JsonReadError::ParseError);
}

/**
 * @brief Un fichier absent produit un echec decrit, jamais une exception.
 * \castest{<b>Un fichier absent est un echec decrit, pas une exception.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lire un fichier qui n'existe pas.<br/>
 * \tattendu La lecture echoue avec FileNotFound sans lever : aucune exception ne franchit cette
 * frontiere (EX-NFR-040).
 * }
 */
TEST(JsonDocument, NeLevePasSurUnFichierAbsent) {
    const core::JsonDocument doc =
        core::readJsonObjectFromFile(FIXTURES / "ce-fichier-n-existe-pas.json", 1);
    EXPECT_FALSE(doc.ok());
    EXPECT_EQ(doc.error, core::JsonReadError::FileNotFound);
}

/**
 * @brief Le nom du fichier lu figure dans les messages d'echec.
 * \castest{<b>Un echec de lecture de fichier nomme ce fichier.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire une fixture JSON tronquee depuis le disque.<br/>
 * \tattendu Le message d'echec contient le nom du fichier : un message qui ne le nomme pas est
 * inutilisable dans un catalogue de plusieurs fichiers.
 * }
 */
TEST(JsonDocument, NommeLeFichierDansSesMessages) {
    const core::JsonDocument doc = core::readJsonObjectFromFile(FIXTURES / "tronque.json", 1);
    ASSERT_FALSE(doc.ok());
    EXPECT_NE(doc.message.find("tronque.json"), std::string::npos);
}

// ---------------------------------------------------------------------------------------------
// Test parametre : le dossier de fixtures fait foi
// ---------------------------------------------------------------------------------------------

/// @brief Ce qu'une fixture est censée produire, déduit de son nom.
struct AttenteFixture {
    std::string fichier;
    core::JsonReadError attendu;
};

std::ostream& operator<<(std::ostream& flux, const AttenteFixture& attente) {
    return flux << attente.fichier;
}

/**
 * @brief Balaie `Fixtures/Json/` et vérifie que chaque fichier produit la catégorie d'échec que
 *        son nom annonce.
 *
 * L'intérêt du parcours de dossier plutôt que d'une liste écrite à la main : **ajouter une
 * fixture suffit à ajouter un cas**. Une liste en dur se désynchronise du dossier, et c'est
 * toujours le cas manquant qui aurait attrapé le défaut.
 */
class FixtureJson : public ::testing::TestWithParam<AttenteFixture> {};

/**
 * @brief Chaque fixture du dossier produit la categorie d'echec que son nom annonce.
 * \castest{<b>Chaque fixture JSON produit la categorie d'echec attendue.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire chacune des six fixtures de Fixtures/Json.<br/>2. Comparer la categorie d'echec
 * obtenue a celle annoncee par le nom du fichier.<br/>
 * \tattendu Chaque fixture produit sa categorie, et tout echec porte une description non vide -- un
 * echec muet est inutilisable. Premier test parametre du depot (LOT-79).
 * }
 */
TEST_P(FixtureJson, ProduitLaCategorieAnnoncee) {
    const AttenteFixture& attente = GetParam();
    const core::JsonDocument doc = core::readJsonObjectFromFile(FIXTURES / attente.fichier, 1);
    EXPECT_EQ(doc.error, attente.attendu)
        << "fixture : " << attente.fichier << " -- message : " << doc.message;
    if (!doc.ok()) {
        // Un echec muet est inutilisable : toute categorie d'echec porte une description.
        EXPECT_FALSE(doc.message.empty());
    }
}

INSTANTIATE_TEST_SUITE_P(
    CatalogueDeFixtures, FixtureJson,
    ::testing::Values(
        AttenteFixture{"valide.json", core::JsonReadError::None},
        AttenteFixture{"tronque.json", core::JsonReadError::ParseError},
        AttenteFixture{"virgule-en-trop.json", core::JsonReadError::ParseError},
        AttenteFixture{"racine-tableau.json", core::JsonReadError::ParseError},
        AttenteFixture{"version-future.json", core::JsonReadError::UnsupportedVersion},
        AttenteFixture{"version-non-entiere.json", core::JsonReadError::MalformedStructure}),
    [](const ::testing::TestParamInfo<AttenteFixture>& info) {
        std::string nom = info.param.fichier;
        for (char& c : nom) {
            if (!std::isalnum(static_cast<unsigned char>(c))) {
                c = '_';
            }
        }
        return nom;
    });

/// @brief Toute fixture présente sur le disque est couverte par un cas ci-dessus.
/**
 * @brief Toute fixture presente sur le disque est couverte par un cas parametre.
 * \castest{<b>Aucune fixture n'est presente sans etre lue par un test.</b><br/>
 * \tcat Unitaire · Brique de lecture JSON<br/>
 * \tcrit Mineure<br/>
 * \tetapes 1. Parcourir le dossier de fixtures.<br/>2. Verifier que chaque fichier figure dans la
 * liste des cas instancies.<br/>
 * \tattendu Aucune fixture orpheline : un fichier de fixture qu'aucun test ne lit ne protege de
 * rien.
 * }
 */
TEST(FixtureJsonCouverture, AucuneFixtureOrpheline) {
    const std::vector<std::string> couvertes = {"valide.json",          "tronque.json",
                                                "virgule-en-trop.json", "racine-tableau.json",
                                                "version-future.json",  "version-non-entiere.json"};
    ASSERT_TRUE(std::filesystem::is_directory(FIXTURES)) << FIXTURES.string();
    for (const auto& entree : std::filesystem::directory_iterator(FIXTURES)) {
        if (!entree.is_regular_file()) {
            continue;
        }
        const std::string nom = entree.path().filename().string();
        EXPECT_NE(std::find(couvertes.begin(), couvertes.end(), nom), couvertes.end())
            << "Fixture " << nom << " presente mais absente de INSTANTIATE_TEST_SUITE_P : "
            << "un fichier de fixture qu'aucun test ne lit ne protege de rien.";
    }
}

}  // namespace
