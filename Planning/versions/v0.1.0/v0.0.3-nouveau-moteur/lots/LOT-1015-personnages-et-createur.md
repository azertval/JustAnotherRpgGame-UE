+++
id = "LOT-1015"
titre = "Les personnages dans le moteur : squelette, animations, créateur Mutable, les quatre héros"
version = "0.0.3"
filiere = "pnj"
statut = "en-cours"
taille = "L"
resume = "Un personnage devient une fiche texte que le créateur Mutable du moteur assemble sur le squelette d'Unreal, animé par les bibliothèques du moteur ; les quatre héros en sont la preuve, et la chaîne maison des personnages est supprimée."
prerequis = ["LOT-1014"]
livrables = [
  "Le plugin Mutable et le plugin MetaHuman Character activés dans `JustAnotherRpgGame.uproject`.",
  "Un constructeur rejouable du créateur — `scripts/assetsGeneration/build_character_creator.py`, un commandlet C++ `JadgBuildCharacterCreator`, ou les deux — qui construit l'objet personnalisable Mutable depuis une description texte rangée sous `Source/Elements/Assets/Characters/`, sans geste dans l'éditeur.",
  "Le format de la fiche de personnage (JSON, schéma sous `Source/Elements/Rpg/schema/`) et son lecteur dans Core, sans dépendance au moteur.",
  "Un acteur du jeu qui instancie un personnage depuis sa fiche : il lit la fiche par Core et donne ses valeurs aux paramètres de l'objet personnalisable.",
  "Le jeu d'animations du moteur — repos, marche, attaque, incantation, coup reçu, mort — reciblé sur le squelette standard d'Unreal par l'IK Retargeter ; l'instant de l'impact (`key`) porté par une donnée texte.",
  "Les armes accrochées par socket à une main, depuis les armes au maître de `Source/Elements/Assets/Master/Weapons` (D-63, qui tranche D-42).",
  "Les quatre héros — Grom, Faelar, Helga, Nessa (fiches de `Source/Elements/Rpg/characters/`) — en MetaHuman, comme preuve du créateur.",
  "La suppression de la chaîne maison (D-64), dans la PR du lot : voir « À supprimer ».",
  "`Planning/standards/personnages-3d.md` réécrit sur ce qui est mesuré dans le moteur.",
  "Les captures de contrôle (repos, marche) à midi et à 22 h, versées à la fiche.",
  "Des tests du moteur `Jadg.Personnages.*` et des tests de Core sur le lecteur de fiches (`Source/Test/Unit/Core`).",
]
criteres = [
  "Les quatre héros se tiennent au repos et marchent sur la carte d'essai des étals, et suivent le meneur.",
  "La fiche d'un héros modifiée — une taille, une couleur de peau, une pièce — change le personnage dans le jeu sans geste dans l'éditeur.",
  "Rejoué, le constructeur redonne les mêmes assets (empreintes) ; `check_orphans.py` passe et cite chaque sortie par son script.",
  "La régénération du graphe Mutable depuis le texte est mesurée et écrite dans la fiche : faisable ou non, et par quoi.",
  "La cadence est mesurée avec les quatre héros à l'écran, à midi et à 22 h, et écrite dans la fiche.",
  "Les tests de Core et `Jadg.Personnages.*` passent (`scripts/build.ps1`, `scripts/build.ps1 -Unreal`).",
]
+++

## Pourquoi

Le jeu final propose beaucoup de personnages différents : 22 espèces jouables
(`Source/Elements/Rpg/species/`), des PNJ par lieu, des adversaires par rencontre. Un maillage par
personnage (D-38) multiplie les commandes Meshy, les liaisons et les contrôles à chaque visage.
L'auteur l'a écarté le 8 octobre 2026 : « au vu de la quantité de personnages différents proposés
par le jeu final il faudrait éviter d'avoir un modèle unique par personnage mais plutôt un créateur
de personnage permettant de modifier facilement un modèle de base pour avoir des personnages
uniques (comme dans des MMORPG type AION ou Black Desert) ». Il demande « la solution la plus
long-termiste, il vaut mieux passer du temps maintenant tant qu'il y a peu de données », et, pour
toute la version, de « réinterpréter mon ancien moteur dans Unreal Engine et tirer au maximum parti
des fonctions du moteur » ([D-63](../../../../vision/decisions.md),
[D-64](../../../../vision/decisions.md)).

