// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_level_draft.cpp
 * @brief Tests unitaires du modèle d'édition mutable (EX-EDIT-002 à EX-EDIT-007).
 */

#include <vector>

#include <gtest/gtest.h>

#include "Core/Levels/GridPosition.h"
#include "Core/Levels/LevelDraft.h"
#include "Core/Levels/LevelLoader.h"
#include "Core/Levels/TileType.h"

namespace {

using core::GridPosition;
using core::LevelDraft;
using core::TileType;

}  // namespace

/**
 * @brief paintTile pose le type demandé sur la case visée.
 * \castest{<b>paintTile pose le type demandé sur la case visée.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu paintTile pose le type demandé sur la case visée.
 * }
 */
TEST(LevelDraftTest, PaintTilePoseLeType) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    draft.paintTile(1, 1, TileType::Solid);
    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Solid);
}

/**
 * @brief Poser une seconde entrée déplace la première (unicité, EX-EDIT-004).
 * \castest{<b>Poser une seconde entrée déplace la première (unicité, EX-EDIT-004).</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Poser une seconde entrée déplace la première (unicité, EX-EDIT-004).
 * }
 */
TEST(LevelDraftTest, SetEntryDeplaceLEntreeExistante) {
    LevelDraft draft = LevelDraft::empty("N", 4, 4);
    draft.setEntry(0, 0);
    ASSERT_TRUE(draft.entry().has_value());
    EXPECT_EQ(*draft.entry(), (GridPosition{0, 0}));

    draft.setEntry(2, 2);
    EXPECT_EQ(*draft.entry(), (GridPosition{2, 2}));
    EXPECT_EQ(draft.tileMap().tile(0, 0), TileType::Empty);
    EXPECT_EQ(draft.tileMap().tile(2, 2), TileType::Entry);
}

/**
 * @brief Peindre par-dessus l'entrée invalide la position d'entrée mémorisée.
 * \castest{<b>Peindre par-dessus l'entrée invalide la position d'entrée mémorisée.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Peindre par-dessus l'entrée invalide la position d'entrée mémorisée.
 * }
 */
TEST(LevelDraftTest, PeindrePardessusLEntreeLInvalide) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    draft.setEntry(1, 1);
    draft.paintTile(1, 1, TileType::Solid);
    EXPECT_FALSE(draft.entry().has_value());
    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Solid);
}

/**
 * @brief Agrandir la grille conserve le contenu existant et complète en cases vides.
 * \castest{<b>Agrandir la grille conserve le contenu existant et complète en cases
 * vides.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Agrandir la grille conserve le contenu existant et complète en cases vides.
 * }
 */
TEST(LevelDraftTest, AgrandirConserveLeContenu) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    draft.setEntry(1, 1);
    draft.resize(5, 5);

    EXPECT_EQ(draft.tileMap().width(), 5);
    EXPECT_EQ(draft.tileMap().height(), 5);
    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Entry);
    EXPECT_EQ(*draft.entry(), (GridPosition{1, 1}));
    EXPECT_EQ(draft.tileMap().tile(4, 4), TileType::Empty);
}

/**
 * @brief Réduire la grille tronque le contenu hors bornes et invalide l'entrée perdue.
 * \castest{<b>Réduire la grille tronque le contenu hors bornes et invalide l'entrée
 * perdue.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Réduire la grille tronque le contenu hors bornes et invalide l'entrée perdue.
 * }
 */
TEST(LevelDraftTest, ReduireTronqueEtInvalideLEntreePerdue) {
    LevelDraft draft = LevelDraft::empty("N", 5, 5);
    draft.setEntry(4, 4);
    draft.paintTile(1, 1, TileType::Solid);

    draft.resize(3, 3);

    EXPECT_EQ(draft.tileMap().width(), 3);
    EXPECT_EQ(draft.tileMap().height(), 3);
    EXPECT_FALSE(draft.entry().has_value());
    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Solid);
}

/**
 * @brief toLevel() sur un brouillon sans entrée échoue avec un message récupérable (EX-EDIT-007).
 * \castest{<b>toLevel() sur un brouillon sans entrée échoue avec un message récupérable
 * (EX-EDIT-007).</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu toLevel() sur un brouillon sans entrée échoue avec un message récupérable
 * (EX-EDIT-007).
 * }
 */
