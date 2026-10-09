// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_attack.cpp
 * @brief Tests de l'attaque (`LOT-21`, `EX-CBT-030`, `EX-CBT-031`, `EX-REG-003`) : 1 et 20
 * naturels, jet amendable, journal, circonstances de l'espace, profils du bestiaire et de la
 * fiche ; la ligne de vue et l'abri entre combattants posés (`LOT-22`, `EX-CBT-021`, `LOT-1017`).
 *
 * Le d20 est **forcé** par un greffon qui substitue le dé : c'est le point d'insertion même que le
 * lot livre, et il rend « un 20 naturel » écrivable sans chercher une graine qui le donne.
 *
 * Les combattants se posent en mètres, au centre des cases d'une salle (`test_support::tile`) ;
 * l'allonge et la portée se mesurent entre les bords de leurs volumes.
 */

#include <cstddef>
#include <filesystem>
#include <initializer_list>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/Attack.h"
#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/CombatState.h"
#include "Core/Combat/SimulatedSpace.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/Ability.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Equipment.h"
#include "Test/Support/CombatSpaceSupport.h"

namespace {

using core::AttackRollStage;
using core::CombatantId;
using core::CombatHook;
using core::CombatSide;
using core::Cover;
using core::DamageType;
using test_support::tile;

/// Le rectangle au sol de la case (@p colonne, @p ligne).
[[nodiscard]] core::GroundRect caseRect(int colonne, int ligne) {
    const float cote = core::METERS_PER_TILE;
    return {static_cast<float>(colonne) * cote, static_cast<float>(ligne) * cote,
            static_cast<float>(colonne + 1) * cote, static_cast<float>(ligne + 1) * cote};
}

/// Un obstacle posé sur une case : un muret, un parapet, une porte fermée.
[[nodiscard]] core::Box obstacle(int colonne, int ligne, float hauteur, Cover abri) {
    return {
        .rect = caseRect(colonne, ligne), .height = hauteur, .blocksMovement = true, .cover = abri};
}

/// Un muret : la moitié de la hauteur d'une créature de taille M (Manuel, « Abri » : un obstacle
/// qui couvre au moins la moitié du corps).
inline constexpr float MURET = 0.75F;
/// Un parapet à hauteur d'épaule : les trois quarts d'une créature de taille M.
inline constexpr float PARAPET = 1.2F;

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
    explicit Duel(int caCible, int pvCible = 30) : combat(test_support::openSpace(10, 10)) {
        combat.enlist(profil("Heroine", CombatSide::Allies, 20, 16, 100), tile(2, 2));
        combat.enlist(profil("Gobelin", CombatSide::Enemies, pvCible, caCible, -100), tile(3, 2));
        EXPECT_TRUE(combat.start(hasard));
    }
    core::DeterministicRandom hasard{42};
    core::CombatState combat;
};

/// Un combat posé dans @p espace, des combattants de taille M aux places @p places, identifiants
/// 1, 2, … dans l'ordre. Les corps s'interposent ; la vue les ignore.
[[nodiscard]] std::unique_ptr<core::CombatState> monter(
    std::shared_ptr<const core::CombatSpace> espace, std::initializer_list<core::Meters3> places) {
    auto combat = std::make_unique<core::CombatState>(std::move(espace));
    int rang = 0;
    for (const core::Meters3 place : places) {
        const core::EnlistResult enrole = combat->enlist(
            profil("C" + std::to_string(++rang), CombatSide::Allies, 10, 12, 0), place);
        EXPECT_TRUE(enrole.combatant.has_value()) << "place " << rang;
    }
    return combat;
}

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
 * @brief L'espace dit la portee et les circonstances : allonge entre les bords, tir au contact.
 * \castest{<b>L'allonge et la portee se mesurent entre les bords des volumes : une creature de
 * taille G touche ce qui borde son volume ; un tir est desavantage au contact d'un ennemi ou
 * au-dela de sa portee normale.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Un ogre de taille G pose sur les cases (5,5) a (6,6), un archer au centre de la case
 * (7,5), un guerrier en (2,5), un rat en (7,11).<br/>2. Mesurer les ecarts ; l'allonge d'une
 * attaque de 1, 2 et 3 cases.<br/>3. L'archer tire au contact de l'ogre ; puis sur le rat, avec
 * une portee 4/12.<br/>4. Une cible a terre.<br/>
 * \tattendu Ogre-archer 0,12 m (le bord de l'ogre borde l'archer) ; guerrier-ogre 3,05 m, hors
 * d'allonge a 1 et 2 cases, a portee a 3 ; archer-rat 7,50 m, hors d'atteinte sans portee ; tir au
 * contact desavantage ; longue portee desavantagee ; aucune attaque declarable contre une cible a
 * terre.
 * }
 */
