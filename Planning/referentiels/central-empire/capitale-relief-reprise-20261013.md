# Capitale — reprise du relief des 13–14 octobre 2026

Cette reprise répond à la correction de direction artistique de l'auteur : la
première scène est trop plate à l'intérieur de la ville. Les hauteurs, tracés
secondaires et formes architecturales ci-dessous sont des propositions
réversibles, expressément autorisées. Les rapports du premier passage restent
historiques ; seuls les rapports et captures régénérés décrivent cette reprise.

## Références et limites de l'interprétation

La carte VTT fixe les voisinages, les cours d'eau et les franchissements. Son
orientation reste ouest en haut et nord à droite. Le livre décrit fonctions,
matériaux et populations ; aucune cote métrique n'est déduite de la perspective.
Les 80 `reference.json`, leurs planches et le panorama v04 ont été confrontés à
la scène. Les terrasses du palais, les marches civiques de Scholarnest et les
jardins étagés de Dweomer motivent la composition proposée. Le panorama resserre
les quartiers et exagère certains monuments : il ne sert pas de relevé 3D.

Les relations carte/livre, propositions et incertitudes restent séparées dans
`references-80.json`. Les souterrains X12 et X13 n'ont aucun accès inventé.
Praharebaagh demeure réservé. Les relations de Cyan Fortress hors cadre sont
conservées ; le prolongement de terrain ne transforme pas ce site en île.

## Diagnostic et correction

Les anciennes plateformes appliquaient un raccord de 70 unités, soit 88,2 m,
autour de nombreuses institutions ; le parvis de l'arène avait une marge de
138,6 m. Les routes nivelaient encore 24 m au-delà de leurs accotements. Leur
enveloppe inférieure à 8 % rabattait les rues vers les contrôles bas.

Les plateformes ont maintenant une transition ordinaire de 15,12 m ; celle de
l'arène mesure 25,2 m. Les routes utilisent 1,5 m d'accotement et 7 m de raccord.
Leur résolution équilibre déblais/remblais par deux enveloppes. Les limites de
pente proposées dépendent des usages : 12 % pour le réseau principal, 14 à
20 % pour certaines voies secondaires et approches. Ce ne sont ni des valeurs
canoniques ni une déclaration d'accessibilité. Le diagnostic tolère 3 points
supplémentaires aux jonctions de la grille de 2 m et publie les valeurs réelles.

Les collines urbaines sont allongées et forment des éperons continus. La mer
reste à −2,5 m et le seuil Arena à 0 m. Emprise, résolution et unique Landscape
sont conservés. Les terrains proposés atteignent notamment 62 m au palais,
52 m à la cathédrale, 46 m à l'université et 58 m à la tour arcanique. La table
finale doit être lue pour les valeurs réellement encodées et posées.

Les fondations des maisons répondent à la pente de leur parcelle. Elles sont
exportées à leurs dimensions définitives pour conserver les UV à 2 m par motif.
Les courtines sont posées sur le point haut de chaque travée et reçoivent des
fondations lorsque leur pied ne suffit plus. Les voies taillées dans le relief
reçoivent des soutènements avec épaisseur et couronnement, interrompus aux
carrefours. Les trois terrasses de jardin du palais sont reliées par des marches
construites. Leur parcours extérieur a été vérifié dans le jeu le 14 octobre.

## Architecture et présentation

Le palais reçoit une rotonde à couverture facettée vert-or, un axe bleu-vert et
des galeries. L'université reçoit une cour ouverte, deux ailes et des arcades de
marbre ; le musée, la salle de discussion et Omathyr possèdent des assemblages
distincts. Les autres institutions secondaires ne sont pas déclarées fidèles
individuellement. Les modèles maîtres existants sont conservés sans décimation.

Stonebreaker Forge remplace un manoir générique trop large par une halle de
14 × 16 m, deux cheminées, une entrée cintrée ouverte, des postes de travail,
des stocks et un escalier de raccord. Son seuil proposé reste à 27 m. La forme
reprend les propositions de la fiche L08-03 ; dimensions et équipements ne sont
pas des faits du livre. Une vue proche supplémentaire montre cet ensemble.

