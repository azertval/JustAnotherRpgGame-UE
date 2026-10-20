# JustAnotherRpgGame

RPG en **C++20** sur **Unreal Engine 5.8** : exploration en temps réel sous une caméra libre, et
rencontres en **combat tactique au tour par tour, en distance**, régi par un système **d20** maison.

> **Fan game non commercial.** Ce jeu gratuit s'inspire des univers de *Dungeons & Dragons* et de
> *Tanares*, sans affiliation ni approbation de leurs ayants droit (Wizards of the Coast, Dragori
> Games). Voir [LICENSE](LICENSE) et [LICENSE-CONTENT](LICENSE-CONTENT).

**Version courante : `0.0.3` — le nouveau moteur**, en cours. Le jeu quitte son moteur maison
(Qt QRhi) pour Unreal Engine 5 ([D-48](Planning/vision/decisions.md), 7 octobre 2026) et change de
dépôt ([D-58](Planning/vision/decisions.md)) : ce dépôt reçoit, par passation, ce que la version
garde — la bibliothèque des règles, les données de contenu, la planification, les scripts. Ce qui
est venu, ce qui est resté et pourquoi : [PASSATION.md](PASSATION.md). Le plan de la version :
[`Planning/versions/v0.1.0/v0.0.3-nouveau-moteur/`](Planning/versions/v0.1.0/v0.0.3-nouveau-moteur/README.md).

## Documentation

Le site du projet est publié à chaque merge sur `main` : **<https://azertval.github.io/JustAnotherRpgGame-UE/>**

