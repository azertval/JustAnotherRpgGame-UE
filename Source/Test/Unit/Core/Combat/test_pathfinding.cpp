// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_pathfinding.cpp
 * @brief Tests du déplacement d'un tour : budget, cases atteignables, chemin déterministe
 *        (`LOT-19`, `EX-CBT-020`, `EX-REG-051`).
 *
 * La règle vérifiée est celle du Manuel des Joueurs, « Jouer sur un quadrillage » : entrer dans une
 * case coûte 1, même en diagonale ; 2 en terrain difficile, à condition de pouvoir le payer ; et
 * l'on ne passe pas en diagonale par le coin d'un mur.
 */

#include <algorithm>
#include <cstdlib>
#include <optional>
#include <random>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/BattleGrid.h"
#include "Core/Combat/Pathfinding.h"
#include "Core/Levels/GridPosition.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/CharacterSheet.h"

namespace {

constexpr core::CombatantId HEROS{1};
constexpr core::CombatantId ALLIE{2};
constexpr core::CombatantId ENNEMI{3};

/// Distance de Tchebychev : la portée d'un déplacement sans obstacle, diagonales comprises.
[[nodiscard]] int tchebychev(core::GridPosition a, core::GridPosition b) {
    return std::max(std::abs(a.column - b.column), std::abs(a.row - b.row));
}

/// Une grille ouverte de @p cote cases, le héros au centre.
[[nodiscard]] core::BattleGrid grilleOuverte(int cote) {
    core::BattleGrid grille{core::TileMap(cote, cote)};
    EXPECT_EQ(grille.place(HEROS, {cote / 2, cote / 2}), core::PlacementResult::Placed);
    return grille;
}

/// Une carte de 9 × 7 avec un mur en L et une mare de boue : de quoi rendre les égalités de coût
/// nombreuses et le départage visible.
[[nodiscard]] core::BattleGrid grilleAccidentee() {
    core::TileMap collision(9, 7);
    for (int row = 1; row <= 4; ++row) {
        collision.setTile(4, row, core::TileType::Wall);
    }
    collision.setTile(5, 4, core::TileType::Wall);
    collision.setTile(6, 4, core::TileType::Wall);
    core::BattleGrid grille(collision);
    grille.setDifficult({2, 5}, true);
    grille.setDifficult({3, 5}, true);
    grille.setDifficult({2, 2}, true);
    EXPECT_EQ(grille.place(HEROS, {1, 3}), core::PlacementResult::Placed);
    return grille;
}

}  // namespace

/**
 * @brief Le budget se deduit de la vitesse en metres, a raison d'une case pour 1,5 m.
 * \castest{<b>Le budget de deplacement vaut la vitesse divisee par 1,5, arrondie en
 * dessous.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Convertir 9 m, 7,5 m, 10 m, 0 m et -3 m.<br/>2. Lire le budget d'une fiche a 9
 * m.<br/>
 * 3. Lire le budget de marche et de vol d'une creature qui ne vole pas, puis d'une qui vole.<br/>
 * \tattendu 6, 5, 6, 0, 0 ; 6 pour la fiche ; la creature sans vol a un budget de vol nul.
 * }
 */
TEST(PathfindingTest, LeBudgetSeDeduitDeLaVitesse) {
    EXPECT_EQ(core::movementBudget(9.0F), 6) << "Manuel des Joueurs : 9 metres, 6 cases";
    EXPECT_EQ(core::movementBudget(7.5F), 5);
    EXPECT_EQ(core::movementBudget(10.0F), 6) << "un segment de 1,50 m entame n'en est pas un";
    EXPECT_EQ(core::movementBudget(13.5F - 4.5F), 6);
    EXPECT_EQ(core::movementBudget(0.0F), 0);
    EXPECT_EQ(core::movementBudget(-3.0F), 0);

    core::CharacterSheet fiche;
    fiche.speedMeters = 9.0F;
    EXPECT_EQ(core::movementBudget(fiche), 6);

    core::Creature loup;
    loup.speed.walk = 12.0F;
    EXPECT_EQ(core::movementBudget(loup, core::Locomotion::Walk), 8);
    EXPECT_EQ(core::movementBudget(loup, core::Locomotion::Fly), 0);
    core::Creature chouette;
    chouette.speed.walk = 1.5F;
    chouette.speed.fly = 18.0F;
    EXPECT_EQ(core::movementBudget(chouette, core::Locomotion::Fly), 12);
}

