// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <cstdint>

/**
 * @file Core/Ecs/Components/Sprite.h
 * @brief Composant d'apparence 2D d'une entité (données pures).
 */

namespace core {

/**
 * @brief Région source dans l'atlas de textures, en **pixels** (origine haut-gauche).
 *
 * Décrit le rectangle de l'atlas à échantillonner pour dessiner l'entité. Exprimée en
 * pixels de texture, indépendamment de la taille de l'atlas (la conversion en
 * coordonnées de texture normalisées se fait côté rendu, qui connaît ces dimensions).
 */
struct AtlasRegion {
    std::int32_t x = 0;
    std::int32_t y = 0;
    std::int32_t width = 0;
    std::int32_t height = 0;
};

/**
 * @brief Couleur RVBA à composantes flottantes dans l'intervalle [0, 1].
 *
 * Valeur par défaut : blanc opaque (1, 1, 1, 1), c'est-à-dire une teinte neutre qui
 * laisse la texture inchangée.
 */
struct Color {
    float r = 1.0f;
    float g = 1.0f;
    float b = 1.0f;
    float a = 1.0f;
};

/**
 * @brief Apparence 2D d'une entité : quelle région de l'atlas dessiner, dans quelle
 *        couche et avec quelle teinte.
 *
 * Donnée pure (`EX-ARCH-011`), lue par le rendu de `HMI` sans mutation (`EX-ARCH-012`) et
 * **agnostique du backend** : aucune ressource DirectX ni handle de texture ici — la
 * résolution région → texture est faite côté `HMI`. La région est en pixels de l'atlas ;
 * la taille à l'écran découle du `Transform` et de l'échelle monde (16 px/unité).
 */
struct Sprite {
    /// Région de l'atlas à échantillonner (en pixels).
    AtlasRegion region{};
    /// Couche de dessin : une valeur plus grande est dessinée **au-dessus**.
    std::int32_t layer = 0;
    /// Teinte multiplicative appliquée à la texture (blanc opaque = inchangée).
    Color tint{};
};

}  // namespace core
