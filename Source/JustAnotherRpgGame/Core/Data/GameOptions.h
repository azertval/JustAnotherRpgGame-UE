// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

/**
 * @file Core/Data/GameOptions.h
 * @brief Les **options du jeu** en fichier texte (`LOT-1014`) : définition, échelle de rendu,
 *        qualité des ombres, volume.
 *
 * ## Le fichier
 *
 *     { "version": 1,
 *       "display":   { "width": 1920, "height": 1080, "fullscreen": true },
 *       "rendering": { "renderScalePercent": 100, "shadowQuality": 3 },
 *       "audio":     { "volumePercent": 100 } }
 *
 * | Champ | Ce qu'il règle | Bornes |
 * |---|---|---|
 * | `display.width` | la largeur de la fenêtre, en pixels | 640 à 7680 |
 * | `display.height` | sa hauteur, en pixels | 360 à 4320 |
 * | `display.fullscreen` | le jeu occupe tout l'écran | booléen |
 * | `rendering.renderScalePercent` | la définition du rendu, en % de la fenêtre | 50 à 200 |
 * | `rendering.shadowQuality` | le palier de qualité des ombres du moteur | 0 à 4 |
 * | `audio.volumePercent` | le volume général | 0 à 100 |
 *
 * ## Deux fichiers, lus l'un sur l'autre
 *
 * Le dépôt porte les valeurs d'usine (`Source/Elements/Options/options.json`) ; le poste du joueur
 * peut porter les siennes. Un fichier se lit **sur une base** : un champ absent garde la valeur de
 * la base, un champ présent la remplace. Lire le fichier du joueur sur celui du dépôt donne donc
 * les réglages du joueur, complétés par ceux d'usine.
 *
 * ## Un champ faux ne fait pas tomber les autres
 *
 * Une valeur du mauvais type ou hors de ses bornes est une **erreur nommée**, et le champ garde la
 * valeur de la base ; les autres champs se lisent. Un champ que le lecteur ne connaît pas est une
 * erreur aussi : une faute de frappe (`volumPercent`) ne doit pas passer pour un réglage. Aucune
 * lecture ne lève (`EX-NFR-040`).
 *
 * Logique pure : ce lecteur ne règle rien. Le moteur applique les valeurs lues
 * (`Bridge/JadgOptions`).
 */

namespace core {

/// Version du format écrite dans le fichier, et plus élevée qui soit lue.
inline constexpr int GAME_OPTIONS_FORMAT_VERSION = 1;

/// @brief Le fichier des options, relatif au dossier des données de contenu.
inline constexpr std::string_view GAME_OPTIONS_FILE = "Options/options.json";

/// @brief Les options du jeu. Les valeurs par défaut sont celles du moteur et de la capture de
///        référence (1920 × 1080) : appliquées, elles ne changent pas l'image.
struct GameOptions {
    /// La définition de la fenêtre, en pixels.
    int width = 1920;
    int height = 1080;
    /// Le jeu occupe tout l'écran.
    bool fullscreen = true;
    /// La définition du rendu, en pourcentage de celle de la fenêtre.
    int renderScalePercent = 100;
    /// Le palier de qualité des ombres du moteur, de 0 (bas) à 4.
    int shadowQuality = 3;
    /// Le volume général, de 0 à 100.
    int volumePercent = 100;

    [[nodiscard]] bool operator==(const GameOptions&) const = default;
};

/// @brief Ce qu'une lecture rend : les options, et ce qui n'a pas pu être lu.
struct GameOptionsResult {
    /// La base, corrigée par chaque champ lu sans erreur.
    GameOptions options{};
    /// Une ligne par champ refusé, ou l'échec de lecture du document. Vide si tout est lu.
    std::vector<std::string> errors;
    /// Faux si le fichier est absent : `options` est alors la base, sans erreur.
    bool found = false;

    [[nodiscard]] bool ok() const {
        return errors.empty();
    }
};

/**
 * @brief Lit des options écrites en JSON, sur une base.
 * @param json Le texte du document.
 * @param base Les valeurs que gardent les champs absents ou refusés.
 * @param origin Nom à faire figurer dans les messages. Facultatif.
 * @return Les options et les erreurs. Ne lève jamais.
 */
[[nodiscard]] GameOptionsResult readGameOptions(std::string_view json, const GameOptions& base = {},
                                                std::string_view origin = {});

/**
 * @brief Comme `readGameOptions`, en lisant d'abord le fichier.
 *
 * Un fichier **absent** n'est pas une erreur : le joueur qui n'a rien réglé n'a pas de fichier.
 * Le résultat porte alors la base et `found == false`.
 */
[[nodiscard]] GameOptionsResult loadGameOptions(const std::filesystem::path& file,
                                                const GameOptions& base = {});

}  // namespace core
