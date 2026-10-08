// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Game/JadgGameMode.h"

#include "Capture/JadgCaptureDirector.h"
#include "Engine/World.h"
#include "Misc/CommandLine.h"
#include "Player/JadgCameraPawn.h"
#include "Player/JadgPlayerController.h"

AJadgGameMode::AJadgGameMode()
{
	DefaultPawnClass = AJadgCameraPawn::StaticClass();
	PlayerControllerClass = AJadgPlayerController::StaticClass();
}

void AJadgGameMode::StartPlay()
{
	Super::StartPlay();

	FString CaptureDir;
	if (FParse::Value(FCommandLine::Get(), TEXT("JadgCapture="), CaptureDir))
	{
		GetWorld()->SpawnActor<AJadgCaptureDirector>();
	}
}
