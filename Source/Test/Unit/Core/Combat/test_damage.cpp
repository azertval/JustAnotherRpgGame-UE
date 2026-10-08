// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_damage.cpp
 * @brief Tests du pipeline de dégâts (`LOT-21`, `EX-CBT-031`, `EX-CBT-032`) : critique, ordre des
 *        résistances, réserves, bornes des points de vie, salve, structures.
 *
 * Les valeurs attendues sont celles du Manuel des Joueurs, chapitre 9 : ses propres exemples
 * (25 dégâts, aura de 5, résistance : 10 ; le clerc à 6 PV sur 12 qui en subit 18) y sont rejoués.
 */

#include <algorithm>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Combat/BattleGrid.h"
#include "Core/Combat/CombatState.h"
#include "Core/Combat/Damage.h"
#include "Core/Levels/TileMap.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/Dice.h"

namespace {

using core::CombatantId;
using core::CombatHook;
using core::CombatSide;
using core::DamageAffinityKind;
using core::DamageFlag;
using core::DamageStage;
using core::DamageType;

[[nodiscard]] core::CombatantProfile profil(const std::string& nom, CombatSide camp, int pv,
                                            int initiative = 0) {
    core::CombatantProfile p{.name = nom,
                             .side = camp,
                             .maximumHitPoints = pv,
                             .currentHitPoints = pv,
                             .dexterity = 10,
                             .initiativeModifier = initiative,
                             .movement = 6};
    return p;
}

/// Des dégâts déjà lancés, d'un montant fixé : le pipeline se teste sans dés.
[[nodiscard]] core::RolledDamage fixe(int montant, DamageType type,
                                      core::DamageFlags drapeaux = 0) {
    return {.clause = {.dice = core::Dice{.count = 0, .faces = 0, .modifier = montant},
                       .type = type,
                       .flags = drapeaux},
            .roll = {},
            .critical = false,
            .amount = montant};
}

core::DamageReport frapper(core::CombatState& combat, const core::DamagePipeline& pipeline,
                           CombatantId cible, std::vector<core::RolledDamage> degats) {
    const std::vector<core::DamageRequest> salve{{.target = cible, .damage = std::move(degats)}};
    return pipeline.apply(combat, salve).front();
}

}  // namespace

/**
 * @brief Un coup critique double les des de degats, jamais le modificateur (EX-CBT-031).
 * \castest{<b>Un coup critique lance deux fois les des de degats et ajoute le modificateur une
 * seule fois.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Lancer 1d6+3 en critique, a deux cents graines.<br/>2. Lancer 1d4-5 sans
 * critique.<br/>
 * \tattendu Deux des lances, modificateur 3, total = somme des des + 3, toujours entre 5 et 15 (un
 * total double irait de 8 a 18) ; le 1d4-5 inflige 0, jamais un nombre negatif.
 * }
 */
TEST(DamageTest, LeCritiqueDoubleLesDesPasLeModificateur) {
    const std::vector<core::DamageClause> dague{
        {.dice = *core::parseDice("1d6+3"), .type = DamageType::Piercing, .flags = 0}};
    int minimum = 100;
    int maximum = 0;
    for (std::uint64_t graine = 1; graine <= 200; ++graine) {
        core::DeterministicRandom hasard(graine);
        const std::vector<core::RolledDamage> lance = core::rollDamage(dague, true, hasard);
        ASSERT_EQ(lance.size(), 1U);
        ASSERT_EQ(lance[0].roll.faces.size(), 2U);
        EXPECT_EQ(lance[0].roll.dice.count, 2);
        EXPECT_EQ(lance[0].roll.dice.modifier, 3);
        EXPECT_EQ(lance[0].amount, lance[0].roll.faces[0] + lance[0].roll.faces[1] + 3);
        EXPECT_TRUE(lance[0].critical);
        minimum = std::min(minimum, lance[0].amount);
        maximum = std::max(maximum, lance[0].amount);
    }
    EXPECT_EQ(minimum, 5);
    EXPECT_EQ(maximum, 15);

    const std::vector<core::DamageClause> faible{
        {.dice = *core::parseDice("1d4-5"), .type = DamageType::Bludgeoning, .flags = 0}};
    core::DeterministicRandom hasard(3);
    EXPECT_EQ(core::rollDamage(faible, false, hasard)[0].amount, 0);
}

