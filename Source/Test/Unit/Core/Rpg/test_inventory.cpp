// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_inventory.cpp
 * @brief Tests de l'inventaire, des emplacements d'équipement et des statistiques dérivées
 *        (`LOT-14`, `EX-INV-020`). Logique pure, sans Qt.
 *
 * Le test central est `LaClasseDArmureNeDerivePasAvecLOrdre` : il équipe et retire dans **six**
 * ordres différents et vérifie qu'on retombe exactement sur la valeur de départ. C'est le critère
 * d'acceptation du lot, et il attrape le défaut qu'une implémentation accumulative ne signale
 * jamais — après trois équipements et deux retraits dans le désordre, la CA a dérivé, et le
 * personnage est simplement devenu un peu plus résistant.
 */

#include <algorithm>
#include <array>
#include <filesystem>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Inventory.h"

namespace {

using core::Ability;
using core::EquipmentSlot;

/// Une fiche minimale : ce que la CA et la charge consultent, et rien d'autre.
[[nodiscard]] core::CharacterSheet fiche(int force = 14, int dexterite = 14) {
    core::CharacterSheet personnage;
    personnage.name = "Sujet d'essai";
    personnage.abilities[static_cast<std::size_t>(Ability::Strength)] = force;
    personnage.abilities[static_cast<std::size_t>(Ability::Dexterity)] = dexterite;
    personnage.speedMeters = 9.0F;
    return personnage;
}

/// Les constantes de création, écrites ici : un test qui les lit dans la donnée vérifie deux
/// choses à la fois, et échoue pour la mauvaise raison le jour où la donnée bouge.
[[nodiscard]] core::CharacterCreationRules regles() {
    core::CharacterCreationRules creation;
    creation.unarmoredArmorClass = 10;
    creation.maximumAbilityScore = 20;
    return creation;
}

[[nodiscard]] core::EncumbranceRules charge() {
    return {.carryingCapacityGramsPerStrength = 7500,
            .encumberedGramsPerStrength = 2500,
            .heavilyEncumberedGramsPerStrength = 5000,
            .encumberedSpeedPenaltyMeters = 3.0F,
            .heavilyEncumberedSpeedPenaltyMeters = 6.0F};
}

/// Un catalogue d'équipement réduit à ce que ces tests portent.
[[nodiscard]] core::EquipmentCatalog catalogueEquipement() {
    core::EquipmentCatalog catalogue;
    catalogue.armors.push_back({.id = "cuir",
                                .name = "Cuir",
                                .category = core::ArmorCategory::Light,
                                .baseArmorClass = 11,
                                .dexterityBonus = true,
                                .weightGrams = 5000});
    catalogue.armors.push_back({.id = "demi-plate",
                                .name = "Demi-plate",
                                .category = core::ArmorCategory::Medium,
                                .baseArmorClass = 15,
                                .dexterityBonus = true,
                                .dexterityBonusMax = 2,
                                .weightGrams = 20000});
    catalogue.armors.push_back({.id = "bouclier",
                                .name = "Bouclier",
                                .category = core::ArmorCategory::Shield,
                                .baseArmorClass = 2,
                                .weightGrams = 3000});
    catalogue.weapons.push_back({.id = "epee-longue",
                                 .name = "Épée longue",
                                 .category = "martial",
                                 .ranged = false,
                                 .damage = core::Dice{.count = 1, .faces = 8},
                                 .damageType = core::DamageType::Slashing,
                                 .weightGrams = 1500});
    catalogue.weapons.push_back({.id = "arc-court",
                                 .name = "Arc court",
                                 .category = "simple",
                                 .ranged = true,
                                 .damage = core::Dice{.count = 1, .faces = 6},
                                 .damageType = core::DamageType::Piercing,
                                 .weightGrams = 1000});
    catalogue.weapons.push_back({.id = "rapiere",
                                 .name = "Rapière",
                                 .category = "martial",
                                 .ranged = false,
                                 .damage = core::Dice{.count = 1, .faces = 8},
                                 .damageType = core::DamageType::Piercing,
                                 .weightGrams = 1000,
                                 .properties = {"finesse"}});
    return catalogue;
}

[[nodiscard]] core::ItemCatalog catalogueObjets() {
    core::ItemCatalog catalogue;
    catalogue.items.push_back(
        {.id = "corde-chanvre", .name = "Corde de chanvre", .weightGrams = 5000});
    catalogue.items.push_back({.id = "torche", .name = "Torche", .weightGrams = 500});
    catalogue.items.push_back({.id = "amulette", .name = "Amulette", .weightGrams = 500});
    return catalogue;
}

}  // namespace

