// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Rpg/Appearance.h
 * @brief L'apparence d'un personnage : la fiche que le créateur de personnage assemble (LOT-1015,
 *        D-63).
 *
 * Un personnage n'est plus un maillage qui lui est propre (D-38) : c'est une **fiche texte** qui
 * donne les valeurs des paramètres d'un objet personnalisable du moteur (Mutable). Core lit la
 * fiche et ne connaît pas Mutable : le moteur traduit chaque champ en paramètre. La fiche de
 * règles (`Rpg/characters/`) et la fiche d'apparence (`Rpg/appearances/`) portent le **même
 * identifiant** : deux fiches liées plutôt qu'une seule, parce que la première est jouée par les
 * règles et la seconde par le moteur, et qu'un PNJ sans fiche de règles (la mère, l'enfant) a
 * quand même une apparence.
 */

#include <filesystem>
#include <map>
#include <string>
#include <string_view>
#include <vector>

#include "Core/Data/JsonDocument.h"

namespace core {

/// @brief Une couleur linéaire, composantes de 0 à 1.
struct AppearanceColor {
    float r = 0.0F;
    float g = 0.0F;
    float b = 0.0F;
    float a = 1.0F;
};

/**
 * @brief Ce que `appearance.schema.json` décrit.
 *
 * `body` et `head` sont des options de paramètres de choix du créateur ; `pieces` les options
 * des emplacements (torse, jambes, pieds, cheveux, barbe, cornes…) ; `colors` les paramètres de
 * couleur ; `weapons` l'arme de chaque main, une pièce des maîtres (`Master/Weapons`) accrochée
 * par socket ; `clips` l'instant d'impact des clips de combat, en secondes, que le combat attend
 * pour toucher la cible.
 */
struct Appearance {
    std::string id;
    std::string name;
    std::string source;
    std::string creator;
    std::string body;
    std::string head;
    /// Du sol au sommet du crâne, en mètres.
    float height = 0.0F;
    std::map<std::string, AppearanceColor> colors;
    std::map<std::string, std::string> pieces;
    /// Clé : `main-hand` ou `off-hand` ; valeur : l'identifiant de la pièce
    /// (`Weapons/brawler-axe`).
    std::map<std::string, std::string> weapons;
    /// Clé : le nom du clip ; valeur : son instant d'impact en secondes.
    std::map<std::string, float> clipKeys;
};

/// @brief Le résultat de la lecture d'une fiche : l'apparence, ou l'échec décrit.
struct AppearanceReadResult {
    Appearance appearance;
    JsonReadError error = JsonReadError::None;
    std::string message;

    [[nodiscard]] bool ok() const {
        return error == JsonReadError::None;
    }
};

/**
 * @brief Lit une fiche d'apparence depuis son texte JSON.
 *
 * Refuse, avec la raison et le chemin du champ : un champ obligatoire absent (`creator`,
 * `body`, `head`, `height`), une taille nulle ou négative, une couleur hors de 0 à 1 ou qui n'a
 * pas trois ou quatre composantes, une main qui n'est ni `main-hand` ni `off-hand`, un `key`
 * négatif. Ne lève jamais.
 *
 * @param json Le texte de la fiche.
 * @param origin Le nom à faire figurer dans les messages.
 */
[[nodiscard]] AppearanceReadResult parseAppearance(std::string_view json,
                                                   std::string_view origin = {});

/// @brief Comme `parseAppearance`, en lisant d'abord le fichier.
[[nodiscard]] AppearanceReadResult readAppearance(const std::filesystem::path& path);

/**
 * @brief Lit toutes les fiches d'un dossier (`Rpg/appearances/`), par identifiant.
 *
 * Une fiche illisible est **écartée** et son message ajouté à `errors` ; les autres sont lues.
 * Un identifiant qui ne correspond pas au nom du fichier est une erreur : c'est par lui que la
 * fiche de règles et la scène retrouvent l'apparence.
 */
[[nodiscard]] std::map<std::string, Appearance> loadAppearances(
    const std::filesystem::path& directory, std::vector<std::string>& errors);

}  // namespace core
