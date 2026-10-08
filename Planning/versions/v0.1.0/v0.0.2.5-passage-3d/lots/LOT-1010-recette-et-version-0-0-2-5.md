+++
id = "LOT-1010"
titre = "Recette et version 0.0.2.5"
version = "0.0.2.5"
filiere = "version"
statut = "livre"
taille = "M"
resume = "Le jeu de la 0.0.2, rejoué en 3D de bout en bout, de jour comme de nuit — et un dépôt où plus rien de l'ancien rendu ne traîne."
prerequis = ["LOT-1007", "LOT-1009", "LOT-1011"]
livrables = [
  "La recette : la quête « Des pommes pour l'arène » par ses trois issues et un combat à quatre contre quatre, joués en 3D au clavier et à la manette, à midi et de nuit.",
  "Le **balayage final** : le contrôle des orphelins, les recherches de la liste ci-dessous, et la suppression de ce qu'ils trouvent encore.",
  "Les références d'image et les captures du guide régénérées ; le cahier de test régénéré.",
  "`bilan.md` dans le dossier de la version : ce que chaque lot a coûté, le coût mesuré d'un personnage, le poids des kits avant et après, et ce que la `0.0.3` en retient.",
  "Les lots d'assets, de PNJ et de cartes de la `0.0.3` relus : ceux qui commandent encore des images 2D sont réécrits, ceux des versions suivantes marqués à réécrire (D-35).",
  "L'installeur éprouvé sur un poste vierge ; le tag `v0.0.2.5`.",
]
criteres = [
  "Les critères de sortie de la version sont tenus.",
  "`check_orphans.py` passe : aucun fichier installé sans citation, aucune citation sans fichier, aucun script sans appelant.",
  "Les seules images de décor qui restent sont celles de la dette déclarée dans le `README.md` de la version ; chacune a un lot de la `0.0.3` qui la retire.",
  "Plus aucun document en vigueur ne prescrit la 2D HD : standards, spécifications, guides, `AGENTS.md`, fiches de lots à faire.",
  "Le poids des kits publiés et la cadence de `bench_world_frame` sont écrits au bilan, avant et après la version.",
]
+++

## Décisions de réalisation

Livré le 5 octobre 2026, branche `lot-1010-recette-0-0-2-5`, **PR #180**, la PR de publication de
la version. Le [bilan](../bilan.md) dit ce que la version a coûté et ce que la suivante en retient.

1. **La recette est celle de l'auteur.** Il a rejoué la quête et la série de l'arène en 3D, de jour
   comme de nuit, et l'a confirmé le 5 octobre. Les suites d'intégration et système les jouent en
   CI. **La manette n'est plus un critère** : elle a été retirée du jeu le 2 octobre, en cours de
   version (`EX-CTRL-002` retirée) ; le critère de sortie est amendé au catalogue, et le dit.
2. **Rien n'a été reconstruit en local**, à la demande de l'auteur : la recette s'appuie sur la CI
   de `main`, sur les relevés de la nightly et sur les mesures des fiches. Deux livrables en
   dépendaient et ne sont **pas faits** — les **captures du guide**, et la **cadence de l'arène**
   sur le poste de référence, renvoyée au `LOT-107`. Le bilan les nomme sous « Ce que la recette
   n'a pas fait ». Les références d'image des tests n'avaient pas à être régénérées : la CI les
   compare à chaque PR.
3. **Le balayage n'a rien eu à supprimer** — aucun orphelin, aucune bande, aucun second rendu. Il a
   corrigé six textes en vigueur qui disaient encore la 2D HD le standard (`README.md`,
   `Planning/README.md`, guides du rendu et du monde, `Levels/README.md`, `Assets/CREDITS.md`), et
   le catalogue, qui décrivait toujours les huit corps de D-31.
4. **La chaîne de publication ne savait pas lire ce numéro.** `extract_release_notes.py` ne
   reconnaissait un tag qu'à trois nombres : `v0.0.2.5` aurait fait échouer la release au moment
   de publier. Corrigé, avec son test (`test_extract_release_notes.py`).