Ce lot pose le créateur et prouve qu'il tient sur les quatre héros. Sans lui, le combat (LOT-1017)
n'a personne à animer, et les vingt maillages de la démo importés tels quels seraient jetés dès
que le créateur arriverait : des assets morts (D-32).

## Périmètre

Dedans : les plugins, le constructeur du créateur, la fiche de personnage et son lecteur, l'acteur
qui instancie une fiche, les animations reciblées, les armes par socket, les quatre héros, la
suppression de la chaîne maison, la réécriture du standard des personnages.

Dehors, nommément :

- les paramètres de race des 22 espèces, la garde-robe commune et les humanoïdes de la démo (la
  mère, l'enfant, le garde, le maître d'arène, les adversaires de l'arène) : au
  [LOT-1024](LOT-1024-createur-especes-et-humanoides.md) ;
- le lion et le loup : au [LOT-1025](LOT-1025-creatures-lion-et-loup.md) ;
- les PNJ des trois lieux : aux lots de la `0.0.4` ;
- la silhouette volante, qui attend sa première créature ;
- les portraits et les jetons : ils restent peints (D-30), rien ne change pour eux ;
- le changement d'arme par l'inventaire : le socket le permet, l'inventaire ne le joue pas ici.

## À supprimer

Dans la PR du lot (D-32, D-59), parce que le moteur fait nativement ce qu'ils faisaient (D-64) :

| Quoi | Où | Pourquoi maintenant |
|---|---|---|
| `rig_character.py`, `rig_quadruped.py` (squelettes `humanoid` à 53 os et `quadruped` à 29 os, clips posés par cibles) | `scripts/assetsGeneration/` | le squelette standard d'Unreal et les animations reciblées les remplacent |
| `retouch_character.py` (la retouche dans Blender, D-44) | `scripts/assetsGeneration/` | plus de clip maison à retoucher |
| `reduce_model.py` | `scripts/assetsGeneration/` | le maître s'importe tel quel (D-53) |
| `render_character_review.py` (les planches) | `scripts/assetsGeneration/` | les captures de contrôle se font dans le moteur |
| `check_character_model.py` | `scripts/checks/` | il contrôle une liaison maison qui n'existe plus |
| `test_rig_character.py`, `test_rig_quadruped.py`, `test_retouch_character.py`, `test_reduce_model.py` | `scripts/tests/` | leurs scripts partent |
| Les 21 maîtres de personnages | `Source/Elements/Assets/Master/Npc/`, leurs entrées de `manifest.json` et de `references.json` | un personnage est une fiche ; les héros sont refaits en MetaHuman, les autres aux LOT-1024 et LOT-1025 |
| Les §1, §2, §4 à §9 et §11 du standard des personnages | `Planning/standards/personnages-3d.md` | réécrits sur les mesures du moteur |

Ce qui cite ces scripts — `build.ps1`, la CI, `check_orphans.py`, le guide du développeur — se
reprend dans la même PR. Les copies réduites des kits (`Common/Characters/**`) et leurs fiches de
liaison suivent le même sort à la republication du kit (D-62).

## Conception

- **Une fiche par personnage.** Elle donne les valeurs des paramètres de l'objet personnalisable :
  le corps, la tête, la taille, les couleurs, les pièces, la garde-robe, l'arme de chaque main.
  Core la lit (nlohmann, comme tout le contenu) et ne connaît pas Mutable ; le moteur traduit. Le
  lien avec la fiche de règles (`Source/Elements/Rpg/characters/`) se décide ici : une même fiche
  ou deux fiches liées, selon ce que le schéma tient le plus simplement.
- **Le créateur est une sortie.** Le graphe Mutable est un asset d'éditeur : il se construit par
  script ou par commandlet depuis la description texte de `Source/Elements/Assets/Characters/`, et
  se régénère comme le reste de `Content/` (D-52, D-60). C'est la première chose que le lot mesure.
- **MetaHuman pour les héros.** Le corps et la tête des quatre héros viennent de MetaHuman
  Creator, piloté en Python dans l'éditeur de la 5.8. Le montage Mutable et MetaHuman suit la
  documentation d'Epic (« Using Mutable and MetaHumans in Unreal Engine », dev.epicgames.com).
  Mutable cuit les maillages : le mélange de visages de MetaHuman ne se fait pas à l'exécution, ce
  qui ne gêne pas des personnages décrits en fiche.
- **Le squelette standard d'Unreal et ses animations.** Les animations viennent des bibliothèques
  du moteur (MetaHuman, Fab) et se reciblent par l'IK Retargeter. Le `key` d'un clip, l'instant de
  l'impact que le combat attend, est une donnée texte à côté de la fiche, pas une notification
  posée à la main dans un asset.
- **Les armes par socket.** L'arme est un modèle à part accroché à une main (D-63) ; les armes au
  maître de `Master/Weapons` servent telles quelles.
- **Fab.** Admis pour les corps de base, la garde-robe et les animations (D-55 étendue). Chaque
  pack se vérifie pour sa licence avant achat, et seul l'auteur achète.

## Risques et questions ouvertes

- **Le graphe Mutable par code.** Relevé sur le poste le 8 octobre 2026 (Unreal 5.8.3) : le
  plugin n'expose publiquement que la création de l'objet (`NewCustomizableObject`) et sa
  compilation ; les classes de nœuds du graphe sont dans ses sources privées. Trois voies à
  mesurer, dans cet ordre : la réflexion sur le graphe (`UEdGraph`, classes de nœuds retrouvées
  par nom, propriétés et broches par réflexion) ; l'inclusion des en-têtes privés du plugin par
  un module d'éditeur du jeu ; le plugin expérimental MutableDataflow. Si aucune ne tient, le lot
  le dit dans la fiche et propose une voie ; aucun asset construit à la main ne reste dans le
  projet. C'est le risque qui peut faire grossir le lot.
- **Mutable est en bêta** depuis la 5.5 : ce qui casse se note avec la version du moteur.
- **Douze influences d'os par sommet** : MetaHuman sous Mutable les exige (réglage
  `BoneInfluences` du plugin) ; le coût à l'écran se mesure avec les quatre héros.