TEST(AttackTest, LEspaceDitLaPorteeEtLesCirconstances) {
    core::CombatState combat(test_support::openSpace(12, 12));
    core::CombatantProfile ogre = profil("Ogre", CombatSide::Enemies, 59, 11, -50);
    ogre.size = core::CreatureSize::Large;
    combat.enlist(profil("Archer", CombatSide::Allies, 12, 14, 100), tile(7, 5));
    combat.enlist(ogre, tile(5, 5, core::CreatureSize::Large));
    combat.enlist(profil("Guerrier", CombatSide::Allies, 20, 18, 0), tile(2, 5));
    // Cinq cases entre les centres, quatre entre les bords : le rat est en (7,11), et non plus en
    // (7,10), pour rester au-dela des 4 cases de la portee normale.
    combat.enlist(profil("Rat", CombatSide::Enemies, 1, 10, -100), tile(7, 11));
    core::DeterministicRandom hasard(5);
    ASSERT_TRUE(combat.start(hasard));

    EXPECT_NEAR(*core::gapBetween(combat, CombatantId{1}, CombatantId{2}), 0.12F, 0.01F);
    EXPECT_NEAR(*core::gapBetween(combat, CombatantId{3}, CombatantId{2}), 3.05F, 0.01F);
    EXPECT_NEAR(*core::gapBetween(combat, CombatantId{1}, CombatantId{4}), 7.5F, 0.01F);
    core::AttackProfile massue = epee();
    EXPECT_TRUE(core::inReach(combat, CombatantId{2}, CombatantId{1}, massue));
    EXPECT_FALSE(core::inReach(combat, CombatantId{3}, CombatantId{2}, massue));
    massue.reach = 2;
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
 * \tetapes 1. Un archer au centre de la case (0,1), un gobelin a la CA 15 en (3,1), un muret de
 * 0,75 m — la moitie d'une creature de taille M — sur la case (2,1).<br/>2. Tirer, d20 force a
 * 12.<br/>3. Tirer avec un greffon qui pose l'abri partiel, puis l'abri total.<br/>4. Tirer avec
 * un greffon qui pose l'abri important.<br/>
 * \tattendu CA 17 et « abri partiel : CA 15 -> 17 » au journal ; CA 17 encore, une seule
 * inscription ; CA 20, deux inscriptions.
 * }
 */
TEST(AttackTest, LAbriChangeLaCAUneFois) {
    const std::shared_ptr<core::SimulatedSpace> salle = test_support::openSpace(6, 3);
    salle->addBox(obstacle(2, 1, MURET, Cover::Half));
    core::CombatState combat(salle);
    combat.enlist(profil("Archer", CombatSide::Allies, 12, 14, 100), tile(0, 1));
    combat.enlist(profil("Gobelin", CombatSide::Enemies, 30, 15, -100), tile(3, 1));
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
 * \tetapes 1. Un archer au centre de la case (1,1), un gobelin en (2,2) derriere deux murs en (2,1)
 * et (1,2), un loup en (0,3), un rat en (5,5).<br/>2. Verifier chaque cible, a distance (portee
 * 2/3) et au contact.<br/>3. Les circonstances du tir vers le loup.<br/>
 * \tattendu Gobelin a 0,62 m, au contact : abri total, a distance comme au contact ; loup :
 * valide ; rat : hors de portee ; soi-meme : non pose ; aucun desavantage de tir au contact.
 * }
 */
