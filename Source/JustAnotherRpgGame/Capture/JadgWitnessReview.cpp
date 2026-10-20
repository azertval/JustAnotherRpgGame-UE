// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgWitnessReview.h"
#include "AI/Navigation/NavQueryFilter.h"
#include "Characters/JadgParty.h"
#include "Characters/JadgWalker.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Engine/World.h"
#include "Engine/Level.h"
#include "Engine/LevelStreaming.h"
#include "EngineUtils.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "HAL/FileManager.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformTime.h"
#include "JustAnotherRpgGame.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Parse.h"
#include "Misc/Paths.h"
#include "NavigationSystem.h"
#include "NavMesh/RecastNavMesh.h"
#include "Player/JadgCameraPawn.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "ShaderCompiler.h"

namespace
{
	TArray<TSharedPtr<FJsonValue>> Coordinates(const FVector& Point)
	{
		return {MakeShared<FJsonValueNumber>(Point.X), MakeShared<FJsonValueNumber>(Point.Y), MakeShared<FJsonValueNumber>(Point.Z)};
	}

	TArray<FName> TaggedIds(const TArray<FName>& ActorTags, const TArray<FName>& ComponentTags, const TCHAR* Prefix)
	{
		TArray<FName> Ids;
		const FString PrefixText(Prefix);
		auto Read = [&](const TArray<FName>& Tags)
		{
			for (FName Tag : Tags)
			{
				const FString Text = Tag.ToString();
				if (Text.StartsWith(PrefixText) && Text.Len() > PrefixText.Len())
				{
					Ids.AddUnique(FName(*Text.RightChop(PrefixText.Len())));
				}
			}
		};
		Read(ActorTags);
		Read(ComponentTags);
		return Ids;
	}
}

AJadgWitnessReview::AJadgWitnessReview()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PostUpdateWork;
}

void AJadgWitnessReview::BeginPlay()
{
	Super::BeginPlay();
	Started = FPlatformTime::Seconds();
	if (FParse::Value(FCommandLine::Get(), TEXT("JadgWitnessWalk="), ReportFile))
	{
		ReportFile = FPaths::ConvertRelativePathToFull(ReportFile);
		IFileManager::Get().MakeDirectory(*FPaths::GetPath(ReportFile), true);
	}
	// Always-loaded sublevels can arrive after this persistent actor begins play.
	LevelAddedHandle = FWorldDelegates::LevelAddedToWorld.AddUObject(this, &AJadgWitnessReview::OnLevelAdded);
	LevelRemovingHandle = FWorldDelegates::PreLevelRemovedFromWorld.AddUObject(this, &AJadgWitnessReview::OnLevelRemoving);
	GatherOccluders();
}

void AJadgWitnessReview::GatherOccluders(ULevel* Only)
{
	if (!bEnableCutaway || GetWorld() == nullptr)
	{
		RestoreOccluders();
		Occluders.Empty();
		return;
	}
	Occluders.RemoveAll([](const FOccluder& Saved) { return !Saved.Component.IsValid(); });
	TSet<UStaticMeshComponent*> Registered;
	for (const FOccluder& Saved : Occluders)
	{
		Registered.Add(Saved.Component.Get());
	}
	TArray<AActor*> Candidates;
	if (Only != nullptr)
	{
		Candidates = Only->Actors;
	}
	else
	{
		for (TActorIterator<AActor> It(GetWorld()); It; ++It)
		{
			Candidates.Add(*It);
		}
	}
	for (AActor* Actor : Candidates)
	{
		if (!IsValid(Actor))
		{
			continue;
		}
		TArray<UStaticMeshComponent*> Components;
		Actor->GetComponents(Components);
		for (UStaticMeshComponent* Component : Components)
		{
			if (Registered.Contains(Component))
			{
				continue;
			}
			const bool bDirect = Actor->ActorHasTag(OccluderTag) || Component->ComponentHasTag(OccluderTag);
			const TArray<FName> SupportIds = TaggedIds(Actor->Tags, Component->ComponentTags, TEXT("JadgWitnessSupport:"));
			if (!bDirect && SupportIds.IsEmpty())
			{
				continue;
			}
			FOccluder Saved;
			Saved.Component = Component;
			Saved.bDirect = bDirect;
			Saved.SupportIds = SupportIds;
			Saved.SurfaceIds = TaggedIds(Actor->Tags, Component->ComponentTags, TEXT("JadgWitnessSurface:"));
			Saved.CameraResponse = Component->GetCollisionResponseToChannel(ECC_Camera);
			Saved.VisibilityResponse = Component->GetCollisionResponseToChannel(ECC_Visibility);
			Saved.bHidden = Component->bHiddenInGame;
			Saved.bHiddenShadow = Component->bCastHiddenShadow;
			Saved.bHiddenIndirect = Component->bAffectIndirectLightingWhileHidden;
			if (bDirect && bIgnoreCameraCollision)
			{
				Component->SetCollisionResponseToChannel(ECC_Camera, ECR_Ignore);
			}
			Occluders.Add(Saved);
			Registered.Add(Component);
		}
	}
}

