// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Les tests d'automatisation du combat joué dans le moteur (LOT-1017, sous-lots 2 et 3) : les
// candidats de l'espace du moteur servent l'IA sans limite de budget ; le combat se monte, se joue
// tour par tour, provoque l'attaque d'opportunité et se résout sur la carte d'arène d'essai, rebâtie
// par le test depuis sa carte de Core (le sol, l'enceinte et les piliers, un bloc par case pleine).
//
//     UnrealEditor-Cmd.exe <projet>.uproject -ExecCmds="Automation RunTests Jadg.Combat; Quit" -nullrhi

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Combat/ActionEconomy.h"
#include "Core/Combat/Arena.h"
#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/Contestants.h"
#include "Core/Combat/EnemyAi.h"
#include "Core/Levels/LevelLoader.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/RpgEnums.h"
#include "Core/World/WorldTravel.h"

#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "Bridge/JadgPaths.h"
#include "Combat/JadgCombat.h"
#include "Combat/JadgCombatSpace.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "EnvironmentQuery/EnvQueryManager.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Game/JadgExploration.h"
#include "Game/JadgGameInstance.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "Misc/Paths.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationSystem.h"
#include "Scene/JadgSceneBuild.h"
#include "World/JadgMapFrame.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags PlayFlags = EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::EngineFilter;

	const TCHAR* const ArenaLevel = TEXT("essai/arene");
	const TCHAR* const ArenaRoot = TEXT("Source/Test/Fixtures/Exploration/Levels");

	UStaticMeshComponent* Cube(UWorld* World, const FVector& Centre, const FVector& Scale)
	{
		UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
		AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(Centre, FRotator::ZeroRotator);
		if (Mesh == nullptr || Actor == nullptr)
		{
			return nullptr;
		}
		Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
		Actor->GetStaticMeshComponent()->SetStaticMesh(Mesh);
		Actor->SetActorScale3D(Scale);
		return Actor->GetStaticMeshComponent();
	}

	core::Volume Medium(float X, float Y)
	{
		return core::volumeOf({X, Y, 0.0f}, core::CreatureSize::Medium);
	}

	/// La carte de Core de l'arène d'essai (`build_essai_maps.py`).
	core::LevelLoadResult LoadArena()
	{
		const std::filesystem::path Root =
			FJadgPaths::ToPath(FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), ArenaRoot)));
		return core::WorldTravel::directoriesLoader({Root})(std::string(TCHAR_TO_UTF8(ArenaLevel)));
	}

	/// Le monde d'un test de l'arène : l'instance du jeu, le monde, le repère.
	struct FArenaWorld
	{
		UJadgGameInstance* Instance = nullptr;
		UWorld* World = nullptr;
		AJadgMapFrame* Frame = nullptr;

		void Close() const
		{
			World->EndPlay(EEndPlayReason::Quit);
			Instance->Shutdown();
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}
	};

	/// Rebâtit l'arène d'essai : le sol, un bloc de 1,5 × 1,5 × 3 m par case pleine, le maillage.
	/// Chaque bloc est remis dans l'octree de la navigation une fois le système créé, et le système
	/// de l'IA (l'EQS) est créé s'il manque : un monde d'essai n'en a pas d'office.
	bool BuildArena(FAutomationTestBase& Test, const core::Level& Level, const TCHAR* Name, FArenaWorld& Out)
	{
		Test.AddExpectedError(TEXT("Unable to find RecastNavMesh instance"), EAutomationExpectedErrorFlags::Contains, 0);
		Out.Instance = NewObject<UJadgGameInstance>(GEngine);
		Out.Instance->InitializeStandalone(Name);
		Out.World = Out.Instance->GetWorld();
		const core::TileMap& Tiles = Level.tileMap();
		const double Width = Tiles.width() * 150.0;
		const double Height = Tiles.height() * 150.0;
		TArray<UStaticMeshComponent*> Blocks;
		Blocks.Add(Cube(Out.World, FVector(Width / 2.0, Height / 2.0, -50.0), FVector(Width / 100.0, Height / 100.0, 1.0)));
		for (int32 Row = 0; Row < Tiles.height(); ++Row)
		{
			for (int32 Column = 0; Column < Tiles.width(); ++Column)
			{
				if (Tiles.isSolid(Column, Row))
				{
					Blocks.Add(Cube(Out.World, FVector((Column + 0.5) * 150.0, (Row + 0.5) * 150.0, 150.0), FVector(1.5, 1.5, 3.0)));
				}
			}
		}
		UJadgSceneBuild::SpawnBoxVolume(Out.World, ANavMeshBoundsVolume::StaticClass(), FVector(Width / 2.0, Height / 2.0, 100.0),
			FVector(Width, Height, 600.0));
		Out.Frame = Out.World->SpawnActor<AJadgMapFrame>();
		Out.Frame->LevelId = ArenaLevel;
		Out.Frame->LevelsRoot = ArenaRoot;
		// Un mode de jeu sans groupe : le combat se monte sans figurines.
		Out.World->GetWorldSettings()->DefaultGameMode = AGameModeBase::StaticClass();
		const FURL Url;
		Out.World->SetGameMode(Url);
		Out.World->InitializeActorsForPlay(Url);
		Out.World->BeginPlay();
		if (UEnvQueryManager::GetCurrent(Out.World) == nullptr)
		{
			Out.World->CreateAISystem();
		}
		if (FNavigationSystem::GetCurrent<UNavigationSystemV1>(Out.World) == nullptr)
		{
			FNavigationSystem::AddNavigationSystemToWorld(*Out.World, FNavigationSystemRunMode::GameMode);
		}
		UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(Out.World);
		if (!Test.TestNotNull(TEXT("le système de navigation"), Navigation))
		{
			return false;
		}
		for (UStaticMeshComponent* Block : Blocks)
		{
			if (Block != nullptr)
			{
				UNavigationSystemV1::UpdateComponentInNavOctree(*Block);
			}
		}
		Navigation->Build();
		Out.World->Tick(LEVELTICK_All, 1.0f / 30.0f);
		// La construction du maillage se finit en tâche de fond : on l'attend.
		for (int32 Frame = 0; Frame < 600 && Navigation->IsNavigationBuildInProgress(); ++Frame)
		{
			Out.World->Tick(LEVELTICK_All, 1.0f / 30.0f);
		}
		return true;
	}

	/// Un combattant de l'arène depuis le bestiaire, du camp @p Side, joué par l'IA si @p bAi.
	core::ArenaContestant Creature(const core::Bestiary& Bestiary, const core::BehaviorCatalog& Behaviors, const char* Id,
		core::CombatSide Side, bool bAi, core::GridPosition Cell)
	{
		core::ArenaContestant Contestant = core::creatureContestant(*Bestiary.find(Id), Side, &Behaviors);
		if (!bAi)
		{
			Contestant.behavior.clear();
		}
		Contestant.position = Cell;
		return Contestant;
	}

	/// Fait passer les tours jusqu'à celui de @p Id ; faux s'il ne vient pas.
	bool UntilTurnOf(core::ArenaSession& Session, core::CombatantId Id)
	{
		for (int32 Guard = 0; Guard < 40; ++Guard)
		{
			if (Session.combat().activeCombatant() == Id)
			{
				return true;
			}
			Session.endTurn();
		}
		return false;
	}

	bool JournalHas(const core::ArenaSession& Session, const char* Text)
	{
		for (const std::string& Line : Session.journal())
		{
			if (Line.find(Text) != std::string::npos)
			{
				return true;
			}
		}
		return false;
	}

	/// Le combat de l'arène d'essai, monté sur le groupe de l'exploration.
	AJadgCombat* MountArena(FAutomationTestBase& Test, const FArenaWorld& Arena, bool bHeroesByAi, uint64 Seed)
	{
		UJadgExploration* Exploration = Arena.Instance->GetSubsystem<UJadgExploration>();
		if (!Test.TestNotNull(TEXT("l'exploration"), Exploration))
		{
			return nullptr;
		}
		Exploration->EngageEncounter(TEXT("arene-bandits"));
		AJadgCombat* Combat = Arena.World->SpawnActor<AJadgCombat>();
		FString Error;
		const bool bMounted = Combat != nullptr && Combat->Mount(TEXT("arene-bandits"), Seed, false, bHeroesByAi, Error);
		Test.TestTrue(*FString::Printf(TEXT("la rencontre se monte (%s)"), *Error), bMounted);
		return bMounted ? Combat : nullptr;
	}

	/// Avance le combat jusqu'à @p Done, au plus @p Frames trames.
	template <typename FDone>
	bool AdvanceUntil(AJadgCombat& Combat, FDone Done, int32 Frames)
	{
		for (int32 Frame = 0; Frame < Frames; ++Frame)
		{
			if (Done())
			{
				return true;
			}
			Combat.Advance(1.0f / 30.0f);
		}
		return Done();
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgCombatCandidatesTest, "Jadg.Combat.Candidats", PlayFlags)

