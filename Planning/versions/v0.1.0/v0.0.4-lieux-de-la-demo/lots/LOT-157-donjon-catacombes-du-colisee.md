+++
id = "LOT-157"
titre = "Donjon — les catacombes du colisée"
version = "0.0.4"
filiere = "cartes"
statut = "a-faire"
taille = "L"
resume = "Sous l'Arena of Fate, les catacombes où les quatre Ungods sont représentés enchaînés, tenues par le Culte de l'Aile d'Ombre."
prerequis = ["LOT-107", "LOT-151"]
livrables = [
  "`Levels/central-empire/capital/arenarea/arena-of-fate/catacombs.json`, dessinée **dans l'éditeur**.",
  "`Regions/central-empire/capital/arenarea/arena-of-fate/catacombs/Scene/` : les pièces propres aux catacombes, `manifest.json`, `appearance.json`.",
  "Les **quatre Ungods enchaînés** : C'thraxis, Droggath, Krynnethoth, Z'ulvath — une pièce maîtresse chacun.",
  "L'ouverture de l'**escalier des catacombes** au fond de la prison (`LOT-107` l'a posé condamné).",
  "La page de galerie de la zone.",
]
criteres = [
  "`LevelEditor --check` passe : aucune case inatteignable, aucun portail sans arrivée — y compris l'escalier de la prison, désormais relié.",
  "Les quatre Ungods sont posés, nommés, et paraissent dans la galerie.",
  "On descend depuis la prison de l'arène et on remonte, sans quitter le jeu.",
]
sources = [
  "Tanares Sourcebook, ch. 4 (p. 68-86) : les quatre Ungods",
  "Tanares Sourcebook, ch. 2 (p. 44-45) : le Culte de l'Aile d'Ombre, ses quatre sectes",
]
+++

## Reprise du 2 octobre 2026 — prescriptions courantes

L'auteur demande une nouvelle base en deux étapes : **mockups générés**, puis **assets et
cartes dans le moteur**. Les niveaux actuels ne répondent plus au niveau visuel attendu.
**Validation de l’auteur, 2 octobre 2026 : les trois mockups sont validés.**
Références de production : `Mockups/V5/arena.png`, `Mockups/V5/undercroft.png` et
`Mockups/V3/catacombs.png`, dans l’atelier ci-dessous. Leurs empreintes sont conservées
dans `Mockups/validation.json`. L’étape 1 est terminée ; cette validation visuelle
ouvre la production des assets puis des cartes, sans clôturer les lots moteur.

**Treize délégations régionales**, confirmées par l'auteur, remplacent les quatre loges
d'alliance prévues dans la conception historique ci-dessous : Central Empire, Republic of
Freelands, Imperial Ben'net, Kingdom of Kolbjörn, Magocracy of Mage Tower, Seashores, Sindile
Forest, Stravian Domains, Storm Islands, Taii'Maku City States, Theocracy of Kepesh, Tsvetan,
Yama. **Une loge et une bannière par région** ; bannière de la grande alliance au-dessus pour
les onze régions affiliées. Taii'Maku et Tsvetan restent sans bannière d'alliance.
Les cultistes ne sont pas représentés dans l'arène. Les blasons se reprennent du livre,
selon le relevé corrigé au référentiel de la Capitale, et non de l'héraldique inventée antérieure.

**Aucun symbole impérial dans les catacombes**, y compris à leur entrée.
Les quatorze statues de la coursive restent prévues. La nouvelle disposition des loges reste
à éprouver dans l'emprise du LOT-107 ; aucune nouvelle dimension n'est fixée ici.

Atelier dans l'espace dédié feat/arena-of-fate-reconstruction :
Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Mockups/.
La galerie, les consignes complètes, les appartenances et les réserves de revue y sont conservées.
Les mentions de quatre loges et d'héraldique inventée dans la conception historique qui suit
sont **supplantées par cette décision** ; elles ne sont plus des critères de production.



## Pourquoi

