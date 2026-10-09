# Core · Combat

Tests unitaires — **201 cas** (28 bloquants, 103 critiques, 70 majeurs). [Retour à la synthèse](README.md).

## Ce que cette page couvre

| Fichier de test | Cas | Bloquant | Critique | Majeur | Mineur |
|---|---|---|---|---|---|
| [`test_action_economy.cpp`](#test-action-economycpp) | 3 | - | 1 | 2 | - |
| [`test_ai_spells.cpp`](#test-ai-spellscpp) | 6 | - | 4 | 2 | - |
| [`test_area_of_effect.cpp`](#test-area-of-effectcpp) | 3 | 1 | 1 | 1 | - |
| [`test_arena.cpp`](#test-arenacpp) | 8 | 2 | 5 | 1 | - |
| [`test_attack.cpp`](#test-attackcpp) | 12 | 4 | 5 | 3 | - |
| [`test_class_brawler.cpp`](#test-class-brawlercpp) | 8 | - | 5 | 3 | - |
| [`test_class_in_arena.cpp`](#test-class-in-arenacpp) | 4 | - | 4 | - | - |
| [`test_class_mage.cpp`](#test-class-magecpp) | 11 | - | 9 | 2 | - |
| [`test_class_priest.cpp`](#test-class-priestcpp) | 6 | - | 6 | - | - |
| [`test_class_scoundrel.cpp`](#test-class-scoundrelcpp) | 7 | - | 5 | 2 | - |
| [`test_combat_preview.cpp`](#test-combat-previewcpp) | 3 | 1 | 2 | - | - |
| [`test_combat_space.cpp`](#test-combat-spacecpp) | 13 | - | - | 13 | - |
| [`test_combat_state.cpp`](#test-combat-statecpp) | 29 | 11 | 12 | 6 | - |
| [`test_damage.cpp`](#test-damagecpp) | 7 | 3 | 3 | 1 | - |
| [`test_death_and_dying.cpp`](#test-death-and-dyingcpp) | 13 | - | 9 | 4 | - |
| [`test_encounter.cpp`](#test-encountercpp) | 12 | - | 7 | 5 | - |
| [`test_encounter_difficulty.cpp`](#test-encounter-difficultycpp) | 3 | - | 3 | - | - |
| [`test_enemy_ai.cpp`](#test-enemy-aicpp) | 12 | 5 | 7 | - | - |
| [`test_map_encounter.cpp`](#test-map-encountercpp) | 4 | - | 3 | 1 | - |
| [`test_party_deployment.cpp`](#test-party-deploymentcpp) | 6 | - | 4 | 2 | - |
| [`test_serie_de_l_arene.cpp`](#test-serie-de-l-arenecpp) | 3 | - | 3 | - | - |
| [`test_simulated_space.cpp`](#test-simulated-spacecpp) | 15 | - | - | 15 | - |
| [`test_tactical_terrain.cpp`](#test-tactical-terraincpp) | 10 | - | 4 | 6 | - |
| [`test_turn_order.cpp`](#test-turn-ordercpp) | 3 | 1 | 1 | 1 | - |

## Exigences vérifiées par cette page

Chaque exigence citée par un cas de cette page, avec les cas qui la citent ; la [matrice de traçabilité](couverture-exigences.md) les rassemble toutes.

| Exigence | Cas |
|---|---|
| `EX-CBT-031` | [`DamageTest.LeCritiqueDoubleLesDesPasLeModificateur`](#damagetestlecritiquedoublelesdespaslemodificateur) |
| `EX-CBT-040` | [`DeathAndDyingTest.TroisEchecsTuent`](#deathanddyingtesttroisechecstuent), [`DeathAndDyingTest.UnVingtReleveUnUnCompteDouble`](#deathanddyingtestunvingtreleveununcomptedouble), [`DeathAndDyingTest.LesDegatsATerreEtLaMortInstantanee`](#deathanddyingtestlesdegatsaterreetlamortinstantanee), [`DeathAndDyingTest.LeJetSeFaitASaPlaceEtUnVingtRejoue`](#deathanddyingtestlejetsefaitasaplaceetunvingtrejoue), [`DeathAndDyingTest.LeJetContreLaMortSeJetteDansLArene`](#deathanddyingtestlejetcontrelamortsejettedanslarene), [`DeathAndDyingTest.FrapperUnInconscientAuContactEstCritique`](#deathanddyingtestfrapperuninconscientaucontactestcritique) |
| `EX-CBT-041` | [`DeathAndDyingTest.UnVingtReleveUnUnCompteDouble`](#deathanddyingtestunvingtreleveununcomptedouble), [`DeathAndDyingTest.UnAllieATerreSeReleveParSoinEtRejoue`](#deathanddyingtestunallieaterresereleveparsoinetrejoue) |
| `EX-CBT-050` | [`DeathAndDyingTest.LIaAcheveOuEpargneSelonSonProfil`](#deathanddyingtestliaacheveouepargneselonsonprofil), [`EnemyAiTest.LIaNeLitQueLEtatEnsanglante`](#enemyaitestlianelitqueletatensanglante) |
| `EX-REG-003` | [`AttackTest.ChaqueJetProduitUneEntreeDeJournalComplete`](#attacktestchaquejetproduituneentreedejournalcomplete) |

## test_action_economy.cpp

### ActionEconomyTest.ChaqueRessourceUneFoisParTour

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_action_economy.cpp:22`

Action, action bonus et reaction se depensent une fois ; le deplacement se depense en plusieurs fois sans jamais revenir dans le tour.

**Étapes**

1. Economie standard a 6 cases.
2. Depenser deux fois l'action, l'action bonus et la reaction.
3. Depenser 2 puis 4 cases, puis 1.
4. Depenser 0, une ressource inconnue, puis restaurer.

**Résultat attendu**

- Vérifie que `economie.spend(ressource)` est vrai.
- Vérifie que `economie.spend(ressource)` est faux.
- Vérifie que `economie.remaining(ressource)` vaut `0`.
- Vérifie que `economie.spend(core::MOVEMENT_RESOURCE, 2)` est vrai.
- Vérifie que `economie.spend(core::MOVEMENT_RESOURCE, 5)` est faux.
- Vérifie que `economie.remaining(core::MOVEMENT_RESOURCE)` vaut `4`.
- Vérifie que `economie.spend(core::MOVEMENT_RESOURCE, 4)` est vrai.
- Vérifie que `economie.spend(core::MOVEMENT_RESOURCE, 1)` est faux.
- Vérifie que `economie.spend(core::MOVEMENT_RESOURCE, 0)` est faux.
- Vérifie que `economie.spend("inconnue")` est faux.
- Vérifie que `economie.has("inconnue")` est faux.
- Vérifie que `economie.remaining(core::ACTION_RESOURCE)` vaut `1`.
- Vérifie que `economie.remaining(core::BONUS_ACTION_RESOURCE)` vaut `1`.
- Vérifie que `economie.remaining(core::REACTION_RESOURCE)` vaut `1`.
- Vérifie que `economie.remaining(core::MOVEMENT_RESOURCE)` vaut `6`.

### ActionEconomyTest.UneRessourceSeDeclareEtSOctroie

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_action_economy.cpp:61`

Une ressource nouvelle se declare sans rien casser, et un octroi ne dure que jusqu'au prochain debut de tour.

**Étapes**

1. Declarer « heroicAction » a 1 par tour.
2. Octroyer une reaction, puis une ressource inconnue.
3. Restaurer.

**Résultat attendu**

- Vérifie que `noms` vaut `(std::vector<std::string>{"action", "bonusAction", "reaction", "movement", "heroicAction"})`.
- Vérifie que `economie.spend("heroicAction")` est vrai.
- Vérifie que `economie.remaining(core::REACTION_RESOURCE)` vaut `2`.
- Vérifie que `economie.remaining("sursis")` vaut `2`.
- Vérifie que `economie.remaining(core::REACTION_RESOURCE)` vaut `1`.
- Vérifie que `economie.remaining("heroicAction")` vaut `1`.
- Vérifie que `economie.remaining("sursis")` vaut `0`.

### CombatCountersTest.LesPorteesSontSeparees

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_action_economy.cpp:95`

« Une fois par tour », « une fois par rencontre » et « immunise 24 heures » se comptent separement.

**Étapes**

1. Incrementer un meme compteur aux portees tour, rencontre et jour.
2. Vider la portee tour.
3. Immuniser un gobelin contre la presence d'un dragon pendant 24 h.

**Résultat attendu**

- Vérifie que `compteurs.increment(core::CounterScope::Turn, "moine", "posture")` vaut `1`.
- Vérifie que `compteurs.increment(core::CounterScope::Turn, "moine", "posture")` vaut `2`.
- Vérifie que `compteurs.value(core::CounterScope::Turn, "moine", "posture")` vaut `0`.
- Vérifie que `compteurs.value(core::CounterScope::Encounter, "moine", "posture")` vaut `1`.
- Vérifie que `compteurs.value(core::CounterScope::Day, "moine", "posture")` vaut `3`.
- Vérifie que `compteurs.value(core::CounterScope::Day, "gobelin", "posture")` vaut `0`.
- Vérifie que `immunites.isImmune("gobelin", "dragon-rouge", maintenant)` est vrai.
- Vérifie que `immunites.isImmune("gobelin", "dragon-bleu", maintenant)` est faux.
- Vérifie que `immunites.isImmune("ogre", "dragon-rouge", maintenant)` est faux.
- Vérifie que `immunites.isImmune("gobelin", "dragon-rouge", maintenant + core::IMMUNITY_DAY_SECONDS - 1)` est vrai.
- Vérifie que `immunites.isImmune("gobelin", "dragon-rouge", maintenant + core::IMMUNITY_DAY_SECONDS - 1)` est faux.

## test_ai_spells.cpp

### AiSpellsTest.LePriestReleveUnAllieATerre

*Critique · Unitaire · IA tactique* — `Source/Test/Unit/Core/Combat/test_ai_spells.cpp:83`

L'IA du Priest releve un allie tombe.

**Étapes**

1. Priest N1 en (1, 3), un allie en (3, 3) porte a 0 PV, un mannequin ennemi en (9, 6).
2. Jouer le tour du Priest par l'IA.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().find(CombatantId{2})->status` vaut `core::CombatantStatus::Down`.
- Vérifie que `core::playTurn(session, catalogue)` est vrai.
- Vérifie que `journalHas(session.journal(), "releve Allie")` est vrai.
- Vérifie que `session.combat().find(CombatantId{2})->status` vaut `core::CombatantStatus::Standing`.
- Vérifie que `lancersDe(session, "cure-wounds")` vaut `1`.

### AiSpellsTest.LePriestBenitUneFois

*Majeur · Unitaire · IA tactique* — `Source/Test/Unit/Core/Combat/test_ai_spells.cpp:115`

L'IA du Priest benit le groupe, une seule fois.

**Étapes**

1. Priest N1 en (1, 3), deux allies en (2, 3) et (1, 4), un mannequin ennemi en (11, 7).
2. Jouer le tour du Priest, finir les tours des autres, rejouer le Priest.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `core::playTurn(session, catalogue)` est vrai.
- Vérifie que `journalHas(session.journal(), "benit 3 allie(s)")` est vrai.
- Vérifie que `std::ranges::find(etats, core::CombatCondition::Blessed)` diffère de `etats.end()`.
- Vérifie que `std::ranges::find(etats, core::CombatCondition::Concentrating)` diffère de `etats.end()`.
- Vérifie que `lancersDe(session, "bless")` vaut `1`.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `core::playTurn(session, catalogue)` est vrai.
- Vérifie que `lancersDe(session, "bless")` vaut `1`.

### AiSpellsTest.LeMageLanceUnSortQuiBlesse

*Critique · Unitaire · IA tactique* — `Source/Test/Unit/Core/Combat/test_ai_spells.cpp:154`

L'IA du Mage lance un sort qui blesse.

**Étapes**

1. Mage N1 en (1, 3), un mannequin ennemi en (7, 3).
2. Jouer le tour du Mage.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `core::playTurn(session, catalogue)` est vrai.
- Vérifie que `journalHas(session.journal(), " : lance ")` est vrai.
- Vérifie que `journalHas(session.journal(), "blesse Mannequin")` est vrai.
- Vérifie que `session.combat().find(CombatantId{2})->profile.currentHitPoints` est strictement inférieur à `60`.

### AiSpellsTest.LaBouleDeFeuEpargneLesAllies

*Critique · Unitaire · IA tactique* — `Source/Test/Unit/Core/Combat/test_ai_spells.cpp:180`

L'IA du Mage epargne ses allies, et groupe ses cibles.

**Étapes**

1. Mage N5 en (1, 3) ; un ennemi en (7, 3) au contact d'un allie en (7, 4) ; jouer le tour.
2. Mage N5 en (1, 3) ; trois ennemis en (8, 3), (9, 3), (8, 4) ; jouer le tour.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `core::playTurn(session, catalogue)` est vrai.
- Vérifie que `lancersDe(session, "fireball")` vaut `avant`.
- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `core::playTurn(session, catalogue)` est vrai.
- Vérifie que `lancersDe(session, "fireball")` vaut `avant - 1`.

### AiSpellsTest.LeBrawlerFrappeDeuxFois

*Critique · Unitaire · IA tactique* — `Source/Test/Unit/Core/Combat/test_ai_spells.cpp:219`

L'IA du Brawler frappe deux fois au niveau 5.

**Étapes**

1. Brawler N5 en (1, 3), un mannequin de 200 PV au contact en (2, 3).
2. Jouer le tour du Brawler.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `core::playTurn(session, catalogue)` est vrai.
- Vérifie que `journalHas(session.journal(), "attaque supplementaire")` est vrai.

### AiSpellsTest.LArmeSpirituelleFrappeParLActionBonus

*Majeur · Unitaire · IA tactique* — `Source/Test/Unit/Core/Combat/test_ai_spells.cpp:244`

L'IA du Priest frappe de l'arme spirituelle par l'action bonus.

**Étapes**

1. Priest N3 en (1, 3), un mannequin de 200 PV en (5, 3).
2. Jouer le tour du Priest.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `core::playTurn(session, catalogue)` est vrai.
- Vérifie que `journalHas(session.journal(), "action bonus")` est vrai.
- Vérifie que `lancersDe(session, "spiritual-weapon")` vaut `avant - 1`.

## test_area_of_effect.cpp

### AreaOfEffectTest.ChaqueFormePrendLesVolumesQuiLaCroisent

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_area_of_effect.cpp:85`

Sphere, cylindre, cone, ligne et cube prennent chacun, parmi des combattants poses, exactement ceux dont le volume croise la forme : un bord suffit, le centre peut etre dehors ; la distance est euclidienne, en metres.

**Étapes**

1. Une sphere de 3 m en (9, 9) : un combattant a l'origine, un a 3,75 m (son bord a 3 m), un en diagonale a 3,54 m, un a 4 m, un sur un plateau de 4 m.
2. Un cylindre de 3 m de rayon et 6 m de haut au meme point.
3. Un cone de 4,50 m vers l'est : un dans l'axe, un dont le centre est hors du cone et le bord dedans, un au-dela de la pointe, un derriere l'origine.
4. Une ligne de 6 m sur 1,50 m vers l'est : dans l'axe, a 0,65 m du bord, a 1,25 m du bord, au-dela du bout.
5. Un cube de 3 m vers le nord : dedans, derriere la face d'origine, a 0,60 m du cote, au-dela.

**Résultat attendu**

- Vérifie que `boule->positionOf(CombatantId{5})->z` vaut `4.0F`, à `0.001F` près.
- Vérifie que `core::combatantsInArea(*boule, sphere)` vaut `ids({1, 2, 3})`.
- Vérifie que `core::combatantsInArea(*boule, cylindre)` vaut `ids({1, 2, 3, 5})`.
- Vérifie que `core::combatantsInArea(*souffle, cone)` vaut `ids({1, 2})`.
- Vérifie que `core::combatantsInArea(*eclair, ligne)` vaut `ids({1, 2})`.
- Vérifie que `core::combatantsInArea(*bloc, cube)` vaut `ids({1, 3})`.

### AreaOfEffectTest.LOrigineEtLesTailles

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_area_of_effect.cpp:149`

Une sphere posee au centre d'un combattant le prend ; un cone qui part du meme centre prend ce qui est devant, pas ce qui est derriere ni sur le cote ; un cone sans direction ne prend rien ; une taille de 1 m, qu'aucun nombre de cases n'ecrit, se joue telle quelle.

**Étapes**

1. Un combattant en (5, 5), un deuxieme a 1,60 m a l'est (son bord a 0,85 m), un troisieme a 1,90 m au sud (son bord a 1,15 m), un quatrieme a 1,80 m a l'ouest.
2. Une sphere de 1 m au centre du premier.
3. Un cone de 3 m vers l'est depuis le meme centre.
4. Un cone dont la direction est son origine.

**Résultat attendu**

- Vérifie que `core::combatantsInArea(*combat, sphere)` vaut `ids({1, 2})`.
- Vérifie que `contient(souffle, 2)` est vrai.
- Vérifie que `contient(souffle, 3)` est faux.
- Vérifie que `contient(souffle, 4)` est faux.
- Vérifie que `core::combatantsInArea(*combat, sansDirection).empty()` est vrai.

### AreaOfEffectTest.UnMurArreteLEffet

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_area_of_effect.cpp:184`

Une sphere posee devant un mur ne prend pas le combattant qu'aucune ligne droite ne relie a son origine ; un corps interpose ne protege pas ; une creature de grande taille dont le bord seul est dans la zone y est, une fois ; un corps a terre est pris.

**Étapes**

1. Une salle 7 × 7 barree d'un mur vertical sur cinq cases, en colonne 4.
2. Une sphere de 4,50 m au centre de la case (3, 3), qui deborde derriere le mur.
3. Un allie en (2, 3), un gobelin derriere le mur en (5, 3), un ogre de taille G sur les cases (0, 5) a (1, 6), un pretre a terre en (1, 3) derriere l'allie, un rat hors de portee en (0, 0).

**Résultat attendu**

- Vérifie que `combat.combatants().size()` vaut `5U`.
- Vérifie que `combat.positionOf(id).has_value()` est vrai.
- Vérifie que `combat.find(CombatantId{4})->status` vaut `core::CombatantStatus::Down`.
- Vérifie que `core::shapeHits(boule, *combat.volumeOf(CombatantId{2}))` est vrai.
- Vérifie que `core::combatantsInArea(combat, boule)` vaut `ids({1, 3, 4})`.

## test_arena.cpp

### ArenaTest.LesPointsDEntreeSeLisentDeLaCarte

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_arena.cpp:172`

Les points d'entree de l'arene se lisent de la carte, ranges par camp puis par rang.

**Étapes**

1. Une piste avec trois entrees par camp, declarees dans le desordre, et une entree sans camp.
2. Lire les points d'entree.

**Résultat attendu**

- Vérifie que `entrees.size()` vaut `6U`.
- Vérifie que `entrees` vaut `attendu`.

### ArenaTest.LaCarteDEssaiAccueilleLesDeuxCamps

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_arena.cpp:193`

La carte d'essai du donjon se charge et ses points d'entree accueillent les deux camps.

**Étapes**

1. Charger la carte d'essai `Levels/donjon.json`.
2. Lire ses points d'entree et verifier qu'une creature de taille M tient au centre de chacun, dans l'espace que la carte donne.

**Résultat attendu**

- Vérifie que `carte.ok()` est vrai.
- Vérifie que `espace.isClear( core::volumeOf(core::tileCenter(entree.position), core::CreatureSize::Medium), core::Locomotion::Walk)` est vrai.
- Vérifie que `allies` est supérieur ou égal à `4`.
- Vérifie que `ennemis` est supérieur ou égal à `4`.

### ArenaTest.LeMontagePlaceAuxEntreesEtRefuseEnLeDisant

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_arena.cpp:224`

Le montage pose chaque combattant au centre du prochain point d'entree libre de son camp, ou de la case demandee, et nomme chaque refus.

**Étapes**

1. Quatre allies sur trois entrees, un ennemi a une case demandee dans le pilier, un ennemi libre.
2. Monter avec la Marque Heroique, puis sans.

**Résultat attendu**

- Vérifie que `montage.allies` vaut `(std::vector<CombatantId>{CombatantId{1}, CombatantId{2}, CombatantId{3}})`.
- Vérifie que `montage.enemies` vaut `(std::vector<CombatantId>{CombatantId{4}})`.
- Vérifie que `montage.refusals.size()` vaut `2U`.
- Vérifie que `montage.refusals[0].who` vaut `"Allie3"`.
- Vérifie que `montage.refusals[0].placement` vaut `core::PlacementResult::OutOfBounds`.
- Vérifie que `montage.refusals[1].who` vaut `"Golem"`.
- Vérifie que `montage.refusals[1].placement` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `memePlace(session.combat().positionOf(CombatantId{1}), tile(2, 3))` est vrai.
- Vérifie que `memePlace(session.combat().positionOf(CombatantId{2}), tile(2, 2))` est vrai.
- Vérifie que `memePlace(session.combat().positionOf(CombatantId{4}), tile(9, 3))` est vrai.
- Vérifie que `session.combat().economy(CombatantId{1})->has(core::HEROIC_ACTION_RESOURCE)` est vrai.
- Vérifie que `session.attacks(CombatantId{4})` diffère de `nullptr`.
- Vérifie que `session.attacks(CombatantId{9})` vaut `nullptr`.
- Vérifie que `session.combat().find(CombatantId{4})->profile.armorClass` vaut `13`.
- Vérifie que `session.combat().economy(CombatantId{1})->has(core::HEROIC_ACTION_RESOURCE)` est faux.

### ArenaTest.LAttaqueSeRefuseEtSeResout

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_arena.cpp:271`

L'action attaquer de l'arene refuse hors tour actif, contre un allie ou un inconnu, hors allonge, sans attaque ou sans action ; a portee elle jette le d20 contre la classe d'armure du profil et l'ecrit au journal.

**Étapes**

1. Heroine en (2,3), compagnon en (2,2), gobelin en (3,3) a la CA 30, un second gobelin en (8,3), graine 3.
2. Attaquer avant le debut ; le compagnon ; un inconnu ; le gobelin lointain ; avec une attaque inexistante.
3. Attaquer le gobelin voisin, puis encore.

**Résultat attendu**

- Vérifie que `session.attack(CombatantId{3}).result` vaut `core::ArenaActionResult::NoActiveTurn`.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::InvalidTarget`.
- Vérifie que `session.attack(CombatantId{9}).result` vaut `core::ArenaActionResult::InvalidTarget`.
- Vérifie que `session.attack(CombatantId{4}).result` vaut `core::ArenaActionResult::OutOfReach`.
- Vérifie que `session.attack(CombatantId{3}, 5).result` vaut `core::ArenaActionResult::NoAttack`.
- Vérifie que `attaque.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `attaque.outcome.has_value()` est vrai.
- Vérifie que `attaque.outcome->roll.check.target` vaut `30`.
- Vérifie que `attaque.outcome->roll.check.modifiers.size()` vaut `1U`.
- Vérifie que `attaque.outcome->roll.check.modifiers[0].value` vaut `5`.
- Vérifie que `session.journal().back()` vaut `attaque.outcome->describe()`.
- Vérifie que `session.journal().back().starts_with("attaque Heroine -> Gobelin")` est vrai.
- Vérifie que `session.attack(CombatantId{3}).result` vaut `core::ArenaActionResult::NoAction`.
- Vérifie que `std::ranges::find_if( session.journal(), [](const std::string& l) { return l.starts_with("attaque declaree"); })` diffère de `session.journal().end()`.

### ArenaTest.LePilierCacheEtAbrite

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_arena.cpp:325`

Dans l'arene, un tir vers une cible cachee par le pilier est refuse ; vers une cible que le pilier abrite partiellement, il est jete contre sa CA + 2, et le journal le dit.

**Étapes**

1. Une archere (portee 16/64) au centre de la case (5,3), un gobelin a la CA 12 en (7,3) derriere le pilier (6,3), un second en (7,5).
2. L'archere tire sur le premier.
3. Elle se place au centre de la case (5,2), d'ou le pilier coupe une ou deux des lignes vers le gobelin, et tire encore.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `session.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::TotalCover`.
- Vérifie que `session.combat().find(CombatantId{1})->economy.remaining(core::ACTION_RESOURCE)` vaut `1`.
- Vérifie que `session.move(tile(5, 2)).result` vaut `core::MoveResult::Moved`.
- Vérifie que `tir.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `tir.outcome.has_value()` est vrai.
- Vérifie que `tir.outcome->roll.armorClass` vaut `14`.
- Vérifie que `session.journal().back().find("abri partiel : CA 12 -> 14")` diffère de `std::string::npos`.

### ArenaTest.LOpportuniteLeDesengagementEtLEsquive

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_arena.cpp:369`

Quitter l'allonge d'un ennemi provoque son attaque d'opportunite, qui depense sa reaction ; se desengager l'evite ; esquiver impose le desavantage a qui attaque.

**Étapes**

1. Heroine au centre de la case (2,3), au contact d'un ogre en (3,3) (CA 1, bonus 0, 1 degat).
2. L'apercu du deplacement vers le centre de (2,5), puis le deplacement.
3. Remonter, se desengager, puis s'eloigner.
4. Remonter, esquiver, finir le tour ; l'ogre attaque l'heroine.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `session.previewOpportunities(tile(2, 5))` vaut `(std::vector<CombatantId>{CombatantId{2}})`.
- Vérifie que `fuite.result` vaut `core::MoveResult::Moved`.
- Vérifie que `memePlace(session.combat().positionOf(CombatantId{1}), tile(2, 5))` est vrai.
- Vérifie que `opportunites(session)` vaut `1`.
- Vérifie que `ecartAuCoup.has_value()` est vrai.
- Vérifie que `core::withinTiles(*ecartAuCoup, 1)` est vrai.
- Vérifie que `dernierPas` diffère de `session.journal().rend()`.
- Vérifie que `dernierPas->starts_with("pas Heroine 3.75,8.25 (")` est vrai.
- Vérifie que `dernierPas->ends_with(" m)")` est vrai.
- Vérifie que `session.combat().find(CombatantId{2})->economy.remaining(core::REACTION_RESOURCE)` vaut `0`.
- Vérifie que `prudente.start()` est vrai.
- Vérifie que `prudente.disengage()` est vrai.
- Vérifie que `prudente.dodge()` est faux.
- Vérifie que `prudente.previewOpportunities(tile(2, 5)).empty()` est vrai.
- Vérifie que `prudente.move(tile(2, 5)).result` vaut `core::MoveResult::Moved`.
- Vérifie que `opportunites(prudente)` vaut `0`.
- Vérifie que `prudente.combat().find(CombatantId{2})->economy.remaining(core::REACTION_RESOURCE)` vaut `1`.
- Vérifie que `esquive.start()` est vrai.
- Vérifie que `esquive.dodge()` est vrai.
- Vérifie que `esquive.endTurn()` est vrai.
- Vérifie que `esquive.combat().activeCombatant()` vaut `CombatantId{2}`.
- Vérifie que `riposte.outcome.has_value()` est vrai.
- Vérifie que `riposte.outcome->roll.check.stance` vaut `core::RollStance::Disadvantage`.
- Vérifie que `riposte.outcome->describe().find("esquive de la cible")` diffère de `std::string::npos`.

### ArenaTest.SePrecipiterDoubleLeDeplacement

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_arena.cpp:454`

L'action se precipiter donne un deplacement supplementaire egal a la vitesse : une destination a 12 m, hors des 9 m d'une vitesse de 6 cases, devient atteignable, et ce qui reste se lit en metres.

**Étapes**

1. Une heroine de vitesse 6 au centre de la case (1,1), un gobelin loin d'elle.
2. Aller au centre de la case (9,1), a 12 m.
3. Se precipiter, puis y aller.
4. Se precipiter encore.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `session.combat().movementLeft()` vaut `9.0F`, à `0.001F` près.
- Vérifie que `session.move(tile(9, 1)).result` vaut `core::MoveResult::Unreachable`.
- Vérifie que `memePlace(session.combat().positionOf(CombatantId{1}), tile(1, 1))` est vrai.
- Vérifie que `session.combat().movementLeft()` vaut `9.0F`, à `0.001F` près.
- Vérifie que `session.dash()` est vrai.
- Vérifie que `session.journal().back()` vaut `"precipitation Heroine"`.
- Vérifie que `session.combat().movementLeft()` vaut `18.0F`, à `0.001F` près.
- Vérifie que `course.result` vaut `core::MoveResult::Moved`.
- Vérifie que `course.path.length` vaut `12.0F`, à `0.01F` près.
- Vérifie que `memePlace(session.combat().positionOf(CombatantId{1}), tile(9, 1))` est vrai.
- Vérifie que `session.combat().movementLeft()` vaut `6.0F`, à `0.01F` près.
- Vérifie que `session.dash()` est faux.

### ArenaTest.UnAffrontementSeJoueSeRejoueEtPersonneNYMeurt

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_arena.cpp:499`

Un affrontement se joue jusqu'a son issue ; le rejeu a la meme graine donne le meme journal ; a la fin, la Marque Heroique releve tout le monde, sauf dans une arene letale.

**Étapes**

1. Deux allies contre trois gobelins, graine 2026, jouer jusqu'a l'issue.
2. Rejouer par `replay`, puis a une autre graine.
3. Meme affrontement dans une arene letale.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.outcome().has_value()` est vrai.
- Vérifie que `session.combat().round()` est supérieur ou égal à `2`.
- Vérifie que `std::count_if(journal.begin(), journal.end(), [](const std::string& l) { return l.starts_with("issue"); })` vaut `1`.
- Vérifie que `journal.back()` vaut `"marque heroique : tous releves"`.
- Vérifie que `c->status` vaut `core::CombatantStatus::Standing`.
- Vérifie que `c->profile.currentHitPoints` vaut `c->profile.maximumHitPoints`.
- Vérifie que `remontage.allies.size()` vaut `2U`.
- Vérifie que `remontage.enemies.size()` vaut `3U`.
- Vérifie que `session.outcome().has_value()` est faux.
- Vérifie que `jouer(session)` vaut `journal`.
- Vérifie que `session.outcome()` vaut `issue`.
- Vérifie que `autre.start()` est vrai.
- Vérifie que `jouer(autre)` diffère de `journal`.
- Vérifie que `letale.start()` est vrai.
- Vérifie que `letale.outcome().has_value()` est vrai.
- Vérifie que `journalLetal.back()` diffère de `"marque heroique : tous releves"`.
- Vérifie que `std::ranges::any_of(letale.combat().combatants(), [&](CombatantId id) { return letale.combat().find(id)->status == core::CombatantStatus::Down; })` est vrai.

## test_attack.cpp

### AttackTest.UnVingtNaturelToucheEtDoubleLesDes

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:130`

Un 20 naturel touche une CA hors d'atteinte, est un critique, et double les des de degats sans doubler le modificateur.

**Étapes**

1. L'heroine (+5, 1d8+3) attaque un gobelin a la CA 40.
2. Le d20 est force a 20.

**Résultat attendu**

- Vérifie que `issue.has_value()` est vrai.
- Vérifie que `issue->roll.hit` est vrai.
- Vérifie que `issue->roll.critical` est vrai.
- Vérifie que `issue->roll.check.total` vaut `25`.
- Vérifie que `issue->damage.size()` vaut `1U`.
- Vérifie que `des.faces.size()` vaut `2U`.
- Vérifie que `des.dice.modifier` vaut `3`.
- Vérifie que `duel.combat.find(CombatantId{2})->profile.currentHitPoints` vaut `30 - perte`.
- Vérifie que `ligne.find("critique (20 naturel)")` diffère de `std::string::npos`.
- Vérifie que `ligne.find("(des doubles)")` diffère de `std::string::npos`.

### AttackTest.UnUnNaturelRateMemeAuDessusDeLaCA

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:162`

Un 1 naturel rate toujours, meme quand le total depasse la classe d'armure.

**Étapes**

1. L'heroine attaque avec +30 un gobelin a la CA 5.
2. Le d20 est force a 1.

**Résultat attendu**

- Vérifie que `issue.has_value()` est vrai.
- Vérifie que `issue->roll.check.total` vaut `31`.
- Vérifie que `issue->roll.hit` est faux.
- Vérifie que `issue->damage.empty()` est vrai.
- Vérifie que `duel.combat.find(CombatantId{2})->profile.currentHitPoints` vaut `30`.
- Vérifie que `issue->describe()` vaut `"attaque Heroine -> Gobelin (Epee longue) : d20 = 1 + 30 (benediction) = 31 contre " "CA 5 : rate (1 naturel)"`.

### AttackTest.ChaqueJetProduitUneEntreeDeJournalComplete

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:189`

Exigences : `EX-REG-003`

Une attaque touchee et une attaque ratee s'ecrivent au journal avec le de, chaque modificateur et son origine, la CA, l'issue, les des de degats, leur type et les PV.

**Étapes**

1. Le d20 force a 12, contre CA 15 : touche.
2. Le d20 force a 4 : rate.

**Résultat attendu**

- Vérifie que `touche.has_value() && touche->report.has_value()` est vrai.
- Vérifie que `touche->describe()` vaut `attendu`.
- Vérifie que `rate.has_value()` est vrai.
- Vérifie que `rate->describe()` vaut `"attaque Heroine -> Gobelin (Epee longue) : d20 = 4 + 3 (Force) + " "2 (maitrise) = 9 contre CA 15 : rate"`.

### AttackTest.LeJetSAmendeAvantQueLIssueNeSoitFigee

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:222`

Un greffon ajoute une source de desavantage avant le jet, relance un de apres le jet, ajoute un modificateur apres avoir vu le total ; l'issue tient compte des trois.

**Étapes**

1. Avant le jet : un desavantage et un seuil critique a 19.
2. Apres les des : substituer 19 au premier de et 19 au second.
3. Avant l'issue : +5 si le total rate.
4. Un attaquant avantage et desavantage a la fois.
5. L'annonce de l'attaque precede le jet.

**Résultat attendu**

- Vérifie que `jet.check.dice.size()` vaut `2U`.
- Vérifie que `issue.has_value()` est vrai.
- Vérifie que `ordre` vaut `(std::vector<std::string>{"declaree", "jet"})`.
- Vérifie que `issue->roll.check.stance` vaut `core::RollStance::Disadvantage`.
- Vérifie que `issue->roll.amendments.size()` vaut `2U`.
- Vérifie que `issue->roll.check.total` vaut `27`.
- Vérifie que `issue->roll.hit` est vrai.
- Vérifie que `issue->roll.critical` est vrai.
- Vérifie que `jet.check.stance` vaut `core::RollStance::Normal`.
- Vérifie que `jet.check.dice.size()` vaut `1U`.
- Vérifie que `jet.check.target` vaut `10`.

### AttackTest.LEspaceDitLaPorteeEtLesCirconstances

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:284`

L'allonge et la portee se mesurent entre les bords des volumes : une creature de taille G touche ce qui borde son volume ; un tir est desavantage au contact d'un ennemi ou au-dela de sa portee normale.

**Étapes**

1. Un ogre de taille G pose sur les cases (5,5) a (6,6), un archer au centre de la case (7,5), un guerrier en (2,5), un rat en (7,11).
2. Mesurer les ecarts ; l'allonge d'une attaque de 1, 2 et 3 cases.
3. L'archer tire au contact de l'ogre ; puis sur le rat, avec une portee 4/12.
4. Une cible a terre.

**Résultat attendu**

- Vérifie que `combat.start(hasard)` est vrai.
- Vérifie que `*core::gapBetween(combat, CombatantId{1}, CombatantId{2})` vaut `0.12F`, à `0.01F` près.
- Vérifie que `*core::gapBetween(combat, CombatantId{3}, CombatantId{2})` vaut `3.05F`, à `0.01F` près.
- Vérifie que `*core::gapBetween(combat, CombatantId{1}, CombatantId{4})` vaut `7.5F`, à `0.01F` près.
- Vérifie que `core::inReach(combat, CombatantId{2}, CombatantId{1}, massue)` est vrai.
- Vérifie que `core::inReach(combat, CombatantId{3}, CombatantId{2}, massue)` est faux.
- Vérifie que `core::inReach(combat, CombatantId{3}, CombatantId{2}, massue)` est faux.
- Vérifie que `core::inReach(combat, CombatantId{3}, CombatantId{2}, massue)` est vrai.
- Vérifie que `core::attackCircumstances(combat, CombatantId{1}, CombatantId{2}, arc).disadvantages` vaut `(std::vector<std::string>{"tir au contact d'un ennemi"})`.
- Vérifie que `core::inReach(combat, CombatantId{1}, CombatantId{4}, arc)` est faux.
- Vérifie que `core::inReach(combat, CombatantId{1}, CombatantId{4}, arc)` est vrai.
- Vérifie que `core::attackCircumstances(combat, CombatantId{1}, CombatantId{4}, arc).disadvantages` vaut `(std::vector<std::string>{"tir au contact d'un ennemi", "longue portee"})`.
- Vérifie que `core::resolveAttack(combat, CombatantId{1}, CombatantId{4}, arc, hasard).has_value()` est faux.

### AttackTest.LesProfilsSeTirentDuBestiaireEtDeLaFiche

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:340`

Les attaques d'une creature se lisent de son bloc ; celles d'un personnage de son arme, de sa Force ou de sa Dexterite et de sa maitrise ; le coup a mains nues vaut 1 + Force ; aucune creature livree n'a de degats sans type.

**Étapes**

1. Une creature a quatre actions : allonge 3 m, sans allonge, sans type, sans degats.
2. Une fiche de Force 16 et Dexterite 18, maitrise +2 : epee longue, rapiere de finesse, filet, mains nues, arme non maitrisee.
3. Charger le bestiaire livre.

**Résultat attendu**

- Vérifie que `attaques.attacks.size()` vaut `2U`.
- Vérifie que `attaques.attacks[0].reach` vaut `2`.
- Vérifie que `attaques.attacks[0].kind` vaut `core::AttackKind::Melee`.
- Vérifie que `attaques.attacks[0].modifiers[0].value` vaut `6`.
- Vérifie que `attaques.attacks[1].kind` vaut `core::AttackKind::Ranged`.
- Vérifie que `attaques.refused` vaut `(std::vector<std::string>{"Etrange : degats sans type"})`.
- Vérifie que `epeeLongue.modifiers[0].source` vaut `"Force"`.
- Vérifie que `epeeLongue.modifiers[0].value` vaut `3`.
- Vérifie que `epeeLongue.modifiers[1].value` vaut `2`.
- Vérifie que `epeeLongue.damage[0].dice` vaut `*core::parseDice("1d8+3")`.
- Vérifie que `finesse.modifiers[0].source` vaut `"Dexterite"`.
- Vérifie que `finesse.damage[0].dice` vaut `*core::parseDice("1d8+4")`.
- Vérifie que `core::weaponAttackFor(fiche, &filet, 2).damage.empty()` est vrai.
- Vérifie que `mains.damage[0].type` vaut `DamageType::Bludgeoning`.
- Vérifie que `mains.damage[0].dice.minimum()` vaut `4`.
- Vérifie que `mains.damage[0].dice.maximum()` vaut `4`.
- Vérifie que `core::weaponAttackFor(fiche, &longue, 2, false).modifiers.size()` vaut `1U`.
- Vérifie que `bestiaire.creatures.empty()` est faux.
- Vérifie que `lues.refused.empty()` est vrai.
- Vérifie que `total` est strictement supérieur à `bestiaire.creatures.size() / 2`.

### AttackTest.LAbriChangeLaCAUneFois

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:425`

Une cible derriere un muret gagne +2 a sa CA ; un greffon qui pose le meme abri ne l'ajoute pas une seconde fois ; un abri important par-dessus porte le bonus a +5, pas a +7 ; un abri total n'est pas un bonus.

**Étapes**

1. Un archer au centre de la case (0,1), un gobelin a la CA 15 en (3,1), un muret de 0,75 m — la moitie d'une creature de taille M — sur la case (2,1).
2. Tirer, d20 force a 12.
3. Tirer avec un greffon qui pose l'abri partiel, puis l'abri total.
4. Tirer avec un greffon qui pose l'abri important.

**Résultat attendu**

- Vérifie que `combat.start(hasard)` est vrai.
- Vérifie que `core::coverBetween(combat, CombatantId{1}, CombatantId{2})` vaut `core::Cover::Half`.
- Vérifie que `simple.has_value()` est vrai.
- Vérifie que `simple->roll.armorClass` vaut `17`.
- Vérifie que `simple->roll.cover` vaut `core::Cover::Half`.
- Vérifie que `simple->describe().find("[abri partiel : CA 15 -> 17] = 12")` diffère de `std::string::npos`.
- Vérifie que `simple->describe().find("= 17 contre CA 17 : touche")` diffère de `std::string::npos`.
- Vérifie que `repose.has_value()` est vrai.
- Vérifie que `repose->roll.armorClass` vaut `17`.
- Vérifie que `repose->roll.amendments.size()` vaut `1U`.
- Vérifie que `important.has_value()` est vrai.
- Vérifie que `important->roll.armorClass` vaut `20`.
- Vérifie que `important->roll.cover` vaut `core::Cover::ThreeQuarters`.
- Vérifie que `important->roll.amendments.size()` vaut `2U`.
- Vérifie que `important->roll.hit` est faux.

### AttackTest.ViserDemandeLaPorteeEtLaVue

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:490`

Une cible derriere un mur ne se vise pas, ni a distance ni au contact par le coin de deux murs ; au-dela de la longue portee non plus ; un ennemi adjacent qui ne voit pas le tireur ne lui impose pas le desavantage du tir au contact.

**Étapes**

1. Un archer au centre de la case (1,1), un gobelin en (2,2) derriere deux murs en (2,1) et (1,2), un loup en (0,3), un rat en (5,5).
2. Verifier chaque cible, a distance (portee 2/3) et au contact.
3. Les circonstances du tir vers le loup.

**Résultat attendu**

- Vérifie que `combat.start(hasard)` est vrai.
- Vérifie que `ecart.has_value()` est vrai.
- Vérifie que `*ecart` vaut `0.62F`, à `0.01F` près.
- Vérifie que `core::adjacentGap(*ecart)` est vrai.
- Vérifie que `core::checkTarget(combat, CombatantId{1}, CombatantId{2}, arc)` vaut `core::TargetCheck::TotalCover`.
- Vérifie que `core::checkTarget(combat, CombatantId{1}, CombatantId{2}, epee())` vaut `core::TargetCheck::TotalCover`.
- Vérifie que `core::checkTarget(combat, CombatantId{1}, CombatantId{3}, arc)` vaut `core::TargetCheck::Valid`.
- Vérifie que `core::checkTarget(combat, CombatantId{1}, CombatantId{4}, arc)` vaut `core::TargetCheck::OutOfReach`.
- Vérifie que `core::checkTarget(combat, CombatantId{1}, CombatantId{1}, arc)` vaut `core::TargetCheck::NotPlaced`.
- Vérifie que `core::attackCircumstances(combat, CombatantId{1}, CombatantId{3}, arc) .disadvantages.empty()` est vrai.

### AttackTest.LesPorteesSeLisentDansLaDonnee

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:538`

Chaque arme qui se tire ou se lance porte ses portees ; l'arc long tire a 30/120 cases, la hallebarde frappe a 2, la dague se lance a 4/12 ; le squelette tire a 16/64.

**Étapes**

1. Charger le catalogue d'armes et le bestiaire livres.
2. Pour chaque arme : portees presentes si et seulement si elle a les munitions ou le lancer.
3. Tirer les profils de l'arc long, de la hallebarde, de la dague (lancee), de l'epee longue (qui ne se lance pas) et du squelette.

**Résultat attendu**

- Vérifie que `catalogue.errors.empty()` est vrai.
- Vérifie que `catalogue.weapons.size()` vaut `37U`.
- Vérifie que `arme.rangeNormal.has_value()` vaut `tiree`.
- Vérifie que `arme.rangeLong.has_value()` vaut `tiree`.
- Vérifie que `tiree` est vrai.
- Vérifie que `arcLong.range.has_value()` est vrai.
- Vérifie que `arcLong.range->normal` vaut `30`.
- Vérifie que `arcLong.range->maximum` vaut `120`.
- Vérifie que `core::weaponAttackFor(fiche, catalogue.findWeapon("hallebarde"), 2).reach` vaut `2`.
- Vérifie que `core::weaponAttackFor(fiche, catalogue.findWeapon("epee-longue"), 2).reach` vaut `1`.
- Vérifie que `dague.has_value() && dague->range.has_value()` est vrai.
- Vérifie que `dague->label` vaut `"Dague (lancer)"`.
- Vérifie que `dague->kind` vaut `core::AttackKind::Ranged`.
- Vérifie que `dague->range->normal` vaut `4`.
- Vérifie que `dague->range->maximum` vaut `12`.
- Vérifie que `dague->modifiers[0].source` vaut `"Dexterite"`.
- Vérifie que `core::thrownAttackFor(fiche, *catalogue.findWeapon("epee-longue"), 2).has_value()` est faux.
- Vérifie que `squelette` diffère de `nullptr`.
- Vérifie que `attaques.attacks.size()` vaut `2U`.
- Vérifie que `attaques.attacks[1].kind` vaut `core::AttackKind::Ranged`.
- Vérifie que `attaques.attacks[1].range.has_value()` est vrai.
- Vérifie que `attaques.attacks[1].range->normal` vaut `16`.
- Vérifie que `attaques.attacks[1].range->maximum` vaut `64`.

### AttackTest.LaVueEstSymetriqueSurDesCartesGenerees

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:602`

A voit B si et seulement si B voit A — verifie exhaustivement sur des cartes generees, pour chaque paire de combattants de taille M poses au centre des cases libres, et pour chaque creature de taille G contre chacun d'eux ; l'abri total equivaut a l'absence de vue.

**Étapes**

1. Generer 20 cartes 5 × 5 a des densites de 10 a 55 % de murs, d'eau profonde, de portes fermees, de parapets et de murets.
2. Poser un combattant au centre de chaque case libre ; pour chaque paire ordonnee, comparer les deux sens de la vue (`core::hasLineOfSight`).
3. Pour chaque bloc libre de 2 × 2 cases, y poser une creature de taille G parmi les autres, et comparer de meme.
4. Pour chacune : l'abri total (`core::coverBetween`) equivaut a l'absence de vue.

**Résultat attendu**

- Vérifie que `enrole.combatant.has_value()` est vrai.
- Vérifie que `verifier(foule, a, b)` est vrai.
- Vérifie que `grand.combatant.has_value()` est vrai.
- Vérifie que `petit.combatant.has_value()` est vrai.
- Vérifie que `verifier(combat, *grand.combatant, *petit.combatant)` est vrai.
- Vérifie que `vues` est strictement supérieur à `3000U`.
- Vérifie que `cachees` est strictement supérieur à `500U`.

### AttackTest.CeQuiArreteLaVue

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:733`

Un mur cache, un gouffre d'eau profonde non ; le coin commun de deux murs ne laisse pas passer le regard ; une porte fermee cache comme un mur, ouverte elle ne cache plus.

**Étapes**

1. Deux combattants alignes, un mur d'une case entre eux ; deux autres sur la rangee voisine.
2. Les memes, separes par une riviere d'eau profonde.
3. Deux combattants en diagonale, deux murs sur les deux autres cases du carre ; puis un seul mur.
4. Une porte fermee dans un couloir, puis ouverte.

**Résultat attendu**

- Vérifie que `core::hasLineOfSight(*derriere, CombatantId{1}, CombatantId{2})` est faux.
- Vérifie que `core::coverBetween(*derriere, CombatantId{1}, CombatantId{2})` vaut `Cover::Total`.
- Vérifie que `core::checkTarget(*derriere, CombatantId{1}, CombatantId{2}, arc)` vaut `core::TargetCheck::TotalCover`.
- Vérifie que `core::hasLineOfSight(*derriere, CombatantId{3}, CombatantId{4})` est vrai.
- Vérifie que `core::hasLineOfSight(*rives, CombatantId{1}, CombatantId{2})` est vrai.
- Vérifie que `core::coverBetween(*rives, CombatantId{1}, CombatantId{2})` vaut `Cover::None`.
- Vérifie que `core::hasLineOfSight(*enCoin, CombatantId{1}, CombatantId{2})` est faux.
- Vérifie que `core::hasLineOfSight(*enCoin, CombatantId{2}, CombatantId{1})` est faux.
- Vérifie que `core::hasLineOfSight(*enDemiCoin, CombatantId{1}, CombatantId{2})` est vrai.
- Vérifie que `core::hasLineOfSight(*deParEtDAutre, CombatantId{1}, CombatantId{2})` est faux.
- Vérifie que `porte->removeBox(battant)` est vrai.
- Vérifie que `core::hasLineOfSight(*deParEtDAutre, CombatantId{1}, CombatantId{2})` est vrai.

### AttackTest.LesAbrisEtCeQuiLesDonne

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_attack.cpp:796`

Un muret et une creature interposee abritent partiellement, un parapet de facon importante ; un angle de mur donne l'abri selon les lignes qu'il coupe, depuis la place du tireur ; les abris ne s'additionnent pas.

**Étapes**

1. Un tireur au centre de la case (0,1), une cible en (3,1), rien entre eux.
2. Un muret de 0,75 m, puis un parapet de 1,20 m, sur la case (2,1) devant la cible.
3. Une creature en (1,1), seule, avec le muret, avec le parapet.
4. Un mur de 3 m en (2,1), et des tireurs en (0,1), (0,0) et (1,0).

**Résultat attendu**

- Vérifie que `core::coverBetween(*rien, CombatantId{1}, CombatantId{2})` vaut `Cover::None`.
- Vérifie que `core::coverBetween(*derriere(MURET, Cover::Half, false), CombatantId{1}, CombatantId{2})` vaut `Cover::Half`.
- Vérifie que `core::coverBetween(*derriere(PARAPET, Cover::ThreeQuarters, false), CombatantId{1}, CombatantId{2})` vaut `Cover::ThreeQuarters`.
- Vérifie que `core::coverBetween(*garde, CombatantId{1}, CombatantId{2})` vaut `Cover::Half`.
- Vérifie que `core::coverBetween(*derriere(MURET, Cover::Half, true), CombatantId{1}, CombatantId{2})` vaut `Cover::Half`.
- Vérifie que `core::coverBetween(*derriere(PARAPET, Cover::ThreeQuarters, true), CombatantId{1}, CombatantId{2})` vaut `Cover::ThreeQuarters`.
- Vérifie que `core::coverBetween(*tireurs, CombatantId{2}, CombatantId{1})` vaut `Cover::Total`.
- Vérifie que `core::coverBetween(*tireurs, CombatantId{3}, CombatantId{1})` vaut `Cover::ThreeQuarters`.
- Vérifie que `core::coverBetween(*tireurs, CombatantId{4}, CombatantId{1})` vaut `Cover::Half`.
- Vérifie que `core::coverBonus(Cover::None)` vaut `0`.
- Vérifie que `core::coverBonus(Cover::Half)` vaut `2`.
- Vérifie que `core::coverBonus(Cover::ThreeQuarters)` vaut `5`.
- Vérifie que `core::coverBonus(Cover::Total)` vaut `0`.

## test_class_brawler.cpp

### ClassBrawlerTest.LaFichePreTireePorteToughAsNails

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_brawler.cpp:61`

La fiche de la page 195 se charge avec Tough as Nails et sa CA de 14.

**Étapes**

1. Charger heros-brawler.json.
2. Lire ses capacites, ses avertissements, sa CA avec ce qu'il porte, et son profil de combat.

**Résultat attendu**

- Vérifie que `charge.warnings.empty()` est vrai.
- Vérifie que `test_support::capacityIds(charge.sheet)` vaut `std::vector<std::string>{"tough-as-nails"}`.
- Vérifie que `test_support::armorClassOf(charge.sheet, charge.inventory)` vaut `14`.
- Vérifie que `profil.damageTraits.affinities.size()` vaut `13U`.
- Vérifie que `profil.damageTraits.affinities.empty()` est faux.
- Vérifie que `profil.damageTraits.affinities.front().source` vaut `"Tough as Nails"`.

### ClassBrawlerTest.ToughAsNailsDonneSaCaSansArmure

*Majeur · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_brawler.cpp:84`

La formule de Tough as Nails se recalcule avec ce que le Brawler porte.

**Étapes**

1. Calculer la CA du Brawler N1 sans rien, avec un bouclier, en cuir, en cuir avec bouclier.

**Résultat attendu**

- Vérifie que `bouclier` diffère de `nullptr`.
- Vérifie que `cuir` diffère de `nullptr`.
- Vérifie que `core::armorClassFor(fiche, catalogues.rules, nullptr, nullptr)` vaut `14`.
- Vérifie que `core::armorClassFor(fiche, catalogues.rules, nullptr, bouclier)` vaut `16`.
- Vérifie que `core::armorClassFor(fiche, catalogues.rules, cuir, nullptr)` vaut `12`.
- Vérifie que `core::armorClassFor(fiche, catalogues.rules, cuir, bouclier)` vaut `14`.

### ClassBrawlerTest.ToughAsNailsDiviseLesDegatsEtSeNomme

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_brawler.cpp:112`

Le mannequin touche le Brawler a 5 PV sur 15 : il retire le tiers des degats, et le journal ecrit « resistance graduee (tranchant ; Tough as Nails) » ; plein de vie, il perd tout.

**Étapes**

1. Monter le Brawler N1 a 5 PV contre un mannequin a +20 au toucher.
2. Passer au tour du mannequin et attaquer ; graine choisie pour toucher.
3. Recommencer a 15 PV.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `attaque.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `coup.has_value()` est vrai.
- Vérifie que `journalHas(session.journal(), "capacites Grom Tranche-Écaille : Tough as Nails")` est vrai.
- Vérifie que `coup->report.has_value()` est vrai.
- Vérifie que `ligne.find("resistance graduee (tranchant ; Tough as Nails)")` diffère de `std::string::npos`.
- Vérifie que `coup->report->hitPointsBefore - coup->report->hitPointsAfter` vaut `std::min(5, lances - retire)`.
- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `attaque.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `plein.has_value() && plein->report.has_value()` est vrai.
- Vérifie que `plein->report->hitPointsBefore - plein->report->hitPointsAfter` vaut `std::min(15, plein->damage.front().amount)`.

### ClassBrawlerTest.HitTheMarkAjouteDeuxAuJet

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_brawler.cpp:176`

Au niveau 3, le jet de la hache porte « + 2 (Hit the Mark) » ; au niveau 2, non.

**Étapes**

1. Monter le Brawler N3, puis N2, contre un mannequin.
2. Attaquer.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, 10, 0)).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `attaque.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `bonus` diffère de `modificateurs.end()`.
- Vérifie que `bonus->value` vaut `2`.
- Vérifie que `journalHas(session.journal(), "+ 2 (Hit the Mark)")` est vrai.
- Vérifie que `bonus` vaut `modificateurs.end()`.

### ClassBrawlerTest.ExtraAttackDonneDeuxAttaquesParAction

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_brawler.cpp:207`

Au niveau 5, le Brawler attaque deux fois dans le tour ; la seconde est nommee au journal ; une troisieme est refusee, et l'action n'est plus la pour esquiver.

**Étapes**

1. Monter le Brawler N5 contre un mannequin.
2. Attaquer trois fois, puis esquiver.
3. Finir le tour, revenir, attaquer deux fois.
4. Refaire au niveau 4.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, 10, 0)).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `session.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), "attaque supplementaire Grom Tranche-Écaille (Extra Attack)")` est vrai.
- Vérifie que `session.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::NoAction`.
- Vérifie que `session.dodge()` est faux.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `session.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `session.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `test_support::journalCount(session.journal(), "attaque supplementaire")` vaut `2U`.
- Vérifie que `avant.mount(combatDe(niveau4, 10, 0)).refusals.empty()` est vrai.
- Vérifie que `avant.start()` est vrai.
- Vérifie que `avant.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `avant.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::NoAction`.

### ClassBrawlerTest.ExtraAttackNeSuitQueLActionAttaquer

*Majeur · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_brawler.cpp:247`

Apres une esquive, le Brawler N5 n'attaque pas.

**Étapes**

1. Monter le Brawler N5.
2. Esquiver, puis attaquer.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, 10, 0)).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.dodge()` est vrai.
- Vérifie que `session.attack(CombatantId{2}).result` vaut `core::ArenaActionResult::NoAction`.
- Vérifie que `session.combat().find(CombatantId{1})->economy.remaining(core::EXTRA_ATTACK_RESOURCE)` vaut `0`.

### ClassBrawlerTest.DuNiveau1AuNiveau5LaTableSeLit

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_brawler.cpp:267`

Monter le Brawler de la page 195 niveau par niveau donne les capacites de la table, sans capacite manquante.

**Étapes**

1. Charger la fiche N1.
2. Monter d'un niveau a la fois jusqu'au 5, lire les capacites, le bonus de maitrise et les PV.

**Résultat attendu**

- Vérifie que `manquants.empty()` est vrai.
- Vérifie que `fiche.level` vaut `niveau`.
- Vérifie que `test_support::capacityIds(fiche)` vaut `attendues[static_cast<std::size_t>(niveau - 1)]`.
- Vérifie que `fiche.maximumHitPoints - pvPrecedents` vaut `10`.
- Vérifie que `test_support::armorClassOf(fiche, charge.inventory)` vaut `14`.
- Vérifie que `core::proficiencyBonus(fiche, test_support::rpgCatalogs().experience)` vaut `3`.
- Vérifie que `core::extraAttacksFrom(fiche.capacities).has_value()` est vrai.
- Vérifie que `core::extraAttacksFrom(fiche.capacities)->count` vaut `1`.

### ClassBrawlerTest.UneAttaqueEnPlusNulleEstRefusee

*Majeur · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_brawler.cpp:307`

Une capacite qui declare « extra-attack » a 0 est refusee et nommee.

**Étapes**

1. Ecrire une capacite extra-attack a value 0 dans un dossier temporaire.
2. Charger le dossier.

**Résultat attendu**

- Vérifie que `catalogue.capacities.empty()` est vrai.
- Vérifie que `catalogue.errors.size()` vaut `1U`.
- Vérifie que `catalogue.errors.front().find("vide.json")` diffère de `std::string::npos`.

## test_class_in_arena.cpp

### ClassInArenaTest.LeBonusEtLesDesDUneCapaciteSeJouentEtSeNomment

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_class_in_arena.cpp:150`

Contre une CA nulle, l'epee de la lutteuse touche : le journal ecrit « + 2 (Coup precis) » et un 1d6 « (Coup precis) » ; une seconde attaque du meme tour n'ajoute plus de des ; au tour suivant, si.

**Étapes**

1. Monter la lutteuse (N1) contre un gobelin a la CA 0, graine choisie pour que le premier coup ne soit pas un 1 naturel.
2. Attaquer.
3. Octroyer une action et rattaquer.
4. Revenir a son tour et rattaquer.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `coup.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `premier.has_value()` est vrai.
- Vérifie que `contient(session.journal(), "capacites Lutteuse : Coup precis, Peau de fer")` est vrai.
- Vérifie que `bonus` diffère de `modificateurs.end()`.
- Vérifie que `bonus->value` vaut `2`.
- Vérifie que `premier->damage.size()` vaut `2U`.
- Vérifie que `premier->damage[0].source.empty()` est vrai.
- Vérifie que `premier->damage[1].source` vaut `"Coup precis"`.
- Vérifie que `premier->damage[1].clause.dice` vaut `(core::Dice{.count = 1, .faces = 6, .modifier = 0})`.
- Vérifie que `premier->damage[1].clause.type` vaut `core::DamageType::Slashing`.
- Vérifie que `ligne.find("+ 2 (Coup precis)")` diffère de `std::string::npos`.
- Vérifie que `ligne.find("tranchant (Coup precis)")` diffère de `std::string::npos`.
- Vérifie que `session.combat().counters().value(core::CounterScope::Turn, "1", "coup-precis")` vaut `1`.
- Vérifie que `second.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `second.outcome->damage.size()` vaut `1U`.
- Vérifie que `session.combat().counters().value(core::CounterScope::Turn, "1", "coup-precis")` vaut `1`.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `session.combat().counters().value(core::CounterScope::Turn, "1", "coup-precis")` vaut `0`.
- Vérifie que `troisieme.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `troisieme.outcome->damage.size()` vaut `2U`.

### ClassInArenaTest.LaResistanceGlobaleSeNommeAuJournal

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_class_in_arena.cpp:227`

Le gobelin touche la lutteuse (Peau de fer) : la trace ecrit « resistance (tranchant ; Peau de fer) », et les PV perdus sont la moitie arrondie a l'inferieur des degats lances.

**Étapes**

1. Monter la lutteuse (N1) et un gobelin a +20 au toucher.
2. Passer au tour du gobelin, attaquer la lutteuse ; graine choisie pour toucher.

**Résultat attendu**

- Vérifie que `profil.damageTraits.affinities.size()` vaut `13U`.
- Vérifie que `profil.damageTraits.applies(core::DamageAffinityKind::Resistance, core::DamageType::Fire, 0)` est vrai.
- Vérifie que `profil.damageTraits.affinities.front().source` vaut `"Peau de fer"`.
- Vérifie que `profil.armorClass` vaut `15`.
- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{2}`.
- Vérifie que `attaque.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `coup.has_value()` est vrai.
- Vérifie que `coup->report.has_value()` est vrai.
- Vérifie que `coup->report->hitPointsBefore - coup->report->hitPointsAfter` vaut `lances / 2`.
- Vérifie que `ligne.find("resistance (tranchant ; Peau de fer)")` diffère de `std::string::npos`.

### ClassInArenaTest.LeDeplacementNeProvoquePasDAttaqueDOpportunite

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_class_in_arena.cpp:275`

La lutteuse (N2, Pas de danseur) quitte l'allonge du gobelin sans etre frappee, la previsualisation ne montre personne, et le journal nomme la capacite ; sans elle, le gobelin frappe.

**Étapes**

1. Lutteuse N2 au contact du gobelin ; previsualiser puis marcher a quatre cases.
2. Meme parcours avec la lutteuse N1, qui n'a pas la capacite.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `session.combat().find(CombatantId{1})->profile.movement` vaut `8`.
- Vérifie que `session.previewOpportunities(core::tileCenter({3, 7})).empty()` est vrai.
- Vérifie que `parcours.result` vaut `core::MoveResult::Moved`.
- Vérifie que `session.combat().positionOf(CombatantId{1})` vaut `core::tileCenter({3, 7})`.
- Vérifie que `contient(session.journal(), "opportunite : ")` est faux.
- Vérifie que `contient(session.journal(), "sans attaque d'opportunite Lutteuse (Pas de danseur)")` est vrai.
- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().find(CombatantId{1})->profile.movement` vaut `6`.
- Vérifie que `session.previewOpportunities(core::tileCenter({3, 7}))` vaut `(std::vector<CombatantId>{CombatantId{2}})`.
- Vérifie que `contient(session.journal(), "opportunite : attaque Gobelin -> Lutteuse")` est vrai.
- Vérifie que `contient(session.journal(), "sans attaque d'opportunite")` est faux.

### ClassInArenaTest.UnSortEpuiseNeSeProposePlusEtUnReposLongLeRend

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_class_in_arena.cpp:326`

La lutteuse lance son trait deux fois, la troisieme est refusee « Exhausted » sans rien depenser ; le sort mineur se lance encore ; le repos long de la fiche rend les deux lancers au montage suivant.

**Étapes**

1. Lire les sorts de la lutteuse dans la session.
2. Lancer le trait, octroyer une action, relancer, octroyer, relancer.
3. Lancer le sort mineur.
4. Depenser les deux lancers sur la fiche, la reposer, remonter.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `sorts` diffère de `nullptr`.
- Vérifie que `sorts->size()` vaut `2U`.
- Vérifie que `(*sorts)[0].id` vaut `"etincelle-d-essai"`.
- Vérifie que `(*sorts)[0].uses` vaut `-1`.
- Vérifie que `(*sorts)[1].id` vaut `"trait-de-feu-d-essai"`.
- Vérifie que `(*sorts)[1].uses` vaut `2`.
- Vérifie que `trait.kind` vaut `core::AttackKind::Ranged`.
- Vérifie que `trait.modifiers.size()` vaut `2U`.
- Vérifie que `trait.modifiers[0].source` vaut `"Intelligence"`.
- Vérifie que `trait.modifiers[0].value` vaut `2`.
- Vérifie que `trait.modifiers[1].source` vaut `"maitrise"`.
- Vérifie que `trait.modifiers[1].value` vaut `2`.
- Vérifie que `trait.damage.size()` vaut `1U`.
- Vérifie que `trait.damage[0].dice` vaut `(core::Dice{.count = 2, .faces = 6, .modifier = 0})`.
- Vérifie que `trait.damage[0].type` vaut `core::DamageType::Fire`.
- Vérifie que `core::hasFlag(trait.damage[0].flags, core::DamageFlag::Spell)` est vrai.
- Vérifie que `trait.range.has_value()` est vrai.
- Vérifie que `trait.range->normal` vaut `24`.
- Vérifie que `trait.range->maximum` vaut `24`.
- Vérifie que `session.castSpell(CombatantId{2}, 1).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `(*sorts)[1].uses` vaut `1`.
- Vérifie que `contient(session.journal(), "sort Trait de feu d'essai (1 restant) : attaque Lutteuse -> Gobelin " "(Trait de feu d'essai)")` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, 1).result` vaut `core::ArenaActionResult::NoAction`.
- Vérifie que `session.castSpell(CombatantId{2}, 1).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `(*sorts)[1].uses` vaut `0`.
- Vérifie que `(*sorts)[1].available()` est faux.
- Vérifie que `session.castSpell(CombatantId{2}, 1).result` vaut `core::ArenaActionResult::Exhausted`.
- Vérifie que `session.combat().find(CombatantId{1})->economy.remaining(core::ACTION_RESOURCE)` vaut `1`.
- Vérifie que `session.castSpell(CombatantId{2}, 0).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `(*sorts)[0].uses` vaut `-1`.
- Vérifie que `contient(session.journal(), "sort Etincelle d'essai : attaque Lutteuse -> Gobelin")` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, 5).result` vaut `core::ArenaActionResult::NoSpell`.
- Vérifie que `core::spendSpellUse(fiche, "trait-de-feu-d-essai")` est vrai.
- Vérifie que `core::spendSpellUse(fiche, "trait-de-feu-d-essai")` est vrai.
- Vérifie que `core::arenaSpellsFor(fiche, *classe, optionsDEssai().spells, 2, ignores)[1].uses` vaut `0`.
- Vérifie que `core::arenaSpellsFor(fiche, *classe, optionsDEssai().spells, 2, ignores)[1].uses` vaut `2`.
- Vérifie que `ignores.empty()` est vrai.

## test_class_mage.cpp

### ClassMageTest.LaFichePreTireeSeJoueAvecSesSortsDeNiveau1

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:89`

La fiche de la page 199 connait trait de feu, lumiere, detection de la magie et projectile magique ; les deux qui se jouent en combat entrent au grimoire.

**Étapes**

1. Charger heros-mage.json.
2. Lire capacites, sorts connus, CA, et le grimoire de combat.

**Résultat attendu**

- Vérifie que `charge.warnings.empty()` est vrai.
- Vérifie que `test_support::capacityIds(charge.sheet)` vaut `(std::vector<std::string>{"simplified-spellcasting", "specific-cantrips"})`.
- Vérifie que `test_support::armorClassOf(charge.sheet, charge.inventory)` vaut `12`.
- Vérifie que `connus` vaut `(std::vector<std::string>{"fire-bolt", "light", "detect-magic", "magic-missile"})`.
- Vérifie que `grimoire.size()` vaut `2U`.
- Vérifie que `grimoire[0].id` vaut `"fire-bolt"`.
- Vérifie que `grimoire[0].mechanism` vaut `core::SpellMechanism::AttackRoll`.
- Vérifie que `grimoire[0].uses` vaut `-1`.
- Vérifie que `toucher` vaut `5`.
- Vérifie que `grimoire[0].attack.damage.front().dice` vaut `(core::Dice{.count = 1, .faces = 10, .modifier = 0})`.
- Vérifie que `grimoire[1].id` vaut `"magic-missile"`.
- Vérifie que `grimoire[1].mechanism` vaut `core::SpellMechanism::AutoHit`.
- Vérifie que `grimoire[1].uses` vaut `2`.
- Vérifie que `grimoire[1].saveDc` vaut `13`.
- Vérifie que `ignores` vaut `(std::vector<std::string>{"Lumiere", "Detection de la magie"})`.

### ClassMageTest.TraitDeFeuEstUneAttaqueDeSort

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:138`

Le Mage lance trait de feu sur un mannequin a six cases ; au niveau 5 le sort lance deux d10.

**Étapes**

1. Mage N1 contre un mannequin en (7, 3).
2. Lancer trait de feu.
3. Refaire au niveau 5.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, {test_support::dummy("Mannequin", {7, 3}, 10, 0)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `lancer.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), "sort Trait de feu : attaque " + std::string(MAGE) + " -> Mannequin")` est vrai.
- Vérifie que `sort.uses` vaut `-1`.
- Vérifie que `sort.attack.damage.front().dice.count` vaut `niveau == 5 ? 2 : 1`.

### ClassMageTest.ProjectileMagiqueToucheSansJet

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:170`

Contre une CA de 40, projectile magique touche : trois fois 1d4+1 de force ; au troisieme lancer du jour, le sort est epuise.

**Étapes**

1. Mage N1 contre un mannequin a la CA 40.
2. Lancer projectile magique ; tour suivant, le relancer ; tour suivant, le relancer.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, {test_support::dummy("Mannequin", {7, 3}, 40, 0)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `lancer.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `lancer.outcome.has_value()` est faux.
- Vérifie que `lancer.summary.find("touche sans jet (3 projectile(s))")` diffère de `std::string::npos`.
- Vérifie que `journalCount(session.journal(), "force")` vaut `1U`.
- Vérifie que `perdus` est supérieur ou égal à `6`.
- Vérifie que `perdus` est inférieur ou égal à `15`.
- Vérifie que `session.castSpell(CombatantId{2}, indice).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), "sort Projectile magique (0 restant)")` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, indice).result` vaut `core::ArenaActionResult::Exhausted`.
- Vérifie que `session.combat().find(CombatantId{1})->economy.remaining(core::ACTION_RESOURCE)` est strictement supérieur à `0`.

### ClassMageTest.ArcaneProtectionDonneTreizePlusDex

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:211`

Au niveau 2, la CA du Mage passe de 12 a 15.

**Étapes**

1. Monter le Mage de la page 199 au niveau 2.
2. Lire sa CA avec ce qu'il porte, et son profil de combat.

**Résultat attendu**

- Vérifie que `test_support::armorClassOf(charge.sheet, charge.inventory)` vaut `15`.
- Vérifie que `std::ranges::find(capacites, "arcane-protection")` diffère de `capacites.end()`.

### ClassMageTest.RayonArdentJetteUnJetParRayon

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:229`

Trois lignes « 1/3 », « 2/3 », « 3/3 » contre un mannequin solide ; contre un mannequin a 1 PV touche au premier rayon, deux rayons perdus.

**Étapes**

1. Mage N3 contre un mannequin a 200 PV, lancer rayon ardent.
2. Mage N3 contre un mannequin a 1 PV et CA 0 ; graine choisie pour que le premier rayon touche.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, {test_support::dummy("Mannequin", {7, 3}, 10, 0, 200)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, sortDe(session, "scorching-ray")).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), rang)` est vrai.
- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, sortDe(session, "scorching-ray")).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `perdus` est vrai.

### ClassMageTest.InvisibiliteGeneLAttaquantEtCesseAuSortSuivant

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:270`

Le Mage invisible est attaque avec desavantage ; son trait de feu suivant a l'avantage, puis l'invisibilite prend fin et le journal le dit.

**Étapes**

1. Mage N3 au contact d'un mannequin ; lancer invisibilite sur soi.
2. Tour du mannequin : il attaque le Mage.
3. Tour du Mage : trait de feu.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, {test_support::dummy("Mannequin", {2, 3}, 10, 5)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, sortDe(session, "invisibility")).result` vaut `core::ArenaActionResult::InvalidTarget`.
- Vérifie que `session.castSpell(CombatantId{1}, sortDe(session, "invisibility")).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `session.hasEffect(CombatantId{1}, core::SpellEffectKind::Invisible)` est vrai.
- Vérifie que `journalHas(session.journal(), "effet Invisibilite sur " + std::string(MAGE))` est vrai.
- Vérifie que `coup.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `std::ranges::find(desavantages, "cible invisible")` diffère de `desavantages.end()`.
- Vérifie que `trait.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `std::ranges::find(avantages, "attaquant invisible")` diffère de `avantages.end()`.
- Vérifie que `journalHas(session.journal(), "fin de l'effet Invisibilite sur " + std::string(MAGE) + " (il lance un sort)")` est vrai.
- Vérifie que `session.hasEffect(CombatantId{1}, core::SpellEffectKind::Invisible)` est faux.

### ClassMageTest.BouleDeFeuFaitSauvegarderToutLeMonde

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:314`

La boule de feu centree sur un mannequin prend son voisin et l'allie a trois cases, pas le mannequin eloigne ; chacun a sa ligne de sauvegarde.

**Étapes**

1. Mage N5 en (1, 3) ; mannequins en (8, 3) et (9, 4), un allie en (8, 6), un mannequin lointain en (3, 7), hors des quatre cases du rayon.
2. Boule de feu sur (8, 3).

**Résultat attendu**

- Vérifie que `session .mount(combatDe(charge, {test_support::dummy("Cible", {8, 3}, 10, 0, 200), test_support::dummy("Voisin", {9, 4}, 10, 0, 200), test_support::dummy("Allie", {8, 6}, 10, 0, 200, core::CombatSide::Allies), test_support::dummy("Lointain", {3, 7}, 10, 0, 200)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `lancer.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `lancer.summary.find("sauvegarde de Dexterite DD 14 ; 3 creature(s)")` diffère de `std::string::npos`.
- Vérifie que `lancer.summary.find("8d6")` diffère de `std::string::npos`.
- Vérifie que `journalHas(session.journal(), nom)` est vrai.
- Vérifie que `journalHas(session.journal(), " Lointain : d20")` est faux.
- Vérifie que `lointain->profile.currentHitPoints` vaut `200`.
- Vérifie que `perdus` est supérieur ou égal à `ligne.find("moitie") != std::string::npos ? 4 : 8`.

### ClassMageTest.VolDonneDouzeCasesEtCedeALaConcentration

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:358`

Le Mage se lance vol : il vole, 12 cases ; il lance ensuite invisibilite, et le vol prend fin, sa marche et ses 6 cases rendues.

**Étapes**

1. Mage N5 ; vol sur soi.
2. Tour suivant : invisibilite sur soi.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, {test_support::dummy("Mannequin", {9, 6}, 10, 0)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `marche` vaut `6`.
- Vérifie que `session.castSpell(CombatantId{1}, sortDe(session, "fly")).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `mage1->profile.locomotion` vaut `core::Locomotion::Fly`.
- Vérifie que `mage1->profile.movement` vaut `12`.
- Vérifie que `mage1->economy.remaining(core::MOVEMENT_RESOURCE)` vaut `12`.
- Vérifie que `journalHas(session.journal(), "vole, 12 cases par tour")` est vrai.
- Vérifie que `session.castSpell(CombatantId{1}, sortDe(session, "invisibility")).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), "fin de l'effet Vol sur " + std::string(MAGE) + " (concentration sur Invisibilite)")` est vrai.
- Vérifie que `apres->profile.locomotion` vaut `core::Locomotion::Walk`.
- Vérifie que `apres->profile.movement` vaut `marche`.
- Vérifie que `session.hasEffect(CombatantId{1}, core::SpellEffectKind::Fly)` est faux.

### ClassMageTest.DuNiveau1AuNiveau5LaTableSeLit

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:397`

Monter le Mage de la page 199 niveau par niveau donne les capacites et les sorts de la table, sans manquant.

**Étapes**

1. Charger la fiche N1.
2. Monter jusqu'au 5, lire capacites et sorts connus.

**Résultat attendu**

- Vérifie que `test_support::levelUpTo(fiche, niveau).empty()` est vrai.
- Vérifie que `fiche.knownSpells.size()` vaut `nombreDeSorts[static_cast<std::size_t>(niveau - 1)]`.
- Vérifie que `test_support::capacityIds(fiche)` vaut `(std::vector<std::string>{"simplified-spellcasting", "specific-cantrips", "experience", "arcane-protection", "ability-score-improvement"})`.
- Vérifie que `sort.perDay` vaut `sort.level == 0 ? 0 : 2`.
- Vérifie que `fiche.knownSpell(id)` diffère de `nullptr`.

### ClassMageTest.UnEffetInconnuEstRefuseEtUnConeNeSeJouePas

*Majeur · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:431`

Un sort a l'effet « petrify » est refuse ; un sort en cone se charge, mais aucun mecanisme ne le joue.

**Étapes**

1. Ecrire les deux sorts dans un dossier temporaire.
2. Charger.

**Résultat attendu**

- Vérifie que `catalogue.errors.size()` vaut `1U`.
- Vérifie que `catalogue.errors.front().find("petrifie.json")` diffère de `std::string::npos`.
- Vérifie que `catalogue.spells.size()` vaut `1U`.
- Vérifie que `core::spellMechanism(catalogue.spells.front()).has_value()` est faux.

### ClassMageTest.UnSortSAnnonceAuDebutEtALaFin

*Majeur · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_mage.cpp:466`

Trait de feu annonce son debut, puis son issue.

**Étapes**

1. Mage N1 contre un mannequin en (7, 3), un observateur d'actions branche.
2. Lancer trait de feu.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, {test_support::dummy("Mannequin", {7, 3}, 10, 0)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `lancer.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `annonces.size()` vaut `2U`.
- Vérifie que `annonces[0].phase` vaut `core::ArenaActionPhase::Begin`.
- Vérifie que `annonces[1].phase` vaut `core::ArenaActionPhase::End`.
- Vérifie que `annonce.actor` vaut `CombatantId{1}`.
- Vérifie que `annonce.target` vaut `CombatantId{2}`.
- Vérifie que `annonce.spell` vaut `"fire-bolt"`.
- Vérifie que `annonce.ranged` est faux.
- Vérifie que `lancer.outcome.has_value()` est vrai.
- Vérifie que `annonces[1].missed` vaut `!lancer.outcome->roll.hit`.

## test_class_priest.cpp

### ClassPriestTest.LaFichePreTireeSeJoueAvecSesSortsDeNiveau1

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_priest.cpp:85`

La fiche de la page 203 connait lumiere, flamme sacree, benediction et soin des blessures ; les trois qui se jouent en combat entrent au grimoire.

**Étapes**

1. Charger heros-priest.json.
2. Lire capacites, CA, grimoire de combat.

**Résultat attendu**

- Vérifie que `charge.warnings.empty()` est vrai.
- Vérifie que `test_support::capacityIds(charge.sheet)` vaut `(std::vector<std::string>{"simplified-spellcasting", "specific-cantrips"})`.
- Vérifie que `test_support::armorClassOf(charge.sheet, charge.inventory)` vaut `17`.
- Vérifie que `grimoire.size()` vaut `3U`.
- Vérifie que `grimoire[0].id` vaut `"sacred-flame"`.
- Vérifie que `grimoire[0].mechanism` vaut `core::SpellMechanism::SavingThrow`.
- Vérifie que `grimoire[0].saveDc` vaut `13`.
- Vérifie que `grimoire[1].id` vaut `"bless"`.
- Vérifie que `grimoire[1].maxTargets` vaut `3`.
- Vérifie que `grimoire[2].id` vaut `"cure-wounds"`.
- Vérifie que `grimoire[2].mechanism` vaut `core::SpellMechanism::Healing`.
- Vérifie que `grimoire[2].healing.has_value()` est vrai.
- Vérifie que `*grimoire[2].healing` vaut `(core::Dice{.count = 1, .faces = 8, .modifier = 3})`.
- Vérifie que `ignores` vaut `(std::vector<std::string>{"Lumiere"})`.

### ClassPriestTest.FlammeSacreeAnnuleSurUneSauvegardeReussie

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_priest.cpp:120`

La flamme sacree fait sauvegarder le mannequin ; qui reussit ne perd rien, qui rate perd les des lances ; au niveau 5, deux d8.

**Étapes**

1. Priest N1 contre un mannequin a six cases, plusieurs graines.
2. Priest N5.

**Résultat attendu**

- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `lancer.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `lancer.summary.find("sauvegarde de Dexterite DD 13 ; 1 creature(s)")` diffère de `std::string::npos`.
- Vérifie que `mannequin->profile.currentHitPoints` vaut `60`.
- Vérifie que `mannequin->profile.currentHitPoints` est strictement inférieur à `60`.
- Vérifie que `reussie && ratee` est vrai.
- Vérifie que `grimoire[0].attack.damage.front().dice.count` vaut `2`.

### ClassPriestTest.SoinDesBlessuresReleveUnAllie

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_priest.cpp:167`

La Priest soigne un allie tombe a 0 PV : il se releve avec 1d8+3 PV ; un ennemi, un allie hors de portee sont refuses.

**Étapes**

1. Priest N1, un allie au contact, un allie a cinq cases, un mannequin ennemi.
2. Porter l'allie a 0 PV.
3. Soigner l'ennemi, l'allie lointain, puis l'allie tombe.

**Résultat attendu**

- Vérifie que `session .mount(combatDe(charge, {test_support::dummy("Allie", {2, 3}, 10, 0, 20, CombatSide::Allies), test_support::dummy("Loin", {6, 3}, 10, 0, 20, CombatSide::Allies), test_support::dummy("Mannequin", {9, 6}, 10, 0)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().find(CombatantId{2})->status` vaut `core::CombatantStatus::Down`.
- Vérifie que `session.castSpell(CombatantId{4}, soin).result` vaut `core::ArenaActionResult::InvalidTarget`.
- Vérifie que `session.castSpell(CombatantId{3}, soin).result` vaut `core::ArenaActionResult::OutOfReach`.
- Vérifie que `lancer.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `lancer.summary.find("soin " + PRIEST + " -> Allie : 1d8+3")` diffère de `std::string::npos`.
- Vérifie que `allie->status` vaut `core::CombatantStatus::Standing`.
- Vérifie que `allie->profile.currentHitPoints` est supérieur ou égal à `4`.
- Vérifie que `allie->profile.currentHitPoints` est inférieur ou égal à `11`.
- Vérifie que `(*session.spells(CombatantId{1}))[soin].uses` vaut `1`.

### ClassPriestTest.BenedictionAjouteUnD4AuxJetsDeTroisAllies

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_priest.cpp:208`

La Priest benit un allie : elle et l'allie le plus proche d'elle le sont aussi, pas le lointain ; l'attaque de l'allie porte « Benediction » ; la sauvegarde de la Priest contre une boule de feu aussi ; l'effet cesse au bout de dix rounds.

**Étapes**

1. Priest N1, allies en (2, 3), (1, 4) et (1, 7) ; un Mage ennemi N5 ; un mannequin.
2. Benediction sur (2, 3).
3. Tour de l'allie : il attaque.
4. Tour du Mage : boule de feu sur la Priest.
5. Dix rounds.

**Résultat attendu**

- Vérifie que `test_support::levelUpTo(mage.sheet, 5).empty()` est vrai.
- Vérifie que `session .mount(combatDe(charge, {test_support::dummy("Allie", {2, 3}, 10, 5, 60, CombatSide::Allies), test_support::dummy("Proche", {1, 4}, 10, 5, 60, CombatSide::Allies), test_support::dummy("Lointain", {1, 7}, 10, 5, 60, CombatSide::Allies), adversaire, test_support::dummy("Mannequin", {3, 3}, 10, 0)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, sortDe(session, "bless")).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), "effet Benediction sur Allie, " + PRIEST + ", Proche : +1d4 aux jets")` est vrai.
- Vérifie que `session.hasEffect(CombatantId{4}, core::SpellEffectKind::Bless)` est faux.
- Vérifie que `session.castSpell(CombatantId{1}, boule).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `sauvegarde.find("(Benediction)")` diffère de `std::string::npos`.
- Vérifie que `coup.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `de` diffère de `modificateurs.end()`.
- Vérifie que `de->value` est supérieur ou égal à `1`.
- Vérifie que `de->value` est inférieur ou égal à `4`.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `journalHas(session.journal(), "fin de l'effet Benediction sur Allie (duree ecoulee)")` est vrai.
- Vérifie que `session.combat().round()` est inférieur ou égal à `12`.

### ClassPriestTest.ArmeSpirituelleFrappeParActionBonus

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_priest.cpp:269`

La Priest invoque l'arme spirituelle sur un mannequin a cinq cases : action bonus depensee, action gardee, 1d8+3 de force ; au tour suivant, l'arme frappe de nouveau et les lancers ne bougent pas.

**Étapes**

1. Priest N3 contre un mannequin en (6, 3).
2. Arme spirituelle ; la relancer dans le meme tour.
3. Tour suivant : la relancer.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, {test_support::dummy("Mannequin", {6, 3}, 10, 0, 200)})) .refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `sort.bonusAction` est vrai.
- Vérifie que `sort.attack.kind` vaut `core::AttackKind::Melee`.
- Vérifie que `sort.attack.damage.front().dice` vaut `(core::Dice{.count = 1, .faces = 8, .modifier = 3})`.
- Vérifie que `session.castSpell(CombatantId{2}, arme).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `helga->economy.remaining(core::BONUS_ACTION_RESOURCE)` vaut `0`.
- Vérifie que `helga->economy.remaining(core::ACTION_RESOURCE)` vaut `1`.
- Vérifie que `session.hasEffect(CombatantId{1}, core::SpellEffectKind::SpiritualWeapon)` est vrai.
- Vérifie que `journalHas(session.journal(), "arme invoquee")` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, arme).result` vaut `core::ArenaActionResult::NoAction`.
- Vérifie que `session.castSpell(CombatantId{2}, arme).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), "sort Arme spirituelle (l'arme frappe de nouveau)")` est vrai.
- Vérifie que `(*session.spells(CombatantId{1}))[arme].uses` vaut `1`.

### ClassPriestTest.DuNiveau1AuNiveau5LaTableSeLit

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_priest.cpp:310`

Monter la Priest de la page 203 jusqu'au niveau 5 donne ses capacites et ses neuf sorts ; epargner les mourants et revigorer entrent au grimoire de combat (LOT-137) ; restauration inferieure ne se joue pas et declare ce qu'elle attend.

**Étapes**

1. Monter de 1 a 5.
2. Lire capacites, sorts connus, grimoire de combat.

**Résultat attendu**

- Vérifie que `test_support::levelUpTo(charge.sheet, niveau).empty()` est vrai.
- Vérifie que `test_support::capacityIds(charge.sheet)` vaut `(std::vector<std::string>{"simplified-spellcasting", "specific-cantrips", "experience", "ability-score-improvement"})`.
- Vérifie que `charge.sheet.knownSpells.size()` vaut `9U`.
- Vérifie que `grimoire.size()` vaut `6U`.
- Vérifie que `ignores.size()` vaut `3U`.
- Vérifie que `std::ranges::any_of(grimoire, [id](const core::ArenaSpell& sort) { return sort.id == id; })` est vrai.
- Vérifie que `catalogues.options.spells.find(id)->requiredMechanisms.empty()` est vrai.
- Vérifie que `restauration` diffère de `nullptr`.
- Vérifie que `restauration->requiredMechanisms.empty()` est faux.

## test_class_scoundrel.cpp

### ClassScoundrelTest.LaFichePreTireePorteSesCapacitesDeNiveau1

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_scoundrel.cpp:90`

La fiche de la page 207 se charge avec Sneak Attack Simplified et Scoundrel's Agility ; sa vitesse est de 12 m, huit cases.

**Étapes**

1. Charger heros-scoundrel.json.
2. Lire capacites, vitesse, CA, profil.

**Résultat attendu**

- Vérifie que `charge.warnings.empty()` est vrai.
- Vérifie que `test_support::capacityIds(charge.sheet)` vaut `(std::vector<std::string>{"sneak-attack-simplified", "scoundrels-agility"})`.
- Vérifie que `charge.sheet.effectiveSpeedMeters()` vaut `12.0F` (comparaison flottante).
- Vérifie que `core::profileFor(charge.sheet).movement` vaut `8`.
- Vérifie que `test_support::armorClassOf(charge.sheet, charge.inventory)` vaut `14`.

### ClassScoundrelTest.LAttaqueSournoiseDemandeUnAllieAuContact

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_scoundrel.cpp:111`

Avec un allie au contact du mannequin, la rapiere ajoute 1d8 nomme ; une seconde touche du meme tour n'ajoute rien ; sans allie au contact, ou avec un allie a terre, rien.

**Étapes**

1. Scoundrel N1, mannequin CA 0, allie en (5, 3).
2. Attaquer, octroyer une action, rattaquer.
3. Refaire avec l'allie en (8, 7), puis avec l'allie au contact mais a terre.

**Résultat attendu**

- Vérifie que `coup.has_value()` est vrai.
- Vérifie que `desSournois(*coup)` vaut `1U`.
- Vérifie que `sournois->clause.dice` vaut `(core::Dice{.count = 1, .faces = 8, .modifier = 0})`.
- Vérifie que `sournois->clause.type` vaut `core::DamageType::Piercing`.
- Vérifie que `journalLine(session.journal(), "attaque " + SCOUNDREL + " -> Mannequin") .find("perforant (Sneak Attack Simplified)")` diffère de `std::string::npos`.
- Vérifie que `second.outcome.has_value()` est vrai.
- Vérifie que `desSournois(*second.outcome)` vaut `0U`.
- Vérifie que `coup.has_value()` est vrai.
- Vérifie que `desSournois(*coup)` vaut `0U`.
- Vérifie que `session.combat().counters().value(core::CounterScope::Turn, "1", "sneak-attack-simplified")` vaut `0`.
- Vérifie que `session.mount(bout).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `coup.has_value()` est vrai.
- Vérifie que `desSournois(*coup)` vaut `0U`.

### ClassScoundrelTest.LesDesSournoisMontentAvecLaTable

*Majeur · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_scoundrel.cpp:175`

Au niveau 3 la capacite active donne 2d8, au niveau 5 3d8, et une seule a la fois.

**Étapes**

1. Monter le Scoundrel au niveau 3, puis 5.
2. Lire les des en plus.

**Résultat attendu**

- Vérifie que `supplements.size()` vaut `1U`.
- Vérifie que `supplements.front().dice` vaut `(core::Dice{.count = des, .faces = 8, .modifier = 0})`.
- Vérifie que `supplements.front().oncePerTurn` est vrai.
- Vérifie que `supplements.front().allyAdjacentToTarget` est vrai.

### ClassScoundrelTest.ScoundrelsAgilityEviteLesAttaquesDOpportunite

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_scoundrel.cpp:197`

La Scoundrel quitte l'allonge du mannequin sans etre frappee, et le journal nomme la capacite ; au niveau 5 sa CA passe a 16.

**Étapes**

1. Scoundrel N1 au contact d'un mannequin qui frappe.
2. Marcher a quatre cases.
3. Lire la CA au niveau 5.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, std::nullopt)).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.previewOpportunities(core::tileCenter({0, 3})).empty()` est vrai.
- Vérifie que `session.move(core::tileCenter({0, 3})).result` vaut `core::MoveResult::Moved`.
- Vérifie que `journalHas(session.journal(), "opportunite :")` est faux.
- Vérifie que `journalHas(session.journal(), "sans attaque d'opportunite " + SCOUNDREL + " (Scoundrel's Agility)")` est vrai.
- Vérifie que `test_support::armorClassOf(niveau5.sheet, niveau5.inventory)` vaut `16`.
- Vérifie que `niveau5.sheet.effectiveSpeedMeters()` vaut `12.0F` (comparaison flottante).
- Vérifie que `core::opportunityImmunityFrom(niveau5.sheet.capacities).has_value()` est vrai.

### ClassScoundrelTest.AdventurersAptitudeAjouteAuxTestsMaitrises

*Majeur · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_scoundrel.cpp:227`

Au niveau 3, Acrobaties (maitrisee) passe de +5 a +6 ; Athletisme (non maitrisee) reste a -1.

**Étapes**

1. Scoundrel N1 puis N3.
2. Lire les modificateurs de competence.

**Résultat attendu**

- Vérifie que `core::skillModifier(n1.sheet, table, competences, "acrobatics").value` vaut `5`.
- Vérifie que `core::skillModifier(n3.sheet, table, competences, "acrobatics").value` vaut `6`.
- Vérifie que `core::skillModifier(n1.sheet, table, competences, "athletics").value` vaut `-1`.
- Vérifie que `core::skillModifier(n3.sheet, table, competences, "athletics").value` vaut `-1`.

### ClassScoundrelTest.PreciseStrikerAjouteUnAuJet

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_scoundrel.cpp:249`

Au niveau 5, le jet de la rapiere porte « + 1 (Precise Striker) ».

**Étapes**

1. Scoundrel N5 contre le mannequin.
2. Attaquer.

**Résultat attendu**

- Vérifie que `session.mount(combatDe(charge, std::nullopt)).refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `coup.outcome.has_value()` est vrai.
- Vérifie que `bonus` diffère de `modificateurs.end()`.
- Vérifie que `bonus->value` vaut `1`.
- Vérifie que `journalHas(session.journal(), "+ 1 (Precise Striker)")` est vrai.

### ClassScoundrelTest.DuNiveau1AuNiveau5LaTableSeLit

*Critique · Unitaire · Classes* — `Source/Test/Unit/Core/Combat/test_class_scoundrel.cpp:272`

Monter la Scoundrel de la page 207 jusqu'au niveau 5 donne les capacites de la table, chaque amelioration remplacant la precedente.

**Étapes**

1. Monter de 1 a 5, lire les capacites.

**Résultat attendu**

- Vérifie que `test_support::levelUpTo(charge.sheet, niveau).empty()` est vrai.
- Vérifie que `test_support::capacityIds(charge.sheet)` vaut `(std::vector<std::string>{"experience", "adventurers-aptitude", "ability-score-improvement", "sneak-attack-simplified-3d8", "scoundrels-agility-armor", "precise-striker"})`.
- Vérifie que `core::proficiencyBonus(charge.sheet, test_support::rpgCatalogs().experience)` vaut `3`.

## test_combat_preview.cpp

### CombatPreviewTest.LaPrevisualisationEstLeJet

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_preview.cpp:85`

Ce que l'ecran montre avant l'attaque -- CA abri compris, posture, sources d'avantage et de desavantage, chance de toucher -- est exactement ce que le jet jette.

**Étapes**

1. Une attaque au contact d'un ennemi pris en tenaille, dans une arene a tenaille.
2. Un tir a longue portee, a travers un allie, sur une cible qui esquive.
3. Une cible hors de portee.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `apercu.has_value()` est vrai.
- Vérifie que `apercu->stance` vaut `core::RollStance::Advantage`.
- Vérifie que `apercu->advantages` vaut `(std::vector<std::string>{"prise en tenaille"})`.
- Vérifie que `apercu->requiredRoll` vaut `8`.
- Vérifie que `apercu->hitPercent()` vaut `88`.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{3}`.
- Vérifie que `session.dodge()` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `apercu.has_value()` est vrai.
- Vérifie que `apercu->cover` vaut `core::Cover::Half`.
- Vérifie que `apercu->armorClass` vaut `14`.
- Vérifie que `apercu->stance` vaut `core::RollStance::Disadvantage`.
- Vérifie que `apercu->disadvantages.size()` vaut `2U`.
- Vérifie que `session.start()` est vrai.
- Vérifie que `apercu.has_value()` est vrai.
- Vérifie que `apercu->check` vaut `core::TargetCheck::OutOfReach`.
- Vérifie que `apercu->hitChance` vaut `0`.
- Vérifie que `core::firstValidAttack(session, CombatantId{2}).has_value()` est faux.
- Vérifie que `core::previewAttack(session, CombatantId{2}, 3).has_value()` est faux.

### CombatPreviewTest.LeDeplacementSePrevisualiseEtLOpportuniteSeDecline

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_preview.cpp:157`

La previsualisation d'un deplacement donne le chemin, le deplacement restant et qui frappera en chemin ; un combattant dont le joueur laisse passer les opportunites ne frappe pas.

**Étapes**

1. Une heroine au contact d'un ogre ; previsualiser un pas qui sort de son allonge.
2. Le joueur dit que l'ogre laisse passer ; previsualiser, puis jouer le pas.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `pas.path.has_value()` est vrai.
- Vérifie que `pas.path->length` vaut `3.0F`, à `0.01F` près.
- Vérifie que `pas.movementLeft` vaut `6.0F`, à `0.01F` près.
- Vérifie que `pas.opportunities` vaut `(std::vector<CombatantId>{CombatantId{2}})`.
- Vérifie que `core::previewMove(session, core::tileCenter({9, 9})).path.has_value()` est faux.
- Vérifie que `session.takesOpportunities(CombatantId{2})` est vrai.
- Vérifie que `core::previewMove(session, core::tileCenter({2, 5})).opportunities.empty()` est vrai.
- Vérifie que `session.move(core::tileCenter({2, 5})).result` vaut `core::MoveResult::Moved`.
- Vérifie que `std::ranges::none_of( session.journal(), [](const std::string& l) { return l.starts_with("opportunite : "); })` est vrai.
- Vérifie que `session.combat().find(CombatantId{2})->economy.remaining(core::REACTION_RESOURCE)` vaut `1`.
- Vérifie que `session.takesOpportunities(CombatantId{2})` est faux.

### CombatPreviewTest.LesCapacitesEntrentDansLaPrevisualisation

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_preview.cpp:199`

Le bonus au jet d'une capacite s'ajoute au jet requis ; les des d'une capacite a condition entrent dans l'esperance quand la condition tient, et la previsualisation nomme la capacite et la raison quand elle ne joue pas.

**Étapes**

1. Une heroine a « +2 au jet » et « 1d6 en plus, une fois par tour, si un allie est au contact de la cible » ; un allie au contact d'une cible, une autre cible seule.
2. Previsualiser sur chaque cible.
3. Frapper la premiere, previsualiser encore.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `flanque.has_value()` est vrai.
- Vérifie que `flanque->attackBonus` vaut `6`.
- Vérifie que `flanque->requiredRoll` vaut `6`.
- Vérifie que `flanque->capacityModifiers.size()` vaut `1U`.
- Vérifie que `flanque->capacityModifiers.front().source` vaut `"Viser juste"`.
- Vérifie que `flanque->extraDamage.size()` vaut `1U`.
- Vérifie que `flanque->extraDamage.front().source` vaut `"Attaque sournoise"`.
- Vérifie que `flanque->extraDamage.front().applies` est vrai.
- Vérifie que `seul.has_value()` est vrai.
- Vérifie que `seul->extraDamage.size()` vaut `1U`.
- Vérifie que `seul->extraDamage.front().applies` est faux.
- Vérifie que `seul->extraDamage.front().reason.empty()` est faux.
- Vérifie que `seul->hitChance` vaut `flanque->hitChance`.
- Vérifie que `flanque->expectedDamage` est strictement supérieur à `seul->expectedDamage`.
- Vérifie que `flanque->expectedDamage - seul->expectedDamage` vaut `flanque->hitChance * 7 + core::criticalChance(20, flanque->stance) * 7`.
- Vérifie que `coup.outcome.has_value()` est vrai.
- Vérifie que `apres.has_value()` est vrai.
- Vérifie que `apres->extraDamage.size()` vaut `1U`.
- Vérifie que `apres->extraDamage.front().applies` est faux.
- Vérifie que `apres->extraDamage.front().reason` vaut `"deja jouee ce tour"`.
- Vérifie que `apres->extraDamage.front().applies` est vrai.

## test_combat_space.cpp

### EspaceDeCombatTest.UneCreatureEstUnCylindreALaTailleDuManuel

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:36`

Une creature est un cylindre a la taille du Manuel.

**Étapes**

1. Lire le rayon et la hauteur des tailles M, G, TG, Gig.

**Résultat attendu**

- Vérifie que `core::creatureRadius(CreatureSize::Medium)` vaut `0.75f` (comparaison flottante).
- Vérifie que `core::creatureHeight(CreatureSize::Medium)` vaut `1.5f` (comparaison flottante).
- Vérifie que `core::creatureRadius(CreatureSize::Large)` vaut `1.5f` (comparaison flottante).
- Vérifie que `core::creatureRadius(CreatureSize::Gargantuan)` vaut `3.0f` (comparaison flottante).
- Vérifie que `core::creatureHeight(CreatureSize::Huge)` vaut `4.5f` (comparaison flottante).

### EspaceDeCombatTest.LAllongeSeMesureEntreLesBords

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:52`

L'allonge se mesure entre les bords des volumes.

**Étapes**

1. Deux creatures M a 2,9 m puis 3,1 m de centre a centre ; une allonge de 3 m a 4,5 m.

**Résultat attendu**

- Vérifie que `core::inReach(medium(0, 0), medium(2.9f, 0))` est vrai.
- Vérifie que `core::inReach(medium(0, 0), medium(3.1f, 0))` est faux.
- Vérifie que `core::inReach(medium(0, 0), medium(4.5f, 0), 3.0f)` est vrai.
- Vérifie que `core::edgeDistance(medium(0, 0), medium(1.0f, 0))` vaut `0.0f` (comparaison flottante).

### EspaceDeCombatTest.LAllongeCompteLaHauteur

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:71`

L'allonge compte la hauteur.

**Étapes**

1. Une cible 2,9 m puis 3,1 m plus haut, au meme point du sol.

**Résultat attendu**

- Vérifie que `core::inReach(medium(0, 0), medium(0, 0, 3.1f))` est faux.
- Vérifie que `core::inReach(medium(0, 0), medium(0, 0, 2.9f))` est vrai.

### EspaceDeCombatTest.DeuxVolumesSeRecouvrentOuNon

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:85`

Deux volumes se recouvrent ou non.

**Étapes**

1. Deux creatures M a 1 m, a 1,5 m, et l'une au-dessus de l'autre.

**Résultat attendu**

- Vérifie que `core::overlap(medium(0, 0), medium(1.0f, 0))` est vrai.
- Vérifie que `core::overlap(medium(0, 0), medium(1.5f, 0))` est faux.
- Vérifie que `core::overlap(medium(0, 0), medium(0, 0, 1.5f))` est faux.

### EspaceDeCombatTest.LaTenailleParAngleRejoueLaLigneDesCentresDuGuide

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:99`

La tenaille par angle rejoue la ligne des centres du Guide.

**Étapes**

1. Les huit cases adjacentes a une cible, deux a deux.

**Résultat attendu**

- Vérifie que `core::flanksByAngle(n, s, target)` est vrai.
- Vérifie que `core::flanksByAngle(n, se, target)` est vrai.
- Vérifie que `core::flanksByAngle(n, sw, target)` est vrai.
- Vérifie que `core::flanksByAngle(ne, s, target)` est vrai.
- Vérifie que `core::flanksByAngle(ne, sw, target)` est vrai.
- Vérifie que `core::flanksByAngle(n, e, target)` est faux.
- Vérifie que `core::flanksByAngle(n, ne, target)` est faux.
- Vérifie que `core::flanksByAngle(ne, se, target)` est faux.
- Vérifie que `core::flanksByAngle(target, s, target)` est faux.

### EspaceDeCombatTest.LAvantageDeHauteurDemandeUneCase

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:131`

L'avantage de hauteur demande une case d'ecart.

**Étapes**

1. Un attaquant 1,5 m, 1,2 m plus haut, puis plus bas que sa cible.

**Résultat attendu**

- Vérifie que `core::hasHighGround(medium(0, 0, 1.5f), medium(2, 0, 0))` est vrai.
- Vérifie que `core::hasHighGround(medium(0, 0, 1.2f), medium(2, 0, 0))` est faux.
- Vérifie que `core::hasHighGround(medium(0, 0, 0), medium(2, 0, 1.5f))` est faux.

### EspaceDeCombatTest.UneSphereToucheCeQuElleCroise

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:144`

Une sphere touche ce qu'elle croise.

**Étapes**

1. Une boule de feu de 6 m ; des creatures M a 6,5 m, 7 m, et en hauteur a 5 m et 6,5 m.

**Résultat attendu**

- Vérifie que `core::shapeHits(fireball, medium(6.5f, 0))` est vrai.
- Vérifie que `core::shapeHits(fireball, medium(7.0f, 0))` est faux.
- Vérifie que `core::shapeHits(fireball, medium(0, 0, 5.0f))` est vrai.
- Vérifie que `core::shapeHits(fireball, medium(0, 0, 6.5f))` est faux.

### EspaceDeCombatTest.UnConeSElargitAvecSaLongueur

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:164`

Un cone s'elargit avec sa longueur.

**Étapes**

1. Un souffle de 4,5 m ; des creatures dans l'axe, sur le cote a 2,9 m et 2 m, derriere l'origine, au-dela du bout ; un cone sans direction.

**Résultat attendu**

- Vérifie que `core::shapeHits(breath, medium(3.0f, 0))` est vrai.
- Vérifie que `core::shapeHits(breath, medium(3.0f, 2.9f))` est faux.
- Vérifie que `core::shapeHits(breath, medium(3.0f, 2.0f))` est vrai.
- Vérifie que `core::shapeHits(breath, medium(-1.5f, 0))` est faux.
- Vérifie que `core::shapeHits(breath, medium(6.0f, 0))` est faux.
- Vérifie que `core::shapeHits(none, medium(1.0f, 0))` est faux.

### EspaceDeCombatTest.UneLigneEtUnCubeSontDesRectangles

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:190`

Une ligne et un cube sont des rectangles.

**Étapes**

1. Un eclair de 30 m sur 1,5 m ; un cube de 4,5 m d'arete, l'origine au milieu d'une face.

**Résultat attendu**

- Vérifie que `core::shapeHits(bolt, medium(0, 20.0f))` est vrai.
- Vérifie que `core::shapeHits(bolt, medium(1.4f, 20.0f))` est vrai.
- Vérifie que `core::shapeHits(bolt, medium(1.6f, 20.0f))` est faux.
- Vérifie que `core::shapeHits(cube, medium(4.0f, 2.0f))` est vrai.
- Vérifie que `core::shapeHits(cube, medium(4.0f, 3.1f))` est faux.
- Vérifie que `core::shapeHits(cube, medium(5.5f, 0))` est faux.

### EspaceDeCombatTest.UnCylindreALaHauteurDeSaDonnee

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:216`

Un cylindre a la hauteur de sa donnee.

**Étapes**

1. Un cylindre de 3 m de rayon et 6 m de haut ; des creatures a 3,5 m, 4 m, et a 5 m puis 6,5 m de haut.

**Résultat attendu**

- Vérifie que `core::shapeHits(column, medium(3.5f, 0))` est vrai.
- Vérifie que `core::shapeHits(column, medium(4.0f, 0))` est faux.
- Vérifie que `core::shapeHits(column, medium(0, 0, 5.0f))` est vrai.
- Vérifie que `core::shapeHits(column, medium(0, 0, 6.5f))` est faux.

### EspaceDeCombatTest.LesVolumesDansUneZoneSontRendusParIndice

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:234`

Les volumes dans une zone sont rendus par indice croissant.

**Étapes**

1. Trois volumes, une sphere de 3 m.

**Résultat attendu**

- Vérifie que `core::volumesInEffect(fireball, volumes)` vaut `expected`.

### EspaceDeCombatTest.UnSegmentTraverseUnCorpsMaisPasSesExtremites

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:248`

Un segment traverse un corps mais pas ses extremites.

**Étapes**

1. Un segment a travers un corps, a cote, au-dessus de la tete, et un qui part du corps.

**Résultat attendu**

- Vérifie que `core::segmentCrosses(a, b, body)` est vrai.
- Vérifie que `core::segmentCrosses(a, {6, 2.0f, 0.75f}, body)` est faux.
- Vérifie que `core::segmentCrosses({0, 0, 2.0f}, {6, 0, 2.0f}, body)` est faux.
- Vérifie que `core::segmentCrosses({3.0f, 0, 0.75f}, b, body)` est faux.

### EspaceDeCombatTest.LesPorteesDuCorpusSeConvertissent

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_combat_space.cpp:269`

Les portees du corpus se convertissent.

**Étapes**

1. 6 cases en metres, 9 m en cases, l'allonge.

**Résultat attendu**

- Vérifie que `core::metersFromTiles(6.0f)` vaut `9.0f` (comparaison flottante).
- Vérifie que `core::tilesFromMeters(9.0f)` vaut `6.0f` (comparaison flottante).
- Vérifie que `core::MELEE_REACH_METERS` vaut `1.5f` (comparaison flottante).

## test_combat_state.cpp

### CombatStateTest.LInitiativeEstJeteeUneFoisEtLOrdreTient

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:276`

L'ordre d'initiative est jete au debut et reste stable de round en round.

**Étapes**

1. Engager trois combattants, graine 7.
2. Jouer trois rounds en terminant chaque tour.
3. Rejouer le meme combat a la meme graine.

**Résultat attendu**

- Vérifie que `combat.start(hasard)` est vrai.
- Vérifie que `c->initiativeRoll.has_value()` est vrai.
- Vérifie que `c->initiativeRoll->total` vaut `c->initiativeRoll->keptDie + place.modifier`.
- Vérifie que `place.total` vaut `c->initiativeRoll->total`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.round()` vaut `4`.
- Vérifie que `combat.turnOrder().entries().size()` vaut `initial.size()`.
- Vérifie que `combat.turnOrder().entries()[rang].combatant` vaut `initial[rang].combatant`.
- Vérifie que `combat.turnOrder().entries()[rang].total` vaut `initial[rang].total`.
- Vérifie que `tours[rang]` vaut `initial[rang].combatant`.
- Vérifie que `tours[rang + 3]` vaut `initial[rang].combatant`.
- Vérifie que `tours[rang + 6]` vaut `initial[rang].combatant`.
- Vérifie que `des` vaut `desRejeu`.
- Vérifie que `tours` vaut `toursRejeu`.

### CombatStateTest.LeTourNeFinitQueSurDemande

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:327`

La fin d'un tour est explicite : epuiser ses ressources ne la declenche pas.

**Étapes**

1. Heroine puis loup.
2. Depenser action, action bonus, reaction et les six cases de l'heroine.
3. Terminer le tour, puis celui du loup.
4. Tenter de terminer un tour depuis un abonne au debut de tour.

**Résultat attendu**

- Vérifie que `combat.endTurn()` est faux.
- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.start(des)` est faux.
- Vérifie que `combat.activeCombatant()` vaut `heroine`.
- Vérifie que `combat.spend(core::ACTION_RESOURCE)` est vrai.
- Vérifie que `combat.spend(core::BONUS_ACTION_RESOURCE)` est vrai.
- Vérifie que `combat.spend(core::REACTION_RESOURCE)` est vrai.
- Vérifie que `combat.spend(core::MOVEMENT_RESOURCE, 6)` est vrai.
- Vérifie que `combat.spend(core::ACTION_RESOURCE)` est faux.
- Vérifie que `combat.phase()` vaut `core::CombatPhase::TurnActive`.
- Vérifie que `combat.activeCombatant()` vaut `heroine`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `loup`.
- Vérifie que `combat.round()` vaut `1`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `heroine`.
- Vérifie que `combat.round()` vaut `2`.
- Vérifie que `combat.economy(heroine)->remaining(core::ACTION_RESOURCE)` vaut `1`.
- Vérifie que `combat.economy(heroine)->remaining(core::MOVEMENT_RESOURCE)` vaut `6`.
- Vérifie que `finsDepuisUnAbonne` vaut `(std::vector<bool>{false, false, false})`.

### CombatStateTest.LaReactionRevientAuDebutDuTourDeSonPorteur

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:373`

Une reaction depensee hors de son tour ne revient qu'au debut du tour de son porteur.

**Étapes**

1. Ordre : heroine, loup, compagnon.
2. Pendant le tour de l'heroine, le compagnon depense sa reaction.
3. Terminer le tour de l'heroine, puis celui du loup.

**Résultat attendu**

- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.economy(compagnon)->spend(core::REACTION_RESOURCE)` est vrai.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `loup`.
- Vérifie que `combat.economy(compagnon)->remaining(core::REACTION_RESOURCE)` vaut `0`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `compagnon`.
- Vérifie que `combat.economy(compagnon)->remaining(core::REACTION_RESOURCE)` vaut `1`.

### CombatStateTest.UneVictoireQuandPlusAucunEnnemiNEstDebout

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:403`

Un combat se termine par une victoire quand plus aucun ennemi n'est debout.

**Étapes**

1. Deux allies contre deux gobelins.
2. Abattre un gobelin, puis faire fuir l'autre... non : abattre le second.
3. Tenter de jouer apres la fin.

**Résultat attendu**

- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.find(premier)->status` vaut `core::CombatantStatus::Down`.
- Vérifie que `combat.phase()` diffère de `core::CombatPhase::Ended`.
- Vérifie que `combat.find(second)->profile.currentHitPoints` vaut `0`.
- Vérifie que `combat.phase()` vaut `core::CombatPhase::Ended`.
- Vérifie que `combat.outcome()` vaut `core::CombatOutcome::Victory`.
- Vérifie que `combat.activeCombatant().has_value()` est faux.
- Vérifie que `combat.endTurn()` est faux.
- Vérifie que `std::count(journal.begin(), journal.end(), "issue")` vaut `1`.

### CombatStateTest.UneDefaiteQuandTousLesAlliesSontATerre

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:439`

Un combat se termine par une defaite quand tous les allies sont a terre ; si les deux camps tombent ensemble, c'est une defaite.

**Étapes**

1. Deux allies contre un ogre ; abattre un allie, puis l'autre.
2. Second combat : une meme salve abat le premier allie, l'ogre et le second allie.

**Résultat attendu**

- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.outcome().has_value()` est faux.
- Vérifie que `combat.outcome()` vaut `core::CombatOutcome::Defeat`.
- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.outcome()` vaut `core::CombatOutcome::Defeat`.

### CombatStateTest.UneFuiteQuandLesAlliesQuittentLaZone

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:481`

Un combat se termine par une fuite quand plus aucun allie n'est debout et que l'un d'eux est parti.

**Étapes**

1. Rencontre dont on ne fuit pas : l'heroine tente de sortir.
2. La rendre fuyable ; l'heroine sort pendant son tour ; un gobelin sort aussi.
3. Le compagnon tombe.

**Résultat attendu**

- Vérifie que `combat.withdraw(heroine)` vaut `core::WithdrawResult::NotInCombat`.
- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `heroine`.
- Vérifie que `combat.withdraw(heroine)` vaut `core::WithdrawResult::NotEscapable`.
- Vérifie que `combat.withdraw(heroine)` vaut `core::WithdrawResult::Withdrawn`.
- Vérifie que `journal` vaut `(std::vector<std::string>{"sortie 1", "fin 1", "debut 2"})`.
- Vérifie que `combat.positionOf(heroine).has_value()` est faux.
- Vérifie que `combat.turnOrder().contains(heroine)` est faux.
- Vérifie que `combat.withdraw(heroine)` vaut `core::WithdrawResult::NotInCombat`.
- Vérifie que `combat.withdraw(gobelin)` vaut `core::WithdrawResult::Withdrawn`.
- Vérifie que `combat.outcome().has_value()` est faux.
- Vérifie que `combat.activeCombatant()` vaut `compagnon`.
- Vérifie que `combat.outcome()` vaut `core::CombatOutcome::Flight`.

### CombatStateTest.QuatreAlliesSansHerosUnique

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:529`

Un combat a quatre allies se deroule sans qu'aucun ne soit traite a part.

**Étapes**

1. Quatre allies contre deux ennemis, graine 11.
2. Jouer trois rounds.
3. Abattre trois allies, jouer un round, puis abattre les ennemis.

**Résultat attendu**

- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.turnOrder().entries().size()` vaut `6U`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `tours.size()` vaut `6U`.
- Vérifie que `nombre` vaut `3`.
- Vérifie que `combat.outcome().has_value()` est faux.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `joueurs` vaut `(std::vector<CombatantId>{allies[3], loup, ours})`.
- Vérifie que `combat.outcome()` vaut `core::CombatOutcome::Victory`.

### CombatStateTest.UnCombatACinqSeDerouleSansFenetreEtSeRejoue

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:580`

Une escarmouche a cinq combattants va du premier round a une fin, et le rejeu a graine fixe est exact.

**Étapes**

1. Deux allies contre trois gobelins, sur une carte a pilier, dans l'espace en metres.
2. Chaque combattant marche vers la place qui le rapproche le plus de l'ennemi le plus proche, frappe a l'allonge (1,5 m entre les bords), termine son tour.
3. Rejouer a la meme graine, puis a une autre.

**Résultat attendu**

- Vérifie que `issue.has_value()` est vrai.
- Vérifie que `rounds` est supérieur ou égal à `2`.
- Vérifie que `std::find(journal.begin(), journal.end(), debut)` diffère de `journal.end()`.
- Vérifie que `std::count(journal.begin(), journal.end(), "issue")` vaut `1`.
- Vérifie que `escarmouche(2026, issueRejeu, roundsRejeu)` vaut `journal`.
- Vérifie que `issueRejeu` vaut `issue`.
- Vérifie que `roundsRejeu` vaut `rounds`.
- Vérifie que `escarmouche(7, autreIssue, autresRounds)` diffère de `journal`.

### CombatStateTest.UnRenfortEntreEnCoursDeCombat

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:616`

Un renfort appele au rang 0 joue au round suivant ; un combattant qui entre apres la place en cours joue ce round-ci.

**Étapes**

1. Heroine (tres haute initiative), repere « renforts » au rang 0, chef (tres basse).
2. Au repere du round 1, faire entrer un gobelin a l'initiative 0.
3. Au round 2, pendant le tour de l'heroine, faire entrer un loup d'initiative plus basse que tout, puis un combattant a la place du loup.

**Résultat attendu**

- Vérifie que `combat.addInitiativeMarker({.count = 0, .name = "renforts"})` est vrai.
- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.round()` vaut `2`.
- Vérifie que `loup.combatant` vaut `CombatantId{4}`.
- Vérifie que `refuse.combatant.has_value()` est faux.
- Vérifie que `refuse.placement` vaut `core::PlacementResult::Occupied`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `journal` vaut `attendu`.
- Vérifie que `combat.combatants().size()` vaut `4U`.

### CombatStateTest.LesCrochetsSAnnoncentDansLOrdre

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:672`

Les crochets du combat s'annoncent dans un ordre fixe, repere fixe et acteur flottant compris.

**Étapes**

1. Heroine (haute initiative), acteur flottant, gobelin (basse), repere « repaire » au rang 20.
2. Round 1 : l'acteur flottant demande a jouer pendant le tour de l'heroine ; une attaque est declaree.
3. Round 2 : il ne demande rien.

**Résultat attendu**

- Vérifie que `combat.addInitiativeMarker({.count = 20, .name = "repaire"})` est vrai.
- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `demandeAvantLePremierTour` vaut `false`.
- Vérifie que `combat.turnOrder().contains(flottant)` est faux.
- Vérifie que `combat.find(flottant)->initiativeRoll.has_value()` est faux.
- Vérifie que `combat.interject(heroine)` est faux.
- Vérifie que `combat.interject(flottant)` est vrai.
- Vérifie que `combat.interject(flottant)` est faux.
- Vérifie que `combat.declareAttack(heroine, gobelin)` est vrai.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `journal` vaut `attendu`.

### CombatStateTest.UnCombattantATerrePasseSonTour

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:722`

Les tours d'un combattant a terre sont passes ; tomber pendant son tour le termine.

**Étapes**

1. Ordre : heroine, loup, compagnon, ours.
2. Abattre le compagnon pendant le tour de l'heroine, puis terminer les tours.
3. Le relever ; au round 2, abattre le loup pendant son propre tour.

**Résultat attendu**

- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `loup`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `ours`.
- Vérifie que `combat.find(compagnon)->status` vaut `core::CombatantStatus::Standing`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `heroine`.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `loup`.
- Vérifie que `journal` vaut `(std::vector<std::string>{"fin 2", "debut 3"})`.
- Vérifie que `combat.activeCombatant()` vaut `compagnon`.

### CombatStateTest.LeDeplacementPaieLeCheminEtLesCampsDisentQuiSeTraverse

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:765`

Le deplacement se paie sur le budget restant ; on traverse un allie, un ennemi a deux tailles d'ecart, en terrain difficile, sans finir dans leur espace ; jamais un ennemi de taille voisine.

**Étapes**

1. Couloir de 7 cases sur 1 (10,5 m sur 1,5 m) : heroine (8 cases, 12 m) au centre de la case 0, compagnon en 1, rat tres petit ennemi en 3.
2. Aller en 1, en 5, en 2, puis en 4.
3. Meme couloir avec un gobelin de taille M a la place du rat.

**Résultat attendu**

- Vérifie que `combat->move(tile(2, 0)).result` vaut `core::MoveResult::NoActiveTurn`.
- Vérifie que `combat->start(des)` est vrai.
- Vérifie que `combat->movementLeft()` vaut `12.0f`, à `CM` près.
- Vérifie que `places.empty()` est faux.
- Vérifie que `proche(places.front().point, tile(0, 0))` est vrai.
- Vérifie que `finales.size()` vaut `2U`.
- Vérifie que `proche(finales[0], tile(2, 0))` est vrai.
- Vérifie que `proche(finales[1], tile(4, 0))` est vrai.
- Vérifie que `combat->routeTo(tile(1, 0)).has_value()` est faux.
- Vérifie que `combat->move(tile(1, 0)).result` vaut `core::MoveResult::Unreachable`.
- Vérifie que `combat->move(tile(5, 0)).result` vaut `core::MoveResult::Unreachable`.
- Vérifie que `premier.result` vaut `core::MoveResult::Moved`.
- Vérifie que `premier.path.length` vaut `6.0f`, à `CM` près.
- Vérifie que `premier.path.points.empty()` est faux.
- Vérifie que `proche(premier.path.points.back(), tile(2, 0))` est vrai.
- Vérifie que `combat->economy(CombatantId{1})->remaining(core::MOVEMENT_RESOURCE)` vaut `4`.
- Vérifie que `combat->movementLeft()` vaut `6.0f`, à `CM` près.
- Vérifie que `second.result` vaut `core::MoveResult::Moved`.
- Vérifie que `second.path.length` vaut `6.0f`, à `CM` près.
- Vérifie que `proche(*combat->positionOf(CombatantId{1}), tile(4, 0))` est vrai.
- Vérifie que `combat->economy(CombatantId{1})->remaining(core::MOVEMENT_RESOURCE)` vaut `0`.
- Vérifie que `combat->movementLeft()` vaut `0.0f`, à `CM` près.
- Vérifie que `fins(combat->destinations()).empty()` est vrai.
- Vérifie que `combat->start(des)` est vrai.
- Vérifie que `finales.size()` vaut `1U`.
- Vérifie que `proche(finales[0], tile(2, 0))` est vrai.
- Vérifie que `combat->routeFor(CombatantId{1}, tile(4, 0), -1.0f).has_value()` est faux.

### CombatStateTest.LeMontageDUneRencontrePlaceEtRefuseEnLeDisant

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:840`

Le montage pose le groupe puis les creatures de la rencontre, et nomme chaque refus avec sa raison.

**Étapes**

1. Carte a un mur ; rencontre de cinq entrees : un gobelin libre, un dans le mur, une creature inconnue, une chauve-souris, un gobelin sur la case de l'heroine.
2. Monter la rencontre avec l'heroine au declencheur.
3. Gagner le combat et le terminer.

**Résultat attendu**

- Vérifie que `montage.allies` vaut `(std::vector<CombatantId>{CombatantId{1}})`.
- Vérifie que `montage.enemies` vaut `(std::vector<CombatantId>{CombatantId{2}, CombatantId{3}})`.
- Vérifie que `montage.refusals.size()` vaut `3U`.
- Vérifie que `montage.refusals[0].who` vaut `"gobelin"`.
- Vérifie que `montage.refusals[0].position` vaut `(core::GridPosition{6, 3})`.
- Vérifie que `montage.refusals[0].placement` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `montage.refusals[1].who` vaut `"fantome"`.
- Vérifie que `montage.refusals[1].placement.has_value()` est faux.
- Vérifie que `montage.refusals[2].placement` vaut `core::PlacementResult::Occupied`.
- Vérifie que `combat.find(CombatantId{1})->profile.initiativeModifier` vaut `3`.
- Vérifie que `combat.find(CombatantId{1})->profile.movement` vaut `6`.
- Vérifie que `combat.positionOf(CombatantId{2}).has_value()` est vrai.
- Vérifie que `proche(*combat.positionOf(CombatantId{2}), tile(5, 3))` est vrai.
- Vérifie que `combat.find(CombatantId{3})->profile.locomotion` vaut `core::Locomotion::Fly`.
- Vérifie que `combat.find(CombatantId{3})->profile.movement` vaut `6`.
- Vérifie que `combat.escapable()` est faux.
- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.withdraw(CombatantId{1})` vaut `core::WithdrawResult::NotEscapable`.
- Vérifie que `combat.outcome()` vaut `core::CombatOutcome::Victory`.
- Vérifie que `drapeaux.isSet("carte/embuscade/3/3")` est vrai.

### CombatStateTest.LeBudgetSeDeduitDeLaVitesse

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1002`

Le budget de deplacement vaut la vitesse divisee par 1,5, arrondie en dessous.

**Étapes**

1. Convertir 9 m, 7,5 m, 10 m, 0 m et -3 m.
2. Lire le budget d'une fiche a 9 m.
3. Lire le budget de marche et de vol d'une creature qui ne vole pas, puis d'une qui vole.

**Résultat attendu**

- Vérifie que `core::movementBudget(9.0F)` vaut `6`.
- Vérifie que `core::movementBudget(7.5F)` vaut `5`.
- Vérifie que `core::movementBudget(10.0F)` vaut `6`.
- Vérifie que `core::movementBudget(13.5F - 4.5F)` vaut `6`.
- Vérifie que `core::movementBudget(0.0F)` vaut `0`.
- Vérifie que `core::movementBudget(-3.0F)` vaut `0`.
- Vérifie que `core::movementBudget(fiche)` vaut `6`.
- Vérifie que `core::movementBudget(loup, core::Locomotion::Walk)` vaut `8`.
- Vérifie que `core::movementBudget(loup, core::Locomotion::Fly)` vaut `0`.
- Vérifie que `core::movementBudget(chouette, core::Locomotion::Fly)` vaut `12`.

### CombatStateTest.LesPlacesAtteignablesSontCellesDuBudget

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1036`

Sur un sol libre, une place est atteignable si et seulement si sa distance tient dans le budget, diagonale comprise : la diagonale n'est plus une case.

**Étapes**

1. Salle ouverte de 11 x 11 cases, heros au centre de la case (5,5).
2. Pour un budget de 0 a 4 cases (0 a 6 m), lire les places de fin et les chemins vers les centres des cases sur la ligne et sur la diagonale.

**Résultat attendu**

- Vérifie que `places.empty()` est faux.
- Vérifie que `proche(places.front().point, centre)` est vrai.
- Vérifie que `places[i].route.length` est inférieur ou égal à `metres + CM`.
- Vérifie que `core::groundDistance(centre, places[i].point)` est inférieur ou égal à `metres + CM`.
- Vérifie que `combat.canStandAt(heros, places[i].point)` est vrai.
- Vérifie que `parmi(finales, ligne)` vaut `k <= budget`.
- Vérifie que `droit.has_value()` vaut `k <= budget`.
- Vérifie que `droit->length` vaut `1.5f * static_cast<float>(k)`, à `CM` près.
- Vérifie que `diagonale.has_value()` vaut `longueur <= metres`.
- Vérifie que `diagonale->length` vaut `longueur`, à `CM` près.

### CombatStateTest.UnMurCouteLeDetour

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1088`

Un mur entre deux places voisines coute le detour.

**Étapes**

1. Carte de 7 x 5 cases, mur en colonne 3 des lignes 0 a 2.
2. Heros au centre de (2,1), cible au centre de (4,1), a 3 m de l'autre cote du mur.

**Résultat attendu**

- Vérifie que `core::groundDistance(tile(2, 1), tile(4, 1))` vaut `3.0f`, à `CM` près.
- Vérifie que `combat.routeFor(heros, tile(4, 1), 7.5f).has_value()` est faux.
- Vérifie que `chemin.has_value()` est vrai.
- Vérifie que `chemin->length` vaut `9.0f`, à `CM` près.
- Vérifie que `chemin->points.empty()` est faux.
- Vérifie que `proche(chemin->points.back(), tile(4, 1))` est vrai.
- Vérifie que `combat.canStandAt(heros, pas)` est vrai.

### CombatStateTest.LeTerrainDifficileDoubleLeCoutEtReduitLaPortee

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1120`

Le terrain difficile double le cout des metres qu'on y marche, et reduit la portee.

**Étapes**

1. Salle ouverte de 11 x 11 cases, heros au centre de (5,5).
2. Rendre difficile la case voisine (6,5) ; chemins vers son centre et vers (7,5), au-dela.
3. Rendre toute la salle difficile, budget de 4 cases (6 m).

**Résultat attendu**

- Vérifie que `boue.has_value()` est vrai.
- Vérifie que `boue->length` vaut `2.25f`, à `CM` près.
- Vérifie que `combat.routeFor(heros, tile(6, 5), 1.5f).has_value()` est faux.
- Vérifie que `auDela.has_value()` est vrai.
- Vérifie que `auDela->length` vaut `3.0f * std::sqrt(2.0f)`, à `CM` près.
- Vérifie que `deux.has_value()` est vrai.
- Vérifie que `deux->length` vaut `6.0f`, à `CM` près.
- Vérifie que `combat.routeFor(heros, tile(8, 5), 6.0f).has_value()` est faux.
- Vérifie que `places.size()` est strictement supérieur à `1U`.
- Vérifie que `core::groundDistance(tile(5, 5), places[i].point)` est inférieur ou égal à `3.0f + CM`.

### CombatStateTest.LeDeplacementSePaieEnCasesEntamees

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1164`

Un pas se paie en cases de 1,5 m entamees, et le reste de la case entamee sert au pas suivant du meme tour : deux pas de 0,75 m coutent une case, pas deux.

**Étapes**

1. Heros (6 cases) au centre de (2,2), un ennemi au loin.
2. Faire un pas de 0,75 m, puis un second de 0,75 m, puis un de 2,25 m.
3. Finir le tour, et celui de l'ennemi.

**Résultat attendu**

- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `heros`.
- Vérifie que `combat.movementLeft()` vaut `9.0f`, à `CM` près.
- Vérifie que `issue.result` vaut `core::MoveResult::Moved`.
- Vérifie que `issue.path.length` vaut `longueur`, à `CM` près.
- Vérifie que `combat.economy(heros)->remaining(core::MOVEMENT_RESOURCE)` vaut `cases`.
- Vérifie que `combat.find(heros)->movementSlack` vaut `reste`, à `CM` près.
- Vérifie que `combat.movementLeft()` vaut `1.5f * static_cast<float>(cases) + reste`, à `CM` près.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.endTurn()` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `heros`.
- Vérifie que `combat.economy(heros)->remaining(core::MOVEMENT_RESOURCE)` vaut `6`.
- Vérifie que `combat.find(heros)->movementSlack` vaut `0.0f`, à `CM` près.
- Vérifie que `combat.movementLeft()` vaut `9.0f`, à `CM` près.

### CombatStateTest.LeTerrainDifficileSeCreeEnCombat

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1208`

Du terrain difficile pose en cours de combat (un seisme) compte des la question suivante.

**Étapes**

1. Heros au centre de (2,2), combat commence.
2. Rendre la case (3,2) difficile.
3. Y aller.

**Résultat attendu**

- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `heros`.
- Vérifie que `combat.routeTo(tile(3, 2)).has_value()` est vrai.
- Vérifie que `combat.routeTo(tile(3, 2))->length` vaut `1.5f`, à `CM` près.
- Vérifie que `combat.routeTo(tile(3, 2)).has_value()` est vrai.
- Vérifie que `combat.routeTo(tile(3, 2))->length` vaut `2.25f`, à `CM` près.
- Vérifie que `combat.move(tile(3, 2)).result` vaut `core::MoveResult::Moved`.
- Vérifie que `combat.economy(heros)->remaining(core::MOVEMENT_RESOURCE)` vaut `4`.
- Vérifie que `combat.movementLeft()` vaut `6.75f`, à `CM` près.

### CombatStateTest.LeTerrainDifficileVientDesZonesDeLaCarte

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1243`

Les proprietes de zone de la carte font le terrain difficile de l'espace.

**Étapes**

1. Construire l'espace d'une carte dont une couche porte difficultTerrain, une autre une regle inconnue, une troisieme une coquille (difficultTerrain: 1).
2. Interroger les cases ; marcher vers chacune depuis sa voisine.

**Résultat attendu**

- Vérifie que `espace->isDifficult(centre.x, centre.y)` vaut `attendu.difficile`.
- Vérifie que `boue.has_value()` est vrai.
- Vérifie que `cercle.has_value()` est vrai.
- Vérifie que `coquille.has_value()` est vrai.
- Vérifie que `boue->length` vaut `2.25f`, à `CM` près.
- Vérifie que `cercle->length` vaut `1.5f`, à `CM` près.
- Vérifie que `coquille->length` vaut `1.5f`, à `CM` près.
- Vérifie que `combat.placementAt(profil("Rat", CombatSide::Enemies, 2), tile(5, 0))` vaut `core::PlacementResult::Obstructed`.

### CombatStateTest.UnAllieSeTraverseUnEnnemiNon

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1292`

Un allie se traverse en terrain difficile, un ennemi de meme taille non, et aucun n'est une place de fin.

**Étapes**

1. Couloir de 5 cases sur 1 : heros en 0, allie en 1, ennemi en 3.
2. Chemins vers les centres des cases 1, 2 et 4.
3. Meme couloir, l'ennemi a la place de l'allie.

**Résultat attendu**

- Vérifie que `derriere.has_value()` est vrai.
- Vérifie que `derriere->length` vaut `6.0f`, à `CM` près.
- Vérifie que `passage->routeFor(HEROS, tile(1, 0), 9.0f).has_value()` est faux.
- Vérifie que `passage->routeFor(HEROS, tile(4, 0), -1.0f).has_value()` est faux.
- Vérifie que `finales.size()` vaut `1U`.
- Vérifie que `proche(finales[0], tile(2, 0))` est vrai.
- Vérifie que `fins(bloque->destinationsFor(HEROS, 9.0f)).empty()` est vrai.
- Vérifie que `bloque->routeFor(HEROS, tile(2, 0), -1.0f).has_value()` est faux.

### CombatStateTest.UnCheminImpossibleEstRefuse

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1327`

Un chemin impossible est refuse.

**Étapes**

1. Carte de 5 x 5 cases coupee en deux par un mur plein.
2. Demander un chemin de l'autre cote, un chemin dans le mur, un chemin pour un combattant inconnu, un chemin pour un combattant sans place.

**Résultat attendu**

- Vérifie que `combat.routeFor(heros, tile(4, 2), -1.0f).has_value()` est faux.
- Vérifie que `combat.routeFor(heros, tile(2, 2), -1.0f).has_value()` est faux.
- Vérifie que `combat.routeFor(CombatantId{9}, tile(1, 2), -1.0f).has_value()` est faux.
- Vérifie que `combat.routeFor(absent, tile(1, 2), -1.0f).has_value()` est faux.
- Vérifie que `places.size()` est strictement supérieur à `1U`.
- Vérifie que `place.point.x` est inférieur ou égal à `3.0f - 0.75f + CM`.
- Vérifie que `combat.destinationsFor(CombatantId{9}, 30.0f).empty()` est vrai.
- Vérifie que `combat.destinationsFor(absent, 30.0f).empty()` est vrai.

### CombatStateTest.UnVolantSurvoleLesObstaclesDeSol

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1362`

Un volant survole les obstacles de sol, pas les murs.

**Étapes**

1. Carte de 5 x 3 cases : la case (2,1) en eau profonde, la case (2,2) en falaise, la case (1,1) en boue, la ligne 0 muree.
2. Chemins du meme combattant au sol, puis en vol, depuis le centre de (0,1).

**Résultat attendu**

- Vérifie que `marche->routeFor(HEROS, tile(3, 1), 9.0f).has_value()` est faux.
- Vérifie que `marche->routeFor(HEROS, tile(3, 2), 9.0f).has_value()` est faux.
- Vérifie que `marche->canStandAt(HEROS, tile(2, 1))` est faux.
- Vérifie que `boueAPied.has_value()` est vrai.
- Vérifie que `boueAPied->length` vaut `2.25f`, à `CM` près.
- Vérifie que `rive.has_value()` est vrai.
- Vérifie que `rive->length` vaut `4.5f`, à `CM` près.
- Vérifie que `boueEnVol.has_value()` est vrai.
- Vérifie que `boueEnVol->length` vaut `1.5f`, à `CM` près.
- Vérifie que `vol->canStandAt(HEROS, tile(2, 1))` est vrai.
- Vérifie que `vol->routeFor(HEROS, tile(2, 2), 9.0f).has_value()` est vrai.
- Vérifie que `combat->routeFor(HEROS, tile(1, 0), -1.0f).has_value()` est faux.
- Vérifie que `combat->canStandAt(HEROS, tile(1, 0))` est faux.

### CombatStateTest.UneGrandeCreatureNePassePasParUnPassageEtroit

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1417`

Une creature G (3 m de diametre) ne passe pas par un passage de 1,5 m.

**Étapes**

1. Salle de 6 x 6 cases coupee par un mur en colonne 3, percee d'une seule case en (3,2).
2. Chemins et places de fin d'un combattant M, puis d'un G, avec 15 m.

**Résultat attendu**

- Vérifie que `combat.routeFor(heros, tile(5, 2), 15.0f).has_value()` est vrai.
- Vérifie que `combat.routeFor(ours, tile(4, 1, core::CreatureSize::Large), 15.0f).has_value()` est faux.
- Vérifie que `places.size()` est strictement supérieur à `1U`.
- Vérifie que `place.point.x + core::creatureRadius(core::CreatureSize::Large)` est inférieur ou égal à `4.5f + CM`.
- Vérifie que `combat.canStandAt(ours, place.point)` est vrai.

### CombatStateTest.LesObstaclesSontCeuxDeLaCollision

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1452`

Les obstacles de l'espace sont ceux de la couche collision.

**Étapes**

1. Un espace lu d'une collision portant un mur, de l'eau peu profonde, de l'eau profonde et une falaise.
2. Demander un placement au centre de chaque case, au sol puis en vol, et hors de la carte.

**Résultat attendu**

- Vérifie que `place(marcheur, 0)` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `place(volant, 0)` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `place(marcheur, 1)` vaut `core::PlacementResult::Placed`.
- Vérifie que `place(marcheur, 2)` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `place(volant, 2)` vaut `core::PlacementResult::Placed`.
- Vérifie que `place(marcheur, 3)` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `place(volant, 3)` vaut `core::PlacementResult::Placed`.
- Vérifie que `place(marcheur, 4)` vaut `core::PlacementResult::Placed`.
- Vérifie que `place(marcheur, 5)` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `place(volant, -1)` vaut `core::PlacementResult::Obstructed`.

### CombatStateTest.UnPlacementImpossibleEstRefuseAvecSaRaison

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1493`

Un placement impossible est refuse avec sa raison, et la place d'un combattant sorti se reprend.

**Étapes**

1. Carte de 8 x 8 cases, mur en (1,1) : enroler hors de la carte, dans le mur, un G a cheval sur le bord.
2. Poser le heros en (3,3), puis tenter un rat sur sa place, a 0,75 m de lui, et un G dont l'emprise le couvre ; poser le rat au contact.
3. Pendant son tour, le heros tente d'aller sur le rat ; il sort ; un renfort entre a sa place.

**Résultat attendu**

- Vérifie que `combat.enlist(profil("Heros", CombatSide::Allies, 10), tile(8, 0)).placement` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `combat.enlist(profil("Heros", CombatSide::Allies, 10), tile(1, 1)).placement` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `combat.enlist(grand, tile(7, 7, core::CreatureSize::Large)).placement` vaut `core::PlacementResult::Obstructed`.
- Vérifie que `combat.combatants().empty()` est vrai.
- Vérifie que `heros` vaut `CombatantId{1}`.
- Vérifie que `combat.enlist(rat, tile(3, 3)).placement` vaut `core::PlacementResult::Occupied`.
- Vérifie que `combat.enlist(rat, Meters3{tile(3, 3).x + 0.75f, tile(3, 3).y, 0.0f}).placement` vaut `core::PlacementResult::Occupied`.
- Vérifie que `combat.enlist(grand, tile(2, 2, core::CreatureSize::Large)).placement` vaut `core::PlacementResult::Occupied`.
- Vérifie que `leRat` vaut `CombatantId{2}`.
- Vérifie que `combat.occupantAt(tile(3, 3))` vaut `heros`.
- Vérifie que `combat.occupantAt(tile(4, 3))` vaut `leRat`.
- Vérifie que `combat.occupantAt(tile(5, 5)).has_value()` est faux.
- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `heros`.
- Vérifie que `combat.move(tile(4, 3)).result` vaut `core::MoveResult::Unreachable`.
- Vérifie que `proche(*combat.positionOf(heros), tile(3, 3))` est vrai.
- Vérifie que `combat.withdraw(heros)` vaut `core::WithdrawResult::Withdrawn`.
- Vérifie que `combat.occupantAt(tile(3, 3)).has_value()` est faux.
- Vérifie que `renfort.placement` vaut `core::PlacementResult::Placed`.
- Vérifie que `renfort.combatant` vaut `CombatantId{4}`.

### CombatStateTest.UneGrandeCreatureOccupeToutSonEmprise

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1554`

Une creature G couvre ses quatre cases et avance en recouvrant sa propre place.

**Étapes**

1. Poser une creature G sur les cases (1,1) a (2,2).
2. A son tour, la deplacer d'une case vers la droite.

**Résultat attendu**

- Vérifie que `core::footprintSide(core::CreatureSize::Tiny)` vaut `1`.
- Vérifie que `core::footprintSide(core::CreatureSize::Large)` vaut `2`.
- Vérifie que `core::footprintSide(core::CreatureSize::Gargantuan)` vaut `4`.
- Vérifie que `combat.occupantAt(centre)` vaut `ours`.
- Vérifie que `combat.occupantAt(tile(3, 1)).has_value()` est faux.
- Vérifie que `combat.start(des)` est vrai.
- Vérifie que `combat.activeCombatant()` vaut `ours`.
- Vérifie que `pas.result` vaut `core::MoveResult::Moved`.
- Vérifie que `pas.path.length` vaut `1.5f`, à `CM` près.
- Vérifie que `combat.occupantAt(tile(1, 1)).has_value()` est faux.
- Vérifie que `combat.occupantAt(tile(3, 2))` vaut `ours`.

### CombatStateTest.MemeEntreeMemeChemin

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1591`

Le chemin est deterministe, et la place de fin annoncee porte le chemin que le deplacement suivra.

**Étapes**

1. Carte accidentee (mur en L, boue), heros au centre de (1,3).
2. Monter cinquante fois le meme combat et demander le chemin vers (7,2) et les places de fin a 18 m.
3. Pour chaque place de fin, redemander son chemin ; puis, le combat commence, aller a l'une d'elles.

**Résultat attendu**

- Vérifie que `chemin.has_value()` est vrai.
- Vérifie que `places.size()` est strictement supérieur à `10U`.
- Vérifie que `autre.has_value()` est vrai.
- Vérifie que `autre->points` vaut `chemin->points`.
- Vérifie que `autre->length` vaut `chemin->length`.
- Vérifie que `autres.size()` vaut `places.size()`.
- Vérifie que `autres[i].point` vaut `places[i].point`.
- Vérifie que `redemande.has_value()` est vrai.
- Vérifie que `redemande->points` vaut `places[i].route.points`.
- Vérifie que `redemande->length` vaut `places[i].route.length`, à `1e-4f` près.
- Vérifie que `places[i].route.length` est inférieur ou égal à `18.0f + CM`.
- Vérifie que `reference->start(des)` est vrai.
- Vérifie que `reference->activeCombatant()` vaut `HEROS`.
- Vérifie que `duTour.size()` est strictement supérieur à `1U`.
- Vérifie que `pas.result` vaut `core::MoveResult::Moved`.
- Vérifie que `pas.path.points` vaut `visee.route.points`.
- Vérifie que `pas.path.length` vaut `visee.route.length`, à `1e-4f` près.

### CombatStateTest.SurDesCartesAleatoiresLeCheminAnnonceSAccorde

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_combat_state.cpp:1646`

Sur douze cartes aleatoires a graine fixe, la place de fin et le chemin demande vers elle s'accordent.

**Étapes**

1. Tirer douze cartes de 12 x 9 cases (graine fixe) : murs, eau profonde, boue, un allie a traverser ; une carte sur trois en vol.
2. Pour chaque place de fin a 21 m, comparer son chemin au chemin demande.

**Résultat attendu**

- Vérifie que `demande.has_value()` est vrai.
- Vérifie que `demande->points` vaut `places[i].route.points`.
- Vérifie que `demande->length` vaut `places[i].route.length`, à `1e-4f` près.
- Vérifie que `demande->length` est inférieur ou égal à `21.0f + CM`.
- Vérifie que `comparaisons` est strictement supérieur à `600`.

## test_damage.cpp

### DamageTest.LeCritiqueDoubleLesDesPasLeModificateur

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_damage.cpp:72`

Exigences : `EX-CBT-031`

Un coup critique lance deux fois les des de degats et ajoute le modificateur une seule fois.

**Étapes**

1. Lancer 1d6+3 en critique, a deux cents graines.
2. Lancer 1d4-5 sans critique.

**Résultat attendu**

- Vérifie que `lance.size()` vaut `1U`.
- Vérifie que `lance[0].roll.faces.size()` vaut `2U`.
- Vérifie que `lance[0].roll.dice.count` vaut `2`.
- Vérifie que `lance[0].roll.dice.modifier` vaut `3`.
- Vérifie que `lance[0].amount` vaut `lance[0].roll.faces[0] + lance[0].roll.faces[1] + 3`.
- Vérifie que `lance[0].critical` est vrai.
- Vérifie que `minimum` vaut `5`.
- Vérifie que `maximum` vaut `15`.
- Vérifie que `core::rollDamage(faible, false, hasard)[0].amount` vaut `0`.

### DamageTest.LesResistancesSAppliquentDansLOrdreDuManuel

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_damage.cpp:110`

Immunite, resistance et vulnerabilite s'appliquent dans l'ordre du Manuel, apres les autres modificateurs, et une seule fois chacune.

**Étapes**

1. 25 degats contondants sur une cible resistante, sous une aura qui retire 5.
2. 25 sur une cible resistante et vulnerable.
3. 25 sur une cible deux fois resistante ; sur une cible immunisee et vulnerable ; une resistance contournee par une source magique ; une source qui ignore les resistances.

**Résultat attendu**

- Vérifie que `exemple.work.hitPointLoss` vaut `10`.
- Vérifie que `exemple.work.trace.size()` vaut `2U`.
- Vérifie que `exemple.work.trace[0].source` vaut `"aura"`.
- Vérifie que `exemple.work.trace[1].source` vaut `"resistance (contondant)"`.
- Vérifie que `exemple.work.trace[1].before` vaut `20`.
- Vérifie que `exemple.work.trace[1].after` vaut `10`.
- Vérifie que `encaisser({{resiste, vulnerable}}, 0, false).work.hitPointLoss` vaut `24`.
- Vérifie que `encaisser({{resiste, resiste}}, 0, false).work.hitPointLoss` vaut `12`.
- Vérifie que `encaisser({{immunise, vulnerable}}, 0, false).work.hitPointLoss` vaut `0`.
- Vérifie que `encaisser({{nonMagique}}, 0, false).work.hitPointLoss` vaut `12`.
- Vérifie que `encaisser({{nonMagique}}, core::flagsOf(DamageFlag::Magical), false).work.hitPointLoss` vaut `25`.
- Vérifie que `encaisser({{resiste}}, core::flagsOf(DamageFlag::IgnoresResistance), false) .work.hitPointLoss` vaut `25`.

### DamageTest.LesEtapesSEnchainentEtLaConversionPrecedeLaResistance

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_damage.cpp:167`

Les cinq etapes du pipeline s'executent dans l'ordre nomme, et un type converti est resiste selon son nouveau type.

**Étapes**

1. Un greffon par etape, qui note son passage.
2. Un greffon de conversion qui change le feu en froid.
3. 20 degats de feu sur une cible resistante au froid.

**Résultat attendu**

- Vérifie que `etat` diffère de `nullptr`.
- Vérifie que `passages` vaut `(std::vector<std::string>{"source", "conversion", "resistances", "reserves", "points de vie"})`.
- Vérifie que `rapport.work.hitPointLoss` vaut `10`.
- Vérifie que `combat.find(CombatantId{1})->profile.currentHitPoints` vaut `40`.

### DamageTest.LesPointsDeVieTemporairesAbsorbentDAbordEtNeSeCumulentPas

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_damage.cpp:205`

Les points de vie temporaires se perdent avant les points de vie, ne se cumulent pas, ne se soignent pas, et absorbent encore a 0 PV sans relever.

**Étapes**

1. Donner 10 PV temporaires, puis 12, puis 5 ; une reserve cumulable de 3.
2. Infliger 7, puis 12.
3. Soigner ; infliger des degats qui ignorent les reserves.
4. A 0 PV, donner des PV temporaires et infliger 4.

**Résultat attendu**

- Vérifie que `combat.grantReserve(id, {.source = temporaires, .amount = 10, .stacks = false})` est vrai.
- Vérifie que `combat.grantReserve(id, {.source = temporaires, .amount = 12, .stacks = false})` est vrai.
- Vérifie que `combat.grantReserve(id, {.source = temporaires, .amount = 5, .stacks = false})` est faux.
- Vérifie que `combat.grantReserve(id, {.source = "Exosquelette", .amount = 3, .stacks = true})` est vrai.
- Vérifie que `combat.reserves(id)->size()` vaut `2U`.
- Vérifie que `combat.reserves(id)->front().amount` vaut `12`.
- Vérifie que `rapport.work.absorbed` vaut `7`.
- Vérifie que `rapport.work.hitPointLoss` vaut `0`.
- Vérifie que `combat.find(id)->profile.currentHitPoints` vaut `20`.
- Vérifie que `combat.reserves(id)->size()` vaut `1U`.
- Vérifie que `combat.reserves(id)->front().amount` vaut `8`.
- Vérifie que `rapport.work.absorbed` vaut `8`.
- Vérifie que `rapport.work.hitPointLoss` vaut `4`.
- Vérifie que `combat.reserves(id)->empty()` est vrai.
- Vérifie que `combat.find(id)->profile.currentHitPoints` vaut `16`.
- Vérifie que `combat.reserves(id)->empty()` est vrai.
- Vérifie que `combat.find(id)->profile.currentHitPoints` vaut `20`.
- Vérifie que `rapport.work.absorbed` vaut `0`.
- Vérifie que `combat.find(id)->status` vaut `core::CombatantStatus::Down`.
- Vérifie que `combat.reserves(id)->front().amount` vaut `50`.
- Vérifie que `rapport.work.absorbed` vaut `4`.
- Vérifie que `combat.find(id)->status` vaut `core::CombatantStatus::Down`.

### DamageTest.LesPointsDeVieSontBornesAZeroEtLExcedentEstRapporte

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_damage.cpp:264`

Les points de vie sont bornes a 0 aux trois bornes, la chute s'annonce une seule fois, et les degats restants au-dela de 0 sont rapportes pour l'agonie.

**Étapes**

1. Une cible a 10 PV : 9 degats, puis 1, puis 5.
2. Le clerc du Manuel, 6 PV sur 12, subit 18 degats d'un coup critique.
3. Un seuil « sous la moitie ».

**Résultat attendu**

- Vérifie que `combat.find(cible)->profile.currentHitPoints` vaut `1`.
- Vérifie que `combat.find(cible)->status` vaut `core::CombatantStatus::Standing`.
- Vérifie que `chutes.empty()` est vrai.
- Vérifie que `moitie` vaut `1`.
- Vérifie que `juste.hitPointsAfter` vaut `0`.
- Vérifie que `juste.overflow` vaut `0`.
- Vérifie que `combat.find(cible)->status` vaut `core::CombatantStatus::Down`.
- Vérifie que `chutes.size()` vaut `1U`.
- Vérifie que `combat.find(cible)->profile.currentHitPoints` vaut `0`.
- Vérifie que `chutes.size()` vaut `1U`.
- Vérifie que `degats.size()` vaut `3U`.
- Vérifie que `degats.back().hitPointsBefore` vaut `0`.
- Vérifie que `moitie` vaut `1`.
- Vérifie que `excedent.hitPointsBefore` vaut `6`.
- Vérifie que `excedent.hitPointsAfter` vaut `0`.
- Vérifie que `excedent.overflow` vaut `12`.
- Vérifie que `chutes.size()` vaut `2U`.
- Vérifie que `chutes.back().overflow` vaut `12`.
- Vérifie que `chutes.back().maximumHitPoints` vaut `12`.
- Vérifie que `chutes.back().critical` est vrai.

### DamageTest.UneSalveSeLanceUneFoisEtSAppliqueDUnCoup

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_damage.cpp:327`

Des degats qui touchent plusieurs cibles sont lances une fois pour toutes, et une salve qui abat les deux camps est une defaite quel que soit l'ordre des cibles.

**Étapes**

1. Un allie et un ennemi a 5 PV, combat commence.
2. Un seul jet de 3d6+10 de feu applique aux deux, l'ennemi en premier.

**Résultat attendu**

- Vérifie que `combat.start(hasard)` est vrai.
- Vérifie que `rapports.size()` vaut `2U`.
- Vérifie que `rapports[0].work.hitPointLoss` vaut `rapports[1].work.hitPointLoss`.
- Vérifie que `combat.outcome()` vaut `core::CombatOutcome::Defeat`.

### DamageTest.LesStructuresOntDesPointsDeVieEtLeBestiaireSesAffinites

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_damage.cpp:358`

Une structure traverse le pipeline avec ses resistances et se dit detruite a 0 PV, et l'espace la retire ; les affinites d'une creature se lisent de son bloc.

**Étapes**

1. Une porte de 10 PV immunisee au poison et resistante au perforant.
2. 30 degats de poison, puis 14 perforants, puis 6 perforants.
3. Une creature resistante au froid, immunisee au poison, vulnerable au feu.

**Résultat attendu**

- Vérifie que `pipeline.applyToStructure(porte, poison).hitPointsAfter` vaut `10`.
- Vérifie que `perce.hitPointsAfter` vaut `3`.
- Vérifie que `perce.work.structure` vaut `std::optional<std::string>("porte")`.
- Vérifie que `porte.destroyed()` est faux.
- Vérifie que `pipeline.applyToStructure(porte, fin).overflow` vaut `0`.
- Vérifie que `porte.destroyed()` est vrai.
- Vérifie que `espace.isClear(derriere, core::Locomotion::Walk)` est faux.
- Vérifie que `espace.removeBox(0)` est vrai.
- Vérifie que `espace.isClear(derriere, core::Locomotion::Walk)` est vrai.
- Vérifie que `espace.isClear(devant, core::Locomotion::Walk)` est vrai.
- Vérifie que `traits.affinities.size()` vaut `3U`.
- Vérifie que `traits.affinities[0].kind` vaut `DamageAffinityKind::Immunity`.
- Vérifie que `traits.applies(DamageAffinityKind::Vulnerability, DamageType::Fire, 0)` est vrai.
- Vérifie que `traits.applies(DamageAffinityKind::Resistance, DamageType::Fire, 0)` est faux.

## test_death_and_dying.cpp

### DeathAndDyingTest.TroisEchecsTuent

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:145`

Exigences : `EX-CBT-040`

Un allie tombe a 0 PV : il agonise ; deux echecs et un succes ne le tuent pas, le troisieme echec le tue, une fois, et plus rien ne le soigne.

**Étapes**

1. Aldric tombe a 0 PV.
2. Jets : 9, 15, 5, puis 3.
3. Le soigner, lui faire jeter encore.

**Résultat attendu**

- Vérifie que `e.combat.find(e.aldric)->status` vaut `CombatantStatus::Down`.
- Vérifie que `e.combat.isDying(e.aldric)` est vrai.
- Vérifie que `e.combat.find(e.aldric)->prone` est vrai.
- Vérifie que `e.combat.activeCombatant()` vaut `e.brune`.
- Vérifie que `e.combat.recordDeathSave(e.aldric, 9, 9)` vaut `DeathSaveOutcome::Failure`.
- Vérifie que `e.combat.recordDeathSave(e.aldric, 15, 15)` vaut `DeathSaveOutcome::Success`.
- Vérifie que `e.combat.recordDeathSave(e.aldric, 5, 5)` vaut `DeathSaveOutcome::Failure`.
- Vérifie que `e.combat.find(e.aldric)->deathSaves` vaut `(core::DeathSaves{.successes = 1, .failures = 2, .stable = false})`.
- Vérifie que `morts` vaut `0`.
- Vérifie que `e.combat.recordDeathSave(e.aldric, 3, 3)` vaut `DeathSaveOutcome::Died`.
- Vérifie que `e.combat.find(e.aldric)->status` vaut `CombatantStatus::Dead`.
- Vérifie que `morts` vaut `1`.
- Vérifie que `e.combat.find(e.aldric)->status` vaut `CombatantStatus::Dead`.
- Vérifie que `e.combat.find(e.aldric)->profile.currentHitPoints` vaut `0`.
- Vérifie que `e.combat.recordDeathSave(e.aldric, 20, 20)` vaut `DeathSaveOutcome::Ignored`.
- Vérifie que `e.combat.declareAttack(e.gobelin, e.aldric)` est faux.

### DeathAndDyingTest.UnVingtReleveUnUnCompteDouble

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:186`

Exigences : `EX-CBT-040`, `EX-CBT-041`

Les d20 extremes du Manuel : 20 rend 1 PV, 1 compte deux echecs, meme quand la benediction porterait le total a 10 ; trois succes stabilisent, des degats refont agoniser, et le soin repart d'un compteur vide.

**Étapes**

1. Aldric a terre jette 1 (total 12).
2. Trois succes, dont un 8 porte a 11.
3. Un point de degats.
4. Un soin de 3.
5. Brune a terre jette 20.

**Résultat attendu**

- Vérifie que `e.combat.recordDeathSave(e.aldric, 1, 12)` vaut `DeathSaveOutcome::Failure`.
- Vérifie que `e.combat.find(e.aldric)->deathSaves.failures` vaut `2`.
- Vérifie que `e.combat.recordDeathSave(e.aldric, 12, 12)` vaut `DeathSaveOutcome::Success`.
- Vérifie que `e.combat.recordDeathSave(e.aldric, 8, 11)` vaut `DeathSaveOutcome::Success`.
- Vérifie que `e.combat.recordDeathSave(e.aldric, 10, 10)` vaut `DeathSaveOutcome::Stabilized`.
- Vérifie que `e.combat.find(e.aldric)->deathSaves` vaut `(core::DeathSaves{.successes = 0, .failures = 0, .stable = true})`.
- Vérifie que `e.combat.isDying(e.aldric)` est faux.
- Vérifie que `e.combat.isDying(e.aldric)` est vrai.
- Vérifie que `e.combat.find(e.aldric)->deathSaves.failures` vaut `1`.
- Vérifie que `aldric->status` vaut `CombatantStatus::Standing`.
- Vérifie que `aldric->profile.currentHitPoints` vaut `3`.
- Vérifie que `aldric->deathSaves` vaut `core::DeathSaves{}`.
- Vérifie que `aldric->prone` est vrai.
- Vérifie que `e.combat.recordDeathSave(e.brune, 20, 20)` vaut `DeathSaveOutcome::Revived`.
- Vérifie que `e.combat.find(e.brune)->status` vaut `CombatantStatus::Standing`.
- Vérifie que `e.combat.find(e.brune)->profile.currentHitPoints` vaut `1`.

### DeathAndDyingTest.LesDegatsATerreEtLaMortInstantanee

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:230`

Exigences : `EX-CBT-040`

Degats a 0 point de vie et mort instantanee, Manuel p. 199 : un coup a terre coute un echec, un critique deux ; des degats restants au moins egaux au maximum tuent sur le coup ; un monstre meurt des 0 PV.

**Étapes**

1. Aldric a terre : 1 degat, puis 1 degat critique.
2. Brune (10 PV) prend 20 degats.
3. Le gobelin tombe a 0.

**Résultat attendu**

- Vérifie que `e.combat.find(e.aldric)->deathSaves.failures` vaut `1`.
- Vérifie que `e.combat.find(e.aldric)->status` vaut `CombatantStatus::Dead`.
- Vérifie que `e.combat.find(e.brune)->status` vaut `CombatantStatus::Dead`.
- Vérifie que `annonces` vaut `(std::vector<CombatHook>{CombatHook::CombatantDowned, CombatHook::CombatantDied})`.
- Vérifie que `e.combat.outcome()` vaut `core::CombatOutcome::Defeat`.

### DeathAndDyingTest.UnMonstreMeurtEtLaMarqueProtege

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:268`

Les monstres et la mort (Manuel p. 199) ; et la Marque Heroique des Arenes : sans mort, on tombe sans agoniser, meme sous des degats massifs.

**Étapes**

1. Le gobelin tombe a 0.
2. Un combat sans mort : Aldric prend 30 degats, les tours passent.

**Résultat attendu**

- Vérifie que `letal.combat.find(letal.gobelin)->status` vaut `CombatantStatus::Dead`.
- Vérifie que `sansMort.combat.find(sansMort.aldric)->status` vaut `CombatantStatus::Down`.
- Vérifie que `sansMort.combat.isDying(sansMort.aldric)` est faux.
- Vérifie que `sansMort.combat.endTurn()` est vrai.
- Vérifie que `jets` vaut `0`.
- Vérifie que `sansMort.combat.find(sansMort.gobelin)->status` vaut `CombatantStatus::Down`.

### DeathAndDyingTest.LeJetSeFaitASaPlaceEtUnVingtRejoue

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:301`

Exigences : `EX-CBT-040`

« A chaque fois que vous commencez un tour a 0 point de vie » : la machine annonce DeathSaveDue a la place d'Aldric, pas a celle d'un stabilise ; un 20 le releve et son tour s'ouvre, debout, trois cases de moins.

**Étapes**

1. Aldric tombe ; Brune stabilisee a terre ; Cedric debout.
2. Les tours passent jusqu'au round 2 ; l'abonne jette 20 pour Aldric.

**Résultat attendu**

- Vérifie que `e.combat.stabilize(e.brune)` est vrai.
- Vérifie que `e.combat.endTurn()` est vrai.
- Vérifie que `jets` vaut `(std::vector<CombatantId>{e.aldric})`.
- Vérifie que `e.combat.round()` vaut `2`.
- Vérifie que `e.combat.activeCombatant()` vaut `e.aldric`.
- Vérifie que `aldric->prone` est faux.
- Vérifie que `aldric->economy.remaining(core::MOVEMENT_RESOURCE)` vaut `3`.

### DeathAndDyingTest.ReviveNeRameneQueLesMorts

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:337`

Seul un mort revient : revive refuse un vivant, et le revenant se releve avec ses points de vie, compteur vide.

**Étapes**

1. revive sur Brune debout.
2. Aldric meurt, revive a 1 PV.

**Résultat attendu**

- Vérifie que `e.combat.revive(e.brune, 1)` est faux.
- Vérifie que `e.combat.find(e.aldric)->status` vaut `CombatantStatus::Dead`.
- Vérifie que `e.combat.find(e.aldric)->diedAtRound.has_value()` est vrai.
- Vérifie que `e.combat.revive(e.aldric, 1)` est vrai.
- Vérifie que `aldric->status` vaut `CombatantStatus::Standing`.
- Vérifie que `aldric->profile.currentHitPoints` vaut `1`.
- Vérifie que `aldric->prone` est vrai.
- Vérifie que `aldric->deathSaves` vaut `core::DeathSaves{}`.
- Vérifie que `aldric->diedAtRound.has_value()` est faux.

### DeathAndDyingTest.UnAllieATerreSeReleveParSoinEtRejoue

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:364`

Exigences : `EX-CBT-041`

Critere du LOT-137 : Bran tombe, inconscient et a terre ; la Priest le soigne au contact ; il se releve, et son tour vient a sa place, ou il se remet debout.

**Étapes**

1. Bran tombe a 0 PV pendant le tour de la Priest.
2. Elle lance soin des blessures sur lui.
3. Elle termine son tour.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `porte(session, CombatantId{2}, CombatCondition::Unconscious)` est vrai.
- Vérifie que `porte(session, CombatantId{2}, CombatCondition::Prone)` est vrai.
- Vérifie que `journalHas(session.journal(), "a terre " + BRAN)` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, sortDe(session, "cure-wounds")).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `bran->status` vaut `CombatantStatus::Standing`.
- Vérifie que `bran->profile.currentHitPoints` est strictement supérieur à `0`.
- Vérifie que `session.conditionsOf(CombatantId{2})` vaut `(std::vector<CombatCondition>{CombatCondition::Prone})`.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{2}`.
- Vérifie que `bran->prone` est faux.
- Vérifie que `bran->economy.remaining(core::MOVEMENT_RESOURCE)` vaut `3`.

### DeathAndDyingTest.LeJetContreLaMortSeJetteDansLArene

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:404`

Exigences : `EX-CBT-040`

Dans une session, qui tient les des jette le d20 de Bran a sa place et l'ecrit : reussite, echec, ou 20 qui le releve.

**Étapes**

1. Bran tombe.
2. La Priest termine son tour.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `journalCount(session.journal(), "jet contre la mort " + BRAN)` vaut `1U`.
- Vérifie que `bran->profile.currentHitPoints` vaut `1`.
- Vérifie que `journalHas(session.journal(), "20 naturel, reprend 1 PV")` est vrai.
- Vérifie que `bran->status` vaut `CombatantStatus::Down`.
- Vérifie que `bran->deathSaves.successes + bran->deathSaves.failures` est supérieur ou égal à `1`.

### DeathAndDyingTest.EpargnerLesMourantsStabilise

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:431`

La Priest de niveau 5 lance epargner les mourants sur Bran a terre : il est stabilise, et son tour passe sans jet.

**Étapes**

1. Bran tombe.
2. Epargner les mourants sur lui ; puis sur la Priest debout.
3. Fin du tour.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.castSpell(CombatantId{1}, epargner).result` vaut `core::ArenaActionResult::InvalidTarget`.
- Vérifie que `session.castSpell(CombatantId{2}, epargner).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), "stabilisation")` est vrai.
- Vérifie que `porte(session, CombatantId{2}, CombatCondition::Stable)` est vrai.
- Vérifie que `porte(session, CombatantId{2}, CombatCondition::Unconscious)` est vrai.
- Vérifie que `session.combat().isDying(CombatantId{2})` est faux.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `journalHas(session.journal(), "jet contre la mort " + BRAN)` est faux.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{3}`.

### DeathAndDyingTest.RevigorerRameneUnMortDeMoinsDUneMinute

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:461`

Bran meurt sous des degats massifs ; soin des blessures ne le ramene pas, revigorer si : 1 PV. Mort de nouveau, onze rounds plus tard, revigorer refuse.

**Étapes**

1. Bran tombe, puis prend 10 degats a terre.
2. Soin, puis revigorer.
3. Il remeurt ; onze rounds passent ; revigorer.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().find(CombatantId{2})->status` vaut `CombatantStatus::Dead`.
- Vérifie que `journalHas(session.journal(), "agonie " + BRAN + " : blesse a terre")` est vrai.
- Vérifie que `journalHas(session.journal(), "mort " + BRAN)` est vrai.
- Vérifie que `porte(session, CombatantId{2}, CombatCondition::Dead)` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, sortDe(session, "cure-wounds")).result` vaut `core::ArenaActionResult::InvalidTarget`.
- Vérifie que `session.castSpell(CombatantId{2}, revigorer).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `journalHas(session.journal(), "retour a la vie")` est vrai.
- Vérifie que `session.combat().find(CombatantId{2})->status` vaut `CombatantStatus::Standing`.
- Vérifie que `session.combat().find(CombatantId{2})->profile.currentHitPoints` vaut `1`.
- Vérifie que `session.combat().find(CombatantId{2})->status` vaut `CombatantStatus::Dead`.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.castSpell(CombatantId{2}, revigorer).result` vaut `core::ArenaActionResult::InvalidTarget`.

### DeathAndDyingTest.FrapperUnInconscientAuContactEstCritique

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:505`

Exigences : `EX-CBT-040`

Manuel, annexe A : Bran, stabilise a terre, est attaque par le gobelin a son contact avec avantage ; touche, le coup est critique et compte deux echecs.

**Étapes**

1. Bran tombe et se stabilise.
2. Tour du gobelin : il attaque Bran.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().stabilize(CombatantId{2})` est vrai.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{3}`.
- Vérifie que `coup.result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `coup.outcome.has_value()` est vrai.
- Vérifie que `std::ranges::find(avantages, "cible inconsciente")` diffère de `avantages.end()`.
- Vérifie que `std::ranges::find(avantages, "cible a terre au contact")` diffère de `avantages.end()`.
- Vérifie que `coup.outcome->roll.critical` est vrai.
- Vérifie que `bran->status == CombatantStatus::Dead || bran->deathSaves.failures == 2` est vrai.
- Vérifie que `journalHas(session.journal(), "critique (cible inconsciente au contact)")` est vrai.

### DeathAndDyingTest.DesDegatsRompentLaConcentration

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:538`

La Priest benie et concentree prend 100 degats : DD 50, la sauvegarde de Constitution echoue, la benediction prend fin.

**Étapes**

1. Benediction sur elle-meme.
2. 100 degats.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.castSpell(CombatantId{1}, sortDe(session, "bless")).result` vaut `core::ArenaActionResult::Done`.
- Vérifie que `porte(session, CombatantId{1}, CombatCondition::Blessed)` est vrai.
- Vérifie que `porte(session, CombatantId{1}, CombatCondition::Concentrating)` est vrai.
- Vérifie que `core::combatConditionLabel(CombatCondition::Concentrating)` vaut `"concentre"`.
- Vérifie que `journalHas(session.journal(), "< 50 : echec ; rompue")` est vrai.
- Vérifie que `journalHas(session.journal(), "(concentration rompue)")` est vrai.
- Vérifie que `session.hasEffect(CombatantId{1}, core::SpellEffectKind::Bless)` est faux.
- Vérifie que `porte(session, CombatantId{1}, CombatCondition::Concentrating)` est faux.

### DeathAndDyingTest.LIaAcheveOuEpargneSelonSonProfil

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_death_and_dying.cpp:569`

Exigences : `EX-CBT-050`

Critere du LOT-137 et du LOT-139 : un gobelin au contact de Bran, a terre. Aldric, debout, est a trois cases (3 m entre les bords) : un profil qui n'acheve pas va frapper Aldric ; un profil qui acheve frappe Bran. Aldric revenu au contact, meme le profil qui acheve frappe Aldric. Les profils livres disent qui acheve.

**Étapes**

1. Aldric a trois cases : planifier le tour du gobelin avec finishDowned 0, puis 1000.
2. Aldric au contact : planifier avec finishDowned 1000.
3. Lire behaviors.json.

**Résultat attendu**

- Vérifie que `session->start()` est vrai.
- Vérifie que `session->combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `session->combat().find(CombatantId{2})->status` vaut `CombatantStatus::Down`.
- Vérifie que `clement.action` vaut `core::TurnAction::Attack`.
- Vérifie que `clement.target` vaut `CombatantId{3}`.
- Vérifie que `cruel.action` vaut `core::TurnAction::Attack`.
- Vérifie que `cruel.target` vaut `CombatantId{2}`.
- Vérifie que `menace.action` vaut `core::TurnAction::Attack`.
- Vérifie que `menace.target` vaut `CombatantId{3}`.
- Vérifie que `profils.errors.empty()` est vrai.
- Vérifie que `profils.find("aggressive")->finishDowned` vaut `75`.
- Vérifie que `profils.find("pack")->finishDowned` vaut `100`.
- Vérifie que `profils.find(id)->finishDowned` vaut `0`.

## test_encounter.cpp

### EncounterTest.UnAllerRetourRestitueLEtatDExploration

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:52`

Un aller-retour exploration -> combat -> exploration restitue l'etat.

**Étapes**

1. Relever un etat d'exploration.
2. Engager une rencontre.
3. La terminer par une victoire.

**Résultat attendu**

- Vérifie que `apres.captured` est vrai.
- Vérifie que `apres.playerPosition.x` vaut `avant.playerPosition.x` (comparaison flottante).
- Vérifie que `apres.playerPosition.y` vaut `avant.playerPosition.y` (comparaison flottante).
- Vérifie que `apres.playerFacing.x` vaut `avant.playerFacing.x` (comparaison flottante).
- Vérifie que `apres.playerFacing.y` vaut `avant.playerFacing.y` (comparaison flottante).
- Vérifie que `apres.cameraPosition.x` vaut `avant.cameraPosition.x` (comparaison flottante).
- Vérifie que `apres.cameraPosition.y` vaut `avant.cameraPosition.y` (comparaison flottante).

### EncounterTest.UnEnnemiVaincuNeReapparaitPas

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:80`

Un ennemi vaincu ne reapparait pas.

**Étapes**

1. Gagner une rencontre portant une cle de drapeau.
2. Interroger les drapeaux.

**Résultat attendu**

- Vérifie que `core::encounterAlreadyCleared(drapeaux, cle)` est faux.
- Vérifie que `drapeaux.isSet(cle)` est vrai.
- Vérifie que `core::encounterAlreadyCleared(drapeaux, cle)` est vrai.

### EncounterTest.UneFuiteNeMarquePasLEnnemiVaincu

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:104`

Une fuite ne marque pas l'ennemi vaincu.

**Étapes**

1. Engager une rencontre portant une cle de drapeau.
2. La terminer par une fuite, puis par une defaite.

**Résultat attendu**

- Vérifie que `drapeaux.isSet(cle)` est faux.
- Vérifie que `apresFuite.captured` est vrai.
- Vérifie que `drapeaux.isSet(cle)` est faux.

### EncounterTest.UneRencontreSansCleSeRedeclenche

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:129`

Une rencontre sans cle de drapeau se redeclenche.

**Étapes**

1. Gagner une rencontre sans cle de drapeau.

**Résultat attendu**

- Vérifie que `core::encounterAlreadyCleared(drapeaux, "")` est faux.

### EncounterTest.UneVictoirePoseLeFaitDeLaRencontreGagnee

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:150`

Une victoire pose le fait encounter/&lt;id&gt;/won, une fuite non.

**Étapes**

1. Gagner une rencontre sans cle d'entite.
2. En fuir une autre.

**Résultat attendu**

- Vérifie que `fait` vaut `"encounter/" + modele.id + "/won"`.
- Vérifie que `drapeaux.isSet(fait)` est faux.
- Vérifie que `drapeaux.isSet(fait)` est vrai.

### EncounterTest.LesCombattantsSePlacentRelativementAuDeclencheur

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:176`

Les combattants se placent relativement au declencheur.

**Étapes**

1. Placer la meme rencontre a deux endroits differents.

**Résultat attendu**

- Vérifie que `ici.size()` vaut `2U`.
- Vérifie que `ici[0].position.column` vaut `10`.
- Vérifie que `ici[0].position.row` vaut `9`.
- Vérifie que `ici[1].position.column` vaut `12`.
- Vérifie que `ici[1].position.row` vaut `11`.
- Vérifie que `ailleurs.size()` vaut `2U`.
- Vérifie que `ailleurs[rang].creatureId` vaut `ici[rang].creatureId`.
- Vérifie que `ailleurs[rang].position.column - ici[rang].position.column` vaut `30`.
- Vérifie que `ailleurs[rang].position.row - ici[rang].position.row` vaut `-8`.

### EncounterTest.UneRencontreNonFuyableLeDeclare

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:206`

Une rencontre non fuyable le declare.

**Étapes**

1. Engager une rencontre declaree non fuyable.

**Résultat attendu**

- Vérifie que `core::beginEncounter(rencontre(true), exploration(), {}, "").escapable` est vrai.
- Vérifie que `core::beginEncounter(rencontre(false), exploration(), {}, "").escapable` est faux.

### EncounterTest.LeCatalogueLivreSeCharge

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:222`

Le catalogue de rencontres livre se charge.

**Étapes**

1. Charger Source/Elements/Rpg/encounters.

**Résultat attendu**

- Vérifie que `catalogue.errors.empty()` est vrai.
- Vérifie que `catalogue.encounters.empty()` est faux.
- Vérifie que `combat.id.empty()` est faux.
- Vérifie que `combat.name.empty()` est faux.
- Vérifie que `combat.combatants.empty()` est faux.
- Vérifie que `combattant.creatureId.empty()` est faux.
- Vérifie que `catalogue.find("colisee-fauves")` diffère de `nullptr`.
- Vérifie que `catalogue.find("rencontre-qui-n-existe-pas")` vaut `nullptr`.

### EncounterTest.UnInstantaneNonReleveSeDistingueDeLOrigine

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:250`

Un instantane non releve se distingue de l'origine.

**Étapes**

1. Construire un instantane par defaut.

**Résultat attendu**

- Vérifie que `vide.captured` est faux.

### EncounterTest.UnEnnemiPosePorteUneCleUneZoneNonN

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:266`

Un ennemi pose porte une cle, une zone n'en porte pas.

**Étapes**

1. Lire une entite de rencontre posee.
2. Lire la meme avec respawns.

**Résultat attendu**

- Vérifie que `declencheur.has_value()` est vrai.
- Vérifie que `declencheur->encounterId` vaut `"colisee-fauves"`.
- Vérifie que `declencheur->position.column` vaut `5`.
- Vérifie que `declencheur->defeatFlagKey.empty()` est faux.
- Vérifie que `declencheurZone.has_value()` est vrai.
- Vérifie que `declencheurZone->defeatFlagKey.empty()` est vrai.

### EncounterTest.DeuxDeclencheursNePartagentJamaisLeurCle

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:297`

Deux declencheurs ne partagent jamais leur cle.

**Étapes**

1. Lire deux entites de rencontre a des cases differentes de la meme carte.
2. Lire la meme case sur deux cartes differentes.

**Résultat attendu**

- Vérifie que `a && b && ailleurs` est vrai.
- Vérifie que `a->defeatFlagKey` diffère de `b->defeatFlagKey`.
- Vérifie que `a->defeatFlagKey` diffère de `ailleurs->defeatFlagKey`.

### EncounterTest.CeQuiNEstPasUnDeclencheurNEnDevientPasUn

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_encounter.cpp:323`

Ce qui n'est pas un declencheur n'en devient pas un.

**Étapes**

1. Lire une entite d'un autre type.
2. Lire une entite de rencontre sans encounterId.

**Résultat attendu**

- Vérifie que `core::encounterTriggerFor(coffre, "grotte").has_value()` est faux.
- Vérifie que `core::encounterTriggerFor(sansRencontre, "grotte").has_value()` est faux.

## test_encounter_difficulty.cpp

### EncounterDifficultyTest.LesReglesSeChargent

*Critique · Unitaire · Combat · Budget* — `Source/Test/Unit/Core/Combat/test_encounter_difficulty.cpp:35`

Les regles du budget de rencontre se chargent.

**Étapes**

1. Charger `Rpg/rules/encounter-difficulty.json`.

**Résultat attendu**

- Vérifie que `rules.ok()` est vrai.
- Vérifie que `rules.categories` vaut `(std::vector<std::string>{"facile", "moyenne", "difficile", "mortelle"})`.
- Vérifie que `rules.thresholds.size()` vaut `20U`.
- Vérifie que `rules.thresholds.front().experience.at("facile")` vaut `25`.
- Vérifie que `rules.thresholds.back().experience.at("mortelle")` vaut `12700`.
- Vérifie que `core::experienceForChallenge(rules, 0.125F)` vaut `25`.
- Vérifie que `core::experienceForChallenge(rules, 5.0F)` vaut `1800`.
- Vérifie que `core::experienceForChallenge(rules, 42.0F)` vaut `0`.

### EncounterDifficultyTest.LExempleDuLivreTient

*Critique · Unitaire · Combat · Budget* — `Source/Test/Unit/Core/Combat/test_encounter_difficulty.cpp:60`

Les seuils du groupe et le multiplicateur suivent l'exemple du Guide du Maitre.

**Étapes**

1. Sommer les seuils de trois niveaux 3 et un niveau 2.
2. Multiplier 500 PX de quatre monstres.
3. Comparer le multiplicateur d'un groupe de deux et de six.

**Résultat attendu**

- Vérifie que `seuils.at("facile")` vaut `275`.
- Vérifie que `seuils.at("moyenne")` vaut `550`.
- Vérifie que `seuils.at("difficile")` vaut `825`.
- Vérifie que `seuils.at("mortelle")` vaut `1400`.
- Vérifie que `core::encounterMultiplierFor(rules, 4, 4)` vaut `2.0` (comparaison flottante).
- Vérifie que `core::encounterMultiplierFor(rules, 1, 4)` vaut `1.0` (comparaison flottante).
- Vérifie que `core::encounterMultiplierFor(rules, 2, 4)` vaut `1.5` (comparaison flottante).
- Vérifie que `core::encounterMultiplierFor(rules, 15, 4)` vaut `4.0` (comparaison flottante).
- Vérifie que `core::encounterMultiplierFor(rules, 1, 2)` vaut `1.5` (comparaison flottante).
- Vérifie que `core::encounterMultiplierFor(rules, 15, 2)` vaut `5.0` (comparaison flottante).
- Vérifie que `core::encounterMultiplierFor(rules, 1, 6)` vaut `0.5` (comparaison flottante).
- Vérifie que `core::encounterMultiplierFor(rules, 4, 6)` vaut `1.5` (comparaison flottante).

### EncounterDifficultyTest.LesBanditsDeLaDemoSontUneRencontreDifficile

*Critique · Unitaire · Combat · Budget* — `Source/Test/Unit/Core/Combat/test_encounter_difficulty.cpp:93`

Les bandits de l'Arena of Fate sont une rencontre difficile pour le groupe de depart.

**Étapes**

1. Juger `arene-bandits` pour quatre niveaux 1.
2. Juger une rencontre d'une creature inconnue.

**Résultat attendu**

- Vérifie que `bandits` diffère de `nullptr`.
- Vérifie que `budget.monsters` vaut `6`.
- Vérifie que `budget.monsterExperience` vaut `150`.
- Vérifie que `budget.multiplier` vaut `2.0` (comparaison flottante).
- Vérifie que `budget.adjustedExperience` vaut `300`.
- Vérifie que `budget.thresholds.at("difficile")` vaut `300`.
- Vérifie que `budget.thresholds.at("mortelle")` vaut `400`.
- Vérifie que `budget.category` vaut `"difficile"`.
- Vérifie que `budget.unknownCreatures.empty()` est vrai.
- Vérifie que `vide.monsters` vaut `0`.
- Vérifie que `vide.category.empty()` est vrai.
- Vérifie que `vide.unknownCreatures.size()` vaut `1U`.
- Vérifie que `vide.unknownCreatures.front()` vaut `"dragon-de-papier"`.

## test_enemy_ai.cpp

### FlankingTest.LAngleAuCentreTranche

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:121`

Deux allies prennent un ennemi en tenaille si leurs centres forment au centre de la cible un angle d'au moins 135 degres, s'ils sont a une case de lui (ecart entre les bords d'au plus 1,5 m), debout, et le voient.

**Étapes**

1. Un ennemi au centre de la case (5,5) ; tester, aux centres des cases voisines, des cotes opposes, des angles opposes, un cote et l'angle oppose, une position en L et deux cases du meme cote.
2. Un ennemi de taille G sur (5,5)-(6,6).
3. Dans un combat : l'allie a terre, une autre place de l'attaquant, puis un allie a une case de l'ennemi mais derriere un mur.

**Résultat attendu**

- Vérifie que `core::flanksByAngle(tile(4, 5), tile(6, 5), moyen)` est vrai.
- Vérifie que `core::flanksByAngle(tile(5, 4), tile(5, 6), moyen)` est vrai.
- Vérifie que `core::flanksByAngle(tile(4, 4), tile(6, 6), moyen)` est vrai.
- Vérifie que `core::flanksByAngle(tile(6, 4), tile(4, 6), moyen)` est vrai.
- Vérifie que `core::flanksByAngle(tile(4, 5), tile(6, 6), moyen)` est vrai.
- Vérifie que `core::flanksByAngle(tile(4, 4), tile(6, 5), moyen)` est vrai.
- Vérifie que `core::flanksByAngle(tile(4, 4), tile(4, 6), moyen)` est faux.
- Vérifie que `core::flanksByAngle(tile(4, 5), tile(5, 4), moyen)` est faux.
- Vérifie que `core::flanksByAngle(tile(4, 5), tile(7, 6), grand)` est vrai.
- Vérifie que `core::flanksByAngle(tile(4, 4), tile(7, 7), grand)` est vrai.
- Vérifie que `core::flanksByAngle(tile(4, 5), tile(5, 7), grand)` est faux.
- Vérifie que `core::isFlanked(session.combat(), CombatantId{1}, CombatantId{3})` est vrai.
- Vérifie que `core::isFlanked(session.combat(), CombatantId{2}, CombatantId{3})` est vrai.
- Vérifie que `core::isFlankedFrom(session.combat(), CombatantId{1}, tile(5, 2), CombatantId{3})` est faux.
- Vérifie que `core::isFlanked(session.combat(), CombatantId{3}, CombatantId{1})` est faux.
- Vérifie que `core::isFlanked(session.combat(), CombatantId{1}, CombatantId{3})` est faux.
- Vérifie que `core::flanksByAngle(tile(4, 3), tile(7, 3), tile(5, 3))` est vrai.
- Vérifie que `core::adjacentGap(ecart(murs, CombatantId{2}, CombatantId{3}))` est vrai.
- Vérifie que `core::hasLineOfSight(murs.combat(), CombatantId{2}, CombatantId{3})` est faux.
- Vérifie que `core::isFlanked(murs.combat(), CombatantId{1}, CombatantId{3})` est faux.

### FlankingTest.LaTenailleDonneLAvantageDansLArene

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:187`

Dans une arene a prise en tenaille, une attaque au corps a corps contre un ennemi pris en tenaille est jetee avec avantage, et le journal le dit ; ailleurs, non.

**Étapes**

1. Deux allies de part et d'autre d'un ennemi, le premier joue.
2. Il attaque, dans une arene avec tenaille puis sans.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `attaque.outcome.has_value()` est vrai.
- Vérifie que `attaque.outcome->roll.check.stance` vaut `tenaille ? core::RollStance::Advantage : core::RollStance::Normal`.
- Vérifie que `attaque.outcome->describe().find("prise en tenaille") != std::string::npos` vaut `tenaille`.

### EnemyAiTest.LeJetRequisEtLEsperanceSuiventLeGuide

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:218`

Le jet requis est la CA moins le bonus d'attaque ; la chance de toucher et l'esperance de degats en decoulent, en entiers.

**Étapes**

1. L'exemple du Guide : des orcs a +5 contre un guerrier a CA 19.
2. La chance d'un jet requis de 14, normal, avec avantage, avec desavantage ; d'un jet requis de 1 et de 25.
3. L'esperance d'un gobelin (+4, 1d6+2) contre CA 15, et contre CA 15 avec un seuil critique a 19.

**Résultat attendu**

- Vérifie que `core::requiredRoll(19, 5)` vaut `14`.
- Vérifie que `core::hitChance(14, core::RollStance::Normal)` vaut `140`.
- Vérifie que `core::hitChance(14, core::RollStance::Advantage)` vaut `231`.
- Vérifie que `core::hitChance(14, core::RollStance::Disadvantage)` vaut `49`.
- Vérifie que `core::hitChance(1, core::RollStance::Normal)` vaut `380`.
- Vérifie que `core::hitChance(25, core::RollStance::Normal)` vaut `20`.
- Vérifie que `core::criticalChance(20, core::RollStance::Normal)` vaut `20`.
- Vérifie que `core::criticalChance(19, core::RollStance::Advantage)` vaut `400 - 18 * 18`.
- Vérifie que `core::attackBonusOf(gobelin)` vaut `4`.
- Vérifie que `core::expectedDamage(gobelin, 15, core::RollStance::Normal)` vaut `2340`.
- Vérifie que `core::expectedDamage(gobelin, 15, core::RollStance::Normal)` vaut `11 * 200 + 7 * 40`.

### EnemyAiTest.LesProfilsSontDesDonnees

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:252`

Les profils de comportement livres se chargent sans erreur, ne tolerent jamais trois menaces, et s'attribuent aux creatures par leurs regles.

**Étapes**

1. Charger behaviors.json.
2. Charger le bestiaire, lire le profil du loup (Tactique de groupe), du sanglier et du singe.
3. Un sanglier synthetique qui tire plus fort qu'il ne mord.

**Résultat attendu**

- Vérifie que `profils.errors.empty()` est vrai.
- Vérifie que `profil` diffère de `nullptr`.
- Vérifie que `profil->toleratedThreats` est inférieur ou égal à `2`.
- Vérifie que `profil->approachPerTile` est strictement supérieur à `0`.
- Vérifie que `profils.defaultBehavior` vaut `"aggressive"`.
- Vérifie que `trouver("wolf")` diffère de `bestiaire.creatures.end()`.
- Vérifie que `trouver("boar")` diffère de `bestiaire.creatures.end()`.
- Vérifie que `trouver("ape")` diffère de `bestiaire.creatures.end()`.
- Vérifie que `core::behaviorFor(*trouver("wolf"), profils)` vaut `"pack"`.
- Vérifie que `core::behaviorFor(*trouver("boar"), profils)` vaut `"aggressive"`.
- Vérifie que `core::behaviorFor(*trouver("ape"), profils)` vaut `"archer"`.
- Vérifie que `core::behaviorFor(tireur, profils)` vaut `"archer"`.

### EnemyAiTest.LIaNeLitQueLEtatEnsanglante

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:309`

Exigences : `EX-CBT-050`

Les points de vie d'un adversaire restent secrets : deux cibles qui ne different que par des points de vie au-dessus de la moitie sont indiscernables ; une cible ensanglantee est preferee.

**Étapes**

1. Un gobelin agressif au contact de deux heros identiques, a 20/20 et 11/20.
2. Planifier son tour.
3. Le second passe a 9/20, planifier encore.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{3}`.
- Vérifie que `plein.action` vaut `core::TurnAction::Attack`.
- Vérifie que `plein.target` vaut `CombatantId{1}`.
- Vérifie que `entame.target` vaut `CombatantId{1}`.
- Vérifie que `entame.score` vaut `plein.score`.
- Vérifie que `ensanglante.target` vaut `CombatantId{2}`.
- Vérifie que `ensanglante.score` est strictement supérieur à `plein.score`.

### EnemyAiTest.PasDeSuicideQuandUneCaseSureExiste

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:349`

Aucun profil ne finit son tour a portee immediate de trois ennemis quand une place moins exposee etait atteignable.

**Étapes**

1. Trois heros inoffensifs aux centres des cases (6,2), (6,4) et (7,3), le dernier ensanglante ; le centre de (6,3) les touche tous, et les places d'ou le gobelin prend le heros ensanglante en tenaille avec son complice en (8,3) -- les plus rentables -- sont a une case des trois. D'autres places frappent au plus deux heros.
2. Pour chaque profil livre, jouer le tour du gobelin.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{4}`.
- Vérifie que `core::playTurn(session, profils)` est vrai.
- Vérifie que `aPortee` est inférieur ou égal à `2`.
- Vérifie que `core::groundDistance(fin, tile(6, 3))` est strictement supérieur à `0.01f`.

### EnemyAiTest.UnTireurNeComptePasDansLAntiSuicide

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:397`

Deux archers allies qui couvrent toute la salle n'empechent pas un prudent d'aller frapper le heros au contact.

**Étapes**

1. Salle 12x8 : un heros de contact en (7,3), deux archers allies en (2,2) et (2,5) dont la portee couvre la salle, un gobelin prudent (tolere une menace) en (5,3).
2. Planifier le tour du gobelin.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{4}`.
- Vérifie que `plan.action` vaut `core::TurnAction::Attack`.
- Vérifie que `plan.target` vaut `CombatantId{1}`.
- Vérifie que `plan.immediateThreats` vaut `1`.

### EnemyAiTest.SansAttaquePossibleChaqueProfilAvance

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:430`

Dans une salle aux dimensions de l'arene, un ennemi de chaque profil qui ne peut pas encore frapper se rapproche a chaque tour, jusqu'a attaquer.

**Étapes**

1. Salle 20x14, heros en (3,6) (+4, 1d8+2), ennemi de contact en (16,6) : treize cases entre les centres, 18 m entre les bords. Pour chacun des profils livres.
2. Le heros passe son tour ; jouer l'ennemi par l'IA, jusqu'a six tours.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `distance` vaut `18.0f`, à `0.01f` près.
- Vérifie que `session.endTurn()` est vrai.
- Vérifie que `core::playTurn(session, profils)` est vrai.
- Vérifie que `apres` est strictement inférieur à `distance - 0.01f`.
- Vérifie que `aAttaque()` est vrai.
- Vérifie que `toursEnnemi` est inférieur ou égal à `4`.

### EnemyAiTest.LeRepliVaALaCaseSureLaPlusProche

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:494`

Une archere prudente tire puis recule juste hors de portee du heros, vers la place la plus proche de lui.

**Étapes**

1. Salle 20x8, heros de contact en (16,3) (6 cases : 9 m), archere prudente en (10,3) a 7 cases de portee (10,5 m entre les bords) : le heros atteint en un tour toute place a moins de 12 m de son centre, et elle tire de la ou elle est.
2. Jouer le tour de l'archere.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{2}`.
- Vérifie que `core::playTurn(session, profils)` est vrai.
- Vérifie que `std::ranges::any_of( journal, [](const std::string& l) { return l.starts_with("attaque Archere -> Heros"); })` est vrai.
- Vérifie que `std::ranges::any_of( journal, [](const std::string& l) { return l.find(": recule en") != std::string::npos; })` est vrai.
- Vérifie que `core::adjacentGap( core::edgeDistance(core::volumeOf(d.point, core::CreatureSize::Medium), elle))` est faux.
- Vérifie que `auHeros` est strictement supérieur à `12.0f`.
- Vérifie que `auHeros` est strictement inférieur à `13.5f`.

### EnemyAiTest.LArchereChercheLaVue

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:545`

Une IA archere cachee de sa cible par un pan de mur se deplace jusqu'a une place qui la voit et tire ; elle n'essaie jamais un tir que la ligne de vue refuse.

**Étapes**

1. Une archere en (3,3), un heros en (8,3) derriere un pan de mur en (6,2)-(6,4) ; elle ne le voit pas.
2. Jouer son tour par l'IA.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{2}`.
- Vérifie que `core::hasLineOfSight(session.combat(), CombatantId{2}, CombatantId{1})` est faux.
- Vérifie que `plan.action` vaut `core::TurnAction::Attack`.
- Vérifie que `plan.moveTo.has_value()` est vrai.
- Vérifie que `core::hasLineOfSightFrom(session.combat(), CombatantId{2}, *plan.moveTo, CombatantId{1})` est vrai.
- Vérifie que `core::playTurn(session, profils)` est vrai.
- Vérifie que `std::ranges::any_of( journal, [](const std::string& l) { return l.starts_with("attaque Archere -> Heros"); })` est vrai.

### EnemyAiTest.SePrecipiterEtChoisirSesOpportunites

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:580`

Une IA qui ne peut attaquer se precipite vers l'ennemi le plus proche ; une IA prudente laisse passer une attaque d'opportunite dont le jet requis depasse son seuil, une agressive la prend.

**Étapes**

1. Un gobelin agressif a seize cases d'un heros ; jouer son tour.
2. Un ogre au contact d'un heros a CA 20 (+4 : jet requis 16) ; le heros s'eloigne au centre de (2,5), hors de l'allonge, l'ogre prudent puis agressif.

**Résultat attendu**

- Vérifie que `session.start()` est vrai.
- Vérifie que `core::playTurn(session, profils)` est vrai.
- Vérifie que `std::ranges::any_of(session.journal(), [](const std::string& l) { return l.starts_with("precipitation Gobelin"); })` est vrai.
- Vérifie que `core::groundDistance(*session.combat().positionOf(CombatantId{2}), tile(1, 1))` est strictement supérieur à `core::metersFromTiles(6.0f)`.
- Vérifie que `session.start()` est vrai.
- Vérifie que `session.combat().activeCombatant()` vaut `CombatantId{1}`.
- Vérifie que `session.move(tile(2, 5)).result` vaut `core::MoveResult::Moved`.
- Vérifie que `core::adjacentGap(ecart(session, CombatantId{1}, CombatantId{2}))` est faux.
- Vérifie que `prises` vaut `std::string(profil) == "aggressive" ? 1 : 0`.

### EnemyAiTest.UnCombatIaContreIaSeTermineToujoursEtSeRejoue

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_enemy_ai.cpp:631`

Sur des configurations generees -- salles, piliers, compositions, profils, tireurs, tenaille ou non --, un combat joue par l'IA des deux cotes atteint son issue ; a graine fixee, deux parties donnent le meme journal.

**Étapes**

1. Pour trente graines, generer une salle de 10 a 16 cases sur 8 a 10 avec des piliers, deux a quatre combattants par camp poses aux centres de leurs cases, chacun avec un profil livre, un tiers de tireurs, la tenaille une fois sur deux.
2. Jouer par l'IA jusqu'a l'issue, avec une garde de 600 tours.
3. Une graine sur trois, rejouer par `replay`.

**Résultat attendu**

- Vérifie que `profils.errors.empty()` est vrai.
- Vérifie que `montage.refusals.empty()` est vrai.
- Vérifie que `session.start()` est vrai.
- Vérifie que `tours` est supérieur ou égal à `0`.
- Vérifie que `session.outcome().has_value()` est vrai.
- Vérifie que `jouerParLIa(session, profils)` vaut `tours`.
- Vérifie que `session.journal()` vaut `journal`.
- Vérifie que `longest` est strictement supérieur à `0`.

## test_map_encounter.cpp

### MapEncounterTest.LaZoneDuDeclencheurEstChoisieEtLesCasesTranslatees

*Critique · Unitaire · Combat sur la carte* — `Source/Test/Unit/Core/Combat/test_map_encounter.cpp:65`

Une rencontre se pose sur la zone de combat du declencheur, cases translatees.

**Étapes**

1. Preparer une rencontre de deux loups, declenchee en (14, 8), heros en (15, 10), sur une carte dont la zone « cour » couvre (10, 5) a (19, 12).

**Résultat attendu**

- Vérifie que `resultat.ok()` est vrai.
- Vérifie que `montage.zone.name` vaut `"cour"`.
- Vérifie que `montage.battlefield.tileMap().width()` vaut `10`.
- Vérifie que `montage.battlefield.tileMap().height()` vaut `8`.
- Vérifie que `montage.heroCell` vaut `(core::GridPosition{.column = 5, .row = 5})`.
- Vérifie que `montage.run.placements.size()` vaut `2U`.
- Vérifie que `montage.run.placements[0].position` vaut `(core::GridPosition{.column = 4, .row = 2})`.
- Vérifie que `montage.run.placements[1].position` vaut `(core::GridPosition{.column = 5, .row = 3})`.
- Vérifie que `montage.run.escapable` est faux.
- Vérifie que `montage.run.defeatFlagKey` vaut `"essai/loups"`.
- Vérifie que `montage.notes.empty()` est vrai.
- Vérifie que `core::zoneToMap(montage.zone, montage.heroCell)` vaut `(core::GridPosition{.column = 15, .row = 10})`.
- Vérifie que `core::mapToZone(montage.zone, {.column = 15, .row = 10})` vaut `montage.heroCell`.

### MapEncounterTest.UnePlaceImpossibleSeRapprocheEtSeNote

*Critique · Unitaire · Combat sur la carte* — `Source/Test/Unit/Core/Combat/test_map_encounter.cpp:100`

Une place impossible est rapprochee de la case voulue, et notee.

**Étapes**

1. Declencher en (12, 7) : le loup « un pas devant » vise (12, 6), un mur.
2. Declencher en (10, 5) avec le heros hors de la zone, en (2, 2) : le second loup vise (11, 5), la place du heros vise une case hors zone.

**Résultat attendu**

- Vérifie que `mur.ok()` est vrai.
- Vérifie que `posee` diffère de `(core::GridPosition{.column = 12, .row = 6})`.
- Vérifie que `std::max(std::abs(posee.column - 12), std::abs(posee.row - 6))` est inférieur ou égal à `1`.
- Vérifie que `mur.setup->notes.size()` vaut `1U`.
- Vérifie que `mur.setup->notes.front().find("wolf")` diffère de `std::string::npos`.
- Vérifie que `dehors.ok()` est vrai.
- Vérifie que `core::zoneToMap(dehors.setup->zone, dehors.setup->heroCell)` vaut `(core::GridPosition{.column = 10, .row = 5})`.
- Vérifie que `std::ranges::find(cases, place.position)` vaut `cases.end()`.
- Vérifie que `dehors.setup->zone.contains(core::zoneToMap(dehors.setup->zone, place.position))` est vrai.

### MapEncounterTest.LeGroupeEntreLaOuIlMarche

*Critique · Unitaire · Combat sur la carte* — `Source/Test/Unit/Core/Combat/test_map_encounter.cpp:141`

Les cases du groupe se posent dans l'ordre de marche, sans partage.

**Étapes**

1. Preparer les loups, declenches en (14, 8), le groupe en (15, 10), (16, 10), (17, 10) et (22, 10) -- la derniere hors de la zone « cour ».
2. Preparer avec un groupe vide.

**Résultat attendu**

- Vérifie que `resultat.ok()` est vrai.
- Vérifie que `montage.partyCells.size()` vaut `4U`.
- Vérifie que `montage.heroCell` vaut `montage.partyCells.front()`.
- Vérifie que `montage.partyCells[0]` vaut `(core::GridPosition{.column = 5, .row = 5})`.
- Vérifie que `montage.partyCells[1]` vaut `(core::GridPosition{.column = 6, .row = 5})`.
- Vérifie que `montage.partyCells[2]` vaut `(core::GridPosition{.column = 7, .row = 5})`.
- Vérifie que `montage.zone.contains(dernier)` est vrai.
- Vérifie que `std::max(std::abs(dernier.column - 22), std::abs(dernier.row - 10))` vaut `3`.
- Vérifie que `cases[i]` diffère de `cases[j]`.
- Vérifie que `montage.notes.size()` vaut `1U`.
- Vérifie que `montage.notes.front().find("suiveur 3")` diffère de `std::string::npos`.
- Vérifie que `vide.ok()` est faux.
- Vérifie que `vide.issue.find("groupe")` diffère de `std::string::npos`.

### MapEncounterTest.SansZoneLaRencontreEstRefusee

*Majeur · Unitaire · Combat sur la carte* — `Source/Test/Unit/Core/Combat/test_map_encounter.cpp:191`

Une rencontre hors de toute zone de combat est refusee.

**Étapes**

1. Declencher en (2, 2), heros en (3, 3), hors de la zone « cour ».

**Résultat attendu**

- Vérifie que `resultat.ok()` est faux.
- Vérifie que `resultat.issue.find("essai")` diffère de `std::string::npos`.
- Vérifie que `resultat.issue.find("2,2")` diffère de `std::string::npos`.
- Vérifie que `resultat.issue.find("3,3")` diffère de `std::string::npos`.

## test_party_deployment.cpp

### PartyDeploymentTest.UneZoneDegageePorteLeGroupeFaceALaRencontre

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_party_deployment.cpp:86`

Une zone dégagée porte le groupe de quatre face à la rencontre.

**Étapes**

1. Une zone de 10 x 6 en (2, 2) sur un champ de 20 x 20, une rencontre de deux rats dont le marqueur est en (9, 4), au bord droit.
2. Juger le déploiement.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdict.valid()` est vrai.
- Vérifie que `verdict.encounterIndex` vaut `1U`.
- Vérifie que `verdict.zoneIndex` vaut `0U`.
- Vérifie que `verdict.partySize` vaut `core::TACTICAL_PARTY_SIZE`.
- Vérifie que `verdict.reachableCells` vaut `60`.
- Vérifie que `verdict.requiredCells` vaut `(2 + 4) * core::TACTICAL_CELLS_PER_COMBATANT`.
- Vérifie que `verdict.partyPlaces.size()` vaut `4U`.
- Vérifie que `verdict.partyPlaces.front()` vaut `(GridPosition{2, 2})`.
- Vérifie que `place.column` est inférieur ou égal à `3`.

### PartyDeploymentTest.LeGroupeEntreDAbordParLesEntreesAlliees

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_party_deployment.cpp:117`

Le groupe entre d'abord par les entrées alliées.

**Étapes**

1. La zone dégagée, deux entrées alliées de rangs 2 et 1 dans la zone, une troisième hors de la zone.
2. Juger.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdict.valid()` est vrai.
- Vérifie que `verdict.partyPlaces.size()` vaut `4U`.
- Vérifie que `verdict.partyPlaces[0]` vaut `(GridPosition{4, 3})`.
- Vérifie que `verdict.partyPlaces[1]` vaut `(GridPosition{5, 6})`.
- Vérifie que `std::ranges::count(verdict.partyPlaces, GridPosition{15, 15})` vaut `0`.

### PartyDeploymentTest.UneZoneQuiLaisseLaFormationDehorsEstRefusee

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_party_deployment.cpp:144`

Une zone qui laisse la formation dehors est refusée.

**Étapes**

1. La zone ramenée à 5 x 6, le marqueur en (9, 4) au-dehors.
2. Juger.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdict.valid()` est faux.
- Vérifie que `verdict.zoneIndex` vaut `0U`.
- Vérifie que `verdict.issues.size()` est supérieur ou égal à `3U`.
- Vérifie que `verdict.issues[0].code` vaut `DeploymentIssueCode::TriggerOutsideZone`.
- Vérifie que `verdict.issues[1].code` vaut `DeploymentIssueCode::CombatantOutsideZone`.
- Vérifie que `verdict.issues[1].cell` vaut `(GridPosition{9, 3})`.
- Vérifie que `verdict.issues[2].code` vaut `DeploymentIssueCode::CombatantOutsideZone`.
- Vérifie que `verdict.issues[2].creatureId` vaut `"rat"`.

### PartyDeploymentTest.UneZoneTropPetiteEstTropEtroite

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_party_deployment.cpp:171`

Une zone de 3 x 2 ne loge ni le groupe ni la manœuvre.

**Étapes**

1. Une zone de 3 x 2 autour d'une rencontre de deux rats.
2. Juger.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdict.reachableCells` vaut `6`.
- Vérifie que `verdict.partyPlaces.size()` vaut `4U`.
- Vérifie que `releve(verdict, DeploymentIssueCode::PartyCannotDeploy)` est faux.
- Vérifie que `releve(verdict, DeploymentIssueCode::ZoneTooNarrow)` est vrai.

### PartyDeploymentTest.LeGroupeNeSeDeploieQueLaOuIlRejointLaRencontre

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_party_deployment.cpp:193`

Le groupe ne se déploie que là où il rejoint la rencontre.

**Étapes**

1. Une zone de 6 x 2 coupée par un mur plein en colonne 5 ; la rencontre à droite du mur, sur deux colonnes.
2. Juger.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdict.reachableCells` vaut `4`.
- Vérifie que `verdict.partyPlaces.size()` vaut `2U`.
- Vérifie que `releve(verdict, DeploymentIssueCode::PartyCannotDeploy)` est vrai.
- Vérifie que `place.column` est strictement supérieur à `5`.

### PartyDeploymentTest.UneRencontreSansZoneEstRefusee

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_party_deployment.cpp:222`

Une rencontre sans zone est refusée.

**Étapes**

1. Une carte sans zone, une rencontre connue et une inconnue.
2. Juger.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdicts.front().zoneIndex.has_value()` est faux.
- Vérifie que `verdicts.front().issues.size()` vaut `1U`.
- Vérifie que `verdicts.front().issues.front().code` vaut `DeploymentIssueCode::NoCombatZone`.
- Vérifie que `verdicts.front().partyPlaces.empty()` est vrai.

## test_serie_de_l_arene.cpp

### SerieDeLArene.LaSerieMonteEnDifficulte

*Critique · Integration · Serie de l'arene · Equilibrage* — `Source/Test/Unit/Core/Combat/test_serie_de_l_arene.cpp:133`

Les six rencontres de la serie sont difficiles, les deux dernieres mortelles, et leur budget croit jusqu'au niveau 5.

**Étapes**

1. Charger les rencontres, le bestiaire et les regles de difficulte livres.
2. Juger chaque rencontre de la serie pour quatre heros de son niveau.

**Résultat attendu**

- Vérifie que `rencontre` diffère de `nullptr`.
- Vérifie que `budget.unknownCreatures.empty()` est vrai.
- Vérifie que `budget.category == "difficile" || budget.category == "mortelle"` est vrai.
- Vérifie que `budget.adjustedExperience` est strictement supérieur à `precedent`.
- Vérifie que `budget.category` vaut `"mortelle"`.

### SerieDeLArene.ChaqueRencontreSeGagneDansSaBande

*Critique · Integration · Serie de l'arene · Equilibrage* — `Source/Test/Unit/Core/Combat/test_serie_de_l_arene.cpp:172`

Chaque rencontre de la serie se gagne dans sa bande de victoires.

**Étapes**

1. Le sable ; le groupe de « Nouvelle partie » monte au niveau de chaque rencontre.
2. Trente combats par rencontre en Release (un en Debug), les deux camps par l'IA.

**Résultat attendu**

- Vérifie que `carte.ok()` est vrai.
- Vérifie que `gagnes` est supérieur ou égal à `bas`.
- Vérifie que `gagnes` est inférieur ou égal à `haut`.

### SerieDeLArene.MesureCompleteParComposition

*Critique · Integration · Serie de l'arene · Equilibrage* — `Source/Test/Unit/Core/Combat/test_serie_de_l_arene.cpp:220`

Sur la serie, l'ecart de victoires entre les quatre trios reste sous vingt points.

**Étapes**

1. Poser `JADG_SIMULATION_SEEDS` (cent) et `JADG_SIMULATION_OUT`.
2. Jouer chaque rencontre par le groupe et par chaque trio.

**Résultat attendu**

- Vérifie que `carte.ok()` est vrai.
- Vérifie que `meilleur - pire` est strictement inférieur à `20.0`.

## test_simulated_space.cpp

### EspaceSimuleTest.UnCheminDroitSurUnPlanVideCouteSaLongueur

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:37`

Un chemin droit sur un plan vide coute sa longueur.

**Étapes**

1. Un plan vide, 6 m a parcourir dans un budget de 9 m.

**Résultat attendu**

- Vérifie que `route.has_value()` est vrai.
- Vérifie que `route->length` vaut `6.0f`, à `0.01f` près.
- Vérifie que `route->points.empty()` est faux.
- Vérifie que `route->points.back().x` vaut `9.0f`, à `0.01f` près.
- Vérifie que `route->points.back().y` vaut `3.0f`, à `0.01f` près.

### EspaceSimuleTest.LeBudgetArreteLeChemin

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:55`

Le budget arrete le chemin.

**Étapes**

1. 9,5 m puis 9 m a parcourir avec 9 m de budget ; sans budget, le coin oppose du plan.

**Résultat attendu**

- Vérifie que `space.route({.mover = medium(3, 3), .destination = {12.5f, 3, 0}, .budget = 9.0f}) .has_value()` est faux.
- Vérifie que `space.route({.mover = medium(3, 3), .destination = {12.0f, 3, 0}, .budget = 9.0f}) .has_value()` est vrai.
- Vérifie que `space.route({.mover = medium(3, 3), .destination = {27, 27, 0}}).has_value()` est vrai.

### EspaceSimuleTest.UnMurSeContourneEtNeSeTraversePas

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:74`

Un mur se contourne et ne se traverse pas.

**Étapes**

1. Un mur de 20 m entre le depart et l'arrivee ; un budget de 11 m puis aucun.

**Résultat attendu**

- Vérifie que `space.route(direct).has_value()` est faux.
- Vérifie que `route.has_value()` est vrai.
- Vérifie que `route->length` est strictement supérieur à `30.0f`.
- Vérifie que `point.x > 9.2f && point.x < 11.8f && point.y < 20.0f` est faux.

### EspaceSimuleTest.OnNeFinitPasDansUnMurNiHorsDuPlan

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:100`

On ne finit pas dans un mur ni hors du plan.

**Étapes**

1. Une destination dans une boite ; un volume au bord du plan.

**Résultat attendu**

- Vérifie que `space.route({.mover = medium(1, 1), .destination = {5, 5, 0}}).has_value()` est faux.
- Vérifie que `space.isClear(medium(0.2f, 5), core::Locomotion::Walk)` est faux.
- Vérifie que `space.isClear(medium(1, 5), core::Locomotion::Walk)` est vrai.

### EspaceSimuleTest.LeTerrainDifficileCouteDouble

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:115`

Le terrain difficile coute double au sol et rien en vol.

**Étapes**

1. Une bande de 3 m de terrain difficile sur 6 m de route.

**Résultat attendu**

- Vérifie que `walking.has_value()` est vrai.
- Vérifie que `walking->length` vaut `9.0f`, à `0.6f` près.
- Vérifie que `flying.has_value()` est vrai.
- Vérifie que `flying->length` vaut `6.0f`, à `0.01f` près.

### EspaceSimuleTest.LEauProfondeArreteLaMarcheEtPasLeVol

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:139`

L'eau profonde arrete la marche et pas le vol.

**Étapes**

1. Une bande d'eau profonde en travers.

**Résultat attendu**

- Vérifie que `space.route({.mover = medium(5, 5), .destination = {5, 20, 0}}).has_value()` est faux.
- Vérifie que `space .route({.mover = medium(5, 5), .destination = {5, 20, 0}, .locomotion = core::Locomotion::Fly}) .has_value()` est vrai.

### EspaceSimuleTest.UnEnnemiBloqueEtUnAllieSeTraverseEnCoutantDouble

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:157`

Un ennemi bloque, un allie se traverse en coutant double.

**Étapes**

1. Un couloir etroit tenu par un ennemi, puis par un allie ; une destination dans l'espace de l'allie.

**Résultat attendu**

- Vérifie que `space.route({.mover = medium(3, 10), .destination = {17, 10, 0}, .blocking = enemy}) .has_value()` est faux.
- Vérifie que `through.has_value()` est vrai.
- Vérifie que `through->length` est strictement supérieur à `16.0f`.
- Vérifie que `space.route({.mover = medium(3, 10), .destination = {10, 10, 0}, .passable = ally}) .has_value()` est faux.

### EspaceSimuleTest.LesCandidatsSontDansLeBudgetEtEnOrdreFixe

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:187`

Les candidats sont dans le budget et en ordre fixe.

**Étapes**

1. Deux demandes identiques, budget de 4,5 m, une boite a cote.

**Résultat attendu**

- Vérifie que `first.size()` vaut `second.size()`.
- Vérifie que `first[i].point` vaut `second[i].point`.
- Vérifie que `first[i].route.points` vaut `second[i].route.points`.
- Vérifie que `first.empty()` est faux.
- Vérifie que `first.front().point` vaut `query.mover.base`.
- Vérifie que `first.front().route.points.empty()` est vrai.
- Vérifie que `core::groundDistance(candidate.point, query.mover.base)` est inférieur ou égal à `4.5f + 0.01f`.
- Vérifie que `candidate.route.length` est inférieur ou égal à `4.5f + 0.01f`.
- Vérifie que `candidate.route.points.empty()` est faux.
- Vérifie que `candidate.route.points.back()` vaut `candidate.point`.
- Vérifie que `space.isClear(core::volumeOf(candidate.point, CreatureSize::Medium), core::Locomotion::Walk)` est vrai.
- Vérifie que `far` est faux.
- Vérifie que `near` est vrai.

### EspaceSimuleTest.UnMurArreteLaVueEtUneToileNon

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:229`

Un mur arrete la vue et une toile non.

**Étapes**

1. Un mur de 3 m ; un regard a 0,75 m puis a 3,5 m ; une toile sans abri.

**Résultat attendu**

- Vérifie que `space.lineOfSight({5, 5, 0.75f}, {15, 5, 0.75f})` est faux.
- Vérifie que `space.lineOfSight({5, 5, 3.5f}, {15, 5, 3.5f})` est vrai.
- Vérifie que `web.lineOfSight({5, 5, 0.75f}, {15, 5, 0.75f})` est vrai.

### EspaceSimuleTest.LAbriSeCompteParLignesCoupees

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:247`

L'abri se compte par lignes coupees.

**Étapes**

1. Rien, un mur plein, un muret d'un metre, un mur qui s'arrete a mi-cible.

**Résultat attendu**

- Vérifie que `core::coverFrom(open, medium(2, 5), medium(12, 5))` vaut `Cover::None`.
- Vérifie que `core::coverFrom(wall, medium(2, 5), medium(12, 5))` vaut `Cover::Total`.
- Vérifie que `core::hasLineOfSight(wall, medium(2, 5), medium(12, 5))` est faux.
- Vérifie que `behindLow == Cover::Half || behindLow == Cover::ThreeQuarters` est vrai.
- Vérifie que `behindLow` diffère de `Cover::Total`.
- Vérifie que `partial` diffère de `Cover::None`.
- Vérifie que `partial` diffère de `Cover::Total`.

### EspaceSimuleTest.UnCorpsInterposeAbriteAMoitie

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:279`

Un corps interpose abrite a moitie.

**Étapes**

1. Une creature sur la ligne, puis a cote.

**Résultat attendu**

- Vérifie que `core::coverFrom(open, medium(2, 5), medium(12, 5), between)` vaut `Cover::Half`.
- Vérifie que `core::coverFrom(open, medium(2, 5), medium(12, 5), aside)` vaut `Cover::None`.

### EspaceSimuleTest.LAbriEstSymetriqueSansCorps

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:295`

La ligne de vue est symetrique.

**Étapes**

1. Deux volumes et deux boites ; la vue dans les deux sens.

**Résultat attendu**

- Vérifie que `core::hasLineOfSight(space, a, b)` vaut `core::hasLineOfSight(space, b, a)`.

### EspaceSimuleTest.UnPlateauDonneSaHauteurAuSol

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:311`

Un plateau donne sa hauteur au sol.

**Étapes**

1. Un plateau a 1,5 m ; un chemin qui y monte.

**Résultat attendu**

- Vérifie que `space.groundHeight(5, 5)` vaut `0.0f` (comparaison flottante).
- Vérifie que `space.groundHeight(15, 5)` vaut `1.5f` (comparaison flottante).
- Vérifie que `route.has_value()` est vrai.
- Vérifie que `route->points.back().z` vaut `1.5f` (comparaison flottante).
- Vérifie que `core::hasHighGround(up, medium(8, 5))` est vrai.

### EspaceSimuleTest.UneGrilleDeCollisionDevientDesBoites

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:331`

Une grille de collision devient des boites.

**Étapes**

1. Une grille 10 x 10 avec un mur d'une colonne perce en bas.

**Résultat attendu**

- Vérifie que `space.width()` vaut `15.0f` (comparaison flottante).
- Vérifie que `space.boxes().size()` vaut `8u`.
- Vérifie que `space.isClear(medium(8.25f, 2.0f), core::Locomotion::Walk)` est faux.
- Vérifie que `route.has_value()` est vrai.
- Vérifie que `route->length` est strictement supérieur à `20.0f`.

### EspaceSimuleTest.LeMemeCheminDeuxFois

*Majeur · Unitaire · Combat en distance (LOT-1017)* — `Source/Test/Unit/Core/Combat/test_simulated_space.cpp:358`

Le meme chemin deux fois.

**Étapes**

1. Une boite, du terrain difficile, la meme demande deux fois.

**Résultat attendu**

- Vérifie que `first.has_value()` est vrai.
- Vérifie que `second.has_value()` est vrai.
- Vérifie que `first->points` vaut `second->points`.
- Vérifie que `first->length` vaut `second->length` (comparaison flottante).

## test_tactical_terrain.cpp

### TacticalTerrainTest.UneRencontreEnChampOuvertEstValide

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:63`

Une rencontre en champ ouvert est un terrain tactique valide.

**Étapes**

1. Poser une rencontre de deux rats au centre d'une carte vide de 20 x 20.
2. Analyser le terrain.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdict.valid()` est vrai.
- Vérifie que `verdict.entityIndex` vaut `0U`.
- Vérifie que `verdict.encounterId` vaut `"rats"`.
- Vérifie que `verdict.placements.size()` vaut `2U`.
- Vérifie que `verdict.requiredCells` vaut `(2 + core::TACTICAL_PARTY_SIZE) * 4`.
- Vérifie que `contient({.column = 10, .row = 10})` est vrai.
- Vérifie que `contient({.column = 16, .row = 10})` est vrai.
- Vérifie que `contient({.column = 4, .row = 10})` est vrai.
- Vérifie que `contient({.column = 10, .row = 4})` est vrai.
- Vérifie que `contient({.column = 14, .row = 14})` est vrai.
- Vérifie que `contient({.column = 15, .row = 15})` est faux.
- Vérifie que `contient({.column = 17, .row = 10})` est faux.
- Vérifie que `verdict.area.front()` vaut `(core::GridPosition{.column = 10, .row = 4})`.
- Vérifie que `verdict.area.back()` vaut `(core::GridPosition{.column = 10, .row = 16})`.
- Vérifie que `core::groundDistance(core::tileCenter(cell), centre)` est inférieur ou égal à `9.0F + 0.01F`.
- Vérifie que `std::ranges::is_sorted(verdict.area, [](core::GridPosition a, core::GridPosition b) { return a.row != b.row ? a.row < b.row : a.column < b.column; })` est vrai.

### TacticalTerrainTest.UnCombattantDansUnMurEstSignale

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:111`

Un combattant pose dans un mur est signale.

**Étapes**

1. Murer la case devant le declencheur.
2. Analyser le terrain.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdicts.front().issues` vaut `attendus`.

### TacticalTerrainTest.UnCombattantHorsDeLaCarteEstSignale

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:135`

Un combattant hors de la carte est signale.

**Étapes**

1. Poser le declencheur sur la premiere ligne : le premier rat tombe en ligne -1.
2. Analyser le terrain.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdicts.front().issues` vaut `attendus`.

### TacticalTerrainTest.DeuxCombattantsSuperposesSontSignales

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:158`

Deux combattants superposes sont signales.

**Étapes**

1. Ecrire une rencontre dont deux combattants partagent un decalage.
2. Analyser le terrain.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdicts.front().issues` vaut `attendus`.

### TacticalTerrainTest.UnCouloirTropEtroitEstSignale

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:186`

Un couloir trop etroit est signale.

**Étapes**

1. Murer une carte de 30 x 3 sauf sa ligne du milieu.
2. Y poser une rencontre de deux combattants alignes.
3. Analyser le terrain.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdict.area.size()` vaut `13U`.
- Vérifie que `verdict.requiredCells` vaut `24`.
- Vérifie que `verdict.issues` vaut `attendus`.

### TacticalTerrainTest.UnDeclencheurDansUnMurNAAucuneZone

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:221`

Un declencheur dans un mur n'a aucune zone.

**Étapes**

1. Murer la case du declencheur d'un champ ouvert.
2. Analyser le terrain.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdicts.front().area.empty()` est vrai.
- Vérifie que `verdicts.front().issues.empty()` est faux.
- Vérifie que `verdicts.front().issues.back().code` vaut `core::TacticalIssueCode::AreaTooNarrow`.

### TacticalTerrainTest.UneRencontreInconnueEstIgnoree

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:243`

Une rencontre inconnue est ignoree.

**Étapes**

1. Poser une rencontre inconnue, puis une connue.
2. Analyser le terrain.

**Résultat attendu**

- Vérifie que `verdicts.size()` vaut `1U`.
- Vérifie que `verdicts.front().entityIndex` vaut `1U`.
- Vérifie que `verdicts.front().encounterId` vaut `"rats"`.

### TacticalTerrainTest.LesAutresEntitesSontIgnorees

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:265`

Les entites qui ne sont pas des rencontres sont ignorees.

**Étapes**

1. Poser un coffre portant un encounterId, et une rencontre sans encounterId, tous deux dans un mur.
2. Analyser le terrain.

**Résultat attendu**

- Vérifie que `core::analyzeEncounterTerrain(collision, entites, catalogue()).empty()` est vrai.

### TacticalTerrainTest.LEmpriseDUneGrandeCreatureVientDuBestiaire

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:289`

L'emprise d'une grande creature vient du bestiaire.

**Étapes**

1. Poser un ogre (taille G) dont seule la case diagonale de son emprise est muree.
2. Analyser sans bestiaire, puis avec.

**Résultat attendu**

- Vérifie que `sansBestiaire.size()` vaut `1U`.
- Vérifie que `sansBestiaire.front().valid()` est vrai.
- Vérifie que `avecBestiaire.size()` vaut `1U`.
- Vérifie que `avecBestiaire.front().issues` vaut `attendus`.

### TacticalTerrainTest.LAnalyseEstDeterministe

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_tactical_terrain.cpp:327`

L'analyse est deterministe.

**Étapes**

1. Poser trois rencontres, dont une mal posee.
2. Analyser deux fois.

**Résultat attendu**

- Vérifie que `premier.size()` vaut `3U`.
- Vérifie que `second.size()` vaut `3U`.
- Vérifie que `premier[i].entityIndex` vaut `i`.
- Vérifie que `premier[i].area` vaut `second[i].area`.
- Vérifie que `premier[i].issues` vaut `second[i].issues`.
- Vérifie que `premier[0].valid()` est vrai.
- Vérifie que `premier[1].valid()` est faux.
- Vérifie que `premier[2].valid()` est faux.

## test_turn_order.cpp

### TurnOrderTest.LOrdreNeDependPasDeLInsertion

*Bloquant · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_turn_order.cpp:69`

L'ordre d'initiative ne depend pas de l'ordre dans lequel on range les combattants.

**Étapes**

1. Cinq places qui ne se distinguent chacune de la suivante que par un critere : total, modificateur, Dexterite, camp, identifiant.
2. Les ranger dans les 120 ordres possibles.

**Résultat attendu**

- Vérifie que `ordre.add(place)` est vrai.
- Vérifie que `ordreDe(ordre)` vaut `attendu`.
- Vérifie que `permutations` vaut `120`.
- Vérifie que `ordre.add(places[0])` est vrai.
- Vérifie que `ordre.add(places[0])` est faux.
- Vérifie que `ordre.entries().size()` vaut `1U`.

### TurnOrderTest.UnRepereFixePerdLesEgalites

*Majeur · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_turn_order.cpp:107`

Les actions de repaire au rang 20 jouent apres un combattant a 20, les renforts au rang 0 en dernier.

**Étapes**

1. Ranger un combattant a 20, un a 12 et un a 0, un repere « repaire » a 20 et un « renforts » a 0.
2. Parcourir le round de place en place.
3. Ranger deux fois le meme repere.

**Résultat attendu**

- Vérifie que `ordre.addMarker({.count = 0, .name = "renforts"})` est vrai.
- Vérifie que `ordre.addMarker({.count = 20, .name = "repaire"})` est vrai.
- Vérifie que `ordre.add(combattant(1, 0))` est vrai.
- Vérifie que `ordre.add(combattant(2, 12))` est vrai.
- Vérifie que `ordre.add(combattant(3, 20))` est vrai.
- Vérifie que `ordre.addMarker({.count = 20, .name = "repaire"})` est faux.
- Vérifie que `parcours` vaut `(std::vector<std::string>{"C3", "repaire", "C2", "C1", "renforts"})`.

### TurnOrderTest.UnePlaceSeCalculeApresUnDepart

*Critique · Unitaire · Combat* — `Source/Test/Unit/Core/Combat/test_turn_order.cpp:139`

Un combattant qui sort ne fait sauter aucun tour ; un renfort joue ce round-ci s'il est range apres la place en cours.

**Étapes**

1. Ordre 18, 12, 6 ; la place en cours est celle de 12.
2. Retirer le combattant a 12.
3. Ranger un renfort a 9, puis un a 15.

**Résultat attendu**

- Vérifie que `ordre.add(combattant(1, 18))` est vrai.
- Vérifie que `ordre.add(combattant(2, 12))` est vrai.
- Vérifie que `ordre.add(combattant(3, 6))` est vrai.
- Vérifie que `enCours.has_value()` est vrai.
- Vérifie que `enCours->combatant()` vaut `core::CombatantId{2}`.
- Vérifie que `ordre.remove(core::CombatantId{2})` est vrai.
- Vérifie que `ordre.remove(core::CombatantId{2})` est faux.
- Vérifie que `ordre.contains(core::CombatantId{2})` est faux.
- Vérifie que `ordre.add(combattant(4, 9))` est vrai.
- Vérifie que `ordre.add(combattant(5, 15))` est vrai.
- Vérifie que `suivante.has_value()` est vrai.
- Vérifie que `suivante->combatant()` vaut `core::CombatantId{4}`.
- Vérifie que `suivante.has_value()` est vrai.
- Vérifie que `suivante->combatant()` vaut `core::CombatantId{3}`.
- Vérifie que `ordre.slotAfter(*suivante).has_value()` est faux.
- Vérifie que `ordre.firstSlot()->combatant()` vaut `core::CombatantId{1}`.
