+++
id = "LOT-1012"
titre = "La porte : le parvis d'Arenarea dans Unreal"
version = "0.0.3"
filiere = "moteur"
statut = "livre"
taille = "L"
resume = "Le parvis d'Arenarea, le Colisée et deux personnages rendus par Unreal Engine 5, sous la caméra libre, à midi et à 22 h : la preuve que le nouveau moteur donne le rendu voulu et se pilote en texte."
prerequis = []
livrables = [
  "Un projet Unreal Engine 5 à part, hors du dépôt du jeu (`Tools/Unreal/Porte1012/`), avec sa version du moteur épinglée et son journal d'installation.",
  "La coque du Colisée (`af-arena-shell.glb`, 878 000 triangles), ses quatorze statues et ses bannières, cinq façades et le dallage du parvis importés **au maître**, en Nanite, avec leurs cartes de couleur, de relief et d'occlusion-rugosité-métal.",
  "Deux personnages liés (`brawler`, `lion`) importés avec leurs squelettes et leurs clips, qui marchent et se tiennent au repos.",
  "La caméra de D-49 : rotation, zoom, inclinaison bornée ; la marche au clic sur un maillage de navigation ; un cycle jour / nuit piloté par `daylight.json`, soleil et lumières de nuit, Lumen actif.",
  "La scène **construite par un script Python d'éditeur** depuis une description en JSON : aucun acteur posé à la main, aucun Blueprint.",
  "Une construction, un test et une capture **sans fenêtre**, en ligne de commande, depuis un script du dépôt.",
  "Les captures du moteur à midi et à 22 h, aux cadrages du joueur (parvis, porte du Colisée, ruelle), et la mesure de cadence et de temps d'ouverture, versées à la fiche.",
  "Le **verdict** de l'auteur, écrit en fin de fiche : la version s'ouvre, ou s'abandonne (pas de repli, D-57).",
]
criteres = [
  "L'auteur juge les captures à midi et à 22 h plus proches de la carte peinte d'Arenarea que le rendu du moteur maison du 7 octobre 2026 (jugement de l'auteur, sur les mêmes cadrages).",
  "La scène tient 60 images par seconde à 1080p sur le poste de référence (RTX 4060 Ti), Lumen et Nanite actifs, caméra en mouvement.",
  "La carte s'ouvre en moins de 5 secondes depuis le lancement.",
  "Le script de construction, relancé sur un projet vierge, redonne la même scène ; aucun fichier `.umap` ni `.uasset` n'a été modifié à la main (comparaison des empreintes avant et après).",
  "`build`, `test` et `capture` s'enchaînent en ligne de commande, sans ouvrir l'éditeur, et sortent en 1 à la première erreur.",
  "Les deux personnages marchent sans glissement ni pénétration du sol, aux seuils du standard des personnages (1,3 mm, 0,53 px à 1080p).",
]
sources = [
  "Plan d'action du 7 octobre 2026 — https://claude.ai/artifact/AHU61AmvLTCPBmDmUBd2Em",
]
+++

## Pourquoi

Toute la version repose sur deux hypothèses que rien n'a prouvé dans ce projet : qu'Unreal rend le
décor existant au niveau que l'auteur attend, et qu'il se pilote **en texte** comme le reste du
dépôt. La `0.0.2.5` s'est ouverte sur une porte de ce genre (LOT-1000) et l'a justifiée : une
journée pour éviter de bâtir un atelier sur une hypothèse fausse. Ici la porte coûte une à deux
semaines et épargne deux mois.

## Périmètre

Dedans : un projet neuf, les pièces les plus abouties du dépôt (le Colisée et ses sculptures, cinq
façades, le dallage), deux personnages, la caméra, la marche, la lumière, la construction par
script, la mesure. Les quatre questions Q-17 à Q-20 ont été tranchées le 7 octobre 2026 (D-55 à
D-58) : bibliothèques du moteur admises pour la nature, caméra libre, pas de repli, nouveau dépôt.
La porte se joue dans un projet à part ; le nouveau dépôt se crée au LOT-1014, sur son verdict.

Dehors, nommément :

- le dépôt du jeu : pas une ligne de `Source/` ne change ; l'ancien moteur se joue comme avant ;
- les règles, le combat, l'interface, les quêtes : rien de Core n'entre dans la porte ;
- la chaîne de décor et le standard 3D (LOT-1019) : les pièces s'importent telles qu'elles sont ;
- Arenarea entier : trois cadrages suffisent à juger.

