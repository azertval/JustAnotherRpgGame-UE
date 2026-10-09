// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/TacticalTerrain.h"

#include <algorithm>
#include <cstdint>
#include <optional>
#include <utility>

#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/CombatTransition.h"
#include "Core/Combat/SimulatedSpace.h"
#include "Core/Rpg/Bestiary.h"

namespace core {

namespace {

[[nodiscard]] CreatureSize tailleDe(const std::string& creatureId, const Bestiary* bestiary) {
    if (bestiary == nullptr) {
        return CreatureSize::Medium;
    }
    const Creature* creature = bestiary->find(creatureId);
    return creature == nullptr ? CreatureSize::Medium : creature->size;
}

// La pose d'un combattant, comme le montage la fait (`core::CombatState::placementAt`) : dans la
// carte, sans toucher un mur, sans recouvrir un combattant déjà posé.
[[nodiscard]] std::optional<TacticalIssueCode> problemeDe(const TileMap& collision,
                                                          const SimulatedSpace& espace,
                                                          const std::vector<Volume>& poses,
                                                          GridPosition ancre, CreatureSize taille,
                                                          Volume& volume) {
    const int cote = footprintSide(taille);
    if (ancre.column < 0 || ancre.row < 0 || ancre.column + cote > collision.width() ||
        ancre.row + cote > collision.height()) {
        return TacticalIssueCode::CombatantOutOfBounds;
    }
    volume = volumeOf(tileCenter(ancre, taille), taille);
    if (!espace.isClear(volume, Locomotion::Walk)) {
        return TacticalIssueCode::CombatantObstructed;
    }
    if (std::ranges::any_of(poses, [&](const Volume& autre) { return overlap(volume, autre); })) {
        return TacticalIssueCode::CombatantsOverlap;
    }
    return std::nullopt;
}

// Les cases dont le centre est une place où un marcheur de taille M, parti du centre du
// déclencheur, peut finir un tour de 9 m — le déclencheur compris. Vide si le déclencheur
// lui-même ne se tient pas.
[[nodiscard]] std::vector<GridPosition> zoneAtteignable(const TileMap& collision,
                                                        const SimulatedSpace& espace,
                                                        GridPosition trigger) {
    const Volume arpenteur = volumeOf(tileCenter(trigger), CreatureSize::Medium);
    if (!espace.isClear(arpenteur, Locomotion::Walk)) {
        return {};
    }
    const RouteQuery requete{
        .mover = arpenteur,
        .destination = {},
        .budget = metersFromTiles(static_cast<float>(TACTICAL_AREA_RADIUS)),
    };
    std::vector<GridPosition> zone;
    for (const Destination& place : espace.candidates(requete)) {
        const GridPosition caseDe = tileOf(place.point);
        const Meters3 centre = tileCenter(caseDe);
        if (caseDe.column < 0 || caseDe.row < 0 || caseDe.column >= collision.width() ||
            caseDe.row >= collision.height() || groundDistance(centre, place.point) > 1e-3f) {
            continue;
        }
        zone.push_back(caseDe);
    }
    std::ranges::sort(zone, [](GridPosition a, GridPosition b) {
        return a.row != b.row ? a.row < b.row : a.column < b.column;
    });
    return zone;
}

}  // namespace

std::vector<EncounterTerrain> analyzeEncounterTerrain(const TileMap& collision,
                                                      const std::vector<MapEntity>& entities,
                                                      const EncounterCatalog& encounters,
                                                      const Bestiary* bestiary) {
    std::vector<EncounterTerrain> verdicts;
    const SimulatedSpace espace = SimulatedSpace::fromTileMap(collision);
    for (std::size_t index = 0; index < entities.size(); ++index) {
        // Le nom de carte n'ouvre que la clé de drapeau, dont cette vérification n'a pas l'usage.
        const std::optional<EncounterTrigger> declencheur =
            encounterTriggerFor(entities[index], "");
        if (!declencheur.has_value()) {
            continue;
        }
        const Encounter* rencontre = encounters.find(declencheur->encounterId);
        if (rencontre == nullptr) {
            continue;
        }

        EncounterTerrain verdict;
        verdict.entityIndex = index;
        verdict.encounterId = declencheur->encounterId;
        verdict.trigger = declencheur->position;
        verdict.placements = placeCombatants(*rencontre, declencheur->position);

        // Le même espace, la même pose que le montage : chaque combattant posé gêne les suivants,
        // et c'est donc le second de deux combattants superposés qui est signalé.
        std::vector<Volume> poses;
        for (const CombatantPlacement& placement : verdict.placements) {
            Volume volume;
            const auto probleme = problemeDe(collision, espace, poses, placement.position,
                                             tailleDe(placement.creatureId, bestiary), volume);
            if (probleme.has_value()) {
                verdict.issues.push_back({.code = *probleme,
                                          .creatureId = placement.creatureId,
                                          .cell = placement.position});
            } else {
                poses.push_back(volume);
            }
        }

        verdict.area = zoneAtteignable(collision, espace, verdict.trigger);
        verdict.requiredCells =
            (static_cast<int>(verdict.placements.size()) + TACTICAL_PARTY_SIZE) *
            TACTICAL_CELLS_PER_COMBATANT;
        if (std::cmp_less(verdict.area.size(), verdict.requiredCells)) {
            verdict.issues.push_back({.code = TacticalIssueCode::AreaTooNarrow,
                                      .creatureId = {},
                                      .cell = verdict.trigger});
        }
        verdicts.push_back(std::move(verdict));
    }
    return verdicts;
}

}  // namespace core
