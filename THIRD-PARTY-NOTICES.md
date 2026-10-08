# Mentions de tiers

Ce fichier recense les composants tiers redistribués avec JustAnotherRpgGame, ou dont il dépend au
build, avec leur licence. Il ne remplace pas les fichiers de licence livrés à côté des ressources
concernées : il y renvoie.

JustAnotherRpgGame est un **fan game non commercial**. Son code est sous **PolyForm Noncommercial
1.0.0** ([`LICENSE`](LICENSE)), ses contenus originaux sous **CC BY-NC-SA 4.0**
([`LICENSE-CONTENT`](LICENSE-CONTENT)).

> **À ne pas confondre.** Les en-têtes `SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0`
> marquent le **code du projet** — `Source/**/*.h`, `Source/**/*.cpp`, `scripts/*.py`, les
> `CMakeLists.txt` — et **rien d'autre**. Les images, les polices, les bibliothèques
> tierces et les univers dont le jeu s'inspire gardent chacun leur propre régime, listé ci-dessous.
> Voir un fichier `.cpp` marqué PolyForm ne dit **rien** de la licence d'un `.png` du même dépôt.

Ces mentions doivent aussi paraître **dans le jeu**, à l'écran *Crédits* : un utilisateur qui
n'ouvrira jamais ce fichier doit tout de même savoir que le jeu est construit avec Unreal Engine,
qu'il embarque des polices sous SIL OFL, et qu'il emprunte à Dungeons & Dragons et à Tanares. Le
texte de l'écran est dans [`credits.json`](Source/Elements/Credits/credits.json) ; l'écran lui-même
se refait sur le nouveau moteur (`LOT-1020`).

La licence des polices (SIL OFL) et celles des bibliothèques (MIT, BSD 3-Clause) sont permissives :
elles autorisent leur usage dans un projet sous une autre licence, à charge d'en conserver les
mentions. Le moteur a son propre contrat, décrit plus bas.

## Univers, règles et marques

Le jeu s'inspire de deux univers de jeu de rôle **qui ne lui appartiennent pas**. Aucune licence du
projet ne s'étend à eux, et le projet n'est **ni affilié, ni approuvé, ni soutenu** par leurs ayants
droit. Les livres ne sont pas versionnés (`Documentation/SourceBook/`, hors dépôt) ; les données
qui en sont extraites portent leur provenance dans un champ `"source"` imposé par schéma.

