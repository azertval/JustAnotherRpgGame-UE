// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_level_draft_editing.cpp
 * @brief Tests unitaires de l'édition des couches et des entités d'un brouillon (`LOT-11`) :
 *        création, peinture, déplacement, annulation, et aller-retour par le chargeur.
 */

#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <variant>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Levels/GridPosition.h"
#include "Core/Levels/LevelDraft.h"
#include "Core/Levels/LevelLoader.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileType.h"

namespace {

// Carte a grille unique (sans couche declaree) : entree, un mur, de l'herbe.
constexpr const char* MAP_FLAT = R"({
  "version": 3,
  "name": "Grille plate",
  "width": 4,
  "height": 3,
  "tiles": [
    { "x": 0, "y": 0, "type": "wall" },
    { "x": 1, "y": 0, "type": "grass" },
    { "x": 1, "y": 1, "type": "entry" }
  ]
})";

// Carte a couches : sol et decor declares, un PNJ.
constexpr const char* MAP_LAYERED = R"({
  "version": 3,
  "name": "Village",
  "width": 4,
  "height": 3,
  "tiles": [
    { "x": 1, "y": 1, "type": "entry" }
  ],
  "layers": [
    { "name": "sol", "kind": "ground", "tiles": [{ "x": 0, "y": 0, "type": "grass" }] },
    { "name": "decor", "kind": "decor", "tiles": [] }
  ],
  "entities": [{ "type": "npc", "x": 2, "y": 2, "dialogue": "heraut" }]
})";

[[nodiscard]] core::LevelDraft draftOf(const char* json) {
    const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(json);
    EXPECT_TRUE(loaded.ok()) << loaded.error;
    return core::LevelDraft::fromLevel(*loaded.level);
}

// Rang de la premiere couche de role @p kind, ou nullopt.
[[nodiscard]] std::optional<std::size_t> indexOfKind(const std::vector<core::TileLayer>& layers,
                                                     core::LayerKind kind) {
    for (std::size_t index = 0; index < layers.size(); ++index) {
        if (layers[index].kind == kind) {
            return index;
        }
    }
    return std::nullopt;
}

}  // namespace

/**
 * @brief La première couche visuelle d'une carte à grille unique en reprend l'image, sans les types
 * de collision, et la grille racine devient la collision.
 * \castest{<b>Ajouter la premiere couche promeut la grille unique.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Ouvrir une carte sans couche declaree.<br/>2. Ajouter une couche de sol.<br/>3.
 * Reconvertir en niveau.<br/>
 * \tattendu Le sol porte le mur et l'herbe mais pas l'entree ; la racine est de role
 * Collision, en tete, et la collision garde l'entree.
 * }
 */
TEST(EditionDeCarteTest, PremiereCoucheVisuellePromeutLaGrilleUnique) {
    core::LevelDraft draft = draftOf(MAP_FLAT);
    ASSERT_EQ(draft.layers().size(), 1U);
    EXPECT_EQ(draft.layers().front().kind, core::LayerKind::Legacy);

    const std::optional<std::size_t> ground = draft.addLayer(core::LayerKind::Ground, "sol");
    ASSERT_TRUE(ground.has_value());
    ASSERT_EQ(draft.layers().size(), 2U);
    EXPECT_EQ(draft.layers().front().kind, core::LayerKind::Collision);
    const core::TileMap& tiles = draft.layers()[*ground].tiles;
    EXPECT_EQ(tiles.tile(0, 0), core::TileType::Wall);
    EXPECT_EQ(tiles.tile(1, 0), core::TileType::Grass);
    EXPECT_EQ(tiles.tile(2, 0), core::TileType::Empty);
    EXPECT_EQ(tiles.tile(1, 1), core::TileType::Empty);

    const core::LevelLoadResult rebuilt = draft.toLevel();
    ASSERT_TRUE(rebuilt.ok()) << rebuilt.error;
    ASSERT_EQ(rebuilt.level->layers().size(), 2U);
    EXPECT_EQ(rebuilt.level->layers().front().kind, core::LayerKind::Collision);
    EXPECT_EQ(rebuilt.level->layers().front().tiles.tile(1, 1), core::TileType::Entry);
    EXPECT_EQ(rebuilt.level->layers()[1].tiles.tile(0, 0), core::TileType::Wall);
}

/**
 * @brief Un brouillon vierge reçoit l'entrée de collision que le chargeur lui donnerait, et une
 * seconde couche naît vide.
 * \castest{<b>Un brouillon vierge s'aligne sur le chargeur.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Creer un brouillon vierge et y poser un mur.<br/>2. Ajouter un sol puis un
 * decor.<br/>
 * \tattendu Trois couches : Collision en tete, le sol avec le mur, le decor vide.
 * }
 */
