// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_map_layers.cpp
 * @brief Tests unitaires du format de carte `version: 3` : couches typées, entités, propriétés
 *        libres et migration ascendante (`EX-LVL-016`, `EX-LVL-017`, `EX-LVL-018`, LOT-04).
 */

#include <cstddef>
#include <string>
#include <variant>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Levels/GridPosition.h"
#include "Core/Levels/LevelDraft.h"
#include "Core/Levels/LevelLoader.h"
#include "Core/Levels/LevelWriter.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileType.h"

namespace {

// Carte version 2 : une grille plate unique, sans couche ni entite. Le format d'avant le LOT-04,
// tel qu'il vit encore dans tous les fichiers de niveau livres.
constexpr const char* MAP_V2 = R"({
  "version": 2,
  "name": "Grille plate",
  "width": 4,
  "height": 3,
  "tiles": [
    { "x": 0, "y": 0, "type": "solid" },
    { "x": 1, "y": 1, "type": "entry" }
  ]
})";

// Carte version 3 complete : la grille racine (collision, entree), deux couches visibles,
// deux entites, et des proprietes libres -- y compris des cles que le chargeur ne connait pas.
// Chargee, elle porte TROIS couches : la racine promue, puis le sol et le decor.
constexpr const char* MAP_V3 = R"({
  "version": 3,
  "name": "Village",
  "width": 4,
  "height": 3,
  "tiles": [
    { "x": 1, "y": 1, "type": "entry" },
    { "x": 0, "y": 0, "type": "solid" }
  ],
  "layers": [
    {
      "name": "sol",
      "kind": "ground",
      "tiles": [
        { "x": 0, "y": 0, "type": "solid" },
        { "x": 1, "y": 0, "type": "solid" }
      ]
    },
    {
      "name": "decor",
      "kind": "decor",
      "tiles": [{ "x": 2, "y": 1, "type": "wall" }],
      "difficultTerrain": true,
      "coverBonus": 2,
      "heightMeters": 1.5,
      "note": "tapis"
    }
  ],
  "entities": [
    { "type": "npc", "x": 2, "y": 2, "dialogue": "bonjour", "level": 3, "hostile": false },
    { "type": "chest", "x": 0, "y": 2 }
  ]
})";

// Couche de @p level portant le role @p kind, ou nullptr.
const core::TileLayer* layerOfKind(const core::Level& level, core::LayerKind kind) {
    for (const core::TileLayer& layer : level.layers()) {
        if (layer.kind == kind) {
            return &layer;
        }
    }
    return nullptr;
}

}  // namespace

/**
 * @brief Une carte `version: 2` se charge sans erreur, sa grille unique promue en couche
 * `Legacy` (`EX-LVL-016`).
 * \castest{<b>Une carte version 2 est promue en couche unique.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte au format version 2, sans tableau 'layers'.<br/>2. Inspecter les
 * couches du niveau obtenu.<br/>
 * \tattendu Le niveau porte exactement une couche, de role Legacy, dont la grille est celle de la
 * carte.
 * }
 */
TEST(CouchesDeCarteTest, CarteVersion2PromueEnCoucheLegacyUnique) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V2);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    ASSERT_EQ(loaded.level->layers().size(), 1u);
    const core::TileLayer& layer = loaded.level->layers().front();
    EXPECT_EQ(layer.kind, core::LayerKind::Legacy);
    EXPECT_EQ(layer.tiles.width(), loaded.level->tileMap().width());
    EXPECT_EQ(layer.tiles.height(), loaded.level->tileMap().height());
    EXPECT_EQ(layer.tiles.tile(0, 0), core::TileType::Solid);
    EXPECT_TRUE(loaded.level->entities().empty());
}

/**
 * @brief Une carte `version: 2` réécrite ressort **sans** tableau `layers` : la promotion ne
 * convertit pas le fichier dans le dos de son auteur (`EX-LVL-016`).
 * \castest{<b>Une carte version 2 reecrite ne gagne pas de tableau 'layers'.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Charger une carte version 2.<br/>2. La reserialiser.<br/>
 * \tattendu Le JSON produit ne contient ni 'layers' ni 'entities'.
 * }
 */
