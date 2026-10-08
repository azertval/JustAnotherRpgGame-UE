// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_format_v4.cpp
 * @brief Tests unitaires du format de carte v4 (`LOT-EDITOR-12`) : versions passées, écriture
 *        canonique, identifiants, cases forcées, variantes, zones peintes, réserve de hauteur,
 *        emprise, type tactique et déduction de la collision.
 */

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/BattleGrid.h"
#include "Core/Levels/CollisionDerivation.h"
#include "Core/Levels/Level.h"
#include "Core/Levels/LevelDraft.h"
#include "Core/Levels/LevelLoader.h"
#include "Core/Levels/LevelVariant.h"
#include "Core/Levels/LevelWriter.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Levels/PieceFootprint.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileType.h"
#include "Core/Resources/ScenePieceManifest.h"

namespace {

using core::GridPosition;
using core::LayerKind;
using core::PieceTactical;
using core::TileType;

const std::filesystem::path FIXTURES = std::filesystem::path{JADG_TEST_FIXTURES_DIR} / "Levels";

[[nodiscard]] std::string lire(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary);
    std::ostringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

[[nodiscard]] core::Level charger(const std::string& json) {
    core::LevelLoadResult loaded = core::LevelLoader::loadFromString(json);
    EXPECT_TRUE(loaded.ok()) << loaded.error;
    return std::move(*loaded.level);
}

[[nodiscard]] core::Level chargerFichier(const std::filesystem::path& path) {
    core::LevelLoadResult loaded = core::LevelLoader::loadFromFile(path);
    EXPECT_TRUE(loaded.ok()) << loaded.error;
    return std::move(*loaded.level);
}

// Manifeste d'essai : un sol, un mur, un banc qu'on enjambe, un etal 2 x 1 qui arrete le pas, une
// flaque qui gene, et un muret renomme (ancien nom `low-wall`).
constexpr const char* MANIFESTE = R"({
  "version": 1, "disposition": "essai",
  "textures": {
    "scene/essai/street": {"file": "street.png", "class": "floor"},
    "scene/essai/wall-left": {"file": "wall-left.png", "class": "tall"},
    "scene/essai/bench": {"file": "bench.png", "class": "tall", "tactical": "open"},
    "scene/essai/stall": {"file": "stall.png", "class": "wide", "footprint": [2, 1],
                          "tactical": "obstacle"},
    "scene/essai/puddle": {"file": "puddle.png", "class": "floor", "tactical": "difficult"},
    "scene/essai/parapet": {"file": "parapet.png", "class": "tall", "tactical": "cover",
                            "aliases": ["scene/essai/low-wall"]},
    "scene/essai/odd": {"file": "odd.png", "class": "tall", "tactical": "bouncy"}
  }
})";

[[nodiscard]] core::ScenePieceManifest manifeste() {
    const core::ScenePieceManifestResult result =
        core::ScenePieceManifest::loadFromString(MANIFESTE);
    EXPECT_TRUE(result.ok()) << result.message;
    return result.manifest;
}

// Deux couches 4 x 2 : un sol de rues sur toute la premiere ligne, un decor vide.
[[nodiscard]] std::vector<core::TileLayer> couches() {
    std::vector<core::TileLayer> layers;
    layers.push_back(core::TileLayer{
        .name = "sol", .kind = LayerKind::Ground, .tiles = core::TileMap(4, 2), .properties = {}});
    layers.push_back(core::TileLayer{.name = "relief",
                                     .kind = LayerKind::Decor,
                                     .tiles = core::TileMap(4, 2),
                                     .properties = {}});
    for (int column = 0; column < 4; ++column) {
        layers[0].tiles.setTile(column, 0, TileType::Dirt);
        layers[0].setPiece(column, 0, "street");
    }
    return layers;
}

}  // namespace

// --- Versions passées et écriture canonique ------------------------------------------------------

