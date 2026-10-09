// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Ui/UiStyle.h"

#include <string>
#include <string_view>

#include <nlohmann/json.hpp>

#include "Core/Data/JsonDocument.h"

namespace core {

namespace {

using Json = nlohmann::json;

[[nodiscard]] std::string prefixed(std::string_view origin, const std::string& message) {
    return origin.empty() ? message : std::string(origin) + " : " + message;
}

[[nodiscard]] int hexDigit(char letter) {
    if (letter >= '0' && letter <= '9') {
        return letter - '0';
    }
    if (letter >= 'a' && letter <= 'f') {
        return letter - 'a' + 10;
    }
    if (letter >= 'A' && letter <= 'F') {
        return letter - 'A' + 10;
    }
    return -1;
}

// Une table rôle → entier positif.
void readIntegers(const Json& object, std::string_view field, std::string_view origin,
                  std::map<std::string, int, std::less<>>& out, std::vector<std::string>& errors) {
    for (const auto& [key, value] : object.items()) {
        if (!value.is_number_integer() || value.get<long long>() <= 0 ||
            value.get<long long>() > 4096) {
            errors.push_back(
                prefixed(origin, std::string(field) + "." + key + " is not a size in pixels"));
            continue;
        }
        out[key] = value.get<int>();
    }
}

[[nodiscard]] bool readPair(const Json& value, int& first, int& second) {
    if (!value.is_array() || value.size() != 2 || !value[0].is_number_integer() ||
        !value[1].is_number_integer()) {
        return false;
    }
    first = value[0].get<int>();
    second = value[1].get<int>();
    return first > 0 && second > 0;
}

void readPiece(const std::string& id, const Json& value, std::string_view origin,
               UiStyleResult& result) {
    const std::string where = "pieces." + id;
    if (!value.is_object()) {
        result.errors.push_back(prefixed(origin, where + " is not an object"));
        return;
    }
    UiPiece piece{.id = id};
    if (!value.contains("size") || !readPair(value["size"], piece.width, piece.height)) {
        result.errors.push_back(prefixed(origin, where + ".size is not [width, height]"));
        return;
    }
    if (value.contains("margins")) {
        const Json& margins = value["margins"];
        bool valid = margins.is_array() && margins.size() == 4;
        for (std::size_t index = 0; valid && index < 4; ++index) {
            valid = margins[index].is_number_integer() && margins[index].get<int>() >= 0;
        }
        if (!valid) {
            result.errors.push_back(
                prefixed(origin, where + ".margins is not [left, top, right, bottom]"));
            return;
        }
        piece.margins = UiMargins{margins[0].get<int>(), margins[1].get<int>(),
                                  margins[2].get<int>(), margins[3].get<int>()};
        if (piece.margins->left + piece.margins->right > piece.width ||
            piece.margins->top + piece.margins->bottom > piece.height) {
            result.errors.push_back(prefixed(origin, where + ".margins exceed the piece"));
            return;
        }
    }
    if (value.contains("states")) {
        for (const Json& state : value["states"]) {
            if (!state.is_string() || state.get<std::string>().empty()) {
                result.errors.push_back(prefixed(origin, where + ".states holds a non-name"));
                return;
            }
            piece.states.push_back(state.get<std::string>());
        }
    }
    for (const auto& [key, ignored] : value.items()) {
        if (key != "size" && key != "margins" && key != "states" && key != "comment") {
            result.errors.push_back(prefixed(origin, where + "." + key + " is not a known field"));
        }
    }
    result.style.pieces[id] = std::move(piece);
}

[[nodiscard]] UiStyleResult styleFrom(const JsonDocument& document, std::string_view origin) {
    UiStyleResult result;
    if (!document.ok()) {
        result.errors.push_back(document.message);
        return result;
    }
    for (const auto& [key, value] : document.root.items()) {
        if (key == "version" || key == "comment") {
            continue;
        }
        if (key == "design") {
            if (!readPair(value, result.style.designWidth, result.style.designHeight)) {
                result.errors.push_back(prefixed(origin, "design is not [width, height]"));
            }
            continue;
        }
        if (!value.is_object()) {
            result.errors.push_back(prefixed(origin, key + " is not an object"));
            continue;
        }
        if (key == "colours") {
            for (const auto& [role, text] : value.items()) {
                const auto colour =
                    text.is_string() ? parseUiColour(text.get<std::string>()) : std::nullopt;
                if (!colour) {
                    result.errors.push_back(
                        prefixed(origin, "colours." + role + " is not #rrggbb"));
                } else {
                    result.style.colours[role] = *colour;
                }
            }
        } else if (key == "fonts") {
            for (const auto& [role, file] : value.items()) {
                if (!file.is_string() || file.get<std::string>().empty()) {
                    result.errors.push_back(
                        prefixed(origin, "fonts." + role + " is not a file name"));
                } else {
                    result.style.fonts[role] = file.get<std::string>();
                }
            }
        } else if (key == "sizes") {
            readIntegers(value, key, origin, result.style.sizes, result.errors);
        } else if (key == "spacing") {
            readIntegers(value, key, origin, result.style.spacing, result.errors);
        } else if (key == "pieces") {
            for (const auto& [id, piece] : value.items()) {
                readPiece(id, piece, origin, result);
            }
        } else {
            result.errors.push_back(prefixed(origin, key + " is not a known section"));
        }
    }
    return result;
}

}  // namespace

std::string UiPiece::file(std::string_view state) const {
    if (states.empty()) {
        return id + ".png";
    }
    return id + "/" + std::string(state.empty() ? std::string_view(states.front()) : state) +
           ".png";
}

std::optional<UiColour> parseUiColour(std::string_view text) {
    if ((text.size() != 7 && text.size() != 9) || text.front() != '#') {
        return std::nullopt;
    }
    float channels[4] = {0.0F, 0.0F, 0.0F, 1.0F};
    for (std::size_t index = 0; index * 2 + 1 < text.size(); ++index) {
        const int high = hexDigit(text[1 + index * 2]);
        const int low = hexDigit(text[2 + index * 2]);
        if (high < 0 || low < 0) {
            return std::nullopt;
        }
        channels[index] = static_cast<float>(high * 16 + low) / 255.0F;
    }
    return UiColour{channels[0], channels[1], channels[2], channels[3]};
}

UiStyleResult readUiStyle(std::string_view json, std::string_view origin) {
    return styleFrom(readJsonObject(json, UI_STYLE_FORMAT_VERSION, origin), origin);
}

UiStyleResult loadUiStyle(const std::filesystem::path& file) {
    return styleFrom(readJsonObjectFromFile(file, UI_STYLE_FORMAT_VERSION),
                     file.filename().string());
}

}  // namespace core