void AJadgWitnessReview::OnLevelAdded(ULevel* Level, UWorld* World)
{
	if (World == GetWorld())
	{
		GatherOccluders(Level);
		bNavigationRefreshPending = true;
		UE_LOG(LogJadg, Display, TEXT("[ArenaWitness] Streaming refresh: %d occluder components"), Occluders.Num());
	}
}

void AJadgWitnessReview::OnLevelRemoving(ULevel* Level, UWorld* World)
{
	if (World != GetWorld())
	{
		return;
	}
	bNavigationRefreshPending = true;
	// The pre-removal event still has live registered components to restore. A
	// null level denotes removal of every level during a map change.
	Occluders.RemoveAll([this, Level](FOccluder& Saved)
	{
		UStaticMeshComponent* Component = Saved.Component.Get();
		if (Component == nullptr)
		{
			return true;
		}
		if (Level == nullptr || (Component->GetOwner() != nullptr && Component->GetOwner()->GetLevel() == Level))
		{
			RestoreOccluder(Saved);
			return true;
		}
		return false;
	});
}

bool AJadgWitnessReview::PrepareFineNavigation()
{
	if (!bFineNavigation)
	{
		return true;
	}
	if (GetWorld() == nullptr)
	{
		return false;
	}
	// Do not rebuild on each intermediate streaming notification. Wait until
	// requested levels and their collision components are present in this world.
	for (ULevelStreaming* Streaming : GetWorld()->GetStreamingLevels())
	{
		if (Streaming != nullptr && ((Streaming->ShouldBeLoaded() && !Streaming->IsLevelLoaded())
			|| (Streaming->ShouldBeVisible() && !Streaming->IsLevelVisible())))
		{
			return false;
		}
	}
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	if (Navigation == nullptr)
	{
		return false;
	}
	TArray<ARecastNavMesh*> RecastMeshes;
	bool bSettingsChanged = false;
	bool bQuerySettingsChanged = false;
	for (TActorIterator<ARecastNavMesh> It(GetWorld()); It; ++It)
	{
		RecastMeshes.Add(*It);
		bSettingsChanged |= !FMath::IsNearlyEqual(It->SimplificationElevationRatio, NavigationElevationRatio);
		bSettingsChanged |= NavigationTileSize > 0.0f && !FMath::IsNearlyEqual(It->TileSizeUU, NavigationTileSize);
		bSettingsChanged |= NavigationAverageLayers > 0.0f && !FMath::IsNearlyEqual(It->AverageLayersPerTile, NavigationAverageLayers);
		bSettingsChanged |= NavigationMaxSimplificationError >= 0.0f
			&& !FMath::IsNearlyEqual(It->MaxSimplificationError, NavigationMaxSimplificationError);
		bQuerySettingsChanged |= NavigationMaxSearchNodes > 0
			&& (!FMath::IsNearlyEqual(It->DefaultMaxSearchNodes, static_cast<float>(NavigationMaxSearchNodes))
				|| !FMath::IsNearlyEqual(It->DefaultMaxHierarchicalSearchNodes, static_cast<float>(NavigationMaxSearchNodes))
				|| It->GetDefaultQueryFilter()->GetMaxSearchNodes() != static_cast<uint32>(NavigationMaxSearchNodes));
		for (uint8 Index = 0; Index < static_cast<uint8>(ENavigationDataResolution::MAX); ++Index)
		{
			const ENavigationDataResolution Resolution = static_cast<ENavigationDataResolution>(Index);
			bSettingsChanged |= !FMath::IsNearlyEqual(It->GetCellSize(Resolution), NavigationCellSize)
				|| !FMath::IsNearlyEqual(It->GetCellHeight(Resolution), NavigationCellHeight);
		}
	}
	if (RecastMeshes.IsEmpty())
	{
		return false;
	}
	if (bQuerySettingsChanged)
	{
		for (ARecastNavMesh* Mesh : RecastMeshes)
		{
			Mesh->DefaultMaxSearchNodes = static_cast<float>(NavigationMaxSearchNodes);
			Mesh->DefaultMaxHierarchicalSearchNodes = static_cast<float>(NavigationMaxSearchNodes);
			Mesh->RecreateDefaultFilter();
		}
	}
	// In a played world (no route report), the local profile is applied once and Recast builds
	// asynchronously, nearest tiles first: a synchronous build froze the game for half a minute,
	// again for every World Partition cell streamed in (demo of the capital, 20 October 2026).
	// Dynamic generation already rebuilds the tiles a streamed cell touches.
	const bool bBlocking = !GetWorld()->IsGameWorld() || !ReportFile.IsEmpty();
	// A navigation mesh baked with its map (Static, World Partition chunks streamed with the
	// cells : WorldPartitionNavigationDataBuilder, capitale_demo.py) is never rebuilt in game :
	// its tiles were generated with the fine profile. Only the query limits apply.
	if (GetWorld()->IsGameWorld() && RecastMeshes.ContainsByPredicate([](const ARecastNavMesh* Mesh)
		{ return Mesh->GetRuntimeGenerationMode() == ERuntimeGenerationType::Static; }))
	{
		bNavigationRefreshPending = false;
		return true;
	}
	if (!bBlocking && !bSettingsChanged)
	{
		bNavigationRefreshPending = false;
	}
	if (bNavigationRefreshPending || bSettingsChanged)
	{
		// Stop automatic runtime generation before mutating its owning actor. Build
		// again with local values; Navigation->Build also waits for completion.
		Navigation->CancelBuild();
		for (ARecastNavMesh* Mesh : RecastMeshes)
		{
			Mesh->EnsureBuildCompletion();
			for (uint8 Index = 0; Index < static_cast<uint8>(ENavigationDataResolution::MAX); ++Index)
			{
				const ENavigationDataResolution Resolution = static_cast<ENavigationDataResolution>(Index);
				Mesh->SetCellSize(Resolution, FMath::Max(1.0f, NavigationCellSize));
				Mesh->SetCellHeight(Resolution, FMath::Max(1.0f, NavigationCellHeight));
			}
			Mesh->SimplificationElevationRatio = FMath::Clamp(NavigationElevationRatio, 0.0f, 1.0f);
			if (NavigationTileSize > 0.0f)
			{
				Mesh->TileSizeUU = NavigationTileSize;
			}
			if (NavigationAverageLayers > 0.0f)
			{
				Mesh->AverageLayersPerTile = NavigationAverageLayers;
			}
			if (NavigationMaxSimplificationError >= 0.0f)
			{
				Mesh->MaxSimplificationError = NavigationMaxSimplificationError;
			}
		}
		if (bBlocking)
		{
			Navigation->Build();
			for (ARecastNavMesh* Mesh : RecastMeshes)
			{
				Mesh->EnsureBuildCompletion();
			}
		}
		else
		{
			for (ARecastNavMesh* Mesh : RecastMeshes)
			{
				Mesh->RebuildAll();
			}
		}
		bNavigationRefreshPending = false;
		++FineNavigationBuilds;
		UE_LOG(LogJadg, Display, TEXT("[ArenaWitness] Local navigation %s: %d meshes, cells %.1f x %.1f cm, elevation %.2f"),
			bBlocking ? TEXT("completed") : TEXT("rebuilding in the background"), RecastMeshes.Num(), NavigationCellSize,
			NavigationCellHeight, NavigationElevationRatio);
	}
	return !Navigation->IsNavigationBuildInProgress();
}