/**
 * @brief Une carte de chaque version passée, gardée en fixture, se charge pour toujours.
 * \castest{<b>Une carte de chaque version se charge.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger `format-v0.json` à `format-v4.json`.<br/>
 * \tattendu Chacune se charge, entrée en (0, 0).
 * }
 */
TEST(FormatV4Test, UneCarteDeChaqueVersionSeCharge) {
    for (const char* nom : {"format-v0.json", "format-v1.json", "format-v2.json", "format-v3.json",
                            "format-v4.json"}) {
        SCOPED_TRACE(nom);
        const core::Level level = chargerFichier(FIXTURES / nom);
        EXPECT_EQ(level.entry(), (GridPosition{0, 0}));
    }
}

/**
 * @brief Charger puis écrire une carte v4 canonique rend le même fichier, octet pour octet.
 * \castest{<b>Une v4 canonique ressort octet pour octet.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger `format-v4.json`.<br/>2. L'écrire.<br/>
 * \tattendu Le texte écrit égale le fichier.
 * }
 */
TEST(FormatV4Test, UneV4CanoniqueRessortOctetPourOctet) {
    const std::filesystem::path path = FIXTURES / "format-v4.json";
    EXPECT_EQ(core::LevelWriter::toJsonString(chargerFichier(path)), lire(path));
}

/**
 * @brief Une carte v3 écrite ressort en v4 : ses assignations sont devenues des pièces de décor,
 *        et relire l'écriture rend encore le même texte.
 * \castest{<b>Une v3 ressort en v4, et se stabilise.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger `format-v3.json` et l'écrire.<br/>2. Relire et réécrire.<br/>
 * \tattendu Version 4, `piece` au lieu de `texture`, deux écritures identiques.
 * }
 */
TEST(FormatV4Test, UneV3RessortEnV4EtSeStabilise) {
    const std::string premiere =
        core::LevelWriter::toJsonString(chargerFichier(FIXTURES / "format-v3.json"));

    EXPECT_NE(premiere.find("\"version\": 4"), std::string::npos);
    EXPECT_NE(premiere.find(R"({"x": 3, "y": 0, "type": "wall", "piece": "wall-left"})"),
              std::string::npos);
    EXPECT_EQ(premiere.find("texture"), std::string::npos);
    EXPECT_EQ(core::LevelWriter::toJsonString(charger(premiere)), premiere);
}

/**
 * @brief La réserve de hauteur (D11) survit à l'aller-retour : étage de couche, hauteur de case et
 *        d'entité.
 * \castest{<b>La réserve de hauteur survit à l'aller-retour.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger `format-v4.json`.<br/>
 * \tattendu `floor` 1 sur le décor, `elevation` 1 en (2, 1) du sol, 2 sur Myr.
 * }
 */
TEST(FormatV4Test, LaReserveDeHauteurSurvitALAllerRetour) {
    const core::Level level = chargerFichier(FIXTURES / "format-v4.json");

    EXPECT_EQ(level.layers()[2].floor, 1);
    EXPECT_EQ(level.layers()[1].elevationAt(2, 1), 1);
    EXPECT_EQ(level.entities().front().elevation, 2);
}

// --- Identifiants, cases forcées -----------------------------------------------------------------

/**
 * @brief Deux entités du même identifiant rendent toute référence `carte#id` ambiguë : refusé.
 * \castest{<b>Deux entités du même id sont refusées.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte dont deux entités portent `e1`.<br/>
 * \tattendu Échec `DuplicateEntityId`.
 * }
 */
TEST(FormatV4Test, DeuxEntitesDuMemeIdSontRefusees) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(R"({
      "version": 4, "width": 2, "height": 1, "tiles": [ {"x": 0, "y": 0, "type": "entry"} ],
      "entities": [ {"id": "e1", "type": "npc", "x": 0, "y": 0},
                    {"id": "e1", "type": "chest", "x": 1, "y": 0} ]
    })");

    EXPECT_EQ(loaded.errorCode, core::LevelValidationError::DuplicateEntityId);
}

