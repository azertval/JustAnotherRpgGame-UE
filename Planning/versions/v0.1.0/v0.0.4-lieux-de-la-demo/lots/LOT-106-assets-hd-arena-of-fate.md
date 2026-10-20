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

## Refonte complète de l'Arena of Fate — décision du 9 octobre 2026

La référence au *Tanares Sourcebook*, la composition et la narration de l'arène sont conservées.
Après comparaison, l'auteur retient **le style fantasy peint précédent**, avec des textures
beaucoup plus détaillées, plus variées et un ensemble moins lisse.
L'extérieur conserve l'emprise monumentale de **189 × 156 × 48 m** ; l'organisation intérieure,
les connexions et les hauteurs sont libres si les fonctions et les flux du lieu restent lisibles.
Tout le décor devra être praticable, y compris les gradins et les loges, dans un parcours physique
continu. Les murs et plafonds seront complets et s'effaceront lorsqu'ils masquent le personnage.
La scène complète devra comprendre la foule, les bannières, les feux et l'ambiance.

**Témoin validé par l'auteur le 9 octobre 2026.** La construction complète est autorisée.
L'auteur précise que l'amélioration doit maintenant venir des props et de l'habillage de la
version finale. Les textures peintes enrichies constituent la base validée. Les accessoires
doivent exprimer la préparation des gladiateurs, la détention, l'entretien, les cérémonies et
les réceptions des délégations, tout en laissant les circulations praticables.
L'auteur précise ensuite **« Décor d'abord, foule ensuite »** : la foule est différée à
l'arrivée des personnages de la nouvelle chaîne. Elle ne conditionne pas cette passe de décor.

### Propagation du témoin enrichi — 10 octobre 2026

L’auteur valide les vues du témoin de jour et de nuit et autorise sa propagation. La carte
complète comporte 1826 éléments, dont 1468 pièces d’architecture et 317 accessoires.
Les sculptures et les emblèmes du projet sont réemployés. L’emprise reste de 189 × 156 m,
avec un sommet à 48,03 m. Les sept niveaux vont des catacombes à −12 m à la terrasse à 46,8 m.
Les gradins, loges, galeries et le seuil sud reprennent les reliefs et matières du témoin.
Les vestiaires conservent leur neutralité ; grilles de cellules, fontaines, liens des
effigies et inscriptions des socles complètent les éléments narratifs de la référence.

Le gameplay existant, les rencontres, le groupe, les étages et leurs données restent
strictement identiques à la carte précédant cette propagation. La foule reste différée,
et la ville d’Arenarea n’entre pas dans ce périmètre.

Nanite conserve les maillages visuels au maître. Les trois sols annulaires utilisent
des collisions architecturales fermées, de mêmes contours à 192 cordes, mêmes hauteurs
et mêmes trémies ; leur géométrie visuelle détaillée reste intacte. Les autres sols et
escaliers gardent une collision fidèle à leur géométrie. Les nervures suivent leurs voûtes,
les appliques suivent leurs murs, et les accessoires suivent leur support de sol lors
de la coupe, avec conservation des collisions et de l’éclairage.

Les 235 positions de contrôle et les 66 points du parcours sont reliés. Le groupe a
parcouru ce trajet dans les deux sens : **132/132 arrêts**, sans portail ni téléportation,
avec les tolérances de 35 cm horizontalement et 10 cm en hauteur.
Les 26 captures à midi et à 22 h proviennent du moteur sans retouche.
Les mesures courtes en 1920 × 1080 sur RTX 4060 Ti donnent **86.3 images/s à midi
et 82.5 à 22 h**, sans foule. Elles décrivent la scène de mesure et ne garantissent
pas la cadence à chaque position ni en combat. Les sons installés ne sont pas audités
par les exécutions sans son.

