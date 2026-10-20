+++
id = "LOT-1028"
titre = "Le générateur : créateur complet en jeu"
version = "0.0.3"
filiere = "interface"
statut = "a-faire"
taille = "L"
resume = "Le joueur règle visage et corps, choisit sa tenue, puis retrouve exactement son apparence ; l'outil de production utilise le même générateur."
prerequis = ["LOT-1026", "LOT-1027", "LOT-1020"]
livrables = ["L'interface UMG à logique C++ : choix d'espèce/base, curseurs visage et corps, cheveux, couleurs, vêtements, aperçu et réinitialisation.", "La gestion des mises à jour asynchrones et des erreurs, la recette sauvegardée et les contrôles de migration.", "Un mode de production partageant les paramètres et la validation : presets, verrouillage de choix, génération déterministe par graine et export de fiches.", "Les tests de sauvegarde/rechargement, changement rapide de paramètres, changement de famille et reconstruction dans un jeu empaqueté."]
criteres = ["Le créateur livré en jeu possède de vrais réglages d'identité faciale et corporelle, distincts des expressions ; les vêtements suivent ces réglages dans les plages publiées.", "Une réponse asynchrone obsolète n'écrase jamais le dernier choix ; la confirmation attend une apparence cohérente et les latences respectent les seuils du LOT-1024.", "Après fermeture et relancement, les paramètres, équipements et couleurs sont identiques ; les données anciennes migrent ou produisent une erreur explicite.", "Le mode de production et le mode joueur reconstruisent la même recette ; aucune dépendance à un outil de création externe n'est nécessaire à l'exécution."]
+++

## Pourquoi

Un générateur d'assets ne suffit pas au créateur complet demandé. Ce lot livre le parcours
visuel en jeu et évite deux implémentations divergentes pour le joueur et les PNJ.

## Périmètre

Dedans : création d'apparence complète dans les familles et plages validées, presets, aperçu,
persistance et mode de production. Dehors : choix de classe, historique, règles de
caractéristiques et validation de personnage au sens des livres, qui restent au LOT-314.
Celui-ci intégrera cet écran au parcours de règles sans réécrire le générateur.

## Conception

Afficher les contraintes propres à l'espèce sans promettre des transformations arbitraires
entre anatomies. Distinguer identité persistante et expressions d'aperçu. Proposer annuler,
réinitialiser, rotation/zoom et un éclairage de contrôle ; localiser les libellés FR/EN.
Reprendre la charte du jeu et ses commandes, sans logique Blueprint.

Regrouper les événements de curseurs, versionner les requêtes et ignorer les réponses
dépassées. Préserver une apparence affichable pendant la reconstruction, gérer l'échec
et libérer les ressources des générations annulées. Tester les changements rapides de
famille et d'équipement, pas seulement le déplacement lent d'un curseur.

La génération de variantes accepte une graine, des paramètres verrouillés et des plages
validées ; elle ne distribue pas les métiers par espèce de manière déterministe.
Les portraits et jetons peints restent une filière distincte (D-30) : préciser leur sélection
dans l'interface sans les remplacer implicitement par une capture du visage.

## Risques et questions ouvertes

L'identité doit rester cohérente aux changements de LOD et après reprise de sauvegarde.
Le temps acceptable d'actualisation se fixe au LOT-1024 et se contrôle ici sur le vrai écran,
avec les pièces du LOT-1027 ; aucune promesse de calcul instantané n'est admise.