## Conception

- **Les pièces viennent du kit, pas d'un nouvel atelier.** Le Colisée, ses statues et ses bannières
  sont déjà au maître et avec leurs trois cartes (D-46) ; les cinq façades sont des retours Meshy
  d'Arenarea. Si ces pièces ne convainquent pas dans Unreal, le moteur n'est pas en cause.
- **La description de scène** est un JSON : une liste d'objets avec leur maillage, leur position en
  mètres, leur rotation et leur échelle ; un terrain plat ; les sources de lumière déclarées comme
  aujourd'hui par le manifeste (`light`, `glow`). C'est l'embryon du format du LOT-1018.
- **La caméra** est libre (D-56), bornée en inclinaison entre une vue rasante et une vue
  plongeante ; le dallage et une végétation d'essai peuvent venir des bibliothèques du moteur
  (D-55), les façades et le Colisée non.
- **Lumen et Nanite** sont les réglages par défaut du moteur, sans précalcul : c'est la continuité
  de D-45. Le cycle jour / nuit lit `daylight.json` tel quel.
- **La mesure** se fait au même endroit que celle de la fiche du LOT-1007 : 1080p, poste de
  référence, caméra en mouvement, `stat unit` et `stat gpu` relevés sur dix secondes.
- **Les captures** se prennent par Movie Render Queue en ligne de commande, aux trois cadrages,
  aux deux heures ; elles se rangent à côté de celles du 5 et du 7 octobre pour comparaison.

## Risques et questions ouvertes

- **Le temps d'installation.** Unreal pèse 60 à 100 Go et compile plusieurs minutes : le poste doit
  avoir la place avant d'ouvrir le lot.
- **Le squelette.** Si l'importateur refuse les clips liés par `rig_character.py` (durées, échelle),
  le reciblage par l'IK Retargeter est la voie ; le LOT-1015 en hérite.
- **Le verdict partagé.** Rendu convaincant mais méthode cassée (un geste de l'éditeur impossible à
  rejouer par script) : sans repli (D-57), c'est à l'auteur de dire s'il accepte une exception
  écrite à D-52 ou s'il abandonne ; la fiche l'écrit, datée.

## Avancement — 8 octobre 2026

La porte tourne de bout en bout, sans fenêtre, par une seule commande :

    powershell scripts/build.ps1 -Unreal -Scene porte-1012 -Capture

Elle construit la cible d'éditeur, lit le contenu (`JadgContentCheck`), reconstruit la carte
depuis `Source/Elements/Scenes/porte-1012.json` (`scripts/maps/build_scene_unreal.py` : 3 950
objets, 2 personnages, 3 cadrages), lance le jeu hors écran, écrit six captures et `mesure.json`,
et sort en 1 à la première erreur. Mesuré le 8 octobre : 83 s, code 0, assets déjà importés.

Les captures sont dans [`annexes/LOT-1012/captures/`](../annexes/LOT-1012/captures/) :
`parvis`, `porte`, `ruelle`, à `1200` et à `2200`. **Le verdict de l'auteur reste à écrire.**

### Mesures (RTX 4060 Ti, 1920 × 1080, Lumen et Nanite actifs, caméra en rotation de 36°/s)

| Heure | Images par seconde | Trame moyenne | 1 % le plus lent | Pire trame | Processeur graphique |
|---|---|---|---|---|---|
| 12:00 | 119 | 8,4 ms | 12,1 ms | 17,2 ms | 5,6 ms |
| 22:00 | 118 | 8,5 ms | 10,3 ms | 11,6 ms | 6,0 ms |

Relevé par le jeu lui-même sur 11,5 s par heure (`Capture/JadgCaptureDirector`), pas par
`stat unit` et `stat gpu`. Le critère des 60 images par seconde est tenu sur cette scène.

**Ouverture** : 15,5 s entre le lancement du processus et la première trame de la carte (26,6 s
au lancement précédent, caches froids), dont 2,3 s de chargement de la carte. Le jeu est lancé
par les binaires de l'éditeur (`-game`), pas empaqueté : le critère des 5 s n'est **pas tenu**
dans cette forme, et ne se juge vraiment que sur un jeu empaqueté, que la porte ne produit pas.

### Ce qui s'écarte de la fiche

