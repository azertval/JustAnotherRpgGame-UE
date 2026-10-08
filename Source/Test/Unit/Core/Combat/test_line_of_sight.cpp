// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_line_of_sight.cpp
 * @brief Tests de la ligne de vue et de l'abri (`LOT-22`, `EX-CBT-021`) : symétrie vérifiée
 * exhaustivement sur des grilles générées, cas de référence, abris qui ne s'additionnent pas.
 */

#include <cstddef>
#include <string>
#include <utility>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/BattleGrid.h"
#include "Core/Combat/LineOfSight.h"
#include "Core/Levels/TileMap.h"
#include "Core/Math/DeterministicRandom.h"

namespace {

using core::Cover;
using core::Footprint;
using core::GridPosition;

[[nodiscard]] Footprint une(int colonne, int ligne, int cote = 1) {
    return {.anchor = {.column = colonne, .row = ligne}, .side = cote};
}

/// Une grille dessinée : `#` mur, `~` eau profonde, `H` herse (abri important), `m` muret (abri
/// partiel), `P` porte fermée (abri total), `.` libre. Une chaîne par ligne.
[[nodiscard]] core::BattleGrid grilleDe(const std::vector<const char*>& lignes) {
    const int hauteur = static_cast<int>(lignes.size());
    const int largeur = static_cast<int>(std::char_traits<char>::length(lignes.front()));
    core::TileMap collision(largeur, hauteur);
    std::vector<std::pair<GridPosition, Cover>> objets;
    for (int ligne = 0; ligne < hauteur; ++ligne) {
        for (int colonne = 0; colonne < largeur; ++colonne) {
            switch (lignes[static_cast<std::size_t>(ligne)][colonne]) {
                case '#':
                    collision.setTile(colonne, ligne, core::TileType::Wall);
                    break;
                case '~':
                    collision.setTile(colonne, ligne, core::TileType::DeepWater);
                    break;
                case 'H':
                    objets.emplace_back(GridPosition{colonne, ligne}, Cover::ThreeQuarters);
                    break;
                case 'm':
                    objets.emplace_back(GridPosition{colonne, ligne}, Cover::Half);
                    break;
                case 'P':
                    objets.emplace_back(GridPosition{colonne, ligne}, Cover::Total);
                    break;
                default:
                    break;
            }
        }
    }
    core::BattleGrid grille(collision);
    for (const auto& [cellule, abri] : objets) {
        EXPECT_EQ(grille.placeObject(cellule, {.kind = "obstacle",
                                               .hitPoints = 10,
                                               .blocksMovement = true,
                                               .cover = abri,
                                               .damageTraits = {}}),
                  core::PlacementResult::Placed);
    }
    return grille;
}

/// Une grille aléatoire : murs, eau profonde, portes et herses, à la densité @p pourcent.
[[nodiscard]] core::BattleGrid grilleGeneree(core::DeterministicRandom& hasard, int cote,
                                             int pourcent) {
    core::TileMap collision(cote, cote);
    std::vector<std::pair<GridPosition, Cover>> objets;
    for (int ligne = 0; ligne < cote; ++ligne) {
        for (int colonne = 0; colonne < cote; ++colonne) {
            if (hasard.nextInt(0, 99) >= pourcent) {
                continue;
            }
            switch (hasard.nextInt(0, 5)) {
                case 0:
                    collision.setTile(colonne, ligne, core::TileType::DeepWater);
                    break;
                case 1:
                    objets.emplace_back(GridPosition{colonne, ligne}, Cover::Total);
                    break;
                case 2:
                    objets.emplace_back(GridPosition{colonne, ligne}, Cover::ThreeQuarters);
                    break;
                default:
                    collision.setTile(colonne, ligne, core::TileType::Wall);
                    break;
            }
        }
    }
    core::BattleGrid grille(collision);
    for (const auto& [cellule, abri] : objets) {
        static_cast<void>(grille.placeObject(cellule, {.kind = "obstacle",
                                                       .hitPoints = 1,
                                                       .blocksMovement = true,
                                                       .cover = abri,
                                                       .damageTraits = {}}));
    }
    return grille;
}

}  // namespace

