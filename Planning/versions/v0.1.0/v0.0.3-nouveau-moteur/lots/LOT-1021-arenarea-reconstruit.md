+++
id = "LOT-1021"
titre = "Arenarea reconstruit au standard D-54"
version = "0.0.3"
filiere = "cartes"
statut = "a-faire"
taille = "XL"
resume = "Arenarea est le premier lieu produit pour de bon sur le nouveau moteur, quartier par quartier depuis sa carte peinte, jusqu'à donner la même impression qu'elle à midi et à 22 h : c'est ici que le coût d'un lieu se mesure."
prerequis = ["LOT-1019"]
livrables = [
  "La description de carte d'Arenarea (format 5), construite par script et retouchée par l'aller-retour de l'éditeur : terrain, berges et quais, rues du plan, les neuf lieux nommés du plan (Arena of Fate, Dusk of Justice, Natural Pool, Golden Chalice, Hippodrome, Inlet's Bazaar, Cloaked Brewer, Arena Gate, Mapleleaf Plaza), l'enceinte et ses portes.",
  "Le kit `arenarea` republié : chaque famille de pièces au standard du LOT-1019, au maître, les variantes qu'il faut pour qu'aucun bâtiment ne se répète à l'écran ; les boîtes et les images du LOT-108 retirées du kit (D-32).",
  "Les arrivées, portails, zones et entités de la quête conservés sous leurs noms : `from-martpart`, `from-arena-of-fate`, `parvis`, le garde, l'enfant ; la quête rejouée sans changer une ligne.",
  "Les captures du moteur à midi et à 22 h, aux cadrages du joueur, pour chacun des neuf lieux, rangées à côté de la carte peinte ; les mesures de cadence et d'ouverture.",
  "Le relevé du coût : pièces commandées, crédits Meshy, temps passé par quartier, poids du kit, triangles de la plus grosse pièce — le nombre que la trajectoire attend depuis la `0.0.1`.",
]
criteres = [
  "L'auteur valide chacun des neuf lieux sur le rendu du moteur, à midi et à 22 h, comme donnant « la même impression » que la carte peinte (D-54) ; aucune validation « en l'état ».",
  "La carte tient 60 images par seconde à 1080p sur le poste de référence, caméra en mouvement, de jour comme de nuit, et s'ouvre en moins de 10 secondes.",
  "La quête « Des pommes pour l'arène » se rejoue de bout en bout sur la carte reconstruite ; ses tests passent avec les nouvelles positions, sans changer la quête.",
  "`--check` passe ; aucune zone inatteignable sur le maillage de navigation hors de celles déclarées.",
  "Le relevé du coût est écrit dans la fiche, quartier par quartier.",
]
sources = [
  "Tanares Sourcebook, p. 91-92, 96-99 (géographie et lieux, jamais comme image d'entrée) ; la carte peinte d'Arenarea de l'atlas (Maps@2)",
]
+++

## Pourquoi

C'est le lot pour lequel la version existe : le lieu que l'auteur a pris en exemple, rendu comme sa
carte. Il remplace la reconstruction du LOT-147, dont le v0 du 5 octobre restait « loin de
l'équivalence visuelle ». Il donne aussi le nombre que toute la trajectoire attend : ce que coûte
un lieu produit pour de bon.

## Périmètre

Dedans : le terrain, les rues, les neuf lieux nommés, l'enceinte, les quais, les jardins, le
mobilier, les lumières de nuit ; le kit ; la quête rejouée ; le relevé du coût.

Dehors, nommément :

- les PNJ d'Arenarea (LOT-114, `0.0.4`) : la carte garde ses deux PNJ de quête et ses mannequins ;
- les intérieurs et les animaux ;
- l'Arena of Fate, portée par le LOT-1022 et posée ici à sa place ;
- l'image de l'onglet Carte : c'est la carte peinte de l'atlas, déjà livrée.

## À supprimer

| Quoi | Où | Pourquoi maintenant |
|---|---|---|
| Les 462 images du LOT-108 encore dans le kit | `capital/arenarea/Scene/`, à la republication | la carte reconstruite ne les cite plus |
| Les 60 modules procéduraux en boîtes de la v0 | même kit | remplacés famille par famille |
| La v0 du LOT-147 (description v4) | `Levels/central-empire/capital/arenarea.json` | remplacée par la description v5 sous le même identifiant |

## Conception

- **Quartier par quartier**, dans l'ordre où le joueur les voit : le parvis et le Colisée (déjà
  posés par la porte), le bassin et ses jardins, le bazar et la porte d'eau, le casino et la maison
  de jeu, l'hippodrome et la place, le pub et la porte de l'arène, les quais. Chaque quartier se
  valide sur captures avant le suivant ; le lot se redécoupe si le premier dépasse la semaine.
- **La carte peinte est la référence de l'impression**, pas un plan à décalquer : le plan du
  Sourcebook donne la géographie (ouest en haut, nord à droite, la rivière, l'enceinte), l'image
  donne la densité, la lumière, la matière.
- **Les variantes** : un bâtiment ne se répète pas dans un même cadrage ; six variantes par famille
  d'habitation, les pièces maîtresses uniques.
- **Les lumières de nuit** à chaque lampadaire, portique et fenêtre éclairée ; leur nombre à l'écran
  se mesure ici, et le standard l'écrit.

## Risques et questions ouvertes

- **La taille** : XL par nature. Si le premier quartier validé coûte plus d'une semaine, le lot se
  redécoupe en un lot par quartier, et la version livre Arenarea partiel avec une dette datée.
- **Le coût Meshy** : une centaine de pièces à trente crédits ; le relevé le dit.
- **La cadence** : des milliers d'objets, Nanite et Lumen ; les niveaux de chargement par quartier
  (D-51) sont la parade si la mesure ne tient pas.
- **La dette du LOT-1016** (clos le 8 octobre 2026), que ce lot retire : **la porte** du LOT-1012
  ne joue aucune carte de Core (ni portail ni PNJ) ; elle reçoit la sienne avec Arenarea
  reconstruit, sur le format du LOT-1018.
