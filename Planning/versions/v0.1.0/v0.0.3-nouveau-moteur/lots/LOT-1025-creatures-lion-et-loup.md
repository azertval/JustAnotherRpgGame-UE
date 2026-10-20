+++
id = "LOT-1025"
titre = "Les créatures : familles animales, lion et loup"
version = "0.0.3"
filiere = "pnj"
statut = "a-faire"
taille = "L"
resume = "Le lion et les deux loups de la rencontre utilisent des rigs et animations validés, intégrés au contrat d'apparence sans dépendre d'une anatomie humaine."
prerequis = ["LOT-1026", "LOT-1017"]
livrables = ["La voie de production documentée des familles animales : source des modèles, rigs, animations, profils de retargeting, physique et import reproductible.", "Un lion et un loup réutilisable, leurs matériaux, LOD et animations de repos, déplacement, attaque, réaction et mort.", "Les recettes d'apparence, collisions/navigation, effets et instants d'impact raccordés aux règles de combat et à la rencontre colisee-fauves.", "Les captures de contrôle à midi et à 22 h et les mesures dans un paquet final avec le lion et deux instances de loup."]
criteres = ["La rencontre colisee-fauves affiche un lion et deux loups distincts en instance, partageant les ressources appropriées, sans mannequin ni rig humain forcé.", "Locomotion, attaque, réaction et mort correspondent au modèle ; contacts au sol, virages, collision/navigation et portée de combat sont contrôlés.", "Les dégâts se déclenchent une seule fois à l'événement d'impact défini ; la mort reste lisible et les acteurs quittent correctement la participation au combat.", "Le chargement, la reconstruction depuis les sources et la sauvegarde/reprise fonctionnent dans le paquet final ; CPU/GPU et mémoire sont consignés."]
+++

## Pourquoi

**Reprise complète du 20 octobre 2026.** La rencontre `colisee-fauves.json` demande un lion et
deux loups. L'ancienne fiche présumait un squelette quadrupède et une bibliothèque de clips
fournis par le moteur : cette disponibilité n'est pas démontrée et n'est plus un prérequis
implicite. Le rig et chaque animation doivent avoir une provenance réelle.

## Périmètre

Dedans : pipeline animal réutilisable, deux espèces, intégration au combat et contrôle.
Dehors : créateur animal complet à curseurs pour le joueur, reste du bestiaire, montures et
vol. Le Gloomfolk appartient au catalogue jouable du LOT-1026 ; son anatomie ne se réduit
ni au mannequin ni à celle des fauves.

## Conception

Le LOT-1026 livre les conventions communes de recette, actions et équipements. Pour chaque
famille animale, choisir un modèle déjà riggé avec animations compatibles, ou démontrer
la préparation d'un rig spécifique. Meshy ou Fab peuvent fournir des sources, mais ni
l'autorig ni le reciblage ne garantissent seuls une locomotion correcte.

Un squelette partagé lion/loup est possible seulement si les proportions et déformations
passent les tests. Autoriser deux rigs avec le même contrat d'actions. Les clips ne sont
pas présumés présents dans Unreal ; leurs droits d'usage et leur version sont consignés.
Le retargeting IK est évalué sur marche/course, pivots, attaque et contacts, avec correction
de la base partagée si nécessaire.

Comparer un Skeletal Mesh préparé directement à une génération via le backend retenu.
Pour une apparence animale fixe, préférer la voie la plus simple qui respecte les besoins
et les budgets ; Mutable n'est pas obligatoire. Les recettes peuvent référencer une base
animale sans passer par un graphe humain. Les proportions et volumes de collision doivent
être cohérents avec navigation et règles, sans modifier les statistiques pour masquer un
problème visuel.

Tester dans une scène dédiée puis dans la démo active sans réintroduire de carte archivée.
Conserver instants d'impact et événements de clips dans des données versionnées. Tester
changement de cible, interruption et mort ; partager les assets entre les deux loups.
Le LOT-1030 mesure les coûts cumulés avec le groupe et les PNJ.

## Risques et questions ouvertes

La qualité du rig, la disponibilité des animations et le coût de préparation se tranchent
sur les assets réels. Aucun budget de triangles de décor ni promesse Nanite n'est une preuve
de coût d'animation. Un achat reste une action distincte de la rédaction de ce lot.