/**
 * @brief Resistance puis vulnerabilite, apres tous les autres modificateurs (Manuel, chapitre 9).
 * \castest{<b>Immunite, resistance et vulnerabilite s'appliquent dans l'ordre du Manuel, apres les
 * autres modificateurs, et une seule fois chacune.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. 25 degats contondants sur une cible resistante, sous une aura qui retire 5.<br/>2. 25
 * sur une cible resistante et vulnerable.<br/>3. 25 sur une cible deux fois resistante ; sur une
 * cible immunisee et vulnerable ; une resistance contournee par une source magique ; une source qui
 * ignore les resistances.<br/>
 * \tattendu 10 (l'exemple du Manuel) ; 24 (12 puis 24, jamais 25) ; 12 ; 0 ; 25 ; 25. La trace
 * nomme chaque etape.
 * }
 */
TEST(DamageTest, LesResistancesSAppliquentDansLOrdreDuManuel) {
    const auto encaisser = [](core::DamageTraits traits, core::DamageFlags drapeaux,
                              bool aura) -> core::DamageReport {
        core::CombatState combat(core::BattleGrid(core::TileMap(6, 6)));
        core::CombatantProfile cible = profil("Cible", CombatSide::Enemies, 100);
        cible.damageTraits = std::move(traits);
        combat.enlist(cible, core::GridPosition{1, 1});
        core::DamagePipeline pipeline;
        if (aura) {
            pipeline.insert(DamageStage::Resistances, [](core::DamageWork& w, core::CombatState*) {
                w.adjust(0, w.portions[0].amount - 5, DamageStage::Resistances, "aura");
            });
        }
        return frapper(combat, pipeline, CombatantId{1},
                       {fixe(25, DamageType::Bludgeoning, drapeaux)});
    };
    const core::DamageAffinity resiste{DamageType::Bludgeoning, DamageAffinityKind::Resistance, 0};
    const core::DamageAffinity vulnerable{DamageType::Bludgeoning,
                                          DamageAffinityKind::Vulnerability, 0};
    const core::DamageAffinity immunise{DamageType::Bludgeoning, DamageAffinityKind::Immunity, 0};

    const core::DamageReport exemple = encaisser({{resiste}}, 0, true);
    EXPECT_EQ(exemple.work.hitPointLoss, 10);
    ASSERT_EQ(exemple.work.trace.size(), 2U);
    EXPECT_EQ(exemple.work.trace[0].source, "aura");
    EXPECT_EQ(exemple.work.trace[1].source, "resistance (contondant)");
    EXPECT_EQ(exemple.work.trace[1].before, 20);
    EXPECT_EQ(exemple.work.trace[1].after, 10);

    EXPECT_EQ(encaisser({{resiste, vulnerable}}, 0, false).work.hitPointLoss, 24);
    EXPECT_EQ(encaisser({{resiste, resiste}}, 0, false).work.hitPointLoss, 12);
    EXPECT_EQ(encaisser({{immunise, vulnerable}}, 0, false).work.hitPointLoss, 0);

    const core::DamageAffinity nonMagique{DamageType::Bludgeoning, DamageAffinityKind::Resistance,
                                          core::flagsOf(DamageFlag::Magical)};
    EXPECT_EQ(encaisser({{nonMagique}}, 0, false).work.hitPointLoss, 12);
    EXPECT_EQ(
        encaisser({{nonMagique}}, core::flagsOf(DamageFlag::Magical), false).work.hitPointLoss, 25);
    EXPECT_EQ(encaisser({{resiste}}, core::flagsOf(DamageFlag::IgnoresResistance), false)
                  .work.hitPointLoss,
              25);
}

/**
 * @brief Les etapes s'executent dans l'ordre, et la conversion precede la resistance.
 * \castest{<b>Les cinq etapes du pipeline s'executent dans l'ordre nomme, et un type converti est
 * resiste selon son nouveau type.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un greffon par etape, qui note son passage.<br/>2. Un greffon de conversion qui
 * change le feu en froid.<br/>3. 20 degats de feu sur une cible resistante au froid.<br/>
 * \tattendu Source, conversion, resistances, reserves, points de vie ; 10 degats subis.
 * }
 */