/**
 * @brief Les cases atteignables correspondent exactement au budget, ni une de plus ni une de moins.
 * \castest{<b>Les cases atteignables correspondent exactement au budget.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Grille ouverte 11x11, heros au centre.<br/>2. Calculer l'aire atteignable pour les
 * budgets 0 a 5.<br/>3. Comparer chaque case a sa distance de Tchebychev.<br/>
 * \tattendu Une case est une destination si et seulement si 1 <= distance <= budget ; le nombre de
 * destinations vaut (2b+1)^2 - 1 ; le cout d'une case vaut sa distance.
 * }
 */
TEST(PathfindingTest, LesCasesAtteignablesCorrespondentExactementAuBudget) {
    const core::BattleGrid grille = grilleOuverte(11);
    const core::GridPosition centre{5, 5};

    for (int budget = 0; budget <= 5; ++budget) {
        const core::ReachableArea aire(grille, {.combatant = HEROS}, budget);
        EXPECT_EQ(aire.origin(), centre);
        const std::size_t attendu =
            static_cast<std::size_t>((2 * budget + 1) * (2 * budget + 1) - 1);
        EXPECT_EQ(aire.destinations().size(), attendu) << "budget " << budget;
        for (int row = 0; row < 11; ++row) {
            for (int column = 0; column < 11; ++column) {
                const core::GridPosition case_{column, row};
                const int distance = tchebychev(case_, centre);
                EXPECT_EQ(aire.canEndAt(case_), distance >= 1 && distance <= budget)
                    << "budget " << budget << ", case (" << column << "," << row << ")";
                if (distance <= budget) {
                    EXPECT_EQ(aire.costTo(case_), distance);
                } else {
                    EXPECT_FALSE(aire.costTo(case_).has_value());
                }
            }
        }
    }
}

/**
 * @brief Un mur coute le detour : la portee se compte sur la grille, pas a vol d'oiseau.
 * \castest{<b>Un mur entre deux cases voisines coute le detour.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Grille 7x5, mur vertical en colonne 3 des lignes 0 a 2.<br/>2. Heros en (2,1), cible
 * en (4,1), a deux cases de l'autre cote du mur.<br/>
 * \tattendu Le cout vaut 6 : le detour par la ligne 3, sans couper le coin du mur ni a l'aller ni
 * au retour. Un budget de 5 ne l'atteint pas, un budget de 6 si.
 * }
 */
TEST(PathfindingTest, UnMurCouteLeDetour) {
    core::TileMap collision(7, 5);
    for (int row = 0; row <= 2; ++row) {
        collision.setTile(3, row, core::TileType::Wall);
    }
    core::BattleGrid grille(collision);
    ASSERT_EQ(grille.place(HEROS, {2, 1}), core::PlacementResult::Placed);

    const core::ReachableArea courte(grille, {.combatant = HEROS}, 5);
    EXPECT_FALSE(courte.canEndAt({4, 1})) << "a vol d'oiseau, la cible n'est qu'a deux cases";
    const core::ReachableArea longue(grille, {.combatant = HEROS}, 6);
    EXPECT_TRUE(longue.canEndAt({4, 1}));
    EXPECT_EQ(longue.costTo({4, 1}), 6);

    const std::optional<core::Path> chemin = core::findPath(grille, {.combatant = HEROS}, {4, 1});
    ASSERT_TRUE(chemin.has_value());
    EXPECT_EQ(chemin->cost, 6);
    EXPECT_EQ(chemin->steps.size(), 6U);
    EXPECT_EQ(chemin->steps.back(), (core::GridPosition{4, 1}));
}

