// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_attack.cpp
 * @brief Tests de l'attaque (`LOT-21`, `EX-CBT-030`, `EX-CBT-031`, `EX-REG-003`) : 1 et 20
 * naturels, jet amendable, journal, circonstances de la grille, profils du bestiaire et de la
 * fiche.
 *
 * Le d20 est **forcé** par un greffon qui substitue le dé : c'est le point d'insertion même que le
 * lot livre, et il rend « un 20 naturel » écrivable sans chercher une graine qui le donne.
 */

#include <cstddef>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/Attack.h"
#include "Core/Combat/BattleGrid.h"
#include "Core/Combat/CombatState.h"
#include "Core/Levels/TileMap.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/Ability.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Equipment.h"

namespace {

using core::AttackRollStage;
using core::CombatantId;
using core::CombatHook;
using core::CombatSide;
using core::DamageType;

[[nodiscard]] core::CombatantProfile profil(const std::string& nom, CombatSide camp, int pv, int ca,
                                            int initiative) {
    core::CombatantProfile p{.name = nom,
                             .side = camp,
                             .maximumHitPoints = pv,
                             .currentHitPoints = pv,
                             .dexterity = 10,
                             .initiativeModifier = initiative,
                             .movement = 6};
    p.armorClass = ca;
    return p;
}

[[nodiscard]] core::AttackProfile epee() {
    core::AttackProfile p;
    p.label = "Epee longue";
    p.modifiers = {{.source = "Force", .value = 3}, {.source = "maitrise", .value = 2}};
    p.damage = {{.dice = *core::parseDice("1d8+3"), .type = DamageType::Slashing, .flags = 0}};
    return p;
}

/// Un greffon qui force le premier d20 à @p valeur.
[[nodiscard]] core::AttackHooks deForce(int valeur) {
    core::AttackHooks crochets;
    crochets.insert(AttackRollStage::DiceRolled,
                    [valeur](core::AttackRoll& jet, core::DeterministicRandom&) {
                        jet.check.dice[0] = valeur;
                        jet.recompute();
                    });
    return crochets;
}

/// Un duel commencé : l'héroïne (1) joue en premier, le gobelin (2) est au contact.
struct Duel {
    explicit Duel(int caCible, int pvCible = 30) : combat(core::BattleGrid(core::TileMap(10, 10))) {
        combat.enlist(profil("Heroine", CombatSide::Allies, 20, 16, 100), core::GridPosition{2, 2});
        combat.enlist(profil("Gobelin", CombatSide::Enemies, pvCible, caCible, -100),
                      core::GridPosition{3, 2});
        EXPECT_TRUE(combat.start(hasard));
    }
    core::DeterministicRandom hasard{42};
    core::CombatState combat;
};

}  // namespace

/**
 * @brief Un 20 naturel touche quelle que soit la CA, et double les des de degats.
 * \castest{<b>Un 20 naturel touche une CA hors d'atteinte, est un critique, et double les des de
 * degats sans doubler le modificateur.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. L'heroine (+5, 1d8+3) attaque un gobelin a la CA 40.<br/>2. Le d20 est force a
 * 20.<br/>
 * \tattendu Touche et critique ; deux d8 lances, modificateur 3 ; PV perdus = somme des deux d8 +
 * 3 ; le journal dit « critique (20 naturel) » et « des doubles ».
 * }
 */
TEST(AttackTest, UnVingtNaturelToucheEtDoubleLesDes) {
    Duel duel(40);
    const core::AttackHooks crochets = deForce(20);
    const std::optional<core::AttackOutcome> issue = core::resolveAttack(
        duel.combat, CombatantId{1}, CombatantId{2}, epee(), duel.hasard, {.hooks = &crochets});
    ASSERT_TRUE(issue.has_value());
    EXPECT_TRUE(issue->roll.hit);
    EXPECT_TRUE(issue->roll.critical);
    EXPECT_EQ(issue->roll.check.total, 25);
    ASSERT_EQ(issue->damage.size(), 1U);
    const core::DiceRoll& des = issue->damage[0].roll;
    ASSERT_EQ(des.faces.size(), 2U);
    EXPECT_EQ(des.dice.modifier, 3);
    const int perte = des.faces[0] + des.faces[1] + 3;
    EXPECT_EQ(duel.combat.find(CombatantId{2})->profile.currentHitPoints, 30 - perte);
    const std::string ligne = issue->describe();
    EXPECT_NE(ligne.find("critique (20 naturel)"), std::string::npos) << ligne;
    EXPECT_NE(ligne.find("(des doubles)"), std::string::npos) << ligne;
}

