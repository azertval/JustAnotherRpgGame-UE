// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_check.cpp
 * @brief Tests du jet de d20 : avantage, seuil, restitution (LOT-12, EX-REG-002, EX-REG-003).
 */

#include <array>
#include <filesystem>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Data/JsonDocument.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/Check.h"

namespace {

constexpr std::uint64_t GRAINE = 20260905U;

const std::filesystem::path DIFFICULTE =
    std::filesystem::path(JADG_RPG_RULES_DIR) / "difficulty.json";

/// @brief Le seuil d'un palier nomme, lu dans la DONNEE -- jamais un litteral (EX-REG-021).
[[nodiscard]] int seuil(std::string_view palier) {
    const core::JsonDocument document = core::readJsonObjectFromFile(DIFFICULTE, 0);
    EXPECT_TRUE(document.ok()) << DIFFICULTE.string() << " : " << document.message;
    if (!document.ok()) {
        return 0;
    }
    for (const auto& entree : document.root["tiers"]) {
        if (entree["id"].get<std::string>() == palier) {
            return entree["dc"].get<int>();
        }
    }
    ADD_FAILURE() << "palier de difficulte inconnu : " << palier;
    return 0;
}

}  // namespace

/**
 * @brief L'avantage garde le meilleur de deux des, le desavantage le pire.
 * \castest{<b>L'avantage garde le meilleur de deux des, le desavantage le pire.</b><br/>
 * \tcat Unitaire · Jet de d20<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lancer mille jets avec avantage, puis mille avec desavantage.<br/>
 * \tattendu Deux des sont lances a chaque fois, et le de retenu est respectivement le maximum et
 * le minimum des deux.
 * }
 */
TEST(CheckTest, AvantageEtDesavantageGardentLeBonDe) {
    core::DeterministicRandom random{GRAINE};
    for (int i = 0; i < 1000; ++i) {
        const core::CheckResult avantage =
            core::rollCheck(10, {}, core::RollStance::Advantage, random);
        ASSERT_EQ(avantage.dice.size(), 2U);
        EXPECT_EQ(avantage.keptDie, std::max(avantage.dice[0], avantage.dice[1]));

        const core::CheckResult desavantage =
            core::rollCheck(10, {}, core::RollStance::Disadvantage, random);
        ASSERT_EQ(desavantage.dice.size(), 2U);
        EXPECT_EQ(desavantage.keptDie, std::min(desavantage.dice[0], desavantage.dice[1]));
    }
}

/**
 * @brief Avantage et desavantage s'annulent, et ne se cumulent pas.
 * \castest{<b>Avantage et desavantage s'annulent entierement, et ne se cumulent jamais.</b><br/>
 * \tcat Unitaire · Jet de d20<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Determiner la posture pour 0/0, 1/0, 0/1, 1/1 et 2/1 sources.<br/>
 * \tattendu Normal, avantage, desavantage, normal, et normal -- deux avantages contre un
 * desavantage s'annulent aussi.
 * }
 */
TEST(CheckTest, AvantageEtDesavantageSAnnulent) {
    EXPECT_EQ(core::rollStance(0, 0), core::RollStance::Normal);
    EXPECT_EQ(core::rollStance(1, 0), core::RollStance::Advantage);
    EXPECT_EQ(core::rollStance(0, 1), core::RollStance::Disadvantage);
    EXPECT_EQ(core::rollStance(1, 1), core::RollStance::Normal);
    // La regle ANNULE, elle ne compte pas : deux avantages contre un desavantage donnent normal.
    // Sans cela, chaque nouvelle capacite demanderait d'arbitrer sa pile contre toutes les autres.
    EXPECT_EQ(core::rollStance(2, 1), core::RollStance::Normal);
    EXPECT_EQ(core::rollStance(1, 3), core::RollStance::Normal);
    EXPECT_EQ(core::rollStance(3, 0), core::RollStance::Advantage);

    // Une posture normale ne lance qu'un seul de.
    core::DeterministicRandom random{GRAINE};
    const core::CheckResult resultat = core::rollCheck(10, {}, core::rollStance(1, 1), random);
    EXPECT_EQ(resultat.dice.size(), 1U);
}

/**
 * @brief Un 1 ou un 20 naturel se distingue d'un total de 1 ou 20.
 * \castest{<b>Un 1 ou 20 naturel se distingue d'un total de 1 ou 20.</b><br/>
 * \tcat Unitaire · Jet de d20<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lancer jusqu'a obtenir un 20 naturel et un 1 naturel.<br/>
 * 2. Construire un resultat de total 20 obtenu avec un de de 8.<br/>
 * \tattendu Les naturels sont detectes ; le total de 20 obtenu avec un 8 ne l'est pas.
 * }
 */
