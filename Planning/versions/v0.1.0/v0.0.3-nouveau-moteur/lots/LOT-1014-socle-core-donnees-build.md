+++
id = "LOT-1014"
titre = "Le socle : Core en module, données, build, tests, CI"
version = "0.0.3"
filiere = "moteur"
statut = "livre"
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

## Avancement — 8 octobre 2026

Le lot est **en cours**. Le socle technique tourne de bout en bout, et ce qui ne servait que le
moteur maison est supprimé ; restent les spécifications et le cahier de tests. Ce qui était fait avant cette reprise — le dépôt, la
passation, Core dans le module du jeu, le commandlet, la CI hébergée — est dans
[`PASSATION.md`](../../../../../PASSATION.md).

### La commande

    powershell scripts/build.ps1 -Unreal

enchaîne cinq temps, sans fenêtre, et sort en 1 à la première erreur. Mesuré le 8 octobre 2026 sur
le poste de référence (RTX 4060 Ti, Unreal Engine 5.8.3) : **133 s, code 0**.

| Temps | Ce qu'il fait | Relevé |
|---|---|---|
| 1 | UnrealBuildTool, cible d'éditeur | 20 s sans changement de code, 40 s pour seize unités recompilées, 0 avertissement |
| 2 | commandlet `JadgContentCheck` | 22 espèces, 13 historiques, 4 classes, 4 fiches, 0 erreur |
| 3 | tests d'automatisation `Jadg.*`, sans processeur graphique | 3 passés, 0 avertissement ; le script relit le rapport et refuse un rapport sans test passé |
| 4 | carte de la scène du socle, par `build_scene_unreal.py` | repère mesuré, 1 objet, 1 cadrage |
| 5 | captures hors écran à midi et à 22 h, comparées à leur référence | pire bloc à 0,66 et 0,88 niveau de sa référence, tolérance 8 |

Le script refuse un moteur d'une autre version que celle que `ci.yml` épingle
(`UNREAL_ENGINE_VERSION`, lue contre `Engine/Build/Build.version`) ; `check_tool_pins.py` tient
l'`IncludeOrderVersion` des deux cibles sur la même. `-NoCapture` saute les temps 4 et 5,
`-Scene porte-1012 -Capture` rejoue la porte, `-UpdateReference` réécrit une référence.

### Les tests du moteur

`Source/JustAnotherRpgGame/Tests/JadgSocleTests.cpp`, trois tests :

- `Jadg.Socle.CarteVide` : l'instance du jeu crée un monde vide, le mode de jeu des cartes du dépôt
  le fait jouer, son pion est la caméra libre, un cadrage s'y crée et commence à jouer ;
- `Jadg.Socle.GroupePreforme` : les quatre fiches de D-28, lues dans le moteur par les lecteurs de
  Core — espèce, historique, six caractéristiques, points de vie, classe d'armure (avec
  l'équipement), vitesse —, aux valeurs des pages 195, 199, 203 et 207 ;
- `Jadg.Socle.Options` : les options se lisent sans erreur, et trois valeurs que le fichier d'usine
  ne porte pas atteignent `r.ScreenPercentage`, `sg.ShadowQuality` et le volume de l'application.

Les tests de Core hors moteur : **634 tests, 100 % passés**, 1 ignoré (sans dossier de modèles),
38 s ; cinq de plus qu'au 7 octobre, ceux des options.

### La capture comparée

Une référence n'est pas une capture mais une **image de blocs** : un pixel par bloc de 24 pixels de
côté, sa couleur moyenne (80 × 45 pour 1920 × 1080 ; 2,4 Ko par capture, contre 2 Mo). Une capture
passe si la part de ses blocs qui s'écartent de plus de `tolerance` niveaux ne dépasse pas
`outliers` (`scripts/checks/compare_captures.py`, dix tests). Relevé sur six captures de la scène
du socle : d'un lancement à l'autre le pire bloc s'écarte de **1,03 niveau sur 255** ; la toute
première capture, la pièce tout juste importée, s'écartait des suivantes de 3,49. La tolérance est
à **8**, la part admise à **0,25 %** ; les deux sont écrites avec leur mesure dans
`Source/Test/Fixtures/Captures/socle-1014/reference.json`.

