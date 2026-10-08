// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_dice.cpp
 * @brief Tests des des, des caracteristiques et de l'echelle (LOT-12, EX-NFR-002).
 */

#include <array>
#include <map>
#include <optional>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/Ability.h"
#include "Core/Rpg/Dice.h"
#include "Core/Rpg/Scale.h"

namespace {

constexpr std::uint64_t GRAINE = 20260905U;

}  // namespace

/**
 * @brief La notation de des est analysee sous ses trois formes.
 * \castest{<b>La notation de des est analysee sous ses trois formes.</b><br/>
 * \tcat Unitaire · Des<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Analyser << 2d6+3 >>, << 1d8 >>, << 4 >> et << 1d4-1 >>.<br/>
 * \tattendu Les quatre donnent le nombre de des, de faces et le modificateur attendus.
 * }
 */
TEST(DiceTest, AnalyseDesTroisFormes) {
    const auto avecModificateur = core::parseDice("2d6+3");
    ASSERT_TRUE(avecModificateur.has_value());
    EXPECT_EQ(avecModificateur->count, 2);
    EXPECT_EQ(avecModificateur->faces, 6);
    EXPECT_EQ(avecModificateur->modifier, 3);

    const auto simple = core::parseDice("1d8");
    ASSERT_TRUE(simple.has_value());
    EXPECT_EQ(*simple, (core::Dice{1, 8, 0}));

    const auto fixe = core::parseDice("4");
    ASSERT_TRUE(fixe.has_value());
    EXPECT_EQ(*fixe, (core::Dice{0, 0, 4}));

    const auto negatif = core::parseDice("1d4-1");
    ASSERT_TRUE(negatif.has_value());
    EXPECT_EQ(negatif->modifier, -1);

    EXPECT_EQ(core::formatDice(*avecModificateur), "2d6+3");
    EXPECT_EQ(core::formatDice(*negatif), "1d4-1");
    EXPECT_EQ(core::formatDice(*fixe), "4");
}

/**
 * @brief Une notation mal formee est refusee, jamais devinee.
 * \castest{<b>Une notation de des mal formee est refusee au lieu d'etre devinee.</b><br/>
 * \tcat Unitaire · Des<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Analyser << ld8 >> (faute d'OCR), une chaine vide, << 1d >>, << d6 >> et
 * << 1d6+2x >>.<br/>
 * \tattendu Les cinq sont refusees, sans exception.
 * }
 */
TEST(DiceTest, UneNotationMalFormeeEstRefusee) {
    // « ld8 » est LA faute que l'OCR du corpus produit (LOT-30) : un `1` lu comme un `l`. Elle est
    // invisible a la relecture et fatale a l'execution ; c'est ici qu'elle doit mourir.
    EXPECT_FALSE(core::parseDice("ld8").has_value());
    EXPECT_FALSE(core::parseDice("").has_value());
    EXPECT_FALSE(core::parseDice("1d").has_value());
    EXPECT_FALSE(core::parseDice("d6").has_value());
    EXPECT_FALSE(core::parseDice("1d6+2x").has_value());
    EXPECT_FALSE(core::parseDice("0d6").has_value());
    EXPECT_FALSE(core::parseDice("1d0").has_value());
}

/**
 * @brief Un lancer reste dans ses bornes et conserve chaque de.
 * \castest{<b>Un lancer de des reste dans ses bornes et conserve le detail de chaque de.</b><br/>
 * \tcat Unitaire · Des<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lancer 2d6+3 mille fois a graine fixe.<br/>
 * \tattendu Chaque total est dans [5, 15], chaque de dans [1, 6], et deux des sont conserves.
 * }
 */
TEST(DiceTest, UnLancerResteDansSesBornes) {
    const core::Dice dice{2, 6, 3};
    core::DeterministicRandom random{GRAINE};
    for (int i = 0; i < 1000; ++i) {
        const core::DiceRoll roll = core::rollDice(dice, random);
        ASSERT_EQ(roll.faces.size(), 2U);
        for (const int face : roll.faces) {
            EXPECT_GE(face, 1);
            EXPECT_LE(face, 6);
        }
        EXPECT_GE(roll.total, dice.minimum());
        EXPECT_LE(roll.total, dice.maximum());
    }
}

