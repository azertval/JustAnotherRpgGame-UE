// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/ActionEconomy.h"

#include <algorithm>

namespace core {

ActionEconomy ActionEconomy::standard(int movement) {
    ActionEconomy economy;
    economy.declare(ACTION_RESOURCE, 1);
    economy.declare(BONUS_ACTION_RESOURCE, 1);
    economy.declare(REACTION_RESOURCE, 1);
    economy.declare(MOVEMENT_RESOURCE, movement);
    return economy;
}

void ActionEconomy::declare(std::string_view id, int perTurn) {
    const int allowance = std::max(perTurn, 0);
    if (ActionResource* existing = find(id)) {
        existing->perTurn = allowance;
        existing->remaining = allowance;
        return;
    }
    _resources.push_back({.id = std::string(id), .perTurn = allowance, .remaining = allowance});
}

bool ActionEconomy::has(std::string_view id) const {
    return find(id) != nullptr;
}

int ActionEconomy::remaining(std::string_view id) const {
    const ActionResource* resource = find(id);
    return resource == nullptr ? 0 : resource->remaining;
}

bool ActionEconomy::spend(std::string_view id, int amount) {
    ActionResource* resource = find(id);
    if (resource == nullptr || amount <= 0 || resource->remaining < amount) {
        return false;
    }
    resource->remaining -= amount;
    return true;
}

void ActionEconomy::grant(std::string_view id, int amount) {
    if (amount <= 0) {
        return;
    }
    ActionResource* resource = find(id);
    if (resource == nullptr) {
        _resources.push_back({.id = std::string(id), .perTurn = 0, .remaining = 0});
        resource = &_resources.back();
    }
    resource->remaining += amount;
}

void ActionEconomy::refresh() {
    for (ActionResource& resource : _resources) {
        resource.remaining = resource.perTurn;
    }
}

ActionResource* ActionEconomy::find(std::string_view id) {
    const auto found = std::ranges::find_if(
        _resources, [id](const ActionResource& resource) { return resource.id == id; });
    return found == _resources.end() ? nullptr : &*found;
}

const ActionResource* ActionEconomy::find(std::string_view id) const {
    const auto found = std::ranges::find_if(
        _resources, [id](const ActionResource& resource) { return resource.id == id; });
    return found == _resources.end() ? nullptr : &*found;
}

}  // namespace core
