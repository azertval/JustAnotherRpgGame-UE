# Version 0.0.4 — les trois lieux de la démo

> **Renumérotée le 7 octobre 2026** ([D-48](../../../vision/decisions.md)) : la `0.0.3` est devenue
> le [nouveau moteur](../v0.0.3-nouveau-moteur/README.md), et les trois lieux passent en `0.0.4`.
> Les fiches ci-dessous ont été écrites pour le moteur maison ; elles se **réécrivent** à la recette
> de la `0.0.3` (LOT-1023), comme D-35 l'a fait pour la 3D. Arenarea est reconstruit par le
> LOT-1021 ; l'Arena of Fate et Martpart sont portés par le LOT-1022 ; le LOT-147 et le LOT-151
> attendent le LOT-1023.

Martpart, Arenarea et l'Arena of Fate produits **pour de bon** : décor en maillages, PNJ en
modèles, cartes définitives. C'est tout ce que la `0.1.0` garde de l'Empire central
([D-47](../../../vision/decisions.md), 5 octobre 2026) : les six autres quartiers intra-muros, la
quête « Les enfants de Martpart » et le reste de la région partent à la
[`0.4.0`](../../v0.4.0/v0.3.1-capitale-intra-muros/README.md), après les systèmes ; la sauvegarde
et les outils de l'éditeur que cette version portait rejoignent la
[`0.2.0`](../../v0.2.0/README.md).

La version ne se tague pas à part : elle se clôt à la recette de la `0.1.0`
([LOT-198](../v0.1.0-demo-finale/lots/LOT-198-recette-et-version-0-1-0.md)), quand « Des pommes
pour l'arène » se rejoue sur les cartes définitives, sans changer une ligne de la quête.

## Les trois lieux

| Lieu | Décor | Carte | PNJ |
|---|---|---|---|
| Arena of Fate — le sable, les vestiaires et la prison | [LOT-106](lots/LOT-106-assets-hd-arena-of-fate.md) | [LOT-107](lots/LOT-107-carte-arena-of-fate.md) | [LOT-113](lots/LOT-113-pnj-arena-of-fate.md) |
| Arena of Fate — son donjon, les catacombes | [LOT-157](lots/LOT-157-donjon-catacombes-du-colisee.md) | (même lot) | (même lot que l'arène) |
| Arenarea | [LOT-147](lots/LOT-147-zone-arenarea-reprise.md) — les livraisons des `LOT-108` et `LOT-109`, **reprises** | (même lot) | [LOT-114](lots/LOT-114-pnj-arenarea.md) |
| Martpart | [LOT-110](lots/LOT-110-assets-hd-martpart.md) | [LOT-111](lots/LOT-111-carte-martpart.md) | [LOT-115](lots/LOT-115-pnj-martpart.md) |

Ce que ces lieux partagent est au kit commun de la Capitale, repris en maillages
([LOT-151](lots/LOT-151-kit-commun-intra-muros.md)).

## Où en sont les lots

- **L'Arena of Fate** : ses trois niveaux sont dans le moteur, en maillages et éclairés, depuis le
  4 octobre 2026 ([D-46](../../../vision/decisions.md), PR #178). Les trois fiches attendent la
  validation artistique de l'auteur, à la qualité finale que la `0.1.0` exige.
- **Arenarea**, **Martpart**, le **kit commun** et les **PNJ** : à faire. Leurs fiches ont été réécrites à la
  recette de la `0.0.2.5` pour commander des maillages et des modèles
  ([D-35](../../../vision/decisions.md)).

## La dette que la version solde

La `0.0.2.5` a laissé des images dans une scène 3D, avec une date de retrait : cette version. Le
tableau est dans [son README](../v0.0.2.5-passage-3d/README.md#la-dette-déclarée-pour-la-003), et
le [standard 3D](../../../standards/style-3d.md#7-les-images-tolérées) dit ce qui reste une image
sans date : les effets, les portraits, les jetons.

## Gabarit d'un lieu

Un lieu se livre en **trois** choses, dans cet ordre :

1. **Décor** — les dix familles du [standard](../../../standards/style-3d.md) passées en revue : ce
   qui vient du commun, ce qui est propre au lieu ; des **maillages**, installés sous
   `Regions/central-empire/…/<lieu>/Scene/`, le kit publié et verrouillé.
2. **PNJ** — nommés (à leur place), neutres (archétypes du commun, proportions du livre), hostiles ;
   un **modèle** par personnage au [standard des personnages](../../../standards/personnages-3d.md),
   portrait, jeton, fiche, placement.
3. **Carte** — jouable, dessinée dans l'éditeur, contrôlée par `--check` ; et l'image du lieu pour
   l'onglet « Carte ».
