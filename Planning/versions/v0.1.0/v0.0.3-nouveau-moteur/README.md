# Version 0.0.3 — le nouveau moteur

Le jeu passe sur **Unreal Engine 5** ([D-48](../../../vision/decisions.md), 7 octobre 2026). La
version se loge entre la recette de la `0.0.2.5` et les trois lieux de la démo, devenus la
[`0.0.4`](../v0.0.4-lieux-de-la-demo/README.md), pour la même raison que le passage à la 3D :
tout lieu produit avant la bascule serait à refaire après.

Le constat de l'auteur, le 7 octobre : le moteur maison et son éditeur ne rendent pas « exactement
le même rendu en jeu que ce que j'ai sur la carte », le jeu « est très moche », les chargements sont
longs et les cartes denses saccadent. Il demande un combat « type Baldur's Gate 3 (non pas en case
mais en distance) » et « un moteur ayant un rendu graphique proche de ce type de production AAA ».
L'instruction complète est dans le [plan d'action du 7 octobre 2026](https://claude.ai/artifact/AHU61AmvLTCPBmDmUBd2Em),
qui mesure l'écart sur Arenarea et en nomme les cinq causes : le format de carte en grille, un rendu
sans lumière indirecte ni post-traitement, rien pour une carte dense (un appel de dessin par
maillage, pas de niveau de détail, chargement synchrone), la caméra fixe et le combat sur grille,
une chaîne de décor qui produit des boîtes.

## Ce qui ne bouge pas

- `Source/Core` : règles d20, classes, capacités, quêtes, dialogues, monde. Il n'inclut pas une
  ligne de Qt : il devient un module du nouveau projet. Seule sa part **spatiale** du combat
  (grille, chemins, ligne de vue, zones, tenaille, terrain tactique) se réécrit en distance (D-50).
- Les **données de contenu** en JSON, les **cartes peintes** de l'atlas, le **HUD** à la charte v2,
  les **portraits** et les **jetons**.
- La **chaîne des personnages** : image de référence, Meshy, squelettes `humanoid` et `quadruped`,
  clips, fiches de liaison, atelier Blender (D-44). Les vingt modèles s'importent au maître (D-53).
- Les **maillages** de l'Arena of Fate et les retours Meshy d'Arenarea.
- `Planning/`, ses lints, la méthode des lots et des bilans, les kits publiés et verrouillés.

## Ce qui tombe

| Bloc | Remplacé par | Retiré par |
|---|---|---|
| `HMI/Graphics`, `HMI/Runtime`, le chargeur glTF maison | le rendu du moteur | reste dans l'ancien dépôt, gelé au LOT-1023 (D-58) |
| L'interface Qt Quick (149 fichiers QML) | UMG construite par C++ (LOT-1020) | idem |
| Le LevelEditor : canevas, outils de grille, format v4 | l'éditeur du moteur, une description de carte en texte (LOT-1018) | idem |
| La caméra orthographique, la projection iso, les images dressées (§1 et §7 du standard 3D) | la caméra libre (D-49) | LOT-1016, LOT-1019 |
| La grille tactique et la part spatiale de `Core/Combat` | le combat en distance (D-50) | LOT-1017 |
| `reduce_model.py`, le budget de triangles | Nanite (D-53) | LOT-1015 |
| Les tests de rendu sous WARP, l'identité au pixel | les tests d'automatisation du moteur, des captures comparées à tolérance | LOT-1014 |

## Les règles de la version

1. **La porte d'abord.** Le [LOT-1012](lots/LOT-1012-porte-le-parvis-d-arenarea.md) ne touche pas
   au dépôt du jeu : un projet à part, le parvis d'Arenarea, deux personnages, la caméra, la
   marche. L'auteur le voit avant qu'un autre lot ne s'ouvre. S'il ne convainc pas, sur l'image ou
   sur la méthode, la version s'abandonne et la `0.0.4` reprend sur le moteur maison : pas de
   repli sur un autre moteur ([D-57](../../../vision/decisions.md) ; le
   [LOT-1013](lots/LOT-1013-porte-de-repli-godot.md) est abandonné avant d'être ouvert).
2. **Tout ce qui s'écrit est du texte** ([D-52](../../../vision/decisions.md)). Le contenu en JSON,
   les cartes en description texte construites par script, le code en C++ et en Python d'éditeur.
   Un `.umap` ou un `.uasset` est une sortie, en Git LFS ou en kit. Pas de logique en Blueprint.
3. **Un nouveau dépôt** ([D-58](../../../vision/decisions.md)). Le dépôt actuel passe en privé,
   sans CI, et reste la référence du moteur maison : il se joue tel quel jusqu'à ce que la démo se
   joue sur le nouveau (règle 2 de la trajectoire). Le nouveau dépôt, créé par l'auteur, reçoit
   par passation et mise au propre ce que la version garde ; rien de Qt n'y entre, et la règle
   D-32 s'y applique dès le premier lot. La recette (LOT-1023) gèle l'ancien dépôt.
4. **Chaque lot qui change l'image livre ses captures**, à midi et à 22 h, au cadrage du joueur :
   leçon 4 du bilan de la `0.0.2.5`.

## L'ordre, et pourquoi

| # | Lot | Filière | Taille | Attend |
|---|---|---|---|---|
| 1 | [LOT-1012](lots/LOT-1012-porte-le-parvis-d-arenarea.md) — la porte : le parvis d'Arenarea dans Unreal | moteur | L | — |
| — | [LOT-1013](lots/LOT-1013-porte-de-repli-godot.md) — la porte de repli sur Godot — **abandonné** ([D-57](../../../vision/decisions.md)) | moteur | M | — |
| 2 | [LOT-1014](lots/LOT-1014-socle-core-donnees-build.md) — le socle : le nouveau dépôt, Core en module, données, build, tests, CI | moteur | L | LOT-1012 |
| 3 | [LOT-1015](lots/LOT-1015-personnages-au-maitre.md) — les vingt personnages dans le moteur | pnj | L | LOT-1014 |
| 4 | [LOT-1016](lots/LOT-1016-camera-et-exploration.md) — caméra, marche, groupe, portails, jour et nuit | moteur | L | LOT-1014 |
| 5 | [LOT-1017](lots/LOT-1017-combat-en-distance.md) — le combat en distance | regles | XL | LOT-1015, LOT-1016 |
| 6 | [LOT-1018](lots/LOT-1018-cartes-composees.md) — le format de carte et sa chaîne | editeur | L | LOT-1016 |
| 7 | [LOT-1019](lots/LOT-1019-chaine-de-decor.md) — la chaîne de décor au niveau du moteur ; le standard 3D réécrit | standard | L | LOT-1018 |
| 8 | [LOT-1020](lots/LOT-1020-interface-umg.md) — les écrans et le HUD en UMG | interface | L | LOT-1016 |
| 9 | [LOT-1021](lots/LOT-1021-arenarea-reconstruit.md) — Arenarea reconstruit au standard D-54 | cartes | XL | LOT-1019 |
| 10 | [LOT-1022](lots/LOT-1022-portage-arena-of-fate-et-martpart.md) — l'Arena of Fate et Martpart portés | cartes | M | LOT-1019 |
| 11 | [LOT-1023](lots/LOT-1023-recette-et-version-0-0-3.md) — recette, retrait de l'ancien moteur, version | version | M | LOT-1017, LOT-1020, LOT-1021, LOT-1022 |

Après le socle, deux filières avancent en parallèle : les personnages (LOT-1015) et l'exploration
(LOT-1016). Le combat (LOT-1017) attend les deux. Les cartes (LOT-1018), le décor (LOT-1019) et
l'interface (LOT-1020) peuvent avancer pendant le combat. Arenarea (LOT-1021) et le portage
(LOT-1022) attendent la chaîne de décor.

La `0.0.2.5` a porté 30 000 lignes en cinq jours ; cette version en pèse trois à cinq fois plus.
Six à dix semaines sont l'ordre de grandeur, à mesurer au bilan, pas une promesse.

## Ce que la version fait aux lots ouverts

- [LOT-106](../v0.0.4-lieux-de-la-demo/lots/LOT-106-assets-hd-arena-of-fate.md), en cours, garde
  son statut : ses maillages sont portés par le LOT-1022, et sa validation artistique se fait sur le
  nouveau moteur.
- [LOT-147](../v0.0.4-lieux-de-la-demo/lots/LOT-147-zone-arenarea-reprise.md) : la reconstruction
  d'Arenarea est faite par le LOT-1021 ; ce qui lui reste — les PNJ, l'image de l'onglet, la
  relecture des postes — se réécrit à la recette.
- [LOT-151](../v0.0.4-lieux-de-la-demo/lots/LOT-151-kit-commun-intra-muros.md) et
  [LOT-107](../v0.0.4-lieux-de-la-demo/lots/LOT-107-carte-arena-of-fate.md) attendent désormais le
  LOT-1023 ; les autres lots de la `0.0.4` en dépendent par eux.
- Les questions que le standard 3D renvoyait au LOT-151 (contour sombre, forme des familles, budget
  d'un maillage de décor) se tranchent au LOT-1019, sur le nouveau moteur.

## Risques

| Risque | Ce qui le réduit |
|---|---|
| Le rendu ne convainc pas plus que l'actuel, parce que les assets restent simplistes (R-15) | la porte importe les meilleures pièces existantes ; le LOT-1019 produit au maître ; les bibliothèques du moteur sont admises pour la nature (D-55) |
| Les fichiers binaires cassent la méthode texte + Git + assistant (R-14) | D-52, vérifiée à la porte ; sans repli : la version s'abandonne (D-57) |
| La CI hébergée ne construit pas Unreal (R-16) | la CI se refait à neuf dans le nouveau dépôt (D-58, LOT-1014) : lints Python hébergés, construction du moteur sur le poste de référence |
| 60 images par seconde avec Lumen sur la RTX 4060 Ti | Lumen logiciel, TSR ou DLSS ; mesuré à la porte |
| La fatigue de l'auteur devant une troisième refonte en trois semaines (R-11) | la porte coûte une à deux semaines et montre un résultat jouable ; rien d'autre n'est engagé avant |
| La version ne « se joue » pas, contre la règle 2 de la trajectoire | l'ancien moteur reste jouable jusqu'à la recette ; la recette rejoue la quête et la série de l'arène sur le nouveau |
