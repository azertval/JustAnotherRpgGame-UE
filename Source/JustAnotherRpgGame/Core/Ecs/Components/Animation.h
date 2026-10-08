// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <memory>

#include "Core/Ecs/AnimationClip.h"

/**
 * @file Core/Ecs/Components/Animation.h
 * @brief Composant d'état d'animation par séquence d'images (données pures).
 */

namespace core {

/**
 * @brief État d'animation courant d'une entité : quel jeu de clips, quel clip, quelle image,
 *        depuis combien de temps.
 *
 * Donnée pure sans logique (`EX-ARCH-011`), mise à jour par `AnimationSystem` et lue par le rendu
 * (`HMI`) pour choisir la région à afficher. Le clip courant est une **projection** de
 * l'état de simulation (ex. l'action en cours d'un combattant) — il ne s'agit pas d'un état piloté
 * directement par une entrée du joueur, ni d'une source de vérité supplémentaire.
 *
 * `clips` est partagé (`shared_ptr` vers une donnée **immuable**) plutôt que copié : plusieurs
 * entités animées par le même jeu (ex. toutes les tuiles d'eau d'un niveau) n'en dupliquent pas le
 * contenu. `nullptr` signifie « pas de jeu assigné » — ceux qui créent le composant assignent
 * toujours un jeu avant de l'ajouter, mais `AnimationSystem` reste sûr face à ce cas
 * (`EX-NFR-040`).
 */
struct Animation {
    /// Jeu de clips utilisé par cette entité (immuable, partagé).
    std::shared_ptr<const ClipSet> clips;
    /// Index du clip courant dans `clips`, déjà résolu (`ClipSet::indexOf`) : la progression au
    /// pas fixe ne compare donc jamais de chaîne, y compris pour un grand nombre d'entités
    /// animées.
    int clipIndex = 0;
    /// Index de l'image courante, **dans le clip** (0-based, borné à `AnimationClip::frames`).
    int frameIndex = 0;
    /// Temps écoulé (secondes) depuis le passage à `frameIndex`.
    float elapsed = 0.0f;
};

}  // namespace core
