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

**Périmètre personnages révisé le 20 octobre 2026 :** [D-68](../../../vision/decisions.md)
remplace les anciennes obligations MetaHuman/Mutable et de squelette unique. Les mentions
de D-63/D-64 dans l'historique de migration ci-dessous décrivent le prototype, pas le choix
de production à éprouver au LOT-1024. Le nouveau découpage figure dans l'ordre des lots.

## Ce qui ne bouge pas

- `Source/Core` : règles d20, classes, capacités, quêtes, dialogues, monde. Il n'inclut pas une
  ligne de Qt : il devient un module du nouveau projet. Seule sa part **spatiale** du combat
  (grille, chemins, ligne de vue, zones, tenaille, terrain tactique) se réécrit en distance (D-50).
- Les **données de contenu** en JSON, les **cartes peintes** de l'atlas, le **HUD** à la charte v2,
  les **portraits** et les **jetons**.
- Pour les **personnages**, seulement : l'image de référence peinte (pour les pièces que Meshy
  produit), le portrait et le jeton peints (D-30), et **Meshy pour les pièces propres au monde**
  (cornes, défenses, queues, oreilles, armures signatures, armes). Le reste de leur chaîne tombe
  (D-63, D-64).
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
| La chaîne maison des personnages (squelettes MPFB, clips posés par cibles, atelier Blender) | MetaHuman, Mutable, bibliothèques d'animations du moteur (D-63, D-64) | LOT-1015 |
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
| 1 | [LOT-1012](lots/LOT-1012-porte-le-parvis-d-arenarea.md) — La porte : le parvis d'Arenarea dans Unreal — **livré** | moteur | L | — |
| — | [LOT-1013](lots/LOT-1013-porte-de-repli-godot.md) — La porte de repli : le même parvis dans Godot — **abandonné** | moteur | M | LOT-1012 |
| 2 | [LOT-1014](lots/LOT-1014-socle-core-donnees-build.md) — Le socle : Core en module, données, build, tests, CI — **livré** | moteur | L | LOT-1012 |
| 3 | [LOT-1015](lots/LOT-1015-personnages-et-createur.md) — Les personnages dans le moteur : squelette, animations, créateur Mutable, les quatre héros — **livré** | pnj | L | LOT-1014 |
| 4 | [LOT-1016](lots/LOT-1016-camera-et-exploration.md) — Caméra, marche, groupe, portails, jour et nuit — **livré** | moteur | L | LOT-1014 |
| 5 | [LOT-1017](lots/LOT-1017-combat-en-distance.md) — Le combat en distance — **livré** | regles | XL | LOT-1015, LOT-1016 |
| 6 | [LOT-1018](lots/LOT-1018-cartes-composees.md) — Le format de carte et sa chaîne : des cartes composées — **livré** | editeur | L | LOT-1016 |
| 7 | [LOT-1019](lots/LOT-1019-chaine-de-decor.md) — La chaîne de décor au niveau du moteur, et le standard 3D réécrit — **livré** | standard | L | LOT-1018 |
| 8 | [LOT-1020](lots/LOT-1020-interface-umg.md) — Les écrans et le HUD en UMG — **livré** | interface | L | LOT-1016 |
| 9 | [LOT-1024](lots/LOT-1024-createur-especes-et-humanoides.md) — Le générateur : choix de chaîne et prototype jouable | pnj | L | LOT-1015, LOT-1016 |
| 10 | [LOT-1026](lots/LOT-1026-bases-anatomiques-et-recettes.md) — Le générateur : bases anatomiques et recettes versionnées | pnj | L | LOT-1024 |
| 11 | [LOT-1027](lots/LOT-1027-garde-robe-et-adaptation.md) — Le générateur : garde-robe et adaptation aux corps | assets | L | LOT-1026 |
| 12 | [LOT-1028](lots/LOT-1028-createur-complet-en-jeu.md) — Le générateur : créateur complet en jeu | interface | L | LOT-1026, LOT-1027, LOT-1020 |
| 13 | [LOT-1029](lots/LOT-1029-presets-metiers-et-personnages-demo.md) — Le générateur : presets métiers et personnages de la démo | pnj | L | LOT-1028, LOT-1017 |
| 14 | [LOT-1025](lots/LOT-1025-creatures-lion-et-loup.md) — Les créatures : familles animales, lion et loup | pnj | L | LOT-1026, LOT-1017 |
| 15 | [LOT-1030](lots/LOT-1030-validation-generateur-et-populations.md) — Le générateur : validation en jeu et passage en production | pnj | M | LOT-1025, LOT-1029 |
| — | [LOT-1021](lots/LOT-1021-arenarea-reconstruit.md) — Arenarea reconstruit au standard D-54 — **abandonné** | cartes | XL | LOT-1019 |
| 16 | [LOT-1022](lots/LOT-1022-portage-arena-of-fate.md) — L'Arena of Fate portée — **livré** | cartes | M | LOT-1019 |
| 17 | [LOT-1023](lots/LOT-1023-recette-et-version-0-0-3.md) — Recette, retrait de l'ancien moteur et version 0.0.3 | version | M | LOT-1017, LOT-1020, LOT-1022, LOT-1030 |