/**
 * @brief Un 1 naturel rate, meme avec un total superieur a la CA.
 * \castest{<b>Un 1 naturel rate toujours, meme quand le total depasse la classe d'armure.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. L'heroine attaque avec +30 un gobelin a la CA 5.<br/>2. Le d20 est force a 1.<br/>
 * \tattendu Total 31 contre CA 5, et pourtant rate ; aucun degat ; le journal dit « rate (1
 * naturel) ».
 * }
 */
TEST(AttackTest, UnUnNaturelRateMemeAuDessusDeLaCA) {
    Duel duel(5);
    core::AttackProfile colosse = epee();
    colosse.modifiers = {{.source = "benediction", .value = 30}};
    const core::AttackHooks crochets = deForce(1);
    const std::optional<core::AttackOutcome> issue = core::resolveAttack(
        duel.combat, CombatantId{1}, CombatantId{2}, colosse, duel.hasard, {.hooks = &crochets});
    ASSERT_TRUE(issue.has_value());
    EXPECT_EQ(issue->roll.check.total, 31);
    EXPECT_FALSE(issue->roll.hit);
    EXPECT_TRUE(issue->damage.empty());
    EXPECT_EQ(duel.combat.find(CombatantId{2})->profile.currentHitPoints, 30);
    EXPECT_EQ(issue->describe(),
              "attaque Heroine -> Gobelin (Epee longue) : d20 = 1 + 30 (benediction) = 31 contre "
              "CA 5 : rate (1 naturel)");
}

/**
 * @brief Chaque jet produit une entree de journal complete et lisible (EX-REG-003).
 * \castest{<b>Une attaque touchee et une attaque ratee s'ecrivent au journal avec le de, chaque
 * modificateur et son origine, la CA, l'issue, les des de degats, leur type et les PV.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Le d20 force a 12, contre CA 15 : touche.<br/>2. Le d20 force a 4 : rate.<br/>
 * \tattendu « d20 = 12 + 3 (Force) + 2 (maitrise) = 17 contre CA 15 : touche ; degats 1d8+3 : ... =
 * ... tranchant ; PV 30 -> ... » puis « = 9 contre CA 15 : rate ».
 * }
 */
TEST(AttackTest, ChaqueJetProduitUneEntreeDeJournalComplete) {
    Duel duel(15);
    const core::AttackHooks douze = deForce(12);
    const std::optional<core::AttackOutcome> touche = core::resolveAttack(
        duel.combat, CombatantId{1}, CombatantId{2}, epee(), duel.hasard, {.hooks = &douze});
    ASSERT_TRUE(touche.has_value() && touche->report.has_value());
    const core::DiceRoll& des = touche->damage[0].roll;
    const std::string attendu =
        "attaque Heroine -> Gobelin (Epee longue) : d20 = 12 + 3 (Force) + 2 (maitrise) = 17 "
        "contre CA 15 : touche ; degats " +
        des.describe() + " tranchant ; PV 30 -> " + std::to_string(30 - des.total);
    EXPECT_EQ(touche->describe(), attendu);

    const core::AttackHooks quatre = deForce(4);
    const std::optional<core::AttackOutcome> rate = core::resolveAttack(
        duel.combat, CombatantId{1}, CombatantId{2}, epee(), duel.hasard, {.hooks = &quatre});
    ASSERT_TRUE(rate.has_value());
    EXPECT_EQ(rate->describe(),
              "attaque Heroine -> Gobelin (Epee longue) : d20 = 4 + 3 (Force) + "
              "2 (maitrise) = 9 contre CA 15 : rate");
}

/**
 * @brief Le jet s'amende a ses trois instants, et l'issue n'est figee qu'apres.
 * \castest{<b>Un greffon ajoute une source de desavantage avant le jet, relance un de apres le jet,
 * ajoute un modificateur apres avoir vu le total ; l'issue tient compte des trois.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Avant le jet : un desavantage et un seuil critique a 19.<br/>2. Apres les des :
 * substituer 19 au premier de et 19 au second.<br/>3. Avant l'issue : +5 si le total rate.<br/>4.
 * Un attaquant avantage et desavantage a la fois.<br/>5. L'annonce de l'attaque precede le
 * jet.<br/>
 * \tattendu Deux des, desavantage ; les substitutions sont inscrites ; 19 est critique ; le
 * modificateur ajoute apres lecture fait toucher une CA 26 ; avantage et desavantage s'annulent ;
 * « declaree » avant « jet ».
 * }
 */
