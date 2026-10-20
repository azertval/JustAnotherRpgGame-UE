# Core/Resources/

Les descriptions des pièces et des lieux, sans dépendance au moteur :

- `ScenePieceManifest` résout les pièces déclarées dans les manifestes d’un lieu.
- `ScenePlace` valide les identifiants de lieu et leurs chemins dans les données.

Les maillages, animations et textures sont importés par les scripts Unreal du dépôt.
La lecture et l’écriture des cartes restent dans `Core/Levels`.
Les familles d’illustrations sont contrôlées par `scripts/checks/check_asset_keys.py`.
