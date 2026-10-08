+++
id = "LOT-110"
titre = "Assets — Martpart, en maillages"
version = "0.0.4"
filiere = "assets"
statut = "a-faire"
taille = "L"
resume = "Les pièces propres à Martpart, produites en maillages au standard 3D et installées dans `capital/martpart/Scene/`."
prerequis = ["LOT-105", "LOT-129", "LOT-151"]
livrables = [
  "`Regions/central-empire/capital/martpart/Scene/` : les pièces en **maillages** (`.glb`) au [standard 3D](../../../../standards/style-3d.md), `manifest.json`, `appearance.json` ; le kit publié et verrouillé.",
  "La commande du lieu, dans l'atelier (`Tools/Assets3D/`) : les dix familles passées en revue, ce qui vient du kit commun, ce qui est propre.",
  "La page de galerie du lieu.",
]
criteres = [
  "Toutes les pièces de l'inventaire ci-dessous paraissent dans la galerie des assets, en maillages.",
  "Le kit de Martpart ne porte plus aucune image de décor : sa part de la dette déclarée par la `0.0.2.5` est soldée, et `check_orphans.py` passe.",
  "Aucune pièce ne double une pièce du kit commun.",
  "L'auteur a validé le lieu sur le rendu du moteur, de jour comme de nuit.",
]
sources = [
  "Tanares Sourcebook, p. 98-99 ; plan VTT (référence seule) : Municipal Market, Stravian Av, Market Gate",
]
+++

## Réécrit à la recette de la `0.0.2.5` ([D-35](../../../../vision/decisions.md), 5 octobre 2026)

Cette fiche commandait des images, par la chaîne du `LOT-104`. Le lieu se produit en **maillages** :
une pièce est un `.glb`, ou l'une des [images que le standard tolère](../../../../standards/style-3d.md#7-les-images-tolérées)
sans date. Le kit de Martpart est de ceux que la `0.0.2.5` a laissés en image jusqu'à cette version
([D-30](../../../../vision/decisions.md)) : ce lot retire ces images dans sa PR
([D-32](../../../../vision/decisions.md)). La facture de référence reste celle du `LOT-105`, V4 ;
la palette et les emblèmes sont ceux du lieu.

## Histoire : reporté à la `0.0.3` (décision [D-25](../../../../vision/decisions.md), 25 septembre 2026)

Ce lot servait la démo. C'est un lot de *world building*, trop complexe pour elle : il rejoint la
`0.0.3`, où un lieu se produit pour de bon. Dans la démo, Martpart est une
**carte de principe** ([LOT-146](../../v0.0.1-demo/lots/LOT-146-cartes-de-principe-de-la-demo.md)),
sans pièce propre : ce lot lui donne ses pièces définitives. Il attend le kit complété (`LOT-151`).

## Le lieu

Le quartier du marché, celui qui ne dort pas : étals sous les lanternes, architecture métissée, ruelles.

## Inventaire des pièces propres

- La halle du Municipal Market (toits bleu-violet), étals garnis (fruits, étoffes, poteries, épices), auvents, lanternes suspendues.
- Façades métissées : trois styles de maison de commerce.
- Ruelles : murs aveugles, escaliers, caisses, linge.
- La **Market Gate**.

Le détail du quartier — texte du livre et lieux nommés sur le plan — est dans
[le référentiel de la Capitale](../../../../referentiels/central-empire/capitale.md).

## Périmètre

Les **pièces de scène** seulement. Les personnages sont au lot des PNJ, la carte au lot de la carte.

## V0 installée dans le jeu — 5 octobre 2026

L'atelier du 5 octobre (`Tools/Assets3D/Regions/central-empire/capital/martpart/Production110/`)
a produit une première version du lieu, installée à la demande de l'auteur dans
`capital/martpart/Scene/` : 34 maillages — la halle du Municipal Market, l'anneau de l'Illu Die,
la Market Gate et le pont, trois pavages, quatre étals garnis, le mobilier, et six retours Meshy
(trois maisons de commerce, le fronton, le treuil, le lampadaire) — et leur manifeste. Les deux
arbres sont ceux d'Arenarea, cités par le manifeste et non copiés. Le kit est publié et verrouillé
sous `martpart@4` (38 fichiers, 93 Mio).

C'est une **v0** : le lot reste à faire. `appearance.json` n'est pas écrit, les pièces communes de
travail (pavages, eau, végétal) attendent leur réconciliation avec le `LOT-151`, et la validation
artistique de l'auteur, de jour comme de nuit, n'est pas acquise.
