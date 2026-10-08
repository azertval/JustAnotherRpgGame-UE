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
 * Un Dijkstra sur un **réseau régulier** de pas `SIMULATION_STEP` (0,5 m), huit voisins, coût
 * euclidien, obstacles élargis du rayon du mobile. Le réseau est un détail de la simulation, pas
 * une règle : le moteur trace sur son maillage de navigation. La destination exacte termine le
 * chemin si le dernier pas est dégagé. À coût égal, le prédécesseur d'indice le plus petit : deux
 * exécutions donnent le même chemin.
 *
 * ## Depuis une carte de l'ancien format
 *
 * `fromTileMap` pose une boîte pleine par case solide : les cartes et les tests écrits sur la
 * grille de collision se rejouent en mètres sans rien redessiner.
 */

#include <cstddef>
#include <optional>
#include <span>
#include <vector>

#include "Core/Combat/CombatSpace.h"

namespace core {

class TileMap;

/// @brief Le pas du réseau de la simulation, en mètres : un tiers de case.
inline constexpr float SIMULATION_STEP = 0.5f;

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
    /// @brief Un plan de @p width × @p height mètres, vide, au sol à 0.
    SimulatedSpace(float width, float height);

    /// @brief Une boîte pleine de 3 m par case solide de @p collision ; les cases font 1,50 m.
    [[nodiscard]] static SimulatedSpace fromTileMap(const TileMap& collision);

    void addBox(Box box);
    void addPlatform(GroundRect rect, float height);
    void addDifficult(GroundRect rect);
    void addDeepWater(GroundRect rect);

    [[nodiscard]] float width() const noexcept {
        return _width;
    }
    [[nodiscard]] float height() const noexcept {
        return _height;
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
    [[nodiscard]] std::vector<Meters3> candidates(const RouteQuery& query) const override;

private:
    struct Node {
        int column = 0;
        int row = 0;
    };
    struct Search {
        std::vector<float> cost;
        std::vector<int> previous;
    };

    [[nodiscard]] int columns() const noexcept;
    [[nodiscard]] int rows() const noexcept;
    [[nodiscard]] Meters3 pointOf(Node node) const noexcept;
    [[nodiscard]] Node nearestNode(Meters3 point) const noexcept;
    [[nodiscard]] bool standable(Meters3 point, const RouteQuery& query) const;
    [[nodiscard]] bool passage(Meters3 from, Meters3 to, const RouteQuery& query) const;
    [[nodiscard]] float entryFactor(Meters3 point, const RouteQuery& query) const;
    [[nodiscard]] Search explore(const RouteQuery& query, float limit) const;

    float _width;
    float _height;
    std::vector<Box> _boxes;
    std::vector<std::pair<GroundRect, float>> _platforms;
    std::vector<GroundRect> _difficult;
    std::vector<GroundRect> _water;
};

}  // namespace core
