# Les cartes dans le moteur : le texte, le niveau, l'aller-retour

Une carte du jeu est un **fichier texte** : sa description au format `jadg-map`, version 5
([`niveaux.md`](../Specification/niveaux.md), §2). Le niveau qu'Unreal ouvre est une **sortie** de
ce fichier, refaite par script ; l'éditeur d'Unreal sert à placer à la souris, et ce qu'on y place
revient dans le texte. Cette page dit comment (`LOT-1018`, D-51, D-52).

## Ce qu'une description porte

Une seule description dit deux choses, d'un même plan :

| Ce que Core joue | Ce que le moteur construit |
|---|---|
| la grille de collision du rez (`tiles`, `forced`) | le terrain (`terrain`, `routes`, `outlines`) |
| les couches de pièces sur leurs cases (`layers`) | les objets en mètres (`objects`), les dallages (`fills`) |
| les entités sur leurs cases, à leur étage (`entities`) | les préfabriqués (`prefabs`), le groupe (`party`), les personnages (`characters`) |
| les étages praticables (`storeys`) | le ciel (`lighting`, `daylight`, `ground`), la navigation, les cadrages (`shots`, `hours`) |

Core lit la v5 par `core::LevelLoader` et passe ce qu'il ne joue pas. Le **repère** est celui de la
grille, en mètres : x vers l'est (les colonnes), y vers le sud (les lignes), z vers le haut ; le
coin de la case (0, 0) tombe en `origin`, une case fait 1,5 m. Un `yaw` tourne le sud vers l'est,
un `pitch` lève l'est, un `roll` lève le sud.

Le texte s'écrit sous une **forme canonique** — une case, un objet, une entité par ligne — par
`scripts/maps/jadg_map.py` : c'est lui qu'écrivent `build_essai_maps.py`, `build_gate_scene.py` et
`read_level.py`. `python scripts/maps/jadg_map.py --canonical` remet une carte écrite à la main dans
cette forme.

## Construire le niveau

```
powershell scripts/build.ps1 -Unreal -Map essai/etages            # le niveau, sans fenêtre
powershell scripts/build.ps1 -Unreal -Map essai/etages -Capture   # puis ses captures, à midi et à 22 h
```

`build.ps1` lance `scripts/maps/build_level.py` dans l'éditeur sans fenêtre (`-run=pythonscript
-JadgMap=<carte> -JadgCheck`). Le script :

1. installe chaque maillage cité par la **chaîne de décor** (`import_scenery_unreal.py`,
   `LOT-1019`) : importé s'il ne l'est pas encore (Interchange, Nanite, collision prise sur le
   maillage) — un maître par son manifeste, une pièce de kit sous `/Game/Kit/…`, une donnée
   d'essai sous `/Game/Fixtures/…` —, et habillé de sa matière complète : une instance de
   `M_Scenery` par matière, des textures compressées (BC7, BC5 pour le relief) et partagées ;
2. **mesure** ce que deviennent les axes d'un `.glb` dans le moteur, sur le bloc repère des données
   d'essai (`Scene/socle/repere.glb`) ;
3. pose le niveau : le **terrain** (un `Landscape` dont les hauteurs et les couches sont régénérées
   en images sous `Saved/Jadg/levels/<carte>/`), les **couches de pièces** par instances (la
   pièce du kit du lieu, du plus propre au plus commun, au centre de son emprise), les **objets**
   (`JadgObject:<id>`), les dallages, les **préfabriqués** (un `AJadgPrefab`, ses objets attachés),
   le ciel, la navigation, le groupe, les PNJ par leur fiche d'apparence, un **repère par entité**
   (`JadgMarker:<id>`) et une **boîte par volume** (`JadgVolume:<id>`), le cadre de la carte de
   Core (`AJadgMapFrame`, ses étages), les cadrages ;
4. **contrôle le maillage de navigation** (`-JadgCheck`) : chaque point d'arrivée, chaque entrée
   d'arène atteint depuis l'entrée ; une entité qu'on sollicite à portée (un portail dans un mur, un
   PNJ derrière son étal) peut être hors du maillage, et le journal le dit ;
5. sauve `/Game/Maps/Levels/<carte>` et écrit son **empreinte** : `Saved/Jadg/levels/<carte>.json`,
   chaque acteur par son étiquette, sa classe, sa transformation arrondie, son maillage, ses
   réglages. Deux constructions de la même description ont la même empreinte.

Une pièce d'une couche que le kit n'a pas (`mp-cypress` à Martpart) reste dans le texte, n'est pas
posée, et se compte dans le journal.

Les **captures** (`-Capture`) passent par la caméra du joueur, aux cadrages et aux heures de la
description, et `mesure.json` écrit la cadence, la mémoire graphique (celle du processus, celle des
textures des maillages de la carte) et les maillages (nombre, triangles Nanite, la plus grosse
pièce). Pour juger un réglage de rendu **avec et sans** sans reconstruire la carte (`LOT-1019`), le
jeu lancé à la main prend `-JadgPost=<a,b…>` : `contour` ajoute le contour sombre (`M_Contour`, que
`build_level.py` écrit ; une carte le pose d'office si `lighting.contour` est vrai), `sans-contour`
le retire, `sans-ao` coupe l'occlusion ambiante d'écran de Lumen, `sans-halo` le halo, et
`sans-ombres-lampes` les ombres des lampes.

Une pièce de décor se contrôle **seule, de ses quatre côtés** avant d'entrer dans une carte :
`python scripts/maps/build_piece_check.py` écrit sa carte de contrôle
(`controle/<pièce>`, pour chaque pièce dont la fiche donne une famille), et
`powershell scripts/build.ps1 -Unreal -Map controle/<pièce> -Capture` en prend la face, la droite,
le dos et la gauche, à midi et à 22 h (le [gabarit de commande](../../Planning/standards/gabarit-commande-zone.md)).

## Retoucher dans l'éditeur, relire

L'auteur ouvre le niveau dans l'éditeur d'Unreal, déplace un objet, tourne un préfabriqué, porte
le repère d'un PNJ une case plus loin, règle un cadrage ; puis :

```
UnrealEditor-Cmd.exe JustAnotherRpgGame.uproject -run=pythonscript ^
    -script="<dépôt>/scripts/maps/read_level.py" -JadgMap=essai/etages -unattended -nosplash -nullrhi
