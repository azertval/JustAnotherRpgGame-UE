+++
id = "LOT-106"
titre = "Assets HD — Arena of Fate (donjon d'Arenarea)"
version = "0.0.4"
filiere = "assets"
statut = "en-cours"
taille = "L"
resume = "Les pièces propres à Arena of Fate, produites au standard et installées dans `capital/arenarea/arena-of-fate/Scene/`."
prerequis = ["LOT-105", "LOT-129"]
livrables = [
  "`Regions/central-empire/capital/arenarea/arena-of-fate/Scene/` : pièces, `manifest.json`, `appearance.json`.",
  "La commande de la zone (`Tools/AssetsHD/`) : les dix familles passées en revue, ce qui vient du kit, ce qui est propre.",
  "La page de galerie de la zone.",
]
criteres = [
  "Toutes les pièces de l'inventaire ci-dessous paraissent dans la galerie, à l'échelle du standard.",
  "Les 14 divinités reconnues ont chacune leur statue, et les 13 délégations régionales chacune leur tribune et son drapeau : la galerie les montre nommées, et aucune ne manque.",
  "Aucune pièce du lot ne représente un Ungod ni le Culte de l'Aile d'Ombre : ces pièces sont au LOT-157.",
  "Aucune pièce ne double une pièce du kit commun.",
]
sources = [
  "Tanares Sourcebook, p. 91-92, 99 : seule arène où l'on conteste un décret impérial",
  "Tanares Sourcebook, ch. 4 (p. 68-86) : les 18 divinités — 14 en statue sur la coursive, les 4 Ungods aux catacombes (LOT-157)",
  "Tanares Sourcebook, ch. 2 (p. 38-49) : les 5 factions — 4 tribunes d'honneur, le Culte n'est pas reçu",
  "Le Colisée de Rome : référence d'architecture (DA de l'auteur, 21 sept. 2026)",
]
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
([LOT-146](../../v0.0.1-demo/lots/LOT-146-cartes-de-principe-de-la-demo.md)), sans pièce propre : ce
lot lui donne ses pièces définitives. Il attend le kit complété (`LOT-151`) et la reprise d'Arenarea
([LOT-147](LOT-147-zone-arenarea-reprise.md)), avec laquelle sa façade se coordonne.

## Le lieu

