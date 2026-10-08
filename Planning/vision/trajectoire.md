# La trajectoire

## Le problème qu'elle résout

L'ancienne feuille de route appelait `0.1.0` le **monde entier** : treize régions, seize classes, le
plan pénombral. Quarante-trois lots restaient, dont la plupart disaient *quoi* sans dire *comment* :
trop de zones, pas assez de conception par zone. En démarrant le travail, l'auteur l'a jugée
titanesque. La trajectoire ci-dessous la remplace par une règle simple : **une version courte,
jouable, détaillée à fond ; les suivantes esquissées ; rien au-delà n'est promis en détail.**

## Les jalons

| Version | Ce qu'elle rend jouable | Nature |
|---|---|---|
| `0.0.1` | **Démo basique** : Martpart, Arenarea et son donjon l'Arena of Fate, en **cartes de principe** (D-25) ; le standard 2D HD ; une quête | détaillée, lot par lot |
| `0.0.2` | **Système de combat** : les quatre classes de base, le combat de groupe, l'interface | détaillée |
| `0.0.2.5` | **Passage à la 3D** (D-29) : même vue isométrique, un maillage par personnage sur un squelette commun (D-38), cycle jour / nuit, l'Arena of Fate en maillages ; le jeu de la `0.0.2` rejoué dans sa nouvelle matière | détaillée, lot par lot |
| `0.0.3` | **Le nouveau moteur** (D-48) : le jeu passe sur Unreal Engine 5, caméra libre, combat en distance à la manière de Baldur's Gate 3, cartes composées ; le jeu de la `0.0.2.5` rejoué sur le nouveau moteur, Arenarea reconstruit | détaillée, lot par lot |
| `0.0.4` | **Les trois lieux de la démo**, produits pour de bon : l'Arena of Fate et son donjon, Arenarea, Martpart — décor au maître, PNJ en modèles, cartes définitives | fiches écrites, **à réécrire** à la recette de la `0.0.3` |
| **`0.1.0`** | **La démo, à sa qualité finale** : ces trois lieux relus d'un bloc et publiés (D-47) | détaillée |
| **`0.2.0`** | **La compagnie**, la sauvegarde, le voyage et les dernières fonctionnalités du jeu et de l'éditeur : après elle, on n'ajoute plus que du contenu | détaillée à la maille de la fonctionnalité |
| **`0.3.0`** | **Classes et espèces, pour de vrai** : 21 espèces, 20 classes, 69 sous-classes, les sorts | détaillée à la maille du paquet |
| `0.3.1` → `0.3.7` | **Une sous-version par zone** de l'Empire central : la Capitale dans ses murs, les faubourgs, les abords, la côte sud, Bak, le nord, l'ouest | fiches écrites, **à réécrire** à l'ouverture (D-35) |
| **`0.4.0`** | **L'Empire central**, relu d'un bloc : toutes ses zones, ses PNJ nommés, ses peuples, ses animaux, ses monstres | détaillée |
| `0.5.0` → `0.16.0` | **Une région majeure par version**, du voisinage de l'Empire vers les confins | prévisionnelle |
| `0.17.0` | Les autres régions : Undertanares, Darkall, Mystical | prévisionnelle |
| `0.18.0` | Le plan pénombral | prévisionnelle |
| **`1.0.0`** | Le monde complet, bac à sable | prévisionnelle |

Chaque version `0.x.0` de région se segmentera en sous-versions **par zone**, comme la `0.4.0`, et
recevra au besoin des lots intermédiaires de correction ou de mécanique.

## Les systèmes d'abord, le monde ensuite

Jusqu'au 5 octobre 2026, la `0.1.0` était l'Empire central entier, et le monde se bâtissait zone
par zone avant que les systèmes soient finis. L'auteur a inversé l'ordre
([D-47](decisions.md)) : la `0.1.0` ne garde que les **trois lieux de la démo**, menés à leur
qualité finale ; viennent ensuite **tous les systèmes** (`0.2.0`, `0.3.0`) ; et seulement alors le
monde, l'Empire central d'abord (`0.4.0`), les autres régions décalées d'un cran. Les lots de
système que portaient les versions de zone — la sauvegarde, le voyage, les outils de l'éditeur —
ont rejoint la `0.2.0`.

