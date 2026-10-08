+++
id = "LOT-1020"
titre = "Les écrans et le HUD en UMG"
version = "0.0.3"
filiere = "interface"
statut = "a-faire"
taille = "L"
resume = "Tous les écrans du jeu à la charte v2 — HUD, Personnage, Équipement, Journal, Groupe, Carte, Options, menus, dialogues, combat, écrans de fin — existent sur le nouveau moteur, construits en C++, avec les mêmes images et les mêmes textes."
prerequis = ["LOT-1016"]
livrables = [
  "Les écrans en UMG construits par C++ (pas de Widget Blueprint) : HUD d'exploration, menu du mercenaire, Personnage, Équipement, Journal, Groupe à quatre, Carte (l'atlas illustré et ses zones cliquables, LOT du 7 octobre), Options, Nouvelle partie et choix du meneur (D-37), dialogues avec choix du locuteur (D-28) et jet en dialogue, interface de combat de groupe (LOT-140) en distance, écrans de fin (LOT-119), menu de débug F9.",
  "La charte v2 reprise telle quelle : parchemins, ornements, polices, portraits, jetons du kit `UI` ; les tailles aux quatre niveaux de l'échelle d'identité (23/14/10/8).",
  "La localisation : les textes du jeu extraits et chargés par le système de texte du moteur, depuis les mêmes fichiers de traduction ; `check_translations.py` rebranché.",
  "Les captures de référence des écrans (vingt aujourd'hui) refaites sur le nouveau moteur et comparées à tolérance en CI.",
  "Le manuel du joueur (`Documentation/Guide/Manuel/`) et ses captures régénérés.",
]
criteres = [
  "Chaque écran du cahier de test s'ouvre, se ferme et se parcourt au clavier et à la souris ; les tests d'interface passent.",
  "Un écran se compare à sa capture du moteur maison : même disposition, mêmes textes, mêmes images (jugement de l'auteur sur les vingt captures côte à côte).",
  "Aucun Widget Blueprint dans le projet ; `check_orphans.py` passe.",
  "Les textes en français et en anglais s'affichent depuis les fichiers de traduction existants.",
]
+++

## Pourquoi

L'interface Qt Quick tombe avec Qt. Les écrans eux-mêmes sont faits, validés et testés : ce lot
les refait sur le nouveau moteur sans en changer le dessin, pour que la recette compare écran à
écran.

## Périmètre

Dedans : tous les écrans, la charte, la localisation, les captures, le manuel.

Dehors, nommément :

- la refonte d'un écran : aucun écran ne change de dessin ici ; une demande passe par un lot ;
- l'aperçu de combat (LOT-1017), que ce lot habille sans le réécrire ;
- la manette, retirée le 2 octobre 2026.

## Conception

- **UMG par C++** : chaque écran est une classe qui construit son arbre de widgets ; les styles
  (images, polices, couleurs) viennent d'un fichier texte, pas d'un `.uasset` de style. Les images
  du kit `UI` s'importent par script, comme les maillages.
- **L'écran Carte** reprend l'atlas illustré et `map-interactions.json` : zones cliquables, voisins,
  bannières, recherche, favoris ; c'est le dernier écran livré sur l'ancien moteur, et le plus
  riche.
- **Les captures de référence** se comparent à tolérance par blocs ; le seuil de 24 par canal du
  moteur maison se remesure sous l'anticrénelage temporel.

## Risques et questions ouvertes

- **Le texte riche** (journal, dialogues) : le système de texte du moteur ne couvre pas tout ce que
  QML faisait ; les balises utilisées s'inventorient en ouvrant le lot.
- **Le volume** : quinze écrans, 149 fichiers QML derrière. Si le lot dépasse la semaine, il se
  redécoupe en exploration, fiche et groupe, combat et fins.
