+++
id = "LOT-111"
titre = "Carte — Martpart"
version = "0.0.4"
filiere = "cartes"
statut = "a-faire"
taille = "M"
resume = "Martpart se parcourt."
prerequis = ["LOT-110", "LOT-103", "LOT-124", "LOT-125", "LOT-128", "LOT-146"]
livrables = [
  "`Levels/central-empire/capital/martpart.json`, dessinée **dans l'éditeur**.",
  "Portails, points d'apparition nommés, zones (combat, déclencheurs de quête).",
]
criteres = [
  "`LevelEditor --check` passe : aucune case inatteignable, aucun portail sans arrivée, aucune référence morte.",
  "La carte tient 60 images par seconde à 1080p sur le poste de référence, de jour comme de nuit.",
  "Ses lumières de nuit sont posées (famille `light`) : la place des étals se lit à 22 h.",
]
maquettes = ["../../v0.0.1-demo/maquettes/plan-martpart.svg"]
+++

## Reporté à la `0.0.3` (décision [D-25](../../../../vision/decisions.md), 25 septembre 2026)

Ce lot servait la démo. C'est un lot de *world building*, trop complexe pour elle : il rejoint la
`0.0.3`, où un lieu se produit pour de bon. Dans la démo, Martpart est une
**carte de principe** ([LOT-146](../../v0.0.1-demo/lots/LOT-146-cartes-de-principe-de-la-demo.md))
de 24 × 11 cases. Ce lot livre la carte définitive, qui la remplace sous le même identifiant.

## Conception

La carte comprend l'entrée du marché où le joueur apparaît ; la place des étals, où la mère interpelle le joueur ; Stravian Avenue jusqu'au portail d'Arenarea ; une ruelle. L'Illu Die Arena n'est **pas** dans la démo (version `0.3.2`).

![Plan de principe](../../v0.0.1-demo/maquettes/plan-martpart.svg)

Le plan ci-dessus est un **schéma de principe** : il fixe ce que la carte contient et comment on y
circule, pas son dessin.

## V0 installée dans le jeu — 5 octobre 2026

La carte de l'atelier (`Production110`) remplace la carte de principe du `LOT-146` sous le même
identifiant : 112 × 88 cases, créée et assemblée par `LevelEditor --new` puis `--apply`. La mère et
l'enfant gardent leurs dialogues et leurs conditions ; l'arrivée `from-arenarea` et le départ
`market-gate` gardent leur nom ; le passage vers Arenarea est au nord, les quatre autres sorties
(Oldtown, Downtown, Scholarnest, Dweomer) sont scellées tant que leurs cartes n'existent pas.
`LevelEditor --check` passe sans avertissement sur cette carte.

C'est une **v0** : le lot reste à faire. La cadence à 1080p n'est pas mesurée, et la lecture de
la place des étals à 22 h reste à valider par l'auteur.