/// Les candidats du moteur sans limite de budget (sous-lot 2) : un ennemi à 15 m en terrain
/// découvert, une place à son contact par un chemin presque droit ; derrière un pilier, une place à
/// son contact par un chemin qui le contourne. Puis l'IA elle-même, sur l'espace du moteur, avance
/// vers son adversaire caché derrière le pilier.
bool FJadgCombatCandidatesTest::RunTest(const FString& Parameters)
{
	const core::LevelLoadResult Loaded = LoadArena();
	FArenaWorld Arena;
	if (!TestTrue(TEXT("l'arène d'essai se lit"), Loaded.ok()) || !BuildArena(*this, *Loaded.level, TEXT("JadgCombatCandidats"), Arena))
	{
		return false;
	}
	const FJadgCombatSpace Space(Arena.World, Arena.Frame);

	const auto BestReach = [&](const core::Volume& Mover, const core::Volume& Enemy) -> std::optional<core::Destination>
	{
		const std::vector<core::Volume> Blocking{Enemy};
		const std::vector<core::Destination> Places =
			Space.candidates({.mover = Mover, .destination = {}, .budget = -1.0f, .blocking = Blocking});
		std::optional<core::Destination> Best;
		for (const core::Destination& Place : Places)
		{
			core::Volume There = Mover;
			There.base = Place.point;
			if (!Place.route.points.empty() && core::inReach(There, Enemy) && (!Best.has_value() || Place.route.length < Best->route.length))
			{
				Best = Place;
			}
		}
		return Best;
	};

	// En terrain découvert, ligne 1 : de (5,25 ; 2,25) à (20,25 ; 2,25), 15 m.
	const std::optional<core::Destination> Open = BestReach(Medium(5.25f, 2.25f), Medium(20.25f, 2.25f));
	const FJadgCandidateStats OpenStats = Space.LastStats();
	AddInfo(FString::Printf(TEXT("sans limite, terrain découvert : %d points, %d places, %.1f ms, %s"), OpenStats.Generated, OpenStats.Kept,
		OpenStats.Milliseconds, OpenStats.bFromEqs ? TEXT("EQS") : TEXT("échantillonnage")));
	TestTrue(TEXT("les points viennent de l'EQS"), OpenStats.bFromEqs);
	if (TestTrue(TEXT("une place au contact de l'ennemi à 15 m"), Open.has_value()))
	{
		// Au contact : 15 m moins les deux rayons et l'allonge, au plus 12 m de chemin.
		TestTrue(*FString::Printf(TEXT("par un chemin presque droit (%.2f m)"), Open->route.length),
			Open->route.length >= 11.0f && Open->route.length <= 13.6f);
	}

	// Derrière le pilier (x de 13,5 à 16,5 m, y de 4,5 à 7,5 m), adossé à sa face est, à 15 m : la
	// ligne droite est coupée ; la place trouvée s'atteint par un chemin dont aucun pas ne traverse.
	const core::Volume Hidden = Medium(2.25f, 6.0f);
	const core::Volume Behind = Medium(17.25f, 6.0f);
	TestFalse(TEXT("le pilier coupe la ligne droite"), Space.lineOfSight({2.25f, 6.0f, 0.75f}, {17.25f, 6.0f, 0.75f}));
	const std::optional<core::Destination> Around = BestReach(Hidden, Behind);
	if (TestTrue(TEXT("une place au contact de l'ennemi caché"), Around.has_value()))
	{
		core::Meters3 From = Hidden.base;
		bool bClear = true;
		for (const core::Meters3& Point : Around->route.points)
		{
			bClear = bClear && Space.lineOfSight({From.x, From.y, 0.75f}, {Point.x, Point.y, 0.75f});
			From = Point;
		}
		AddInfo(FString::Printf(TEXT("contourné : place (%.2f ; %.2f), %d pas, %.2f m"), Around->point.x, Around->point.y,
			static_cast<int32>(Around->route.points.size()), Around->route.length));
		TestTrue(TEXT("aucun pas du chemin ne traverse le pilier"), bClear);
		TestTrue(TEXT("la place n'est pas dans le pilier"), Around->point.x < 13.4f || Around->point.x > 16.6f || Around->point.y < 4.4f
			|| Around->point.y > 7.6f);
	}

	// Au pied du pilier, face ouest (12 m), l'ennemi adossé à la face est : toute place à son contact
	// est derrière le pilier, et le chemin s'y plie.
	const core::Volume Foot = Medium(12.0f, 6.0f);
	const std::optional<core::Destination> Bent = BestReach(Foot, Behind);
	if (TestTrue(TEXT("une place au contact, le pilier entre les deux"), Bent.has_value()))
	{
		const float Straight = core::groundDistance(Foot.base, Bent->point);
		AddInfo(FString::Printf(TEXT("plié : place (%.2f ; %.2f), %d pas, %.2f m contre %.2f m à vol d'oiseau"), Bent->point.x, Bent->point.y,
			static_cast<int32>(Bent->route.points.size()), Bent->route.length, Straight));
		TestTrue(TEXT("le chemin contourne le pilier"), Bent->route.points.size() >= 2 && Bent->route.length > Straight + 0.2f);
	}

	// L'IA sur l'espace du moteur : un bandit, son adversaire caché derrière le pilier, avance.
	const std::filesystem::path Rpg = FJadgPaths::RpgRoot();
	const core::Bestiary Bestiary = core::loadBestiary(Rpg / "creatures");
	const core::BehaviorCatalog Behaviors = core::loadBehaviors(Rpg / "rules" / "behaviors.json");
	core::ArenaSession Session(*Loaded.level, std::make_shared<FJadgCombatSpace>(Arena.World, Arena.Frame));
	const core::ArenaBout Bout{.contestants = {Creature(Bestiary, Behaviors, "bandit", core::CombatSide::Allies, false, {3, 4}),
								   Creature(Bestiary, Behaviors, "bandit", core::CombatSide::Enemies, true, {13, 4})},
		.seed = 3,
		.lethal = true,
		.heroicMark = false,
		.flanking = false,
		.escapable = true};
	const core::ArenaMount Mounted = Session.mount(Bout);
	if (TestEqual(TEXT("deux combattants posés"), static_cast<int32>(Mounted.allies.size() + Mounted.enemies.size()), 2) && Session.start()
		&& TestTrue(TEXT("le tour du bandit vient"), UntilTurnOf(Session, Mounted.enemies[0])))
	{
		const core::Meters3 Before = *Session.combat().positionOf(Mounted.enemies[0]);
		const core::Meters3 Foe = *Session.combat().positionOf(Mounted.allies[0]);
		TestTrue(TEXT("l'IA joue son tour"), core::playTurn(Session, Behaviors));
		const core::Meters3 After = *Session.combat().positionOf(Mounted.enemies[0]);
		AddInfo(FString::Printf(TEXT("le bandit va de (%.2f ; %.2f) en (%.2f ; %.2f)"), Before.x, Before.y, After.x, After.y));
		TestTrue(TEXT("l'IA avance vers son adversaire"), core::groundDistance(After, Foe) < core::groundDistance(Before, Foe) - 1.0f);
	}
	Arena.Close();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgCombatMountTest, "Jadg.Combat.Montage", PlayFlags)

