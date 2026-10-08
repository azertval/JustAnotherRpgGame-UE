// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_equipment.cpp
 * @brief Tests des armes et des armures (LOT-34).
 *
 * L'acceptation du lot tient en deux phrases : la CA calculee par le moteur pour chacune des 13
 * armures du catalogue egale la colonne CA de la table du livre ; et le poids total d'un
 * inventaire de depart correspond au calcul manuel. Les deux valeurs de reference sont RECOPIEES
 * A LA MAIN des Basic Rules -- comparer la sortie de la generation a elle-meme passerait quelle
 * que soit la faute d'extraction.
 */

#include <array>
#include <filesystem>
#include <string>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Equipment.h"

namespace {

const std::filesystem::path RPG{JADG_RPG_DIR};

[[nodiscard]] const core::EquipmentCatalog& catalogue() {
    static const core::EquipmentCatalog charge =
        core::loadEquipment(RPG / "weapons", RPG / "armors");
    return charge;
}

[[nodiscard]] const core::CharacterCreationRules& regles() {
    static const core::CharacterCreationRules lues =
        core::loadCharacterCreationRules(RPG / "rules" / "character-creation.json");
    return lues;
}

// La table des armures des Basic Rules p. 50, colonne par colonne, RECOPIEE A LA MAIN. `dexMax`
// vaut -1 quand la Dexterite ne s'ajoute pas du tout, et 99 quand elle s'ajoute sans plafond.
constexpr int SANS_DEXTERITE = -1;
constexpr int SANS_PLAFOND = 99;

struct ArmureDuLivre {
    const char* id;
    const char* categorie;
    int base;
    int dexMax;
    int forceExigee;  // 0 si aucune
    bool discretion;  // Desavantage
    int poidsGrammes;
    int prixCuivre;
};

// << Armure | VO | CA | Force | Discretion | Poids | Prix >>, treize rangees.
constexpr auto ARMURES = std::to_array<ArmureDuLivre>({
    {"matelassee", "light", 11, SANS_PLAFOND, 0, true, 4000, 500},
    {"cuir", "light", 11, SANS_PLAFOND, 0, false, 5000, 1000},
    {"cuir-cloute", "light", 12, SANS_PLAFOND, 0, false, 6500, 4500},
    {"peaux", "medium", 12, 2, 0, false, 6000, 1000},
    {"chemise-de-mailles", "medium", 13, 2, 0, false, 10000, 5000},
    {"ecailles", "medium", 14, 2, 0, true, 22500, 5000},
    {"cuirasse", "medium", 14, 2, 0, false, 10000, 40000},
    {"demi-plate", "medium", 15, 2, 0, true, 20000, 75000},
    {"broigne", "heavy", 14, SANS_DEXTERITE, 0, true, 20000, 3000},
    {"cotte-de-mailles", "heavy", 16, SANS_DEXTERITE, 13, true, 27500, 7500},
    {"clibanion", "heavy", 17, SANS_DEXTERITE, 15, true, 30000, 20000},
    {"harnois", "heavy", 18, SANS_DEXTERITE, 15, true, 32500, 150000},
    {"bouclier", "shield", 2, SANS_DEXTERITE, 0, false, 3000, 1000},
});

// Une fiche dont la Dexterite est elevee : c'est elle qui revele une armure lourde a qui l'on
// appliquerait la Dexterite a tort. Avec un modificateur de +1, la faute serait invisible.
[[nodiscard]] core::CharacterSheet ficheAgile(int dexterite) {
    core::CharacterSheet fiche;
    fiche.name = "Essai";
    fiche.abilities = {10, dexterite, 10, 10, 10, 10};
    return fiche;
}

}  // namespace

/**
 * @brief Les deux catalogues se chargent sans erreur.
 * \castest{<b>Les armes et les armures livrees se chargent toutes.</b><br/>
 * \tcat Unitaire · Equipement<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger weapons/ et armors/.<br/>
 * \tattendu 37 armes, 13 armures, aucune erreur.
 * }
 */