TEST(EditionDeCarteTest, BrouillonViergeRecoitLaCoucheDeCollision) {
    core::LevelDraft draft = core::LevelDraft::empty("vierge", 3, 2);
    draft.paintTile(0, 0, core::TileType::Wall);
    ASSERT_EQ(draft.addLayer(core::LayerKind::Ground, "sol"), std::optional<std::size_t>{1});
    ASSERT_EQ(draft.addLayer(core::LayerKind::Decor, "decor"), std::optional<std::size_t>{2});

    ASSERT_EQ(draft.layers().size(), 3U);
    EXPECT_EQ(draft.layers()[0].kind, core::LayerKind::Collision);
    EXPECT_EQ(draft.layers()[1].tiles.tile(0, 0), core::TileType::Wall);
    EXPECT_EQ(draft.layers()[2].tiles.tile(0, 0), core::TileType::Empty);
}

/**
 * @brief Seules les couches visuelles se créent : la collision est la grille racine.
 * \castest{<b>Une couche de collision ne se cree pas.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Demander une couche Collision, puis Legacy.<br/>
 * \tattendu Les deux sont refusees, rien n'est empile.
 * }
 */
TEST(EditionDeCarteTest, CoucheNonVisuelleRefusee) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    EXPECT_FALSE(draft.addLayer(core::LayerKind::Collision, "x").has_value());
    EXPECT_FALSE(draft.addLayer(core::LayerKind::Legacy, "x").has_value());
    EXPECT_FALSE(draft.canUndo());
}

/**
 * @brief Peindre une couche visuelle n'accepte que des types d'image, et ne touche ni la
 * collision ni les autres couches.
 * \castest{<b>Peindre le sol laisse la collision intacte.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Peindre de l'eau sur le sol.<br/>2. Tenter une entree sur le sol.<br/>3.
 * Reconvertir.<br/>
 * \tattendu L'eau est sur le sol, l'entree refusee, la collision et le decor vides en cette case.
 * }
 */
TEST(EditionDeCarteTest, PeindreUneCoucheVisuelleNeTouchePasLaCollision) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    const std::size_t ground = *indexOfKind(draft.layers(), core::LayerKind::Ground);
    const std::size_t decor = *indexOfKind(draft.layers(), core::LayerKind::Decor);

    EXPECT_TRUE(draft.paintLayerTile(ground, 2, 1, core::TileType::Water));
    EXPECT_FALSE(draft.paintLayerTile(ground, 2, 1, core::TileType::Entry));
    EXPECT_FALSE(draft.paintLayerTile(ground, 9, 9, core::TileType::Water));

    const core::LevelLoadResult rebuilt = draft.toLevel();
    ASSERT_TRUE(rebuilt.ok()) << rebuilt.error;
    EXPECT_EQ(rebuilt.level->tileMap().tile(2, 1), core::TileType::Empty);
    EXPECT_EQ(rebuilt.level->layers()[ground].tiles.tile(2, 1), core::TileType::Water);
    EXPECT_EQ(rebuilt.level->layers()[decor].tiles.tile(2, 1), core::TileType::Empty);
}

/**
 * @brief La collision ne se peint pas par les mutateurs de couche, et un geste sans effet
 * n'empile rien.
 * \castest{<b>Un geste de couche refuse n'empile rien.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Peindre l'entree de collision par paintLayerTile.<br/>2. Repeindre l'herbe deja
 * posee sur le sol.<br/>
 * \tattendu Les deux sont refuses et l'historique reste vide.
 * }
 */
TEST(EditionDeCarteTest, GesteDeCoucheSansEffetNEmpileRien) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    const std::size_t collision = *indexOfKind(draft.layers(), core::LayerKind::Collision);
    const std::size_t ground = *indexOfKind(draft.layers(), core::LayerKind::Ground);
    EXPECT_FALSE(draft.paintLayerTile(collision, 0, 0, core::TileType::Wall));
    EXPECT_FALSE(draft.paintLayerTile(ground, 0, 0, core::TileType::Grass));
    EXPECT_FALSE(draft.canUndo());
}

/**
 * @brief Un bloc peint sur une couche coûte un pas d'annulation, et un bloc contenant un type
 * refusé est refusé en entier.
 * \castest{<b>Un bloc de couche est un seul pas d'annulation.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Peindre un bloc 2x2 de sable qui deborde du bord droit.<br/>2. Annuler.<br/>3.
 * Peindre un bloc melant sable et entree.<br/>
 * \tattendu Le bloc est decoupe au bord, une annulation le retire entierement, le bloc mixte est
 * refuse.
 * }
 */