TEST(CouchesDeCarteTest, CarteVersion2ReecriteSansTableauDeCouches) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V2);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    const std::string json = core::LevelWriter::toJsonString(*loaded.level);
    EXPECT_EQ(json.find("\"layers\""), std::string::npos) << json;
    EXPECT_EQ(json.find("\"entities\""), std::string::npos) << json;
}

/**
 * @brief Une carte à trois couches et deux entités survit à l'aller-retour chargement → écriture
 * → rechargement (`EX-LVL-016`, `EX-LVL-017`).
 * \castest{<b>Une carte a trois couches et deux entites survit a l'aller-retour.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte version 3 a trois couches et deux entites.<br/>2. La reserialiser
 * puis la recharger.<br/>3. Comparer couches et entites au niveau d'origine.<br/>
 * \tattendu Roles, noms, grilles, types d'entites et positions sont identiques.
 * }
 */
TEST(CouchesDeCarteTest, AllerRetourSurTroisCouchesEtDeuxEntites) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V3);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    const std::string json = core::LevelWriter::toJsonString(*loaded.level);
    const core::LevelLoadResult reloaded = core::LevelLoader::loadFromString(json);
    ASSERT_TRUE(reloaded.ok()) << reloaded.error << "\n" << json;

    ASSERT_EQ(reloaded.level->layers().size(), loaded.level->layers().size());
    for (std::size_t index = 0; index < loaded.level->layers().size(); ++index) {
        const core::TileLayer& before = loaded.level->layers()[index];
        const core::TileLayer& after = reloaded.level->layers()[index];
        EXPECT_EQ(after.name, before.name);
        EXPECT_EQ(after.kind, before.kind);
        ASSERT_EQ(after.tiles.width(), before.tiles.width());
        ASSERT_EQ(after.tiles.height(), before.tiles.height());
        for (int row = 0; row < before.tiles.height(); ++row) {
            for (int column = 0; column < before.tiles.width(); ++column) {
                EXPECT_EQ(after.tiles.tile(column, row), before.tiles.tile(column, row))
                    << "couche '" << before.name << "' en (" << column << ", " << row << ")";
            }
        }
    }

    ASSERT_EQ(reloaded.level->entities().size(), 2u);
    EXPECT_EQ(reloaded.level->entities()[0].type, "npc");
    EXPECT_EQ(reloaded.level->entities()[0].position, (core::GridPosition{2, 2}));
    EXPECT_EQ(reloaded.level->entities()[1].type, "chest");
    EXPECT_EQ(reloaded.level->entities()[1].position, (core::GridPosition{0, 2}));
}

/**
 * @brief Les champs inconnus d'une couche sont ignorés sans erreur et **préservés** à la
 * réécriture, chacun dans son type JSON (`EX-LVL-018`).
 * \castest{<b>Les champs inconnus d'une couche sont preserves a la reecriture.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une couche portant quatre cles inconnues (booleen, entier, reel,
 * chaine).<br/>2. Reserialiser puis recharger.<br/>
 * \tattendu Les quatre cles sont toujours la, avec leur valeur et leur type.
 * }
 */
TEST(CouchesDeCarteTest, ChampsInconnusDUneCouchePreservesALaReecriture) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V3);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    const std::string json = core::LevelWriter::toJsonString(*loaded.level);
    const core::LevelLoadResult reloaded = core::LevelLoader::loadFromString(json);
    ASSERT_TRUE(reloaded.ok()) << reloaded.error;

    const core::TileLayer* decor = layerOfKind(*reloaded.level, core::LayerKind::Decor);
    ASSERT_NE(decor, nullptr);
    ASSERT_EQ(decor->properties.size(), 4u);
    EXPECT_EQ(std::get<bool>(decor->properties.at("difficultTerrain")), true);
    EXPECT_EQ(std::get<std::int64_t>(decor->properties.at("coverBonus")), 2);
    EXPECT_DOUBLE_EQ(std::get<double>(decor->properties.at("heightMeters")), 1.5);
    EXPECT_EQ(std::get<std::string>(decor->properties.at("note")), "tapis");
}