L'amphithéâtre ovale en bord de baie, **à la manière du Colisée de Rome** : sable en contrebas,
podium de marbre, trois niveaux d'arcades superposées, attique à pilastres, gradins rouges, feux
sur le pourtour. La direction artistique complète est dans
[le référentiel de la Capitale](../../../../referentiels/central-empire/capitale.md#larena-of-fate--architecture-et-iconographie-da-de-lauteur-21-sept-2026).
Elle est la **commande** de ce lot ; ce qui suit n'en est que le découpage en pièces.

## Ce que ce lot habille : deux niveaux sur trois

Le monument en compte trois (D-18) :

| Niveau | Ce qu'il est | Ce lot ? |
|---|---|---|
| **0 — l'arène** | sable, podium, coursive, gradins | **oui** |
| **−1 — sous les tribunes** | vestiaires des gladiateurs, **prison des condamnés** | **oui** |
| **−2 — les catacombes** | les Ungods enchaînés, le donjon cultiste | **non** — `LOT-157` |

Au niveau 0, du sable vers l'extérieur, la scène se lit en **trois anneaux**, et l'inventaire suit
ce découpage :

1. **Le podium** — mur droit de deux cases, plaqué de marbre, balustrade au sommet ;
2. **La coursive des dieux** — **14 socles à statue** face au sable, un brasero entre deux socles ;
3. **Les gradins** — **quatre secteurs de peuple**, chacun percé d'une **tribune d'honneur** de
   faction, drapeau tendu devant ; derrière eux, l'enceinte à arcades et l'attique.

## Inventaire des pièces propres

**01 Sols** — sable (dalle de fond répétable en 3 variantes, règle du §4 du standard), pavé de la
coursive et du niveau −1, bordures sable / pavé / marbre.

**02 Façades** — enceinte extérieure : travée d'arcade toscane (rez), ionienne (1er), corinthienne
(2e), panneau d'attique à pilastre et corbeau de mât, angle rentrant, angle sortant.

**03 Colonnes** — les trois ordres en pièce isolée, pour les loges et le seuil.

**04 Accès** — **porte du triomphe** et **porte des morts** (grand axe), herse, grille de vestiaire,
bouche de vomitoire.

**05 Balustrades** — couronnement du podium (droite, angle, pilier) ; garde-corps de loge.

**06 Pièces maîtresses** — **14 statues de divinités** sur socle gravé, en marbre clair, plus un
socle particulier pour Fumetsu Tenshinkin, qui n'est pas un vrai dieu. **4 tribunes d'honneur** :
la loge impériale (la plus grande) et trois loges ouvertes. Braseros du pourtour. **Aucune pièce
d'Ungod ni du Culte** : elles sont au `LOT-157`, avec les catacombes.

**07 Végétal** — néant : rien ne pousse dans une arène (la famille est passée en revue et écartée).

**08 Mobilier** — niveau −1. **Vestiaires des gladiateurs** : râtelier d'armes, banc, fontaine,
seau, torche murale. **Prison des condamnés** : grille de cellule, paillasse, chaîne murale, banc
de garde, brasero de corps de garde. Les deux jeux ne se ressemblent pas : l'un est un vestiaire,
l'autre une geôle.

**09 Bâtiments** — **gradins du peuple en HD**, quatre secteurs, chacun dans la couleur de sa faction ;
les bandes de foule existantes sont en pixel art et se refont. Les deux gardiens de l'entrée.

**10 Seuils** — parvis de la porte du triomphe, escalier du niveau −1, arche de vomitoire, et
l'**escalier des catacombes** au fond de la prison : la pièce est produite ici, **condamnée et
close** ; ce qu'il y a derrière est au `LOT-157`.

**Les drapeaux** — quatre bannières de faction (Empire tanaréen, Forces alliées, Arcanum, Forces
de Darkall), au repos et animées au vent ; le Culte n'est pas reçu, donc pas de cinquième. Héraldique **inventée**, décrite au
référentiel : le livre donne les emblèmes en image, jamais en texte, et **rien n'est décalqué**.
La bannière au lion de l'Empire vient du kit commun (LOT-105), en grand format.

Le détail du quartier — texte du livre et lieux nommés sur le plan — est dans
[le référentiel de la Capitale](../../../../referentiels/central-empire/capitale.md).

## Une sous-zone, pas un quartier

L'Arena of Fate est un **donjon d'Arenarea** (décision D-16) : un lieu clos, à plusieurs salles —
vestiaire A, vestiaire B, couloir, sable —, où l'on entre **depuis le quartier**, par la porte de
l'arène au bout du parvis. Elle n'a pas d'entrée sur le plan de la Capitale : l'onglet « Carte »
la montre **dans** Arenarea. Ses assets et sa carte se rangent sous `capital/arenarea/arena-of-fate/`,
et elle puise d'abord dans le kit d'Arenarea, puis dans celui de la Capitale.

## Périmètre

Les **pièces de scène** seulement. Les figurines sont au lot des PNJ, la carte au lot de la carte.
**Les catacombes en sont dehors** — pièces, Ungods enchaînés, iconographie du Culte : tout cela est
au `LOT-157`. Ce lot s'arrête à la porte condamnée au fond de la prison.

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
[guide des données](../../../../../Documentation/Guide/guide-donnees.md#larena-of-fate--une-carte-à-trois-étages).

**Le kit.** 105 maillages, 297 Mio, 2,04 millions de triangles ; les 18 images de la carte de
principe et 29 pièces des premières générations (arcades, podium, gradins et loges remplacés par la
coque ; murs hauts que le plan ne pose plus) sont retirés. S'y ajoutent, par
`arena_fate_enclosures.py` : l'**enceinte ovale** de chaque sous-sol, les escaliers tournés vers
l'est, l'ouest et le sud, la trémie des catacombes et les **feux du pourtour**. La coque du Colisée
reçoit l'**attique** de la DA — pilastres, fenêtres carrées, corbeaux, mâts de velum —, au nord
seulement : côté caméra il cacherait le sable.

**La matière.** Chaque pièce porte relief et occlusion-rugosité-métal (D-46) : ceux de son original
pour les 24 sculptures de l'auteur, dérivés de sa couleur pour l'architecture, une matière par case
d'atlas. Chargé en entier, le kit tient 0,7 Gio de mémoire graphique, textures partagées ; il en
tiendrait 3,3 sans ce partage.

**Ce qui reste ouvert.** La validation artistique de l'auteur, sur captures du moteur à midi et à
22 h. La finesse des sculptures est celle des modèles reçus. La coque est un seul maillage de
878 000 triangles : le budget d'un maillage de décor reste à mesurer (LOT-151), et la cadence de
l'arène est à relever au bilan de la `0.0.2.5`. Le critère des « 13 tribunes nommées dans la
galerie » se lit désormais sur la coque et ses treize bannières : les loges n'en sont plus des
pièces séparées.

**Le statut de la fiche.** Les trois lots du Colisée sont intégrés ensemble et attendent la
validation de l'auteur. Le graphe du planning ne dit « en cours » qu'un lot dont les prérequis sont
livrés : le `LOT-106` l'est, le `LOT-107` et le `LOT-157`, qui en dépendent, restent « à faire »
jusqu'à sa livraison — leur travail est fait, c'est leur clôture qui attend.

**Les prérequis.** Le kit s'est produit avant le kit commun intra-muros (`LOT-151`) et la reprise
d'Arenarea (`LOT-147`), pour la recette de la `0.0.2.5` : il ne les attend plus. Sa façade se
coordonnera avec le parvis quand le `LOT-147` le reprendra.

## Ce que la `0.1.0` en attend ([D-47](../../../../vision/decisions.md), 5 octobre 2026)

La `0.1.0` ne garde que trois lieux, et l'Arena of Fate — son sable, son niveau −1, ses catacombes —
est l'un d'eux : ce lot reste à la `0.0.3`, et doit y atteindre sa **qualité finale**. Ce qui
l'ouvre encore est écrit ci-dessus ; la clôture se fait sur la validation de l'auteur, sur le rendu
du moteur, de jour comme de nuit. La recette de la `0.0.2.5` a rejoué la quête et la série sur ces
trois cartes ([bilan](../../v0.0.2.5-passage-3d/bilan.md)).

## Le portage au nouveau moteur (LOT-1022, 9 octobre 2026)

L'Arena of Fate est désormais **une seule carte à trois étages** ([LOT-1022](../../v0.0.3-nouveau-moteur/lots/LOT-1022-portage-arena-of-fate-et-martpart.md), D-51) : le
sable, les vestiaires et la prison (niveau −1, à −5,5 m), les catacombes (niveau −2, à −12,1 m),
leurs pièces et leurs entités telles que les trois cartes de la v4 les posaient, un niveau de
chargement par étage. Les escaliers sont aux mêmes cases ; ils relient les étages par les portails
de la v4, qui visent désormais la carte elle-même. Rendu du moteur, **à juger par l'auteur à la
recette** :

- le sable, l'ensemble : [midi](../../v0.0.3-nouveau-moteur/annexes/LOT-1022/captures/arena-of-fate-ensemble-1200.png), [22 h](../../v0.0.3-nouveau-moteur/annexes/LOT-1022/captures/arena-of-fate-ensemble-2200.png) ;
- le sable, au cadrage du joueur : [midi](../../v0.0.3-nouveau-moteur/annexes/LOT-1022/captures/arena-of-fate-sable-1200.png), [22 h](../../v0.0.3-nouveau-moteur/annexes/LOT-1022/captures/arena-of-fate-sable-2200.png) ;
- les vestiaires et la prison : [midi](../../v0.0.3-nouveau-moteur/annexes/LOT-1022/captures/arena-of-fate-vestiaires-ensemble-1200.png), [22 h](../../v0.0.3-nouveau-moteur/annexes/LOT-1022/captures/arena-of-fate-vestiaires-ensemble-2200.png) ;
- les catacombes : [midi](../../v0.0.3-nouveau-moteur/annexes/LOT-1022/captures/arena-of-fate-catacombes-ensemble-1200.png), [22 h](../../v0.0.3-nouveau-moteur/annexes/LOT-1022/captures/arena-of-fate-catacombes-ensemble-2200.png).

La cadence, les trois étages chargés : 102 images/s à 1080p, de jour comme de nuit (le critère
de D-54 est de 60) ; le sable seul, 108. Le détail est dans la fiche du lot.
