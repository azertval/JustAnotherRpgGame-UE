+++
id = "LOT-1015"
titre = "Les vingt personnages dans le moteur, au maître"
version = "0.0.3"
filiere = "pnj"
statut = "a-faire"
taille = "L"
resume = "Les vingt modèles de la démo, leurs deux squelettes et leurs clips vivent dans le nouveau moteur, importés au maître sans décimation ; la chaîne Meshy, l'atelier Blender et les fiches de liaison restent ceux du standard."
prerequis = ["LOT-1014"]
livrables = [
  "Un script d'import (`scripts/assetsGeneration/import_character_unreal.py`, piloté par la fiche d'atelier) qui prend le `.glb` lié au maître, son squelette et ses clips, et produit le maillage squelettique, les animations et le portrait dans le projet ; rejouable, sans geste dans l'éditeur.",
  "Les squelettes `humanoid` (53 os) et `quadruped` (29 os) comme squelettes du moteur, avec leurs clips (six et cinq) ; si l'importateur refuse les clips liés, le reciblage par l'IK Retargeter, décrit dans la fiche de liaison.",
  "Les vingt personnages importés : les quatre héros, la mère, l'enfant, le garde, le maître d'arène, les adversaires de la série, le lion et le loup ; portraits et jetons repris tels quels.",
  "`reduce_model.py` retiré ; `personnages-3d.md` révisé : le modèle se livre au maître (D-53), le budget d'un modèle est un poids sur disque, mesuré ici sur les vingt.",
  "L'atelier des assets (vue Character, aller-retour Blender, D-44) rebranché : une fiche de liaison ou de retouche modifiée rejoue l'import.",
  "Les captures de contrôle de chaque personnage (repos, marche) sur le nouveau moteur, comme `render_character_review.py` les produisait.",
]
criteres = [
  "Les vingt personnages se tiennent au repos et marchent dans le moteur sans glissement ni pénétration du sol, aux seuils du standard (1,3 mm, 0,53 px à 1080p) ; `check_character_model.py` passe.",
  "Un personnage se reconnaît à côté de son portrait (jugement de l'auteur, sur les captures de contrôle).",
  "Aucun `.glb` ni clip n'a été retouché à la main : l'import relancé depuis les fiches redonne les mêmes fichiers (empreintes).",
  "Le poids sur disque des vingt modèles au maître est écrit dans le standard, avec le poids en mémoire graphique mesuré sur huit personnages à l'écran.",
]
+++

## Pourquoi

La production de personnages est devenue le poste le plus prévisible du projet (bilan de la
`0.0.2.5`) : dix-sept liaisons sur dix-huit sans intervention. Ce lot la garde telle quelle et ne
change que la sortie : le moteur. Il profite de D-53 pour cesser de décimer.

## Périmètre

Dedans : l'import, les squelettes, les clips, les vingt modèles, l'atelier rebranché, la révision
du standard des personnages.

Dehors, nommément :

- de nouveaux personnages : les PNJ des trois lieux restent aux lots de la `0.0.4` ;
- les armes tenues (D-42 laisse la question ouverte) ;
- la silhouette `flying`, qui attend sa première créature.

## À supprimer

| Quoi | Où | Pourquoi maintenant |
|---|---|---|
| `reduce_model.py` et ses tests | `scripts/assetsGeneration/` | le maître s'importe tel quel (D-53) |
| Les copies réduites à 100 000 triangles dans les kits | `Common/Characters/**`, à la republication du kit | remplacées par les maîtres ; deux modèles pour un personnage serait un asset mort |

Le kit `Common` est republié avec les maîtres depuis le nouveau dépôt ; l'ancien dépôt garde son
verrou sur `Common@9` et ne bouge plus (D-58).

## Conception

- **Le maître est la source.** Meshy produit entre 10 000 et 2,6 millions de triangles selon la
  pièce ; Nanite pour les maillages squelettiques les prend. Si une mesure montre qu'un personnage
  au maître coûte trop à l'écran, la fiche de liaison porte un plafond par personnage, pas le
  standard.
- **Les clips** viennent de `rig_character.py` et `rig_quadruped.py` ; ils ont été réglés une fois
  par silhouette et ne se refont pas. Le trot du quadrupède, encore à approuver (LOT-1011), se juge
  ici dans le moteur.
- **Le portrait du PNJ en dialogue** et le jeton restent peints (D-30) ; rien ne change pour eux.

## Risques et questions ouvertes

- **Le reciblage.** Si les clips ne s'importent pas tels quels, l'IK Retargeter vers un squelette
  du moteur est la voie ; le coût est d'une journée par silhouette, pas par personnage.
- **La texture plus pâle que la figurine**, constat ouvert du standard §11 : sous Lumen et un
  espace linéaire, elle peut disparaître ou s'aggraver ; à juger sur les captures.
