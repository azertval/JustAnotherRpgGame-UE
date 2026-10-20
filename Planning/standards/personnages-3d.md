# Les personnages 3D

## Cadre applicable depuis le 20 octobre 2026

La [révision D-68](../vision/decisions.md) remplace les obligations de fournisseur MetaHuman,
d'assembleur Mutable et de squelette universel. Le besoin confirmé est un **créateur complet
en jeu**, avec réglages du visage et du corps. Les sections numérotées ci-dessous conservent
les mesures et le contrat provisoire du LOT-1015 ; elles ne prouvent pas la chaîne finale.

- **LOT-1024** : comparaison de fabrication et d'assemblage, prototype empaqueté, décision
  sur mesures avant production ; Mutable premier candidat, modulaire natif en comparaison,
  MetaHuman ou Character Creator comme sources possibles. Collections reste une option à
  vérifier, pas l'équivalent présumé de MetaHuman Creator dans le jeu.
- **LOT-1026** : familles anatomiques, bases, morphs d'identité, rigs, recettes versionnées
  et migration. L'identité reste distincte des expressions ; les rigs peuvent différer.
- **LOT-1027** : vêtements adaptés aux plages corporelles, matériaux, masques et compatibilités.
- **LOT-1028** : interface de création en jeu et mode de production sur le même générateur.
- **LOT-1029** : héros et PNJ de la démo, presets métiers et migration des remplacements.
- **LOT-1025** : lion/loup avec rigs et animations de provenance vérifiée.
- **LOT-1030** : validation empaquetée, densité et coûts, puis publication du standard final.

Les Gloomfolk exigent un bas de corps de scorpion ; les Taii'maku six doigts. Le contrat
commun porte sur les actions et les équipements, pas sur un nombre d'os unique.
La préparation initiale des sources doit être démontrée et chiffrée au LOT-1024 ; la cible
est l'absence de correction individuelle lors de l'assemblage de chaque PNJ.
Les sources et exports sont conservés, les sorties Unreal régénérables ; les règles restent
dans Core et la logique d'interface en C++. Un JSON ne convertit pas automatiquement les
UV, morphs ou vêtements lors d'un changement de base.

Les seuils sont fixés avant les essais selon le matériel et les scènes cibles. Le jeu
empaqueté doit prouver les curseurs, les vêtements aux extrêmes combinés, les animations,
la sauvegarde et la reconstruction. Les mesures de huit mannequins ne valent pas capacité
de foule. Les portraits et jetons peints restent inchangés (D-30).

## État historique mesuré au LOT-1015

> **Réécrit au [LOT-1015](../versions/v0.1.0/v0.0.3-nouveau-moteur/lots/LOT-1015-personnages-et-createur.md),
> 8 octobre 2026**, sur les décisions [D-63](../vision/decisions.md) et [D-64](../vision/decisions.md)
> et sur ce que le lot a mesuré dans Unreal Engine 5.8.3. La page précédente décrivait la chaîne de
> l'ancien moteur (squelettes `humanoid` et `quadruped`, clips posés par cibles, retouche dans
> Blender, contrôles de l'export) ; elle est supprimée avec cette chaîne (D-64) et reste lisible
> dans l'histoire du dépôt et dans les fiches de la `0.0.2.5`.

Un personnage est **une fiche texte** que le **créateur de personnage** du moteur assemble. Cette
page fixe ce contrat. Elle complète le [standard 3D](style-3d.md) et, comme lui, n'écrit que des
valeurs **mesurées** ou des **décisions datées** de l'auteur ; ce qui n'est ni l'un ni l'autre est
écrit comme ouvert, avec le lot qui le tranche.

## 1. Ce dont est fait un personnage

| Élément | Où | Partagé ou propre |
|---|---|---|
| La **fiche d'apparence** : créateur, corps, tête, taille, couleurs, pièces, arme de chaque main, instant d'impact des clips | `Source/Elements/Rpg/appearances/<id>.json`, schéma `appearance.schema.json`, même identifiant que la fiche de règles (`Rpg/characters/`) | propre |
| La **fiche de règles** (classe, espèce, inventaire) | `Source/Elements/Rpg/characters/<id>.json` | propre ; un PNJ de scène peut n'avoir qu'une fiche d'apparence |
| Le **créateur** : un objet personnalisable Mutable, ses corps, ses clips, ses sockets | décrit par `Source/Elements/Assets/Characters/<creator>.json` ; construit sous `Content/Characters/Creator/` par le commandlet `JadgBuildCharacterCreator` | partagé par tous les personnages de sa famille (`humanoid`) |
| Le **squelette** et les **clips** | ceux du moteur : le mannequin d'Unreal (`SK_Mannequin`) et ses animations, posés sous `Content/Characters/Mannequins/` par `import_mannequin_unreal.py` | partagés |
| Les **armes** | les maîtres Meshy de `Source/Elements/Assets/Master/Weapons/`, installés par `import_scenery_unreal.py` (LOT-1019), accrochés par socket (D-63, qui tranche D-42) | partagées |
| Le **portrait** (512 × 512) et le **jeton** (128 × 128), **peints** | avec le personnage, comme avant (D-30) | propres |