Les feuilles disposent d'une variation de pigment par instance. Les cartes
physiques et leurs conventions d'import restent celles des parents existants.
Le déplacement Nanite reste désactivé dans la capitale. Les paramètres du témoin
ne constituent toujours pas une preuve de déplacement validé.

Les chaussées, ponts, soutènements, fondations et escaliers construits conservent
100 % des triangles dans le maillage de repli utilisé par leurs collisions.
Le rendu reste Nanite. Une approximation relative à l'étendue d'une longue voie
mince ne suffit pas à garantir le raccord entre collision, dallage et Landscape.
Le réglage est local à ces ouvrages générés et figure dans l'audit moteur.
Le pavage est subdivisé tous les mètres dans les deux directions et posé à
10 cm au-dessus de l'échantillon du terrain ; la dalle garde 12 cm d'épaisseur.
Les anciennes facettes de 3 m sur toute la largeur laissaient affleurer le sol
aux raccords et dans les dévers. Les cibles de marche suivent les nouveaux
triangles de chaussée, indépendamment de la projection Recast.
La voie supérieure d'Oldtown garde sa collision physique, mais ne participe
plus à la rastérisation de Recast : son chevauchement avec la voie principale
créait un obstacle de navigation. Le terrain nivelé porte sa navigation ; les
autres chaussées, ponts, soutènements et escaliers continuent à y participer.
Sur le tronçon d'Oldtown qui provoquait un détour, le chemin calculé est passé
de 532 m à 53 m. Ce tronçon a ensuite été franchi dans le jeu, collisions actives,
sur la version finale avec cette exclusion ciblée.

Old Bridge conserve son tablier et ses arches. Trois variantes de travée ouvrent
les parapets aux deux culées, là où les rues arrivent de biais : une travée
ouverte, puis une demi-travée de raccord, à chaque extrémité. Les parapets restent
continus au centre. Les sondes de collision avaient identifié ces garde-corps
comme les obstacles physiques des arrivées, et non une lacune du sol.

Un prolongement visuel des bordures masque les coupes du Landscape. Sa première
couronne reprend chaque sommet de bord à 2 m, puis s'étend par couronnes jusqu'à
1 600 m. Les sommets communs sont soudés et leurs normales lissées. Il partage
le matériau herbe/roche du paysage. Il n'a aucune collision ni fonction de
terrain concurrent ; la zone jouable est le Landscape. Les couronnes éloignées
sont espacées de 20 m pour éviter les grands pans triangulaires observés lors
d'un premier rendu ; les UV restent continus sur le plan horizontal. Les quatre
recouvrements B–E du bord sont encodés dans RGBA des sommets, puis fondus sur
100 m vers les couches naturelles du décor. Un port du même graphe de matériau
lit ces couleurs sur le décor, à la place des couches réservées au Landscape.
Les textures et paramètres physiques restent identiques.

## Reproduction et preuves

La sauvegarde est `Saved/Jadg/capital-relief-revision/before/` : sources des
générateurs, descriptions de niveau, rapports, captures, GLB, paquets des niveaux,
`CapitalLandscape` et maillages `Content/Kit/Built/capital-urban`. Elle conserve
les changements locaux présents au démarrage. Elle n'est pas un commit Git.

Procédure complète :

```powershell
pwsh scripts/maps/review_capital_landscape.ps1
```

Les options `-SkipPrepare`, `-SkipBuild`, `-SkipMainCaptures`,
`-SkipWitnessCaptures`, `-SkipBuffers` et `-SkipRuntimeWalk` permettent les reprises
ciblées. Une seule instance Unreal à la fois. Blender et Unreal doivent pouvoir
utiliser leurs caches locaux. Les exécutables sont lancés hors fenêtre.

Les caméras historiques sont figées dans `capital_comparison_shots.json` pour
les comparaisons exactes. Les nouvelles vues `proche-*` suivent les altitudes
révisées. Une ancienne caméra proche peut se retrouver masquée par une nouvelle
colline ; elle n'est pas déplacée silencieusement dans la comparaison.

`report_capital_relief_revision.py` fournit cartes de hauteur et pente à échelles
communes, coupes avant/après et statistiques par quartier. Les percentiles P10–P90
mesurent le relief intérieur sans compter les crêtes périphériques. Les quais
et champs conservent les pentes correspondant à leur fonction.