/**
 * @brief Meme graine, meme suite : la rejouabilite est stricte.
 * \castest{<b>Deux generateurs de meme graine produisent exactement la meme suite de des.</b><br/>
 * \tcat Unitaire · Des<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lancer cent fois 3d8 avec deux generateurs de meme graine.<br/>
 * 2. Recommencer avec une graine differente.<br/>
 * \tattendu Les deux premieres suites sont identiques de en de ; la troisieme differe.
 * }
 */
TEST(DiceTest, RejouabiliteStricte) {
    // Sans determinisme, AUCUN test de combat n'est ecrivable (EX-NFR-002). C'est la propriete
    // dont depend tout le reste de la filiere de jeu.
    const core::Dice dice{3, 8, 0};
    core::DeterministicRandom a{GRAINE};
    core::DeterministicRandom b{GRAINE};
    core::DeterministicRandom autre{GRAINE + 1};

    std::vector<int> suiteA;
    std::vector<int> suiteB;
    std::vector<int> suiteAutre;
    for (int i = 0; i < 100; ++i) {
        suiteA.push_back(core::rollDice(dice, a).total);
        suiteB.push_back(core::rollDice(dice, b).total);
        suiteAutre.push_back(core::rollDice(dice, autre).total);
    }
    EXPECT_EQ(suiteA, suiteB);
    EXPECT_NE(suiteA, suiteAutre);
}

/**
 * @brief La distribution d'un d20 est uniforme sur cent mille tirages.
 * \castest{<b>La distribution d'un d20 est uniforme sur cent mille tirages a graine fixe.</b><br/>
 * \tcat Unitaire · Des<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Tirer cent mille d20 a graine fixe et compter chaque face.<br/>
 * \tattendu Les vingt faces sortent, et chaque effectif s'ecarte de moins de 10 % de la moyenne
 * attendue.
 * }
 */
TEST(DiceTest, DistributionUniformeSurCentMilleTirages) {
    constexpr int TIRAGES = 100000;
    constexpr int FACES = 20;
    core::DeterministicRandom random{GRAINE};
    std::map<int, int> effectifs;
    for (int i = 0; i < TIRAGES; ++i) {
        ++effectifs[random.nextInt(1, FACES)];
    }

    ASSERT_EQ(effectifs.size(), static_cast<std::size_t>(FACES))
        << "toutes les faces doivent sortir";
    const double attendu = static_cast<double>(TIRAGES) / FACES;
    for (const auto& [face, compte] : effectifs) {
        EXPECT_GE(face, 1);
        EXPECT_LE(face, FACES);
        // 10 % de marge : large pour un ecart statistique normal (l'ecart-type vaut ici environ
        // 1,4 % de la moyenne), etroit pour un biais systematique, qui est ce qu'on cherche.
        EXPECT_NEAR(static_cast<double>(compte), attendu, attendu * 0.10)
            << "face " << face << " deseequilibree";
    }
}

/**
 * @brief `nextInt` respecte ses bornes, y compris degenerees.
 * \castest{<b>Le tirage entier respecte ses bornes, y compris quand elles sont egales.</b><br/>
 * \tcat Unitaire · Des<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Tirer dix mille fois dans [3, 3], puis dans [-5, 5].<br/>
 * \tattendu Le premier rend toujours 3 ; le second reste dans ses bornes et les atteint toutes
 * deux.
 * }
 */
TEST(DiceTest, BornesDuTirageEntier) {
    core::DeterministicRandom random{GRAINE};
    for (int i = 0; i < 100; ++i) {
        EXPECT_EQ(random.nextInt(3, 3), 3) << "un intervalle vide est une valeur fixe";
    }

    bool minAtteint = false;
    bool maxAtteint = false;
    for (int i = 0; i < 10000; ++i) {
        const int valeur = random.nextInt(-5, 5);
        ASSERT_GE(valeur, -5);
        ASSERT_LE(valeur, 5);
        minAtteint = minAtteint || valeur == -5;
        maxAtteint = maxAtteint || valeur == 5;
    }
    EXPECT_TRUE(minAtteint) << "la borne inferieure doit etre atteignable";
    EXPECT_TRUE(maxAtteint) << "la borne superieure doit etre atteignable (intervalle ferme)";
}

