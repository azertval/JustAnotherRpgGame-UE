// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgWitnessReview.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgWitnessCutawayTest, "Jadg.Witness.CutawayRestoresPhysicsAndLighting",
	EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::EngineFilter)

bool FJadgWitnessCutawayTest::RunTest(const FString& Parameters)
{
	UGameInstance* Instance = NewObject<UGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("JadgWitnessCutaway"));
	UWorld* World = Instance->GetWorld();
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (!TestNotNull(TEXT("world"), World) || !TestNotNull(TEXT("collision cube"), Cube))
	{
		Instance->Shutdown();
		return false;
	}
	auto Block = [&](const FVector& Centre, bool bActorTag, bool bComponentTag)
	{
		AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(Centre, FRotator::ZeroRotator);
		UStaticMeshComponent* Component = Actor->GetStaticMeshComponent();
		Component->SetMobility(EComponentMobility::Movable);
		Component->SetStaticMesh(Cube);
		Component->SetCollisionProfileName(TEXT("BlockAll"));
		Component->SetCastHiddenShadow(false);
		Component->SetAffectIndirectLightingWhileHidden(false);
		if (bActorTag)
		{
			Actor->Tags.Add(TEXT("JadgWitnessOccluder"));
		}
		if (bComponentTag)
		{
			Component->ComponentTags.Add(TEXT("JadgWitnessOccluder"));
		}
		return Component;
	};
	UStaticMeshComponent* First = Block(FVector::ZeroVector, true, false);
	UStaticMeshComponent* Second = Block(FVector(200.0, 0.0, 0.0), false, true);
	UStaticMeshComponent* Outside = Block(FVector(0.0, 500.0, 0.0), true, false);
	UStaticMeshComponent* Untagged = Block(FVector(400.0, 0.0, 0.0), false, false);
	UStaticMeshComponent* AlreadyHidden = Block(FVector(600.0, 0.0, 0.0), true, false);
	AlreadyHidden->SetHiddenInGame(true);
	Outside->GetOwner()->Tags.Add(TEXT("JadgWitnessSurface:test-floor"));
	UStaticMeshComponent* Supported = Block(FVector(0.0, 700.0, 0.0), false, false);
	Supported->GetOwner()->Tags.Add(TEXT("JadgWitnessSupport:test-floor"));
	Supported->GetOwner()->Tags.Add(TEXT("JadgWitnessSurface:test-prop"));
	UStaticMeshComponent* Chained = Block(FVector(0.0, 900.0, 0.0), false, false);
	Chained->GetOwner()->Tags.Add(TEXT("JadgWitnessSupport:test-prop"));
	UStaticMeshComponent* HiddenDependent = Block(FVector(0.0, 1100.0, 0.0), false, false);
	HiddenDependent->GetOwner()->Tags.Add(TEXT("JadgWitnessSupport:test-floor"));
	HiddenDependent->SetHiddenInGame(true);
	UStaticMeshComponent* OtherSupport = Block(FVector(0.0, 1300.0, 0.0), false, false);
	OtherSupport->GetOwner()->Tags.Add(TEXT("JadgWitnessSupport:other-floor"));
	AJadgWitnessReview* Review = World->SpawnActor<AJadgWitnessReview>();
	TestFalse(TEXT("fine navigation is opt-in and leaves other maps unchanged"), Review->bFineNavigation);
	TestEqual(TEXT("tile size preserves the existing profile by default"), Review->NavigationTileSize, 0.0f);
	TestEqual(TEXT("layer estimate preserves the existing profile by default"), Review->NavigationAverageLayers, 0.0f);
	TestEqual(TEXT("simplification preserves the existing profile by default"), Review->NavigationMaxSimplificationError, -1.0f);
	TestEqual(TEXT("search budget preserves the existing profile by default"), Review->NavigationMaxSearchNodes, 0);
	TestTrue(TEXT("disabled fine profile does not require navigation data"), Review->PrepareFineNavigation());
	// A failed readiness check must still expire; captures without a walk report
	// and an already completed walk must never acquire this failure deadline.
	Review->ReportFile = TEXT("not-written-by-this-test");
	Review->Started = 10.0;
	Review->StartupTimeout = 5.0f;
	TestFalse(TEXT("navigation startup remains within its deadline"), Review->NavigationWaitTimedOut(15.0));
	TestTrue(TEXT("navigation startup expires despite not being ready"), Review->NavigationWaitTimedOut(15.01));
	Review->bWalking = true;
	Review->LegStarted = 20.0;
	Review->LegTimeout = 2.0f;
	TestFalse(TEXT("navigation wait during a leg uses its own clock"), Review->NavigationWaitTimedOut(21.0));
	TestTrue(TEXT("navigation wait during a leg expires"), Review->NavigationWaitTimedOut(22.01));
	Review->bDone = true;
	TestFalse(TEXT("completed walk cannot expire while awaiting navigation"), Review->NavigationWaitTimedOut(1000.0));
	Review->bDone = false;
	Review->ReportFile.Reset();
	TestFalse(TEXT("a capture without a walk report has no walk deadline"), Review->NavigationWaitTimedOut(1000.0));
	Review->bWalking = false;
	Review->StartupTimeout = 120.0f;
	Review->LegTimeout = 90.0f;
	// Use the real actor lifecycle: DispatchBeginPlay alone leaves an actor in
	// an uninitialized fixture, so Destroy would legitimately skip RouteEndPlay.
	// The base mode starts this isolated world without spawning the game's party.
	World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
	const FURL Url;
	World->SetGameMode(Url);
	World->InitializeActorsForPlay(Url);
	World->BeginPlay();
	TestTrue(TEXT("fixture world has begun play"), World->HasBegunPlay());
	TestTrue(TEXT("review is initialized before its destruction is tested"), Review->IsActorInitialized());
	TestTrue(TEXT("review has begun play through the world's lifecycle"), Review->HasActorBegunPlay());
	TestEqual(TEXT("tagged walls ignore camera probe"), First->GetCollisionResponseToChannel(ECC_Camera), ECR_Ignore);
	TestEqual(TEXT("camera change does not disable pawn collision"), First->GetCollisionResponseToChannel(ECC_Pawn), ECR_Block);
	Review->UpdateCutaway(FVector(-200.0, 0.0, 0.0), FVector(800.0, 0.0, 0.0));
	TestTrue(TEXT("first actual obstacle is cut"), First->bHiddenInGame);
	TestTrue(TEXT("second obstacle behind first is also cut"), Second->bHiddenInGame);
	TestFalse(TEXT("a wall off the actual sight segment remains visible"), Outside->bHiddenInGame);
	TestFalse(TEXT("an untagged obstacle is not cut"), Untagged->bHiddenInGame);
	TestTrue(TEXT("cut wall retains hidden shadows"), First->bCastHiddenShadow);
	TestTrue(TEXT("cut wall retains indirect light"), First->bAffectIndirectLightingWhileHidden);
	TestEqual(TEXT("cut wall still blocks locomotion"), First->GetCollisionResponseToChannel(ECC_Pawn), ECR_Block);
	TestEqual(TEXT("cut roof does not intercept ground clicks"), First->GetCollisionResponseToChannel(ECC_Visibility), ECR_Ignore);
	// A second evaluation must retain the cut even though the click channel is ignored.
	Review->UpdateCutaway(FVector(-200.0, 0.0, 0.0), FVector(800.0, 0.0, 0.0));
	TestTrue(TEXT("direct geometry trace still finds a cut roof"), First->bHiddenInGame);
	Review->UpdateCutaway(FVector(-200.0, -500.0, 0.0), FVector(800.0, -500.0, 0.0));
	TestFalse(TEXT("moving the camera restores a previously cut wall"), First->bHiddenInGame);
	TestFalse(TEXT("hidden shadow state restored"), First->bCastHiddenShadow);
	TestFalse(TEXT("hidden indirect state restored"), First->bAffectIndirectLightingWhileHidden);
	TestEqual(TEXT("visible roof restores click collision"), First->GetCollisionResponseToChannel(ECC_Visibility), ECR_Block);
	Review->UpdateCutaway(FVector(-200.0, 0.0, 0.0), FVector(800.0, 0.0, 0.0));
	Review->RestoreOccluders();
	TestFalse(TEXT("shutdown restores currently cut visibility"), First->bHiddenInGame);
	TestEqual(TEXT("shutdown restores original camera collision"), First->GetCollisionResponseToChannel(ECC_Camera), ECR_Block);
	TestEqual(TEXT("shutdown restores original click collision"), First->GetCollisionResponseToChannel(ECC_Visibility), ECR_Block);
	TestTrue(TEXT("an initially hidden component remains hidden"), AlreadyHidden->bHiddenInGame);
	Review->GatherOccluders();
	TestEqual(TEXT("dependent prop keeps its original camera physics"), Supported->GetCollisionResponseToChannel(ECC_Camera), ECR_Block);
	Review->UpdateCutaway(FVector(-200.0, 500.0, 0.0), FVector(200.0, 500.0, 0.0));
	TestTrue(TEXT("support floor is cut by its actual geometry"), Outside->bHiddenInGame);
	TestTrue(TEXT("prop away from the ray follows its cut support"), Supported->bHiddenInGame);
	TestTrue(TEXT("a dependency chain follows the same support cut"), Chained->bHiddenInGame);
	TestFalse(TEXT("unrelated support does not hide another prop"), OtherSupport->bHiddenInGame);
	TestTrue(TEXT("supported prop retains hidden shadows"), Supported->bCastHiddenShadow);
	TestTrue(TEXT("supported prop retains indirect lighting"), Supported->bAffectIndirectLightingWhileHidden);
	TestEqual(TEXT("supported prop retains pawn collision"), Supported->GetCollisionResponseToChannel(ECC_Pawn), ECR_Block);
	TestEqual(TEXT("supported prop releases hidden click collision"), Supported->GetCollisionResponseToChannel(ECC_Visibility), ECR_Ignore);
	Review->GatherOccluders();
	Review->UpdateCutaway(FVector(-200.0, -500.0, 0.0), FVector(200.0, -500.0, 0.0));
	TestFalse(TEXT("support restoration reveals the originally visible prop"), Supported->bHiddenInGame);
	TestFalse(TEXT("support restoration reveals a chained prop"), Chained->bHiddenInGame);
	TestTrue(TEXT("refresh and support restoration preserve an initially hidden prop"), HiddenDependent->bHiddenInGame);
	TestFalse(TEXT("dependent original shadow state restored"), Supported->bCastHiddenShadow);
	TestFalse(TEXT("dependent original indirect state restored"), Supported->bAffectIndirectLightingWhileHidden);
	TestEqual(TEXT("dependent click collision restored"), Supported->GetCollisionResponseToChannel(ECC_Visibility), ECR_Block);
	Review->UpdateCutaway(FVector(-200.0, 500.0, 0.0), FVector(200.0, 500.0, 0.0));
	Review->RestoreOccluders();
	TestFalse(TEXT("shutdown restores a cut dependent"), Supported->bHiddenInGame);
	TestTrue(TEXT("shutdown keeps an initially hidden dependent hidden"), HiddenDependent->bHiddenInGame);
	// Exercise our delegate targets directly: synthetic broadcasts would also
	// reach editor listeners which require a genuine streaming operation.
	UStaticMeshComponent* Late = Block(FVector(800.0, 0.0, 0.0), true, false);
	Review->OnLevelAdded(World->PersistentLevel, nullptr);
	Review->UpdateCutaway(FVector(-200.0, 0.0, 0.0), FVector(1000.0, 0.0, 0.0));
	TestFalse(TEXT("a notification from another world does not register late geometry"), Late->bHiddenInGame);
	Review->OnLevelAdded(World->PersistentLevel, World);
	TestTrue(TEXT("registration does not reveal already cut components"), First->bHiddenInGame);
	Review->UpdateCutaway(FVector(-200.0, 0.0, 0.0), FVector(1000.0, 0.0, 0.0));
	TestTrue(TEXT("a late loaded obstacle is cut"), Late->bHiddenInGame);
	TestEqual(TEXT("late loaded geometry ignores the camera probe"), Late->GetCollisionResponseToChannel(ECC_Camera), ECR_Ignore);
	TestEqual(TEXT("late loaded geometry retains pawn physics"), Late->GetCollisionResponseToChannel(ECC_Pawn), ECR_Block);
	Review->OnLevelAdded(World->PersistentLevel, World);
	Review->RestoreOccluders();
	TestFalse(TEXT("repeated registration preserves initial visible state"), Late->bHiddenInGame);
	TestEqual(TEXT("repeated registration preserves original camera response"), Late->GetCollisionResponseToChannel(ECC_Camera), ECR_Block);
	TestEqual(TEXT("repeated registration preserves original click response"), First->GetCollisionResponseToChannel(ECC_Visibility), ECR_Block);
	Review->GatherOccluders();
	Review->UpdateCutaway(FVector(-200.0, 0.0, 0.0), FVector(1000.0, 0.0, 0.0));
	Review->OnLevelRemoving(World->PersistentLevel, nullptr);
	TestTrue(TEXT("removal notification from another world leaves current cut intact"), Late->bHiddenInGame);
	Review->OnLevelRemoving(World->PersistentLevel, World);
	TestFalse(TEXT("level removal restores cut visibility"), Late->bHiddenInGame);
	TestEqual(TEXT("level removal restores camera collision"), Late->GetCollisionResponseToChannel(ECC_Camera), ECR_Block);
	TestEqual(TEXT("level removal restores click collision"), Late->GetCollisionResponseToChannel(ECC_Visibility), ECR_Block);
	Review->UpdateCutaway(FVector(-200.0, 0.0, 0.0), FVector(1000.0, 0.0, 0.0));
	TestFalse(TEXT("removed geometry is no longer processed"), Late->bHiddenInGame);
	Review->GatherOccluders();
	Review->UpdateCutaway(FVector(-200.0, 500.0, 0.0), FVector(200.0, 500.0, 0.0));
	Review->OnLevelRemoving(World->PersistentLevel, World);
	TestFalse(TEXT("level removal restores supported props"), Supported->bHiddenInGame);
	TestEqual(TEXT("level removal restores supported click collision"), Supported->GetCollisionResponseToChannel(ECC_Visibility), ECR_Block);
	TestTrue(TEXT("level removal preserves initially hidden dependent state"), HiddenDependent->bHiddenInGame);
	Review->GatherOccluders();
	Review->UpdateCutaway(FVector(-200.0, 500.0, 0.0), FVector(200.0, 500.0, 0.0));
	TestTrue(TEXT("review destruction succeeds"), Review->Destroy());
	TestFalse(TEXT("EndPlay restores a currently cut dependent"), Supported->bHiddenInGame);
	TestTrue(TEXT("EndPlay preserves initially hidden dependent state"), HiddenDependent->bHiddenInGame);
	TestFalse(TEXT("destroying review releases addition callback"), FWorldDelegates::LevelAddedToWorld.IsBoundToObject(Review));
	TestFalse(TEXT("destroying review releases removal callback"), FWorldDelegates::PreLevelRemovedFromWorld.IsBoundToObject(Review));
	World->EndPlay(EEndPlayReason::Quit);
	TestFalse(TEXT("fixture world has ended play before cleanup"), World->HasBegunPlay());
	Instance->Shutdown();
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif
