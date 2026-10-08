// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/World/Atlas.h"

#include <algorithm>
#include <array>
#include <functional>
#include <iterator>
#include <set>
#include <system_error>
#include <utility>

#include "Core/Data/JsonDocument.h"

namespace core {

namespace {

// Les entrees de catalogue ne portent pas de champ `version` : ce sont des donnees, pas des
// documents de format. `0` desactive la garde de version, comme le fait deja le bestiaire.
constexpr int SANS_GARDE_DE_VERSION = 0;

constexpr std::array<std::string_view, kRegionGradeCount> NOMS_DE_NOTE{"veryLow", "low", "normal",
                                                                       "high", "veryHigh"};

// Dans l'ordre de `RegionAxis`, et dans celui ou le livre les imprime.
constexpr std::array<std::string_view, kRegionAxisCount> NOMS_D_AXE{
    "citizenFreedom", "crimeAndViolence", "economicProsperity", "governmentCorruption",
    "magicAccess",    "monsterPresence",  "politicalStability"};

// Un champ obligatoire absent est une donnee invalide, jamais une valeur par defaut : rendre
// false et remplir `raison` plutot que lever (EX-NFR-040).
[[nodiscard]] bool lireTexte(const nlohmann::json& objet, const char* champ, std::string& sortie,
                             std::string& raison) {
    const auto trouve = objet.find(champ);
    if (trouve == objet.end() || !trouve->is_string()) {
        raison = std::string{"champ '"} + champ + "' absent ou non textuel";
        return false;
    }
    sortie = trouve->get<std::string>();
    return true;
}

[[nodiscard]] std::string lireTexteFacultatif(const nlohmann::json& objet, const char* champ) {
    const auto trouve = objet.find(champ);
    return (trouve != objet.end() && trouve->is_string()) ? trouve->get<std::string>()
                                                          : std::string{};
}

// `null` est une valeur du schema, pas une absence : le livre ecrit parfois une population sans
// chiffre. La distinguer de zero est tout l'objet de l'optional.
[[nodiscard]] std::optional<int> lireEntierFacultatif(const nlohmann::json& objet,
                                                      const char* champ) {
    const auto trouve = objet.find(champ);
    if (trouve == objet.end() || !trouve->is_number_integer()) {
        return std::nullopt;
    }
    return trouve->get<int>();
}

[[nodiscard]] std::vector<std::string> lireTextes(const nlohmann::json& objet, const char* champ) {
    std::vector<std::string> valeurs;
    const auto trouve = objet.find(champ);
    if (trouve == objet.end() || !trouve->is_array()) {
        return valeurs;
    }
    for (const auto& element : *trouve) {
        if (element.is_string()) {
            valeurs.push_back(element.get<std::string>());
        }
    }
    return valeurs;
}

[[nodiscard]] bool lireStatistique(const nlohmann::json& parent, std::string_view nomAxe,
                                   RegionStatistic& sortie, std::string& raison) {
    const auto trouve = parent.find(nomAxe);
    if (trouve == parent.end() || !trouve->is_array() || trouve->empty()) {
        raison = std::string{"axe '"} + std::string{nomAxe} + "' absent ou vide";
        return false;
    }
    for (const auto& element : *trouve) {
        if (!element.is_object()) {
            raison = std::string{"axe '"} + std::string{nomAxe} + "' : appreciation non objet";
            return false;
        }
        const auto note = element.find("grade");
        if (note == element.end() || !note->is_string()) {
            raison = std::string{"axe '"} + std::string{nomAxe} + "' : note absente";
            return false;
        }
        const std::optional<RegionGrade> valeur = regionGradeFromName(note->get<std::string>());
        if (!valeur.has_value()) {
            // Une note inconnue n'est PAS rabattue sur `normal` : ce serait une region paisible
            // par accident, indiscernable d'une region paisible par conception.
            raison = std::string{"axe '"} + std::string{nomAxe} + "' : note '" +
                     note->get<std::string>() + "' hors des cinq valeurs";
            return false;
        }
        sortie.appraisals.push_back(
            RegionAppraisal{.grade = *valeur, .scope = lireTexteFacultatif(element, "scope")});
    }
    return true;
}

[[nodiscard]] bool lirePopulation(const nlohmann::json& objet, RegionPopulation& sortie,
                                  std::string& raison) {
    const auto trouve = objet.find("population");
    if (trouve == objet.end() || !trouve->is_object()) {
        raison = "champ 'population' absent ou non objet";
        return false;
    }
    sortie.total = lireEntierFacultatif(*trouve, "total");
    sortie.otherPercent = lireEntierFacultatif(*trouve, "otherPercent");

    const auto especes = trouve->find("species");
    if (especes == trouve->end() || !especes->is_array() || especes->empty()) {
        raison = "champ 'population/species' absent ou vide";
        return false;
    }
    for (const auto& element : *especes) {
        RegionSpeciesShare part;
        if (!element.is_object() || !lireTexte(element, "species", part.species, raison) ||
            !lireTexte(element, "label", part.label, raison)) {
            raison.insert(0, "population/species : ");
            return false;
        }
        const std::optional<int> pourcent = lireEntierFacultatif(element, "percent");
        if (!pourcent.has_value()) {
            raison = "population/species : champ 'percent' absent ou non entier";
            return false;
        }
        part.percent = *pourcent;
        sortie.species.push_back(std::move(part));
    }
    return true;
}

[[nodiscard]] bool lireRegion(const nlohmann::json& racine, const std::string& fichier,
                              Region& sortie, std::vector<std::string>& erreurs) {
    std::string raison;
    if (!lireTexte(racine, "id", sortie.id, raison) ||
        !lireTexte(racine, "name", sortie.name, raison) ||
        !lireTexte(racine, "source", sortie.source, raison) ||
        !lireTexte(racine, "government", sortie.government, raison) ||
        !lireTexte(racine, "faction", sortie.faction, raison) ||
        !lirePopulation(racine, sortie.population, raison)) {
        erreurs.push_back(fichier + " : " + raison + '.');
        return false;
    }

    const auto statistiques = racine.find("statistics");
    if (statistiques == racine.end() || !statistiques->is_object()) {
        erreurs.push_back(fichier + " : champ 'statistics' absent ou non objet.");
        return false;
    }
    for (std::size_t rang = 0; rang < kRegionAxisCount; ++rang) {
        if (!lireStatistique(*statistiques, NOMS_D_AXE[rang], sortie.statistics[rang], raison)) {
            std::string message = fichier;
            message += " : ";
            message += raison;
            message += '.';
            erreurs.push_back(std::move(message));
            return false;
        }
    }

    sortie.neighbors = lireTextes(racine, "neighbors");
    sortie.locations = lireTextes(racine, "locations");
    return true;
}

[[nodiscard]] bool lireLieu(const nlohmann::json& racine, const std::string& fichier,
                            Location& sortie, std::vector<std::string>& erreurs) {
    std::string raison;
    if (!lireTexte(racine, "id", sortie.id, raison) ||
        !lireTexte(racine, "name", sortie.name, raison) ||
        !lireTexte(racine, "source", sortie.source, raison) ||
        !lireTexte(racine, "region", sortie.region, raison)) {
        erreurs.push_back(fichier + " : " + raison + '.');
        return false;
    }
    sortie.description = lireTexteFacultatif(racine, "description");
    return true;
}

// Le dossier est BALAYE : une liste de noms ecrite en C++ serait une seconde source de verite, et
// le premier lieu ajoute par le LOT-80 en sortirait invisible.
[[nodiscard]] std::vector<std::filesystem::path> fichiersJson(
    const std::filesystem::path& dossier) {
    std::vector<std::filesystem::path> fichiers;
    std::error_code code;
    for (const auto& entree : std::filesystem::directory_iterator(dossier, code)) {
        if (entree.is_regular_file(code) && entree.path().extension() == ".json") {
            fichiers.push_back(entree.path());
        }
    }
    std::ranges::sort(fichiers);
    return fichiers;
}

}  // namespace

std::string_view regionGradeName(RegionGrade grade) {
    return NOMS_DE_NOTE[static_cast<std::size_t>(grade)];
}

std::optional<RegionGrade> regionGradeFromName(std::string_view name) {
    const auto trouve = std::ranges::find(NOMS_DE_NOTE, name);
    if (trouve == NOMS_DE_NOTE.end()) {
        return std::nullopt;
    }
    return static_cast<RegionGrade>(std::distance(NOMS_DE_NOTE.begin(), trouve));
}

std::string_view regionAxisName(RegionAxis axis) {
    return NOMS_D_AXE[static_cast<std::size_t>(axis)];
}

const Region* Atlas::findRegion(std::string_view id) const {
    const auto trouve = std::ranges::find(regions, id, &Region::id);
    return trouve == regions.end() ? nullptr : &*trouve;
}

const Location* Atlas::findLocation(std::string_view id) const {
    const auto trouve = std::ranges::find(locations, id, &Location::id);
    return trouve == locations.end() ? nullptr : &*trouve;
}

std::vector<std::string> Atlas::unreachableFrom(std::string_view from) const {
    std::set<std::string, std::less<>> vues;
    if (findRegion(from) != nullptr) {
        std::vector<std::string> pile{std::string{from}};
        vues.insert(std::string{from});
        while (!pile.empty()) {
            const std::string courante = std::move(pile.back());
            pile.pop_back();
            const Region* region = findRegion(courante);
            if (region == nullptr) {
                continue;
            }
            for (const std::string& voisin : region->neighbors) {
                if (findRegion(voisin) != nullptr && vues.insert(voisin).second) {
                    pile.push_back(voisin);
                }
            }
        }
    }
    std::vector<std::string> isolees;
    for (const Region& region : regions) {
        if (!vues.contains(region.id)) {
            isolees.push_back(region.id);
        }
    }
    return isolees;
}

Atlas loadAtlas(const std::filesystem::path& directory) {
    Atlas atlas;

    std::error_code code;
    if (!std::filesystem::is_directory(directory, code)) {
        // Un dossier absent n'est PAS un monde vide : les deux se ressemblent a l'execution, et
        // confondre << pas installe >> avec << aucune region >> fait chercher longtemps du
        // mauvais cote.
        atlas.errors.push_back(directory.string() + " : dossier d'atlas absent ou illisible.");
        return atlas;
    }

    for (const std::filesystem::path& chemin : fichiersJson(directory / "regions")) {
        const std::string nom = chemin.filename().string();
        const JsonDocument document = readJsonObjectFromFile(chemin, SANS_GARDE_DE_VERSION);
        if (!document.ok()) {
            atlas.errors.push_back(document.message);
            continue;
        }
        Region region;
        if (lireRegion(document.root, nom, region, atlas.errors)) {
            atlas.regions.push_back(std::move(region));
        }
    }

    for (const std::filesystem::path& chemin : fichiersJson(directory / "locations")) {
        const std::string nom = chemin.filename().string();
        const JsonDocument document = readJsonObjectFromFile(chemin, SANS_GARDE_DE_VERSION);
        if (!document.ok()) {
            atlas.errors.push_back(document.message);
            continue;
        }
        Location lieu;
        if (lireLieu(document.root, nom, lieu, atlas.errors)) {
            atlas.locations.push_back(std::move(lieu));
        }
    }

    if (atlas.regions.empty()) {
        atlas.errors.push_back(directory.string() +
                               " : aucune region lue. Un atlas sans region n'est pas un monde.");
    }

    std::ranges::sort(atlas.regions, {}, &Region::id);
    std::ranges::sort(atlas.locations, {}, &Location::id);
    return atlas;
}

}  // namespace core
