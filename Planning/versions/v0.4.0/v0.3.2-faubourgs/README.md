# Version 0.3.2 — les faubourgs

> **Reportée à la `0.4.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026) : c'était la `0.0.4`. Le
> monde se bâtit après les systèmes ; ses fiches se réécrivent à l'ouverture de la version
> ([D-35](../../../vision/decisions.md)), pour commander des maillages et des personnages en modèles.

Hors les murs : quatre faubourgs et les docks. Le style change — bois, torchis, ruelles, pauvreté —
et demande son propre kit. Les deux autres arènes de la Capitale donnent la **gradation** : Braves
Arena pour les débutants, Illu Die Arena pour la renommée, Arena of Fate pour la politique.

## Gabarit d'une zone

Un lot de zone livre les **trois** choses que la zone demande, dans cet ordre :

1. **Assets HD** — les dix familles du [standard](../../../standards/style-3d.md) passées en revue : ce qui vient
   du commun, ce qui est propre à la zone ; installés sous `Regions/central-empire/…/<zone>/Scene/`.
2. **PNJ** — nommés (à leur place), neutres (archétypes du commun, proportions du livre), hostiles ;
   figurines, portraits, fiches, placements.
3. **Carte** — jouable, dessinée dans l'éditeur, contrôlée par `--check` ; et l'image de la zone pour
   l'onglet « Carte ».

Un lot de zone qui dépasse la taille **L** se redécoupe en trois lots (assets, PNJ, carte), comme
ceux de la `0.0.1`.
