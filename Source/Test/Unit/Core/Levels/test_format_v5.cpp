// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_format_v5.cpp
 * @brief Tests unitaires du format de carte v5, `jadg-map` (`LOT-1018`) : ce que Core lit d'une
 *        description de carte du moteur — les étages praticables (D-51), l'étage de chaque entité,
 *        les volumes en mètres —, ce qu'il refuse, et ce que l'exploration en joue.
 */

#include <filesystem>
#include <fstream>
#include <map>
#include <optional>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>

#include <gtest/gtest.h>

#include "Core/Levels/Level.h"
#include "Core/Levels/LevelLoader.h"
#include "Core/Levels/MapEntity.h"
#include "Core/World/CombatZone.h"
#include "Core/World/ExplorationSession.h"
#include "Core/World/FollowTrail.h"
#include "Core/World/WorldTravel.h"

namespace {

using core::GridPosition;

const std::filesystem::path FIXTURES = std::filesystem::path{JADG_TEST_FIXTURES_DIR} / "Levels";
const std::filesystem::path ELEMENTS{JADG_ELEMENTS_DIR};
constexpr std::string_view ARENA_OF_FATE = "central-empire/capital/arenarea/arena-of-fate";

[[nodiscard]] std::string lire(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary);
    std::ostringstream buffer;
    buffer << file.rdbuf();
    return buffer.str();
}

[[nodiscard]] core::Level chargerV5() {
    core::LevelLoadResult loaded = core::LevelLoader::loadFromFile(FIXTURES / "format-v5.json");
    EXPECT_TRUE(loaded.ok()) << loaded.error;
    return std::move(*loaded.level);
}

[[nodiscard]] const core::MapEntity& entite(const core::Level& level, std::string_view id) {
    for (const core::MapEntity& entity : level.entities()) {
        if (entity.id == id) {
            return entity;
        }
    }
    ADD_FAILURE() << "entite absente : " << id;
    return level.entities().front();
}

// Une carte v5 minimale, ou l'on remplace une ligne pour la rendre fautive.
[[nodiscard]] std::string carteV5(const std::string& extra, const std::string& entity = {}) {
    return R"({"format": "jadg-map", "version": 5, "name": "x", "width": 3, "height": 3, )" +
           extra + R"("tiles": [{"x": 0, "y": 0, "type": "entry"}], "entities": [)" + entity + "]}";
}

// La carte v5 de la fixture et la carte ou mene son portail.
[[nodiscard]] core::WorldTravel::MapLoader chargeur() {
    return [](std::string_view mapId) {
        if (mapId == "v5") {
            return core::LevelLoader::loadFromFile(FIXTURES / "format-v5.json");
        }
        return core::LevelLoader::loadFromString(R"({"version": 4, "name": "ailleurs",
          "width": 3, "height": 3, "tiles": [{"x": 0, "y": 0, "type": "entry"}],
          "entities": [{"id": "e1", "type": "spawnPoint", "x": 1, "y": 1, "name": "porte"}]})");
    };
}

[[nodiscard]] bool aEntre(const std::vector<core::ExplorationEvent>& events, std::string_view map) {
    for (const core::ExplorationEvent& event : events) {
        if (event.kind == core::ExplorationEventKind::MapEntered && event.value == map) {
            return true;
        }
    }
    return false;
}

[[nodiscard]] std::vector<core::ExplorationEvent> mene(core::ExplorationSession& session,
                                                       float column, float row, int storey) {
    core::ExplorationIntent intent;
    intent.carried = core::CellPoint{.column = column, .row = row};
    intent.storey = storey;
    return session.update(intent, 1.0F / 30.0F);
}

}  // namespace

/**
 * @brief Une description de carte v5 se lit : ses étages, l'étage et le volume de ses entités,
 *        ramenés au repère de la grille par son origine (`EX-LVL-031`, `EX-LVL-032`, `EX-LVL-033`).
 * \castest{<b>Une carte v5 se lit, étages et volumes compris.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Charger `format-v5.json` (deux étages, origine en (3 ; -1,5) m).<br/>
 * \tattendu Deux étages, le rez à 0 m et l'étage à 3 m ; le panneau est à l'étage 1, le portail au
 * rez ; le volume de la zone de combat commence au coin de la grille (0 ; 0 ; -0,5) m.
 * }
 */
