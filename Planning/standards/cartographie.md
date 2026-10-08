# Cartographie du jeu

Décisions de l’auteur du **5 octobre 2026** : l’atlas illustré de la capitale est validé,
ce format devient le standard des cartes du jeu. Il s’étend au monde, aux régions et à tous
les lieux géographiques documentés. Les étages supérieurs des bâtiments ne sont pas accessibles
au joueur. Les treize factions régionales et les **cultistes**, sans région dédiée, forment
le catalogue des quatorze factions.

Décision de l’auteur du **6 octobre 2026** : toutes les cartes utilisent le même
format paysage. Les deux références absolues de facture et de cadrage sont
`Tools/WorldAtlas20261005/generated-images/exec-3f2751ae-d49b-4e2c-ad21-07f0bb8d8ee2.png`
pour les villes et leurs quartiers, et
`Tools/WorldAtlas20261005/generated-images/exec-ea864bc9-a14c-4f2b-bae3-e56209bdae6d.png`
pour le monde et les paysages. Leurs dimensions mesurées sont respectivement
1536 × 1024 et 1492 × 1054 pixels. La livraison commune reprend **1536 × 1024**,
le format de la capitale. Les légendes de ces références ne remplacent pas les
noms et la géographie établis par le corpus.

Une ville se **reconstruit entièrement dans la vue isométrique oblique de la
capitale** : une reprise du plan aérien du livre, même repeinte, ne convient pas.
Le livre établit les lieux, leurs fonctions et leurs relations ; sa composition
graphique ne se transfère pas. Les quartiers et zones conservent les formes de
leur nouvelle carte maîtresse. Les plans schématiques restent issus de leurs
données de construction ; ils sont exportés dans le même cadre paysage.

## Références et cohérence

La seule référence de géographie mondiale est `Documentation/SourceBook/VTT/Map - World.jpg`.
Les textes du livre et les référentiels du planning établissent le contenu des lieux.
Les anciennes illustrations ne fixent pas une nouvelle côte, rivière ou implantation.
Les illustrations du jeu sont originales ; les pixels du corpus ne sont pas livrés au jeu.
L'auteur précise que reprendre simplement la présentation du VTT ne convient pas : seule sa
géographie fait référence. L'atlas validé de la capitale fixe la facture illustrée commune :
reliefs en volume, matières peintes, eau, lumière et cartouches. Cette facture s'adapte aux
biomes sans conserver les icônes noires et blanches ni la typographie du VTT.

La capitale reprend l’atlas validé `Tools/Assets3D/Regions/central-empire/capital/AtlasCoherent20261005/`.
Une même empreinte architecturale relie le quartier, l’extérieur, les volumes et l’intérieur.
`Source/Elements/Maps/architectures.json` conserve les enveloppes validées de la capitale,
leurs empreintes et les repères des salles, en coordonnées graphiques sans unité.
Les tracés des subdivisions et des parcours validés y sont conservés avec la même empreinte,
pour que les lots dédiés puissent reprendre les salles dans ces volumes.
Les salles tiennent dans l’enveloppe commune. Les niveaux accessibles de l’Arena of Fate restent
l’arène, les vestiaires/prisons et les catacombes, reliées par la prison.
Un étage supérieur visible dans une référence conserve son volume extérieur ; il ne reçoit
pas de plan accessible. Une fenêtre ou une arcade ne suffit pas à établir un étage.

Le dessin cartographique ne constitue **pas une grille jouable**. Ses coordonnées graphiques
ne se convertissent pas en mètres ou en cases. Les scènes parcourables sont réalisées dans
leurs lots dédiés, avec le standard 3D et les dimensions établies par ces lots.

## Format et interface

`Source/Elements/Maps/world-maps.json` porte `cartographyVersion: 2`, le catalogue `plates`
et le catalogue `factions`. Les sections historiques monde/régions/villes restent lisibles
par les consommateurs antérieurs ; leurs anciens repères ne sont pas posés sur une nouvelle
illustration sans relevé spécifique.
Les lieux uniquement nommés sur le VTT possèdent une vue rapprochée de l'illustration régionale
commune. Le cadrage de consultation suit l'étendue géographique de référence ; il ne pose pas
un repère de scène. Les reliefs et formes sont ainsi identiques entre ces vues et leur région.
`scripts/maps/canonical_vtt_places.json` conserve le relevé visuel des noms et des cadres du VTT,
distinct de l'ancien catalogue peint, ainsi que les variantes des titres du livre.

Chaque carte possède un identifiant stable, un nom, une image originale, un parent et un type.
Les passages supplémentaires nomment une carte existante. Tous les parents rejoignent le monde,
sans cycle. Une carte se consulte avant que sa scène soit construite. `playerMap` relie uniquement
une scène déjà identifiée à sa fiche ; il ne prétend pas créer cette scène.

