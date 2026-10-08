// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/SimulatedSpace.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <queue>
#include <utility>

#include "Core/Levels/TileMap.h"

namespace core {

namespace {

constexpr float EPSILON = 1e-4f;
constexpr float INFINITE = std::numeric_limits<float>::infinity();

/// @brief La distance au sol d'un point à un rectangle : 0 dedans.
[[nodiscard]] float distanceToRect(float x, float y, const GroundRect& rect) noexcept {
    const float dx = std::max({rect.minX - x, 0.0f, x - rect.maxX});
    const float dy = std::max({rect.minY - y, 0.0f, y - rect.maxY});
    return std::hypot(dx, dy);
}

/// @brief Vrai si un disque recouvre le rectangle, bords compris.
[[nodiscard]] bool discMeetsRect(float x, float y, float radius, const GroundRect& rect) noexcept {
    return distanceToRect(x, y, rect) < radius - EPSILON;
}

/// @brief Vrai si le segment traverse la boîte, extrémités exceptées (méthode des tranches).
[[nodiscard]] bool segmentCrossesBox(Meters3 from, Meters3 to, const Box& box) noexcept {
    float tMin = 0.0f;
    float tMax = 1.0f;
    const float start[3] = {from.x, from.y, from.z};
    const float delta[3] = {to.x - from.x, to.y - from.y, to.z - from.z};
    const float low[3] = {box.rect.minX, box.rect.minY, 0.0f};
    const float high[3] = {box.rect.maxX, box.rect.maxY, box.height};
    for (int axis = 0; axis < 3; ++axis) {
        if (std::fabs(delta[axis]) <= EPSILON) {
            if (start[axis] < low[axis] - EPSILON || start[axis] > high[axis] + EPSILON) {
                return false;
            }
            continue;
        }
        float t0 = (low[axis] - start[axis]) / delta[axis];
        float t1 = (high[axis] - start[axis]) / delta[axis];
        if (t0 > t1) {
            std::swap(t0, t1);
        }
        tMin = std::max(tMin, t0);
        tMax = std::min(tMax, t1);
        if (tMin > tMax + EPSILON) {
            return false;
        }
    }
    // Un segment qui ne fait que toucher la boîte à son extrémité n'est pas coupé par elle.
    return tMax - tMin > EPSILON && tMin < 1.0f - EPSILON && tMax > EPSILON;
}

[[nodiscard]] bool discMeetsVolume(float x, float y, float radius, const Volume& other) noexcept {
    return std::hypot(x - other.base.x, y - other.base.y) < radius + other.radius - EPSILON;
}

}  // namespace

SimulatedSpace::SimulatedSpace(float width, float height)
    : _width(std::max(width, SIMULATION_STEP)), _height(std::max(height, SIMULATION_STEP)) {}

SimulatedSpace SimulatedSpace::fromTileMap(const TileMap& collision) {
    SimulatedSpace space(static_cast<float>(collision.width()) * METERS_PER_TILE,
                         static_cast<float>(collision.height()) * METERS_PER_TILE);
    for (int row = 0; row < collision.height(); ++row) {
        for (int column = 0; column < collision.width(); ++column) {
            if (collision.isSolid(column, row)) {
                const float x = static_cast<float>(column) * METERS_PER_TILE;
                const float y = static_cast<float>(row) * METERS_PER_TILE;
                space.addBox({.rect = {x, y, x + METERS_PER_TILE, y + METERS_PER_TILE},
                              .height = 3.0f,
                              .blocksMovement = true,
                              .cover = Cover::Total});
            }
        }
    }
    return space;
}

void SimulatedSpace::addBox(Box box) {
    _boxes.push_back(box);
}

void SimulatedSpace::addPlatform(GroundRect rect, float height) {
    _platforms.emplace_back(rect, height);
}

void SimulatedSpace::addDifficult(GroundRect rect) {
    _difficult.push_back(rect);
}

void SimulatedSpace::addDeepWater(GroundRect rect) {
    _water.push_back(rect);
}

bool SimulatedSpace::isDifficult(float x, float y) const noexcept {
    return std::any_of(_difficult.begin(), _difficult.end(),
                       [&](const GroundRect& rect) { return rect.contains(x, y); });
}

float SimulatedSpace::groundHeight(float x, float y) const {
    float height = 0.0f;
    for (const auto& [rect, top] : _platforms) {
        if (rect.contains(x, y)) {
            height = std::max(height, top);
        }
    }
    return height;
}

bool SimulatedSpace::isClear(const Volume& volume, Locomotion locomotion) const {
    const float x = volume.base.x;
    const float y = volume.base.y;
    const float r = volume.radius;
    if (x - r < -EPSILON || y - r < -EPSILON || x + r > _width + EPSILON ||
        y + r > _height + EPSILON) {
        return false;
    }
    for (const Box& box : _boxes) {
        if (box.blocksMovement && discMeetsRect(x, y, r, box.rect)) {
            return false;
        }
    }
    if (locomotion == Locomotion::Walk) {
        for (const GroundRect& water : _water) {
            if (discMeetsRect(x, y, r, water)) {
                return false;
            }
        }
    }
    return true;
}

bool SimulatedSpace::lineOfSight(Meters3 from, Meters3 to) const {
    return std::none_of(_boxes.begin(), _boxes.end(), [&](const Box& box) {
        return box.cover != Cover::None && segmentCrossesBox(from, to, box);
    });
}

int SimulatedSpace::columns() const noexcept {
    return static_cast<int>(std::floor(_width / SIMULATION_STEP + EPSILON)) + 1;
}

int SimulatedSpace::rows() const noexcept {
    return static_cast<int>(std::floor(_height / SIMULATION_STEP + EPSILON)) + 1;
}

Meters3 SimulatedSpace::pointOf(Node node) const noexcept {
    const float x = static_cast<float>(node.column) * SIMULATION_STEP;
    const float y = static_cast<float>(node.row) * SIMULATION_STEP;
    return {x, y, groundHeight(x, y)};
}

SimulatedSpace::Node SimulatedSpace::nearestNode(Meters3 point) const noexcept {
    const int column =
        std::clamp(static_cast<int>(std::lround(point.x / SIMULATION_STEP)), 0, columns() - 1);
    const int row =
        std::clamp(static_cast<int>(std::lround(point.y / SIMULATION_STEP)), 0, rows() - 1);
    return {column, row};
}

bool SimulatedSpace::standable(Meters3 point, const RouteQuery& query) const {
    Volume here = query.mover;
    here.base = point;
    if (!isClear(here, query.locomotion)) {
        return false;
    }
    return std::none_of(query.blocking.begin(), query.blocking.end(), [&](const Volume& other) {
        return discMeetsVolume(point.x, point.y, query.mover.radius, other);
    });
}

bool SimulatedSpace::passage(Meters3 from, Meters3 to, const RouteQuery& query) const {
    // Pas de coin coupé : le milieu du pas doit tenir, et, en diagonale, les deux côtés.
    const Meters3 middle{(from.x + to.x) / 2.0f, (from.y + to.y) / 2.0f, 0.0f};
    if (!standable({middle.x, middle.y, groundHeight(middle.x, middle.y)}, query)) {
        return false;
    }
    if (std::fabs(to.x - from.x) > EPSILON && std::fabs(to.y - from.y) > EPSILON) {
        const Meters3 a{to.x, from.y, groundHeight(to.x, from.y)};
        const Meters3 b{from.x, to.y, groundHeight(from.x, to.y)};
        return standable(a, query) && standable(b, query);
    }
    return true;
}

float SimulatedSpace::entryFactor(Meters3 point, const RouteQuery& query) const {
    float factor = 1.0f;
    if (query.locomotion == Locomotion::Walk && isDifficult(point.x, point.y)) {
        factor = 2.0f;
    }
    // L'espace d'une créature qu'on traverse compte pour du terrain difficile (Manuel, PDF p. 193).
    for (const Volume& other : query.passable) {
        if (discMeetsVolume(point.x, point.y, query.mover.radius, other)) {
            factor = 2.0f;
            break;
        }
    }
    return factor;
}

SimulatedSpace::Search SimulatedSpace::explore(const RouteQuery& query, float limit) const {
    const int cols = columns();
    const int count = cols * rows();
    Search search{std::vector<float>(static_cast<std::size_t>(count), INFINITE),
                  std::vector<int>(static_cast<std::size_t>(count), -1)};
    const Node start = nearestNode(query.mover.base);
    const int startIndex = start.row * cols + start.column;
    const Meters3 startPoint = pointOf(start);
    const float offset = groundDistance(query.mover.base, startPoint);
    if (limit >= 0.0f && offset > limit + EPSILON) {
        return search;
    }
    search.cost[static_cast<std::size_t>(startIndex)] = offset;

    using Entry = std::pair<float, int>;
    std::priority_queue<Entry, std::vector<Entry>, std::greater<>> open;
    open.emplace(offset, startIndex);
    constexpr int DX[8] = {1, -1, 0, 0, 1, 1, -1, -1};
    constexpr int DY[8] = {0, 0, 1, -1, 1, -1, 1, -1};
    while (!open.empty()) {
        const auto [cost, index] = open.top();
        open.pop();
        if (cost > search.cost[static_cast<std::size_t>(index)] + EPSILON) {
            continue;
        }
        const Node node{index % cols, index / cols};
        const Meters3 here = pointOf(node);
        for (int k = 0; k < 8; ++k) {
            const Node next{node.column + DX[k], node.row + DY[k]};
            if (next.column < 0 || next.row < 0 || next.column >= cols || next.row >= rows()) {
                continue;
            }
            const Meters3 there = pointOf(next);
            if (!standable(there, query) || !passage(here, there, query)) {
                continue;
            }
            const float step = groundDistance(here, there) * entryFactor(there, query);
            const float total = cost + step;
            if (limit >= 0.0f && total > limit + EPSILON) {
                continue;
            }
            const int nextIndex = next.row * cols + next.column;
            float& best = search.cost[static_cast<std::size_t>(nextIndex)];
            if (total < best - EPSILON ||
                (std::fabs(total - best) <= EPSILON &&
                 index < search.previous[static_cast<std::size_t>(nextIndex)])) {
                best = total;
                search.previous[static_cast<std::size_t>(nextIndex)] = index;
                open.emplace(total, nextIndex);
            }
        }
    }
    return search;
}

std::optional<Route> SimulatedSpace::route(const RouteQuery& query) const {
    const Search search = explore(query, query.budget);
    const int cols = columns();
    const Node goal = nearestNode(query.destination);
    const int goalIndex = goal.row * cols + goal.column;
    const float goalCost = search.cost[static_cast<std::size_t>(goalIndex)];
    if (goalCost == INFINITE) {
        return std::nullopt;
    }
    const Node start = nearestNode(query.mover.base);
    const int startIndex = start.row * cols + start.column;
    if (goalIndex != startIndex && !standable(pointOf(goal), query)) {
        return std::nullopt;
    }
    std::vector<Meters3> points;
    for (int index = goalIndex; index != startIndex && index >= 0;
         index = search.previous[static_cast<std::size_t>(index)]) {
        points.push_back(pointOf({index % cols, index / cols}));
    }
    std::reverse(points.begin(), points.end());
    Route result{std::move(points), goalCost};
    // La destination exacte termine le chemin si le dernier pas est dégagé.
    const Meters3 exact{query.destination.x, query.destination.y,
                        groundHeight(query.destination.x, query.destination.y)};
    const Meters3 last = result.points.empty() ? query.mover.base : result.points.back();
    const float tail = groundDistance(last, exact);
    if (tail > EPSILON && standable(exact, query) && passage(last, exact, query)) {
        const float total = result.length + tail * entryFactor(exact, query);
        if (query.budget < 0.0f || total <= query.budget + EPSILON) {
            result.points.push_back(exact);
            result.length = total;
        }
    }
    if (result.points.empty()) {
        return std::nullopt;
    }
    // On ne finit pas dans l'espace d'une créature qu'on traverse.
    const Meters3 end = result.points.back();
    for (const Volume& other : query.passable) {
        if (discMeetsVolume(end.x, end.y, query.mover.radius, other)) {
            return std::nullopt;
        }
    }
    return result;
}

std::vector<Meters3> SimulatedSpace::candidates(const RouteQuery& query) const {
    std::vector<Meters3> result;
    result.push_back(query.mover.base);
    const Search search = explore(query, query.budget);
    const int cols = columns();
    for (std::size_t index = 0; index < search.cost.size(); ++index) {
        if (search.cost[index] == INFINITE) {
            continue;
        }
        const Meters3 point =
            pointOf({static_cast<int>(index) % cols, static_cast<int>(index) / cols});
        if (groundDistance(point, query.mover.base) <= EPSILON || !standable(point, query)) {
            continue;
        }
        const bool onAlly =
            std::any_of(query.passable.begin(), query.passable.end(), [&](const Volume& other) {
                return discMeetsVolume(point.x, point.y, query.mover.radius, other);
            });
        if (!onAlly) {
            result.push_back(point);
        }
    }
    return result;
}

}  // namespace core
