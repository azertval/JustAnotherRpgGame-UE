// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Player/JadgPlayerController.h"

#include "Characters/JadgWalker.h"
#include "EngineUtils.h"
#include "InputCoreTypes.h"
#include "NavigationSystem.h"
#include "Player/JadgCameraPawn.h"

namespace
{
	// Réglages de la porte ; les commandes du jeu sont le LOT-1016.
	constexpr float TurnDegreesPerSecond = 90.0f;
	constexpr float TiltDegreesPerSecond = 45.0f;
	constexpr float MouseDegreesPerUnit = 0.25f;
	constexpr float PanCentimetresPerSecond = 1500.0f;
	constexpr float ZoomStep = 0.88f;
}

AJadgPlayerController::AJadgPlayerController()
{
	bShowMouseCursor = true;
	bEnableClickEvents = false;
	bEnableMouseOverEvents = false;
}

void AJadgPlayerController::BeginPlay()
{
	Super::BeginPlay();

	for (TActorIterator<AJadgWalker> It(GetWorld()); It; ++It)
	{
		if (It->bPlayable)
		{
			Hero = *It;
			break;
		}
	}
	if (AJadgCameraPawn* View = Cast<AJadgCameraPawn>(GetPawn()))
	{
		if (Hero != nullptr)
		{
			View->SetActorLocation(Hero->GetActorLocation());
			View->Follow(Hero);
		}
	}

	FInputModeGameAndUI Mode;
	Mode.SetHideCursorDuringCapture(false);
	SetInputMode(Mode);
}

void AJadgPlayerController::PlayerTick(float DeltaSeconds)
{
	Super::PlayerTick(DeltaSeconds);

	AJadgCameraPawn* View = Cast<AJadgCameraPawn>(GetPawn());
	if (View == nullptr)
	{
		return;
	}

	float Turn = 0.0f;
	float Tilt = 0.0f;
	if (IsInputKeyDown(EKeys::A)) { Turn -= TurnDegreesPerSecond * DeltaSeconds; }
	if (IsInputKeyDown(EKeys::E)) { Turn += TurnDegreesPerSecond * DeltaSeconds; }
	if (IsInputKeyDown(EKeys::R)) { Tilt += TiltDegreesPerSecond * DeltaSeconds; }
	if (IsInputKeyDown(EKeys::F)) { Tilt -= TiltDegreesPerSecond * DeltaSeconds; }
	if (IsInputKeyDown(EKeys::RightMouseButton))
	{
		float DeltaX = 0.0f;
		float DeltaY = 0.0f;
		GetInputMouseDelta(DeltaX, DeltaY);
		Turn += DeltaX * MouseDegreesPerUnit;
		Tilt -= DeltaY * MouseDegreesPerUnit;
	}
	if (Turn != 0.0f) { View->AddYaw(Turn); }
	if (Tilt != 0.0f) { View->AddPitch(Tilt); }

	if (WasInputKeyJustPressed(EKeys::MouseScrollUp)) { View->Zoom(ZoomStep); }
	if (WasInputKeyJustPressed(EKeys::MouseScrollDown)) { View->Zoom(1.0f / ZoomStep); }

	FVector2D Move = FVector2D::ZeroVector;
	if (IsInputKeyDown(EKeys::Z) || IsInputKeyDown(EKeys::Up)) { Move.X += 1.0; }
	if (IsInputKeyDown(EKeys::S) || IsInputKeyDown(EKeys::Down)) { Move.X -= 1.0; }
	if (IsInputKeyDown(EKeys::D) || IsInputKeyDown(EKeys::Right)) { Move.Y += 1.0; }
	if (IsInputKeyDown(EKeys::Q) || IsInputKeyDown(EKeys::Left)) { Move.Y -= 1.0; }
	View->Pan(Move.GetSafeNormal() * PanCentimetresPerSecond * DeltaSeconds);

	if (WasInputKeyJustPressed(EKeys::SpaceBar) && Hero != nullptr)
	{
		View->Follow(Hero);
	}
	if (WasInputKeyJustPressed(EKeys::LeftMouseButton))
	{
		OrderWalk();
	}
}

void AJadgPlayerController::OrderWalk()
{
	if (Hero == nullptr)
	{
		return;
	}
	FHitResult Hit;
	if (!GetHitResultUnderCursor(ECC_Visibility, true, Hit))
	{
		return;
	}
	// Le point cliqué peut être un mur ou un toit : il est ramené sur le maillage de navigation.
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	FNavLocation OnMesh;
	if (Navigation != nullptr && Navigation->ProjectPointToNavigation(Hit.ImpactPoint, OnMesh, FVector(200.0, 200.0, 400.0)))
	{
		Hero->WalkTo(OnMesh.Location);
	}
}
