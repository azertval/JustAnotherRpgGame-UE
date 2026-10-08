// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Math/Vector2.h
 * @brief Vecteur 2D à composantes flottantes, propre à `Core` (sans dépendance DirectX).
 */

namespace core {

/**
 * @brief Vecteur bidimensionnel en coordonnées monde (composantes `float`).
 *
 * Type mathématique fondamental de la simulation, indépendant de tout backend
 * graphique (`EX-ARCH-040`). La conversion vers `DirectXMath` se fera plus tard,
 * uniquement côté `HMI`. L'axe Y suit la convention du projet (origine haut-gauche,
 * Y vers le bas), mais `Vector2` reste purement algébrique.
 */
struct Vector2 {
    float x = 0.0f;
    float y = 0.0f;

    Vector2() = default;

    /**
     * @brief Construit un vecteur à partir de ses composantes.
     * @param xComponent Composante horizontale.
     * @param yComponent Composante verticale.
     */
    Vector2(float xComponent, float yComponent);

    Vector2& operator+=(const Vector2& other);
    Vector2& operator-=(const Vector2& other);
    Vector2& operator*=(float scalar);
    Vector2& operator/=(float scalar);

    /**
     * @brief Produit scalaire avec un autre vecteur.
     * @param other Autre opérande.
     * @return La somme des produits composante à composante.
     */
    [[nodiscard]] float dot(const Vector2& other) const;

    /**
     * @brief Carré de la longueur euclidienne (évite une racine carrée).
     * @return `x*x + y*y`.
     */
    [[nodiscard]] float lengthSquared() const;

    /**
     * @brief Longueur euclidienne du vecteur.
     * @return `sqrt(x*x + y*y)`.
     */
    [[nodiscard]] float length() const;

    /**
     * @brief Renvoie le vecteur normalisé (longueur 1).
     * @return Un vecteur unitaire de même direction ; le vecteur nul si la
     *         longueur est négligeable (aucune direction définie).
     */
    [[nodiscard]] Vector2 normalized() const;
};

[[nodiscard]] Vector2 operator+(const Vector2& lhs, const Vector2& rhs);
[[nodiscard]] Vector2 operator-(const Vector2& lhs, const Vector2& rhs);
[[nodiscard]] Vector2 operator*(const Vector2& vector, float scalar);
[[nodiscard]] Vector2 operator*(float scalar, const Vector2& vector);
[[nodiscard]] Vector2 operator/(const Vector2& vector, float scalar);
[[nodiscard]] Vector2 operator-(const Vector2& vector);

/**
 * @brief Égalité approchée entre deux vecteurs (comparaison par tolérance).
 * @param lhs Premier opérande.
 * @param rhs Second opérande.
 * @return `true` si les composantes coïncident à la tolérance près.
 */
[[nodiscard]] bool operator==(const Vector2& lhs, const Vector2& rhs);
[[nodiscard]] bool operator!=(const Vector2& lhs, const Vector2& rhs);

}  // namespace core
