# Contribuer à JustAnotherRpgGame

Le dépôt est celui du **nouveau moteur** : Unreal Engine 5.8, version `0.0.3`
([D-48, D-58](Planning/vision/decisions.md)). Les règles de la version sont dans
[`AGENTS.md`](AGENTS.md) ; cette page dit comment une contribution arrive sur `main`.

## Ce qui entre dans le dépôt, et ce qui n'y entre pas

- **Du texte** (D-52) : C++, JSON de contenu, scripts Python d'éditeur, descriptions de carte. **Pas
  de logique en Blueprint.**
- **Un `.uasset` ou un `.umap` est une sortie** : un script du dépôt le régénère, et il part en
  **Git LFS** (`.gitattributes`). On ne le retouche pas dans l'éditeur ; on rejoue le script. Avant
  le premier commit d'un clone : `git lfs install`.
- **Rien de ce que le moteur régénère** : `Binaries/`, `Intermediate/`, `DerivedDataCache/`,
  `Saved/`, les solutions Visual Studio (`.gitignore`).
- **Ni livre source, ni texte extrait d'un livre** (EX-CNT-023). Le dépôt est public :
  `Documentation/SourceBook/`, un PDF, un cache d'extraction, un lecteur plein texte n'y entrent
  jamais, même pour un commit. `scripts/checks/check_no_sourcebook.py` le refuse avant le commit et
  en CI ; les **données finales** (`Source/Elements/`, avec leur champ `source`) sont, elles, suivies.
- **Les images et maillages des kits** restent hors de Git : ils viennent d'archives publiées
  (`scripts/fetch_assets.py`, d'après `kits.lock.json`). Aucun fichier au-delà de 5 Mio, et un
  binaire doit avoir une extension déclarée dans `.gitattributes` — l'y déclarer est la décision
  d'admettre une nouvelle famille.
- **Rien de Qt, de QML ni de QRhi** (D-58).

## Poste de développement

- **Moteur** : Unreal Engine 5.8, associé au `.uproject`. **Visual Studio** avec les outils C++ x64.
- **Construire et vérifier sans fenêtre** :
  - `pwsh scripts/build.ps1` — les tests de Core **hors du moteur** (CMake + Ninja + GoogleTest) ;
    `-Preset ninja-release` pour la configuration Release, `-Clean` pour repartir de rien ;
  - `pwsh scripts/build.ps1 -Unreal` — la cible d'éditeur par UnrealBuildTool, le commandlet
    `JadgContentCheck`, qui lit les données de contenu par les lecteurs de Core, les tests
    d'automatisation du moteur (`Jadg.*`), puis la carte du socle reconstruite par script et ses
    captures comparées à leur référence. `-EnginePath` si le registre ne donne pas le moteur,
    `-NoCapture` sans processeur graphique.
- **Vérifier le poste** : `powershell -ExecutionPolicy Bypass -File scripts/setup_dev.ps1` compare
  les outils installés aux versions de `ci.yml` (moteur compris) ; `-Install` installe ce qui manque.
- **Python des scripts** (`pyproject.toml`, `uv.lock`) : `uv sync --locked` crée `.venv/` avec
  exactement les dépendances du runner. Tests des scripts : `uv run pytest`.
- **Hooks** (`.pre-commit-config.yaml`) : avant chaque commit, livres sources, clang-format, ruff,
  actionlint, zizmor, gitleaks, conflits de fusion et de casse, YAML, JSON et garde-fou binaires ;
  à la rédaction du message, son format. À installer **dans chaque worktree** :
  `pre-commit install`. Tout rejouer : `pre-commit run --all-files`.
- **Tous les contrôles du référentiel en une commande** : `uv run scripts/check.py`. Il lit les
  étapes du job `lint-exigences` dans `ci.yml` et les exécute, puis lance les hooks — un contrôle
  ajouté à la CI y est rejoué sans qu'on y pense.
- Les versions d'outils (clang-format, uv, pre-commit, PSScriptAnalyzer) sont écrites une fois,
  dans le bloc `env:` de `.github/workflows/ci.yml`.

## Le code

- **`Core` ne dépend pas du moteur.** Ses inclusions sont `"Core/<Module>/<Fichier>.h"`, jamais un
  nom seul. Une règle que le moteur impose à Core s'écrit dans Core et vaut pour les deux
  constructions.
- **Core avant le moteur** dans l'ordre des inclusions d'un fichier du jeu : les en-têtes de Core
  ne doivent voir aucune macro d'Unreal (`check`, `verify`, `ensure`).
- **clang-format** s'applique à `Core` et à ses tests (`Source/Test/`), pas au code du pont
  (`Bridge/`, `Commandlets/`, le module) : il trie les inclusions, et déferait la règle
  précédente. Ce code-là suit les conventions d'Unreal (préfixes `F`, `U`, `A`, macros de
  réflexion).
- Un nouveau comportement de Core arrive avec son test GoogleTest.

## Messages de commit — Conventional Commits

Format : `<type>(<portée facultative>): <description à l'impératif>`, ou, sur une branche de lot,
`LOT-NNNN — <description>` (tiret cadratin). Vérifié par le hook `commit-msg`
(`scripts/ci/check_commit_message.py`) ; les messages de fusion, `Revert` et `fixup!` sont admis.

