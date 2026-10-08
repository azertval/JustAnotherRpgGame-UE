// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <cstddef>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "Core/Levels/GridPosition.h"
#include "Core/Levels/Level.h"
#include "Core/World/WorldTravel.h"

/**
 * @file Core/World/CombatZone.h
 * @brief La **zone de combat** d'une carte : le rectangle nommé où l'on se bat, et lui seul
 *        (`EX-LVL-018`, `LOT-09`).
 *
 * ## Pourquoi une zone, et non la carte entière
 *
 * Le Colisée est un lieu : on y marche dans le hall, les couloirs, les vestiaires et les tribunes,
 * et l'on ne s'y bat pas — le livre ne fait combattre que sur le sable. Prendre la carte entière
 * pour grille tactique donnerait un affrontement de mille trois cent soixante cases dont mille
 * seraient des gradins.
 *
 * La zone est donc **déclarée sur la carte**, comme une entité que l'éditeur pose
 * (`core::COMBAT_ZONE_ENTITY_TYPE`) : sa case est le coin haut-gauche, ses propriétés donnent son
 * nom et sa taille. `core::ArenaSession` ne joue que dessus, et les cases hors zone lui sont
 * **inconnues** : c'est ce que `cropLevelToZone` garantit, en lui donnant une carte qui n'est que
 * la zone.
 */

namespace core {

/// @brief Type d'entité d'une zone de combat : le rectangle où l'on se bat.
inline constexpr std::string_view COMBAT_ZONE_ENTITY_TYPE = "combatZone";
/// @brief Propriété d'une zone : son nom, unique dans la carte — l'arène du catalogue le désigne.
inline constexpr std::string_view COMBAT_ZONE_NAME_PROPERTY = "name";
/// @brief Propriété d'une zone : sa largeur, en cases.
inline constexpr std::string_view COMBAT_ZONE_WIDTH_PROPERTY = "width";
/// @brief Propriété d'une zone : sa hauteur, en cases.
inline constexpr std::string_view COMBAT_ZONE_HEIGHT_PROPERTY = "height";

/// @brief Une zone de combat : son nom, son coin haut-gauche, sa taille.
struct CombatZone {
    std::string name;
    GridPosition origin{};
    int columns = 0;
    int rows = 0;

    /// @return Vrai si @p cell est dans la zone.
    [[nodiscard]] bool contains(GridPosition cell) const noexcept;

    [[nodiscard]] bool operator==(const CombatZone&) const = default;
};

/// @return Les zones de combat de @p level, dans l'ordre des entités.
[[nodiscard]] std::vector<CombatZone> combatZonesOf(const Level& level);

/// @return La zone de combat que déclare @p entity : son nom, sa case, sa taille (0 si elle
///         manque ou n'est pas un entier). L'appelant a vérifié le type.
[[nodiscard]] CombatZone combatZoneOf(const MapEntity& entity);

/**
 * @brief Le verdict tactique d'une zone de combat : ce que l'éditeur montre pendant qu'on la tire
 *        (`LOT-EDITOR-05`), et ce que `validateCombatZones` rapporte au chargement.
 */
struct CombatZoneTerrain {
    /// Rang de l'entité dans la liste d'entités de la carte.
    std::size_t entityIndex = 0;
    CombatZone zone;
    /// Les cases de la zone où l'on peut se tenir, triées (ligne, colonne).
    std::vector<GridPosition> freeCells;
    /// Les cases de la zone qui sont solides, triées (ligne, colonne).
    std::vector<GridPosition> blockedCells;
    /// Les entrées d'arène (`core::ARENA_ENTRY_ENTITY_TYPE`) dans la zone, par rang d'entité.
    std::vector<std::size_t> entriesInside;
    /// Les entrées d'arène hors de la zone : un combat dans cette zone ne les voit pas
    /// (`cropLevelToZone` les écarte).
    std::vector<std::size_t> entriesOutside;
    /// Ce qui empêche la zone d'être une grille tactique : `CombatZoneDegenerate`,
    /// `CombatZoneOutOfBounds` ou `CombatZoneBlocked`. Rien pour une zone jouable.
    std::optional<WorldIssueCode> issue;
};

/**
 * @brief Le verdict de chaque zone de combat de @p entities sur la collision @p collision, dans
 *        l'ordre des entités.
 *
 * Il prend une grille et des entités, et non une carte : l'éditeur le calcule sur son brouillon à
 * chaque geste, sans reconstruire de `Level`.
 */
[[nodiscard]] std::vector<CombatZoneTerrain> analyzeCombatZones(
    const TileMap& collision, const std::vector<MapEntity>& entities);

/// @return La zone nommée @p name, ou `nullptr`. Un nom vide rend la **première** zone : une carte
///         à une seule zone n'a pas à se nommer deux fois.
[[nodiscard]] const CombatZone* findCombatZone(const std::vector<CombatZone>& zones,
                                               std::string_view name);

/**
 * @brief Relève ce qui empêche une zone d'être une grille tactique (`EX-NFR-040`).
 *
 * Trois défauts, et ils se voient au **chargement**, pas au moment où le héraut lance le combat :
 * une zone dégénérée (largeur ou hauteur nulle), une zone qui déborde de la carte, une zone dont
 * aucune case n'est libre — un affrontement dans un mur.
 */
[[nodiscard]] std::vector<WorldIssue> validateCombatZones(std::string_view mapId,
                                                          const Level& level);

/**
 * @brief La carte réduite à @p zone : la grille tactique que `core::ArenaSession` prend pour
 *        terrain.
 *
 * Les cases hors zone n'y sont pas, et sont donc inconnues de la session — ce qui est exactement
 * ce qu'on veut : une créature ne doit pas pouvoir marcher du sable jusqu'aux tribunes. Les
 * entités de la zone sont **translatées** avec elle (les points d'entrée des deux camps gardent
 * leur place relative) ; celles du dehors sont écartées.
 *
 * Le cadrage de la carte réduite est `WholeLevel` : une grille de combat tient dans l'écran, c'est
 * tout l'intérêt de la borner.
 */
[[nodiscard]] Level cropLevelToZone(const Level& level, const CombatZone& zone);

}  // namespace core
