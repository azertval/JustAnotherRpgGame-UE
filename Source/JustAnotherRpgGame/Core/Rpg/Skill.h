// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Rpg/Skill.h
 * @brief Le catalogue des compétences et la caractéristique de chacune (`LOT-13`).
 */

#include <filesystem>
#include <string>
#include <string_view>
#include <vector>

#include "Core/Rpg/Ability.h"

namespace core {

/**
 * @brief Une compétence et la caractéristique dont elle dépend.
 *
 * **La correspondance compétence → caractéristique est une donnée**, jamais un `switch` : c'est
 * elle qui décide si l'Athlétisme se jette en Force ou en Dextérité, et une règle maison qui
 * changerait ce rattachement ne doit pas demander de recompiler (`EX-VIS-007`). Les dix-huit
 * entrées viennent du catalogue du `LOT-43`.
 */
struct SkillDefinition {
    std::string id;
    std::string name;
    Ability ability = Ability::Strength;
};

/// @brief Les compétences chargées, et ce qui n'a pas pu l'être.
struct SkillCatalog {
    std::vector<SkillDefinition> skills;
    std::vector<std::string> errors;

    /// @brief La compétence portant cet identifiant, ou `nullptr`.
    [[nodiscard]] const SkillDefinition* find(std::string_view id) const;
};

/**
 * @brief Charge le catalogue des compétences depuis son dossier.
 *
 * @param directory `Source/Elements/Rpg/skills`.
 * @return Le catalogue et la liste des échecs. Ne lève jamais (`EX-NFR-040`).
 */
[[nodiscard]] SkillCatalog loadSkills(const std::filesystem::path& directory);

}  // namespace core