TEST(FormatV5Test, UneCarteV5SeLitEtagesEtVolumesCompris) {
    const core::Level level = chargerV5();
    ASSERT_EQ(level.storeys().size(), 2U);
    EXPECT_EQ(level.storeys()[0], (core::Storey{.name = "rez", .z = 0.0F}));
    EXPECT_EQ(level.storeys()[1], (core::Storey{.name = "etage", .z = 3.0F}));
    EXPECT_EQ(level.entry(), (GridPosition{0, 0}));
    EXPECT_EQ(entite(level, "e1").storey, 0);
    EXPECT_EQ(entite(level, "e2").storey, 1);
    ASSERT_TRUE(entite(level, "e4").volume.has_value());
    const core::MapVolume volume = *entite(level, "e4").volume;
    EXPECT_FLOAT_EQ(volume.minX, 0.0F);
    EXPECT_FLOAT_EQ(volume.minY, 0.0F);
    EXPECT_FLOAT_EQ(volume.minZ, -0.5F);
    EXPECT_FLOAT_EQ(volume.maxX, 6.0F);
    EXPECT_FLOAT_EQ(volume.maxY, 6.0F);
    EXPECT_FLOAT_EQ(volume.maxZ, 3.0F);
    EXPECT_FALSE(entite(level, "e1").volume.has_value());
}

/**
 * @brief Les sections de construction (terrain, objets, lumières, notes) ne sont pas des
 *        propriétés de carte : Core les passe ; une couche garde sa hauteur en mètres et une entité
 *        ce que la scène lit d'elle (apparence, cap) (`EX-LVL-031`).
 * \castest{<b>Core passe les sections de construction d'une v5.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger `format-v5.json`.<br/>
 * \tattendu Ni `place`, ni `comment`, ni `terrain` dans les propriétés de la carte ; la couche
 * `toit` porte `z` = 3 ; le PNJ porte `appearance` et `heading`.
 * }
 */
TEST(FormatV5Test, CorePasseLesSectionsDeConstruction) {
    const core::Level level = chargerV5();
    for (const char* cle : {"place", "comment", "terrain", "objects", "format", "origin"}) {
        EXPECT_FALSE(level.properties().contains(cle)) << cle;
    }
    bool toit = false;
    for (const core::TileLayer& layer : level.layers()) {
        if (layer.name == "toit") {
            toit = true;
            ASSERT_TRUE(layer.properties.contains("z"));
            EXPECT_DOUBLE_EQ(std::get<double>(layer.properties.at("z")), 3.0);
        }
    }
    EXPECT_TRUE(toit);
    const core::MapEntity& pnj = entite(level, "e6");
    EXPECT_EQ(std::get<std::string>(pnj.properties.at("appearance")), "pantin");
    EXPECT_DOUBLE_EQ(std::get<double>(pnj.properties.at("heading")), 90.0);
}

/**
 * @brief Ce que la v5 refuse : une carte qui ne se déclare pas, les réserves de la v4, un étage
 *        absent, des étages mal ordonnés, un volume retourné, une variante.
 * \castest{<b>Une v5 fautive est refusée avec sa raison.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger sept cartes v5 fautives.<br/>
 * \tattendu Chacune est refusée (`ParseError` ou `OutOfBounds`), le message nomme la faute.
 * }
 */
TEST(FormatV5Test, UneV5FautiveEstRefuseeAvecSaRaison) {
    struct Cas {
        std::string json;
        core::LevelValidationError code;
        std::string mot;
    };
    const std::vector<Cas> cas{
        {R"({"version": 5, "name": "x", "width": 1, "height": 1,
             "tiles": [{"x": 0, "y": 0, "type": "entry"}]})",
         core::LevelValidationError::ParseError, "format"},
        {carteV5("", R"({"id": "e1", "type": "npc", "x": 1, "y": 1, "elevation": 2})"),
         core::LevelValidationError::ParseError, "elevation"},
        {carteV5(R"("layers": [{"name": "t", "kind": "decor", "floor": 1, "tiles": []}], )"),
         core::LevelValidationError::ParseError, "floor"},
        {carteV5("", R"({"id": "e1", "type": "npc", "x": 1, "y": 1, "storey": 1})"),
         core::LevelValidationError::OutOfBounds, "etage"},
        {carteV5(R"("storeys": [{"name": "a", "z": 0.0}, {"name": "b", "z": 0.0}], )"),
         core::LevelValidationError::ParseError, "storeys"},
        {carteV5("", R"({"id": "e1", "type": "zone", "x": 1, "y": 1,
                         "volume": {"min": [2, 2, 0], "max": [1, 3, 1]}})"),
         core::LevelValidationError::ParseError, "volume"},
        {R"({"format": "jadg-map", "version": 5, "name": "x", "base": "y", "entities": []})",
         core::LevelValidationError::ParseError, "Variante"},
    };
    for (const Cas& un : cas) {
        SCOPED_TRACE(un.json);
        const core::LevelLoadResult loaded = core::LevelLoader::loadFromString(un.json);
        ASSERT_FALSE(loaded.ok());
        EXPECT_EQ(loaded.errorCode, un.code);
        EXPECT_NE(loaded.error.find(un.mot), std::string::npos) << loaded.error;
    }
}

