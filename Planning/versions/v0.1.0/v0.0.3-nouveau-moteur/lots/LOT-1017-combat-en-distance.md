+++
id = "LOT-1017"
titre = "Le combat en distance"
version = "0.0.3"
filiere = "regles"
statut = "en-cours"
taille = "XL"
resume = "Le combat se joue en mètres, à la manière de Baldur's Gate 3 : déplacement libre sur le maillage de navigation, ligne de vue par rayon, zones en volumes, hauteur comptée ; les règles, les classes et l'IA de la 0.0.2 ne changent pas."
prerequis = ["LOT-1015", "LOT-1016"]
livrables = [
  "`Core/Combat` sans grille : `BattleGrid`, `Pathfinding`, `LineOfSight`, `AreaOfEffect`, `Flanking`, `TacticalTerrain` et `IsoProjection` remplacés par un modèle en mètres — positions, rayons d'allonge, budgets de déplacement, volumes de zone — derrière une interface d'espace que le moteur implémente (navigation, rayons) et que les tests simulent.",
  "Les règles spatiales du *Manuel* en mètres : allonge 1,5 m, déplacement 9 m, cône 4,5 m, sphère 6 m, attaques d'opportunité au départ de l'allonge, prise en tenaille par angles, abri par part cachée du volume, avantage de hauteur.",
  "L'IA des profils du Guide du Maître (LOT-23) avec les mêmes poids, le choix de position par EQS ; les cinq profils JSON inchangés.",
  "L'aperçu de combat (LOT-140) en distance : le chemin tracé, la portée restante, les cibles atteignables, le compte des capacités ; la sélection au clic et au clavier.",
  "Les zones de combat et le déploiement du groupe (LOT-143) en volumes posés sur la carte ; `analyzePartyDeployment` et `inspect` sur ces volumes.",
  "La série de l'arène et la simulation à cent graines de la recette `0.0.2` rejouées en distance ; les écarts entre trios écrits dans la fiche, comme D-36 les a mesurés.",
  "Les tests de Core réécrits sur l'espace simulé ; les tests d'intégration du combat sur le moteur.",
]
criteres = [
  "Un combat à quatre contre quatre se joue de bout en bout dans l'Arena of Fate, au clavier et à la souris, avec déplacement libre, attaques d'opportunité, zones et abri.",
  "Chaque capacité des quatre classes a le même effet qu'en `0.0.2`, à la distance près : la simulation à cent graines donne un écart entre trios inférieur à 20 points, comme à la recette `0.0.2`.",
  "Un sort de zone touche exactement les créatures dont le volume croise le sien ; un rayon bloqué par un mur ne touche pas.",
  "Un personnage en hauteur a l'avantage que le *Manuel* lui donne ; la hauteur se lit dans l'aperçu.",
  "Les tests de Core passent sans GPU ; les profils d'IA n'ont pas changé d'une valeur.",
]
sources = [
  "Manuel des Joueurs, ch. 9 (combat) ; Guide du Maître, p. 247-255 (IA)",
]
+++

## Pourquoi

Le *Manuel* compte en mètres. La grille n'était qu'une façon de les dessiner, et elle a imposé des
demi-cases, un départage de chemins et un abri non additionné (LOT-19, LOT-22). Un combat en
distance rapproche le jeu de la règle écrite et de ce que l'auteur attend : « non pas en case mais
en distance ». C'est le lot de moteur le plus lourd de la version ; il se découpe à l'ouverture.

## Périmètre

Dedans : la part spatiale de `Core/Combat`, les règles spatiales du *Manuel*, l'IA, l'aperçu, les
zones de combat, la série de l'arène, les tests.

Dehors, nommément :

- les jets, les dégâts, l'économie d'actions, les états, l'agonie et la mort (LOT-20, LOT-21,
  LOT-137) : inchangés ;
- les classes, les capacités, les sorts (LOT-131 à LOT-136) : inchangés, leurs portées passent en
  mètres par une table ;