/**
 * @brief On ne passe pas en diagonale par le coin d'un mur.
 * \castest{<b>Une diagonale ne coupe pas le coin d'un mur.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Grille 3x3, mur en (1,0).<br/>2. Heros en (0,0), cible (1,1) en diagonale.<br/>3.
 * Meme chose avec de l'eau profonde a la place du mur.<br/>
 * \tattendu Contre le mur, la diagonale est interdite et le cout vaut 2 (par (0,1)) ; contre l'eau
 * profonde, qui ne remplit pas l'espace, elle est permise et coute 1.
 * }
 */
TEST(PathfindingTest, UneDiagonaleNeCoupePasLeCoinDUnMur) {
    core::TileMap murs(3, 3);
    murs.setTile(1, 0, core::TileType::Wall);
    core::BattleGrid grilleMur(murs);
    ASSERT_EQ(grilleMur.place(HEROS, {0, 0}), core::PlacementResult::Placed);
    EXPECT_EQ(core::ReachableArea(grilleMur, {.combatant = HEROS}, 3).costTo({1, 1}), 2);

    core::TileMap mare(3, 3);
    mare.setTile(1, 0, core::TileType::DeepWater);
    core::BattleGrid grilleMare(mare);
    ASSERT_EQ(grilleMare.place(HEROS, {0, 0}), core::PlacementResult::Placed);
    EXPECT_EQ(core::ReachableArea(grilleMare, {.combatant = HEROS}, 3).costTo({1, 1}), 1);
}

/**
 * @brief Le terrain difficile double le cout, et reduit la portee en consequence.
 * \castest{<b>Le terrain difficile double le cout et reduit la portee.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Grille ouverte 11x11, heros au centre, budget 4.<br/>2. Rendre difficile une case
 * voisine, puis toute la grille.<br/>3. Recalculer l'aire avec un budget de 1 contre une case
 * difficile.<br/>
 * \tattendu La case difficile coute 2 ; toute la grille difficile ramene les 80 destinations a 24
 * (portee 2 au lieu de 4) ; avec un budget de 1, la case difficile voisine est hors de portee.
 * }
 */
TEST(PathfindingTest, LeTerrainDifficileDoubleLeCoutEtReduitLaPortee) {
    core::BattleGrid grille = grilleOuverte(11);
    const core::GridPosition voisine{6, 5};

    grille.setDifficult(voisine, true);
    const core::ReachableArea uneCase(grille, {.combatant = HEROS}, 4);
    EXPECT_EQ(uneCase.costTo(voisine), 2);
    EXPECT_EQ(uneCase.costTo({7, 5}), 2) << "le detour par la diagonale evite la boue";
    EXPECT_FALSE(core::ReachableArea(grille, {.combatant = HEROS}, 1).canEndAt(voisine))
        << "il faut pouvoir payer l'entree entiere";

    EXPECT_EQ(core::ReachableArea(grilleOuverte(11), {.combatant = HEROS}, 4).destinations().size(),
              80U);
    for (int row = 0; row < 11; ++row) {
        for (int column = 0; column < 11; ++column) {
            grille.setDifficult({column, row}, true);
        }
    }
    const core::ReachableArea boue(grille, {.combatant = HEROS}, 4);
    EXPECT_EQ(boue.destinations().size(), 24U);
    EXPECT_EQ(boue.costTo({7, 7}), 4);
    EXPECT_FALSE(boue.costTo({8, 5}).has_value());
}

/**
 * @brief On traverse un allie si la requete le permet, jamais un ennemi, et l'on ne finit sur
 * aucun.
 * \castest{<b>Un allie se traverse, un ennemi non, et aucun ne sert de destination.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Couloir 5x1 : heros en (0,0), allie en (1,0), ennemi en (3,0).<br/>2. Calculer
 * l'aire sans droit de passage, puis en autorisant l'allie.<br/>
 * \tattendu Sans droit de passage, rien n'est atteignable ; avec, (2,0) l'est pour 2 et (1,0) a un
 * cout mais n'est pas une destination ; l'ennemi ferme le couloir.
 * }
 */