Le 7 octobre 2026, l'auteur a jugé le moteur maison et son éditeur incapables d'atteindre la
qualité des cartes de l'atlas et a décidé le passage sur Unreal Engine 5 ([D-48](decisions.md)) :
c'est la `0.0.3`, un système au sens de cet ordre, et les trois lieux glissent en `0.0.4`.

Trois raisons tiennent cet ordre. Un lieu produit pour de bon, du premier asset à la carte jouée,
donne le **coût d'un lieu** avant qu'on en commande vingt. Un système fini avant le monde ne se
refait pas sur vingt zones livrées. Et la règle 3 — les fonctionnalités se ferment à la `0.2.0` —
cesse d'avoir des exceptions logées dans des versions de zone.

## L'ordre des régions

Par **proximité de l'Empire central**, d'après les voisinages de l'atlas
(`Source/Elements/World/regions/`) : on n'ouvre une région que si l'on peut y **marcher** depuis
une région déjà ouverte.

| Cercle | Versions | Régions |
|---|---|---|
| Voisines de l'Empire | `0.5.0` → `0.10.0` | Imperial Benênet, Seashores, Sindile Forest, Theocracy of Kepesh, Stravian Domains, Tsvetan |
| Second cercle | `0.11.0` → `0.14.0` | Republic of Freelands, Magocracy of Mage Tower, Kingdom of Kolbjörn, Taii-Maku City States |
| Confins | `0.15.0`, `0.16.0` | Storm Islands, Yama |

L'ordre **à l'intérieur** d'un cercle est une préférence, pas une contrainte : il se revoit à la
recette de la `0.3.0`. Deux arguments pèseront : la Republic of Freelands porte le siège de la
Guilde des Aventuriers et trente-trois PNJ nommés — elle mérite peut-être de passer plus tôt ;
Stravian Domains ouvre sur Undertanares.

Le détail de chaque région est dans [le référentiel](../referentiels/monde/regions.md).

## Les cinq règles

1. **Une seule version est détaillée à fond** : la prochaine. Les autres ont un périmètre et des
   critères de sortie ; leurs lots se précisent quand elles approchent. Les fiches de zone de
   l'Empire central, écrites quand il était la `0.1.0`, sont gardées et marquées **à réécrire**.
2. **Chaque version se joue.** Pas de version « technique » : même la `0.0.2`, qui est un système,
   se juge sur un combat joué de bout en bout.
3. **Les fonctionnalités se ferment à la `0.2.0`.** Tout ce qui suit est du contenu. Une
   fonctionnalité demandée après passe par une décision écrite.
4. **L'ordre des lots se calcule**, il ne s'arbitre pas : parmi les lots dont tous les prérequis
   sont livrés, celui de la version la plus proche, puis celui qui en débloque le plus.
5. **Chaque version se clôt par un bilan** qui recale les suivantes : ce qui a coûté plus que
   prévu, ce qu'une zone pèse, ce qu'un PNJ demande.

## Ce qu'on ne sait pas encore

**Ce que coûte une zone.** Toute la trajectoire repose sur ce nombre, et il n'existe pas : aucune
zone n'a été produite au standard du jeu final : Arenarea (`LOT-108`, `LOT-109`) l'a été en deçà, et se
refait (D-25). La `0.0.3` en donnera un premier relevé avec Arenarea reconstruit sur le nouveau
moteur (LOT-1021), la `0.0.4` le confirmera pour les trois lieux de la démo, et la recette de la
`0.1.0` l'écrira avant que l'Empire central s'ouvre.
D'ici là, aucune date n'est annoncée — ce serait une extrapolation, pas une prévision. À l'échelle :
l'Empire central compte une vingtaine de zones ; le monde complet, une centaine, plus le plan
pénombral.