- les mécanismes propres à Larian (surfaces, poussée, lancer d'objets, dés visibles) : à la `0.2.0`
  par une décision écrite, règle 3 de la trajectoire ;
- l'interface de combat finale (LOT-1020) : ce lot livre l'aperçu et une interface de travail.

## Conception

Trois lots à l'ouverture, dans cet ordre :

1. **Les règles spatiales** (L). Un `CombatSpace` abstrait : positions en mètres, un volume par
   créature (cylindre de taille du *Manuel*), `reach`, `pathLength`, `lineOfSight`, `cover`,
   `shapeHits`. Deux implémentations : la simulation de Core pour les tests (un plan avec des
   obstacles) et le moteur (navigation, rayons). `TurnOrder`, `ActionEconomy`, `Attack`, `Damage`
   ne voient que l'interface.
2. **L'IA** (M). Les profils gardent leurs poids ; l'espérance en entiers (LOT-23) s'évalue sur des
   positions candidates fournies par EQS (couverts, hauteurs, distances) au lieu des cases voisines.
3. **L'interface de travail et les zones** (M). L'aperçu, la sélection, les volumes de combat, le
   déploiement ; la série de l'arène et la simulation.

Décisions déjà prises : une case de 1,5 m reste l'**unité** du *Manuel* pour les portées écrites
dans les données (une portée « 6 cases » vaut 9 m), sans grille à l'écran. Les attaques
d'opportunité et la tenaille suivent le *Manuel*, pas Larian. La hauteur donne l'avantage du
*Manuel*, rien de plus.

### Les combattants

Le [LOT-1015](LOT-1015-personnages-et-createur.md) ne livre que les quatre héros, faits par le
créateur de personnage (D-63). Les adversaires humanoïdes de l'arène reçoivent leurs fiches au
[LOT-1024](LOT-1024-createur-especes-et-humanoides.md), le lion et le loup au
[LOT-1025](LOT-1025-creatures-lion-et-loup.md). D'ici là, la série de l'arène se joue avec des
fiches provisoires sur le corps des héros ; elles se remplacent quand ces lots livrent.

Le [LOT-1016](LOT-1016-camera-et-exploration.md) laisse à ce lot une dette : **les personnages ne
se bloquent pas**, ni entre membres du groupe ni contre un PNJ, et le meneur traverse un PNJ qui est
sur son chemin. Le combat en distance en a besoin (allonge, attaques d'opportunité) : ce lot la
retire.

## Risques et questions ouvertes

- **Le déterminisme.** Un combat se rejoue à l'identique (graine explicite) : la navigation du
  moteur doit être déterministe pour une même carte, ou la simulation de Core doit suffire aux
  tests. À trancher au premier sous-lot.
- **Les rencontres sur la carte** (LOT-139) : une rencontre paraît à son marqueur ; sans grille, le
  marqueur devient un volume. Le LOT-1018 doit le porter dans la description de carte.
- **L'équilibre.** Le déplacement libre favorise les tireurs et les lanceurs ; la simulation le
  dira, et le Brawler gradué (D-36) se recale si l'écart dépasse 20 points.

## Avancement — 9 octobre 2026

Ouvert le 8 octobre au soir par l'assistant, en autonomie (consignes de l'auteur : pas de
validation visuelle en cours de lot, rien d'acheté). **Le lot n'est pas livré** : le sous-lot 1
l'est — le modèle en mètres, puis, dans la nuit du 9, la grille retirée de `Core/Combat` et tout
ce qui la consommait passé sur l'espace (plus bas) — ; ce qui manque est écrit à la fin,
nommément.

### Ce qui est fait

- **L'espace de combat en mètres** (`Core/Combat/CombatSpace.h`, `.cpp`), sans grille : une
  créature est un **cylindre** posé au sol (`core::Volume`, rayon et hauteur tirés de son emprise
  du Manuel : 0,75 m et 1,50 m pour une M, 1,50 m et 3 m pour une G) ; l'**allonge** se mesure
  entre les bords, en trois dimensions (`core::inReach`, 1,50 m) ; une **zone** est une forme
  (`core::Effect`, `core::shapeHits` : sphère et cylindre exacts en trois dimensions, cône, ligne
  et cube dans le plan, une créature est dedans si son volume la croise) ; la **tenaille** est un
  angle au centre de la cible (`core::flanksByAngle`) ; l'**avantage de hauteur** demande une
  case d'écart (`core::hasHighGround`) ; l'**abri** garde la méthode du Guide (`core::coverFrom` :
  des lignes du meilleur point de l'attaquant vers quatre points du bord de la cible étagés sur sa
  hauteur ; une ou deux coupées, partiel ; trois, important ; quatre, total ; un corps interposé,
  partiel). Les portées du corpus restent en cases : `core::metersFromTiles`.
- **L'interface `core::CombatSpace`** — hauteur du sol, place libre, ligne de vue, chemin dans un
  budget, positions candidates — et ses **deux implémentations** : `core::SimulatedSpace` (un plan
  borné, des boîtes, des plateaux, du terrain difficile, de l'eau profonde ; Dijkstra sur un réseau
  de 0,5 m, huit voisins, sans coin coupé, déterministe ; `fromTileMap` lit une grille de
  collision de l'ancien format), et `FJadgCombatSpace` dans le moteur
  (`Source/JustAnotherRpgGame/Combat/`) : maillage de navigation pour le chemin et le budget,
  rayons pour la vue et le sol, balayage de capsule pour la place, échantillonnage à la demi-case
  pour les candidats. Les règles ne voient que l'interface.
- **Les types partagés** quittent `BattleGrid.h` pour `CombatTypes.h` (`CombatantId`,
  `Locomotion`, `Cover`, `coverBonus`, `AreaShape`, `footprintSide`) : consommables depuis le
  moteur, ce que `BattleGrid.h` ne permet pas (sa méthode `check`).
- **`IsoProjection` est retirée** (D-32, D-49) : la caméra est libre, le moteur projette ; plus
  rien ne la consommait. Les guides et spécifications qui la citaient sont repris.
- **28 tests de Core** (`test_combat_space.cpp`, `test_simulated_space.cpp`) et un test du moteur
  (`Jadg.Combat.Espace`).

### Les décisions de réalisation

| Décision | Ce qui est retenu | Pourquoi |
|---|---|---|
| Le déterminisme | **La simulation de Core suffit aux tests** ; le moteur n'a pas à être déterministe. Les tests de règles, la série de l'arène et la simulation à cent graines jouent sur `SimulatedSpace` ; le moteur ne joue que ce que le joueur voit | un maillage de navigation ne promet pas le même chemin d'une version à l'autre, et aucun test de règle n'a besoin de lui |
| La tenaille | un angle d'au moins **135°** au centre de la cible | c'est la valeur exacte où la règle de la ligne des centres du Guide bascule sur les huit cases adjacentes : deux cases adjacentes font 135° ou plus quand la ligne traverse deux côtés opposés, 90° au plus sinon (`LaTenailleParAngleRejoueLaLigneDesCentresDuGuide`) |
| La hauteur d'une créature | le côté de son emprise | le Manuel donne à une créature un espace **cubique** |
| L'avantage de hauteur | la base de l'attaquant au moins **1,50 m** au-dessus de celle de la cible, et rien d'autre | une case ; le Manuel ne donne ni bonus de dégâts ni de portée |
| Les zones en hauteur | sphère et cylindre exacts ; cône, ligne et cube dans le plan, à moins de leur taille en hauteur de leur origine | le jeu n'a qu'une terrasse ; le reste viendra avec une carte qui le demande |
| Le réseau de la simulation | un pas de 0,5 m ; la demi-case (0,75 m) pour un espace lu d'une carte en tuiles (9 octobre) | un détail de la simulation, pas une règle ; assez fin pour qu'une créature M passe une porte de 1,50 m, et les centres des cases d'une carte en sont des nœuds |

### Ce qui se vérifie — première part (9 octobre 2026)

Mesuré le 9 octobre 2026 sur le poste de référence (Unreal Engine 5.8.3).

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | **663 tests de Core, 100 % passés** (28 nouveaux, 9 retirés avec `IsoProjection`) |
| `powershell scripts/build.ps1 -Unreal -NoCapture` | code 0 : la cible d'éditeur se construit sans avertissement du code, mannequin, créateur et `JadgContentCheck` passent, **14 tests du moteur passés** (`Jadg.Combat.Espace` en plus des 13 du LOT-1015) ; les captures du socle ne sont pas rejouées, aucune scène n'a changé |
| `scripts/check.py`, lints, cahier de test | `scripts/check.py` 17 contrôles verts ; `lint_planning`, `lint_docs` (549 pages), cahier de test régénéré (675 cas) ; clang-format et ruff passés |

### La grille retirée — seconde part du sous-lot 1 (9 octobre 2026, nuit)

**`Core/Combat` n'a plus de grille.** `BattleGrid`, `Pathfinding` et `LineOfSight` sont supprimés,
avec leurs tests ; plus rien dans `Source/`, `scripts/` ni `Documentation/` ne cite `BattleGrid`
ni `IsoProjection` hors des fiches de `Planning/`. Ce qui est migré, module par module :

| Module | En mètres |
|---|---|
| `CombatState` | un `std::shared_ptr<const CombatSpace>` ; chaque combattant a sa base (`Combatant::position`, au sol de l'espace) ; `enlist`, `join`, `move` en `Meters3` ; `placementAt` (tenir dans l'espace sans recouvrir un autre volume), `routeTo` / `routeFor`, `destinations` / `destinationsFor` (les candidats de l'espace, chacun avec son chemin), `movementLeft` ; le droit de passage du Manuel devient les volumes `blocking` et `passable` de la requête. `movementBudget` y a déménagé |
| `Attack` | `gapBetween` / `gapFrom` (écart entre les bords, en 3D), `withinTiles`, `adjacentGap` (« à une case » = 1,50 m entre les bords), `profileReaches` ; `hasLineOfSight`, `coverBetween` sur l'espace ; l'avantage « hauteur » dans `attackCircumstances` ; `TargetCheck::NotPlaced` |
| `Damage` | `core::Structure` (points de vie, affinités) et `applyToStructure(Structure&)` ; l'espace retire la boîte détruite (`SimulatedSpace::removeBox`) |
| `AreaOfEffect` | `combatantsInArea(combat, Effect)` : le volume croise la forme et l'origine ne le tient pas sous abri total. Les gabarits « la moitié de la case » et `areaTilesFromMeters` disparaissent ; `ArenaSpell::areaRadiusMeters` porte le rayon du corpus tel quel |
| `Flanking` | `isFlankedFrom(…, Meters3, …)` : `flanksByAngle` (135°), chacun à une case de la cible et la voyant |
| `TacticalTerrain`, `PartyDeployment` | verdicts toujours en cases de la carte, calculés sur `SimulatedSpace::fromTileMap` : pose au centre de l'emprise (`core::tileCenter`), zone = les cases dont le centre est un candidat dans 9 m |
| `CombatPreview` | `MovePreview` : le chemin (`Route`) et les **mètres** qui resteraient |
| `MapEncounter` | inchangé : la carte, ses zones et le marqueur restent en cases (voir plus bas) |
| `EnemyAi` | mêmes poids, mêmes clés ; les places viennent de `CombatState::destinations` ; l'approche se cherche sur les candidats sans limite, et se paie en **centimètres** au taux `approachPerTile` par case de 150 cm ; aucun flottant dans le score. Les cinq profils de `behaviors.json` n'ont pas changé d'une valeur |
| `Arena` | `ArenaSession(Level, espace)` — par défaut `SimulatedSpace::fromLevel` ; les contestants restent placés sur des cases de la carte, posés à leur centre ; l'attaque d'opportunité tombe au dernier point tenable du chemin avant que l'écart entre les bords ne dépasse l'allonge ; journal « pas Nom 5.25,6.75 (3.00 m) » ; `MoveObserver` reçoit la `Route` |

Ce qui a changé dans l'espace :

- **`candidates` rend des `core::Destination`** (la place et son chemin) : l'IA lit le chemin de
  chaque place sans relancer une recherche. `FJadgCombatSpace` suit (le chemin que le maillage a
  déjà calculé pour vérifier la place).
- **`SimulatedSpace`** : un pas de réseau par espace — 0,5 m par défaut, la **demi-case**
  (0,75 m) pour un espace lu d'une carte en tuiles, dont les centres et coins de cases sont alors
  des nœuds (une créature M passe une porte d'une case) ; ce que la carte laisse libre se calcule
  une fois par rayon, au demi-pas ; `fromTileMap` fusionne les suites de cases pleines d'une ligne
  et fait de l'**eau profonde et de la falaise** de l'eau (le vol les franchit, la vue les
  traverse, comme la grille le faisait) ; **`fromLevel`** y ajoute le terrain difficile des zones
  (`difficultTerrain`, D13) ; `removeBox`. Deux corrections trouvées par les tests réécrits : le
  coût du terrain difficile se lit **au milieu du pas** (un pas qui s'arrêtait sur le bord d'une
  case difficile la payait double sans y être entré) ; la vue ne passe plus **par le coin commun
  de deux murs** qui se touchent.
- **Le paiement du déplacement.** `profile.movement` et `MOVEMENT_RESOURCE` restent en cases
  (l'unité des données : les tests de classes gardent leurs valeurs, 8 cases pour le Brawler au
  niveau 2, 12 pour le *vol*) ; le chemin se mesure en mètres ; un pas se paie en **cases
  entamées**, et ce qui reste de la dernière sert au pas suivant du même tour
  (`Combatant::movementSlack`) : deux pas de 0,75 m coûtent une case, pas deux. Décision de
  réalisation, posée en question ci-dessous.

Les tests : **663 tests de Core avant, 663 après, 100 % verts**. Retirés avec la mécanique de
grille : 23 (`test_battle_grid` 7, `test_pathfinding` 13, `test_line_of_sight` 3). Ce qui y
testait une règle du Manuel est porté, et seul ce qui ne testait que la grille a disparu — la
diagonale qui coûte une case, le coin de mur en diagonale, le départage des chemins de même coût,
`zonesAt`, l'objet posé sur une case, les points en demi-cases : `test_combat_state` 13 → 29
(budget de vitesse, détour d'un mur, terrain difficile, allié traversé et ennemi qui bloque, vol
au-dessus de l'eau et de la falaise, grande créature dans un couloir, placement refusé et sa
raison, terrain difficile des zones et créé en combat, déterminisme sur des cartes tirées au sort,
paiement en cases entamées), `test_attack` 9 → 12 (vue symétrique sur 20 cartes générées, ce qui
arrête la vue, les abris qui ne s'additionnent pas), `test_arena` 7 → 8 (se précipiter), et la
série de l'arène (3, ci-dessous). Les tests de classes (`test_class_*.cpp`,
`test_class_in_arena.cpp`) passent avec leurs valeurs ; seuls leurs appels `move` désignent la case
par son centre. Valeurs attendues changées, chacune pour la même règle : la zone de terrain
tactique n'est plus le carré de 13 × 13 cases mais les cases à moins de 9 m (quatre en diagonale,
pas cinq) ; deux paires de cases « un côté et l'angle opposé » prennent désormais en tenaille
(l'angle de 135° décidé le 8 octobre) ; un muret de 1 m devant une créature M donne un abri
**important** — l'abri se compte en lignes étagées sur la hauteur, et le Manuel parle de la moitié
du corps : le muret des tests fait 0,75 m ; dans `SansAttaquePossibleChaqueProfilAvance`, le
prudent et l'archer mettent quatre tours au lieu de trois à atteindre leur cible (les chemins du
réseau hors des axes sont jusqu'à 8 % plus longs que la ligne droite).

### La série de l'arène et la simulation à cent graines, rejouées en distance

Le banc de la recette `0.0.2` vivait dans les tests d'intégration de l'ancien dépôt et lisait
`hmi::` : il entre ici sans rien de Qt (`Source/Test/Support/ArenaSimulation.h`, les combattants
montés par Core seul ; `Source/Test/Unit/Core/Combat/test_serie_de_l_arene.cpp`). Les trois tests
de la série : la difficulté croissante, la garde par rencontre (en Release, trente graines et les
bandes de la `0.0.2`, qui passent ; en Debug **une** graine, la terminaison seule — un combat à
dix se joue en six à sept secondes en Debug), et la mesure complète, sautée sans
`JADG_SIMULATION_SEEDS`.

Mesure complète, Release, cent graines par case, sur `SimulatedSpace::fromLevel` du sable de
l'Arena of Fate, le 9 octobre 2026 :

| Composition | arene-bandits (niv. 1) | arene-gladiateurs (niv. 2) | arene-morts (niv. 3) | arene-veteran (niv. 4) | arene-capitaine (niv. 5) | arene-champion (niv. 5) | Série |
|---|---:|---:|---:|---:|---:|---:|---:|
| groupe | 70 % | 64 % | 83 % | 61 % | 80 % | 76 % | 72.3 % |
| sans brawler | 16 % | 1 % | 9 % | 1 % | 21 % | 19 % | 11.2 % |
| sans priest | 26 % | 17 % | 1 % | 0 % | 24 % | 11 % | 13.2 % |
| sans scoundrel | 34 % | 4 % | 27 % | 25 % | 29 % | 55 % | 29.0 % |
| sans mage | 32 % | 16 % | 11 % | 0 % | 0 % | 0 % | 9.8 % |

**Écart entre trios : 19,2 points** (critère : moins de 20, D-36) ; il était de 15,8 à la recette
`0.0.2`. Le groupe entier gagne 72,3 % de la série (71,2 % en `0.0.2`). Le meilleur trio reste
celui sans Scoundrel (29,0 %, 24,7 % en `0.0.2`), le pire celui sans Mage (9,8 %, 8,8 %) : le
critère tient, de peu, et la marge a fondu de 4,2 à 0,8 point. La mesure a pris 26 minutes. Le
Brawler gradué (D-36) n'est pas recalé : la fiche ne le demande qu'au-delà de 20 points.

### Ce qui se vérifie (9 octobre 2026, nuit)

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | **663 tests de Core, 100 % passés** |
| `powershell scripts/build.ps1 -Unreal -NoCapture` | code 0 : cible d'éditeur, `JadgContentCheck`, **14 tests du moteur passés** (`Jadg.Combat.Espace` compris, sur les `Destination`) |
| `scripts/check.py`, lints, cahier | 17 contrôles verts ; `lint_planning`, `lint_docs` (549 pages) ; cahier de test régénéré |

### Ce qui reste au lot

- **Les zones de combat et le marqueur de rencontre en volumes** : la carte (tuiles, entités,
  `CombatZone`, placements de formation, points d'entrée) reste en cases ; le combat les lit au
  centre des cases (`core::tileCenter`). La description de carte du `LOT-1018` doit porter les
  volumes ; d'ici là, rien n'est inventé.
- **Les sous-lots 2 et 3** : l'IA sur les candidats **EQS** du moteur (`FJadgCombatSpace` échantillonne
  à la demi-case et ne sait pas répondre à un budget **sans limite**, dont l'approche de l'IA a
  besoin), le combat qui se joue dans le moteur, l'aperçu dessiné, le parcours du combat, les
  captures.
- **Le moteur n'exclut pas un combattant du maillage** le temps d'une requête (inchangé).
- **La dette du LOT-1016** (les personnages ne se bloquent pas) n'est pas retirée.
- **Les spécifications** : les exigences qui écrivent encore la grille (`EX-CBT-001`, `EX-CBT-020`,
  `EX-CBT-021`, `EX-CBT-061`, la justification d'`EX-EXP-001`, la décision de cadrage n° 2 de
  `vision.md`) et les maquettes qui la dessinent (`combat-grille-portee.svg`,
  `combat-tenaille-zone.svg`, `combat-tour-et-agonie.svg`, `combat-ia-evaluation.svg`…) ne sont
  pas réécrites : la prose autour l'est, et `Specification/combat.md` les nomme ; le texte d'une
  exigence est à l'auteur. `EX-EDIT-054` et `EX-LVL-022` ne changent que le symbole qu'elles
  citent (`CombatState::placementAt`, `zoneCells`).

### Questions pour l'auteur

1. **Le déplacement se paie-t-il en cases entamées ?** Retenu : la vitesse reste un nombre de
   cases (la donnée), un pas en entame autant qu'il en faut, et le reste de la dernière sert au
   pas suivant du même tour. L'autre lecture — dépenser les mètres exacts — ferait passer
   `MOVEMENT_RESOURCE` en centimètres et changerait les valeurs des tests de classes.
2. **L'avantage de hauteur vaut-il au contact comme à distance ?** Retenu : oui, la décision du
   8 octobre ne distingue pas.
3. **Une herse, une meurtrière** : l'abri se compte en lignes coupées par la géométrie ; une boîte
   pleine de toute la hauteur donne un abri total, jamais l'abri important que le Manuel donne à
   la herse. Faut-il un obstacle « ajouré » dans l'espace (une boîte qui ne coupe qu'une ligne sur
   deux, par exemple), ou attendre les pièces du moteur ?
4. **L'origine d'un cône, d'une ligne, d'un cube** : une créature est prise dès qu'un bord croise
   la forme ; un cône parti du bord de son lanceur peut donc le prendre, alors que le Manuel dit
   que l'origine n'est pas dans la zone. Exclure le lanceur de ses propres cônes, lignes et cubes ?
   (Seule la sphère sert en jeu aujourd'hui.)
5. **Les exigences en grille** (`EX-CBT-001`, `EX-CBT-020`, `EX-CBT-021`, `EX-CBT-061`) : les
   réécrire en distance — « les cases atteignables sont montrées » devient-il « les places
   atteignables », ou seulement le chemin et la portée restante comme la fiche le dit ?
6. **L'équilibre** : l'écart entre trios passe de 15,8 à 19,2 points en distance, sous le
   critère de 20 mais à 0,8 point de lui. Faut-il le resserrer avant la recette (un réglage
   du Scoundrel, dont le trio sans lui reste le meilleur), ou attendre les fiches définitives
   des adversaires (LOT-1024, LOT-1025) ?
