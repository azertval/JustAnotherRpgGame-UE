+++
id = "LOT-1018"
titre = "Le format de carte et sa chaîne : des cartes composées"
version = "0.0.3"
filiere = "editeur"
statut = "en-cours"
taille = "L"
resume = "Une carte se décrit en texte — terrain, objets à transformation libre, zones, entités, portails — et se construit en niveau par script ; l'éditeur du moteur la retouche, et ce qu'il retouche revient dans le texte."
prerequis = ["LOT-1016"]
livrables = [
  "Le format `jadg-map`, version 5, en JSON : terrain (hauteurs, matières peintes, eau), objets (maillage, position en mètres, rotation, échelle, étage), routes et contours, zones nommées et volumes de combat, entités (arrivées, portails, PNJ, lumières, rencontres), notes ; spécifié dans `Documentation/Specification/niveaux.md`, schéma `level.schema.json`.",
  "`build_level.py` (script Python d'éditeur) : construit le niveau Unreal depuis la description, régénérable, et `read_level.py` qui relit un niveau retouché dans l'éditeur et réécrit la description — l'aller-retour, comme D-44 l'a fait pour Blender.",
  "Le contrôle de contenu (`ContentCheck`, `--check`) comme commandlet : portails appariés, arrivées citées, zones nommées, cases inatteignables devenues zones inatteignables sur le maillage de navigation.",
  "Les préfabriqués (LOT-130) comme acteurs composés, déclarés en texte ; le mode Quêtes (LOT-144) et les drapeaux comme outil d'éditeur en Python, sur les mêmes JSON qu'aujourd'hui.",
  "La migration des quatre cartes livrées (Arenarea v0, Martpart v0, les trois niveaux de l'Arena of Fate) du format v4 vers la version 5 : un script, les cartes relues par `--check`.",
  "L'arborescence par niveaux (LOT-124) et le kit par lieu inchangés : la description de carte vit dans `Levels/`, ses maillages dans le kit du lieu.",
]
criteres = [
  "`build_level.py` relancé sur un projet vierge redonne le même niveau (empreinte) ; `read_level.py` après une retouche dans l'éditeur réécrit une description que `build_level.py` reconstruit à l'identique.",
  "Les quatre cartes migrées s'ouvrent, se parcourent et passent `--check` ; les portails de la démo s'enchaînent.",
  "Une carte à deux étages praticables se joue sans changer de carte (D-51) : escalier, étage, redescente.",
  "Aucun `.umap` n'est modifié à la main : `check_orphans.py` cite chaque niveau par le script qui le produit.",
]
+++

## Pourquoi

Le format v4 est la première des cinq causes de l'écart : une grille de cases, sans rotation ni
terrain, ne peut pas porter la ville de l'atlas. Ce lot remplace le format, et garde ce qui faisait
la valeur de l'éditeur : le contrôle du contenu, les préfabriqués, le mode Quêtes, l'arborescence.
Il pose la règle D-52 sur l'objet qui la met le plus à l'épreuve : une carte.

## Périmètre

Dedans : le format, la construction, la relecture, le contrôle, les préfabriqués, le mode Quêtes,
la migration des cartes livrées.

Dehors, nommément :

- la production de décor (LOT-1019) : ce lot pose les pièces existantes ;
- Arenarea reconstruit (LOT-1021) : ce lot migre la v0 telle quelle ;
- les outils de l'éditeur de la `0.2.0` (peupler une zone, semis, horaires, onglet Carte) : leurs
  fiches se relisent pour le nouvel éditeur, à la recette.

## À supprimer

Rien dans ce lot : le format v4, le LevelEditor et ses tests vivent dans l'ancien dépôt, qui se
joue jusqu'à la recette (D-58). Dans le nouveau dépôt, ils ne sont jamais entrés.

## Conception

- **Le texte est la source, le niveau est une sortie.** La description est ce que Git relit, ce que
  les lints contrôlent, ce que l'assistant écrit. L'éditeur du moteur sert à placer à la main ce
  qu'un script ne place pas bien ; `read_level.py` ramène le geste dans le texte, et rien d'autre
  n'en revient.
- **Le terrain** est un `Landscape` : hauteurs et couches de matière en images régénérées depuis
  la description (une carte de hauteurs, une image par couche), pas peintes dans l'éditeur. Les
  berges, les dénivelés et les rues du plan en viennent.
- **Un lieu à plusieurs étages est une carte** (D-51) : les trois niveaux de l'Arena of Fate se
  superposent dans une seule description, avec des niveaux de chargement par étage.
