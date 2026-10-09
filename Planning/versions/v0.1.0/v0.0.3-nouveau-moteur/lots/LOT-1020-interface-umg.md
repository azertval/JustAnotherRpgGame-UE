+++
id = "LOT-1020"
titre = "Les écrans et le HUD en UMG"
version = "0.0.3"
filiere = "interface"
statut = "en-cours"
taille = "L"
resume = "Tous les écrans du jeu à la charte v2 — HUD, Personnage, Équipement, Journal, Groupe, Carte, Options, menus, dialogues, combat, écrans de fin — existent sur le nouveau moteur, construits en C++, avec les mêmes images et les mêmes textes."
prerequis = ["LOT-1016"]
livrables = [
  "Les écrans en UMG construits par C++ (pas de Widget Blueprint) : HUD d'exploration, menu du mercenaire, Personnage, Équipement, Journal, Groupe à quatre, Carte (l'atlas illustré et ses zones cliquables, LOT du 7 octobre), Options, Nouvelle partie et choix du meneur (D-37), dialogues avec choix du locuteur (D-28) et jet en dialogue, interface de combat de groupe (LOT-140) en distance, écrans de fin (LOT-119), menu de débug F9.",
  "La charte v2 reprise telle quelle : parchemins, ornements, polices, portraits, jetons du kit `UI` ; les tailles aux quatre niveaux de l'échelle d'identité (23/14/10/8).",
  "La localisation : les textes du jeu extraits et chargés par le système de texte du moteur, depuis les mêmes fichiers de traduction ; `check_translations.py` rebranché.",
  "Les captures de référence des écrans (vingt aujourd'hui) refaites sur le nouveau moteur et comparées à tolérance en CI.",
  "Le manuel du joueur (`Documentation/Guide/Manuel/`) et ses captures régénérés.",
]
criteres = [
  "Chaque écran du cahier de test s'ouvre, se ferme et se parcourt au clavier et à la souris ; les tests d'interface passent.",
  "Un écran se compare à sa capture du moteur maison : même disposition, mêmes textes, mêmes images (jugement de l'auteur sur les vingt captures côte à côte).",
  "Aucun Widget Blueprint dans le projet ; `check_orphans.py` passe.",
  "Les textes en français et en anglais s'affichent depuis les fichiers de traduction existants.",
]
+++

## Pourquoi

L'interface Qt Quick tombe avec Qt. Les écrans eux-mêmes sont faits, validés et testés : ce lot
les refait sur le nouveau moteur sans en changer le dessin, pour que la recette compare écran à
écran.

## Périmètre

Dedans : tous les écrans, la charte, la localisation, les captures, le manuel.

Dehors, nommément :

- la refonte d'un écran : aucun écran ne change de dessin ici ; une demande passe par un lot ;
- l'aperçu de combat (LOT-1017), que ce lot habille sans le réécrire ;
- la manette, retirée le 2 octobre 2026.

## Conception

- **UMG par C++** : chaque écran est une classe qui construit son arbre de widgets ; les styles
  (images, polices, couleurs) viennent d'un fichier texte, pas d'un `.uasset` de style. Les images
  du kit `UI` s'importent par script, comme les maillages.
- **L'écran Carte** reprend l'atlas illustré et `map-interactions.json` : zones cliquables, voisins,
  bannières, recherche, favoris ; c'est le dernier écran livré sur l'ancien moteur, et le plus
  riche.
- **Les captures de référence** se comparent à tolérance par blocs ; le seuil de 24 par canal du
  moteur maison se remesure sous l'anticrénelage temporel.

## Risques et questions ouvertes

- **Le texte riche** (journal, dialogues) : le système de texte du moteur ne couvre pas tout ce que
  QML faisait ; les balises utilisées s'inventorient en ouvrant le lot.
- **Le volume** : quinze écrans, 149 fichiers QML derrière. Si le lot dépasse la semaine, il se
  redécoupe en exploration, fiche et groupe, combat et fins.

## Avancement — 9 octobre 2026

Le lot est ouvert sur la branche `lot/1020-interface-umg`, non livré : les trois parts de l'ordre
de livraison (exploration ; fiche et groupe ; combat et fins) ont chacune leurs écrans, et la
recette de l'image est à l'auteur.

### Ce qui est fait