FString AJadgWitnessReview::GetNavigationSettingsJson() const
{
	TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
	TArray<TSharedPtr<FJsonValue>> Meshes;
	if (GetWorld() != nullptr)
	{
		for (TActorIterator<ARecastNavMesh> It(GetWorld()); It; ++It)
		{
			TSharedRef<FJsonObject> Settings = MakeShared<FJsonObject>();
			Settings->SetStringField(TEXT("actor"), It->GetPathName());
			Settings->SetNumberField(TEXT("tileSizeCm"), It->TileSizeUU);
			Settings->SetNumberField(TEXT("averageLayers"), It->AverageLayersPerTile);
			Settings->SetNumberField(TEXT("maxSimplificationError"), It->MaxSimplificationError);
			Settings->SetNumberField(TEXT("elevationRatio"), It->SimplificationElevationRatio);
			Settings->SetNumberField(TEXT("maxSearchNodes"), It->DefaultMaxSearchNodes);
			Settings->SetNumberField(TEXT("maxHierarchicalSearchNodes"), It->DefaultMaxHierarchicalSearchNodes);
			Settings->SetNumberField(TEXT("filterMaxSearchNodes"), It->GetDefaultQueryFilter()->GetMaxSearchNodes());
			Settings->SetArrayField(TEXT("defaultQueryExtentCm"), Coordinates(It->GetDefaultQueryExtent()));
			TArray<TSharedPtr<FJsonValue>> Resolutions;
			for (uint8 Index = 0; Index < static_cast<uint8>(ENavigationDataResolution::MAX); ++Index)
			{
				const ENavigationDataResolution Resolution = static_cast<ENavigationDataResolution>(Index);
				TSharedRef<FJsonObject> Params = MakeShared<FJsonObject>();
				Params->SetNumberField(TEXT("cellSizeCm"), It->GetCellSize(Resolution));
				Params->SetNumberField(TEXT("cellHeightCm"), It->GetCellHeight(Resolution));
				Resolutions.Add(MakeShared<FJsonValueObject>(Params));
			}
			Settings->SetArrayField(TEXT("resolutions"), Resolutions);
			Meshes.Add(MakeShared<FJsonValueObject>(Settings));
		}
	}
	Report->SetArrayField(TEXT("meshes"), Meshes);
	FString Json;
	FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
	return Json;
}