- **Les entités** gardent leurs identifiants et leurs noms : `from-martpart`, `parvis`, les
  arrivées de la quête ne changent pas, pour que les tests de la quête ne changent pas non plus.

## Risques et questions ouvertes

- **L'aller-retour.** Tout ce que l'éditeur sait faire ne se relit pas en texte (un acteur exotique,
  un réglage de rendu). La règle est : ce qui ne se relit pas ne se fait pas dans l'éditeur ; la
  liste de ce que `read_level.py` relit est la frontière, écrite dans la spécification.
- **La taille.** Arenarea v0 compte 1 663 placements ; une carte reconstruite en comptera dix fois
  plus. La construction par script doit tenir en minutes, pas en heures ; mesurée sur la migration.
- **La dette du LOT-1016** (clos le 8 octobre 2026), que ce lot retire : **deux étages l'un
  au-dessus de l'autre** — la trace de la file du groupe est en deux dimensions, éprouvée sur une
  terrasse et sa rampe seulement — et **la carte de Core de la porte** : la grille d'Arenarea de
  l'ancien jeu ne décrit pas le parvis construit dans Unreal, le format de carte les met d'accord.

## Avancement — 9 octobre 2026

Fait par l'assistant, en autonomie, sur la branche `lot/1018-cartes-composees`. Le lot est
**ouvert** (`en-cours`) : sa clôture est une décision de l'auteur. Rien de ce qui suit n'a été vu
dans une fenêtre : les images sont **à juger par l'auteur à la recette**. Le fonctionnement est
décrit dans [Les cartes dans le moteur](../../../../../Documentation/Guide/guide-cartes-moteur.md) ;
le format, dans [`niveaux.md`](../../../../../Documentation/Specification/niveaux.md) §2
(`EX-LVL-031` à `EX-LVL-039`).

### Ce qui est fait

- **Le format `jadg-map`, version 5** (`EX-LVL-031`) : une description par carte, qui se déclare
  et dit à la fois ce que Core joue (grille de collision du rez, couches de pièces, entités sur
  leurs cases) et ce que le moteur construit (terrain, routes et contours, objets en mètres avec
  lacet, tangage, roulis, échelle et étage, dallages, préfabriqués, groupe, personnages, lumières,
  ciel, navigation, cadrages, notes). Schéma `level.schema.json` réécrit pour la v5. Repère : x
  vers l'est, y vers le sud, z vers le haut, le coin de la case (0, 0) en `origin`.
- **Core lit la v5** (sans moteur, `core::LevelLoader`) : le format déclaré, l'origine, les
  **étages** (`core::Storey`, `EX-LVL-032`), l'étage et le **volume** de chaque entité
  (`core::MapVolume`, `EX-LVL-033`) ; `elevation` et `floor` sont refusés dans une v5 (D-51),
  une v5 n'est jamais une variante. Les zones de combat se lisent de leur volume
  (`core::combatZoneOf`, `core::volumeCells`) : le montage du `LOT-1017` les prend telles quelles.
  L'exploration ne sollicite, ne franchit, ne déclenche que ce qui est à l'étage du héros
  (`core::ExplorationIntent::storey`) ; un point d'arrivée pose à son étage ; la trace du groupe
  porte la hauteur de chaque pas (`core::FollowTrail::heightBehind`). Dix tests GoogleTest
  (`test_format_v5.cpp`, fixture `format-v5.json`). Core lit toujours la v4 (`EX-LVL-005`) et
  l'écrit encore pour ses tests (`LEVEL_WRITER_VERSION`).
- **`scripts/maps/jadg_map.py`** : la seule écriture d'une v5, sous sa forme canonique ; le
  **contrôle de contenu** (`--check`, en CI) ; la **migration** (`--migrate`) ; la résolution des
  pièces des kits (du lieu vers le monde) et les préfabriqués.
- **`scripts/maps/build_level.py`** (`EX-LVL-034`) **absorbe `build_scene_unreal.py`**, supprimé
  avec `Source/Elements/Scenes/` (D-32) : une seule chaîne construit tous les niveaux, sous
  `/Game/Maps/Levels/<carte>` — la porte et le socle compris. Il pose le **terrain** (un
  `Landscape` dont les hauteurs et les poids des couches sont régénérés en images, l'eau d'un
  contour — `UJadgSceneBuild::SpawnLandscape`), les couches de pièces **par instances**
  (`SpawnInstances`), les objets, les dallages, les **préfabriqués** (`AJadgPrefab`), le groupe et
  les PNJ par leur fiche, un repère par entité, une boîte par volume, le cadre de Core et ses
  étages (`AJadgMapFrame::StoreyHeights`), les cadrages ; il contrôle le **maillage de
  navigation** (`-JadgCheck`, `UnreachablePoints`) et écrit l'**empreinte** du niveau.
