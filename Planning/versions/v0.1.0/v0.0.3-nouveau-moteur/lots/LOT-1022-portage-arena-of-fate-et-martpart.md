+++
id = "LOT-1022"
titre = "L'Arena of Fate et Martpart portés"
version = "0.0.3"
filiere = "cartes"
statut = "a-faire"
taille = "M"
resume = "Les trois niveaux de l'Arena of Fate, dans une seule carte, et Martpart à l'état de sa v0 se jouent sur le nouveau moteur : la démo s'enchaîne de bout en bout."
prerequis = ["LOT-1019"]
livrables = [
  "L'Arena of Fate en une description de carte (format 5) à trois étages praticables — le sable, les vestiaires et la prison, les catacombes — de même emprise ovale, les escaliers aux mêmes positions (D-46, D-51) ; ses 105 maillages au maître, textures partagées ; la série de l'arène rejouée.",
  "Martpart en description de carte, ses 34 maillages et les deux arbres, au niveau de sa v0 ; les portails vers Arenarea appariés.",
  "Les captures à midi et à 22 h des trois étages et de Martpart, versées à la fiche et aux fiches LOT-106, LOT-107, LOT-157 de la `0.0.4`.",
  "Les mesures de cadence et d'ouverture des deux cartes.",
]
criteres = [
  "La démo s'enchaîne par ses portails : Martpart, Arenarea, l'Arena of Fate et son donjon, et retour ; `--check` passe sur les trois cartes.",
  "La série de l'arène se joue sur le sable ; le combat de groupe de la recette `0.0.2` s'y rejoue.",
  "Les deux cartes tiennent 60 images par seconde à 1080p sur le poste de référence, de jour comme de nuit.",
  "L'auteur confirme sur captures que l'Arena of Fate n'a rien perdu de ce qu'il avait validé le 4 octobre 2026 (jugement de l'auteur).",
]
+++

## Pourquoi

La démo compte trois lieux ; la version doit se jouer sur les trois (règle 2 de la trajectoire).
L'Arena of Fate est le lieu le plus abouti du dépôt, en maillages au maître : son portage est le
test de D-51 (trois étages dans une carte) et de D-53 (2,04 millions de triangles sans réduction).
Martpart n'est qu'une v0 : il se porte tel quel, sa production reste aux lots de la `0.0.4`.

## Périmètre

Dedans : les deux cartes, leurs maillages, les portails, les captures, les mesures.

Dehors, nommément :

- la qualité finale de Martpart (LOT-110, LOT-111) et la validation artistique de l'Arena of Fate
  (LOT-106), qui restent à la `0.0.4` ;
- le donjon cultiste des catacombes (LOT-157).

## À supprimer

| Quoi | Où | Pourquoi maintenant |
|---|---|---|
| Les trois descriptions v4 de l'Arena of Fate et celle de Martpart | `Levels/central-empire/capital/arenarea/arena-of-fate/`, `Levels/.../martpart.json` | remplacées par les descriptions v5 sous les mêmes identifiants |

Les kits `arena-of-fate@6` et `martpart@4` se republient avec les mêmes maillages ; seules les
sorties du moteur changent.

## Conception

- **Une seule carte pour trois étages** : chaque étage est un niveau de chargement de la même
  description ; les escaliers relient par le maillage de navigation, sans portail.
- **Les textures partagées** (D-46) le restent : le moteur déduplique à l'import.
- **La série de l'arène** se rejoue avec les distances du LOT-1017 ; les zones de déploiement
  deviennent des volumes posés sur le sable.

## Risques et questions ouvertes

- **La coque à 878 000 triangles** sous Nanite avec trois étages chargés : la cadence se mesure
  étage par étage ; si un étage ne tient pas, il se décharge quand on n'y est pas.
