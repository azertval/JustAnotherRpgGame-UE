// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/PartyDeployment.h"

#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <tuple>
#include <utility>
#include <variant>

#include "Core/Combat/Arena.h"
#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/CombatTransition.h"
#include "Core/Combat/SimulatedSpace.h"
#include "Core/Combat/TacticalTerrain.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/World/CombatZone.h"

namespace core {

namespace {

[[nodiscard]] CreatureSize tailleDe(const std::string& creatureId, const Bestiary* bestiary) {
    if (bestiary == nullptr) {
        return CreatureSize::Medium;
    }
    const Creature* creature = bestiary->find(creatureId);
    return creature == nullptr ? CreatureSize::Medium : creature->size;
}

[[nodiscard]] int distance(GridPosition a, GridPosition b) noexcept {
    return std::max(std::abs(a.column - b.column), std::abs(a.row - b.row));
}

// L'ordre de lecture : ligne, puis colonne -- deterministe, donc rejouable.
[[nodiscard]] bool avant(GridPosition a, GridPosition b) noexcept {
    return std::tie(a.row, a.column) < std::tie(b.row, b.column);
}

// La distance de @p cell au rectangle de @p zone ; 0 dedans.
[[nodiscard]] int distanceALaZone(const CombatZone& zone, GridPosition cell) noexcept {
    const auto ecart = [](int valeur, int debut, int taille) {
        if (valeur < debut) {
            return debut - valeur;
        }
        const int fin = debut + std::max(taille, 1) - 1;
        return valeur > fin ? valeur - fin : 0;
    };
    return std::max(ecart(cell.column, zone.origin.column, zone.columns),
                    ecart(cell.row, zone.origin.row, zone.rows));
}

// La zone de la rencontre : celle du marqueur, sinon la plus proche ; a egalite, la premiere.
[[nodiscard]] const CombatZoneTerrain* zoneDe(const std::vector<CombatZoneTerrain>& zones,
                                              GridPosition trigger) {
    const CombatZoneTerrain* choisie = nullptr;
    int meilleure = std::numeric_limits<int>::max();
    for (const CombatZoneTerrain& zone : zones) {
        const int d = distanceALaZone(zone.zone, trigger);
        if (d < meilleure) {
            choisie = &zone;
            meilleure = d;
        }
    }
    return choisie;
}

// La collision reduite a la zone, que l'appelant a verifiee posee sur la carte : la grille que
// `cropLevelToZone` donne au combat.
[[nodiscard]] TileMap decouper(const TileMap& collision, const CombatZone& zone) {
    TileMap grille{zone.columns, zone.rows};
    for (int ligne = 0; ligne < zone.rows; ++ligne) {
        for (int colonne = 0; colonne < zone.columns; ++colonne) {
            grille.setTile(colonne, ligne,
                           collision.tile(zone.origin.column + colonne, zone.origin.row + ligne));
        }
    }
    return grille;
}

// Les entrees d'arene alliees de la zone, par rang puis ordre de lecture (`arenaEntryPoints`).
[[nodiscard]] std::vector<GridPosition> entreesAlliees(const std::vector<MapEntity>& entities,
                                                       const CombatZone& zone) {
    std::vector<std::pair<std::int64_t, GridPosition>> entrees;
    for (const MapEntity& entite : entities) {
        if (entite.type != ARENA_ENTRY_ENTITY_TYPE || !zone.contains(entite.position)) {
            continue;
        }
        const auto camp = entite.properties.find(std::string{ARENA_SIDE_PROPERTY});
        const std::string* texte =
            camp == entite.properties.end() ? nullptr : std::get_if<std::string>(&camp->second);
        if (texte == nullptr || *texte != "allies") {
            continue;
        }
        const auto rang = entite.properties.find(std::string{ARENA_RANK_PROPERTY});
        const std::int64_t* entier =
            rang == entite.properties.end() ? nullptr : std::get_if<std::int64_t>(&rang->second);
        entrees.emplace_back(entier != nullptr ? *entier : 0, entite.position);
    }
    std::ranges::sort(entrees, [](const auto& a, const auto& b) {
        return a.first != b.first ? a.first < b.first : avant(a.second, b.second);
    });
    std::vector<GridPosition> cases;
    for (const auto& [rang, cell] : entrees) {
        cases.push_back(cell);
    }
    return cases;
}

// Les cases de la zone dont le centre se rejoint a pied depuis celui de @p depart, depart compris,
// en cases de la zone, triees. Vide si le depart ne se tient pas.
[[nodiscard]] std::vector<GridPosition> atteignables(const TileMap& grille,
                                                     const SimulatedSpace& espace,
                                                     GridPosition depart) {
    const Volume arpenteur = volumeOf(tileCenter(depart), CreatureSize::Medium);
    if (!espace.isClear(arpenteur, Locomotion::Walk)) {
        return {};
    }
    // Sans budget : on cherche ce qui est relie, pas ce qu'un tour parcourt.
    const RouteQuery requete{.mover = arpenteur, .destination = {}, .budget = -1.0f};
    std::vector<GridPosition> cases;
    for (const Destination& place : espace.candidates(requete)) {
        const GridPosition cell = tileOf(place.point);
        if (cell.column < 0 || cell.row < 0 || cell.column >= grille.width() ||
            cell.row >= grille.height() || groundDistance(tileCenter(cell), place.point) > 1e-3f) {
            continue;
        }
        cases.push_back(cell);
    }
    std::ranges::sort(cases, avant);
    return cases;
}

// Vrai si un des volumes poses couvre le centre de la case.
[[nodiscard]] bool occupee(const std::vector<Volume>& poses, GridPosition cell) {
    const Meters3 centre = tileCenter(cell);
    return std::ranges::any_of(poses, [&](const Volume& volume) {
        return groundDistance(centre, volume.base) < volume.radius - 1e-3f;
    });
}

// La case libre de la zone la plus proche du marqueur : d'ou l'on arpente quand le marqueur est
// dehors ou dans un mur.
[[nodiscard]] std::optional<GridPosition> departDe(const CombatZoneTerrain& zone,
                                                   GridPosition trigger) {
    std::optional<GridPosition> meilleure;
    for (const GridPosition cell : zone.freeCells) {
        if (!meilleure || distance(cell, trigger) < distance(*meilleure, trigger)) {
            meilleure = cell;
        }
    }
    return meilleure;
}

void deployer(const TileMap& collision, const std::vector<MapEntity>& entities,
              const CombatZoneTerrain& zone, const Bestiary* bestiary, PartyDeployment& verdict) {
    const CombatZone& rectangle = zone.zone;
    const TileMap grille = decouper(collision, rectangle);
    const auto versZone = [&rectangle](GridPosition cell) {
        return GridPosition{.column = cell.column - rectangle.origin.column,
                            .row = cell.row - rectangle.origin.row};
    };
    const auto versCarte = [&rectangle](GridPosition cell) {
        return GridPosition{.column = cell.column + rectangle.origin.column,
                            .row = cell.row + rectangle.origin.row};
    };

    if (!rectangle.contains(verdict.trigger)) {
        verdict.issues.push_back({.code = DeploymentIssueCode::TriggerOutsideZone,
                                  .creatureId = {},
                                  .cell = verdict.trigger});
    }

    // La formation posee sur la zone seule, comme le montage la pose sur la carte reduite : ce
    // qui en sort est hors du combat. Un mur ou un chevauchement est dit par le terrain.
    const SimulatedSpace espace = SimulatedSpace::fromTileMap(grille);
    std::vector<Volume> posee;
    for (const CombatantPlacement& adversaire : verdict.formation) {
        const CreatureSize taille = tailleDe(adversaire.creatureId, bestiary);
        const GridPosition ancre = versZone(adversaire.position);
        const int cote = footprintSide(taille);
        if (ancre.column < 0 || ancre.row < 0 || ancre.column + cote > grille.width() ||
            ancre.row + cote > grille.height()) {
            verdict.issues.push_back({.code = DeploymentIssueCode::CombatantOutsideZone,
                                      .creatureId = adversaire.creatureId,
                                      .cell = adversaire.position});
            continue;
        }
        const Volume volume = volumeOf(tileCenter(ancre, taille), taille);
        if (espace.isClear(volume, Locomotion::Walk) &&
            std::ranges::none_of(posee,
                                 [&](const Volume& autre) { return overlap(volume, autre); })) {
            posee.push_back(volume);
        }
    }

    const std::optional<GridPosition> depart =
        rectangle.contains(verdict.trigger) &&
                !collision.isSolid(verdict.trigger.column, verdict.trigger.row)
            ? std::make_optional(verdict.trigger)
            : departDe(zone, verdict.trigger);
    const std::vector<GridPosition> reliees =
        depart ? atteignables(grille, espace, versZone(*depart)) : std::vector<GridPosition>{};
    verdict.reachableCells = static_cast<int>(reliees.size());

    // Les places du groupe : reliees a la formation, et que la formation n'occupe pas.
    std::vector<GridPosition> candidates;
    for (const GridPosition cell : reliees) {
        if (!occupee(posee, cell)) {
            candidates.push_back(versCarte(cell));
        }
    }
    const auto prendre = [&](GridPosition cell) {
        const auto trouvee = std::ranges::find(candidates, cell);
        if (trouvee == candidates.end() ||
            std::cmp_greater_equal(verdict.partyPlaces.size(), verdict.partySize)) {
            return false;
        }
        verdict.partyPlaces.push_back(cell);
        candidates.erase(trouvee);
        return true;
    };
    for (const GridPosition entree : entreesAlliees(entities, rectangle)) {
        std::ignore = prendre(entree);
    }
    // Le front oppose au marqueur, puis ses plus proches voisines.
    if (verdict.partyPlaces.empty() && !candidates.empty()) {
        const GridPosition front =
            *std::ranges::max_element(candidates, [&verdict](GridPosition a, GridPosition b) {
                const int da = distance(a, verdict.trigger);
                const int db = distance(b, verdict.trigger);
                return da != db ? da < db : avant(b, a);
            });
        std::ignore = prendre(front);
    }
    while (std::cmp_less(verdict.partyPlaces.size(), verdict.partySize) && !candidates.empty()) {
        const GridPosition ancre = verdict.partyPlaces.front();
        const GridPosition voisine =
            *std::ranges::min_element(candidates, [ancre](GridPosition a, GridPosition b) {
                const int da = distance(a, ancre);
                const int db = distance(b, ancre);
                return da != db ? da < db : avant(a, b);
            });
        std::ignore = prendre(voisine);
    }
    if (std::cmp_less(verdict.partyPlaces.size(), verdict.partySize)) {
        verdict.issues.push_back({.code = DeploymentIssueCode::PartyCannotDeploy,
                                  .creatureId = {},
                                  .cell = rectangle.origin});
    }
    if (verdict.reachableCells < verdict.requiredCells) {
        verdict.issues.push_back({.code = DeploymentIssueCode::ZoneTooNarrow,
                                  .creatureId = {},
                                  .cell = rectangle.origin});
    }
}

}  // namespace

std::vector<PartyDeployment> analyzePartyDeployment(const TileMap& collision,
                                                    const std::vector<MapEntity>& entities,
                                                    const EncounterCatalog& encounters,
                                                    const Bestiary* bestiary) {
    const std::vector<CombatZoneTerrain> zones = analyzeCombatZones(collision, entities);
    std::vector<PartyDeployment> verdicts;
    for (std::size_t index = 0; index < entities.size(); ++index) {
        // Le nom de carte n'ouvre que la cle de drapeau, dont ce verdict n'a pas l'usage.
        const std::optional<EncounterTrigger> declencheur =
            encounterTriggerFor(entities[index], "");
        if (!declencheur.has_value()) {
            continue;
        }
        const Encounter* rencontre = encounters.find(declencheur->encounterId);
        if (rencontre == nullptr) {
            continue;
        }
        PartyDeployment verdict;
        verdict.encounterIndex = index;
        verdict.encounterId = declencheur->encounterId;
        verdict.trigger = declencheur->position;
        verdict.formation = placeCombatants(*rencontre, declencheur->position);
        verdict.partySize = TACTICAL_PARTY_SIZE;
        verdict.requiredCells = (static_cast<int>(verdict.formation.size()) + verdict.partySize) *
                                TACTICAL_CELLS_PER_COMBATANT;

        const CombatZoneTerrain* zone = zoneDe(zones, verdict.trigger);
        if (zone == nullptr) {
            verdict.issues.push_back({.code = DeploymentIssueCode::NoCombatZone,
                                      .creatureId = {},
                                      .cell = verdict.trigger});
        } else {
            verdict.zoneIndex = zone->entityIndex;
            if (!zone->issue.has_value()) {
                deployer(collision, entities, *zone, bestiary, verdict);
            }
        }
        verdicts.push_back(std::move(verdict));
    }
    return verdicts;
}

}  // namespace core
