# Contrôles & entrées

> Statut : **livré** pour l'exploration, les écrans et le combat, au clavier et à la souris,
> sur le nouveau moteur (LOT-1016, LOT-1017, LOT-1020).
> Dépend de [`gameplay.md`](gameplay.md).

## 1. Périphériques
- **EX-CTRL-001** — Le jeu doit être jouable **entièrement au clavier**.

## 2. Commandes du jeu

Les entrées sont traduites en **commandes nommées** : un écran ou le jeu réagit à « marcher »,
« interagir » ou « fermer », jamais à une touche en particulier. Les touches ci-dessous sont celles
que livre `Config/DefaultGame.ini` (`UJadgControls`, LOT-1016, LOT-1017, LOT-1020) ; elles se
changent dans ce fichier texte.

| Commande | Touches livrées | Effet |
|----------|-----------------|-------|
| `Walk` | clic gauche | le groupe marche au point cliqué ; sur un personnage, le meneur va lui parler ; en combat, la cible ou la destination |
| `Interact` (`EX-CTRL-022`) | F | sollicite ce que le meneur a à portée ; en dialogue, « continuer » |
| `NextLeader` (`EX-EXP-014`) | Tab | passe la main au suivant du groupe ; en dialogue, la parole au suivant (D-28) |
| `Recenter` | Début | ramène la caméra sur le meneur, ou sur le combattant actif |
| `Turn`, `Tilt` | A / E, R / V | tourne, incline la caméra |
| `Look` | C, clic droit tenu | la souris tourne et incline la caméra |
| `Zoom` | molette | rapproche ou éloigne la caméra |
| `PanForward`, `PanRight` | Z / S, D / Q, flèches | déplace le point visé |
| `Choice1` … `Choice6` | 1 … 6 | la réponse de ce rang, en dialogue ; la capacité de ce rang, en combat |
| `Attack`, `Capacity`, `EndTurn` | X, W, Espace | en combat : attaquer la cible, lancer la capacité choisie, finir le tour |
| `Menu` | Échap | ouvre ou ferme le menu du mercenaire |
| `Party`, `Sheet`, `Inventory`, `Journal`, `Map` | G, P, I, J, M | ouvre ou ferme le groupe, la fiche, l'équipement, le journal, la carte |
| `Debug` | F9 | ouvre ou ferme le menu de débogage |

Dans un **écran** (une page qui couvre le jeu), le clavier est à l'écran : les flèches et Tab
passent d'un bouton à l'autre (le bouton focalisé porte la marque du kit, `EX-IHM-071`), Entrée et
Espace valident, Échap ferme ; tout bouton se clique aussi.

- **EX-CTRL-010** — Chaque commande du jeu est une **commande nommée**, dissociée de la touche
  physique qui la déclenche : plusieurs touches peuvent mener à la même intention de jeu.
- **EX-CTRL-022** — **Interagir** doit être une commande dédiée (`Interact`, F)
  qui déclenche l'entité à portée du héros — à moins de 1,5 case, celle qu'il regarde d'abord —
  dialogue, coffre, portail (`EX-EXP-004`).

Les événements Qt sont traduits en intentions avant d'atteindre `Core`, qui ne connaît aucun
périphérique physique.

## 3. Réactivité
- **EX-CTRL-020** — La latence entre une entrée et son effet ne doit pas
  dépasser **un pas** de simulation : une touche enfoncée est lue au pas suivant, jamais perdue
  entre deux.

## Exigences retirées {#ctrl-retirees}

> Ancres conservées, jamais renumérotées : les lots livrés s'y réfèrent.

- **EX-CTRL-013** *(retirée au `LOT-88`)* — commande de ruée (dash) : le jeu n'a
  pas de ruée.
- **EX-CTRL-012** *(retirée au `LOT-1020`)* — raccourcis de l'éditeur Qt reconfigurables par
  fichier : l'éditeur de cartes Qt n'est pas dans ce dépôt (D-59) ; les commandes du jeu, elles,
  se règlent dans `Config/DefaultGame.ini`.
- **EX-CTRL-002** *(retirée le 2 octobre 2026)* — prise en charge de la manette XInput.
- **EX-CTRL-011** *(retirée le 2 octobre 2026)* — échantillonnage des fronts d'un bouton de manette.
- **EX-CTRL-021** *(retirée au `LOT-88`)* — échantillonnage des entrées par la
  boucle d'une fenêtre native : Qt distribue désormais les événements.

## Traçabilité
Les commandes du jeu sont lues par `UJadgControls` (`Player/JadgControls.h`) et deviennent des
actions d'Enhanced Input créées par le contrôleur du joueur (`AJadgPlayerController`), sans asset ;
les écrans prennent le clavier par Slate (`UJadgScreen`, LOT-1020). `Core` ne reçoit que des
intentions (`core::ExplorationIntent`), sans dépendance inverse. Les tests `Jadg.Exploration.Commandes`
et le tour des écrans (`build.ps1 -Unreal -Ecrans`) jouent ces touches.
Voir [`exigences-non-fonctionnelles.md`](exigences-non-fonctionnelles.md) pour l'architecture.
