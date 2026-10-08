+++
id = "LOT-1016"
titre = "Caméra, marche, groupe, portails, jour et nuit"
version = "0.0.3"
filiere = "moteur"
statut = "a-faire"
resume = "On explore une carte sur le nouveau moteur : la caméra libre de D-49, le groupe de quatre qui suit le meneur au clic, les interactions, les portails entre cartes et le cycle jour / nuit."
taille = "L"
prerequis = ["LOT-1014"]
livrables = [
  "La caméra de D-49 : rotation, zoom et inclinaison bornés, recentrage sur le meneur, réglages en fichier texte ; au clavier et à la souris, comme le jeu depuis le 2 octobre 2026.",
  "La marche au clic sur le maillage de navigation ; le groupe de quatre qui suit le meneur en file (reprend `FollowTrail`, LOT-138) ; le changement de meneur (Tab).",
  "L'interaction à 1,5 m (LOT-118, PR #138) : parler, ramasser, actionner ; le portrait du PNJ en dialogue.",
  "Les portails et points d'arrivée entre cartes, lus depuis les données de Core ; les drapeaux de quête qui les scellent (LOT-116).",
  "L'horloge du monde (une heure par minute réelle, D-45) et `daylight.json` pilotant le soleil, le ciel et la lune du moteur ; les lumières de nuit déclarées par les pièces ou posées comme entité `light`.",
  "Les captures à midi et à 22 h sur la carte d'essai du socle, versées à la fiche.",
]
criteres = [
  "La quête « Des pommes pour l'arène » se parcourt hors combat sur une carte d'essai : dialogue, jet de Persuasion, portails ; les tests d'intégration de la quête passent sur le nouveau moteur.",
  "Les quatre membres du groupe suivent le meneur sans se chevaucher ni rester bloqués ; un changement de meneur se fait en une touche.",
  "À 22 h, une lanterne éclaire le mur devant elle et pas celui derrière : les lumières de nuit portent une ombre.",
  "La caméra ne traverse ni le sol ni les murs ; ses bornes se règlent sans recompiler.",
]
+++

## Pourquoi

Le jeu doit se jouer à chaque instant : avant le combat, avant l'interface, il faut pouvoir marcher
dans une carte, parler et passer une porte. C'est le lot qui rend le nouveau moteur **jouable** au
sens de la trajectoire, et celui qui fait tomber la vue isométrique.

## Périmètre

Dedans : la caméra, la marche, le groupe, les interactions, les portails, le jour et la nuit.

Dehors, nommément :

- le combat (LOT-1017) ; la bascule vers le combat est posée mais mène à une arène vide ;
- l'interface : ce lot utilise un HUD minimal (noms, points de vie), le vrai vient au LOT-1020 ;
- les cartes : il joue sur la carte d'essai du socle et sur le parvis de la porte.

## Conception

- **La caméra** est un composant à ressort, cible le meneur, bornes en inclinaison (entre 25° et
  70°), en distance et en hauteur sous le terrain ; la rotation est libre (D-56).
- **Le déplacement** passe par le maillage de navigation du moteur (Recast) ; le groupe reprend la
  file de `FollowTrail` avec des points d'arrêt à distance fixe. Les blocages aux portes se traitent
  par des zones de navigation étroites, pas par du code.
- **Les interactions** gardent leur portée en mètres (1,5 m) ; l'indice visuel est un contour, pas
  un jeton.
- **L'heure** reste une donnée de Core (`DayLight`) ; le moteur ne fait que la lire. Les lumières
  de nuit portent une ombre (ce que le moteur maison ne faisait pas) ; leur nombre à l'écran n'est
  plus borné à trente-deux, et se mesure.

## Risques et questions ouvertes

- **Le groupe dans les escaliers et les étages** (D-51) : le maillage de navigation les couvre, la
  file doit suivre en hauteur ; à éprouver sur la carte d'essai à deux niveaux.
- **La bascule vers le combat** change de nature sans grille : les zones de combat de l'éditeur
  (LOT-143) deviennent des volumes ; le LOT-1017 en hérite.

## Avancement — 8 octobre 2026