/**
 * @brief Un lieu à sous-sols est une carte : le rez en tête à 0 m, puis ses sous-sols, chacun à sa
 *        hauteur négative ; un point d'arrivée du sous-sol y pose le héros (`EX-LVL-032`,
 * LOT-1022).
 * \castest{<b>Une carte v5 à sous-sols se lit.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger une carte dont le rez est à 0 m, un sous-sol à -5,5 m et un second à
 * -11,5 m, un point d'arrivée au second.<br/>
 * 2. Charger la même carte, le rez à -5,5 m en tête.<br/>
 * 3. Charger la même carte, deux sous-sols à -5,5 m.<br/>
 * \tattendu 1. Trois étages, dans l'ordre écrit ; le point d'arrivée est à l'étage 2, et y pose
 * le héros. 2. et 3. Refusées, le message nomme `storeys`.
 * }
 */
TEST(FormatV5Test, UneCarteASousSolsSeLit) {
    const std::string sousSols =
        R"("storeys": [{"name": "sable", "z": 0.0}, {"name": "vestiaires", "z": -5.5},
                       {"name": "catacombes", "z": -11.5}], )";
    const std::string arrivee =
        R"({"id": "e1", "type": "spawnPoint", "x": 2, "y": 2, "storey": 2, "name": "bas"})";
    const core::LevelLoadResult loaded =
        core::LevelLoader::loadFromString(carteV5(sousSols, arrivee));
    ASSERT_TRUE(loaded.ok()) << loaded.error;
    const core::Level& level = *loaded.level;
    ASSERT_EQ(level.storeys().size(), 3U);
    EXPECT_EQ(level.storeys()[1], (core::Storey{.name = "vestiaires", .z = -5.5F}));
    EXPECT_EQ(level.storeys()[2], (core::Storey{.name = "catacombes", .z = -11.5F}));
    EXPECT_EQ(core::arrivalStoreyAt(level, "bas"), 2);

    for (const std::string& fautive :
         {std::string{R"("storeys": [{"name": "a", "z": -5.5}, {"name": "b", "z": 0.0}], )"},
          std::string{R"("storeys": [{"name": "a", "z": 0.0}, {"name": "b", "z": -5.5},
                                     {"name": "c", "z": -5.5}], )"}}) {
        SCOPED_TRACE(fautive);
        const core::LevelLoadResult refusee = core::LevelLoader::loadFromString(carteV5(fautive));
        ASSERT_FALSE(refusee.ok());
        EXPECT_NE(refusee.error.find("storeys"), std::string::npos) << refusee.error;
    }
}

/**
 * @brief Les cases d'un volume sont celles dont le centre tombe dans son emprise au sol ; un volume
 *        plus étroit qu'une case garde la case de son centre.
 * \castest{<b>Un volume se ramène aux cases de son emprise.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Ramener un volume de 0 à 6 m sur 0 à 4,5 m, puis un volume de 0,5 m de côté.<br/>
 * \tattendu Quatre colonnes sur trois lignes depuis (0, 0) ; puis la seule case du centre.
 * }
 */
TEST(FormatV5Test, UnVolumeSeRameneAuxCasesDeSonEmprise) {
    const core::VolumeCells large = core::volumeCells(core::MapVolume{
        .minX = 0.0F, .minY = 0.0F, .minZ = 0.0F, .maxX = 6.0F, .maxY = 4.5F, .maxZ = 2.0F});
    EXPECT_EQ(large.origin, (GridPosition{0, 0}));
    EXPECT_EQ(large.columns, 4);
    EXPECT_EQ(large.rows, 3);
    const core::VolumeCells etroit = core::volumeCells(core::MapVolume{
        .minX = 3.1F, .minY = 1.6F, .minZ = 0.0F, .maxX = 3.6F, .maxY = 2.1F, .maxZ = 1.0F});
    EXPECT_EQ(etroit.origin, (GridPosition{2, 1}));
    EXPECT_EQ(etroit.columns, 1);
    EXPECT_EQ(etroit.rows, 1);
}