TEST(PathfindingTest, UnAllieSeTraverseUnEnnemiNon) {
    core::BattleGrid grille{core::TileMap(5, 1)};
    ASSERT_EQ(grille.place(HEROS, {0, 0}), core::PlacementResult::Placed);
    ASSERT_EQ(grille.place(ALLIE, {1, 0}), core::PlacementResult::Placed);
    ASSERT_EQ(grille.place(ENNEMI, {3, 0}), core::PlacementResult::Placed);

    const core::ReachableArea bloque(grille, {.combatant = HEROS}, 6);
    EXPECT_TRUE(bloque.destinations().empty());

    const core::Mover heros{.combatant = HEROS, .canPassThrough = [](core::CombatantId autre) {
                                return autre == ALLIE;
                            }};
    const core::ReachableArea passage(grille, heros, 6);
    EXPECT_EQ(passage.destinations(), (std::vector<core::GridPosition>{{2, 0}}));
    // La case d'une autre creature compte comme terrain difficile (Manuel des Joueurs, PDF p. 193).
    EXPECT_EQ(passage.costTo({1, 0}), 2);
    EXPECT_EQ(passage.costTo({2, 0}), 3);
    EXPECT_FALSE(passage.canEndAt({1, 0}));
    EXPECT_FALSE(passage.costTo({4, 0}).has_value());
    EXPECT_FALSE(core::findPath(grille, heros, {4, 0}).has_value());
    EXPECT_FALSE(core::findPath(grille, heros, {1, 0}).has_value());
}

/**
 * @brief Meme entree, meme chemin : le departage est une regle ecrite.
 * \castest{<b>Meme entree, meme chemin, et le departage suit la regle du plus petit
 * indice.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Grille ouverte 3x3, heros en (0,0).<br/>2. Demander le chemin vers (2,0) et vers
 * (0,2), chacun a deux chemins de cout 2.<br/>3. Repeter cent fois la requete sur une grille
 * accidentee.<br/>
 * \tattendu Vers (2,0) : (1,0) puis (2,0) ; vers (0,2) : (0,1) puis (0,2) ; les cent chemins sont
 * identiques.
 * }
 */
TEST(PathfindingTest, MemeEntreeMemeChemin) {
    core::BattleGrid petite{core::TileMap(3, 3)};
    ASSERT_EQ(petite.place(HEROS, {0, 0}), core::PlacementResult::Placed);
    const std::optional<core::Path> versLaDroite =
        core::findPath(petite, {.combatant = HEROS}, {2, 0});
    ASSERT_TRUE(versLaDroite.has_value());
    EXPECT_EQ(versLaDroite->steps, (std::vector<core::GridPosition>{{1, 0}, {2, 0}}))
        << "(1,0) et (1,1) atteignent (2,0) au meme cout : (1,0) est sur la droite";
    const std::optional<core::Path> versLeBas =
        core::findPath(petite, {.combatant = HEROS}, {0, 2});
    ASSERT_TRUE(versLeBas.has_value());
    EXPECT_EQ(versLeBas->steps, (std::vector<core::GridPosition>{{0, 1}, {0, 2}}));

    const core::BattleGrid grille = grilleAccidentee();
    const std::optional<core::Path> reference =
        core::findPath(grille, {.combatant = HEROS}, {7, 2});
    ASSERT_TRUE(reference.has_value());
    for (int essai = 0; essai < 100; ++essai) {
        const core::BattleGrid copie = grilleAccidentee();
        const std::optional<core::Path> chemin =
            core::findPath(copie, {.combatant = HEROS}, {7, 2});
        ASSERT_TRUE(chemin.has_value());
        EXPECT_EQ(chemin->steps, reference->steps);
        EXPECT_EQ(chemin->cost, reference->cost);
    }
}

