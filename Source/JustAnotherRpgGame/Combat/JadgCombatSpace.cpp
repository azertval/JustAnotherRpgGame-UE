// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/CombatSpace.h"

#include <algorithm>
#include <cmath>

#include "Combat/JadgCombatSpace.h"

#include "AI/Navigation/NavigationTypes.h"
#include "CollisionQueryParams.h"
#include "Components/SceneComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "EnvironmentQuery/EnvQuery.h"
#include "EnvironmentQuery/EnvQueryManager.h"
#include "EnvironmentQuery/EnvQueryOption.h"
#include "EnvironmentQuery/Generators/EnvQueryGenerator_SimpleGrid.h"
#include "EnvironmentQuery/Items/EnvQueryItemType_Point.h"
#include "GameFramework/Actor.h"
#include "HAL/PlatformTime.h"
#include "NavigationData.h"
#include "NavigationSystem.h"
#include "UObject/Package.h"
#include "UObject/UObjectGlobals.h"
#include "World/JadgMapFrame.h"

namespace
{
	constexpr float CentimetersPerMeter = 100.0f;
	/// La hauteur depuis laquelle on cherche le sol, et jusqu'où.
	constexpr float ProbeHeight = 5000.0f;
	/// Deux points du maillage plus proches que cela sont la même place, en centimètres.
	constexpr double SamePlace = 5.0;
}

FJadgCombatSpace::FJadgCombatSpace(UWorld* InWorld, const AJadgMapFrame* InFrame, FVector2D InOriginCells)
	: World(InWorld), Frame(InFrame), OriginCells(InOriginCells)
{
}

FJadgCombatSpace::~FJadgCombatSpace()
{
	// Le demandeur de l'EQS part avec l'espace, si son monde est encore là.
	AActor* Held = Querier.Get();
	if (Held != nullptr && World != nullptr && !World->bIsTearingDown && GEngine != nullptr && GEngine->GetWorldContextFromWorld(World) != nullptr)
	{
		Held->Destroy();
	}
}

FVector FJadgCombatSpace::ToWorld(core::Meters3 Point) const
{
	const FVector Ground = Frame->ToWorld(
		FVector2D(Point.x / core::METERS_PER_TILE, Point.y / core::METERS_PER_TILE) + OriginCells);
	return FVector(Ground.X, Ground.Y, Frame->GetActorLocation().Z + Point.z * CentimetersPerMeter);
}

core::Meters3 FJadgCombatSpace::FromWorld(const FVector& Point) const
{
	const FVector2D Cell = Frame->ToCell(Point) - OriginCells;
	return {static_cast<float>(Cell.X) * core::METERS_PER_TILE, static_cast<float>(Cell.Y) * core::METERS_PER_TILE,
		static_cast<float>((Point.Z - Frame->GetActorLocation().Z) / CentimetersPerMeter)};
}

float FJadgCombatSpace::groundHeight(float X, float Y) const
{
	const FVector Top = ToWorld({X, Y, ProbeHeight / CentimetersPerMeter});
	const FVector Bottom = ToWorld({X, Y, -ProbeHeight / CentimetersPerMeter});
	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(JadgGround), false);
	if (World->LineTraceSingleByObjectType(Hit, Top, Bottom, FCollisionObjectQueryParams(ECC_WorldStatic), Params))
	{
		return FromWorld(Hit.ImpactPoint).z;
	}
	return 0.0f;
}

bool FJadgCombatSpace::isClear(const core::Volume& Volume, core::Locomotion Locomotion) const
{
	// Le cylindre, un centimètre en retrait : un volume tangent à un mur (une créature M au centre de
	// la case voisine) tient, comme dans la simulation de Core.
	const float Radius = FMath::Max(1.0f, Volume.radius * CentimetersPerMeter - 1.0f);
	const float HalfHeight = Volume.height * CentimetersPerMeter / 2.0f;
	// Le cylindre, posé un doigt au-dessus du sol pour ne pas toucher ce qu'il foule.
	const FVector Centre = ToWorld({Volume.base.x, Volume.base.y, Volume.base.z}) + FVector(0.0, 0.0, HalfHeight + 2.0);
	// La carte seule — le décor statique —, jamais une figurine : les corps sont les volumes de Core.
	FCollisionQueryParams Params(SCENE_QUERY_STAT(JadgClear), false);
	const bool bBlocked = World->OverlapAnyTestByObjectType(
		Centre, FQuat::Identity, FCollisionObjectQueryParams(ECC_WorldStatic), FCollisionShape::MakeCapsule(Radius, HalfHeight), Params);
	if (bBlocked)
	{
		return false;
	}
	if (Locomotion == core::Locomotion::Walk)
	{
		// Au sol, il faut un sol : un point du maillage de navigation sous les pieds.
		const UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
		FNavLocation OnMesh;
		return Navigation != nullptr
			&& Navigation->ProjectPointToNavigation(ToWorld(Volume.base), OnMesh, FVector(Radius, Radius, 100.0));
	}
	return true;
}

