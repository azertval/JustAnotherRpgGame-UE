+++
id = "LOT-1022"
titre = "L'Arena of Fate et Martpart portés"
version = "0.0.3"
filiere = "cartes"
statut = "a-faire"
taille = "M"
resume = "Les trois niveaux de l'Arena of Fate, dans une seule carte, et Martpart à l'état de sa v0 se jouent sur le nouveau moteur : la démo s'enchaîne de bout en bout."
prerequis = ["LOT-1019"]
livrables = [
  "L'Arena of Fate en une description de carte (format 5) à trois étages praticables — le sable, les vestiaires et la prison, les catacombes — de même emprise ovale, les escaliers aux mêmes positions (D-46, D-51) ; ses 105 maillages au maître, textures partagées ; la série de l'arène rejouée.",
  "Martpart en description de carte, ses 34 maillages et les deux arbres, au niveau de sa v0 ; les portails vers Arenarea appariés.",
  "Les captures à midi et à 22 h des trois étages et de Martpart, versées à la fiche et aux fiches LOT-106, LOT-107, LOT-157 de la `0.0.4`.",
  "Les mesures de cadence et d'ouverture des deux cartes.",
]
criteres = [
  "La démo s'enchaîne par ses portails : Martpart, Arenarea, l'Arena of Fate et son donjon, et retour ; `--check` passe sur les trois cartes.",
  "La série de l'arène se joue sur le sable ; le combat de groupe de la recette `0.0.2` s'y rejoue.",
  "Les deux cartes tiennent 60 images par seconde à 1080p sur le poste de référence, de jour comme de nuit.",
  "L'auteur confirme sur captures que l'Arena of Fate n'a rien perdu de ce qu'il avait validé le 4 octobre 2026 (jugement de l'auteur).",
]
+++

## Pourquoi

La démo compte trois lieux ; la version doit se jouer sur les trois (règle 2 de la trajectoire).
L'Arena of Fate est le lieu le plus abouti du dépôt, en maillages au maître : son portage est le
test de D-51 (trois étages dans une carte) et de D-53 (2,04 millions de triangles sans réduction).
Martpart n'est qu'une v0 : il se porte tel quel, sa production reste aux lots de la `0.0.4`.

## Périmètre

Dedans : les deux cartes, leurs maillages, les portails, les captures, les mesures.

Dehors, nommément :

- la qualité finale de Martpart (LOT-110, LOT-111) et la validation artistique de l'Arena of Fate
  (LOT-106), qui restent à la `0.0.4` ;
- le donjon cultiste des catacombes (LOT-157).

## À supprimer

| Quoi | Où | Pourquoi maintenant |
|---|---|---|
| Les trois descriptions v4 de l'Arena of Fate et celle de Martpart | `Levels/central-empire/capital/arenarea/arena-of-fate/`, `Levels/.../martpart.json` | remplacées par les descriptions v5 sous les mêmes identifiants |

Les kits `arena-of-fate@6` et `martpart@4` se republient avec les mêmes maillages ; seules les
sorties du moteur changent.

## Conception

- **Une seule carte pour trois étages** : chaque étage est un niveau de chargement de la même
  description ; les escaliers relient par le maillage de navigation, sans portail.
- **Les textures partagées** (D-46) le restent : le moteur déduplique à l'import.
- **La série de l'arène** se rejoue avec les distances du LOT-1017 ; les zones de déploiement
  deviennent des volumes posés sur le sable.

## Risques et questions ouvertes

- **La coque à 878 000 triangles** sous Nanite avec trois étages chargés : la cadence se mesure
  étage par étage ; si un étage ne tient pas, il se décharge quand on n'y est pas.

## Avancement — 9 octobre 2026

