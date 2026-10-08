// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/CombatSpace.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <numbers>

namespace core {

namespace {

constexpr float EPSILON = 1e-4f;

struct Vec2 {
    float x = 0.0f;
    float y = 0.0f;
};

[[nodiscard]] Vec2 flat(Meters3 p) noexcept {
    return {p.x, p.y};
}

[[nodiscard]] float dot(Vec2 a, Vec2 b) noexcept {
    return a.x * b.x + a.y * b.y;
}

[[nodiscard]] float length(Vec2 a) noexcept {
    return std::hypot(a.x, a.y);
}

[[nodiscard]] Vec2 minus(Vec2 a, Vec2 b) noexcept {
    return {a.x - b.x, a.y - b.y};
}

/// @brief La distance d'un point à un segment, dans le plan.
[[nodiscard]] float distanceToSegment(Vec2 p, Vec2 a, Vec2 b) noexcept {
    const Vec2 ab = minus(b, a);
    const float ab2 = dot(ab, ab);
    if (ab2 <= EPSILON * EPSILON) {
        return length(minus(p, a));
    }
    const float t = std::clamp(dot(minus(p, a), ab) / ab2, 0.0f, 1.0f);
    return length(minus(p, Vec2{a.x + t * ab.x, a.y + t * ab.y}));
}

/// @brief Vrai si le point est dans le polygone convexe @p polygon (sommets dans un sens fixe).
[[nodiscard]] bool insideConvex(Vec2 p, std::span<const Vec2> polygon) noexcept {
    bool positive = false;
    bool negative = false;
    for (std::size_t i = 0; i < polygon.size(); ++i) {
        const Vec2 a = polygon[i];
        const Vec2 b = polygon[(i + 1) % polygon.size()];
        const float cross = (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);
        if (cross > EPSILON) {
            positive = true;
        } else if (cross < -EPSILON) {
            negative = true;
        }
    }
    return !(positive && negative);
}

/// @brief Vrai si un disque croise un polygone convexe : son centre y est, ou un côté passe à
/// moins du rayon.
[[nodiscard]] bool discMeetsConvex(Vec2 center, float radius,
                                   std::span<const Vec2> polygon) noexcept {
    if (insideConvex(center, polygon)) {
        return true;
    }
    for (std::size_t i = 0; i < polygon.size(); ++i) {
        if (distanceToSegment(center, polygon[i], polygon[(i + 1) % polygon.size()]) <=
            radius + EPSILON) {
            return true;
        }
    }
    return false;
}

/// @brief Le plan vertical du volume croise-t-il la bande [@p low, @p high] ?
[[nodiscard]] bool verticalOverlap(const Volume& volume, float low, float high) noexcept {
    return volume.base.z <= high + EPSILON && volume.base.z + volume.height >= low - EPSILON;
}

/// @brief La direction unitaire de @p origin vers @p toward, ou rien si les deux se confondent.
[[nodiscard]] std::optional<Vec2> direction(Meters3 origin, Meters3 toward) noexcept {
    const Vec2 d = minus(flat(toward), flat(origin));
    const float len = length(d);
    if (len <= EPSILON) {
        return std::nullopt;
    }
    return Vec2{d.x / len, d.y / len};
}

}  // namespace

float edgeDistance(const Volume& a, const Volume& b) noexcept {
    const float horizontal = std::max(0.0f, groundDistance(a.base, b.base) - a.radius - b.radius);
    const float aTop = a.base.z + a.height;
    const float bTop = b.base.z + b.height;
    float vertical = 0.0f;
    if (a.base.z > bTop) {
        vertical = a.base.z - bTop;
    } else if (b.base.z > aTop) {
        vertical = b.base.z - aTop;
    }
    return std::hypot(horizontal, vertical);
}

bool overlap(const Volume& a, const Volume& b) noexcept {
    if (groundDistance(a.base, b.base) >= a.radius + b.radius - EPSILON) {
        return false;
    }
    return a.base.z < b.base.z + b.height - EPSILON && b.base.z < a.base.z + a.height - EPSILON;
}

bool flanksByAngle(Meters3 a, Meters3 b, Meters3 target) noexcept {
    const Vec2 ta = minus(flat(a), flat(target));
    const Vec2 tb = minus(flat(b), flat(target));
    const float la = length(ta);
    const float lb = length(tb);
    if (la <= EPSILON || lb <= EPSILON) {
        return false;
    }
    const float cosine = dot(ta, tb) / (la * lb);
    const float threshold = std::cos(FLANKING_ANGLE_DEGREES * std::numbers::pi_v<float> / 180.0f);
    return cosine <= threshold + EPSILON;
}

namespace {

[[nodiscard]] bool inside(Meters3 point, const Volume& volume) noexcept {
    return groundDistance(point, volume.base) < volume.radius - EPSILON &&
           point.z > volume.base.z + EPSILON && point.z < volume.base.z + volume.height - EPSILON;
}

}  // namespace

bool segmentCrosses(Meters3 from, Meters3 to, const Volume& volume) noexcept {
    // Les extrémités ne comptent pas : ce qui part d'un corps ou y arrive n'est pas coupé par lui.
    if (inside(from, volume) || inside(to, volume)) {
        return false;
    }
    // Le segment en trois dimensions contre un cylindre vertical : on cherche le paramètre t où
    // la distance au sol à l'axe passe sous le rayon, puis on vérifie la hauteur sur cet
    // intervalle.
    const Vec2 a = flat(from);
    const Vec2 b = flat(to);
    const Vec2 c = flat(volume.base);
    const Vec2 d = minus(b, a);
    const Vec2 f = minus(a, c);
    const float qa = dot(d, d);
    const float qb = 2.0f * dot(f, d);
    const float qc = dot(f, f) - volume.radius * volume.radius;
    float t0 = 0.0f;
    float t1 = 1.0f;
    if (qa <= EPSILON * EPSILON) {
        if (qc > 0.0f) {
            return false;
        }
    } else {
        const float discriminant = qb * qb - 4.0f * qa * qc;
        if (discriminant < 0.0f) {
            return false;
        }
        const float root = std::sqrt(discriminant);
        t0 = std::max(0.0f, (-qb - root) / (2.0f * qa));
        t1 = std::min(1.0f, (-qb + root) / (2.0f * qa));
        if (t0 >= t1 - EPSILON) {
            return false;
        }
    }
    const float z0 = from.z + t0 * (to.z - from.z);
    const float z1 = from.z + t1 * (to.z - from.z);
    const float low = std::min(z0, z1);
    const float high = std::max(z0, z1);
    return low <= volume.base.z + volume.height - EPSILON && high >= volume.base.z + EPSILON;
}

bool shapeHits(const Effect& effect, const Volume& volume) noexcept {
    const Vec2 center = flat(volume.base);
    switch (effect.shape) {
        case AreaShape::Sphere: {
            // Le point du cylindre le plus proche du centre de la sphère.
            const float ground =
                std::max(0.0f, groundDistance(effect.origin, volume.base) - volume.radius);
            const float z =
                std::clamp(effect.origin.z, volume.base.z, volume.base.z + volume.height);
            const float gap = std::hypot(ground, effect.origin.z - z);
            return gap <= effect.size + EPSILON;
        }
        case AreaShape::Cylinder: {
            if (groundDistance(effect.origin, volume.base) >
                effect.size + volume.radius + EPSILON) {
                return false;
            }
            return verticalOverlap(volume, effect.origin.z, effect.origin.z + effect.width);
        }
        case AreaShape::Cone:
        case AreaShape::Line:
        case AreaShape::Cube: {
            const std::optional<Vec2> axis = direction(effect.origin, effect.toward);
            if (!axis || effect.size <= EPSILON) {
                return false;
            }
            if (!verticalOverlap(volume, effect.origin.z - effect.size,
                                 effect.origin.z + effect.size)) {
                return false;
            }
            const Vec2 o = flat(effect.origin);
            const Vec2 side{-axis->y, axis->x};
            std::array<Vec2, 4> polygon{};
            std::size_t count = 0;
            if (effect.shape == AreaShape::Cone) {
                // Un triangle : au bout, la largeur égale la longueur.
                const Vec2 tip{o.x + axis->x * effect.size, o.y + axis->y * effect.size};
                const float half = effect.size / 2.0f;
                polygon = {o, Vec2{tip.x + side.x * half, tip.y + side.y * half},
                           Vec2{tip.x - side.x * half, tip.y - side.y * half}, Vec2{}};
                count = 3;
            } else {
                const float half =
                    (effect.shape == AreaShape::Line ? effect.width : effect.size) / 2.0f;
                const Vec2 end{o.x + axis->x * effect.size, o.y + axis->y * effect.size};
                polygon = {Vec2{o.x + side.x * half, o.y + side.y * half},
                           Vec2{end.x + side.x * half, end.y + side.y * half},
                           Vec2{end.x - side.x * half, end.y - side.y * half},
                           Vec2{o.x - side.x * half, o.y - side.y * half}};
                count = 4;
            }
            return discMeetsConvex(center, volume.radius,
                                   std::span<const Vec2>(polygon.data(), count));
        }
    }
    return false;
}

std::vector<std::size_t> volumesInEffect(const Effect& effect, std::span<const Volume> volumes) {
    std::vector<std::size_t> hits;
    for (std::size_t i = 0; i < volumes.size(); ++i) {
        if (shapeHits(effect, volumes[i])) {
            hits.push_back(i);
        }
    }
    return hits;
}

namespace {

/// @brief Quatre points du bord d'un volume, qui échantillonnent sa hauteur : à un, trois, cinq et
/// sept huitièmes, en tournant autour de lui. Un muret cache les bas, pas les hauts.
[[nodiscard]] std::array<Meters3, 4> rimPoints(const Volume& volume) noexcept {
    const float r = volume.radius;
    const float h = volume.height;
    const float z = volume.base.z;
    return {Meters3{volume.base.x + r, volume.base.y, z + h * 0.125f},
            Meters3{volume.base.x, volume.base.y + r, z + h * 0.375f},
            Meters3{volume.base.x - r, volume.base.y, z + h * 0.625f},
            Meters3{volume.base.x, volume.base.y - r, z + h * 0.875f}};
}

[[nodiscard]] Cover coverForLines(int blockedByMap, bool blockedByBody) noexcept {
    Cover cover = Cover::None;
    if (blockedByMap >= 4) {
        return Cover::Total;
    }
    if (blockedByMap == 3) {
        cover = Cover::ThreeQuarters;
    } else if (blockedByMap >= 1) {
        cover = Cover::Half;
    }
    if (blockedByBody && cover == Cover::None) {
        cover = Cover::Half;
    }
    return cover;
}

[[nodiscard]] Cover coverFromOrigin(const CombatSpace& space, Meters3 origin, const Volume& target,
                                    std::span<const Volume> interposed) {
    int blocked = 0;
    bool body = false;
    for (const Meters3 point : rimPoints(target)) {
        if (!space.lineOfSight(origin, point)) {
            ++blocked;
            continue;
        }
        for (const Volume& other : interposed) {
            if (segmentCrosses(origin, point, other)) {
                body = true;
                break;
            }
        }
    }
    return coverForLines(blocked, body);
}

}  // namespace

Cover coverFrom(const CombatSpace& space, const Volume& attacker, const Volume& target,
                std::span<const Volume> interposed) {
    Cover best = Cover::Total;
    std::array<Meters3, 5> origins{};
    origins[0] = centerOf(attacker);
    const std::array<Meters3, 4> rim = rimPoints(attacker);
    std::copy(rim.begin(), rim.end(), origins.begin() + 1);
    for (const Meters3 origin : origins) {
        const Cover cover = coverFromOrigin(space, origin, target, interposed);
        if (cover < best) {
            best = cover;
        }
        if (best == Cover::None) {
            break;
        }
    }
    return best;
}

Cover coverFromPoint(const CombatSpace& space, Meters3 origin, const Volume& target,
                     std::span<const Volume> interposed) {
    return coverFromOrigin(space, origin, target, interposed);
}

bool hasLineOfSight(const CombatSpace& space, const Volume& a, const Volume& b) {
    return coverFrom(space, a, b) != Cover::Total;
}

}  // namespace core