/**
 * @brief Les champs inconnus d'une entité sont ignorés sans erreur et **préservés** à la
 * réécriture (`EX-LVL-018`).
 * \castest{<b>Les champs inconnus d'une entite sont preserves a la reecriture.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une entite portant un dialogue, un niveau et un drapeau.<br/>2.
 * Reserialiser puis recharger.<br/>
 * \tattendu Les trois cles sont toujours la, avec leur valeur et leur type.
 * }
 */
TEST(CouchesDeCarteTest, ChampsInconnusDUneEntitePreservesALaReecriture) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V3);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    const std::string json = core::LevelWriter::toJsonString(*loaded.level);
    const core::LevelLoadResult reloaded = core::LevelLoader::loadFromString(json);
    ASSERT_TRUE(reloaded.ok()) << reloaded.error;

    ASSERT_EQ(reloaded.level->entities().size(), 2u);
    const core::MapEntity& npc = reloaded.level->entities().front();
    ASSERT_EQ(npc.properties.size(), 3u);
    EXPECT_EQ(std::get<std::string>(npc.properties.at("dialogue")), "bonjour");
    EXPECT_EQ(std::get<std::int64_t>(npc.properties.at("level")), 3);
    EXPECT_EQ(std::get<bool>(npc.properties.at("hostile")), false);
    EXPECT_TRUE(reloaded.level->entities().back().properties.empty());
}

/**
 * @brief La grille consommée par le gameplay est celle de la couche de **collision**, pas celle du
 * sol ni du décor (`EX-LVL-016`).
 * \castest{<b>La couche de collision est la grille du gameplay.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte dont le decor pose un mur en (2, 1), absent de la
 * collision.<br/>2. Lire la grille du niveau.<br/>
 * \tattendu La case (2, 1) est vide dans la grille du niveau : le decor ne bloque pas.
 * }
 */
TEST(CouchesDeCarteTest, LaCoucheDeCollisionEstLaGrilleDuGameplay) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V3);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    EXPECT_EQ(loaded.level->tileMap().tile(0, 0), core::TileType::Solid);
    EXPECT_EQ(loaded.level->tileMap().tile(2, 1), core::TileType::Empty);
    const core::TileLayer* decor = layerOfKind(*loaded.level, core::LayerKind::Decor);
    ASSERT_NE(decor, nullptr);
    EXPECT_EQ(decor->tiles.tile(2, 1), core::TileType::Wall);

    // La couche de tete EST la grille racine, promue : meme contenu, role Collision.
    const core::TileLayer* collision = layerOfKind(*loaded.level, core::LayerKind::Collision);
    ASSERT_NE(collision, nullptr);
    EXPECT_EQ(&loaded.level->layers().front(), collision);
    EXPECT_EQ(collision->tiles.tile(1, 1), core::TileType::Entry);
}

/**
 * @brief Une carte d'une version **future** est refusée avec un message explicite et une erreur
 * typée (`EX-LVL-005`, `EX-NFR-040`).
 * \castest{<b>Une carte d'une version future est refusee explicitement.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte declarant la version suivant la version courante.<br/>
 * \tattendu Le chargement echoue avec l'erreur UnsupportedFormatVersion et un message nommant la
 * version.
 * }
 */
TEST(CouchesDeCarteTest, CarteDUneVersionFutureRefuseeAvecUnMessageExplicite) {
    const std::string future = std::to_string(core::LEVEL_FORMAT_VERSION + 1);
    const std::string carte = R"({
      "version": )" + future + R"(,
      "name": "Trop neuve",
      "width": 2,
      "height": 2,
      "tiles": [
        { "x": 0, "y": 0, "type": "entry" }
      ]
    })";
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(carte);
    ASSERT_FALSE(loaded.ok());
    EXPECT_EQ(loaded.errorCode, core::LevelValidationError::UnsupportedFormatVersion);
    EXPECT_NE(loaded.error.find(future), std::string::npos) << loaded.error;
}