Le lot est **réalisé pour l'essentiel et pas clos** : la quête des pommes se joue hors combat dans
le jeu lancé, sur deux cartes d'essai, sans personne ; ce qui manque est dit plus bas. L'en-tête
reste à `a-faire` : `lint_planning.py` refuse un lot `en-cours` dont un prérequis n'est pas livré,
et le LOT-1014 est encore `en-cours`. Sa clôture est une décision de l'auteur.

Le fonctionnement est décrit dans
[L'exploration dans le moteur](../../../../../Documentation/Guide/guide-exploration-moteur.md).

### Le partage : le moteur déplace, Core décide

Le meneur marche sur le maillage de navigation d'Unreal ; Core ne refait pas ce pas, il le
**constate** (`core::ExplorationIntent::carried`) et en tire le portail de la case atteinte, les
zones, l'interaction, les étapes de quête. La règle est écrite dans Core et testée hors du moteur.
Core reçoit aussi `ExplorationSession::interactionTarget()` : ce que le meneur solliciterait, sans
le solliciter — l'écran le désigne avant qu'on appuie.

Ce que le moteur apporte, plutôt que du code du jeu :

| Besoin | Ce qui le tient |
|---|---|
| le chemin du meneur et des suiveurs | maillage de navigation Recast, construit à l'ouverture de la carte ; `AAIController::MoveToLocation` |
| la caméra hors du sol et des murs | `USpringArmComponent`, sonde sur le canal `ECC_Camera` |
| les commandes | Enhanced Input : actions et contexte créés en C++ depuis `Config/DefaultGame.ini`, sans asset |
| l'ombre des lumières de nuit | lumières ponctuelles mobiles, ombres virtuelles |
| le contour de ce qu'on peut solliciter | tampon de gabarit (profondeur personnalisée) et matière de post-traitement écrite par script |
| le passage d'une carte à l'autre | `OpenLevel` ; l'état de la partie dans un sous-système de l'instance du jeu |
| les réglages en texte | le système de configuration du moteur (`UPROPERTY(config)`) |

### Ce qui se vérifie, et comment

Mesuré le 8 octobre 2026 sur le poste de référence (RTX 4060 Ti, Unreal Engine 5.8, 1920 × 1080).

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | **637 tests de Core, 100 % passés**, 1 ignoré (modèles de l'atelier absents) : deux nouveaux (`UnHerosMeneFranchitLePortailOuIlArrive`, `LaCibleDInteractionSeLitSansInteragir`) et un revenu, que la passation réservait à ce lot (`ToutFamilleLueParLeJeuEstDansLaTable`, réécrit sur le module du jeu et sur les cartes que le moteur joue) |
| `powershell scripts/build.ps1 -Unreal` | **9 tests du moteur passés, 0 avertissement** (six nouveaux, `Jadg.Exploration.*`) ; les captures du socle restent à leur référence |
| `powershell scripts/build.ps1 -Unreal -Parcours` | code 0 : la quête rendue 40 s après le lancement du processus, dont 15 s avant le premier ordre |
| `pytest` | 272 passés (huit nouveaux, `test_build_essai_maps.py`) |

Les six tests du moteur (`Source/JustAnotherRpgGame/Tests/JadgExplorationTests.cpp`) :

- `Jadg.Exploration.QueteDesPommes` — le test d'intégration de la quête, porté de l'ancien dépôt :
  sur le **contenu livré** (Martpart, Arenarea, le vestiaire), la mère, le portail, la zone du
  parvis, le garde et son jet ; puis les deux suites, **une graine par issue** (la graine 1 réussit
  le jet de Persuasion, la graine 2 le rate) : la voie de la parole jusqu'à la quête rendue, la voie
  de l'arène jusqu'au vestiaire. Le combat est le LOT-1017.
- `Jadg.Exploration.CartesDEssai` — les deux cartes d'essai se lisent ; le portail dépose au point
  d'arrivée nommé ; le passage condamné et le passage fermé par un drapeau de quête ne s'ouvrent pas.
- `Jadg.Exploration.Groupe` — sur un sol et son maillage de navigation : le meneur parcourt dix
  cases, les trois suiveurs s'arrêtent à une, deux et trois cases derrière lui (à 0,4 case près),
  aucun couple à moins de 0,6 case ; la main passe au suivant.
- `Jadg.Exploration.Camera` — l'inclinaison et la distance s'arrêtent à leurs bornes, la rotation
  est libre ; un mur dressé entre le point visé et la caméra la rapproche (de 16 m à moins de 8) ;
  un cadrage de capture le traverse.
- `Jadg.Exploration.HeureDuMonde` — soixante secondes font une heure ; réglée, l'heure se fige ; une
  lumière de nuit est éteinte à midi, allumée à 22 h, et porte une ombre ; un feu n'en porte pas.
- `Jadg.Exploration.Commandes` — chaque touche du fichier nomme une commande connue.

### Le parcours

`-Parcours` construit les deux cartes d'essai, lance le jeu hors écran et y joue la quête **par les
ordres d'un joueur** : marcher près de la mère, la solliciter à la touche, accepter ; marcher
jusqu'au portail ; entrer dans la zone du parvis, plaider (Persuasion 16 contre DD 15, graine 1) ;
revenir par le portail ; cliquer la mère. Les deux cartes du moteur s'ouvrent l'une après l'autre,
la partie passe de l'une à l'autre. Son journal et trois de ses images sont dans
[`annexes/LOT-1016/captures/`](../annexes/LOT-1016/captures/) : `parcours.json`,
`parcours-invite.png` (l'invite et le contour), `parcours-garde.png` (la réponse qui annonce son
jet), `parcours-persuasion.png` (le jet joué).

Les cartes d'essai (`essai/etals`, `essai/parvis`) sont écrites par
`scripts/maps/build_essai_maps.py` : la carte de Core et la description de scène viennent du même
plan. Elles ne lisent aucun kit d'assets et jouent les dialogues et la quête **livrés**.

### Les captures

Dans [`annexes/LOT-1016/captures/`](../annexes/LOT-1016/captures/), à midi et à 22 h : `etals`,
`lanterne` (la lanterne et son pan de mur, vus du nord-est) et `parvis`. À 22 h, la face du mur
tournée vers la lanterne est éclairée et le sol derrière lui est dans son ombre
(`lanterne-2200.png`). Le HUD n'est pas dans une capture de scène (l'heure qu'il écrit la ferait
changer d'une minute à l'autre) ; il est dans celles du parcours.

### Les mesures

Dix secondes par heure, caméra en rotation, comme au LOT-1012 (`mesure-*.json`, même dossier).

| Carte | Heure | Images par seconde | Trame moyenne | 1 % le plus lent | Processeur graphique |
|---|---|---|---|---|---|
| étals (245 objets, 6 personnages, 1 lumière de nuit) | 12:00 | 108 | 9,3 ms | 12,0 ms | 8,7 ms |
| étals | 22:00 | 108 | 9,3 ms | 11,0 ms | 8,8 ms |
| parvis d'essai | 12:00 | 108 | 9,3 ms | 13,1 ms | 8,7 ms |
| parvis d'essai | 22:00 | 107 | 9,4 ms | 11,2 ms | 8,8 ms |
| la porte (LOT-1012), groupe de quatre | 12:00 | 88 | 11,4 ms | 27,5 ms | 10,3 ms |
| la porte, groupe de quatre | 22:00 | 88 | 11,3 ms | 22,1 ms | 10,6 ms |

**La porte ne rend plus les 119 images par seconde de sa clôture.** Ce lot n'en est pas la cause :
le code d'avant le lot, reconstruit et mesuré le même jour sur la même carte, donne 89,1 images par
seconde à midi (10,2 ms de processeur graphique) ; avec le héros seul au lieu des quatre, 89,9 ;
avec le tampon de gabarit éteint, 88,1. L'écart avec le 8 octobre au matin vient d'ailleurs — le
poste ou la carte — et n'est pas cherché ici.

**Les lumières de nuit.** La porte en porte seize : huit lumières de nuit avec ombre et huit feux
sans ombre portée. Leur coût propre n'est pas isolé : midi et 22 h se rendent à la même cadence.

### Ce qui s'écarte de la fiche

- **La touche d'interaction est Espace ou Entrée, pas E.** `E` tourne la caméra (A / E, comme à la
  porte) ; `controles.md` écrit « E ou Espace » pour l'ancien jeu. Une ligne de
  `Config/DefaultGame.ini` suffit à trancher : à l'auteur.
- **Les distances de la caméra sont celles de la porte** (4 m à 120 m), que personne n'a jugées
  dans une fenêtre ; seule l'inclinaison (25° à 70°) vient de la fiche.
- **Le portrait du PNJ en dialogue n'est pas affiché.** Le HUD minimal écrit qui parle ; le portrait
  vient avec l'interface (LOT-1020).
- **Seul « parler » est joué dans le moteur.** Ramasser et actionner passent par le même chemin de
  Core (`Interacted`), mais aucune carte d'essai ne porte de coffre ni de panneau.
- **La bascule vers le combat est notée, pas ouverte** : une rencontre engagée par un dialogue ou
  une interaction s'écrit au journal (`[Groupe] rencontre … engagée`) ; il n'y a pas d'arène vide.
- **Le soleil et la lune sont la même lumière dirigée**, comme au LOT-1012 : la table du jour donne
  sa direction et sa couleur à toute heure. Aucun astre n'est dessiné à part.
- **Un PNJ prend son personnage dans la description de scène** (`"entity"`), pas dans la propriété
  `figure` de son entité : les personnages entrent dans le moteur au LOT-1015.
- **La porte ne joue aucune carte de Core** : elle reçoit le groupe de quatre, la caméra, les
  commandes et l'heure, pas de portail ni de PNJ. Sa carte de Core est celle du LOT-1021.