void AJadgWitnessReview::UpdateCutaway(const FVector& Camera, const FVector& Target)
{
	FCollisionQueryParams Query(SCENE_QUERY_STAT(JadgWitnessCutaway), true);
	TArray<bool> Cuts;
	Cuts.Init(false, Occluders.Num());
	TMap<FName, TArray<int32>> Dependents;
	TSet<FName> CutSurfaces;
	TArray<FName> PendingSurfaces;
	auto EnqueueSurfaces = [&](const FOccluder& Saved)
	{
		for (FName Id : Saved.SurfaceIds)
		{
			if (!CutSurfaces.Contains(Id))
			{
				CutSurfaces.Add(Id);
				PendingSurfaces.Add(Id);
			}
		}
	};
	// First evaluate real camera intersections independently of dependency order.
	// A prop without the occluder tag never acquires its own ray-based cut.
	for (int32 Index = 0; Index < Occluders.Num(); ++Index)
	{
		const FOccluder& Saved = Occluders[Index];
		UStaticMeshComponent* Component = Saved.Component.Get();
		if (Component == nullptr || Saved.bHidden || !Component->GetVisibleFlag())
		{
			continue;
		}
		for (FName Id : Saved.SupportIds)
		{
			Dependents.FindOrAdd(Id).Add(Index);
		}
		FHitResult Hit;
		// Query each component itself: hidden components still block character physics,
		// and all obstacles along the segment are found, not only the first world hit.
		// The bounds first: a complex trace per occluder and per frame (two thousand in the
		// arena of the capital) cost more than the frame itself.
		const FBox Bounds = Component->Bounds.GetBox();
		Cuts[Index] = bEnableCutaway && Saved.bDirect
			&& (Bounds.IsInside(Camera) || Bounds.IsInside(Target)
				|| FMath::LineBoxIntersection(Bounds, Camera, Target, Target - Camera))
			&& Component->LineTraceComponent(Hit, Camera, Target, Query);
		if (Cuts[Index])
		{
			EnqueueSurfaces(Saved);
		}
	}
	// Propagate support cuts, including surfaces which are themselves supported.
	// Each component/surface is enqueued once; cycles cannot create a cut alone.
	for (int32 Cursor = 0; Cursor < PendingSurfaces.Num(); ++Cursor)
	{
		if (const TArray<int32>* Children = Dependents.Find(PendingSurfaces[Cursor]))
		{
			for (int32 Index : *Children)
			{
				if (!Cuts[Index])
				{
					Cuts[Index] = true;
					EnqueueSurfaces(Occluders[Index]);
				}
			}
		}
	}
	for (int32 Index = 0; Index < Occluders.Num(); ++Index)
	{
		FOccluder& Saved = Occluders[Index];
		UStaticMeshComponent* Component = Saved.Component.Get();
		if (Component == nullptr || Saved.bHidden || !Component->GetVisibleFlag())
		{
			continue;
		}
		const bool bCutNow = Cuts[Index];
		if (bCutNow != Saved.bCut)
		{
			if (bCutNow)
			{
				++CutEvents;
				Component->SetCastHiddenShadow(bKeepHiddenShadows || Saved.bHiddenShadow);
				Component->SetAffectIndirectLightingWhileHidden(bKeepHiddenIndirectLighting || Saved.bHiddenIndirect);
			}
			Component->SetHiddenInGame(bCutNow);
			// The invisible roof must not intercept the player's ground click. The
			// direct component trace above still finds its geometry on later frames.
			Component->SetCollisionResponseToChannel(ECC_Visibility, bCutNow ? ECR_Ignore : Saved.VisibilityResponse);
			if (!bCutNow)
			{
				Component->SetCastHiddenShadow(Saved.bHiddenShadow);
				Component->SetAffectIndirectLightingWhileHidden(Saved.bHiddenIndirect);
			}
			Saved.bCut = bCutNow;
		}
	}
}