TEST(DamageTest, LesEtapesSEnchainentEtLaConversionPrecedeLaResistance) {
    core::CombatState combat(core::BattleGrid(core::TileMap(6, 6)));
    core::CombatantProfile cible = profil("Elementaire", CombatSide::Enemies, 50);
    cible.damageTraits.affinities.push_back({DamageType::Cold, DamageAffinityKind::Resistance, 0});
    combat.enlist(cible, core::GridPosition{1, 1});

    std::vector<std::string> passages;
    core::DamagePipeline pipeline;
    for (const DamageStage etape :
         {DamageStage::HitPoints, DamageStage::Reserves, DamageStage::Resistances,
          DamageStage::Conversion, DamageStage::Source}) {
        pipeline.insert(etape, [&passages, etape](core::DamageWork&, core::CombatState* etat) {
            EXPECT_NE(etat, nullptr);
            passages.emplace_back(core::damageStageName(etape));
        });
    }
    pipeline.insert(DamageStage::Conversion, [](core::DamageWork& w, core::CombatState*) {
        w.portions[0].type = DamageType::Cold;
    });
    const core::DamageReport rapport =
        frapper(combat, pipeline, CombatantId{1}, {fixe(20, DamageType::Fire)});
    EXPECT_EQ(passages, (std::vector<std::string>{"source", "conversion", "resistances", "reserves",
                                                  "points de vie"}));
    EXPECT_EQ(rapport.work.hitPointLoss, 10);
    EXPECT_EQ(combat.find(CombatantId{1})->profile.currentHitPoints, 40);
}

/**
 * @brief Les points de vie temporaires absorbent d'abord et ne se cumulent pas.
 * \castest{<b>Les points de vie temporaires se perdent avant les points de vie, ne se cumulent pas,
 * ne se soignent pas, et absorbent encore a 0 PV sans relever.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Donner 10 PV temporaires, puis 12, puis 5 ; une reserve cumulable de 3.<br/>2.
 * Infliger 7, puis 12.<br/>3. Soigner ; infliger des degats qui ignorent les reserves.<br/>4. A 0
 * PV, donner des PV temporaires et infliger 4.<br/>
 * \tattendu 12 retenus, 5 refuses ; les 7 absorbes (3 cumulables, puis 4 temporaires) ; sur 12,
 * 8 absorbes et 4 PV perdus ; le soin ne rend aucune reserve ; des degats qui ignorent les reserves
 * vont aux PV ; a 0 PV la reserve absorbe encore et le combattant reste a terre.
 * }
 */
TEST(DamageTest, LesPointsDeVieTemporairesAbsorbentDAbordEtNeSeCumulentPas) {
    core::CombatState combat(core::BattleGrid(core::TileMap(6, 6)));
    combat.enlist(profil("Guerrier", CombatSide::Allies, 20), core::GridPosition{1, 1});
    const CombatantId id{1};
    const core::DamagePipeline pipeline;
    const std::string temporaires(core::TEMPORARY_HIT_POINTS);

    EXPECT_TRUE(combat.grantReserve(id, {.source = temporaires, .amount = 10, .stacks = false}));
    EXPECT_TRUE(combat.grantReserve(id, {.source = temporaires, .amount = 12, .stacks = false}));
    EXPECT_FALSE(combat.grantReserve(id, {.source = temporaires, .amount = 5, .stacks = false}));
    EXPECT_TRUE(combat.grantReserve(id, {.source = "Exosquelette", .amount = 3, .stacks = true}));
    ASSERT_EQ(combat.reserves(id)->size(), 2U);
    EXPECT_EQ(combat.reserves(id)->front().amount, 12);

    // La plus recente absorbe d'abord : 3 d'exosquelette, puis 4 de temporaires.
    core::DamageReport rapport = frapper(combat, pipeline, id, {fixe(7, DamageType::Slashing)});
    EXPECT_EQ(rapport.work.absorbed, 7);
    EXPECT_EQ(rapport.work.hitPointLoss, 0);
    EXPECT_EQ(combat.find(id)->profile.currentHitPoints, 20);
    ASSERT_EQ(combat.reserves(id)->size(), 1U);
    EXPECT_EQ(combat.reserves(id)->front().amount, 8);

    // Manuel : 5 temporaires et 7 degats font perdre les 5, puis 2 PV. Ici 8 et 12 : 4 PV.
    rapport = frapper(combat, pipeline, id, {fixe(12, DamageType::Slashing)});
    EXPECT_EQ(rapport.work.absorbed, 8);
    EXPECT_EQ(rapport.work.hitPointLoss, 4);
    EXPECT_TRUE(combat.reserves(id)->empty());
    EXPECT_EQ(combat.find(id)->profile.currentHitPoints, 16);

    combat.heal(id, 10);
    EXPECT_TRUE(combat.reserves(id)->empty());
    EXPECT_EQ(combat.find(id)->profile.currentHitPoints, 20);

    combat.grantReserve(id, {.source = temporaires, .amount = 50, .stacks = false});
    rapport = frapper(combat, pipeline, id,
                      {fixe(20, DamageType::Psychic, core::flagsOf(DamageFlag::IgnoresReserves))});
    EXPECT_EQ(rapport.work.absorbed, 0);
    EXPECT_EQ(combat.find(id)->status, core::CombatantStatus::Down);
    EXPECT_EQ(combat.reserves(id)->front().amount, 50);

    rapport = frapper(combat, pipeline, id, {fixe(4, DamageType::Slashing)});
    EXPECT_EQ(rapport.work.absorbed, 4);
    EXPECT_EQ(combat.find(id)->status, core::CombatantStatus::Down);
}