TEST(EditionDeCarteTest, BlocDeCoucheEnUnPasEtRefuseSiMixte) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    const std::size_t decor = *indexOfKind(draft.layers(), core::LayerKind::Decor);
    const std::vector<std::vector<core::TileType>> sand = {
        {core::TileType::Sand, core::TileType::Sand}, {core::TileType::Sand, core::TileType::Sand}};

    ASSERT_TRUE(draft.paintLayerRegion(decor, 3, 0, sand));
    EXPECT_EQ(draft.layers()[decor].tiles.tile(3, 0), core::TileType::Sand);
    EXPECT_EQ(draft.layers()[decor].tiles.tile(3, 1), core::TileType::Sand);
    ASSERT_TRUE(draft.undo());
    EXPECT_EQ(draft.layers()[decor].tiles.tile(3, 0), core::TileType::Empty);
    EXPECT_FALSE(draft.canUndo());

    const std::vector<std::vector<core::TileType>> mixed = {
        {core::TileType::Sand, core::TileType::Entry}};
    EXPECT_FALSE(draft.paintLayerRegion(decor, 0, 0, mixed));
    EXPECT_EQ(draft.layers()[decor].tiles.tile(0, 0), core::TileType::Empty);
}

/**
 * @brief Déplacer une couche échange son rang avec sa voisine visuelle, sans franchir la collision.
 * \castest{<b>Une couche se deplace entre couches visuelles.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Reculer le decor.<br/>2. Reculer encore le decor devenu premier visuel.<br/>3.
 * Avancer le dernier, puis la collision.<br/>
 * \tattendu Le decor passe derriere le sol, puis reste en place devant la collision ; le dernier
 * reste dernier ; la collision est refusee.
 * }
 */
TEST(EditionDeCarteTest, DeplacerUneCoucheNeFranchitPasLaCollision) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    ASSERT_EQ(draft.layers()[1].kind, core::LayerKind::Ground);
    ASSERT_EQ(draft.layers()[2].kind, core::LayerKind::Decor);

    EXPECT_EQ(draft.moveLayer(2, /*forward=*/false), std::optional<std::size_t>{1});
    EXPECT_EQ(draft.layers()[1].kind, core::LayerKind::Decor);
    EXPECT_EQ(draft.moveLayer(1, /*forward=*/false), std::optional<std::size_t>{1});
    EXPECT_EQ(draft.moveLayer(2, /*forward=*/true), std::optional<std::size_t>{2});
    EXPECT_FALSE(draft.moveLayer(0, /*forward=*/true).has_value());
}

/**
 * @brief Retirer la dernière couche visuelle rend la grille racine au rôle `Legacy`, comme la
 * relecture le ferait.
 * \castest{<b>Retirer toutes les couches visuelles rend la grille unique.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Retirer le decor puis le sol.<br/>2. Reconvertir.<br/>
 * \tattendu Une seule couche, Legacy, dans le brouillon comme dans le niveau relu.
 * }
 */
TEST(EditionDeCarteTest, RetirerLesCouchesVisuellesRendLaGrilleUnique) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    EXPECT_TRUE(draft.removeLayer(2));
    EXPECT_TRUE(draft.removeLayer(1));
    EXPECT_FALSE(draft.removeLayer(0));
    ASSERT_EQ(draft.layers().size(), 1U);
    EXPECT_EQ(draft.layers().front().kind, core::LayerKind::Legacy);

    const core::LevelLoadResult rebuilt = draft.toLevel();
    ASSERT_TRUE(rebuilt.ok()) << rebuilt.error;
    ASSERT_EQ(rebuilt.level->layers().size(), 1U);
    EXPECT_EQ(rebuilt.level->layers().front().kind, core::LayerKind::Legacy);
}

/**
 * @brief Renommer et changer le rôle d'une couche sont annulables et traversent l'enregistrement.
 * \castest{<b>Nom et role d'une couche s'editent.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Renommer le sol, puis en faire un decor.<br/>2. Reconvertir.<br/>3. Annuler deux
 * fois.<br/>
 * \tattendu Le niveau relu porte le nouveau nom et le role decor ; les annulations rendent l'etat
 * d'origine.
 * }
 */
