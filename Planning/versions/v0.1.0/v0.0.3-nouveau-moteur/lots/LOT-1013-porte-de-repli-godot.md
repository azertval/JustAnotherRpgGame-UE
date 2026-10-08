+++
id = "LOT-1013"
titre = "La porte de repli : le même parvis dans Godot"
version = "0.0.3"
filiere = "moteur"
statut = "abandonne"
taille = "M"
resume = "La porte du LOT-1012 rejouée sur Godot 4, pour le cas où Unreal convainc sur l'image mais casse la méthode de travail en texte."
prerequis = ["LOT-1012"]
livrables = [
  "Un projet Godot 4 à part (`Tools/Godot/Porte1013/`), version épinglée, avec les mêmes pièces, les deux mêmes personnages, la même caméra et la même marche que le LOT-1012.",
  "La scène construite par script depuis la même description JSON ; les scènes `.tscn` et ressources `.tres` en texte, relues dans Git.",
  "Les captures à midi et à 22 h aux trois cadrages du LOT-1012, la cadence et le temps d'ouverture, versés à la fiche.",
  "Le **verdict** de l'auteur, en fin de fiche, et la révision de D-48 qu'il entraîne.",
]
criteres = [
  "Les captures se comparent cadrage pour cadrage à celles du LOT-1012 et du moteur maison ; l'auteur dit laquelle il garde.",
  "60 images par seconde à 1080p sur le poste de référence, GI par SDF active.",
  "Le projet entier est lisible en texte : aucun fichier binaire hors maillages, textures et sons.",
]
+++

## Abandonné le 7 octobre 2026

Avant d'être ouvert, par [D-57](../../../../vision/decisions.md) : l'auteur ne veut pas d'un repli
qui demande d'apprendre un nouveau langage. Si la porte du LOT-1012 échoue, la version s'abandonne
et la `0.0.4` reprend sur le moteur maison. La fiche reste pour l'histoire ; son numéro n'est pas
repris.

## Pourquoi

Ce lot n'existait que pour un verdict précis du LOT-1012 : l'image convainc, la méthode non. Godot
range tout en texte et se pilote en C++ par GDExtension ; son plafond de rendu est plus bas (ni
Nanite ni Lumen), mais il ne demande aucune exception à la règle D-52. Deux portes jouées en
parallèle doubleraient le coût sans changer la décision (Q-19) : celle-ci ne s'ouvre qu'en repli.

## Périmètre

Dedans : le même parvis, les mêmes personnages, les mêmes mesures, avec les outils de Godot.

Dehors : tout ce qui n'était pas dans le LOT-1012. Si ce lot s'ouvre, les fiches LOT-1014 à
LOT-1023 se relisent avant d'être ouvertes : leurs livrables nomment des outils d'Unreal.

## Conception

- La description de scène du LOT-1012 se rejoue telle quelle : c'est elle qui est jugée portable.
- Les maillages au maître passent par l'importateur de Godot avec ses niveaux de détail
  automatiques ; les maîtres Meshy à 2,6 millions de triangles se réduisent à l'import, pas par
  `reduce_model.py`.

## Risques et questions ouvertes

- Si Godot convainc sur la méthode mais pas sur l'image, l'auteur arbitre entre les deux ; la
  décision D-48 est révisée dans un cas comme dans l'autre, datée.
