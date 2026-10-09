// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/SimulatedSpace.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <optional>
#include <queue>
#include <utility>

#include "Core/Levels/Level.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"

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

/// @brief L'intervalle des paramètres où le segment touche la boîte, bords compris (méthode des
/// tranches), ou rien s'il ne la touche pas.
[[nodiscard]] std::optional<std::pair<float, float>> segmentTouchesBox(Meters3 from, Meters3 to,
                                                                       const Box& box) noexcept {
    float tMin = 0.0f;
    float tMax = 1.0f;
    const float start[3] = {from.x, from.y, from.z};
    const float delta[3] = {to.x - from.x, to.y - from.y, to.z - from.z};
    const float low[3] = {box.rect.minX, box.rect.minY, 0.0f};
    const float high[3] = {box.rect.maxX, box.rect.maxY, box.height};
    for (int axis = 0; axis < 3; ++axis) {
        if (std::fabs(delta[axis]) <= EPSILON) {
            if (start[axis] < low[axis] - EPSILON || start[axis] > high[axis] + EPSILON) {
                return std::nullopt;
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
            return std::nullopt;
        }
    }
    return std::pair{tMin, tMax};
}

/// @brief Vrai si le segment traverse la boîte, extrémités exceptées.
[[nodiscard]] bool segmentCrossesBox(Meters3 from, Meters3 to, const Box& box) noexcept {
    const std::optional<std::pair<float, float>> touch = segmentTouchesBox(from, to, box);
    // Un segment qui ne fait que toucher la boîte à son extrémité n'est pas coupé par elle.
    return touch.has_value() && touch->second - touch->first > EPSILON &&
           touch->first < 1.0f - EPSILON && touch->second > EPSILON;
}

/**
 * @brief Vrai si le segment passe **entre** deux boîtes qui se touchent : au même point, à une
 *        hauteur que les deux couvrent, l'une d'un côté de lui et l'autre de l'autre.
 *
 * Le coin commun de deux murs en diagonale ne laisse pas passer le regard (`core::checkTarget`) :
 * le segment qui y passe ne fait que frôler chaque boîte, et aucune ne le coupe seule. Un regard
 * qui longe la face d'un mur fait de plusieurs boîtes les frôle toutes du même côté, et passe.
 */
[[nodiscard]] bool segmentPinchedBetween(Meters3 from, Meters3 to, const Box& a,
                                         std::pair<float, float> touchA, const Box& b,
                                         std::pair<float, float> touchB) noexcept {
    const float t = std::max(touchA.first, touchB.first);
    if (t > std::min(touchA.second, touchB.second) + EPSILON || t <= EPSILON ||
        t >= 1.0f - EPSILON) {
        return false;
    }
    const float dx = to.x - from.x;
    const float dy = to.y - from.y;
    const float px = from.x + t * dx;
    const float py = from.y + t * dy;
    const float pz = from.z + t * (to.z - from.z);
    if (pz >= std::min(a.height, b.height) - EPSILON) {
        return false;
    }
    const auto side = [&](const Box& box) {
        const float cx = (box.rect.minX + box.rect.maxX) / 2.0f - px;
        const float cy = (box.rect.minY + box.rect.maxY) / 2.0f - py;
        return dx * cy - dy * cx;
    };
    return side(a) * side(b) < 0.0f;
}

[[nodiscard]] bool discMeetsVolume(float x, float y, float radius, const Volume& other) noexcept {
    return std::hypot(x - other.base.x, y - other.base.y) < radius + other.radius - EPSILON;
}

// Ce que le vol franchit : l'eau profonde et la falaise arretent la marche, pas le vol ni la vue.
[[nodiscard]] bool groundOnly(TileType type) noexcept {
    return type == TileType::DeepWater || type == TileType::Cliff;
}

[[nodiscard]] GroundRect rectOfTiles(int firstColumn, int endColumn, int row) noexcept {
    const float y = static_cast<float>(row) * METERS_PER_TILE;
    return {static_cast<float>(firstColumn) * METERS_PER_TILE, y,
            static_cast<float>(endColumn) * METERS_PER_TILE, y + METERS_PER_TILE};
}

[[nodiscard]] bool marksDifficult(const PropertyMap& properties) {
    const auto found = properties.find(std::string(DIFFICULT_TERRAIN_PROPERTY));
    if (found == properties.end()) {
        return false;
    }
    const bool* value = std::get_if<bool>(&found->second);
    return value != nullptr && *value;
}

}  // namespace

SimulatedSpace::SimulatedSpace(float width, float height, float step)
    : _width(std::max(width, step)), _height(std::max(height, step)), _step(step) {}