/**
 * @brief Une zone de combat v5 est un volume (`LOT-1017`, `LOT-1018`, `EX-LVL-033`) : le montage
 *        d'une rencontre en tire sa grille tactique.
 * \castest{<b>Une zone de combat v5 se lit de son volume.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger `format-v5.json`.<br/>2. Lire ses zones de combat.<br/>
 * \tattendu Une zone « cour », de (0, 0), quatre colonnes sur quatre lignes : les cases dont le
 * centre est dans le volume, pas les propriétés `width` et `height` qu'elle n'a pas.
 * }
 */
TEST(FormatV5Test, UneZoneDeCombatV5SeLitDeSonVolume) {
    const std::vector<core::CombatZone> zones = core::combatZonesOf(chargerV5());
    ASSERT_EQ(zones.size(), 1U);
    EXPECT_EQ(zones[0].name, "cour");
    EXPECT_EQ(zones[0].origin, (GridPosition{0, 0}));
    EXPECT_EQ(zones[0].columns, 4);
    EXPECT_EQ(zones[0].rows, 4);
}

/**
 * @brief Deux étages superposés (D-51, `EX-LVL-032`) : à la verticale du portail du rez, le héros
 *        de l'étage ne le franchit pas ; redescendu sur la même case, il le franchit.
 * \castest{<b>Un portail du rez ne se franchit pas depuis l'étage.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Ouvrir `format-v5.json` à l'entrée.<br/>2. Mener le héros sur la case du portail, à
 * l'étage 1.<br/>3. Le redescendre au rez sur la même case.<br/>
 * \tattendu Rien à l'étage ; au rez, la carte « ailleurs » s'ouvre.
 * }
 */
TEST(FormatV5Test, UnPortailDuRezNeSeFranchitPasDepuisLEtage) {
    core::ExplorationSession session{chargeur()};
    ASSERT_TRUE(session.start("v5", ""));
    EXPECT_EQ(session.heroStorey(), 0);
    EXPECT_FALSE(aEntre(mene(session, 2.5F, 1.5F, 1), "ailleurs"));
    EXPECT_EQ(session.heroStorey(), 1);
    EXPECT_TRUE(aEntre(mene(session, 2.5F, 1.5F, 0), "ailleurs"));
}

/**
 * @brief Ce qui est à l'étage se sollicite de l'étage : le panneau posé au-dessus du portail n'est
 *        désigné que d'un héros à l'étage 1.
 * \castest{<b>Un panneau de l'étage ne se désigne que de l'étage.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mener le héros face au panneau, au rez.<br/>2. Le mener au même point, à
 * l'étage 1.<br/>
 * \tattendu Au rez, aucune cible ; à l'étage, le panneau.
 * }
 */
TEST(FormatV5Test, UnPanneauDeLEtageNeSeDesigneQueDeLEtage) {
    core::ExplorationSession session{chargeur()};
    ASSERT_TRUE(session.start("v5", ""));
    static_cast<void>(mene(session, 0.6F, 1.5F, 0));
    static_cast<void>(mene(session, 1.5F, 1.5F, 0));
    EXPECT_FALSE(session.interactionTarget().has_value());
    static_cast<void>(mene(session, 1.5F, 1.5F, 1));
    const std::optional<core::Interactable> cible = session.interactionTarget();
    ASSERT_TRUE(cible.has_value());
    EXPECT_EQ(cible->type, "sign");
}

/**
 * @brief L'Arena of Fate livrée est une carte à trois étages (LOT-1022) : on y entre d'Arenarea au
 *        vestibule des vestiaires (niveau −1), et un portail de la v4 entre deux niveaux mène
 *        désormais à un autre étage de la même carte.
 * \castest{<b>L'Arena of Fate est une carte à trois étages.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger l'Arena of Fate du contenu livré.<br/>2. Y entrer par « from-arenarea ».<br/>
 * 3. Mener le héros, à l'étage 1, sur le portail de la porte du triomphe (4, 12).<br/>
 * \tattendu Trois étages, le sable à 0 m et deux sous-sols en dessous ; le héros arrive au
 * vestibule (16, 19), à l'étage 1 ; le portail le pose au sable (6, 12), à l'étage 0, sur la même
 * carte.
 * }
 */