- **`scripts/maps/read_level.py`** relit la **frontière** de l'éditeur (`EX-LVL-035`, tableau dans
  `niveaux.md`) ; **`check_level_roundtrip.py`** prouve l'aller-retour, à chaque
  `build.ps1 -Unreal`.
- **Le contrôle de contenu** à trois niveaux (`EX-LVL-036`) : le texte (`jadg_map.py --check`,
  étape de CI), Core (`JadgContentCheck` lit chaque carte et valide le graphe des portails), le
  niveau construit (le maillage de navigation).
- **Les préfabriqués** (`EX-LVL-037`) : format `jadg-prefab` ; les cinq tampons de l'ancien
  éditeur migrés (`Editor/Prefabs/`) ; le Colisée de la porte en est un.
- **Le mode Quêtes** (`EX-LVL-038`, `scripts/maps/quest_mode.py`) : une carte vue à une étape de
  quête, sur les JSON des quêtes et des dialogues ; dans l'éditeur, il cache les acteurs des
  entités absentes ; `--check` (en CI) refuse un drapeau que rien ne déclare.
- **La migration des quatre cartes** (`EX-LVL-039`) : Arenarea, Martpart, l'Arena of Fate et ses
  deux niveaux, **telles quelles** — grille, couches, entités et identifiants inchangés —, leurs
  notes d'éditeur entrées dans la description (`*.editor.json` supprimés). Les tests de la quête
  n'ont pas changé d'une ligne (`Jadg.Exploration.QueteDesPommes` passe sur le contenu migré).
  Les cartes d'essai sont écrites en v5 par `build_essai_maps.py` ; l'arène d'essai porte sa zone
  de combat et son marqueur **en volumes**.
- **Les dettes du LOT-1016.** **Deux étages superposés** : la carte d'essai `essai/etages` (un
  plancher à 3 m, une rampe, un portail du rez sous le plancher qui mène au palier de l'étage, un
  panneau et une lanterne de l'étage à sa verticale, un terrain autour) et
  `Jadg.Exploration.DeuxEtages` : le meneur monte, la file le suit en hauteur, le panneau de
  l'étage se désigne, rien ne se franchit à la verticale du portail ; redescendu, le portail le
  pose au palier, à l'étage, la file avec lui. **La porte joue sa carte de Core** :
  `porte-1012.json`, écrite par `build_gate_scene.py`, dont la grille vient de la géométrie qu'il
  pose (l'ellipse du Colisée, l'emprise mesurée des façades, la ruelle hors du dallage) ; le groupe
  y entre par les fiches des héros.

### Les décisions de réalisation

| Décision | Ce qui est retenu | Pourquoi |
|---|---|---|
| Le repère de la v5 | celui de la grille : x est, y sud, z haut, en mètres ; un lacet tourne le sud vers l'est (comme les scènes du LOT-1012) | les cases et les mètres ont les mêmes axes ; un volume se ramène à des cases par une soustraction |
| Les étages | `storeys` déclarés, `storey` par entité ; l'étage du héros lu par le moteur à la hauteur de ses pieds (un demi-mètre de tolérance) | Core constate, il ne refait pas le pas (LOT-1016) |
| La file en hauteur | la hauteur portée par la trace de Core ; le maillage cherché à 1,2 m du point sur une carte à étages | sans cela, un suiveur à l'étage cherchait sa place au rez, sous lui |
| Les couches de pièces | une pièce par case, au centre de son emprise (le manifeste du kit), par instances | « telle quelle » ; 12 913 pièces en 163 acteurs |
| La hauteur d'un étage de décor de la v4 | 3 m par étage (`floor` devient `z`) | **provisoire** : la v4 la donnait en pixels d'art ; à juger, et Arenarea se reconstruit au LOT-1021 |
| Une entité de la v5 | sa case reste écrite ; le volume s'y ajoute | ce que Core tire d'une carte ne change pas pour le jeu |
| L'empreinte | les acteurs par étiquette, classe, transformation arrondie (0,1 cm, 0,01°), maillage, réglages ; ce que le moteur ajoute (maillage de navigation, monde) en est exclu | les noms internes des objets changent d'une construction à l'autre |
| Le repère du moteur | mesuré une fois, sur le bloc repère des données d'essai | toute pièce `.glb` passe par le même import ; plus de `frameReference` par carte |
| L'écrivain de Core | reste en v4 | une v5 porte des sections que Core ne lit pas ; elle s'écrit par `jadg_map.py` |

