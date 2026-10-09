# L'exploration dans le moteur

[Monde et exploration](guide-monde.md) décrit les **règles** de l'exploration : elles sont dans
Core, sans une ligne du moteur. Cette page décrit ce qui les **joue** dans Unreal depuis le
`LOT-1016` : la caméra, la marche du groupe, les commandes, et le pont qui donne à Core la case du
meneur. Tout ce qui suit vit dans `Source/JustAnotherRpgGame/`, hors de `Core/`.

## Le partage : le moteur déplace, Core décide

Le meneur marche sur le **maillage de navigation** du moteur (Recast) : le chemin, la pente et
l'escalier sont ceux d'Unreal. Core ne refait pas ce pas et ne le confronte pas à sa grille : il le
**constate**. À chaque trame, la case du meneur lui est donnée
(`core::ExplorationIntent::carried`), et il en tire ce qu'il tire d'un pas marché : l'orientation,
le portail de la case atteinte, les zones à déclencheur, l'interaction, les étapes de quête.

| Qui | Fait quoi |
|---|---|
| le moteur | le chemin et le déplacement (maillage de navigation, `ACharacter`), la caméra, les ombres, les entrées |
| Core | les portails et leurs drapeaux, les points d'arrivée, la présence des entités, la portée d'interaction, les dialogues et leurs jets, les quêtes, l'heure du monde, la trace de la file |

La règle « un portail se franchit en y **arrivant** » reste donc celle de Core, et vaut pour les
deux constructions : elle se teste hors du moteur
(`ExplorationSessionTest.UnHerosMeneFranchitLePortailOuIlArrive`).

## Les pièces

| Classe | Fichier | Rôle |
|---|---|---|
| `UJadgExploration` | `Game/JadgExploration.h` | sous-système de l'instance du jeu : la session de Core, gardée d'une carte à l'autre ; le dialogue ouvert ; l'heure ; le groupe ; les textes |
| `AJadgMapFrame` | `World/JadgMapFrame.h` | relie une carte du moteur à une carte de Core : son identifiant, où tombe sa case (0, 0), ce que deviennent ses axes |
| `AJadgParty` | `Characters/JadgParty.h` | le groupe sur la carte : le meneur, la file, le pas d'exploration, les entités présentes, le contour |
| `AJadgWalker` | `Characters/JadgWalker.h` | un personnage lié : membre du groupe (`PartyRank`) ou entité de la carte (`EntityId`) |
| `AJadgCameraPawn` | `Player/JadgCameraPawn.h` | la caméra libre de D-49, à ressort |
| `AJadgPlayerController`, `UJadgControls` | `Player/` | les commandes, lues dans un fichier texte |
| `AJadgDayLight` | `World/JadgDayLight.h` | l'heure du monde appliquée au soleil, au ciel et aux lumières de nuit |
| `AJadgHud` | `UI/JadgHud.h` | le gestionnaire des écrans (LOT-1020) : le HUD d'exploration (lieu, heure, groupe, annonce, invite, rencontre), le dialogue, les pages ([manuel du joueur](Manuel/README.md)) |
| `AJadgWalkthrough` | `Capture/JadgWalkthrough.h` | joue la quête des pommes sur les cartes d'essai, sans personne, par les touches et les clics du joueur |

Aucun en-tête du moteur ne montre un type de Core : `UJadgExploration` parle en `FString` et en
`FVector2D`, et garde l'état de Core derrière un pointeur (`FState`). Une case est une position
continue (colonne, ligne), le centre de la case (4, 2) en (4,5 ; 2,5).

## Une carte du moteur, une carte de Core

Une carte de Core garde ses entités sur des cases de 1,5 m. Depuis le `LOT-1018`, la carte du
moteur et la carte de Core sont **une seule description** (format v5,
[Les cartes dans le moteur](guide-cartes-moteur.md)) : `build_level.py` en construit le niveau,
`/Game/Maps/Levels/<id>` (`AJadgMapFrame::MapPackage`) — le chemin qu'un portail ouvre —, et y pose
un `AJadgMapFrame` au coin de la case (0, 0), avec les axes **mesurés** à l'import et la hauteur de
chaque étage. Toute carte du moteur joue sa carte de Core : la porte du `LOT-1012` aussi, dont la
grille est tirée de la géométrie construite (`build_gate_scene.py`).