- **La fonction du corps MetaHuman en Python** (`RemoveBodyRig`) manquait en 5.8.0 et était
  annoncée pour le correctif 5.8.2 ; le poste est en 5.8.3, avec les scripts d'exemple du plugin
  (`MetaHumanCharacter/Content/Python/examples/`). Si elle manque encore, le contournement
  s'écrit ici.
- **Les licences Fab** : à vérifier pack par pack, avant achat, par l'auteur.
- **Le poids** d'un personnage sur disque et en mémoire graphique : à mesurer ici, pas à deviner.

## Avancement — 8 octobre 2026

Réalisé en autonomie par l'assistant (consigne de l'auteur : pas de validation visuelle en cours de
lot ; les captures se jugent à la recette). Deux consignes de plus, le même jour : sur Fab,
seulement des assets gratuits sous licence standard, aucun achat ; le contenu livré avec le moteur
reste la première source. Ce lot n'a rien pris sur Fab : tout vient du moteur.

### Ce qui est fait

- **La fiche d'apparence** : `Source/Elements/Rpg/appearances/<id>.json`, schéma
  `appearance.schema.json`, famille `appearances` de `check_rpg_data.py` ; lecteur
  `core::readAppearance` (`Core/Rpg/Appearance`), quatre tests de Core. Deux fiches liées plutôt
  qu'une : la fiche de règles est jouée par les règles, celle d'apparence par le moteur, et un PNJ
  sans règles (le pantin) a quand même une apparence.