### Ce qui se mesure

Mesuré le 9 octobre 2026 sur le poste de référence (Unreal Engine 5.8.3, RTX 4060 Ti, i7-8700),
éditeur sans fenêtre (`-nullrhi`), chaque carte construite avec l'import de ses maillages.

| Carte | Placements | Construction | dont import | Pièces sans maillage |
|---|---|---|---|---|
| Arenarea v0 | 12 913 pièces de couche (dont les 1 663 de décor), 163 acteurs | **165 s** | 111 s (120 maillages) | 14 (`reused-af-*`) |
| Martpart v0 | 10 104 pièces, 54 acteurs | 109 s | 94 s | 113 (`mp-cypress`, `mp-tree`) |
| Arena of Fate | 374 pièces | 84 s | 70 s | 0 |
| — sous les tribunes | 689 pièces | 52 s | 41 s | 0 |
| — catacombes | 665 pièces | 67 s | 55 s | 0 |
| porte-1012 | 25 objets, 3 634 dalles, 373 objets du Colisée | 4,7 s | (déjà importés) | 0 |
| essai/etages (terrain compris) | 55 objets, 192 dalles, terrain de 127 × 127 sommets | 0,8 s | — | — |

La construction tient **en minutes**, et l'essentiel est l'import des maillages, fait une fois :
la pose d'Arenarea, hors import, prend environ 50 s. Le contrôle du maillage de navigation passe
sur les onze cartes.

L'aller-retour (`check_level_roundtrip.py`) : construit de rien, la même empreinte reconstruit ;
retouché (un mur déplacé de 37 cm et 21 cm et tourné de 15°, la rampe allongée d'un dixième, le
panneau porté d'une case, un cadrage incliné de 5°), relu — quatre gestes, eux seuls —, reconstruit
depuis le texte relu : l'empreinte du niveau retouché.

Cadence (captures, dix secondes par heure, caméra en rotation) :

| Carte | 12 h | 22 h |
|---|---|---|
| essai/etages | 106,8 images/s (9,4 ms, GPU 8,8 ms) | 104,0 images/s (9,6 ms) |
| Arena of Fate (migrée) | 108,4 images/s (9,2 ms, GPU 8,6 ms) | 109,3 images/s (9,2 ms) |

Les captures, à midi et à 22 h, sont dans [`annexes/LOT-1018/captures/`](../annexes/LOT-1018/captures/)
avec les mesures et les empreintes d'Arenarea et de Martpart. **À juger par l'auteur à la
recette** : les pièces de l'Arena of Fate y sont grises, sans leur texture.

### Ce qui se vérifie (9 octobre 2026)

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | **677 tests de Core, 100 % passés** (10 nouveaux, `FormatV5Test`) |
| `powershell scripts/build.ps1 -Unreal` | code 0 : cible d'éditeur, `JadgContentCheck` (11 cartes lues par Core), **20 tests du moteur passés** (`Jadg.Exploration.DeuxEtages` nouveau), `jadg_map.py --check` (11 cartes, 0 erreur, 3 avertissements : trois points d'arrivée de la v4 qu'aucun portail ne cite), l'aller-retour réussi, le socle reconstruit par `build_level.py` et ses captures à leur référence (pire bloc 0,63 et 0,91 sur 255) |
| `powershell scripts/build.ps1 -Unreal -Parcours` | code 0 : les trois cartes d'essai migrées construites, la quête rendue 52 s après le lancement |
| `powershell scripts/build.ps1 -Unreal -ParcoursCombat -Seed 2` | code 0 : victoire au round 7, retour au parvis, le meneur à la même case, `encounter/arene-bandits/won` posé ; la zone de combat et le marqueur en volumes |
| `scripts/check.py --sans-hooks` | **18 contrôles verts** (dont les deux nouveaux : cartes v5, drapeaux des cartes) ; pytest 275 passés ; `lint_planning`, `lint_docs`, cahier de test régénéré (689 cas) ; ruff et clang-format passés |

### Les critères

| Critère | État |
|---|---|
| `build_level.py` relancé sur un projet vierge redonne le même niveau ; `read_level.py` après une retouche réécrit une description que `build_level.py` reconstruit à l'identique | **tenu** sur la carte à deux étages : de rien (le niveau et ses maillages d'essai effacés), reconstruit, retouché, relu, reconstruit — empreintes égales. Le « projet vierge » est celui de la carte (ses sorties), pas `Content/` entier |
| Les quatre cartes migrées s'ouvrent, se parcourent et passent `--check` ; les portails de la démo s'enchaînent | **partiel** : les cinq niveaux se construisent, passent `--check` et le contrôle du maillage, l'Arena of Fate s'ouvre dans le jeu (captures) ; les portails de la démo s'enchaînent **dans Core** (`QueteDesPommes`, sur le contenu migré) et dans le jeu sur les cartes d'essai migrées (`-Parcours`). Personne n'a marché de Martpart à Arenarea dans le jeu lancé |
| Une carte à deux étages praticables se joue sans changer de carte : escalier, étage, redescente | **tenu** (`Jadg.Exploration.DeuxEtages`) ; l'escalier est une rampe |
| Aucun `.umap` n'est modifié à la main : `check_orphans.py` cite chaque niveau par le script qui le produit | **tenu** : `/Game/Maps/Levels` (`jadg_map.py`, `build_level.py`) ; les anciennes `Porte1012` et `Socle1014` retirées du poste |

