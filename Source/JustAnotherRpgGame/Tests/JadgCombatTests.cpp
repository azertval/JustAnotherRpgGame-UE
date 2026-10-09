// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Les tests d'automatisation du combat en distance (LOT-1017) : l'espace de combat du moteur
// répond aux mêmes questions que la simulation de Core, sur un sol, un mur et un maillage de
// navigation construits par le test.
//
//     UnrealEditor-Cmd.exe <projet>.uproject -ExecCmds="Automation RunTests Jadg.Combat; Quit" -nullrhi

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Combat/CombatSpace.h"
#include "Core/Rpg/RpgEnums.h"

#include <cmath>
#include <optional>
#include <vector>

#include "Combat/JadgCombatSpace.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Game/JadgGameInstance.h"
#include "Game/JadgGameMode.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationSystem.h"
#include "Scene/JadgSceneBuild.h"
#include "World/JadgDayLight.h"
#include "World/JadgMapFrame.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags CombatFlags = EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::EngineFilter;

	AStaticMeshActor* Block(UWorld* World, const FVector& Centre, const FVector& Scale)
	{
		UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
		AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(Centre, FRotator::ZeroRotator);
		if (Cube == nullptr || Actor == nullptr)
		{
			return nullptr;
		}
		Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
		Actor->GetStaticMeshComponent()->SetStaticMesh(Cube);
		Actor->SetActorScale3D(Scale);
		return Actor;
	}

	core::Volume Medium(float X, float Y, float Z = 0.0f)
	{
		return core::volumeOf({X, Y, Z}, core::CreatureSize::Medium);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgCombatSpaceTest, "Jadg.Combat.Espace", CombatFlags)