**Le socle UMG en C++** (`Source/JustAnotherRpgGame/UI/`). `UJadgScreen` est la classe de base :
chaque écran construit son arbre d'UMG dans `Build`, avec le constructeur `FJadgUi` (textes,
pièces 9-patch, boutons, jauges, colonnes, canevas), et relit le jeu dans `Refresh` ; il n'a pas
d'état à lui. `UJadgButton` porte son geste en C++ (le clic, Entrée, `Activate` jouent la même
fonction) et le fleuron du kit quand il a le focus du clavier (`EX-IHM-071`). `AJadgHud` remplace
le HUD de canevas du LOT-1016 et devient le **gestionnaire** : le jeu (HUD d'exploration, ou
interface du combat dès qu'un combat est monté), la conversation (le dialogue, tant qu'il est
ouvert), et une **pile de pages** ; une page met le jeu en pause et prend le clavier, la dernière
refermée le rend à la scène ; le jeu ouvre lui-même la fin qu'un dialogue écrit
(`UJadgExploration::TakeEnding`) et la défaite. Chaque page a son pied « Retour » pour la souris.
Aucun Widget Blueprint, aucun asset de style.

**Le style en fichier texte** : `Source/Elements/Assets/UI/style.json`, lu par
`core::loadUiStyle` (`Core/Ui/UiStyle.h`, testé hors du moteur) — 24 couleurs (les rôles relevés
des LOT-66, 76, 87 et 140, tels que `Tokens.qml` les tenait), 6 polices, 6 tailles en pixels à
1080 lignes (58, 36, 24, 24, 18, 14), 3 écarts, 67 pièces du kit avec leurs marges 9-patch et leurs
états (le cahier des assets du LOT-87). `UJadgStyle` en fait des pinceaux et des polices ; une pièce
absente retombe sur un aplat des jetons cerclé d'or (`EX-IHM-075`), une police absente sur celle du
moteur (`EX-IHM-052`). L'échelle d'UMG (côté le plus court, 1 à 1080 lignes) et les polices à 72
points par pouce (une taille vaut des pixels) tiennent le facteur réel de la charte v2.

