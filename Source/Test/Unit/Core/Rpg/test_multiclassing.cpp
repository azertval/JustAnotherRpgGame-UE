// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_multiclassing.cpp
 * @brief Tests du cumul des emplacements de sorts multiclasses (LOT-43, EX-RPG-041).
 */

#include <array>
#include <filesystem>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Data/JsonDocument.h"
#include "Core/Rpg/Multiclassing.h"

namespace {

const std::filesystem::path REGLE =
    std::filesystem::path(JADG_RPG_RULES_DIR) / "multiclassing.json";

/// @brief La table d'emplacements LIVREE : neuf valeurs par niveau de lanceur, indexee de 1 a 20.
[[nodiscard]] std::vector<std::array<int, 9>> tableLivree() {
    const core::JsonDocument document = core::readJsonObjectFromFile(REGLE, 0);
    EXPECT_TRUE(document.ok()) << REGLE.string() << " : " << document.message;
    std::vector<std::array<int, 9>> table(21, std::array<int, 9>{});
    if (!document.ok()) {
        return table;
    }
    for (const auto& ligne : document.root["spellSlots"]) {
        const int niveau = ligne["casterLevel"].get<int>();
        const auto& emplacements = ligne["slots"];
        for (std::size_t i = 0; i < table[0].size() && i < emplacements.size(); ++i) {
            table[static_cast<std::size_t>(niveau)][i] = emplacements[i].get<int>();
        }
    }
    return table;
}

constexpr core::ClassLevel plein(int niveau) {
    return {niveau, core::CasterProgression::Full};
}
constexpr core::ClassLevel demi(int niveau) {
    return {niveau, core::CasterProgression::Half};
}
constexpr core::ClassLevel tiers(int niveau) {
    return {niveau, core::CasterProgression::Third};
}
constexpr core::ClassLevel pacte(int niveau) {
    return {niveau, core::CasterProgression::Pact};
}

}  // namespace

/**
 * @brief L'exemple travaille du Manuel des Joueurs est reproduit a l'identique.
 * \castest{<b>L'exemple de multiclassage du Manuel des Joueurs est reproduit a
 * l'identique.</b><br/>
 * \tcat Unitaire · Multiclassage<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Calculer le niveau de lanceur d'un rodeur 4 / magicien 3.<br/>
 * 2. Lire les emplacements correspondants dans la table livree.<br/>
 * \tattendu Niveau de lanceur 5, et quatre emplacements de niveau 1, trois de niveau 2, deux de
 * niveau 3 -- les valeurs que le livre annonce lui-meme.
 * }
 */
TEST(MulticlassingTest, ExempleTravailleDuManuelDesJoueurs) {
    // « ce rodeur 4/magicien 3, vous etes considere comme un personnage de niveau 5 pour
    //  determiner vos emplacements de sorts : vous avez donc quatre emplacements de niveau 1,
    //  trois emplacements de niveau 2 et deux emplacements de niveau 3 » (p. 167).
    //
    // C'est le meilleur cas de test disponible : c'est le LIVRE qui verifie l'implementation, et
    // non l'implementation qui verifie sa propre arithmetique.
    const std::array<core::ClassLevel, 2> personnage{demi(4), plein(3)};
    const int niveau = core::multiclassCasterLevel(personnage);
    EXPECT_EQ(niveau, 5);

    const auto table = tableLivree();
    ASSERT_GT(table.size(), static_cast<std::size_t>(niveau));
    EXPECT_EQ(table[static_cast<std::size_t>(niveau)][0], 4);
    EXPECT_EQ(table[static_cast<std::size_t>(niveau)][1], 3);
    EXPECT_EQ(table[static_cast<std::size_t>(niveau)][2], 2);
}

/**
 * @brief L'arrondi se fait par classe, jamais sur le total.
 * \castest{<b>L'arrondi du niveau de lanceur se fait par classe, jamais sur le total.</b><br/>
 * \tcat Unitaire · Multiclassage<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Calculer le niveau de lanceur d'un paladin 3 / rodeur 3.<br/>
 * 2. Calculer celui d'un guerrier 5 / roublard 5 sous archetype.<br/>
 * \tattendu 2 et non 3 pour le premier ; 2 et non 3 pour le second.
 * }
 */
TEST(MulticlassingTest, LArrondiSeFaitParClasse) {
    // Paladin 3 + rodeur 3 : 1 + 1 = 2. Sommer d'abord et diviser ensuite donnerait 3, soit un
    // emplacement de trop -- a un niveau ou c'en est un tiers de plus.
    const std::array<core::ClassLevel, 2> paladinRodeur{demi(3), demi(3)};
    EXPECT_EQ(core::multiclassCasterLevel(paladinRodeur), 2);

    // Guerrier 5 + roublard 5 sous archetype : 1 + 1 = 2, et non 10 / 3 = 3.
    const std::array<core::ClassLevel, 2> guerrierRoublard{tiers(5), tiers(5)};
    EXPECT_EQ(core::multiclassCasterLevel(guerrierRoublard), 2);
}

