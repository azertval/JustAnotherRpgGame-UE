// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Core.h"
#include "Core/Rpg/CharacterOptions.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Party.h"

#include <filesystem>
#include <string>

#include "Commandlets/JadgContentCheckCommandlet.h"

#include "Bridge/JadgLog.h"
#include "Bridge/JadgPaths.h"
#include "JustAnotherRpgGame.h"

UJadgContentCheckCommandlet::UJadgContentCheckCommandlet()
{
	IsClient = false;
	// Vrai : le moteur crée alors l'éditeur (GEditor), que des modules chargés au démarrage exigent même
	// sans fenêtre ; faux, le commandlet tombe avant Main sur une assertion de l'éditeur.
	IsEditor = true;
	IsServer = false;
	LogToConsole = true;
	ShowErrorCount = true;
}

int32 UJadgContentCheckCommandlet::Main(const FString& Params)
{
	FJadgCoreLogBridge::Install();

	const std::filesystem::path Rpg = FJadgPaths::RpgRoot();
	UE_LOG(LogJadg, Display, TEXT("Core %s ; catalogues : %s"),
		*FJadgPaths::ToFString(core::Engine::version()), *FJadgPaths::ToFString(Rpg.string()));

	int32 ErrorCount = 0;
	const auto Report = [&ErrorCount](const std::vector<std::string>& Errors, const TCHAR* What)
	{
		for (const std::string& Error : Errors)
		{
			UE_LOG(LogJadg, Error, TEXT("%s : %s"), What, *FJadgPaths::ToFString(Error));
			++ErrorCount;
		}
	};

	// Les catalogues : espèces, historiques, classes, capacités, sorts, règles, expérience.
	const core::CharacterOptions Options = core::loadCharacterOptions(Rpg);
	Report(Options.errors, TEXT("options de personnage"));
	const core::CharacterCreationRules Rules =
		core::loadCharacterCreationRules(Rpg / "rules" / "character-creation.json");
	Report(Rules.errors, TEXT("règles de création"));
	const core::ExperienceTable Experience = core::loadExperienceTable(Rpg / "rules" / "experience.json");
	Report(Experience.errors, TEXT("table d'expérience"));
	UE_LOG(LogJadg, Display, TEXT("%d espèces, %d historiques, %d classes"),
		static_cast<int32>(Options.species.size()), static_cast<int32>(Options.backgrounds.size()),
		static_cast<int32>(Options.classes.size()));

	// Les fiches pré-tirées : le groupe préformé de D-28.
	const core::PartyCandidates Candidates = core::loadPartyCandidates(Rpg / "characters");
	Report(Candidates.errors, TEXT("fiches du groupe"));
	if (Candidates.candidates.empty())
	{
		UE_LOG(LogJadg, Error, TEXT("aucune fiche dans %s"), *FJadgPaths::ToFString((Rpg / "characters").string()));
		++ErrorCount;
	}

	for (const core::PartyCandidate& Candidate : Candidates.candidates)
	{
		const core::LoadedCharacterSheet Loaded =
			core::loadCharacterSheet(Candidate.file, Options, Rules, Experience);
		Report(Loaded.errors, *FJadgPaths::ToFString(Candidate.id));
		for (const std::string& Warning : Loaded.warnings)
		{
			UE_LOG(LogJadg, Warning, TEXT("%s : %s"), *FJadgPaths::ToFString(Candidate.id), *FJadgPaths::ToFString(Warning));
		}
		const core::CharacterSheet& Sheet = Loaded.sheet;
		UE_LOG(LogJadg, Display,
			TEXT("%s — %s %s niveau %d ; FOR %d DEX %d CON %d INT %d SAG %d CHA %d ; PV %d/%d ; CA %d ; vitesse %.1f m"),
			*FJadgPaths::ToFString(Sheet.name), *FJadgPaths::ToFString(Sheet.speciesId),
			*FJadgPaths::ToFString(Sheet.classId), Sheet.level, Sheet.abilities[0], Sheet.abilities[1],
			Sheet.abilities[2], Sheet.abilities[3], Sheet.abilities[4], Sheet.abilities[5],
			Sheet.currentHitPoints, Sheet.maximumHitPoints, Sheet.armorClass, Sheet.speedMeters);
	}

	if (ErrorCount > 0)
	{
		UE_LOG(LogJadg, Error, TEXT("%d erreur(s) de contenu"), ErrorCount);
		return 1;
	}
	UE_LOG(LogJadg, Display, TEXT("Contenu lu sans erreur : %d fiche(s)"), static_cast<int32>(Candidates.candidates.size()));
	return 0;
}