void AJadgWitnessReview::RestoreOccluder(FOccluder& Saved)
{
	if (UStaticMeshComponent* Component = Saved.Component.Get())
	{
		Component->SetHiddenInGame(Saved.bHidden);
		Component->SetCastHiddenShadow(Saved.bHiddenShadow);
		Component->SetAffectIndirectLightingWhileHidden(Saved.bHiddenIndirect);
		Component->SetCollisionResponseToChannel(ECC_Camera, Saved.CameraResponse);
		Component->SetCollisionResponseToChannel(ECC_Visibility, Saved.VisibilityResponse);
		Saved.bCut = false;
	}
}

void AJadgWitnessReview::RestoreOccluders()
{
	for (FOccluder& Saved : Occluders)
	{
		RestoreOccluder(Saved);
	}
}

bool AJadgWitnessReview::NavigationWaitTimedOut(double Now) const
{
	if (ReportFile.IsEmpty() || bDone)
	{
		return false;
	}
	return Now - (bWalking ? LegStarted : Started) > (bWalking ? LegTimeout : StartupTimeout);
}

void AJadgWitnessReview::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	for (TActorIterator<AJadgCameraPawn> Camera(GetWorld()); Camera; ++Camera)
	{
		UpdateCutaway(Camera->GetCameraLocation(), Camera->GetActorLocation());
		break;
	}
	if (!PrepareFineNavigation())
	{
		if (NavigationWaitTimedOut(FPlatformTime::Seconds()))
		{
			Finish(1, bWalking ? TEXT("navigation/streaming timeout during route")
				: TEXT("startup timeout: navigation/streaming not ready"));
		}
		return;
	}
	if (ReportFile.IsEmpty() || bDone)
	{
		return;
	}
	AJadgParty* Party = AJadgParty::Find(GetWorld());
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	if (!bWalking)
	{
		if (FPlatformTime::Seconds() - Started > StartupTimeout)
		{
			Finish(1, TEXT("startup timeout: leader/navigation/shaders not ready"));
			return;
		}
		if (Party == nullptr || Party->Leader() == nullptr || Navigation == nullptr || Navigation->IsNavigationBuildInProgress()
			|| (GShaderCompilingManager != nullptr && GShaderCompilingManager->IsCompiling())
			|| GetWorld()->GetTimeSeconds() < 2.0)
		{
			return;
		}
		StartWalk(*Party);
	}
	if (bWalking && !bDone && Party != nullptr && Party->Leader() != nullptr)
	{
		TickWalk(*Party, DeltaSeconds);
	}
	else if (bWalking && !bDone)
	{
		Finish(1, TEXT("leader disappeared during walk"));
	}
}

void AJadgWitnessReview::StartWalk(AJadgParty& Party)
{
	if (RoutePoints.IsEmpty())
	{
		Finish(1, TEXT("route_points is empty"));
		return;
	}
	WalkPoints = RoutePoints;
	PreviousFeet = Party.Leader()->Feet();
	if (bWalkReturn)
	{
		for (int32 Index = RoutePoints.Num() - 2; Index >= 0; --Index)
		{
			WalkPoints.Add(RoutePoints[Index]);
		}
		WalkPoints.Add(PreviousFeet);
	}
	bWalking = true;
	LegStarted = FPlatformTime::Seconds();
	Sample(Party, false);
	UE_LOG(LogJadg, Display, TEXT("[ArenaWitness] Walking %d points, return=%s, without teleport or portal"),
		WalkPoints.Num(), bWalkReturn ? TEXT("true") : TEXT("false"));
}