Les empreintes des sources, des captures et des rapports actuels sont conservées dans
[le relevé de validation technique](../annexes/LOT-106/modern-decor-validation.json).
La revue se reproduit avec `scripts/maps/review_arena_fate_modern.ps1 -Walk` ; `-Generate`
refait aussi les sources Blender. Les rapports sont dans `Saved/Jadg/arena-fate-modern/`
et les captures dans `Saved/Captures/arena-fate-modern/`. La validation artistique finale
de l’arène complète reste distincte de l’approbation du témoin.

### Style peint conservé — matières enrichies du 9 octobre

L'auteur préfère le style peint précédent et demande davantage de détails et de variations.
La passe dessin accentuée est retirée, avec ses deux matériaux Unreal. La palette, les
cadrages, l'éclairage et les formes de la proposition peinte sont conservés.

Les huit matières sont enrichies : pores et traces de taille du calcaire, veines et variations
de poli du marbre, patine et rayures du bronze, métal martelé, tissage du tissu, fibres et nœuds
du bois, grains du sable et du mortier. Les normales et cartes ORM peintes passent en 2048².
Elles proviennent de champs physiques indépendants de la couleur ; le relief crête à crête
mesuré atteint 3,31 mm pour le calcaire, 1,15 mm pour le bois et 0,83 mm pour le bronze.

L'outil intégré de génération d'images enrichit la peinture originale du calcaire. Le résultat
est conservé intact en 1254² dans
`Source/Elements/Assets/Built/arena-witness-materials/inputs/stone_cream_painted_detail.png`,
avec sa consigne complète dans `stone_cream_painted_detail.provenance.json`. Aucune image du
sourcebook n'est envoyée. Unreal prépare ses mipmaps ; la répétabilité exacte de cette image
générée reste une limite distincte des champs procéduraux, dont la périodicité est contrôlée.

Chaque bloc de calcaire ou de marbre porte une graine constante, y compris sur ses biseaux.
Le matériau s'en sert pour décaler ensemble couleur, relief et ORM ; les teintes varient aussi
entre blocs. Cet attribut n'affecte pas l'opacité. La comparaison des 16 GLB confirme les mêmes
1 191 484 triangles, positions à 10 µm près, UV et couleurs RGB. La réexportation change quelques
normales de moins de 0,0057 degré, sans modifier les surfaces praticables
(`Saved/Jadg/arena-witness/detail-alpha-comparison.json`).

Le moteur construit les matériaux sans erreur de shader et retrouve tous les points de
navigation. Le parcours physique **50/50** déjà réalisé reste applicable aux sols et escaliers
inchangés. Les 72 PNG des trois familles historiques et leurs empreintes sont vérifiés ; les
mesures des huit matières peintes sont consignées dans
`Saved/Jadg/arena-witness/texture-detail-validation.json`.

Les dix captures finales sont dans `Saved/Captures/arena-witness/painted/`. La galerie
`Saved/Captures/arena-witness/index.html` compare les matières enrichies au style peint conservé
dans `arena-witness-before-drawn/painted/`, aux mêmes heures et cadrages. La revue visuelle
confirme les détails du calcaire en gros plan et la variation entre blocs au cadrage du joueur,
de jour comme de nuit. Les relevés courts donnent **92,8 images/s à midi et 95,7 à 22 h** en
1920 × 1080 sur RTX 4060 Ti. Ces mesures portent uniquement sur le témoin sans foule.
Le style peint est retenu par l'auteur ; le témoin présente maintenant la qualité de matière
demandée pour revue, avant la reconstruction complète de l'arène.

### Dessin plus marqué — essai écarté du 9 octobre

L'auteur demande un **« style dessin encore plus marqué »**. La géométrie, les collisions,
les points de passage et les cinq cadrages restent identiques. Les matériaux mélangent un
pigment uni à leurs textures : calcaire à 28 % de texture, marbre à 25 %, tissu à 70 % ; les
normales de surface sont atténuées et la pierre devient plus mate. Les PNG sources sont conservés.