Ce que la carte de Core fait paraître :

- un **PNJ** est une entité `npc` qui nomme sa fiche d'apparence (`"appearance"`) : le niveau pose
  son personnage, et au lancement il se pose sur la case et à l'étage que Core lui donne, et ne paraît que si l'entité est présente sous les
  drapeaux — l'enfant ne rentre auprès de sa mère qu'une fois libéré, sans que la carte se recharge ;
- une **lumière** posée comme entité `light` devient une lumière ponctuelle du moteur
  (`AJadgDayLight::AddLamp`) : une lumière de nuit porte une ombre et suit `lamps` de la table du
  jour, un feu toujours allumé éclaire sans ombre portée ;
- un **objet du décor** peut montrer une entité (`"entity"` sur un objet) : il est présent et
  désignable avec elle — un coffre, qui ne s'ouvre qu'une fois, un panneau, qui se relit ;
- les **portails**, les **points d'arrivée** et les **zones** n'ont pas d'acteur : c'est la case du
  meneur qui les déclenche.

Un **portail** franchi rend un `MapEntered` : `AJadgParty` ouvre la carte du moteur de la carte
cible (`OpenLevel`), et le groupe s'y pose au point d'arrivée que Core a retenu. La session vit
dans l'instance du jeu : drapeaux, quêtes, heure et ordre du groupe passent la porte avec lui. Un
portail **condamné**, ou **fermé** par un drapeau de quête, ne s'ouvre pas : le HUD le dit.

## Le groupe

Les personnages que la carte pose pour le groupe (`party`, par leur fiche d'apparence, au rang 0 à
3) forment le groupe, le meneur en tête. Le clic envoie le meneur ; les autres mettent leurs pas dans les siens. La trace est
celle de Core (`core::FollowTrail`) : le suiveur de rang `r` vise le point situé à
`r × SPACING_CELLS` cases derrière le meneur **le long de son chemin**, et y va par le maillage de
navigation. Un suiveur ne coupe donc pas un angle que le meneur a contourné.

- Un suiveur reçoit un nouvel ordre quand son point a bougé de 0,2 case ; à moins de 20 cm de son
  point, il n'y est pas renvoyé.
- À l'arrivée sur une carte, la file se range dans le dos du meneur, à une case l'un de l'autre,
  tant que le maillage porte. Le maillage d'une carte se construit après son lancement : le groupe
  attend sur le point d'arrivée et se range dès qu'il porte.