- **La description du créateur** : `Source/Elements/Assets/Characters/humanoid.json` (corps,
  clips, sockets, dossier des armes, taille de référence), lecteur `core::readCharacterCreator`,
  trois tests de Core ; `check_orphans.py` y lit les chemins de contenu qu'elle produit.
- **Le créateur Mutable par réflexion** : commandlet `JadgBuildCharacterCreator`
  (`Characters/JadgCreatorGraph`). **Mesuré : la première voie tient.** Les classes de nœuds
  privées se retrouvent par leur chemin, les propriétés s'écrivent par `ImportText` (chemins
  d'objets complets), les broches se relient par le schéma ; compilation synchrone (43
  opérations, 0,1 s), paquet enregistré (150 Kio). Deux pièges relevés : la fonction de
  bibliothèque du plugin synchronise l'explorateur de contenu et casse sans fenêtre (on passe par
  la fabrique) ; le commutateur de composants n'a de catégorie de broches qu'au chargement d'un
  asset (on la lui donne à la création). Rejoué, le commandlet garde l'asset (empreinte de la
  description dans les métadonnées du paquet) ; `-JadgForce` reconstruit par-dessus.
- **Le mannequin du moteur** : `import_mannequin_unreal.py` copie 32 assets (87 Mio) depuis les
  gabarits d'Unreal, au même chemin de contenu, avec empreintes ; six clips (repos, marche,
  attaque, attaque chargée pour l'incantation, coup reçu, mort).
- **L'acteur** : `AJadgWalker::Appearance` ; `JadgAppearance::Apply` pose corps (instance Mutable,
  paramètre `Body` ; le maillage de référence est visible dès le lancement, l'instance le remplace
  quand elle est prête), clips et `ClipKeys`, échelle à la taille, armes aux sockets `hand_r` et
  `hand_l` depuis `Master/Weapons` (26 maîtres importés sur le poste). `PlayOnce` joue un clip de
  combat une fois.
- **Les scènes** : un `characters` de `build_scene_unreal.py` prend `"appearance"` ; les cartes
  d'essai jouent les quatre héros (fiches `heros-*`) et le pantin pour les PNJ.
- **Les suppressions** de D-64 : six scripts, quatre tests, les 21 maîtres PNJ (fichiers, manifeste,
  références, famille `npc`, `Content/Master/Npc`), le contrôle du `.glb` de `check_hd_assets.py` ;
  les lecteurs `.glb` de `reduce_model.py` vivent dans `material_maps.py`, qui en a besoin.
- **Le standard** `personnages-3d.md` est réécrit sur les mesures.
- **Les tests du moteur** `Jadg.Personnages.Createur`, `.Fiche`, `.FicheModifiee`.

### Ce qui se vérifie

Mesuré le 8 octobre 2026 sur le poste de référence (RTX 4060 Ti, Unreal Engine 5.8.3).

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | 644 tests de Core : 643 passés, 1 ignoré (sept nouveaux) |
| `powershell scripts/build.ps1 -Unreal -NoCapture` | la cible d'éditeur se construit (un avertissement du système de construction, pas du code), le mannequin se pose, le créateur se construit, `JadgContentCheck` passe, 13 tests du moteur : 10 passés dans ce passage, les 3 `Jadg.Personnages.*` passés au passage suivant (`-ExecCmds="Automation RunTests Jadg.Personnages"`) après que l'acteur demande la compilation du créateur chargé ; **un passage complet des 13 ensemble reste à rejouer** |
| `powershell scripts/build.ps1 -Unreal` (captures du socle) | les deux captures se prennent (115,6 images par seconde à midi) et **passent** à leur référence (`compare_captures.py`, écart moyen 0,45 et 0,39) ; la première trame est venue 928 s après le lancement (compilation des shaders des plugins ajoutés), et le passage a été arrêté par le système, mémoire basse, juste après la mesure |
| `pytest` | 209 passés (quatorze retirés avec la chaîne, un remplacé) |
| `scripts/check.py` | 17 contrôles, tous verts après la régénération du cahier de test |
| `ruff`, clang-format, `lint_planning`, `lint_docs` | passés |

