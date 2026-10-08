<!-- Titre : `LOT-NNNN — ce que la PR livre`, ou `type(portée): description` (CONTRIBUTING.md). -->

## Ce que livre cette PR

<!-- Le lot (lien vers sa fiche sous Planning/versions/), et ce qui change pour le joueur ou l'auteur. -->

## Vérifié sur le poste

La CI hébergée n'a pas le moteur : ce qui suit ne se vérifie qu'ici.

- [ ] `pwsh scripts/build.ps1` — tests de Core hors moteur
- [ ] `pwsh scripts/build.ps1 -Unreal` — cible d'éditeur, puis commandlet `JadgContentCheck`
- [ ] `uv run scripts/check.py` — contrôles du référentiel et hooks

## Règles de la version

- [ ] Tout ce qui est écrit est du texte ; aucun `.uasset` ni `.umap` retouché à la main : chacun sort d'un script du dépôt, cité ci-dessous, et part en Git LFS (D-52)
- [ ] Aucune logique en Blueprint
- [ ] Les inclusions de `Core` précèdent celles du moteur dans les fichiers du jeu
- [ ] Ce que la PR remplace (asset, script, document) est supprimé ici (D-32)
- [ ] Aucun livre source ni texte extrait d'un livre (EX-CNT-023)
- [ ] `CHANGELOG.md`, section « Non publié », ou label `no-changelog`

## Captures

<!-- Si la PR change l'image : à midi et à 22 h, au cadrage du joueur. Sinon : « sans objet ». -->

## Sorties régénérées

<!-- Pour chaque binaire ajouté ou modifié : le script qui le produit et la commande rejouée. -->
