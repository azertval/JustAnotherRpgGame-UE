// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "JustAnotherRpgGame.h"

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Core.h"

#include "Bridge/JadgLog.h"
#include "Bridge/JadgPaths.h"

DEFINE_LOG_CATEGORY(LogJadg);

void FJustAnotherRpgGameModule::StartupModule()
{
	FJadgCoreLogBridge::Install();
	UE_LOG(LogJadg, Log, TEXT("Core %s compilé dans le module ; données de contenu : %s"),
		*FJadgPaths::ToFString(core::Engine::version()), *FJadgPaths::ElementsDir());
}

void FJustAnotherRpgGameModule::ShutdownModule()
{
	FJadgCoreLogBridge::Uninstall();
}

IMPLEMENT_PRIMARY_GAME_MODULE(FJustAnotherRpgGameModule, JustAnotherRpgGame, "JustAnotherRpgGame");