| Partie | La question | En ligne | Dans le dépôt |
|---|---|---|---|
| Guide | **Comment** ça marche, et comment s'en servir ? | [Guide](https://azertval.github.io/JustAnotherRpgGame-UE/Guide/index.html) | [`Documentation/Guide/`](Documentation/Guide/README.md) |
| Spécifications | **Quoi**, et **pourquoi** ? Les exigences `EX-…` | [Spécifications](https://azertval.github.io/JustAnotherRpgGame-UE/Specification/index.html) | [`Documentation/Specification/`](Documentation/Specification/README.md) |
| Cahier de test | Qu'est-ce qui est **vérifié** ? | [Cahier de test](https://azertval.github.io/JustAnotherRpgGame-UE/CahierTest/index.html) | [`Documentation/CahierTest/`](Documentation/CahierTest/README.md) |
| Métiers de Tanares | Quels métiers, quelles populations, et pourquoi ces choix ? | [Étude](https://azertval.github.io/JustAnotherRpgGame-UE/Metiers/index.html) · [Explorateur interactif](https://azertval.github.io/JustAnotherRpgGame-UE/Metiers/explorateur.html) | [`Documentation/Metiers/`](Documentation/Metiers/README.md) |
| Planification | **Quand**, et dans quel ordre ? Versions, lots, décisions | [Planification](https://azertval.github.io/JustAnotherRpgGame-UE/planning/index.html) | [`Planning/`](Planning/README.md) |

Le guide, les spécifications et le cahier de test décrivent encore, pour partie, le moteur maison :
leur relecture est au [LOT-1014](Planning/versions/v0.1.0/v0.0.3-nouveau-moteur/lots/LOT-1014-socle-core-donnees-build.md)
(voir [PASSATION.md](PASSATION.md)). La référence du code (Doxygen) et la page qualité ne sont pas
encore republiées. Contribuer : [CONTRIBUTING.md](CONTRIBUTING.md).

## Les règles de la version

1. **Tout ce qui s'écrit est du texte** ([D-52](Planning/vision/decisions.md)) : C++, JSON de
   contenu, scripts Python d'éditeur, descriptions de carte. Un `.umap` ou un `.uasset` est une
   sortie régénérée par script, en Git LFS. Pas de logique en Blueprint.
2. **`Core` reste la bibliothèque des règles**, sans une ligne du moteur : elle se compile dans le
   module du jeu et, séparément, avec GoogleTest, sans Unreal.
3. **Un lot qui remplace un fichier le supprime** dans sa propre PR (D-32).

## Arborescence

| Dossier | Contenu |
|---|---|
| `JustAnotherRpgGame.uproject`, `Config/` | Le projet du moteur (UE 5.8, module `JustAnotherRpgGame`) |
| `Source/JustAnotherRpgGame/Core/` | Les règles : d20, classes, capacités, sorts, quêtes, dialogues, monde. Inclusions en `"Core/<Module>/<Fichier>.h"` |
| `Source/JustAnotherRpgGame/Bridge/`, `Commandlets/` | Ce que le moteur impose : chemins, journal, le commandlet de contrôle du contenu |
| `Source/ThirdParty/nlohmann/` | nlohmann/json 3.11.3, en-tête unique |
| `Source/Elements/` | Les données de contenu en JSON : `Rpg/`, `World/`, `Levels/`, `Maps/`, `Localization/`. Les kits d'assets s'installent par `scripts/fetch_assets.py` |
| `Source/Elements/Assets/Master/` | Les maillages Meshy **au maître** (D-53) : `manifest.json` est suivi, avec la fiche de chaque pièce, les `.glb` (2,7 Go) non. `import_scenery_unreal.py` les installe en Nanite sous `Content/Master/`, avec leur matière complète (LOT-1019) |
| `Source/Test/Unit/Core/` | Les tests GoogleTest de Core, hors moteur (`CMakeLists.txt` à la racine) |
| `Planning/` | Vision, décisions, versions, lots, standards |
| `Documentation/` | Spécifications, guides, cahier de test (à relire : voir la passation) |
| `scripts/` | Assets, contrôles, documentation, release |

## Construire

```powershell
# Les tests de Core hors du moteur (CMake + Ninja + GoogleTest, environnement MSVC x64 établi par le script)
pwsh scripts/build.ps1

# Le projet Unreal : la cible d'éditeur, le contenu, les tests du moteur, une capture comparée — sans fenêtre
pwsh scripts/build.ps1 -Unreal
```

Le second enchaîne cinq temps et sort en 1 à la première erreur :

1. `Build.bat JustAnotherRpgGameEditor Win64 Development` ;
2. le commandlet `JadgContentCheck`, qui lit les catalogues de `Source/Elements/Rpg` par les
   lecteurs de Core et construit les fiches du groupe préformé ;
3. les tests d'automatisation du moteur (`Automation RunTests Jadg`, sans processeur graphique) :
   une carte vide s'ouvre sous l'instance et le mode de jeu, les quatre fiches du groupe préformé
   ont les valeurs de leur page, les options du jeu atteignent le moteur ;
4. les cartes contrôlées (`scripts/maps/jadg_map.py --check`), et l'aller-retour d'une carte entre
   son texte et l'éditeur (`scripts/maps/check_level_roundtrip.py`) ;
5. le niveau du socle, reconstruit par script (`scripts/maps/build_level.py`) depuis sa description
   `Source/Test/Fixtures/Exploration/Levels/socle-1014.json` — il ne lit aucun kit d'assets ;
6. ses captures à midi et à 22 h, prises hors écran, puis comparées à tolérance et par blocs à
   leur référence (`Source/Test/Fixtures/Captures/socle-1014/`).

`-NoCapture` saute les temps 5 et 6 sur un poste sans processeur graphique ; `-Map central-empire/capital/martpart
-Capture` construit et capture le niveau de la porte à la place ; `-UpdateReference` réécrit la
référence d'une image qui a changé exprès. Le moteur doit être la version que `ci.yml` épingle
(`UNREAL_ENGINE_VERSION`).

Les **options du jeu** — définition, échelle de rendu, qualité des ombres, volume — sont un fichier
texte, `Source/Elements/Options/options.json`, lu au lancement ; un poste peut porter les siennes
dans `Saved/Options/options.json`. Le **numéro de version** a une seule source, `VERSION.txt`.

## L’Arena of Fate

Les anciennes scènes de comparaison sont retirées. Leurs primitives de géométrie
réutilisées vivent dans `scripts/assetsGeneration/arena_geometry.py` et
`arena_sculpted_geometry.py` ; elles servent à l’arène complète et aux quartiers.

La reconstruction complète se régénère par `scripts/maps/review_arena_fate_modern.ps1`.
`-Generate` régénère l’architecture, le mobilier et l’ambiance ; `-Walk` ajoute le contrôle des
liaisons physiques entre niveaux. L’ancienne carte est archivée localement avant remplacement.
Les rapports vont dans `Saved/Jadg/arena-fate-modern/` et la galerie à midi et à 22 h dans
`Saved/Captures/arena-fate-modern/index.html`. La validation du témoin ne vaut pas recette de
cette reconstruction ; les contrôles moteur et les captures doivent être examinés. La foule
est reportée après le décor, conformément au choix de l’auteur.

La propagation du témoin impérial, autorisée le 10 octobre 2026, comporte 1826 éléments :
1468 pièces d’architecture, 317 accessoires et 41 statues, emblèmes et sculptures
réemployés. Les loges, les reliefs des gradins, les arcades aux proportions réelles, les nervures,
les fonds de joints fermés et les matières des pièces de service reprennent le témoin validé.
Le seuil sud aux lions, les galeries et les mécanismes bas du velum complètent cette passe.
Les sept niveaux physiques vont des catacombes à −12 m à la terrasse à 46,8 m.
Les trois sols annulaires gardent leur géométrie visuelle complète ; leurs collisions
architecturales fermées reprennent les mêmes contours à 192 cordes, hauteurs et trémies.
Les données de gameplay, de groupe et d’étages restent strictement identiques à la carte
précédente ; les 235 positions de contrôle et les 66 points du parcours restent reliés.
Le groupe a parcouru le trajet réel dans les deux sens : **132/132 arrêts réussis**,
depuis les catacombes jusqu’à la terrasse, sans téléportation.
Les 26 vues à midi et à 22 h et le relevé sans foule sont dans `Saved/Captures/arena-fate-modern/` :
86.3 images/s à midi et 82.5 à 22 h en 1080p sur NVIDIA GeForce RTX 4060 Ti, hors chargement.
Ces mesures courtes portent sur la scène de mesure, pas sur chaque cadrage ni sur le combat.
La validation du témoin reste distincte de la revue finale de cette arène complète.
La commande habituelle `build_level.py -JadgMap=central-empire/capital/arenarea/arena-of-fate`
utilise aussi ce constructeur pour conserver les matières peintes, la coupe des occultants et
l’ambiance. Le contrôleur de navigation et de visibilité est sauvegardé dans le niveau persistant ;
les accessoires suivent l’effacement de leur sol sans perdre leurs collisions ni leurs ombres.
L’archive locale reste une sauvegarde ; les reconstructions relisent le gameplay
de la carte courante. Six anciens points d’arrivée sont conservés pour compatibilité : le
contrôle de carte les signale sans portail associé, puisque leurs escaliers sont désormais physiques.

## Les quartiers d’Arenarea et Martpart

La construction des quartiers, complétée par le relief autorisé le 11 octobre 2026,
se régénère par :

```powershell
pwsh scripts/maps/review_capital_districts.ps1 -Generate -Compile -Walk
```

`-District arenarea` ou `-District martpart` limite la revue à un quartier.
Les générateurs `build_arenarea_district.py` et `build_martpart_district.py` assemblent
des pièces simples dans Blender ; `scripts/assetsGeneration/district_foliage.py`
construit leurs arbres et haies à partir de branches et de petites masses feuillues.
Les maîtres visibles restent entiers. Les deux quartiers leur associent des volumes
physiques construits depuis les mêmes dimensions : ouvertures, marches, quais,
toitures, troncs et bacs. `--collision-only` sur le générateur d’Arenarea renouvelle ces volumes sans
réexporter les modèles visibles ; la génération complète les inclut également.
`build_capital_districts.py` les installe avec les
matières peintes de l’Arena of Fate et `district_atmosphere.py` ajoute eau, vent,
feux, fumée, ambiances locales et passants animés. `-SkipBuild` réutilise la carte
installée si les empreintes des sources correspondent ; `-SkipCapture` omet seulement
les images et la mesure graphique. Le cache de cette revue se crée dans
`Saved/DerivedDataCache/` sur le disque du projet, sans déplacer le cache existant.

Les identités, dialogues, conditions de quête et destinations des portails sont
comparés à la carte courante avant remplacement. Les anciennes descriptions et
cartes natives restent récupérables dans `Saved/Jadg/districts/`. La construction
refuse de remplacer une carte dont les lieux de visite ne sont pas reliés par la
navigation. `-Walk` fait ensuite marcher le groupe sur le parcours aller-retour.
La reprise du 11 octobre 2026 ajoute un relief partagé par les sols, les accès et
les personnages : `scripts/maps/district_surface.py`, les données `groundHeightfield`
et les emprises locales `storeyRegions`. Arenarea s’étage de 0 à 12 m et Martpart
de 0 à 8,2 m. Les altitudes ne remplacent pas les étages de gameplay : l’étage
du Cloaked Brewer Pub conserve son accès par escalier. Les chaussées suivent
les triangles du terrain ; les bases des gradins compensent localement la pente.
Le dernier lot d’appuis du mobilier de Martpart est préparé, mais son import
physique reste refusé par le contrôle décrit ci-dessous.
La révision précédente complète est conservée sous
`Saved/Jadg/districts/relief-20261011/before/` ; les résultats du 10 octobre
ne valident pas les quartiers remaniés.
La galerie se trouve dans `Saved/Captures/districts/index.html`, avec les vues de
jour et de nuit ; les rapports détaillés sont dans `Saved/Jadg/districts/`.
Chaque revue conserve les empreintes de sa carte et de son manifeste : la galerie
écarte les parcours et captures d'une variante précédente. `collision.json` et
`memory.json` gardent les contrôles de couverture physique et de mémoire.
Les modèles des passants sont provisoirement Manny et Quinn : le projet contient
leurs animations, mais pas encore la garde-robe civile définitive.

État arrêté le 11 octobre 2026 à la demande de l’auteur : **la validation complète
n’est pas acquise**. Arenarea est reconstruite avec 2 210 éléments et 226 contrôles
de navigation réussis. Ses 50 captures de jour et de nuit ont été inspectées.
Sur RTX 4060 Ti en 1920 × 1080, la mesure courte donne 74,7 images/s à midi et
75,1 à 22 h, avec douze passants animés. Le parcours physique s’arrête toutefois
après **12 étapes sur 364**, près de la tribune courbe nord-est de l’hippodrome.
Les pieds sont à la bonne altitude ; une collision directe n’est pas démontrée.
Le diagnostic est dans `relief-20261011/arenarea-walk-failure-review.json`.

Martpart conserve sa dernière carte reconstruite de **1 189 éléments** et les
18 captures correspondantes. Le candidat de **1 190 éléments et 108 maillages**
ajoute les appuis ajustés sous le mobilier. Sa reconstruction a été refusée :
Unreal restitue 148 420 triangles pour le proxy des appuis, contre 148 656 dans
le fichier source, même avec la suppression des triangles dégénérés désactivée.
Ces derniers appuis ne sont donc pas installés dans la carte jouable. L’audit
signale également 477 normales imprécises sur des microfaces par nouveau
maillage, d’aire individuelle inférieure à 2,70 mm² ; les volumes sources sont
fermés et leurs triangles correctement orientés. Aucune capture ni marche
précédente ne valide ce candidat.

Les 102 tests Python ciblés réussissent et le contrôle des fichiers orphelins
passe. Le contrôle Core inchangé compte 702 réussites et 2 tests ignorés.
Les tests Unreal et les transferts entre les trois cartes n’ont pas été rejoués
sur cet état final : l’import de Martpart bloque cette étape. Le bilan courant
est `Saved/Jadg/districts/validation-stopped-version.json` ; l’ancien
`validation-summary.json` reste un historique du 10 octobre.

Les réserves visuelles d’Arenarea portent notamment sur les arrière-plans nus,
les répétitions de bâtiments, les espaces peu habillés et l’éclairage uniforme.
Les mesures courtes ne garantissent pas tous les cadrages. Les ambiances sonores
sont installées, mais les captures et parcours utilisent `-NoSound` : aucune
écoute n’est validée. L’appréciation artistique finale reste celle de l’auteur.
Aucune nouvelle passe de construction n’est engagée après cet état arrêté.

## Les maillages au maître

Unreal ne borne pas le nombre de triangles d'un maillage : Nanite le découpe lui-même. Les pièces
Meshy se livrent donc **au maître**, sans décimation (D-53). Elles vivent sous
`Source/Elements/Assets/Master/<Famille>/<Référence>.glb` : une pièce porte le nom de sa **référence**
(le dieu de Tanares, la fiche de personnage, la pièce d'équipement), jamais le nom inventé par Meshy.
`references.json` relie chaque retour Meshy à sa référence et dit d'où vient l'attribution ;
`manifest.json` dit, pour chaque pièce, son empreinte, ses triangles et l'asset qu'elle produit.

```powershell
# Ranger un dossier de retours Meshy dans le kit et écrire le manifeste
python scripts/assetsGeneration/build_master_manifest.py D:\Telechargement\Assets

# Refaire les fiches des pièces déjà rangées (famille, classe, emprise, matière lue dans le .glb)
python scripts/assetsGeneration/build_master_manifest.py --refresh

# Installer les pièces du manifeste dans le projet — Nanite, matière, textures compressées —, sans fenêtre
& "<moteur>\Engine\Binaries\Win64\UnrealEditor-Cmd.exe" JustAnotherRpgGame.uproject `
    -run=pythonscript -script="scripts/assetsGeneration/import_scenery_unreal.py" -unattended -nosplash -nullrhi
```

L'installation est rejouable (LOT-1019) : une pièce déjà présente n'est pas réimportée
(`-JadgForce` pour la refaire), une pièce dont l'empreinte ne correspond plus au manifeste arrête le
script ; `-JadgKit=Regions/…/arena-of-fate/Scene` installe les pièces d'un kit, et un rapport de
poids s'écrit sous `Saved/Jadg/scenery/`.
`-JadgFamily=Weapons`, `-JadgOnly=Statues/Harvest_Fairy`, `-JadgLimit=3` bornent l'import.

Ouvrir `JustAnotherRpgGame.uproject` dans l'éditeur ou générer la solution Visual Studio depuis
le `.uproject` fonctionne comme pour tout projet C++ du moteur.

## Licence

Code sous [PolyForm Noncommercial 1.0.0](LICENSE) ; contenu sous les termes de
[LICENSE-CONTENT](LICENSE-CONTENT) ; bibliothèques tierces dans
[THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