/// La rencontre `arene-bandits` se monte dans l'arène d'essai : les quatre héros de l'exploration à
/// leurs points d'entrée, les six bandits autour du marqueur, chacun sur le maillage de navigation,
/// et un premier tour.
bool FJadgCombatMountTest::RunTest(const FString& Parameters)
{
	const core::LevelLoadResult Loaded = LoadArena();
	FArenaWorld Arena;
	if (!TestTrue(TEXT("l'arène d'essai se lit"), Loaded.ok()) || !BuildArena(*this, *Loaded.level, TEXT("JadgCombatMontage"), Arena))
	{
		return false;
	}
	if (AJadgCombat* Combat = MountArena(*this, Arena, false, 1))
	{
		int32 Allies = 0;
		int32 Enemies = 0;
		UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(Arena.World);
		for (const FJadgFighter& Fighter : Combat->Fighters())
		{
			(Fighter.bAlly ? Allies : Enemies) += 1;
			const TOptional<FVector> Base = Combat->PositionOf(Fighter.Id);
			FNavLocation OnMesh;
			TestTrue(*FString::Printf(TEXT("%s est posé sur le maillage"), *Fighter.Name),
				Base.IsSet() && Navigation->ProjectPointToNavigation(Base.GetValue(), OnMesh, FVector(10.0, 10.0, 100.0)));
			if (Fighter.bAlly && Base.IsSet())
			{
				const FVector2D Cell = Arena.Frame->ToCell(Base.GetValue());
				TestTrue(*FString::Printf(TEXT("%s entre par la colonne 3 (%.2f ; %.2f)"), *Fighter.Name, Cell.X, Cell.Y),
					FMath::IsNearlyEqual(Cell.X, 3.5, 0.01) && Cell.Y > 5.0 && Cell.Y < 9.0);
			}
		}
		TestEqual(TEXT("quatre héros"), Allies, 4);
		TestEqual(TEXT("six bandits"), Enemies, 6);
		TestTrue(TEXT("un combattant a la main"), Combat->ActiveId() != 0);
		TestTrue(TEXT("le premier round est ouvert"), Combat->Round() >= 1);
	}
	Arena.Close();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgCombatTurnTest, "Jadg.Combat.Tour", PlayFlags)

