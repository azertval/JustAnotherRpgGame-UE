// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/World/CombatZone.h"

#include <algorithm>
#include <cstdint>
#include <optional>
#include <utility>
#include <variant>

#include "Core/Combat/Arena.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"

namespace core {

namespace {

[[nodiscard]] std::string texteDe(const MapEntity& entite, std::string_view cle) {
    const auto trouvee = entite.properties.find(std::string{cle});
    if (trouvee == entite.properties.end()) {
        return {};
    }
    const std::string* texte = std::get_if<std::string>(&trouvee->second);
    return texte != nullptr ? *texte : std::string{};
}

// Un entier de propriete, ou 0 : une taille ecrite en texte est une saisie fautive, pas une taille
// a deviner -- la zone sera signalee degeneree.
[[nodiscard]] int entierDe(const MapEntity& entite, std::string_view cle) {
    const auto trouvee = entite.properties.find(std::string{cle});
    if (trouvee == entite.properties.end()) {
        return 0;
    }
    const std::int64_t* entier = std::get_if<std::int64_t>(&trouvee->second);
    return entier != nullptr ? static_cast<int>(*entier) : 0;
}

// La grille decoupee sur la zone : les cases du dehors n'y sont pas.
[[nodiscard]] TileMap decouper(const TileMap& source, const CombatZone& zone) {
    TileMap grille{std::max(1, zone.columns), std::max(1, zone.rows)};
    for (int ligne = 0; ligne < grille.height(); ++ligne) {
        for (int colonne = 0; colonne < grille.width(); ++colonne) {
            const int x = zone.origin.column + colonne;
            const int y = zone.origin.row + ligne;
            if (source.inBounds(x, y)) {
                grille.setTile(colonne, ligne, source.tile(x, y));
            }
        }
    }
    return grille;
}

}  // namespace

bool CombatZone::contains(GridPosition cell) const noexcept {
    return cell.column >= origin.column && cell.row >= origin.row &&
           cell.column < origin.column + columns && cell.row < origin.row + rows;
}

CombatZone combatZoneOf(const MapEntity& entity) {
    return CombatZone{.name = texteDe(entity, COMBAT_ZONE_NAME_PROPERTY),
                      .origin = entity.position,
                      .columns = entierDe(entity, COMBAT_ZONE_WIDTH_PROPERTY),
                      .rows = entierDe(entity, COMBAT_ZONE_HEIGHT_PROPERTY)};
}

std::vector<CombatZone> combatZonesOf(const Level& level) {
    std::vector<CombatZone> zones;
    for (const MapEntity& entite : level.entities()) {
        if (entite.type == COMBAT_ZONE_ENTITY_TYPE) {
            zones.push_back(combatZoneOf(entite));
        }
    }
    return zones;
}

namespace {

// Ce qui empeche la zone d'etre une grille tactique, avant de compter ses cases : une taille nulle,
// ou un debord de la carte.
[[nodiscard]] std::optional<WorldIssueCode> formeFautive(const TileMap& collision,
                                                         const CombatZone& zone) {
    if (zone.columns <= 0 || zone.rows <= 0) {
        return WorldIssueCode::CombatZoneDegenerate;
    }
    if (!collision.inBounds(zone.origin.column, zone.origin.row) ||
        !collision.inBounds(zone.origin.column + zone.columns - 1,
                            zone.origin.row + zone.rows - 1)) {
        return WorldIssueCode::CombatZoneOutOfBounds;
    }
    return std::nullopt;
}

// Les cases de la zone posees sur la carte, libres puis pleines : meme une zone qui deborde, pour
// que l'editeur montre sa partie posee pendant qu'on la ramene.
void releverCases(const TileMap& collision, CombatZoneTerrain& verdict) {
    const CombatZone& zone = verdict.zone;
    for (int ligne = 0; ligne < std::max(zone.rows, 0); ++ligne) {
        for (int colonne = 0; colonne < std::max(zone.columns, 0); ++colonne) {
            const GridPosition cell{.column = zone.origin.column + colonne,
                                    .row = zone.origin.row + ligne};
            if (collision.inBounds(cell.column, cell.row)) {
                (collision.isSolid(cell.column, cell.row) ? verdict.blockedCells
                                                          : verdict.freeCells)
                    .push_back(cell);
            }
        }
    }
}

[[nodiscard]] CombatZoneTerrain analyserZone(const TileMap& collision,
                                             const std::vector<MapEntity>& entities,
                                             std::size_t rang) {
    CombatZoneTerrain verdict{.entityIndex = rang,
                              .zone = combatZoneOf(entities[rang]),
                              .freeCells = {},
                              .blockedCells = {},
                              .entriesInside = {},
                              .entriesOutside = {},
                              .issue = std::nullopt};
    for (std::size_t autre = 0; autre < entities.size(); ++autre) {
        if (entities[autre].type == ARENA_ENTRY_ENTITY_TYPE) {
            (verdict.zone.contains(entities[autre].position) ? verdict.entriesInside
                                                             : verdict.entriesOutside)
                .push_back(autre);
        }
    }
    verdict.issue = formeFautive(collision, verdict.zone);
    releverCases(collision, verdict);
    // Une zone entierement pleine n'est pas un terrain tactique : personne ne peut s'y poser.
    if (!verdict.issue && verdict.freeCells.empty()) {
        verdict.issue = WorldIssueCode::CombatZoneBlocked;
    }
    return verdict;
}

}  // namespace

std::vector<CombatZoneTerrain> analyzeCombatZones(const TileMap& collision,
                                                  const std::vector<MapEntity>& entities) {
    std::vector<CombatZoneTerrain> verdicts;
    for (std::size_t rang = 0; rang < entities.size(); ++rang) {
        if (entities[rang].type == COMBAT_ZONE_ENTITY_TYPE) {
            verdicts.push_back(analyserZone(collision, entities, rang));
        }
    }
    return verdicts;
}

const CombatZone* findCombatZone(const std::vector<CombatZone>& zones, std::string_view name) {
    if (zones.empty()) {
        return nullptr;
    }
    if (name.empty()) {
        return &zones.front();
    }
    const auto trouvee = std::ranges::find(zones, name, &CombatZone::name);
    return trouvee != zones.end() ? &*trouvee : nullptr;
}

std::vector<WorldIssue> validateCombatZones(std::string_view mapId, const Level& level) {
    std::vector<WorldIssue> defauts;
    for (const CombatZoneTerrain& verdict : analyzeCombatZones(level.tileMap(), level.entities())) {
        if (verdict.issue) {
            defauts.push_back(WorldIssue{.mapId = std::string{mapId},
                                         .position = verdict.zone.origin,
                                         .code = *verdict.issue,
                                         .value = verdict.zone.name});
        }
    }
    return defauts;
}

Level cropLevelToZone(const Level& level, const CombatZone& zone) {
    // Une grille de combat tient dans l'ecran : c'est tout l'interet de la borner.
    LevelData reduite{.name = level.name(),
                      .tileMap = decouper(level.tileMap(), zone),
                      .layers = {},
                      .entities = {},
                      .entry = {}};
    const auto translater = [&zone](GridPosition cell) {
        return GridPosition{.column = cell.column - zone.origin.column,
                            .row = cell.row - zone.origin.row};
    };

    for (const TileLayer& couche : level.layers()) {
        // La grille racine est promue en tete des couches par le chargeur : la redecouper ici en
        // ferait une seconde copie, et la carte reduite porterait deux fois sa collision.
        if (couche.kind == LayerKind::Collision || couche.kind == LayerKind::Legacy) {
            continue;
        }
        TileLayer decoupee{.name = couche.name,
                           .kind = couche.kind,
                           .tiles = decouper(couche.tiles, zone),
                           .properties = couche.properties,
                           .floor = couche.floor};
        // Les pieces et les hauteurs suivent leurs cases : une arene decoupee garde son habillage.
        for (int ligne = 0; ligne < zone.rows; ++ligne) {
            for (int colonne = 0; colonne < zone.columns; ++colonne) {
                const int source = zone.origin.column + colonne;
                const int sourceLigne = zone.origin.row + ligne;
                decoupee.setPiece(colonne, ligne, std::string{couche.pieceAt(source, sourceLigne)});
                decoupee.setElevation(colonne, ligne, couche.elevationAt(source, sourceLigne));
            }
        }
        reduite.layers.push_back(std::move(decoupee));
    }

    for (const MapEntity& entite : level.entities()) {
        if (!zone.contains(entite.position)) {
            continue;
        }
        MapEntity translatee = entite;
        translatee.position = translater(entite.position);
        translatee.cells.clear();
        for (const GridPosition cell : entite.cells) {
            if (zone.contains(cell)) {
                translatee.cells.push_back(translater(cell));
            }
        }
        reduite.entities.push_back(std::move(translatee));
    }

    for (const GridPosition cell : level.forcedCollision()) {
        if (zone.contains(cell)) {
            reduite.forcedCollision.push_back(translater(cell));
        }
    }

    // L'entree de la carte reduite : celle de la carte si elle est dans la zone, son coin sinon.
    // Une grille de combat ne s'en sert pas -- l'arene pose les combattants sur leurs points
    // d'entree --, mais un champ menteur finirait par etre lu.
    if (zone.contains(level.entry())) {
        reduite.entry = GridPosition{.column = level.entry().column - zone.origin.column,
                                     .row = level.entry().row - zone.origin.row};
    }

    return Level{std::move(reduite)};
}

}  // namespace core