SimulatedSpace SimulatedSpace::fromTileMap(const TileMap& collision) {
    SimulatedSpace space(static_cast<float>(collision.width()) * METERS_PER_TILE,
                         static_cast<float>(collision.height()) * METERS_PER_TILE, TILE_MAP_STEP);
    // Une suite de cases de meme nature sur une ligne fait un seul rectangle.
    for (int row = 0; row < collision.height(); ++row) {
        int column = 0;
        while (column < collision.width()) {
            const TileType type = collision.tile(column, row);
            if (!isSolid(type)) {
                ++column;
                continue;
            }
            const bool water = groundOnly(type);
            const int first = column;
            while (column < collision.width() && isSolid(collision.tile(column, row)) &&
                   groundOnly(collision.tile(column, row)) == water) {
                ++column;
            }
            if (water) {
                space.addDeepWater(rectOfTiles(first, column, row));
            } else {
                space.addBox({.rect = rectOfTiles(first, column, row),
                              .height = 3.0f,
                              .blocksMovement = true,
                              .cover = Cover::Total});
            }
        }
    }
    return space;
}

SimulatedSpace SimulatedSpace::fromLevel(const Level& level, const TileMap& collision) {
    SimulatedSpace space = fromTileMap(collision);
    const auto difficile = [&](GridPosition cell) {
        if (cell.column >= 0 && cell.row >= 0 && cell.column < collision.width() &&
            cell.row < collision.height()) {
            space.addDifficult(rectOfTiles(cell.column, cell.column + 1, cell.row));
        }
    };
    for (const TileLayer& layer : level.layers()) {
        if (!marksDifficult(layer.properties) || layer.tiles.width() != collision.width() ||
            layer.tiles.height() != collision.height()) {
            continue;
        }
        for (int row = 0; row < collision.height(); ++row) {
            for (int column = 0; column < collision.width(); ++column) {
                if (layer.tiles.tile(column, row) != TileType::Empty) {
                    difficile({column, row});
                }
            }
        }
    }
    for (const MapEntity& entity : level.entities()) {
        if (entity.type == ZONE_ENTITY_TYPE && marksDifficult(entity.properties)) {
            for (const GridPosition cell : zoneCells(entity)) {
                difficile(cell);
            }
        }
    }
    return space;
}

void SimulatedSpace::addBox(Box box) {
    _boxes.push_back(box);
    _clearances.clear();
}

bool SimulatedSpace::removeBox(std::size_t index) {
    if (index >= _boxes.size()) {
        return false;
    }
    _boxes.erase(_boxes.begin() + static_cast<std::ptrdiff_t>(index));
    _clearances.clear();
    return true;
}

void SimulatedSpace::addPlatform(GroundRect rect, float height) {
    _platforms.emplace_back(rect, height);
}

void SimulatedSpace::addDifficult(GroundRect rect) {
    _difficult.push_back(rect);
}

void SimulatedSpace::addDeepWater(GroundRect rect) {
    _water.push_back(rect);
    _clearances.clear();
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
    std::vector<std::pair<const Box*, std::pair<float, float>>> touched;
    for (const Box& box : _boxes) {
        if (box.cover == Cover::None) {
            continue;
        }
        if (segmentCrossesBox(from, to, box)) {
            return false;
        }
        if (const std::optional<std::pair<float, float>> touch = segmentTouchesBox(from, to, box)) {
            touched.emplace_back(&box, *touch);
        }
    }
    for (std::size_t i = 0; i < touched.size(); ++i) {
        for (std::size_t j = i + 1; j < touched.size(); ++j) {
            if (segmentPinchedBetween(from, to, *touched[i].first, touched[i].second,
                                      *touched[j].first, touched[j].second)) {
                return false;
            }
        }
    }
    return true;
}

int SimulatedSpace::columns() const noexcept {
    return static_cast<int>(std::floor(_width / _step + EPSILON)) + 1;
}

int SimulatedSpace::rows() const noexcept {
    return static_cast<int>(std::floor(_height / _step + EPSILON)) + 1;
}

Meters3 SimulatedSpace::pointOf(Node node) const noexcept {
    const float x = static_cast<float>(node.column) * _step;
    const float y = static_cast<float>(node.row) * _step;
    return {x, y, groundHeight(x, y)};
}

SimulatedSpace::Node SimulatedSpace::nearestNode(Meters3 point) const noexcept {
    const int column = std::clamp(static_cast<int>(std::lround(point.x / _step)), 0, columns() - 1);
    const int row = std::clamp(static_cast<int>(std::lround(point.y / _step)), 0, rows() - 1);
    return {column, row};
}

const SimulatedSpace::Clearance& SimulatedSpace::clearanceFor(float radius,
                                                              Locomotion locomotion) const {
    for (const Clearance& clearance : _clearances) {
        if (std::fabs(clearance.radius - radius) <= EPSILON && clearance.locomotion == locomotion) {
            return clearance;
        }
    }
    const float half = _step / 2.0f;
    const int cols = 2 * (columns() - 1) + 1;
    const int lines = 2 * (rows() - 1) + 1;
    Clearance clearance{.radius = radius,
                        .locomotion = locomotion,
                        .clear = std::vector<bool>(static_cast<std::size_t>(cols * lines), false)};
    for (int row = 0; row < lines; ++row) {
        for (int column = 0; column < cols; ++column) {
            const Volume here{
                .base = {static_cast<float>(column) * half, static_cast<float>(row) * half, 0.0f},
                .radius = radius,
                .height = 0.0f};
            clearance.clear[static_cast<std::size_t>(row * cols + column)] =
                isClear(here, locomotion);
        }
    }
    _clearances.push_back(std::move(clearance));
    return _clearances.back();
}

