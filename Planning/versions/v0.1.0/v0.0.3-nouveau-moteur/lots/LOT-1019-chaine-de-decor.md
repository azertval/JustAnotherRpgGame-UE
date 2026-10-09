+++
id = "LOT-1019"
titre = "La chaîne de décor au niveau du moteur, et le standard 3D réécrit"
version = "0.0.3"
filiere = "standard"
statut = "a-faire"
taille = "L"
resume = "Chaque famille de pièces d'un lieu se produit au maître, avec sa matière complète, et s'installe dans le moteur par script ; le standard 3D dit sur mesures ce qu'une pièce doit être."
prerequis = ["LOT-1018"]
livrables = [
  "`style-3d.md` réécrit : §1 géométrie (unité, origine, caméra libre, échelle du décor), §3 poids (sur disque, mesuré), §4 matières (cartes PBR complètes, textures compressées par le moteur, pas de JPEG), §6 familles (les dix familles relues : ce qui vient de Meshy, ce qui vient des bibliothèques du moteur — D-55 —, ce qui se compose), §7 supprimé (plus d'image tolérée dans le décor), §8 les questions tranchées ou renvoyées.",
  "Le gabarit de commande d'une zone (`gabarit-commande-zone.md`) révisé pour commander des pièces au maître, toutes faces, sous une caméra qui tourne.",
  "`import_scenery_unreal.py` : une pièce Meshy ou une pièce des bibliothèques entre dans le projet par script, avec son manifeste (emprise, classe, lumières, matière) ; la vue Scenery de l'atelier (LOT-1008, reportée) livrée sur ce script.",
  "Une **famille témoin** produite au nouveau standard — les façades d'Arenarea, six variantes au moins — rendue sur le parvis de la porte à midi et à 22 h, comparée à la carte peinte et aux captures du 7 octobre.",
  "Le contour sombre, la forme de chaque famille et le budget d'un maillage de décor, que le standard renvoyait au LOT-151, tranchés ici sur captures.",
  "`material_maps.py` et la chaîne procédurale Blender des boîtes d'Arenarea retirés ; les kits republiés portent des maillages au maître.",
]
criteres = [
  "La famille témoin est validée par l'auteur sur le rendu du moteur, à midi et à 22 h, aux cadrages du joueur, comme « au niveau de la carte peinte » (jugement de l'auteur).",
  "Le standard ne contient que des valeurs mesurées sur ce lot ou des décisions datées ; aucune valeur reprise du standard précédent sans remesure.",
  "Une pièce s'installe par script depuis sa fiche sans geste dans l'éditeur ; `check_orphans.py` cite chaque pièce installée.",
  "Le poids du kit témoin et le nombre de triangles de sa plus grosse pièce sont écrits dans la fiche (leçon 3 du bilan de la `0.0.2.5`).",
]
+++

## Pourquoi

Un moteur de ce niveau ne rend bien que des assets de ce niveau (R-15). Soixante modules
d'Arenarea sortent d'un script Blender en boîtes ; les cinq pièces qui ressemblent à l'image
viennent de Meshy. Ce lot renverse la proportion et écrit ce qu'une pièce doit être, sur mesures,
avant qu'Arenarea ne se reconstruise.

## Périmètre

Dedans : le standard, le gabarit de commande, l'import par script, la vue Scenery, une famille
témoin, les questions laissées par le LOT-151.

Dehors, nommément :

- Arenarea entier (LOT-1021) : une famille suffit à écrire le standard ;
- les personnages (LOT-1015), qui ont leur page ;
- le kit commun de la Capitale (LOT-151) : il se produit à la `0.0.4`, au standard écrit ici.

## À supprimer

