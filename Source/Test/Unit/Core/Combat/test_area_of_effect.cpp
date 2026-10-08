// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_area_of_effect.cpp
 * @brief Tests des zones d'effet (`LOT-22`) : gabarits figés par des cas de référence dessinés,
 * origine incluse ou non selon la forme, lignes d'effet coupées par les murs.
 *
 * Chaque gabarit se compare à un **dessin** : `X` pour une case de la zone. Un dessin se relit
 * contre la règle — « au moins la moitié de la case » — en un coup d'œil, là où une liste de
 * coordonnées ne se relit pas.
 */

#include <algorithm>
#include <cstddef>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/AreaOfEffect.h"
#include "Core/Combat/BattleGrid.h"
#include "Core/Combat/CombatState.h"
#include "Core/Levels/TileMap.h"
#include "Core/Math/DeterministicRandom.h"

namespace {

using core::AreaOfEffect;
using core::AreaShape;
using core::GridPoint;
using core::GridPosition;

/// Le dessin des cases : `X` dans la zone, `#` mur, `.` sinon.
[[nodiscard]] std::vector<std::string> dessin(const std::vector<GridPosition>& cases, int largeur,
                                              int hauteur,
                                              const core::BattleGrid* grille = nullptr) {
    std::vector<std::string> lignes(static_cast<std::size_t>(hauteur),
                                    std::string(static_cast<std::size_t>(largeur), '.'));
    if (grille != nullptr) {
        for (int ligne = 0; ligne < hauteur; ++ligne) {
            for (int colonne = 0; colonne < largeur; ++colonne) {
                if (grille->blocksSight({colonne, ligne})) {
                    lignes[static_cast<std::size_t>(ligne)][static_cast<std::size_t>(colonne)] =
                        '#';
                }
            }
        }
    }
    for (const GridPosition cellule : cases) {
        lignes[static_cast<std::size_t>(cellule.row)][static_cast<std::size_t>(cellule.column)] =
            'X';
    }
    return lignes;
}

[[nodiscard]] std::string enClair(const std::vector<std::string>& lignes) {
    std::string texte = "\n";
    for (const std::string& ligne : lignes) {
        texte += ligne + '\n';
    }
    return texte;
}

}  // namespace

/**
 * @brief Les gabarits couvrent exactement les cases de référence.
 * \castest{<b>Sphère, cylindre, cône, ligne et cube couvrent chacun les cases de leur dessin de
 * référence : une case est dans la zone si la forme en couvre au moins la moitié.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Sphère de rayon 2 sur une intersection ; cylindre identique.<br/>2. Cône de 3 vers
 * l'est depuis le milieu du bord d'une case.<br/>3. Ligne
 * de 4 sur 1 vers l'est depuis le milieu d'un bord ; la même en diagonale depuis un coin.<br/>4.
 * Cube d'arête 2 vers le nord depuis une intersection.<br/>
 * \tattendu Chaque gabarit est identique à son dessin, case pour case.
 * }
 */
