# Elements/Levels/

Cartes du jeu, une **description texte** par carte (`EX-LVL-001`), au format `jadg-map`, version 5
(`LOT-1018`, D-51, D-52) : ce que Core joue — la grille de collision, les couches de pièces, les
entités sur leurs cases et à leur étage — et ce que le moteur construit — le terrain, les objets en
mètres, les préfabriqués, le groupe, le ciel, la navigation, les cadrages. Spécification :
`Documentation/Specification/niveaux.md` (§2) ; schéma :
`Documentation/Specification/level.schema.json` ; guide :
`Documentation/Guide/guide-cartes-moteur.md`.

Les cartes suivent **le même découpage que les assets** — `<région>/<ville>/<zone>.json`, la
sous-zone sous son dossier de zone : `central-empire/capital/arenarea.json`, `martpart.json`,
`arenarea/arena-of-fate.json`, `arenarea/arena-of-fate/undercroft.json` et `catacombs.json`, les
cinq cartes de la démo, **migrées de la v4 telles quelles** (`jadg_map.py --migrate`) ;
`porte-1012.json`, la carte de la porte (`LOT-1012`), écrite par `scripts/maps/build_gate_scene.py`.
Une carte a pour identifiant son **chemin relatif** : un portail vise
`central-empire/capital/martpart`, et son niveau du moteur est `/Game/Maps/Levels/<identifiant>`.

- **Le texte est la source, le niveau une sortie.** `scripts/maps/build_level.py` construit le
  niveau ; l'éditeur d'Unreal le retouche à la souris, et `scripts/maps/read_level.py` ramène dans
  le texte ce qui est dans sa frontière. Ce qui ne se relit pas ne se fait pas dans l'éditeur.
- Le **`name`** d'une carte est une clé de traduction, `map.<identifiant>.name`
  (`map.central-empire.capital.martpart.name`), que chaque catalogue de `Localization/` porte.
- La **forme canonique** (une case, un objet, une entité par ligne : un geste, une ligne de diff)
  et le **contrôle de contenu** — portails appariés, arrivées citées, zones nommées, cases
  inatteignables — sont ceux de `python scripts/maps/jadg_map.py --check`, en CI.
- Les entités gardent leurs identifiants (`"id"`, jamais réemployés, `"nextEntityId"`) : quêtes,
  drapeaux et sauvegardes citent une entité par `carte#id`.

> **Ce `README.md` est le gardien du dossier (`LOT-123`).** Git ne garde pas un dossier vide : sans
> lui, un `Levels/` sans aucune carte disparaîtrait du dépôt.
