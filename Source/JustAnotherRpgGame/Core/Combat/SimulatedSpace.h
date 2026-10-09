// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/SimulatedSpace.h
 * @brief L'espace de combat simulé : un plan borné, des boîtes, des plateaux, du terrain
 *        difficile (`LOT-1017`, D-50). Pour les tests et la simulation de la série, sans moteur.
 *
 * ## Ce qu'il simule
 *
 * - **Des boîtes** alignées sur les axes : un mur, un tonneau, une herse. Chacune dit si elle
 *   arrête le déplacement, à quelle hauteur elle monte, et l'abri qu'elle donne (une boîte à abri
 *   total arrête la vue, comme un mur).
 * - **Des plateaux** : une hauteur de sol sur un rectangle ; la terrasse de la carte d'essai. Le
 *   sol est à 0 ailleurs. Un plateau se monte par ses bords, sans rampe : la simulation ne joue pas
 *   la pente, c'est au moteur de le faire (maillage de navigation).
 * - **Du terrain difficile** sur un rectangle : y entrer coûte double au sol.
 * - **De l'eau profonde** sur un rectangle : infranchissable au sol, survolée.
 *
 * ## Le chemin
 *
 * Un Dijkstra sur un **réseau régulier** — pas de `SIMULATION_STEP` (0,5 m) par défaut —, huit
 * voisins, coût euclidien, obstacles élargis du rayon du mobile. Le réseau est un détail de la
 * simulation, pas une règle : le moteur trace sur son maillage de navigation. La destination
 * exacte termine le chemin si le dernier pas est dégagé. À coût égal, le prédécesseur d'indice le
 * plus petit : deux exécutions donnent le même chemin. Ce que la carte oppose à un mobile d'un
 * rayon donné se calcule une fois, au demi-pas, et se garde : seuls les combattants se relisent à
 * chaque question.
 *
 * ## Depuis une carte en tuiles
 *
 * `fromTileMap` pose une boîte pleine par suite de cases solides d'une même ligne — de l'eau
 * profonde pour l'eau profonde et la falaise, que le vol franchit et que le regard traverse —, sur
 * un réseau à la **demi-case** (0,75 m) : le centre et les coins de chaque case en sont des nœuds,
 * et une créature M passe une porte d'une case. `fromLevel` y ajoute le terrain difficile que les
 * zones de la carte déclarent (`difficultTerrain`, décision D13 de l'éditeur). Les cartes et les
 * tests écrits sur la grille de collision se rejouent en mètres sans rien redessiner.
 */

#include <cstddef>
#include <optional>
#include <span>
#include <utility>
#include <vector>

#include "Core/Combat/CombatSpace.h"

namespace core {

class Level;
class TileMap;

/// @brief Le pas du réseau de la simulation, en mètres, par défaut : un tiers de case.
inline constexpr float SIMULATION_STEP = 0.5f;

/// @brief Le pas du réseau d'un espace lu d'une carte en tuiles : la demi-case.
inline constexpr float TILE_MAP_STEP = METERS_PER_TILE / 2.0f;

/// @brief Un rectangle au sol, bords compris.
struct GroundRect {
    float minX = 0.0f;
    float minY = 0.0f;
    float maxX = 0.0f;
    float maxY = 0.0f;

    [[nodiscard]] bool contains(float x, float y) const noexcept {
        return x >= minX && x <= maxX && y >= minY && y <= maxY;
    }
};

/// @brief Une boîte posée sur le plan.
struct Box {
    GroundRect rect;
    /// La hauteur de la boîte, depuis le sol.
    float height = 3.0f;
    /// Vrai si elle arrête le déplacement, au sol comme en vol.
    bool blocksMovement = true;
    /// L'abri qu'elle donne ; `Cover::Total` arrête la vue.
    Cover cover = Cover::Total;
};

class SimulatedSpace : public CombatSpace {
public:
    /// @brief Un plan de @p width × @p height mètres, vide, au sol à 0, sur un réseau de pas
    /// @p step.
    SimulatedSpace(float width, float height, float step = SIMULATION_STEP);

    /**
     * @brief Une boîte pleine de 3 m par suite de cases solides de @p collision, ligne par
     *        ligne ; les cases font 1,50 m, le réseau est à la demi-case.
     */
    [[nodiscard]] static SimulatedSpace fromTileMap(const TileMap& collision);

    /**
     * @brief L'espace de @p level sur @p collision — sa grille de collision, ou une grille qui en
     *        dérive —, plus le terrain difficile de ses zones : les couches à propriétés et les
     *        entités `zone` qui portent `difficultTerrain: true`, case par case.
     */
    [[nodiscard]] static SimulatedSpace fromLevel(const Level& level, const TileMap& collision);

    void addBox(Box box);
    /// @brief Retire la boîte d'indice @p index — une structure détruite ; faux s'il n'y en a pas.
    bool removeBox(std::size_t index);
    void addPlatform(GroundRect rect, float height);
    void addDifficult(GroundRect rect);
    void addDeepWater(GroundRect rect);

    [[nodiscard]] float width() const noexcept {
        return _width;
    }
    [[nodiscard]] float height() const noexcept {
        return _height;
    }
    [[nodiscard]] float step() const noexcept {
        return _step;
    }
    [[nodiscard]] const std::vector<Box>& boxes() const noexcept {
        return _boxes;
    }

    /// @brief Vrai si entrer là coûte double au sol.
    [[nodiscard]] bool isDifficult(float x, float y) const noexcept;

    // --- CombatSpace ---------------------------------------------------------------------------

    [[nodiscard]] float groundHeight(float x, float y) const override;
    [[nodiscard]] bool isClear(const Volume& volume, Locomotion locomotion) const override;
    [[nodiscard]] bool lineOfSight(Meters3 from, Meters3 to) const override;
    [[nodiscard]] std::optional<Route> route(const RouteQuery& query) const override;
    [[nodiscard]] std::vector<Destination> candidates(const RouteQuery& query) const override;

private:
    struct Node {
        int column = 0;
        int row = 0;
    };
    struct Search {
        std::vector<float> cost;
        std::vector<int> previous;
    };
    /// Ce que la carte laisse libre, au demi-pas, pour un rayon et une manière de se déplacer.
    struct Clearance {
        float radius = 0.0f;
        Locomotion locomotion = Locomotion::Walk;
        std::vector<bool> clear;
    };

    [[nodiscard]] int columns() const noexcept;
    [[nodiscard]] int rows() const noexcept;
    [[nodiscard]] Meters3 pointOf(Node node) const noexcept;
    [[nodiscard]] Node nearestNode(Meters3 point) const noexcept;
    [[nodiscard]] bool standable(Meters3 point, const RouteQuery& query) const;
    [[nodiscard]] bool passage(Meters3 from, Meters3 to, const RouteQuery& query) const;
    /// Le facteur du pas @p from — @p to : 2 si son milieu est en terrain difficile, au sol, ou
    /// dans l'espace d'un corps traversé.
    [[nodiscard]] float entryFactor(Meters3 from, Meters3 to, const RouteQuery& query) const;
    [[nodiscard]] Search explore(const RouteQuery& query, float limit) const;
    [[nodiscard]] const Clearance& clearanceFor(float radius, Locomotion locomotion) const;
    /// Vrai si la carte seule laisse le mobile se tenir au point ; lu au demi-pas s'il y tombe.
    [[nodiscard]] bool staticallyClear(Meters3 point, const RouteQuery& query) const;
    /// Le chemin, départ exclu, jusqu'au nœud @p index de @p search.
    [[nodiscard]] Route routeTo(const Search& search, int startIndex, int index) const;

    float _width;
    float _height;
    float _step;
    std::vector<Box> _boxes;
    std::vector<std::pair<GroundRect, float>> _platforms;
    std::vector<GroundRect> _difficult;
    std::vector<GroundRect> _water;
    mutable std::vector<Clearance> _clearances;
};

}  // namespace core