/**
 * @brief La ligne de vue est symétrique, sur des grilles générées, pour toutes les paires.
 * \castest{<b>A voit B si et seulement si B voit A — vérifié exhaustivement sur des grilles
 * générées, pour chaque paire de points de grille et chaque paire d'emprises, 1 × 1 et 2
 * × 2.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Générer 20 grilles 5 × 5 à des densités de 10 à 55 % de murs, d'eau profonde, de
 * portes et de herses.<br/>2. Pour chaque paire ordonnée de points de grille : comparer les deux
 * sens du segment.<br/>3. Pour chaque paire ordonnée d'emprises 1 × 1, et d'emprises 2 × 2 contre
 * 1 × 1 : comparer les deux sens de la ligne de vue.<br/>4. Pour chacune : l'abri total équivaut à
 * l'absence de ligne de vue.<br/>
 * \tattendu Aucune asymétrie ; aucune divergence entre abri total et vue ; des paires vues et
 * des paires cachées dans les deux familles, pour que la vérification ne soit pas creuse.
 * }
 */
TEST(LineOfSightTest, LaVueEstSymetriqueSurDesGrillesGenerees) {
    core::DeterministicRandom hasard(2222);
    std::size_t vues = 0;
    std::size_t cachees = 0;
    std::size_t segments = 0;
    for (int essai = 0; essai < 20; ++essai) {
        const int cote = 5;
        const core::BattleGrid grille = grilleGeneree(hasard, cote, 10 + (essai % 10) * 5);

        for (int ay = 0; ay <= 2 * cote; ay += 2) {
            for (int ax = 0; ax <= 2 * cote; ax += 2) {
                for (int by = 0; by <= 2 * cote; by += 2) {
                    for (int bx = 0; bx <= 2 * cote; bx += 2) {
                        const core::GridPoint a{.x = ax, .y = ay};
                        const core::GridPoint b{.x = bx, .y = by};
                        ASSERT_EQ(core::isSightClear(grille, a, b),
                                  core::isSightClear(grille, b, a))
                            << "grille " << essai << " : (" << ax << "," << ay << ") <-> (" << bx
                            << "," << by << ")";
                        ++segments;
                    }
                }
            }
        }

        for (int cote2 : {1, 2}) {
            for (int ay = 0; ay + cote2 <= cote; ++ay) {
                for (int ax = 0; ax + cote2 <= cote; ++ax) {
                    for (int by = 0; by < cote; ++by) {
                        for (int bx = 0; bx < cote; ++bx) {
                            const Footprint a = une(ax, ay, cote2);
                            const Footprint b = une(bx, by);
                            const bool ab = core::hasLineOfSight(grille, a, b);
                            ASSERT_EQ(ab, core::hasLineOfSight(grille, b, a))
                                << "grille " << essai << " : (" << ax << "," << ay << ")x" << cote2
                                << " <-> (" << bx << "," << by << ")";
                            ASSERT_EQ(core::coverFrom(grille, a, b) == Cover::Total, !ab);
                            ASSERT_EQ(core::coverFrom(grille, b, a) == Cover::Total, !ab);
                            (ab ? vues : cachees) += 1;
                        }
                    }
                }
            }
        }
    }
    EXPECT_GT(segments, 25000U);
    EXPECT_GT(vues, 5000U);
    EXPECT_GT(cachees, 1000U);
}

/**
 * @brief Ce qui arrête la vue, et ce qui ne l'arrête pas.
 * \castest{<b>Un mur caché, un gouffre non ; le coin commun de deux murs ne laisse pas passer le
 * regard ; une porte fermée cache comme un mur.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Deux combattants alignés, un mur d'une case entre eux.<br/>2. Les mêmes, séparés par
 * une rivière d'eau profonde.<br/>3. Deux combattants en diagonale, deux murs sur les deux autres
 * cases du carré ; puis un seul mur.<br/>4. Une porte fermée entre deux combattants.<br/>
 * \tattendu Mur : pas de vue, abri total ; eau : vue, aucun abri ; deux murs en coin : pas de
 * vue ; un seul : vue ; porte : pas de vue.
 * }
 */