bool SimulatedSpace::staticallyClear(Meters3 point, const RouteQuery& query) const {
    const float half = _step / 2.0f;
    const long column = std::lround(point.x / half);
    const long row = std::lround(point.y / half);
    const int cols = 2 * (columns() - 1) + 1;
    const int lines = 2 * (rows() - 1) + 1;
    const bool onLattice = std::fabs(static_cast<float>(column) * half - point.x) <= EPSILON &&
                           std::fabs(static_cast<float>(row) * half - point.y) <= EPSILON;
    if (onLattice && column >= 0 && row >= 0 && column < cols && row < lines) {
        const Clearance& clearance = clearanceFor(query.mover.radius, query.locomotion);
        return clearance.clear[static_cast<std::size_t>(row * cols + column)];
    }
    Volume here = query.mover;
    here.base = point;
    return isClear(here, query.locomotion);
}

bool SimulatedSpace::standable(Meters3 point, const RouteQuery& query) const {
    if (!staticallyClear(point, query)) {
        return false;
    }
    return std::none_of(query.blocking.begin(), query.blocking.end(), [&](const Volume& other) {
        return discMeetsVolume(point.x, point.y, query.mover.radius, other);
    });
}

bool SimulatedSpace::passage(Meters3 from, Meters3 to, const RouteQuery& query) const {
    // Pas de coin coupé : le milieu du pas doit tenir, et, en diagonale, les deux côtés.
    const Meters3 middle{(from.x + to.x) / 2.0f, (from.y + to.y) / 2.0f, 0.0f};
    if (!standable(middle, query)) {
        return false;
    }
    if (std::fabs(to.x - from.x) > EPSILON && std::fabs(to.y - from.y) > EPSILON) {
        const Meters3 a{to.x, from.y, 0.0f};
        const Meters3 b{from.x, to.y, 0.0f};
        return standable(a, query) && standable(b, query);
    }
    return true;
}

float SimulatedSpace::entryFactor(Meters3 from, Meters3 to, const RouteQuery& query) const {
    // Le pas se lit en son milieu, pas à son arrivée : un pas qui s'arrête au bord d'une zone
    // difficile sans y entrer coûte simple, et celui qui en sort jusqu'à son bord coûte double.
    const float x = (from.x + to.x) / 2.0f;
    const float y = (from.y + to.y) / 2.0f;
    float factor = 1.0f;
    if (query.locomotion == Locomotion::Walk && isDifficult(x, y)) {
        factor = 2.0f;
    }
    // L'espace d'une créature qu'on traverse compte pour du terrain difficile (Manuel, PDF p. 193).
    for (const Volume& other : query.passable) {
        if (discMeetsVolume(x, y, query.mover.radius, other)) {
            factor = 2.0f;
            break;
        }
    }
    return factor;
}

SimulatedSpace::Search SimulatedSpace::explore(const RouteQuery& query, float limit) const {
    const int cols = columns();
    const int lines = rows();
    const int count = cols * lines;
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
            if (next.column < 0 || next.row < 0 || next.column >= cols || next.row >= lines) {
                continue;
            }
            const Meters3 there = pointOf(next);
            const float step = groundDistance(here, there);
            if (limit >= 0.0f && cost + step > limit + EPSILON) {
                continue;
            }
            if (!standable(there, query) || !passage(here, there, query)) {
                continue;
            }
            const float total = cost + step * entryFactor(here, there, query);
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

Route SimulatedSpace::routeTo(const Search& search, int startIndex, int index) const {
    const int cols = columns();
    Route result{{}, search.cost[static_cast<std::size_t>(index)]};
    for (int at = index; at != startIndex && at >= 0;
         at = search.previous[static_cast<std::size_t>(at)]) {
        result.points.push_back(pointOf({at % cols, at / cols}));
    }
    std::reverse(result.points.begin(), result.points.end());
    return result;
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
    Route result = routeTo(search, startIndex, goalIndex);
    // La destination exacte termine le chemin si le dernier pas est dégagé.
    const Meters3 exact{query.destination.x, query.destination.y,
                        groundHeight(query.destination.x, query.destination.y)};
    const Meters3 last = result.points.empty() ? query.mover.base : result.points.back();
    const float tail = groundDistance(last, exact);
    if (tail > EPSILON && standable(exact, query) && passage(last, exact, query)) {
        const float total = result.length + tail * entryFactor(last, exact, query);
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

std::vector<Destination> SimulatedSpace::candidates(const RouteQuery& query) const {
    std::vector<Destination> result;
    result.push_back({query.mover.base, {}});
    const Search search = explore(query, query.budget);
    const int cols = columns();
    const Node start = nearestNode(query.mover.base);
    const int startIndex = start.row * cols + start.column;
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
            Route path = routeTo(search, startIndex, static_cast<int>(index));
            if (path.points.empty()) {
                // Le nœud du départ, à l'écart du point de départ exact : un pas de rien.
                path.points.push_back(point);
            }
            result.push_back({point, std::move(path)});
        }
    }
    return result;
}

}  // namespace core
