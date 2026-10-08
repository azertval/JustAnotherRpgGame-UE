# Versions

Une version par dossier. Le catalogue est [`versions.toml`](versions.toml) ; il donne l'ordre, la
nature et le périmètre de chacune. Une version **détaillée** a son dossier, avec :

- `README.md` — ce que la version a de particulier (facultatif) ;
- `bilan.md` — le bilan écrit à la recette, quand la version est livrée : ce qui a coûté plus que
  prévu, ce que la suivante en retient ;
- `lots/` — une fiche par lot, au [gabarit](../standards/gabarit-lot.md) ;
- `maquettes/` — plans de principe, maquettes d'écran, schémas de quête.

| Dossier | Versions |
|---|---|
| `v0.1.0/` | le référentiel de **la démo** : `0.0.1` (démo), `0.0.2` (combat), `0.0.2.5` (passage à la 3D), `0.0.3` (le nouveau moteur), `0.0.4` (les trois lieux, produits pour de bon), `0.1.0` (recette) |
| `v0.2.0/` | la compagnie, la sauvegarde, le voyage et les dernières fonctionnalités |
| `v0.3.0/` | classes et espèces |
| `v0.4.0/` | le référentiel **Empire central** : `0.3.1` à `0.3.7` (une sous-version par zone), `0.4.0` (recette) |

Les versions **prévisionnelles** (`0.5.0` à `1.0.0`) n'ont pas de dossier : une ligne du catalogue
leur suffit tant qu'elles sont loin. Les numéros de lots vont par centaine : `LOT-1xx` pour le
référentiel `0.1.0`, `LOT-2xx` pour la `0.2.0`, `LOT-3xx` pour la `0.3.0`. La `0.0.2.5`, ajoutée
après coup au référentiel `0.1.0`, en garde le **1** sur quatre chiffres — `LOT-1000` à
`LOT-1011` : il ne restait que neuf numéros libres en `1xx` pour ses onze lots. La `0.0.3`, le
nouveau moteur, continue la série : `LOT-1012` à `LOT-1023`.

**Un lot garde son numéro quand il change de version.** Depuis le 5 octobre 2026
([D-47](../vision/decisions.md)), l'Empire central est le référentiel `0.4.0` : ses lots de zone,
écrits quand il était le `0.1.0`, restent des `LOT-15x` à `LOT-19x`, et les lots de système passés
à la `0.2.0` restent `LOT-150` à `LOT-171`. Seuls les lots **nés** pour la `0.4.0` prennent un
`LOT-4xx` — le premier est le `LOT-400`.

À lire d'abord : [la quête de la démo](v0.1.0/v0.0.1-demo/quete-demo.md), puis
[le bilan de la 0.0.1](v0.1.0/v0.0.1-demo/bilan.md).