TEST(LevelDraftTest, ToLevelSansEntreeEchoueProprement) {
    LevelDraft draft = LevelDraft::empty("Incomplet", 4, 4);
    draft.paintTile(1, 1, TileType::Wall);

    const core::LevelLoadResult result = draft.toLevel();
    EXPECT_FALSE(result.ok());
    EXPECT_FALSE(result.error.empty());
}

/**
 * @brief Un brouillon reconstruit depuis un niveau existant restitue son contenu.
 * \castest{<b>Un brouillon reconstruit depuis un niveau existant restitue son contenu.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un brouillon reconstruit depuis un niveau existant restitue son contenu.
 * }
 */
TEST(LevelDraftTest, FromLevelRestitueLeContenu) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(R"({
        "name": "Depart", "width": 3, "height": 3,
        "tiles": [ {"x":0,"y":0,"type":"entry"}, {"x":2,"y":2,"type":"wall"} ] })");
    ASSERT_TRUE(loaded.ok()) << loaded.error;

    const LevelDraft draft = LevelDraft::fromLevel(*loaded.level);
    EXPECT_EQ(draft.name(), "Depart");
    EXPECT_EQ(*draft.entry(), (GridPosition{0, 0}));
    EXPECT_EQ(draft.tileMap().tile(2, 2), TileType::Wall);
}

/**
 * @brief Un brouillon neuf ne peut ni annuler ni refaire.
 * \castest{<b>Un brouillon neuf ne peut ni annuler ni refaire.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Un brouillon neuf ne peut ni annuler ni refaire.
 * }
 */
TEST(LevelDraftTest, BrouillonNeufSansHistorique) {
    const LevelDraft draft = LevelDraft::empty("N", 4, 4);
    EXPECT_FALSE(draft.canUndo());
    EXPECT_FALSE(draft.canRedo());
}

/**
 * @brief undo() après une peinture restitue l'état exact précédent.
 * \castest{<b>undo() après une peinture restitue l'état exact précédent.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu undo() après une peinture restitue l'état exact précédent.
 * }
 */
TEST(LevelDraftTest, UndoApresPeintureRestitueLEtatPrecedent) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    draft.paintTile(1, 1, TileType::Solid);
    ASSERT_TRUE(draft.canUndo());

    const bool undone = draft.undo();

    EXPECT_TRUE(undone);
    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Empty);
    EXPECT_FALSE(draft.canUndo());
    EXPECT_TRUE(draft.canRedo());
}

/**
 * @brief redo() après un undo() restitue l'état muté.
 * \castest{<b>redo() après un undo() restitue l'état muté.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu redo() après un undo() restitue l'état muté.
 * }
 */
TEST(LevelDraftTest, RedoApresUndoRestitueLEtatMute) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    draft.paintTile(1, 1, TileType::Solid);
    draft.undo();

    const bool redone = draft.redo();

    EXPECT_TRUE(redone);
    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Solid);
    EXPECT_TRUE(draft.canUndo());
    EXPECT_FALSE(draft.canRedo());
}

/**
 * @brief Une séquence de N mutations suivie de N undo() restitue l'état initial exact.
 * \castest{<b>Une séquence de N mutations suivie de N undo() restitue l'état initial
 * exact.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Une séquence de N mutations suivie de N undo() restitue l'état initial exact.
 * }
 */
TEST(LevelDraftTest, SequenceDeMutationsPuisUndoRestitueLEtatInitial) {
    LevelDraft draft = LevelDraft::empty("N", 5, 5);
    draft.paintTile(0, 0, TileType::Solid);
    draft.setEntry(1, 1);
    draft.paintTile(2, 2, TileType::Dirt);

    ASSERT_TRUE(draft.undo());
    ASSERT_TRUE(draft.undo());
    ASSERT_TRUE(draft.undo());

    EXPECT_FALSE(draft.canUndo());
    EXPECT_EQ(draft.tileMap().tile(0, 0), TileType::Empty);
    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Empty);
    EXPECT_EQ(draft.tileMap().tile(2, 2), TileType::Empty);
    EXPECT_FALSE(draft.entry().has_value());
}

/**
 * @brief Une nouvelle mutation après un undo() invalide la branche de refaire.
 * \castest{<b>Une nouvelle mutation après un undo() invalide la branche de refaire.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu Une nouvelle mutation après un undo() invalide la branche de refaire.
 * }
 */