Le LOT-1015 reste un prototype historique : il ne démontre pas une chaîne MetaHuman
habillée ni les curseurs d'identité dans le jeu. **Reprise du 20 octobre 2026 (D-68)** :
le LOT-1024 choisit la chaîne sur un créateur témoin empaqueté avant toute production.
L'existant est remplaçable ; Mutable est le premier candidat, MetaHuman une source possible.

Le chemin du générateur devient :

```text
LOT-1024 : comparaison et preuve en jeu
  -> LOT-1026 : bases anatomiques, rigs, morphs et recettes
       -> LOT-1027 : garde-robe
            -> LOT-1028 : créateur complet en jeu et outil de production
                 -> LOT-1029 : héros, PNJ de la démo et presets métiers
       -> LOT-1025 : familles animales, lion et loup
  -> LOT-1030 : validation commune (attend LOT-1029 et LOT-1025)
       -> LOT-1023 : recette de version
```

Les prérequis complets sont ceux du tableau et des fiches : l'interface s'appuie aussi sur
LOT-1020, la production et les animaux sur LOT-1017. Les bases anatomiques peuvent partager
des conventions sans imposer un squelette universel. Le LOT-314 réutilise l'apparence livrée
pour le parcours de règles en 0.3.0. Les lots de peuplement consomment la chaîne validée ;
ils ne sont pas remplacés par un remplissage automatique de la capitale dans ces lots.

Le 20 octobre 2026, l'auteur livre les LOT-1017 à LOT-1020 et la part Arena of Fate du
LOT-1022 avec la version ; il abandonne le LOT-1021 et rend la part Martpart du LOT-1022,
redites du périmètre de la `0.0.4` (LOT-106, LOT-110, LOT-147, LOT-157).
Cette révision du générateur conserve ces changements. La recette attend le LOT-1030 ;
les essais utilisent la démo active autour de l'arène, sans restaurer les cartes archivées.

La `0.0.2.5` a porté 30 000 lignes en cinq jours ; cette version en pèse trois à cinq fois plus.
Six à dix semaines étaient l'ordre de grandeur initial, pas une promesse. Le découpage du
générateur du 20 octobre impose une nouvelle estimation après le prototype LOT-1024 ; aucune
durée de production de garde-robe n'est déduite des seuls essais sur mannequins.

## Ce que la version fait aux lots ouverts

- [LOT-106](../v0.0.4-lieux-de-la-demo/lots/LOT-106-assets-hd-arena-of-fate.md), en cours, garde
  son statut : ses maillages sont portés par le LOT-1022, et sa validation artistique se fait sur le
  nouveau moteur.
- [LOT-147](../v0.0.4-lieux-de-la-demo/lots/LOT-147-zone-arenarea-reprise.md) : la reconstruction
  d'Arenarea lui revient (le LOT-1021, qui la redisait, est abandonné le 20 octobre 2026) ; elle
  se fait sur le nouveau moteur, avec la chaîne de décor du LOT-1019.
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
