// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#include "Exploration/JadgDistrictLife.h"

#include "AIController.h"
#include "Characters/JadgAppearance.h"
#include "Characters/JadgWalker.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SceneComponent.h"
#include "CollisionShape.h"
#include "Engine/PointLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/FileManager.h"
#include "Json.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "Navigation/PathFollowingComponent.h"
#include "NavigationSystem.h"
#include "JustAnotherRpgGame.h"

AJadgDistrictLife::AJadgDistrictLife()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.2f;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("DistrictOrigin"));
	CrowdAppearances = {TEXT("district-citizen-manny"), TEXT("district-citizen-quinn")};
}

void AJadgDistrictLife::BeginPlay()
{
	Super::BeginPlay();
	StartedAt = GetWorld()->GetTimeSeconds();
	for (TActorIterator<APointLight> Light(GetWorld()); Light; ++Light)
	{
		if (Light->ActorHasTag(TEXT("JadgDistrictFlicker")))
		{
			FFlameLight& Saved = FlameLights.Emplace_GetRef();
			Saved.Component = Light->PointLightComponent;
			Saved.BaseIntensity = Light->PointLightComponent->Intensity;
			Saved.Phase = static_cast<float>(FlameLights.Num()) * 1.971f;
		}
	}
}

bool AJadgDistrictLife::TryPopulate()
{
	if (CrowdCount <= 0 || CrowdRouteLengths.IsEmpty())
	{
		return true;
	}
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	if (Navigation == nullptr || Navigation->IsNavigationBuildInProgress()
		|| Navigation->GetDefaultNavDataInstance(FNavigationSystem::DontCreate) == nullptr)
	{
		return false;
	}
	if (CrowdAppearances.IsEmpty() || !JadgAppearance::CreatorIsBuilt(TEXT("humanoid")))
	{
		++AppearanceFailures;
		UE_LOG(LogJadg, Error, TEXT("[DistrictLife] Mutable creator or appearance identifiers missing; no substitute population spawned"));
		return true;
	}
	TArray<TArray<FVector>> Routes;
	int32 Offset = 0;
	for (const int32 Length : CrowdRouteLengths)
	{
		if (Length < 2 || Offset + Length > CrowdPoints.Num())
		{
			++RejectedRoutes;
			Offset += FMath::Max(0, Length);
			continue;
		}
		TArray<FVector> Points;
		bool bValid = true;
		for (int32 PointIndex = 0; PointIndex < Length; ++PointIndex)
		{
			FNavLocation Projected;
			const FVector Asked = CrowdPoints[Offset + PointIndex];
			if (!Navigation->ProjectPointToNavigation(Asked, Projected, FVector(80.0, 80.0, 150.0))
				|| FMath::Abs(Projected.Location.Z - Asked.Z) > 100.0)
			{
				bValid = false;
				break;
			}
			Points.Add(Projected.Location);
		}
		Offset += Length;
		if (bValid)
		{
			Routes.Add(MoveTemp(Points));
		}
		else
		{
			++RejectedRoutes;
		}
	}
	if (Routes.IsEmpty())
	{
		UE_LOG(LogJadg, Error, TEXT("[DistrictLife] Authored citizen routes do not project to navigation"));
		return true;
	}
	const int32 Number = FMath::Clamp(CrowdCount, 0, 32);
	const AJadgWalker* Defaults = GetDefault<AJadgWalker>();
	const float HalfHeight = Defaults->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
	const float Radius = Defaults->GetCapsuleComponent()->GetUnscaledCapsuleRadius();
	const FCollisionShape Capsule = FCollisionShape::MakeCapsule(Radius, HalfHeight);
	const FCollisionQueryParams SpawnQuery(SCENE_QUERY_STAT(JadgDistrictResidentSpawn), false, this);
	ANavigationData* NavData = Navigation->GetDefaultNavDataInstance(FNavigationSystem::DontCreate);
	for (int32 Index = 0; Index < Number; ++Index)
	{
		const TArray<FVector>& Route = Routes[Index % Routes.Num()];
		const int32 StartIndex = (Index / Routes.Num()) % Route.Num();
		const FVector AskedGround = Route[StartIndex];
		AJadgWalker* Walker = nullptr;
		// Recast projects an agent centre, but an authored point can still be too
		// close to a decorative collider for the real capsule. Try nearby grounded
		// positions, checking full navigation and capsule clearance before spawn.
		for (int32 Attempt = 0; Attempt < 25 && Walker == nullptr; ++Attempt)
		{
			FVector Asked = AskedGround;
			if (Attempt > 0)
			{
				const float Angle = static_cast<float>((Attempt - 1) % 8) * UE_PI / 4.0f;
				const float SearchRadius = 60.0f * (1 + (Attempt - 1) / 8);
				Asked += FVector(FMath::Cos(Angle) * SearchRadius, FMath::Sin(Angle) * SearchRadius, 0.0);
			}
			FNavLocation Projected;
			if (!Navigation->ProjectPointToNavigation(Asked, Projected, FVector(40.0, 40.0, 100.0))
				|| FMath::Abs(Projected.Location.Z - AskedGround.Z) > 60.0)
			{
				++SpawnCandidateRejections;
				continue;
			}
			const FVector Centre = Projected.Location + FVector(0.0, 0.0, HalfHeight + 2.0f);
			if (GetWorld()->OverlapBlockingTestByProfile(Centre, FQuat::Identity, TEXT("Pawn"), Capsule, SpawnQuery))
			{
				++SpawnCandidateRejections;
				continue;
			}
			const FPathFindingQuery PathQuery(nullptr, *NavData, Projected.Location,
				Route[(StartIndex + 1) % Route.Num()]);
			const FPathFindingResult Path = Navigation->FindPathSync(PathQuery);
			if (!Path.IsSuccessful() || Path.IsPartial())
			{
				++SpawnCandidateRejections;
				continue;
			}
			const FTransform Placement(FRotator::ZeroRotator, Centre);
			Walker = GetWorld()->SpawnActorDeferred<AJadgWalker>(AJadgWalker::StaticClass(),
				Placement, this, nullptr, ESpawnActorCollisionHandlingMethod::AdjustIfPossibleButDontSpawnIfColliding);
			if (Walker == nullptr)
			{
				++SpawnCandidateRejections;
				continue;
			}
			Walker->Appearance = CrowdAppearances[Index % CrowdAppearances.Num()];
			Walker->WalkSpeed = ResidentWalkSpeed;
			Walker->PartyRank = -1;
			Walker->Tags.Add(TEXT("JadgDistrictResident"));
			Walker->FinishSpawning(Placement);
			// Deferred spawning can fail during FinishSpawning, before BeginPlay
			// applies the appearance. Do not misreport that as a missing asset.
			if (!IsValid(Walker) || Walker->IsActorBeingDestroyed())
			{
				++SpawnCandidateRejections;
				Walker = nullptr;
			}
		}
		if (Walker == nullptr)
		{
			++SpawnFailures;
			UE_LOG(LogJadg, Error, TEXT("[DistrictLife] Citizen %d has no capsule-clear grounded spawn near %s"),
				Index, *AskedGround.ToString());
			continue;
		}
		if (!Walker->bFromCreator || Walker->IdleClip == nullptr || Walker->WalkClip == nullptr)
		{
			++AppearanceFailures;
			UE_LOG(LogJadg, Error, TEXT("[DistrictLife] %s lacks Mutable body or animation clips"), *Walker->Appearance);
			Walker->Destroy();
			continue;
		}
		FResident& Resident = Residents.Emplace_GetRef();
		Resident.Walker = Walker;
		Resident.Route = Route;
		Resident.Destination = (StartIndex + 1) % Route.Num();
		Resident.PreviousFeet = Walker->Feet();
		Resident.WaitUntil = GetWorld()->GetTimeSeconds() + Index * 0.35;
		Resident.RequestedIndex = Index;
	}
	UE_LOG(LogJadg, Display, TEXT("[DistrictLife] %d animated residents, %d rejected routes, %d appearance failures, %d spawn failures, %d unsuitable placement candidates"),
		Residents.Num(), RejectedRoutes, AppearanceFailures, SpawnFailures, SpawnCandidateRejections);
	return true;
}

