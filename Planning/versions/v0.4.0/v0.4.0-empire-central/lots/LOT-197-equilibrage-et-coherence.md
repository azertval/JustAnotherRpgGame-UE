+++
id = "LOT-197"
titre = "Équilibrage et contrôle de cohérence"
version = "0.4.0"
filiere = "regles"
statut = "a-faire"
taille = "L"
resume = "La région se joue du niveau 1 au niveau 5 sans mur ni promenade ; le contenu est contrôlé d'un bloc."
prerequis = ["LOT-195", "LOT-196"]
reprend = ["LOT-49"]
livrables = [
  "La courbe de difficulté par zone, réglée par simulation.",
  "Le contrôle de cohérence du contenu : toute référence résolue, tout texte traduit, tout asset cité.",
]
criteres = [
  "Aucune rencontre obligatoire n'a un taux de victoire simulé sous 50 % au niveau attendu.",
]
+++

> **Reporté à la `0.4.0`** ([D-47](../../../../vision/decisions.md), 5 octobre 2026). La `0.1.0` ne garde que les
> trois lieux de la démo : cette fiche, écrite pour la `0.1.0`, sert désormais la
> `0.4.0` — l'Empire central —, après les systèmes (`0.2.0`, `0.3.0`).

## Périmètre

Le niveau maximal de la `0.4.0` est **5** : c'est ce que les quatre classes de base couvrent.