5. **La relecture des lots de zone (D-35) a porté une décision de l'auteur, D-47.** Le 5 octobre,
   il resserre la `0.1.0` sur les trois lieux de la démo, à leur qualité finale ; le reste de
   l'Empire central part à la `0.4.0`, après les systèmes. Trois choix de numérotation et de
   rangement lui ont été posés le jour même : sous-versions `0.3.1` à `0.3.7` puis `0.4.0`, régions
   décalées d'un cran ; tous les lots de système des versions de zone à la `0.2.0` ; la `0.0.3`
   pour les trois lieux et la `0.1.0` pour leur recette. En conséquence :
   - les fiches de décor et de PNJ de la `0.0.3` sont **réécrites** pour commander des maillages et
     des modèles (`LOT-110`, `LOT-113`, `LOT-114`, `LOT-115`, `LOT-151`) ; celles de l'Arena of Fate,
     déjà en maillages, reçoivent ce que la `0.1.0` en attend ; la fiche du `LOT-147`, que l'auteur
     reprend en ce moment, n'est pas touchée ;
   - trente-deux fiches de zone sont **déplacées** sous `v0.4.0/`, marquées à réécrire, sous leur
     numéro ; huit fiches de système passent à la `0.2.0`, leurs prérequis et leurs critères
     recalés sur ce qui existera alors ; le `LOT-198` reste la recette de la `0.1.0`, et le
     `LOT-400` naît pour celle de la `0.4.0`.
6. **La version.** `CMakeLists.txt` porte `0.0.2.5` ; le CHANGELOG ferme la section
   `## [0.0.2.5] - 2026-10-05` (PR au label `no-changelog`) ; le tag `v0.0.2.5` se pose sur le
   commit de fusion, `release.yml` teste, empaquette, lance les archives et publie.

## Ce qui n'est pas ici

- Les **captures du guide** et la **cadence de l'arène** : voir la décision 2.
- L'installeur sur un **poste vierge** : c'est le test de fumée de `release.yml` qui en tient lieu,
  comme aux deux versions précédentes.
- Le **coût en temps et en régénérations** d'un personnage, que l'auteur tient dans son atelier
  (`LOT-1009`).

## Pourquoi

Une version qui change la matière du jeu sans en changer une règle ne se juge que d'une façon : on
rejoue ce qu'on jouait. Et la règle de la version — chaque lot retire ce qu'il remplace — se
vérifie une dernière fois d'un bloc, parce qu'un oubli se voit mieux à la fin qu'en cours de route.

## À supprimer

Ce lot ne devrait rien avoir à supprimer : s'il trouve quelque chose, c'est un oubli d'un lot
précédent, et le bilan le nomme.

| Recherche | Attendu |
|---|---|
| `git grep -n "ScenePainter\|SceneImages"` | rien (LOT-1002) |
| `git ls-files "Source/Elements/Assets/**/Characters/**/*.anim.json"` | rien (LOT-1006) |
| `git grep -n "\"portraits\"" Source scripts` | rien (LOT-1011) |
| `git grep -ln "2D HD\|style-2d-hd" -- . ":!Planning/standards/archives" ":!Planning/versions/v0.0.0" ":!CHANGELOG.md"` | seulement des fiches **livrées**, les décisions datées et les textes remplacés d'`exigences-retirees.md` |
| PNG sous `floors/`, `walls/`, `balustrades/`, `stairs/`, `roofs/` du kit de la Capitale | **ils restent** : dette déclarée pour la `0.0.3` (D-43, LOT-151) |
| Scripts de `scripts/` sans appelant | rien (`check_orphans.py`) |
| Tests désactivés ou références d'image que plus aucun test ne lit | rien |
| Anciennes versions des kits dans `kits.lock.json` | une entrée par kit, la dernière |

Ce qui reste **à dessein**, et que le balayage ne doit pas emporter : les bandes d'effets de
`Common/Fx/`, les portraits et jetons peints, les cartes peintes, l'interface, les documents
archivés, et la dette déclarée pour la `0.0.3`.

## Risques et questions ouvertes

- Les lots de zone de la `0.0.3` ont été écrits pour des kits 2D. Les relire ici évite d'ouvrir la
  `0.0.3` sur des fiches fausses ; c'est la décision D-35. Si la réécriture dépasse
  la taille de ce lot, elle devient un lot à part, avant le tag.
