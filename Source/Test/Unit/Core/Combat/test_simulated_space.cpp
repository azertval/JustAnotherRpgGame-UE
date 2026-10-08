// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_simulated_space.cpp
 * @brief L'espace simulé (`LOT-1017`) : chemins en mètres, budget, obstacles, terrain difficile,
 *        vue, abri, hauteur du sol, déterminisme, et la lecture d'une grille de collision.
 */

#include <algorithm>
#include <cmath>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/SimulatedSpace.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"

namespace {

using core::Box;
using core::Cover;
using core::CreatureSize;
using core::GroundRect;
using core::Meters3;
using core::RouteQuery;
using core::SimulatedSpace;
using core::Volume;

Volume medium(float x, float y, float z = 0.0f) {
    return core::volumeOf({x, y, z}, CreatureSize::Medium);
}

/**
 * \castest{<b>Un chemin droit sur un plan vide coute sa longueur.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un plan vide, 6 m a parcourir dans un budget de 9 m.<br/>
 * \tattendu Un chemin de 6 m qui finit a la destination exacte.}
 */
TEST(EspaceSimuleTest, UnCheminDroitSurUnPlanVideCouteSaLongueur) {
    const SimulatedSpace space(30.0f, 30.0f);
    const RouteQuery query{.mover = medium(3, 3), .destination = {9, 3, 0}, .budget = 9.0f};
    const auto route = space.route(query);
    ASSERT_TRUE(route.has_value());
    EXPECT_NEAR(route->length, 6.0f, 0.01f);
    ASSERT_FALSE(route->points.empty());
    EXPECT_NEAR(route->points.back().x, 9.0f, 0.01f);
    EXPECT_NEAR(route->points.back().y, 3.0f, 0.01f);
}

/**
 * \castest{<b>Le budget arrete le chemin.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. 9,5 m puis 9 m a parcourir avec 9 m de budget ; sans budget, le coin oppose du
 * plan.<br/>
 * \tattendu Refuse a 9,5 m, accepte a 9 m ; tout s'atteint sans budget.}
 */
TEST(EspaceSimuleTest, LeBudgetArreteLeChemin) {
    const SimulatedSpace space(30.0f, 30.0f);
    // 9 m de déplacement (une vitesse de 9 m) : 9,5 m sont hors d'atteinte, 9 m s'atteignent.
    EXPECT_FALSE(space.route({.mover = medium(3, 3), .destination = {12.5f, 3, 0}, .budget = 9.0f})
                     .has_value());
    EXPECT_TRUE(space.route({.mover = medium(3, 3), .destination = {12.0f, 3, 0}, .budget = 9.0f})
                    .has_value());
    // Sans budget, tout s'atteint.
    EXPECT_TRUE(space.route({.mover = medium(3, 3), .destination = {27, 27, 0}}).has_value());
}

/**
 * \castest{<b>Un mur se contourne et ne se traverse pas.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un mur de 20 m entre le depart et l'arrivee ; un budget de 11 m puis aucun.<br/>
 * \tattendu Refuse dans le budget ; sans budget, le chemin fait plus de 30 m et aucun point n'est
 * dans le mur.}
 */
TEST(EspaceSimuleTest, UnMurSeContourneEtNeSeTraversePas) {
    SimulatedSpace space(30.0f, 30.0f);
    // Un mur de x = 10 à 11, de y = 0 à 20 : on passe par le haut, en y > 20.
    space.addBox({.rect = {10, 0, 11, 20}});
    const RouteQuery direct{.mover = medium(5, 5), .destination = {16, 5, 0}, .budget = 11.0f};
    EXPECT_FALSE(space.route(direct).has_value());
    const RouteQuery around{.mover = medium(5, 5), .destination = {16, 5, 0}};
    const auto route = space.route(around);
    ASSERT_TRUE(route.has_value());
    // Le détour passe au-dessus de y = 20 : au moins 2 × 15 m de montée et descente, plus le
    // travers.
    EXPECT_GT(route->length, 30.0f);
    for (const Meters3& point : route->points) {
        EXPECT_FALSE(point.x > 9.2f && point.x < 11.8f && point.y < 20.0f)
            << "le chemin traverse le mur en " << point.x << ", " << point.y;
    }
}

/**
 * \castest{<b>On ne finit pas dans un mur ni hors du plan.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Une destination dans une boite ; un volume au bord du plan.<br/>
 * \tattendu Pas de chemin ; la place au bord n'est pas libre, a 1 m du bord elle l'est.}
 */
TEST(EspaceSimuleTest, OnNeFinitPasDansUnMurNiHorsDuPlan) {
    SimulatedSpace space(10.0f, 10.0f);
    space.addBox({.rect = {4, 4, 6, 6}});
    EXPECT_FALSE(space.route({.mover = medium(1, 1), .destination = {5, 5, 0}}).has_value());
    EXPECT_FALSE(space.isClear(medium(0.2f, 5), core::Locomotion::Walk));
    EXPECT_TRUE(space.isClear(medium(1, 5), core::Locomotion::Walk));
}

/**
 * \castest{<b>Le terrain difficile coute double au sol et rien en vol.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Une bande de 3 m de terrain difficile sur 6 m de route.<br/>
 * \tattendu Environ 9 m a pied, 6 m en vol.}
 */
TEST(EspaceSimuleTest, LeTerrainDifficileCouteDouble) {
    SimulatedSpace space(30.0f, 30.0f);
    // Une bande de 3 m de terrain difficile en travers : 6 m de route dont 3 à double coût = 9 m.
    space.addDifficult({6.0f, 0.0f, 9.0f, 30.0f});
    const auto walking =
        space.route({.mover = medium(3, 3), .destination = {9, 3, 0}, .budget = 9.5f});
    ASSERT_TRUE(walking.has_value());
    EXPECT_NEAR(walking->length, 9.0f, 0.6f);
    // En vol, le terrain difficile ne compte pas.
    const auto flying = space.route({.mover = medium(3, 3),
                                     .destination = {9, 3, 0},
                                     .budget = 9.5f,
                                     .locomotion = core::Locomotion::Fly});
    ASSERT_TRUE(flying.has_value());
    EXPECT_NEAR(flying->length, 6.0f, 0.01f);
}

/**
 * \castest{<b>L'eau profonde arrete la marche et pas le vol.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Une bande d'eau profonde en travers.<br/>
 * \tattendu Pas de chemin a pied, un chemin en vol.}
 */
TEST(EspaceSimuleTest, LEauProfondeArreteLaMarcheEtPasLeVol) {
    SimulatedSpace space(30.0f, 30.0f);
    space.addDeepWater({0.0f, 10.0f, 30.0f, 12.0f});
    EXPECT_FALSE(space.route({.mover = medium(5, 5), .destination = {5, 20, 0}}).has_value());
    EXPECT_TRUE(space
                    .route({.mover = medium(5, 5),
                            .destination = {5, 20, 0},
                            .locomotion = core::Locomotion::Fly})
                    .has_value());
}

/**
 * \castest{<b>Un ennemi bloque, un allie se traverse en coutant double.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un couloir etroit tenu par un ennemi, puis par un allie ; une destination dans
 * l'espace de l'allie.<br/>
 * \tattendu Pas de chemin a travers l'ennemi ; a travers l'allie, plus de 16 m pour 14 ; on ne
 * finit pas dans son espace.}
 */
TEST(EspaceSimuleTest, UnEnnemiBloqueEtUnAllieSeTraverseEnCoutantDouble) {
    SimulatedSpace space(30.0f, 30.0f);
    // Un couloir de 1,6 m de large en y, de x = 5 à 15 : rien ne contourne ce qui s'y tient.
    space.addBox({.rect = {5, 0, 15, 9.2f}});
    space.addBox({.rect = {5, 10.8f, 15, 30}});
    const std::vector<Volume> enemy{medium(10, 10)};
    const std::vector<Volume> ally{medium(10, 10)};
    EXPECT_FALSE(
        space.route({.mover = medium(3, 10), .destination = {17, 10, 0}, .blocking = enemy})
            .has_value());
    const auto through =
        space.route({.mover = medium(3, 10), .destination = {17, 10, 0}, .passable = ally});
    ASSERT_TRUE(through.has_value());
    // 14 m, dont l'espace de l'allié (1,5 m de diamètre plus le rayon du mobile de chaque côté,
    // soit 3 m) compte double : environ 17 m.
    EXPECT_GT(through->length, 16.0f);
    // On ne finit pas dans l'espace de l'allié.
    EXPECT_FALSE(space.route({.mover = medium(3, 10), .destination = {10, 10, 0}, .passable = ally})
                     .has_value());
}

/**
 * \castest{<b>Les candidats sont dans le budget et en ordre fixe.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Deux demandes identiques, budget de 4,5 m, une boite a cote.<br/>
 * \tattendu Les memes points dans le meme ordre, le depart en tete, tous libres et dans le budget ;
 * 9 m est absent, 4 m present.}
 */
TEST(EspaceSimuleTest, LesCandidatsSontDansLeBudgetEtEnOrdreFixe) {
    SimulatedSpace space(20.0f, 20.0f);
    space.addBox({.rect = {8, 8, 12, 12}});
    const RouteQuery query{.mover = medium(5, 5), .destination = {}, .budget = 4.5f};
    const std::vector<Meters3> first = space.candidates(query);
    const std::vector<Meters3> second = space.candidates(query);
    EXPECT_EQ(first, second);
    ASSERT_FALSE(first.empty());
    EXPECT_EQ(first.front(), query.mover.base);
    for (const Meters3& point : first) {
        EXPECT_LE(core::groundDistance(point, query.mover.base), 4.5f + 0.01f);
        EXPECT_TRUE(
            space.isClear(core::volumeOf(point, CreatureSize::Medium), core::Locomotion::Walk));
    }
    // Un point à 9 m n'y est pas ; un point à 4 m y est.
    const bool far = std::any_of(first.begin(), first.end(), [](const Meters3& p) {
        return std::fabs(p.x - 14.0f) < 0.01f && std::fabs(p.y - 5.0f) < 0.01f;
    });
    const bool near = std::any_of(first.begin(), first.end(), [](const Meters3& p) {
        return std::fabs(p.x - 9.0f) < 0.01f && std::fabs(p.y - 5.0f) < 0.01f;
    });
    EXPECT_FALSE(far);
    EXPECT_TRUE(near);
}

/**
 * \castest{<b>Un mur arrete la vue et une toile non.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un mur de 3 m ; un regard a 0,75 m puis a 3,5 m ; une toile sans abri.<br/>
 * \tattendu Coupe sous le mur, degage par-dessus, degage a travers la toile.}
 */
TEST(EspaceSimuleTest, UnMurArreteLaVueEtUneToileNon) {
    SimulatedSpace space(20.0f, 20.0f);
    space.addBox({.rect = {9, 0, 10, 20}, .height = 3.0f, .cover = Cover::Total});
    EXPECT_FALSE(space.lineOfSight({5, 5, 0.75f}, {15, 5, 0.75f}));
    // Par-dessus le mur, on voit.
    EXPECT_TRUE(space.lineOfSight({5, 5, 3.5f}, {15, 5, 3.5f}));
    SimulatedSpace web(20.0f, 20.0f);
    web.addBox({.rect = {9, 0, 10, 20}, .blocksMovement = false, .cover = Cover::None});
    EXPECT_TRUE(web.lineOfSight({5, 5, 0.75f}, {15, 5, 0.75f}));
}

/**
 * \castest{<b>L'abri se compte par lignes coupees.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Rien, un mur plein, un muret d'un metre, un mur qui s'arrete a mi-cible.<br/>
 * \tattendu Aucun abri ; abri total sans ligne de vue ; abri partiel ou important derriere le muret
 * ; un abri ni nul ni total derriere le demi-mur.}
 */
TEST(EspaceSimuleTest, LAbriSeCompteParLignesCoupees) {
    // Rien entre les deux : aucun abri.
    SimulatedSpace open(20.0f, 20.0f);
    EXPECT_EQ(core::coverFrom(open, medium(2, 5), medium(12, 5)), Cover::None);
    // Un mur plein entre les deux : abri total, et pas de ligne de vue.
    SimulatedSpace wall(20.0f, 20.0f);
    wall.addBox({.rect = {7, 0, 8, 20}});
    EXPECT_EQ(core::coverFrom(wall, medium(2, 5), medium(12, 5)), Cover::Total);
    EXPECT_FALSE(core::hasLineOfSight(wall, medium(2, 5), medium(12, 5)));
    // Un muret d'un mètre : il coupe les lignes vers le bas du corps, pas vers le haut.
    SimulatedSpace low(20.0f, 20.0f);
    low.addBox({.rect = {7, 0, 8, 20}, .height = 1.0f, .cover = Cover::Half});
    const Cover behindLow = core::coverFrom(low, medium(2, 5), medium(12, 5));
    EXPECT_TRUE(behindLow == Cover::Half || behindLow == Cover::ThreeQuarters);
    EXPECT_NE(behindLow, Cover::Total);
    // Un mur qui s'arrête à y = 5,2 : la cible en y = 5 est à moitié cachée, l'attaquant
    // choisit son meilleur point.
    SimulatedSpace half(20.0f, 20.0f);
    half.addBox({.rect = {7, 0, 8, 5.2f}});
    const Cover partial = core::coverFrom(half, medium(2, 5), medium(12, 5));
    EXPECT_NE(partial, Cover::None);
    EXPECT_NE(partial, Cover::Total);
}

/**
 * \castest{<b>Un corps interpose abrite a moitie.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Une creature sur la ligne, puis a cote.<br/>
 * \tattendu Abri partiel, puis aucun.}
 */
TEST(EspaceSimuleTest, UnCorpsInterposeAbriteAMoitie) {
    const SimulatedSpace open(20.0f, 20.0f);
    const std::vector<Volume> between{medium(7, 5)};
    EXPECT_EQ(core::coverFrom(open, medium(2, 5), medium(12, 5), between), Cover::Half);
    // À côté de la ligne, il n'abrite pas.
    const std::vector<Volume> aside{medium(7, 8)};
    EXPECT_EQ(core::coverFrom(open, medium(2, 5), medium(12, 5), aside), Cover::None);
}

/**
 * \castest{<b>La ligne de vue est symetrique.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Deux volumes et deux boites ; la vue dans les deux sens.<br/>
 * \tattendu La meme reponse.}
 */
TEST(EspaceSimuleTest, LAbriEstSymetriqueSansCorps) {
    SimulatedSpace space(20.0f, 20.0f);
    space.addBox({.rect = {7, 0, 8, 5.2f}});
    space.addBox({.rect = {10, 7, 14, 8}});
    const Volume a = medium(2, 5);
    const Volume b = medium(12, 5);
    EXPECT_EQ(core::hasLineOfSight(space, a, b), core::hasLineOfSight(space, b, a));
}

/**
 * \castest{<b>Un plateau donne sa hauteur au sol.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Un plateau a 1,5 m ; un chemin qui y monte.<br/>
 * \tattendu Le sol est a 0 puis 1,5 m ; l'arrivee est a 1,5 m et a l'avantage de la hauteur.}
 */
TEST(EspaceSimuleTest, UnPlateauDonneSaHauteurAuSol) {
    SimulatedSpace space(20.0f, 20.0f);
    space.addPlatform({10, 0, 20, 20}, 1.5f);
    EXPECT_FLOAT_EQ(space.groundHeight(5, 5), 0.0f);
    EXPECT_FLOAT_EQ(space.groundHeight(15, 5), 1.5f);
    const auto route = space.route({.mover = medium(5, 5), .destination = {15, 5, 0}});
    ASSERT_TRUE(route.has_value());
    EXPECT_FLOAT_EQ(route->points.back().z, 1.5f);
    // Monté sur le plateau, on a l'avantage de la hauteur sur qui est resté en bas.
    const Volume up = core::volumeOf(route->points.back(), CreatureSize::Medium);
    EXPECT_TRUE(core::hasHighGround(up, medium(8, 5)));
}

/**
 * \castest{<b>Une grille de collision devient des boites.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Une grille 10 x 10 avec un mur d'une colonne perce en bas.<br/>
 * \tattendu Un plan de 15 m, huit boites, le mur bloque, le chemin fait plus de 20 m par le
 * passage.}
 */
TEST(EspaceSimuleTest, UneGrilleDeCollisionDevientDesBoites) {
    core::TileMap collision(10, 10);
    for (int row = 0; row < 10; ++row) {
        collision.setTile(5, row, core::TileType::Wall);
    }
    // Deux cases ouvertes en bas (lignes 8 et 9 : y de 12 à 15) : une créature M y passe.
    collision.setTile(5, 8, core::TileType::Empty);
    collision.setTile(5, 9, core::TileType::Empty);
    const SimulatedSpace space = SimulatedSpace::fromTileMap(collision);
    EXPECT_FLOAT_EQ(space.width(), 15.0f);
    EXPECT_EQ(space.boxes().size(), 8u);
    EXPECT_FALSE(space.isClear(medium(8.25f, 2.0f), core::Locomotion::Walk));
    // On passe par les cases ouvertes du bas.
    const auto route =
        space.route({.mover = medium(2.25f, 2.25f), .destination = {12.75f, 2.25f, 0}});
    ASSERT_TRUE(route.has_value());
    EXPECT_GT(route->length, 20.0f);
}

/**
 * \castest{<b>Le meme chemin deux fois.</b><br/>
 * \tcat Unitaire · Combat en distance (LOT-1017)<br/>
 * \tcrit Majeure<br/>
 * \tetapes 1. Une boite, du terrain difficile, la meme demande deux fois.<br/>
 * \tattendu Les memes points et la meme longueur.}
 */
TEST(EspaceSimuleTest, LeMemeCheminDeuxFois) {
    SimulatedSpace space(30.0f, 30.0f);
    space.addBox({.rect = {10, 5, 12, 25}});
    space.addDifficult({14, 0, 16, 30});
    const RouteQuery query{.mover = medium(3, 15), .destination = {25, 15, 0}};
    const auto first = space.route(query);
    const auto second = space.route(query);
    ASSERT_TRUE(first.has_value());
    ASSERT_TRUE(second.has_value());
    EXPECT_EQ(first->points, second->points);
    EXPECT_FLOAT_EQ(first->length, second->length);
}

}  // namespace