/**
 * @brief Le brouillon donne un identifiant neuf à toute entité posée, et ne le redonne jamais,
 *        même après une annulation.
 * \castest{<b>Un identifiant donné n'est jamais redonné.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Poser un coffre dans `format-v4.json` (compteur à 4).<br/>2. Annuler, poser un
 * autre coffre.<br/>
 * \tattendu `e4`, puis `e5` ; le compteur écrit vaut 6.
 * }
 */
TEST(FormatV4Test, UnIdentifiantDonneNEstJamaisRedonne) {
    core::LevelDraft draft =
        core::LevelDraft::fromLevel(chargerFichier(FIXTURES / "format-v4.json"));

    const auto premier = draft.placeEntity(core::MapEntity{.type = "chest", .position = {2, 0}});
    ASSERT_TRUE(premier.has_value());
    EXPECT_EQ(draft.entities()[*premier].id, "e4");

    ASSERT_TRUE(draft.undo());
    const auto second = draft.placeEntity(core::MapEntity{.type = "chest", .position = {2, 0}});
    ASSERT_TRUE(second.has_value());
    EXPECT_EQ(draft.entities()[*second].id, "e5");
    EXPECT_NE(draft.toJson().find("\"nextEntityId\": 6"), std::string::npos);
}

/**
 * @brief `entityIdFor` et `entityIdNumber` sont réciproques ; un id d'une autre forme n'a pas de
 *        numéro.
 * \castest{<b>Un id e&lt;n&gt; se lit et s'écrit.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Écrire et relire `e12`, puis lire `herald` et `e`.<br/>
 * \tattendu 12, puis rien.
 * }
 */
TEST(FormatV4Test, UnIdENSeLitEtSEcrit) {
    EXPECT_EQ(core::entityIdFor(12), "e12");
    EXPECT_EQ(core::entityIdNumber("e12"), 12);
    EXPECT_FALSE(core::entityIdNumber("herald").has_value());
    EXPECT_FALSE(core::entityIdNumber("e").has_value());
    EXPECT_FALSE(core::entityIdNumber("e1x").has_value());
}

/**
 * @brief Les cases forcées se rangent (ligne, colonne), sans doublon : l'écriture est canonique.
 * \castest{<b>Les cases forcées se rangent sans doublon.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger des cases forcées en désordre, dont un doublon.<br/>
 * \tattendu (1, 0), (0, 1), une seule fois chacune.
 * }
 */
TEST(FormatV4Test, LesCasesForceesSeRangentSansDoublon) {
    const core::Level level = charger(R"({
      "version": 4, "width": 2, "height": 2, "tiles": [ {"x": 0, "y": 0, "type": "entry"} ],
      "forced": [ {"x": 0, "y": 1}, {"x": 1, "y": 0}, {"x": 0, "y": 1} ]
    })");

    EXPECT_EQ(level.forcedCollision(), (std::vector<GridPosition>{{1, 0}, {0, 1}}));
}

/**
 * @brief Une case forcée hors de la carte est refusée.
 * \castest{<b>Une case forcée hors carte est refusée.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Charger une case forcée en (5, 5) sur une carte 2 × 2.<br/>
 * \tattendu Échec `OutOfBounds`.
 * }
 */
TEST(FormatV4Test, UneCaseForceeHorsCarteEstRefusee) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(R"({
      "version": 4, "width": 2, "height": 2, "tiles": [ {"x": 0, "y": 0, "type": "entry"} ],
      "forced": [ {"x": 5, "y": 5} ]
    })");

    EXPECT_EQ(loaded.errorCode, core::LevelValidationError::OutOfBounds);
}

// --- Variantes -----------------------------------------------------------------------------------

/**
 * @brief Une variante reprend les cases de sa base, trouvée en remontant les dossiers, change de
 *        planche et porte ses propres entités ; elle se réécrit en variante, octet pour octet.
 * \castest{<b>Une variante reprend les cases de sa base.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger `variante/quartier/nuit.json`, variante de `base`.<br/>2. La réécrire.<br/>
 * \tattendu Grille et entrée de la base, planche `coliseum-doom`, une seule entité (la sienne),
 * même texte.
 * }
 */