TEST(LineOfSightTest, CeQuiArreteLaVue) {
    const core::BattleGrid mur = grilleDe({"...", ".#.", "..."});
    EXPECT_FALSE(core::hasLineOfSight(mur, une(0, 1), une(2, 1)));
    EXPECT_EQ(core::coverFrom(mur, une(0, 1), une(2, 1)), Cover::Total);
    EXPECT_TRUE(core::hasLineOfSight(mur, une(0, 0), une(2, 0)));

    const core::BattleGrid riviere = grilleDe({"..~..", "..~..", "..~.."});
    EXPECT_TRUE(core::hasLineOfSight(riviere, une(0, 1), une(4, 1)));
    EXPECT_EQ(core::coverFrom(riviere, une(0, 1), une(4, 1)), Cover::None);

    const core::BattleGrid coin = grilleDe({".#", "#."});
    EXPECT_FALSE(core::hasLineOfSight(coin, une(0, 0), une(1, 1)));
    const core::BattleGrid demiCoin = grilleDe({".#", ".."});
    EXPECT_TRUE(core::hasLineOfSight(demiCoin, une(0, 0), une(1, 1)));

    const core::BattleGrid porte = grilleDe({"#.#", "#P#", "#.#"});
    EXPECT_FALSE(core::hasLineOfSight(porte, une(1, 0), une(1, 2)));
}

/**
 * @brief L'abri partiel, important et total, et ce qui les donne.
 * \castest{<b>Un muret et une créature interposée abritent partiellement, une herse de façon
 * importante ; un angle de mur donne l'abri selon les lignes qu'il coupe ; les abris ne
 * s'additionnent pas.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un tireur, une cible à trois cases, rien entre eux.<br/>2. Un muret, puis une herse,
 * sur la case devant la cible.<br/>3. Une créature sur cette case.<br/>4. La cible derrière un
 * angle de mur.<br/>5. La herse et une créature ensemble.<br/>
 * \tattendu Aucun abri ; partiel ; important ; partiel pour la créature ; l'angle donne le compte
 * des lignes du Guide du Maître ; herse et créature : important, le meilleur des deux, jamais
 * davantage ; bonus +2 et +5.
 * }
 */
TEST(LineOfSightTest, LesAbrisEtCeQuiLesDonne) {
    const core::BattleGrid libre = grilleDe({".....", ".....", "....."});
    EXPECT_EQ(core::coverFrom(libre, une(0, 1), une(3, 1)), Cover::None);

    const core::BattleGrid muret = grilleDe({".....", "..m..", "....."});
    EXPECT_EQ(core::coverFrom(muret, une(0, 1), une(3, 1)), Cover::Half);
    const core::BattleGrid herse = grilleDe({".....", "..H..", "....."});
    EXPECT_EQ(core::coverFrom(herse, une(0, 1), une(3, 1)), Cover::ThreeQuarters);

    const std::vector<Footprint> garde{une(2, 1)};
    EXPECT_EQ(core::coverFrom(libre, une(0, 1), une(3, 1), garde), Cover::Half);
    EXPECT_EQ(core::coverFrom(herse, une(0, 1), une(3, 1), garde), Cover::ThreeQuarters);

    // L'angle : la cible en (3, 1), le mur en (2, 1), le tireur en (0, 0). Depuis le coin (0, 0)
    // de sa case, les lignes vers le haut de la cible passent au-dessus du mur, celles vers le bas
    // le touchent : deux sur quatre, abri partiel.
    const core::BattleGrid angle = grilleDe({".....", "..#..", "....."});
    EXPECT_EQ(core::coverFrom(angle, une(0, 0), une(3, 1)), Cover::Half);
    // Depuis le seul point (0, 0) : le mur coupe les deux lignes du bas, une creature en (2, 0)
    // les deux du haut. Additionnes, ils couperaient les quatre et cacheraient la cible ; ils ne
    // s'additionnent pas.
    const core::GridPoint coin{.x = 0, .y = 0};
    const std::vector<Footprint> voisin{une(2, 0)};
    EXPECT_EQ(core::coverFromPoint(angle, coin, une(3, 1)), Cover::Half);
    EXPECT_EQ(core::coverFromPoint(libre, coin, une(3, 1), voisin), Cover::Half);
    EXPECT_EQ(core::coverFromPoint(angle, coin, une(3, 1), voisin), Cover::Half);
    EXPECT_EQ(core::coverFrom(angle, une(0, 0), une(3, 1), voisin), Cover::Half);

    EXPECT_EQ(core::coverBonus(Cover::None), 0);
    EXPECT_EQ(core::coverBonus(Cover::Half), 2);
    EXPECT_EQ(core::coverBonus(Cover::ThreeQuarters), 5);
    EXPECT_EQ(core::coverBonus(Cover::Total), 0);
}