| Livrable | État |
|---|---|
| Le format v5, spécifié, schéma | tenu |
| `build_level.py` et `read_level.py`, l'aller-retour | tenu |
| Le contrôle de contenu comme commandlet | tenu à trois niveaux : le commandlet (`JadgContentCheck`) lit les cartes et valide le graphe ; le texte et le maillage sont contrôlés par script |
| Les préfabriqués ; le mode Quêtes | tenu (`jadg-prefab`, `quest_mode.py`) ; le mode Quêtes n'a pas d'interface dans l'éditeur : un script qu'on lance |
| La migration des quatre cartes | tenu |
| L'arborescence et le kit par lieu inchangés | tenu |

### Ce qui s'écarte de la fiche

- **Le lecteur v4 n'est pas supprimé** : la v5 est la v4 plus ce que la construction lit, lus par
  une seule fonction ; `EX-LVL-005` veut que toute version passée se lise, et des dizaines de tests
  de Core écrivent leurs cartes en v4. L'écrivain de Core reste en v4 pour eux.
- **La spécification de l'ancien éditeur n'est pas supprimée** (`editeur-niveaux.md`) : elle dit
  désormais qu'elle décrit le `LevelEditor` de l'ancien dépôt ; ses exigences sont citées par
  `core::LevelDraft` et ses tests. La fiche ne demande rien à supprimer.
- **Les trois niveaux de l'Arena of Fate restent trois cartes** : la conception les veut en une
  seule (D-51) ; c'est le `LOT-1022`, et les fusionner ici aurait changé les identifiants de carte
  que la quête cite.
- **Le lion de la porte** garde son maillage lié (`characters`), dette du `LOT-1015`.
- **L'escalier est une rampe** : aucun maillage d'escalier n'est dans les données d'essai.

### Ce qui reste au lot

- Marcher dans le jeu lancé de Martpart à Arenarea et jusqu'à l'Arena of Fate par leurs portails
  (un parcours sur les cartes migrées) ; les captures de Martpart et d'Arenarea.
- Les pièces des cartes migrées que les kits n'ont pas (`mp-cypress`, `mp-tree`, `reused-af-*`).
- L'interface du mode Quêtes dans l'éditeur (un panneau) ; aujourd'hui un script.

### Questions pour l'auteur

1. **La hauteur d'un étage de décor de la v4** : 3 m par étage, provisoire. Une autre valeur, ou
   attendre Arenarea reconstruit (LOT-1021) ?
2. **Le lecteur v4** : le garder (`EX-LVL-005`, les tests de Core) ou réécrire les tests en v5 et
   ne plus lire que la v5 ?
3. **`editeur-niveaux.md`** : le retirer en entier (et réécrire les citations de `core::LevelDraft`)
   ou le relire pour le nouvel éditeur à la recette ?
4. **L'escalier** : une rampe suffit-elle à l'essai, ou faut-il un maillage d'escalier ?
5. **Les textures des pièces de kit** : l'Arena of Fate sort grise de la chaîne ; est-ce attendu
   jusqu'au LOT-1019 (la chaîne de décor), ou une matière à reprendre ici ?
