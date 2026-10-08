// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Rpg/Skill.h"

#include <algorithm>
#include <system_error>

#include "Core/Data/JsonDocument.h"

namespace core {

namespace {

// Les entrees de catalogue ne portent pas de champ `version` : ce sont des donnees, pas des
// documents de format (meme choix qu'au LOT-33 et au LOT-36).
constexpr int SANS_GARDE_DE_VERSION = 0;

}  // namespace

const SkillDefinition* SkillCatalog::find(std::string_view id) const {
    const auto trouve = std::ranges::find(skills, id, &SkillDefinition::id);
    return trouve == skills.end() ? nullptr : &*trouve;
}

SkillCatalog loadSkills(const std::filesystem::path& directory) {
    SkillCatalog catalogue;

    std::error_code code;
    if (!std::filesystem::is_directory(directory, code)) {
        // Un dossier absent n'est PAS un catalogue vide : sans compétence, tout jet de compétence
        // retomberait sur le modificateur nu, ce qui se joue et ne se voit pas.
        catalogue.errors.push_back(directory.string() + " : dossier de competences absent.");
        return catalogue;
    }

    std::vector<std::filesystem::path> fichiers;
    for (const auto& entree : std::filesystem::directory_iterator(directory, code)) {
        if (entree.is_regular_file(code) && entree.path().extension() == ".json") {
            fichiers.push_back(entree.path());
        }
    }
    std::ranges::sort(fichiers);

    for (const std::filesystem::path& chemin : fichiers) {
        const JsonDocument document = readJsonObjectFromFile(chemin, SANS_GARDE_DE_VERSION);
        if (!document.ok()) {
            // Le message porte deja le fichier et la ligne (EX-CNT-010).
            catalogue.errors.push_back(document.message);
            continue;
        }
        const std::string nom = chemin.filename().string();
        const auto identifiant = document.root.find("id");
        const auto libelle = document.root.find("name");
        const auto caracteristique = document.root.find("ability");
        if (identifiant == document.root.end() || !identifiant->is_string() ||
            libelle == document.root.end() || !libelle->is_string() ||
            caracteristique == document.root.end() || !caracteristique->is_string()) {
            catalogue.errors.push_back(nom + " : champs 'id', 'name' ou 'ability' absents.");
            continue;
        }
        const std::optional<Ability> lue = parseAbility(caracteristique->get<std::string>());
        if (!lue.has_value()) {
            // Une caracteristique inconnue est SIGNALEE, jamais devinee : la deviner ferait jeter
            // l'Athletisme en Charisme sans qu'aucun message ne le dise (EX-CNT-011).
            catalogue.errors.push_back(nom + " : caracteristique '" +
                                       caracteristique->get<std::string>() +
                                       "' inconnue du moteur.");
            continue;
        }
        catalogue.skills.push_back({.id = identifiant->get<std::string>(),
                                    .name = libelle->get<std::string>(),
                                    .ability = *lue});
    }
    std::ranges::sort(catalogue.skills, {}, &SkillDefinition::id);
    return catalogue;
}

}  // namespace core