L'ancien `arena_witness_illustration.py` construisait une passe propre au témoin : luminance
regroupée par paliers, ombres légèrement refroidies, lumières réchauffées et contours
brun-charbon fondés sur la profondeur. Elle passe après la profondeur de champ et avant
l'anticrénelage temporel d'Unreal. Le second réglage adoucit les transitions et réduit le
crénelage visible au premier essai. La lumière réelle, le cycle jour/nuit et les autres effets
de sélection sont conservés.

Les dix captures de cet essai sont archivées dans
`Saved/Jadg/arena-witness/drawn-rejected/captures/`. La galerie comparait
la fantasy peinte précédente (`arena-witness-before-drawn/painted/`) à cette proposition.
Les relevés courts en 1920 × 1080 sur RTX 4060 Ti donnent **100,5 images/s à midi et 103,3 à
22 h**, sur cet extrait sans foule ; ils ne préjugent pas de la scène complète. Le parcours
**50/50** de l'étape précédente reste applicable : aucun sol, escalier ni collision n'a changé.
Le moteur a construit les matériaux et produit les captures sans erreur de shader ; Ruff et
le contrôle des assets/scripts orphelins passent. Le rendu reste soumis à la validation
artistique de l'auteur avant la reconstruction complète. **Essai ensuite écarté par l'auteur**,
qui préfère le style peint précédent ; ses sources et captures sont archivées dans
`Saved/Jadg/arena-witness/drawn-rejected/`, et la passe est retirée de la scène.

### Reprise fantasy illustrée après le premier retour