| Type | Usage |
|------|-------|
| `feat` | Nouvelle fonctionnalité |
| `fix` | Correction de bug |
| `docs` | Documentation seule |
| `refactor` | Refonte sans changement de comportement |
| `test` | Ajout ou modification de tests |
| `build` | Build, UnrealBuildTool, CMake, dépendances |
| `ci` | Intégration continue |
| `chore` | Tâche diverse (config, outillage) |

La portée correspond en général au module : `core`, `bridge`, `elements`, `assets`, `test`, `build`.

## Branches et Pull Requests

- `main` est **protégée** (règle de branche du dépôt) : **aucun push direct**, ni réécriture
  d'historique, ni suppression. Toute évolution passe par une **Pull Request**.
- **Une branche par lot** : `lot/LOT-1016-camera-et-exploration`. Pour un correctif hors lot :
  `fix/...` ; pour de la documentation seule : `docs/...`.
- La PR suit le gabarit (`.github/pull_request_template.md`) et se fusionne quand **les contrôles
  requis sont verts** et que ses conversations sont résolues.

### Ce que la CI vérifie, et ce qu'elle ne peut pas vérifier

Les runners hébergés n'ont pas Unreal Engine, et sa licence interdit de le leur livrer. Les
contrôles requis d'une PR sont donc ceux qui ne dépendent pas du moteur :

| Contrôle requis | Ce qu'il fait |
|---|---|
| `core-tests (ninja)`, `core-tests (ninja-release)` | Construit `Core` seule et lance ses tests GoogleTest, en Debug et en Release |
| `format` | clang-format sur `Core` et ses tests |
| `lint-exigences` | Livres sources, exigences, lexique, manifeste du corpus, clés d'assets, catalogues RPG contre leurs schémas, traductions, scripts PowerShell, versions d'outils (moteur compris), binaires, JSON, scripts sans appelant et sorties du moteur sans script, tests des scripts |
| `pre-commit` | Les hooks du poste, sur tout le dépôt |
| `changelog` | La PR ajoute une ligne à `## [Non publié]`, ou porte le label `no-changelog` |

**La construction du moteur, ses tests et ses captures se vérifient sur le poste, avant d'ouvrir
la PR** : `pwsh scripts/build.ps1 -Unreal`, case à cocher du gabarit. Le workflow `Unreal`
(`unreal.yml`) les rejoue chaque nuit sur le poste de référence et à la demande (onglet *Actions*).

> Ce workflow ne se déclenche **jamais** sur une PR : le dépôt est public, et un runner
> auto-hébergé exécuterait le code d'un fork sur le poste de l'auteur. Sa mise en service (runner,
> variables `UNREAL_RUNNER` et `UNREAL_ENGINE_PATH`) est décrite en tête de `unreal.yml`.

### Avant d'ouvrir une PR

1. `pwsh scripts/build.ps1` passe à 100 %.
2. `pwsh scripts/build.ps1 -Unreal` construit sans erreur ni avertissement, le commandlet sort en
   0, les tests d'automatisation passent et les captures du socle tiennent leur référence.
3. `uv run scripts/check.py` est vert ; sur un poste qui a les kits,
   `python scripts/checks/check_orphans.py` aussi (la CI ne voit pas leurs images).
4. Une PR qui **change l'image** livre ses captures, à midi et à 22 h, au cadrage du joueur ; si
   elle change celle du socle, elle réécrit sa référence (`-UpdateReference`) et le dit.
5. Une PR qui ajoute ou modifie un `.uasset` ou un `.umap` nomme le **script qui le produit** ;
   `git lfs ls-files` le liste, et `check_orphans.py` refuse celui qu'aucun script ne cite.
6. Ce que la PR remplace — asset, script, document — est **supprimé dans la PR** (D-32).
7. `CHANGELOG.md` (section `## [Non publié]`) consigne l'apport, sinon label `no-changelog`.

## Automatisations

- **CI** (`ci.yml`) et **CHANGELOG** (`changelog.yml`) : sur chaque PR vers `main`. Un nouveau push
  annule le run précédent ; tout workflow se relance à la main (`workflow_dispatch`).
- **Unreal** (`unreal.yml`) : la nuit et à la demande, sur le poste de référence.
- **Site** (`docs.yml`) : à chaque merge sur `main`, publie sur la branche **`gh-pages`** les pages
  de documentation, l'étude des métiers et le site de planification (`/planning/`). Le voir en
  local : `python Documentation/outils/build_docs_site.py --out build/site`.
- Les actions GitHub sont **épinglées par SHA** de commit, le tag en commentaire ; **Dependabot**
  (`.github/dependabot.yml`) propose leur mise à jour chaque semaine, en une PR, ainsi que celle des
  dépendances Python (`uv.lock`).

Ne sont pas encore refaits dans ce dépôt, et le seront par leur lot : la publication d'une version
(empaquetage du jeu, notes de version), la référence du code et la page qualité du site
(LOT-1023 ; voir [`PASSATION.md`](PASSATION.md)).