TEST(FormatV4Test, UneVarianteReprendLesCasesDeSaBase) {
    const std::filesystem::path path = FIXTURES / "variante" / "quartier" / "nuit.json";
    const core::Level base = chargerFichier(FIXTURES / "variante" / "base.json");
    const core::Level variante = chargerFichier(path);

    EXPECT_EQ(variante.base(), "base");
    EXPECT_EQ(variante.tileMap().width(), 3);
    EXPECT_EQ(variante.tileMap().tile(2, 1), TileType::Wall);
    EXPECT_EQ(variante.entry(), base.entry());
    ASSERT_EQ(variante.entities().size(), 1U);
    EXPECT_EQ(variante.entities().front().type, "spawnPoint");
    const auto scene = variante.layers()[1].properties.find("scene");
    ASSERT_NE(scene, variante.layers()[1].properties.end());
    EXPECT_EQ(std::get<std::string>(scene->second), "coliseum-doom");
    EXPECT_EQ(variante.layers()[1].pieceAt(1, 0), "sand-2");

    EXPECT_EQ(core::LevelWriter::toJsonString(variante), lire(path));
}

/**
 * @brief Sans moyen de lire sa base, une variante est refusée plutôt que chargée sans cases.
 * \castest{<b>Une variante sans base est refusée.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger la variante depuis une chaîne, sans résolveur.<br/>2. Déclarer une base
 * introuvable depuis un fichier.<br/>
 * \tattendu `MissingBase` les deux fois.
 * }
 */
TEST(FormatV4Test, UneVarianteSansBaseEstRefusee) {
    const std::string texte = lire(FIXTURES / "variante" / "quartier" / "nuit.json");
    EXPECT_EQ(core::LevelLoader::loadFromString(texte).errorCode,
              core::LevelValidationError::MissingBase);

    const core::LevelLoadResult sansBase = core::LevelLoader::loadFromString(
        R"({"version": 4, "name": "x", "base": "nulle-part"})",
        [](std::string_view id) { return core::LevelLoader::loadFromFile(FIXTURES / id); });
    EXPECT_EQ(sansBase.errorCode, core::LevelValidationError::MissingBase);
}

/**
 * @brief Une variante ne porte pas de cases : un champ de grille la fait refuser.
 * \castest{<b>Une variante qui porte des cases est refusée.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Charger une variante qui déclare `tiles`.<br/>
 * \tattendu `ParseError`.
 * }
 */
TEST(FormatV4Test, UneVarianteQuiPorteDesCasesEstRefusee) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(
        R"({"version": 4, "base": "base", "tiles": []})", [](std::string_view) {
            return core::LevelLoader::loadFromFile(FIXTURES / "format-v4.json");
        });

    EXPECT_EQ(loaded.errorCode, core::LevelValidationError::ParseError);
}

// --- Zones (D13) ---------------------------------------------------------------------------------

/**
 * @brief Une zone **peinte** couvre ses cases et elles seules ; `BattleGrid::zonesAt` la lit et
 *        applique son terrain difficile.
 * \castest{<b>Une zone peinte est lue par la grille tactique.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger `format-v4.json` (zone peinte en (1, 1) et (2, 2)).<br/>2. Construire sa
 * `BattleGrid`.<br/>
 * \tattendu Zone et difficulté en (1, 1) et (2, 2), rien en (2, 1).
 * }
 */
TEST(FormatV4Test, UneZonePeinteEstLueParLaGrilleTactique) {
    const core::Level level = chargerFichier(FIXTURES / "format-v4.json");
    const core::BattleGrid grid(level);
    const auto porteLaZone = [&grid](GridPosition cell) {
        const std::vector<const core::PropertyMap*> zones = grid.zonesAt(cell);
        return std::ranges::any_of(
            zones, [](const core::PropertyMap* zone) { return zone->contains("ratio"); });
    };

    EXPECT_TRUE(porteLaZone({1, 1}));
    EXPECT_TRUE(porteLaZone({2, 2}));
    EXPECT_FALSE(porteLaZone({2, 1}));
    EXPECT_TRUE(grid.isDifficult({2, 2}));
    EXPECT_FALSE(grid.isDifficult({2, 1}));
}