/// Un tour complet : le joueur déplace son héros et finit son tour, puis l'IA joue les six bandits
/// jusqu'à ce que la main revienne à ce héros.
bool FJadgCombatTurnTest::RunTest(const FString& Parameters)
{
	const core::LevelLoadResult Loaded = LoadArena();
	FArenaWorld Arena;
	if (!TestTrue(TEXT("l'arène d'essai se lit"), Loaded.ok()) || !BuildArena(*this, *Loaded.level, TEXT("JadgCombatTour"), Arena))
	{
		return false;
	}
	if (AJadgCombat* Combat = MountArena(*this, Arena, false, 1))
	{
		TestTrue(TEXT("le tour d'un héros vient"), AdvanceUntil(*Combat, [&] { return Combat->IsPlayerTurn(); }, 600));
		const int32 Hero = Combat->ActiveId();
		const FVector Before = Combat->PositionOf(Hero).Get(FVector::ZeroVector);
		const float Budget = Combat->MovementLeft();
		TestTrue(TEXT("le héros a son déplacement"), Budget > 5.0f);
		TestTrue(TEXT("le joueur déplace son héros de 3 m vers l'est"), Combat->MoveTo(Before + FVector(300.0, 0.0, 0.0)));
		TestTrue(TEXT("les gestes se montrent"), AdvanceUntil(*Combat, [&] { return !Combat->IsBusy(); }, 300));
		const FVector After = Combat->PositionOf(Hero).Get(FVector::ZeroVector);
		TestTrue(*FString::Printf(TEXT("le héros a marché (%.0f cm)"), FVector::Dist2D(Before, After)), FVector::Dist2D(Before, After) > 200.0);
		TestTrue(TEXT("il lui reste moins de mètres"), Combat->MovementLeft() < Budget);
		const int32 JournalBefore = Combat->Journal(100000).Num();
		TestTrue(TEXT("le joueur finit son tour"), Combat->EndTurn());
		// Les autres héros finissent leur tour sans rien faire : on attend que la main revienne à celui-ci.
		TestTrue(TEXT("le tour du même héros revient, un round plus tard"), AdvanceUntil(*Combat, [&]
		{
			if (Combat->IsPlayerTurn() && Combat->ActiveId() != Hero)
			{
				Combat->EndTurn();
			}
			return (Combat->IsPlayerTurn() && Combat->ActiveId() == Hero) || Combat->IsOver();
		}, 6000));
		int32 AiLines = 0;
		const TArray<FString> Journal = Combat->Journal(100000);
		for (int32 Index = JournalBefore; Index < Journal.Num(); ++Index)
		{
			AiLines += Journal[Index].StartsWith(TEXT("ia ")) ? 1 : 0;
		}
		AddInfo(Combat->CandidateReport());
		AddInfo(FString::Printf(TEXT("%d décision(s) de l'IA entre les deux tours de héros"), AiLines));
		TestTrue(TEXT("l'IA a joué les bandits entre les deux"), AiLines >= 6);
	}
	Arena.Close();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgCombatOpportunityTest, "Jadg.Combat.Opportunite", PlayFlags)

