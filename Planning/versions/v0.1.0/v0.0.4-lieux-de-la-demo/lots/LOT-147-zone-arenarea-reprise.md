+++
id = "LOT-147"
titre = "Zone — Arenarea, repris au standard du jeu final"
version = "0.0.4"
filiere = "cartes"
statut = "a-faire"
taille = "L"
resume = "Les assets et la carte d'Arenarea livrés par les LOT-108 et LOT-109 sont refaits au standard que le jeu final exige ; la carte de principe de la démo leur cède la place."
prerequis = ["LOT-151"]
livrables = [
  "`Regions/central-empire/capital/arenarea/Scene/` repris : chaque poste de la [checklist du LOT-108](../../../../standards/checklist-lot108-arenarea.md) relu pièce par pièce, refait là où il est en deçà du standard, gardé là où il le tient ; le kit republié et verrouillé (`@2`).",
  "Les compléments du commun de la Capitale (postes C) relus de même, sans retoucher les pièces validées du `LOT-105`.",
  "`Levels/central-empire/capital/arenarea.json` : la carte du quartier entier, reprise sur les pièces refaites, dessinée **dans l'éditeur** ; elle remplace la carte de principe du `LOT-146` sous le même identifiant, et garde ses arrivées et ses zones nommées.",
  "L'image de la zone pour l'onglet « Carte », peinte par l'auteur, sous `capital/arenarea/Map/`.",
  "Le relevé de ce qui n'était pas au standard dans les deux livraisons, versé au [standard](../../../../standards/style-3d.md) ou à la [consigne de production](../../../../standards/style-3d.md) : ce qu'une zone ne doit plus livrer.",
]
criteres = [
  "L'auteur valide la zone sur la galerie **et** sur le rendu du moteur, à 1080p et 2160p, comme au standard du jeu final — pas « en l'état ».",
  "Le sol de la zone est posé sur douze cases sur douze sans motif régulier ; chaque pièce tient la palette de l'Empire et la lumière du standard.",
  "`LevelEditor --check` passe ; la carte tient 60 images par seconde à 1080p sur le poste de référence.",
  "La quête « Des pommes pour l'arène » se rejoue de bout en bout sur la carte reprise, sans changer une ligne de la quête.",
]
sources = [
  "Tanares Sourcebook, p. 91-92, 96-99 ; plan VTT (référence seule)",
]
+++

## Pourquoi

Les [LOT-108](../../v0.0.1-demo/lots/LOT-108-assets-hd-arenarea.md) et
[LOT-109](../../v0.0.1-demo/lots/LOT-109-carte-arenarea.md) ont été livrés le 24 septembre 2026
et validés en l'état. Relus le lendemain, ils sont **loin du standard de qualité** que l'auteur veut
pour le jeu final ([D-25](../../../../vision/decisions.md)) : ils sont à refaire. La démo n'en
dépend plus — elle se joue sur des cartes de principe (`LOT-146`) — et la reprise trouve sa place
ici, avec les six autres quartiers, où une zone se produit pour de bon.

Ce lot est aussi l'occasion d'apprendre : ce qui, dans ces deux livraisons, n'était pas au
standard doit s'écrire dans le standard lui-même, pour qu'aucune zone de la `0.0.3` ne le refasse.

## Périmètre

**Dedans** : les pièces de scène d'Arenarea et les compléments communs qu'il a versés, la carte
jouable, l'image de l'onglet. La checklist du `LOT-108` reste l'inventaire ; ce lot ne l'étend pas.

**Pas dedans** : les PNJ d'Arenarea (`LOT-114`), l'Arena of Fate (`LOT-106`, `LOT-107`) — dont la
façade se coordonne avec ce lot —, les intérieurs, les animaux.

## Conception

Ce qui est repris se décide **sur pièce**, à la relecture : une pièce qui tient le standard se
garde, une pièce qui ne le tient pas se refait, jamais « on refait tout » par principe. La
production suit la [consigne](../../../../standards/style-3d.md) et le
[gabarit de commande](../../../../standards/gabarit-commande-zone.md), comme toute zone. La carte
reprend le tracé du `LOT-109` — le quartier entier, ses lieux nommés, ses portails condamnés vers
les cartes qui n'existent pas encore — sur les pièces refaites.

## Risques et questions ouvertes

- **La taille.** Le `LOT-108` a installé 1 491 pièces. Si la relecture en refait la majorité, le
  lot est un `XL` et se redécoupe (assets, puis carte), comme le gabarit de la version le prévoit.
