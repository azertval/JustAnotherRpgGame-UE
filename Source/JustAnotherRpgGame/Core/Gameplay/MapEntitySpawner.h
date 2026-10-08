// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Gameplay/MapEntitySpawner.h
 * @brief Instanciation ECS des entités de la couche `objects` d'un niveau (`LOT-10`).
 */

#include <functional>
#include <string>
#include <string_view>
#include <vector>

#include "Core/Ecs/Entity.h"

namespace core {

class World;
class Level;
struct MapEntity;

/**
 * @brief Les types d'entité que ce lot sait rendre **interactifs**, et ce qu'ils consomment.
 *
 * Une table, et non un `if` par famille : le `LOT-15` y a ajouté les PNJ et le `LOT-09` les
 * portails, et chacun devrait sinon retoucher la même fonction. `Core` ne connaît aucune sémantique
 * de type
 * (`core::MapEntity`) ; il connaît en revanche **ce qui ne se prend qu'une fois**, qui est une
 * propriété structurelle et non un comportement.
 */
struct InteractableKind {
    /// Type de la couche `objects` : `"chest"`, `"sign"`…
    std::string_view type;
    /// Vrai si l'interaction ne peut avoir lieu qu'une fois — le coffre, pas le panneau.
    bool consumable = false;
    /// Clé de localisation de l'invite, ou vide.
    std::string_view promptKey;
};

/// @brief Les familles connues : coffre, panneau (`LOT-10`), PNJ (`LOT-15`). Le `LOT-09` ajoutera
/// les portails.
[[nodiscard]] const std::vector<InteractableKind>& knownInteractableKinds();

/**
 * @brief Peuple un `World` d'une **entité par objet** de la couche `objects`.
 *
 * Chaque `core::MapEntity` devient une entité portant un `Transform` (sa case, en unités monde) et,
 * si son type est connu, un `Interactable`. Un type **inconnu** produit tout de même une entité :
 * c'est une erreur de conception tolérée, pas une carte invalide (`EX-NFR-040`), et la refuser
 * ferait disparaître un objet de la carte sans que l'auteur comprenne pourquoi.
 *
 * Le nom de carte entre dans la **clé de drapeau** de chaque entité consommable : deux cartes
 * peuvent porter un coffre à la même case sans se marcher dessus.
 *
 * @param world Monde à peupler.
 * @param level Niveau source.
 * @param mapName Nom de la carte, pour les clés de drapeau.
 * @param onEntity Rappel invoqué après chaque création, avec l'entité et l'objet dont elle vient.
 *        Permet à la présentation d'y attacher ses propres composants sans que `Core` connaisse
 *        l'habillage (`EX-NFR-011`).
 * @return Le nombre d'entités créées.
 */
std::size_t spawnMapEntities(World& world, const Level& level, std::string_view mapName,
                             const std::function<void(Entity, const MapEntity&)>& onEntity = {});

}  // namespace core
