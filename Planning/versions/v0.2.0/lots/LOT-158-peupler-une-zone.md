+++
id = "LOT-158"
titre = "Éditeur — peupler une zone"
version = "0.2.0"
filiere = "editeur"
statut = "a-faire"
taille = "M"
resume = "Des dizaines de PNJ par quartier se posent en quelques gestes, aux proportions que le livre donne, et se retouchent à plusieurs."
prerequis = ["LOT-142"]
livrables = [
  "Un **pinceau de foule** : sur une zone peinte, il pose des `npc` tirés des archétypes du lieu et de ses niveaux communs, selon les proportions de la région (84 humains, 5 gnomes… lues en données), à graine notée.",
  "L'**édition à plusieurs** dans l'inspecteur : une propriété changée sur une sélection l'est sur toutes les entités qui la portent, en un pas d'annulation.",
  "La sélection au **lasso**, et par filtre (« tous les `npc` sans dialogue »).",
  "Le catalogue des lieux distingue quartier, ville et région : une sentinelle ne « garde » plus une ville entière par erreur.",
  "`--check` : un PNJ **nommé** du référentiel placé deux fois, ou absent de la zone où le livre le met, est signalé.",
]
criteres = [
  "Une place de cent passants se peuple en un geste ; le décompte par espèce est à deux points des proportions du livre ; le même geste rejoué par `--apply` avec la même graine rend le même fichier.",
  "Trente PNJ reçoivent la même réplique d'ambiance en une saisie.",
  "L'auteur a repeuplé un des trois lieux de la `0.1.0` sans ouvrir le JSON.",
]
sources = ["Tanares Sourcebook, p. 90 : proportions de la population de l'Empire"]
+++

> **Rattaché à la `0.2.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026). Ce lot servait la `0.0.3`, une
> version de zone ; les zones partent à la `0.4.0`, et les systèmes se finissent avant le monde.
> Il garde son numéro. Ce qu'il éprouvait sur une zone du monde s'éprouve sur les trois lieux
> de la `0.1.0` ou sur des données d'essai, et se rejoue sur la zone quand elle vient.

## Pourquoi

La démo compte cinq PNJ à rôle et une foule. La `0.3.1` en ouvre six quartiers, chacun peuplé
[aux proportions du livre](../../../referentiels/central-empire/population-neutre.md). L'éditeur pose **une** entité à
la fois et n'édite **une** fiche à la fois ([audit](../../../standards/audit-editeur.md), §3) : à
l'échelle de la Capitale, c'est le poste le plus lent de la filière cartes.

## Périmètre

Des PNJ **postés**. Les trajets et les horaires sont au LOT-169. Le pinceau de foule pose des
entités ordinaires : rien de nouveau dans le format.