TEST(LevelDraftTest, MutationApresUndoInvalideLeRefaire) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    draft.paintTile(0, 0, TileType::Solid);
    draft.undo();
    ASSERT_TRUE(draft.canRedo());

    draft.paintTile(1, 1, TileType::Dirt);

    EXPECT_FALSE(draft.canRedo());
    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Dirt);
}

/**
 * @brief undo()/redo() sur une pile vide est sans effet (pas de plantage).
 * \castest{<b>undo()/redo() sur une pile vide est sans effet (pas de plantage).</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu undo()/redo() sur une pile vide est sans effet (pas de plantage).
 * }
 */
TEST(LevelDraftTest, UndoRedoSurPileVideSansEffet) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    EXPECT_FALSE(draft.undo());
    EXPECT_FALSE(draft.redo());
    EXPECT_EQ(draft.tileMap().tile(0, 0), TileType::Empty);
}

/**
 * @brief paintRegion applique un bloc homogène comme une succession de paintTile équivalente.
 * \castest{<b>paintRegion applique un bloc homogène comme une succession de paintTile
 * équivalente.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu paintRegion applique un bloc homogène comme une succession de paintTile équivalente.
 * }
 */
TEST(LevelDraftTest, PaintRegionAppliqueLeBlocEntier) {
    LevelDraft draft = LevelDraft::empty("N", 5, 5);
    const std::vector<std::vector<TileType>> block = {
        {TileType::Solid, TileType::Solid},
        {TileType::Solid, TileType::Solid},
    };
    draft.paintRegion(1, 1, block);

    EXPECT_EQ(draft.tileMap().tile(1, 1), TileType::Solid);
    EXPECT_EQ(draft.tileMap().tile(2, 1), TileType::Solid);
    EXPECT_EQ(draft.tileMap().tile(1, 2), TileType::Solid);
    EXPECT_EQ(draft.tileMap().tile(2, 2), TileType::Solid);
    EXPECT_EQ(draft.tileMap().tile(0, 0), TileType::Empty);
}

/**
 * @brief paintRegion ne pousse qu'un seul snapshot undo pour tout le bloc.
 * \castest{<b>paintRegion ne pousse qu'un seul snapshot undo pour tout le bloc.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu paintRegion ne pousse qu'un seul snapshot undo pour tout le bloc.
 * }
 */
TEST(LevelDraftTest, PaintRegionUnSeulSnapshotUndo) {
    LevelDraft draft = LevelDraft::empty("N", 5, 5);
    const std::vector<std::vector<TileType>> block = {
        {TileType::Dirt, TileType::Dirt, TileType::Dirt},
    };
    draft.paintRegion(0, 0, block);

    ASSERT_TRUE(draft.undo());
    EXPECT_FALSE(draft.canUndo());
    EXPECT_EQ(draft.tileMap().tile(0, 0), TileType::Empty);
    EXPECT_EQ(draft.tileMap().tile(1, 0), TileType::Empty);
    EXPECT_EQ(draft.tileMap().tile(2, 0), TileType::Empty);
}

/**
 * @brief paintRegion découpe silencieusement le bloc aux bords de la grille.
 * \castest{<b>paintRegion découpe silencieusement le bloc aux bords de la grille.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu paintRegion découpe silencieusement le bloc aux bords de la grille.
 * }
 */
TEST(LevelDraftTest, PaintRegionDecoupeAuxBords) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    const std::vector<std::vector<TileType>> block = {
        {TileType::Solid, TileType::Solid, TileType::Solid},
        {TileType::Solid, TileType::Solid, TileType::Solid},
    };
    draft.paintRegion(1, 2, block);  // deborde largeur (colonne 3) et hauteur (ligne 3)

    EXPECT_EQ(draft.tileMap().tile(1, 2), TileType::Solid);
    EXPECT_EQ(draft.tileMap().tile(2, 2), TileType::Solid);
}

/**
 * @brief paintRegion qui inclut une position d'entrée déplace l'entrée existante (même sémantique
 *        que paintTile).
 * \castest{<b>paintRegion qui inclut une position d'entrée déplace l'entrée existante.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu paintRegion qui inclut une position d'entrée déplace l'entrée existante.
 * }
 */
