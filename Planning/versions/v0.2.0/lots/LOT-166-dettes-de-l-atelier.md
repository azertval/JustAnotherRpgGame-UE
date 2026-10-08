+++
id = "LOT-166"
titre = "Éditeur — les dettes de l'atelier"
version = "0.2.0"
filiere = "editeur"
statut = "a-faire"
taille = "M"
resume = "Ce que les cartes de la `0.1.0` ont appris de l'outil : les petites gênes notées « pas fait » dans ses lots, et celles que la recette a trouvées."
prerequis = ["LOT-198"]
livrables = [
  "Un **verrou de session** : deux éditeurs ouverts ne se proposent plus les brouillons l'un de l'autre ; les onglets de la dernière séance se rouvrent.",
  "Le panneau « Problems » contrôle le **brouillon**, pas seulement le fichier enregistré.",
  "Les préfabriqués se renomment, se déplacent d'un niveau à l'autre et se suppriment depuis la fenêtre ; les `carte#id` internes à un tampon sont réécrits à la pose.",
  "Un point s'insère au milieu d'un trajet ; le miroir accepte une ligne de grille ; le seau pose des pièces larges.",
  "`--apply` rejoue les couches, le redimensionnement et la pose de l'entrée ; son format a un schéma JSON publié.",
  "Les touches d'outils passent par `EditorKeyBindings`.",
  "Les anomalies inscrites par le [LOT-127](../../v0.1.0/v0.0.1-demo/lots/LOT-127-recette-de-l-editeur-a-la-main.md).",
]
criteres = [
  "Chaque ligne « pas fait » des dossiers `LOT-EDITOR-01` à `14` est levée, ou écartée avec sa raison dans la feuille de route de l'éditeur.",
  "Un scénario `--apply` par retouche de logique ; le cahier de recette de l'éditeur est rejoué par l'auteur.",
]
+++

> **Rattaché à la `0.2.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026). Ce lot servait la `0.0.4`, une
> version de zone ; les zones partent à la `0.4.0`, et les systèmes se finissent avant le monde.
> Il garde son numéro. Ce qu'il éprouvait sur une zone du monde s'éprouve sur les trois lieux
> de la `0.1.0` ou sur des données d'essai, et se rejoue sur la zone quand elle vient.

## Pourquoi

Aucune de ces dettes n'empêche de dessiner une carte ; toutes coûtent un peu à chaque carte. Le lot
est placé **après** la `0.1.0` exprès : ses cartes faites diront lesquelles pèsent vraiment, et
celles qui ne gênent personne seront écartées plutôt que faites. La liste est dans
l'[audit](../../../standards/audit-editeur.md), §4.

## Périmètre

Le confort de l'atelier. Les limites du **jeu** relevées par l'audit — seule la première couche de
décor est lue, la gêne et l'abri déduits d'une pièce ne sont pas joués — ne sont pas ici.