/**
 * @brief Une zone **rectangle** couvre `width` × `height` cases depuis sa case.
 * \castest{<b>Une zone rectangle couvre son rectangle.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Demander les cases d'une zone 2 × 1 en (1, 0).<br/>
 * \tattendu (1, 0) et (2, 0).
 * }
 */
TEST(FormatV4Test, UneZoneRectangleCouvreSonRectangle) {
    const core::MapEntity zone{
        .type = std::string{core::ZONE_ENTITY_TYPE},
        .position = {1, 0},
        .properties = {{"width", std::int64_t{2}}, {"height", std::int64_t{1}}}};

    EXPECT_EQ(core::zoneCells(zone), (std::vector<GridPosition>{{1, 0}, {2, 0}}));
}

// --- Emprise, type tactique, déduction -----------------------------------------------------------

/**
 * @brief L'emprise d'une pièce s'étend depuis son ancre vers les colonnes et lignes croissantes, et
 *        son pied est le coin opposé.
 * \castest{<b>Une emprise s'étend depuis son ancre.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Demander les cases et le pied d'une emprise 2 × 1 ancrée en (3, 4).<br/>
 * \tattendu (3, 4), (4, 4) ; pied (5, 5).
 * }
 */
TEST(FormatV4Test, UneEmpriseSEtendDepuisSonAncre) {
    const core::PieceFootprint etal{.columns = 2, .rows = 1};

    EXPECT_EQ(core::footprintCells({3, 4}, etal), (std::vector<GridPosition>{{3, 4}, {4, 4}}));
    EXPECT_EQ(core::footprintFootCorner({3, 4}, etal), (GridPosition{5, 5}));
    EXPECT_EQ(core::footprintFootCorner({3, 4}, {}), (GridPosition{4, 5}));
}

/**
 * @brief Le manifeste donne son type tactique à chaque pièce : déclaré, ou par défaut selon la
 *        classe (un sol passe, une pièce debout arrête la vue) ; il trouve une pièce par un ancien
 *        nom.
 * \castest{<b>Le manifeste dit ce qu'une pièce oppose.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Lire le manifeste d'essai.<br/>
 * \tattendu `street` passe, `wall-left` arrête la vue, `stall` le pas ; `low-wall` désigne
 * `parapet` ; un nom tactique inconnu garde le défaut.
 * }
 */
TEST(FormatV4Test, LeManifesteDitCeQuUnePieceOppose) {
    const core::ScenePieceManifest pieces = manifeste();

    EXPECT_EQ(pieces.find("street")->tactical, PieceTactical::Open);
    EXPECT_EQ(pieces.find("wall-left")->tactical, PieceTactical::Solid);
    EXPECT_EQ(pieces.find("bench")->tactical, PieceTactical::Open);
    EXPECT_EQ(pieces.find("stall")->tactical, PieceTactical::Obstacle);
    EXPECT_EQ(pieces.find("odd")->tactical, PieceTactical::Solid);
    ASSERT_NE(pieces.find("low-wall"), nullptr);
    EXPECT_EQ(pieces.find("low-wall")->name, "parapet");
}

/**
 * @brief La déduction : le sol passe, une case que rien ne couvre arrête la vue, un mur l'arrête,
 *        un étal large arrête le pas sur ses deux cases, et la plus forte contribution l'emporte.
 * \castest{<b>La collision se déduit des pièces.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Poser un étal 2 × 1 en (0, 0), un mur en (3, 0), un banc en (2, 0).<br/>2. Déduire.
 * <br/>
 * \tattendu `cliff` en (0, 0) et (1, 0), vide en (2, 0), `wall` en (3, 0), `wall` sur la ligne
 * vide.
 * }
 */