TEST(EquipmentTest, LesDeuxCataloguesSeChargent) {
    const core::EquipmentCatalog& lus = catalogue();
    for (const std::string& erreur : lus.errors) {
        ADD_FAILURE() << erreur;
    }
    EXPECT_EQ(lus.weapons.size(), 37U) << "la table des Basic Rules p. 48 porte 37 armes";
    EXPECT_EQ(lus.armors.size(), ARMURES.size())
        << "la table des Basic Rules p. 50 porte 13 rangees, bouclier compris";
    EXPECT_TRUE(regles().ok());
}

/**
 * @brief Les 13 armures portent les valeurs de la table du livre.
 * \castest{<b>Chaque armure du catalogue porte la CA, le poids et le prix du livre.</b><br/>
 * \tcat Unitaire · Equipement<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Pour les 13 rangees de la table p. 50, comparer categorie, CA de base, plafond de
 * Dexterite, Force exigee, discretion, poids et prix aux valeurs recopiees a la main.<br/>
 * \tattendu Les sept colonnes coincident pour chacune.
 * }
 */
TEST(EquipmentTest, LesTreizeArmuresPortentLesValeursDuLivre) {
    for (const ArmureDuLivre& attendue : ARMURES) {
        const core::Armor* armure = catalogue().findArmor(attendue.id);
        ASSERT_NE(armure, nullptr) << attendue.id << " absente du catalogue";
        EXPECT_EQ(core::armorCategoryName(armure->category), attendue.categorie) << attendue.id;
        EXPECT_EQ(armure->baseArmorClass, attendue.base) << attendue.id << " : CA de base";
        EXPECT_EQ(armure->weightGrams, attendue.poidsGrammes) << attendue.id << " : poids";
        EXPECT_EQ(armure->price, attendue.prixCuivre) << attendue.id << " : prix";
        EXPECT_EQ(armure->stealthDisadvantage, attendue.discretion) << attendue.id;

        if (attendue.dexMax == SANS_DEXTERITE) {
            EXPECT_FALSE(armure->dexterityBonus)
                << attendue.id << " : une armure lourde n'ajoute pas la Dexterite";
        } else {
            EXPECT_TRUE(armure->dexterityBonus) << attendue.id;
            if (attendue.dexMax == SANS_PLAFOND) {
                EXPECT_FALSE(armure->dexterityBonusMax.has_value())
                    << attendue.id << " : une armure legere n'a pas de plafond";
            } else {
                ASSERT_TRUE(armure->dexterityBonusMax.has_value()) << attendue.id;
                EXPECT_EQ(*armure->dexterityBonusMax, attendue.dexMax) << attendue.id;
            }
        }
        if (attendue.forceExigee == 0) {
            EXPECT_FALSE(armure->strengthRequired.has_value()) << attendue.id;
        } else {
            ASSERT_TRUE(armure->strengthRequired.has_value()) << attendue.id;
            EXPECT_EQ(*armure->strengthRequired, attendue.forceExigee) << attendue.id;
        }
    }
}

/**
 * @brief La CA calculee par le moteur egale celle de la table, pour les 13 armures.
 * \castest{<b>La classe d'armure calculee pour chaque armure egale la colonne CA du livre.</b><br/>
 * \tcat Unitaire · Equipement<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Avec une Dexterite de 18 (modificateur +4), calculer la CA de chaque armure.<br/>
 * 2. La comparer a la formule de la colonne CA, appliquee a la main.<br/>
 * \tattendu Les treize coincident, y compris le plafond des armures intermediaires et l'absence
 * de bonus des armures lourdes.
 * }
 */