TEST(AreaOfEffectTest, LesGabaritsCouvrentLesCasesDeReference) {
    const auto gabarit = [](const AreaOfEffect& zone, int cote) {
        return dessin(core::areaTemplate(zone, cote, cote), cote, cote);
    };

    // Sphere de rayon 2 (3 m) sur l'intersection (4, 4) : les quatre cases d'angle n'en ont
    // qu'un quart.
    AreaOfEffect sphere{
        .shape = AreaShape::Sphere, .origin = {.x = 8, .y = 8}, .toward = {}, .size = 2};
    const std::vector<std::string> boule{"........", "........", "...XX...", "..XXXX..",
                                         "..XXXX..", "...XX...", "........", "........"};
    EXPECT_EQ(gabarit(sphere, 8), boule) << enClair(gabarit(sphere, 8));
    AreaOfEffect cylindre = sphere;
    cylindre.shape = AreaShape::Cylinder;
    EXPECT_EQ(gabarit(cylindre, 8), boule);

    // Cone de 3 vers l'est depuis le milieu du bord droit de la case (1, 3) : 1, 1, 3 cases. La
    // premiere case en a exactement la moitie, et la moitie suffit.
    const AreaOfEffect cone{.shape = AreaShape::Cone,
                            .origin = {.x = 4, .y = 7},
                            .toward = {.x = 6, .y = 7},
                            .size = 3};
    const std::vector<std::string> souffle{".......", ".......", "....X..", "..XXX..",
                                           "....X..", ".......", "......."};
    EXPECT_EQ(gabarit(cone, 7), souffle) << enClair(gabarit(cone, 7));

    // Ligne de 4 sur 1 vers l'est depuis le milieu du bord gauche de la case (0, 1).
    const AreaOfEffect ligne{.shape = AreaShape::Line,
                             .origin = {.x = 0, .y = 3},
                             .toward = {.x = 2, .y = 3},
                             .size = 4,
                             .width = 1};
    EXPECT_EQ(gabarit(ligne, 5),
              (std::vector<std::string>{".....", "XXXX.", ".....", ".....", "....."}))
        << enClair(gabarit(ligne, 5));

    // La meme en diagonale depuis le coin (0, 0) : quatre cases de long font 2,83 diagonales, et la
    // troisieme case est couverte a plus de la moitie.
    AreaOfEffect diagonale = ligne;
    diagonale.origin = {.x = 0, .y = 0};
    diagonale.toward = {.x = 2, .y = 2};
    EXPECT_EQ(gabarit(diagonale, 5),
              (std::vector<std::string>{"X....", ".X...", "..X..", ".....", "....."}))
        << enClair(gabarit(diagonale, 5));

    // Cube d'arete 2 vers le nord depuis l'intersection (2, 4) : l'origine est au milieu de la
    // face.
    const AreaOfEffect cube{.shape = AreaShape::Cube,
                            .origin = {.x = 4, .y = 8},
                            .toward = {.x = 4, .y = 0},
                            .size = 2};
    EXPECT_EQ(gabarit(cube, 5),
              (std::vector<std::string>{".....", ".....", ".XX..", ".XX..", "....."}))
        << enClair(gabarit(cube, 5));
}

/**
 * @brief L'origine est incluse dans une sphère, pas dans un cône ; une zone sans direction est
 * vide.
 * \castest{<b>Une sphère posée au centre d'une case la contient ; un cône qui part du même centre
 * n'en couvre qu'un huitième et ne la contient pas ; un cône sans direction ne couvre
 * rien.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Sphère de rayon 1 au centre de la case (2, 2).<br/>2. Cône de 2 vers l'est depuis le
 * même centre.<br/>3. Un cône dont la direction est son origine.<br/>4. Convertir 6 m, 4,50 m, 7,50
 * m et 1 m en cases.<br/>
 * \tattendu (2, 2) dans la sphère ; (2, 2) hors du cône ; aucune case ; 4, 3, 5, et rien pour 1 m.
 * }
 */
TEST(AreaOfEffectTest, LOrigineEtLesTailles) {
    const auto contient = [](const std::vector<GridPosition>& cases, GridPosition cellule) {
        return std::ranges::find(cases, cellule) != cases.end();
    };
    const GridPoint centre = core::centerOf({2, 2});
    const AreaOfEffect sphere{
        .shape = AreaShape::Sphere, .origin = centre, .toward = {}, .size = 1};
    EXPECT_TRUE(contient(core::areaTemplate(sphere, 5, 5), GridPosition{2, 2}));

    const AreaOfEffect cone{.shape = AreaShape::Cone,
                            .origin = centre,
                            .toward = {.x = centre.x + 2, .y = centre.y},
                            .size = 2};
    const std::vector<GridPosition> souffle = core::areaTemplate(cone, 5, 5);
    EXPECT_FALSE(contient(souffle, GridPosition{2, 2}));
    EXPECT_TRUE(contient(souffle, GridPosition{3, 2}));

    AreaOfEffect sansDirection = cone;
    sansDirection.toward = centre;
    EXPECT_TRUE(core::areaTemplate(sansDirection, 5, 5).empty());

    EXPECT_EQ(core::areaTilesFromMeters(6.0F), 4);
    EXPECT_EQ(core::areaTilesFromMeters(4.5F), 3);
    EXPECT_EQ(core::areaTilesFromMeters(7.5F), 5);
    EXPECT_FALSE(core::areaTilesFromMeters(1.0F).has_value());
}

