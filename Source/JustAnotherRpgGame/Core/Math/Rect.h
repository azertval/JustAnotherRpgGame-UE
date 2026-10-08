// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Core/Math/Vector2.h"

/**
 * @file Core/Math/Rect.h
 * @brief Rectangle aligné sur les axes en coordonnées monde, propre à `Core`.
 */

namespace core {

/**
 * @brief Rectangle aligné sur les axes (AABB) en unités monde.
 *
 * Origine au coin **haut-gauche**, axe Y orienté vers le **bas** (convention du
 * projet). Les dimensions sont supposées positives ou nulles. Sert de brique aux
 * tests de contenance et d'intersection (culling, collisions grossières, zones
 * d'édition). Sans dépendance DirectX (`EX-ARCH-040`).
 */
struct Rect {
    /// Coin haut-gauche du rectangle.
    Vector2 position{};
    /// Dimensions (largeur en x, hauteur en y), attendues >= 0.
    Vector2 size{};

    Rect() = default;

    /**
     * @brief Construit un rectangle à partir de son coin haut-gauche et de sa taille.
     * @param topLeft    Coin haut-gauche.
     * @param dimensions Largeur et hauteur (>= 0).
     */
    Rect(const Vector2& topLeft, const Vector2& dimensions);

    /// @return Abscisse du bord gauche.
    [[nodiscard]] float left() const;
    /// @return Abscisse du bord droit (`left + largeur`).
    [[nodiscard]] float right() const;
    /// @return Ordonnée du bord supérieur.
    [[nodiscard]] float top() const;
    /// @return Ordonnée du bord inférieur (`top + hauteur`).
    [[nodiscard]] float bottom() const;

    /**
     * @brief Teste si un point est contenu dans le rectangle.
     *
     * L'appartenance est **inclusive** sur les bords haut/gauche et **exclusive**
     * sur les bords bas/droit, afin qu'une grille de rectangles jointifs pave le
     * plan sans recouvrement ni trou.
     *
     * @param point Point à tester, en coordonnées monde.
     * @return `true` si le point est à l'intérieur ou sur un bord inclus.
     */
    [[nodiscard]] bool contains(const Vector2& point) const;

    /**
     * @brief Teste le recouvrement avec un autre rectangle.
     *
     * Le simple **contact par un bord** (aires disjointes qui se touchent) n'est
     * pas considéré comme une intersection.
     *
     * @param other Autre rectangle.
     * @return `true` si les deux rectangles partagent une aire strictement positive.
     */
    [[nodiscard]] bool intersects(const Rect& other) const;
};

}  // namespace core
