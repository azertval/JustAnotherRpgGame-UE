// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Math/Rect.h"

namespace core {

// Construit un rectangle à partir de son coin haut-gauche et de sa taille.
Rect::Rect(const Vector2& topLeft, const Vector2& dimensions)
    : position(topLeft), size(dimensions) {}

// Abscisse du bord gauche.
// La composante x de la position.
float Rect::left() const {
    return position.x;
}

// Abscisse du bord droit.
// `left + largeur`.
float Rect::right() const {
    return position.x + size.x;
}

// Ordonnée du bord supérieur.
// La composante y de la position.
float Rect::top() const {
    return position.y;
}

// Ordonnée du bord inférieur.
// `top + hauteur`.
float Rect::bottom() const {
    return position.y + size.y;
}

// Teste si un point est contenu dans le rectangle.
//
// L'appartenance est **inclusive** sur les bords haut/gauche et **exclusive**
// sur les bords bas/droit, afin qu'une grille de rectangles jointifs pave le
// plan sans recouvrement ni trou.
//
// `true` si le point est à l'intérieur ou sur un bord inclus.
bool Rect::contains(const Vector2& point) const {
    // Inclusif haut/gauche, exclusif bas/droit : des rectangles jointifs pavent
    // le plan sans recouvrement ni trou.
    return point.x >= left() && point.x < right() && point.y >= top() && point.y < bottom();
}

// Teste le recouvrement avec un autre rectangle.
//
// Le simple **contact par un bord** (aires disjointes qui se touchent) n'est
// pas considéré comme une intersection.
//
// `true` si les deux rectangles partagent une aire strictement positive.
bool Rect::intersects(const Rect& other) const {
    // Recouvrement strict : le contact par un bord ne compte pas comme intersection.
    return left() < other.right() && right() > other.left() && top() < other.bottom() &&
           bottom() > other.top();
}

}  // namespace core