| Univers ou ouvrage | Ayant droit | Régime | Ce que le jeu en tire |
|---|---|---|---|
| **System Reference Document 5.1** | Wizards of the Coast LLC | **CC BY 4.0** — seule partie ouverte | mécaniques du d20 (`"source": "srd"`) |
| *Dungeons & Dragons*, *D&D* | Wizards of the Coast LLC | **marques déposées** | inspiration ; aucune marque dans le nom ni le logo du jeu |
| *Manuel des Joueurs*, *Guide du Maître*, *Manuel des Monstres* (5ᵉ éd., VF) | © Wizards of the Coast LLC, VF Black Book Éditions | tous droits réservés | règles, vocabulaire et bestiaire (`"source": "phb-fr"`) |
| *Basic Rules* en français | © Wizards of the Coast LLC, traduction communautaire [AideDD](https://www.aidedd.org/) | tous droits réservés | règles de base |
| *Player's Guide to Tanares*, *Tanares Sourcebook*, feuilles de personnage, cartes VTT | © **Dragori Games, Inc.** | tous droits réservés ; « Tanares », « Penumbral Plane » et les noms réservés sont *Product Identity* | monde, régions, espèces, dialogues (`"source": "tanares"`) ; **aucune image** : les deux cartes du monde extraites ont été retirées (`LOT-94`), et [`illustrations.json`](Source/Elements/Assets/UI/illustrations.json) refuse cette provenance ; les cartes de l'écran « Carte » ([`Assets/Maps/`](Source/Elements/Assets/Maps/manifest.json)) sont **peintes par l'auteur** d'après la géographie de ce monde, sans lettrage, et aucune n'est une image du livre |

Attribution exigée par la CC BY 4.0 du SRD :

> This work includes material taken from the System Reference Document 5.1 (“SRD 5.1”) by Wizards of
> the Coast LLC and available at <https://dnd.wizards.com/resources/systems-reference-document>. The
> SRD 5.1 is licensed under the Creative Commons Attribution 4.0 International License available at
> <https://creativecommons.org/licenses/by/4.0/legalcode>.

**Pourquoi c'est tenable, et jusqu'où.** Le dépôt est public, le projet gratuit et non commercial ;
aucun livre ni texte extrait d'un livre n'y entre (`EX-CNT-023`), et aucun paquet du jeu n'est
diffusé. Ce statut ne vaut **pas** autorisation : la politique de *fan content* de Wizards of the
Coast exclut explicitement les jeux, même gratuits, et Dragori Games ne publie aucune politique
équivalente. Diffuser le jeu supposerait donc l'accord écrit de Dragori Games pour Tanares, et de
ne garder de D&D que le SRD. Un ayant droit qui demande le retrait d'un élément l'obtient.

## Bibliothèques

| Composant | Version | Licence | Mode | Redistribué ? |
|---|---|---|---|---|
| [Unreal Engine](https://www.unrealengine.com/) | 5.8 (`UNREAL_ENGINE_VERSION`, `ci.yml`) | **contrat de licence d'Unreal Engine** (EULA d'Epic Games) | Installé hors dépôt | Pas par ce dépôt ; un jeu empaqueté en embarque le code objet (voir plus bas) |
| [GoogleTest](https://github.com/google/googletest) | v1.15.2 | BSD 3-Clause | FetchContent (`CMakeLists.txt`) | Non — tests de Core seulement |
| [nlohmann/json](https://github.com/nlohmann/json) | v3.11.3 | MIT | En-tête unique vendu dans `Source/ThirdParty/nlohmann/`, avec sa licence | **Oui** — le fichier est dans le dépôt, et il est compilé dans le jeu |

Le **chargeur de maillages** (`core::readMeshFile`, `LOT-1003`) lit le format glTF 2.0 binaire
(`.glb`), spécification ouverte du Khronos Group, sans bibliothèque dédiée : l'enveloppe binaire est
lue par le code du projet, son bloc JSON par **nlohmann/json**, déjà lié. Dans le jeu, c'est le
moteur qui importe les maillages et leurs images (Interchange), par les scripts du dépôt.

`DirectX` ne figure pas ici : il provient du **Windows SDK** et relève de sa licence, comme tout
composant du système d'exploitation.

### Unreal Engine et son contrat de licence

Le jeu est construit avec **Unreal Engine 5** (décision D-48), sous le contrat de licence
d'Unreal Engine d'Epic Games. Ce que cela veut dire pour ce dépôt :

1. **Le moteur n'est pas dans le dépôt.** Ni ses sources ni ses binaires n'y sont suivis : il
   s'installe à part, et `scripts/build.ps1 -Unreal` vérifie sa version. Le dépôt ne porte que le
   code du jeu et les scripts qui pilotent le moteur.
2. **Les sorties du moteur** (`.uasset`, `.umap`) se régénèrent par script depuis les données du
   dépôt (D-52).
3. **Un jeu empaqueté embarque le code objet du moteur.** Les mentions que le contrat demande à un
   produit distribué (la marque Unreal® et le droit d'auteur d'Epic Games dans les crédits) sont
   **à relire sur le texte du contrat** au premier paquet (`LOT-1023`) : aucun paquet n'est
   produit avant.

## Ressources

Toutes les ressources tierces sont déjà créditées à l'endroit où elles vivent — ce tableau n'en est
que l'index.

| Type | Emplacement | Licence | Détail |
|---|---|---|---|
| Graphismes | `Source/Elements/Assets/` | aucune ressource tierce : images propres au projet | [`Assets/CREDITS.md`](Source/Elements/Assets/CREDITS.md) |
| Police *Cinzel* | `Source/Elements/Assets/Fonts/` | SIL Open Font License 1.1 | `Cinzel-LICENSE.txt` |
| Police *IM Fell English* | `Source/Elements/Assets/Fonts/` | SIL Open Font License 1.1 | `IMFellEnglish-LICENSE.txt` |
| Police *Pinyon Script* | `Source/Elements/Assets/Fonts/` | SIL Open Font License 1.1 | `PinyonScript-LICENSE.txt` |

La **SIL OFL** exige une attribution : les fichiers de licence doivent accompagner les polices
partout où elles sont redistribuées.

## Entretien

Ce fichier se met à jour **avec** la dépendance qu'il décrit, jamais après coup : ajouter une
bibliothèque ou une ressource tierce sans l'inscrire ici, c'est perdre l'information au moment où
elle est encore connue.
