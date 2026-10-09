// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <array>
#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

/**
 * @file Core/Ui/MapInteractions.h
 * @brief Les **lieux cliquables** de l'écran Carte (LOT-1020), lus dans
 *        `Source/Elements/Maps/map-interactions.json` (l'atlas illustré du 7 octobre 2026).
 *
 * Chaque lieu est dessiné sur l'illustration de son **parent** (`parent`) : les régions sur le
 * monde (`world`), les lieux d'une région sur la région, les quartiers sur la ville, les
 * bâtiments sur le quartier. Un lieu qui est lui-même le parent d'autres lieux s'**ouvre** : son
 * illustration est celle où ses enfants sont dessinés. La bannière d'un lieu est son rectangle
 * `label` (x, y, largeur, hauteur), en coordonnées normalisées sur l'illustration.
 *
 * Un lieu qui déborde sur une illustration voisine y est aussi dessiné (`neighbours`) : il compte
 * alors parmi les lieux de ce parent-là, marqué voisin.
 *
 * Logique pure : aucune dépendance au moteur ; une lecture ne lève jamais.
 */

namespace core {

/// Un lieu dessiné sur une illustration.
struct MapZone {
    std::string id;
    /// Le lieu sur l'illustration duquel il est dessiné ; `world` pour le monde.
    std::string parent;
    /// L'illustration où il est dessiné, relative à `Source/Elements/Assets`.
    std::string image;
    /// Sa bannière : x, y, largeur, hauteur, de 0 à 1 sur l'illustration.
    std::array<float, 4> label{};
    /// Vrai s'il déborde ici depuis l'illustration voisine (`neighbours`).
    bool neighbour = false;
};

/// Les lieux de la carte.
struct MapInteractions {
    std::vector<MapZone> zones;
    std::vector<std::string> errors;

    /// Les lieux dessinés sur l'illustration de @p node, voisins compris.
    [[nodiscard]] std::vector<const MapZone*> childrenOf(std::string_view node) const;
    /// L'illustration de @p node : celle de ses enfants ; vide s'il n'en a pas (il ne s'ouvre pas).
    [[nodiscard]] std::string imageOf(std::string_view node) const;
    /// Le parent de @p id, là où il est dessiné en propre ; vide s'il est inconnu.
    [[nodiscard]] std::string parentOf(std::string_view id) const;
};

/// Lit `map-interactions.json`. Ne lève jamais.
[[nodiscard]] MapInteractions readMapInteractions(std::string_view json,
                                                  std::string_view origin = {});

/// Comme `readMapInteractions`, en lisant d'abord le fichier ; un fichier absent est une erreur.
[[nodiscard]] MapInteractions loadMapInteractions(const std::filesystem::path& file);

}  // namespace core
