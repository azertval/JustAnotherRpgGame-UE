# Core/Math/

Types mathématiques **propres à `Core`**, sans dépendance DirectX (conversion vers `DirectXMath` uniquement côté `HMI`).

- `Vector2` — vecteur 2D flottant (opérateurs, produit scalaire, longueur, normalisation, égalité approchée).
- `Rect` — rectangle aligné sur les axes (bords, `contains`, `intersects`), origine haut-gauche, Y-bas.
- `MathUtils.h` — `approximatelyEqual` et `EPSILON` pour les comparaisons flottantes.
- `DeterministicRandom.h` — générateur pseudo-aléatoire déterministe, à graine explicite.

Réf. specs : `EX-ARCH-040`.