TEST(AttackTest, LeJetSAmendeAvantQueLIssueNeSoitFigee) {
    Duel duel(26);
    std::vector<std::string> ordre;
    duel.combat.subscribe(
        CombatHook::AttackDeclared,
        [&ordre](core::CombatState&, const core::CombatEvent&) { ordre.emplace_back("declaree"); });
    core::AttackHooks crochets;
    crochets.insert(AttackRollStage::BeforeRoll,
                    [&ordre](core::AttackRoll& jet, core::DeterministicRandom&) {
                        ordre.emplace_back("jet");
                        jet.disadvantages.emplace_back("aveugle");
                        jet.criticalThreshold = 19;
                    });
    crochets.insert(AttackRollStage::DiceRolled,
                    [](core::AttackRoll& jet, core::DeterministicRandom&) {
                        ASSERT_EQ(jet.check.dice.size(), 2U);
                        jet.substitute(0, 19, "Presage");
                        jet.substitute(1, 19, "Presage");
                    });
    crochets.insert(AttackRollStage::BeforeOutcome,
                    [](core::AttackRoll& jet, core::DeterministicRandom&) {
                        if (!jet.check.succeeded()) {
                            jet.addModifier({.source = "Garde du futur", .value = 5});
                        }
                    });
    core::AttackProfile faible = epee();
    faible.modifiers = {{.source = "Force", .value = 3}};
    const std::optional<core::AttackOutcome> issue = core::resolveAttack(
        duel.combat, CombatantId{1}, CombatantId{2}, faible, duel.hasard, {.hooks = &crochets});
    ASSERT_TRUE(issue.has_value());
    EXPECT_EQ(ordre, (std::vector<std::string>{"declaree", "jet"}));
    EXPECT_EQ(issue->roll.check.stance, core::RollStance::Disadvantage);
    EXPECT_EQ(issue->roll.amendments.size(), 2U);
    EXPECT_EQ(issue->roll.check.total, 27);
    EXPECT_TRUE(issue->roll.hit);
    EXPECT_TRUE(issue->roll.critical);

    core::AttackRoll annule;
    annule.armorClass = 10;
    annule.advantages = {"aide"};
    annule.disadvantages = {"a terre"};
    const core::AttackRoll jet = core::rollAttack(annule, core::AttackHooks{}, duel.hasard);
    EXPECT_EQ(jet.check.stance, core::RollStance::Normal);
    EXPECT_EQ(jet.check.dice.size(), 1U);
    EXPECT_EQ(jet.check.target, 10);
}

/**
 * @brief La grille dit la portee et les circonstances : allonge, emprise, tir au contact.
 * \castest{<b>L'allonge se mesure entre emprises, et un tir est desavantage au contact d'un ennemi
 * ou au-dela de sa portee normale.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Un ogre de taille G ancre en (5,5), un archer en (7,5), un guerrier en (2,2).<br/>2.
 * Mesurer les distances ; l'allonge d'une attaque de 1 et de 2 cases.<br/>3. L'archer tire au
 * contact de l'ogre ; puis a 5 cases avec une portee 4/12.<br/>4. Une cible a terre.<br/>
 * \tattendu Ogre-archer 1 (l'emprise borde l'archer) ; tir au contact desavantage ; longue portee
 * desavantagee ; aucune attaque declarable contre une cible a terre.
 * }
 */
