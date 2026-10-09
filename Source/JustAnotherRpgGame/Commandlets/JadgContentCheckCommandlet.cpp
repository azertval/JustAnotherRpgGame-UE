// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Core.h"
#include "Core/Rpg/CharacterOptions.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Party.h"
#include "Core/World/WorldGraph.h"
#include "Core/World/WorldTravel.h"

#include <filesystem>
#include <string>

#include "Commandlets/JadgContentCheckCommandlet.h"

#include "Bridge/JadgLog.h"
#include "Bridge/JadgPaths.h"
#include "JustAnotherRpgGame.h"
#include "Misc/Paths.h"

namespace
{
	/// Ce que dit un défaut du graphe du monde, en clair.
	const TCHAR* IssueText(core::WorldIssueCode Code)
	{
		switch (Code)
		{
		case core::WorldIssueCode::UnreadableMap:
			return TEXT("carte illisible");
		case core::WorldIssueCode::MissingTargetMap:
			return TEXT("portail sans carte visée");
		case core::WorldIssueCode::UnknownTargetMap:
			return TEXT("portail vers une carte inconnue");
		case core::WorldIssueCode::UnreadableTargetMap:
			return TEXT("portail vers une carte illisible");
		case core::WorldIssueCode::MissingArrivalPoint:
			return TEXT("portail sans point d'arrivée");
		case core::WorldIssueCode::UnknownArrivalPoint:
			return TEXT("portail vers un point d'arrivée inconnu");
		case core::WorldIssueCode::DuplicateArrivalPoint:
			return TEXT("point d'arrivée en double");
		case core::WorldIssueCode::CombatZoneDegenerate:
			return TEXT("zone de combat dégénérée");
		case core::WorldIssueCode::CombatZoneOutOfBounds:
			return TEXT("zone de combat hors de la carte");
		case core::WorldIssueCode::CombatZoneBlocked:
			return TEXT("zone de combat sans case libre");
		}
		return TEXT("défaut");
	}
}

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

	// Les cartes (format v5, LOT-1018) : celles du jeu et celles des essais, lues par le lecteur de
	// Core, puis le graphe de leurs portails — carte et point d'arrivée visés, zones de combat. Le
	// contrôle du texte (arrivées citées, zones nommées, cases inatteignables) est celui de
	// `scripts/maps/jadg_map.py --check` ; celui du maillage de navigation, de `build_level.py`.
	const std::filesystem::path TrialLevels =
		FJadgPaths::ToPath(FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), TEXT("Source/Test/Fixtures/Exploration/Levels"))));
	int32 MapCount = 0;
	for (const std::filesystem::path& Root : {FJadgPaths::ToPath(FJadgPaths::ElementsDir()) / "Levels", TrialLevels})
	{
		const core::WorldGraph Graph = core::loadWorldGraph(Root);
		MapCount += static_cast<int32>(Graph.maps.size());
		for (const core::WorldIssue& Issue : core::validateWorldGraph(Graph))
		{
			UE_LOG(LogJadg, Error, TEXT("carte %s (%d ; %d) : %s %s"), *FJadgPaths::ToFString(Issue.mapId), Issue.position.column,
				Issue.position.row, IssueText(Issue.code), *FJadgPaths::ToFString(Issue.value));
			++ErrorCount;
		}
	}
	UE_LOG(LogJadg, Display, TEXT("%d carte(s) lue(s) par Core"), MapCount);
	if (MapCount == 0)
	{
		UE_LOG(LogJadg, Error, TEXT("aucune carte lue"));
		++ErrorCount;
	}

	if (ErrorCount > 0)
	{
		UE_LOG(LogJadg, Error, TEXT("%d erreur(s) de contenu"), ErrorCount);
		return 1;
	}
	UE_LOG(LogJadg, Display, TEXT("Contenu lu sans erreur : %d fiche(s)"), static_cast<int32>(Candidates.candidates.size()));
	return 0;
}
