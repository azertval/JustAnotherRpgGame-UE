// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : nlohmann et la description du créateur ne voient aucune macro d'Unreal.
#include "Core/Rpg/CharacterCreator.h"

#include <string>

#include "Commandlets/JadgBuildCharacterCreatorCommandlet.h"

#include "Bridge/JadgPaths.h"
#include "Characters/JadgCreatorGraph.h"
#include "JustAnotherRpgGame.h"
#include "Misc/Parse.h"

UJadgBuildCharacterCreatorCommandlet::UJadgBuildCharacterCreatorCommandlet()
{
	IsClient = false;
	IsServer = false;
	IsEditor = true;
	LogToConsole = true;
}

int32 UJadgBuildCharacterCreatorCommandlet::Main(const FString& Params)
{
	FString Id = TEXT("humanoid");
	FParse::Value(*Params, TEXT("JadgCreator="), Id);
	const bool bForce = FParse::Param(*Params, TEXT("JadgForce"));

	const std::filesystem::path Description =
		FJadgPaths::ToPath(FJadgPaths::ElementsDir()) / "Assets" / "Characters" / (std::string(TCHAR_TO_UTF8(*Id)) + ".json");
	const core::CharacterCreatorReadResult Lue = core::readCharacterCreator(Description);
	if (!Lue.ok())
	{
		UE_LOG(LogJadg, Error, TEXT("[Createur] %s"), *FJadgPaths::ToFString(Lue.message));
		return 1;
	}

	FString Erreur;
	const JadgCreatorGraph::EBuild Resultat = JadgCreatorGraph::Build(Lue.creator, bForce, Erreur);
	if (Resultat == JadgCreatorGraph::EBuild::Failed)
	{
		UE_LOG(LogJadg, Error, TEXT("[Createur] %s"), *Erreur);
		return 1;
	}
	UE_LOG(LogJadg, Display, TEXT("[Createur] %s : %s"), *FJadgPaths::ToFString(Lue.creator.asset),
		Resultat == JadgCreatorGraph::EBuild::Kept ? TEXT("déjà à jour") : TEXT("construit et compilé"));
	return 0;
}