/// L'attaque d'opportunité au départ de l'allonge, sur l'espace du moteur : un combattant au contact
/// d'un bandit s'en éloigne de 4,5 m ; le bandit frappe et dépense sa réaction. Désengagé, non.
bool FJadgCombatOpportunityTest::RunTest(const FString& Parameters)
{
	const core::LevelLoadResult Loaded = LoadArena();
	FArenaWorld Arena;
	if (!TestTrue(TEXT("l'arène d'essai se lit"), Loaded.ok()) || !BuildArena(*this, *Loaded.level, TEXT("JadgCombatOpportunite"), Arena))
	{
		return false;
	}
	const std::filesystem::path Rpg = FJadgPaths::RpgRoot();
	const core::Bestiary Bestiary = core::loadBestiary(Rpg / "creatures");
	const core::BehaviorCatalog Behaviors = core::loadBehaviors(Rpg / "rules" / "behaviors.json");
	for (const bool bDisengage : {false, true})
	{
		core::ArenaSession Session(*Loaded.level, std::make_shared<FJadgCombatSpace>(Arena.World, Arena.Frame));
		// Le fuyard est un vétéran : il tient debout sous le coup d'un bandit.
		const core::ArenaBout Bout{.contestants = {Creature(Bestiary, Behaviors, "veteran", core::CombatSide::Allies, false, {6, 1}),
									   Creature(Bestiary, Behaviors, "bandit", core::CombatSide::Enemies, false, {7, 1})},
			.seed = 5,
			.lethal = false,
			.heroicMark = false,
			.flanking = false,
			.escapable = true};
		const core::ArenaMount Mounted = Session.mount(Bout);
		if (Mounted.allies.empty() || Mounted.enemies.empty() || !Session.start() || !UntilTurnOf(Session, Mounted.allies[0]))
		{
			AddError(FString::Printf(TEXT("le tour du fuyard ne vient pas (%d allié, %d ennemi, %d refus, phase %d)"),
				static_cast<int32>(Mounted.allies.size()), static_cast<int32>(Mounted.enemies.size()), static_cast<int32>(Mounted.refusals.size()),
				static_cast<int32>(Session.combat().phase())));
			break;
		}
		if (bDisengage)
		{
			TestTrue(TEXT("il se désengage"), Session.disengage());
		}
		const core::MoveOutcome Moved = Session.move(core::tileCenter({3, 1}));
		TestTrue(TEXT("il quitte l'allonge"), Moved.result == core::MoveResult::Moved);
		const int Reaction = Session.combat().find(Mounted.enemies[0])->economy.remaining(core::REACTION_RESOURCE);
		if (bDisengage)
		{
			TestFalse(TEXT("désengagé, aucune attaque d'opportunité"), JournalHas(Session, "opportunite"));
			TestEqual(TEXT("la réaction du bandit reste"), Reaction, 1);
		}
		else
		{
			TestTrue(TEXT("le bandit frappe au départ de l'allonge"), JournalHas(Session, "opportunite"));
			TestEqual(TEXT("sa réaction est dépensée"), Reaction, 0);
		}
	}
	Arena.Close();
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgCombatResolutionTest, "Jadg.Combat.Resolution", PlayFlags)