- **Le catalogue des textes** est lu par quelques lignes du moteur (`fr.lang`, clé = valeur) ; trois
  invites (« Parler », « Ouvrir », « Lire ») sont écrites dans le HUD. Le lecteur se décide au
  LOT-1020.

### Les critères

| Critère | État |
|---|---|
| La quête se parcourt hors combat sur une carte d'essai ; les tests d'intégration passent sur le nouveau moteur | **tenu** pour la voie de la parole, jouée de bout en bout dans le jeu lancé (`-Parcours`) ; les tests d'intégration portés passent (`Jadg.Exploration.QueteDesPommes`, deux issues). La voie de l'arène s'arrête au vestiaire : le combat est le LOT-1017 |
| Les quatre suivent sans se chevaucher ni rester bloqués ; un changement de meneur en une touche | **tenu sur ce qui est mesuré** : dix cases en ligne droite (`Jadg.Exploration.Groupe`) et les deux cartes du parcours, portes comprises. Un angle de mur serré n'est mesuré que dans Core (`UnGroupeDeQuatrePasseLesAnglesSansResterCoince`) |
| À 22 h, une lanterne éclaire le mur devant elle et pas celui derrière | **tenu sur capture** (`lanterne-2200.png`) ; le jugement de l'image est à l'auteur |
| La caméra ne traverse ni le sol ni les murs ; ses bornes se règlent sans recompiler | **tenu pour un mur** (`Jadg.Exploration.Camera`) ; le sol passe par la même sonde et n'a pas son test. Les bornes sont dans `Config/DefaultGame.ini` |

### Ce qui reste au lot

- **Personne n'a joué dans une fenêtre.** Les tests et le parcours donnent leurs ordres au groupe
  et au dialogue ; ils ne passent pas par le clavier ni la souris. Les touches sont vérifiées dans
  leur fichier, pas sous la main : le clic droit qui tourne, la molette, le clic sur un PNJ sont à
  essayer par l'auteur.
- **Les étages** (D-51) : la trace de la file est en deux dimensions ; un suiveur prend le point du
  maillage de navigation le plus proche de son point, ce qui n'est pas éprouvé sur une carte à deux
  niveaux. Aucune carte d'essai n'a d'escalier.
- **Les personnages ne se bloquent pas** : ni entre membres du groupe, ni contre un PNJ. Le meneur
  traverse un PNJ s'il est sur son chemin.
- **Un coffre, un panneau** sur une carte d'essai, et l'annonce de ce qu'on y trouve.
- `controles.md` décrit encore les commandes de l'ancien jeu : il se reprend avec les
  spécifications (LOT-1014, LOT-1023).
