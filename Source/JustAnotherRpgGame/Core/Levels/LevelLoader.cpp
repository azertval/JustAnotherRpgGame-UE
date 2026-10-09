// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Levels/LevelLoader.h"

#include <algorithm>
#include <fstream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <nlohmann/json.hpp>

#include "Core/Data/JsonDocument.h"
#include "Core/Levels/LevelVariant.h"
#include "Core/Levels/LevelsLog.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Levels/TileLayer.h"
#include "Core/Levels/TileMap.h"
#include "Core/Levels/TileType.h"
#include "Core/Levels/TileTypeName.h"

namespace core {

namespace {

// Premiere version ou la grille racine ne porte plus d'assignation de texture (LOT-EDITOR-12).
constexpr int PIECES_ON_LAYERS_VERSION = 4;

// Premiere version a etre une description de carte du moteur (LOT-1018) : etages, volumes, et les
// sections que la construction lit et que Core ignore.
constexpr int SCENE_FORMAT_VERSION = 5;

// Ce qu'une carte v5 declare en tete : le format, pour qu'un JSON quelconque ne passe pas pour une
// carte.
constexpr const char* SCENE_FORMAT_NAME = "jadg-map";

// Nom de la couche de decor creee pour recevoir les assignations d'une carte v3 qui n'en a pas.
constexpr const char* MIGRATED_RELIEF_LAYER_NAME = "relief";

// Construit un résultat d'échec avec un message et un code categorise (EX-EDIT-012).
// Journalise systematiquement la raison ici (point unique) : chaque site d'appel n'a pas a le
// refaire, et un echec de chargement reste tracable meme hors du contexte HMI (tests, outillage).
[[nodiscard]] LevelLoadResult failure(std::string message, LevelValidationError code) {
    LEVELS_LOG_WARNING("Echec du chargement : " + message);
    return LevelLoadResult{.level = std::nullopt, .error = std::move(message), .errorCode = code};
}

[[nodiscard]] std::string cellText(int x, int y) {
    return "(" + std::to_string(x) + ", " + std::to_string(y) + ")";
}

// --- Couches et entites (LOT-04, format version 3 et suivantes) ------------------------------

// Role d'une couche d'apres son champ "kind". Valeur de conception par defaut (Ground) si absent
// ou non reconnu -- meme tolerance que le reste du format (EX-NFR-040) : une couche au role
// inconnu s'affiche, elle ne fait pas echouer le chargement de la carte entiere.
[[nodiscard]] LayerKind parseLayerKind(const nlohmann::json& layer) {
    const std::string name = layer.value("kind", std::string{"ground"});
    for (int raw = 0; raw < LAYER_KIND_COUNT; ++raw) {
        const auto kind = static_cast<LayerKind>(raw);
        if (layerKindName(kind) == name) {
            return kind;
        }
    }
    return LayerKind::Ground;
}

// Range dans @p properties toute cle de @p object qui n'est pas dans @p known.
//
// Une cle inconnue n'est ni rejetee (elle ferait echouer un fichier produit par une version
// ulterieure) ni perdue (l'editeur la ferait disparaitre au premier enregistrement) : elle est
// conservee telle quelle et reemise.
//
// Les valeurs COMPOSITES (objet, tableau) n'entrent pas dans core::PropertyValue et sont ignorees
// -- limite documentee sur core::PropertyMap.
void collectProperties(const nlohmann::json& object, const std::set<std::string>& known,
                       PropertyMap& properties) {
    for (const auto& [key, value] : object.items()) {
        if (known.contains(key)) {
            continue;
        }
        if (value.is_boolean()) {
            properties[key] = value.get<bool>();
        } else if (value.is_number_integer()) {
            properties[key] = value.get<std::int64_t>();
        } else if (value.is_number_float()) {
            properties[key] = value.get<double>();
        } else if (value.is_string()) {
            properties[key] = value.get<std::string>();
        }
    }
}

// Les cles racine que le chargeur connait : tout le reste devient une propriete de carte
// (LOT-EDITOR-09), gardee telle quelle et reemise.
[[nodiscard]] const std::set<std::string>& knownRootKeys() {
    static const std::set<std::string> known{"version",      "name",   "width",    "height",
                                             "tiles",        "layers", "entities", "forced",
                                             "nextEntityId", "base",   "scene"};
    return known;
}

// Les cles racine d'une carte v5 que Core lit (format, origine, etages) ou que seule la
// construction du niveau lit (`scripts/maps/build_level.py`) : le terrain, les objets, les
// prefabriques, les lumieres, le ciel, la navigation, le groupe, les cadrages, les notes. Core les
// passe sans les ranger : ce ne sont pas des proprietes de carte, et l'ecriture d'une v5 est celle
// de `scripts/maps/jadg_map.py`, qui les garde.
[[nodiscard]] const std::set<std::string>& sceneRootKeys() {
    static const std::set<std::string> known{
        "format",   "origin",     "storeys",    "place",       "comment",  "terrain",
        "objects",  "fills",      "prefabs",    "routes",      "outlines", "lighting",
        "daylight", "ground",     "navigation", "party",       "shots",    "hours",
        "notes",    "assetsRoot", "characters", "storeyLevels"};
    return known;
}

// Les cles racine connues pour la version @p version.
[[nodiscard]] std::set<std::string> rootKeysFor(int version) {
    std::set<std::string> known = knownRootKeys();
    if (version >= SCENE_FORMAT_VERSION) {
        known.insert(sceneRootKeys().begin(), sceneRootKeys().end());
    }
    return known;
}

// Un nombre JSON, entier ou reel.
[[nodiscard]] float numberOf(const nlohmann::json& value, const std::string& where) {
    if (!value.is_number()) {
        throw std::invalid_argument(where + " : nombre attendu");
    }
    return value.get<float>();
}

// L'origine d'une carte v5 : ou tombe le coin de la case (0, 0), en metres, dans le repere de la
// carte. Absente : a l'origine.
struct SceneOrigin {
    float x = 0.0F;
    float y = 0.0F;
};

[[nodiscard]] SceneOrigin parseOrigin(const nlohmann::json& root) {
    if (!root.contains("origin")) {
        return {};
    }
    const nlohmann::json& origin = root.at("origin");
    if (!origin.is_array() || origin.size() != 2) {
        throw std::invalid_argument("'origin' : deux nombres attendus (x, y en metres)");
    }
    return SceneOrigin{.x = numberOf(origin[0], "origin"), .y = numberOf(origin[1], "origin")};
}

// Les etages d'une carte v5 (D-51) : le rez en tete, a la hauteur 0, puis les autres, chacun a sa
// hauteur -- au-dessus pour un etage, en dessous pour un sous-sol (les catacombes de l'Arena of
// Fate, LOT-1022) --, jamais deux a la meme.
[[nodiscard]] std::vector<Storey> parseStoreys(const nlohmann::json& root) {
    std::vector<Storey> storeys;
    if (!root.contains("storeys")) {
        return storeys;
    }
    if (!root.at("storeys").is_array()) {
        throw std::invalid_argument("'storeys' doit etre une liste");
    }
    for (const nlohmann::json& storey : root.at("storeys")) {
        Storey parsed{.name = storey.value("name", std::string{}),
                      .z = numberOf(storey.at("z"), "storeys.z")};
        const bool deja = std::ranges::any_of(
            storeys, [&parsed](const Storey& autre) { return autre.z == parsed.z; });
        if (storeys.empty() ? parsed.z != 0.0F : deja) {
            throw std::invalid_argument(
                "'storeys' : le rez en tete a la hauteur 0, puis chaque etage ou sous-sol a "
                "la sienne, jamais deux a la meme");
        }
        storeys.push_back(std::move(parsed));
    }
    return storeys;
}

// Le volume d'une entite v5, ramene du repere de la carte a celui de la grille.
[[nodiscard]] MapVolume parseVolume(const nlohmann::json& volume, SceneOrigin origin) {
    const nlohmann::json& low = volume.at("min");
    const nlohmann::json& high = volume.at("max");
    if (!low.is_array() || !high.is_array() || low.size() != 3 || high.size() != 3) {
        throw std::invalid_argument("'volume' : min et max, trois nombres chacun");
    }
    MapVolume parsed{.minX = numberOf(low[0], "volume") - origin.x,
                     .minY = numberOf(low[1], "volume") - origin.y,
                     .minZ = numberOf(low[2], "volume"),
                     .maxX = numberOf(high[0], "volume") - origin.x,
                     .maxY = numberOf(high[1], "volume") - origin.y,
                     .maxZ = numberOf(high[2], "volume")};
    if (parsed.maxX <= parsed.minX || parsed.maxY <= parsed.minY || parsed.maxZ <= parsed.minZ) {
        throw std::invalid_argument("'volume' : chaque cote de max depasse celui de min");
    }
    return parsed;
}

// Ce qu'une entite v5 ajoute a la v4 : son etage et son volume.
struct SceneContext {
    int version = 0;
    SceneOrigin origin{};
    std::size_t storeyCount = 0;
};

// Une case {x, y} d'une liste de cases ("forced", "cells"), bornee a la carte.
[[nodiscard]] std::optional<LevelLoadResult> parseCell(const nlohmann::json& cell,
                                                       const TileMap& map, const std::string& where,
                                                       GridPosition& position) {
    position = GridPosition{.column = cell.at("x").get<int>(), .row = cell.at("y").get<int>()};
    if (!map.inBounds(position.column, position.row)) {
        return failure(
            "Case hors bornes dans " + where + " en " + cellText(position.column, position.row),
            LevelValidationError::OutOfBounds);
    }
    return std::nullopt;
}

// Une case d'une couche : son type, sa piece et sa hauteur (format v4).
[[nodiscard]] std::optional<LevelLoadResult> parseLayerTile(const nlohmann::json& tile,
                                                            TileLayer& layer, int version) {
    const int x = tile.at("x").get<int>();
    const int y = tile.at("y").get<int>();
    if (!layer.tiles.inBounds(x, y)) {
        return failure("Tuile hors bornes dans la couche '" + layer.name + "' en " + cellText(x, y),
                       LevelValidationError::OutOfBounds);
    }
    const std::optional<TileType> type = parseTileType(tile.at("type").get<std::string>());
    if (!type) {
        return failure("Type de tuile inconnu dans la couche '" + layer.name +
                           "' : " + tile.at("type").get<std::string>(),
                       LevelValidationError::UnknownTileType);
    }
    layer.tiles.setTile(x, y, *type);
    if (tile.contains("piece")) {
        layer.setPiece(x, y, tile.at("piece").get<std::string>());
    }
    if (tile.contains("elevation")) {
        // La hauteur reservee de la v4 tombe avec elle (D-51) : une v5 pose ses objets en metres.
        if (version >= SCENE_FORMAT_VERSION) {
            return failure(
                "'elevation' dans une carte v5 : la hauteur reservee de la v4 tombe "
                "avec elle (D-51) ; une piece se pose en metres ('z' de la couche)",
                LevelValidationError::ParseError);
        }
        layer.setElevation(x, y, tile.at("elevation").get<int>());
    }
    return std::nullopt;
}

// Traite le tableau racine optionnel "layers" (LOT-04). Absent = carte version 2, dont la grille
// unique est promue par l'appelant. Chaque couche porte sa propre grille, aux MEMES dimensions que
// la carte : une couche decalee d'une case rendrait la collision incoherente avec l'affichage,
// d'ou le refus plutot qu'un redimensionnement silencieux.
[[nodiscard]] std::optional<LevelLoadResult> parseLayers(const nlohmann::json& root, int width,
                                                         int height, int version,
                                                         std::vector<TileLayer>& layers) {
    if (!root.contains("layers")) {
        return std::nullopt;
    }
    if (!root.at("layers").is_array()) {
        return failure("Le champ 'layers' doit etre une liste", LevelValidationError::ParseError);
    }
    static const std::set<std::string> known{"name", "kind", "tiles", "floor"};
    for (const nlohmann::json& layerJson : root.at("layers")) {
        if (version >= SCENE_FORMAT_VERSION && layerJson.contains("floor")) {
            return failure(
                "'floor' dans une couche d'une carte v5 : l'etage de decor de la v4 tombe "
                "avec elle (D-51) ; la couche se pose a sa hauteur ('z', en metres)",
                LevelValidationError::ParseError);
        }
        TileLayer layer{.name = layerJson.value("name", std::string{}),
                        .kind = parseLayerKind(layerJson),
                        .tiles = TileMap(width, height),
                        .properties = {},
                        .floor = layerJson.value("floor", 0)};
        if (layerJson.contains("tiles")) {
            if (!layerJson.at("tiles").is_array()) {
                return failure("Le champ 'tiles' d'une couche doit etre une liste",
                               LevelValidationError::ParseError);
            }
            for (const nlohmann::json& tile : layerJson.at("tiles")) {
                if (std::optional<LevelLoadResult> error = parseLayerTile(tile, layer, version)) {
                    return error;
                }
            }
        }
        // Une couche 'collision' DECLAREE est refusee : la collision d'une carte est son tableau
        // racine "tiles", et l'accepter ici creerait une seconde grille a tenir d'accord avec la
        // premiere -- celle ou vit l'entree (EX-LVL-016, EX-NFR-040).
        if (layer.kind == LayerKind::Collision) {
            return failure(
                "Couche 'collision' declaree dans 'layers' : la grille de collision "
                "d'une carte est son tableau racine 'tiles'",
                LevelValidationError::ParseError);
        }
        collectProperties(layerJson, known, layer.properties);
        layers.push_back(std::move(layer));
    }
    return std::nullopt;
}

// Traite le tableau racine optionnel "entities" (LOT-04). Core n'attribue AUCUNE semantique au
// champ "type" : c'est le gameplay qui l'interprete, et une entite de type inconnu est une erreur
// de conception toleree plutot qu'une carte invalide (EX-NFR-040). Un identifiant, lui, est unique
// (decision D8) : deux entites du meme id rendraient ambigue toute reference `carte#id`.
[[nodiscard]] std::optional<LevelLoadResult> parseEntities(const nlohmann::json& root,
                                                           const TileMap& map,
                                                           const SceneContext& scene,
                                                           std::vector<MapEntity>& entities) {
    if (!root.contains("entities")) {
        return std::nullopt;
    }
    if (!root.at("entities").is_array()) {
        return failure("Le champ 'entities' doit etre une liste", LevelValidationError::ParseError);
    }
    static const std::set<std::string> known{"id",        "type",  "x",      "y",
                                             "elevation", "cells", "storey", "volume"};
    std::set<std::string> ids;
    for (const nlohmann::json& entityJson : root.at("entities")) {
        MapEntity entity{.type = entityJson.value("type", std::string{}),
                         .position = GridPosition{.column = entityJson.value("x", 0),
                                                  .row = entityJson.value("y", 0)},
                         .properties = {},
                         .id = entityJson.value("id", std::string{}),
                         .elevation = entityJson.value("elevation", 0),
                         .cells = {}};
        if (!map.inBounds(entity.position.column, entity.position.row)) {
            return failure(
                "Entite hors bornes en " + cellText(entity.position.column, entity.position.row),
                LevelValidationError::OutOfBounds);
        }
        if (scene.version >= SCENE_FORMAT_VERSION) {
            if (entityJson.contains("elevation")) {
                return failure("'elevation' sur l'entite '" + entity.id +
                                   "' d'une carte v5 : son etage se dit par 'storey' (D-51)",
                               LevelValidationError::ParseError);
            }
            entity.storey = entityJson.value("storey", 0);
            const std::size_t storeys = std::max<std::size_t>(1, scene.storeyCount);
            if (entity.storey < 0 || static_cast<std::size_t>(entity.storey) >= storeys) {
                return failure("L'entite '" + entity.id + "' est a l'etage " +
                                   std::to_string(entity.storey) + ", que la carte n'a pas",
                               LevelValidationError::OutOfBounds);
            }
            if (entityJson.contains("volume")) {
                entity.volume = parseVolume(entityJson.at("volume"), scene.origin);
            }
        }
        if (!entity.id.empty() && !ids.insert(entity.id).second) {
            return failure("Deux entites portent l'identifiant '" + entity.id + "'",
                           LevelValidationError::DuplicateEntityId);
        }
        if (entityJson.contains("cells")) {
            if (!entityJson.at("cells").is_array()) {
                return failure("Le champ 'cells' d'une entite doit etre une liste",
                               LevelValidationError::ParseError);
            }
            for (const nlohmann::json& cellJson : entityJson.at("cells")) {
                GridPosition cell;
                if (std::optional<LevelLoadResult> error =
                        parseCell(cellJson, map, "une zone peinte", cell)) {
                    return error;
                }
                entity.cells.push_back(cell);
            }
        }
        collectProperties(entityJson, known, entity.properties);
        entities.push_back(std::move(entity));
    }
    return std::nullopt;
}

// Cases de collision forcees a la main (format v4, decision D10) : triees (ligne, colonne), sans
// doublon -- l'ecriture est canonique, et une meme case forcee deux fois ne veut rien dire de plus.
[[nodiscard]] std::optional<LevelLoadResult> parseForced(const nlohmann::json& root,
                                                         const TileMap& map,
                                                         std::vector<GridPosition>& forced) {
    if (!root.contains("forced")) {
        return std::nullopt;
    }
    if (!root.at("forced").is_array()) {
        return failure("Le champ 'forced' doit etre une liste", LevelValidationError::ParseError);
    }
    for (const nlohmann::json& cellJson : root.at("forced")) {
        GridPosition cell;
        if (std::optional<LevelLoadResult> error =
                parseCell(cellJson, map, "les cases forcees", cell)) {
            return error;
        }
        forced.push_back(cell);
    }
    const auto byRow = [](GridPosition left, GridPosition right) {
        return std::pair{left.row, left.column} < std::pair{right.row, right.column};
    };
    std::ranges::sort(forced, byRow);
    const auto [first, last] = std::ranges::unique(forced);
    forced.erase(first, last);
    return std::nullopt;
}

// Accumulateurs remplis case par case par parseTile() ci-dessous -- toutes des références vers
// les variables locales de LevelLoader::loadFromString, un seul jeu construit pour tout le
// tableau `tiles`.
struct TileParseState {
    TileMap& map;
    GridPosition& entry;
    int& entryCount;
    std::set<std::pair<int, int>>& occupiedPositions;
    // Assignations de texture d'une carte v3, a ranger comme pieces de la couche de decor.
    std::vector<std::pair<GridPosition, std::string>>& legacyTextures;
    int version;
};

// Traite UNE entrée du tableau racine `tiles` (la grille de collision) : pose la tuile et alimente
// les accumulateurs de @p state. std::nullopt en cas de succès, sinon l'échec à renvoyer
// IMMÉDIATEMENT -- aucun état partiel n'est jamais renvoyé avec succès.
[[nodiscard]] std::optional<LevelLoadResult> parseTile(const nlohmann::json& tile,
                                                       TileParseState& state) {
    const int x = tile.at("x").get<int>();
    const int y = tile.at("y").get<int>();
    const std::string typeName = tile.at("type").get<std::string>();

    const std::optional<TileType> type = parseTileType(typeName);
    if (!type) {
        return failure("Type de tuile inconnu : " + typeName,
                       LevelValidationError::UnknownTileType);
    }
    if (!state.map.inBounds(x, y)) {
        return failure("Tuile hors bornes en " + cellText(x, y), LevelValidationError::OutOfBounds);
    }
    if (!state.occupiedPositions.emplace(x, y).second) {
        return failure("Deux tuiles a la meme position " + cellText(x, y),
                       LevelValidationError::DuplicatePosition);
    }
    state.map.setTile(x, y, *type);

    // Piece assignee a la case d'une carte v3 (EX-EDIT-043) : elle quitte la grille de collision
    // pour la couche de decor, ou elle a toujours ete dessinee. Une v4 qui en porte encore une
    // melangerait les deux formats : refusee, plutot que lue a moitie.
    if (tile.contains("texture")) {
        if (state.version >= PIECES_ON_LAYERS_VERSION) {
            return failure("Champ 'texture' dans la grille de collision d'une carte v4 en " +
                               cellText(x, y) + " : la piece se nomme sur sa couche ('piece')",
                           LevelValidationError::ParseError);
        }
        state.legacyTextures.emplace_back(GridPosition{.column = x, .row = y},
                                          tile.at("texture").get<std::string>());
    }

    if (*type == TileType::Entry) {
        state.entry = GridPosition{.column = x, .row = y};
        ++state.entryCount;
    }
    return std::nullopt;
}

// Version du format (EX-LVL-005) : absente = version initiale (0), sans erreur ni avertissement
// (retrocompatibilite des niveaux anterieurs a ce champ).
[[nodiscard]] std::optional<LevelLoadResult> parseVersion(const nlohmann::json& root,
                                                          int& version) {
    version = root.value("version", 0);
    if (version > LEVEL_FORMAT_VERSION) {
        return failure("Version de format non geree : " + std::to_string(version) +
                           " (maximum gere : " + std::to_string(LEVEL_FORMAT_VERSION) + ")",
                       LevelValidationError::UnsupportedFormatVersion);
    }
    return std::nullopt;
}

// Valide les champs d'en-tête obligatoires (width/height/tiles, dimensions strictement positives)
// et extrait @p width/@p height. std::nullopt en cas de succès, sinon l'échec à renvoyer.
[[nodiscard]] std::optional<LevelLoadResult> parseHeader(const nlohmann::json& root, int& width,
                                                         int& height) {
    if (!root.contains("width") || !root.contains("height") || !root.contains("tiles")) {
        return failure("Champ obligatoire manquant (width, height ou tiles)",
                       LevelValidationError::ParseError);
    }
    if (!root.at("tiles").is_array()) {
        return failure("Le champ 'tiles' doit etre une liste", LevelValidationError::ParseError);
    }

    width = root.at("width").get<int>();
    height = root.at("height").get<int>();
    if (width <= 0 || height <= 0) {
        return failure("Dimensions invalides (width et height doivent etre > 0)",
                       LevelValidationError::ParseError);
    }
    if (width > MAX_LEVEL_SIDE || height > MAX_LEVEL_SIDE) {
        return failure("Dimensions invalides (width et height ne depassent pas " +
                           std::to_string(MAX_LEVEL_SIDE) + ")",
                       LevelValidationError::ParseError);
    }
    return std::nullopt;
}

// Exactement une entrée (EX-LVL-004).
[[nodiscard]] std::optional<LevelLoadResult> validateEntryCount(int entryCount) {
    if (entryCount == 0) {
        return failure("Carte sans entree (aucune tuile 'entry')",
                       LevelValidationError::InvalidEntryCount);
    }
    if (entryCount > 1) {
        return failure("Plusieurs entrees dans la carte (une seule attendue)",
                       LevelValidationError::InvalidEntryCount);
    }
    return std::nullopt;
}

// Range les assignations d'une carte v3 comme pieces de la PREMIERE couche de decor -- celle que la
// composition lisait deja pour le relief -- ou d'une couche de decor creee pour elles.
void adoptLegacyTextures(std::vector<std::pair<GridPosition, std::string>>& textures, int width,
                         int height, std::vector<TileLayer>& layers) {
    if (textures.empty()) {
        return;
    }
    auto decor = std::ranges::find(layers, LayerKind::Decor, &TileLayer::kind);
    if (decor == layers.end()) {
        layers.push_back(TileLayer{.name = MIGRATED_RELIEF_LAYER_NAME,
                                   .kind = LayerKind::Decor,
                                   .tiles = TileMap(width, height),
                                   .properties = {}});
        decor = std::prev(layers.end());
    }
    for (auto& [cell, piece] : textures) {
        decor->setPiece(cell.column, cell.row, std::move(piece));
    }
}

// Le compteur d'identifiants (decision D8) : au moins 1.
[[nodiscard]] int parseNextEntityId(const nlohmann::json& root) {
    return std::max(1, root.value("nextEntityId", 1));
}

// Une variante (decision D12) : son nom, sa base, sa planche, ses entites. Ni case ni couche --
// elles viennent de la base. Les entites sont bornees par la carte de base.
[[nodiscard]] LevelLoadResult loadVariant(const nlohmann::json& root, int version,
                                          const LevelLoader::BaseResolver& resolveBase) {
    const std::string baseId = root.at("base").get<std::string>();
    if (version < PIECES_ON_LAYERS_VERSION) {
        return failure("Variante ('base') dans une carte de version " + std::to_string(version) +
                           " : les variantes datent de la version 4",
                       LevelValidationError::ParseError);
    }
    if (version >= SCENE_FORMAT_VERSION) {
        return failure(
            "Variante ('base') dans une carte v5 : une description de carte du moteur "
            "porte ses propres objets, elle ne reprend pas ceux d'une autre",
            LevelValidationError::ParseError);
    }
    for (const char* cellField : {"width", "height", "tiles", "layers", "forced"}) {
        if (root.contains(cellField)) {
            return failure(std::string{"Une variante ne porte pas de cases : champ '"} + cellField +
                               "' en trop",
                           LevelValidationError::ParseError);
        }
    }
    if (!resolveBase) {
        return failure("Variante de '" + baseId + "' sans moyen de charger sa base",
                       LevelValidationError::MissingBase);
    }
    LevelLoadResult base = resolveBase(baseId);
    if (!base.ok()) {
        return failure("Base '" + baseId + "' de la variante illisible : " + base.error,
                       LevelValidationError::MissingBase);
    }
    if (!base.level->base().empty()) {
        return failure("La base '" + baseId + "' est elle-meme une variante",
                       LevelValidationError::MissingBase);
    }
    std::vector<MapEntity> entities;
    if (std::optional<LevelLoadResult> error = parseEntities(
            root, base.level->tileMap(), SceneContext{.version = version}, entities)) {
        return std::move(*error);
    }
    PropertyMap variantProperties;
    collectProperties(root, rootKeysFor(version), variantProperties);
    return LevelLoadResult{
        .level = applyVariant(*base.level, LevelData{.name = root.value("name", std::string{}),
                                                     .tileMap = TileMap(1, 1),
                                                     .entities = std::move(entities),
                                                     .nextEntityId = parseNextEntityId(root),
                                                     .base = baseId,
                                                     .scene = root.value("scene", std::string{}),
                                                     .properties = variantProperties}),
        .error = {}};
}

// Une carte ordinaire, toutes versions confondues.
[[nodiscard]] LevelLoadResult loadMap(const nlohmann::json& root, int version) {
    int width = 0;
    int height = 0;
    if (std::optional<LevelLoadResult> headerError = parseHeader(root, width, height)) {
        return std::move(*headerError);
    }

    std::string name = root.value("name", std::string{});
    TileMap map(width, height);

    GridPosition entry{};
    int entryCount = 0;
    std::set<std::pair<int, int>> occupiedPositions;
    std::vector<std::pair<GridPosition, std::string>> legacyTextures;

    TileParseState tileState{.map = map,
                             .entry = entry,
                             .entryCount = entryCount,
                             .occupiedPositions = occupiedPositions,
                             .legacyTextures = legacyTextures,
                             .version = version};
    for (const nlohmann::json& tile : root.at("tiles")) {
        if (std::optional<LevelLoadResult> tileError = parseTile(tile, tileState)) {
            return std::move(*tileError);
        }
    }
    if (std::optional<LevelLoadResult> countError = validateEntryCount(entryCount)) {
        return std::move(*countError);
    }

    LEVELS_LOG_TRACE("Carte chargee : '" + name + "' (" + std::to_string(width) + "x" +
                     std::to_string(height) + ")");
    // Le tableau racine "layers" ne porte que les couches VISIBLES (sol, decor) : la grille de
    // collision, elle, EST le tableau racine "tiles" -- celui qui porte l'entree, et dont dependent
    // l'exploration et la grille de combat tactique. Une seule source de verite.
    std::vector<TileLayer> declaredLayers;
    if (std::optional<LevelLoadResult> layersError =
            parseLayers(root, width, height, version, declaredLayers)) {
        return std::move(*layersError);
    }
    SceneContext scene{.version = version};
    std::vector<Storey> storeys;
    if (version >= SCENE_FORMAT_VERSION) {
        try {
            scene.origin = parseOrigin(root);
            storeys = parseStoreys(root);
        } catch (const std::invalid_argument& error) {
            return failure(error.what(), LevelValidationError::ParseError);
        }
        scene.storeyCount = storeys.size();
    }
    adoptLegacyTextures(legacyTextures, width, height, declaredLayers);
    std::vector<MapEntity> entities;
    std::optional<LevelLoadResult> entitiesError;
    try {
        entitiesError = parseEntities(root, map, scene, entities);
    } catch (const std::invalid_argument& error) {
        return failure(error.what(), LevelValidationError::ParseError);
    }
    if (entitiesError) {
        return std::move(*entitiesError);
    }
    std::vector<GridPosition> forced;
    if (std::optional<LevelLoadResult> forcedError = parseForced(root, map, forced)) {
        return std::move(*forcedError);
    }

    // La grille racine est PROMUE en couche de tete, pour que tout consommateur boucle sur
    // `layers()` sans cas particulier (EX-LVL-016). Son role dit ce qu'elle vaut : `Collision`
    // quand la carte declare des couches visibles a cote, `Legacy` quand elle n'en declare
    // aucune -- une grille plate de version 2, qui vaut alors a la fois decor et collision.
    std::vector<TileLayer> layers;
    layers.reserve(declaredLayers.size() + 1);
    layers.push_back(
        TileLayer{.name = {},
                  .kind = declaredLayers.empty() ? LayerKind::Legacy : LayerKind::Collision,
                  .tiles = map,
                  .properties = {}});
    for (TileLayer& declared : declaredLayers) {
        layers.push_back(std::move(declared));
    }

    // Toute cle racine inconnue est une propriete de la carte (LOT-EDITOR-09) : la region et
    // l'ambiance en sont, et une cle ecrite par un editeur plus recent traverse celui-ci.
    PropertyMap properties;
    collectProperties(root, rootKeysFor(version), properties);

    return LevelLoadResult{.level = Level(LevelData{.name = std::move(name),
                                                    .tileMap = std::move(map),
                                                    .layers = std::move(layers),
                                                    .entities = std::move(entities),
                                                    .entry = entry,
                                                    .forcedCollision = std::move(forced),
                                                    .nextEntityId = parseNextEntityId(root),
                                                    .properties = std::move(properties),
                                                    .storeys = std::move(storeys)}),
                           .error = {}};
}

}  // namespace

// Charge un niveau depuis une chaine JSON.
LevelLoadResult LevelLoader::loadFromString(std::string_view json,
                                            const BaseResolver& resolveBase) {
    // Enveloppe commune : brique partagee du LOT-79 (EX-CNT-012). La garde de version est
    // desactivee (0) parce que `parseVersion` porte la sienne, avec sa propre categorie d'echec.
    const JsonDocument document = readJsonObject(json, 0, "niveau");
    if (!document.ok()) {
        return failure(document.message, LevelValidationError::ParseError);
    }
    const nlohmann::json& root = document.root;
    try {
        int version = 0;
        if (std::optional<LevelLoadResult> versionError = parseVersion(root, version)) {
            return std::move(*versionError);
        }
        if (version >= SCENE_FORMAT_VERSION &&
            root.value("format", std::string{}) != SCENE_FORMAT_NAME) {
            return failure(std::string{"Carte v5 sans \"format\": \""} + SCENE_FORMAT_NAME +
                               "\" : une description de carte se declare",
                           LevelValidationError::ParseError);
        }
        if (root.contains("base")) {
            return loadVariant(root, version, resolveBase);
        }
        return loadMap(root, version);
    } catch (const nlohmann::json::exception& error) {
        return failure(std::string("JSON invalide : ") + error.what(),
                       LevelValidationError::ParseError);
    }
}

// Charge un niveau depuis un fichier (lecture binaire puis delegation a loadFromString).
LevelLoadResult LevelLoader::loadFromFile(const std::filesystem::path& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        return failure("Fichier de niveau introuvable : " + path.string(),
                       LevelValidationError::FileNotFound);
    }
    std::ostringstream buffer;
    buffer << file.rdbuf();
    // La base d'une variante se lit sans resolveur : une base qui serait elle-meme une variante est
    // refusee, et une chaine de variantes ne peut donc pas boucler.
    const BaseResolver resolveBase = [&path](std::string_view baseId) {
        const std::optional<std::filesystem::path> basePath = findVariantBase(path, baseId);
        if (!basePath) {
            return failure("Base '" + std::string{baseId} + "' introuvable depuis " + path.string(),
                           LevelValidationError::MissingBase);
        }
        std::ifstream baseFile(*basePath, std::ios::binary);
        std::ostringstream baseBuffer;
        baseBuffer << baseFile.rdbuf();
        return loadFromString(baseBuffer.str());
    };
    return loadFromString(buffer.str(), resolveBase);
}

}  // namespace core
