// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_rpg_enums.cpp
 * @brief Tests des enumerations RPG et de leur coincidence avec les schemas (LOT-32, EX-CNT-011).
 */

#include <filesystem>
#include <optional>
#include <set>
#include <string>
#include <string_view>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Data/JsonDocument.h"
#include "Core/Rpg/RpgEnumNames.h"
#include "Core/Rpg/RpgEnums.h"

namespace {

// Le schema qui porte les trois enumerations fermees. Chemin injecte par CMake : le test lit la
// donnee LIVREE, pas une copie -- une copie divergerait, et le test cesserait de prouver quoi que
// ce soit exactement quand il compterait.
const std::filesystem::path COMMON_SCHEMA =
    std::filesystem::path(JADG_RPG_SCHEMA_DIR) / "common.schema.json";

/// @brief Les valeurs de `$defs/<definition>/enum` du schema commun.
[[nodiscard]] std::set<std::string> enumDuSchema(std::string_view definition) {
    // supportedVersion = 0 : un JSON Schema ne porte pas le champ `version` du projet, et la
    // garde de version n'a donc rien a garder ici.
    const core::JsonDocument document = core::readJsonObjectFromFile(COMMON_SCHEMA, 0);
    EXPECT_TRUE(document.ok()) << COMMON_SCHEMA.string() << " : " << document.message;
    if (!document.ok()) {
        return {};
    }

    std::set<std::string> valeurs;
    const auto& defs = document.root["$defs"];
    const auto trouve = defs.find(std::string{definition});
    EXPECT_NE(trouve, defs.end()) << "definition absente du schema : " << definition;
    if (trouve == defs.end()) {
        return valeurs;
    }
    for (const auto& valeur : (*trouve)["enum"]) {
        valeurs.insert(valeur.get<std::string>());
    }
    return valeurs;
}

/// @brief Les noms produits par le C++ pour toute une enumeration.
template <typename Enum, typename Nommer>
[[nodiscard]] std::set<std::string> nomsDuMoteur(std::span<const Enum> valeurs, Nommer nommer) {
    std::set<std::string> noms;
    for (const Enum valeur : valeurs) {
        noms.insert(nommer(valeur));
    }
    return noms;
}

}  // namespace

/**
 * @brief Chaque valeur des trois enumerations fait l'aller-retour par son nom sans perte.
 * \castest{<b>Chaque valeur des enumerations RPG fait l'aller-retour par son nom sans
 * perte.</b><br/>
 * \tcat Unitaire · Enumerations RPG<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Pour chaque type de degats, condition et ecole de magie, convertir en nom puis
 * reconvertir en valeur.<br/>
 * \tattendu La valeur d'origine est retrouvee a chaque fois.
 * }
 */
TEST(RpgEnumsTest, AllerRetourSurToutesLesValeurs) {
    for (const core::DamageType type : core::allDamageTypes()) {
        const std::string nom = core::damageTypeName(type);
        ASSERT_FALSE(nom.empty()) << "type de degats sans nom";
        const std::optional<core::DamageType> relu = core::parseDamageType(nom);
        ASSERT_TRUE(relu.has_value()) << "nom non relu : " << nom;
        EXPECT_EQ(*relu, type) << "aller-retour incorrect pour " << nom;
    }
    for (const core::Condition condition : core::allConditions()) {
        const std::string nom = core::conditionName(condition);
        ASSERT_FALSE(nom.empty()) << "condition sans nom";
        const std::optional<core::Condition> relu = core::parseCondition(nom);
        ASSERT_TRUE(relu.has_value()) << "nom non relu : " << nom;
        EXPECT_EQ(*relu, condition) << "aller-retour incorrect pour " << nom;
    }
    for (const core::MagicSchool school : core::allMagicSchools()) {
        const std::string nom = core::magicSchoolName(school);
        ASSERT_FALSE(nom.empty()) << "ecole sans nom";
        const std::optional<core::MagicSchool> relu = core::parseMagicSchool(nom);
        ASSERT_TRUE(relu.has_value()) << "nom non relu : " << nom;
        EXPECT_EQ(*relu, school) << "aller-retour incorrect pour " << nom;
    }
    for (const core::CreatureSize size : core::allCreatureSizes()) {
        const std::string nom = core::creatureSizeName(size);
        ASSERT_FALSE(nom.empty()) << "taille sans nom";
        const std::optional<core::CreatureSize> relu = core::parseCreatureSize(nom);
        ASSERT_TRUE(relu.has_value()) << "nom non relu : " << nom;
        EXPECT_EQ(*relu, size) << "aller-retour incorrect pour " << nom;
    }
}

/**
 * @brief Deux valeurs distinctes ne partagent jamais le meme nom.
 * \castest{<b>Deux valeurs distinctes d'une enumeration RPG ne portent jamais le meme nom.</b><br/>
 * \tcat Unitaire · Enumerations RPG<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Collecter les noms de chaque enumeration dans un ensemble.<br/>
 * \tattendu Chaque ensemble contient autant d'elements que l'enumeration a de valeurs.
 * }
 */
