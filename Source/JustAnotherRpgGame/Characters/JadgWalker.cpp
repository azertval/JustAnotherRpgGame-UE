// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Characters/JadgWalker.h"

#include "AIController.h"
#include "Characters/JadgAppearance.h"
#include "JustAnotherRpgGame.h"
#include "Animation/AnimSequence.h"
#include "Components/CapsuleComponent.h"
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
	// Un personnage entre le point visé et la caméra ne la rapproche pas : ni son maillage, ni sa
	// capsule, que le profil « Pawn » du moteur oppose à la sonde de la caméra.
	GetMesh()->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
}

void AJadgWalker::BeginPlay()
{
	Super::BeginPlay();
	GetCharacterMovement()->MaxWalkSpeed = WalkSpeed;
	// Les personnages se bloquent entre eux (LOT-1017) et s'évitent : un PNJ se désigne au clic.
	SetInCombat(false);
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
	if (!EntityId.IsEmpty())
	{
		GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	}
	if (!Appearance.IsEmpty())
	{
		FString Erreur;
		if (!JadgAppearance::Apply(*this, Appearance, Erreur))
		{
			UE_LOG(LogJadg, Error, TEXT("[Personnage] %s : %s"), *GetName(), *Erreur);
		}
	}
	Play(IdleClip);
}

bool AJadgWalker::PlayOnce(FName Clip)
{
	UAnimSequence* Once = Clips.FindRef(Clip);
	if (Once == nullptr)
	{
		return false;
	}
	GetMesh()->PlayAnimation(Once, false);
	GetMesh()->SetPlayRate(1.0f);
	bWalking = false;
	bHolding = false;
	OnceUntil = GetWorld()->GetTimeSeconds() + FMath::Max(Once->GetPlayLength(), 0.05f);
	return true;
}

bool AJadgWalker::PlayAndHold(FName Clip)
{
	if (!PlayOnce(Clip))
	{
		return false;
	}
	OnceUntil = 0.0;
	bHolding = true;
	return true;
}

void AJadgWalker::ReturnToRest()
{
	OnceUntil = 0.0;
	bHolding = false;
	bWalking = false;
	Play(IdleClip);
}

float AJadgWalker::ClipSeconds(FName Clip) const
{
	const UAnimSequence* Found = Clips.FindRef(Clip);
	return Found != nullptr ? Found->GetPlayLength() : 0.0f;
}

float AJadgWalker::ImpactSeconds(FName Clip) const
{
	if (const float* Key = ClipKeys.Find(Clip))
	{
		return *Key;
	}
	return ClipSeconds(Clip) / 2.0f;
}

void AJadgWalker::SetInCombat(bool bInCombat)
{
	UCharacterMovementComponent* Movement = GetCharacterMovement();
	// Hors combat, la capsule bloque les autres personnages et l'évitement les écarte ; en combat,
	// Core tient l'espace et la figurine suit le chemin payé.
	SetBlocksCharacters(!bInCombat);
	Movement->SetAvoidanceEnabled(!bInCombat);
	Movement->AvoidanceConsiderationRadius = 200.0f;
	Movement->AvoidanceWeight = 0.5f;
	// En combat, chaque combattant se désigne au clic, comme un PNJ.
	if (bInCombat || !EntityId.IsEmpty())
	{
		GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
	}
}

void AJadgWalker::SetBlocksCharacters(bool bBlocks)
{
	GetCapsuleComponent()->SetCollisionResponseToChannel(ECC_Pawn, bBlocks ? ECR_Block : ECR_Ignore);
}

void AJadgWalker::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	const float Speed = GetVelocity().Size2D();
	const bool bNowWalking = Speed > 5.0f;
	if (OnceUntil > 0.0 && GetWorld()->GetTimeSeconds() >= OnceUntil)
	{
		// Le clip joué une fois est fini : retour au repos, ou à la marche.
		OnceUntil = 0.0;
		bWalking = bNowWalking;
		Play(bWalking ? WalkClip : IdleClip);
	}
	if (bHolding || OnceUntil > 0.0)
	{
		// Un geste ou une pose tenue ne s'interrompt pas pour la marche.
	}
	else if (bNowWalking != bWalking)
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

void AJadgWalker::WalkTo(const FVector& Destination, float AcceptanceRadius)
{
	if (AAIController* AI = Cast<AAIController>(GetController()))
	{
		AI->MoveToLocation(Destination, AcceptanceRadius, false);
	}
}

void AJadgWalker::StopWalking()
{
	if (AAIController* AI = Cast<AAIController>(GetController()))
	{
		AI->StopMovement();
	}
}

bool AJadgWalker::IsWalking() const
{
	const AAIController* AI = Cast<AAIController>(GetController());
	return AI != nullptr && AI->GetMoveStatus() != EPathFollowingStatus::Idle;
}

void AJadgWalker::StandOn(const FVector& Ground, float Yaw)
{
	StopWalking();
	const FVector Centre = Ground + FVector(0.0, 0.0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
	SetActorLocationAndRotation(Centre, FRotator(0.0f, Yaw, 0.0f), false, nullptr, ETeleportType::TeleportPhysics);
}

FVector AJadgWalker::Feet() const
{
	return GetActorLocation() - FVector(0.0, 0.0, GetCapsuleComponent()->GetScaledCapsuleHalfHeight());
}

void AJadgWalker::SetOutlined(bool bOutlined)
{
	GetMesh()->SetRenderCustomDepth(bOutlined);
	GetMesh()->SetCustomDepthStencilValue(bOutlined ? 1 : 0);
}

void AJadgWalker::Play(UAnimSequence* Clip)
{
	if (Clip != nullptr)
	{
		GetMesh()->PlayAnimation(Clip, true);
		GetMesh()->SetPlayRate(1.0f);
	}
}