/**
 * @brief Les PV sont bornes a 0, la chute s'annonce une fois, l'excedent est rapporte.
 * \castest{<b>Les points de vie sont bornes a 0 aux trois bornes, la chute s'annonce une seule
 * fois, et les degats restants au-dela de 0 sont rapportes pour l'agonie.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Bloquant<br/>
 * \tetapes 1. Une cible a 10 PV : 9 degats, puis 1, puis 5.<br/>2. Le clerc du Manuel, 6 PV sur
 * 12, subit 18 degats d'un coup critique.<br/>3. Un seuil « sous la moitie ».<br/>
 * \tattendu 1 PV et debout ; 0 PV, a terre, chute annoncee ; toujours 0, degats annonces sans
 * seconde chute ; excedent de 12 et critique dans l'evenement ; le seuil n'est franchi qu'une fois.
 * }
 */
TEST(DamageTest, LesPointsDeVieSontBornesAZeroEtLExcedentEstRapporte) {
    core::CombatState combat(core::BattleGrid(core::TileMap(6, 6)));
    combat.enlist(profil("Cible", CombatSide::Enemies, 10), core::GridPosition{1, 1});
    core::CombatantProfile clerc = profil("Clerc", CombatSide::Allies, 12);
    clerc.currentHitPoints = 6;
    combat.enlist(clerc, core::GridPosition{3, 3});

    std::vector<core::CombatEvent> degats;
    std::vector<core::CombatEvent> chutes;
    int moitie = 0;
    combat.subscribe(CombatHook::DamageTaken, [&](core::CombatState&, const core::CombatEvent& e) {
        degats.push_back(e);
        moitie += core::crossedBelow(e, 1, 2) ? 1 : 0;
    });
    combat.subscribe(CombatHook::CombatantDowned,
                     [&](core::CombatState&, const core::CombatEvent& e) { chutes.push_back(e); });
    const core::DamagePipeline pipeline;
    const CombatantId cible{1};

    frapper(combat, pipeline, cible, {fixe(9, DamageType::Slashing)});
    EXPECT_EQ(combat.find(cible)->profile.currentHitPoints, 1);
    EXPECT_EQ(combat.find(cible)->status, core::CombatantStatus::Standing);
    EXPECT_TRUE(chutes.empty());
    EXPECT_EQ(moitie, 1);

    const core::DamageReport juste =
        frapper(combat, pipeline, cible, {fixe(1, DamageType::Slashing)});
    EXPECT_EQ(juste.hitPointsAfter, 0);
    EXPECT_EQ(juste.overflow, 0);
    EXPECT_EQ(combat.find(cible)->status, core::CombatantStatus::Down);
    EXPECT_EQ(chutes.size(), 1U);

    frapper(combat, pipeline, cible, {fixe(5, DamageType::Slashing)});
    EXPECT_EQ(combat.find(cible)->profile.currentHitPoints, 0);
    EXPECT_EQ(chutes.size(), 1U);
    ASSERT_EQ(degats.size(), 3U);
    EXPECT_EQ(degats.back().hitPointsBefore, 0);
    EXPECT_EQ(moitie, 1);

    core::RolledDamage critique = fixe(18, DamageType::Bludgeoning);
    critique.critical = true;
    const core::DamageReport excedent = frapper(combat, pipeline, CombatantId{2}, {critique});
    EXPECT_EQ(excedent.hitPointsBefore, 6);
    EXPECT_EQ(excedent.hitPointsAfter, 0);
    EXPECT_EQ(excedent.overflow, 12);
    ASSERT_EQ(chutes.size(), 2U);
    EXPECT_EQ(chutes.back().overflow, 12);
    EXPECT_EQ(chutes.back().maximumHitPoints, 12);
    EXPECT_TRUE(chutes.back().critical);
}

