+++
id = "LOT-1018"
titre = "Le format de carte et sa chaîne : des cartes composées"
version = "0.0.3"
filiere = "editeur"
statut = "a-faire"
taille = "L"
resume = "Une carte se décrit en texte — terrain, objets à transformation libre, zones, entités, portails — et se construit en niveau par script ; l'éditeur du moteur la retouche, et ce qu'il retouche revient dans le texte."
prerequis = ["LOT-1016"]
livrables = [
  "Le format `jadg-map`, version 5, en JSON : terrain (hauteurs, matières peintes, eau), objets (maillage, position en mètres, rotation, échelle, étage), routes et contours, zones nommées et volumes de combat, entités (arrivées, portails, PNJ, lumières, rencontres), notes ; spécifié dans `Documentation/Specification/niveaux.md`, schéma `level.schema.json`.",
  "`build_level.py` (script Python d'éditeur) : construit le niveau Unreal depuis la description, régénérable, et `read_level.py` qui relit un niveau retouché dans l'éditeur et réécrit la description — l'aller-retour, comme D-44 l'a fait pour Blender.",
  "Le contrôle de contenu (`ContentCheck`, `--check`) comme commandlet : portails appariés, arrivées citées, zones nommées, cases inatteignables devenues zones inatteignables sur le maillage de navigation.",
  "Les préfabriqués (LOT-130) comme acteurs composés, déclarés en texte ; le mode Quêtes (LOT-144) et les drapeaux comme outil d'éditeur en Python, sur les mêmes JSON qu'aujourd'hui.",
  "La migration des quatre cartes livrées (Arenarea v0, Martpart v0, les trois niveaux de l'Arena of Fate) du format v4 vers la version 5 : un script, les cartes relues par `--check`.",
  "L'arborescence par niveaux (LOT-124) et le kit par lieu inchangés : la description de carte vit dans `Levels/`, ses maillages dans le kit du lieu.",
]
criteres = [
  "`build_level.py` relancé sur un projet vierge redonne le même niveau (empreinte) ; `read_level.py` après une retouche dans l'éditeur réécrit une description que `build_level.py` reconstruit à l'identique.",
  "Les quatre cartes migrées s'ouvrent, se parcourent et passent `--check` ; les portails de la démo s'enchaînent.",
  "Une carte à deux étages praticables se joue sans changer de carte (D-51) : escalier, étage, redescente.",
  "Aucun `.umap` n'est modifié à la main : `check_orphans.py` cite chaque niveau par le script qui le produit.",
]
+++

## Pourquoi

Le format v4 est la première des cinq causes de l'écart : une grille de cases, sans rotation ni
terrain, ne peut pas porter la ville de l'atlas. Ce lot remplace le format, et garde ce qui faisait
la valeur de l'éditeur : le contrôle du contenu, les préfabriqués, le mode Quêtes, l'arborescence.
Il pose la règle D-52 sur l'objet qui la met le plus à l'épreuve : une carte.

## Périmètre

Dedans : le format, la construction, la relecture, le contrôle, les préfabriqués, le mode Quêtes,
la migration des cartes livrées.

Dehors, nommément :

- la production de décor (LOT-1019) : ce lot pose les pièces existantes ;
- Arenarea reconstruit (LOT-1021) : ce lot migre la v0 telle quelle ;
- les outils de l'éditeur de la `0.2.0` (peupler une zone, semis, horaires, onglet Carte) : leurs
  fiches se relisent pour le nouvel éditeur, à la recette.

## À supprimer

Rien dans ce lot : le format v4, le LevelEditor et ses tests vivent dans l'ancien dépôt, qui se
joue jusqu'à la recette (D-58). Dans le nouveau dépôt, ils ne sont jamais entrés.

## Conception

- **Le texte est la source, le niveau est une sortie.** La description est ce que Git relit, ce que
  les lints contrôlent, ce que l'assistant écrit. L'éditeur du moteur sert à placer à la main ce
  qu'un script ne place pas bien ; `read_level.py` ramène le geste dans le texte, et rien d'autre
  n'en revient.
- **Le terrain** est un `Landscape` : hauteurs et couches de matière en images régénérées depuis
  la description (une carte de hauteurs, une image par couche), pas peintes dans l'éditeur. Les
  berges, les dénivelés et les rues du plan en viennent.
- **Un lieu à plusieurs étages est une carte** (D-51) : les trois niveaux de l'Arena of Fate se
  superposent dans une seule description, avec des niveaux de chargement par étage.
- **Les entités** gardent leurs identifiants et leurs noms : `from-martpart`, `parvis`, les
  arrivées de la quête ne changent pas, pour que les tests de la quête ne changent pas non plus.

## Risques et questions ouvertes

- **L'aller-retour.** Tout ce que l'éditeur sait faire ne se relit pas en texte (un acteur exotique,
  un réglage de rendu). La règle est : ce qui ne se relit pas ne se fait pas dans l'éditeur ; la
  liste de ce que `read_level.py` relit est la frontière, écrite dans la spécification.
- **La taille.** Arenarea v0 compte 1 663 placements ; une carte reconstruite en comptera dix fois
  plus. La construction par script doit tenir en minutes, pas en heures ; mesurée sur la migration.