**L'import par script** : `scripts/assetsGeneration/import_ui_unreal.py` importe les 250 images du
manifeste `illustrations.json` sous `/Game/UI/Kit/` (texture d'interface, sans mipmaps), vérifie
leur empreinte et la garde sur l'asset ; rejoué sans changement : « 0 importé(s), 250 à jour ».
Les six polices de `style.json` deviennent `/Game/UI/Fonts/` par le commandlet `JadgImportFonts` ;
rejoué : « 0 écrite(s), 6 à jour ». Les deux tournent à chaque `build.ps1 -Unreal`. `awaiting.json`
ne nomme plus les polices ni `illustrations.json` : ils ont leur lecteur.

**Les écrans** — tous ceux de la fiche :

| Écran | Classe | Ouvert par |
|---|---|---|
| HUD d'exploration : lieu, heure et cadran du jour, carte, groupe (portraits, noms, points de vie, meneur en or), écrans, annonce, invite, rencontre | `UJadgHudScreen` | toujours, hors combat |
| Dialogue : portrait et nom de qui parle, réplique, jet joué, réponses au clic ou au chiffre, **qui parle pour le groupe** (D-28) | `UJadgDialogueScreen` | une conversation ouverte |
| Interface du combat : round et ordre d'initiative, cible et circonstances, combattant actif et ses mètres, attaque et capacités en cases cliquables, fin du tour, refus, issue, historique | `UJadgCombatScreen` | un combat monté |
| Menu du titre : continuer, nouvelle partie, options, quitter | `UJadgTitleScreen` | le lancement d'une partie jouée |
| Menu du mercenaire : reprendre, options, retour au titre, quitter | `UJadgPauseScreen` | Échap, « Menu » |
| Options : langue ; définition, plein écran, rendu, ombres ; volume ; par défaut, annuler, appliquer (enregistré dans le fichier du poste) | `UJadgOptionsScreen` | le titre, le menu, le combat |
| Nouvelle partie et choix du meneur (D-37) | `UJadgPartyScreen` | « Nouvelle partie » |
| Groupe à quatre : ordre de marche, choisir, mener, avancer, reculer, fiche | `UJadgPartyScreen` | G, « Groupe » |
| Personnage : caractéristiques autour du portrait, valeurs dérivées, identité, points de vie, expérience, signature, compétences | `UJadgCharacterScreen` | P, « Personnage » |
| Équipement : ce qui est porté, le sac, la charge, la bourse, l'objet choisi | `UJadgEquipmentScreen` | I, « Équipement » |
| Journal : quêtes commencées et leur état, étapes de la quête choisie | `UJadgJournalScreen` | J, « Journal » |
| Carte : l'atlas illustré, ses lieux cliquables par leur bannière, ouvrir, remonter, voisins, recherche, favoris | `UJadgMapScreen` | M, « Carte » |
| Fin de la démonstration ; défaite | `UJadgEndScreen` | le dialogue final ; un combat perdu |
| Débogage : carte, case, étage, heure, rencontre, cadence, images du kit ; régler l'heure | `UJadgDebugScreen` | F9 |

Les commandes des écrans entrent dans `Config/DefaultGame.ini` (`Menu`, `Party`, `Sheet`,
`Inventory`, `Journal`, `Map`, `Debug`) ; en dialogue, `NextLeader` (Tab) donne la parole au
suivant. Core et le moteur gagnent ce que les écrans lisent : la langue dans les options
(`interface.language`, `core::writeGameOptions` pour enregistrer), les vues de la fiche, de
l'inventaire et du journal, la voix d'un dialogue, l'ordre de marche, la partie neuve
(`UJadgExploration`), l'issue d'un combat (`AJadgCombat::OutcomeCode`), les lieux de la carte
(`core::loadMapInteractions`).

**La localisation — le format retenu.** Le catalogue est le **`.lang` par clé**, un fichier par
langue (`fr.lang`, `en.lang`) : une paire `clé = valeur` par ligne, trous `%1` à `%9`. Core le lit
(`core::parseTextCatalog`, `Core/Ui/TextCatalog.h`) ; le moteur en fait une **table de chaînes**
par langue (`Jadg.fr`, `Jadg.en`) et les écrans prennent leurs textes en `FText` par
`FText::FromStringTable`, leurs trous par `FText::Format` (`core::toEngineFormat` réécrit `%1` en
`{0}`). Le catalogue Qt Linguist `jadg_en.ts` est retiré (D-32) : ses libellés sont repris par clé
(158 clés nouvelles dans chaque langue, 278 en tout) ; `check_translations.py` contrôle désormais
les deux `.lang` et les clés écrites dans le code ; `test_dialogue.cpp` revient dans les tests de
Core. Aucune balise de texte riche n'est employée par les textes du jeu : l'inventaire est vide.

**Le tour des écrans** (`AJadgScreensTour`, `build.ps1 -Unreal -Ecrans`) : dans le jeu lancé hors
écran, sur les étals, chaque page s'ouvre par la touche du jeu injectée dans le contrôleur, est
capturée interface comprise, voit son focus déplacé par une flèche injectée dans Slate, puis se
ferme par Échap injecté ; les gestes se jouent par des **clics injectés** au centre des boutons
(choisir et mener au groupe, la réponse du dialogue, un lieu et « Ouvrir » sur la carte,
« Options », l'onglet, la langue suivante, « Appliquer », « Nouvelle partie ») et sont jugés à leur
effet ; Tab donne la parole au suivant ; le jeu passe en anglais par l'écran Options et rend au
poste son fichier d'options. Sur l'arène, la rencontre `arene-bandits` est figée au tour du joueur
et son interface capturée. 24 captures, comparées à tolérance à
`Source/Test/Fixtures/Captures/ecrans-1020/` ; copies en JPEG dans
`annexes/LOT-1020/captures/`.

**Les tests du moteur** `Jadg.Interface.Style`, `.Textes`, `.Ecrans` (chaque écran se construit
sous l'instance du jeu, montre son titre, a ses boutons, une page prend Échap et a un bouton à
focaliser, un écran posé sur le jeu laisse Échap au jeu), `.Gestes` (« Mener », la voix d'un
dialogue, la réponse au bouton, la fiche en français puis en anglais). Tests de Core :
`TextCatalogTest`, `UiStyleTest`, `MapInteractionsTest`, la langue des options.

**Les documents** : le manuel du joueur réécrit (`Documentation/Guide/Manuel/README.md`, dix
captures du tour), `controles.md` sur les commandes réelles, `interface-ihm.md` (ce qui vaut, ce qui
est retiré au LOT-1020), le guide des données (la localisation), les guides du combat et de
l'exploration, `PASSATION.md`, le CHANGELOG.

### Les décisions de réalisation

- **Le « menu du mercenaire » est le menu de pause** de l'ancien jeu (`PauseForm`, « Menu » du
  HUD) ; le menu principal est le menu du titre, ouvert au lancement d'une partie jouée (jamais
  sous un automate : parcours, captures, tour). Les entrées inopérantes de l'ancien titre
  (« Charger une partie », « Crédits ») ne sont pas reprises (`EX-IHM-072`).
- **Les tailles** sont celles que `Tokens.qml` écrivait en pixels à 1080 lignes (58, 36, 24, 18,
  14). L'échelle « 23/14/10/8 » de la fiche ne se trouve ni dans le corpus, ni dans les fiches du
  LOT-87, ni dans `Tokens.qml` : elle n'est pas appliquée (question 1).