/**
 * @brief Une salve se lance une fois et s'applique d'un seul coup.
 * \castest{<b>Des degats qui touchent plusieurs cibles sont lances une fois pour toutes, et une
 * salve qui abat les deux camps est une defaite quel que soit l'ordre des cibles.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Un allie et un ennemi a 5 PV, combat commence.<br/>2. Un seul jet de 3d6+10 de feu
 * applique aux deux, l'ennemi en premier.<br/>
 * \tattendu Les deux perdent le meme montant ; les deux sont a terre ; l'issue est une defaite.
 * }
 */
TEST(DamageTest, UneSalveSeLanceUneFoisEtSAppliqueDUnCoup) {
    core::CombatState combat(core::BattleGrid(core::TileMap(8, 8)));
    combat.enlist(profil("Heros", CombatSide::Allies, 5, 100), core::GridPosition{1, 1});
    combat.enlist(profil("Ogre", CombatSide::Enemies, 5, -100), core::GridPosition{5, 5});
    core::DeterministicRandom hasard(11);
    ASSERT_TRUE(combat.start(hasard));

    const std::vector<core::DamageClause> boule{{.dice = *core::parseDice("3d6+10"),
                                                 .type = DamageType::Fire,
                                                 .flags = core::flagsOf(DamageFlag::Spell)}};
    const std::vector<core::RolledDamage> jet = core::rollDamage(boule, false, hasard);
    const std::vector<core::DamageRequest> salve{{.target = CombatantId{2}, .damage = jet},
                                                 {.target = CombatantId{1}, .damage = jet}};
    const std::vector<core::DamageReport> rapports = core::DamagePipeline{}.apply(combat, salve);
    ASSERT_EQ(rapports.size(), 2U);
    EXPECT_EQ(rapports[0].work.hitPointLoss, rapports[1].work.hitPointLoss);
    EXPECT_EQ(combat.outcome(), core::CombatOutcome::Defeat);
}

/**
 * @brief Les structures ont des points de vie et des resistances ; le bestiaire donne ses
 * affinites.
 * \castest{<b>Une structure de la grille traverse le pipeline avec ses resistances et quitte la
 * grille detruite ; les affinites d'une creature se lisent de son bloc.</b><br/>
 * \tcat Unitaire · Combat<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Une porte de 10 PV immunisee au poison et resistante au perforant.<br/>2. 30 degats
 * de poison, puis 14 perforants, puis 6 perforants.<br/>3. Une creature resistante au froid,
 * immunisee au poison, vulnerable au feu.<br/>
 * \tattendu Porte intacte, puis 3 PV, puis detruite ; trois affinites dans l'ordre immunite,
 * resistance, vulnerabilite.
 * }
 */
TEST(DamageTest, LesStructuresOntDesPointsDeVieEtLeBestiaireSesAffinites) {
    core::BattleGrid grille(core::TileMap(6, 6));
    core::GridObject porte{
        .kind = "porte", .hitPoints = 10, .blocksMovement = true, .damageTraits = {}};
    porte.damageTraits.affinities = {{DamageType::Poison, DamageAffinityKind::Immunity, 0},
                                     {DamageType::Piercing, DamageAffinityKind::Resistance, 0}};
    const core::GridPosition ou{2, 2};
    ASSERT_EQ(grille.placeObject(ou, porte), core::PlacementResult::Placed);
    const core::DamagePipeline pipeline;
    const std::vector<core::RolledDamage> poison{fixe(30, DamageType::Poison)};
    EXPECT_EQ(pipeline.applyToStructure(grille, ou, poison).hitPointsAfter, 10);
    const std::vector<core::RolledDamage> fleches{fixe(14, DamageType::Piercing)};
    EXPECT_EQ(pipeline.applyToStructure(grille, ou, fleches).hitPointsAfter, 3);
    ASSERT_NE(grille.objectAt(ou), nullptr);
    const std::vector<core::RolledDamage> fin{fixe(6, DamageType::Piercing)};
    EXPECT_EQ(pipeline.applyToStructure(grille, ou, fin).overflow, 0);
    EXPECT_EQ(grille.objectAt(ou), nullptr);

    core::Creature elementaire;
    elementaire.damageResistances = {DamageType::Cold};
    elementaire.damageImmunities = {DamageType::Poison};
    elementaire.damageVulnerabilities = {DamageType::Fire};
    const core::DamageTraits traits = core::damageTraitsFor(elementaire);
    ASSERT_EQ(traits.affinities.size(), 3U);
    EXPECT_EQ(traits.affinities[0].kind, DamageAffinityKind::Immunity);
    EXPECT_TRUE(traits.applies(DamageAffinityKind::Vulnerability, DamageType::Fire, 0));
    EXPECT_FALSE(traits.applies(DamageAffinityKind::Resistance, DamageType::Fire, 0));
}