/**
 * @brief Équiper une armure change la CA du montant attendu, et la retirer **restitue exactement**
 *        la valeur d'origine, quel que soit l'ordre des opérations.
 * \castest{<b>La classe d'armure ne derive pas avec l'ordre des equipements.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Relever la CA sans equipement.<br/>2. Jouer six ordres d'equipement et de retrait
 * d'une armure et d'un bouclier.<br/>3. Relever la CA apres chaque sequence complete.<br/>
 * \tattendu La CA revient exactement a sa valeur de depart dans les six cas.
 * }
 */
TEST(InventoryTest, LaClasseDArmureNeDerivePasAvecLOrdre) {
    const core::CharacterSheet personnage = fiche();
    const core::EquipmentCatalog equipement = catalogueEquipement();
    const core::ItemCatalog objets = catalogueObjets();
    const core::ItemLookup catalogues{.items = &objets, .equipment = &equipement};

    core::Inventory sac;
    const int depart =
        core::derivedStatsFor(personnage, sac, catalogues, regles(), charge()).armorClass;
    EXPECT_EQ(depart, 12) << "10 + modificateur de Dexterite (+2), sans armure";

    // Six sequences qui posent et retirent les memes deux pieces dans des ordres differents. Une
    // implementation qui ACCUMULE les bonus survit a la premiere et derive sur les suivantes.
    const std::vector<std::vector<std::pair<bool, EquipmentSlot>>> sequences = {
        {{true, EquipmentSlot::Torso},
         {true, EquipmentSlot::OffHand},
         {false, EquipmentSlot::Torso},
         {false, EquipmentSlot::OffHand}},
        {{true, EquipmentSlot::OffHand},
         {true, EquipmentSlot::Torso},
         {false, EquipmentSlot::OffHand},
         {false, EquipmentSlot::Torso}},
        {{true, EquipmentSlot::Torso},
         {true, EquipmentSlot::OffHand},
         {false, EquipmentSlot::OffHand},
         {false, EquipmentSlot::Torso}},
        {{true, EquipmentSlot::OffHand},
         {false, EquipmentSlot::OffHand},
         {true, EquipmentSlot::Torso},
         {false, EquipmentSlot::Torso}},
        {{true, EquipmentSlot::Torso},
         {false, EquipmentSlot::Torso},
         {true, EquipmentSlot::Torso},
         {false, EquipmentSlot::Torso}},
        {{true, EquipmentSlot::OffHand},
         {true, EquipmentSlot::Torso},
         {false, EquipmentSlot::Torso},
         {false, EquipmentSlot::OffHand}},
    };

    for (std::size_t rang = 0; rang < sequences.size(); ++rang) {
        for (const auto& [poser, emplacement] : sequences[rang]) {
            if (poser) {
                static_cast<void>(
                    core::equip(sac, emplacement,
                                emplacement == EquipmentSlot::Torso ? "demi-plate" : "bouclier"));
            } else {
                static_cast<void>(core::unequip(sac, emplacement));
            }
        }
        EXPECT_EQ(core::derivedStatsFor(personnage, sac, catalogues, regles(), charge()).armorClass,
                  depart)
            << "la CA a derive apres la sequence " << rang;
    }
}