void AJadgDistrictLife::UpdateResident(FResident& Resident, double Now)
{
	AJadgWalker* Walker = Resident.Walker.Get();
	if (Walker == nullptr || Resident.Route.IsEmpty())
	{
		return;
	}
	const FVector Feet = Walker->Feet();
	Resident.TravelledCm += FVector::Dist2D(Feet, Resident.PreviousFeet);
	Resident.PreviousFeet = Feet;
	if (Now < Resident.WaitUntil)
	{
		return;
	}
	const FVector Target = Resident.Route[Resident.Destination];
	if (FVector::DistSquared2D(Feet, Target) <= FMath::Square(50.0)
		&& FMath::Abs(Feet.Z - Target.Z) < 100.0)
	{
		Walker->StopWalking();
		++Resident.Reached;
		Resident.Destination = (Resident.Destination + 1) % Resident.Route.Num();
		Resident.bOrdered = false;
		Resident.WaitUntil = Now + 1.0 + (Resident.Reached % 4) * 0.35;
		return;
	}
	AAIController* Controller = Cast<AAIController>(Walker->GetController());
	if (Controller == nullptr)
	{
		Walker->SpawnDefaultController();
		return;
	}
	if (Resident.bOrdered && Controller->GetMoveStatus() != EPathFollowingStatus::Idle)
	{
		if (Now - Resident.OrderedAt < 60.0)
		{
			return;
		}
		Walker->StopWalking();
	}
	// Complete paths only: an unreachable point is reported instead of endlessly
	// pretending to patrol a partial path. Routes remain authored, never teleported.
	const EPathFollowingRequestResult::Type Request = Controller->MoveToLocation(Target, 35.0f,
		false, true, false, false, nullptr, false);
	Resident.OrderedAt = Now;
	Resident.bOrdered = Request != EPathFollowingRequestResult::Failed;
	if (!Resident.bOrdered)
	{
		++Resident.RejectedPaths;
		Resident.WaitUntil = Now + 4.0;
	}
}

