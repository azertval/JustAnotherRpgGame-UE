// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Game/JadgExplorationState.h
 * @brief L'état de Core que garde `UJadgExploration` : la session d'exploration, les catalogues, le
 *        groupe et ses fiches (LOT-1016) ; le combat joué dans le moteur le lit (LOT-1017).
 *
 * Il inclut Core **avant** le moteur : un fichier du jeu qui s'en sert l'inclut en tête, avant tout
 * en-tête d'Unreal (`AGENTS.md`). `JadgExploration.h` ne le montre pas.
 */

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Gameplay/Quest.h"
#include "Core/Levels/Level.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/CharacterOptions.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Dialogue.h"
#include "Core/Rpg/Party.h"
#include "Core/Rpg/Skill.h"
#include "Core/World/ExplorationSession.h"

#include <cstdint>
#include <filesystem>
#include <map>
#include <memory>
#include <string>
#include <vector>

#include "Game/JadgExploration.h"

/// Celui qui parle au PNJ (défini dans `JadgExploration.cpp`).
class FJadgPartyListener;

struct UJadgExploration::FState
{
	/// Les dossiers de cartes, dans l'ordre où une carte s'y cherche.
	std::vector<std::filesystem::path> LevelDirs;
	std::unique_ptr<core::ExplorationSession> Session;

	core::DialogueCatalog Dialogues;
	core::DifficultyScale Difficulty;
	core::CharacterOptions Options;
	core::CharacterCreationRules Rules;
	core::ExperienceTable Experience;
	core::SkillCatalog Skills;

	core::Party Party;
	/// Les fiches et les sacs du groupe, par identifiant de fiche.
	std::map<std::string, core::LoadedCharacterSheet> Sheets;

	/// Le dialogue ouvert : la suite aléatoire et l'interlocuteur vivent autant que le runner.
	std::unique_ptr<core::DeterministicRandom> Random;
	std::unique_ptr<FJadgPartyListener> Listener;
	std::unique_ptr<core::DialogueRunner> Runner;
	std::uint64_t NextSeed = 0;
	std::uint64_t Conversations = 0;

	~FState();

	core::LoadedCharacterSheet* Leader()
	{
		const auto Found = Sheets.find(std::string(Party.leader()));
		return Found != Sheets.end() ? &Found->second : nullptr;
	}

	const core::MapEntity* Find(const std::string& EntityId) const
	{
		const core::Level* Map = Session->map();
		if (Map == nullptr)
		{
			return nullptr;
		}
		for (const core::MapEntity& Entity : Map->entities())
		{
			if (Entity.id == EntityId)
			{
				return &Entity;
			}
		}
		return nullptr;
	}
};
