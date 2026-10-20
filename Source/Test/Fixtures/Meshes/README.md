# Maillages des tests Unreal

Ces fichiers servent aux niveaux de test actifs `socle-1014` et `essai/*`.
`scripts/assetsGeneration/build_mesh_fixture.py` écrit les GLB et leurs textures
incorporées sans bibliothèque externe ; `--check` vérifie leurs octets.

- `Assets/Scene/ilot/` : sol, mur, toit, dallage et manifeste des pièces.
- `Assets/Scene/socle/repere.glb` : bloc dissymétrique de calibration des axes à l’import.

Les tests Python contrôlent leur format et leurs dimensions. Les niveaux du
moteur sont construits par `scripts/maps/build_level.py` depuis leurs descriptions v5.
