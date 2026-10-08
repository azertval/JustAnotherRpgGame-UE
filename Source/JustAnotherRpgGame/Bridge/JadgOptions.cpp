// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Data/GameOptions.h"

#include <string>

#include "Bridge/JadgOptions.h"

#include "Bridge/JadgPaths.h"
#include "HAL/IConsoleManager.h"
#include "JustAnotherRpgGame.h"
#include "Misc/App.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Misc/CoreMisc.h"
#include "Misc/Paths.h"
#include "UnrealEngine.h"

namespace
{
	void SetVariable(const TCHAR* Name, int32 Value)
	{
		if (IConsoleVariable* Variable = IConsoleManager::Get().FindConsoleVariable(Name))
		{
			Variable->Set(Value, ECVF_SetByGameSetting);
		}
		else
		{
			UE_LOG(LogJadg, Warning, TEXT("[Options] variable %s absente du moteur"), Name);
		}
	}
}

FString FJadgOptions::FactoryFile()
{
	return FPaths::Combine(FJadgPaths::ElementsDir(), FJadgPaths::ToFString(std::string(core::GAME_OPTIONS_FILE)));
}

FString FJadgOptions::PlayerFile()
{
	return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Options"), TEXT("options.json")));
}

int32 FJadgOptions::Read(core::GameOptions& OutOptions)
{
	int32 ErrorCount = 0;
	const auto Report = [&ErrorCount](const core::GameOptionsResult& Result)
	{
		for (const std::string& Error : Result.errors)
		{
			UE_LOG(LogJadg, Error, TEXT("[Options] %s"), *FJadgPaths::ToFString(Error));
			++ErrorCount;
		}
	};

	const core::GameOptionsResult Factory = core::loadGameOptions(FJadgPaths::ToPath(FactoryFile()));
	Report(Factory);
	if (!Factory.found)
	{
		UE_LOG(LogJadg, Error, TEXT("[Options] fichier d'usine absent : %s"), *FactoryFile());
		++ErrorCount;
	}

	const core::GameOptionsResult Player = core::loadGameOptions(FJadgPaths::ToPath(PlayerFile()), Factory.options);
	Report(Player);
	OutOptions = Player.options;
	return ErrorCount;
}

void FJadgOptions::Apply(const core::GameOptions& Options)
{
	SetVariable(TEXT("r.ScreenPercentage"), Options.renderScalePercent);
	SetVariable(TEXT("sg.ShadowQuality"), Options.shadowQuality);
	FApp::SetVolumeMultiplier(static_cast<float>(Options.volumePercent) / 100.0f);

	// La fenêtre du jeu n'existe pas encore : le moteur la crée à la définition demandée ici. Une
	// définition donnée sur la ligne de commande l'emporte (les captures : -ResX, -ResY).
	const TCHAR* CommandLine = FCommandLine::Get();
	FString Given;
	const bool bGivenOnCommandLine = FParse::Value(CommandLine, TEXT("ResX="), Given)
		|| FParse::Value(CommandLine, TEXT("ResY="), Given) || FParse::Value(CommandLine, TEXT("Res="), Given);
	const bool bOwnWindow = !GIsEditor && !IsRunningCommandlet() && FApp::CanEverRender() && !bGivenOnCommandLine;
	if (bOwnWindow)
	{
		FSystemResolution::RequestResolutionChange(Options.width, Options.height,
			Options.fullscreen ? EWindowMode::WindowedFullscreen : EWindowMode::Windowed);
		IConsoleManager::Get().CallAllConsoleVariableSinks();
	}

	UE_LOG(LogJadg, Display, TEXT("[Options] %d x %d%s, rendu %d %%, ombres %d, volume %d %%%s"),
		Options.width, Options.height, Options.fullscreen ? TEXT(" plein écran") : TEXT(" fenêtré"),
		Options.renderScalePercent, Options.shadowQuality, Options.volumePercent,
		bOwnWindow ? TEXT("") : TEXT(" (définition non appliquée : pas de fenêtre de jeu, ou donnée sur la ligne de commande)"));
}