TEST(EquipmentTest, LaCaCalculeeEgaleLaColonneDuLivre) {
    // Dexterite 18 = modificateur +4. C'est le choix qui REVELE la faute : avec +1, appliquer la
    // Dexterite a un harnois donnerait 19 au lieu de 18, un ecart qu'on lit mal ; avec +4, il
    // donne 22, et le plafond +2 des armures intermediaires se distingue nettement du sans-plafond
    // des legeres.
    const core::CharacterSheet fiche = ficheAgile(18);
    const int dexterite = fiche.modifier(core::Ability::Dexterity);
    ASSERT_EQ(dexterite, 4);

    for (const ArmureDuLivre& attendue : ARMURES) {
        if (attendue.dexMax == SANS_DEXTERITE && std::string{attendue.categorie} == "shield") {
            continue;  // Le bouclier a son propre cas, plus bas.
        }
        const core::Armor* armure = catalogue().findArmor(attendue.id);
        ASSERT_NE(armure, nullptr) << attendue.id;

        int attendu = attendue.base;
        if (attendue.dexMax == SANS_PLAFOND) {
            attendu += dexterite;
        } else if (attendue.dexMax != SANS_DEXTERITE) {
            attendu += std::min(dexterite, attendue.dexMax);
        }
        EXPECT_EQ(core::armorClassFor(fiche, regles(), armure, nullptr), attendu)
            << attendue.id << " : la colonne CA du livre dit " << attendue.base
            << (attendue.dexMax == SANS_DEXTERITE ? " sans Dexterite" : " plus Dexterite");
    }
}

/**
 * @brief Le bouclier ajoute, il ne remplace pas.
 * \castest{<b>Un bouclier ajoute son bonus a la classe d'armure, seul ou avec une armure.</b><br/>
 * \tcat Unitaire · Equipement<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Calculer la CA d'un personnage en bouclier seul, puis en harnois et bouclier.<br/>
 * \tattendu Le bouclier seul donne la base sans armure plus la Dexterite plus 2 ; avec le harnois,
 * 18 plus 2.
 * }
 */
TEST(EquipmentTest, LeBouclierAjouteIlNeRemplacePas) {
    const core::CharacterSheet fiche = ficheAgile(18);
    const core::Armor* bouclier = catalogue().findArmor("bouclier");
    const core::Armor* harnois = catalogue().findArmor("harnois");
    ASSERT_NE(bouclier, nullptr);
    ASSERT_NE(harnois, nullptr);

    // Bouclier SEUL, passe en position d'armure : il ne remplace pas la base. Le traiter comme une
    // armure donnerait une CA de 2 a un personnage en bouclier seul.
    EXPECT_EQ(core::armorClassFor(fiche, regles(), bouclier, nullptr),
              regles().unarmoredArmorClass + fiche.modifier(core::Ability::Dexterity));
    EXPECT_EQ(core::armorClassFor(fiche, regles(), nullptr, bouclier),
              regles().unarmoredArmorClass + fiche.modifier(core::Ability::Dexterity) +
                  bouclier->baseArmorClass);
    EXPECT_EQ(core::armorClassFor(fiche, regles(), harnois, bouclier),
              harnois->baseArmorClass + bouclier->baseArmorClass);
}

/**
 * @brief Le poids d'un inventaire de depart correspond au calcul manuel.
 * \castest{<b>Le poids total d'un inventaire de depart egale la somme calculee a la main.</b><br/>
 * \tcat Unitaire · Equipement<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Composer l'inventaire d'un guerrier : cotte de mailles, epee longue, bouclier et
 * deux javelines.<br/>
 * 2. Comparer le total au calcul fait a la main depuis les poids du livre.<br/>
 * \tattendu 27,5 + 1,5 + 3 + 2 x 1 = 34 kg, soit 34 000 g.
 * }
 */
