// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Rpg/Check.h"

#include <algorithm>
#include <utility>

#include "Core/Data/JsonDocument.h"

namespace core {

CheckResult rollCheck(int target, std::span<const Modifier> modifiers, RollStance stance,
                      DeterministicRandom& random) {
    CheckResult resultat;
    resultat.target = target;
    resultat.stance = stance;

    // Les DEUX des sont conserves en cas d'avantage ou de desavantage, pas seulement celui qui est
    // retenu : c'est ce que le joueur veut voir pour comprendre ce que son avantage lui a rapporte
    // (EX-REG-003).
    resultat.dice.push_back(random.nextInt(1, D20_FACES));
    if (stance != RollStance::Normal) {
        resultat.dice.push_back(random.nextInt(1, D20_FACES));
    }

    switch (stance) {
        case RollStance::Advantage:
            resultat.keptDie = *std::ranges::max_element(resultat.dice);
            break;
        case RollStance::Disadvantage:
            resultat.keptDie = *std::ranges::min_element(resultat.dice);
            break;
        case RollStance::Normal:
            resultat.keptDie = resultat.dice.front();
            break;
    }

    resultat.modifiers.assign(modifiers.begin(), modifiers.end());
    resultat.total = resultat.keptDie;
    for (const Modifier& modificateur : resultat.modifiers) {
        resultat.total += modificateur.value;
    }
    return resultat;
}

std::string_view rollStanceName(RollStance stance) noexcept {
    // switch exhaustif sans default.
    switch (stance) {
        case RollStance::Normal:
            return "normal";
        case RollStance::Advantage:
            return "avantage";
        case RollStance::Disadvantage:
            return "desavantage";
    }
    return {};
}

std::string CheckResult::describe() const {
    std::string texte = "d20";
    if (stance != RollStance::Normal) {
        texte += " (";
        texte += rollStanceName(stance);
        texte += " : ";
        bool premier = true;
        for (const int de : dice) {
            if (!premier) {
                texte += ", ";
            }
            texte += std::to_string(de);
            premier = false;
        }
        texte += ')';
    }
    texte += " = " + std::to_string(keptDie);
    for (const Modifier& modificateur : modifiers) {
        texte += modificateur.value >= 0 ? " + " : " - ";
        texte += std::to_string(modificateur.value >= 0 ? modificateur.value : -modificateur.value);
        texte += " (" + modificateur.source + ')';
    }
    texte += " = " + std::to_string(total);
    texte += total >= target ? " >= " : " < ";
    texte += std::to_string(target);
    texte += total >= target ? " : reussite" : " : echec";
    if (isNaturalTwenty()) {
        texte += " (20 naturel)";
    } else if (isNaturalOne()) {
        texte += " (1 naturel)";
    }
    return texte;
}

const DifficultyTier* DifficultyScale::find(std::string_view id) const {
    const auto trouve = std::ranges::find(tiers, id, &DifficultyTier::id);
    return trouve == tiers.end() ? nullptr : &*trouve;
}

DifficultyScale loadDifficultyScale(const std::filesystem::path& path) {
    DifficultyScale echelle;
    // Une regle, pas un document de format : pas de champ `version` (meme choix qu'au LOT-33).
    const JsonDocument document = readJsonObjectFromFile(path, 0);
    if (!document.ok()) {
        echelle.errors.push_back(path.string() + " : " + document.message);
        return echelle;
    }
    const auto degres = document.root.find("tiers");
    if (degres == document.root.end() || !degres->is_array()) {
        echelle.errors.push_back(path.string() + " : champ 'tiers' absent ou non tableau.");
        return echelle;
    }
    for (const auto& degre : *degres) {
        const auto id = degre.find("id");
        const auto dc = degre.find("dc");
        if (!degre.is_object() || id == degre.end() || !id->is_string() || dc == degre.end() ||
            !dc->is_number_integer()) {
            // Ecarte en le NOMMANT : un degre sans nombre, garde a 0, ferait reussir tout jet qui
            // le vise, ce qui se joue et ne se voit pas.
            echelle.errors.push_back(path.string() + " : degre sans identifiant ou sans 'dc'.");
            continue;
        }
        DifficultyTier lu;
        lu.id = id->get<std::string>();
        lu.dc = dc->get<int>();
        if (const auto nom = degre.find("name"); nom != degre.end() && nom->is_string()) {
            lu.name = nom->get<std::string>();
        }
        echelle.tiers.push_back(std::move(lu));
    }
    return echelle;
}

}  // namespace core