- **Ce que « standard du jeu final » veut dire** n'est écrit nulle part avec cette exigence : le
  premier geste du lot est de le dire, sur les pièces livrées, avant d'en refaire une.

## Atelier du 5 octobre 2026 — reprise en cours

L'auteur demande une image du quartier entier comme référence de la reconstruction, puis un
rendu en jeu équivalent et des images séparées pour les pièces qu'il produira avec Meshy.
La proposition originale et son prototype sont dans
`Tools/Assets3D/Regions/central-empire/capital/arenarea/Production147/` :
`Reference/arenarea-master-v2.png`, `layout-contract.json`, `galerie.html`, `audit.json` et
`MeshyReferences/`. Cette image est une **proposition**, pas une validation artistique de l'auteur.
Les pages 96–99 du Sourcebook servent à la géographie et aux lieux, sans être utilisées comme
images d'entrée du générateur. La référence du Colisée déjà produite sert à la cohérence visuelle.

Le prototype de 128 × 88 cases a été créé et assemblé par les commandes natives de l'éditeur.
Il comporte 137 maillages locaux actifs avec textures albédo, normales et ORM embarquées :
60 modules d'architecture, 72 de mobilier et de finition, et les cinq retours Meshy reçus.
La statue du champion, le char, l'enseigne du pub et les deux arbres sont intégrés ; les exports
reçus sont conservés intacts. La chaîne règle l'échelle et l'origine sans décimation ni retouche
manuelle, et reprend les cartes sources dans les copies moteur à 1024 px. Les modèles
existants du Colisée sont réemployés ; ses trois cartes et la carte Arenarea de production sont
inchangées. Le contrôle natif ne relève aucune erreur ; le contrôle des accès ne relève aucune
case ouverte inaccessible. Les captures du moteur sont versées à l'atelier.

**Le lot reste à faire : l'équivalence visuelle n'est pas acquise.** La densité des façades,
les jardins, les quais et le mobilier doivent encore être rapprochés de l'image. Le relevé
`audit-postes-lot108.json` confronte les 102 postes aux pièces du prototype : 78 partiels,
18 absents, 4 postes avec retours Meshy intégrés et 2 réemployés du Colisée. Leur validation
artistique reste ouverte ; un retour intégré ne complète pas toutes les variantes de son poste.
La terrasse du pub, les étals de luxe, les jardins, les tours et les tribunes courbes couvertes
sont assemblés en volumes réels. `import_returns.py`, `build_details.py` et `place_details.py`
complètent la chaîne de l'atelier. Les captures de jeu du parvis, du pub et de l'hippodrome sont
réellement à 1920 × 1080. Deux arrivées de revue locales sans portail expliquent deux
avertissements supplémentaires du contrôle natif, en plus des cinq historiques de Martpart.
La diversité des façades, les berges, les finitions et raccords manquants, la comparaison au
LOT-105 V4 absent de ce poste, le contrôle à 2160p, la mesure à 60 ips, le rejeu de la quête
et la validation artistique restent ouverts. Le kit n'est ni publié ni verrouillé.

## V0 installée dans le jeu — 5 octobre 2026

À la demande de l'auteur, le prototype de l'atelier est installé tel quel dans `Source/Elements` :
`Levels/central-empire/capital/arenarea.json` (128 × 88 cases) et sa fiche d'éditeur remplacent la
carte de principe du `LOT-146` sous le même identifiant, et les 137 maillages rejoignent
`capital/arenarea/Scene/` avec leur manifeste. Les arrivées `from-martpart` et
`from-arena-of-fate`, le garde, l'enfant et la zone `parvis` gardent leur nom ; la quête n'a pas
changé d'une ligne, seuls ses tests ont reçu les cases de la nouvelle carte. Les deux arrivées de
revue (`revue-pub`, `revue-hippodrome`) restent, avec leurs deux avertissements au contrôle natif.
Le kit est publié et verrouillé sous `arenarea@3` (600 fichiers, 890 Mio) : c'est le kit de la
v0, pas le kit repris que ce lot doit livrer.

C'est une **v0** : le lot reste à faire. Les images du `LOT-108` sont encore dans le kit — leur
retrait ([D-32](../../../../vision/decisions.md)) appartient à la livraison finale, quand la
relecture poste par poste aura dit ce qui se garde. La validation artistique, le contrôle à 2160p,
la mesure à 60 images par seconde et l'image de l'onglet « Carte » restent dus.