/**
 * @brief Le chemin suit la droite entre le depart et l'arrivee : il ne monte pas pour redescendre.
 * \castest{<b>Sur une grille ouverte, le chemin retenu parmi ceux de meme cout est le plus proche
 * de la droite depart-arrivee, et reste dans la boite qui les englobe.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Grille ouverte 11x11, heros au centre (5,5).<br/>2. Demander le chemin vers (9,3),
 * en haut a droite, par l'aire et par A*.<br/>3. Verifier toute destination de l'aire.<br/>
 * \tattendu Vers (9,3) : (6,4) (7,4) (8,3) (9,3), jamais (8,2) ; vers toute destination, aucun pas
 * ne sort du rectangle entre le depart et l'arrivee.
 * }
 */
TEST(PathfindingTest, LeCheminSuitLaDroite) {
    const core::BattleGrid grille = grilleOuverte(11);
    const core::ReachableArea aire(grille, {.combatant = HEROS}, 6);

    const std::optional<core::Path> hautDroite = aire.pathTo({9, 3});
    ASSERT_TRUE(hautDroite.has_value());
    EXPECT_EQ(hautDroite->steps, (std::vector<core::GridPosition>{{6, 4}, {7, 4}, {8, 3}, {9, 3}}))
        << "l'ancien departage par plus petit indice montait en (8,2) avant de redescendre";
    EXPECT_EQ(core::findPath(grille, {.combatant = HEROS}, {9, 3})->steps, hautDroite->steps);

    for (const core::GridPosition destination : aire.destinations()) {
        const std::optional<core::Path> chemin = aire.pathTo(destination);
        ASSERT_TRUE(chemin.has_value());
        const int colonneMin = std::min(5, destination.column);
        const int colonneMax = std::max(5, destination.column);
        const int ligneMin = std::min(5, destination.row);
        const int ligneMax = std::max(5, destination.row);
        for (const core::GridPosition pas : chemin->steps) {
            EXPECT_GE(pas.column, colonneMin)
                << "vers " << destination.column << "," << destination.row;
            EXPECT_LE(pas.column, colonneMax)
                << "vers " << destination.column << "," << destination.row;
            EXPECT_GE(pas.row, ligneMin) << "vers " << destination.column << "," << destination.row;
            EXPECT_LE(pas.row, ligneMax) << "vers " << destination.column << "," << destination.row;
        }
    }
}

/**
 * @brief A* et l'aire atteignable rendent le meme chemin vers toute case atteignable.
 * \castest{<b>findPath et ReachableArea::pathTo rendent le meme chemin.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Grille accidentee (mur en L, boue).<br/>2. Calculer l'aire pour un budget
 * de 12.<br/>3. Pour chaque destination, comparer pathTo a findPath.<br/>
 * \tattendu Memes cases, meme cout, et chaque pas est une case voisine du precedent.
 * }
 */
TEST(PathfindingTest, LAireEtAStarRendentLeMemeChemin) {
    const core::BattleGrid grille = grilleAccidentee();
    const core::ReachableArea aire(grille, {.combatant = HEROS}, 12);
    ASSERT_FALSE(aire.destinations().empty());

    for (const core::GridPosition destination : aire.destinations()) {
        const std::optional<core::Path> parAire = aire.pathTo(destination);
        const std::optional<core::Path> parAStar =
            core::findPath(grille, {.combatant = HEROS}, destination);
        ASSERT_TRUE(parAire.has_value());
        ASSERT_TRUE(parAStar.has_value());
        EXPECT_EQ(parAire->steps, parAStar->steps)
            << "destination (" << destination.column << "," << destination.row << ")";
        EXPECT_EQ(parAire->cost, parAStar->cost);
        EXPECT_EQ(aire.costTo(destination), parAire->cost);

        core::GridPosition precedente = aire.origin();
        for (const core::GridPosition pas : parAire->steps) {
            EXPECT_EQ(tchebychev(pas, precedente), 1);
            precedente = pas;
        }
    }
}