void AJadgWitnessReview::TickWalk(AJadgParty& Party, float DeltaSeconds)
{
	AJadgWalker& Leader = *Party.Leader();
	const FVector Feet = Leader.Feet();
	// A portal/placement jump cannot silently pass a point. Allow ordinary step-up
	// and falling velocity, while rejecting discontinuities larger than 3 metres.
	const double MaxTravel = FMath::Max(300.0, Leader.GetVelocity().Size() * FMath::Max(DeltaSeconds, 0.0f) * 2.0 + 100.0);
	if (FVector::Distance(Feet, PreviousFeet) > MaxTravel)
	{
		Sample(Party, false);
		Finish(1, TEXT("discontinuous movement detected"));
		return;
	}
	PreviousFeet = Feet;
	const double Now = FPlatformTime::Seconds();
	if (Now - LastSample >= SampleInterval)
	{
		Sample(Party, false);
	}
	const FVector Destination = WalkPoints[PointIndex];
	if (FVector::Dist2D(Feet, Destination) <= PointTolerance && FMath::Abs(Feet.Z - Destination.Z) <= HeightTolerance)
	{
		Leader.StopWalking();
		Sample(Party, true);
		UE_LOG(LogJadg, Display, TEXT("[ArenaWitness] Point %d reached: %.1f %.1f %.1f cm"), PointIndex, Feet.X, Feet.Y, Feet.Z);
		++PointIndex;
		Orders = 0;
		LegStarted = Now;
		if (PointIndex == WalkPoints.Num())
		{
			Finish(0, TEXT("round trip completed"));
		}
		return;
	}
	if (Now - LegStarted > LegTimeout)
	{
		Sample(Party, false);
		Finish(1, FString::Printf(TEXT("point %d timeout; feet %.1f %.1f %.1f cm"), PointIndex, Feet.X, Feet.Y, Feet.Z));
		return;
	}
	if (Orders == 0 || (!Leader.IsWalking() && Now - LastOrder > 1.0))
	{
		if (Orders >= 3)
		{
			Finish(1, FString::Printf(TEXT("point %d stopped outside XY/Z tolerance after three orders"), PointIndex));
			return;
		}
		UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
		FNavLocation Projected;
		if (Navigation == nullptr || !Navigation->ProjectPointToNavigation(Destination, Projected, FVector(50.0, 50.0, HeightTolerance)))
		{
			Finish(1, FString::Printf(TEXT("point %d has no navigation at requested height"), PointIndex));
			return;
		}
		Party.OrderWalk(Destination);
		LastOrder = Now;
		++Orders;
	}
}

void AJadgWitnessReview::Sample(const AJadgParty& Party, bool bReached)
{
	LastSample = FPlatformTime::Seconds();
	TSharedPtr<FJsonObject> Entry = MakeShared<FJsonObject>();
	Entry->SetNumberField(TEXT("seconds"), LastSample - Started);
	Entry->SetNumberField(TEXT("point"), PointIndex);
	Entry->SetArrayField(TEXT("feetCm"), Coordinates(Party.Leader()->Feet()));
	Entry->SetBoolField(TEXT("reached"), bReached);
	if (WalkPoints.IsValidIndex(PointIndex))
	{
		Entry->SetArrayField(TEXT("targetCm"), Coordinates(WalkPoints[PointIndex]));
	}
	TArray<TSharedPtr<FJsonValue>> Members;
	for (const AJadgWalker* Member : Party.GetMembers())
	{
		if (Member != nullptr)
		{
			Members.Add(MakeShared<FJsonValueArray>(Coordinates(Member->Feet())));
		}
	}
	Entry->SetArrayField(TEXT("membersFeetCm"), Members);
	int32 CutCount = 0;
	for (const FOccluder& Item : Occluders)
	{
		CutCount += Item.bCut ? 1 : 0;
	}
	Entry->SetNumberField(TEXT("cutComponents"), CutCount);
	for (TActorIterator<AJadgCameraPawn> Camera(GetWorld()); Camera; ++Camera)
	{
		Entry->SetArrayField(TEXT("cameraCm"), Coordinates(Camera->GetCameraLocation()));
		Entry->SetArrayField(TEXT("cameraTargetCm"), Coordinates(Camera->GetActorLocation()));
		break;
	}
	const TSharedPtr<FJsonValue> Value = MakeShared<FJsonValueObject>(Entry);
	Samples.Add(Value);
	if (bReached)
	{
		Reached.Add(Value);
	}
}

