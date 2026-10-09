// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/Flanking.h"

#include <algorithm>
#include <optional>

namespace core {

namespace {

// Debout, a une case de la cible, et la voyant depuis @p base.
[[nodiscard]] bool auContactEtVoit(const CombatState& combat, CombatantId qui, Meters3 base,
                                   CombatantId cible) {
    const std::optional<float> ecart = gapFrom(combat, qui, base, cible);
    return ecart.has_value() && adjacentGap(*ecart) && hasLineOfSightFrom(combat, qui, base, cible);
}

}  // namespace

bool isFlankedFrom(const CombatState& combat, CombatantId attacker, Meters3 attackerBase,
                   CombatantId target) {
    const Combatant* assaillant = combat.find(attacker);
    const Combatant* cible = combat.find(target);
    const std::optional<Meters3> centreCible = combat.positionOf(target);
    if (assaillant == nullptr || cible == nullptr || !centreCible.has_value() ||
        attacker == target || assaillant->status != CombatantStatus::Standing ||
        !auContactEtVoit(combat, attacker, attackerBase, target)) {
        return false;
    }
    const auto prendEnTenaille = [&](const CombatantId autre) {
        const Combatant* allie = combat.find(autre);
        if (autre == attacker || autre == target || allie == nullptr ||
            !allie->position.has_value() || allie->status != CombatantStatus::Standing ||
            allie->profile.side != assaillant->profile.side) {
            return false;
        }
        return auContactEtVoit(combat, autre, *allie->position, target) &&
               flanksByAngle(attackerBase, *allie->position, *centreCible);
    };
    return std::ranges::any_of(combat.combatants(), prendEnTenaille);
}

bool isFlanked(const CombatState& combat, CombatantId attacker, CombatantId target) {
    const std::optional<Meters3> base = combat.positionOf(attacker);
    return base.has_value() && isFlankedFrom(combat, attacker, *base, target);
}

bool isAdjacentToAllyOf(const CombatState& combat, CombatantId attacker, CombatantId target) {
    const Combatant* attaquant = combat.find(attacker);
    if (attaquant == nullptr) {
        return false;
    }
    return std::ranges::any_of(combat.combatants(), [&](const CombatantId autre) {
        const Combatant* allie = combat.find(autre);
        if (autre == attacker || autre == target || allie == nullptr ||
            allie->status != CombatantStatus::Standing ||
            allie->profile.side != attaquant->profile.side) {
            return false;
        }
        const std::optional<float> ecart = gapBetween(combat, autre, target);
        return ecart.has_value() && adjacentGap(*ecart);
    });
}

}  // namespace core