TEST(AttackTest, LaGrilleDitLaPorteeEtLesCirconstances) {
    core::CombatState combat(core::BattleGrid(core::TileMap(12, 12)));
    core::CombatantProfile ogre = profil("Ogre", CombatSide::Enemies, 59, 11, -50);
    ogre.size = core::CreatureSize::Large;
    combat.enlist(profil("Archer", CombatSide::Allies, 12, 14, 100), core::GridPosition{7, 5});
    combat.enlist(ogre, core::GridPosition{5, 5});
    combat.enlist(profil("Guerrier", CombatSide::Allies, 20, 18, 0), core::GridPosition{2, 2});
    combat.enlist(profil("Rat", CombatSide::Enemies, 1, 10, -100), core::GridPosition{7, 10});
    core::DeterministicRandom hasard(5);
    ASSERT_TRUE(combat.start(hasard));

    EXPECT_EQ(core::gridDistance(combat, CombatantId{1}, CombatantId{2}), 1);
    EXPECT_EQ(core::gridDistance(combat, CombatantId{3}, CombatantId{2}), 3);
    core::AttackProfile massue = epee();
    EXPECT_TRUE(core::inReach(combat, CombatantId{2}, CombatantId{1}, massue));
    EXPECT_FALSE(core::inReach(combat, CombatantId{3}, CombatantId{2}, massue));
    massue.reach = 3;
    EXPECT_TRUE(core::inReach(combat, CombatantId{3}, CombatantId{2}, massue));

    core::AttackProfile arc = epee();
    arc.kind = core::AttackKind::Ranged;
    EXPECT_EQ(core::attackCircumstances(combat, CombatantId{1}, CombatantId{2}, arc).disadvantages,
              (std::vector<std::string>{"tir au contact d'un ennemi"}));
    EXPECT_FALSE(core::inReach(combat, CombatantId{1}, CombatantId{4}, arc));
    arc.range = core::AttackRange{.normal = 4, .maximum = 12};
    EXPECT_TRUE(core::inReach(combat, CombatantId{1}, CombatantId{4}, arc));
    EXPECT_EQ(core::attackCircumstances(combat, CombatantId{1}, CombatantId{4}, arc).disadvantages,
              (std::vector<std::string>{"tir au contact d'un ennemi", "longue portee"}));

    combat.applyDamage(CombatantId{4}, 5);
    EXPECT_FALSE(
        core::resolveAttack(combat, CombatantId{1}, CombatantId{4}, arc, hasard).has_value());
}

/**
 * @brief Les profils se tirent du bestiaire et de l'arme de la fiche, selon le Manuel.
 * \castest{<b>Les attaques d'une creature se lisent de son bloc ; celles d'un personnage de son
 * arme, de sa Force ou de sa Dexterite et de sa maitrise ; le coup a mains nues vaut 1 + Force ;
 * aucune creature livree n'a de degats sans type.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Une creature a quatre actions : allonge 3 m, sans allonge, sans type, sans
 * degats.<br/>2. Une fiche de Force 16 et Dexterite 18, maitrise +2 : epee longue, rapiere de
 * finesse, filet, mains nues, arme non maitrisee.<br/>3. Charger le bestiaire livre.<br/>
 * \tattendu Allonge de 2 cases, une attaque a distance, un refus nomme, une action ignoree ; Force
 * +3 et 1d8+3 ; Dexterite +4 et 1d8+4 ; filet sans degats ; mains nues 1 + 3 contondant ; pas de
 * maitrise ; zero refus sur les creatures livrees.
 * }
 */