void AJadgWitnessReview::Finish(int32 ExitCode, const FString& Reason)
{
	if (bDone)
	{
		return;
	}
	bDone = true;
	TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
	Report->SetBoolField(TEXT("completed"), ExitCode == 0);
	Report->SetNumberField(TEXT("exitCode"), ExitCode);
	Report->SetStringField(TEXT("reason"), Reason);
	Report->SetBoolField(TEXT("return"), bWalkReturn);
	Report->SetNumberField(TEXT("pointsPlanned"), WalkPoints.Num());
	Report->SetNumberField(TEXT("pointsReached"), PointIndex);
	Report->SetNumberField(TEXT("seconds"), FPlatformTime::Seconds() - Started);
	Report->SetNumberField(TEXT("cutEvents"), CutEvents);
	Report->SetNumberField(TEXT("occluderComponents"), Occluders.Num());
	Report->SetBoolField(TEXT("fineNavigation"), bFineNavigation);
	Report->SetNumberField(TEXT("fineNavigationBuilds"), FineNavigationBuilds);
	Report->SetStringField(TEXT("effectiveNavigationJson"), GetNavigationSettingsJson());
	if (bFineNavigation)
	{
		Report->SetNumberField(TEXT("navigationCellSizeCm"), NavigationCellSize);
		Report->SetNumberField(TEXT("navigationCellHeightCm"), NavigationCellHeight);
		Report->SetNumberField(TEXT("navigationElevationRatio"), NavigationElevationRatio);
	}
	Report->SetNumberField(TEXT("xyToleranceCm"), PointTolerance);
	Report->SetNumberField(TEXT("zToleranceCm"), HeightTolerance);
	Report->SetStringField(TEXT("cutaway"), TEXT("hard visibility cut; physics retained; original component lighting flags preserved"));
	Report->SetBoolField(TEXT("forceHiddenShadows"), bKeepHiddenShadows);
	Report->SetBoolField(TEXT("forceHiddenIndirectLighting"), bKeepHiddenIndirectLighting);
	Report->SetArrayField(TEXT("samples"), Samples);
	Report->SetArrayField(TEXT("reached"), Reached);
	if (AJadgParty* Party = AJadgParty::Find(GetWorld()); Party != nullptr && Party->Leader() != nullptr)
	{
		AJadgWalker& Leader = *Party->Leader();
		Leader.StopWalking();
		const UCapsuleComponent& Capsule = *Leader.GetCapsuleComponent();
		const UCharacterMovementComponent& Movement = *Leader.GetCharacterMovement();
		Report->SetNumberField(TEXT("capsuleRadiusCm"), Capsule.GetScaledCapsuleRadius());
		Report->SetNumberField(TEXT("capsuleHalfHeightCm"), Capsule.GetScaledCapsuleHalfHeight());
		Report->SetNumberField(TEXT("maxStepHeightCm"), Movement.MaxStepHeight);
		Report->SetNumberField(TEXT("walkableFloorAngleDegrees"), Movement.GetWalkableFloorAngle());
		Report->SetNumberField(TEXT("maxWalkSpeedCmPerSecond"), Movement.MaxWalkSpeed);
	}
	FString Json;
	FJsonSerializer::Serialize(Report, TJsonWriterFactory<>::Create(&Json));
	if (!FFileHelper::SaveStringToFile(Json, *ReportFile, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
	{
		ExitCode = 1;
		UE_LOG(LogJadg, Error, TEXT("[ArenaWitness] Could not write %s"), *ReportFile);
	}
	UE_LOG(LogJadg, Display, TEXT("[ArenaWitness] %s; report %s"), *Reason, *ReportFile);
	RestoreOccluders();
	FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(ExitCode));
}

void AJadgWitnessReview::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	FWorldDelegates::LevelAddedToWorld.Remove(LevelAddedHandle);
	FWorldDelegates::PreLevelRemovedFromWorld.Remove(LevelRemovingHandle);
	RestoreOccluders();
	Occluders.Empty();
	Super::EndPlay(EndPlayReason);
}
