// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Game/JadgGameMode.h"

#include "Capture/JadgCaptureDirector.h"
#include "Capture/JadgWalkthrough.h"
#include "Characters/JadgParty.h"
#include "Engine/World.h"
#include "Misc/CommandLine.h"
#include "Player/JadgCameraPawn.h"
#include "Player/JadgPlayerController.h"
#include "UI/JadgHud.h"

AJadgGameMode::AJadgGameMode()
{
	DefaultPawnClass = AJadgCameraPawn::StaticClass();
	PlayerControllerClass = AJadgPlayerController::StaticClass();
	HUDClass = AJadgHud::StaticClass();
}

void AJadgGameMode::StartPlay()
{
	Super::StartPlay();

	// Après le lancement de la carte : ses personnages ont commencé à jouer, le groupe les trouve.
	GetWorld()->SpawnActor<AJadgParty>();

	FString CaptureDir;
	if (FParse::Value(FCommandLine::Get(), TEXT("JadgCapture="), CaptureDir))
	{
		GetWorld()->SpawnActor<AJadgCaptureDirector>();
	}
	else if (FParse::Value(FCommandLine::Get(), TEXT("JadgParcours="), CaptureDir))
	{
		GetWorld()->SpawnActor<AJadgWalkthrough>();
	}
}