Ce qui a changé par rapport à D-38 : plus de maillage par personnage, plus de fiche de liaison,
plus de clip posé par le dépôt. Ce qui faisait le but de D-31 et de D-38 — un squelette et des
animations communs — est tenu par le moteur.

## 2. La chaîne

| Étape | Qui | Ce qui en sort |
|---|---|---|
| 1. **Poser les corps et les clips du moteur** | `scripts/assetsGeneration/import_mannequin_unreal.py --engine <moteur>` : copie, depuis `Templates/TemplateResources/High/Characters/Content/Mannequins/`, les maillages, matières, textures, rigs et six clips, au même chemin de contenu | 32 assets sous `Content/Characters/Mannequins/` (87 Mio) ; rejoué, rien ne se recopie si l'empreinte est la même |
| 2. **Construire le créateur** | `UnrealEditor-Cmd … -run=JadgBuildCharacterCreator`, sans fenêtre, depuis `Assets/Characters/humanoid.json` | `Content/Characters/Creator/CO_Humanoid.uasset` (150 Kio), compilé ; rejoué, gardé si la description n'a pas changé (empreinte dans les métadonnées du paquet), `-JadgForce` reconstruit |
| 3. **Écrire la fiche** d'un personnage | à la main, dans `Rpg/appearances/` ; `check_rpg_data.py` la valide contre son schéma, Core la lit (`core::readAppearance`) | une fiche |
| 4. **Poser le personnage** | la scène nomme la fiche (le `party` d'une carte, ou l'`appearance` d'une entité `npc`, que `build_level.py` pose) ; `AJadgWalker` l'applique au lancement (`JadgAppearance::Apply`) | le corps choisi par le paramètre `Body` de l'instance Mutable, les six clips, l'échelle, les armes aux sockets |
| 5. **Contrôler** | `scripts/build.ps1 -Unreal` : les étapes 1 et 2, puis les tests `Jadg.Personnages.*` ; les captures de la scène d'essai | les relevés de la fiche du lot ; les captures que l'auteur juge à la recette |

Les deux premières étapes sont celles de `scripts/build.ps1 -Unreal` : aucun geste dans l'éditeur,
aucun asset fait à la main (D-52, D-60).

## 3. Le créateur

Mesuré le 8 octobre 2026, Unreal 5.8.3, plugin Mutable (bêta) :

- Les classes de nœuds du graphe Mutable sont **privées** au plugin ; ce sont des `UCLASS`. Le
  commandlet les retrouve par leur chemin (`/Script/CustomizableObjectEditor.…`), crée les nœuds
  par `NewObject`, écrit leurs propriétés par `ImportText` (chemins d'objets **complets**,
  `/Game/…/SKM_Manny_Simple.SKM_Manny_Simple`), relie les broches par le schéma du plugin, puis
  compile de façon synchrone et enregistre le paquet. La fonction de bibliothèque du plugin
  (`NewCustomizableObject`) synchronise l'explorateur de contenu et **ne tient pas sans fenêtre** :
  l'objet se crée par sa fabrique.
- Le graphe d'un corps (5.8) : nœud **Skeletal Mesh** (une broche `LOD i - Section j - Mesh` par
  section) → **Skeletal Mesh Section** (matière de la section) → **Skeletal Mesh Make** (broche
  `LOD 0`, tableau) → **Skeletal Mesh Object Make** → **Component Skeletal Mesh** (nom `Body`,
  maillage de référence) → **Component Switch** (sa catégorie de broches se donne à la création,
  elle ne vient qu'au chargement sinon) ← **Enum Parameter** `Body` → l'objet racine, broche
  `Components`.
- Compilation : 43 opérations, 5,4 Mio de données diffusées, 0,1 s pour trois corps (Manny,
  Quinn, et `mannequin`, le même maillage que Manny). Un objet chargé depuis le disque n'est pas
  compilé dans l'éditeur tant qu'on ne le lui demande pas : l'acteur le demande (`Compile`,
  synchrone) ; en jeu empaqueté, la cuisson le fait (à vérifier au LOT-1023).