La [DA de l'Arena of Fate](../../../../referentiels/central-empire/capitale.md#larena-of-fate--architecture-et-iconographie-da-de-lauteur-21-sept-2026)
(D-18) sort les Ungods et le Culte du colisée : **ni statue, ni loge, ni bannière au-dessus du
sable**. Ce qui est chassé de l'arène est sous elle. Les catacombes sont le revers du monument —
l'Empire montre quatorze dieux au public et tient les quatre autres enchaînés sous la prison — et
elles valent un donjon à elles seules, pas une salle de plus.

Sans ce lot, l'escalier posé au fond de la prison par le `LOT-107` reste une porte condamnée.

## Périmètre

**Dedans** : la carte des catacombes, ses pièces de scène propres, les quatre Ungods enchaînés,
l'iconographie du Culte, la liaison avec la prison.

**Dehors** : les monstres et les PNJ du Culte (lot de PNJ de la version), la quête qui y mène,
et tout ce qui touche au niveau 0 ou −1 du colisée — c'est le `LOT-106` et le `LOT-107`.

## Conception

Le seul accès est **par la prison** de l'arène, et il est gardé : on n'entre pas dans les
catacombes par la rue. Le donjon est un lieu clos à plusieurs salles, sous la ville, au-dessous du
niveau −1 du colisée.

Les **quatre Ungods** y sont **représentés, enchaînés** — des représentations, pas les entités.
Chacun est une pièce maîtresse, à sa mesure : C'thraxis, Droggath, Krynnethoth, Z'ulvath.

## Risques et questions ouvertes

- **La version.** Le donjon est posé en `0.0.3` parce qu'Arenarea est intra-muros et que le kit
  commun intra-muros (`LOT-151`) lui sert de base. À déplacer si l'auteur préfère le rattacher à la
  quête qui l'ouvrira.
- **Le contenu du donjon** — nombre de salles, rencontres, récompense — n'est pas arrêté : il se
  décide au démarrage du lot, avec la quête qui y conduit.

## Intégration du 4 octobre 2026

Les trois cartes sont dans le moteur, en maillages et éclairées, sur la branche
`lot-107-arena-of-fate-trois-zones-3d` : c'est ce que la recette de la `0.0.2.5`
([LOT-1010](../../v0.0.2.5-passage-3d/lots/LOT-1010-recette-et-version-0-0-2-5.md)) rejoue. La
proposition du 3 octobre — trois cartes de tailles différentes, des sous-sols rectangulaires, des
escaliers sans correspondance — est remplacée : l'auteur a demandé le 4 octobre des niveaux
« logiques entre eux », aux entrées qui se répondent, et un Colisée dont on sente le grandiose
([D-46](../../../../vision/decisions.md)).

**Une emprise, trois étages.** L'arène, le niveau −1 et les catacombes font **34 × 24 cases** et
partagent l'ovale de la coque. Un escalier a les mêmes cases à l'étage qu'il quitte et à celui
qu'il rejoint :

| Escalier | Cases | Relie |
|---|---|---|
| porte du triomphe (ouest) | (2-4, 11-12) | le sable et le niveau −1 |
| porte des morts (est) | (29-31, 11-12) | le sable et le niveau −1 |
| parvis (sud, sous le portail monumental) | (16-17, 20-22) | Arenarea et le niveau −1 |
| descente des catacombes (fond de la prison) | (22-23, 4-6) | le niveau −1 et les catacombes |

La chaîne — scripts, commandes, contrôles — est écrite au
[guide des données](../../../../../Documentation/Guide/guide-donnees.md#larena-of-fate--la-chaîne-de-ses-trois-niveaux).

**Le donjon.** Quatre chapelles en croix autour du sanctuaire du Culte, sous le centre du sable :
C'thraxis au nord, Z'ulvath au sud, Droggath à l'ouest, Krynnethoth à l'est — chacun enchaîné sur
son socle devant son cadre, l'autel et deux braseros à ses pieds. Quatre ossuaires occupent les
angles de la croix. Le seul accès est l'escalier de la prison, qui remonte sous la trémie du
niveau −1. Aucun symbole impérial ; les bannières du Culte ne sont qu'ici.

**Les pièces** des catacombes sont dans le kit de l'Arena of Fate (`arena-of-fate/Scene/`), avec
celles des deux autres niveaux : le dossier `catacombs/Scene/` du livrable n'a pas lieu d'être, les
trois cartes partagent une planche.

**Ce qui reste ouvert.** La validation artistique de l'auteur ; les **rencontres** et la récompense
du donjon, qui se décident avec la quête qui y conduit ; la version du lot, toujours inscrite à la
`0.0.3`.

**Le statut de la fiche.** Les trois lots du Colisée sont intégrés ensemble et attendent la
validation de l'auteur. Le graphe du planning ne dit « en cours » qu'un lot dont les prérequis sont
livrés : le `LOT-106` l'est, le `LOT-107` et le `LOT-157`, qui en dépendent, restent « à faire »
jusqu'à sa livraison — leur travail est fait, c'est leur clôture qui attend.

## Ce que la `0.1.0` en attend ([D-47](../../../../vision/decisions.md), 5 octobre 2026)

La `0.1.0` ne garde que trois lieux, et l'Arena of Fate — son sable, son niveau −1, ses catacombes —
est l'un d'eux : ce lot reste à la `0.0.3`, et doit y atteindre sa **qualité finale**. Ce qui
l'ouvre encore est écrit ci-dessus ; la clôture se fait sur la validation de l'auteur, sur le rendu
du moteur, de jour comme de nuit. La recette de la `0.0.2.5` a rejoué la quête et la série sur ces
trois cartes ([bilan](../../v0.0.2.5-passage-3d/bilan.md)).

La question de **sa version** — posée plus haut, « à déplacer si l'auteur préfère le rattacher à la
quête qui l'ouvrira » — est tranchée par la même décision : le donjon est de la `0.1.0`, avec l'arène.
Ses rencontres et sa récompense restent à décider.
