// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <filesystem>
#include <map>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

/**
 * @file Core/Ui/UiStyle.h
 * @brief Le **style des écrans** en fichier texte (LOT-1020) : couleurs, polices, tailles,
 *        espacements et pièces du kit `UI` (`Source/Elements/Assets/UI/style.json`).
 *
 * La charte v2 (LOT-87) tenait ces grandeurs dans `Tokens.qml` et le cahier des assets ; le nouveau
 * moteur les lit ici, une seule fois, au lancement (`EX-IHM-051`) — aucun asset de style.
 *
 *     { "version": 1,
 *       "design": [1920, 1080],
 *       "colours": { "panel": "#0c0c0c", "panelEdge": "#e4a43c" },
 *       "fonts":   { "title": "Cinzel-SemiBold.ttf", "body": "IMFellEnglish-Regular.ttf" },
 *       "sizes":   { "screenTitle": 36, "section": 24, "body": 18, "caption": 14 },
 *       "spacing": { "small": 8, "medium": 16, "large": 32 },
 *       "pieces":  { "frame/panel-dark": { "size": [512, 512], "margins": [112, 112, 112, 112] },
 *                    "button/default":   { "size": [280, 56], "margins": [48, 0, 48, 0],
 *                                          "states": ["normal", "hover", "pressed", "disabled"] } }
 * }
 *
 * | Champ | Ce qu'il porte |
 * |---|---|
 * | `design` | la définition de conception : les grandeurs sont écrites pour elle, en pixels |
 * | `colours` | un rôle → `#rrggbb` ou `#rrggbbaa`, relevé (LOT-66, LOT-87), jamais choisi à vue |
 * | `fonts` | un rôle → un fichier de `Source/Elements/Assets/Fonts/` |
 * | `sizes` | un rôle → une taille de police, en pixels à la définition de conception |
 * | `spacing` | un rôle → un écart, en pixels à la définition de conception |
 * | `pieces` | une pièce du kit `UI`, par son chemin sans extension : sa taille, ses marges 9-patch
 * (gauche, haut, droite, bas) s'il en a, ses états — chaque état est l'image `<pièce>/<état>.png` |
 *
 * Une pièce sans `margins` a une taille fixe : elle ne s'étire pas (`EX-IHM-075`).
 *
 * Logique pure : aucune dépendance au moteur. Une valeur fausse est une erreur nommée, et le reste
 * se lit ; aucune lecture ne lève.
 */

namespace core {

/// Version du format écrite dans le fichier, et plus élevée qui soit lue.
inline constexpr int UI_STYLE_FORMAT_VERSION = 1;

/// Une couleur, composantes de 0 à 1, dans l'espace sRGB du fichier.
struct UiColour {
    float red = 0.0F;
    float green = 0.0F;
    float blue = 0.0F;
    float alpha = 1.0F;

    [[nodiscard]] bool operator==(const UiColour&) const = default;
};

/// Les marges 9-patch d'une pièce, en pixels de son image.
struct UiMargins {
    int left = 0;
    int top = 0;
    int right = 0;
    int bottom = 0;

    [[nodiscard]] bool operator==(const UiMargins&) const = default;
};

/// Une pièce du kit `UI`.
struct UiPiece {
    /// Son chemin dans le kit, sans extension : `frame/panel-dark`.
    std::string id;
    int width = 0;
    int height = 0;
    /// Absentes : la pièce a une taille fixe.
    std::optional<UiMargins> margins;
    /// Ses états, chacun une image `<id>/<état>.png` ; vide : l'image `<id>.png`.
    std::vector<std::string> states;

    /// Le fichier de l'état @p state, relatif au kit ; celui de la pièce si elle n'a pas d'états.
    [[nodiscard]] std::string file(std::string_view state = {}) const;
};

/// Le style des écrans.
struct UiStyle {
    int designWidth = 1920;
    int designHeight = 1080;
    std::map<std::string, UiColour, std::less<>> colours;
    std::map<std::string, std::string, std::less<>> fonts;
    std::map<std::string, int, std::less<>> sizes;
    std::map<std::string, int, std::less<>> spacing;
    std::map<std::string, UiPiece, std::less<>> pieces;
};

/// Ce qu'une lecture rend : le style, et ce qui n'a pas pu être lu.
struct UiStyleResult {
    UiStyle style;
    std::vector<std::string> errors;

    [[nodiscard]] bool ok() const noexcept {
        return errors.empty();
    }
};

/// Lit `#rrggbb` ou `#rrggbbaa` ; rien si l'écriture est fausse.
[[nodiscard]] std::optional<UiColour> parseUiColour(std::string_view text);

/// Lit un style écrit en JSON. Ne lève jamais.
[[nodiscard]] UiStyleResult readUiStyle(std::string_view json, std::string_view origin = {});

/// Comme `readUiStyle`, en lisant d'abord le fichier ; un fichier absent est une erreur.
[[nodiscard]] UiStyleResult loadUiStyle(const std::filesystem::path& file);

}  // namespace core
