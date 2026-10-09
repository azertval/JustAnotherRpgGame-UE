// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_area_of_effect.cpp
 * @brief Tests des zones d'effet dans le combat (`LOT-22`, `LOT-1017`) : qui une forme posée dans
 * l'espace prend parmi les combattants posés, l'origine, et les lignes d'effet coupées par les
 * murs.
 *
 * La géométrie des cinq formes est testée seule dans `test_combat_space.cpp`
 * (`core::shapeHits`). Ici, la règle se lit sur un combat monté (`core::combatantsInArea`) : une
 * créature est prise si son **volume** croise la forme — un bord suffit — et si l'origine ne la
 * tient pas sous abri total. Les gabarits de cases (« une case est dans la zone si la forme en
 * couvre la moitié ») et la conversion des tailles en cases ne sont plus : la forme est exacte, en
 * mètres.
 */

#include <algorithm>
#include <cstdint>
#include <initializer_list>
#include <memory>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/AreaOfEffect.h"
#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/CombatState.h"
#include "Core/Combat/SimulatedSpace.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"
#include "Test/Support/CombatSpaceSupport.h"

namespace {

using core::AreaShape;
using core::CombatantId;
using core::Effect;
using core::Meters3;
using test_support::tile;

[[nodiscard]] core::CombatantProfile profil(
    const char* nom, core::CombatSide camp,
    core::CreatureSize taille = core::CreatureSize::Medium) {
    core::CombatantProfile p{.name = nom,
                             .side = camp,
                             .maximumHitPoints = 10,
                             .currentHitPoints = 10,
                             .dexterity = 10,
                             .initiativeModifier = 0,
                             .movement = 6};
    p.size = taille;
    return p;
}

/// Un combat dans @p espace, des combattants de taille M aux places @p places (identifiants 1, 2,
/// … dans l'ordre).
[[nodiscard]] std::unique_ptr<core::CombatState> monter(
    std::shared_ptr<const core::CombatSpace> espace, std::initializer_list<Meters3> places) {
    auto combat = std::make_unique<core::CombatState>(std::move(espace));
    for (const Meters3 place : places) {
        EXPECT_TRUE(combat->enlist(profil("Gobelin", core::CombatSide::Enemies), place)
                        .combatant.has_value())
            << place.x << "," << place.y;
    }
    return combat;
}

[[nodiscard]] std::vector<CombatantId> ids(std::initializer_list<int> valeurs) {
    std::vector<CombatantId> liste;
    for (const int valeur : valeurs) {
        liste.push_back(CombatantId{static_cast<std::uint32_t>(valeur)});
    }
    return liste;
}

[[nodiscard]] bool contient(const std::vector<CombatantId>& pris, int id) {
    return std::ranges::find(pris, CombatantId{static_cast<std::uint32_t>(id)}) != pris.end();
}

}  // namespace

/**
 * @brief Chaque forme prend exactement les combattants dont le volume la croise.
 * \castest{<b>Sphere, cylindre, cone, ligne et cube prennent chacun, parmi des combattants poses,
 * exactement ceux dont le volume croise la forme : un bord suffit, le centre peut etre dehors ; la
 * distance est euclidienne, en metres.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Une sphere de 3 m en (9, 9) : un combattant a l'origine, un a 3,75 m (son bord a
 * 3 m), un en diagonale a 3,54 m, un a 4 m, un sur un plateau de 4 m.<br/>2. Un cylindre de 3 m de
 * rayon et 6 m de haut au meme point.<br/>3. Un cone de 4,50 m vers l'est : un dans l'axe, un dont
 * le centre est hors du cone et le bord dedans, un au-dela de la pointe, un derriere
 * l'origine.<br/>4. Une ligne de 6 m sur 1,50 m vers l'est : dans l'axe, a 0,65 m du bord, a
 * 1,25 m du bord, au-dela du bout.<br/>5. Un cube de 3 m vers le nord : dedans, derriere la face
 * d'origine, a 0,60 m du cote, au-dela.<br/>
 * \tattendu Sphere : 1, 2, 3 — pas le cinquieme, a 4 m au-dessus ; cylindre : 1, 2, 3, 5 ; cone :
 * 1, 2 ; ligne : 1, 2 ; cube : 1, 3.
 * }
 */