TEST(LevelDraftTest, PaintRegionDeplaceLEntree) {
    LevelDraft draft = LevelDraft::empty("N", 4, 4);
    draft.setEntry(0, 0);
    const std::vector<std::vector<TileType>> block = {{TileType::Entry}};
    draft.paintRegion(2, 2, block);

    EXPECT_EQ(draft.tileMap().tile(0, 0), TileType::Empty);
    EXPECT_EQ(*draft.entry(), (GridPosition{2, 2}));
}

/**
 * @brief paintRegion avec un bloc vide est sans effet (pas de snapshot undo créé).
 * \castest{<b>paintRegion avec un bloc vide est sans effet.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu paintRegion avec un bloc vide est sans effet.
 * }
 */
TEST(LevelDraftTest, PaintRegionBlocVideSansEffet) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    draft.paintRegion(0, 0, {});
    EXPECT_FALSE(draft.canUndo());
}

/**
 * @brief wouldResizeDropContent détecte la perte de l'entrée.
 * \castest{<b>wouldResizeDropContent détecte la perte de l'entrée.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu wouldResizeDropContent détecte la perte de l'entrée.
 * }
 */
TEST(LevelDraftTest, WouldResizeDropContentDetecteLaPerte) {
    LevelDraft draft = LevelDraft::empty("N", 5, 5);
    draft.setEntry(4, 4);

    // L'entree (4,4) sortirait des bornes d'une grille 3x3.
    EXPECT_TRUE(draft.wouldResizeDropContent(3, 3));
    // Reduire uniquement la largeur suffit a la perdre.
    EXPECT_TRUE(draft.wouldResizeDropContent(2, 5));
    // Agrandir ne perd jamais rien.
    EXPECT_FALSE(draft.wouldResizeDropContent(10, 10));
    // Memes dimensions : rien ne bouge.
    EXPECT_FALSE(draft.wouldResizeDropContent(5, 5));
}

/**
 * @brief wouldResizeDropContent est faux sur un brouillon vierge, quelle que soit la taille visee.
 * \castest{<b>wouldResizeDropContent est faux sur un brouillon vierge, quelle que soit la taille
 * visee.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu wouldResizeDropContent est faux sur un brouillon vierge, quelle que soit la taille
 * visee.
 * }
 */
TEST(LevelDraftTest, WouldResizeDropContentFauxSurBrouillonVierge) {
    const LevelDraft draft = LevelDraft::empty("N", 5, 5);
    EXPECT_FALSE(draft.wouldResizeDropContent(1, 1));
}

/**
 * @brief L'annulation d'un redimensionnement restitue les dimensions et le contenu précédents.
 * \castest{<b>L'annulation d'un redimensionnement restitue les dimensions et le contenu
 * précédents.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * \tattendu L'annulation d'un redimensionnement restitue les dimensions et le contenu
 * précédents.
 * }
 */
TEST(LevelDraftTest, UndoApresRedimensionnementRestitueLesDimensions) {
    LevelDraft draft = LevelDraft::empty("N", 5, 5);
    draft.setEntry(4, 4);

    draft.resize(2, 2);
    ASSERT_FALSE(draft.entry().has_value());

    draft.undo();

    EXPECT_EQ(draft.tileMap().width(), 5);
    EXPECT_EQ(draft.tileMap().height(), 5);
    ASSERT_TRUE(draft.entry().has_value());
    EXPECT_EQ(*draft.entry(), (GridPosition{4, 4}));
}

/**
 * @brief La révision change à chaque mutation et revient à sa valeur quand `undo()` la défait :
 *        c'est elle qui dit à l'éditeur si la carte porte des modifications (`LOT-EDITOR-01`).
 * \castest{<b>La révision du brouillon suit l'historique d'annulation.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Relever la révision d'un brouillon neuf.<br/>2. Peindre, défaire, refaire.<br/>
 * \tattendu Peindre change la révision ; défaire rend la révision de départ ; refaire rend celle
 * d'après la peinture ; une nouvelle mutation après un défaire donne une révision jamais vue.
 * }
 */
