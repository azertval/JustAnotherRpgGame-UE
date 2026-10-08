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
