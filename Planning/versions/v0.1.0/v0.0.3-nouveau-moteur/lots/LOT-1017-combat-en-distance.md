+++
id = "LOT-1017"
titre = "Le combat en distance"
version = "0.0.3"
filiere = "regles"
statut = "a-faire"
taille = "XL"
resume = "Le combat se joue en mètres, à la manière de Baldur's Gate 3 : déplacement libre sur le maillage de navigation, ligne de vue par rayon, zones en volumes, hauteur comptée ; les règles, les classes et l'IA de la 0.0.2 ne changent pas."
prerequis = ["LOT-1015", "LOT-1016"]
livrables = [
  "`Core/Combat` sans grille : `BattleGrid`, `Pathfinding`, `LineOfSight`, `AreaOfEffect`, `Flanking`, `TacticalTerrain` et `IsoProjection` remplacés par un modèle en mètres — positions, rayons d'allonge, budgets de déplacement, volumes de zone — derrière une interface d'espace que le moteur implémente (navigation, rayons) et que les tests simulent.",
  "Les règles spatiales du *Manuel* en mètres : allonge 1,5 m, déplacement 9 m, cône 4,5 m, sphère 6 m, attaques d'opportunité au départ de l'allonge, prise en tenaille par angles, abri par part cachée du volume, avantage de hauteur.",
  "L'IA des profils du Guide du Maître (LOT-23) avec les mêmes poids, le choix de position par EQS ; les cinq profils JSON inchangés.",
  "L'aperçu de combat (LOT-140) en distance : le chemin tracé, la portée restante, les cibles atteignables, le compte des capacités ; la sélection au clic et au clavier.",
  "Les zones de combat et le déploiement du groupe (LOT-143) en volumes posés sur la carte ; `analyzePartyDeployment` et `inspect` sur ces volumes.",
  "La série de l'arène et la simulation à cent graines de la recette `0.0.2` rejouées en distance ; les écarts entre trios écrits dans la fiche, comme D-36 les a mesurés.",
  "Les tests de Core réécrits sur l'espace simulé ; les tests d'intégration du combat sur le moteur.",
]
criteres = [
  "Un combat à quatre contre quatre se joue de bout en bout dans l'Arena of Fate, au clavier et à la souris, avec déplacement libre, attaques d'opportunité, zones et abri.",
  "Chaque capacité des quatre classes a le même effet qu'en `0.0.2`, à la distance près : la simulation à cent graines donne un écart entre trios inférieur à 20 points, comme à la recette `0.0.2`.",
  "Un sort de zone touche exactement les créatures dont le volume croise le sien ; un rayon bloqué par un mur ne touche pas.",
  "Un personnage en hauteur a l'avantage que le *Manuel* lui donne ; la hauteur se lit dans l'aperçu.",
  "Les tests de Core passent sans GPU ; les profils d'IA n'ont pas changé d'une valeur.",
]
sources = [
  "Manuel des Joueurs, ch. 9 (combat) ; Guide du Maître, p. 247-255 (IA)",
]
+++

## Pourquoi

Le *Manuel* compte en mètres. La grille n'était qu'une façon de les dessiner, et elle a imposé des
demi-cases, un départage de chemins et un abri non additionné (LOT-19, LOT-22). Un combat en
distance rapproche le jeu de la règle écrite et de ce que l'auteur attend : « non pas en case mais
en distance ». C'est le lot de moteur le plus lourd de la version ; il se découpe à l'ouverture.

## Périmètre

Dedans : la part spatiale de `Core/Combat`, les règles spatiales du *Manuel*, l'IA, l'aperçu, les
zones de combat, la série de l'arène, les tests.

Dehors, nommément :

- les jets, les dégâts, l'économie d'actions, les états, l'agonie et la mort (LOT-20, LOT-21,
  LOT-137) : inchangés ;
- les classes, les capacités, les sorts (LOT-131 à LOT-136) : inchangés, leurs portées passent en
  mètres par une table ;
- les mécanismes propres à Larian (surfaces, poussée, lancer d'objets, dés visibles) : à la `0.2.0`
  par une décision écrite, règle 3 de la trajectoire ;
- l'interface de combat finale (LOT-1020) : ce lot livre l'aperçu et une interface de travail.

## Conception

Trois lots à l'ouverture, dans cet ordre :

1. **Les règles spatiales** (L). Un `CombatSpace` abstrait : positions en mètres, un volume par
   créature (cylindre de taille du *Manuel*), `reach`, `pathLength`, `lineOfSight`, `cover`,
   `shapeHits`. Deux implémentations : la simulation de Core pour les tests (un plan avec des
   obstacles) et le moteur (navigation, rayons). `TurnOrder`, `ActionEconomy`, `Attack`, `Damage`
   ne voient que l'interface.
2. **L'IA** (M). Les profils gardent leurs poids ; l'espérance en entiers (LOT-23) s'évalue sur des
   positions candidates fournies par EQS (couverts, hauteurs, distances) au lieu des cases voisines.
3. **L'interface de travail et les zones** (M). L'aperçu, la sélection, les volumes de combat, le
   déploiement ; la série de l'arène et la simulation.

Décisions déjà prises : une case de 1,5 m reste l'**unité** du *Manuel* pour les portées écrites
dans les données (une portée « 6 cases » vaut 9 m), sans grille à l'écran. Les attaques
d'opportunité et la tenaille suivent le *Manuel*, pas Larian. La hauteur donne l'avantage du
*Manuel*, rien de plus.

## Risques et questions ouvertes

- **Le déterminisme.** Un combat se rejoue à l'identique (graine explicite) : la navigation du
  moteur doit être déterministe pour une même carte, ou la simulation de Core doit suffire aux
  tests. À trancher au premier sous-lot.
- **Les rencontres sur la carte** (LOT-139) : une rencontre paraît à son marqueur ; sans grille, le
  marqueur devient un volume. Le LOT-1018 doit le porter dans la description de carte.
- **L'équilibre.** Le déplacement libre favorise les tireurs et les lanceurs ; la simulation le
  dira, et le Brawler gradué (D-36) se recale si l'écart dépasse 20 points.
