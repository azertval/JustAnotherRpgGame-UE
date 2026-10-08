// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <string>

#include "Core/Levels/GridPosition.h"

/**
 * @file Core/Ecs/Components/Interactable.h
 * @brief Composant d'une entité de carte avec laquelle le joueur peut interagir (données pures).
 */

namespace core {

/**
 * @brief Marque une entité comme **cible d'interaction** et porte de quoi la désigner.
 *
 * Donnée pure sans logique (`EX-ARCH-011`). Le composant ne dit **pas** ce que l'interaction fait :
 * un coffre, un panneau et un PNJ portent le même composant et se distinguent par leur `type`,
 * que le gameplay interprète. `Core` ne connaît aucune sémantique de `type` — c'est la règle que
 * `core::MapEntity` pose déjà, et la reprendre ici évite qu'une énumération fermée oblige chaque
 * lot suivant à modifier ce fichier pour ajouter une famille.
 *
 * La **case** est portée en plus du `Transform` parce que l'interaction raisonne en cases, pas en
 * unités monde : la cible est « la case devant le personnage », et la retrouver depuis une position
 * flottante demanderait une division dont l'arrondi déciderait du résultat aux frontières.
 */
struct Interactable {
    /// Type de l'entité, libre : `"chest"`, `"sign"`, `"npc"`, `"portal"`…
    std::string type;

    /// Case occupée par l'entité.
    GridPosition position;

    /**
     * @brief Clé du drapeau de monde qui dit si cette interaction a **déjà eu lieu**.
     *
     * Vide pour une entité qu'on peut solliciter indéfiniment — un panneau se relit, un PNJ se
     * reparle. Renseignée pour ce qui ne se prend qu'une fois : le coffre. Voir
     * `core::keyForEntity()`, qui la fabrique.
     */
    std::string consumedFlag;

    /**
     * @brief Clé de localisation de l'invite affichée quand la cible est à portée.
     *
     * Une **clé**, jamais un texte : l'invite est de l'interface, et le `Core` n'écrit pas de
     * français. Vide pour une entité qui n'annonce rien.
     */
    std::string promptKey;

    /// @brief Vrai si l'interaction ne peut avoir lieu qu'une fois.
    [[nodiscard]] bool isConsumable() const {
        return !consumedFlag.empty();
    }
};

}  // namespace core
