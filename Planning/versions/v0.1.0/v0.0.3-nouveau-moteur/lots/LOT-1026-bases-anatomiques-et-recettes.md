+++
id = "LOT-1026"
titre = "Le générateur : bases anatomiques et recettes versionnées"
version = "0.0.3"
filiere = "pnj"
statut = "a-faire"
taille = "L"
resume = "Les familles de corps, leurs formes d'identité et leurs rigs se reconstruisent depuis des recettes indépendantes de l'interface et du fournisseur."
prerequis = ["LOT-1024"]
livrables = [
  "Le contrat d'apparence versionné, son schéma JSON, son lecteur Core et l'adaptateur de la chaîne retenue ; migration des anciennes fiches.",
  "La matrice des 22 entrées d'espèces actuelles : famille, base, rig, paramètres, plages admises, source et restrictions ; décision explicite sur les espèces du corpus absentes du catalogue.",
  "Les bases et morphs réutilisables, un exemple par entrée couverte, les rigs et profils de retargeting, collisions et emplacements d'équipement.",
  "Les scripts d'import/construction, manifestes de sources, contrôles de reconstruction et mise à jour du standard.",
]
criteres = [
  "Chaque entrée du catalogue couvert reconstruit son exemple et ses paramètres d'identité ; une valeur hors plage, une combinaison interdite ou une version inconnue produit une erreur explicite.",
  "Les Taii'maku conservent six doigts et les Gloomfolk leur anatomie de scorpion avec locomotion ; les corps petits, trapus, enfant et drakéide passent leurs contrôles propres.",
  "Modifier l'identité préserve les expressions, les yeux et dents, les articulations, les prises et les contacts au sol dans le paquet final.",
  "La migration préserve les identifiants et références de gameplay ; les sources permettent de reconstruire les assets dans un répertoire de sortie vierge.",
]
+++

## Pourquoi

Les vêtements et les sauvegardes dépendent des bases. Ce lot stabilise ce contrat après la
preuve du LOT-1024, sans imposer MetaHuman, Mutable ni le mannequin à une anatomie incompatible.

## Périmètre

Dedans : bases, morphs d'identité, rigs, adaptation du squelette aux proportions, physique,
recette et migration. Dehors : garde-robe complète (LOT-1027), interface finale (LOT-1028),
PNJ de la démo (LOT-1029) et fauves (LOT-1025).

## Conception

La recette contient des identifiants sémantiques : famille, espèce, base, paramètres d'identité,
pièces équipées et matériaux ; l'adaptateur traduit ces valeurs pour le backend retenu.
Les règles restent dans Core sans dépendance Unreal. La fiche d'apparence ne se substitue pas
à la fiche de règles, et un PNJ d'ambiance peut n'avoir qu'une apparence.

Ne pas confondre les 22 entrées actuelles et 22 anatomies distinctes : certaines sont des
variantes partageant une base. Inventorier humain, elfes et variantes, demi-elfe, demi-orc,
nains et variantes, halfelins et variantes, gnome, tieffelin, drakéide, cirrus, gloomfolk et
taii'maku. Documenter le cas Soulborn et tout autre écart au corpus, sans ajout silencieux.
Une matrice ne vaut livraison que lorsque ses lignes ont un exemple fonctionnel.

Partager les conventions d'action et d'équipement, pas obligatoirement les squelettes.
Les mains à six doigts, cornes, queues, museaux et bas de corps de scorpion ont leurs
compatibilités explicites. Les ailes des anciens cirrus ne deviennent pas un attribut de tous.
Un changement de proportions doit mettre à jour les articulations et volumes nécessaires ;
un morph de surface seul n'est pas toujours suffisant.

Le contrat décrit aussi les plages combinables, LOD et raccords de tête/corps. Les sources
de fabrication sont conservées ; aucun pipeline de migration ne promet de convertir
automatiquement les UV, morphs ou vêtements d'une topologie à une autre.
Captures de contrôle à midi et à 22 h au cadrage du joueur, avec planche des espèces.

## Risques et questions ouvertes

Une famille dont le coût dépasse le lot est redécoupée avant réalisation, sans fausse clôture
de sa couverture. La préparation des bases doit rester rejouable à partir de sources conservées.
Le LOT-1024 fixe les voies admises ; ce lot en livre le catalogue et contrôle leurs limites.
