+++
id = "LOT-314"
titre = "La création de personnage"
version = "0.3.0"
filiere = "interface"
statut = "a-faire"
taille = "L"
resume = "Le parcours de règles (espèce, classe, historique, caractéristiques et équipement) intègre le créateur d'apparence visage/corps déjà livré."
prerequis = ["LOT-301", "LOT-306", "LOT-307", "LOT-308", "LOT-313", "LOT-1030"]
livrables = [
  "L'écran de création, à la charte v2 ; les trois méthodes de caractéristiques ; intégration du créateur d'apparence LOT-1028 et de sa recette versionnée, sans seconde implémentation.",
]
criteres = [
  "Tout personnage que les livres permettent de créer se crée dans le jeu.",
]
+++

## Conception

Les fiches préfabriquées restent proposées : « jouer tout de suite ».

Répartition du 20 octobre 2026 : les curseurs visage/corps, la garde-robe, l'aperçu et la
sauvegarde d'apparence appartiennent aux LOT-1026 à LOT-1030 de la 0.0.3. Ce lot relie ce
créateur aux choix de règles et à l'équipement initial ; il vérifie la cohérence entre
espèce choisie, famille anatomique et objets autorisés. Il ne reporte pas la création
visuelle complète à la 0.3.0 et ne redéfinit pas les rigs ou morphs.
