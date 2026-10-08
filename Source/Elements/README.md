# Source/Elements/

**Assets et éléments statiques** du jeu.

## Périmètre
- `Levels/` — cartes (`.json`) au format de l'ancien moteur ; le format de carte du nouveau est le
  `LOT-1018`.
- `Localization/` — catalogues de traduction (`.lang`, `.ts`).
- `Assets/` — images, maillages et polices (scènes, PNJ, cartes peintes, illustrations, polices,
  maillages au maître) ; voir `Assets/README.md`.
- `Rpg/` — catalogues du jeu de rôle (espèces, classes, historiques, compétences, créatures,
  équipement, règles et leurs schémas).
- `World/` — atlas du monde (régions, villes, lieux), plans de ville, dialogues et quêtes.
- `Scenes/` — descriptions de scène, d'où `scripts/maps/build_scene_unreal.py` construit une carte
  du moteur (`LOT-1012` ; embryon du format du `LOT-1018`).
- `Options/` — `options.json`, les options d'usine du jeu, lues au lancement (`LOT-1014`).
- `Editor/` — ce que l'éditeur de niveaux produit et réutilise : les préfabriqués d'un lieu
  (`Prefabs/`) et les modèles de carte (`Templates/`).
- `Maps/` — `world-maps.json`, positions relevées sur les cartes peintes (`LOT-94`).
- `Credits/` — `credits.json`, les crédits affichés par le jeu.

Ces éléments restent hors de `Content/`, en texte (D-52) : ils sont lus par les lecteurs de Core
(`../JustAnotherRpgGame/Core/`), auxquels le module du jeu dit où ils sont (`Bridge/JadgPaths`).
Aucun n'est converti en `DataTable` ni en `.uasset` de données.

> Note : les images des kits d'assets ne vivent pas dans Git. Elles sont publiées à part et
> récupérées par `scripts/fetch_assets.py` d'après `Assets/kits.lock.json` ; le dépôt ne garde que
> les manifestes (voir `Assets/README.md`).