- **Les polices** passent par un commandlet : l'importeur de polices du moteur
  (`FontFileImportFactory`) demande une fenêtre et s'arrête sur une assertion en commandlet
  (relevé du 9 octobre 2026).
- **Les portraits de PNJ et les illustrations de la carte** se lisent dans leur fichier au premier
  affichage, comme le HUD du LOT-1016 lisait les portraits : ce sont des œuvres du kit
  (`Assets/Maps`, les figurines), pas des pièces d'interface ; rien n'en est importé.
- **Une page met le jeu en pause** (l'ancien jeu arrêtait le héros) : une seule règle, portée par
  le gestionnaire (`EX-IHM-091`).
- **Les captures des parcours** (LOT-1016, LOT-1017) et du socle restent prises sans l'interface
  d'UMG, comme avant : leur référence ne change pas ; seules celles du tour des écrans la portent.

### Ce qui se mesure

| Mesure | Valeur |
|---|---|
| Seuil des captures des écrans | tolérance 12 niveaux sur 255, 0,25 % des blocs ; relevé sur deux tours : pages au pire 2,11, HUD 0,82 (midi) et 5,43 (22 h), débogage 11,99 sur les blocs de sa cadence |
| Import du kit rejoué | 0 image réimportée, 250 à jour ; 0 police réécrite, 6 à jour |
| Textes | 278 clés par langue, 86 nommées en dur dans le code et contrôlées |

### Ce qui se vérifie (9 octobre 2026, RTX 4060 Ti, Unreal Engine 5.8.3)

| Commande | Relevé |
|---|---|
| `powershell scripts/build.ps1` | **702 tests de Core, 100 % passés** (`TextCatalogTest`, `UiStyleTest`, `MapInteractionsTest`, la langue des options ; `test_dialogue.cpp` recompilé) |
| `powershell scripts/build.ps1 -Unreal` | code 0, 0 avertissement de compilation : import de l'interface (250 images à jour, 6 polices à jour), `JadgContentCheck`, **24 tests du moteur passés** (dont les 4 `Jadg.Interface.*`), cartes contrôlées, captures du socle à leur référence (pire bloc 1,55) |
| `powershell scripts/build.ps1 -Unreal -Ecrans` | code 0 : le tour des écrans et celui du combat, 24 captures **toutes à leur référence** (pires blocs : HUD à 22 h 7,09, menu 4,07, combat 3,04, débogage 2,54, pages ≤ 1,11) |
| `powershell scripts/build.ps1 -Unreal -Parcours` | code 0 : la quête rendue à 53,0 s ; la fin de la démonstration ne s'ouvre pas sous un automate (premier passage bloqué par sa pause, corrigé) |
| `powershell scripts/build.ps1 -Unreal -ParcoursCombat -Seed 2` | code 0 : victoire, retour au parvis à 127,3 s, le meneur à sa case, `encounter/arene-bandits/won` posé |
| `scripts/check.py --sans-hooks`, lints, ruff, clang-format, pytest | voir le relevé de la PR : pytest 245 passés, `check_translations` 278 clés, `check_orphans` vert, cahier régénéré |

### Comparaison avec l'ancien jeu — à juger par l'auteur à la recette

Le dépôt ne garde que **neuf** des vingt captures de l'ancien jeu (`Documentation/Guide/captures/`) ;
les onze autres sont restées dans l'ancien dépôt. Sept ont leur écran ici et sont mises côte à côte
dans `annexes/LOT-1020/captures/cote-a-cote/` (l'ancienne à gauche, 1280 × 720 ; la nouvelle à
droite, réduite de 1920 × 1080) : `hud-1200` (vue de jeu), `dialogue`, `personnage` (fiche),
`equipement` (inventaire), `options`, `combat` (HUD de combat), `carte` (carte du monde). Deux n'en
ont pas : la galerie d'assets (un outil de l'ancien jeu, hors de la fiche) et l'écran des
compétences et sorts (voir les écarts). Même disposition, mêmes textes et mêmes images : c'est le
jugement de l'auteur, que le lot ne prononce pas.

### Les critères