/**
 * @brief La magie de pacte n'entre pas dans le cumul.
 * \castest{<b>Les emplacements de magie de pacte n'entrent pas dans le cumul multiclasse.</b><br/>
 * \tcat Unitaire · Multiclassage<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Calculer le niveau de lanceur d'un sorcier 5 / magicien 3.<br/>
 * \tattendu 3, la contribution du seul magicien ; les cinq niveaux de magie de pacte sont comptes
 * a part (EX-RPG-052).
 * }
 */
TEST(MulticlassingTest, LaMagieDePacteEstCompteeAPart) {
    // Les additionner doublerait la puissance du personnage sans que rien ne le signale : la
    // magie de pacte fournit des emplacements peu nombreux, toujours au niveau maximal, et
    // recuperes au repos COURT, en parallele des emplacements ordinaires.
    const std::array<core::ClassLevel, 2> sorcierMagicien{pacte(5), plein(3)};
    EXPECT_EQ(core::multiclassCasterLevel(sorcierMagicien), 3);
}

/**
 * @brief Les classes sans incantation n'apportent rien, et le total est borne a 20.
 * \castest{<b>Une classe sans incantation n'apporte rien au niveau de lanceur, borne a 20.</b><br/>
 * \tcat Unitaire · Multiclassage<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Calculer le niveau d'un barbare 10 seul, puis d'un magicien 20 / clerc 20.<br/>
 * \tattendu 0 pour le premier ; 20 pour le second, la table ne depassant pas ce niveau.
 * }
 */
TEST(MulticlassingTest, ClassesSansIncantationEtBorneSuperieure) {
    const std::array<core::ClassLevel, 1> barbare{core::ClassLevel{10}};
    EXPECT_EQ(core::multiclassCasterLevel(barbare), 0);

    const std::array<core::ClassLevel, 2> impossible{plein(20), plein(20)};
    EXPECT_EQ(core::multiclassCasterLevel(impossible), 20);
}

/**
 * @brief Les noms de progression font l'aller-retour, et un nom inconnu est refuse.
 * \castest{<b>Les noms de progression de lanceur font l'aller-retour sans perte.</b><br/>
 * \tcat Unitaire · Multiclassage<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Convertir chaque progression en nom, puis le nom en progression.<br/>
 * 2. Analyser un nom inconnu.<br/>
 * \tattendu La progression d'origine est retrouvee ; le nom inconnu est refuse sans exception.
 * }
 */
TEST(MulticlassingTest, AllerRetourDesNomsDeProgression) {
    for (const core::CasterProgression progression :
         {core::CasterProgression::None, core::CasterProgression::Third,
          core::CasterProgression::Half, core::CasterProgression::Full,
          core::CasterProgression::Pact}) {
        const std::string_view nom = core::casterProgressionName(progression);
        ASSERT_FALSE(nom.empty());
        const auto relu = core::parseCasterProgression(nom);
        ASSERT_TRUE(relu.has_value()) << "nom non relu : " << nom;
        EXPECT_EQ(*relu, progression);
    }
    // Deviner « none » ferait taire un lanceur : un nom inconnu se refuse.
    EXPECT_FALSE(core::parseCasterProgression("plein").has_value());
    EXPECT_FALSE(core::parseCasterProgression("").has_value());
}

/**
 * @brief La progression declaree par la donnee est celle que le moteur connait.
 * \castest{<b>Les progressions de lanceur de la donnee sont toutes connues du moteur.</b><br/>
 * \tcat Unitaire · Multiclassage<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lire `casterProgression` de multiclassing.json.<br/>
 * 2. Analyser chaque valeur avec `parseCasterProgression`.<br/>
 * \tattendu Les douze classes sont presentes et leurs progressions sont toutes reconnues.
 * }
 */
TEST(MulticlassingTest, LesProgressionsDeLaDonneeSontConnuesDuMoteur) {
    const core::JsonDocument document = core::readJsonObjectFromFile(REGLE, 0);
    ASSERT_TRUE(document.ok()) << REGLE.string() << " : " << document.message;

    const auto& progressions = document.root["casterProgression"];
    EXPECT_EQ(progressions.size(), 12U) << "les douze classes doivent declarer leur progression";
    for (const auto& entree : progressions) {
        const auto nom = entree["progression"].get<std::string>();
        EXPECT_TRUE(core::parseCasterProgression(nom).has_value())
            << "progression inconnue du moteur pour " << entree["class"].get<std::string>() << " : "
            << nom;
    }
}
