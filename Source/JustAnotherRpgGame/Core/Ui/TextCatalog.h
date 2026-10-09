// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <filesystem>
#include <string>
#include <string_view>
#include <unordered_map>
#include <vector>

/**
 * @file Core/Ui/TextCatalog.h
 * @brief Le **catalogue des textes** du jeu : un fichier `<langue>.lang` par langue (LOT-1020).
 *
 * ## Le format, décidé au LOT-1020
 *
 *     # commentaire
 *     dialogue.check.announce = %1 · DD %2
 *
 * Une paire `clé = valeur` par ligne, en UTF-8 ; les lignes vides et celles qui commencent par `#`
 * sont ignorées ; seul le premier `=` sépare, les espaces de bord sont retirés. Les clés sont des
 * identifiants anglais (`domaine.nom`), les mêmes dans chaque langue ; un **trou** s'écrit `%1` à
 * `%9`, dans l'ordre des arguments.
 *
 * Le catalogue Qt Linguist de l'ancien jeu (`jadg_en.ts`, des phrases françaises traduites) est
 * retiré : les écrans du nouveau moteur nomment leurs textes par clé, comme les données du jeu.
 *
 * ## Dans le moteur
 *
 * Le moteur charge chaque catalogue dans une **table de chaînes** (`FStringTable`) et les écrans
 * prennent leurs textes en `FText` depuis elle ; ses trous s'écrivent `{0}`, `{1}`… :
 * `toEngineFormat` les traduit, et protège les accolades de la valeur.
 *
 * Logique pure : aucune dépendance au moteur.
 */

namespace core {

/// Une table clé → texte, telle qu'un fichier `.lang` la donne.
using TextTable = std::unordered_map<std::string, std::string>;

/**
 * @brief Lit le contenu d'un fichier `.lang`.
 * @param content Le texte, UTF-8 ; une marque d'ordre des octets en tête est ignorée.
 * @return La table ; une clé répétée garde sa dernière valeur.
 */
[[nodiscard]] TextTable parseTextCatalog(std::string_view content);

/**
 * @brief Lit le fichier @p file.
 * @return La table ; vide si le fichier ne se lit pas.
 */
[[nodiscard]] TextTable loadTextCatalog(const std::filesystem::path& file);

/// Les numéros des trous de @p text (`%1` → 1), triés, chacun une fois.
[[nodiscard]] std::vector<int> textPlaceholders(std::string_view text);

/**
 * @brief Remplit les trous de @p text : `%1` par le premier argument, `%2` par le second…
 *
 * Un trou sans argument reste écrit tel quel : il se voit à l'écran, au lieu de disparaître.
 */
[[nodiscard]] std::string formatText(std::string_view text,
                                     const std::vector<std::string>& arguments);

/**
 * @brief Le texte dans l'écriture des formats de texte du moteur : `%1` devient `{0}`, `%2` `{1}` ;
 *        `{`, `}` et le caractère d'échappement `` ` `` de la valeur sont protégés par `` ` ``.
 */
[[nodiscard]] std::string toEngineFormat(std::string_view text);

}  // namespace core