TEST(AttackTest, ViserDemandeLaPorteeEtLaVue) {
    core::TileMap murs(6, 6);
    murs.setTile(2, 1, core::TileType::Wall);
    murs.setTile(1, 2, core::TileType::Wall);
    core::CombatState combat{test_support::spaceOf(murs)};
    combat.enlist(profil("Archer", CombatSide::Allies, 12, 14, 100), tile(1, 1));
    combat.enlist(profil("Gobelin", CombatSide::Enemies, 7, 15, 0), tile(2, 2));
    combat.enlist(profil("Loup", CombatSide::Enemies, 11, 13, -50), tile(0, 3));
    combat.enlist(profil("Rat", CombatSide::Enemies, 1, 10, -100), tile(5, 5));
    core::DeterministicRandom hasard(4);
    ASSERT_TRUE(combat.start(hasard));

    core::AttackProfile arc = epee();
    arc.kind = core::AttackKind::Ranged;
    arc.range = core::AttackRange{.normal = 2, .maximum = 3};
    // En diagonale, les centres sont a 2,12 m : 0,62 m entre les bords, au contact.
    const std::optional<float> ecart = core::gapBetween(combat, CombatantId{1}, CombatantId{2});
    ASSERT_TRUE(ecart.has_value());
    EXPECT_NEAR(*ecart, 0.62F, 0.01F);
    EXPECT_TRUE(core::adjacentGap(*ecart));
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{2}, arc),
              core::TargetCheck::TotalCover);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{2}, epee()),
              core::TargetCheck::TotalCover);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{3}, arc),
              core::TargetCheck::Valid);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{4}, arc),
              core::TargetCheck::OutOfReach);
    EXPECT_EQ(core::checkTarget(combat, CombatantId{1}, CombatantId{1}, arc),
              core::TargetCheck::NotPlaced);
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

/**
 * @brief La ligne de vue entre combattants est symetrique, sur des cartes generees, pour toutes
 *        les paires.
 * \castest{<b>A voit B si et seulement si B voit A — verifie exhaustivement sur des cartes
 * generees, pour chaque paire de combattants de taille M poses au centre des cases libres, et pour
 * chaque creature de taille G contre chacun d'eux ; l'abri total equivaut a l'absence de
 * vue.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Generer 20 cartes 5 × 5 a des densites de 10 a 55 % de murs, d'eau profonde, de
 * portes fermees, de parapets et de murets.<br/>2. Poser un combattant au centre de chaque case
 * libre ; pour chaque paire ordonnee, comparer les deux sens de la vue
 * (`core::hasLineOfSight`).<br/>3. Pour chaque bloc libre de 2 × 2 cases, y poser une creature de
 * taille G parmi les autres, et comparer de meme.<br/>4. Pour chacune : l'abri total
 * (`core::coverBetween`) equivaut a l'absence de vue.<br/>
 * \tattendu Aucune asymetrie ; aucune divergence entre abri total et vue ; des paires vues et des
 * paires cachees, pour que la verification ne soit pas creuse.
 * }
 */