| Quoi | Où | Pourquoi maintenant |
|---|---|---|
| La chaîne procédurale Blender d'Arenarea (`build_architecture.py`, `build_details.py`, `place_details.py`) | `Tools/Assets3D/.../Production147/` (atelier local) et leurs copies sous `scripts/assetsGeneration/` | elle produit des boîtes que le standard interdit |
| `material_maps.py` (cartes dérivées d'une couleur de base) | `scripts/assetsGeneration/` | une pièce livre ses vraies cartes, ou se recommande |
| §7 du standard 3D, les images tolérées | `Planning/standards/style-3d.md` | plus aucune image ne se dresse sous une caméra libre (D-49) |

Les kits `arenarea@3`, `martpart@4` et `capital/Common@3`, en images et en boîtes, restent lus par
l'ancien moteur jusqu'à la recette ; leur retrait est au LOT-1023.

## Conception

- **Meshy pour l'architecture et le mobilier**, au maître, PBR activé : la décision du 2 octobre
  (« réduction par `reduce_model.py` ») tombe avec D-53. Une pièce se commande depuis une image
  peinte au style du lieu, vue de trois quarts, toutes faces finies.
- **Les bibliothèques du moteur pour la nature** (D-55, tranchée) : sols, roches, végétation,
  matières de base viennent de Megascans ou de Fab ; l'architecture, le mobilier et les personnages
  restent produits pour le lieu. Chaque pièce de bibliothèque est citée par son manifeste avec sa
  licence et son identifiant, et `check_orphans.py` la contrôle comme une pièce Meshy.
- **Les textures** sont compressées par le moteur à l'import (BC7, BC5 pour le relief) ; le kit
  porte les sources (PNG) et le projet leurs sorties régénérées.
- **La facture peinte** (critère de l'auteur du 23 septembre, §5) reste le critère de style : les
  matières sont propres, sans grain ; le contour sombre se juge ici avec et sans.
- **Le lieu se juge sur le rendu du moteur, pas sur une image** : leçon 1 du bilan de la `0.0.2.5`,
  et D-54.

## Risques et questions ouvertes

- **Le coût Meshy.** Trente crédits par pièce au barème des personnages ; une famille de six
  variantes en coûte deux cents. Le relevé du coût par pièce manque toujours (leçon 5 du bilan) :
  ce lot l'écrit pour la famille témoin.
- **Toutes faces.** Une pièce vue sous une caméra qui tourne n'a plus de dos caché ; les retours
  Meshy ont parfois un dos pauvre. Le gabarit de commande le demande ; le contrôle le vérifie sur
  quatre captures.

## Avancement — 9 octobre 2026

Fait par l'assistant, en autonomie, sur la branche `lot/1019-chaine-de-decor`. Le lot est
**ouvert** ; sa fiche reste `a-faire` tant que le LOT-1018, son prérequis, n'est pas livré
(`lint_planning.py` refuse un lot en cours sur un prérequis ouvert) ; sa clôture est une décision
de l'auteur. Rien de ce qui suit n'a été vu
dans une fenêtre : les images sont **à juger par l'auteur à la recette**. Ce qu'une pièce doit
être est dans le [standard 3D](../../../../standards/style-3d.md), réécrit ; comment elle entre
dans le moteur, dans le [guide des données](../../../../../Documentation/Guide/guide-donnees.md)
(« La chaîne de décor ») et le [guide des cartes](../../../../../Documentation/Guide/guide-cartes-moteur.md) ;
l'exigence, dans [`rendu-technique.md`](../../../../../Documentation/Specification/rendu-technique.md)
(`EX-REN-057` à `EX-REN-059`).

### Pourquoi l'Arena of Fate sortait grise (question 5 du LOT-1018)

Mesuré dans le jeu lancé : « *Material …/af-paving-a/Materials/painted-matter missing usage flag
InstancedStaticMeshes! Default Material will be used in game.* » Les pièces d'une couche se posent
**en instances** ; leur matière, celle qu'Interchange crée pour un `.glb` (une instance de
`M_GLTF`, une matière du moteur, qu'on ne peut pas sauver dans le projet), n'est pas compilée pour
les instances, et le jeu lui substitue la matière par défaut — la grille grise de la capture. Les
cartes étaient pourtant toutes là : les 105 pièces du kit portent couleur, relief et
occlusion-rugosité-métal. Une deuxième cause s'est montrée au premier passage texturé : une
texture neuve se compresse pour le jeu à son premier chargement, et la première capture sortait
avec un sable et des dieux noirs ; le passage de captures attend désormais la construction des
assets, comme celle des shaders.

### Ce qui est fait

- **La chaîne de décor** (`scripts/assetsGeneration/import_scenery_unreal.py`, `EX-REN-057`,
  `EX-REN-058`) : une pièce entre dans le projet par script depuis sa **fiche** — l'entrée du
  manifeste des maîtres (objet `sheet`), d'un kit (`Scene/manifest.json`) ou des bibliothèques
  (`Library/manifest.json`) —, importée au maître par Interchange si elle manque ou a changé,
  Nanite, collision sur le maillage ; puis **habillée** : chaque image du `.glb` devient une
  texture du projet, **une par contenu** (`/Game/Scenery/Textures/T_<rôle>_<empreinte>`),
  compressée **BC7** (couleur sRGB, occlusion-rugosité-métal linéaire) ou **BC5** (relief, vert
  retourné) ; chaque matière devient une instance de `M_Scenery` (ou `M_SceneryMasked` pour un
  alpha), partagée de même (`/Game/Scenery/Materials/MI_<empreinte>`), avec ses facteurs glTF ;
  ce qu'Interchange avait produit est retiré. `M_Scenery` est écrite nœud par nœud, à deux faces,
  utilisable en instances et en Nanite. `build_level.py` passe par elle pour chaque maillage qu'une
  carte pose ; seule, elle installe les maîtres et les bibliothèques, ou un kit (`-JadgKit`), et
  écrit le poids de chaque pièce (`Saved/Jadg/scenery/<ensemble>.json`).
- **La fiche d'une pièce** (`scenery_sheets.py`, sans moteur, testé hors du moteur) : famille du
  standard, classe, emprise, type tactique, lumière, matière lue dans le `.glb` (les cartes, leurs
  formats et tailles, ce qui manque), et pour une pièce de bibliothèque sa source, son identifiant
  et sa licence ; une fiche fautive ne s'installe pas. `build_master_manifest.py --refresh` refait
  les fiches des maîtres depuis `references.json` (la façade témoin : famille `02`, `tall`,
  `solid`, hauteur 12 m provisoire) ; le manifeste des bibliothèques est prêt et **vide**.
- **`check_orphans.py`** cite chaque pièce installée par sa fiche (le champ `asset` des
  manifestes des maîtres et des bibliothèques), en plus des scripts qui produisent `/Game/Kit`,
  `/Game/Master`, `/Game/Scenery`.
- **La matière des pièces existantes** : les 105 pièces du kit de l'Arena of Fate, les 49 maîtres
  et les 9 pièces du Colisée installées par la chaîne ; l'Arena of Fate **sort texturée**
  ([capture de midi](../annexes/LOT-1019/captures/arena-of-fate-ensemble-1200.png), à comparer à
  [celle du LOT-1018](../annexes/LOT-1018/captures/arena-of-fate-ensemble-1200.png)).
- **Le post-traitement réglable au passage de captures** (`EX-REN-059`, `AJadgCaptureDirector`,
  `-JadgPost`) : le **contour sombre**, une passe de post-traitement écrite par script
  (`M_Contour`, `build_level.py` : un bord où la profondeur saute de plus de 2 % d'un pixel à son
  voisin, teinté du bronze foncé du standard 2D ; une carte le pose d'office par
  `lighting.contour`), l'occlusion ambiante d'écran de Lumen, le halo, les ombres des lampes ;
  `mesure.json` écrit en plus la mémoire graphique et les maillages de la carte. Le passage attend
  que les textures et les maillages aient fini de se construire.
- **La famille témoin** : la façade au maître posée **six fois** sur le parvis de la porte (quatre
  au sud, deux qui bordent la ruelle ; `build_gate_scene.py`), et un cadrage du joueur sur elle
  (`facades` : 30 m, 35°) ; rendue à midi et à 22 h.
- **La carte de contrôle d'une pièce** (`scripts/maps/build_piece_check.py`) : la pièce seule et
  quatre cadrages — face, droite, dos, gauche —, à midi et à 22 h ; `build.ps1 -Map controle/<pièce>
  -Capture` la vérifie à jour avant de la construire. Celle de la façade témoin est capturée.
- **Le Colisée sans carte dérivée** : `build_colosseum.py` exporte la couleur de base, et la
  rugosité et le métal de chaque matière en **facteurs** (les valeurs de D-46) ; ses neuf pièces
  sont régénérées.
- **`style-3d.md` réécrit** sur ces mesures et les décisions datées ; **`gabarit-commande-zone.md`
  révisé** (pièces au maître, toutes faces, une caméra qui tourne, quatre captures de contrôle du
  dos) ; la **commande des six façades** écrite pour l'auteur (ci-dessous).
- **Tests** : `Jadg.Decor.Matiere` (une pièce de chaque origine : Nanite, matière parente du
  décor, utilisable en instances et en Nanite, textures partagées, BC7 et BC5) et
  `Jadg.Decor.TexturesPartagees` (les trois sables de l'Arena of Fate, une seule instance) ;
  `test_scenery_sheets.py` (21 cas), `test_build_piece_check.py` (4), un cas de plus à
  `test_check_orphans.py`.
- **Suppressions** (D-32) : `import_master_unreal.py` (absorbé) ; `material_maps.py` et ses
  tests ; les scripts Blender du kit de l'Arena of Fate (`arena_fate_architecture.py`,
  `arena_fate_architecture_v2.py`, `arena_fate_enclosures.py`, `arena_fate_iconography.py`,
  `arena_fate_underground_v3.py`, `arena_fate_matters.json`, `import_arena_fate_meshy.py`,
  `import_arena_fate_subsoil_meshy.py`, `install_arena_fate.py`) ; la maquette du standard 2D
  (`build_hd_mockup.py`, son test, `Source/Test/Fixtures/HdMockup/`, `HdMockupScene.h`, qu'aucun
  test ne lisait plus) ; le §7 du standard. Les kits anciens restent (LOT-1023).

### Les décisions de réalisation

| Décision | Ce qui est retenu | Pourquoi |
|---|---|---|
| La fiche d'une pièce | l'entrée de son manifeste (kit, maîtres, bibliothèques), pas un fichier par pièce | les kits la portaient déjà (classe, emprise, type tactique, lumière) ; le manifeste des maîtres reçoit un objet `sheet`, parce que son `family` est le dossier du kit |
| `import_master_unreal.py` et `import_arena_fate_meshy.py` | le premier est **absorbé** ; le second est **retiré**, pas absorbé | le second ne mettait rien dans le moteur : il mettait à l'échelle et posait les sculptures dans des `.glb` de l'ancien kit, sans leurs cartes ; la carte les pose désormais à leur hauteur |
| La matière | une matière parente du dépôt et des instances, plutôt que la matière glTF du moteur | celle du moteur ne se compile pas pour les instances et ne se sauve pas dans le projet |
| Les textures | importées depuis les images du `.glb`, une par contenu | le partage que l'ancien moteur faisait (D-46) : 315 images, 102 textures pour le kit de l'Arena of Fate |
| Les maillages déjà importés | habillés en place, sans réimport | le maillage ne change pas ; réimporter les maîtres prend des dizaines de minutes |
| Le contour | une passe de post-traitement sur la profondeur, réglée au passage de captures | la juger avec et sans sans reconstruire la carte ; une carte la pose par sa description si l'auteur la garde |
| La commande des façades | dans l'atelier local (`Tools/…/arenarea/commande.md`), son inventaire ici | la décision de l'auteur du 23 septembre 2026 (rien de `Tools/` ne se livre) |
| La famille témoin | la façade au maître six fois, pas six variantes | les variantes n'existent pas : seul l'auteur commande à Meshy |

### Ce qui se mesure

Mesuré le 9 octobre 2026 sur le poste de référence (Unreal Engine 5.8.3, RTX 4060 Ti, i7-8700),
jeu lancé hors écran en 1920 × 1080, caméra en rotation dix secondes par heure ; poids relevés par
`import_scenery_unreal.py` (annexes : `poids-kit-arena-of-fate.json`, `poids-maitres.json`).

**Le kit de l'Arena of Fate et sa plus grosse pièce** (leçon 3 du bilan de la `0.0.2.5`) :

| | Pièces | Triangles | `.glb` | Maillages dans le projet | Textures dans le projet |
|---|---:|---:|---:|---:|---:|
| Le kit | 105 | 2 043 379 | 296,7 Mio | 81,6 Mio | 58,9 Mio, 102 textures |
| Sa plus grosse pièce, `af-arena-shell` | 1 | 877 645 (865 214 en Nanite) | 85,5 Mio | 26,6 Mio | 4,6 Mio |

Le dossier du kit dans le projet passe de **857 Mo** (l'import du LOT-1018, une copie de chaque
image par pièce) à **112 Mo**, plus les 59 Mio de textures partagées. La carte de l'Arena of Fate
(48 maillages distincts, 2,85 millions de triangles) : **58,5 Mio de textures en mémoire
graphique** (93 textures, mipmaps chargées), 202,5 Mio entières ; 3 556 Mio de mémoire graphique
pour le processus ; **107,4 images/s** à midi, 107,1 à 22 h, contre 107,6 et 107,5 grise, mesurées
le même jour : la matière ne coûte rien de mesurable.

**Les maîtres** : 49 pièces, 1 784 Mio de `.glb`, 1 739 Mio de maillages et 401 Mio de textures
(147) dans le projet ; le dossier `Content/Master` passe de 2,6 Go à 1,7 Go. La façade témoin :
2 679 696 triangles, `.glb` de 87,7 Mio, 94,7 Mio de maillage et 11,1 Mio de textures (trois
images JPEG de 2048 × 2048, comme les 49 retours Meshy).

**La porte, avec la famille témoin** (60 maillages distincts, **33,5 millions** de triangles Nanite,
le plus gros `statue-dorsi` à 2 900 460) : **89,8 images/s** à midi (processeur graphique 9,8 ms),
91,0 à 22 h ; 123 Mio de textures en mémoire graphique (113 textures), 461 Mio entières. Le LOT-1012
mesurait 118,6 images/s sur une porte plus légère (sans le Colisée en pièces, ni le groupe). C'est
la mesure qui **tranche le budget d'un maillage de décor** : pas de budget de triangles (D-53), la
cadence de D-54 (60) tenue avec une marge d'un tiers sur la scène la plus lourde du dépôt.

**Le post-traitement, avec et sans** (porte, même construction ; la cadence varie de ± 4 images/s
d'un passage à l'autre, le temps du processeur graphique de ± 0,2 ms) :

| Passage | 12 h | 22 h | Pixels qui changent de plus de 16 niveaux, cadrage `porte`, 12 h / 22 h |
|---|---|---|---|
| tel que livré (occlusion, halo 0,6, ombres des lampes, sans contour) | 88,7 images/s, 9,74 ms | 89,2, 9,99 ms | — |
| `contour` | 93,1, 9,79 ms | 89,2, 10,02 ms | 1,9 % / 1,7 % |
| `sans-ao` | 93,3, 9,40 ms | 95,4, 9,62 ms | 2,2 % / 1,3 % |
| `sans-halo` | 96,3, 9,70 ms | 94,7, 9,92 ms | 0,1 % / 0,3 % (une teinte d'ensemble : 5 niveaux en moyenne) |
| `sans-ombres-lampes` | 92,0, 9,79 ms | 91,6, 9,76 ms | 0,0 % / 8,2 % ; la ruelle à 22 h : 34,6 % |

Aucun réglage ne coûte plus de 0,4 ms au processeur graphique : le choix est **de rendu**, pas de
cadence.

### Les questions du standard 3D, §8

| Question | État | Captures |
|---|---|---|
| Le budget d'un maillage de décor | **tranché par la mesure** (ci-dessus) : pas de budget de triangles ; le poids sur disque s'écrit | `mesure-porte.json`, `poids-*.json` |
| La forme des familles 02, 03, 04, 07, 09, 10 | **tranchée** : des maillages (D-49, D-55, D-56) ; l'origine de la famille 09 reste ouverte | — |
| Le contour sombre | **à juger par l'auteur à la recette** | [avec](../annexes/LOT-1019/captures/contour-porte-1200.png) et [sans](../annexes/LOT-1019/captures/porte-porte-1200.png) à midi ; [avec](../annexes/LOT-1019/captures/contour-porte-2200.png) et [sans](../annexes/LOT-1019/captures/porte-porte-2200.png) à 22 h |
| L'occlusion ambiante d'écran | **à juger par l'auteur** | [sans](../annexes/LOT-1019/captures/sans-ao-porte-1200.png) et [avec](../annexes/LOT-1019/captures/porte-porte-1200.png) à midi ; [sans](../annexes/LOT-1019/captures/sans-ao-porte-2200.png) et [avec](../annexes/LOT-1019/captures/porte-porte-2200.png) à 22 h |
| Le halo des flammes | **à juger par l'auteur** | [sans](../annexes/LOT-1019/captures/sans-halo-porte-1200.png) et [avec](../annexes/LOT-1019/captures/porte-porte-1200.png) à midi ; [sans](../annexes/LOT-1019/captures/sans-halo-porte-2200.png) et [avec](../annexes/LOT-1019/captures/porte-porte-2200.png) à 22 h |
| Les ombres portées des lampes | **à juger par l'auteur** | [sans](../annexes/LOT-1019/captures/sans-ombres-lampes-ruelle-1200.png) et [avec](../annexes/LOT-1019/captures/porte-ruelle-1200.png) à midi ; [sans](../annexes/LOT-1019/captures/sans-ombres-lampes-ruelle-2200.png) et [avec](../annexes/LOT-1019/captures/porte-ruelle-2200.png) à 22 h |

### La famille témoin — à juger par l'auteur à la recette

La façade au maître, six fois sur le parvis, au cadrage du joueur
([midi](../annexes/LOT-1019/captures/porte-facades-1200.png),
[22 h](../annexes/LOT-1019/captures/porte-facades-2200.png)), dans la porte entière
([parvis](../annexes/LOT-1019/captures/porte-parvis-1200.png),
[ruelle](../annexes/LOT-1019/captures/porte-ruelle-1200.png), et leurs captures de 22 h), et seule,
de ses quatre côtés ([midi](../annexes/LOT-1019/captures/controle-facade-quatre-cotes-1200.png),
[22 h](../annexes/LOT-1019/captures/controle-facade-quatre-cotes-2200.png) : face, droite ; dos,
gauche). À comparer à la carte peinte (`Source/Elements/Assets/Maps/capital/images/arenarea.png`)
et aux captures du 7 octobre ([`annexes/LOT-1012/captures/`](../annexes/LOT-1012/captures/)). Le
dos de la façade est fini (des arcades sans auvents) ; la caméra de capture, celle du joueur, ne
centre pas la pièce dans l'image.

### La commande des six façades

Écrite au gabarit révisé, dans l'atelier (`Tools/Assets3D/Regions/central-empire/capital/arenarea/commande.md`),
pour l'auteur, qui peint les références et commande à Meshy. Chacune : famille `02`, `tall`,
`solid` ; une image de référence de trois quarts, fond uni, sans ombre, dans la facture de la carte
peinte ; le dos, les côtés et le toit finis ; Meshy au maître, PBR activé ; hauteur et emprise
**ouvertes**.

| Pièce | Ce que la référence montre | Toutes faces |
|---|---|---|
| `facade-1`, la maison à loggia | haute et étroite, rez à refends et porte cintrée, loggia de trois arcades au dernier étage | dos à deux baies par étage, pignons aveugles |
| `facade-2`, l'échoppe à arcades | rez en arcades sur des devantures, auvents bourgogne, balconnets de fer forgé | réserve et porte de service ; arcade d'angle en retour |
| `facade-3`, la maison d'angle à tourelle | deux façades égales, tourelle ronde à toit conique à l'angle | faces de cour enduites, tourelle finie sur tout son tour |
| `facade-4`, la demeure à portique | portique de quatre colonnes de marbre sous fronton, fenêtres à frontons alternés | façade sur jardin et terrasse |
| `facade-5`, la maison à balcon de bois | balcon de bois sombre sur consoles, volets bourgogne, lucarne | escalier extérieur au dos |
| `facade-6`, la maison à tour carrée | corps à deux étages et tour carrée à baies géminées | tour finie sur ses quatre faces |

**Coût** : 30 crédits par pièce au barème des personnages — **à confirmer par l'auteur** — : 180
crédits pour les six, reprises non comprises.

### Ce qui se vérifie (9 octobre 2026, RTX 4060 Ti, Unreal Engine 5.8.3)

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | **702 tests de Core, 100 % passés** (Core n'a pas changé) |
| `powershell scripts/build.ps1 -Unreal` | code 0 : cible d'éditeur, `JadgContentCheck`, **26 tests du moteur passés** (`Jadg.Decor.Matiere` et `Jadg.Decor.TexturesPartagees` nouveaux), `jadg_map.py --check` (12 cartes, 0 erreur, 3 avertissements, ceux du LOT-1018), l'aller-retour réussi, le socle reconstruit et ses captures à leur référence (pire bloc 1,62 et 1,63 sur 255) |
| `powershell scripts/build.ps1 -Unreal -Parcours` | code 0 : la quête rendue 54 s après le lancement |
| `powershell scripts/build.ps1 -Unreal -ParcoursCombat -Seed 2` | code 0 : victoire au round 7, retour au parvis, le meneur à la même case, `encounter/arene-bandits/won` posé |
| `powershell scripts/build.ps1 -Unreal -Ecrans` | premier passage refusé : huit captures où le décor se voit (le HUD sur les étals, le combat sur l'arène, le menu) s'écartaient de leur référence, le sol des cartes d'essai, posé en instances, ayant désormais sa texture ; référence réécrite (`-UpdateReference`), puis rejoué : **code 0, les 24 captures à leur référence** |
| `powershell scripts/build.ps1 -Unreal -Map porte-1012 -Capture` | code 0 : les huit captures (quatre cadrages, deux heures) ; 91,3 images/s à midi, 88,3 à 22 h |
| `scripts/check.py --sans-hooks` | **18 contrôles verts** ; pytest 280 passés (26 nouveaux, ceux de `material_maps` et de la maquette retirés) ; `lint_planning`, `lint_docs`, cahier de test régénéré (697 cas) ; ruff passé ; Core inchangé, clang-format sans objet |
| `scripts/checks/check_orphans.py` (avec les kits et `Content/`) | aucun asset ni script orphelin, aucune sortie du moteur sans script |

### Les critères

| Critère | État |
|---|---|
| La famille témoin est validée par l'auteur sur le rendu du moteur, à midi et à 22 h, aux cadrages du joueur, comme « au niveau de la carte peinte » | **non tenu, ouvert** : jugement de l'auteur ; la famille n'a aujourd'hui qu'une pièce, posée six fois, les six variantes sont commandées (captures ci-dessus) |
| Le standard ne contient que des valeurs mesurées sur ce lot ou des décisions datées ; aucune valeur reprise du standard précédent sans remesure | **partiel** : §1, §3, §4, §6, §8 écrits sur les mesures du lot ou des décisions datées ; le §2 (format d'échange) est gardé **inchangé**, comme le lot le demandait, avec ses valeurs du LOT-1000 ; les critères du §5 sont la décision de l'auteur du 23 septembre ; la palette est une donnée du lieu (`region.json`) |
| Une pièce s'installe par script depuis sa fiche sans geste dans l'éditeur ; `check_orphans.py` cite chaque pièce installée | **tenu** : 105 pièces de kit, 49 maîtres, 9 pièces construites ; `check_orphans.py` vert avec `Content/` |
| Le poids du kit témoin et le nombre de triangles de sa plus grosse pièce sont écrits dans la fiche | **tenu** pour ce qui existe : la façade témoin (2 679 696 triangles, 87,7 Mio, 94,7 + 11,1 Mio dans le projet) et le kit de l'Arena of Fate (296,7 Mio, `af-arena-shell` à 877 645 triangles) |

| Livrable | État |
|---|---|
| `style-3d.md` réécrit | tenu (le §2 inchangé, à la demande du lot) |
| Le gabarit de commande révisé | tenu |
| `import_scenery_unreal.py` et son manifeste ; la vue Scenery de l'atelier | **partiel** : la chaîne et les fiches tenues ; la vue Scenery de l'atelier (LOT-1008) n'est pas livrée — l'atelier est une fenêtre Qt de l'ancien dépôt (D-58) ; ce qui en tient lieu est la carte de contrôle d'une pièce |
| Une famille témoin de six variantes au moins, rendue à midi et à 22 h | **partiel** : la seule façade au maître, six fois ; les six variantes sont une commande pour l'auteur |
| Le contour, la forme des familles, le budget d'un maillage de décor, tranchés sur captures | **partiel** : le budget et la forme tranchés ; le contour (et le post-traitement) rendus avec et sans, **à juger par l'auteur** |
| `material_maps.py` et la chaîne procédurale retirés ; les kits republiés au maître | **partiel** : les scripts retirés ; aucun kit n'est republié (l'Arena of Fate se reprend au LOT-1022, Arenarea au LOT-1021, les anciens kits partent au LOT-1023) |

### Ce qui s'écarte de la fiche

- **Le statut reste `a-faire`** : `lint_planning.py` refuse qu'un lot soit en cours sur un prérequis
  ouvert, et le LOT-1018 n'est pas livré.
- **La famille témoin n'a qu'une pièce** : Meshy ne se commande que par l'auteur (décision du
  8 octobre 2026). Le critère reste ouvert jusqu'au retour de la commande.
- **Aucune pièce de bibliothèque** : sur Fab, seul l'auteur se connecte ; le manifeste et son
  contrôle sont prêts, vides.
- **Le Colisée reste construit par script** (`build_colosseum.py`) : il perd ses cartes dérivées
  (une couleur et des facteurs, plus de relief peint) ; son image change à la porte. Ses pièces
  portent deux à quatre matières, ce que le §2 (une seule matière par modèle) interdit : la chaîne
  les prend, le standard l'écrit comme une pièce composée jusqu'au LOT-1021.
- **La commande vit dans l'atelier local**, pas dans le dépôt (décision du 23 septembre 2026) ; son
  inventaire est ci-dessus.
- **La référence des captures des écrans est réécrite** : le sol des étals et de l'arène d'essai,
  posé en instances, sortait lui aussi avec la matière par défaut ; il porte désormais sa texture.
- **`AGENTS.md` n'est pas modifié** : il cite encore `import_master_unreal.py` (ligne 42) et un
  §7 du standard « à réécrire » (ligne 47) ; c'est un fichier de consignes, laissé à l'auteur.
- **L'aller-retour journalise six avertissements de l'éditeur** (« *Error opening file* ») sur les
  matières et textures qu'Interchange avait créées pour les données d'essai et que la chaîne retire :
  le registre des assets les connaît encore au moment où le contrôle efface le dossier. Le contrôle
  passe.
- **Les annexes pèsent 59 Mo** (24 captures PNG en 1920 × 1080) : chaque question du §8 a ses
  captures avec et sans, à midi et à 22 h.

### Ce qui reste au lot

- **La commande des six façades** : l'auteur peint les références et commande à Meshy ; les
  retours se rangent (`build_master_manifest.py`, une fiche par façade dans `references.json`), se
  contrôlent (`build_piece_check.py`) et remplacent les six exemplaires de la porte.
- **Les jugements de l'auteur** : la famille témoin, le contour, l'occlusion, le halo, les ombres
  des lampes ; ce qu'il garde s'écrit dans la description de la porte (`lighting`) et au §8.
- Une pièce de bibliothèque, quand l'auteur en prend une sur Fab.
- Les deux lignes d'`AGENTS.md`.

### Questions pour l'auteur

1. **Le contour sombre** : le garder (et où : toutes les cartes, ou le décor seul), ou l'abandonner ?
   Sa force et sa couleur (bronze foncé du standard 2D) sont des réglages d'essai.
2. **L'occlusion ambiante d'écran, le halo, les ombres des lampes** : les garder tels quels ?
3. **La façade d'Arenarea** est-elle une façade (famille 02) ou un bâtiment (09) ? Les Bâtiments
   sont-ils des pièces Meshy entières ou des compositions de façades ?
4. **L'échelle des façades** : quelle hauteur au faîtage (12 m aujourd'hui, provisoire) ?
5. **Le coût Meshy** d'une pièce de décor : 30 crédits, comme un personnage ?
6. **Le parvis** : les façades du sud tournent leur devant vers la ruelle, et leur dos vers le
   parvis où marche le joueur. Est-ce voulu, ou faut-il les retourner ?
7. **La commande** : la garder dans l'atelier local (décision du 23 septembre), ou la verser aux
   annexes du lot pour qu'elle se relise dans la PR ?
8. **Le Colisée** : son relief dérivé est retiré ; reste-t-il construit par script jusqu'au
   LOT-1021, ou se commande-t-il en pièces modulaires à Meshy ?