/**
 * @brief Le modificateur de caracteristique s'arrondit vers le bas.
 * \castest{<b>Le modificateur de caracteristique s'arrondit vers le bas, y compris en
 * negatif.</b><br/>
 * \tcat Unitaire · Caracteristiques<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Calculer le modificateur pour 1, 7, 8, 9, 10, 11, 15 et 20.<br/>
 * \tattendu -5, -2, -1, -1, 0, 0, +2, +5 -- le cas de 7 distinguant l'arrondi vers le bas de la
 * troncature vers zero.
 * }
 */
TEST(DiceTest, ModificateurArrondiVersLeBas) {
    EXPECT_EQ(core::abilityModifier(1), -5);
    EXPECT_EQ(core::abilityModifier(3), -4);
    // LE cas qui distingue les deux arrondis : (7 - 10) / 2 tronque vers zero donnerait -1.
    EXPECT_EQ(core::abilityModifier(7), -2);
    EXPECT_EQ(core::abilityModifier(8), -1);
    EXPECT_EQ(core::abilityModifier(9), -1);
    EXPECT_EQ(core::abilityModifier(10), 0);
    EXPECT_EQ(core::abilityModifier(11), 0);
    EXPECT_EQ(core::abilityModifier(15), 2);
    EXPECT_EQ(core::abilityModifier(20), 5);
    EXPECT_EQ(core::abilityModifier(30), 10);
}

/**
 * @brief Les six caracteristiques font l'aller-retour par leur nom.
 * \castest{<b>Les six caracteristiques font l'aller-retour par leur nom sans perte.</b><br/>
 * \tcat Unitaire · Caracteristiques<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Convertir chaque caracteristique en nom, puis le nom en caracteristique.<br/>
 * 2. Analyser un nom francais.<br/>
 * \tattendu Les six sont retrouvees ; le nom francais est refuse.
 * }
 */
TEST(DiceTest, AllerRetourDesCaracteristiques) {
    EXPECT_EQ(core::allAbilities().size(), 6U);
    for (const core::Ability ability : core::allAbilities()) {
        const std::string_view nom = core::abilityName(ability);
        ASSERT_FALSE(nom.empty());
        const auto relu = core::parseAbility(nom);
        ASSERT_TRUE(relu.has_value()) << "nom non relu : " << nom;
        EXPECT_EQ(*relu, ability);
    }
    // Le francais est la valeur AFFICHEE, jamais la cle (EX-CNT-011).
    EXPECT_FALSE(core::parseAbility("force").has_value());
}

/**
 * @brief L'echelle du monde convertit metres et cases dans les deux sens.
 * \castest{<b>L'echelle du monde convertit metres et cases dans les deux sens.</b><br/>
 * \tcat Unitaire · Echelle<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Convertir 9 metres en cases, puis 6 cases en metres.<br/>
 * \tattendu 6 cases et 9 metres -- une case vaut 1,5 m, et la conversion est reversible.
 * }
 */
TEST(DiceTest, EchelleDuMonde) {
    // Les portees du corpus sont en metres (« allonge 1,50 m », « vitesse 9 m ») et la grille
    // compte en cases : la conversion existe forcement quelque part, et elle n'existe qu'ici.
    EXPECT_FLOAT_EQ(core::METERS_PER_TILE, 1.5f);
    EXPECT_FLOAT_EQ(core::tilesFromMeters(9.0f), 6.0f);
    EXPECT_FLOAT_EQ(core::metersFromTiles(6.0f), 9.0f);
    EXPECT_FLOAT_EQ(core::tilesFromMeters(core::metersFromTiles(4.0f)), 4.0f);
}