/**
 * @brief Un mur arrête l'effet ; les combattants d'une zone se comptent une fois.
 * \castest{<b>Une sphère posée derrière un mur n'atteint pas les cases qu'aucune ligne droite ne
 * relie à son origine, ni le mur lui-même ; une créature de grande taille à moitié dans la zone y
 * est, une fois.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Une grille 7 × 7 barrée d'un mur vertical sur cinq cases, en colonne 4.<br/>2. Une
 * sphère de rayon 3 au centre de la case (3, 3), dont le gabarit déborde derrière le mur.<br/>3.
 * Un gobelin derrière le mur, un ogre de taille G à cheval sur le bord de la zone, un allié dans
 * la zone.<br/>
 * \tattendu Le gabarit couvre les colonnes 1 à 5 ; la colonne 5, derrière le mur, et le mur
 * lui-même en sortent ; l'allié et l'ogre sont touchés, une fois chacun ; le gobelin non.
 * }
 */
TEST(AreaOfEffectTest, UnMurArreteLEffet) {
    core::TileMap collision(7, 7);
    for (int ligne = 1; ligne <= 5; ++ligne) {
        collision.setTile(4, ligne, core::TileType::Wall);
    }
    const core::BattleGrid grille(collision);
    const AreaOfEffect boule{
        .shape = AreaShape::Sphere, .origin = core::centerOf({3, 3}), .toward = {}, .size = 3};
    const std::vector<GridPosition> gabarit = core::areaTemplate(boule, 7, 7);
    const std::vector<GridPosition> atteintes = core::affectedCells(grille, boule);
    // Le gabarit seul couvre les colonnes 1 a 5 ; la colonne 5, entierement derriere le mur, et le
    // mur lui-meme sortent de la zone.
    EXPECT_EQ(dessin(gabarit, 7, 7),
              (std::vector<std::string>{".......", ".XXXXX.", ".XXXXX.", ".XXXXX.", ".XXXXX.",
                                        ".XXXXX.", "......."}));
    EXPECT_EQ(dessin(atteintes, 7, 7, &grille),
              (std::vector<std::string>{".......", ".XXX#..", ".XXX#..", ".XXX#..", ".XXX#..",
                                        ".XXX#..", "......."}))
        << "gabarit :" << enClair(dessin(gabarit, 7, 7))
        << "atteintes :" << enClair(dessin(atteintes, 7, 7, &grille));

    core::CombatState combat{core::BattleGrid(collision)};
    core::CombatantProfile profil{.name = "Allie",
                                  .side = core::CombatSide::Allies,
                                  .maximumHitPoints = 10,
                                  .currentHitPoints = 10,
                                  .dexterity = 10,
                                  .initiativeModifier = 0,
                                  .movement = 6};
    combat.enlist(profil, GridPosition{2, 3});
    profil.name = "Gobelin";
    profil.side = core::CombatSide::Enemies;
    combat.enlist(profil, GridPosition{5, 3});
    profil.name = "Ogre";
    profil.size = core::CreatureSize::Large;
    combat.enlist(profil, GridPosition{0, 5});
    EXPECT_EQ(core::combatantsInArea(combat, boule),
              (std::vector<core::CombatantId>{core::CombatantId{1}, core::CombatantId{3}}));
}
