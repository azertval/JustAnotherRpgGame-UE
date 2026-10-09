// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Data/GameOptions.h"

#include <algorithm>
#include <array>
#include <string>
#include <string_view>
#include <system_error>

#include <nlohmann/json.hpp>

#include "Core/Data/JsonDocument.h"

namespace core {

namespace {

using Json = nlohmann::json;

// Un champ entier : sa section, son nom, où il se range, ses bornes.
struct IntegerField {
    std::string_view section;
    std::string_view name;
    int GameOptions::* member;
    int low;
    int high;
};

// Un champ booléen : sa section, son nom, où il se range.
struct FlagField {
    std::string_view section;
    std::string_view name;
    bool GameOptions::* member;
};

// La table du format : une seule écriture de chaque nom et de chaque borne.
constexpr std::array<std::string_view, 4> SECTIONS{"display", "rendering", "audio", "interface"};
constexpr std::array<IntegerField, 5> INTEGERS{{
    {"display", "width", &GameOptions::width, 640, 7680},
    {"display", "height", &GameOptions::height, 360, 4320},
    {"rendering", "renderScalePercent", &GameOptions::renderScalePercent, 50, 200},
    {"rendering", "shadowQuality", &GameOptions::shadowQuality, 0, 4},
    {"audio", "volumePercent", &GameOptions::volumePercent, 0, 100},
}};
constexpr std::array<FlagField, 1> FLAGS{{
    {"display", "fullscreen", &GameOptions::fullscreen},
}};

// Un code de langue : deux lettres minuscules (« fr », « en »).
[[nodiscard]] bool isLanguageCode(const std::string& code) {
    return code.size() == 2 && std::all_of(code.begin(), code.end(), [](char letter) {
               return letter >= 'a' && letter <= 'z';
           });
}

[[nodiscard]] std::string prefixed(std::string_view origin, const std::string& message) {
    return origin.empty() ? message : std::string(origin) + " : " + message;
}

void readSection(std::string_view section, const Json& object, std::string_view origin,
                 GameOptionsResult& result) {
    for (const auto& [key, value] : object.items()) {
        if (key == "comment") {
            continue;
        }
        const std::string where = std::string(section) + "." + key;
        bool known = false;
        for (const IntegerField& field : INTEGERS) {
            if (field.section != section || field.name != key) {
                continue;
            }
            known = true;
            if (!value.is_number_integer()) {
                result.errors.push_back(prefixed(origin, where + " is not an integer"));
            } else if (const auto read = value.get<long long>();
                       read < field.low || read > field.high) {
                result.errors.push_back(prefixed(origin, where + " out of range [" +
                                                             std::to_string(field.low) + ", " +
                                                             std::to_string(field.high) + "]"));
            } else {
                result.options.*field.member = static_cast<int>(read);
            }
        }
        for (const FlagField& field : FLAGS) {
            if (field.section != section || field.name != key) {
                continue;
            }
            known = true;
            if (!value.is_boolean()) {
                result.errors.push_back(prefixed(origin, where + " is not a boolean"));
            } else {
                result.options.*field.member = value.get<bool>();
            }
        }
        if (section == "interface" && key == "language") {
            known = true;
            if (!value.is_string() || !isLanguageCode(value.get<std::string>())) {
                result.errors.push_back(prefixed(origin, where + " is not a language code"));
            } else {
                result.options.language = value.get<std::string>();
            }
        }
        if (!known) {
            result.errors.push_back(prefixed(origin, where + " is not a known option"));
        }
    }
}

[[nodiscard]] GameOptionsResult optionsFrom(const JsonDocument& document, const GameOptions& base,
                                            std::string_view origin) {
    GameOptionsResult result{.options = base, .errors = {}, .found = true};
    if (!document.ok()) {
        result.errors.push_back(document.message);
        return result;
    }
    for (const auto& [key, value] : document.root.items()) {
        if (key == "version" || key == "comment") {
            continue;
        }
        if (std::find(SECTIONS.begin(), SECTIONS.end(), key) == SECTIONS.end()) {
            result.errors.push_back(prefixed(origin, key + " is not a known section"));
        } else if (!value.is_object()) {
            result.errors.push_back(prefixed(origin, key + " is not an object"));
        } else {
            readSection(key, value, origin, result);
        }
    }
    return result;
}

}  // namespace

GameOptionsResult readGameOptions(std::string_view json, const GameOptions& base,
                                  std::string_view origin) {
    return optionsFrom(readJsonObject(json, GAME_OPTIONS_FORMAT_VERSION, origin), base, origin);
}

GameOptionsResult loadGameOptions(const std::filesystem::path& file, const GameOptions& base) {
    std::error_code ignored;
    if (!std::filesystem::exists(file, ignored)) {
        return GameOptionsResult{.options = base, .errors = {}, .found = false};
    }
    return optionsFrom(readJsonObjectFromFile(file, GAME_OPTIONS_FORMAT_VERSION), base,
                       file.filename().string());
}

std::string writeGameOptions(const GameOptions& options) {
    Json document = Json::object();
    document["version"] = GAME_OPTIONS_FORMAT_VERSION;
    for (const IntegerField& field : INTEGERS) {
        document[std::string(field.section)][std::string(field.name)] = options.*field.member;
    }
    for (const FlagField& field : FLAGS) {
        document[std::string(field.section)][std::string(field.name)] = options.*field.member;
    }
    document["interface"]["language"] = options.language;
    return document.dump(2) + "\n";
}

}  // namespace core
