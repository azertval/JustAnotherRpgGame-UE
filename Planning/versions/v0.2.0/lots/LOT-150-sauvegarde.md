+++
id = "LOT-150"
titre = "La sauvegarde"
version = "0.2.0"
filiere = "moteur"
statut = "a-faire"
taille = "L"
resume = "Une partie se sauvegarde et se reprend : groupe, fiches, inventaire, drapeaux, position."
prerequis = ["LOT-142"]
reprend = ["LOT-17"]
livrables = [
  "Le format de sauvegarde, versionné, et sa migration.",
  "Emplacements, sauvegarde automatique au changement de carte.",
  "L'écran Charger / Sauvegarder.",
]
criteres = [
  "Une partie sauvegardée dans un quartier se reprend à l'identique, drapeaux de quête compris.",
  "Une sauvegarde d'une version antérieure se charge ou est refusée avec un message clair — jamais un plantage.",
]
+++

> **Rattaché à la `0.2.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026). Ce lot servait la `0.0.3`, une
> version de zone ; les zones partent à la `0.4.0`, et les systèmes se finissent avant le monde.
> Il garde son numéro. Ce qu'il éprouvait sur une zone du monde s'éprouve sur les trois lieux
> de la `0.1.0` ou sur des données d'essai, et se rejoue sur la zone quand elle vient.

## Périmètre

Pas de sauvegarde **en combat** : on sauvegarde en exploration.

## Exigences

Ce que ce lot réalise, ou réalisera, s'écrit dans les spécifications :

- `EX-GP-070` — ce qu'une sauvegarde écrit : la liste des personnages, la carte, la case, les drapeaux.
- `EX-GP-071` — un format versionné, lu pour toujours, jamais écrasé en silence.