TEST(AttackTest, LaVueEstSymetriqueSurDesCartesGenerees) {
    core::DeterministicRandom hasard(2222);
    std::size_t vues = 0;
    std::size_t cachees = 0;
    // Verifie la paire dans les deux sens ; faux a la premiere divergence.
    const auto verifier = [&](const core::CombatState& combat, CombatantId a, CombatantId b) {
        const bool ab = core::hasLineOfSight(combat, a, b);
        const bool ba = core::hasLineOfSight(combat, b, a);
        const bool totalAb = core::coverBetween(combat, a, b) == Cover::Total;
        const bool totalBa = core::coverBetween(combat, b, a) == Cover::Total;
        (ab ? vues : cachees) += 1;
        return ab == ba && totalAb == !ab && totalBa == !ba;
    };
    for (int essai = 0; essai < 20; ++essai) {
        const int cote = 5;
        const int pourcent = 10 + (essai % 10) * 5;
        core::TileMap carte(cote, cote);
        std::vector<core::Box> boites;
        std::vector<std::vector<bool>> libre(static_cast<std::size_t>(cote),
                                             std::vector<bool>(static_cast<std::size_t>(cote)));
        for (int ligne = 0; ligne < cote; ++ligne) {
            for (int colonne = 0; colonne < cote; ++colonne) {
                libre[static_cast<std::size_t>(colonne)][static_cast<std::size_t>(ligne)] =
                    hasard.nextInt(0, 99) >= pourcent;
                if (libre[static_cast<std::size_t>(colonne)][static_cast<std::size_t>(ligne)]) {
                    continue;
                }
                switch (hasard.nextInt(0, 5)) {
                    case 0:
                        carte.setTile(colonne, ligne, core::TileType::DeepWater);
                        break;
                    case 1:
                        boites.push_back(obstacle(colonne, ligne, 3.0F, Cover::Total));
                        break;
                    case 2:
                        boites.push_back(obstacle(colonne, ligne, PARAPET, Cover::ThreeQuarters));
                        break;
                    case 3:
                        boites.push_back(obstacle(colonne, ligne, MURET, Cover::Half));
                        break;
                    default:
                        carte.setTile(colonne, ligne, core::TileType::Wall);
                        break;
                }
            }
        }
        const std::shared_ptr<core::SimulatedSpace> espace = test_support::spaceOf(carte);
        for (const core::Box& boite : boites) {
            espace->addBox(boite);
        }
        const auto estLibre = [&](int colonne, int ligne) {
            return libre[static_cast<std::size_t>(colonne)][static_cast<std::size_t>(ligne)];
        };

        // Un combattant de taille M au centre de chaque case libre.
        core::CombatState foule(espace);
        std::vector<CombatantId> poses;
        for (int ligne = 0; ligne < cote; ++ligne) {
            for (int colonne = 0; colonne < cote; ++colonne) {
                if (!estLibre(colonne, ligne)) {
                    continue;
                }
                const core::EnlistResult enrole =
                    foule.enlist(profil("M", CombatSide::Allies, 10, 12, 0), tile(colonne, ligne));
                ASSERT_TRUE(enrole.combatant.has_value()) << colonne << "," << ligne;
                poses.push_back(*enrole.combatant);
            }
        }
        for (const CombatantId a : poses) {
            for (const CombatantId b : poses) {
                if (a != b) {
                    ASSERT_TRUE(verifier(foule, a, b))
                        << "carte " << essai << " : #" << static_cast<int>(a) << " <-> #"
                        << static_cast<int>(b);
                }
            }
        }

        // Une creature de taille G sur chaque bloc libre de 2 × 2, parmi les autres.
        for (int ay = 0; ay + 1 < cote; ++ay) {
            for (int ax = 0; ax + 1 < cote; ++ax) {
                if (!estLibre(ax, ay) || !estLibre(ax + 1, ay) || !estLibre(ax, ay + 1) ||
                    !estLibre(ax + 1, ay + 1)) {
                    continue;
                }
                core::CombatState combat(espace);
                core::CombatantProfile ogre = profil("G", CombatSide::Enemies, 10, 12, 0);
                ogre.size = core::CreatureSize::Large;
                const core::EnlistResult grand =
                    combat.enlist(ogre, tile(ax, ay, core::CreatureSize::Large));
                ASSERT_TRUE(grand.combatant.has_value()) << ax << "," << ay;
                for (int ligne = 0; ligne < cote; ++ligne) {
                    for (int colonne = 0; colonne < cote; ++colonne) {
                        const bool dessous =
                            colonne >= ax && colonne <= ax + 1 && ligne >= ay && ligne <= ay + 1;
                        if (!estLibre(colonne, ligne) || dessous) {
                            continue;
                        }
                        const core::EnlistResult petit = combat.enlist(
                            profil("M", CombatSide::Allies, 10, 12, 0), tile(colonne, ligne));
                        ASSERT_TRUE(petit.combatant.has_value()) << colonne << "," << ligne;
                        ASSERT_TRUE(verifier(combat, *grand.combatant, *petit.combatant))
                            << "carte " << essai << " : G (" << ax << "," << ay << ") <-> M ("
                            << colonne << "," << ligne << ")";
                    }
                }
            }
        }
    }
    EXPECT_GT(vues, 3000U);
    EXPECT_GT(cachees, 500U);
}