- **Le projet n'est pas à part.** Le nouveau dépôt existait déjà (LOT-1014 commencé le 7 octobre) :
  la porte s'est jouée dedans, pas dans `Tools/Unreal/Porte1012/`.
- **Les cinq façades n'existent pas.** Les cinq retours Meshy d'Arenarea sont un arbre, un cyprès,
  une enseigne, une statue et un char. Le dossier de l'auteur ne porte qu'un bâtiment,
  `Terracotta_Palazzo` : il est posé cinq fois, à 12 m de haut — hauteur **choisie, non mesurée**,
  marquée `provisional` dans la description. À trancher par l'auteur.
- **Les sculptures viennent du maître**, reliées par leur nom Meshy (`build_gate_scene.py`) : les
  quatorze statues et les deux lions du kit sont remplacés par les maîtres du 7 octobre, leur pose
  mesurée par superposition (recouvrement de 0,80 à 0,92).
- **Les captures ne passent pas par Movie Render Queue** mais par la caméra du joueur, dans le jeu
  lancé hors écran : c'est l'image que le joueur a.
- **Un peu de C++ d'éditeur** (`Scene/JadgSceneBuild`) : créer un acteur et donner sa forme à un
  volume de navigation ne se font pas en Python sans fenêtre dans la 5.8. Le script les appelle ;
  aucun geste à la main, aucun Blueprint. D-52 tient.
- **Le maillage de navigation** se calcule au lancement (`RuntimeGeneration=Dynamic`), il n'est pas
  dans la carte.

### Ce qui reste, avant le verdict

- **Les deux personnages sortent presque noirs.** Leur `.glb` lié ne porte qu'une carte de couleur ;
  le métal par défaut de glTF (1) s'applique. À corriger dans la chaîne (LOT-1015), pas à la main.
- **Le ciel de midi est sombre et la nuit claire** : la table `daylight.json` est appliquée telle
  quelle, à exposition fixe. Réglage à juger sur les captures.
- **Le sol s'arrête au bord du dallage** : au-delà, le vide.
- **La marche** (clic, navigation, glissement et pénétration aux seuils du standard) n'est pas
  mesurée : le lion fait sa ronde sur les captures, rien de plus n'est vérifié. La caméra et le
  clic n'ont pas été essayés dans une fenêtre.
- **Les empreintes avant / après** d'une reconstruction sur projet vierge ne sont pas comparées.
- **Le poids** : `Content/` fait 3,1 Go, hors Git ; la question du quota LFS (PASSATION) reste
  ouverte.

## Reprise après le premier retour de l'auteur — 8 octobre 2026

L'auteur, sur les premières captures : « le colisée est beaucoup trop petit », « les textures /
éléments 3D ne sont pas encore de qualité suffisante, il faut pousser encore plus le rendu pour
avoir un aspect plus propre et moderne », « pour le personnage le mesh est rendu sans texture » ;
puis : « pour la taille rendue de l'arena base-toi sur le Colisée de Rome ». Les captures de
l'annexe sont **celles d'après cette reprise** ; les mesures ci-dessus sont celles d'avant.

- **Le Colisée est à la hauteur de celui de Rome** : 48 m. La coque du kit fait 17,54 m de haut,
  le groupe est donc posé à l'échelle 2,7366 (`groups[].scale`) et mesure 134 × 96 m, pour
  189 × 156 m à Rome : ses proportions ne sont pas celles du modèle, et une échelle par la longueur
  (× 3,86) l'aurait porté à 68 m de haut. Statues, lions, bannières et feux suivent ; les statues
  font 7,7 m. Choix de l'axe à confirmer par l'auteur.
- **Les personnages ont leur texture.** La matière qu'Interchange donne à un `.glb` n'est pas
  compilée pour un maillage lié : le jeu la remplaçait par la matière par défaut (journal du
  moteur : « missing usage flag SkeletalMesh »). Le script crée `M_Character` et une instance par
  personnage, portée par l'acteur. Vaut pour le LOT-1015.