bool FJadgCombatSpace::lineOfSight(core::Meters3 From, core::Meters3 To) const
{
	// Les corps n'arrêtent pas la vue (Core les compte à part) : le décor statique seul.
	FCollisionQueryParams Params(SCENE_QUERY_STAT(JadgSight), false);
	return !World->LineTraceTestByObjectType(ToWorld(From), ToWorld(To), FCollisionObjectQueryParams(ECC_WorldStatic), Params);
}

bool FJadgCombatSpace::OverlapsBlocking(core::Meters3 Point, const core::RouteQuery& Query) const
{
	core::Volume Here = Query.mover;
	Here.base = Point;
	const auto Meets = [&](const core::Volume& Other) { return core::overlap(Here, Other); };
	return std::any_of(Query.blocking.begin(), Query.blocking.end(), Meets)
		|| std::any_of(Query.passable.begin(), Query.passable.end(), Meets);
}

std::optional<core::Route> FJadgCombatSpace::route(const core::RouteQuery& Query) const
{
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	const ANavigationData* NavData = Navigation != nullptr ? Navigation->GetDefaultNavDataInstance(FNavigationSystem::DontCreate) : nullptr;
	if (NavData == nullptr)
	{
		return std::nullopt;
	}
	// Le chemin sans objet du moteur (`FindPathSync`) : l'IA en demande des centaines par tour.
	const FPathFindingQuery PathQuery(nullptr, *NavData, ToWorld(Query.mover.base), ToWorld(Query.destination));
	const FPathFindingResult Found = Navigation->FindPathSync(PathQuery);
	if (!Found.IsSuccessful() || !Found.Path.IsValid() || Found.IsPartial() || Found.Path->GetPathPoints().Num() < 2)
	{
		return std::nullopt;
	}
	const float Length = static_cast<float>(Found.Path->GetLength()) / CentimetersPerMeter;
	if (Query.budget >= 0.0f && Length > Query.budget + 1e-3f)
	{
		return std::nullopt;
	}
	core::Route Result;
	Result.length = Length;
	const TArray<FNavPathPoint>& Points = Found.Path->GetPathPoints();
	for (int32 Index = 1; Index < Points.Num(); ++Index)
	{
		Result.points.push_back(FromWorld(Points[Index].Location));
	}
	if (OverlapsBlocking(Result.points.back(), Query))
	{
		return std::nullopt;
	}
	return Result;
}

float FJadgCombatSpace::GridHalfWidth(const core::RouteQuery& Query) const
{
	if (Query.budget >= 0.0f)
	{
		return Query.budget;
	}
	// Sans limite : jusqu'au coin le plus loin du maillage de navigation de la carte.
	const UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	const FBox Bounds = Navigation != nullptr ? Navigation->GetNavigableWorldBounds() : FBox(ForceInit);
	if (!Bounds.IsValid)
	{
		return 30.0f;
	}
	const FVector From = ToWorld(Query.mover.base);
	double Far = 0.0;
	for (const double X : {Bounds.Min.X, Bounds.Max.X})
	{
		for (const double Y : {Bounds.Min.Y, Bounds.Max.Y})
		{
			Far = FMath::Max(Far, FMath::Max(FMath::Abs(X - From.X), FMath::Abs(Y - From.Y)));
		}
	}
	return static_cast<float>(Far / CentimetersPerMeter);
}

UEnvQuery* FJadgCombatSpace::QueryFor(float HalfWidth) const
{
	const int32 Key = FMath::RoundToInt32(HalfWidth * CentimetersPerMeter);
	if (const TStrongObjectPtr<UEnvQuery>* Known = Queries.Find(Key))
	{
		return Known->Get();
	}
	// La requête construite en C++ (aucun asset) : une option, un générateur en grille autour du
	// demandeur, projeté sur le maillage de navigation. Son nom porte sa demi-largeur : le
	// gestionnaire d'EQS garde une copie de chaque requête par nom.
	// Un nom unique : deux espaces (deux combats, deux tests) ne se partagent pas une requête.
	const FName Name = MakeUniqueObjectName(GetTransientPackage(), UEnvQuery::StaticClass(),
		FName(*FString::Printf(TEXT("JadgCandidats_%d"), Key)));
	UEnvQuery* Query = NewObject<UEnvQuery>(GetTransientPackage(), Name);
	UEnvQueryOption* Option = NewObject<UEnvQueryOption>(Query);
	UEnvQueryGenerator_SimpleGrid* Grid = NewObject<UEnvQueryGenerator_SimpleGrid>(Option);
	Grid->GridSize.DefaultValue = HalfWidth * CentimetersPerMeter;
	Grid->SpaceBetween.DefaultValue = CandidateStep * CentimetersPerMeter;
	Grid->ProjectionData.TraceMode = EEnvQueryTrace::Navigation;
	Grid->ProjectionData.bCanProjectDown = true;
	Grid->ProjectionData.ExtentX = 20.0f;
	Grid->ProjectionData.ProjectDown = 300.0f;
	Grid->ProjectionData.ProjectUp = 300.0f;
	Option->Generator = Grid;
	Query->GetOptionsMutable().Add(Option);
	Queries.Add(Key, TStrongObjectPtr<UEnvQuery>(Query));
	return Query;
}

