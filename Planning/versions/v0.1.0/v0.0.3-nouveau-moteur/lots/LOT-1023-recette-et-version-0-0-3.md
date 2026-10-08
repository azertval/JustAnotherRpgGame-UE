+++
id = "LOT-1023"
titre = "Recette, retrait de l'ancien moteur et version 0.0.3"
version = "0.0.3"
filiere = "version"
statut = "a-faire"
taille = "M"
resume = "La démo se rejoue de bout en bout sur le nouveau moteur, l'ancien dépôt est gelé, le bilan est écrit, les fiches de la 0.0.4 sont réécrites, le tag v0.0.3 est posé dans le nouveau dépôt."
prerequis = ["LOT-1017", "LOT-1020", "LOT-1021", "LOT-1022", "LOT-1024", "LOT-1025"]
livrables = [
  "La quête « Des pommes pour l'arène » par ses trois issues et la série de l'arène, jouées par l'auteur sur le nouveau moteur, de jour et de nuit ; les suites d'intégration et système vertes sur `main`.",
  "Le **gel de l'ancien dépôt** (D-58) : un dernier commit qui marque la fin du moteur maison, le README de tête qui renvoie au nouveau dépôt et au tag `v0.0.2.5`, l'archivage GitHub ; le balayage du nouveau dépôt — rien de `Qt`, `QRhi`, `QML`, `LevelEditor`, format v4 n'y est entré, et ce que la passation avait laissé passer par erreur est retiré dans la PR de la recette (D-32).",
  "Les mesures de cadence et d'ouverture des trois cartes sur le poste de référence, et le poids des kits et du dépôt, dans le bilan.",
  "`bilan.md` : ce qui a coûté plus que prévu, le coût d'Arenarea, ce que la `0.0.4` doit en retenir ; `README.md`, `AGENTS.md`, le guide du développeur et les spécifications de rendu mis à jour.",
  "Les fiches de la `0.0.4` réécrites pour le nouveau moteur (comme D-35 l'a fait pour la 3D) : LOT-106, 107, 110, 111, 113, 114, 115, 147, 151, 157 ; les fiches de l'éditeur de la `0.2.0` (LOT-158, 159, 166, 167, 168, 169) relues.",
  "L'installeur et les notes de version ; le tag `v0.0.3`.",
]
criteres = [
  "Plus une ligne de Qt, de QML ni de QRhi dans le nouveau dépôt ; sa CI est verte ; l'ancien dépôt est archivé et privé.",
  "`check_orphans.py`, `check_binary_files.py`, `lint_planning.py` et `lint_docs.py` passent ; aucun fichier LFS sans script producteur.",
  "Les trois cartes tiennent 60 images par seconde à 1080p sur le poste de référence, de jour comme de nuit, et s'ouvrent en moins de 10 secondes.",
  "L'auteur a joué la démo par ses trois issues sur le nouveau moteur et l'écrit dans la fiche.",
  "Le tag `v0.0.3` est posé ; l'archive se lance sur un poste vierge (test de fumée de `release.yml`).",
]
+++

## Pourquoi

Une version se clôt par un bilan qui recale les suivantes (règle 5 de la trajectoire), et celle-ci
change de dépôt (D-58) : l'ancien se gèle à la fin, parce que le jeu devait rester jouable
jusque-là. Le bilan donne le premier coût d'un lieu produit pour de bon ; les fiches de la
`0.0.4` s'écrivent dessus.

## Périmètre

Dedans : le rejeu, le retrait, les mesures, le bilan, les fiches réécrites, la version.

Dehors, nommément :

- un joueur extérieur : il reste un livrable du LOT-198 ;
- toute correction qui dépasse la journée : elle devient un lot de la `0.0.4`.

## Conception

- **Le balayage final**, comme au LOT-1010, sur le nouveau dépôt : `grep` de `Qt`, `QRhi`, `QML`,
  `ScenePainter`, `MeshBatch`, `LevelEditor`, `jadg-editor-gestures`, `level v4` ; aucun résultat
  attendu dans `Source/` et `scripts/` ; les fiches livrées de `Planning/` les gardent comme
  histoire.
- **Les kits** : le verrou du nouveau dépôt ne porte que les kits republiés ; les anciennes
  archives restent dans les releases de l'ancien dépôt.
- **Le bilan** chiffre : lignes retirées et ajoutées, poids du dépôt et des kits, coût d'Arenarea
  par quartier, crédits Meshy, cadence des trois cartes, durée réelle de la version contre les six
  à dix semaines annoncées.

## Risques et questions ouvertes

- **Un lot de la version non livré** (Arenarea partiel, interface redécoupée) : la recette se fait
  sur ce qui est livré, la dette s'écrit avec le lot qui la retire, et le tag se pose quand même si
  la démo se joue ; sinon la version attend.
- **La dette du LOT-1016** (clos le 8 octobre 2026), que la recette retire : **la main sur la
  souris** — jouer dans une fenêtre, juger la sensation des commandes et les distances de la caméra
  (4 m à 120 m, reprises de la porte sans être réglées) — et **la cadence de la porte**, 88 images
  par seconde au lieu des 119 de sa clôture, avant le LOT-1016 comme après, cause non cherchée.
