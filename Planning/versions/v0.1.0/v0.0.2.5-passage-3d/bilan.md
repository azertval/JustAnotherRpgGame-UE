# Bilan de la version 0.0.2.5 — passage à la 3D

Écrit à la recette ([LOT-1010](lots/LOT-1010-recette-et-version-0-0-2-5.md)), le 5 octobre 2026,
comme la [cinquième règle de la trajectoire](../../../vision/trajectoire.md) le demande : ce qui a
coûté plus que prévu, et ce que la version suivante doit en retenir. Les chiffres viennent des
fiches de lot, du `CHANGELOG.md`, de l'historique Git, de `kits.lock.json` et des relevés de la
nightly. **Aucune mesure n'a été refaite sur le poste pour ce bilan** : l'auteur a demandé de ne
rien reconstruire en local, et ce qui aurait demandé un build est écrit comme dû, plus bas.

## En une page

| | |
|---|---|
| Ouverte | 30 septembre 2026 (D-29, PR #163), le jour du tag `v0.0.2` |
| Livrée | 5 octobre 2026, tag `v0.0.2.5` — **cinq jours** |
| Lots | **11 livrés** sur 12 (`LOT-1000` à `LOT-1011`) : 3 M, 8 L ; 1 clos sans modification (`LOT-1004`, D-43) |
| PR | treize, de #166 à #178 ; 598 fichiers de `Source/` touchés, 30 450 lignes ajoutées, 12 900 retirées |
| Décisions prises en route | D-38 à D-47 (dix), dont quatre ont changé le périmètre : D-38, D-43, D-46, D-47 |
| Critères de sortie | 4 sur 4, le premier **amendé** : la manette a été retirée en cours de version (voir [ci-dessous](#les-critères-de-sortie)) |
| Ce qui reste dû | les captures du guide ; la cadence de l'arène sur le poste de référence ; le coût en crédits et en temps d'un personnage ; le joueur extérieur |

La version a tenu ses deux buts : **une production de personnages stable** — vingt modèles liés
à deux squelettes, sans une retouche de maillage — et **un cycle jour / nuit**. Elle n'a pas
converti le décor de la Capitale, reporté d'un bloc à la `0.0.3` (D-43), et elle a livré en échange
ce qui n'était pas prévu : l'Arena of Fate entière en maillages, sur trois niveaux (D-46).

## Les critères de sortie

| Critère | Tenu par |
|---|---|
| La quête « Des pommes pour l'arène » et un combat à quatre contre quatre se rejouent de bout en bout en 3D, de jour comme de nuit, au clavier comme à la manette | **Jouée par l'auteur**, qui l'a confirmé le 5 octobre 2026 ; les suites d'intégration et système jouent la quête par ses issues et la série de l'arène, vertes en CI sur `main` (PR #178). **Au clavier et à la souris** : la manette a été retirée du jeu le 2 octobre (`EX-CTRL-002` retirée, révision de l'interface), et le critère tombe avec elle sur ce point. La nuit n'a pas de test système : elle est tenue par les tests de rendu éclairé (`test_lit_render`, `test_scene_lighting`, `test_world_light`) et par le jeu de l'auteur |
| Les quatre héros sont des modèles installés par l'atelier ; plus aucune bande d'animation de figurine ne reste | `LOT-1006` (132 bandes retirées), `LOT-1009` (dix-huit humanoïdes par `LevelEditor --apply`), `LOT-1011` (le lion et le loup) ; `git ls-files "…/Characters/**/*.anim.json"` ne trouve rien ; les 24 bandes de `Common/Fx/` restent, à dessein |
| L'éditeur montre exactement ce que le jeu dessine : un seul rendu, plus aucun peintre `QPainter` de la scène | `LOT-1002` : `--render` identique au pixel au rendu du jeu ; `ScenePainter` et `SceneImages` ne paraissent plus dans `Source/` |
| Le contrôle des orphelins passe ; les seules images de décor restantes sont celles de la dette déclarée | `check_orphans.py`, en CI depuis le `LOT-1001`, vert sur `main` ; la dette est celle du [README](README.md#la-dette-déclarée-pour-la-003), diminuée du kit de l'Arena of Fate |

## Le balayage final

Les recherches de la fiche, lancées sur `origin/main` (`e41b1411a`) :

| Recherche | Attendu | Trouvé |
|---|---|---|
| `ScenePainter`, `SceneImages` | rien | rien dans `Source/` ni dans `scripts/` ; le `CHANGELOG`, l'audit de l'éditeur et des fiches **livrées** les nomment, comme histoire |
| `*.anim.json` sous `Characters/` | rien | rien |
| `"portraits"` dans `Source` et `scripts` | rien | une ligne, `check_hd_assets.py` : le **refus** de la liste, posé par le `LOT-1011` — elle reste |
| « 2D HD », `style-2d-hd` hors archives | fiches livrées, décisions datées, textes retirés | cela, la **dette déclarée** (la maquette 2D HD et ses tests, D-43), et six textes en vigueur qui la disaient encore le standard : `README.md`, `Planning/README.md`, le guide du rendu, le guide du monde, `Levels/README.md`, `Assets/CREDITS.md` — **corrigés dans la PR de la recette** |
| PNG d'architecture du kit de la Capitale | ils restent | ils restent : 1 737 fichiers dans `capital/Common@3` |
| Scripts sans appelant | rien | rien |
| Tests désactivés, références d'image que rien ne lit | rien | aucun test désactivé (des `GTEST_SKIP` conditionnels seulement : pas de carte graphique, variable d'environnement absente) ; les 24 références QML sont toutes lues, la liste des écrans étant calculée |
| Anciennes versions des kits au verrou | une entrée par kit | huit kits, huit entrées |

Le balayage n'a donc rien eu à supprimer, comme la fiche l'espérait. Il a trouvé autre chose :
**un défaut de la chaîne de publication**. `extract_release_notes.py` ne reconnaissait un tag qu'à
trois nombres : `v0.0.2.5` gardait son `v`, la section du `CHANGELOG` restait introuvable, et la
release aurait échoué après quarante minutes de build, au moment de publier. Corrigé et testé
dans la PR de la recette.

## Les mesures

### Le poids des kits publiés

D'après `kits.lock.json`, au tag `v0.0.2` et aujourd'hui :

| Kit | `v0.0.2` | `v0.0.2.5` | Fichiers |
|---|---:|---:|---:|
| `Common` | 35,5 Mio (`@4`) | 66,8 Mio (`@9`) | 164 → 38 |
| `Maps` | 15,5 Mio | 15,5 Mio | 16 |
| `central-empire/Common` | 0,3 Mio (`@1`) | 10,1 Mio (`@3`) | 4 → 7 |
| `capital/Common` | 101,3 Mio (`@1`) | 110,7 Mio (`@3`) | 1 734 → 1 737 |
| `capital/arenarea` | 57,8 Mio | 57,8 Mio | 463 |
| `capital/arenarea/arena-of-fate` | 2,6 Mio (`@2`) | **421,3 Mio** (`@6`) | 19 → 145 |
| `capital/martpart` | 0,3 Mio (`@1`) | 9,8 Mio (`@3`) | 1 → 4 |
| `UI` | 11,4 Mio | 11,4 Mio | 250 |
| **Total** | **224,8 Mio** | **703,4 Mio** | |

Le jeu publié triple. Deux causes, de poids très inégal : **vingt modèles de personnage**, de 8 à
11 Mio chacun — environ 180 Mio répartis par niveau —, et **le kit de l'Arena of Fate**, à lui
seul 419 Mio de plus : 105 maillages, 2,04 millions de triangles, dont la coque du Colisée
(878 000 triangles) et 24 sculptures gardées dans la finesse de leur original. `Common` perd 126
fichiers en gagnant du poids : 132 bandes de figurine sont parties, des modèles sont arrivés.

### La cadence

Sur le **poste de référence**, mesures des fiches de lot (Release, 1080p, huit personnages) :

| Mesure | Valeur | Lot |
|---|---:|---|
| `WorldFrameStrips1080p` — huit figurines en bandes, l'état de la `0.0.2` | 5,8 à 5,9 ms | `LOT-1005` |
| `WorldFrameEightModels1080p` — huit modèles de 100 000 triangles, sans éclairage | 6,18 ms | `LOT-1007` |
| `WorldFrameLitEightModels1080p` — crépuscule, huit lumières de nuit | 6,24 ms | `LOT-1007` |
| `WorldFrameShadowedEightModels1080p` — le même, ombres portées | **6,47 ms** | `LOT-1007` |

La version entière — modèles, lumière, ombres — coûte donc **0,6 à 0,7 ms par image**, pour
16,7 ms disponibles. `bench_world_frame` sur Arenarea, dans la nightly (Release, `windows-2022`,
rendu logiciel — des valeurs à comparer entre elles, pas au poste) :

| Mesure | `7c419c351` (`v0.0.2`) | `197c29683` (3 octobre) |
|---|---:|---:|
| `ArenareaSnapshot` | 0,095 ms | 0,160 à 0,168 ms |
| `ArenareaComposeWholeMap` | 0,135 ms | 0,132 à 0,158 ms |
| `ArenareaBuildStaticScene` | 0,136 ms | 0,131 à 0,158 ms |
| `ArenareaFrame1080p` | 3,55 µs | 3,35 à 3,91 µs |
| `ArenareaFrame1080pEightModels` (pose de huit squelettes) | — | 42 à 49 µs |

`ArenareaSnapshot` a pris 0,07 ms entre les deux commits ; la cause n'a pas été cherchée, et la
mesure reste à trois ordres de grandeur sous l'image. Le reste tient dans le bruit de deux relevés
du même commit.

**Ce qui manque** : la cadence de **l'Arena of Fate**, la seule carte en maillages, sur le poste de
référence — le critère du `LOT-107` et la question que le `LOT-106` renvoyait à ce bilan. Aucune
mesure ne la couvre, la nightly ayant tourné avant l'arrivée de la carte (PR #178). Elle se relève
au `LOT-107`, avant sa clôture.

### Le coût d'un personnage

Ce que la chaîne mesure, d'après le [LOT-1009](lots/LOT-1009-les-quatre-heros.md#le-coût-dun-personnage)
et le `LOT-1011` :

| | |
|---|---|
| Modèles produits | 20 : dix-huit humanoïdes sur le squelette `humanoid` (53 os), le lion et le loup sur `quadruped` (29 os) |
| Par modèle | une image de référence, une génération Meshy, une fiche de liaison ; 100 000 triangles, un `.glb` lié de 8 à 11 Mio |
| Fiches de liaison | 17 sur 18 **estimées** par le script, sans correction ; une seule écrite à la main (la hauteur du brawler) |
| Retouches de maillage, de poids ou d'animation | **aucune** |
| Clips | réglés une fois par silhouette : six pour l'humanoïde, cinq pour le quadrupède |
| Crédits Meshy | 30 par personnage au barème du standard (image vers 3D 20, texture 10), avant toute régénération |

Le **temps passé** par personnage et le **nombre de régénérations** ne sont pas dans le dépôt :
l'auteur les tient dans son atelier, et la ligne « à compléter par l'auteur » du `LOT-1009` l'est
toujours. C'est le nombre que les lots de PNJ de la `0.0.3` attendent.

## Ce que chaque lot a coûté

| Lot | Taille | PR | Ce qui a pesé |
|---|---|---|---|
| `LOT-1000` — la preuve | M | #166 | trois chaînes essayées : les corps communs MPFB refusés, TripoSR refusé, Meshy retenu. La porte a tenu son rôle : D-31 est tombée avant d'avoir rien coûté au moteur |
| `LOT-1001` — le standard 3D | M | #167 | cinq décisions de l'auteur en un jour (D-38 à D-42, dont D-41 remplacée le jour même) ; `check_orphans.py` |
| `LOT-1002` — le canevas sur le rendu du jeu | L | #168 | conforme à sa taille ; a retiré le second rendu et sa parité |
| `LOT-1003` — maillages et profondeur | L | #169 | conforme ; les quatre cartes identiques au pixel |
| `LOT-1004` — le kit en maillages | L | #172 | **rien** : clos sans modification (D-43), reporté à la `0.0.3` |
| `LOT-1005` — squelette et animations | L | #170 | la chaîne de liaison, perdue, réécrite (`rig_character.py`) |
| `LOT-1006` — le squelette commun | L | #171 | livré en deux temps, une PR intermédiaire |
| `LOT-1008` — l'atelier des assets | L | #173 | la vue Character seule, la vue Scenery suivant le kit à la `0.0.3` ; l'aller-retour par Blender ajouté en route (D-44) |
| `LOT-1009` — les personnages | L | #174 | dix-huit modèles au lieu de quatre ; les fauves détachés |
| `LOT-1011` — les fauves | L | #175 | **né en route** : un second squelette, cinq clips |
| `LOT-1007` — éclairage | L | #177 | l'étude demandée par l'auteur (D-45) a écarté tout précalcul |
| `LOT-1010` — la recette | M | #180 | la réorganisation du planning (D-47) |

Hors lots, trois chantiers ont traversé la version : la **révision de l'interface** (menus du
mercenaire, HUD, retrait de la manette), l'**anticrénelage** (#176), et l'**Arena of Fate en
maillages** (#178, `LOT-106`, `LOT-107`, `LOT-157`), reprise trois fois en trois jours — mockups
validés le 2 octobre, première proposition 3D refusée le 3, niveaux superposés le 4.

## Ce qui a coûté plus que prévu

- **L'hypothèse de départ sur les personnages était fausse.** La version s'est ouverte sur D-31 —
  huit corps, une texture, des pièces d'équipement — et l'a abandonnée au premier lot. Le
  catalogue, le README et la trajectoire l'ont portée cinq jours après sa chute : c'est corrigé
  ici.
- **Les fauves.** Un quadrupède n'entre pas dans un squelette d'humanoïde : un lot L de plus,
  que la fiche du `LOT-1009` annonçait comme un risque.
- **Le décor.** Le but « décor d'architecture en maillages » a été retiré de la version (D-43),
  puis en partie rempli par un lieu qui n'y était pas inscrit. L'Arena of Fate a été produite
  **avant** le kit commun dont ses lots dépendaient : ses fiches le disent, le graphe non.
- **Le poids.** 421 Mio pour un lieu. D-23 n'impose aucun budget, et ce n'est pas un défaut ; mais
  l'archive du jeu, de 325 Mio à la `0.0.2`, grossit d'autant. Le budget d'un maillage de décor,
  que le standard laisse ouvert, se mesure au `LOT-151` — avant qu'un second lieu se produise à ce
  régime.

## Ce qui a marché, et se garde

- **La porte.** Un lot de preuve qui ne touche pas au moteur, avec un critère d'abandon : il a
  coûté une journée et évité de bâtir un atelier pour des corps dont l'auteur ne voulait pas.
- **« Un lot supprime ce qu'il remplace » (D-32), tenu par un contrôle.** La recette n'a trouvé
  aucun fichier mort. Sans `check_orphans.py`, elle en aurait trouvé.
- **L'éditeur avant le moteur.** Le canevas branché sur le rendu du jeu tant que ce rendu était en
  2D : la 3D est arrivée dans l'éditeur le jour où elle est arrivée dans le jeu.
- **Identique au pixel.** Chaque lot de moteur a rendu les quatre cartes livrées avant et après,
  sans un pixel d'écart : la bascule n'a rien cassé de ce qui se jouait.
- **Rien de précalculé** (D-45) : l'éclairage entier pour 0,3 ms, sans lot de cuisson ni donnée de
  plus à tenir à jour.
- **Un personnage est une fiche.** Dix-sept liaisons sur dix-huit sans intervention : la
  production de personnages est devenue le poste le plus prévisible du projet.

## Ce que la recette n'a pas fait

Écrit pour que cela ne se perde pas : la fiche le demandait.

| Quoi | Pourquoi | Où cela va |
|---|---|---|
| Les **captures du guide** régénérées | elles se prennent dans le jeu construit, et rien n'a été reconstruit en local | à la première PR qui touche le manuel ; le manuel du joueur décrit encore des mannequins et des jetons |
| La **cadence de l'arène** sur le poste de référence | même raison | `LOT-107` |
| L'installeur sur un **poste vierge** | comme à la `0.0.1` et à la `0.0.2`, c'est le test de fumée de `release.yml` qui en tient lieu : chaque archive est décompressée ailleurs, lancée, et doit rendre une image | `LOT-198` |
| Un **joueur extérieur** | il n'y en a pas eu, pour la troisième version | `LOT-198`, où il devient un livrable |
| Le **trot** des fauves approuvé dans le jeu ; la **validation artistique** de l'Arena of Fate | à l'auteur | `LOT-1011` (constat ouvert au standard), `LOT-106` |

Les références d'image des tests n'ont pas eu à être régénérées : la CI les compare à chaque PR,
et elle est verte. Le cahier de test est à jour de `main`.

## Ce que la version suivante doit en retenir

1. **Un lieu se juge sur le rendu du moteur, pas sur une image.** L'Arena of Fate a été refaite
   trois fois ; ce qui a tranché, à chaque fois, c'est la carte dans le jeu, à midi et à 22 h.
2. **Le graphe doit dire l'ordre réel.** Trois fiches « à faire » dont le travail est intégré, un
   kit produit avant son prérequis : la `0.0.3` s'ouvre sur un planning qui ne ment plus sur
   l'ordre, ou elle perd la règle 4.
3. **Le poids se regarde lieu par lieu.** Sans budget, mais avec un relevé : chaque lot de décor
   écrit le poids de son kit et le nombre de triangles de sa plus grosse pièce.
4. **Ce qui demande un build ne se promet pas à une recette sans build.** Les captures et les
   mesures sont des livrables des lots qui changent l'image, pas de la recette.
5. **Le coût humain d'un personnage manque toujours.** Tant qu'il n'est pas écrit, les lots de
   PNJ sont taillés à l'estime.

## Ce que la version laisse aux suivantes

La recette a porté une décision de planification, [D-47](../../../vision/decisions.md) : la `0.1.0`
ne garde que les trois lieux de la démo, les systèmes se finissent ensuite, et le monde vient
après. Les lots de zone ont été relus comme D-35 le demandait : ceux de la `0.0.3` **réécrits**
pour commander des maillages et des modèles, ceux de l'Empire central **marqués à réécrire**.

| À | Quoi | Où c'est écrit |
|---|---|---|
| `0.0.3` | Les trois lieux de la démo produits pour de bon ; la **dette d'images** soldée : le kit de la Capitale, Arenarea, Martpart | D-30, D-43, D-47 ; [README de la `0.0.3`](../v0.0.4-lieux-de-la-demo/README.md) |
| `0.0.3` | Le contour sombre, la forme de chaque famille de pièces, le budget d'un maillage de décor | [standard 3D, §8](../../../standards/style-3d.md#8-ce-qui-reste-ouvert) ; `LOT-151` |
| `0.1.0` | La recette des trois lieux, le joueur extérieur, l'installeur sur un poste vierge | `LOT-198` |
| `0.2.0` | La sauvegarde, le voyage, les outils de l'éditeur que portaient les versions de zone | D-47 ; [README de la `0.2.0`](../../v0.2.0/README.md) |
| `0.4.0` | Le reste de l'Empire central, en sous-versions `0.3.1` à `0.3.7` | D-47 ; fiches à réécrire (D-35) |
| sans date | Le post-traitement de l'image ; la silhouette `flying` ; la vue Scenery de l'atelier | standard 3D, §8 ; `LOT-1008` |
