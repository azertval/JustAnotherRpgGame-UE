# Le standard 3D

Le jeu se rend dans **Unreal Engine 5** depuis la `0.0.3` ([D-48](../vision/decisions.md)) : la
caméra est en perspective et tourne librement ([D-49](../vision/decisions.md),
[D-56](../vision/decisions.md)), un maillage se livre **au maître** et Nanite le prend tel quel
([D-53](../vision/decisions.md)), Lumen éclaire, et plus aucune image ne se dresse dans le décor.
Ce document fixe ce qu'une **pièce de décor** doit être pour ce moteur ; les personnages ont leur
page, [personnages 3D](personnages-3d.md).

Il est **normatif**, et il ne contient que deux sortes de valeurs : celles que le
[LOT-1019](../versions/v0.1.0/v0.0.3-nouveau-moteur/lots/LOT-1019-chaine-de-decor.md) a
**mesurées** dans le moteur — le 9 octobre 2026, sur le poste de référence (Unreal Engine 5.8.3,
RTX 4060 Ti, i7-8700, 1920 × 1080) —, et les **décisions datées** de l'auteur. Ce qui n'est ni
l'un ni l'autre est écrit **ouvert**, avec le lot ou la question qui le tranche
([§8](#8-ce-qui-est-tranché-ce-qui-reste-ouvert)) : le standard ne devine pas, et il ne reprend
aucune valeur de sa version précédente (la vue isométrique de la `0.0.2.5`) sans l'avoir remesurée.

## 1. La géométrie

| Règle | Valeur | D'où elle vient |
|---|---|---|
| Une case | **1,5 m** de côté | la grille du *Manuel*, sur laquelle le combat est réglé (`core::METERS_PER_TILE`) |
| Unité | le **mètre** dans le `.glb`, à l'échelle 1 ; le moteur compte en centimètres (× 100) | mesuré : le repère est relu à chaque construction de carte sur un bloc dissymétrique (`repere.glb`) — « X moteur = +X du .glb, Y = +Z du .glb, Z = +Y du .glb » |
| Le haut, le devant | le haut est **+Y** du `.glb` (+Z du moteur) ; le devant d'une pièce est **+Z** du `.glb`, le sud de la carte à lacet nul | mesuré (même relevé) ; `build_level.py` |
| Origine | **un retour Meshy garde la sienne** : le centre de sa boîte, pas son pied (la façade témoin va de −0,95 à +0,95 en hauteur) ; la carte pose la pièce **par sa hauteur** (`height`), qui ramène son pied au sol. Une pièce construite par script a son origine au sol | mesuré sur les 49 maîtres ; D-53 interdit de retoucher le `.glb` |
| Échelle | **aucune n'est livrée par Meshy** : la taille d'une pièce est la hauteur que sa fiche ou sa carte lui donne. Celle de la façade témoin, 12 m, est **provisoire** (aucune cote de la commande) | mesuré ; question à l'auteur ([§8](#8-ce-qui-est-tranché-ce-qui-reste-ouvert)) |
| Caméra | **perspective, libre** : rotation entière, inclinaison bornée, zoom | D-49 et D-56 (7 octobre 2026) |
| Cadrage du joueur | inclinaison de **25 à 70°** sous l'horizon, distance de **4 à 120 m** du point visé (départ : 40°, 16 m) | `Config/DefaultGame.ini` (LOT-1016 ; la distance la plus longue est celle de la porte, pas encore jugée dans une fenêtre) ; une pièce se juge dans ces bornes |
| Toutes faces | une pièce n'a **pas de dos caché** : la caméra en fait le tour | D-56 ; contrôlé sur quatre captures (le [gabarit de commande](gabarit-commande-zone.md)) |

La hauteur d'un étage de décor reste **ouverte** : 3 m par étage dans les cartes migrées, provisoire
([LOT-1018](../versions/v0.1.0/v0.0.3-nouveau-moteur/lots/LOT-1018-cartes-composees.md), question 1).
Le Colisée de la porte a les dimensions de celui de Rome (189 × 156 m, 48 m ; décision de l'auteur
du 8 octobre 2026).

## 2. Le format d'échange

| Règle | Valeur | D'où elle vient |
|---|---|---|
| Fichier | **`.glb`** (glTF 2.0 binaire), **un modèle par fichier**, autonome : géométrie, textures **incorporées** — la couleur de base, et depuis D-46 le relief et l'occlusion-rugosité-métal —, et pour un personnage squelette et clips | mesuré au LOT-1000 (export `Khronos glTF Blender I/O`, Blender 5.2) ; [D-46](../vision/decisions.md) |
| Attributs d'un sommet | `POSITION`, `NORMAL`, `TEXCOORD_0` ; pour un modèle animé `JOINTS_0` et `WEIGHTS_0`, soit **quatre os au plus par sommet**, poids normalisés | mesuré au LOT-1000 (écart à 1 inférieur à 3 × 10⁻⁸) |
| Maillage | **un seul maillage, une seule primitive, une seule matière** par modèle ; triangles indexés | mesuré au LOT-1000 |
| Atelier | **Blender, piloté par script, sans fenêtre** ; aucune retouche à la main d'un maillage : ce qui ne sort pas du script se recommande | mesuré au LOT-1000 (Blender 5.2.2) |
| Stockage | comme une image de kit : **hors de Git**, publié en archive et verrouillé ([arborescence](arborescence-assets.md#le-stockage)) | règle du LOT-108, inchangée |

## 3. Le poids

**Il n'y a pas de budget de triangles** (D-53) : Nanite prend la pièce au maître. Le budget d'un
maillage de décor, que le standard renvoyait au LOT-151, est tranché ici **par la mesure** : la
porte, qui pose les plus lourds maillages livrés, tient la cadence de D-54 avec une marge.

| Mesure, porte (`porte-1012`) | Valeur |
|---|---|
| Maillages distincts posés | 60, dont les 14 dieux et les 2 lions au maître (1,8 à 2,9 millions de triangles chacun) et la façade témoin posée six fois (2,68 millions) |
| Triangles Nanite des maillages distincts | **33,5 millions** ; le plus gros : `statue-dorsi`, 2 900 460 |
| Cadence, caméra en rotation | **88,7 images/s** à midi (11,3 ms, processeur graphique 9,7 ms), **89,2** à 22 h ; la cible de D-54 est 60 |
| Textures de ces maillages | 113, **123 Mio en mémoire graphique** (mipmaps chargées à la fin du passage), 461 Mio entières |

Ce qui se mesure d'une pièce est donc son **poids sur disque**, à la source et dans le projet
(`import_scenery_unreal.py`, rapport `Saved/Jadg/scenery/<ensemble>.json`) :

| Pièce | Triangles (`.glb` / Nanite) | `.glb` | Maillage dans le projet | Textures dans le projet |
|---|---:|---:|---:|---:|
| Façade témoin (`arenarea-palazzo-terracotta`, Meshy) | 2 679 696 | 87,7 Mio | 94,7 Mio | 11,1 Mio (3 × 2048²) |
| Un dieu (`statue-bauron`, Meshy) | 2 221 596 | 70,6 Mio | 77,8 Mio | 9,3 Mio |
| Coque de l'Arena of Fate (`af-arena-shell`, script) | 877 645 / 865 214 | 85,5 Mio | 26,6 Mio | 4,6 Mio |

| Ensemble | Pièces | `.glb` | Maillages dans le projet | Textures dans le projet |
|---|---:|---:|---:|---:|
| Les maîtres (statues, armes, la façade) | 49 | 1 784 Mio | 1 739 Mio | 401 Mio (147 textures) |
| Le kit de l'Arena of Fate | 105 | 297 Mio | 81,6 Mio | 58,9 Mio (102 textures) |

Une image que deux pièces portent n'est importée **qu'une fois** : le kit de l'Arena of Fate porte
315 images pour 102 contenus distincts, et son dossier du projet passe de 857 Mo (une copie par
pièce, l'import d'avant) à 112 Mo, plus ses 59 Mio de textures partagées.

Le plafond de **5 Mio par fichier** (`check_binary_files.py`) porte sur les fichiers suivis par Git :
un `.glb` n'y est pas. **Aucun budget de poids par zone** ([D-23](../vision/decisions.md)) ; un kit
ne se bride pas pour tenir un poids (décision de l'auteur du 24 septembre 2026).

## 4. Les matières et la lumière

- **Une matière complète** ([D-46](../vision/decisions.md), 4 octobre 2026) : la **couleur de
  base**, le **relief** (`normalTexture`, repère tangent) et l'**occlusion-rugosité-métal**
  (`metallicRoughnessTexture` : rugosité dans le vert, métal dans le bleu ; occlusion dans le rouge
  quand `occlusionTexture` cite la même image). Mesuré sur les maîtres : **Meshy livre les trois
  cartes**, en JPEG de 2048 × 2048, sur ses 49 retours. Une pièce dont il manque une carte le dit
  dans sa fiche (`material.missing`) ; elle se rend, mais elle ne tient pas le standard.
- **Une pièce livre ses vraies cartes, ou se recommande** (fiche du LOT-1019) : aucune carte ne se
  dérive plus d'une couleur de base (`material_maps.py` est retiré). Une pièce construite par
  script porte sa couleur de base et sa rugosité et son métal en **facteurs** ; ceux du Colisée
  sont les valeurs jugées sur captures le 4 octobre 2026 (D-46) : calcaire **0,88**, marbre
  **0,36**, sable **0,96**, velours **0,92**, bronze **0,42** et métallique. Son relief est **dans
  son maillage** (§5).
- **Les textures se compressent dans le moteur**, à l'import : **BC7** pour la couleur de base
  (sRGB) et l'occlusion-rugosité-métal (linéaire), **BC5** pour le relief, dont le vert est
  retourné (glTF est en repère OpenGL). Une source que le dépôt fabrique s'écrit en **PNG** ; un
  retour Meshy garde les images qu'il apporte, sans réencodage (fiche du LOT-1019 ; le JPEG de
  D-46 pour la couleur de base tombe).
- **Une matière parente, écrite par script** : `M_Scenery` (opaque) et `M_SceneryMasked` (un
  alpha `MASK` ou `BLEND` devient un masque), deux faces, utilisables en instances et en Nanite.
  La matière glTF du moteur ne l'est pas en instances : dans le jeu lancé elle cède à la matière
  par défaut — c'est la carte grise de l'Arena of Fate au LOT-1018, mesurée et corrigée ici.
- **Peint, sans grain** (§5) : aplats modelés, matières propres, sans bruit ni microdétail.
- **La lumière vient du moteur** (Lumen, le soleil et le ciel de la table du jour, les lampes) :
  une texture ne porte ni ombre portée, ni ombre propre marquée, ni reflet de lumière orientée
  (décision du LOT-1007, 3 octobre 2026). Une pièce se juge **éclairée**, à midi et à 22 h.
- **Une pièce qui éclaire le dit dans sa fiche** ([D-45](../vision/decisions.md), 3 octobre
  2026) : le champ `light` donne sa couleur (`#rrggbb`), sa portée (`range` ou `radius`) et sa
  hauteur en mètres, si elle tremble (`flicker`) et si elle reste allumée de jour (`always`) ;
  `build_level.py` en fait une source ponctuelle. Les portées et les intensités de la porte sont
  **à juger par l'auteur** sur les captures de 22 h du LOT-1019 (`lampCandelas`,
  `fireCandelas` : réglages provisoires de la carte).

### La palette de l'Empire central

Relevée sur la planche de référence d'Arenarea, écrite dans `region.json` : une donnée du lieu, pas
une valeur de rendu. Chaque région aura la sienne, dans son référentiel.

| Teinte | Usage |
|---|---|
| **Ivoire** `#efe6d2` | marbre, enduits, lumière |
| **Sable** `#d9c7a3` | pierre calcaire, sols |
| **Gris chaud** `#9c948a` | ombres de pierre, pavés |
| **Bronze foncé** `#5c4a2a` | ferronnerie, bois sombre |
| **Bourgogne** `#8e2335` | l'accent impérial : bannières, tuiles, auvents |
| **Or vieilli** `#c9a45c` | emblèmes, chapiteaux, dorures |
| **Vert feuillage** `#3f6b34` | cyprès, haies, jardins |
| **Eau sourde** `#2f7f86` | fontaines, bassins |

## 5. Critères de qualité validés par l'auteur

Confirmés le **23 septembre 2026** sur le LOT-105 V4 (après la reprise du relief des sols, des
balustres et des haies), et repris ici parce qu'ils ne dépendent pas de la matière : ils valent
pour un kit en maillages comme ils valaient pour un kit peint.

- **Fidélité au style d'origine** : garder la facture peinte et les références approuvées ; pas de
  variante générique. L'emblème du lieu se reprend de sa référence, il ne s'invente pas.
- **Grille exacte** : emprises en cases entières, échelle cohérente, origine au sol. Aucun
  ajustement par placement pour masquer une mauvaise calibration.
- **Continuité entre modules** : deux pièces voisines d'une même famille se prolongent — joints
  alignés, phase commune, bords compatibles ; ni couture, ni damier.
- **Vraies pièces d'angle** : angles rentrants et sortants des murs, balustrades et haies, sans
  trou, chevauchement ni étirement de texture.
- **Matière propre, relief lisible** : pas de bruit ni de microdétail, mais la pierre taillée, ses
  biseaux et ses joints creux se lisent. En 3D le relief est **dans le maillage**, pas peint dessus.
- **Volume réel** : balustres modelés, haies au dessus arrondi, raccords continus jusque dans les
  angles. C'était un critère d'image ; c'est désormais la définition de la pièce.
- **Validation en assemblage** : une carte qui réunit toutes les pièces, avec répétitions de sols
  et raccords droits et d'angle, **rendue par le moteur** à plusieurs échelles. Une planche de
  pièces isolées ne suffit pas.
- **Retouches ciblées et réversibles** : le reste d'un kit validé se préserve ; les versions
  précédentes, les sources et les scripts se gardent dans l'atelier.

La référence d'un lieu est **sa carte peinte**, jugée par l'auteur sur captures du moteur à midi et
à 22 h, aux cadrages du joueur ([D-54](../vision/decisions.md), 7 octobre 2026) ; elle remplace le
rendu du LOT-105 V4 pour le décor.

## 6. Les familles de pièces d'un lieu

Les dix familles restent le **gabarit d'inventaire** d'une zone : un lot d'assets de zone les passe
en revue et dit, pour chacune, ce qu'il prend au **commun** et ce qu'il produit en **propre**
([arborescence](arborescence-assets.md), [gabarit de commande](gabarit-commande-zone.md)). Toutes
sont des **maillages** : plus aucune image ne se dresse sous une caméra libre (D-49). Leur
**origine** suit [D-55](../vision/decisions.md) (7 octobre 2026) : l'architecture et le mobilier se
produisent pour le lieu, par **Meshy**, au maître ; la nature, les sols et les matières viennent des
**bibliothèques** du moteur (Megascans, Fab) ; ce qui est trop grand pour une commande se
**compose** de pièces posées par script (un préfabriqué, `jadg-prefab`).

| # | Famille | Emprise type | Origine | Ce qui existe aujourd'hui |
|---|---|---|---|---|
| 01 | Sols | 1 × 1 | bibliothèque (le sol naturel, en terrain) ; Meshy pour un dallage taillé propre au lieu | les dalles des kits (`ar-paving-*`, `af-paving-*`), à reprendre |
| 02 | Façades et murs | 2 × 1, 3 × 1 | Meshy | **la façade témoin** (`arenarea-palazzo-terracotta`) ; six variantes commandées (LOT-1019) |
| 03 | Colonnes | 1 × 1, 3 × 1 | Meshy | rien au maître |
| 04 | Accès | 2 × 1 | Meshy | rien au maître |
| 05 | Balustrades | 2 × 1, angle | Meshy | rien au maître |
| 06 | Pièces maîtresses | 3 × 3 et plus | Meshy | les 22 statues au maître |
| 07 | Végétal | 1 × 1 à 3 × 1 | bibliothèque | les cyprès et l'arbre Meshy du kit d'Arenarea, à reprendre |
| 08 | Mobilier | 1 × 1 | Meshy | les meubles des kits, à reprendre |
| 09 | Bâtiments | 3 × 2 et plus | **ouvert** : une pièce Meshy entière, comme la façade témoin, ou une composition de façades | — |
| 10 | Seuils | 3 × 3 et plus | composé | le Colisée de la porte : neuf pièces construites par script (`build_colosseum.py`), posées en préfabriqué |

Une pièce de **bibliothèque** est citée par sa fiche avec sa **licence** et son **identifiant**
(`Source/Elements/Assets/Library/manifest.json`), et contrôlée comme une pièce Meshy. Aucune n'est
entrée au LOT-1019 : sur Fab, seul l'auteur se connecte, et rien ne s'achète (décision du 8 octobre
2026).

La règle de la **dalle de fond** demeure : une zone livre d'abord un sol répétable, sans bordure,
en **trois variantes au moins**, avant ses panneaux décoratifs.

## 7. Les images tolérées

**Retirées au LOT-1019** : plus aucune image ne se dresse dans le décor (D-49). Ce qui reste une image n'est pas du décor et n'est pas régi ici : les portraits et
les jetons, peints ([D-30](../vision/decisions.md), [personnages 3D](personnages-3d.md), §8), et
les effets de `Common/Fx/`.

## 8. Ce qui est tranché, ce qui reste ouvert

Les questions que le standard renvoyait au LOT-151 et à un lot de rendu sont posées ici sur captures
du moteur, à midi et à 22 h, aux cadrages de la porte
([annexes du LOT-1019](../versions/v0.1.0/v0.0.3-nouveau-moteur/annexes/LOT-1019/)). Le passage de
captures règle le post-traitement sans reconstruire la carte (`-JadgPost`, `AJadgCaptureDirector`).

| Question | État | Sur quoi |
|---|---|---|
| Le **budget d'un maillage de décor** | **tranché par la mesure** : pas de budget de triangles ; le poids sur disque est mesuré et écrit (§3) | la porte : 33,5 millions de triangles Nanite distincts à 88,7 images/s |
| La **forme** des familles 02, 03, 04, 07, 09, 10 | **tranché** : des maillages (§6) | D-49, D-55, D-56 |
| L'**origine** de la famille 09, Bâtiments | **ouvert** : une pièce Meshy entière ou une composition de façades | l'auteur, avec le retour de la commande des façades |
| Le **contour sombre** | une passe de post-traitement écrite par script (`M_Contour`, `build_level.py` : un bord où la profondeur saute, bronze foncé) ; captures avec et sans — **à juger par l'auteur à la recette** | `porte-base` et `porte-contour` |
| L'**occlusion ambiante d'écran** | celle de Lumen, active ; captures avec et sans — **à juger par l'auteur** | `porte-base` et `porte-sans-ao` |
| Le **halo** des flammes | `bloom` 0,6 sur la porte ; captures avec et sans — **à juger par l'auteur** | `porte-base` et `porte-sans-halo` |
| Les **ombres portées des lampes** | portées par les lampes, pas par les feux ; captures avec et sans — **à juger par l'auteur** | `porte-base` et `porte-sans-ombres-lampes` |
| L'**échelle** d'une pièce Meshy | **ouvert** : Meshy n'en livre pas ; la façade témoin est à 12 m, provisoire | la cote que la commande donnera |
| La **hauteur d'un étage** de décor | **ouvert** : 3 m, provisoire | LOT-1018, question 1 |
| Le **coût Meshy** d'une pièce | **ouvert** : 30 crédits au barème des personnages, à confirmer par l'auteur | le retour de la commande des façades |
| Le squelette `quadruped`, ses clips | ouvert | le lion et le loup (LOT-1025) |
| La silhouette `flying` : un squelette par morphologie | ouvert | le premier lot qui en produit une |

## 9. Ce que le standard interdit

- **Aucune image du corpus** dans le jeu, ni affichée, ni décalquée, ni donnée en référence à un
  générateur (règle du `LOT-94`, inchangée).
- **Aucune image dressée** dans le décor (D-49).
- **Aucune carte dérivée** d'une couleur de base : une pièce livre ses cartes, ou se recommande.
- **Aucun asset mort** : un lot qui remplace une pièce la supprime dans sa PR
  ([D-32](../vision/decisions.md)) ; `scripts/checks/check_orphans.py` le vérifie en CI.
- **Aucune retouche à la main** d'un maillage, d'une texture ou d'une animation, ni d'un asset du
  moteur : la chaîne se rejoue par script (`import_scenery_unreal.py`), ou la pièce se recommande.
- **Aucune figurine ne se commande plus en bandes** : un personnage est un modèle
  ([personnages 3D](personnages-3d.md)).