void AJadgDistrictLife::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const double Now = GetWorld()->GetTimeSeconds();
	for (const FFlameLight& Saved : FlameLights)
	{
		if (UPointLightComponent* Light = Saved.Component.Get())
		{
			const float Time = static_cast<float>(Now);
			Light->SetIntensity(Saved.BaseIntensity * (0.94f + 0.045f * FMath::Sin(Time * 11.0f + Saved.Phase)
				+ 0.015f * FMath::Sin(Time * 19.7f + Saved.Phase * 2.0f)));
		}
	}
	if (!bPopulationReady)
	{
		// Give the game, all collision components and dynamic navigation time to initialise.
		if (Now - StartedAt >= 2.0)
		{
			bPopulationReady = TryPopulate();
		}
		if (!bPopulationReady && Now - StartedAt > NavigationStartupTimeout)
		{
			bPopulationReady = true;
			++RejectedRoutes;
			UE_LOG(LogJadg, Error, TEXT("[DistrictLife] Navigation startup timed out; population was not spawned"));
		}
	}
	for (FResident& Resident : Residents)
	{
		UpdateResident(Resident, Now);
	}
}

FString AJadgDistrictLife::GetLifeReportJson() const
{
	const TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
	Report->SetBoolField(TEXT("ready"), bPopulationReady);
	Report->SetNumberField(TEXT("requestedResidents"), CrowdCount);
	Report->SetNumberField(TEXT("spawnedResidents"), Residents.Num());
	Report->SetNumberField(TEXT("rejectedRoutes"), RejectedRoutes);
	Report->SetNumberField(TEXT("appearanceFailures"), AppearanceFailures);
	Report->SetNumberField(TEXT("spawnFailures"), SpawnFailures);
	Report->SetNumberField(TEXT("spawnCandidateRejections"), SpawnCandidateRejections);
	Report->SetNumberField(TEXT("elapsedSeconds"), GetWorld() != nullptr ? GetWorld()->GetTimeSeconds() - StartedAt : 0.0);
	Report->SetStringField(TEXT("appearanceScope"), TEXT("Existing Mutable Manny/Quinn; civilian clothing unavailable, provisional visuals"));
	TArray<TSharedPtr<FJsonValue>> Entries;
	for (const FResident& Resident : Residents)
	{
		const TSharedRef<FJsonObject> Entry = MakeShared<FJsonObject>();
		const AJadgWalker* Walker = Resident.Walker.Get();
		Entry->SetBoolField(TEXT("alive"), Walker != nullptr);
		Entry->SetNumberField(TEXT("requestedIndex"), Resident.RequestedIndex);
		Entry->SetBoolField(TEXT("mutableBody"), Walker != nullptr && Walker->bFromCreator);
		Entry->SetBoolField(TEXT("animationClips"), Walker != nullptr && Walker->IdleClip != nullptr && Walker->WalkClip != nullptr);
		Entry->SetStringField(TEXT("appearance"), Walker != nullptr ? Walker->Appearance : FString{});
		Entry->SetNumberField(TEXT("travelledMetres"), Resident.TravelledCm / 100.0);
		Entry->SetNumberField(TEXT("waypointsReached"), Resident.Reached);
		Entry->SetNumberField(TEXT("pathRequestsRejected"), Resident.RejectedPaths);
		Entries.Add(MakeShared<FJsonValueObject>(Entry));
	}
	Report->SetArrayField(TEXT("residents"), Entries);
	FString Json;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
	FJsonSerializer::Serialize(Report, Writer);
	return Json;
}

void AJadgDistrictLife::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	const FString Json = GetLifeReportJson();
	UE_LOG(LogJadg, Display, TEXT("[DistrictLifeReport] %s"), *Json);
	FString ReportPath;
	if (!FParse::Value(FCommandLine::Get(), TEXT("JadgDistrictLifeReport="), ReportPath))
	{
		ReportPath = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Jadg/districts"),
			GetWorld()->GetMapName(), TEXT("life.json"));
	}
	IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportPath), true);
	if (!FFileHelper::SaveStringToFile(Json, *ReportPath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
	{
		UE_LOG(LogJadg, Error, TEXT("[DistrictLife] Could not write runtime report: %s"), *ReportPath);
	}
	for (const FFlameLight& Saved : FlameLights)
	{
		if (UPointLightComponent* Light = Saved.Component.Get())
		{
			Light->SetIntensity(Saved.BaseIntensity);
		}
	}
	for (const FResident& Resident : Residents)
	{
		if (AJadgWalker* Walker = Resident.Walker.Get())
		{
			Walker->Destroy();
		}
	}
	Super::EndPlay(EndPlayReason);
}
