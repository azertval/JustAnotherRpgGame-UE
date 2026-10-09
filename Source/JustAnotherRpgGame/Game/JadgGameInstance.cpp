// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Data/GameOptions.h"

#include "Game/JadgGameInstance.h"

#include "Bridge/JadgOptions.h"
#include "Bridge/JadgPaths.h"
#include "UI/JadgTexts.h"

void UJadgGameInstance::Init()
{
	Super::Init();

	// Un champ refusé est journalisé et garde sa valeur d'usine : le jeu se lance quand même.
	core::GameOptions Options;
	FJadgOptions::Read(Options);
	FJadgOptions::Apply(Options);
	FJadgTexts::SetLanguage(FJadgPaths::ToFString(Options.language));
}
