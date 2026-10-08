+++
id = "LOT-107"
titre = "Carte — Arena of Fate (donjon d'Arenarea)"
version = "0.0.4"
filiere = "cartes"
statut = "a-faire"
taille = "M"
resume = "L'Arena of Fate se parcourt, **à l'intérieur d'Arenarea**."
prerequis = ["LOT-106", "LOT-103", "LOT-126", "LOT-127", "LOT-128", "LOT-146", "LOT-1023"]
livrables = [
  "`Levels/central-empire/capital/arenarea/arena-of-fate.json` (le sable et ses anneaux) et `arena-of-fate/undercroft.json` (le niveau −1 : vestiaires et prison), dessinées **dans l'éditeur** et reliées par l'escalier de la porte du triomphe (décision D-21).",
  "Portails, points d'apparition nommés, zones (combat, déclencheurs de quête).",
]
criteres = [
  "`LevelEditor --check` passe : aucune case inatteignable, aucun portail sans arrivée, aucune référence morte.",
  "La carte tient 60 images par seconde à 1080p sur le poste de référence.",
  "Les 14 statues et les 13 tribunes d'honneur régionales sont posées et nommées ; `--check` ne relève aucune référence morte vers elles.",
  "Les vestiaires et la prison sont deux chemins distincts vers l'escalier de la porte du triomphe, tous deux atteignables ; l'escalier des catacombes est posé et condamné.",
]
maquettes = ["../../v0.0.1-demo/maquettes/plan-arena-of-fate.svg"]
+++

## Reprise V2 du Colisée — décision du 3 octobre 2026

La première proposition 3D est refusée par l’auteur : textures trop simples, statues
insuffisantes, bannières à mieux répartir. La reprise se fait **carte par carte**, en commençant
par le Colisée, selon cinq étapes : repérer les pièces complexes pour Meshy, construire les
volumes simples localement, générer les matières riches, générer la foule, rendre la carte.

Les quatorze références individuelles des dieux et un lion gardien sont livrés en PNG pour la
génération Meshy **par l’auteur**. Les modèles procéduraux de dieux sont retirés du jeu ;
les quinze modèles Meshy fournis ensuite par l’auteur sont intégrés : quatorze sculptures divines et deux lions sur leurs socles. Les originaux sont conservés intacts ; les copies installées sont normalisées par script sans simplification. Breith, la Dualité et les
Esprits de la Nature comportent des choix de représentation explicités avec les sources.

Portail monumental, loge impériale, velums, gradins, moulures, mâts et supports de foule sont
construits par script. Les textures originales comprennent cinq matières et deux vues de foule.
La galerie `Tools/Assets3D/Regions/central-empire/capital/arenarea/arena-of-fate/Production/V2/index.html`
donne les images Meshy, les matières, la foule et les rendus. La validation artistique finale
reste ouverte sur l’assemblage avec les modèles fournis, désormais intégrés.

Les vestiaires et les catacombes sont préservés pendant cette passe. Ils suivront chacun ce
cycle lors de leur propre reprise. Leurs contraintes de neutralité restent inchangées.


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
**Complément de l'auteur du 2 octobre 2026 : regrouper les bannières par alliance ; les
vestiaires sont une zone neutre, sans aucun symbole impérial.** La V5 validée fixe quatre bannières
communes au-dessus des groupes régionaux et retire l'héraldique impériale du sous-sol.

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



## Reporté à la `0.0.3` (décision [D-25](../../../../vision/decisions.md), 25 septembre 2026)

Ce lot servait la démo. C'est un lot de *world building*, trop complexe pour elle : il rejoint la
`0.0.3`, où il s'inscrit avec les six autres quartiers intra-muros. Dans la démo, l'Arena of Fate
est une **carte de principe**
([LOT-146](../../v0.0.1-demo/lots/LOT-146-cartes-de-principe-de-la-demo.md)) : le sable, le
vestiaire A et l'escalier, en maquette. Ce lot livre les deux cartes définitives, qui la remplacent
sous le même identifiant ; la pré-carte montée avec les pièces de `Tools/AssetsHD/Colisee/` n'a plus
lieu d'être, la carte de principe en tient le rôle.

## Une sous-zone, pas un quartier

L'Arena of Fate est un **donjon d'Arenarea** (décision D-16) : un lieu clos, à plusieurs salles —
vestiaire A, vestiaire B, couloir, sable —, où l'on entre **depuis le quartier**, par la porte de
l'arène au bout du parvis. Elle n'a pas d'entrée sur le plan de la Capitale : l'onglet « Carte »
la montre **dans** Arenarea. Ses assets et sa carte se rangent sous `capital/arenarea/arena-of-fate/`,
et elle puise d'abord dans le kit d'Arenarea, puis dans celui de la Capitale.

## Conception

La carte comprend une **pré-carte** d'abord, montée avec les pièces déjà présentes dans `Tools/AssetsHD/Colisee/` (sols, murs, angles, gardiens) : elle éprouve la chaîne et le rendu HD avant que le reste des pièces existe. Puis la carte finale : le sable (zone de combat), l'enceinte, le vestiaire A où arrive le condamné, le vestiaire B, le couloir, la porte vers Arenarea.

### Le tracé, d'après la DA