Le parcours physique emploie `JadgWitnessReview`, les collisions et la vitesse
normale de 3 m/s. Il traverse Arenarea, Arching Bridge, Oldtown, Old Bridge,
Market Gate, les approches de Dweomer/Scholarnest, la montée du palais et ses
trois terrasses. La navigation utilise une maille horizontale de 25 cm et une
hauteur de cellule de 10 cm ; chaque cible est contrôlée avec une marge verticale
de 35 cm, identique à celle de la marche. Les hauteurs des chaussées proviennent
de leurs triangles construits, distincts du terrain sous-jacent. Le rapport
conserve chaque échantillon et toute interruption. Le premier échec au départ
est archivé dans `Saved/Jadg/capital-relief-revision/runtime-first-failure.json`.
Un second essai, arrêté dans un détour d'Oldtown après 20 points, est conservé
dans `runtime-oldtown-failure.json`, avec les sondes de collision et les chemins
du diagnostic. Les trajets entre points sont désormais mesurés séparément pour
repérer les grands détours que la seule connectivité ne signale pas.
L'essai suivant a franchi Oldtown, puis révélé la coupure de navigation d'Old
Bridge après 26 points. Il est conservé dans `runtime-old-bridge-failure.json`.
Le lancement d'une marche vérifie désormais ensemble la connectivité depuis le
départ, les destinations et la projection stricte des 105 cibles.
La recherche de chemins seule ne vaut pas validation physique. Le résultat est
rattaché aux empreintes du niveau, du terrain et du parcours.

L'essai final du 14 octobre atteint 105/105 cibles, sans téléportation : 5 007,64 m
mesurés en 27 min 49,55 s de marche, après 80,16 s de démarrage. Les pieds montent
jusqu'à 63,34 m. Oldtown, les deux culées d'Old Bridge, le parvis universitaire,
la montée du palais et les trois terrasses sont franchis. Les 17 destinations
Recast sont atteignables et les 105 projections strictes passent. Ce résultat ne
valide ni tous les seuils individuels, ni les intérieurs ou les rues secondaires.

Les vérifications des sources comptent 51 tests Python réussis ; six d'entre eux
ont nécessité un dossier temporaire explicite après une erreur de création de
dossier dans le bac à sable. Le contrôle de contenu n'a aucune erreur. La forge
conserve un avertissement d'import concernant des tangentes presque nulles,
malgré l'absence de triangles dégénérés dans le contrôle du GLB ; son rendu a été
examiné. Ce point reste à résoudre dans l'export des surfaces concernées.

Les 29 tests moteur `Jadg.*` ont été relancés sur la dernière compilation et
réussissent tous, sans échec ni test omis (14 octobre, 03 h 31, heure de Paris).

Les performances sont remesurées en 1080p dans les quatre vues du premier
passage. La cible reste 60 images/s ; les chiffres d'une autre réalisation ne
sont pas réutilisés. Les résultats, limites et vues sont dans
`Saved/Jadg/capital-landscape/review.html`.

Les huit mesures finales du 14 octobre couvrent 41,0 à 71,2 images/s ; trois
atteignent 60 en moyenne. Par vue, midi / 22 h : ensemble 58,9 / 60,5 ; Water
Gate 66,0 / 71,2 ; Market Gate–Old Bridge 41,0 / 48,1 ; Scholarnest–Dweomer
48,4 / 53,6. Le p99 varie de 31,10 à 44,00 ms. La cible n'est donc pas tenue.
La plage du premier passage était 44,7–74,5 : cette reprise ne constitue pas
un gain de performance. Le relief plus détaillé, les ouvrages et le décor
périphérique demandent encore un travail de rendu ciblé, sans décimation des
modèles maîtres. Les mesures durent environ onze secondes, caméra en rotation ;
elles ne constituent pas un profil de performance de toute la marche.

Les 46 captures finales comprennent les 16 cadrages historiques inchangés aux
deux heures et sept vues proches nouvelles aux deux heures. La caméra historique
`joueur-universite` se trouve maintenant masquée par le relief : ce défaut de
comparaison est conservé et signalé, avec une vue `proche-universite` dégagée.
Les raccords de bordure, les finitions de façade, la densité des espaces publics
et l'horizon lointain restent des chantiers artistiques. Les grands jardins et
leurs escaliers sont construits et parcourus, sans prétendre achever leur décor.