```

`read_level.py` réécrit la description. Il ne relit que la **frontière** — les objets, les
préfabriqués posés, les repères et les volumes des entités, les cadrages — et une valeur qui ne
diffère que par l'arrondi garde son écriture : relire un niveau intact ne change pas un octet.
**Ce qui ne se relit pas ne se fait pas dans l'éditeur** : un acteur ajouté, un maillage changé, le
terrain sculpté, une lumière réglée seraient refaits par `build_level.py` tels que le texte les dit.
La frontière complète est dans [`niveaux.md`](../Specification/niveaux.md) (`EX-LVL-035`).

L'**aller-retour** est un contrôle du build (`powershell scripts/build.ps1 -Unreal`,
`scripts/maps/check_level_roundtrip.py`), sur la carte à deux étages, dans un niveau à part : la
construire de rien (le niveau et ses maillages d'essai effacés), la reconstruire — même empreinte —,
la retoucher par l'API de l'éditeur comme à la souris (un mur déplacé et tourné, la rampe allongée,
le panneau de l'étage porté d'une case, un cadrage incliné), la relire — quatre gestes relus, eux
seuls —, la reconstruire depuis le texte relu : l'empreinte du niveau retouché.

## Deux étages dans une carte

Un lieu à plusieurs étages est une carte (D-51). La carte déclare ses étages (`storeys`) et chaque
entité nomme le sien (`storey`). `AJadgMapFrame` connaît leur hauteur (`StoreyHeights`) : à chaque
pas, `AJadgParty` dit à Core l'étage des pieds du meneur (`UJadgExploration::SetStorey`), et Core ne
sollicite que ce qui est à cet étage — à la verticale du portail du rez, le meneur de l'étage passe.
Un point d'arrivée pose le groupe à son étage. La trace du groupe porte la hauteur de chaque pas
(`core::FollowTrail::heightBehind`) : un suiveur monte l'escalier derrière le meneur, et cherche sa
place sur le maillage **près de cette hauteur** (à 1,2 m près, moins qu'un demi-étage), pas sous
lui au rez.

La carte d'essai `essai/etages` (`build_essai_maps.py`) le montre : un plancher à 3 m sur la moitié
est de la salle, une rampe, un portail du rez sous le plancher qui mène au palier de l'étage, et à
sa verticale un panneau et une lanterne de l'étage. `Jadg.Exploration.DeuxEtages` y joue la montée,
le passage au-dessus du portail, la redescente et le portail.

### Les sous-sols et les niveaux de chargement (`LOT-1022`)

Le rez est le premier étage déclaré, à 0 m ; les autres ont chacun leur hauteur, **au-dessus** pour
un étage, **en dessous** pour un sous-sol — jamais deux à la même. L'étage d'un point est le plus
haut dont le sol est sous lui (`AJadgMapFrame::StoreyAt`), dans l'ordre des hauteurs, pas des rangs.
Une couche de pièces (`layers`) et un objet nomment leur étage (`storey`) et se posent au-dessus de
son sol (`z`). La grille de collision de Core reste celle du rez ; un sous-sol n'a que le maillage
de navigation du moteur. Un portail peut viser la carte où il est : le groupe se pose au point
d'arrivée, à son étage, sans que la carte se rouvre.

Une carte qui le déclare (`"storeyLevels": true`) se construit en **un niveau de chargement par
étage** (`<niveau de la carte>-etage-<nom>`, `LevelStreamingAlwaysLoaded`) : le décor d'un étage
(ses couches, ses objets et leurs lumières) y va, le ciel, la navigation, les personnages, les
repères et les cadrages restent dans le niveau de la carte ; `AJadgMapFrame::StoreyLevels` les
nomme, et `ShowStorey` en cache un (il quitte le monde, reste chargé). Un cadrage qui regarde un
étage (`storey`) cache, le temps de sa capture, les étages au-dessus de lui ;
`build.ps1 -Unreal -Map <carte> -Capture -Etages <rangs>` ne montre que ces étages, et mesure leur
cadence. L'Arena of Fate est la première (voir le [guide des données](guide-donnees.md)).

## Contrôler le contenu

| Quoi | Où | Commande |
|---|---|---|
| le schéma, les identifiants, les bornes, les étages ; les portails appariés, les arrivées citées, les zones nommées, les cases inatteignables au rez ; la forme canonique | le texte, en CI | `python scripts/maps/jadg_map.py --check` |
| chaque carte se lit par Core ; le graphe des portails, les zones de combat | `JadgContentCheck` | `powershell scripts/build.ps1 -Unreal` |
| chaque point d'arrivée atteint sur le maillage de navigation, ou par un portail de la même carte | le niveau construit | `build_level.py -JadgCheck` |
| les drapeaux qu'une carte lit sans qu'aucune quête ne les déclare | le texte, en CI | `python scripts/maps/quest_mode.py --check` |

## Préfabriqués et mode Quêtes

Un **préfabriqué** est un fichier de `Source/Elements/Editor/Prefabs/<niveau>/<nom>.json`
(format `jadg-prefab`) : des objets autour d'une origine, par maillage ou par pièce du kit de son
lieu. Le Colisée de la porte en est un (`central-empire/capital/arenarea/colisee`, écrit par
`build_gate_scene.py`). Une carte le pose (`prefabs`) ; dans l'éditeur, il se déplace d'un bloc, et
seule sa place se relit.

Le **mode Quêtes** montre une carte à une étape de quête :

```
python scripts/maps/quest_mode.py essai/parvis --step pommes/acceptee
```

dit, entité par entité, ce qui est présent et la condition qui en décide (la règle de Core) ; lancé
dans l'éditeur (`-JadgMap=… -JadgStep=…`), il cache dans la vue les acteurs des entités absentes.

## Migrer une carte de l'ancien dépôt

```
python scripts/maps/jadg_map.py --migrate Source/Elements/Levels/<chemin>.json
```

réécrit une v4 en v5 à sa place : la grille, les couches, les entités et leurs identifiants ne
changent pas ; l'étage de décor d'une couche devient sa hauteur (3 m par étage, provisoire) ; les
notes de l'éditeur entrent dans la description ; le groupe, le ciel, la navigation et un cadrage
s'ajoutent. Les quatre cartes de la démo ont été migrées ainsi.

## Voir aussi

- [L'exploration dans le moteur](guide-exploration-moteur.md) — ce que le jeu fait d'une carte.
- [Niveaux : modèle, couches, entités, chargement](guide-niveaux.md) — le modèle de Core.
