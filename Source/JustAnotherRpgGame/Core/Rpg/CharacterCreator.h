// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Rpg/CharacterCreator.h
 * @brief La description du créateur de personnage (LOT-1015, D-63) : les corps, les clips, les
 *        sockets que l'objet personnalisable du moteur et l'acteur du jeu partagent.
 *
 * `Source/Elements/Assets/Characters/<id>.json` est la **source** du créateur : le commandlet
 * `JadgBuildCharacterCreator` en construit l'asset Mutable (D-52 : la sortie se régénère), et
 * l'acteur y lit, pour une fiche d'apparence, le maillage d'un corps, le clip d'un nom, le socket
 * d'une main. Core la lit et ne connaît ni Mutable ni les assets : ce sont des chemins de texte.
 */

#include <filesystem>
#include <map>
#include <string>
#include <string_view>

#include "Core/Data/JsonDocument.h"

namespace core {

struct CharacterCreator {
    std::string id;
    /// L'objet personnalisable, en chemin de contenu (`/Game/Characters/Creator/CO_Humanoid`).
    std::string asset;
    /// Le nom du composant squelettique de l'objet personnalisable (`Body`).
    std::string component;
    /// Le squelette commun des corps, en chemin de contenu.
    std::string skeleton;
    /// La taille, en mètres, qu'un corps a sans mise à l'échelle.
    float referenceHeight = 0.0F;
    /// Option du paramètre `Body` -> chemin de contenu du maillage squelettique.
    std::map<std::string, std::string> bodies;
    /// Nom du clip -> chemin de contenu de l'animation.
    std::map<std::string, std::string> clips;
    /// `main-hand`, `off-hand` -> nom du socket (os) qui porte l'arme.
    std::map<std::string, std::string> sockets;
    /// Le dossier de contenu des armes au maître (`/Game/Master/Weapons`).
    std::string weapons;
};

struct CharacterCreatorReadResult {
    CharacterCreator creator;
    JsonReadError error = JsonReadError::None;
    std::string message;

    [[nodiscard]] bool ok() const {
        return error == JsonReadError::None;
    }
};

/// @brief Lit une description depuis son texte. Refuse un corps ou un clip sans chemin `/Game/…`.
[[nodiscard]] CharacterCreatorReadResult parseCharacterCreator(std::string_view json,
                                                               std::string_view origin = {});

/// @brief Comme `parseCharacterCreator`, en lisant d'abord le fichier.
[[nodiscard]] CharacterCreatorReadResult readCharacterCreator(const std::filesystem::path& path);

}  // namespace core