Les couches sont `illustration`, `plan`, `interior` et `architecture`, selon les références
effectivement disponibles. Aucun étage supérieur inaccessible n’est livré comme couche.
Les cartes livrées mesurent **1536 × 1024** ; le jeu les ajuste sans les étirer
ni recouper une partie du plan à l’ouverture. Les vues rapprochées gardent
le même rapport 3:2. Le déplacement,
le zoom, la recherche, le retour et le choix des vues fonctionnent aux différentes échelles.

L’emblème de la faction dominante se pose dans l’habillage de la carte, à partir de l’image de
référence existante, partagée entre toutes ses cartes. Il ne se régénère pas sur chaque illustration.
L'auteur demande de conserver une place pour les bannières : une bande de l'habillage est réservée
en dehors de l'image et des commandes. La bannière garde ses proportions natives ; elle ne cache
aucun accès, salle ou bâtiment du plan.
Les références se trouvent dans `arena-of-fate/Mockups/delegations.json` et `Production/Iconography/`.
Un contrôle politique local que les sources n’établissent pas ne s’invente pas : l’appartenance
régionale et une domination locale démontrée doivent rester distinguables dans les données.
Chaque fiche porte `factionBasis` : `regional` (la faction de sa région), `local` (une domination
démontrée par les sources, comme les cultistes des catacombes) ou `non-etablie` (aucune faction ;
l'écran le dit en toutes lettres). Le chargeur et `check_map_assets.py` refusent toute autre
combinaison. L'emblème ne remplace jamais le blason de l'interface : il n'a que sa bande.
Décision de l’auteur du 7 octobre 2026 : sur la **carte du monde**, la bannière de chaque faction
s’affiche en plus à droite du nom de sa région, à taille et écart constants. Elle est posée par l’interface, depuis la même image
de référence, sans retoucher l’illustration ; un territoire sans faction établie n’en porte pas.
Les bannières de délégation peintes dans l’Arena of Fate ne sont pas des passages vers les régions.

Décision de l’auteur du 7 octobre 2026, remplaçant les cadres du 6 octobre : les **noms déjà
imprimés sur la carte sont cliquables**, sans jeton. Leur survol ou leur sélection dessine en noir
le **contour précis du territoire** concerné, jamais un rectangle générique. Le cadrage de la
caméra reste distinct de ce contour. L’habillage reprend les parchemins, ornements, polices et
couleurs du jeu. Les lieux sans relevé restent accessibles par la liste et la recherche.

L’**Atelier des zones**, accessible dans l’atlas en mode développement, règle séparément la zone
cliquable du nom et les sommets du territoire, avec plusieurs contours pour les îles. Il écrit
`Source/Elements/Maps/map-interactions.json`, sans retoucher les illustrations ni les cadrages de
`world-maps.json`. Les coordonnées sont normalisées sur l’illustration entière du parent ; son
empreinte SHA-256 invalide le relevé si l’image change. Les premiers tracés issus du mockup sont
des brouillons (`reviewed: false`), pas des frontières validées. Seul l’auteur coche leur validation.
Une retouche remet ce statut à faux. Le chargeur refuse les polygones dégénérés, croisés ou hors
image ; l’enregistrement est atomique et refuse d’écraser une modification externe.

Décision de l’auteur du 7 octobre 2026 : le relevé couvre **toutes les sous-cartes**, et les noms
de **lieux voisins** imprimés sur une illustration y sont cliquables aussi. Une illustration de
région montre ses limitrophes, un plan de quartier nomme les quartiers d’à côté : ces lieux gardent
leur fiche et leur carte mère, mais reçoivent un second contour, rangé sous `neighbours` par carte
hôte, avec l’empreinte de l’illustration hôte. Le contour ne couvre que la part du lieu peinte sur
cette illustration. L’atelier règle les voisins déjà relevés d’une carte ; un nouveau voisin
s’ajoute dans le fichier. Un nom imprimé sans aucune fiche reste inerte tant que le catalogue ne le
connaît pas. Les relevés des sous-cartes s’appuient sur le livre et la carte de référence pour la
nature et l’étendue des lieux, et sur l’illustration pour leur forme ; leur justification lieu par
lieu est conservée dans `Tools/WorldAtlasZones20261007/`.

## Production et vérification

`scripts/maps/build_world_atlas.py prepare` prépare les descriptions et les recadrages du VTT
destinés uniquement au travail de référence. Les cartes originales sont produites avec l’outil
intégré de génération d’images, une commande par illustration. Depuis la décision de l’auteur
du 5 octobre 2026, le dossier physique de production sur ce poste est
`D:/Tools/WorldAtlas20261005/`, avec les illustrations dans `images/` et les sorties originales
dans `generated-images/`. Les anciens chemins du projet et du dossier de génération pointent
vers cet emplacement : les prochaines sorties de cette tâche sont enregistrées sur D:.
Les copies déplacées ont été vérifiées par empreinte SHA-256. Les vues rapprochées référencent ces illustrations communes,
avec leur cadre, et ne fabriquent pas une copie raster ni un nouveau bâtiment.
Les douze vues de Fisherman’s Wharf partagent également la carte maître reconstruite
de la ville ; leurs cadres sont relevés sur cette nouvelle illustration, jamais
repris du plan vertical du livre. Les zones de Darkall
et Mystical conservent de même leurs paysages communs ; les cadres sont des vues graphiques,
sans nouvelles coordonnées de scène ni limites politiques.
Le cache partagé des archives du jeu est également déplacé vers `D:/Tools/JadgAssets/` ;
l’ancien chemin `%LOCALAPPDATA%/JadgAssets` y est redirigé pour les installations futures.
Les commandes des illustrations sont conservées dans
`generation-specs.json`.

La reprise du 6 octobre est conservée dans
`Tools/WorldAtlasReview20261006/` : `style-masters.json` identifie les deux
références de l’auteur par empreinte, `records/` garde les commandes effectivement
exécutées et leurs sorties, et `final-selection.json` distingue les sorties
retenues des essais remplacés. `images/` et `capital/images/` contiennent les
illustrations maîtres révisées ; l’installation les applique avant les anciennes
sources. `registered-views.json` garde les cadres relevés sur les nouvelles
illustrations. Un lieu sans repère démontré conserve une vue de contexte de son
parent, sans position ponctuelle inventée. Les quartiers supplémentaires des
capitales et leurs citations sources sont dans `scripts/maps/capital_views.json`.

`scripts/maps/review_world_atlas.py` produit l’inventaire, les empreintes et les
planches de comparaison dans `build/atlas-homogeneity-20261006/`. La revue
distingue les images livrées des essais et versions écartées du dossier brut.

`scripts/maps/build_world_atlas.py install` installe les fichiers sous `Assets/Maps/`, écrit leurs
empreintes et leurs tailles dans le manifeste et actualise le catalogue du jeu. Il refuse une
livraison avec des images manquantes. Les anciennes images effectivement remplacées sont
supprimées dans la même modification, conformément à D-32.

`scripts/checks/check_map_assets.py` vérifie les images, leurs empreintes, les quatorze références
de faction, les parents, les passages, les couches accessibles et l’absence d’image orpheline.
Les tests `WorldMapsTest` éprouvent le chargement et le refus d’un catalogue incohérent.
La compilation QML et les captures du jeu vérifient ensuite la présentation réelle.

Décisions de l’auteur du 7 octobre 2026 : chaque bâtiment doté d’une vue intérieure
reçoit deux illustrations séparées, « Extérieur » et « Intérieur », comme Arena of Fate.
Les deux vues gardent la même enveloppe, la même caméra et le même voisinage. Les images
ne précisent ni les noms ni les numéros des salles et ne portent aucune mention
« proposé ». Les pièces validées et les deux références de facture restent la base
des reprises ; aucun décor, monument ou ornement supplémentaire ne sert à remplir la carte.
Illu Die Arena garde la toiture rouge de Martpart et de La Capitale. Mesoriver montre
la rivière et la plaine sous les îles flottantes. Les quartiers déjà cadrés de Kolbjörn
Capital, Pakaitos et Feargus sont nommés sur leurs illustrations.

La reprise de l’audit est conservée dans `Tools/WorldAtlasAudit20261007/`.
`scripts/maps/apply_atlas_audit.py` rejoue les corrections de données et de plans,
reçoit les nouvelles illustrations natives 1536 × 1024 et les installe avec leurs
empreintes. `approved-registration.json` contient les cadrages relevés sur l’image
du parent concerné, avec l’empreinte de cette image ; une image modifiée invalide le
relevé. Les propositions issues de lecture automatique restent dans un fichier de
travail et ne changent jamais seules un cadre. Le catalogue conserve les noms complets
de Fisherman’s Wharf et leurs formes courtes lisibles sur la carte comme alias.
Le livre emploie « Malland Hing Halls » en titre et « Malland King Halls » dans le
texte (page PDF 82) : le nom du catalogue est conservé et cette divergence est documentée.

Les nouveaux assets suivent le circuit des archives verrouillées des kits. Une archive locale
de production ne constitue pas une publication : le verrou distribué désigne uniquement une
archive effectivement disponible à l’installation.
