// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_layer_pieces.cpp
 * @brief Tests unitaires des **pièces** nommées par les cases de couche (format v4,
 *        `LOT-EDITOR-12`, `EX-EDIT-043`).
 */

#include <string>

#include <gtest/gtest.h>

#include "Core/Levels/Level.h"
#include "Core/Levels/LevelDraft.h"
#include "Core/Levels/LevelLoader.h"
#include "Core/Levels/LevelWriter.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileType.h"

namespace {

using core::LayerKind;
using core::LevelDraft;
using core::TileType;

// Carte v4 de 4 x 4 : un sol, un decor dont la case (1, 1) est un mur habille de `wall-red`.
constexpr const char* CARTE_V4 = R"({
  "version": 4, "name": "habillee", "width": 4, "height": 4,
  "tiles": [ {"x": 0, "y": 0, "type": "entry"}, {"x": 1, "y": 1, "type": "wall"} ],
  "layers": [
    {"name": "sol", "kind": "ground", "tiles": [ {"x": 0, "y": 0, "type": "dirt", "piece": "street"} ]},
    {"name": "relief", "kind": "decor", "tiles": [ {"x": 1, "y": 1, "type": "wall", "piece": "wall-red"} ]}
  ]
})";

[[nodiscard]] core::Level charger(const char* json) {
    core::LevelLoadResult loaded = core::LevelLoader::loadFromString(json);
    EXPECT_TRUE(loaded.ok()) << loaded.error;
    return std::move(*loaded.level);
}

// Rang de la couche de decor dans les couches d'un brouillon charge de CARTE_V4 : la collision est
// promue en tete, puis le sol, puis le decor.
constexpr std::size_t DECOR = 2;

}  // namespace

/**
 * @brief Une case de couche v4 porte son type **et** sa pièce, lus tels qu'écrits.
 * \castest{<b>Une case de couche porte son type et sa pièce.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger une carte v4 dont le décor nomme une pièce.<br/>2. Lire la case.<br/>
 * \tattendu La case de décor vaut `wall` et nomme `wall-red` ; le sol nomme `street`.
 * }
 */
TEST(LayerPiecesTest, UneCaseDeCouchePorteSonTypeEtSaPiece) {
    const core::Level level = charger(CARTE_V4);

    ASSERT_EQ(level.layers().size(), 3U);
    EXPECT_EQ(level.layers()[1].pieceAt(0, 0), "street");
    EXPECT_EQ(level.layers()[DECOR].tiles.tile(1, 1), TileType::Wall);
    EXPECT_EQ(level.layers()[DECOR].pieceAt(1, 1), "wall-red");
    EXPECT_TRUE(level.layers()[DECOR].pieceAt(2, 2).empty());
}

/**
 * @brief Une carte v3 est lue pour toujours : son assignation `"texture"` de la grille racine
 *        devient la pièce de la même case sur la couche de décor.
 * \castest{<b>L'assignation d'une carte v3 devient une pièce du décor.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger une carte v3 dont la grille racine porte une texture.<br/>2. Lire la couche
 * de décor.<br/>
 * \tattendu La pièce est sur le décor, à la même case ; la collision ne porte plus rien d'autre que
 * son type.
 * }
 */
TEST(LayerPiecesTest, LAssignationDUneCarteV3DevientUnePieceDuDecor) {
    const core::Level level = charger(R"({
      "version": 3, "width": 4, "height": 4,
      "tiles": [ {"x": 0, "y": 0, "type": "entry"},
                 {"x": 2, "y": 1, "type": "wall", "texture": "wall-left"} ],
      "layers": [ {"kind": "ground", "tiles": []}, {"kind": "decor", "tiles": [
                  {"x": 2, "y": 1, "type": "wall"} ]} ]
    })");

    EXPECT_EQ(level.layers()[DECOR].pieceAt(2, 1), "wall-left");
    EXPECT_EQ(level.tileMap().tile(2, 1), TileType::Wall);
}

/**
 * @brief Une carte v3 qui habille des cases sans couche de décor en reçoit une, nommée « relief ».
 * \castest{<b>Une v3 sans décor reçoit une couche de relief.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte v2 plate dont une tuile porte une texture.<br/>2. Lire ses
 * couches.<br/>
 * \tattendu Une couche de décor « relief » porte la pièce ; rien n'est perdu.
 * }
 */
TEST(LayerPiecesTest, UneV3SansDecorRecoitUneCoucheDeRelief) {
    const core::Level level = charger(R"({
      "width": 4, "height": 4,
      "tiles": [ {"x": 0, "y": 0, "type": "entry"},
                 {"x": 2, "y": 2, "type": "solid", "texture": "crate"} ]
    })");

    ASSERT_EQ(level.layers().size(), 2U);
    EXPECT_EQ(level.layers()[1].kind, LayerKind::Decor);
    EXPECT_EQ(level.layers()[1].name, "relief");
    EXPECT_EQ(level.layers()[1].pieceAt(2, 2), "crate");
}

/**
 * @brief Une carte v4 qui porte encore une assignation `"texture"` est refusée, pas lue à moitié.
 * \castest{<b>Une v4 qui porte une texture racine est refusée.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une v4 dont une tuile racine porte `texture`.<br/>
 * \tattendu Échec `ParseError`.
 * }
 */