/// Un sol de 24 × 18 m, un mur d'un mètre d'épaisseur en travers des douze premiers mètres de
/// profondeur en x = 12 m, et son maillage de navigation : le sol est à 0, la place est libre
/// hors du mur, le mur coupe la vue et se contourne, le budget borne le chemin, les candidats
/// sont atteignables.
bool FJadgCombatSpaceTest::RunTest(const FString& Parameters)
{
	AddExpectedError(TEXT("Unable to find RecastNavMesh instance"), EAutomationExpectedErrorFlags::Contains, 0);
	UJadgGameInstance* Instance = NewObject<UJadgGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("JadgCombatSpace"));
	UWorld* World = Instance->GetWorld();

	AStaticMeshActor* Floor = Block(World, FVector(1200.0, 900.0, -50.0), FVector(24.0, 18.0, 1.0));
	// Le mur : x de 11,5 à 12,5 m, y de 0 à 12 m, 3 m de haut.
	AStaticMeshActor* Wall = Block(World, FVector(1200.0, 600.0, 150.0), FVector(1.0, 12.0, 3.0));
	if (!TestNotNull(TEXT("le sol"), Floor) || !TestNotNull(TEXT("le mur"), Wall))
	{
		return false;
	}
	UJadgSceneBuild::SpawnBoxVolume(World, ANavMeshBoundsVolume::StaticClass(), FVector(1200.0, 900.0, 100.0), FVector(2400.0, 1800.0, 600.0));
	// Le repère joue la carte d'essai des étals : un repère sans carte de Core est une erreur du jeu.
	World->SpawnActor<AJadgDayLight>();
	AJadgMapFrame* Frame = World->SpawnActor<AJadgMapFrame>();
	Frame->LevelId = TEXT("essai/etals");
	Frame->LevelsRoot = TEXT("Source/Test/Fixtures/Exploration/Levels");
	World->GetWorldSettings()->DefaultGameMode = AJadgGameMode::StaticClass();
	const FURL Url;
	World->SetGameMode(Url);
	World->InitializeActorsForPlay(Url);
	World->BeginPlay();
	if (FNavigationSystem::GetCurrent<UNavigationSystemV1>(World) == nullptr)
	{
		FNavigationSystem::AddNavigationSystemToWorld(*World, FNavigationSystemRunMode::GameMode);
	}
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!TestNotNull(TEXT("le système de navigation"), Navigation))
	{
		return false;
	}
	Navigation->Build();
	World->Tick(LEVELTICK_All, 1.0f / 30.0f);

	const FJadgCombatSpace Space(World, Frame);

	// Le sol et la place.
	TestTrue(TEXT("le sol est à zéro"), std::fabs(Space.groundHeight(5.0f, 5.0f)) < 0.05f);
	TestTrue(TEXT("la place est libre loin du mur"), Space.isClear(Medium(5.0f, 5.0f), core::Locomotion::Walk));
	TestFalse(TEXT("le mur n'est pas une place"), Space.isClear(Medium(12.0f, 6.0f), core::Locomotion::Walk));
	TestFalse(TEXT("hors du sol, pas de place au sol"), Space.isClear(Medium(5.0f, -5.0f), core::Locomotion::Walk));

	// La vue.
	TestFalse(TEXT("le mur coupe la vue"), Space.lineOfSight({5.0f, 6.0f, 0.75f}, {19.0f, 6.0f, 0.75f}));
	TestTrue(TEXT("au-delà du mur, on voit"), Space.lineOfSight({5.0f, 15.0f, 0.75f}, {19.0f, 15.0f, 0.75f}));
	TestEqual(TEXT("l'abri derrière le mur est total"), static_cast<int>(core::coverFrom(Space, Medium(5.0f, 6.0f), Medium(19.0f, 6.0f))),
		static_cast<int>(core::Cover::Total));
	TestEqual(TEXT("aucun abri en terrain découvert"), static_cast<int>(core::coverFrom(Space, Medium(5.0f, 15.0f), Medium(19.0f, 15.0f))),
		static_cast<int>(core::Cover::None));

	// Le chemin et le budget.
	const std::optional<core::Route> Straight = Space.route({.mover = Medium(3.0f, 15.0f), .destination = {9.0f, 15.0f, 0.0f}, .budget = 9.0f});
	if (TestTrue(TEXT("six mètres en ligne droite"), Straight.has_value()))
	{
		TestTrue(*FString::Printf(TEXT("le chemin droit fait six mètres (%.2f)"), Straight->length), std::fabs(Straight->length - 6.0f) < 0.5f);
		TestTrue(TEXT("le chemin finit à destination"), core::groundDistance(Straight->points.back(), {9.0f, 15.0f, 0.0f}) < 0.3f);
	}
	TestFalse(TEXT("le budget arrête le chemin"), Space.route({.mover = Medium(3.0f, 15.0f), .destination = {15.0f, 15.0f, 0.0f}, .budget = 9.0f}).has_value());
	const std::optional<core::Route> Around = Space.route({.mover = Medium(5.0f, 3.0f), .destination = {19.0f, 3.0f, 0.0f}});
	if (TestTrue(TEXT("le mur se contourne"), Around.has_value()))
	{
		TestTrue(*FString::Printf(TEXT("le détour est plus long que la ligne droite (%.2f)"), Around->length), Around->length > 20.0f);
	}
	const std::vector<core::Volume> Enemy{Medium(9.0f, 15.0f)};
	TestFalse(TEXT("on ne finit pas sur un ennemi"),
		Space.route({.mover = Medium(3.0f, 15.0f), .destination = {9.0f, 15.0f, 0.0f}, .blocking = Enemy}).has_value());

	// Les candidats.
	const core::RouteQuery Query{.mover = Medium(5.0f, 15.0f), .destination = {}, .budget = 4.5f};
	const std::vector<core::Destination> Candidates = Space.candidates(Query);
	TestTrue(*FString::Printf(TEXT("des candidats dans 4,5 m (%d)"), static_cast<int32>(Candidates.size())), Candidates.size() > 10);
	bool bAllReachable = true;
	for (const core::Destination& Candidate : Candidates)
	{
		bAllReachable = bAllReachable && core::groundDistance(Candidate.point, Query.mover.base) <= 4.5f + 0.01f
			&& Candidate.route.length <= 4.5f + 0.01f;
	}
	TestTrue(TEXT("tous les candidats sont dans le budget"), bAllReachable);

	World->EndPlay(EEndPlayReason::Quit);
	Instance->Shutdown();
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

#endif
