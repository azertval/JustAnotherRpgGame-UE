// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Ecs/AnimationClip.h"

#include <utility>

namespace core {

namespace {
// Clip de repli d'un jeu vide : une seule image d'indice 0, jamais animee.
// Statique plutot que reconstruit a chaque appel : clipAt() est lu potentiellement a chaque pas
// fixe pour chaque entite animee.
const AnimationClip& emptyClip() {
    static const AnimationClip empty{.name = {},
                                     .frames = {0},
                                     .frameDuration = 0.0F,
                                     .endMode = ClipEndMode::Loop,
                                     .nextClip = {}};
    return empty;
}
}  // namespace

void ClipSet::addClip(AnimationClip clip) {
    const std::string name = clip.name;
    const auto existing = _byName.find(name);
    if (existing != _byName.end()) {
        _clips[static_cast<std::size_t>(existing->second)] = std::move(clip);
        return;
    }
    _byName.emplace(name, static_cast<int>(_clips.size()));
    _clips.push_back(std::move(clip));
}

int ClipSet::indexOf(std::string_view name) const noexcept {
    const auto found = _byName.find(name);
    return found == _byName.end() ? -1 : found->second;
}

const AnimationClip& ClipSet::clipAt(int index) const noexcept {
    if (_clips.empty()) {
        return emptyClip();
    }
    // Repli deterministe sur le premier clip du jeu pour tout index hors bornes (EX-NFR-040),
    // plutot qu'un acces hors bornes ou une exception.
    if (index < 0 || static_cast<std::size_t>(index) >= _clips.size()) {
        return _clips.front();
    }
    return _clips[static_cast<std::size_t>(index)];
}

}  // namespace core
