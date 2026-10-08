// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_tile_type_name.cpp
 * @brief Tests unitaires de la correspondance type de tuile <-> nom textuel (EX-LVL-003).
 */

#include <optional>
#include <set>
#include <string>

#include <gtest/gtest.h>

#include "Core/Levels/TileType.h"
#include "Core/Levels/TileTypeName.h"

namespace {

// Dernier type de l'enumeration : borne du parcours exhaustif, tiree de `TILE_TYPE_COUNT` pour
// suivre d'elle-meme un type ajoute.
constexpr int LAST_TILE_TYPE = core::TILE_TYPE_COUNT - 1;

}  // namespace

/**
 * @brief Chaque type de tuile fait l'aller-retour nom -> type sans perte.
 * \castest{<b>Chaque type de tuile fait l'aller-retour par son nom textuel sans perte.</b><br/>
 * \tcat Unitaire · Nom de type de tuile<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Pour tous les types, convertir le type en nom, puis le nom en type.<br/>
 * \tattendu Le type d'origine est retrouve a chaque fois.
 * }
 */
TEST(TileTypeNameTest, AllerRetourSurTousLesTypes) {
    for (int raw = 0; raw <= LAST_TILE_TYPE; ++raw) {
        const auto type = static_cast<core::TileType>(raw);
        const std::string name = core::tileTypeName(type);
        const std::optional<core::TileType> parsed = core::parseTileType(name);

        ASSERT_TRUE(parsed.has_value()) << "nom non relu : " << name;
        EXPECT_EQ(*parsed, type) << "aller-retour incorrect pour " << name;
    }
}

/**
 * @brief Deux types distincts ne partagent jamais le meme nom.
 * \castest{<b>Deux types de tuiles distincts ne portent jamais le meme nom.</b><br/>
 * \tcat Unitaire · Nom de type de tuile<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Collecter les noms de tous les types dans un ensemble.<br/>
 * \tattendu L'ensemble contient autant d'elements qu'il y a de types.
 * }
 */
TEST(TileTypeNameTest, LesNomsSontUniques) {
    std::set<std::string> names;
    for (int raw = 0; raw <= LAST_TILE_TYPE; ++raw) {
        names.insert(core::tileTypeName(static_cast<core::TileType>(raw)));
    }

    EXPECT_EQ(names.size(), static_cast<std::size_t>(LAST_TILE_TYPE + 1));
}

/**
 * @brief Un nom inconnu est refuse, jamais devine.
 * \castest{<b>Un nom de type inconnu est refuse au lieu d'etre devine.</b><br/>
 * \tcat Unitaire · Nom de type de tuile<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Convertir une chaine vide, un nom inexistant et un nom de casse differente.<br/>
 * \tattendu Les trois conversions echouent, sans exception.
 * }
 */
TEST(TileTypeNameTest, NomInconnuRefuse) {
    EXPECT_FALSE(core::parseTileType("").has_value());
    EXPECT_FALSE(core::parseTileType("mur").has_value());
    // La comparaison est sensible a la casse : « Solid » n'est pas « solid ». Un fichier ecrit a la
    // main avec une casse fantaisiste doit etre signale, pas interprete.
    EXPECT_FALSE(core::parseTileType("Solid").has_value());
}
