// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_combat_space.cpp
 * @brief Les règles spatiales en mètres, sans carte (`LOT-1017`, D-50) : volumes, allonge,
 *        tenaille par angle, hauteur, zones.
 *
 * Les valeurs attendues sont calculées à la main dans les commentaires : deux créatures M ont un
 * rayon de 0,75 m, et l'allonge est 1,50 m.
 */

#include <array>
#include <cmath>
#include <numbers>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/CombatSpace.h"
#include "Core/Rpg/RpgEnums.h"

namespace {

using core::AreaShape;
using core::CreatureSize;
using core::Effect;
using core::Meters3;
using core::Volume;

Volume medium(float x, float y, float z = 0.0f) {
    return core::volumeOf({x, y, z}, CreatureSize::Medium);
}

/**
 * \castest{<b>Une creature est un cylindre a la taille du Manuel.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Lire le rayon et la hauteur des tailles M, G, TG, Gig.<br/>
 * \tattendu M : 0,75 m et 1,50 m ; G : 1,50 m ; Gig : 3 m ; TG : 4,50 m de haut.}
 */
TEST(EspaceDeCombatTest, UneCreatureEstUnCylindreALaTailleDuManuel) {
    // Une créature M tient dans une case de 1,50 m : rayon 0,75 m, hauteur 1,50 m. Une G, 2 × 2.
    EXPECT_FLOAT_EQ(core::creatureRadius(CreatureSize::Medium), 0.75f);
    EXPECT_FLOAT_EQ(core::creatureHeight(CreatureSize::Medium), 1.5f);
    EXPECT_FLOAT_EQ(core::creatureRadius(CreatureSize::Large), 1.5f);
    EXPECT_FLOAT_EQ(core::creatureRadius(CreatureSize::Gargantuan), 3.0f);
    EXPECT_FLOAT_EQ(core::creatureHeight(CreatureSize::Huge), 4.5f);
}

/**
 * \castest{<b>L'allonge se mesure entre les bords des volumes.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Deux creatures M a 2,9 m puis 3,1 m de centre a centre ; une allonge de 3 m a 4,5
 * m.<br/>
 * \tattendu A portee a 2,9 m, hors d'allonge a 3,1 m ; la hallebarde atteint a 4,5 m ; au contact
 * la distance des bords est nulle.}
 */
TEST(EspaceDeCombatTest, LAllongeSeMesureEntreLesBords) {
    // Centres à 2,9 m : bords à 1,4 m, à portée ; à 3,1 m, bords à 1,6 m, hors d'allonge.
    EXPECT_TRUE(core::inReach(medium(0, 0), medium(2.9f, 0)));
    EXPECT_FALSE(core::inReach(medium(0, 0), medium(3.1f, 0)));
    // Une allonge de 3 m (une hallebarde) atteint à 4,5 m de centre à centre.
    EXPECT_TRUE(core::inReach(medium(0, 0), medium(4.5f, 0), 3.0f));
    // Au contact, la distance des bords est nulle.
    EXPECT_FLOAT_EQ(core::edgeDistance(medium(0, 0), medium(1.0f, 0)), 0.0f);
}

/**
 * \castest{<b>L'allonge compte la hauteur.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Une cible 2,9 m puis 3,1 m plus haut, au meme point du sol.<br/>
 * \tattendu A portee a 2,9 m, hors d'allonge a 3,1 m.}
 */
TEST(EspaceDeCombatTest, LAllongeCompteLaHauteur) {
    // Une cible 3 m plus haut, au même point du sol : 1,5 m de vide au-dessus de la tête de
    // l'attaquant (1,5 m de haut) — hors d'allonge de justesse.
    EXPECT_FALSE(core::inReach(medium(0, 0), medium(0, 0, 3.1f)));
    EXPECT_TRUE(core::inReach(medium(0, 0), medium(0, 0, 2.9f)));
}

/**
 * \castest{<b>Deux volumes se recouvrent ou non.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Deux creatures M a 1 m, a 1,5 m, et l'une au-dessus de l'autre.<br/>
 * \tattendu Recouvrement a 1 m seulement.}
 */
TEST(EspaceDeCombatTest, DeuxVolumesSeRecouvrentOuNon) {
    EXPECT_TRUE(core::overlap(medium(0, 0), medium(1.0f, 0)));
    EXPECT_FALSE(core::overlap(medium(0, 0), medium(1.5f, 0)));
    // L'un au-dessus de l'autre, sans se toucher.
    EXPECT_FALSE(core::overlap(medium(0, 0), medium(0, 0, 1.5f)));
}

/**
 * \castest{<b>La tenaille par angle rejoue la ligne des centres du Guide.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Les huit cases adjacentes a une cible, deux a deux.<br/>
 * \tattendu Tenaille pour N-S, N-SE, N-SO, NE-S, NE-SO (135 degres ou plus) ; pas pour N-E, N-NE,
 * NE-SE ; un attaquant confondu avec la cible ne forme aucun angle.}
 */
TEST(EspaceDeCombatTest, LaTenailleParAngleRejoueLaLigneDesCentresDuGuide) {
    // Les huit cases adjacentes à une cible en (0, 0), centres à 1,5 m. Sur la grille du Guide,
    // deux attaquants prennent en tenaille si la ligne de leurs centres traverse deux côtés
    // opposés de la case cible : N–S, N–SE, N–SO, NE–S, NE–SO, E–O, … ; pas N–E, ni N–NE, ni
    // NE–SE (la ligne longe le côté sans le traverser).
    const Meters3 target{0, 0, 0};
    const Meters3 n{0, -1.5f, 0};
    const Meters3 s{0, 1.5f, 0};
    const Meters3 e{1.5f, 0, 0};
    const Meters3 ne{1.5f, -1.5f, 0};
    const Meters3 se{1.5f, 1.5f, 0};
    const Meters3 sw{-1.5f, 1.5f, 0};
    EXPECT_TRUE(core::flanksByAngle(n, s, target));     // 180°
    EXPECT_TRUE(core::flanksByAngle(n, se, target));    // 135°
    EXPECT_TRUE(core::flanksByAngle(n, sw, target));    // 135°
    EXPECT_TRUE(core::flanksByAngle(ne, s, target));    // 135°
    EXPECT_TRUE(core::flanksByAngle(ne, sw, target));   // 180°
    EXPECT_FALSE(core::flanksByAngle(n, e, target));    // 90°
    EXPECT_FALSE(core::flanksByAngle(n, ne, target));   // 45°
    EXPECT_FALSE(core::flanksByAngle(ne, se, target));  // 90°
    // Un attaquant confondu avec la cible ne forme aucun angle.
    EXPECT_FALSE(core::flanksByAngle(target, s, target));
}

/**
 * \castest{<b>L'avantage de hauteur demande une case d'ecart.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un attaquant 1,5 m, 1,2 m plus haut, puis plus bas que sa cible.<br/>
 * \tattendu Avantage a 1,5 m seulement.}
 */
TEST(EspaceDeCombatTest, LAvantageDeHauteurDemandeUneCase) {
    EXPECT_TRUE(core::hasHighGround(medium(0, 0, 1.5f), medium(2, 0, 0)));
    EXPECT_FALSE(core::hasHighGround(medium(0, 0, 1.2f), medium(2, 0, 0)));
    EXPECT_FALSE(core::hasHighGround(medium(0, 0, 0), medium(2, 0, 1.5f)));
}

/**
 * \castest{<b>Une sphere touche ce qu'elle croise.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Une boule de feu de 6 m ; des creatures M a 6,5 m, 7 m, et en hauteur a 5 m et 6,5
 * m.<br/>
 * \tattendu Touchees a 6,5 m et a 5 m de haut ; epargnees a 7 m et a 6,5 m de haut.}
 */
TEST(EspaceDeCombatTest, UneSphereToucheCeQuElleCroise) {
    // Boule de feu : rayon 6 m en (0, 0). Une créature M centrée à 6,5 m a son bord à 5,75 m :
    // touchée. À 7 m, bord à 6,25 m : épargnée.
    const Effect fireball{.shape = AreaShape::Sphere, .origin = {0, 0, 0}, .size = 6.0f};
    EXPECT_TRUE(core::shapeHits(fireball, medium(6.5f, 0)));
    EXPECT_FALSE(core::shapeHits(fireball, medium(7.0f, 0)));
    // En hauteur : une créature sur une terrasse à 5 m, au même point du sol, a sa base à 5 m
    // du centre — touchée ; à 6,5 m, non.
    EXPECT_TRUE(core::shapeHits(fireball, medium(0, 0, 5.0f)));
    EXPECT_FALSE(core::shapeHits(fireball, medium(0, 0, 6.5f)));
}

/**
 * \castest{<b>Un cone s'elargit avec sa longueur.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un souffle de 4,5 m ; des creatures dans l'axe, sur le cote a 2,9 m et 2 m, derriere
 * l'origine, au-dela du bout ; un cone sans direction.<br/>
 * \tattendu Dans l'axe et a 2 m de cote : touchees ; les autres non ; sans direction, rien.}
 */
TEST(EspaceDeCombatTest, UnConeSElargitAvecSaLongueur) {
    // Souffle de 4,5 m vers +x depuis (0, 0) : au bout, 4,5 m de large (2,25 m de chaque côté).
    const Effect breath{
        .shape = AreaShape::Cone, .origin = {0, 0, 0}, .toward = {1, 0, 0}, .size = 4.5f};
    EXPECT_TRUE(core::shapeHits(breath, medium(3.0f, 0)));
    // À 3 m de l'origine, le cône fait 1,5 m de demi-largeur ; une créature à 2,9 m de côté
    // (bord à 2,15 m) est dehors, à 2,0 m de côté (bord à 1,25 m) dedans.
    EXPECT_FALSE(core::shapeHits(breath, medium(3.0f, 2.9f)));
    EXPECT_TRUE(core::shapeHits(breath, medium(3.0f, 2.0f)));
    // Derrière l'origine, rien ; au-delà de la longueur, rien.
    EXPECT_FALSE(core::shapeHits(breath, medium(-1.5f, 0)));
    EXPECT_FALSE(core::shapeHits(breath, medium(6.0f, 0)));
    // Sans direction, la zone est vide.
    const Effect none{
        .shape = AreaShape::Cone, .origin = {0, 0, 0}, .toward = {0, 0, 0}, .size = 4.5f};
    EXPECT_FALSE(core::shapeHits(none, medium(1.0f, 0)));
}

/**
 * \castest{<b>Une ligne et un cube sont des rectangles.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un eclair de 30 m sur 1,5 m ; un cube de 4,5 m d'arete, l'origine au milieu d'une
 * face.<br/>
 * \tattendu Les bords comptent : 1,4 m de cote touche, 1,6 m non ; le cube s'arrete a son arete.}
 */
TEST(EspaceDeCombatTest, UneLigneEtUnCubeSontDesRectangles) {
    // Éclair : 30 m de long, 1,5 m de large, vers +y.
    const Effect bolt{.shape = AreaShape::Line,
                      .origin = {0, 0, 0},
                      .toward = {0, 1, 0},
                      .size = 30.0f,
                      .width = 1.5f};
    EXPECT_TRUE(core::shapeHits(bolt, medium(0, 20.0f)));
    EXPECT_TRUE(core::shapeHits(bolt, medium(1.4f, 20.0f)));   // bord à 0,65 m du centre
    EXPECT_FALSE(core::shapeHits(bolt, medium(1.6f, 20.0f)));  // bord à 0,85 m
    // Cube de 4,5 m d'arête, l'origine au milieu d'une face, vers +x.
    const Effect cube{
        .shape = AreaShape::Cube, .origin = {0, 0, 0}, .toward = {1, 0, 0}, .size = 4.5f};
    EXPECT_TRUE(core::shapeHits(cube, medium(4.0f, 2.0f)));
    EXPECT_FALSE(core::shapeHits(cube, medium(4.0f, 3.1f)));
    EXPECT_FALSE(core::shapeHits(cube, medium(5.5f, 0)));
}

/**
 * \castest{<b>Un cylindre a la hauteur de sa donnee.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un cylindre de 3 m de rayon et 6 m de haut ; des creatures a 3,5 m, 4 m, et a 5 m
 * puis 6,5 m de haut.<br/>
 * \tattendu Touchees a 3,5 m et a 5 m de haut ; pas a 4 m ni a 6,5 m de haut.}
 */
TEST(EspaceDeCombatTest, UnCylindreALaHauteurDeSaDonnee) {
    // Un cylindre de 3 m de rayon et 6 m de haut depuis le sol.
    const Effect column{
        .shape = AreaShape::Cylinder, .origin = {0, 0, 0}, .size = 3.0f, .width = 6.0f};
    EXPECT_TRUE(core::shapeHits(column, medium(3.5f, 0)));
    EXPECT_FALSE(core::shapeHits(column, medium(4.0f, 0)));
    EXPECT_TRUE(core::shapeHits(column, medium(0, 0, 5.0f)));
    EXPECT_FALSE(core::shapeHits(column, medium(0, 0, 6.5f)));
}

/**
 * \castest{<b>Les volumes dans une zone sont rendus par indice croissant.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Trois volumes, une sphere de 3 m.<br/>
 * \tattendu Les indices 0 et 2.}
 */
TEST(EspaceDeCombatTest, LesVolumesDansUneZoneSontRendusParIndice) {
    const std::vector<Volume> volumes{medium(1, 0), medium(10, 0), medium(0, 2)};
    const Effect fireball{.shape = AreaShape::Sphere, .origin = {0, 0, 0}, .size = 3.0f};
    const std::vector<std::size_t> expected{0, 2};
    EXPECT_EQ(core::volumesInEffect(fireball, volumes), expected);
}

/**
 * \castest{<b>Un segment traverse un corps mais pas ses extremites.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un segment a travers un corps, a cote, au-dessus de la tete, et un qui part du
 * corps.<br/>
 * \tattendu Seul le premier est coupe.}
 */
TEST(EspaceDeCombatTest, UnSegmentTraverseUnCorpsMaisPasSesExtremites) {
    const Volume body = medium(3.0f, 0);
    const Meters3 a{0, 0, 0.75f};
    const Meters3 b{6, 0, 0.75f};
    EXPECT_TRUE(core::segmentCrosses(a, b, body));
    // Un segment qui passe à côté.
    EXPECT_FALSE(core::segmentCrosses(a, {6, 2.0f, 0.75f}, body));
    // Un segment qui passe au-dessus de la tête.
    EXPECT_FALSE(core::segmentCrosses({0, 0, 2.0f}, {6, 0, 2.0f}, body));
    // Un segment qui part du corps n'est pas coupé par lui.
    EXPECT_FALSE(core::segmentCrosses({3.0f, 0, 0.75f}, b, body));
}

/**
 * \castest{<b>Les portees du corpus se convertissent.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. 6 cases en metres, 9 m en cases, l'allonge.<br/>
 * \tattendu 9 m, 6 cases, 1,5 m.}
 */
TEST(EspaceDeCombatTest, LesPorteesDuCorpusSeConvertissent) {
    // « 6 cases » font 9 m ; « 9 m » font 6 cases.
    EXPECT_FLOAT_EQ(core::metersFromTiles(6.0f), 9.0f);
    EXPECT_FLOAT_EQ(core::tilesFromMeters(9.0f), 6.0f);
    EXPECT_FLOAT_EQ(core::MELEE_REACH_METERS, 1.5f);
}

}  // namespace