| Critère | État |
|---|---|
| Chaque écran du cahier de test s'ouvre, se ferme et se parcourt au clavier et à la souris ; les tests d'interface passent | **tenu** : le tour des écrans ouvre chaque page par sa touche, y déplace le focus, la ferme par Échap, et joue ses gestes par des clics injectés ; `Jadg.Interface.*` passent. Le cahier de test de l'ancien jeu décrit encore des écrans QML (LOT-1023) |
| Un écran se compare à sa capture du moteur maison : même disposition, mêmes textes, mêmes images | **à juger par l'auteur** : sept comparaisons côte à côte sur les neuf captures du dépôt |
| Aucun Widget Blueprint dans le projet ; `check_orphans.py` passe | **tenu** : aucun `.uasset` de widget ; `/Game/UI/Kit` et `/Game/UI/Fonts` sont cités par `import_ui_unreal.py` |
| Les textes en français et en anglais s'affichent depuis les fichiers de traduction existants | **tenu** : `fr.lang` et `en.lang` en tables de chaînes ; captures `hud-en`, `menu-en`, `personnage-en` ; `Jadg.Interface.Gestes` |

| Livrable | État |
|---|---|
| Les écrans en UMG construits par C++ | **tenu** pour les quinze écrans de la fiche ; voir les écarts pour ce qu'ils n'ont pas de l'ancien jeu |
| La charte v2 telle quelle, tailles de l'échelle d'identité | **partiel** : parchemins, ornements, polices, jetons, médaillons du kit ; les tailles sont celles de `Tokens.qml`, pas « 23/14/10/8 » (question 1) ; pas de portrait des héros (question 2) |
| La localisation par le système de texte du moteur, `check_translations.py` rebranché | **tenu** |
| Les captures de référence des écrans, comparées à tolérance | **tenu** sur le poste : 24 captures ; la CI n'a pas le moteur (D-61) |
| Le manuel du joueur et ses captures | **tenu** : réécrit, court, dix captures |

### Ce qui s'écarte de la fiche

- **Vingt captures attendues, vingt-quatre faites, neuf comparables** : la fiche compte vingt
  captures du moteur maison ; neuf seulement sont dans ce dépôt.
- **Des écrans de l'ancien jeu ne sont pas refaits**, parce que la fiche ne les nomme pas :
  compétences et sorts (`SkillsForm`), marchand, équipe de mercenaires (`CompanyForm`), crédits,
  galerie d'assets.
- **Le dialogue** n'a pas le champ « Attitude » (la donnée n'est pas exposée par Core à
  l'interface) ; la parole passe au suivant par Tab, pas au précédent par Maj+Tab : la commande
  n'a pas de touche à modificateur.
- **Les portraits des héros** : aucun n'existe dans le nouveau moteur (les héros sont des
  MetaHuman, LOT-1015) ; les médaillons montrent le buste vide du kit.
- **L'équipement se lit, il ne se change pas** : « Équiper » et « Jeter » de l'ancien écran ne sont
  pas repris ; les onglets de catégories non plus.
- **La carte** : les lieux se cliquent par leur bannière (le rectangle `label`), pas par leur
  contour ; les voisins sont ceux de l'atlas (régions) et les lieux qui débordent d'une illustration
  voisine ; les favoris vivent le temps de la partie ; le zoom de l'ancien écran n'est pas repris ;
  le champ de recherche a le style du moteur.
- **Le HUD** : un nom trop long pour sa carte de groupe est coupé à ses deux bords.
- **« Commencer »** (la nouvelle partie lancée) n'est joué ni par le tour ni par un test : il
  relit la partie et rouvre la carte.
- **Le combat** : pas d'onglets « Toutes / Actions / Sorts », pas de « Détails du calcul » ; les
  capacités ont une icône commune.
- **Les noms des données** (objets, armes, lieux de l'atlas) restent ceux de leurs fichiers : ils
  ne passent pas par les catalogues.

### Ce qui reste au lot

- Le jugement de l'auteur sur les comparaisons côte à côte, et les retouches qui en sortiront.
- Les écarts ci-dessus que l'auteur voudra au lot plutôt qu'à un lot suivant.
- Le cahier de test : ses cas de recette manuelle des écrans décrivent l'ancien jeu (LOT-1023).

### Questions pour l'auteur

1. **L'échelle « 23/14/10/8 »** de la fiche : d'où vient-elle ? Le dépôt ne connaît que celle de
   `Tokens.qml` (58, 36, 24, 18, 14 pixels à 1080 lignes), appliquée ici.
2. **Les portraits des héros** : une capture de chaque MetaHuman par script (une caméra de
   portrait), ou des portraits peints (D-30 les gardait peints) ?
3. **Les écrans de l'ancien jeu hors de la fiche** (compétences et sorts, marchand, équipe,
   crédits) : à un lot suivant, ou à celui-ci ?
4. **La pause sous une page** : le jeu s'arrête dès qu'une page s'ouvre ; l'ancien jeu arrêtait
   seulement le héros. Garder la pause ?
