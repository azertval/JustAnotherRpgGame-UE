+++
id = "LOT-1024"
titre = "Le générateur : choix de chaîne et prototype jouable"
version = "0.0.3"
filiere = "pnj"
statut = "a-faire"
taille = "L"
resume = "Un créateur témoin empaqueté prouve les curseurs visage et corps, les vêtements et les anatomies difficiles avant de choisir la chaîne de production."
prerequis = ["LOT-1015", "LOT-1016"]
livrables = ["Une matrice des exigences, des familles anatomiques et des options de fabrication et d'assemblage, avec sources, versions et limites vérifiées.", "Un prototype isolé, reproductible et empaqueté : identité du visage, proportions corporelles, deux vêtements, expression, locomotion et sauvegarde.", "Un comparatif Mutable / assemblage natif sur les mêmes assets exportés ; MetaHuman / Character Creator / base riggée évalués séparément pour la fabrication.", "Des preuves anatomiques : corps trapu, main à six doigts et ébauche articulée de Gloomfolk ; stratégie explicite enfant et tête drakéide.", "Un relevé des temps de préparation, corrections, latences, mémoire et rendu, et une décision motivée de chaîne retenue ou de rejet."]
criteres = ["Dans le paquet final, nez et mâchoire, corpulence et proportions changent ; les extrêmes combinés restent compatibles avec vêtements, expressions, yeux, dents, rig et physique.", "Après sauvegarde, fermeture et relancement, l'identité et la tenue sont reconstruites sans éditeur ni service de création externe.", "Le matériel, les scènes, la résolution et les seuils de qualité, latence, CPU/GPU et mémoire sont fixés avant les essais ; les résultats sont consignés, sans extrapolation depuis les mannequins.", "Chaque anatomie témoin dispose d'une voie démontrée ; aucun réglage seulement disponible dans un outil de fabrication n'est présenté comme une capacité du jeu.", "La décision technique et le jugement artistique sont consignés ; en cas d'échec, les lots de production restent bloqués et le lot n'est pas déclaré livré."]
+++

## Pourquoi

**Reprise complète du 20 octobre 2026, à la demande de l'auteur.** Le besoin est un créateur
complet **en jeu**, avec réglage du visage et du corps, également utilisable pour produire les
PNJ. Le prototype du LOT-1015 est remplaçable : ses mesures portent sur des mannequins, pas sur
quatre MetaHuman habillés. Ni sa présence ni D-63 ne dispensent de comparer les solutions.

Le présent lot conserve l'identifiant d'entrée du chantier ; la couverture des espèces,
la garde-robe et les personnages de la démo sont désormais répartis entre LOT-1026 à LOT-1029.
La révision de planification [D-68](../../../../vision/decisions.md) prime sur les anciennes
obligations de fournisseur et de squelette universel.

## Périmètre

Dedans : une tranche verticale de création dans un jeu empaqueté et la décision de production.
Le témoin n'a pas besoin du parcours final de création des règles ni de la carte capitale.
Dehors : bibliothèque complète, production de PNJ, peuplement de la capitale, achat automatique
de packs, refonte des règles et relance des anciennes cartes archivées.

## Conception

| Niveau de décision | Candidats | Ce que l'essai doit établir |
|---|---|---|
| Fabrication | MetaHuman, Character Creator, base modulaire riggée ou spécifique | Export des formes d'identité, rig et vêtements ; coût réel et automatisation |
| Assemblage | Mutable en premier candidat, modulaire natif comme comparaison | Réglages en jeu, qualité, latence, mémoire, maintenance |
| Option ciblée | MetaHuman Collections | Couverture réelle et maturité ; pas d'équivalence présumée avec Creator en jeu |
| Interface | UMG avec logique C++, témoin minimal | Réactivité, limites des paramètres, sauvegarde ; aucune logique Blueprint |

L'analyse documentaire des 19–20 octobre recommande **des bases conçues pour les morphs
d'identité en jeu et des familles anatomiques**, avec Mutable comme premier candidat.
Ce n'est pas une mesure de supériorité. Les expressions animées restent distinctes des formes
d'identité. Une recette JSON ne rend pas portables les UV, poids de skinning et vêtements.

Comparer les fabricants sur les mêmes exigences et vêtements sources lorsque possible ;
comparer les assembleurs sur **exactement les mêmes assets exportés**. Vérifier les limites
de déformation, groom/cheveux, LOD, collision et génération asynchrone. Essayer les demandes
rapides et successives, sans reconstruire tout le personnage à chaque événement de curseur.
Prévoir tunique et manteau long, ainsi qu'un témoin de gant ou de pièce rigide.

Les Gloomfolk ont un bas de corps de scorpion (Player's Guide p. 40–41), les Taii'maku six
doigts (p. 54–55). Les petites tailles et les enfants ne sont pas des adultes réduits.
Les 22 fiches actuelles sont un inventaire de départ : confronter le catalogue aux populations
de `Documentation/Metiers`, notamment les Soulborn absents de ces fiches. Leur inclusion
ou report doit être explicite, sans inventer ici leurs règles de jeu.

Le budget personnages s'inscrit dans les objectifs globaux existants : mesurer au cadrage réel,
avec groupe proche et densités croissantes représentatives de rue/arène. Huit personnages ne
sont ni une limite de conception ni une preuve de capacité d'une foule.

Les sources et scripts du témoin vont dans le dépôt ; captures, mesures et versions des outils
dans les annexes du lot. Aucun changement de carte active n'est nécessaire. Les conclusions
mettent à jour le standard personnages avant l'ouverture du LOT-1026.

Sources techniques à revérifier sur la version installée :
[Mutable Morph](https://github.com/anticto/Mutable-Documentation/wiki/Skeletal-Mesh-Morph),
[Mutable Reshape](https://github.com/anticto/Mutable-Documentation/wiki/Skeletal-Mesh-Reshape),
[modulaire natif](https://dev.epicgames.com/documentation/unreal-engine/working-with-modular-characters-in-unreal-engine),
[MetaHuman 5.8](https://dev.epicgames.com/documentation/metahuman/metahuman-5-8-release-notes-in-unreal-engine),
[Collections](https://dev.epicgames.com/documentation/metahuman/metahuman-collections-in-unreal-engine),
[export Character Creator](https://manual.reallusion.com/Character-Creator-5/Content/ENU/5.0/17-Metahuman-Interoperability/Exporting-Characters-to-UE.htm).

## Risques et questions ouvertes

- Une belle capture ou l'export des expressions ne prouve pas les curseurs d'identité.
- La préparation spécialisée initiale des bases et vêtements doit être chiffrée. Objectif :
  aucune correction par PNJ après validation de sa famille, pas absence de préparation initiale.
- Les outils externes et leurs achats ne sont pas engagés par cette fiche. Leur coût, leurs
  sources conservables et les opérations automatisables font partie de la décision.
- Une API privée du plugin, telle que celle utilisée par l'ancien constructeur, impose
  un contrôle de compatibilité et de reconstruction ; sa stabilité ne se présume pas.