TEST(EquipmentTest, LePoidsDUnInventaireDeDepartCorrespondAuCalculManuel) {
    const core::Armor* cotte = catalogue().findArmor("cotte-de-mailles");
    const core::Armor* bouclier = catalogue().findArmor("bouclier");
    const core::Weapon* epee = catalogue().findWeapon("epee-longue");
    const core::Weapon* javeline = catalogue().findWeapon("javeline");
    ASSERT_NE(cotte, nullptr);
    ASSERT_NE(bouclier, nullptr);
    ASSERT_NE(epee, nullptr);
    ASSERT_NE(javeline, nullptr);

    const std::vector<core::InventoryEntry> sac = {
        {cotte->weightGrams, 1},
        {epee->weightGrams, 1},
        {bouclier->weightGrams, 1},
        {javeline->weightGrams, 2},
    };
    // Calcul manuel depuis la table du livre : 27,5 kg + 1,5 kg + 3 kg + 2 x 1 kg = 34 kg.
    constexpr int TOTAL_ATTENDU_GRAMMES = 34000;
    EXPECT_EQ(core::totalWeightGrams(sac), TOTAL_ATTENDU_GRAMMES);

    // Une quantite nulle ne pese rien -- et une quantite negative non plus, plutot que de retirer
    // du poids au sac.
    const std::vector<core::InventoryEntry> avecVides = {
        {cotte->weightGrams, 1}, {epee->weightGrams, 0}, {bouclier->weightGrams, -3}};
    EXPECT_EQ(core::totalWeightGrams(avecVides), cotte->weightGrams);
    EXPECT_EQ(core::totalWeightGrams({}), 0);
}

/**
 * @brief Le filet n'inflige aucun degat, et le catalogue le dit.
 * \castest{<b>Une arme sans degats est chargee sans que des lui soient inventes.</b><br/>
 * \tcat Unitaire · Equipement<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger le filet et une arme ordinaire.<br/>
 * \tattendu Le filet n'a ni des ni type de degats ; la dague a les deux.
 * }
 */
TEST(EquipmentTest, LeFiletNInfligeAucunDegat) {
    const core::Weapon* filet = catalogue().findWeapon("filet");
    ASSERT_NE(filet, nullptr);
    EXPECT_FALSE(filet->damage.has_value())
        << "une arme a 0 degat se joue comme une arme qui touche pour rien, ce qui est faux : le "
           "filet entrave";
    EXPECT_FALSE(filet->damageType.has_value());
    EXPECT_FALSE(filet->text.empty()) << "ses proprietes disent ce qu'il fait";

    const core::Weapon* dague = catalogue().findWeapon("dague");
    ASSERT_NE(dague, nullptr);
    ASSERT_TRUE(dague->damage.has_value());
    EXPECT_EQ(dague->damage->count, 1);
    EXPECT_EQ(dague->damage->faces, 4);
    ASSERT_TRUE(dague->damageType.has_value());
    EXPECT_EQ(*dague->damageType, core::DamageType::Piercing);
}

/**
 * @brief Les armes portent leur categorie et leur portee, qui viennent des intertitres.
 * \castest{<b>Chaque arme porte la categorie et la portee de son intertitre.</b><br/>
 * \tcat Unitaire · Equipement<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Verifier la categorie et la portee de quatre armes, une par groupe du livre.<br/>
 * \tattendu Baton courante au corps a corps, fronde courante a distance, rapiere de guerre au
 * corps a corps, arc long de guerre a distance.
 * }
 */
TEST(EquipmentTest, LesArmesPortentLeurCategorieEtLeurPortee) {
    // La categorie ne figure PAS dans la rangee : elle vient de l'intertitre du livre. Une
    // extraction qui ne lirait que les rangees produirait 37 armes sans categorie -- ce qu'aucun
    // schema ne refuserait, `category` etant requis sans que rien ne dise qu'il est juste.
    struct Attendu {
        const char* id;
        const char* categorie;
        bool distance;
    };
    for (const Attendu& cas : std::to_array<Attendu>({{"baton", "simple", false},
                                                      {"fronde", "simple", true},
                                                      {"rapiere", "martial", false},
                                                      {"arc-long", "martial", true}})) {
        const core::Weapon* arme = catalogue().findWeapon(cas.id);
        ASSERT_NE(arme, nullptr) << cas.id;
        EXPECT_EQ(arme->category, cas.categorie) << cas.id;
        EXPECT_EQ(arme->ranged, cas.distance) << cas.id;
    }
}