- **Le rendu** : anticrénelage temporel (TSR ; le projet n'en avait aucun), soleil × 1,8 et lumière
  du ciel × 0,45 pour laisser Lumen porter la lumière rebondie, ciel éclairci, brume volumétrique,
  halo, vignette, ombres de contact, lampes à 60 cd, un sol uni jusqu'à l'horizon. Tout se règle
  dans `lighting` et `ground` de la description ; valeurs provisoires, à juger.

| Heure | Images par seconde | Trame moyenne | 1 % le plus lent | Pire trame | Processeur graphique |
|---|---|---|---|---|---|
| 12:00 | 110 | 9,1 ms | 11,1 ms | 13,9 ms | 7,9 ms |
| 22:00 | 107 | 9,3 ms | 11,3 ms | 12,8 ms | 8,2 ms |

8 002 objets ; ouverture en 16,3 s (même réserve : jeu non empaqueté).

**Ce que le moteur ne corrige pas.** La coque du Colisée porte toute sa surface sur trois images
de 3072 × 2048 ; agrandie 2,7 fois, sa pierre est floue de près, et ses moulures sont des boîtes.
Le dallage est une dalle de 1,5 m répétée. Le palazzo, les statues et les lions, au maître,
tiennent le gros plan ; les pièces de l'ancien kit, non. Un rendu « propre et moderne » demande
que la coque et les sols soient refaits au maître (LOT-1019) ou pris dans les bibliothèques du
moteur pour les sols et matières (D-55) : la porte ne peut que le constater.

## Deuxième reprise — le Colisée en pièces, 8 octobre 2026

L'auteur, sur les captures de la première reprise : « il faut vraiment se rendre compte de la
taille de l'arena of fate et que le parvis rende sa grandeur par rapport aux images de référence ;
aujourd'hui l'arena est composée d'un seul asset mais il faudrait plutôt le rendre en plusieurs
pour pouvoir avoir un vrai rendu de qualité ». La coque agrandie est **retirée de la scène** ; le
Colisée est reconstruit en pièces, aux dimensions de celui de Rome.

- **Le générateur** `scripts/assetsGeneration/build_colosseum.py` (Blender sans fenêtre, lancé par
  le Python du poste) produit neuf pièces sous `Source/Elements/Assets/Built/colisee/` avec leur
  manifeste (empreintes, triangles, dimensions) : une travée de chaque ordre (toscan, ionique,
  corinthien : demi-piliers, arc, écoinçons, entablement à denticules, colonne engagée cannelée,
  galerie derrière l'arc, garde-corps de marbre aux étages), une travée d'attique (pilastres,
  fenêtre, corbeaux, mât de velum et flamme), la porte axiale (tours à colonnes jumelées, arc de
  10 m sur 19 m traversant deux ordres, panneau d'attique, socles des lions, tunnel de 54 m
  jusqu'au sable avec ses lampadaires), un quart des gradins (podium, 52 rangs, deux promenoirs,
  galerie haute ; ouvert sur l'axe sous la voûte du tunnel, fermé au-dessus), la loge impériale,
  le sable, le socle d'une statue. **Chaque face est texturée au mètre** (la pierre se répète tous
  les 3 m, le marbre tous les 2 m, en projection absolue : pas de couture entre faces coplanaires) ;
  chaque matière porte ses cartes de relief et d'occlusion-rugosité-métal dérivées par
  `material_maps.py` (D-46). Les textures sont les cinq couleurs de base de l'atelier de l'Arena
  of Fate, copiées hors Git sous `Tools/`. Les pièces sont hors des kits verrouillés (`.gitignore`,
  `Built/**/*.glb`) : le manifeste seul est suivi.
- **L'anneau** est calculé une seule fois, `build_colosseum.ring_bays()` : 80 cordes à longueur
  d'arc égale sur l'ellipse de 189 × 156 m (périmètre 543 m, travée de 6,79 m), la travée 0 plein
  sud ; chaque pièce est posée au milieu de sa corde, tournée sur la normale sortante ; les
  demi-piliers des bouts se recouvrent. `build_gate_scene.py` est réécrit : il pose 77 travées par
  ordre et 80 d'attique, la porte à la place des trois travées du sud, les gradins quatre fois par
  symétrie (deux en miroir), la loge au nord, le sable ; puis les **quatorze dieux au maître**
  dans les arcs du deuxième ordre de part et d'autre de la porte, à 5,2 m sur leur socle, les deux
  lions à 5 m sur les tours, dix-sept bannières du kit pendues à l'attique (l'empire au-dessus de
  la porte ; le Culte n'y flotte pas), huit feux sur le podium et deux vasques devant la porte.
  373 objets ; `build.ps1 -Scene porte-1012` refuse un `colisee.json` périmé (`--check`). La
  méthode de pose par superposition au kit (première version du script) n'a plus d'objet et est
  retirée avec ses tests ; les tests portent maintenant sur l'anneau.
- **La scène** : le groupe à l'échelle 1, centre à Z = −60,5 (façade sud à 17,5, porte à 19) ; le
  dallage s'arrête au pied du Colisée (`fills[].excludeEllipses`) ; le repère se mesure sur le
  quart de gradins. Les cadrages changent pour que la taille se lise : `parvis` depuis le sud,
  au-dessus des toits, à 118 m, la façade d'un bord à l'autre et les maisons pour échelle ; `porte`
  depuis le parvis à 34 m, presque à hauteur d'homme, la porte et ses lions vus d'en bas.
- **L'import** d'une pièce construite est rejouable : `build_scene_unreal.py` note l'empreinte du
  `.glb` importé (`Intermediate/Jadg/imports.json`) et réimporte une pièce régénérée.

L'aperçu Blender de l'anneau (Workbench, avant Unreal) a servi à régler la porte, d'abord trop
modeste (9 m sur 14,5 m) pour une façade de 48 m.

Construit et capturé le 8 octobre 2026 par `powershell scripts/build.ps1 -Unreal -Scene porte-1012
-Capture -EnginePath "E:\Epic Games\UE_5.8"` (le registre ne donne pas le moteur depuis ce
shell ; `pwsh` n'existe pas sur le poste) : 4 032 objets, 9 imports, code 0. Les captures de
l'annexe sont celles-ci ; la mesure :

| Heure | Images par seconde | Trame moyenne | 1 % le plus lent | Pire trame | Processeur graphique |
|---|---|---|---|---|---|
| 12:00 | 119 | 8,4 ms | 11,1 ms | 12,4 ms | 7,2 ms |
| 22:00 | 107 | 9,3 ms | 14,4 ms | 18,7 ms | 7,3 ms |

Ouverture en 17,3 s (même réserve : jeu non empaqueté). Le quart de gradins (48 000 triangles)
est posé quatre fois, les 320 travées sont quatre maillages : le monument de 189 m coûte moins
que la coque agrandie.

**Ce qui reste à juger par l'auteur, sur ces captures :** la lecture de la taille (le cadrage
`parvis` montre le quartier au pied du monument ; les maisons à 12 m, hauteur provisoire, en
donnent l'échelle) ; la facture des pièces (une seule texture de pierre et une de marbre, sans
usure ni variation d'une travée à l'autre ; les chapiteaux et les claveaux sont géométriques, sans
sculpture) ; la nuit, toujours claire (table du jour appliquée telle quelle). Le ciel de midi, la
brume et l'exposition n'ont pas changé depuis la première reprise.

## Clôture — 8 octobre 2026

L'auteur clôt le lot le 8 octobre 2026 : « lot 1012 terminer ». La fiche passe à `livre` sur cette
décision, PR_PLACEHOLDER. Il n'a pas écrit d'autre verdict que celui-là ; la version continue
(le LOT-1014 est déjà ouvert sur ce dépôt).

Le lot est clos **sans que tous ses critères soient tenus** ; ce qui manque est écrit ici, pour le
lot qui le reprend ou pour l'auteur :

- **L'ouverture en moins de 5 s** n'est pas tenue (15,5 à 17,3 s, jeu lancé par les binaires de
  l'éditeur) et ne se juge que sur un jeu empaqueté : question ouverte, à la recette (LOT-1023) au
  plus tard.
- **La marche aux seuils du standard** (glissement, pénétration du sol) n'est pas mesurée ; la
  caméra et le clic n'ont pas été essayés dans une fenêtre : LOT-1016.
- **Les empreintes avant / après** d'une reconstruction sur projet vierge ne sont pas comparées :
  question ouverte.
- **Les cinq façades** n'existent pas (un palazzo posé cinq fois, hauteur provisoire de 12 m) ; la
  facture des pièces du Colisée et des sols reste à juger : LOT-1019 et LOT-1021.
- **La matière des personnages** dans la chaîne (`M_Character` est créée par le script de scène) :
  LOT-1015.
- **`Content/` n'est pas suivi** (3,3 Go de `.uasset` et de `.umap` régénérables par
  `build.ps1 -Unreal -Scene porte-1012`) : le quota Git LFS reste à trancher par l'auteur
  (`PASSATION.md`).