TEST(AttackTest, LesProfilsSeTirentDuBestiaireEtDeLaFiche) {
    core::Creature monstre;
    monstre.actions.push_back({.name = "Morsure",
                               .text = "...",
                               .attackBonus = 6,
                               .reach = 3.0F,
                               .damage = core::parseDice("1d4+4"),
                               .damageType = DamageType::Piercing});
    monstre.actions.push_back({.name = "Crachat",
                               .text = "...",
                               .attackBonus = 4,
                               .reach = std::nullopt,
                               .damage = core::parseDice("2d6"),
                               .damageType = DamageType::Acid});
    monstre.actions.push_back({.name = "Etrange",
                               .text = "...",
                               .attackBonus = 4,
                               .reach = 1.5F,
                               .damage = core::parseDice("1d6"),
                               .damageType = std::nullopt});
    monstre.actions.push_back({.name = "Toile", .text = "...", .attackBonus = 5});
    const core::CreatureAttacks attaques = core::attacksFor(monstre);
    ASSERT_EQ(attaques.attacks.size(), 2U);
    EXPECT_EQ(attaques.attacks[0].reach, 2);
    EXPECT_EQ(attaques.attacks[0].kind, core::AttackKind::Melee);
    EXPECT_EQ(attaques.attacks[0].modifiers[0].value, 6);
    EXPECT_EQ(attaques.attacks[1].kind, core::AttackKind::Ranged);
    EXPECT_EQ(attaques.refused, (std::vector<std::string>{"Etrange : degats sans type"}));

    core::CharacterSheet fiche;
    fiche.abilities[static_cast<std::size_t>(core::Ability::Strength)] = 16;
    fiche.abilities[static_cast<std::size_t>(core::Ability::Dexterity)] = 18;
    core::Weapon longue{.name = "Epee longue",
                        .category = "martial",
                        .ranged = false,
                        .damage = core::parseDice("1d8"),
                        .damageType = DamageType::Slashing};
    const core::AttackProfile epeeLongue = core::weaponAttackFor(fiche, &longue, 2);
    EXPECT_EQ(epeeLongue.modifiers[0].source, "Force");
    EXPECT_EQ(epeeLongue.modifiers[0].value, 3);
    EXPECT_EQ(epeeLongue.modifiers[1].value, 2);
    EXPECT_EQ(epeeLongue.damage[0].dice, *core::parseDice("1d8+3"));

    core::Weapon rapiere = longue;
    rapiere.properties = {"finesse"};
    const core::AttackProfile finesse = core::weaponAttackFor(fiche, &rapiere, 2);
    EXPECT_EQ(finesse.modifiers[0].source, "Dexterite");
    EXPECT_EQ(finesse.damage[0].dice, *core::parseDice("1d8+4"));

    core::Weapon filet{.name = "Filet", .category = "martial", .ranged = true};
    EXPECT_TRUE(core::weaponAttackFor(fiche, &filet, 2).damage.empty());

    const core::AttackProfile mains = core::weaponAttackFor(fiche, nullptr, 2);
    EXPECT_EQ(mains.damage[0].type, DamageType::Bludgeoning);
    EXPECT_EQ(mains.damage[0].dice.minimum(), 4);
    EXPECT_EQ(mains.damage[0].dice.maximum(), 4);
    EXPECT_EQ(core::weaponAttackFor(fiche, &longue, 2, false).modifiers.size(), 1U);

    const core::Bestiary bestiaire =
        core::loadBestiary(std::filesystem::path(JADG_RPG_CREATURES_DIR));
    ASSERT_FALSE(bestiaire.creatures.empty());
    std::size_t total = 0;
    for (const core::Creature& creature : bestiaire.creatures) {
        const core::CreatureAttacks lues = core::attacksFor(creature);
        EXPECT_TRUE(lues.refused.empty()) << creature.id;
        total += lues.attacks.size();
    }
    EXPECT_GT(total, bestiaire.creatures.size() / 2);
}

/**
 * @brief L'abri change la CA de son montant, une fois, et le meilleur seul compte (LOT-22).
 * \castest{<b>Une cible derriere un muret gagne +2 a sa CA ; un greffon qui pose le meme abri ne
 * l'ajoute pas une seconde fois ; un abri important par-dessus porte le bonus a +5, pas a +7 ; un
 * abri total n'est pas un bonus.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Un archer en (0,1), un gobelin a la CA 15 en (3,1), un muret en (2,1).<br/>2. Tirer,
 * d20 force a 12.<br/>3. Tirer avec un greffon qui pose l'abri partiel, puis l'abri total.<br/>4.
 * Tirer avec un greffon qui pose l'abri important.<br/>
 * \tattendu CA 17 et « abri partiel : CA 15 -> 17 » au journal ; CA 17 encore, une seule
 * inscription ; CA 20, deux inscriptions.
 * }
 */