/**
 * @brief Un chemin impossible est refuse, et une destination hors de l'aire l'est aussi.
 * \castest{<b>Un chemin impossible est refuse.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Grille coupee en deux par un mur plein.<br/>2. Demander un chemin de l'autre cote,
 * un chemin vers un mur, un chemin pour un combattant absent.<br/>
 * \tattendu Aucun chemin dans les trois cas ; pathTo refuse aussi le point de depart.
 * }
 */
TEST(PathfindingTest, UnCheminImpossibleEstRefuse) {
    core::TileMap collision(5, 5);
    for (int row = 0; row < 5; ++row) {
        collision.setTile(2, row, core::TileType::Wall);
    }
    core::BattleGrid grille(collision);
    ASSERT_EQ(grille.place(HEROS, {0, 2}), core::PlacementResult::Placed);

    EXPECT_FALSE(core::findPath(grille, {.combatant = HEROS}, {4, 2}).has_value());
    EXPECT_FALSE(core::findPath(grille, {.combatant = HEROS}, {2, 2}).has_value());
    EXPECT_FALSE(core::findPath(grille, {.combatant = ENNEMI}, {1, 2}).has_value());

    const core::ReachableArea aire(grille, {.combatant = HEROS}, 20);
    EXPECT_FALSE(aire.pathTo({0, 2}).has_value());
    EXPECT_FALSE(aire.pathTo({4, 2}).has_value());
    EXPECT_EQ(aire.destinations().size(), 9U);
    EXPECT_TRUE(core::ReachableArea(grille, {.combatant = ENNEMI}, 20).destinations().empty());
}

/**
 * @brief Un volant survole l'eau profonde et ignore la boue, mais pas les murs.
 * \castest{<b>Un volant survole les obstacles de sol, pas les murs.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Couloir 5x3 : colonne 2 en eau profonde, case (1,1) en boue, ligne 0 murée.<br/>2.
 * Calculer l'aire du meme combattant au sol, puis en vol.<br/>
 * \tattendu Au sol, l'autre rive est inaccessible et la boue coute 2 ; en vol, l'autre rive est
 * atteinte et la boue coute 1 ; la ligne muree reste hors d'atteinte dans les deux cas.
 * }
 */
TEST(PathfindingTest, UnVolantSurvoleLesObstaclesDeSol) {
    core::TileMap collision(5, 3);
    for (int column = 0; column < 5; ++column) {
        collision.setTile(column, 0, core::TileType::Wall);
    }
    collision.setTile(2, 1, core::TileType::DeepWater);
    collision.setTile(2, 2, core::TileType::DeepWater);
    core::BattleGrid grille(collision);
    grille.setDifficult({1, 1}, true);
    ASSERT_EQ(grille.place(HEROS, {0, 1}), core::PlacementResult::Placed);

    const core::ReachableArea marche(grille, {.combatant = HEROS}, 6);
    EXPECT_FALSE(marche.canEndAt({3, 1}));
    EXPECT_EQ(marche.costTo({1, 1}), 2);

    const core::Mover volant{.combatant = HEROS, .locomotion = core::Locomotion::Fly};
    const core::ReachableArea vol(grille, volant, 6);
    EXPECT_TRUE(vol.canEndAt({3, 1}));
    EXPECT_EQ(vol.costTo({1, 1}), 1);
    EXPECT_TRUE(vol.canEndAt({2, 1}))
        << "un volant se tient en vol stationnaire au-dessus de l'eau";
    EXPECT_FALSE(vol.costTo({1, 0}).has_value());
}

/**
 * @brief Une grande creature ne passe pas par un couloir d'une case.
 * \castest{<b>Une creature 2x2 ne passe pas par un couloir d'une case.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Salle 6x6 coupee par un mur en colonne 3, percee d'une seule case en (3,2).<br/>2.
 * Calculer l'aire d'un combattant 1x1, puis d'un 2x2, au budget 10.<br/>
 * \tattendu Le 1x1 passe de l'autre cote ; le 2x2 n'y parvient pas, et ses destinations sont
 * toutes des places ou son emprise tient.
 * }
 */
