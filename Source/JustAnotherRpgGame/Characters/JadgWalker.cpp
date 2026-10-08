// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Characters/JadgWalker.h"

#include "AIController.h"
#include "Animation/AnimSequence.h"
#include "Components/SkeletalMeshComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Navigation/PathFollowingComponent.h"

AJadgWalker::AJadgWalker()
{
	PrimaryActorTick.bCanEverTick = true;

	AIControllerClass = AAIController::StaticClass();
	AutoPossessAI = EAutoPossessAI::PlacedInWorldOrSpawned;

	// Le personnage regarde où il va ; il ne suit pas le regard d'un contrôleur.
	bUseControllerRotationYaw = false;
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->bOrientRotationToMovement = true;
	Movement->RotationRate = FRotator(0.0f, 540.0f, 0.0f);
	// Le chemin se suit à l'accélération du mouvement, pas à vitesse imposée : le clip s'y règle.
	Movement->bRequestedMoveUseAcceleration = true;

	GetMesh()->SetAnimationMode(EAnimationMode::AnimationSingleNode);
}

void AJadgWalker::BeginPlay()
{
	Super::BeginPlay();
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	Play(IdleClip);
}

void AJadgWalker::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const float Speed = GetVelocity().Size2D();
	const bool bNowWalking = Speed > 5.0f;
	if (bNowWalking != bWalking)
	{
		bWalking = bNowWalking;
		Play(bWalking ? WalkClip : IdleClip);
	}
	if (bWalking && WalkSpeed > 0.0f)
	{
		GetMesh()->SetPlayRate(Speed / WalkSpeed);
	}

	if (!Patrol.IsEmpty())
	{
		const AAIController* AI = Cast<AAIController>(GetController());
		if (AI != nullptr && AI->GetMoveStatus() == EPathFollowingStatus::Idle)
		{
			WalkTo(Patrol[PatrolIndex]);
			PatrolIndex = (PatrolIndex + 1) % Patrol.Num();
		}
	}
}

void AJadgWalker::WalkTo(const FVector& Destination)
{
	if (AAIController* AI = Cast<AAIController>(GetController()))
	{
		AI->MoveToLocation(Destination, 5.0f, false);
	}
}

void AJadgWalker::Play(UAnimSequence* Clip)
{
	if (Clip != nullptr)
	{
		GetMesh()->PlayAnimation(Clip, true);
		GetMesh()->SetPlayRate(1.0f);
	}
}
