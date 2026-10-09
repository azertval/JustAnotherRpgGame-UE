// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Ui/MapInteractions.h"

#include <string>

#include <nlohmann/json.hpp>

#include "Core/Data/JsonDocument.h"

namespace core {

namespace {

using Json = nlohmann::json;

constexpr int MAP_INTERACTIONS_FORMAT_VERSION = 1;

// Une zone lue : son image et sa bannière ; faux, avec l'erreur, si l'une manque.
bool readZone(const std::string& id, const std::string& parent, const Json& value, bool neighbour,
              std::string_view origin, MapInteractions& out) {
    const std::string where =
        std::string(origin) + " : " + id + (neighbour ? " (" + parent + ")" : "");
    if (!value.is_object() || !value.contains("image") || !value["image"].is_string()) {
        out.errors.push_back(where + " : no image");
        return false;
    }
    MapZone zone{.id = id,
                 .parent = parent,
                 .image = value["image"].get<std::string>(),
                 .neighbour = neighbour};
    if (value.contains("label")) {
        const Json& label = value["label"];
        if (!label.is_array() || label.size() != 4) {
            out.errors.push_back(where + " : label is not [x, y, width, height]");
            return false;
        }
        for (std::size_t index = 0; index < 4; ++index) {
            if (!label[index].is_number()) {
                out.errors.push_back(where + " : label is not [x, y, width, height]");
                return false;
            }
            zone.label[index] = label[index].get<float>();
        }
    }
    out.zones.push_back(std::move(zone));
    return true;
}

MapInteractions interactionsFrom(const JsonDocument& document, std::string_view origin) {
    MapInteractions out;
    if (!document.ok()) {
        out.errors.push_back(document.message);
        return out;
    }
    const Json& root = document.root;
    if (root.contains("entries") && root["entries"].is_object()) {
        for (const auto& [id, value] : root["entries"].items()) {
            const std::string parent =
                value.is_object() && value.contains("parent") && value["parent"].is_string()
                    ? value["parent"].get<std::string>()
                    : std::string();
            if (parent.empty()) {
                out.errors.push_back(std::string(origin) + " : " + id + " : no parent");
                continue;
            }
            (void)readZone(id, parent, value, false, origin, out);
        }
    } else {
        out.errors.push_back(std::string(origin) + " : no entries");
    }
    if (root.contains("neighbours") && root["neighbours"].is_object()) {
        for (const auto& [id, others] : root["neighbours"].items()) {
            if (!others.is_object()) {
                continue;
            }
            for (const auto& [parent, value] : others.items()) {
                (void)readZone(id, parent, value, true, origin, out);
            }
        }
    }
    return out;
}

}  // namespace

std::vector<const MapZone*> MapInteractions::childrenOf(std::string_view node) const {
    std::vector<const MapZone*> found;
    for (const MapZone& zone : zones) {
        if (zone.parent == node) {
            found.push_back(&zone);
        }
    }
    return found;
}

std::string MapInteractions::imageOf(std::string_view node) const {
    for (const MapZone& zone : zones) {
        if (zone.parent == node && !zone.neighbour) {
            return zone.image;
        }
    }
    return {};
}

std::string MapInteractions::parentOf(std::string_view id) const {
    for (const MapZone& zone : zones) {
        if (zone.id == id && !zone.neighbour) {
            return zone.parent;
        }
    }
    return {};
}

MapInteractions readMapInteractions(std::string_view json, std::string_view origin) {
    return interactionsFrom(readJsonObject(json, MAP_INTERACTIONS_FORMAT_VERSION, origin), origin);
}

MapInteractions loadMapInteractions(const std::filesystem::path& file) {
    return interactionsFrom(readJsonObjectFromFile(file, MAP_INTERACTIONS_FORMAT_VERSION),
                            file.filename().string());
}

}  // namespace core