TArray<FVector> FJadgCombatSpace::GridPoints(const core::RouteQuery& Query, float HalfWidth) const
{
	TArray<FVector> Points;
	const FVector Centre = ToWorld(Query.mover.base);
	UEnvQueryManager* Manager = UEnvQueryManager::GetCurrent(World);
	if (Manager != nullptr)
	{
		AActor* Held = Querier.Get();
		if (Held == nullptr)
		{
			FActorSpawnParameters Spawn;
			Spawn.ObjectFlags |= RF_Transient;
			Spawn.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
			Held = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform(Centre), Spawn);
			if (Held != nullptr && Held->GetRootComponent() == nullptr)
			{
				USceneComponent* Root = NewObject<USceneComponent>(Held, TEXT("Racine"));
				Held->SetRootComponent(Root);
				Root->RegisterComponent();
			}
			Querier = Held;
		}
		if (Held != nullptr)
		{
			Held->SetActorLocation(Centre);
			FEnvQueryRequest Request(QueryFor(HalfWidth), Held);
			const TSharedPtr<FEnvQueryResult> Result = Manager->RunInstantQuery(Request, EEnvQueryRunMode::AllMatching);
			if (Result.IsValid() && Result->IsSuccessful())
			{
				for (int32 Index = 0; Index < Result->Items.Num(); ++Index)
				{
					Points.Add(Result->GetItemAsLocation(Index));
				}
				Stats.bFromEqs = true;
				return Points;
			}
		}
	}

	// L'échantillonnage de secours : la même grille, projetée point par point.
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (Navigation == nullptr)
	{
		return Points;
	}
	const int32 Steps = FMath::CeilToInt32(HalfWidth / CandidateStep);
	for (int32 Row = -Steps; Row <= Steps; ++Row)
	{
		for (int32 Column = -Steps; Column <= Steps; ++Column)
		{
			const core::Meters3 Flat{Query.mover.base.x + static_cast<float>(Column) * CandidateStep,
				Query.mover.base.y + static_cast<float>(Row) * CandidateStep, Query.mover.base.z};
			FNavLocation OnMesh;
			if (Navigation->ProjectPointToNavigation(ToWorld(Flat), OnMesh, FVector(20.0, 20.0, 300.0)))
			{
				Points.Add(OnMesh.Location);
			}
		}
	}
	Stats.bFromEqs = false;
	return Points;
}

std::vector<core::Destination> FJadgCombatSpace::candidates(const core::RouteQuery& Query) const
{
	const double Start = FPlatformTime::Seconds();
	Stats = FJadgCandidateStats();
	std::vector<core::Destination> Result;
	Result.push_back({Query.mover.base, {}});

	const float HalfWidth = GridHalfWidth(Query);
	const TArray<FVector> Points = GridPoints(Query, HalfWidth);
	Stats.Generated = Points.Num();
	const FVector Origin = ToWorld(Query.mover.base);
	// Deux points de la grille que la projection pose au même endroit sont une seule place.
	TSet<FIntPoint> Seen;
	Seen.Add(FIntPoint(FMath::RoundToInt32(Origin.X / SamePlace), FMath::RoundToInt32(Origin.Y / SamePlace)));
	for (const FVector& OnMesh : Points)
	{
		bool bSeen = false;
		Seen.Add(FIntPoint(FMath::RoundToInt32(OnMesh.X / SamePlace), FMath::RoundToInt32(OnMesh.Y / SamePlace)), &bSeen);
		if (bSeen)
		{
			continue;
		}
		const core::Meters3 Point = FromWorld(OnMesh);
		if (Query.budget >= 0.0f && core::groundDistance(Point, Query.mover.base) > Query.budget + 1e-3f)
		{
			continue;
		}
		core::Volume Here = Query.mover;
		Here.base = Point;
		if (!isClear(Here, Query.locomotion) || OverlapsBlocking(Point, Query))
		{
			continue;
		}
		core::RouteQuery Reach = Query;
		Reach.destination = Point;
		if (std::optional<core::Route> Path = route(Reach))
		{
			Result.push_back({Point, std::move(*Path)});
		}
	}
	Stats.Kept = static_cast<int32>(Result.size()) - 1;
	Stats.Milliseconds = (FPlatformTime::Seconds() - Start) * 1000.0;
	Sum.Queries += 1;
	Sum.EqsQueries += Stats.bFromEqs ? 1 : 0;
	Sum.Generated += Stats.Generated;
	Sum.Kept += Stats.Kept;
	Sum.Milliseconds += Stats.Milliseconds;
	Sum.WorstMilliseconds = FMath::Max(Sum.WorstMilliseconds, Stats.Milliseconds);
	if (Query.budget < 0.0f)
	{
		Sum.UnlimitedQueries += 1;
		Sum.UnlimitedMilliseconds += Stats.Milliseconds;
		Sum.WorstUnlimitedMilliseconds = FMath::Max(Sum.WorstUnlimitedMilliseconds, Stats.Milliseconds);
	}
	return Result;
}
