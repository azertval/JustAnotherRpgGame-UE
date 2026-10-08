# Les personnages 3D

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
| Les **armes** | les maîtres Meshy de `Source/Elements/Assets/Master/Weapons/`, importés par `import_master_unreal.py`, accrochés par socket (D-63, qui tranche D-42) | partagées |
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
| 4. **Poser le personnage** | la scène nomme la fiche (`"appearance"` d'un `characters` de `build_scene_unreal.py`) ; `AJadgWalker` l'applique au lancement (`JadgAppearance::Apply`) | le corps choisi par le paramètre `Body` de l'instance Mutable, les six clips, l'échelle, les armes aux sockets |
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
  description, à ajouter au LOT-1024 avec les corps de race.

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
  taille par espèce vient au LOT-1024.
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
2026), aux tailles du [standard](style-3d.md#7-les-images-tolérées) : 512 × 512 et 128 × 128. Le
portrait se peint avant toute pièce de référence : c'est lui qui fixe le visage.

## 9. Ce qui reste ouvert

| Question | Se tranche au |
|---|---|
| Les corps et têtes des 22 espèces : ce que MetaHuman atteint, ce qui demande Meshy ou Fab | LOT-1024 |
| Les couleurs et la garde-robe comme paramètres du créateur | LOT-1024 |
| Le contenu optionnel de MetaHuman sur le poste | l'auteur, par le lanceur Epic |
| Les quadrupèdes : Mutable ou un maillage désigné par la fiche | LOT-1025 |
| Le poids en mémoire graphique de huit personnages à l'écran | LOT-1024 (huit humanoïdes) |
| La compilation du créateur dans un jeu empaqueté | LOT-1023 |