TEST(LayerPiecesTest, UneV4QuiPorteUneTextureRacineEstRefusee) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(R"({
      "version": 4, "width": 2, "height": 2,
      "tiles": [ {"x": 0, "y": 0, "type": "entry"}, {"x": 1, "y": 1, "type": "wall", "texture": "w"} ]
    })");

    EXPECT_FALSE(loaded.ok());
    EXPECT_EQ(loaded.errorCode, core::LevelValidationError::ParseError);
}

/**
 * @brief Peindre un **autre** type sur une case de couche habillée retire sa pièce ; le **même**
 *        type la garde — un coup de pinceau involontaire ne l'efface pas.
 * \castest{<b>Un autre type retire la pièce, le même la garde.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Repeindre `wall` sur la case habillée.<br/>2. Peindre `dirt` dessus.<br/>
 * \tattendu La pièce survit au premier geste, pas au second.
 * }
 */
TEST(LayerPiecesTest, UnAutreTypeRetireLaPieceLeMemeLaGarde) {
    LevelDraft draft = LevelDraft::fromLevel(charger(CARTE_V4));

    EXPECT_FALSE(draft.paintLayerTile(DECOR, 1, 1, TileType::Wall));
    EXPECT_EQ(draft.layers()[DECOR].pieceAt(1, 1), "wall-red");

    EXPECT_TRUE(draft.paintLayerTile(DECOR, 1, 1, TileType::Dirt));
    EXPECT_TRUE(draft.layers()[DECOR].pieceAt(1, 1).empty());
}

/**
 * @brief `paintLayerRegion` retire aussi la pièce d'une case dont le type change, et l'annulation
 *        la rend.
 * \castest{<b>Une région repeinte retire la pièce ; l'annulation la rend.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Peindre un bloc de sable sur la case habillée.<br/>2. Annuler.<br/>
 * \tattendu Pièce retirée, puis rendue telle quelle.
 * }
 */
TEST(LayerPiecesTest, UneRegionRepeinteRetireLaPieceLAnnulationLaRend) {
    LevelDraft draft = LevelDraft::fromLevel(charger(CARTE_V4));

    ASSERT_TRUE(draft.paintLayerRegion(DECOR, 1, 1, {{TileType::Sand, TileType::Sand}}));
    EXPECT_TRUE(draft.layers()[DECOR].pieceAt(1, 1).empty());

    ASSERT_TRUE(draft.undo());
    EXPECT_EQ(draft.layers()[DECOR].pieceAt(1, 1), "wall-red");
}

/**
 * @brief Réduire la grille tronque les pièces hors des nouvelles bornes et garde les autres.
 * \castest{<b>Réduire la grille tronque les pièces hors bornes.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Réduire la carte à 2 × 2, puis à 1 × 1.<br/>
 * \tattendu La pièce de (1, 1) survit à 2 × 2 et disparaît à 1 × 1.
 * }
 */
TEST(LayerPiecesTest, ReduireLaGrilleTronqueLesPiecesHorsBornes) {
    LevelDraft draft = LevelDraft::fromLevel(charger(CARTE_V4));

    draft.resize(2, 2);
    EXPECT_EQ(draft.layers()[DECOR].pieceAt(1, 1), "wall-red");

    draft.resize(1, 1);
    EXPECT_FALSE(draft.layers()[DECOR].hasPieces());
}

/**
 * @brief Pièces et hauteurs survivent à l'aller-retour ; l'écrivain n'émet jamais `"texture"`.
 * \castest{<b>Pièces et hauteurs survivent à l'aller-retour.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Donner une hauteur à une case habillée.<br/>2. Écrire puis relire.<br/>
 * \tattendu Même pièce, même hauteur ; aucun champ `texture`.
 * }
 */
TEST(LayerPiecesTest, PiecesEtHauteursSurviventALAllerRetour) {
    core::LevelData data = charger(CARTE_V4).data();
    data.layers[DECOR].setElevation(1, 1, 2);

    const std::string json = core::LevelWriter::buildJson(data);
    EXPECT_EQ(json.find("\"texture\""), std::string::npos);
    const core::Level relue = charger(json.c_str());

    EXPECT_EQ(relue.layers()[DECOR].pieceAt(1, 1), "wall-red");
    EXPECT_EQ(relue.layers()[DECOR].elevationAt(1, 1), 2);
    EXPECT_EQ(relue.layers()[1].pieceAt(0, 0), "street");
}

/**
 * @brief Une case de couche **vide** qui nomme une pièce s'écrit quand même : rien de ce que
 *        l'auteur a posé ne se perd.
 * \castest{<b>Une case vide qui nomme une pièce s'écrit.</b><br/>
 * \tcat Unitaire · Pièces de couche<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Nommer une pièce sur une case sans type.<br/>2. Écrire puis relire.<br/>
 * \tattendu La case relue nomme la pièce, de type `empty`.
 * }
 */
TEST(LayerPiecesTest, UneCaseVideQuiNommeUnePieceSEcrit) {
    core::LevelData data = charger(CARTE_V4).data();
    data.layers[DECOR].setPiece(3, 3, "banner");

    const core::Level relue = charger(core::LevelWriter::buildJson(data).c_str());

    EXPECT_EQ(relue.layers()[DECOR].pieceAt(3, 3), "banner");
    EXPECT_EQ(relue.layers()[DECOR].tiles.tile(3, 3), TileType::Empty);
}
