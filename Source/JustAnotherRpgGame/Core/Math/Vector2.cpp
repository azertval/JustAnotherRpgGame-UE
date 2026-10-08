// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Math/Vector2.h"

#include <cmath>

#include "Core/Math/MathUtils.h"

namespace core {

// Construit un vecteur à partir de ses composantes.
Vector2::Vector2(float xComponent, float yComponent) : x(xComponent), y(yComponent) {}

// Ajoute un autre vecteur composante à composante.
// Une référence sur ce vecteur, modifié.
Vector2& Vector2::operator+=(const Vector2& other) {
    x += other.x;
    y += other.y;
    return *this;
}

// Soustrait un autre vecteur composante à composante.
// Une référence sur ce vecteur, modifié.
Vector2& Vector2::operator-=(const Vector2& other) {
    x -= other.x;
    y -= other.y;
    return *this;
}

// Met le vecteur à l'échelle par un scalaire.
// Une référence sur ce vecteur, modifié.
Vector2& Vector2::operator*=(float scalar) {
    x *= scalar;
    y *= scalar;
    return *this;
}

// Divise le vecteur par un scalaire.
// Une référence sur ce vecteur, modifié.
Vector2& Vector2::operator/=(float scalar) {
    x /= scalar;
    y /= scalar;
    return *this;
}

// Produit scalaire avec un autre vecteur.
// La somme des produits composante à composante.
float Vector2::dot(const Vector2& other) const {
    return (x * other.x) + (y * other.y);
}

// Carré de la longueur euclidienne (évite une racine carrée).
// `x*x + y*y`.
float Vector2::lengthSquared() const {
    return (x * x) + (y * y);
}

// Longueur euclidienne du vecteur.
// `sqrt(x*x + y*y)`.
float Vector2::length() const {
    return std::sqrt(lengthSquared());
}

// Renvoie le vecteur normalisé (longueur 1).
// Un vecteur unitaire de même direction ; le vecteur nul si la longueur
// est négligeable (aucune direction définie).
Vector2 Vector2::normalized() const {
    const float magnitude = length();
    if (magnitude <= EPSILON) {
        // Le vecteur nul (ou quasi nul) n'a pas de direction : on renvoie zéro.
        return Vector2{};
    }
    return Vector2{x / magnitude, y / magnitude};
}

// Somme de deux vecteurs.
// Le vecteur somme.
Vector2 operator+(const Vector2& lhs, const Vector2& rhs) {
    return Vector2{lhs.x + rhs.x, lhs.y + rhs.y};
}

// Différence de deux vecteurs.
// Le vecteur différence `lhs - rhs`.
Vector2 operator-(const Vector2& lhs, const Vector2& rhs) {
    return Vector2{lhs.x - rhs.x, lhs.y - rhs.y};
}

// Produit d'un vecteur par un scalaire.
// Le vecteur mis à l'échelle.
Vector2 operator*(const Vector2& vector, float scalar) {
    return Vector2{vector.x * scalar, vector.y * scalar};
}

// Produit d'un scalaire par un vecteur (commutatif).
// Le vecteur mis à l'échelle.
Vector2 operator*(float scalar, const Vector2& vector) {
    return vector * scalar;
}

// Division d'un vecteur par un scalaire.
// Le vecteur divisé.
Vector2 operator/(const Vector2& vector, float scalar) {
    return Vector2{vector.x / scalar, vector.y / scalar};
}

// Opposé d'un vecteur.
// Le vecteur de composantes opposées.
Vector2 operator-(const Vector2& vector) {
    return Vector2{-vector.x, -vector.y};
}

// Égalité approchée entre deux vecteurs (comparaison par tolérance).
// `true` si les composantes coïncident à la tolérance près.
bool operator==(const Vector2& lhs, const Vector2& rhs) {
    return approximatelyEqual(lhs.x, rhs.x) && approximatelyEqual(lhs.y, rhs.y);
}

// Inégalité approchée entre deux vecteurs.
// `true` si les vecteurs diffèrent au-delà de la tolérance.
bool operator!=(const Vector2& lhs, const Vector2& rhs) {
    return !(lhs == rhs);
}

}  // namespace core