### Ce qui s'écarte de la fiche

- **MetaHuman n'habille pas les héros.** Mesuré sans fenêtre, avec et sans processeur graphique :
  l'asset se crée, le corps paramétrique se règle (30 contraintes, taille engagée), mais la peau et
  l'assemblage s'arrêtent sur l'assertion `BodyTexture` : le **contenu optionnel** du plugin
  (`MetaHumanCharacter/Content/Optional/`) n'est pas installé sur le poste. Son installation passe
  par le lanceur Epic : **un geste de l'auteur**. Les quatre héros sont donc des corps du mannequin
  (Manny pour Grom et Faelar, Quinn pour Helga et Nessa), et le bloc `metahuman` des fiches attend.
- **Les têtes, les couleurs, la garde-robe** sont lues et pas jouées : le contenu du moteur n'a ni
  tête à part, ni matière de peau paramétrée, ni vêtement. Ce sont des paramètres à ajouter au
  créateur au LOT-1024, avec les corps de race.
- **Le reciblage** n'a pas été nécessaire : corps et clips partagent le squelette du mannequin.
  L'IK Retargeter servira quand un corps d'un autre squelette arrivera (MetaHuman, Fab).
- **L'instant d'impact** est dans la fiche d'apparence (`clips.attack.key`), pas dans un fichier à
  part.
- **Les captures de contrôle des héros et la cadence à quatre** ne sont pas prises : les passages
  `-Parcours` et `-Scene essai-1016-etals -Capture` ont été arrêtés par le système (mémoire basse)
  avant de commencer. **À rejouer** sur le poste, et à juger par l'auteur à la recette.

### Les critères

| Critère | État |
|---|---|
| Les quatre héros se tiennent au repos et marchent sur la carte des étals, suivent le meneur | **tenu sur les tests** (`Jadg.Personnages.Fiche` : corps, clips, échelle ; `Jadg.Exploration.*` : le groupe de quatre, désormais quatre héros, passe) ; **pas vu dans une image** : captures à rejouer |
| Une fiche modifiée change le personnage sans geste dans l'éditeur | **tenu** pour le corps, la taille et les armes (`Jadg.Personnages.FicheModifiee` ; Grom et Helga diffèrent par leur fiche seule) |
| Rejoué, le constructeur redonne les mêmes assets ; `check_orphans.py` passe | **tenu** : mannequin par empreintes, créateur gardé si la description n'a pas changé ; `check_orphans.py` vert |
| La régénération du graphe Mutable depuis le texte est mesurée | **tenu** : faisable, par réflexion (voie 1) ; détail au standard §3 |
| La cadence avec les quatre héros à l'écran, à midi et à 22 h | **non tenu** : passage arrêté avant la mesure, à rejouer |
| Les tests de Core et `Jadg.Personnages.*` passent | **tenu** (voir le tableau ; un passage complet des 13 tests ensemble à rejouer) |

### Ce qui reste au lot

- Rejouer `scripts/build.ps1 -Unreal`, `-Unreal -Parcours` et `-Unreal -Scene essai-1016-etals
  -Capture` sur le poste, verser les captures et les mesures dans `annexes/LOT-1015/captures/`.
- Le contenu optionnel de MetaHuman, puis les héros en MetaHuman (fiches : `body: metahuman`, bloc
  `metahuman`) — ou l'auteur décide que le mannequin suffit à la 0.0.3.
- L'orientation des armes dans la main (un décalage par pièce dans la description), à juger sur
  les captures.
- Le retour au repos après un clip joué une fois (`PlayOnce`) : avec le tour de combat, LOT-1017.
- Le poids en mémoire graphique de huit personnages : LOT-1024.