TEST(EditionDeCarteTest, NomEtRoleDUneCoucheSEditent) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    EXPECT_TRUE(draft.renameLayer(1, "prairie"));
    EXPECT_FALSE(draft.renameLayer(1, "prairie"));
    EXPECT_TRUE(draft.setLayerKind(1, core::LayerKind::Decor));
    EXPECT_FALSE(draft.setLayerKind(1, core::LayerKind::Collision));

    const core::LevelLoadResult rebuilt = draft.toLevel();
    ASSERT_TRUE(rebuilt.ok()) << rebuilt.error;
    EXPECT_EQ(rebuilt.level->layers()[1].name, "prairie");
    EXPECT_EQ(rebuilt.level->layers()[1].kind, core::LayerKind::Decor);

    ASSERT_TRUE(draft.undo());
    ASSERT_TRUE(draft.undo());
    EXPECT_EQ(draft.layers()[1].name, "sol");
    EXPECT_EQ(draft.layers()[1].kind, core::LayerKind::Ground);
}

/**
 * @brief Une couche prend une propriété — le lieu dont elle tire ses pièces (`LOT-EDITOR-06`) —
 * en un pas d'annulation, et la garde à l'enregistrement.
 * \castest{<b>Une propriete de couche s'edite et se defait.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Donner `scene = martpart` a la couche de sol, puis la meme valeur encore.<br/>2.
 * Tenter une cle vide et la grille de collision.<br/>3. Reconvertir, puis annuler.<br/>
 * \tattendu Un seul pas ; le niveau relu porte le lieu ; l'annulation le retire.
 * }
 */
TEST(EditionDeCarteTest, UneProprieteDeCoucheSEditeEtSeDefait) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    EXPECT_TRUE(draft.setLayerProperty(1, "scene", std::string{"martpart"}));
    EXPECT_FALSE(draft.setLayerProperty(1, "scene", std::string{"martpart"}));
    EXPECT_FALSE(draft.setLayerProperty(1, "", std::string{"martpart"}));
    EXPECT_FALSE(draft.setLayerProperty(0, "scene", std::string{"martpart"}));

    const core::LevelLoadResult rebuilt = draft.toLevel();
    ASSERT_TRUE(rebuilt.ok()) << rebuilt.error;
    const core::PropertyMap& proprietes = rebuilt.level->layers()[1].properties;
    ASSERT_TRUE(proprietes.contains("scene"));
    EXPECT_EQ(std::get<std::string>(proprietes.at("scene")), "martpart");

    ASSERT_TRUE(draft.undo());
    EXPECT_FALSE(draft.layers()[1].properties.contains("scene"));
}

/**
 * @brief Poser, déplacer, renseigner et retirer une entité : chaque geste est un pas
 * d'annulation, et l'entité traverse l'enregistrement.
 * \castest{<b>Une entite se pose, se deplace et se renseigne.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Poser un coffre en (0, 2).<br/>2. Le deplacer en (1, 2).<br/>3. Lui donner une
 * propriete.<br/>4. Reconvertir, puis annuler trois fois.<br/>
 * \tattendu Le niveau relu porte le coffre en (1, 2) avec sa propriete ; trois annulations le
 * retirent.
 * }
 */
TEST(EditionDeCarteTest, EntiteSePoseSeDeplaceEtSeRenseigne) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    const std::optional<std::size_t> chest = draft.placeEntity(
        core::MapEntity{.type = "chest", .position = {.column = 0, .row = 2}, .properties = {}});
    ASSERT_EQ(chest, std::optional<std::size_t>{1});
    EXPECT_TRUE(draft.moveEntity(*chest, {.column = 1, .row = 2}));
    EXPECT_TRUE(draft.setEntityProperty(*chest, "loot", std::string{"potion"}));

    const core::LevelLoadResult rebuilt = draft.toLevel();
    ASSERT_TRUE(rebuilt.ok()) << rebuilt.error;
    ASSERT_EQ(rebuilt.level->entities().size(), 2U);
    const core::MapEntity& relu = rebuilt.level->entities()[1];
    EXPECT_EQ(relu.type, "chest");
    EXPECT_EQ(relu.position, (core::GridPosition{.column = 1, .row = 2}));
    EXPECT_EQ(relu.properties.at("loot"), core::PropertyValue{std::string{"potion"}});

    ASSERT_TRUE(draft.undo());
    ASSERT_TRUE(draft.undo());
    ASSERT_TRUE(draft.undo());
    EXPECT_EQ(draft.entities().size(), 1U);
}