/**
 * @brief Les trois formes de la table du livre donnent trois classes d'armure différentes.
 * \castest{<b>Chaque categorie d'armure applique sa propre regle de Dexterite.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Equiper une armure legere, puis une intermediaire, avec une Dexterite de 18.<br/>
 * 2. Ajouter un bouclier.<br/>
 * \tattendu Legere : 11 + 4. Intermediaire : 15 + 2 (plafonne). Bouclier : +2 par-dessus.
 * }
 */
TEST(InventoryTest, ChaqueCategorieDArmureAppliqueSaRegle) {
    const core::CharacterSheet personnage = fiche(14, 18);  // modificateur de Dexterite : +4
    const core::EquipmentCatalog equipement = catalogueEquipement();
    const core::ItemLookup catalogues{.equipment = &equipement};
    core::Inventory sac;

    static_cast<void>(core::equip(sac, EquipmentSlot::Torso, "cuir"));
    EXPECT_EQ(core::derivedStatsFor(personnage, sac, catalogues, regles(), charge()).armorClass, 15)
        << "armure legere : la Dexterite s'ajoute sans plafond";

    static_cast<void>(core::equip(sac, EquipmentSlot::Torso, "demi-plate"));
    EXPECT_EQ(core::derivedStatsFor(personnage, sac, catalogues, regles(), charge()).armorClass, 17)
        << "armure intermediaire : la Dexterite est plafonnee a +2";

    static_cast<void>(core::equip(sac, EquipmentSlot::OffHand, "bouclier"));
    EXPECT_EQ(core::derivedStatsFor(personnage, sac, catalogues, regles(), charge()).armorClass, 19)
        << "le bouclier s'AJOUTE, il ne remplace pas";
}

/**
 * @brief Équiper une pièce à un emplacement qui en portait déjà une rend la précédente.
 * \castest{<b>Un emplacement ne porte jamais deux pieces, et ce qui en sort est rendu.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Equiper une armure, puis une autre au meme emplacement.<br/>
 * \tattendu La premiere est rendue a l'appelant, et l'emplacement ne porte que la seconde.
 * }
 */
TEST(InventoryTest, UnEmplacementRendCeQuIlPortait) {
    core::Inventory sac;
    EXPECT_EQ(core::equip(sac, EquipmentSlot::Torso, "cuir"), "");
    EXPECT_EQ(core::equip(sac, EquipmentSlot::Torso, "demi-plate"), "cuir");
    EXPECT_EQ(sac.at(EquipmentSlot::Torso), "demi-plate");
    EXPECT_EQ(core::unequip(sac, EquipmentSlot::Torso), "demi-plate");
    EXPECT_FALSE(sac.isEquipped(EquipmentSlot::Torso));
}

/**
 * @brief Le sac empile les lignes identiques, et une ligne vidée disparaît.
 * \castest{<b>Le sac empile, et une ligne videe disparait.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Ajouter deux fois le meme objet.<br/>2. En retirer plus qu'il n'y en a.<br/>
 * \tattendu Une seule ligne de quantite cumulee ; le retrait rend ce qui existait, et la ligne
 * disparait.
 * }
 */
TEST(InventoryTest, LeSacEmpileEtSeVide) {
    core::Inventory sac;
    core::addToBackpack(sac, "torche", 3);
    core::addToBackpack(sac, "torche", 2);
    ASSERT_EQ(sac.backpack.size(), 1U);
    EXPECT_EQ(sac.backpack.front().quantity, 5);

    EXPECT_EQ(core::removeFromBackpack(sac, "torche", 10), 5) << "on ne retire que ce qui existe";
    EXPECT_TRUE(sac.backpack.empty());
    EXPECT_EQ(core::removeFromBackpack(sac, "torche", 1), 0);
}

/**
 * @brief Le poids porté additionne le sac ET l'équipement, dans une seule unité.
 * \castest{<b>Le poids porte compte le sac et l'equipement.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Equiper une armure et une arme.<br/>2. Ajouter des objets au sac.<br/>
 * \tattendu Le total est la somme des grammes, quantites comprises.
 * }
 */
