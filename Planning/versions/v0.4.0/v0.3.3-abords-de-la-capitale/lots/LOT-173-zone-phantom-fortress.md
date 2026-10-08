+++
id = "LOT-173"
titre = "Zone — Phantom Fortress"
version = "0.3.3"
filiere = "cartes"
statut = "a-faire"
taille = "XL"
resume = "Phantom Fortress : assets HD, PNJ, carte jouable et carte de l'onglet."
prerequis = ["LOT-170", "LOT-171", "LOT-167"]
livrables = [
  "Les assets HD propres à Phantom Fortress, et ce qu'elle verse au commun.",
  "Ses PNJ nommés, neutres et hostiles : figurines, portraits, fiches, placements.",
  "Sa carte jouable et son image pour l'onglet « Carte ».",
]
criteres = [
  "La zone se parcourt ; `LevelEditor --check` passe.",
  "Chaque PNJ nommé que le livre y place y est.",
  "Rien n'y double le commun.",
]
sources = ["Tanares Sourcebook, p. 94"]
+++

> **Reporté à la `0.4.0`** ([D-47](../../../../vision/decisions.md), 5 octobre 2026). La `0.1.0` ne garde que les
> trois lieux de la démo : cette fiche, écrite pour la `0.0.5`, sert désormais la
> `0.3.3` — les abords de la Capitale —, après les systèmes (`0.2.0`, `0.3.0`).
> **À réécrire** à l'ouverture de sa version ([D-35](../../../../vision/decisions.md)) : elle a été écrite pour
> des kits d'images, et commandera des **maillages** au [standard 3D](../../../../standards/style-3d.md) et des
> personnages en modèles. Ses lieux, ses PNJ et ses sources restent la référence.

## Le lieu

À quelques milles de la Capitale : plan cruciforme dans un mur circulaire, quatre cours, tour centrale ; prison souterraine autour d'un abîme noir, cellules antimagie, fantômes qui hantent le sommeil.

## PNJ

Officiers Ironhand, prisonniers, un bibliothécaire de la propagande.

## Hostiles

**Ironhand Soldier, Brute, Arbalist** (SB p. 326-327) ; fantômes de mages (*Manuel des Monstres*).

## Premier donjon

Plusieurs cartes reliées (cours, ailes, étages bas, souterrain) : l'éditeur sait gérer un **lieu à plusieurs cartes** depuis le `LOT-EDITOR-09` (onglets, graphe, liens posés des deux côtés). Les cours sont du plein air : [LOT-167](../../../v0.2.0/lots/LOT-167-grandes-cartes-de-plein-air.md).

Détail : [zones](../../../../referentiels/central-empire/zones.md) · [Capitale](../../../../referentiels/central-empire/capitale.md) ·
[PNJ nommés](../../../../referentiels/central-empire/pnj-nommes.md) · [hostiles](../../../../referentiels/central-empire/hostiles.md).