/**
 * @brief Une tuile hors bornes dans une couche est refusée, en nommant la couche fautive
 * (`EX-LVL-004`).
 * \castest{<b>Une tuile hors bornes dans une couche est refusee.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte dont une couche pose une tuile en dehors de la grille.<br/>
 * \tattendu Le chargement echoue avec l'erreur OutOfBounds et un message nommant la couche.
 * }
 */
TEST(CouchesDeCarteTest, TuileHorsBornesDansUneCoucheRefusee) {
    constexpr const char* MAP = R"({
      "version": 3,
      "name": "Debordement",
      "width": 2,
      "height": 2,
      "tiles": [
        { "x": 0, "y": 0, "type": "entry" }
      ],
      "layers": [
        { "name": "sol", "kind": "ground", "tiles": [{ "x": 5, "y": 0, "type": "solid" }] }
      ]
    })";
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP);
    ASSERT_FALSE(loaded.ok());
    EXPECT_EQ(loaded.errorCode, core::LevelValidationError::OutOfBounds);
    EXPECT_NE(loaded.error.find("sol"), std::string::npos) << loaded.error;
}

/**
 * @brief Une entité posée hors de la grille est refusée (`EX-LVL-017`).
 * \castest{<b>Une entite hors bornes est refusee.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte dont une entite est posee en dehors de la grille.<br/>
 * \tattendu Le chargement echoue avec l'erreur OutOfBounds.
 * }
 */
TEST(CouchesDeCarteTest, EntiteHorsBornesRefusee) {
    constexpr const char* MAP = R"({
      "version": 3,
      "name": "Egaree",
      "width": 2,
      "height": 2,
      "tiles": [
        { "x": 0, "y": 0, "type": "entry" }
      ],
      "entities": [{ "type": "npc", "x": 9, "y": 0 }]
    })";
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP);
    ASSERT_FALSE(loaded.ok());
    EXPECT_EQ(loaded.errorCode, core::LevelValidationError::OutOfBounds);
}

/**
 * @brief Un rôle de couche inconnu ne fait pas échouer la carte : la couche est chargée comme sol
 * (`EX-NFR-040`).
 * \castest{<b>Un role de couche inconnu ne fait pas echouer la carte.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Charger une carte dont une couche declare un role inconnu.<br/>
 * \tattendu La carte se charge, la couche prenant le role Ground.
 * }
 */
TEST(CouchesDeCarteTest, RoleDeCoucheInconnuRetombeSurLeSol) {
    constexpr const char* MAP = R"({
      "version": 3,
      "name": "Role inconnu",
      "width": 2,
      "height": 2,
      "tiles": [
        { "x": 0, "y": 0, "type": "entry" }
      ],
      "layers": [{ "name": "brouillard", "kind": "weather", "tiles": [] }]
    })";
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP);
    ASSERT_TRUE(loaded.ok()) << loaded.error;
    // Deux couches : la grille racine promue, puis la couche au role inconnu.
    ASSERT_EQ(loaded.level->layers().size(), 2u);
    EXPECT_EQ(loaded.level->layers().back().kind, core::LayerKind::Ground);
    EXPECT_EQ(loaded.level->layers().back().name, "brouillard");
}

/**
 * @brief Le brouillon d'édition **transporte** couches et entités : ouvrir puis réenregistrer une
 * carte multi-couches ne les efface pas (`EX-EDIT-011`, `EX-LVL-016`).
 * \castest{<b>Le brouillon d'edition preserve couches et entites.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte version 3 et en faire un brouillon d'edition.<br/>2. Reconvertir
 * le brouillon en niveau, sans rien modifier.<br/>
 * \tattendu Les trois couches et les deux entites sont toujours la.
 * }
 */
TEST(CouchesDeCarteTest, BrouillonDEditionPreserveCouchesEtEntites) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V3);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    const core::LevelDraft draft = core::LevelDraft::fromLevel(*loaded.level);
    EXPECT_EQ(draft.layers().size(), 3u);
    EXPECT_EQ(draft.entities().size(), 2u);

    const core::LevelLoadResult rebuilt = draft.toLevel();
    ASSERT_TRUE(rebuilt.ok()) << rebuilt.error;
    EXPECT_EQ(rebuilt.level->layers().size(), 3u);
    EXPECT_EQ(rebuilt.level->entities().size(), 2u);
}