TEST(InventoryTest, LePoidsPorteCompteLeSacEtLEquipement) {
    const core::EquipmentCatalog equipement = catalogueEquipement();
    const core::ItemCatalog objets = catalogueObjets();
    const core::ItemLookup catalogues{.items = &objets, .equipment = &equipement};

    core::Inventory sac;
    static_cast<void>(core::equip(sac, EquipmentSlot::Torso, "cuir"));            // 5000
    static_cast<void>(core::equip(sac, EquipmentSlot::MainHand, "epee-longue"));  // 1500
    core::addToBackpack(sac, "torche", 4);                                        // 4 x 500
    core::addToBackpack(sac, "corde-chanvre", 1);                                 // 5000

    EXPECT_EQ(core::carriedWeightGrams(sac, catalogues), 5000 + 1500 + 2000 + 5000);
}

/**
 * @brief Un identifiant qu'aucun catalogue ne porte est **signalé**, pas confondu avec un objet
 *        sans masse.
 * \castest{<b>Un identifiant inconnu des catalogues est signale.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre au sac un identifiant absent des catalogues.<br/>
 * \tattendu Il figure dans les identifiants inconnus, et ne pese rien.
 * }
 */
TEST(InventoryTest, UnIdentifiantInconnuEstSignale) {
    const core::EquipmentCatalog equipement = catalogueEquipement();
    const core::ItemCatalog objets = catalogueObjets();
    const core::ItemLookup catalogues{.items = &objets, .equipment = &equipement};

    core::Inventory sac;
    core::addToBackpack(sac, "bidule-inexistant", 1);
    static_cast<void>(core::equip(sac, EquipmentSlot::Head, "heaume-fantome"));

    const std::vector<std::string> inconnus = core::unknownIds(sac, catalogues);
    EXPECT_EQ(inconnus, (std::vector<std::string>{"bidule-inexistant", "heaume-fantome"}));
    EXPECT_EQ(core::carriedWeightGrams(sac, catalogues), 0);
}

/**
 * @brief Les trois seuils de charge, et le comportement défini au dépassement.
 * \castest{<b>La charge franchit ses trois seuils et definit le depassement.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger un personnage de Force 10 en dessous du premier seuil, puis entre les deux,
 * puis au-dela du second, puis au-dela de la capacite.<br/>
 * \tattendu Non encombre, encombre (-3 m), lourdement encombre (-6 m), puis hors capacite avec
 * une vitesse nulle.
 * }
 */
TEST(InventoryTest, LaChargeFranchitSesSeuils) {
    const core::CharacterSheet personnage = fiche(10, 10);  // capacite : 75 kg
    const core::ItemCatalog objets = catalogueObjets();
    const core::ItemLookup catalogues{.items = &objets};

    const auto etat = [&](int torches) {
        core::Inventory sac;
        core::addToBackpack(sac, "torche", torches);  // 500 g piece
        return core::derivedStatsFor(personnage, sac, catalogues, regles(), charge());
    };

    // Seuils pour Force 10 : encombre au-dela de 25 kg, lourdement au-dela de 50, capacite 75.
    const core::DerivedStats leger = etat(20);  // 10 kg
    EXPECT_EQ(leger.encumbrance, core::EncumbranceLevel::Unencumbered);
    EXPECT_FLOAT_EQ(leger.speedMeters, 9.0F);
    EXPECT_EQ(leger.carryingCapacityGrams, 75000);

    const core::DerivedStats encombre = etat(80);  // 40 kg
    EXPECT_EQ(encombre.encumbrance, core::EncumbranceLevel::Encumbered);
    EXPECT_FLOAT_EQ(encombre.speedMeters, 6.0F);

    const core::DerivedStats lourd = etat(120);  // 60 kg
    EXPECT_EQ(lourd.encumbrance, core::EncumbranceLevel::HeavilyEncumbered);
    EXPECT_FLOAT_EQ(lourd.speedMeters, 3.0F);

    const core::DerivedStats trop = etat(200);  // 100 kg, au-dela de la capacite
    EXPECT_EQ(trop.encumbrance, core::EncumbranceLevel::OverCapacity);
    EXPECT_FLOAT_EQ(trop.speedMeters, 0.0F) << "au-dela de la capacite, il ne porte plus";
}