TEST(CheckTest, NaturelsDistinguesDuTotal) {
    core::DeterministicRandom random{GRAINE};
    bool vingtVu = false;
    bool unVu = false;
    for (int i = 0; i < 2000 && !(vingtVu && unVu); ++i) {
        const core::CheckResult resultat =
            core::rollCheck(10, {}, core::RollStance::Normal, random);
        if (resultat.keptDie == 20) {
            EXPECT_TRUE(resultat.isNaturalTwenty());
            EXPECT_FALSE(resultat.isNaturalOne());
            vingtVu = true;
        }
        if (resultat.keptDie == 1) {
            EXPECT_TRUE(resultat.isNaturalOne());
            EXPECT_FALSE(resultat.isNaturalTwenty());
            unVu = true;
        }
    }
    EXPECT_TRUE(vingtVu);
    EXPECT_TRUE(unVu);

    // Un TOTAL de 20 obtenu avec un de de 8 et douze points de bonus n'est pas un 20 naturel.
    // Les confondre rendrait critique un jet sur deux a haut niveau.
    core::CheckResult total20;
    total20.dice = {8};
    total20.keptDie = 8;
    total20.total = 20;
    EXPECT_FALSE(total20.isNaturalTwenty());
}

/**
 * @brief Les modificateurs s'appliquent et gardent leur origine.
 * \castest{<b>Les modificateurs d'un jet s'appliquent et conservent leur origine.</b><br/>
 * \tcat Unitaire · Jet de d20<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lancer un jet avec +3 de Dexterite et +2 de maitrise.<br/>
 * 2. Lire la restitution.<br/>
 * \tattendu Le total vaut le de plus 5 ; la restitution nomme les deux origines et le seuil.
 * }
 */
TEST(CheckTest, ModificateursEtRestitution) {
    core::DeterministicRandom random{GRAINE};
    const std::array<core::Modifier, 2> modificateurs{
        core::Modifier{"Dexterite", 3},
        core::Modifier{"maitrise", 2},
    };
    const int cible = seuil("moyenne");
    ASSERT_EQ(cible, 15) << "le palier « moyenne » vient de la DONNEE, pas d'un litteral";

    const core::CheckResult resultat =
        core::rollCheck(cible, modificateurs, core::RollStance::Normal, random);
    EXPECT_EQ(resultat.total, resultat.keptDie + 5);
    EXPECT_EQ(resultat.target, cible);
    EXPECT_EQ(resultat.succeeded(), resultat.total >= cible);

    // « Vous echouez » n'apprend rien ; la restitution doit permettre de reconstituer le jet
    // (EX-REG-003).
    const std::string restitution = resultat.describe();
    EXPECT_NE(restitution.find("Dexterite"), std::string::npos);
    EXPECT_NE(restitution.find("maitrise"), std::string::npos);
    EXPECT_NE(restitution.find(std::to_string(cible)), std::string::npos);
    EXPECT_NE(restitution.find(std::to_string(resultat.total)), std::string::npos);
}

/**
 * @brief L'echelle de difficulte est une donnee complete et croissante.
 * \castest{<b>L'echelle de difficulte est une donnee complete et croissante.</b><br/>
 * \tcat Unitaire · Jet de d20<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Lire les paliers de difficulty.json.<br/>
 * \tattendu Six paliers, de 5 a 30, en ordre croissant -- aucun n'est ecrit dans le code
 * (EX-REG-021).
 * }
 */
TEST(CheckTest, EchelleDeDifficulteEnDonnee) {
    const core::JsonDocument document = core::readJsonObjectFromFile(DIFFICULTE, 0);
    ASSERT_TRUE(document.ok()) << DIFFICULTE.string() << " : " << document.message;

    const auto& paliers = document.root["tiers"];
    ASSERT_EQ(paliers.size(), 6U);
    int precedent = 0;
    for (const auto& palier : paliers) {
        const int dc = palier["dc"].get<int>();
        EXPECT_GT(dc, precedent) << "les paliers doivent etre strictement croissants";
        precedent = dc;
    }
    EXPECT_EQ(seuil("tres-facile"), 5);
    EXPECT_EQ(seuil("quasi-impossible"), 30);
}
