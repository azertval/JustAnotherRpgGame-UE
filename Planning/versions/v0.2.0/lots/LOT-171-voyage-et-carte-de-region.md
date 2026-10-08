+++
id = "LOT-171"
titre = "Le voyage et la carte de région"
version = "0.2.0"
filiere = "moteur"
statut = "a-faire"
taille = "L"
resume = "On quitte une zone, on choisit une destination sur la carte de l'Empire, on y arrive — le temps passe, la route a ses rencontres."
prerequis = ["LOT-198"]
reprend = ["LOT-42", "LOT-70 (horloge, en partie)"]
livrables = [
  "Le voyage entre zones depuis la carte de région ; durée, rencontres de route.",
  "Le temps de voyage, qui fait avancer l'horloge du monde — livrée au `LOT-1007` (D-45), elle n'est plus à faire ici ; le calendrier lunaire attend la `0.2.0`.",
]
criteres = [
  "Entre deux zones reliées sur la carte de région, aller et retour : la durée fait avancer l'horloge du monde, et la route a sa rencontre — sur des données d'essai, à graine fixée.",
  "Le premier trajet du jeu, de la Capitale à Phantom Fortress par la route impériale, se joue quand la zone existe : c'est un critère de la `0.3.3` (LOT-173).",
]
+++

> **Rattaché à la `0.2.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026). Ce lot servait la `0.0.5`, une
> version de zone ; les zones partent à la `0.4.0`, et les systèmes se finissent avant le monde.
> Il garde son numéro. Ce qu'il éprouvait sur une zone du monde s'éprouve sur les trois lieux
> de la `0.1.0` ou sur des données d'essai, et se rejoue sur la zone quand elle vient.

## Périmètre

Le voyage **dans l'Empire**. Les frontières sont fermées jusqu'à la `0.5.0`.