TEST(RpgEnumsTest, LesNomsSontUniques) {
    EXPECT_EQ(nomsDuMoteur(core::allDamageTypes(), core::damageTypeName).size(),
              core::allDamageTypes().size());
    EXPECT_EQ(nomsDuMoteur(core::allConditions(), core::conditionName).size(),
              core::allConditions().size());
    EXPECT_EQ(nomsDuMoteur(core::allMagicSchools(), core::magicSchoolName).size(),
              core::allMagicSchools().size());
    EXPECT_EQ(nomsDuMoteur(core::allCreatureSizes(), core::creatureSizeName).size(),
              core::allCreatureSizes().size());
}

/**
 * @brief Un nom inconnu est refuse, jamais devine.
 * \castest{<b>Un nom d'enumeration RPG inconnu est refuse au lieu d'etre devine.</b><br/>
 * \tcat Unitaire · Enumerations RPG<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Analyser une chaine vide, un terme francais, et un nom de casse differente.<br/>
 * \tattendu Les trois analyses echouent, sans exception.
 * }
 */
TEST(RpgEnumsTest, UnNomInconnuEstRefuse) {
    EXPECT_FALSE(core::parseDamageType("").has_value());
    // Le francais est la valeur AFFICHEE, jamais la cle : c'est le scenario exact d'EX-CNT-011,
    // ou la donnee dit << psychique >> et le moteur ne connait que << psychic >>.
    EXPECT_FALSE(core::parseDamageType("psychique").has_value());
    EXPECT_FALSE(core::parseDamageType("Psychic").has_value());
    EXPECT_FALSE(core::parseCondition("empoisonne").has_value());
    EXPECT_FALSE(core::parseMagicSchool("invocation").has_value());
    // Le livre ecrit la taille en ABREGE -- << Bete de taille P >>. L'abreviation est une notation
    // du corpus, traduite a l'extraction ; le moteur, lui, ne connait que la valeur du schema.
    EXPECT_FALSE(core::parseCreatureSize("P").has_value());
    EXPECT_FALSE(core::parseCreatureSize("moyenne").has_value());
}

/**
 * @brief Les enumerations du C++ et celles des schemas sont identiques (EX-CNT-011).
 * \castest{<b>Les enumerations partagees entre le C++ et les schemas JSON sont identiques.</b><br/>
 * \tcat Unitaire · Enumerations RPG<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lire les enumerations `damageType`, `conditionRef` et `magicSchool` de
 * `common.schema.json`.<br/>
 * 2. Les comparer aux noms produits par `core::DamageType`, `core::Condition` et
 * `core::MagicSchool`.<br/>
 * \tattendu Les trois paires d'ensembles sont egales ; ajouter une valeur d'un seul cote fait
 * echouer ce test.
 * }
 */
TEST(RpgEnumsTest, LesEnumerationsCoincidentAvecLesSchemas) {
    // C'est le point ou une donnee et un moteur divergent en silence : le JSON declare une valeur
    // que le C++ ne connait pas, elle tombe dans un cas par defaut, et le sort cesse de faire des
    // degats sans que rien ne l'annonce. Ce test est ce qui rend cette divergence impossible.
    EXPECT_EQ(nomsDuMoteur(core::allDamageTypes(), core::damageTypeName),
              enumDuSchema("damageType"))
        << "core::DamageType et common.schema.json/$defs/damageType divergent";
    EXPECT_EQ(nomsDuMoteur(core::allConditions(), core::conditionName),
              enumDuSchema("conditionRef"))
        << "core::Condition et common.schema.json/$defs/conditionRef divergent";
    EXPECT_EQ(nomsDuMoteur(core::allMagicSchools(), core::magicSchoolName),
              enumDuSchema("magicSchool"))
        << "core::MagicSchool et common.schema.json/$defs/magicSchool divergent";
    // La taille se confronte au SCHEMA et non au lexique : le lexique n'en porte que cinq sous la
    // categorie << taille >>, << Moyenne >> ayant echappe a l'extraction du glossaire. Le schema,
    // lui, porte bien les six.
    EXPECT_EQ(nomsDuMoteur(core::allCreatureSizes(), core::creatureSizeName), enumDuSchema("size"))
        << "core::CreatureSize et common.schema.json/$defs/size divergent";
}

/**
 * @brief Les ensembles fermes ont le cardinal que les regles leur donnent.
 * \castest{<b>Les enumerations fermees du RPG ont le nombre de valeurs fixe par les
 * regles.</b><br/>
 * \tcat Unitaire · Enumerations RPG<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Compter les types de degats, les conditions et les ecoles de magie.<br/>
 * \tattendu 13, 15 et 8 respectivement.
 * }
 */
TEST(RpgEnumsTest, LesEnsemblesFermesOntLeurCardinal) {
    // Ces trois nombres sont fixes par les regles du jeu, pas par le corpus. Les ecrire ici fait
    // qu'une valeur retiree par megarde -- un `case` supprime lors d'une resolution de conflit --
    // ne passe pas inapercue : le test de coincidence, lui, resterait vert si les deux cotes
    // perdaient la meme valeur.
    EXPECT_EQ(core::allDamageTypes().size(), 13U);
    EXPECT_EQ(core::allConditions().size(), 15U);
    EXPECT_EQ(core::allMagicSchools().size(), 8U);
    EXPECT_EQ(core::allCreatureSizes().size(), 6U);
}
