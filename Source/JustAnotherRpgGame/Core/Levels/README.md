# Core/Levels/

Modèle de carte et chargement/sérialisation JSON.

- `TileType` — types de tuiles d'une carte (`Empty`, `Solid`, `Entry` et le terrain du RPG :
  `Grass`, `Dirt`, `Sand`, `Water`, `DeepWater`, `Wall`, `Cliff`, `Bridge`, `Stairs`, `LOT-08`) et
  utilitaires associés (`isSolid`) ; `TileTypeName` — leur nom dans le format JSON.
- `TileMap` — grille dense `width × height` de `TileType`, origine haut-gauche.
- `GridPosition` — position entière dans la grille (colonne, ligne).
- `Level` — carte assemblée et immuable : `TileMap` de collision, couches, entités, entrée (une
  seule case `Entry` par carte) et pièces assignées par case.
- `LevelLoader` — chargement d'un niveau depuis le format JSON (liste de tuiles-objets),
  avec validation (`EX-LVL-004`) et résultat récupérable (`LevelLoadResult`, jamais d'exception).
- `LevelWriter` — sérialisation d'un niveau vers le format JSON, symétrique à `LevelLoader`.
- `LevelDraft` — représentation **mutable** d'un niveau en cours d'édition (peinture, undo/redo,
  redimensionnement) ; `toLevel()` revalide via le même chemin que `LevelLoader`.
- `TileLayer` — couche de tuiles typée d'une carte (`LOT-04`) : nom libre, rôle (`Ground`, `Decor`,
  `Collision`, `Legacy`), grille et propriétés libres.
- `MapEntity` — entité placée sur une carte (PNJ, coffre, panneau, portail, déclencheur) : type
  libre non interprété par `Core`, case, et propriétés libres.
- `LevelProperties` — `PropertyMap`, dictionnaire ordonné de propriétés libres (`bool`, entier,
  réel, chaîne) porté par une couche ou une entité ; recueille aussi les champs que le chargeur ne
  reconnaît pas, pour les réécrire intacts (`EX-LVL-018`).

Réf. specs : `EX-LVL-001`…`EX-LVL-018`, `EX-EDIT-001`…`EX-EDIT-017`.
