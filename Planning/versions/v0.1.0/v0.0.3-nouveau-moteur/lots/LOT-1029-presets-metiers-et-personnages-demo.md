+++
id = "LOT-1029"
titre = "Le générateur : presets métiers et personnages de la démo"
version = "0.0.3"
filiere = "pnj"
statut = "a-faire"
taille = "L"
resume = "Les héros, habitants et adversaires de la démo deviennent des recettes du nouveau générateur, avec des presets professionnels réutilisables."
prerequis = ["LOT-1028", "LOT-1017"]
livrables = ["Les presets de production séparant anatomie, culture, métier, milieu social, affiliation et variations individuelles, avec provenance et graine.", "La migration des quatre héros, de la mère, de l'enfant, du garde Ironhand, du maître d'arène et des adversaires effectivement référencés.", "Les recettes de bandit, archer, capitaine, berserker, brute, gladiateur, combattant, vétéran, squelette et zombie, complétées par l'inventaire des rencontres actives.", "Le raccord des apparences à la démo actuelle autour de l'arène et la suppression contrôlée des remplacements provisoires devenus inutiles."]
criteres = ["Tous les identifiants de personnage référencés par la quête et les rencontres actives résolvent une apparence validée, sans mannequin de remplacement.", "Le garde, la mère, l'enfant, le maître d'arène et les adversaires se reconnaissent au cadrage joueur ; leurs portraits peints restent cohérents.", "Un preset produit plusieurs variantes reproductibles sans copier corps et textures à chaque PNJ ; un PNJ nommé conserve sa recette explicite.", "Les captures repos/marche/attaque, à midi et à 22 h, et le relevé des références migrées sont livrés."]
+++

## Pourquoi

La production en série n'est ouverte qu'après validation des bases, de la garde-robe et du
créateur. Ce lot reprend la livraison de personnages auparavant concentrée dans le LOT-1024.

## Périmètre

Dedans : personnages nécessaires à la démo et petit ensemble de presets réutilisables.
Dehors : remplir la capitale entière, les gradins ou tous les lieux de la 0.0.4 ; les fauves
restent au LOT-1025. Les lots de peuplement consomment ensuite ces recettes.

## Conception

L'inventaire fait foi à partir des cartes, dialogues et rencontres actifs, pas d'un ancien
compte de vingt modèles. La démo actuelle est centrée sur `/Game/Capitale/Cartes/Capitale` :
mère à l'étal, enfant en cellule, garde de la prison, maître d'arène au bord du sable.
Ne pas restaurer les anciennes cartes archivées ni leurs placements.

La bibliothèque de métiers donne des possibilités visuelles, pas une tenue unique par
branche. Employer les contraintes locales et les accessoires pour distinguer artisans,
civils et soldats. Les parts de population proposées dans `Documentation/Metiers` ne sont
pas des fréquences canoniques et les marges métier/espèce/milieu ne constituent pas une
jointure complète ; expliciter les hypothèses des presets.

Les héros Grom, Faelar, Helga et Nessa passent par le même contrat. Le squelette et le zombie
requièrent leur base validée, sans supposer qu'une texture suffit. Les personnages nommés
conservent leurs identifiants de règles, quêtes et sauvegardes.
Avant de retirer un asset provisoire, vérifier ses références, sa recette de remplacement
et la reconstruction ; aucune suppression générale des travaux en cours.

## Risques et questions ouvertes

La liste de PNJ peut évoluer avec la carte active : conserver un inventaire daté et tracer les
écarts. Les noms et apparences encore ouverts ne sont pas inventés comme faits du Sourcebook.
La densité et les performances de population se valident au LOT-1030.