/**
 * @brief Ce qui arrete la vue entre deux combattants, et ce qui ne l'arrete pas.
 * \castest{<b>Un mur cache, un gouffre d'eau profonde non ; le coin commun de deux murs ne laisse
 * pas passer le regard ; une porte fermee cache comme un mur, ouverte elle ne cache
 * plus.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Deux combattants alignes, un mur d'une case entre eux ; deux autres sur la rangee
 * voisine.<br/>2. Les memes, separes par une riviere d'eau profonde.<br/>3. Deux combattants en
 * diagonale, deux murs sur les deux autres cases du carre ; puis un seul mur.<br/>4. Une porte
 * fermee dans un couloir, puis ouverte.<br/>
 * \tattendu Mur : pas de vue, abri total, cible refusee ; la rangee voisine se voit ; eau : vue,
 * aucun abri ; deux murs en coin : pas de vue, dans les deux sens ; un seul : vue ; porte fermee :
 * pas de vue ; ouverte : vue.
 * }
 */
TEST(AttackTest, CeQuiArreteLaVue) {
    core::TileMap mur(3, 3);
    mur.setTile(1, 1, core::TileType::Wall);
    const auto derriere =
        monter(test_support::spaceOf(mur), {tile(0, 1), tile(2, 1), tile(0, 0), tile(2, 0)});
    EXPECT_FALSE(core::hasLineOfSight(*derriere, CombatantId{1}, CombatantId{2}));
    EXPECT_EQ(core::coverBetween(*derriere, CombatantId{1}, CombatantId{2}), Cover::Total);
    core::AttackProfile arc = epee();
    arc.kind = core::AttackKind::Ranged;
    arc.range = core::AttackRange{.normal = 16, .maximum = 64};
    EXPECT_EQ(core::checkTarget(*derriere, CombatantId{1}, CombatantId{2}, arc),
              core::TargetCheck::TotalCover);
    EXPECT_TRUE(core::hasLineOfSight(*derriere, CombatantId{3}, CombatantId{4}));

    core::TileMap riviere(5, 3);
    for (int ligne = 0; ligne < 3; ++ligne) {
        riviere.setTile(2, ligne, core::TileType::DeepWater);
    }
    const auto rives = monter(test_support::spaceOf(riviere), {tile(0, 1), tile(4, 1)});
    EXPECT_TRUE(core::hasLineOfSight(*rives, CombatantId{1}, CombatantId{2}));
    EXPECT_EQ(core::coverBetween(*rives, CombatantId{1}, CombatantId{2}), Cover::None);

    core::TileMap coin(2, 2);
    coin.setTile(1, 0, core::TileType::Wall);
    coin.setTile(0, 1, core::TileType::Wall);
    const auto enCoin = monter(test_support::spaceOf(coin), {tile(0, 0), tile(1, 1)});
    EXPECT_FALSE(core::hasLineOfSight(*enCoin, CombatantId{1}, CombatantId{2}));
    EXPECT_FALSE(core::hasLineOfSight(*enCoin, CombatantId{2}, CombatantId{1}));
    core::TileMap demiCoin(2, 2);
    demiCoin.setTile(1, 0, core::TileType::Wall);
    const auto enDemiCoin = monter(test_support::spaceOf(demiCoin), {tile(0, 0), tile(1, 1)});
    EXPECT_TRUE(core::hasLineOfSight(*enDemiCoin, CombatantId{1}, CombatantId{2}));

    core::TileMap couloir(3, 3);
    for (int ligne = 0; ligne < 3; ++ligne) {
        couloir.setTile(0, ligne, core::TileType::Wall);
        couloir.setTile(2, ligne, core::TileType::Wall);
    }
    const std::shared_ptr<core::SimulatedSpace> porte = test_support::spaceOf(couloir);
    const std::size_t battant = porte->boxes().size();
    porte->addBox(obstacle(1, 1, 3.0F, Cover::Total));
    const auto deParEtDAutre = monter(porte, {tile(1, 0), tile(1, 2)});
    EXPECT_FALSE(core::hasLineOfSight(*deParEtDAutre, CombatantId{1}, CombatantId{2}));
    ASSERT_TRUE(porte->removeBox(battant));
    EXPECT_TRUE(core::hasLineOfSight(*deParEtDAutre, CombatantId{1}, CombatantId{2}));
}