/**
 * @brief Sans règle de charge chargée, la fiche ne prétend pas connaître une règle qui manque.
 * \castest{<b>Sans regle de charge, aucun encombrement n'est affirme.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Deriver les statistiques avec des bornes de charge non chargees.<br/>
 * \tattendu La charge reste << non encombre >>, la capacite vaut zero, et la vitesse est intacte.
 * }
 */
TEST(InventoryTest, SansRegleDeChargeAucunEncombrementNEstAffirme) {
    const core::CharacterSheet personnage = fiche(10, 10);
    const core::ItemCatalog objets = catalogueObjets();
    const core::ItemLookup catalogues{.items = &objets};
    core::Inventory sac;
    core::addToBackpack(sac, "corde-chanvre", 100);  // 500 kg

    const core::DerivedStats derivees =
        core::derivedStatsFor(personnage, sac, catalogues, regles(), core::EncumbranceRules{});
    EXPECT_EQ(derivees.encumbrance, core::EncumbranceLevel::Unencumbered);
    EXPECT_EQ(derivees.carryingCapacityGrams, 0);
    EXPECT_FLOAT_EQ(derivees.speedMeters, 9.0F);
}

/**
 * @brief La caractéristique d'attaque suit l'arme : Force au corps à corps, Dextérité à distance,
 *        la meilleure des deux pour une arme de finesse.
 * \castest{<b>La caracteristique d'attaque suit l'arme portee.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Equiper une arme de melee, puis une arme a distance, puis une arme de finesse, avec
 * une Dexterite superieure a la Force.<br/>
 * \tattendu Force, puis Dexterite, puis Dexterite (la meilleure des deux).
 * }
 */
TEST(InventoryTest, LaCaracteristiqueDAttaqueSuitLArme) {
    const core::CharacterSheet personnage = fiche(12, 18);
    const core::EquipmentCatalog equipement = catalogueEquipement();
    const core::ItemLookup catalogues{.equipment = &equipement};
    core::Inventory sac;

    static_cast<void>(core::equip(sac, EquipmentSlot::MainHand, "epee-longue"));
    core::DerivedStats derivees =
        core::derivedStatsFor(personnage, sac, catalogues, regles(), charge());
    EXPECT_EQ(derivees.attackAbility, Ability::Strength);
    ASSERT_TRUE(derivees.damage.has_value());
    EXPECT_EQ(derivees.damage->faces, 8);

    static_cast<void>(core::equip(sac, EquipmentSlot::MainHand, "arc-court"));
    derivees = core::derivedStatsFor(personnage, sac, catalogues, regles(), charge());
    EXPECT_EQ(derivees.attackAbility, Ability::Dexterity);

    static_cast<void>(core::equip(sac, EquipmentSlot::MainHand, "rapiere"));
    derivees = core::derivedStatsFor(personnage, sac, catalogues, regles(), charge());
    EXPECT_EQ(derivees.attackAbility, Ability::Dexterity) << "finesse : la meilleure des deux";

    static_cast<void>(core::unequip(sac, EquipmentSlot::MainHand));
    derivees = core::derivedStatsFor(personnage, sac, catalogues, regles(), charge());
    EXPECT_FALSE(derivees.damage.has_value()) << "main vide : aucun de a lancer";
}

/**
 * @brief Un bouclier rangé au torse compte quand même comme un bouclier.
 * \castest{<b>C'est la categorie qui dit comment une piece compte, pas l'emplacement.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Ranger un bouclier a l'emplacement du torse.<br/>
 * \tattendu La CA vaut la base sans armure plus le bonus du bouclier, et non 2.
 * }
 */