L'arène est dessinée **à la manière du Colisée de Rome** ([DA complète au référentiel](../../../../referentiels/central-empire/capitale.md#larena-of-fate--architecture-et-iconographie-da-de-lauteur-21-sept-2026)).
La carte fait **34 × 24 cases**, mais **seuls le sable et le niveau −1 se parcourent** : les trois
anneaux qui les entourent sont du décor en hauteur, posé une fois, et ne coûtent aucune case
d'atteignabilité.

| Anneau | Cases | Parcouru ? | Ce qu'il porte |
|---|---|---|---|
| Sable | ovale de **22 × 14** | **oui** — c'est la zone de combat | dalle de fond en 3 variantes, marques au sol |
| Podium | 1 case, 2 de haut | non | mur de marbre, balustrade ; infranchissable des deux côtés |
| Coursive des dieux | 1 case | non | **14 socles à statue** répartis régulièrement, braseros entre eux |
| Gradins | 3 à 5 cases | non | **4 secteurs de peuple**, chacun percé d'une **tribune d'honneur** avec son **drapeau** devant ; enceinte à arcades et attique en fond |

Les **14 statues** se répartissent sur la coursive, régulièrement, face au sable ; les **4 tribunes**
sont dans l'anneau suivant et ne se disputent donc aucune place avec elles. L'ordre autour de
l'ovale est fixé par la DA (D-18) : la **loge impériale** sur le grand axe côté parvis — celle que
le combattant voit en levant les yeux —, les **Forces alliées** en face, **Arcanum** et **Forces de
Darkall** sur le petit axe. Ni statue d'Ungod ni loge du Culte : ils sont deux niveaux plus bas.

### Le niveau −1 : vestiaires et prison

Sous les tribunes, un second niveau se parcourt, et il tient **deux quartiers qui ne communiquent
pas entre eux** :

- les **vestiaires des gladiateurs** — ceux qui combattent de leur plein gré ; le portail vers le
  **parvis d'Arenarea** est au bout de leur couloir ;
- la **prison** — les **condamnés à mort envoyés au jeu dans l'arène** : cellules à grille, corps
  de garde, la salle où le maître d'arène vient chercher le condamné.

Les deux couloirs débouchent sur le même **escalier de la porte du triomphe**, qui monte au sable ;
la **porte des morts** est en face. Dans la quête de la démo, le condamné arrive par la prison et
son adversaire par les vestiaires : les deux chemins doivent donc être distincts et tous deux
atteignables.

Au fond de la prison, l'**escalier des catacombes** descend au niveau −2. Il est posé sur la carte
et **condamné** : c'est le crochet du `LOT-157`. Le contrôle de l'éditeur doit l'accepter comme
porte sans arrivée — sinon la carte est marquée d'un portail mort : c'est `portal.sealed`, au
[LOT-126](../../v0.0.1-demo/lots/LOT-126-ce-que-la-quete-demande-aux-cartes.md).

### Deux cartes, pas deux étages

Le niveau −1 est **sous** les gradins, qui occupent les mêmes cases en décor. Un niveau est une carte
(décision D-21) : le lot livre **deux cartes** — `arena-of-fate.json`, le sable et ses anneaux, et
`arena-of-fate/undercroft.json`, les vestiaires et la prison. L'**escalier de la porte du triomphe** est le
portail entre elles ; la **porte des morts** en est un second. Le portail vers le parvis d'Arenarea et
l'escalier condamné des catacombes sont sur la carte du sous-sol. La taille de 34 × 24 ne vaut que
pour la carte du sable ; celle du sous-sol se fixe au tracé. L'onglet « Carte » montre les deux sous la
même sous-zone.

![Plan de principe](../../v0.0.1-demo/maquettes/plan-arena-of-fate.svg)

Le plan ci-dessus est un **schéma de principe** : il fixe ce que la carte contient et comment on y
circule, pas son dessin.

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

**Le niveau −1** suit la conception ci-dessus : les **vestiaires** des gladiateurs à l'ouest, la
**prison** à l'est, séparés par un mur plein. Ils ne communiquent que par la **galerie axiale**,
sous le grand axe du sable, qui mène de la prison à la salle du triomphe ; les deux vestiaires y
débouchent chacun par sa baie. Le parvis d'Arenarea entre au sud, par le vestibule du vestiaire B ;
sous `condamne`, sa herse est close. La porte des morts descend à l'est, dans la salle des morts de
la prison ; la descente des catacombes est au fond de la prison nord.

**L'arène** garde son sable, ses treize délégations et ses quatorze statues ; elle gagne onze
**feux** sur son pourtour, un entre deux statues, qui éclairent le sable de nuit.

**Contrôles.** `LevelEditor --check` : 0 erreur ; `check_arena_fate.py --require-meshy
--underground-v3` et `check_arena_fate_levels.py` passent. La taille de 34 × 24 vaut désormais pour
les trois cartes — la phrase de la conception qui la réservait au sable est remplacée. L'escalier
des catacombes n'est plus condamné : le `LOT-157` l'ouvre dans la même livraison.

**Ce qui reste ouvert.** La validation artistique de l'auteur ; la cadence à 1080p sur le poste de
référence (critère du lot), à relever au bilan ; les cloisons du niveau −1 sont basses pour laisser
voir les salles — un mur qui s'efface devant le héros serait l'affaire du moteur.

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
