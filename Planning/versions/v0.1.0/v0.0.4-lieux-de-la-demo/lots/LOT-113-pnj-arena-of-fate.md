+++
id = "LOT-113"
titre = "PNJ — Arena of Fate (donjon d'Arenarea)"
version = "0.0.4"
filiere = "pnj"
statut = "a-faire"
taille = "M"
resume = "Les habitants de Arena of Fate : modèles, portraits, fiches, placements."
prerequis = ["LOT-107", "LOT-112", "LOT-1009", "LOT-1011"]
livrables = [
  "`capital/arenarea/arena-of-fate/Characters/` pour les PNJ propres ; les archétypes de citadins dans `capital/Common/Characters/`.",
  "Pour chaque PNJ : son **modèle** au [standard des personnages](../../../../standards/personnages-3d.md) — un maillage qui lui est propre, lié au squelette commun, installé par l'atelier des assets d'après sa fiche d'atelier —, son portrait et son jeton peints, et sa fiche (`Rpg/`) quand il en a une.",
  "Les placements sur la carte définitive (entités), et les répliques d'ambiance, en français et en anglais.",
  "Le kit du lieu republié et verrouillé.",
]
criteres = [
  "Chaque PNJ de la liste est visible à sa place sur la carte, par son modèle : aucun ne s'affiche par le mannequin.",
  "`LevelEditor --check` et `check_character_model.py` passent sur chaque modèle installé.",
  "Aucun portrait ni jeton n'est une image du corpus.",
  "Les archétypes communs resservent d'un lieu à l'autre sans copie.",
]
sources = ["Référentiel : Arena of Fate dans `referentiels/central-empire/`"]
+++

## Réécrit à la recette de la `0.0.2.5` ([D-35](../../../../vision/decisions.md), 5 octobre 2026)

Cette fiche commandait des **figurines** en bandes peintes, par la chaîne du `LOT-104`. Depuis le
passage à la 3D, un personnage est un **modèle** ([D-38](../../../../vision/decisions.md)) : une
image de référence de face en pose neutre, un maillage généré sans arme, une fiche de liaison au
squelette commun, et l'installation par l'atelier (`LevelEditor --apply`, une fiche d'atelier par
personnage). Les six clips sont déjà là : un personnage ne coûte plus que son image, sa génération
et sa liaison — le relevé est au
[LOT-1009](../../v0.0.2.5-passage-3d/lots/LOT-1009-les-quatre-heros.md#le-coût-dun-personnage).

**Déjà livrés** par le `LOT-1009`, en modèles : le **maître d'arène**, les deux gardes Ironhand (le modèle `ironhand-soldier`), et tous les adversaires de la série de l'arène — bandits, malfrat, berserker, vétéran, gladiateur, capitaine, morts, le lion et le loup (`LOT-1011`). Ce lot ne les refait pas.

**Reste à produire** : **Galender, the Weapon Master** (CC p. 48) et les **Twin Tigers** (CC p. 135) — présents, non combattus ; un soigneur, les condamnés de la prison. La foule des gradins n'est pas faite de personnages : elle est dans le kit du lieu (`LOT-106`).

La **foule** se pose à la main, entité par entité, d'après les archétypes : le pinceau de foule
([LOT-158](../../../v0.2.0/lots/LOT-158-peupler-une-zone.md)) est un outil de la `0.2.0`
([D-47](../../../../vision/decisions.md)) et ne se fait pas attendre ici.

## Histoire : reporté à la `0.0.3` (décision [D-25](../../../../vision/decisions.md), 25 septembre 2026)

Ce lot servait la démo. C'est un lot de *world building*, trop complexe pour elle : il rejoint la
`0.0.3`, où un lieu se produit pour de bon. Dans la démo, le maître d'arène
et le combattant de l'arène sont tenus par les **mannequins**
([LOT-145](../../v0.0.2-combat/lots/LOT-145-mannequins-de-remplacement.md)) ou par des **jetons**
(`LOT-128`), posés sur les cartes de principe du
[LOT-146](../../v0.0.1-demo/lots/LOT-146-cartes-de-principe-de-la-demo.md) ; leurs dialogues sont au
`LOT-120`. Ce lot leur donne leurs figurines, leurs portraits et la foule, avec le pinceau de foule
du `LOT-158`. Une figurine livrée remplace son mannequin sans toucher à la carte.

## Les PNJ

- **Le maître d'arène** — il lance la série et la récompense. **Livré** (`LOT-1009`).
- **Galender, the Weapon Master** (CC p. 48) et les **Twin Tigers** (CC p. 135) : présents, non combattus — trop forts pour la démo. **À produire.**
- Neutres : deux gardes Ironhand (**livrés**), un soigneur et des condamnés (**à produire**).
- Hostiles : les adversaires des six rencontres de la série (`LOT-142`). **Livrés** (`LOT-1009`, `LOT-1011`).

Proportions de la foule (livre, p. 90) : sur cent passants, 84 humains, 5 gnomes, 3 elfes d'été,
2 tieffelins, 2 nains, 2 soulborns. Voir [la population neutre](../../../../referentiels/central-empire/population-neutre.md)
et [les PNJ nommés](../../../../referentiels/central-empire/pnj-nommes.md).

## Une sous-zone, pas un quartier

L'Arena of Fate est un **donjon d'Arenarea** (décision D-16) : un lieu clos, à plusieurs salles —
vestiaire A, vestiaire B, couloir, sable —, où l'on entre **depuis le quartier**, par la porte de
l'arène au bout du parvis. Elle n'a pas d'entrée sur le plan de la Capitale : l'onglet « Carte »
la montre **dans** Arenarea. Ses assets et sa carte se rangent sous `capital/arenarea/arena-of-fate/`,
et elle puise d'abord dans le kit d'Arenarea, puis dans celui de la Capitale.

## Périmètre

Pas de routine de déplacement ni d'horaire : les PNJ sont **postés**, de jour comme de nuit. Les horaires viennent avec le [LOT-169](../../../v0.2.0/lots/LOT-169-horaires-et-trajets.md), à la `0.2.0`.