TEST(PathfindingTest, UneGrandeCreatureNePassePasParUnCouloirEtroit) {
    core::TileMap collision(6, 6);
    for (int row = 0; row < 6; ++row) {
        if (row != 2) {
            collision.setTile(3, row, core::TileType::Wall);
        }
    }
    core::BattleGrid grille(collision);
    ASSERT_EQ(grille.place(HEROS, {0, 0}), core::PlacementResult::Placed);
    ASSERT_EQ(grille.place(ENNEMI, {0, 3}, 2), core::PlacementResult::Placed);

    EXPECT_TRUE(core::ReachableArea(grille, {.combatant = HEROS}, 10).canEndAt({5, 2}));

    const core::ReachableArea ours(grille, {.combatant = ENNEMI}, 10);
    ASSERT_FALSE(ours.destinations().empty());
    for (const core::GridPosition place : ours.destinations()) {
        EXPECT_LT(place.column, 3) << "le 2x2 est passe de l'autre cote du mur";
        EXPECT_TRUE(grille.canStand(place, 2, ENNEMI));
    }
}

/**
 * @brief Sur deux cents cartes tirees d'une graine fixe, A* et l'aire rendent toujours le meme
 * chemin.
 * \castest{<b>Sur deux cents cartes aleatoires a graine fixe, A* et l'aire s'accordent.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Tirer deux cents grilles 12x9 (graine fixe) : murs, eau profonde, boue, un allie a
 * traverser.<br/>2. Pour chaque destination de l'aire au budget 14, comparer pathTo et
 * findPath.<br/>
 * \tattendu Chemins et couts identiques partout : le departage ne depend pas de l'algorithme.
 * }
 */
TEST(PathfindingTest, SurDesCartesAleatoiresAStarEtLAireSAccordent) {
    std::mt19937 tirage(19);
    std::uniform_int_distribution<int> de(0, 99);
    int comparaisons = 0;
    for (int carte = 0; carte < 200; ++carte) {
        core::TileMap collision(12, 9);
        for (int row = 0; row < 9; ++row) {
            for (int column = 0; column < 12; ++column) {
                const int valeur = de(tirage);
                if (valeur < 18) {
                    collision.setTile(column, row, core::TileType::Wall);
                } else if (valeur < 24) {
                    collision.setTile(column, row, core::TileType::DeepWater);
                }
            }
        }
        collision.setTile(1, 1, core::TileType::Grass);
        collision.setTile(2, 1, core::TileType::Grass);
        core::BattleGrid grille(collision);
        for (int row = 0; row < 9; ++row) {
            for (int column = 0; column < 12; ++column) {
                if (de(tirage) < 20) {
                    grille.setDifficult({column, row}, true);
                }
            }
        }
        ASSERT_EQ(grille.place(HEROS, {1, 1}), core::PlacementResult::Placed);
        ASSERT_EQ(grille.place(ALLIE, {2, 1}), core::PlacementResult::Placed);
        const core::Locomotion locomotion =
            carte % 3 == 0 ? core::Locomotion::Fly : core::Locomotion::Walk;
        const core::Mover heros{
            .combatant = HEROS,
            .locomotion = locomotion,
            .canPassThrough = [](core::CombatantId autre) { return autre == ALLIE; }};

        const core::ReachableArea aire(grille, heros, 14);
        for (const core::GridPosition destination : aire.destinations()) {
            const std::optional<core::Path> parAire = aire.pathTo(destination);
            const std::optional<core::Path> parAStar = core::findPath(grille, heros, destination);
            ASSERT_TRUE(parAire.has_value());
            ASSERT_TRUE(parAStar.has_value());
            EXPECT_EQ(parAire->steps, parAStar->steps)
                << "carte " << carte << ", destination (" << destination.column << ","
                << destination.row << ")";
            EXPECT_EQ(parAire->cost, parAStar->cost);
            ++comparaisons;
        }
    }
    EXPECT_GT(comparaisons, 2000) << "les cartes tirees doivent laisser de la place ou aller";
}
