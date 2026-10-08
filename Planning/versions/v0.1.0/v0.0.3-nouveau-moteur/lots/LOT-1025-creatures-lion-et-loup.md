+++
id = "LOT-1025"
titre = "Les créatures : lion et loup"
version = "0.0.3"
filiere = "pnj"
statut = "a-faire"
taille = "M"
resume = "Le lion et le loup de la rencontre des fauves marchent et attaquent dans le moteur, sur un squelette quadrupède du moteur, décrits par la même fiche de personnage que les humanoïdes."
prerequis = ["LOT-1015"]
livrables = [
  "Le lion et le loup, produits par Meshy avec son rig automatique ou pris sur Fab, sur un squelette quadrupède du moteur.",
  "Leurs animations, prises dans les bibliothèques du moteur et reciblées par l'IK Retargeter, l'instant de l'impact (`key`) porté par une donnée texte comme au LOT-1015.",
  "Leurs fiches, au format de la fiche de personnage du LOT-1015.",
  "Les captures de contrôle (repos, marche, attaque), à midi et à 22 h.",
]
criteres = [
  "Les deux fauves marchent et attaquent sur la carte d'essai, instanciés depuis leur fiche.",
  "La cadence est mesurée avec les deux fauves à l'écran et écrite dans la fiche.",
]
+++

## Pourquoi

La rencontre des fauves (`Source/Elements/Rpg/encounters/colisee-fauves.json` : un lion, deux
loups) en a besoin pour le combat. Le squelette `quadruped` maison à 29 os et `rig_quadruped.py`
sont partis au [LOT-1015](LOT-1015-personnages-et-createur.md) (D-64) : les fauves passent sur un
squelette du moteur, comme les humanoïdes.

## Périmètre

Dedans : le lion, le loup, leur squelette, leurs animations, leurs fiches, les captures.

Dehors, nommément :

- les autres créatures de `Source/Elements/Rpg/creatures/` : avec le lieu qui les emploie ;
- la silhouette volante ;
- les portraits et les jetons : ils restent peints (D-30).

## Risques et questions ouvertes

- **La source du squelette.** Le rig automatique de Meshy ou un pack Fab : le choix se fait sur ce
  que l'IK Retargeter accepte, et se mesure ; la licence d'un pack Fab se vérifie avant achat, par
  l'auteur.
- **Le créateur pour un quadrupède.** Que l'objet personnalisable Mutable vaille aussi pour les
  fauves, ou qu'une fiche y désigne seulement un maillage, se décide ici.
