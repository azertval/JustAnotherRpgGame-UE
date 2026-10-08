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
validation visuelle en cours de lot, rien d'acheté). **Le lot n'est pas livré** : la première
part du sous-lot 1 l'est, et ce qui manque est écrit plus bas, nommément.

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
| Le réseau de la simulation | un pas de 0,5 m | un détail de la simulation, pas une règle ; assez fin pour qu'une créature M passe une porte de 1,50 m |

### Ce qui se vérifie

Mesuré le 9 octobre 2026 sur le poste de référence (Unreal Engine 5.8.3).

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | **663 tests de Core, 100 % passés** (28 nouveaux, 9 retirés avec `IsoProjection`) |
| `powershell scripts/build.ps1 -Unreal -NoCapture` | code 0 : la cible d'éditeur se construit sans avertissement du code, mannequin, créateur et `JadgContentCheck` passent, **14 tests du moteur passés** (`Jadg.Combat.Espace` en plus des 13 du LOT-1015) ; les captures du socle ne sont pas rejouées, aucune scène n'a changé |
| `scripts/check.py`, lints, cahier de test | `scripts/check.py` 17 contrôles verts ; `lint_planning`, `lint_docs` (549 pages), cahier de test régénéré (675 cas) ; clang-format et ruff passés |

### Ce qui s'écarte de la fiche, et ce qui manque

- **La grille est toujours là.** `CombatState`, `Attack`, `AreaOfEffect`, `LineOfSight`,
  `Flanking`, `Pathfinding`, `TacticalTerrain`, `PartyDeployment`, `MapEncounter`, `EnemyAi` et
  `Arena` jouent encore sur `BattleGrid` et `GridPosition` ; leurs tests aussi (quinze fichiers,
  environ 300 cas). Le modèle en mètres existe à côté, testé, et rien ne le consomme encore. La
  fiche demandait qu'ils soient **remplacés** : c'est la seconde part du sous-lot 1, qui n'est pas
  faite. Son ordre, mesuré sur ce que chaque module touche : `CombatState` (positions en
  `Meters3`, `CombatSpace` à la place de `BattleGrid`, `move` et `reachable` par `route` et
  `candidates`), puis `Attack` (`inReach`, `coverFrom`), `AreaOfEffect` (`shapeHits`), `Flanking`
  (`flanksByAngle` + allonge + vue), `CombatPreview`, `MapEncounter` et `PartyDeployment` (les
  volumes de combat et le déploiement), `TacticalTerrain` (le verdict de l'éditeur sur un
  `SimulatedSpace::fromTileMap`), `EnemyAi` (les candidats de l'espace), `Arena` ; `BattleGrid`,
  `Pathfinding`, `LineOfSight` et leurs tests partent en dernier.
- **Les sous-lots 2 et 3 ne sont pas ouverts** : l'IA sur des candidats (elle dépend de
  `CombatState` en mètres), le combat qui se joue dans le moteur (l'arène vide du LOT-1016 le reste),
  les zones de combat en volumes, le déploiement, l'aperçu, le parcours du combat, les captures.
- **Le moteur n'exclut pas un combattant du maillage** le temps d'une requête : les volumes
  `blocking` d'un chemin ne comptent qu'à l'arrivée, pas sur le trajet. Un modificateur de
  navigation par combattant est la voie, au sous-lot 3.
- **La dette du LOT-1016** (les personnages ne se bloquent pas) n'est pas retirée.

### Ce qui reste au lot

Tout ce que le paragraphe précédent nomme, dans l'ordre qu'il donne. La première part du sous-lot
1 — le modèle, l'interface, ses deux implémentations, leurs tests — est ce sur quoi le reste se
pose, et elle est livrée verte.
