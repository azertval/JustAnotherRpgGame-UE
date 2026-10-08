+++
id = "LOT-159"
titre = "Éditeur — l'onglet « Carte » depuis l'éditeur"
version = "0.2.0"
filiere = "editeur"
statut = "a-faire"
taille = "M"
resume = "Rattacher une carte jouable au plan de sa ville, de sa région et du monde se fait dans l'éditeur, et se contrôle : plus de `world-maps.json` écrit à la main."
prerequis = ["LOT-142"]
livrables = [
  "La vue de ville devient **éditable** : le cadre d'un quartier se tire sur le plan peint, une sous-zone se range **dans** sa zone (décision D-16), et l'éditeur écrit `Maps/world-maps.json` et `World/cities/*.json` de façon canonique.",
  "Une vue de **région** sur le même modèle : les zones de l'Empire posées sur sa carte peinte.",
  "Le rendu `--render --plan` du LOT-128 proposé comme **fond de travail** pour peindre l'image de l'onglet — jamais l'image livrée.",
  "`--check` : la région d'une carte existe à l'atlas ; chaque carte jouable a son entrée et son image d'onglet ; chaque quartier cliquable mène à une carte qui existe.",
]
criteres = [
  "Les lieux de la `0.1.0` — Martpart, Arenarea et, dans Arenarea, l'Arena of Fate et ses sous-sols — se rattachent au plan de la Capitale depuis l'éditeur, sans éditer un JSON à la main ; `check_map_assets.py` et `check_rpg_data.py` restent verts.",
  "Renommer une carte (`--rename-map`) suit `world-maps.json` comme il suit déjà les villes.",
]
+++

> **Rattaché à la `0.2.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026). Ce lot servait la `0.0.3`, une
> version de zone ; les zones partent à la `0.4.0`, et les systèmes se finissent avant le monde.
> Il garde son numéro. Ce qu'il éprouvait sur une zone du monde s'éprouve sur les trois lieux
> de la `0.1.0` ou sur des données d'essai, et se rejoue sur la zone quand elle vient.

## Pourquoi

Chaque lot de zone livre « l'image de la zone pour l'onglet « Carte » et son entrée dans
`world-maps.json` ». L'éditeur **lit** ce fichier et ne l'écrit pas ; les cadres de quartier y sont
provisoires depuis le `LOT-EDITOR-09`, et la région d'une carte n'est contrôlée contre rien
([audit](../../../standards/audit-editeur.md), §3). À trois cartes, cela s'écrit à la main ; à une
vingtaine de zones, non.

## Périmètre

Le **rattachement**. Les images d'onglet restent peintes par l'auteur (décision D-15).