TEST(AreaOfEffectTest, ChaqueFormePrendLesVolumesQuiLaCroisent) {
    // Une salle de 18 m de cote, un plateau de 4 m sous le cinquieme.
    const std::shared_ptr<core::SimulatedSpace> salle = test_support::openSpace(12, 12);
    salle->addPlatform({8.25F, 10.25F, 9.75F, 11.75F}, 4.0F);
    const auto boule = monter(salle, {{9.0F, 9.0F, 0.0F},
                                      {12.75F, 9.0F, 0.0F},
                                      {11.5F, 11.5F, 0.0F},
                                      {9.0F, 13.0F, 0.0F},
                                      {9.0F, 11.0F, 0.0F}});
    ASSERT_NEAR(boule->positionOf(CombatantId{5})->z, 4.0F, 0.001F);
    Effect sphere{.shape = AreaShape::Sphere, .origin = {9.0F, 9.0F, 0.0F}, .size = 3.0F};
    EXPECT_EQ(core::combatantsInArea(*boule, sphere), ids({1, 2, 3}));
    Effect cylindre = sphere;
    cylindre.shape = AreaShape::Cylinder;
    cylindre.width = 6.0F;
    EXPECT_EQ(core::combatantsInArea(*boule, cylindre), ids({1, 2, 3, 5}));

    const auto souffle =
        monter(test_support::openSpace(12, 12),
               {{6.0F, 9.0F, 0.0F}, {6.0F, 11.2F, 0.0F}, {8.5F, 9.0F, 0.0F}, {1.5F, 9.0F, 0.0F}});
    const Effect cone{.shape = AreaShape::Cone,
                      .origin = {3.0F, 9.0F, 0.0F},
                      .toward = {6.0F, 9.0F, 0.0F},
                      .size = 4.5F};
    EXPECT_EQ(core::combatantsInArea(*souffle, cone), ids({1, 2}));

    const auto eclair =
        monter(test_support::openSpace(12, 12),
               {{6.0F, 3.0F, 0.0F}, {4.5F, 4.4F, 0.0F}, {7.5F, 5.0F, 0.0F}, {9.9F, 3.0F, 0.0F}});
    const Effect ligne{.shape = AreaShape::Line,
                       .origin = {3.0F, 3.0F, 0.0F},
                       .toward = {10.0F, 3.0F, 0.0F},
                       .size = 6.0F,
                       .width = 1.5F};
    EXPECT_EQ(core::combatantsInArea(*eclair, ligne), ids({1, 2}));

    const auto bloc = monter(
        test_support::openSpace(12, 12),
        {{13.5F, 13.5F, 0.0F}, {13.5F, 16.2F, 0.0F}, {15.6F, 13.5F, 0.0F}, {13.5F, 10.6F, 0.0F}});
    const Effect cube{.shape = AreaShape::Cube,
                      .origin = {13.5F, 15.0F, 0.0F},
                      .toward = {13.5F, 0.0F, 0.0F},
                      .size = 3.0F};
    EXPECT_EQ(core::combatantsInArea(*bloc, cube), ids({1, 3}));
}

/**
 * @brief L'origine au centre d'un combattant, et une taille qui n'est pas un multiple de la case.
 * \castest{<b>Une sphere posee au centre d'un combattant le prend ; un cone qui part du meme centre
 * prend ce qui est devant, pas ce qui est derriere ni sur le cote ; un cone sans direction ne prend
 * rien ; une taille de 1 m, qu'aucun nombre de cases n'ecrit, se joue telle quelle.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Un combattant en (5, 5), un deuxieme a 1,60 m a l'est (son bord a 0,85 m), un
 * troisieme a 1,90 m au sud (son bord a 1,15 m), un quatrieme a 1,80 m a l'ouest.<br/>2. Une sphere
 * de 1 m au centre du premier.<br/>3. Un cone de 3 m vers l'est depuis le meme centre.<br/>4. Un
 * cone dont la direction est son origine.<br/>
 * \tattendu Sphere : le premier et le deuxieme, pas le troisieme ; cone : le deuxieme, ni le
 * troisieme ni le quatrieme ; cone sans direction : personne.
 * }
 */