- **Les personnages se bloquent** (`LOT-1017`, dette du `LOT-1016`) : la capsule de chacun bloque
  celle des autres, membres du groupe et PNJ (canal `Pawn`), et l'évitement réciproque du
  mouvement (RVO du `CharacterMovementComponent`, rayon de considération 2 m, poids 0,5) les
  écarte l'un de l'autre au lieu de les pousser : un meneur qui fait demi-tour contourne ses
  suiveurs. Une file posée sur un seul point (le maillage pas encore prêt à l'arrivée) ne se
  bloque pas tant que ses membres se recouvrent — sinon ils repoussaient le meneur hors de la case
  que Core lui donne (mesuré : 0,57 case au retour de l'arène) — ; elle se bloque dès qu'ils sont
  écartés. En combat, Core tient l'espace : la capsule ne bloque plus les autres personnages et
  l'évitement se coupe (`AJadgWalker::SetInCombat`).
- **Passer la main** (`Tab`) : le meneur va en queue (`EX-EXP-014`), `core::Party` tourne avec lui,
  la caméra suit le nouveau meneur.

## Interagir

La cible est celle que Core désigne (`core::findInteractionTarget`, à moins de 1,5 case, ce que le
meneur regarde d'abord). `core::ExplorationSession::interactionTarget` la rend **sans la
solliciter** : l'écran la montre avant qu'on appuie.

- Le **contour** : l'acteur désigné est marqué dans le tampon de gabarit (profondeur
  personnalisée), et une matière de post-traitement dessine son contour (`M_Outline`, écrite par
  `build_level.py` ; `r.CustomDepth=3`).
- La **touche** d'interaction (`F`) sollicite la cible du moment.
- Le **clic** sur un PNJ, un coffre ou un panneau envoie le meneur à une case de lui, puis le fait
  interagir dès qu'il l'a à portée.

Un coffre ouvert n'est plus une cible : Core ne le désigne plus, le contour le quitte. Core ne dit
que la famille de ce qu'on sollicite ; ce qu'un coffre contient viendra avec l'inventaire à l'écran.

Un dialogue qui s'ouvre **gèle la carte** : le meneur s'arrête, l'heure ne passe plus. Le HUD
écrit qui parle, la réplique, les réponses numérotées — une réponse qui mène à un jet l'annonce
(« Persuasion · DD 15 ») — et le jet qui vient d'être joué. La graine du jet est un compteur de la
partie, ou celle que `UJadgExploration::SetSeed` fixe.

**Le portrait** de celui qui parle est celui de sa figurine : la propriété `figure` de son entité,
résolue par Core (`core::figureDirectory`), donne un dossier de `Source/Elements/Assets`, et le HUD
y lit `portrait.png`. Rien n'en est importé dans le projet. Sans figurine, ou sur un poste sans les
kits, le dialogue s'écrit sans portrait.

## La bascule vers le combat

Une rencontre s'engage par un dialogue (`startEncounter`, le maître d'arène) ou par une entité de
la carte. `UJadgExploration::Encounter` la nomme ; tant qu'elle tient, la carte est gelée et
l'heure ne passe pas. `AJadgParty` ouvre la **carte d'arène** (`ArenaMap`, dans
`Config/DefaultGame.ini` : `/Game/Maps/Levels/essai/arene`). Dans l'arène, le groupe ne joue pas
la carte de Core de l'arène en exploration — la session garde la carte quittée, gelée — : il crée
le **combat** (`AJadgCombat`, `LOT-1017`), qui monte la rencontre sur la carte de Core que nomme le
repère de l'arène et se joue (le [guide du combat](guide-combat.md) le décrit). Le maillage de
navigation de l'arène se construit après son lancement : le groupe remonte le combat à chaque
trame jusqu'à ce qu'il tienne (trois trames sur le poste de référence, 600 au plus).

À l'issue, `UJadgExploration::ResolveEncounter` l'écrit par `core::endEncounter` — une victoire
pose `encounter/<rencontre>/won`, que les dialogues lisent —, les points de vie et les lancers
restants passent sur les fiches (à terre : 1 PV ; debout : ses PV, au moins 1 ; une défaite ne
laisse rien), et la carte quittée se rouvre, **le groupe là où il était** : la session d'exploration
a gardé la case du meneur, gelée, et la file se range derrière lui.

`-JadgRencontre=<id>` engage une rencontre au lancement de l'arène elle-même ; avec
`-JadgCapture`, le combat se monte et reste figé sur son déploiement pour les captures.

## La caméra

`AJadgCameraPawn` est le **point visé** ; la caméra le regarde au bout d'un bras à ressort
(`USpringArmComponent`). Elle tourne librement (D-56), s'incline entre deux bornes, zoome entre
deux distances, suit le meneur ou se détache quand on déplace le point visé.

**Elle ne traverse ni le sol ni les murs** : le bras sonde le décor entre le point visé et la
caméra (canal `ECC_Camera`) et la rapproche de ce qu'il rencontre. Les personnages n'arrêtent pas
la sonde. Un cadrage de capture (`SetView`) pose la vue sans elle.

Les bornes se règlent dans `Config/DefaultGame.ini`, sans recompiler :

| Réglage | Valeur livrée | Ce qu'il borne |
|---|---|---|
| `MinPitch`, `MaxPitch` | 25°, 70° | l'inclinaison sous l'horizon (fiche du `LOT-1016`) |
| `MinDistance`, `MaxDistance` | 4 m, 120 m | la distance au point visé (valeurs de la porte, pas encore jugées dans une fenêtre) |
| `StartPitch`, `StartDistance` | 40°, 16 m | la vue au lancement |
| `FollowHeight` | 1 m | la hauteur visée au-dessus des pieds du meneur |
| `ProbeSize` | 12 cm | le rayon de la sonde |
| `FollowSpeed` | 6 | la vivacité du suivi |

## Les commandes

Une commande est **nommée**, dissociée de sa touche (`EX-CTRL-010`). Les touches sont des lignes de
`Config/DefaultGame.ini` (`[/Script/JustAnotherRpgGame.JadgControls]`) ; au lancement le contrôleur
en fait des actions d'Enhanced Input créées en C++, sans asset ni Blueprint.

| Commande | Effet | Touches livrées |
|---|---|---|
| `Walk` | le meneur marche vers le point cliqué ; sur un PNJ, il va lui parler ; en combat, la cible ou la destination | clic gauche |
| `Interact` | solliciter la cible ; en dialogue, « continuer » | F |
| `NextLeader` | passer la main au suivant ; sans effet en combat | Tab |
| `Recenter` | ramener la caméra sur le meneur ; en combat, sur le combattant actif | Début |
| `Choice1` … `Choice6` | donner la réponse de ce rang ; en combat, choisir la capacité de ce rang | 1 … 6 |
| `Attack`, `Capacity`, `EndTurn` | en combat : attaquer la cible, lancer la capacité choisie, finir le tour (`LOT-1017`) | X, W, Espace |
| `Turn`, `Tilt` | tourner, incliner la caméra | A / E, R / V |
| `Look` + `LookTurn`, `LookTilt` | tourner et incliner à la souris | C tenue, ou clic droit tenu |
| `Zoom` | rapprocher, éloigner | molette |
| `PanForward`, `PanRight` | déplacer le point visé | Z / S, D / Q, flèches |

`F` pour interagir et `C` pour tourner la caméra sont une décision de l'auteur (8 octobre 2026) ;
l'invite du HUD écrit la touche que le fichier donne à `Interact`.

## L'heure

L'heure du monde est celle de Core (`core::WorldClock`, une heure par minute réelle, D-45) :
`UJadgExploration` la fait passer avec l'exploration, `AJadgDayLight` la lit à chaque trame et
l'applique au soleil, au ciel et aux lumières de nuit. Elle se fige pendant un dialogue. Une carte
qui déclare une heure fixe (`hour`) se montre à cette heure. `Jadg.Time 22:00` la règle et la fige,
`Jadg.Time run` la relance.

## Vérifier

| Quoi | Commande |
|---|---|
| les tests du moteur (`Jadg.Exploration.*`), sans fenêtre | `pwsh scripts/build.ps1 -Unreal -NoCapture` |
| une carte d'essai et ses captures | `pwsh scripts/build.ps1 -Unreal -Map essai/etals -Capture` |
| la quête des pommes jouée dans le jeu lancé | `pwsh scripts/build.ps1 -Unreal -Parcours` |
| la rencontre `arene-bandits` jouée dans le jeu lancé | `pwsh scripts/build.ps1 -Unreal -ParcoursCombat -Seed 2` |

Les cartes d'essai sont écrites par `scripts/maps/build_essai_maps.py`, une description v5 chacune,
la grille et ce qui se construit tirés du même plan — les étals, le parvis, l'arène du combat
(`essai/arene`) et la carte à deux étages (`essai/etages`, `LOT-1018`).

Le **parcours** joue par les entrées du joueur : il presse les touches que le fichier donne aux
commandes, injectées dans le contrôleur (`APlayerController::InputKey`), qui passent donc par
Enhanced Input comme celles d'un clavier ; un clic est le bouton gauche pressé, le pointeur posé sur
sa cible (`AJadgPlayerController::PointAt`), après vérification qu'il la désigne. Il essaie d'abord
chaque commande de caméra et la juge à son effet, puis joue la quête : le clic au sol, la touche
d'interaction, les réponses au clavier, le clic sur le coffre, sur le maître d'arène — à qui il
répond « attendre » : le combat a son propre parcours —, sur la mère.
Les trois marches vers un portail ou une zone restent des ordres donnés au groupe. Il capture
chaque réplique et quitte en erreur dès qu'une commande n'a pas son effet.

Ce qu'il ne remplace pas : une main sur la souris. La sensation — vitesse de rotation, pas de la
molette, précision du clic — se juge dans une fenêtre.
