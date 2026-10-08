// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Player/JadgCameraPawn.h"

#include "Camera/CameraComponent.h"
#include "GameFramework/SpringArmComponent.h"

AJadgCameraPawn::AJadgCameraPawn()
{
	PrimaryActorTick.bCanEverTick = true;

	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Target"));

	Arm = CreateDefaultSubobject<USpringArmComponent>(TEXT("Arm"));
	Arm->SetupAttachment(RootComponent);
	// Le décor ne rapproche pas la caméra : une façade entre elle et le héros se traite au LOT-1016.
	Arm->bDoCollisionTest = false;
	Arm->bUsePawnControlRotation = false;
	Arm->bEnableCameraLag = false;

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(Arm, USpringArmComponent::SocketName);
}

void AJadgCameraPawn::BeginPlay()
{
	Super::BeginPlay();
	Pitch = FMath::Clamp(StartPitch, MinPitch, MaxPitch);
	Distance = FMath::Clamp(StartDistance, MinDistance, MaxDistance);
	Yaw = GetActorRotation().Yaw;
	SetActorRotation(FRotator::ZeroRotator);
	ApplyArm();
}

void AJadgCameraPawn::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (Followed != nullptr)
	{
		// Les pieds de l'acteur, pas son centre : la hauteur visée ne dépend pas de sa capsule.
		FVector Origin;
		FVector Extent;
		Followed->GetActorBounds(true, Origin, Extent);
		const FVector Goal(Origin.X, Origin.Y, Origin.Z - Extent.Z + FollowHeight);
		SetActorLocation(FMath::VInterpTo(GetActorLocation(), Goal, DeltaSeconds, 6.0f));
	}
}

void AJadgCameraPawn::AddYaw(float Degrees)
{
	Yaw = FRotator::NormalizeAxis(Yaw + Degrees);
	ApplyArm();
}

void AJadgCameraPawn::AddPitch(float Degrees)
{
	Pitch = FMath::Clamp(Pitch + Degrees, MinPitch, MaxPitch);
	ApplyArm();
}

void AJadgCameraPawn::Zoom(float Factor)
{
	Distance = FMath::Clamp(Distance * Factor, MinDistance, MaxDistance);
	ApplyArm();
}

void AJadgCameraPawn::Pan(const FVector2D& ForwardRight)
{
	if (ForwardRight.IsNearlyZero())
	{
		return;
	}
	Followed = nullptr;
	const FRotator Heading(0.0f, Yaw, 0.0f);
	const FVector Forward = Heading.Vector();
	const FVector Right = FRotationMatrix(Heading).GetUnitAxis(EAxis::Y);
	AddActorWorldOffset(Forward * ForwardRight.X + Right * ForwardRight.Y);
}

void AJadgCameraPawn::Follow(AActor* Actor)
{
	Followed = Actor;
}

void AJadgCameraPawn::SetView(const FVector& Target, float InYaw, float PitchBelowHorizon, float InDistance)
{
	Followed = nullptr;
	SetActorLocation(Target);
	Yaw = InYaw;
	Pitch = PitchBelowHorizon;
	Distance = InDistance;
	ApplyArm();
}

void AJadgCameraPawn::ApplyArm()
{
	Arm->TargetArmLength = Distance;
	Arm->SetRelativeRotation(FRotator(-Pitch, Yaw, 0.0f));
}
