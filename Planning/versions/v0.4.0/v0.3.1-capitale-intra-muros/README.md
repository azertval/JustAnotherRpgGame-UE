# Version 0.3.1 — la Capitale dans ses murs

> **Reportée à la `0.4.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026) : c'était la `0.0.3`. Le
> monde se bâtit après les systèmes ; ses fiches se réécrivent à l'ouverture de la version
> ([D-35](../../../vision/decisions.md)), pour commander des maillages et des personnages en modèles.

Six quartiers, par paires de voisins, autour des trois lieux que la
[`0.1.0`](../../v0.1.0/v0.1.0-demo-finale/README.md) a produits. La quête du livre que l'ancien
`LOT-16` avait écrite, « Les enfants de Martpart », revient ici : la ville a désormais de quoi la
porter, et la sauvegarde (`LOT-150`, `0.2.0`) de quoi la reprendre.

## Ce qui reste à écrire

Le kit commun de la Capitale ([LOT-151](../../v0.1.0/v0.0.4-lieux-de-la-demo/lots/LOT-151-kit-commun-intra-muros.md))
se reprend à la `0.0.3` pour les trois lieux de la démo. Ce que les **six nouveaux quartiers**
partagent et qu'il n'aura pas — marbre blanc, lanternes magiques, statues, grilles, enseignes de
guilde — n'a plus de fiche : un lot de kit s'écrit à l'ouverture de cette version, sur ce que la
`0.0.3` aura appris du coût d'un kit en maillages.

## Gabarit d'une zone

Un lot de zone livre les **trois** choses que la zone demande, dans cet ordre :

1. **Assets** — les dix familles du [standard](../../../standards/style-3d.md) passées en revue : ce qui vient
   du commun, ce qui est propre à la zone ; installés sous `Regions/central-empire/…/<zone>/Scene/`.
2. **PNJ** — nommés (à leur place), neutres (archétypes du commun, proportions du livre), hostiles ;
   modèles, portraits, fiches, placements.
3. **Carte** — jouable, dessinée dans l'éditeur, contrôlée par `--check` ; et l'image de la zone pour
   l'onglet « Carte ».

Un lot de zone qui dépasse la taille **L** se redécoupe en trois lots (assets, PNJ, carte), comme
ceux de la `0.0.3`.