L'auteur juge les trois traitements du premier témoin difficiles à distinguer, les textures
pauvres et l'ensemble plat. Il ouvre une direction dessin fantasy comme les portraits.
La proposition suivante reprend ensemble la géométrie, les matières et l'éclairage : 286 pierres
modelées, 534 dalles taillées, 72 tambours cannelés, des filets de bronze, des joints sur mortier
reculé et une variation colorée par bloc. Les trois volées (deux d'accès, une dans les gradins)
deviennent des volumes fermés continus, sans les anciens nez de marche superposés.
Les points de passage et les cinq cadrages restent inchangés.

La couleur du calcaire est une peinture minérale originale produite avec l'outil intégré de
génération d'images. Son PNG source est conservé intact dans
`Source/Elements/Assets/Built/arena-witness-materials/inputs/stone_cream_painted.png`, avec les
consignes et limites dans `stone_cream_painted.provenance.json`. Aucune image du sourcebook
n'a été fournie au générateur. Les cartes de normales et d'ORM proviennent de champs physiques
indépendants. Unreal effectue le traitement vers une puissance de deux pour les mipmaps ; la
périodicité de l'image générée n'est pas mathématiquement garantie.

Le témoin reçoit un ciel de réflexion gradué, un soleil plus défini et des lampes plus locales.
La galerie compare **l'avant et la proposition globale**, et non deux seules matières. Le
premier essai est conservé dans `Saved/Captures/arena-witness-before-fantasy/`. Les dix nouvelles
captures sont conservées dans `Saved/Captures/arena-witness-before-drawn/painted/`, à midi et à 22 h, avec
les cinq cadrages identiques. Les grandes faces de mortier aux ouvertures sont corrigées ; les
diagonales des anciens nez de marche ne sont plus visibles dans cette passe.

Le nouveau parcours physique est validé : **50 points sur 50**, aller-retour en 135,0 secondes,
dans `Saved/Jadg/arena-witness/walk-painted.json`. La dernière correction recule seulement le
support des cinq murs ; la comparaison des triangles et attributs des sols et escaliers, à
10 µm près et indépendamment de l'ordre d'export, confirme leur invariance
(`Saved/Jadg/arena-witness/mortar-canonical-comparison.json`).

La capture finale mesure **96,8 images/s à midi et 101,4 à 22 h**, en 1920 × 1080 sur RTX 4060 Ti
(`Saved/Captures/arena-witness-before-drawn/painted/mesure.json`). Ces relevés courts portent sur ce seul extrait
sans foule. Le rendu conserve une base 3D éclairée par Unreal et des matières peintes ; il ne
prétend pas reproduire exactement le dessin des portraits. La direction artistique reste à
valider avant toute reconstruction complète.

### Premier témoin présenté — mesures antérieures à la reprise

La première étape est un témoin Unreal réunissant une arcade, des gradins, une salle voûtée et un
escalier. Il a été présenté : `scripts/assetsGeneration/build_arena_witness.py` génère la
géométrie modulaire avec Blender, `build_arena_witness_textures.py` les textures, et
`scripts/maps/build_arena_witness_scene.py` les trois scènes. La commande
`scripts/maps/review_arena_witness.ps1 -Generate -Compile -Walk` orchestre la génération et la revue. Les trois traitements partagent la même
géométrie et le même éclairage ; seul le traitement visuel varie. Ce témoin est un extrait de
l'arène, pas le remplacement de la carte complète. Les rendus au cadrage du joueur, à midi et à
22 h sont conservés dans `Saved/Captures/arena-witness-before-fantasy/index.html` ; la validation artistique par
l'auteur est **en attente** avant la reconstruction complète.

**État de la production du témoin.** La compilation de la cible éditeur sous Unreal Engine 5.8.3
a réussi ; `JadgContentCheck` valide quatre fiches. Le rapport
`Saved/Automation/Jadg/index.json` consigne 27 tests réussis, sans avertissement ni échec ;
`check_orphans.py` passe. La galerie locale est produite par
`scripts/maps/render_arena_witness_review.py`. Ces contrôles ne valent pas validation artistique.

La marche complète du personnage sur la géométrie commune est validée : 50 points sur 50,
aller-retour physique sans portail, dont les deux côtés des sept rangées, la loge, la salle et
l'escalier à deux volées (`Saved/Jadg/arena-witness/walk-stylized.json`). Le contrôle de hauteur
est de 10 cm. La navigation propre au témoin emploie des cellules de 5 × 2 cm et conserve
l'erreur verticale dans ses contours ; les arrêts se font sur les paliers et les rangées.
Les 30 captures des trois traitements sont produites (cinq cadrages à deux heures). Les mesures
sur RTX 4060 Ti en 1920 × 1080, consignées dans chaque `mesure.json`, concernent uniquement
ce témoin sans foule :

| Traitement | Midi | 22 h |
|---|---:|---:|
| Réalisme stylisé | 101,6 images/s | 101,3 images/s |
| Peint remanié | 99,3 images/s | 99,3 images/s |
| Réalisme poussé | 102,8 images/s | 96,8 images/s |

Ces relevés courts ne préjugent pas de la cadence de l'arène complète. Le traitement peint porte
sur les matières ; il n'ajoute pas de shader de rendu non photoréaliste. Le témoin emploie une
coupe franche de visibilité : la
collision et la physique restent actives, comme les ombres et l'éclairage indirect des éléments
masqués. La transition fondue reste à affiner pour la carte complète. Ce témoin n'ajoute ni foule
ni effets visuels nouveaux.

**Réserve de revue visuelle.** De fines diagonales restent visibles sur certaines marches dans
la vue éloignée, alors que le cadrage rapproché est net. Les normales horizontales des marches
sont correctes dans le GLB. Un essai temporaire à `r.Nanite.MaxPixelsPerEdge=0.25`
(`Saved/Captures/arena-witness/nanite-detail-probe/`) ne les a pas supprimées ; leur cause reste
à établir. Aucun réglage de cet essai n'est conservé. La galerie permet le choix des matières,
sans valider cette finition géométrique ni la carte complète.

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

L'Arena of Fate est désormais **une seule carte à trois étages** ([LOT-1022](../../v0.0.3-nouveau-moteur/lots/LOT-1022-portage-arena-of-fate.md), D-51) : le
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
