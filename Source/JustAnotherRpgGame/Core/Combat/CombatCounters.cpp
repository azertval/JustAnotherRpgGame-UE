// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/CombatCounters.h"

#include <algorithm>

namespace core {

int ScopedCounters::increment(CounterScope scope, std::string_view owner, std::string_view key,
                              int amount) {
    int& counter = _values[std::make_tuple(scope, std::string(owner), std::string(key))];
    counter += amount;
    return counter;
}

int ScopedCounters::value(CounterScope scope, std::string_view owner, std::string_view key) const {
    const auto found = _values.find(std::make_tuple(scope, std::string(owner), std::string(key)));
    return found == _values.end() ? 0 : found->second;
}

void ScopedCounters::clear(CounterScope scope) {
    std::erase_if(_values, [scope](const auto& item) { return std::get<0>(item.first) == scope; });
}

void ImmunityLedger::grant(std::string_view creature, std::string_view source,
                           std::int64_t untilSecond) {
    const auto key = std::make_tuple(std::string(creature), std::string(source));
    const auto found = _until.find(key);
    if (found == _until.end()) {
        _until.emplace(key, untilSecond);
        return;
    }
    found->second = std::max(found->second, untilSecond);
}

bool ImmunityLedger::isImmune(std::string_view creature, std::string_view source,
                              std::int64_t nowSecond) const {
    const auto found = _until.find(std::make_tuple(std::string(creature), std::string(source)));
    return found != _until.end() && nowSecond < found->second;
}

void ImmunityLedger::expire(std::int64_t nowSecond) {
    std::erase_if(_until, [nowSecond](const auto& item) { return item.second <= nowSecond; });
}

}  // namespace core