/**
 * @brief La grille éditée dans le brouillon **est** la couche de collision : une tuile peinte s'y
 * retrouve à l'enregistrement (`EX-LVL-016`).
 * \castest{<b>Une tuile peinte dans l'editeur atteint la couche de collision.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Ouvrir une carte version 3 en brouillon.<br/>2. Peindre un solide en (2, 0).<br/>3.
 * Reconvertir le brouillon en niveau.<br/>
 * \tattendu La couche de collision porte le solide en (2, 0), le sol et le decor sont inchanges.
 * }
 */
TEST(CouchesDeCarteTest, TuilePeinteAtteintLaCoucheDeCollision) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V3);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    core::LevelDraft draft = core::LevelDraft::fromLevel(*loaded.level);
    draft.paintTile(2, 0, core::TileType::Solid);

    const core::LevelLoadResult rebuilt = draft.toLevel();
    ASSERT_TRUE(rebuilt.ok()) << rebuilt.error;

    const core::TileLayer* collision = layerOfKind(*rebuilt.level, core::LayerKind::Collision);
    ASSERT_NE(collision, nullptr);
    EXPECT_EQ(collision->tiles.tile(2, 0), core::TileType::Solid);

    const core::TileLayer* ground = layerOfKind(*rebuilt.level, core::LayerKind::Ground);
    ASSERT_NE(ground, nullptr);
    EXPECT_EQ(ground->tiles.tile(2, 0), core::TileType::Empty);
    EXPECT_EQ(ground->tiles.tile(1, 0), core::TileType::Solid);
}

/**
 * @brief Redimensionner un brouillon redimensionne **toutes** ses couches et abandonne les
 * entités sorties de la grille (`EX-LVL-016`, `EX-LVL-017`).
 * \castest{<b>Un redimensionnement emporte couches et entites.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Ouvrir une carte version 3 de 4x3 en brouillon.<br/>2. La redimensionner en
 * 2x2.<br/>
 * \tattendu Les couches font toutes 2x2, et les entites sorties de la grille ont disparu.
 * }
 */
TEST(CouchesDeCarteTest, RedimensionnementEmporteCouchesEtEntites) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP_V3);
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    core::LevelDraft draft = core::LevelDraft::fromLevel(*loaded.level);
    EXPECT_TRUE(draft.wouldResizeDropContent(2, 2));
    draft.resize(2, 2);

    for (const core::TileLayer& layer : draft.layers()) {
        EXPECT_EQ(layer.tiles.width(), 2);
        EXPECT_EQ(layer.tiles.height(), 2);
    }
    // Les deux entites vivaient en y = 2 : la grille reduite ne leur laisse plus de case.
    EXPECT_TRUE(draft.entities().empty());
}

/**
 * @brief Une couche `collision` **déclarée** est refusée : la grille de collision d'une carte est
 * son tableau racine `tiles` (`EX-LVL-016`).
 * \castest{<b>Une couche 'collision' declaree est refusee.</b><br/>
 * \tcat Unitaire · Couches de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte declarant une couche de role 'collision'.<br/>
 * \tattendu Le chargement echoue, avec un message renvoyant au tableau racine 'tiles'.
 * }
 */
TEST(CouchesDeCarteTest, CoucheDeCollisionDeclareeRefusee) {
    constexpr const char* MAP = R"({
      "version": 3,
      "name": "Deux grilles",
      "width": 2,
      "height": 2,
      "tiles": [
        { "x": 0, "y": 0, "type": "entry" }
      ],
      "layers": [
        { "name": "collision", "kind": "collision", "tiles": [] }
      ]
    })";
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(MAP);
    ASSERT_FALSE(loaded.ok());
    EXPECT_EQ(loaded.errorCode, core::LevelValidationError::ParseError);
    EXPECT_NE(loaded.error.find("tiles"), std::string::npos) << loaded.error;
}
