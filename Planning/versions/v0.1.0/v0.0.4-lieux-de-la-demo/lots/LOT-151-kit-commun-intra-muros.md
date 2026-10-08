+++
id = "LOT-151"
titre = "Assets — le kit de la Capitale, en maillages"
version = "0.0.4"
filiere = "assets"
statut = "a-faire"
taille = "L"
resume = "Le kit commun de la Capitale repris en maillages pour les trois lieux de la `0.1.0` : son architecture, son mobilier, ses pièces maîtresses — la dette d'images de la `0.0.2.5`."
prerequis = ["LOT-142", "LOT-1003", "LOT-1023"]
reprend = ["LOT-1004"]
livrables = [
  "L'**architecture du kit en maillages** — sols, murs, balustrades, haies, escaliers, toits —, sous les mêmes clés : les livrables du `LOT-1004`, clos sans modification (D-43), repris tels que sa fiche les énonce.",
  "Le [standard 3D](../../../../standards/style-3d.md) complété de ce que le `LOT-1004` devait trancher : le **contour sombre**, la **forme** de chaque pièce des familles à classer, le **budget** d'un maillage de décor.",
  "Le **mobilier** et les **pièces maîtresses** du kit que les trois lieux posent, en maillages : la tolérance de D-30 s'arrête à cette version.",
  "Les pièces d'Arenarea (`LOT-108`) qui resservent **promues** au commun, avant sa reprise (`LOT-147`) ; le kit publié et verrouillé.",
]
criteres = [
  "Les critères du `LOT-1004` sont tenus : cartes livrées rechargées sans retouche, facture jugée côte à côte par l'auteur, plus aucun PNG dans `floors/`, `walls/`, `balustrades/`, `stairs/` et `roofs/`, mécanisme d'étage 2D et recouvrement des dalles retirés.",
  "Plus aucune image de mobilier ni de pièce maîtresse du kit n'est posée sur les cartes de la `0.1.0` ; `check_orphans.py` passe.",
  "Aucune pièce d'Arenarea n'est copiée : celles qui resservent sont montées au commun par renommage outillé.",
]
+++

## Réécrit à la recette de la `0.0.2.5` ([D-35](../../../../vision/decisions.md), [D-47](../../../../vision/decisions.md), 5 octobre 2026)

Deux choses changent.

**Le périmètre se resserre.** Ce lot devait d'abord donner aux **six nouveaux quartiers** ce que le
kit de la démo n'avait pas — marbre blanc, lanternes magiques, statues, grilles, enseignes de
guilde. Ces quartiers partent à la `0.3.1` (D-47), et ces pièces avec eux : elles n'ont plus de
fiche, un lot de kit s'écrira à l'ouverture de leur
[version](../../../v0.4.0/v0.3.1-capitale-intra-muros/README.md). Ce lot ne sert plus que les trois
lieux de la `0.1.0` : Arenarea, Martpart et, pour ce qu'elle prend au commun, l'Arena of Fate.

**Il devient le lot de la dette.** Ce qu'il garde est ce que la `0.0.2.5` lui a laissé : l'architecture
du kit en maillages (`LOT-1004`, D-43), et le mobilier et les pièces maîtresses que D-30 tolérait en
image jusqu'ici. Sa taille passe de M à **L**, celle du `LOT-1004` dont il hérite. S'il la dépasse,
il se redécoupe — l'architecture, puis le mobilier et les pièces maîtresses —, comme le gabarit de
la version le prévoit. L'Arena of Fate s'est produite avant lui, pour la recette de la `0.0.2.5`
(D-46) : ses 105 maillages sont le premier relevé de ce que coûte un kit de décor, et le budget
d'un maillage de décor se mesure d'abord là.

## Pourquoi

Première épreuve de la règle de promotion : c'est ici qu'on voit si l'arborescence tient.

> **Étendu le 2 octobre 2026** ([D-43](../../../../vision/decisions.md)). Le
> [LOT-1004](../../v0.0.2.5-passage-3d/lots/LOT-1004-kit-de-la-capitale-en-maillages.md) — le kit
> de la Capitale en maillages — est clos sans modification : l'auteur reprend l'intégralité des
> assets à cette version. Ce lot hérite de son inventaire, de ses critères et de sa rubrique
> « À supprimer » (les 1 340 images d'architecture, le mécanisme d'étage 2D, le recouvrement des
> dalles, la maquette 2D HD), qui se lisent dans sa fiche. La taille et le découpage de ce lot se
> revoient à la recette de la `0.0.2.5` (LOT-1010, D-35), où les lots de la `0.0.3` se réécrivent : c'est fait, ci-dessus.
