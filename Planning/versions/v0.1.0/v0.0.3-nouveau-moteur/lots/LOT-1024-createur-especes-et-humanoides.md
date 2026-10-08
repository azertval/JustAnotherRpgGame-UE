+++
id = "LOT-1024"
titre = "Le créateur : les 22 espèces et les humanoïdes de la démo"
version = "0.0.3"
filiere = "pnj"
statut = "a-faire"
taille = "L"
resume = "Le créateur de personnage sait faire chacune des 22 espèces jouables, et les humanoïdes de la démo — la mère, l'enfant, le garde, le maître d'arène et les adversaires de l'arène — y sont des fiches."
prerequis = ["LOT-1015"]
livrables = [
  "Les paramètres de race du créateur pour les 22 espèces de `Source/Elements/Rpg/species/` — corps, têtes, oreilles, défenses, cornes, queues, écailles, tailles —, mesurés espèce par espèce : ce que MetaHuman atteint par conformation, ce qui demande un corps ou une tête Meshy ou Fab, écrit dans la fiche.",
  "La garde-robe commune du créateur.",
  "Une fiche d'exemple par espèce, qui se construit.",
  "Les fiches des humanoïdes de la démo : la mère, l'enfant, le garde (soldat Ironhand), le maître d'arène, et les adversaires de la série de l'arène — bandit, bandit archer, capitaine des bandits, berserker, brute, gladiateur, combattant de l'arène, vétéran, squelette, zombie.",
  "Les captures de contrôle (repos, marche) de chaque humanoïde, à midi et à 22 h ; une planche des 22 espèces au repos.",
]
criteres = [
  "Chaque espèce a une fiche d'exemple qui se construit par le constructeur du créateur, sans geste dans l'éditeur.",
  "Un PNJ se reconnaît à côté de son portrait peint (jugement de l'auteur, sur les captures de contrôle).",
  "Huit personnages à l'écran : la cadence est mesurée et écrite dans la fiche.",
]
+++

## Pourquoi

Le [LOT-1015](LOT-1015-personnages-et-createur.md) prouve le créateur sur quatre héros MetaHuman.
Le jeu en demande plus : 22 espèces jouables, dont plusieurs que MetaHuman ne produit pas tel
quel, et les humanoïdes de la quête et de l'arène, qui avaient chacun leur maillage Meshy jusqu'à
D-63. Ce lot fait du créateur l'outil de tout humanoïde du jeu ; sans lui, le combat se joue avec
des fiches provisoires sur le corps des héros.

## Périmètre

Dedans : les paramètres de race des 22 espèces, la garde-robe commune, les fiches des humanoïdes
de la démo, les captures, la planche des espèces.

Dehors, nommément :

- les PNJ des trois lieux : aux lots de la `0.0.4` ;
- le lion et le loup : au [LOT-1025](LOT-1025-creatures-lion-et-loup.md) ;
- la silhouette volante ;
- les portraits et les jetons : ils restent peints (D-30).

## Conception

- **Les espèces** (`Source/Elements/Rpg/species/`), toutes de taille moyenne ou petite : l'humain ;
  l'elfe et ses six variantes (haut-elfe, elfe des bois, elfes de printemps, d'été, d'automne et
  d'hiver) ; le demi-elfe ; le demi-orc ; le nain, le nain des collines et le nain des montagnes ;
  le halfelin, le halfelin pied-léger et le halfelin robuste ; le gnome ; le tieffelin ; le
  drakéide ; le cirrus ; le gloomfolk ; le taii'maku. Le gnome et les trois halfelins sont de
  petite taille.
- **Ce que MetaHuman atteint** se mesure, espèce par espèce, et s'écrit dans une table de la fiche.
  Le drakéide est hors de sa portée (D-63) ; les petites tailles, les nains et le demi-orc sont à
  mesurer, comme le cirrus, le gloomfolk et le taii'maku, sur leur description dans les données.
  Ce qui manque devient un corps ou une tête Meshy ou Fab, ou une
  pièce Meshy (cornes, défenses, queues, oreilles, écailles).
- **Les humanoïdes de la démo** reprennent les adversaires des rencontres de l'arène
  (`Source/Elements/Rpg/encounters/arene-*.json`). Le soldat Ironhand est le garde du parvis
  (`Source/Elements/World/dialogues/garde.json`) ; il n'est dans aucune rencontre.
- **Les armes** sont celles de `Master/Weapons`, accrochées par socket (D-63).

## Risques et questions ouvertes

- **Les races hors de MetaHuman.** Un corps ou une tête Meshy doit tenir sur le squelette standard
  d'Unreal et dans le graphe Mutable comme un corps MetaHuman ; le coût par espèce est inconnu
  avant la mesure.
- **Les morts-vivants.** Le squelette et le zombie s'écartent le plus d'un corps humain : leur voie
  (conformation, corps Meshy ou Fab) se décide sur mesure.
- **Les licences Fab**, pack par pack, avant achat, par l'auteur.
