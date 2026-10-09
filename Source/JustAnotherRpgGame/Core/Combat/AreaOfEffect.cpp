// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/AreaOfEffect.h"

#include <optional>

#include "Core/Combat/CombatState.h"

namespace core {

std::vector<CombatantId> combatantsInArea(const CombatState& combat, const Effect& area) {
    std::vector<CombatantId> pris;
    for (const CombatantId id : combat.combatants()) {
        const std::optional<Volume> volume = combat.volumeOf(id);
        if (!volume.has_value() || !shapeHits(area, *volume)) {
            continue;
        }
        // L'effet s'etend en lignes droites depuis l'origine : seul un abri total l'arrete.
        if (coverFromPoint(combat.space(), area.origin, *volume) == Cover::Total) {
            continue;
        }
        pris.push_back(id);
    }
    return pris;
}

}  // namespace core
