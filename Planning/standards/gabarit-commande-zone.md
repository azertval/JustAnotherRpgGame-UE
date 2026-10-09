# Gabarit de la commande d'une zone

Un lot d'assets de zone commence par **sa commande** : une page qui passe en revue les dix familles
du [standard](style-3d.md#6-les-familles-de-pièces-dun-lieu), dit pour chacune ce qui vient du
**commun** et ce que la zone produit en **propre** (voir l'[arborescence](arborescence-assets.md)),
et suit chaque pièce de la commande au maillage installé dans le moteur. Livré par le
[LOT-104](../versions/v0.1.0/v0.0.1-demo/lots/LOT-104-chaine-de-production-hd.md) pour les images,
**révisé au [LOT-1019](../versions/v0.1.0/v0.0.3-nouveau-moteur/lots/LOT-1019-chaine-de-decor.md)**
pour le nouveau moteur : une pièce se commande **au maître**, **toutes faces finies**, pour une
**caméra qui tourne** (D-49, D-53, D-56). Plus aucune pièce ne se commande en image.

## Où elle vit

Dans l'atelier local, sous le même arbre que la zone :
`Tools/Assets3D/Regions/<région>/<ville>/<zone>/commande.md`, avec les **images de référence**
peintes par l'auteur (`references/`). Comme tout `Tools/`, elles restent **locales** : rien n'y est
livré (décision de l'auteur, 23 septembre 2026). La fiche du lot qui passe la commande en recopie
l'inventaire et l'état de chaque pièce.

## Le chemin d'une pièce

| Étape | Qui | Ce qui en sort |
|---|---|---|
| 1. **Commander** | l'assistant écrit la fiche de commande de la pièce (ci-dessous) | la commande, dans l'atelier ; son inventaire, dans la fiche du lot |
| 2. **Peindre la référence** | l'auteur peint l'image de référence que la fiche décrit : la pièce seule, de **trois quarts**, au style du lieu, fond uni, sans ombre portée ni lumière orientée marquée | l'image, dans l'atelier |
| 3. **Générer** | l'auteur l'envoie à **Meshy**, **au maître** (sans réduction), **PBR activé**, et télécharge le `.glb` | le retour Meshy, dans le dossier de téléchargement |
| 4. **Ranger** | l'assistant ajoute le retour à `Source/Elements/Assets/Master/references.json` — son identifiant et sa **fiche** (`sheet` : famille, classe, emprise, type tactique, hauteur, lumière) —, puis `python scripts/assetsGeneration/build_master_manifest.py <dossier des retours>` | le `.glb` sous `Master/<famille>/`, son entrée au manifeste avec sa matière lue dans le fichier |
| 5. **Installer** | `import_scenery_unreal.py` (ou la première carte qui la pose, par `build_level.py`) | le maillage en Nanite, sa matière, ses textures compressées, dans le projet |
| 6. **Contrôler le dos** | `python scripts/maps/build_piece_check.py`, puis `powershell scripts/build.ps1 -Unreal -Map controle/<pièce> -Capture` | **quatre captures** — face, droite, dos, gauche —, à midi et à 22 h |
| 7. **Juger** | l'auteur, sur les quatre captures puis sur la pièce posée dans sa carte, aux cadrages du joueur ([D-54](../vision/decisions.md)) | `validée`, ou `à recommander` avec sa raison |

La commande ne modèle pas et ne retouche rien : une pièce qui ne tient pas se **recommande** (une
référence repeinte, une génération refaite), ou se corrige dans sa fiche quand c'est la mesure qui se
trompe — sa hauteur, son emprise —, pas le maillage. Une pièce au **dos pauvre** sur ses captures de
contrôle se recommande : sous une caméra qui tourne, il n'y a plus de dos caché.

Une pièce des **bibliothèques** du moteur (nature, sols, matières : [D-55](../vision/decisions.md))
ne se commande pas : sa fiche entre au manifeste des bibliothèques
(`Source/Elements/Assets/Library/manifest.json`) avec sa **licence** et son **identifiant**, et
suit les étapes 5 à 7. Rien ne s'achète sans l'auteur.

## La page

Recopier ce qui suit dans `commande.md`, puis le remplir.

````markdown
# Commande — <zone>

Lot : LOT-NNN. Lieu : `Regions/<région>/<ville>/<zone>/`. Accent : <couleur>.
Carte peinte : <chemin de la carte de l'auteur>. Direction artistique : <lien vers le référentiel>.

## Inventaire

| # | Famille | Origine | Du commun | Propre | État |
|---|---|---|---|---|---|
| 01 | Sols | bibliothèque / Meshy | | | |
| 02 | Façades et murs | Meshy | | | |
| 03 | Colonnes | Meshy | | | |
| 04 | Accès | Meshy | | | |
| 05 | Balustrades | Meshy | | | |
| 06 | Pièces maîtresses | Meshy | | | |
| 07 | Végétal | bibliothèque | | *néant : écarté, et pourquoi* | écarté |
| 08 | Mobilier | Meshy | | | |
| 09 | Bâtiments | | | | |
| 10 | Seuils | composé | | | |

Une famille ne reste jamais vide : elle est remplie, prise au commun, ou **écartée avec sa
raison**. La colonne « Origine » suit le standard (§6). La famille 01 livre d'abord sa dalle de
fond répétable, en trois variantes au moins.

## Commandes

### <identifiant-de-la-pièce>

| Champ | Valeur |
|---|---|
| Famille | `02` |
| Classe, type tactique | `tall`, `solid` |
| Hauteur, emprise | en mètres et en cases de 1,5 m — ou **ouvert**, avec la question |
| Lumière | aucune, ou couleur, portée, hauteur |
| Image de référence | `references/<pièce>.png` — ce qu'elle montre, en une phrase |
| Toutes faces | ce que montrent le dos et les côtés, que la référence ne voit pas |
| Meshy | au maître, PBR activé ; coût au barème connu |

Reçue le … (`<nom du retour Meshy>`). Contrôle du dos : <captures>. État : …

## Poids

<poids des pièces reçues, tel que `import_scenery_unreal.py` l'écrit> — pour mémoire : une zone n'a
pas de budget (D-23).
````

## Les états d'une pièce

`commandé` (fiche écrite) → `référence peinte` → `reçu` (retour Meshy rangé au maître) → `installé`
(dans le projet, quatre captures de contrôle) → `validé` (jugé par l'auteur dans sa carte) ; ou
`à recommander`, ou `écarté`, avec sa raison. Une pièce installée qui double une pièce du commun est
une faute : elle se **promeut** ou se retire (arborescence, règle 1).
