// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Rpg/CharacterCreator.h"

#include <fstream>
#include <sstream>

namespace core {

namespace {

constexpr int SANS_GARDE_DE_VERSION = 0;

[[nodiscard]] CharacterCreatorReadResult refus(std::string_view origin, const std::string& champ,
                                               std::string_view raison) {
    CharacterCreatorReadResult result;
    result.error = JsonReadError::MalformedStructure;
    result.message = std::string(origin) + " : " + champ + " : " + std::string(raison);
    return result;
}

[[nodiscard]] bool cheminDeContenu(const std::string& valeur) {
    return valeur.rfind("/Game/", 0) == 0 && valeur.size() > 6;
}

}  // namespace

CharacterCreatorReadResult parseCharacterCreator(std::string_view json, std::string_view origin) {
    const JsonDocument document = readJsonObject(json, SANS_GARDE_DE_VERSION, origin);
    if (!document.ok()) {
        CharacterCreatorReadResult result;
        result.error = document.error;
        result.message = document.message;
        return result;
    }
    const nlohmann::json& racine = document.root;
    CharacterCreatorReadResult result;
    CharacterCreator& creator = result.creator;

    for (const auto& [champ, cible] : std::initializer_list<std::pair<const char*, std::string*>>{
             {"id", &creator.id},
             {"asset", &creator.asset},
             {"component", &creator.component},
             {"skeleton", &creator.skeleton},
             {"weapons", &creator.weapons}}) {
        const auto it = racine.find(champ);
        if (it == racine.end() || !it->is_string() || it->get<std::string>().empty()) {
            return refus(origin, champ, "chaîne non vide attendue");
        }
        *cible = it->get<std::string>();
    }
    for (const char* champ : {"asset", "skeleton", "weapons"}) {
        if (!cheminDeContenu(racine.at(champ).get<std::string>())) {
            return refus(origin, champ, "chemin de contenu /Game/… attendu");
        }
    }

    const auto taille = racine.find("referenceHeight");
    if (taille == racine.end() || !taille->is_number() || taille->get<float>() <= 0.0F) {
        return refus(origin, "referenceHeight", "taille strictement positive attendue, en mètres");
    }
    creator.referenceHeight = taille->get<float>();

    for (const auto& [champ, cible, contenu] :
         std::initializer_list<std::tuple<const char*, std::map<std::string, std::string>*, bool>>{
             {"bodies", &creator.bodies, true},
             {"clips", &creator.clips, true},
             {"sockets", &creator.sockets, false}}) {
        const auto it = racine.find(champ);
        if (it == racine.end() || !it->is_object() || it->empty()) {
            return refus(origin, champ, "objet non vide attendu");
        }
        for (const auto& [nom, valeur] : it->items()) {
            if (!valeur.is_string() || valeur.get<std::string>().empty()) {
                return refus(origin, std::string(champ) + "/" + nom, "chaîne non vide attendue");
            }
            if (contenu && !cheminDeContenu(valeur.get<std::string>())) {
                return refus(origin, std::string(champ) + "/" + nom,
                             "chemin de contenu /Game/… attendu");
            }
            (*cible)[nom] = valeur.get<std::string>();
        }
    }
    for (const char* clip : {"idle", "walk"}) {
        if (!creator.clips.count(clip)) {
            return refus(origin, std::string("clips/") + clip, "le clip est obligatoire");
        }
    }
    return result;
}

CharacterCreatorReadResult readCharacterCreator(const std::filesystem::path& path) {
    std::ifstream fichier(path, std::ios::binary);
    if (!fichier) {
        CharacterCreatorReadResult result;
        result.error = JsonReadError::FileNotFound;
        result.message = path.string() + " : fichier absent ou illisible";
        return result;
    }
    std::ostringstream texte;
    texte << fichier.rdbuf();
    return parseCharacterCreator(texte.str(), path.filename().string());
}

}  // namespace core
