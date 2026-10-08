// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Rpg/Appearance.h"

#include <algorithm>
#include <fstream>
#include <initializer_list>
#include <sstream>
#include <system_error>
#include <utility>

namespace core {

namespace {

constexpr int SANS_GARDE_DE_VERSION = 0;

[[nodiscard]] AppearanceReadResult refus(std::string_view origin, std::string_view champ,
                                         std::string_view raison) {
    AppearanceReadResult result;
    result.error = JsonReadError::MalformedStructure;
    result.message = std::string(origin) + " : " + std::string(champ) + " : " + std::string(raison);
    return result;
}

[[nodiscard]] bool lireChaine(const nlohmann::json& objet, const char* champ, std::string& cible) {
    const auto it = objet.find(champ);
    if (it == objet.end() || !it->is_string() || it->get<std::string>().empty()) {
        return false;
    }
    cible = it->get<std::string>();
    return true;
}

}  // namespace

AppearanceReadResult parseAppearance(std::string_view json, std::string_view origin) {
    const JsonDocument document = readJsonObject(json, SANS_GARDE_DE_VERSION, origin);
    if (!document.ok()) {
        AppearanceReadResult result;
        result.error = document.error;
        result.message = document.message;
        return result;
    }
    const nlohmann::json& racine = document.root;
    AppearanceReadResult result;
    Appearance& fiche = result.appearance;

    for (const auto& [champ, cible] :
         std::initializer_list<std::pair<const char*, std::string*>>{{"id", &fiche.id},
                                                                     {"name", &fiche.name},
                                                                     {"source", &fiche.source},
                                                                     {"creator", &fiche.creator},
                                                                     {"body", &fiche.body},
                                                                     {"head", &fiche.head}}) {
        if (!lireChaine(racine, champ, *cible)) {
            return refus(origin, champ, "chaîne non vide attendue");
        }
    }

    const auto taille = racine.find("height");
    if (taille == racine.end() || !taille->is_number()) {
        return refus(origin, "height", "nombre attendu, en mètres");
    }
    fiche.height = taille->get<float>();
    if (fiche.height <= 0.0F) {
        return refus(origin, "height", "une taille est strictement positive");
    }

    if (const auto couleurs = racine.find("colors"); couleurs != racine.end()) {
        if (!couleurs->is_object()) {
            return refus(origin, "colors", "objet attendu");
        }
        for (const auto& [nom, valeur] : couleurs->items()) {
            if (!valeur.is_array() || valeur.size() < 3 || valeur.size() > 4) {
                return refus(origin, "colors/" + nom, "trois ou quatre composantes attendues");
            }
            AppearanceColor couleur;
            float* composantes[] = {&couleur.r, &couleur.g, &couleur.b, &couleur.a};
            for (std::size_t i = 0; i < valeur.size(); ++i) {
                if (!valeur[i].is_number()) {
                    return refus(origin, "colors/" + nom, "composante non numérique");
                }
                *composantes[i] = valeur[i].get<float>();
                if (*composantes[i] < 0.0F || *composantes[i] > 1.0F) {
                    return refus(origin, "colors/" + nom, "composante hors de 0 à 1");
                }
            }
            fiche.colors[nom] = couleur;
        }
    }

    if (const auto pieces = racine.find("pieces"); pieces != racine.end()) {
        if (!pieces->is_object()) {
            return refus(origin, "pieces", "objet attendu");
        }
        for (const auto& [emplacement, valeur] : pieces->items()) {
            if (!valeur.is_string()) {
                return refus(origin, "pieces/" + emplacement, "chaîne attendue");
            }
            fiche.pieces[emplacement] = valeur.get<std::string>();
        }
    }

    if (const auto armes = racine.find("weapons"); armes != racine.end()) {
        if (!armes->is_object()) {
            return refus(origin, "weapons", "objet attendu");
        }
        for (const auto& [main, valeur] : armes->items()) {
            if (main != "main-hand" && main != "off-hand") {
                return refus(origin, "weapons/" + main, "main-hand ou off-hand attendu");
            }
            if (!valeur.is_string() || valeur.get<std::string>().empty()) {
                return refus(origin, "weapons/" + main, "identifiant de pièce attendu");
            }
            fiche.weapons[main] = valeur.get<std::string>();
        }
    }

    if (const auto clips = racine.find("clips"); clips != racine.end()) {
        if (!clips->is_object()) {
            return refus(origin, "clips", "objet attendu");
        }
        for (const auto& [nom, valeur] : clips->items()) {
            if (!valeur.is_object()) {
                return refus(origin, "clips/" + nom, "objet attendu");
            }
            if (const auto key = valeur.find("key"); key != valeur.end()) {
                if (!key->is_number() || key->get<float>() < 0.0F) {
                    return refus(origin, "clips/" + nom + "/key",
                                 "instant d'impact positif attendu, en secondes");
                }
                fiche.clipKeys[nom] = key->get<float>();
            }
        }
    }

    return result;
}

AppearanceReadResult readAppearance(const std::filesystem::path& path) {
    std::ifstream fichier(path, std::ios::binary);
    if (!fichier) {
        AppearanceReadResult result;
        result.error = JsonReadError::FileNotFound;
        result.message = path.string() + " : fichier absent ou illisible";
        return result;
    }
    std::ostringstream texte;
    texte << fichier.rdbuf();
    return parseAppearance(texte.str(), path.filename().string());
}

std::map<std::string, Appearance> loadAppearances(const std::filesystem::path& directory,
                                                  std::vector<std::string>& errors) {
    std::map<std::string, Appearance> fiches;
    std::error_code ec;
    if (!std::filesystem::is_directory(directory, ec)) {
        errors.push_back(directory.string() + " : dossier absent");
        return fiches;
    }
    std::vector<std::filesystem::path> chemins;
    for (const auto& entree : std::filesystem::directory_iterator(directory, ec)) {
        if (entree.is_regular_file() && entree.path().extension() == ".json") {
            chemins.push_back(entree.path());
        }
    }
    std::sort(chemins.begin(), chemins.end());
    for (const auto& chemin : chemins) {
        AppearanceReadResult lue = readAppearance(chemin);
        if (!lue.ok()) {
            errors.push_back(lue.message);
            continue;
        }
        if (lue.appearance.id != chemin.stem().string()) {
            errors.push_back(chemin.filename().string() + " : l'identifiant « " +
                             lue.appearance.id + " » n'est pas le nom du fichier");
            continue;
        }
        fiches[lue.appearance.id] = std::move(lue.appearance);
    }
    return fiches;
}

}  // namespace core
