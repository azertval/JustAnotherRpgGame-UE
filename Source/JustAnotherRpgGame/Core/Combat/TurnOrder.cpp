// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/TurnOrder.h"

#include <algorithm>
#include <utility>

namespace core {

namespace {

[[nodiscard]] bool markerBefore(const InitiativeMarker& first, const InitiativeMarker& second) {
    if (first.count != second.count) {
        return first.count > second.count;
    }
    return first.name < second.name;
}

}  // namespace

bool actsBefore(const InitiativeEntry& first, const InitiativeEntry& second) noexcept {
    if (first.total != second.total) {
        return first.total > second.total;
    }
    if (first.modifier != second.modifier) {
        return first.modifier > second.modifier;
    }
    if (first.dexterity != second.dexterity) {
        return first.dexterity > second.dexterity;
    }
    if (first.side != second.side) {
        return first.side == CombatSide::Allies;
    }
    return first.combatant < second.combatant;
}

bool slotBefore(const TurnSlot& first, const TurnSlot& second) {
    if (first.count() != second.count()) {
        return first.count() > second.count();
    }
    // À rang égal, un combattant passe avant un repère : les actions de repaire se jouent au rang
    // 20 « en perdant les égalités ».
    if (first.entry.has_value() != second.entry.has_value()) {
        return first.entry.has_value();
    }
    if (first.entry.has_value()) {
        return actsBefore(*first.entry, *second.entry);
    }
    return markerBefore(first.marker, second.marker);
}

bool TurnOrder::add(const InitiativeEntry& entry) {
    if (contains(entry.combatant)) {
        return false;
    }
    const auto place = std::ranges::upper_bound(_entries, entry, actsBefore);
    _entries.insert(place, entry);
    return true;
}

bool TurnOrder::remove(CombatantId combatant) {
    const auto found = std::ranges::find_if(_entries, [combatant](const InitiativeEntry& entry) {
        return entry.combatant == combatant;
    });
    if (found == _entries.end()) {
        return false;
    }
    _entries.erase(found);
    return true;
}

bool TurnOrder::addMarker(InitiativeMarker marker) {
    const bool duplicate = std::ranges::any_of(_markers, [&marker](const InitiativeMarker& other) {
        return other.count == marker.count && other.name == marker.name;
    });
    if (duplicate) {
        return false;
    }
    const auto place = std::ranges::upper_bound(_markers, marker, markerBefore);
    _markers.insert(place, std::move(marker));
    return true;
}

bool TurnOrder::contains(CombatantId combatant) const {
    return find(combatant) != nullptr;
}

const InitiativeEntry* TurnOrder::find(CombatantId combatant) const {
    const auto found = std::ranges::find_if(_entries, [combatant](const InitiativeEntry& entry) {
        return entry.combatant == combatant;
    });
    return found == _entries.end() ? nullptr : &*found;
}

std::optional<TurnSlot> TurnOrder::firstSlot() const {
    std::optional<TurnSlot> best;
    if (!_entries.empty()) {
        best = TurnSlot{.entry = _entries.front(), .marker = {}};
    }
    if (!_markers.empty()) {
        TurnSlot marker{.entry = std::nullopt, .marker = _markers.front()};
        if (!best.has_value() || slotBefore(marker, *best)) {
            best = std::move(marker);
        }
    }
    return best;
}

std::optional<TurnSlot> TurnOrder::slotAfter(const TurnSlot& slot) const {
    // Les deux listes sont triées : la place qui suit est la plus avancée des deux premières
    // candidates strictement après `slot`, une par liste.
    std::optional<TurnSlot> best;
    for (const InitiativeEntry& entry : _entries) {
        TurnSlot candidate{.entry = entry, .marker = {}};
        if (slotBefore(slot, candidate)) {
            best = std::move(candidate);
            break;
        }
    }
    for (const InitiativeMarker& marker : _markers) {
        TurnSlot candidate{.entry = std::nullopt, .marker = marker};
        if (slotBefore(slot, candidate)) {
            if (!best.has_value() || slotBefore(candidate, *best)) {
                best = std::move(candidate);
            }
            break;
        }
    }
    return best;
}

}  // namespace core