La scène du socle (`Source/Elements/Scenes/socle-1014.json`) ne lit **aucun kit** : son seul
maillage est un bloc des données d'essai suivies par Git, dissymétrique sur ses trois axes
(`build_mesh_fixture.py`), sur lequel le changement de repère se mesure. Un poste qui n'a que le
dépôt la construit. Ses captures entières restent dans `Saved/Captures/socle-1014/` : la commande
les refait, elles ne pèsent pas dans le dépôt.

### Les options du jeu

`Source/Elements/Options/options.json` : définition et plein écran, échelle de rendu, qualité des
ombres, volume. `core::loadGameOptions` (`Core/Data/GameOptions`) le lit **sur une base** : le
fichier d'usine d'abord, puis celui du poste (`Saved/Options/options.json`) s'il existe. Un champ
hors bornes, du mauvais type ou inconnu est une erreur nommée et garde la valeur de la base ; les
autres se lisent. L'instance du jeu (`UJadgGameInstance`, `Bridge/JadgOptions`) applique au
lancement : `r.ScreenPercentage`, `sg.ShadowQuality`, le volume de l'application, et la définition
de la fenêtre avant sa création — sauf dans l'éditeur, dans un commandlet, ou si la ligne de
commande en donne une (les captures).

Les valeurs d'usine sont celles du moteur et de la capture de référence (1920 × 1080, 100 %,
palier 3, volume 100) : appliquées, elles ne changent pas l'image. Les **bornes** de l'échelle de
rendu (50 à 200 %) sont un choix de ce lot, à juger par l'auteur ; celles des ombres (0 à 4) sont
les paliers du moteur.

### Les contrôles

- **`check_orphans.py`** lit `Content/` : un `.uasset` ou un `.umap` dont aucun script du dépôt ni
  aucune description de scène ne cite le chemin `/Game/…` (ou un dossier qui le contient) est une
  erreur, comme tout autre fichier trouvé là. Il ne connaît plus les arbres de l'ancien dépôt ni
  le `.qml`. Sur le poste, kits installés : **0 orphelin**, 3,3 Go de `Content/` compris. En CI il
  tourne avec `--sans-kits`, les images des kits n'étant pas sur le runner.
- **`Source/Elements/Assets/awaiting.json`** : cinq polices, le manifeste des illustrations de l'interface et l'apparence d'Arenarea sont venus
  par passation et n'ont plus de lecteur — l'ancien moteur les chargeait par `Tokens.qml` et par
  son rendu. Plutôt que de les supprimer ou de les laisser passer pour mortes, la liste nomme le
  lot qui les attend (LOT-1020, LOT-1018) ; une entrée dont le lot est livré devient une erreur.
- **`check_binary_files.py`** : une sortie du moteur suivie hors de Git LFS est refusée, quelle que
  soit sa taille ; un fichier en LFS n'est plus pris pour un binaire non déclaré quand ses octets
  sont sur le poste.
- **Le numéro de version** a une seule source, `VERSION.txt`, lue par `JustAnotherRpgGame.Build.cs`
  et par le `CMakeLists.txt` des tests de Core.

### Rien d'hérité (D-59)

L'auteur, le 8 octobre : « supprime tout ce qui est inutile, on n'en garde pas de legacy, j'ai
séparé les git pour cela ». Sont donc **supprimés**, et non archivés ; tous restent dans l'ancien
dépôt :

