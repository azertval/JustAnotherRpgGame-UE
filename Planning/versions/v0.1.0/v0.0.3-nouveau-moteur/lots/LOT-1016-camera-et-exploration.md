+++
id = "LOT-1016"
titre = "Caméra, marche, groupe, portails, jour et nuit"
version = "0.0.3"
filiere = "moteur"
statut = "a-faire"
resume = "On explore une carte sur le nouveau moteur : la caméra libre de D-49, le groupe de quatre qui suit le meneur au clic, les interactions, les portails entre cartes et le cycle jour / nuit."
taille = "L"
prerequis = ["LOT-1014"]
livrables = [
  "La caméra de D-49 : rotation, zoom et inclinaison bornés, recentrage sur le meneur, réglages en fichier texte ; au clavier et à la souris, comme le jeu depuis le 2 octobre 2026.",
  "La marche au clic sur le maillage de navigation ; le groupe de quatre qui suit le meneur en file (reprend `FollowTrail`, LOT-138) ; le changement de meneur (Tab).",
  "L'interaction à 1,5 m (LOT-118, PR #138) : parler, ramasser, actionner ; le portrait du PNJ en dialogue.",
  "Les portails et points d'arrivée entre cartes, lus depuis les données de Core ; les drapeaux de quête qui les scellent (LOT-116).",
  "L'horloge du monde (une heure par minute réelle, D-45) et `daylight.json` pilotant le soleil, le ciel et la lune du moteur ; les lumières de nuit déclarées par les pièces ou posées comme entité `light`.",
  "Les captures à midi et à 22 h sur la carte d'essai du socle, versées à la fiche.",
]
criteres = [
  "La quête « Des pommes pour l'arène » se parcourt hors combat sur une carte d'essai : dialogue, jet de Persuasion, portails ; les tests d'intégration de la quête passent sur le nouveau moteur.",
  "Les quatre membres du groupe suivent le meneur sans se chevaucher ni rester bloqués ; un changement de meneur se fait en une touche.",
  "À 22 h, une lanterne éclaire le mur devant elle et pas celui derrière : les lumières de nuit portent une ombre.",
  "La caméra ne traverse ni le sol ni les murs ; ses bornes se règlent sans recompiler.",
]
+++

## Pourquoi

Le jeu doit se jouer à chaque instant : avant le combat, avant l'interface, il faut pouvoir marcher
dans une carte, parler et passer une porte. C'est le lot qui rend le nouveau moteur **jouable** au
sens de la trajectoire, et celui qui fait tomber la vue isométrique.

## Périmètre

Dedans : la caméra, la marche, le groupe, les interactions, les portails, le jour et la nuit.

Dehors, nommément :

- le combat (LOT-1017) ; la bascule vers le combat est posée mais mène à une arène vide ;
- l'interface : ce lot utilise un HUD minimal (noms, points de vie), le vrai vient au LOT-1020 ;
- les cartes : il joue sur la carte d'essai du socle et sur le parvis de la porte.

## Conception

- **La caméra** est un composant à ressort, cible le meneur, bornes en inclinaison (entre 25° et
  70°), en distance et en hauteur sous le terrain ; la rotation est libre (D-56).
- **Le déplacement** passe par le maillage de navigation du moteur (Recast) ; le groupe reprend la
  file de `FollowTrail` avec des points d'arrêt à distance fixe. Les blocages aux portes se traitent
  par des zones de navigation étroites, pas par du code.
- **Les interactions** gardent leur portée en mètres (1,5 m) ; l'indice visuel est un contour, pas
  un jeton.
- **L'heure** reste une donnée de Core (`DayLight`) ; le moteur ne fait que la lire. Les lumières
  de nuit portent une ombre (ce que le moteur maison ne faisait pas) ; leur nombre à l'écran n'est
  plus borné à trente-deux, et se mesure.

## Risques et questions ouvertes

- **Le groupe dans les escaliers et les étages** (D-51) : le maillage de navigation les couvre, la
  file doit suivre en hauteur ; à éprouver sur la carte d'essai à deux niveaux.
- **La bascule vers le combat** change de nature sans grille : les zones de combat de l'éditeur
  (LOT-143) deviennent des volumes ; le LOT-1017 en hérite.