/**
 * @brief Les gestes d'entité refusés ou sans effet n'empilent rien.
 * \castest{<b>Un geste d'entite refuse n'empile rien.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Poser hors de la grille.<br/>2. Deplacer sur place, hors grille, un rang
 * inconnu.<br/>3. Reassigner la meme propriete, retirer une propriete absente.<br/>
 * \tattendu Tout est refuse, l'historique reste vide.
 * }
 */
TEST(EditionDeCarteTest, GesteDEntiteSansEffetNEmpileRien) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    EXPECT_FALSE(draft
                     .placeEntity(core::MapEntity{
                         .type = "chest", .position = {.column = 4, .row = 0}, .properties = {}})
                     .has_value());
    EXPECT_FALSE(draft.moveEntity(0, {.column = 2, .row = 2}));
    EXPECT_FALSE(draft.moveEntity(0, {.column = -1, .row = 2}));
    EXPECT_FALSE(draft.moveEntity(7, {.column = 0, .row = 0}));
    EXPECT_FALSE(draft.setEntityProperty(0, "dialogue", std::string{"heraut"}));
    EXPECT_FALSE(draft.removeEntityProperty(0, "absente"));
    EXPECT_FALSE(draft.removeEntity(3));
    EXPECT_FALSE(draft.canUndo());
}

/**
 * @brief `entityAt` rend la dernière entité posée sur une case partagée, et retirer une propriété
 * est annulable.
 * \castest{<b>La case partagee designe l'entite du dessus.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Poser un panneau sur la case du PNJ.<br/>2. Designer la case.<br/>3. Retirer le
 * dialogue du PNJ puis annuler.<br/>
 * \tattendu Le panneau est designe ; le dialogue revient apres annulation.
 * }
 */
TEST(EditionDeCarteTest, CasePartageeDesigneLEntiteDuDessus) {
    core::LevelDraft draft = draftOf(MAP_LAYERED);
    const std::optional<std::size_t> sign = draft.placeEntity(
        core::MapEntity{.type = "sign", .position = {.column = 2, .row = 2}, .properties = {}});
    ASSERT_TRUE(sign.has_value());
    EXPECT_EQ(draft.entityAt({.column = 2, .row = 2}), sign);
    EXPECT_FALSE(draft.entityAt({.column = 0, .row = 0}).has_value());

    EXPECT_TRUE(draft.removeEntityProperty(0, "dialogue"));
    EXPECT_FALSE(draft.entities()[0].properties.contains("dialogue"));
    ASSERT_TRUE(draft.undo());
    EXPECT_TRUE(draft.entities()[0].properties.contains("dialogue"));
}

/**
 * @brief Un geste qui enchaîne plusieurs mutations se défait en un pas (`LOT-EDITOR-04`).
 * \castest{<b>Un geste = un pas d'annulation.</b><br/>
 * \tcat Unitaire · Edition de carte<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Ouvrir un geste, peindre trois cases l'une après l'autre, le fermer.<br/>2. Ouvrir
 * un geste sans rien changer.<br/>3. Annuler, refaire.<br/>
 * \tattendu Un seul pas empilé, aucun pour le geste vide ; annuler rend les trois cases, refaire
 * les repeint ; la révision a changé à chaque mutation.
 * }
 */
TEST(EditionDeCarteTest, UnGesteSeDefaitEnUnPas) {
    core::LevelDraft draft = draftOf(MAP_FLAT);
    const std::uint64_t avant = draft.revision();
    {
        const core::GestureScope geste(draft);
        EXPECT_TRUE(draft.inGesture());
        draft.paintTile(2, 0, core::TileType::Wall);
        const std::uint64_t apresUne = draft.revision();
        draft.paintTile(3, 0, core::TileType::Wall);
        EXPECT_NE(draft.revision(), apresUne);
        draft.paintTile(3, 1, core::TileType::Wall);
    }
    EXPECT_FALSE(draft.inGesture());
    EXPECT_EQ(draft.undoDepth(), 1U);
    {
        const core::GestureScope vide(draft);
        draft.paintTile(3, 1, core::TileType::Wall);  // déjà un mur : rien ne change.
    }
    EXPECT_EQ(draft.undoDepth(), 1U);

    const std::uint64_t apres = draft.revision();
    ASSERT_TRUE(draft.undo());
    EXPECT_EQ(draft.revision(), avant);
    EXPECT_EQ(draft.tileMap().tile(2, 0), core::TileType::Empty);
    EXPECT_EQ(draft.tileMap().tile(3, 1), core::TileType::Empty);
    ASSERT_TRUE(draft.redo());
    EXPECT_EQ(draft.revision(), apres);
    EXPECT_EQ(draft.tileMap().tile(3, 1), core::TileType::Wall);
}
