// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Ui/TextCatalog.h"

#include <algorithm>
#include <fstream>
#include <iterator>
#include <string>
#include <string_view>

namespace core {

namespace {

[[nodiscard]] std::string_view trim(std::string_view text) {
    const auto blank = [](char letter) {
        return letter == ' ' || letter == '\t' || letter == '\r';
    };
    while (!text.empty() && blank(text.front())) {
        text.remove_prefix(1);
    }
    while (!text.empty() && blank(text.back())) {
        text.remove_suffix(1);
    }
    return text;
}

// Le numéro du trou qui commence en @p at (`%1` à `%9`) ; 0 s'il n'y en a pas.
[[nodiscard]] int placeholderAt(std::string_view text, std::size_t at) {
    if (at + 1 >= text.size() || text[at] != '%') {
        return 0;
    }
    const char digit = text[at + 1];
    return digit >= '1' && digit <= '9' ? digit - '0' : 0;
}

}  // namespace

TextTable parseTextCatalog(std::string_view content) {
    constexpr std::string_view BOM = "\xEF\xBB\xBF";
    if (content.starts_with(BOM)) {
        content.remove_prefix(BOM.size());
    }
    TextTable table;
    while (!content.empty()) {
        const std::size_t newline = content.find('\n');
        const std::string_view line = trim(content.substr(0, newline));
        content =
            newline == std::string_view::npos ? std::string_view{} : content.substr(newline + 1);
        if (line.empty() || line.front() == '#') {
            continue;
        }
        const std::size_t separator = line.find('=');
        if (separator == std::string_view::npos) {
            continue;
        }
        const std::string_view key = trim(line.substr(0, separator));
        if (!key.empty()) {
            table.insert_or_assign(std::string(key), std::string(trim(line.substr(separator + 1))));
        }
    }
    return table;
}

TextTable loadTextCatalog(const std::filesystem::path& file) {
    std::ifstream stream(file, std::ios::binary);
    if (!stream) {
        return {};
    }
    const std::string content{std::istreambuf_iterator<char>(stream),
                              std::istreambuf_iterator<char>()};
    return parseTextCatalog(content);
}

std::vector<int> textPlaceholders(std::string_view text) {
    std::vector<int> found;
    for (std::size_t at = 0; at < text.size(); ++at) {
        if (const int number = placeholderAt(text, at); number != 0) {
            found.push_back(number);
        }
    }
    std::ranges::sort(found);
    found.erase(std::unique(found.begin(), found.end()), found.end());
    return found;
}

std::string formatText(std::string_view text, const std::vector<std::string>& arguments) {
    std::string out;
    out.reserve(text.size());
    for (std::size_t at = 0; at < text.size(); ++at) {
        const int number = placeholderAt(text, at);
        if (number != 0 && static_cast<std::size_t>(number) <= arguments.size()) {
            out += arguments[static_cast<std::size_t>(number) - 1];
            ++at;
        } else {
            out += text[at];
        }
    }
    return out;
}

std::string toEngineFormat(std::string_view text) {
    std::string out;
    out.reserve(text.size() + 8);
    for (std::size_t at = 0; at < text.size(); ++at) {
        if (const int number = placeholderAt(text, at); number != 0) {
            out += '{';
            out += std::to_string(number - 1);
            out += '}';
            ++at;
            continue;
        }
        const char letter = text[at];
        if (letter == '{' || letter == '}' || letter == '`') {
            out += '`';
        }
        out += letter;
    }
    return out;
}

}  // namespace core