TEST(InventoryTest, LaCategorieDecideAvantLEmplacement) {
    const core::CharacterSheet personnage = fiche(14, 14);
    const core::EquipmentCatalog equipement = catalogueEquipement();
    const core::ItemLookup catalogues{.equipment = &equipement};

    core::Inventory sac;
    static_cast<void>(core::equip(sac, EquipmentSlot::Torso, "bouclier"));
    EXPECT_EQ(core::derivedStatsFor(personnage, sac, catalogues, regles(), charge()).armorClass, 14)
        << "10 + Dex(+2) + bouclier(2)";
}

/**
 * @brief Les seize emplacements se nomment et se relisent dans les deux sens.
 * \castest{<b>Les seize emplacements se nomment et se relisent.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Mineur<br/>
 * \tetapes 1. Convertir chaque emplacement en nom, puis le nom en emplacement.<br/>
 * \tattendu L'aller-retour redonne l'emplacement de depart, et un nom inconnu ne se devine pas.
 * }
 */
TEST(InventoryTest, LesEmplacementsSeNommentEtSeRelisent) {
    for (std::size_t rang = 0; rang < core::EQUIPMENT_SLOT_COUNT; ++rang) {
        const auto emplacement = static_cast<EquipmentSlot>(rang);
        const std::string_view nom = core::equipmentSlotName(emplacement);
        EXPECT_FALSE(nom.empty());
        EXPECT_EQ(core::parseEquipmentSlot(nom), emplacement);
    }
    EXPECT_FALSE(core::parseEquipmentSlot("chapeau-de-paille").has_value());
}

/**
 * @brief Le catalogue d'objets LIVRÉ se charge, et ses poids sont utilisables.
 * \castest{<b>Le catalogue d'objets livre se charge.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger Source/Elements/Rpg/items.<br/>
 * \tattendu Le catalogue est non vide, sans erreur, et chaque objet porte un identifiant.
 * }
 */
TEST(InventoryTest, LeCatalogueLivreSeCharge) {
    const core::ItemCatalog catalogue =
        core::loadItems(std::filesystem::path(JADG_RPG_DIR) / "items");
    EXPECT_TRUE(catalogue.errors.empty())
        << (catalogue.errors.empty() ? "" : catalogue.errors.front());
    EXPECT_GT(catalogue.items.size(), 100U);
    for (const core::Item& objet : catalogue.items) {
        EXPECT_FALSE(objet.id.empty());
        EXPECT_FALSE(objet.name.empty()) << objet.id;
        EXPECT_GE(objet.weightGrams, 0) << objet.id;
    }
}

/**
 * @brief Les bornes de charge LIVRÉES se chargent, et portent les valeurs du livre.
 * \castest{<b>Les bornes de charge livrees portent les valeurs du livre.</b><br/>
 * \tcat Unitaire · Inventaire<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger Source/Elements/Rpg/rules/encumbrance.json.<br/>
 * \tattendu 7,5 kg par point de Force, seuils a 2,5 et 5, penalites de 3 et 6 metres.
 * }
 */
TEST(InventoryTest, LesBornesDeChargeLivreesSontCellesDuLivre) {
    const core::EncumbranceRules regles =
        core::loadEncumbranceRules(std::filesystem::path(JADG_RPG_RULES_DIR) / "encumbrance.json");
    ASSERT_TRUE(regles.isLoaded());
    EXPECT_EQ(regles.carryingCapacityGramsPerStrength, 7500);
    EXPECT_EQ(regles.encumberedGramsPerStrength, 2500);
    EXPECT_EQ(regles.heavilyEncumberedGramsPerStrength, 5000);
    EXPECT_FLOAT_EQ(regles.encumberedSpeedPenaltyMeters, 3.0F);
    EXPECT_FLOAT_EQ(regles.heavilyEncumberedSpeedPenaltyMeters, 6.0F);
}