/// La rencontre jouée jusqu'à son issue, les héros tenus par l'IA du profil de leur classe ; l'issue
/// s'écrit dans la partie : une victoire pose `encounter/arene-bandits/won`, une défaite non, et la
/// rencontre n'est plus engagée.
bool FJadgCombatResolutionTest::RunTest(const FString& Parameters)
{
	const core::LevelLoadResult Loaded = LoadArena();
	FArenaWorld Arena;
	if (!TestTrue(TEXT("l'arène d'essai se lit"), Loaded.ok()) || !BuildArena(*this, *Loaded.level, TEXT("JadgCombatResolution"), Arena))
	{
		return false;
	}
	// Graine 2 : une victoire dans la simulation de Core sur la même carte (29 sur 40 graines).
	if (AJadgCombat* Combat = MountArena(*this, Arena, true, 2))
	{
		UJadgExploration* Exploration = Arena.Instance->GetSubsystem<UJadgExploration>();
		TestTrue(TEXT("le combat se résout"), AdvanceUntil(*Combat, [&] { return Combat->IsResolved(); }, 20000));
		const FString Outcome = Combat->Outcome();
		AddInfo(FString::Printf(TEXT("issue %s au round %d ; %s"), *Outcome, Combat->Round(), *Combat->CandidateReport()));
		TestFalse(TEXT("il y a une issue"), Outcome.IsEmpty());
		TestTrue(TEXT("la rencontre n'est plus engagée"), Exploration->Encounter().IsEmpty());
		TestEqual(TEXT("une victoire, et elle seule, pose le drapeau"), Exploration->Flag(TEXT("encounter/arene-bandits/won")),
			Outcome == TEXT("Victoire") ? FString(TEXT("1")) : FString());
		if (Outcome == TEXT("Victoire"))
		{
			for (const FJadgMember& Member : Exploration->Members())
			{
				TestTrue(*FString::Printf(TEXT("%s garde au moins 1 PV"), *Member.Name), Member.HitPoints >= 1);
			}
		}
	}
	Arena.Close();
	return true;
}

#endif
