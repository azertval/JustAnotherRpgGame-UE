+++
id = "LOT-168"
titre = "Éditeur — le semis assisté"
version = "0.2.0"
filiere = "editeur"
statut = "a-faire"
taille = "M"
resume = "Une forêt, un éboulis, un champ de fleurs se sèment sur une sélection, à graine notée, et ce que l'auteur a retouché survit à un nouveau semis."
prerequis = ["LOT-167"]
reprend = ["LOT-EDITOR-11 (génération assistée)"]
livrables = [
  "Un outil **Semis** : sur une sélection ou une zone peinte, il pose des pièces d'une liste pondérée (trois chênes, un rocher, deux buissons), à densité et espacement réglés, en respectant collision, emprises et chemins d'accès.",
  "Des **recettes de semis** enregistrées par niveau de l'arborescence (« lisière de Bak », « prairie impériale »), à côté des préfabriqués.",
  "Les **régions verrouillées** de `<carte>.editor.json` : un nouveau semis ne touche ni une case verrouillée ni une pièce posée à la main.",
  "La graine et la recette notées dans l'annexe de la carte ; le geste est rejouable par `--apply`.",
]
criteres = [
  "Semer une lisière, retoucher une clairière, la verrouiller, ressemer avec une autre graine : la clairière est intacte et `--check` reste vert — toute case utile est encore atteignable.",
  "Même recette, même graine : même fichier, octet pour octet.",
]
+++

> **Rattaché à la `0.2.0`** ([D-47](../../../vision/decisions.md), 5 octobre 2026). Ce lot servait la `0.0.5`, une
> version de zone ; les zones partent à la `0.4.0`, et les systèmes se finissent avant le monde.
> Il garde son numéro. Ce qu'il éprouvait sur une zone du monde s'éprouve sur les trois lieux
> de la `0.1.0` ou sur des données d'essai, et se rejoue sur la zone quand elle vient.

## Pourquoi

C'est ce qui reste de `LOT-EDITOR-11`. Tel qu'écrit, il pilotait le générateur de terrain du
`LOT-40` — qui est **écarté** : les cartes se dessinent, zone par zone
([correspondance](../../../vision/correspondance-ancienne-roadmap.md)). Aucun générateur n'existe
dans `Core`, et il n'y en aura pas. Mais son critère d'acceptation disait juste : *générer,
retoucher, régénérer, la retouche est intacte*. Une forêt de cent cases ne se plante pas arbre par
arbre ; le semis est un **outil de dessin**, une fonction pure de l'éditeur, pas un générateur de
cartes.

## Périmètre

**Pas dedans** : générer une carte entière, son relief, ses routes ou ses bâtiments ; piloter quoi
que ce soit du jeu. La version `0.3.5` (forêt de Bak) en est le premier vrai client.
