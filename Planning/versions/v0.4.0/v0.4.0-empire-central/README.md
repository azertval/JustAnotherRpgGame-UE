# Version 0.4.0 — l'Empire central

> **Reportée à la `0.4.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026) : c'était la `0.1.0`. Le
> monde se bâtit après les systèmes ; ses fiches se réécrivent à l'ouverture de la version
> ([D-35](../../../vision/decisions.md)), pour commander des maillages et des personnages en modèles.

Pas de nouvelle zone : la région est **relue d'un bloc**. C'est le premier monde qu'on montre — la
[`0.1.0`](../../v0.1.0/v0.1.0-demo-finale/README.md) n'en montrait que trois lieux.

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