- Ce que le créateur **ne fait pas encore** : les têtes (`head` est lu, pas joué), les couleurs
  (lues, pas jouées : la matière du mannequin n'a pas de paramètre de peau), les pièces de
  garde-robe (aucune dans le contenu du moteur). Ce sont des paramètres de plus dans la
  description ; leur remplacement est éprouvé au LOT-1024, puis livré aux LOT-1026 et LOT-1027.

## 4. MetaHuman

Mesuré le 8 octobre 2026 : MetaHuman Creator (plugin `MetaHumanCharacter`, dans l'éditeur) se
pilote en Python sans fenêtre, avec `-nullrhi` comme avec le processeur graphique — un asset
`MetaHumanCharacter` se crée, s'ouvre à l'édition, ses **30 contraintes du corps** (`Height`,
`Chest`, `Waist`, `Inseam`…) se lisent et s'engagent (`commit_body_state`, taille 190 cm). La
**peau et l'assemblage** (`commit_skin_settings`, `build_meta_human`) s'arrêtent sur une assertion
`BodyTexture` : le dossier `MetaHumanCharacter/Content/Optional/` du moteur n'est pas installé sur
le poste (textures du corps, modèles de synthèse de texture). Il s'installe par le lanceur Epic
(contenu optionnel de MetaHuman Creator) ; c'est un geste de l'auteur. D'ici là, les corps sont
ceux du mannequin, et le bloc `metahuman` des fiches attend.

## 5. Les clips

Les six clips du jeu et l'animation du mannequin qui les joue (`humanoid.json`) :

| Clip | Animation du moteur | Remarque |
|---|---|---|
| `idle` | `Anims/Unarmed/MM_Idle` | boucle |
| `walk` | `Anims/Unarmed/Walk/MF_Unarmed_Walk_Fwd` | boucle, jouée au prorata de la vitesse réelle (`WalkSpeed`) |
| `attack` | `Anims/Unarmed/Attack/MM_Attack_01` | une fois ; impact à `key` de la fiche (0,4 s pour les héros) |
| `cast` | `Anims/Unarmed/Attack/MM_ChargedAttack` | une fois ; le contenu du moteur n'a pas de clip de sort, c'est l'attaque chargée qui tient la place (à juger par l'auteur) |
| `hit` | `Anims/Rifle/HitReact/MM_HitReact_Front_Med_01` | une fois |
| `death` | `Anims/Death/MM_Death_Front_01` | une fois |

L'instant d'impact (`key`) est une donnée de la **fiche d'apparence**, en secondes, lue par Core
(`clipKeys`) et portée par l'acteur (`ClipKeys`) : le combat (LOT-1017) y accroche le touché de la
cible. Les clips se jouent sans graphe d'animation ni Blueprint (`AnimationSingleNode`) ; un clip
joué une fois (`PlayOnce`) reste sur sa dernière image jusqu'au prochain ordre — le retour au repos
est à écrire au LOT-1017 avec le tour de combat.

La règle de la marche de l'ancien moteur (une case de 1,5 m en 0,5 s) ne vaut plus : la vitesse
est celle de l'acteur (`WalkSpeed`, 3 m/s), le clip suit.

## 6. La taille, les armes

- **La taille** de la fiche (`height`, du sol au sommet du crâne, en mètres) met l'acteur à
  l'échelle `height / referenceHeight` (1,80 m pour le mannequin), capsule comprise, debout au
  même point du sol. Les fiches des quatre héros portent 1,95 m (Grom), 1,80 m (Faelar), 1,45 m
  (Helga), 1,70 m (Nessa) — des valeurs de départ, **à juger par l'auteur à la recette** ; une
  taille et des plages de proportions par famille viennent au LOT-1026 après preuve au LOT-1024.
- **Les armes** : la pièce de `Master/Weapons` nommée par la fiche (`main-hand`, `off-hand`),
  accrochée à l'os `hand_r` ou `hand_l` du mannequin (`sockets` de `humanoid.json`), sans
  collision. L'orientation d'un maître Meshy dans la main n'est pas réglée : **à juger par
  l'auteur à la recette**, et à régler par une donnée de la description (un décalage par pièce),
  pas à la main.

## 7. L'image de référence (pour une pièce Meshy)

Décision de l'auteur, 1er octobre 2026, qui vaut pour toute pièce que Meshy produit (cornes,
défenses, queues, armures signatures, armes) : le maillage se génère depuis **une vue de face en
pose neutre**, peinte par le générateur d'images d'après le portrait validé — de face, fond uni,
sans ombre au sol, la facture et la palette du portrait. Un maillage refusé se **régénère**, il ne
se retouche pas.

## 8. Portrait et jeton

**Portrait et jeton restent peints** ([D-30](../vision/decisions.md), maintenue le 8 octobre
2026), aux tailles du [standard 2D archivé](archives/style-2d-hd.md#5-les-figurines) : 512 × 512 et 128 × 128. Le
portrait se peint avant toute pièce de référence : c'est lui qui fixe le visage.

## 9. Ce qui reste ouvert

| Question | Se tranche au |
|---|---|
| Choix de fabricant, assembleur et préparation initiale ; prototype avec curseurs en jeu | LOT-1024 |
| Les bases, rigs et morphs des 22 entrées actuelles ; écart Soulborn/corpus | LOT-1026 |
| Les couleurs, matériaux, garde-robe et adaptation aux corps | LOT-1027 |
| L'interface complète visage/corps et sa sauvegarde | LOT-1028 |
| Les héros et PNJ, les presets professionnels | LOT-1029 |
| Le contenu optionnel de MetaHuman si cette voie est retenue | vérification au LOT-1024 |
| Les quadrupèdes : rigs/clips sourcés, maillage direct ou générateur | LOT-1025 |
| Les coûts du groupe proche et des densités de rue/arène | seuils LOT-1024, recette LOT-1030 |
| La génération et la cuisson dans un jeu empaqueté | preuve LOT-1024, livraison LOT-1028, recette LOT-1030 |