TEST(AttackTest, LAbriChangeLaCAUneFois) {
    core::CombatState combat(core::BattleGrid(core::TileMap(6, 3)));
    ASSERT_EQ(combat.grid().placeObject({2, 1}, {.kind = "muret",
                                                 .hitPoints = 10,
                                                 .blocksMovement = true,
                                                 .cover = core::Cover::Half,
                                                 .damageTraits = {}}),
              core::PlacementResult::Placed);
    combat.enlist(profil("Archer", CombatSide::Allies, 12, 14, 100), core::GridPosition{0, 1});
    combat.enlist(profil("Gobelin", CombatSide::Enemies, 30, 15, -100), core::GridPosition{3, 1});
    core::DeterministicRandom hasard(8);
    ASSERT_TRUE(combat.start(hasard));

    core::AttackProfile arc = epee();
    arc.kind = core::AttackKind::Ranged;
    arc.range = core::AttackRange{.normal = 16, .maximum = 64};
    ASSERT_EQ(core::coverBetween(combat, CombatantId{1}, CombatantId{2}), core::Cover::Half);

    const core::AttackHooks douze = deForce(12);
    const std::optional<core::AttackOutcome> simple =
        core::resolveAttack(combat, CombatantId{1}, CombatantId{2}, arc, hasard, {.hooks = &douze});
    ASSERT_TRUE(simple.has_value());
    EXPECT_EQ(simple->roll.armorClass, 17);
    EXPECT_EQ(simple->roll.cover, core::Cover::Half);
    EXPECT_NE(simple->describe().find("[abri partiel : CA 15 -> 17] = 12"), std::string::npos)
        << simple->describe();
    EXPECT_NE(simple->describe().find("= 17 contre CA 17 : touche"), std::string::npos);

    core::AttackHooks deuxFois = deForce(12);
    deuxFois.insert(AttackRollStage::BeforeRoll,
                    [](core::AttackRoll& jet, core::DeterministicRandom&) {
                        jet.applyCover(core::Cover::Half);
                        jet.applyCover(core::Cover::Total);
                    });
    const std::optional<core::AttackOutcome> repose = core::resolveAttack(
        combat, CombatantId{1}, CombatantId{2}, arc, hasard, {.hooks = &deuxFois});
    ASSERT_TRUE(repose.has_value());
    EXPECT_EQ(repose->roll.armorClass, 17);
    EXPECT_EQ(repose->roll.amendments.size(), 1U);

    core::AttackHooks herse = deForce(12);
    herse.insert(AttackRollStage::BeforeRoll,
                 [](core::AttackRoll& jet, core::DeterministicRandom&) {
                     jet.applyCover(core::Cover::ThreeQuarters);
                 });
    const std::optional<core::AttackOutcome> important =
        core::resolveAttack(combat, CombatantId{1}, CombatantId{2}, arc, hasard, {.hooks = &herse});
    ASSERT_TRUE(important.has_value());
    EXPECT_EQ(important->roll.armorClass, 20);
    EXPECT_EQ(important->roll.cover, core::Cover::ThreeQuarters);
    EXPECT_EQ(important->roll.amendments.size(), 2U);
    EXPECT_FALSE(important->roll.hit);
}

/**
 * @brief Viser demande la portee et la vue ; un ennemi qu'on ne voit pas ne gene pas le tir.
 * \castest{<b>Une cible derriere un mur ne se vise pas, ni a distance ni au contact par le coin de
 * deux murs ; au-dela de la longue portee non plus ; un ennemi adjacent qui ne voit pas le tireur
 * ne lui impose pas le desavantage du tir au contact.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un archer en (1,1), un gobelin en (2,2) derriere deux murs en (2,1) et (1,2), un loup
 * en (0,3), un rat en (5,5).<br/>2. Verifier chaque cible, a distance (portee 2/3) et au
 * contact.<br/>3. Les circonstances du tir vers le loup.<br/>
 * \tattendu Gobelin : abri total, a distance comme au contact ; loup : valide ; rat : hors de
 * portee ; soi-meme : hors grille ; aucun desavantage de tir au contact.
 * }
 */
TEST(AttackTest, ViserDemandeLaPorteeEtLaVue) {
    core::TileMap murs(6, 6);
    murs.setTile(2, 1, core::TileType::Wall);
    murs.setTile(1, 2, core::TileType::Wall);
    core::CombatState combat{core::BattleGrid(murs)};
    combat.enlist(profil("Archer", CombatSide::Allies, 12, 14, 100), core::GridPosition{1, 1});
    combat.enlist(profil("Gobelin", CombatSide::Enemies, 7, 15, 0), core::GridPosition{2, 2});
    combat.enlist(profil("Loup", CombatSide::Enemies, 11, 13, -50), core::GridPosition{0, 3});
    combat.enlist(profil("Rat", CombatSide::Enemies, 1, 10, -100), core::GridPosition{5, 5});
    core::DeterministicRandom hasard(4);
    ASSERT_TRUE(combat.start(hasard));

    core::AttackProfile arc = epee();
    arc.kind = core::AttackKind::Ranged;
    arc.range = core::AttackRange{.normal = 2, .maximum = 3};
    EXPECT_EQ(core::gridDistance(combat, CombatantId{1}, CombatantId{2}), 1);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{2}, arc),
              core::TargetCheck::TotalCover);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{2}, epee()),
              core::TargetCheck::TotalCover);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{3}, arc),
              core::TargetCheck::Valid);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{4}, arc),
              core::TargetCheck::OutOfReach);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{1}, arc),
              core::TargetCheck::NotOnGrid);
    EXPECT_TRUE(core::attackCircumstances(combat, CombatantId{1}, CombatantId{3}, arc)
                    .disadvantages.empty());
}