TEST(FormatV5Test, LArenaOfFateEstUneCarteATroisEtages) {
    const core::WorldTravel::MapLoader charge =
        core::WorldTravel::directoriesLoader({ELEMENTS / "Levels"});
    const core::LevelLoadResult loaded = charge(ARENA_OF_FATE);
    ASSERT_TRUE(loaded.ok()) << loaded.error;
    const std::vector<core::Storey>& etages = loaded.level->storeys();
    ASSERT_EQ(etages.size(), 3U);
    EXPECT_EQ(etages[0].z, 0.0F);
    EXPECT_LT(etages[1].z, 0.0F);
    EXPECT_LT(etages[2].z, etages[1].z);

    core::ExplorationSession session{charge};
    ASSERT_TRUE(session.start(std::string{ARENA_OF_FATE}, "from-arenarea"));
    EXPECT_EQ(session.heroCell(), (GridPosition{16, 19}));
    EXPECT_EQ(session.heroStorey(), 1);
    static_cast<void>(mene(session, 5.5F, 12.5F, 1));
    EXPECT_TRUE(aEntre(mene(session, 4.5F, 12.5F, 1), ARENA_OF_FATE));
    EXPECT_EQ(session.heroCell(), (GridPosition{6, 12}));
    EXPECT_EQ(session.heroStorey(), 0);
}

/**
 * @brief Un point d'arrivée à l'étage pose le héros à l'étage.
 * \castest{<b>On arrive à l'étage de son point d'arrivée.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Entrer dans `format-v5.json` par le point d'arrivée « palier ».<br/>
 * \tattendu Le héros est en (3, 1), à l'étage 1.
 * }
 */
TEST(FormatV5Test, OnArriveALEtageDeSonPointDArrivee) {
    core::ExplorationSession session{chargeur()};
    ASSERT_TRUE(session.start("v5", "palier"));
    EXPECT_EQ(session.heroCell(), (GridPosition{3, 1}));
    EXPECT_EQ(session.heroStorey(), 1);
}

/**
 * @brief La trace du groupe porte la hauteur de chaque pas (D-51) : un suiveur à une case derrière
 *        le meneur qui monte se tient à la hauteur de ce point-là, pas au sol.
 * \castest{<b>La trace du groupe suit en hauteur.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Tracer quatre pas d'une case, de 0 à 300 de hauteur.<br/>2. Lire la hauteur à une
 * case et demie derrière le meneur.<br/>
 * \tattendu 150, à mi-chemin des pas à 100 et à 200 ; 0 sur une trace tracée sans hauteur.
 * }
 */
TEST(FormatV5Test, LaTraceDuGroupeSuitEnHauteur) {
    core::FollowTrail trail;
    trail.reset({core::TrailPoint{0.0F, 0.0F}});
    trail.record(core::TrailPoint{1.0F, 0.0F}, 100.0F);
    trail.record(core::TrailPoint{2.0F, 0.0F}, 200.0F);
    trail.record(core::TrailPoint{3.0F, 0.0F}, 300.0F);
    EXPECT_FLOAT_EQ(trail.heightBehind(1.5F), 150.0F);
    EXPECT_FLOAT_EQ(trail.heightBehind(0.0F), 300.0F);
    EXPECT_FLOAT_EQ(trail.heightBehind(10.0F), 0.0F);
    core::FollowTrail plat;
    plat.reset({core::TrailPoint{0.0F, 0.0F}});
    plat.record(core::TrailPoint{1.0F, 0.0F});
    EXPECT_FLOAT_EQ(plat.heightBehind(0.5F), 0.0F);
}

/**
 * @brief Une v4 se lit toujours sous la v5 (`EX-LVL-005`, `EX-LVL-039`) : elle n'a ni étage ni
 *        volume.
 * \castest{<b>Une v4 se lit sans étage ni volume.</b><br/>
 * \tcat Unitaire · Format v5<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Charger `format-v4.json`.<br/>
 * \tattendu Aucun étage déclaré ; chaque entité au rez, sans volume.
 * }
 */
TEST(FormatV5Test, UneV4SeLitSansEtageNiVolume) {
    const core::LevelLoadResult loaded =
        core::LevelLoader::loadFromString(lire(FIXTURES / "format-v4.json"));
    ASSERT_TRUE(loaded.ok()) << loaded.error;
    EXPECT_TRUE(loaded.level->storeys().empty());
    for (const core::MapEntity& entity : loaded.level->entities()) {
        EXPECT_EQ(entity.storey, 0);
        EXPECT_FALSE(entity.volume.has_value());
    }
}