Fait par l'assistant, en autonomie, sur la branche `lot/1022-portage-arena-of-fate-et-martpart`.
Le lot est **ouvert** ; sa fiche reste `a-faire` tant que le LOT-1019, son prérequis, n'est pas
livré (`lint_planning.py` refuse un lot en cours sur un prérequis ouvert) ; sa clôture est une
décision de l'auteur. Rien de ce qui suit n'a été vu dans une fenêtre : les images sont **à juger
par l'auteur à la recette**. La carte est décrite au
[guide des données](../../../../../Documentation/Guide/guide-donnees.md#larena-of-fate--une-carte-à-trois-étages),
ses étages et ses niveaux de chargement au
[guide des cartes](../../../../../Documentation/Guide/guide-cartes-moteur.md#les-sous-sols-et-les-niveaux-de-chargement-lot-1022) ;
l'exigence, `EX-LVL-032`, `EX-LVL-034` et `EX-LVL-036` de
[`niveaux.md`](../../../../../Documentation/Specification/niveaux.md).

### Ce qui est fait

- **L'Arena of Fate en une carte à trois étages** (`Levels/central-empire/capital/arenarea/arena-of-fate.json`,
  D-51) : le **sable** (le rez, à 0 m), les **vestiaires et la prison** (`vestiaires-et-prison`,
  niveau −1) et les **catacombes** (niveau −2), fusionnés des trois cartes migrées du LOT-1018
  **tels quels** — la grille du sable, ses `forced`, les 26 couches des trois niveaux (1 728
  pièces, les 105 du kit), leurs entités et leurs notes —, sous la même emprise de 34 × 24 cases ;
  les escaliers sont aux cases de la v4. Chaque couche et chaque entité d'un sous-sol nomme son
  étage (`storey`) ; une note aussi.
- **Les sous-sols dans le format v5** : un étage peut être **sous** le rez (`storeys` : le rez en
  tête à 0 m, puis chaque étage ou sous-sol à sa hauteur, jamais deux à la même) — Core
  (`LevelLoader`, deux tests GoogleTest), `jadg_map.py`, le schéma, `EX-LVL-032` ; l'étage d'un
  point est le plus haut dont le sol est sous lui, dans l'ordre des hauteurs
  (`AJadgMapFrame::StoreyAt`). Une couche de pièces nomme son étage et se pose au-dessus de son
  sol (`build_level.py`).
- **La hauteur d'un sous-sol est mesurée**, pas devinée : ce qu'il porte doit tenir sous le sol du
  dessus (relevé dans les `.glb` du kit, sous les cases de sol de l'étage du dessus). Sous le sable,
  le plus haut est l'enceinte des vestiaires (5,40 m) : le niveau −1 est à **−5,5 m**. Sous les
  vestiaires, le cadre de chapelle (5,88 m) et le puits des catacombes, qui descend de 3,12 m
  au-dessus de l'escalier des catacombes haut de 3,45 m (6,57 m) : le niveau −2 est à **−12,1 m**.
- **Un niveau de chargement par étage** (`"storeyLevels": true`, `EX-LVL-034`) : `build_level.py`
  construit le décor de chaque étage (couches, objets, lumières) dans son niveau
  (`/Game/Maps/Levels/…/arena-of-fate-etage-<nom>`), l'ajoute au niveau de la carte, toujours
  chargé (`LevelStreamingAlwaysLoaded`) ; le ciel, la navigation, les personnages, les repères, le
  cadre et les cadrages restent dans le niveau de la carte. `AJadgMapFrame::StoreyLevels` les
  nomme, `ShowStorey` en cache un. Construite de rien, imports faits : 3,6 à 3,9 s.
- **Les captures et la cadence par étage** : un cadrage qui regarde un étage (`storey`) cache, le
  temps de sa capture, les étages au-dessus (`AJadgCaptureDirector`) ; `-JadgEtages` (et
  `build.ps1 -Unreal -Map <carte> -Capture -Etages <rangs>`) ne montre que ces étages-là et mesure
  leur cadence. Six cadrages : l'ensemble et le cadrage du joueur de chaque étage.
- **Les escaliers relient par portail, pas par le maillage** (voir les écarts) : les portails de la
  v4 entre deux niveaux — la porte du triomphe (`e2`, `e20`), la porte des morts (`e3`, `e27`), la
  descente des catacombes (`e25`, `e33`) — visent désormais **la carte elle-même** ; le groupe se
  pose au point d'arrivée, à son étage, sans que la carte se rouvre (`AJadgParty::Travel`). Un
  portail dans le plein (une porte dans un mur, le haut d'un escalier) **se franchit au contact** :
  le meneur envoyé vers lui y entre quand il s'arrête à moins de deux cases de son centre, à son
  étage (`AJadgParty::OrderWalk`) — le portail du parvis est sur la deuxième marche d'un escalier
  que le maillage ne gravit pas : le meneur s'arrête au pied, à 1,8 case — ce que le contrôle des cartes admettait déjà (« une case
  voisine atteinte suffit ») et que le moteur ne faisait pas. Le contrôle du maillage de navigation
  (`build_level.py -JadgCheck`, `EX-LVL-036`) suit les portails d'une carte : chaque point
  d'arrivée de chaque étage est atteint depuis l'entrée du sable.
- **La série de l'arène se joue sur le sable** : l'Arena of Fate est la **carte d'arène du jeu**
  (`ArenaMap`, `Config/DefaultGame.ini`) ; elle s'explore aussi, et n'est l'arène que tant qu'une
  rencontre y est engagée (`AJadgParty::InArena`) ; `-JadgArene=<paquet>` en donne une autre pour
  un passage (l'arène d'essai du tour des écrans, qui garde sa référence). La zone de combat du
  sable et les six marqueurs de la série sont des **volumes** (les mêmes cases : la simulation de
  Core ne change pas), et les **quatre points d'entrée du groupe** sont ceux du banc de la série
  (`ArenaSimulation.h`, devant le maître, vers l'est). `-ParcoursCombat` y joue
  `arene-bandits`, graine 2, depuis le parvis d'essai.
- **Martpart au niveau de sa v0**, et ses deux arbres : `mp-cypress` et `mp-tree` sont dans le
  kit, sous un autre nom — le manifeste de Martpart les donne (`mesh` :
  `../../arenarea/Scene/ar-meshy-cypres.glb`, `ar-meshy-arbre-ombrage.glb`), mais
  `jadg_map.resolve_piece` ne cherchait que le fichier du nom de la pièce. Il lit désormais, en
  dernier recours, le maillage que le manifeste du kit donne à la pièce : les **113** arbres se
  posent, et les **14** pièces `reused-af-*` d'Arenarea (le mobilier repris de l'Arena of Fate)
  aussi. Ses portails vers Arenarea sont appariés (`e4` ↔ `from-martpart`, `e2` ↔ `from-arenarea`) ;
  un cadrage du joueur sur la mère à son étal s'ajoute à celui de relecture.
- **La démo s'enchaîne dans le jeu lancé** : `AJadgDemoWalkthrough` (`build.ps1 -Unreal
  -ParcoursDemo`) marche de Martpart — de Market Gate à la place des étals, puis à Stravian
  Avenue — à Arenarea, à l'Arena of Fate — le vestibule des vestiaires, le sable par la porte du
  triomphe, retour aux vestiaires, les catacombes par leur descente, la prison —, à Arenarea par
  l'escalier du parvis et retour à Martpart par Herofate Avenue : neuf étapes, chacune un ordre de
  marche donné au groupe vers un portail, chaque arrivée capturée, l'**ouverture** de chaque carte
  mesurée (de la dernière trame de la carte quittée à la première de la suivante). Il attend le
  maillage de navigation, et reprend à une étape (`-JadgDemoEtape`). Le HUD ne lui ouvre pas le
  menu du titre, qui mettait le jeu en pause (`LaunchedByAutomaton`).
- **Le contrôle des parcours** : le moteur lancé en jeu depuis l'éditeur sortait en 0 sur un
  parcours arrêté (relevé sur le parcours du combat) ; `build.ps1` lit désormais le journal
  (`completed`) des trois parcours.
- **Le parcours du combat amène le point visé** sur une destination ou une cible que le décor
  cache (une bannière, une tribune, une statue du sable) ou que la vue a quittée, trois fois au
  plus, de plus haut et en tournant d'un tiers de tour, avant de cliquer — ce qu'un joueur fait ;
  une cible se désigne aussi par l'arme qu'elle porte, ou par un bord de sa figurine.
- **Suppressions** (D-32) : `arena-of-fate/undercroft.json` et `arena-of-fate/catacombs.json`
  (remplacées sous l'identifiant de l'Arena of Fate ; le portail d'Arenarea, l'atlas
  `world-maps.json` et `build_world_atlas.py` le visent), leurs noms dans les catalogues ;
  `check_arena_fate.py` et `check_arena_fate_levels.py` (les contrôles des trois cartes : la même
  emprise et les escaliers superposés sont désormais la carte elle-même) ; `arena_fate_arena_v2.py`
  et ses deux données (`arena_fate_anchors.json`, `arena_fate_v2_baseline.json`), les gestes de
  l'ancien éditeur pour le sable. Du poste : les deux niveaux des sous-sols et leurs empreintes.
- **Tests** : `FormatV5Test.UneCarteASousSolsSeLit`, `FormatV5Test.LArenaOfFateEstUneCarteATroisEtages`
  (la carte livrée : trois étages, l'arrivée au vestibule à l'étage 1, le portail de la porte du
  triomphe qui pose au sable sur la même carte) ; `Jadg.Exploration.QueteDesPommes` mène désormais
  à l'Arena of Fate, au vestibule, à l'étage 1 ; deux cas de `test_jadg_map.py` (la pièce partagée
  par son manifeste, la carte à sous-sols).

### Les décisions de réalisation

| Décision | Ce qui est retenu | Pourquoi |
|---|---|---|
| Le rez de l'Arena of Fate | le sable, à 0 m ; les sous-sols en dessous | la grille de Core est celle du rez : la série de l'arène (sa simulation, `SimulatedSpace::fromLevel`) se joue sur la grille du sable ; l'atlas dit « niveau −1 », « niveau −2 » |
| Un sous-sol dans le format | un étage à hauteur négative, après le rez ; jamais deux à la même hauteur | le plus petit changement à la règle « le rez à 0, puis des hauteurs croissantes », qui faisait du rez l'étage le plus bas |
| La hauteur d'un sous-sol | celle, mesurée dans les `.glb`, de ce qu'il porte sous le sol du dessus, arrondie au dixième au-dessus : 5,5 m et 6,6 m | 3,45 m (la hauteur des escaliers) faisait percer le sable par les voûtes (4,30 m) et l'enceinte des vestiaires (5,40 m), et le sol des vestiaires par les cadres de chapelle (5,88 m) et les bannières du culte (5,61 m) |
| Les escaliers | les pièces de la v4, aux mêmes cases, à leur taille ; les étages reliés par les portails de la v4, qui visent la même carte | les escaliers du kit ne relient pas deux étages superposés (mesuré, ci-dessous) |
| Un portail dans le plein | franchi au contact (deux cases), à son étage, par le meneur envoyé vers lui | ce que le contrôle des cartes admet ; sans cela, un portail hors du maillage ne se franchissait pas dans le jeu |
| Les niveaux de chargement | `LevelStreamingAlwaysLoaded`, un par étage, le décor seul ; la carte le déclare (`storeyLevels`) | toujours chargés avec la carte, ils arrivent avant le groupe ; la carte d'essai à deux étages et son aller-retour ne changent pas |
| Tout chargé, ou l'étage absent déchargé | **tout chargé** | mesuré : 102 à 104 images/s les trois étages chargés, 108 le sable seul (ci-dessous) ; décharger les sous-sols ne gagne que 0,3 ms de processeur graphique, et rien sous le critère |
| La première étape de la démo | Market Gate, la place des étals, puis Stravian Avenue | un ordre direct de Market Gate à Stravian Avenue s'arrête toujours en (60 ; 9,4) (ci-dessous) ; c'est aussi le chemin de la quête |
| La carte d'arène | l'Arena of Fate, arène tant qu'une rencontre y est engagée ; `-JadgArene` pour une autre | la série se joue sur le sable, et la carte s'explore aussi ; le tour des écrans garde l'arène d'essai et sa référence |
| Les points d'entrée du groupe | (9 à 12, 10), ceux du banc de la série | aucune valeur devinée : la simulation de Core déploie le groupe là |
| La pièce partagée d'un kit | le maillage que le manifeste lui donne, en dernier recours | les cyprès et les arbres de Martpart sont ceux d'Arenarea ; Arenarea, telle quelle, n'en change pas autrement |

### Ce qui se mesure

Mesuré le 9 octobre 2026 sur le poste de référence (Unreal Engine 5.8.3, RTX 4060 Ti, i7-8700),
jeu lancé hors écran en 1920 × 1080 par les binaires de l'éditeur, caméra en rotation dix
secondes par heure autour du premier cadrage gardé.

**La cadence, étage par étage** (lancé comme `build.ps1 -Map … -Capture -Etages <rang>`,
`mesure-arena-of-fate-*.json`) ; au passage de la recette (`-Capture`, les trois étages), **103,5
images/s à midi et 103,7 à 22 h** (9,66 ms, GPU 8,92 ms) :

| Étages montrés | Maillages, triangles Nanite | 12 h | 22 h |
|---|---|---|---|
| les trois (le choix retenu) | 111, 3,42 millions | **101,7 images/s** (9,83 ms, GPU 8,97 ms) | **102,1** (9,80 ms, GPU 8,94 ms) |
| le sable seul | 48, 2,85 millions | 107,5 (9,30 ms, GPU 8,66 ms) | 108,2 (9,24 ms) |
| les vestiaires seuls | 39, 1,67 million | 123,6 (8,09 ms, GPU 7,40 ms) | 123,0 (8,13 ms) |
| les catacombes seules | 39, 1,68 million | 126,0 (7,94 ms, GPU 7,27 ms) | 122,8 (8,15 ms) |

La coque (`af-arena-shell`, 865 214 triangles en Nanite) est le plus gros maillage. Les trois
étages chargés, la mémoire graphique du processus est de 3 665 Mio, les textures des maillages de
92,6 Mio chargées (118 textures), 237 Mio entières. Le LOT-1019 mesurait 107,4 et 107,1 images/s
sur le sable seul, la carte d'un seul niveau : la même cadence. La `0.0.2.5` n'a jamais mesuré la
cadence de l'Arena of Fate ([bilan](../../v0.0.2.5-passage-3d/bilan.md), « ce qui manque ») : il
n'y a pas d'ancienne mesure à comparer.

**Pourquoi les escaliers ne relient pas les étages** (relevé sur le maillage de navigation du
niveau construit et dans les `.glb`) : l'enceinte des vestiaires (`af-undercroft-shell`) a un
**sol plein** sur tout l'ovale, puits des catacombes compris — l'escalier des catacombes arrive
sous lui ; l'escalier de la porte du triomphe (`af-stair-w`) monte vers l'ouest, sous l'enceinte de
l'arène, où le sable n'a pas de sol ; celui de la porte des morts (`af-stair-e`), vers l'est, de
même ; retournés, ils se heurtent au couloir des vestiaires par leur haut. Dans la v4, ces
escaliers étaient un décor au pied d'un portail. Mis à la hauteur des étages (5,5 m pour 3,9 m de
course), ils dépassent aussi la pente que le maillage admet (44°).

**Martpart** (`-Map central-empire/capital/martpart -Capture`, `mesure-martpart.json`) : **111,0
images/s à midi, 111,8 à 22 h** (9,01 ms, GPU 8,28 ms ; 1,93 million de triangles Nanite) ;
10 217 pièces posées, aucune sans maillage ; construite en 42 s la première fois (les arbres
importés), 2 s ensuite.

**L'ouverture** : d'une carte à l'autre par un portail, dans le jeu lancé (le parcours de la démo,
`parcours-demo.json`), de la dernière trame de la carte quittée à la première de la suivante :
Arenarea **1,01 s** (de Martpart) et **0,91 s** (de l'Arena of Fate), l'Arena of Fate **0,92 s**,
Martpart **0,52 s**. Depuis le lancement du processus (les binaires de l'éditeur, `-game`),
jusqu'à la première trame : 16,8 s pour l'Arena of Fate, 16,2 s pour Martpart, dont le démarrage
de l'éditeur, comme au LOT-1012.

**La démo** (`-ParcoursDemo`) : neuf étapes en 215 s depuis le lancement ; Market Gate à la place
des étals 38 s, à Stravian Avenue 24 s, l'escalier d'Arenarea 43 s, les quatre portails de l'Arena
of Fate 1 à 13 s chacun, l'escalier du parvis 21 s, Herofate Avenue 42 s. Un ordre direct de
Market Gate à Stravian Avenue s'arrête, à chaque essai et après six ordres, en (60,0 ; 9,4) — le
contrôle du maillage de l'éditeur (`-JadgCheck`) dit pourtant `from-arenarea` atteint depuis
l'entrée ; ni l'attente du maillage du jeu ni 16 384 nœuds de recherche n'y changent rien. Le
détour par la place des étals passe.

**Le combat sur le sable** (`-ParcoursCombat -Seed 2`, `parcours-combat-sable.json`) :
`arene-bandits` monté à la deuxième ou troisième tentative (le maillage du sable se construit après
l'ouverture), **victoire au round 7**, 19 tours de héros joués au clavier et à la souris, retour
au parvis, le meneur à la même case, `encounter/arene-bandits/won` posé. Sur trois passages de la
graine 2, deux sont allés au bout sans geste de caméra ; dans le troisième, au round 6, une
destination puis une cible étaient cachées : c'est ce qui a donné les gestes de caméra du parcours
(ci-dessus).

### Ce qui se vérifie (9 octobre 2026, RTX 4060 Ti, Unreal Engine 5.8.3)

Rejoué une passe à la fois, un processus du moteur à la fois, sur le dernier état de la branche.

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | **704 tests de Core, 100 % passés** (2 nouveaux : `UneCarteASousSolsSeLit`, `LArenaOfFateEstUneCarteATroisEtages`) ; la série de l'arène sur la grille du sable, inchangée |
| `powershell scripts/build.ps1 -Unreal` | code 0 : cible d'éditeur, `JadgContentCheck`, **26 tests du moteur passés** (`Jadg.Exploration.QueteDesPommes` mène au vestibule, à l'étage 1), `jadg_map.py --check` (**10 cartes**, 0 erreur, les 3 avertissements du LOT-1018), l'aller-retour réussi, le socle et ses captures à leur référence (pire bloc 1,59 et 2,15 sur 255) |
| `powershell scripts/build.ps1 -Unreal -Parcours` | code 0 : la quête rendue 53 s après le lancement |
| `powershell scripts/build.ps1 -Unreal -ParcoursCombat -Seed 2` | code 0 : sur le sable de l'Arena of Fate, victoire au round 7, 19 tours de héros, retour au parvis à la même case, `encounter/arene-bandits/won` posé |
| `powershell scripts/build.ps1 -Unreal -Ecrans` | code 0 : les **24 captures à leur référence** (l'arène d'essai par `-JadgArene`) |
| `powershell scripts/build.ps1 -Unreal -ParcoursDemo` | code 0 : les trois cartes construites et leur maillage contrôlé, neuf étapes de Martpart à Martpart, journal `completed` |
| `powershell scripts/build.ps1 -Unreal -Map central-empire/capital/arenarea/arena-of-fate -Capture` | code 0 : les 12 captures, 103,5 et 103,7 images/s |
| `powershell scripts/build.ps1 -Unreal -Map central-empire/capital/martpart -Capture` | code 0 : les 4 captures, 111,0 et 111,8 images/s |
| `scripts/check.py --sans-hooks` | **18 contrôles verts** ; pytest 282 passés (2 nouveaux) ; `lint_planning`, `lint_docs`, cahier de test régénéré (699 cas) ; `jadg_map --check`, `quest_mode --check` |
| `scripts/checks/check_orphans.py` (avec les kits et `Content/`) | aucun asset ni script orphelin, aucune sortie du moteur sans script (les niveaux des étages sous `/Game/Maps/Levels`) |
| `ruff check scripts`, clang-format sur Core et ses tests | passés |

### Les captures — à juger par l'auteur à la recette

Dans [`annexes/LOT-1022/captures/`](../annexes/LOT-1022/captures/), à midi et à 22 h :

| Lieu | Ensemble | Au cadrage du joueur |
|---|---|---|
| le sable | [midi](../annexes/LOT-1022/captures/arena-of-fate-ensemble-1200.png), [22 h](../annexes/LOT-1022/captures/arena-of-fate-ensemble-2200.png) | [midi](../annexes/LOT-1022/captures/arena-of-fate-sable-1200.png), [22 h](../annexes/LOT-1022/captures/arena-of-fate-sable-2200.png) |
| les vestiaires et la prison (le sable caché) | [midi](../annexes/LOT-1022/captures/arena-of-fate-vestiaires-ensemble-1200.png), [22 h](../annexes/LOT-1022/captures/arena-of-fate-vestiaires-ensemble-2200.png) | [midi](../annexes/LOT-1022/captures/arena-of-fate-vestiaires-1200.png), [22 h](../annexes/LOT-1022/captures/arena-of-fate-vestiaires-2200.png) |
| les catacombes (les étages du dessus cachés) | [midi](../annexes/LOT-1022/captures/arena-of-fate-catacombes-ensemble-1200.png), [22 h](../annexes/LOT-1022/captures/arena-of-fate-catacombes-ensemble-2200.png) | [midi](../annexes/LOT-1022/captures/arena-of-fate-catacombes-1200.png), [22 h](../annexes/LOT-1022/captures/arena-of-fate-catacombes-2200.png) |
| Martpart | [midi](../annexes/LOT-1022/captures/martpart-ensemble-1200.png), [22 h](../annexes/LOT-1022/captures/martpart-ensemble-2200.png) | [midi](../annexes/LOT-1022/captures/martpart-etals-1200.png), [22 h](../annexes/LOT-1022/captures/martpart-etals-2200.png) |

Le combat sur le sable : [le déploiement](../annexes/LOT-1022/captures/sable-combat-02.png),
[l'issue](../annexes/LOT-1022/captures/sable-combat-04.png). La démo, dans le jeu, HUD compris :
[le vestibule](../annexes/LOT-1022/captures/demo-03.png),
[le sable](../annexes/LOT-1022/captures/demo-04.png),
[les catacombes](../annexes/LOT-1022/captures/demo-06.png),
[le retour à Martpart](../annexes/LOT-1022/captures/demo-09.png). Elles sont citées des fiches
LOT-106, LOT-107 et LOT-157 de la `0.0.4`. Le sable au cadrage du joueur est pris du milieu de
l'arène (55°) : à 40°, la caméra de capture, sans collision, tombait dans les tribunes du sud.

### Les critères

| Critère | État |
|---|---|
| La démo s'enchaîne par ses portails : Martpart, Arenarea, l'Arena of Fate et son donjon, et retour ; `--check` passe sur les trois cartes | **tenu** : `-ParcoursDemo` va de Martpart à Arenarea, à l'Arena of Fate — vestibule, sable, catacombes —, et revient à Martpart par Arenarea, code 0, journal `completed` ; `jadg_map.py --check` passe sur les trois cartes (0 erreur ; les trois avertissements du LOT-1018, des points d'arrivée d'Arenarea et de Martpart qu'aucun portail ne cite), `JadgContentCheck` vert, le maillage de navigation contrôlé sur les trois (`-JadgCheck`) |
| La série de l'arène se joue sur le sable ; le combat de groupe de la recette `0.0.2` s'y rejoue | **partiel** : `arene-bandits` se joue sur le sable de l'Arena of Fate, au clavier et à la souris, graine 2 : **victoire au round 7**, 19 tours de héros, retour au parvis, `encounter/arene-bandits/won` posé ; les cinq autres rencontres de la série ne s'enchaînent pas encore dans le moteur (le `levelUp` et le `rest` du dialogue, LOT-1017) ; dans Core, la série se mesure sur la grille du sable, inchangée |
| Les deux cartes tiennent 60 images par seconde à 1080p sur le poste de référence, de jour comme de nuit | **tenu** : l'Arena of Fate, ses trois étages chargés, 101,7 et 102,1 images/s ; Martpart 111,0 et 111,8 ; au passage de la recette, l'Arena of Fate 103,5 et 103,7 |
| L'auteur confirme sur captures que l'Arena of Fate n'a rien perdu de ce qu'il avait validé le 4 octobre 2026 | **non tenu, ouvert** : jugement de l'auteur ; les captures du 4 octobre sont dans l'ancien dépôt |

| Livrable | État |
|---|---|
| L'Arena of Fate en une description à trois étages, même emprise, escaliers aux mêmes positions ; ses 105 maillages au maître, textures partagées ; la série rejouée | **tenu**, sauf les escaliers praticables : les étages se relient par les portails de la v4 (écart) |
| Martpart en description, ses 34 maillages et les deux arbres, au niveau de sa v0 ; les portails vers Arenarea appariés | **tenu** : 10 217 pièces posées, aucune sans maillage (29 des 34 maillages du kit sont posés par la v0, les 5 autres ne l'étaient pas) |
| Les captures à midi et à 22 h des trois étages et de Martpart, versées à la fiche et aux fiches LOT-106, LOT-107, LOT-157 | **tenu** (ci-dessous) |
| Les mesures de cadence et d'ouverture des deux cartes | **tenu** : la cadence (ci-dessus) ; l'ouverture d'une carte par un portail sous 1,1 s (critère du brief : 10 s) ; depuis le lancement du processus, 16 à 17 s, démarrage de l'éditeur compris |

### Ce qui s'écarte de la fiche

- **Le statut reste `a-faire`** : `lint_planning.py` refuse qu'un lot soit en cours sur un prérequis
  ouvert, et le LOT-1019 n'est pas livré.
- **Les escaliers ne relient pas les étages par le maillage de navigation** (la conception le
  voulait, « sans portail ») : mesuré, les pièces du kit ne le permettent pas — l'enceinte des
  vestiaires a un sol plein, les escaliers des deux portes montent sous l'enceinte de l'arène. Les
  étages se relient par les **portails de la v4**, qui visent la même carte ; les escaliers restent
  aux mêmes cases, en décor. Un escalier praticable demande une pièce neuve (une trémie dans
  l'enceinte, un escalier qui débouche sur le sable) : une commande pour l'auteur (question 1).
- **Les identifiants des catacombes `e7` et `e8`** étaient ceux de deux marqueurs du sable : ils
  deviennent `e32` et `e33` ; le point d'arrivée des catacombes, nommé comme celui du sable
  (`from-undercroft`), devient `catacombs-from-undercroft`. Tous les autres identifiants, arrivées
  et portails sont conservés, `from-arenarea` et le vestibule compris.
- **Le format change** : un étage peut être un sous-sol, une couche nomme son étage, une carte se
  découpe en niveaux de chargement (`storeyLevels`) — `EX-LVL-032`, `EX-LVL-034`, `EX-LVL-036`
  réécrites ; un cadrage nomme l'étage qu'il regarde.
- **Un portail dans le plein se franchit au contact** (deux cases, à son étage) : c'est un
  changement du jeu (`AJadgParty`), que le contrôle des cartes admettait déjà.
- **La démo passe par la place des étals** avant Stravian Avenue : l'ordre direct s'arrête en
  route (ci-dessus) ; la cause n'est pas trouvée.
- **L'heure fixe des sous-sols** (`"hour": "22:00"` de la v4) tombe : une carte n'a qu'une heure, et
  le sable a le cycle du jour ; sous le sable et l'enceinte des vestiaires, la lumière du jour
  n'entre pas.
- **La carte d'arène du jeu change** : l'Arena of Fate remplace l'arène d'essai (`ArenaMap`) ; le
  tour des écrans garde l'arène d'essai par `-JadgArene`, et sa référence.
- **Le parcours du combat amène le point visé** sur une destination ou une cible que le décor cache,
  une fois par clic : sur le sable, une destination au nord était cachée par une bannière.
- **`arena_fate_levels.py` reste** : il ne sert plus aux cartes, mais l'audit de l'atlas
  (`apply_atlas_audit.py`) en tire le plan des deux sous-sols.
- **Les captures validées par l'auteur le 4 octobre 2026 ne sont pas dans le dépôt** : elles sont
  celles du moteur maison, dans l'ancien dépôt (D-58). La comparaison est à l'auteur.
- **L'ouverture sous 10 s** ne se mesure, jeu lancé par les binaires de l'éditeur, qu'entre deux
  cartes (le passage d'un portail) ; depuis le lancement du processus, elle compte le démarrage de
  l'éditeur (16 à 20 s), comme au LOT-1012.

### Ce qui reste au lot

- **Les jugements de l'auteur** : l'Arena of Fate n'a-t-elle rien perdu de ce qu'il avait validé le
  4 octobre 2026 ; les hauteurs des sous-sols ; la caméra du joueur dans un sous-sol (sous le sable,
  elle se rapproche du meneur ; les captures cachent les étages du dessus, le jeu ne le fait pas).
- **Des escaliers praticables**, si l'auteur les veut (question 1).
- **La série entière dans le moteur** : `arene-bandits` se joue sur le sable ; les rencontres
  suivantes s'engagent par le dialogue du maître, mais le `levelUp` et le `rest` que ce dialogue
  demande ne sont pas joués par le moteur (`LOT-1017`, ce qui reste).
- **Le combat de groupe de la recette `0.0.2`** se rejoue sur le sable pour `arene-bandits` ; les
  cinq autres combats de la série, non.
- **Le chemin direct de Market Gate à Stravian Avenue** dans le jeu : il s'arrête en (60 ; 9,4),
  quand le contrôle du maillage de l'éditeur le dit ouvert. À voir dans une fenêtre, le maillage
  de navigation affiché (`show Navigation`) ; la démo passe par la place des étals.
- **Le parcours du combat n'est pas tout à fait déterministe** : sur la même graine, un passage sur
  trois a demandé de déplacer la caméra au round 6 ; le combat s'est joué de même.

### Questions pour l'auteur

1. **Les escaliers.** Les étages se relient par les portails de la v4 ; les escaliers sont un
   décor. Faut-il des escaliers praticables — une trémie dans l'enceinte des vestiaires, des
   escaliers qui débouchent sur le sable — à commander, ou les portails suffisent-ils à la
   `0.1.0` ?
2. **Les hauteurs des sous-sols** : 5,5 m et 6,6 m, la mesure de ce qu'ils portent. Un autre
   choix (les rapprocher, et raboter les voûtes et les cadres de chapelle) ?
3. **La caméra dans un sous-sol** : cacher les étages au-dessus du meneur dans le jeu, comme les
   captures le font, ou garder la caméra sous le sable ?
4. **L'Arena of Fate, carte d'arène du jeu** : la série s'y joue depuis le parvis d'essai ; le
   maître d'arène du sable (`e5`) l'engagera-t-il sur la même carte, sans la rouvrir (la question 7
   du LOT-1017) ?