/**
 * @brief Les portees et l'allonge se lisent dans la donnee structuree, jamais dans la prose.
 * \castest{<b>Chaque arme qui se tire ou se lance porte ses portees ; l'arc long tire a 30/120
 * cases, la hallebarde frappe a 2, la dague se lance a 4/12 ; le squelette tire a 16/64.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger le catalogue d'armes et le bestiaire livres.<br/>2. Pour chaque arme :
 * portees presentes si et seulement si elle a les munitions ou le lancer.<br/>3. Tirer les profils
 * de l'arc long, de la hallebarde, de la dague (lancee), de l'epee longue (qui ne se lance pas) et
 * du squelette.<br/>
 * \tattendu Aucune arme sans portee qui se tire, aucune portee sans raison ; 30/120 ; allonge 2 ;
 * « Dague (lancer) » a distance, 4/12, Dexterite ; pas d'epee lancee ; l'arc court du squelette a
 * 16/64.
 * }
 */
TEST(AttackTest, LesPorteesSeLisentDansLaDonnee) {
    const std::filesystem::path rpg{JADG_RPG_CREATURES_DIR};
    const core::EquipmentCatalog catalogue =
        core::loadEquipment(rpg.parent_path() / "weapons", rpg.parent_path() / "armors");
    ASSERT_TRUE(catalogue.errors.empty());
    ASSERT_EQ(catalogue.weapons.size(), 37U);
    for (const core::Weapon& arme : catalogue.weapons) {
        const bool tiree =
            core::hasProperty(arme, "ammunition") || core::hasProperty(arme, "thrown");
        EXPECT_EQ(arme.rangeNormal.has_value(), tiree) << arme.id;
        EXPECT_EQ(arme.rangeLong.has_value(), tiree) << arme.id;
        if (arme.ranged) {
            EXPECT_TRUE(tiree) << arme.id;
        }
    }

    core::CharacterSheet fiche;
    fiche.abilities[static_cast<std::size_t>(core::Ability::Strength)] = 12;
    fiche.abilities[static_cast<std::size_t>(core::Ability::Dexterity)] = 16;
    const core::AttackProfile arcLong =
        core::weaponAttackFor(fiche, catalogue.findWeapon("arc-long"), 2);
    ASSERT_TRUE(arcLong.range.has_value());
    EXPECT_EQ(arcLong.range->normal, 30);
    EXPECT_EQ(arcLong.range->maximum, 120);
    EXPECT_EQ(core::weaponAttackFor(fiche, catalogue.findWeapon("hallebarde"), 2).reach, 2);
    EXPECT_EQ(core::weaponAttackFor(fiche, catalogue.findWeapon("epee-longue"), 2).reach, 1);

    const std::optional<core::AttackProfile> dague =
        core::thrownAttackFor(fiche, *catalogue.findWeapon("dague"), 2);
    ASSERT_TRUE(dague.has_value() && dague->range.has_value());
    EXPECT_EQ(dague->label, "Dague (lancer)");
    EXPECT_EQ(dague->kind, core::AttackKind::Ranged);
    EXPECT_EQ(dague->range->normal, 4);
    EXPECT_EQ(dague->range->maximum, 12);
    EXPECT_EQ(dague->modifiers[0].source, "Dexterite");
    EXPECT_FALSE(core::thrownAttackFor(fiche, *catalogue.findWeapon("epee-longue"), 2).has_value());

    const core::Bestiary bestiaire = core::loadBestiary(rpg);
    const core::Creature* squelette = bestiaire.find("skeleton");
    ASSERT_NE(squelette, nullptr);
    const core::CreatureAttacks attaques = core::attacksFor(*squelette);
    ASSERT_EQ(attaques.attacks.size(), 2U);
    EXPECT_EQ(attaques.attacks[1].kind, core::AttackKind::Ranged);
    ASSERT_TRUE(attaques.attacks[1].range.has_value());
    EXPECT_EQ(attaques.attacks[1].range->normal, 16);
    EXPECT_EQ(attaques.attacks[1].range->maximum, 64);
}