/**
 * @brief L'abri partiel, important et total entre combattants, et ce qui les donne.
 * \castest{<b>Un muret et une creature interposee abritent partiellement, un parapet de facon
 * importante ; un angle de mur donne l'abri selon les lignes qu'il coupe, depuis la place du
 * tireur ; les abris ne s'additionnent pas.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un tireur au centre de la case (0,1), une cible en (3,1), rien entre eux.<br/>2. Un
 * muret de 0,75 m, puis un parapet de 1,20 m, sur la case (2,1) devant la cible.<br/>3. Une
 * creature en (1,1), seule, avec le muret, avec le parapet.<br/>4. Un mur de 3 m en (2,1), et des
 * tireurs en (0,1), (0,0) et (1,0).<br/>
 * \tattendu Aucun abri ; partiel ; important ; partiel pour la creature ; muret et creature :
 * partiel, parapet et creature : important — le meilleur des deux, jamais davantage ; derriere le
 * mur : total, important, partiel, selon le nombre de lignes coupees ; bonus +2 et +5.
 * }
 */
TEST(AttackTest, LesAbrisEtCeQuiLesDonne) {
    const auto rien = monter(test_support::openSpace(5, 3), {tile(0, 1), tile(3, 1)});
    EXPECT_EQ(core::coverBetween(*rien, CombatantId{1}, CombatantId{2}), Cover::None);

    // Le muret couvre la moitie du corps de la cible, le parapet les trois quarts.
    const auto derriere = [](float hauteur, Cover abri, bool garde) {
        const std::shared_ptr<core::SimulatedSpace> salle = test_support::openSpace(5, 3);
        salle->addBox(obstacle(2, 1, hauteur, abri));
        return garde ? monter(salle, {tile(0, 1), tile(3, 1), tile(1, 1)})
                     : monter(salle, {tile(0, 1), tile(3, 1)});
    };
    EXPECT_EQ(
        core::coverBetween(*derriere(MURET, Cover::Half, false), CombatantId{1}, CombatantId{2}),
        Cover::Half);
    EXPECT_EQ(core::coverBetween(*derriere(PARAPET, Cover::ThreeQuarters, false), CombatantId{1},
                                 CombatantId{2}),
              Cover::ThreeQuarters);

    // Une creature interposee abrite a moitie ; avec un muret, l'abri reste partiel : les lignes
    // que le muret coupe et celles que le corps coupe ne s'additionnent pas.
    const auto garde = monter(test_support::openSpace(5, 3), {tile(0, 1), tile(3, 1), tile(1, 1)});
    EXPECT_EQ(core::coverBetween(*garde, CombatantId{1}, CombatantId{2}), Cover::Half);
    EXPECT_EQ(
        core::coverBetween(*derriere(MURET, Cover::Half, true), CombatantId{1}, CombatantId{2}),
        Cover::Half);
    EXPECT_EQ(core::coverBetween(*derriere(PARAPET, Cover::ThreeQuarters, true), CombatantId{1},
                                 CombatantId{2}),
              Cover::ThreeQuarters);

    // L'angle d'un mur : depuis l'axe, il cache tout ; en biais, il coupe trois lignes, puis
    // deux. Les tireurs s'abritent les uns les autres sans changer un abri que le mur donne deja.
    core::TileMap angle(5, 3);
    angle.setTile(2, 1, core::TileType::Wall);
    const auto tireurs =
        monter(test_support::spaceOf(angle), {tile(3, 1), tile(0, 1), tile(0, 0), tile(1, 0)});
    EXPECT_EQ(core::coverBetween(*tireurs, CombatantId{2}, CombatantId{1}), Cover::Total);
    EXPECT_EQ(core::coverBetween(*tireurs, CombatantId{3}, CombatantId{1}), Cover::ThreeQuarters);
    EXPECT_EQ(core::coverBetween(*tireurs, CombatantId{4}, CombatantId{1}), Cover::Half);

    EXPECT_EQ(core::coverBonus(Cover::None), 0);
    EXPECT_EQ(core::coverBonus(Cover::Half), 2);
    EXPECT_EQ(core::coverBonus(Cover::ThreeQuarters), 5);
    EXPECT_EQ(core::coverBonus(Cover::Total), 0);
}