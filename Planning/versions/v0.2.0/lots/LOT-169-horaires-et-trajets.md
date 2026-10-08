+++
id = "LOT-169"
titre = "Éditeur — horaires et trajets"
version = "0.2.0"
filiere = "editeur"
statut = "a-faire"
taille = "S"
resume = "Ce que l'horloge du monde change sur une carte se règle et se voit dans l'éditeur : qui est où à quelle heure, ce qui ferme la nuit."
prerequis = ["LOT-171"]
livrables = [
  "Les **horaires** déclarés au contrat d'extension : une plage d'heures dans la condition de présence, des étapes horodatées sur une `route`.",
  "Un **curseur d'heure** au canevas, à côté du sélecteur d'état de partie du LOT-126 : il montre la carte à l'heure choisie, et l'essai en part.",
  "`--check` : un PNJ dont l'horaire laisse un trou, une route dont une étape tombe sur une case bloquée.",
]
criteres = [
  "Un garde relevé à la tombée de la nuit : au canevas, le curseur passé de midi à minuit échange les deux entités ; l'essai dans le jeu fait de même.",
  "Aucun code par famille dans l'éditeur.",
]
+++

> **Rattaché à la `0.2.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026). Ce lot servait la `0.0.5`, une
> version de zone ; les zones partent à la `0.4.0`, et les systèmes se finissent avant le monde.
> Il garde son numéro. Ce qu'il éprouvait sur une zone du monde s'éprouve sur les trois lieux
> de la `0.1.0` ou sur des données d'essai, et se rejoue sur la zone quand elle vient.

## Pourquoi

La famille `route` attend ses horaires depuis le `LOT-EDITOR-05` ; le
[LOT-171](LOT-171-voyage-et-carte-de-region.md) apporte l'horloge. Petit lot : le mécanisme de
condition et le sélecteur d'état existent depuis le LOT-126, il n'y a qu'une dimension à ajouter.