TEST(AreaOfEffectTest, LOrigineEtLesTailles) {
    const auto combat =
        monter(test_support::openSpace(6, 6),
               {{5.0F, 5.0F, 0.0F}, {6.6F, 5.0F, 0.0F}, {5.0F, 6.9F, 0.0F}, {3.2F, 5.0F, 0.0F}});
    const Meters3 centre{5.0F, 5.0F, 0.0F};
    const Effect sphere{.shape = AreaShape::Sphere, .origin = centre, .size = 1.0F};
    EXPECT_EQ(core::combatantsInArea(*combat, sphere), ids({1, 2}));

    const Effect cone{
        .shape = AreaShape::Cone, .origin = centre, .toward = {8.0F, 5.0F, 0.0F}, .size = 3.0F};
    const std::vector<CombatantId> souffle = core::combatantsInArea(*combat, cone);
    EXPECT_TRUE(contient(souffle, 2));
    EXPECT_FALSE(contient(souffle, 3));
    EXPECT_FALSE(contient(souffle, 4));

    Effect sansDirection = cone;
    sansDirection.toward = centre;
    EXPECT_TRUE(core::combatantsInArea(*combat, sansDirection).empty());
}

/**
 * @brief Un mur arrete l'effet, un corps non ; les combattants d'une zone se comptent une fois.
 * \castest{<b>Une sphere posee devant un mur ne prend pas le combattant qu'aucune ligne droite ne
 * relie a son origine ; un corps interpose ne protege pas ; une creature de grande taille dont le
 * bord seul est dans la zone y est, une fois ; un corps a terre est pris.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Une salle 7 × 7 barree d'un mur vertical sur cinq cases, en colonne 4.<br/>2. Une
 * sphere de 4,50 m au centre de la case (3, 3), qui deborde derriere le mur.<br/>3. Un allie en
 * (2, 3), un gobelin derriere le mur en (5, 3), un ogre de taille G sur les cases (0, 5) a (1, 6),
 * un pretre a terre en (1, 3) derriere l'allie, un rat hors de portee en (0, 0).<br/>
 * \tattendu L'allie, l'ogre et le pretre, une fois chacun ; ni le gobelin ni le rat.
 * }
 */
TEST(AreaOfEffectTest, UnMurArreteLEffet) {
    core::TileMap collision(7, 7);
    for (int ligne = 1; ligne <= 5; ++ligne) {
        collision.setTile(4, ligne, core::TileType::Wall);
    }
    core::CombatState combat(test_support::spaceOf(collision));
    combat.enlist(profil("Allie", core::CombatSide::Allies), tile(2, 3));
    combat.enlist(profil("Gobelin", core::CombatSide::Enemies), tile(5, 3));
    combat.enlist(profil("Ogre", core::CombatSide::Enemies, core::CreatureSize::Large),
                  tile(0, 5, core::CreatureSize::Large));
    core::CombatantProfile pretre = profil("Pretre", core::CombatSide::Allies);
    pretre.currentHitPoints = 0;
    combat.enlist(pretre, tile(1, 3));
    combat.enlist(profil("Rat", core::CombatSide::Enemies), tile(0, 0));
    ASSERT_EQ(combat.combatants().size(), 5U);
    for (const CombatantId id : combat.combatants()) {
        ASSERT_TRUE(combat.positionOf(id).has_value()) << static_cast<int>(id);
    }
    ASSERT_EQ(combat.find(CombatantId{4})->status, core::CombatantStatus::Down);

    const Effect boule{.shape = AreaShape::Sphere, .origin = tile(3, 3), .size = 4.5F};
    // Le gobelin est dans la forme — son bord a 2,25 m de l'origine — mais derriere le mur.
    ASSERT_TRUE(core::shapeHits(boule, *combat.volumeOf(CombatantId{2})));
    EXPECT_EQ(core::combatantsInArea(combat, boule), ids({1, 3, 4}));
}
