+++
id = "LOT-1014"
titre = "Le socle : Core en module, données, build, tests, CI"
version = "0.0.3"
filiere = "moteur"
statut = "a-faire"
taille = "L"
resume = "Le nouveau dépôt existe (D-58), reçoit par passation ce que la version garde, construit Core comme module du projet Unreal, lit les données de contenu, se teste et se contrôle en ligne de commande : tout lot suivant s'y pose."
prerequis = ["LOT-1012"]
livrables = [
  "Le **nouveau dépôt**, créé par l'auteur (D-58), avec sa passation : `Source/Core` (sans copie ni réécriture), `Source/Elements` (données de contenu, cartes peintes, kits verrouillés), `Planning/`, `Documentation/` (relue : ce qui décrit le moteur maison part en archive), `scripts/` (assets, checks, docs, release ; rien de Qt), la licence, le CHANGELOG repris à la `0.0.3` ; une page `PASSATION.md` qui dit ce qui est venu, ce qui est resté dans l'ancien dépôt et pourquoi.",
  "L'ancien dépôt passé en **privé, sans CI**, par l'auteur, avec un README de tête qui renvoie au nouveau.",
  "`Source/Unreal/` : le projet du jeu (`JustAnotherRpgGame.uproject`), ses modules `Core` (la bibliothèque des règles, compilée depuis `Source/Core` sans copie), `Game` et `GameEditor` ; la version du moteur épinglée dans `scripts/ci/check_tool_pins.py`.",
  "Le chargement des données de contenu — classes, capacités, rencontres, dialogues, quêtes, atlas, lieux — depuis `Source/Elements`, par les lecteurs de Core, sans conversion en `DataTable` binaire.",
  "Les options du jeu (définition, échelle de rendu, qualité des ombres, volume) en fichier texte, lues au lancement.",
  "`scripts/build.ps1` étendu : `-Unreal` construit le projet, lance les tests d'automatisation et produit une capture, sans fenêtre ; sort en 1 à la première erreur.",
  "Les tests de Core rebranchés tels quels (GoogleTest hors du moteur) ; les premiers tests d'automatisation du moteur (ouverture d'une carte vide, chargement d'un personnage, une capture comparée à tolérance).",
  "La CI **refaite à neuf** dans le nouveau dépôt (D-58), sans reprendre l'actuelle : les lints Python, les contrôles et les tests de Core sur les runners hébergés ; la construction Unreal, ses tests et ses captures sur le poste de référence, la nuit ; Git LFS pour les sorties binaires (D-52). Ce qui revient de l'ancienne CI (lints, contrôles, CHANGELOG, notes de version) se réécrit un par un, et chaque reprise se justifie dans la fiche.",
  "`check_orphans.py` et `check_binary_files.py` étendus au nouveau projet : un `.uasset` non régénéré par un script du dépôt est une erreur.",
]
criteres = [
  "`scripts/build.ps1 -Unreal` construit le projet et passe ses tests sur le poste de référence et sur le runner auto-hébergé, sans fenêtre.",
  "Les tests de Core passent sans modification de leur code, hors chemins.",
  "Une partie se crée depuis les données de contenu : le groupe préformé de D-28 a ses quatre fiches, valeur pour valeur, lues dans le moteur.",
  "Aucun fichier binaire suivi par Git hors LFS n'est produit par ce lot ; `check_binary_files.py` passe.",
  "Le nouveau dépôt ne contient aucune ligne de Qt, de QML ni de QRhi, et `check_orphans.py` y passe dès ce lot ; l'ancien dépôt est privé et se joue toujours tel quel.",
]
+++

## Pourquoi

L'auteur veut une passation et une mise au propre (D-58) : un dépôt neuf qui ne porte que ce que
le nouveau moteur garde, sans l'histoire de Qt ni une CI à démêler. Un portage sans socle se fait deux fois. Ce lot pose l'endroit où tout le reste s'écrit : le projet,
le module Core, les données, la construction sans fenêtre et la CI. Il ne rend rien de nouveau à
l'écran ; il rend tout le reste possible et vérifiable.

## Périmètre

Dedans : le projet, le module Core, le chargement des données, le build, les tests, la CI, le
stockage des sorties binaires.

Dehors, nommément :

- tout ce qui s'affiche : la caméra (LOT-1016), l'interface (LOT-1020) ;
- les personnages (LOT-1015) et les cartes (LOT-1018) ;
- le gel de l'ancien dépôt, qui reste joué jusqu'à la recette (LOT-1023) ;
- la reprise de l'ancienne CI telle quelle : elle se refait, elle ne se copie pas.

## Conception

- **Core n'est pas copié.** Le module Unreal `Core` compile les sources de `Source/Core` en place
  par son `Build.cs` ; GoogleTest continue de les tester hors du moteur. Si une règle du moteur
  (allocation, exceptions) force une modification de Core, elle s'écrit dans Core et vaut pour les
  deux constructions tant que l'ancienne existe.
- **Les données restent en JSON** et se lisent par les lecteurs de Core (nlohmann) ; aucune
  `DataTable` ni `.uasset` de données. Un lecteur Unreal n'est écrit que là où le moteur l'impose
  (textures, maillages, sons), et il est régénérable.
- **Git LFS** reçoit les `.uasset` et `.umap` régénérés, avec une règle : chaque fichier LFS est
  cité par le script qui le produit, et `check_orphans.py` le vérifie. Les kits publiés en release
  (`publish_asset_kit.py`) continuent de porter les maillages et textures.
- **La construction du moteur** se fait sur le poste de référence la nuit, par un runner
  auto-hébergé du nouveau dépôt ; le moteur y est installé une fois, sur D:. Les runners hébergés
  ne construisent pas Unreal (R-16).
- **La passation** est un script (`scripts/release/passation.py`, dans l'ancien dépôt) qui copie
  les dossiers gardés et écrit `PASSATION.md` ; relancé, il redonne le même contenu. L'histoire
  Git ne vient pas : le nouveau dépôt commence à la `0.0.3`, et l'ancien reste lisible en privé.
- **Les captures de test** se comparent à tolérance par blocs, comme `test_hd_mockup_render` le
  faisait ; l'identité au pixel n'a plus de sens sous Lumen et un anticrénelage temporel.

## Risques et questions ouvertes

- **Les exceptions et la STL.** Core utilise des exceptions et des conteneurs standard ; Unreal
  compile sans exceptions par défaut. Le module Core les active pour lui seul ; à vérifier au
  premier build.
- **Le temps de compilation.** Un module Core de 198 fichiers se recompile à chaque changement de
  règle : la compilation unitaire par module le borne ; mesuré ici.
- **Le runner.** S'il n'y a qu'un poste, la nightly et le jeu de l'auteur se partagent la machine.