TEST(FormatV4Test, LaCollisionSeDeduitDesPieces) {
    std::vector<core::TileLayer> layers = couches();
    layers[1].setPiece(0, 0, "stall");
    layers[1].setPiece(2, 0, "bench");
    layers[1].tiles.setTile(3, 0, TileType::Wall);
    layers[1].setPiece(3, 0, "wall-left");
    const core::ScenePieceManifest pieces = manifeste();

    const core::CollisionDerivation derivee = core::deriveCollision(layers, 4, 2, &pieces);

    EXPECT_EQ(derivee.collision.tile(0, 0), TileType::Cliff);
    EXPECT_EQ(derivee.collision.tile(1, 0), TileType::Cliff);
    EXPECT_EQ(derivee.collision.tile(2, 0), TileType::Empty);
    EXPECT_EQ(derivee.collision.tile(3, 0), TileType::Wall);
    for (int column = 0; column < 4; ++column) {
        EXPECT_EQ(derivee.collision.tile(column, 1), TileType::Wall) << column;
    }
    EXPECT_TRUE(derivee.unknownPieces.empty());
    EXPECT_TRUE(derivee.unplayed.empty());
}

/**
 * @brief Sans pièce, le type décide ; une pièce inconnue retombe sur son type et est relevée ; la
 *        gêne et l'abri se déduisent vides et sont relevés ; un ancien nom compte.
 * \castest{<b>Types, pièces inconnues, gêne et abri.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser de l'eau profonde sans pièce, une pièce inconnue sur un mur, une flaque, un
 * muret par son ancien nom.<br/>2. Déduire.<br/>
 * \tattendu `cliff`, `wall` relevé inconnu, vide et vide relevés non joués.
 * }
 */
TEST(FormatV4Test, TypesPiecesInconnuesGeneEtAbri) {
    std::vector<core::TileLayer> layers = couches();
    layers[0].tiles.setTile(0, 1, TileType::DeepWater);
    layers[1].tiles.setTile(1, 1, TileType::Wall);
    layers[1].setPiece(1, 1, "introuvable");
    layers[0].setPiece(2, 1, "puddle");
    layers[1].setPiece(3, 1, "low-wall");
    const core::ScenePieceManifest pieces = manifeste();

    const core::CollisionDerivation derivee = core::deriveCollision(layers, 4, 2, &pieces);

    EXPECT_EQ(derivee.collision.tile(0, 1), TileType::Cliff);
    EXPECT_EQ(derivee.collision.tile(1, 1), TileType::Wall);
    EXPECT_EQ(derivee.collision.tile(2, 1), TileType::Empty);
    EXPECT_EQ(derivee.collision.tile(3, 1), TileType::Empty);
    EXPECT_EQ(derivee.unknownPieces, (std::vector<GridPosition>{{1, 1}}));
    EXPECT_EQ(derivee.unplayed, (std::vector<GridPosition>{{2, 1}, {3, 1}}));
}

/**
 * @brief La grille écrite s'accorde avec la déduction là où elles valent pareil, l'entrée comptant
 *        pour une case vide.
 * \castest{<b>L'entrée s'accorde avec une case vide.</b><br/>
 * \tcat Unitaire · Format v4<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Comparer une entrée à du vide, un mur à du vide.<br/>
 * \tattendu Accord, puis désaccord.
 * }
 */
TEST(FormatV4Test, LEntreeSAccordeAvecUneCaseVide) {
    core::TileMap ecrite(2, 1);
    ecrite.setTile(0, 0, TileType::Entry);
    ecrite.setTile(1, 0, TileType::Wall);
    const core::TileMap deduite(2, 1);

    EXPECT_TRUE(core::collisionAgrees(ecrite, deduite, 0, 0));
    EXPECT_FALSE(core::collisionAgrees(ecrite, deduite, 1, 0));
}