TEST(LevelDraftTest, LaRevisionSuitLHistorique) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    const auto initial = draft.revision();
    draft.paintTile(1, 1, TileType::Solid);
    const auto painted = draft.revision();
    EXPECT_NE(painted, initial);

    ASSERT_TRUE(draft.undo());
    EXPECT_EQ(draft.revision(), initial);
    ASSERT_TRUE(draft.redo());
    EXPECT_EQ(draft.revision(), painted);

    ASSERT_TRUE(draft.undo());
    draft.paintTile(2, 2, TileType::Solid);
    EXPECT_NE(draft.revision(), initial);
    EXPECT_NE(draft.revision(), painted);
}

/**
 * @brief Repeindre une case du même type ne fait rien : ni pas d'historique, ni révision neuve.
 * \castest{<b>Repasser le pinceau sur une case déjà du bon type ne modifie pas la carte.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Peindre une case, relever la révision.<br/>2. Repeindre la même case du même type, et
 * un bloc qui ne change rien.<br/>
 * \tattendu Révision et profondeur d'historique inchangées.
 * }
 */
TEST(LevelDraftTest, RepeindreLeMemeTypeNeModifieRien) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    draft.paintTile(1, 1, TileType::Solid);
    const auto revision = draft.revision();
    const std::size_t depth = draft.undoDepth();

    draft.paintTile(1, 1, TileType::Solid);
    draft.paintRegion(1, 1, {{TileType::Solid}});
    draft.paintRegion(5, 5, {{TileType::Wall}});  // hors de la carte
    EXPECT_EQ(draft.revision(), revision);
    EXPECT_EQ(draft.undoDepth(), depth);
}

/**
 * @brief L'historique d'annulation est plafonné : au-delà, le pas le plus ancien est oublié et le
 *        plus récent reste défaisable.
 * \castest{<b>L'historique d'annulation est plafonné.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Enchaîner plus de mutations que le plafond.<br/>2. Défaire autant que possible.<br/>
 * \tattendu La profondeur s'arrête au plafond ; tout défaire rend l'état d'après les mutations
 * oubliées, pas le brouillon vierge.
 * }
 */
TEST(LevelDraftTest, LHistoriqueEstPlafonne) {
    constexpr int WIDTH = 20;
    const std::size_t extra = 10;
    const std::size_t total = LevelDraft::UNDO_HISTORY_LIMIT + extra;
    LevelDraft draft = LevelDraft::empty("N", WIDTH, static_cast<int>(total / WIDTH) + 1);
    for (std::size_t index = 0; index < total; ++index) {
        draft.paintTile(static_cast<int>(index % WIDTH), static_cast<int>(index / WIDTH),
                        TileType::Solid);
    }
    EXPECT_EQ(draft.undoDepth(), LevelDraft::UNDO_HISTORY_LIMIT);

    while (draft.undo()) {}
    // Les dix premières cases, peintes avant le plafond, ne se défont plus.
    for (std::size_t index = 0; index < extra; ++index) {
        EXPECT_EQ(
            draft.tileMap().tile(static_cast<int>(index % WIDTH), static_cast<int>(index / WIDTH)),
            TileType::Solid);
    }
    EXPECT_EQ(
        draft.tileMap().tile(static_cast<int>(extra % WIDTH), static_cast<int>(extra / WIDTH)),
        TileType::Empty);
}

/**
 * @brief `toJson` rend le brouillon même incomplet, et relu par le chargeur il redonne la carte.
 * \castest{<b>Le brouillon se sérialise sans validation, pour la sauvegarde automatique.</b><br/>
 * \tcat Unitaire · Level Draft<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Sérialiser un brouillon sans entrée.<br/>2. Poser une entrée, sérialiser,
 * recharger.<br/>
 * \tattendu Le premier JSON n'est pas vide (le chargeur le refuse) ; le second se recharge à
 * l'identique de ce que `toLevel` rend.
 * }
 */
TEST(LevelDraftTest, ToJsonRendUnBrouillonIncomplet) {
    LevelDraft draft = LevelDraft::empty("N", 3, 3);
    const std::string incomplete = draft.toJson();
    EXPECT_FALSE(incomplete.empty());
    EXPECT_FALSE(core::LevelLoader::loadFromString(incomplete).ok());

    draft.paintTile(1, 1, TileType::Entry);
    const core::LevelLoadResult reloaded = core::LevelLoader::loadFromString(draft.toJson());
    ASSERT_TRUE(reloaded.ok()) << reloaded.error;
    EXPECT_EQ(reloaded.level->entry(), (GridPosition{.column = 1, .row = 1}));
}