- **neuf scripts** : `receive_ui_assets.py` (importait `check_ui_assets`, resté là-bas, et
  réécrivait `Artwork.qml`) ; `check_assets_brief.py` (lisait `Tokens.qml`) ; `seed_translations.py`
  (migration vers Qt Linguist, faite au LOT-86) ; `package_release.ps1`, `smoke_test_release.ps1` et
  `write_sha256sums.ps1` (empaquetage par `windeployqt` ; la publication se refait au LOT-1023) ;
  `clang_tidy_sarif.py`, `merge_sarif.py`, `ci_summary.py` (jobs de l'ancienne CI, non repris) ;
- **huit guides du moteur maison** : `guide-ihm-qt.md`, `guide-rendu.md`, `guide-editeur.md`,
  `guide-ecrans.md`, `guide-design-ihm.md`, `guide-audio.md`, `guide-entrees.md`,
  `guide-conception-qds.md` ; avec eux `guide-outils.md` (la chaîne CMake et Qt, l'ancienne CI,
  l'ancienne publication) et `guide-outils-developpement.md` (le menu de développement du jeu Qt) ;
- **le Manuel** (`Guide/Manuel/`, cinq pages : jouer au jeu Qt, se servir du LevelEditor) et
  `Documentation/outils/capture_screens.py`, qui photographiait ces deux binaires ;
- **vingt-cinq captures et figures** du guide que plus aucune page ne montrait.

Les liens vers ces pages sont retirés des pages qui restent (le texte du lien demeure) ; les index
du guide renvoient à `README.md` et `CONTRIBUTING.md` pour la construction et la CI. Le son n'a pas
de lot dans la `0.0.3` : l'auteur l'ajoutera plus tard.

**Les cinq spécifications restent** (`architecture.md`, `controles.md`, `rendu-technique.md`,
`interface-ihm.md`, `editeur-niveaux.md`) : elles sont le lieu de déclaration des exigences `EX-…`,
que `lint_exigences.py` ne lit que sous `Documentation/Specification`. Les retirer rendrait
orphelines 175 exigences que le code et les tests de Core citent encore : chacune se réécrit ou se
retire dans les règles, exigence par exigence, avec le lot qui reprend son sujet.

### Ce qui s'écarte de la fiche

- **Core n'est pas un module à part** et il n'y a pas de `Source/Unreal/` : le projet est à la
  racine, Core dans le module du jeu (`PASSATION.md`, « Core dans le module du jeu »).
- **La passation n'a pas été un script.** `scripts/release/passation.py` n'existe pas dans
  l'ancien dépôt : la copie s'est faite à la main le 7 octobre, et `PASSATION.md` en est le
  relevé. Elle ne se rejoue pas.
- **« Chargement d'un personnage »** est ici le chargement de ses **fiches** par Core. Un
  personnage en maillage lié — squelette, clips, matière — est le LOT-1015.
- **La carte vide du test** est un monde créé par l'instance du jeu, pas un `.umap` : les tests
  d'automatisation tournent sans processeur graphique et sans `Content/`. Le `.umap` du socle est
  ouvert par le temps 5, qui le capture.
- **La capture ne se compare pas dans le cadre d'automatisation du moteur** mais par un script
  Python, après le jeu lancé hors écran : c'est l'image du joueur, et la comparaison se teste
  sans moteur.
- **Aucun `.uasset` n'est en Git LFS** : `Content/` n'est pas suivi (D-60).

### Les critères

| Critère | État |
|---|---|
| `build.ps1 -Unreal` construit et passe ses tests, sans fenêtre | **tenu sur le poste de référence** (133 s, code 0) ; **pas de runner auto-hébergé**, par décision (D-61) |
| Les tests de Core passent sans modification de leur code | tenu pour 634 tests ; `test_dialogue.cpp` n'est toujours pas compilé et un balayage reste filtré, tous deux parce qu'ils lisent `Source/HMI` (LOT-1020, LOT-1016) |
| Une partie se crée depuis les données ; les quatre fiches de D-28, valeur pour valeur, dans le moteur | **les quatre fiches : tenu** (`Jadg.Socle.GroupePreforme`). Aucun écran ni aucun flux « nouvelle partie » n'existe dans le moteur : ce lot ne crée pas de partie |
| Aucun binaire suivi hors LFS ; `check_binary_files.py` passe | tenu : ce lot ajoute deux images de blocs de 2,4 Ko et un `.glb` d'essai de 18 Ko, de familles déclarées |
| Aucune ligne de Qt, de QML ni de QRhi ; `check_orphans.py` passe ; l'ancien dépôt est privé | `check_orphans.py` **passe**. **« Aucune ligne de Qt » n'est pas tenu** : voir ci-dessous |

Ce qui cite encore Qt, hors `Planning/` (l'histoire) :

- **`check_translations.py`, son test et `Localization/jadg_en.ts`** : le catalogue des
  traductions anglaises est au format Qt Linguist. Ce sont des données du jeu, pas un héritage à
  jeter ; leur format se décide avec l'interface (LOT-1020) ;
- **les commentaires de Core** (« sans Qt ni GPU », une douzaine d'en-têtes) et
  `test_iso_projection.cpp`, qui compare une projection à l'ancienne scène QML : Core est venu
  sans une ligne modifiée. La projection disparaît avec la grille (LOT-1017) ;
- **les cinq spécifications**, des pages de guide qui nomment encore `hmi::…`, et la **recette
  manuelle** du cahier de tests, écrite pour l'ancien jeu : elle se réécrit à la recette
  (LOT-1023).

Le **cahier de tests** est réengendré : 647 cas, 14 pages, tous de `Core` ; les douze pages qui
portaient sur des tests restés dans l'ancien dépôt ont disparu avec lui. 42 liens de la
documentation suivent Core à son nouveau chemin, six vers ce qui n'est pas dans ce dépôt sont
retirés. `lint_planning`, `lint_docs` et `generate_cahier_test --check` sont verts et **dans la CI**.

### Les décisions du 8 octobre

- **D-60 — `Content/` reste sur le poste.** 3,3 Go de `.uasset` et de `.umap`, tous régénérables,
  que le quota d'un compte gratuit ne tient pas en Git LFS. `Content/` est ignoré ; rien ne
  s'y télécharge, tout s'y reconstruit. Pour la scène du socle, le dépôt suffit ; pour la porte,
  il faut les kits et les maîtres sur le poste. Aucune sauvegarde hors de Git n'est mise en place
  par ce lot : les maîtres (2,7 Go de `.glb`, la seule pièce qui ne se régénère pas) sont dans le
  dossier de l'auteur, hors du dépôt.
- **D-61 — pas de runner auto-hébergé pour l'instant.** Le dépôt est public et il n'y a qu'un
  poste : un runner y tournerait en service pour rejouer ce que `build.ps1 -Unreal` vérifie déjà
  avant chaque PR, en 133 s. `unreal.yml` reste écrit, dormant. Le critère « sur le runner
  auto-hébergé » **n'est donc pas tenu, par décision**.
- **D-62 — les kits se publient sur ce dépôt à la `0.0.3`** (LOT-1023). D'ici là `fetch_assets.py`,
  `check_map_assets.py`, `check_hd_assets.py` et la part « assets » de `check_orphans.py` ne
  tournent que sur un poste qui a déjà les kits.
- **`THIRD-PARTY-NOTICES.md`** dit que le dépôt est public, et nomme Unreal Engine à la place de
  Qt ; les mentions que son contrat demande à un produit distribué se relisent au premier paquet
  (LOT-1023).

### Ce qui reste au lot

- les cinq spécifications, à reprendre exigence par exigence ;
- `publish_asset_kit.py`
  nomme encore `check_ui_assets.py`, resté dans l'ancien dépôt, pour le kit de l'interface ;
- le commandlet et les tests du moteur n'ont pas été lancés sur un poste **sans** `Content/` : la
  carte de démarrage de l'éditeur (`Porte1012`) y manque, et ce que le moteur en dit n'est pas
  relevé ;
- la publication d'une version, la référence Doxygen et la page qualité du site, que le LOT-1023
  reprend ; les répertoires de `Source/Elements` à embarquer dans un paquet.

## Clôture — 8 octobre 2026

L'auteur clôt le lot le 8 octobre 2026 : « le lot 1014 est livrée ». La fiche passe à `livre` sur
cette décision, PR #4. Il n'a pas écrit d'autre verdict que celui-là.

Le lot est clos **sans que tous ses critères soient tenus** ; ce qui manque est écrit plus haut
(« Les critères », « Ce qui reste au lot ») et passe aux lots qui le reprennent :

- **Le runner auto-hébergé** n'existe pas, par décision (D-61) : la construction du moteur, ses
  tests et ses captures se vérifient sur le poste avant chaque PR.
- **« Aucune ligne de Qt »** n'est pas tenu : le catalogue des traductions anglaises reste au
  format Qt Linguist (LOT-1020), les commentaires de Core et `test_iso_projection.cpp` partent
  avec la grille (LOT-1017).
- **Les cinq spécifications** et la recette manuelle du cahier de tests décrivent encore l'ancien
  jeu : LOT-1023.
- **`test_dialogue.cpp`** n'est toujours pas compilé (LOT-1020) ; le balayage des familles
  d'entités est revenu au LOT-1016.
- **Aucune partie ne se crée** depuis un écran : LOT-1020.
- La publication d'une version, la référence Doxygen, la page qualité du site et les répertoires
  à embarquer dans un paquet : LOT-1023.
