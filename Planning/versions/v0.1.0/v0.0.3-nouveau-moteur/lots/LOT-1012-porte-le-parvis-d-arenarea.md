+++
id = "LOT-1012"
titre = "La porte : le parvis d'Arenarea dans Unreal"
version = "0.0.3"
filiere = "moteur"
statut = "a-faire"
taille = "L"
resume = "Le parvis d'Arenarea, le Colisée et deux personnages rendus par Unreal Engine 5, sous la caméra libre, à midi et à 22 h : la preuve que le nouveau moteur donne le rendu voulu et se pilote en texte."
prerequis = []
livrables = [
  "Un projet Unreal Engine 5 à part, hors du dépôt du jeu (`Tools/Unreal/Porte1012/`), avec sa version du moteur épinglée et son journal d'installation.",
  "La coque du Colisée (`af-arena-shell.glb`, 878 000 triangles), ses quatorze statues et ses bannières, cinq façades et le dallage du parvis importés **au maître**, en Nanite, avec leurs cartes de couleur, de relief et d'occlusion-rugosité-métal.",
  "Deux personnages liés (`brawler`, `lion`) importés avec leurs squelettes et leurs clips, qui marchent et se tiennent au repos.",
  "La caméra de D-49 : rotation, zoom, inclinaison bornée ; la marche au clic sur un maillage de navigation ; un cycle jour / nuit piloté par `daylight.json`, soleil et lumières de nuit, Lumen actif.",
  "La scène **construite par un script Python d'éditeur** depuis une description en JSON : aucun acteur posé à la main, aucun Blueprint.",
  "Une construction, un test et une capture **sans fenêtre**, en ligne de commande, depuis un script du dépôt.",
  "Les captures du moteur à midi et à 22 h, aux cadrages du joueur (parvis, porte du Colisée, ruelle), et la mesure de cadence et de temps d'ouverture, versées à la fiche.",
  "Le **verdict** de l'auteur, écrit en fin de fiche : la version s'ouvre, ou s'abandonne (pas de repli, D-57).",
]
criteres = [
  "L'auteur juge les captures à midi et à 22 h plus proches de la carte peinte d'Arenarea que le rendu du moteur maison du 7 octobre 2026 (jugement de l'auteur, sur les mêmes cadrages).",
  "La scène tient 60 images par seconde à 1080p sur le poste de référence (RTX 4060 Ti), Lumen et Nanite actifs, caméra en mouvement.",
  "La carte s'ouvre en moins de 5 secondes depuis le lancement.",
  "Le script de construction, relancé sur un projet vierge, redonne la même scène ; aucun fichier `.umap` ni `.uasset` n'a été modifié à la main (comparaison des empreintes avant et après).",
  "`build`, `test` et `capture` s'enchaînent en ligne de commande, sans ouvrir l'éditeur, et sortent en 1 à la première erreur.",
  "Les deux personnages marchent sans glissement ni pénétration du sol, aux seuils du standard des personnages (1,3 mm, 0,53 px à 1080p).",
]
sources = [
  "Plan d'action du 7 octobre 2026 — https://claude.ai/artifact/AHU61AmvLTCPBmDmUBd2Em",
]
+++

## Pourquoi

Toute la version repose sur deux hypothèses que rien n'a prouvé dans ce projet : qu'Unreal rend le
décor existant au niveau que l'auteur attend, et qu'il se pilote **en texte** comme le reste du
dépôt. La `0.0.2.5` s'est ouverte sur une porte de ce genre (LOT-1000) et l'a justifiée : une
journée pour éviter de bâtir un atelier sur une hypothèse fausse. Ici la porte coûte une à deux
semaines et épargne deux mois.

## Périmètre

Dedans : un projet neuf, les pièces les plus abouties du dépôt (le Colisée et ses sculptures, cinq
façades, le dallage), deux personnages, la caméra, la marche, la lumière, la construction par
script, la mesure. Les quatre questions Q-17 à Q-20 ont été tranchées le 7 octobre 2026 (D-55 à
D-58) : bibliothèques du moteur admises pour la nature, caméra libre, pas de repli, nouveau dépôt.
La porte se joue dans un projet à part ; le nouveau dépôt se crée au LOT-1014, sur son verdict.

Dehors, nommément :

- le dépôt du jeu : pas une ligne de `Source/` ne change ; l'ancien moteur se joue comme avant ;
- les règles, le combat, l'interface, les quêtes : rien de Core n'entre dans la porte ;
- la chaîne de décor et le standard 3D (LOT-1019) : les pièces s'importent telles qu'elles sont ;
- Arenarea entier : trois cadrages suffisent à juger.

## Conception

- **Les pièces viennent du kit, pas d'un nouvel atelier.** Le Colisée, ses statues et ses bannières
  sont déjà au maître et avec leurs trois cartes (D-46) ; les cinq façades sont des retours Meshy
  d'Arenarea. Si ces pièces ne convainquent pas dans Unreal, le moteur n'est pas en cause.
- **La description de scène** est un JSON : une liste d'objets avec leur maillage, leur position en
  mètres, leur rotation et leur échelle ; un terrain plat ; les sources de lumière déclarées comme
  aujourd'hui par le manifeste (`light`, `glow`). C'est l'embryon du format du LOT-1018.
- **La caméra** est libre (D-56), bornée en inclinaison entre une vue rasante et une vue
  plongeante ; le dallage et une végétation d'essai peuvent venir des bibliothèques du moteur
  (D-55), les façades et le Colisée non.
- **Lumen et Nanite** sont les réglages par défaut du moteur, sans précalcul : c'est la continuité
  de D-45. Le cycle jour / nuit lit `daylight.json` tel quel.
- **La mesure** se fait au même endroit que celle de la fiche du LOT-1007 : 1080p, poste de
  référence, caméra en mouvement, `stat unit` et `stat gpu` relevés sur dix secondes.
- **Les captures** se prennent par Movie Render Queue en ligne de commande, aux trois cadrages,
  aux deux heures ; elles se rangent à côté de celles du 5 et du 7 octobre pour comparaison.

## Risques et questions ouvertes

- **Le temps d'installation.** Unreal pèse 60 à 100 Go et compile plusieurs minutes : le poste doit
  avoir la place avant d'ouvrir le lot.
- **Le squelette.** Si l'importateur refuse les clips liés par `rig_character.py` (durées, échelle),
  le reciblage par l'IK Retargeter est la voie ; le LOT-1015 en hérite.
- **Le verdict partagé.** Rendu convaincant mais méthode cassée (un geste de l'éditeur impossible à
  rejouer par script) : sans repli (D-57), c'est à l'auteur de dire s'il accepte une exception
  écrite à D-52 ou s'il abandonne ; la fiche l'écrit, datée.
