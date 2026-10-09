// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/CombatSpace.h"

#include <algorithm>
#include <cmath>

#include "Combat/JadgCombatSpace.h"

#include "CollisionQueryParams.h"
#include "Engine/World.h"
#include "NavigationPath.h"
#include "NavigationSystem.h"
#include "World/JadgMapFrame.h"

namespace
{
	constexpr float CentimetersPerMeter = 100.0f;
	/// Le pas d'échantillonnage des candidats, en mètres : une demi-case.
	constexpr float CandidateStep = 0.75f;
	/// La hauteur depuis laquelle on cherche le sol, et jusqu'où.
	constexpr float ProbeHeight = 5000.0f;
}

FJadgCombatSpace::FJadgCombatSpace(UWorld* InWorld, const AJadgMapFrame* InFrame) : World(InWorld), Frame(InFrame) {}

FVector FJadgCombatSpace::ToWorld(core::Meters3 Point) const
{
	const FVector Ground = Frame->ToWorld(FVector2D(Point.x / core::METERS_PER_TILE, Point.y / core::METERS_PER_TILE));
	return FVector(Ground.X, Ground.Y, Frame->GetActorLocation().Z + Point.z * CentimetersPerMeter);
}

core::Meters3 FJadgCombatSpace::FromWorld(const FVector& Point) const
{
	const FVector2D Cell = Frame->ToCell(Point);
	return {static_cast<float>(Cell.X) * core::METERS_PER_TILE, static_cast<float>(Cell.Y) * core::METERS_PER_TILE,
		static_cast<float>((Point.Z - Frame->GetActorLocation().Z) / CentimetersPerMeter)};
}

float FJadgCombatSpace::groundHeight(float X, float Y) const
{
	const FVector Top = ToWorld({X, Y, ProbeHeight / CentimetersPerMeter});
	const FVector Bottom = ToWorld({X, Y, -ProbeHeight / CentimetersPerMeter});
	FHitResult Hit;
	FCollisionQueryParams Params(SCENE_QUERY_STAT(JadgGround), false);
	if (World->LineTraceSingleByChannel(Hit, Top, Bottom, ECC_WorldStatic, Params))
	{
		return FromWorld(Hit.ImpactPoint).z;
	}
	return 0.0f;
}

bool FJadgCombatSpace::isClear(const core::Volume& Volume, core::Locomotion Locomotion) const
{
	const float Radius = Volume.radius * CentimetersPerMeter;
	const float HalfHeight = Volume.height * CentimetersPerMeter / 2.0f;
	// Le cylindre, posé un doigt au-dessus du sol pour ne pas toucher ce qu'il foule.
	const FVector Centre = ToWorld({Volume.base.x, Volume.base.y, Volume.base.z}) + FVector(0.0, 0.0, HalfHeight + 2.0);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(JadgClear), false);
	const bool bBlocked = World->OverlapBlockingTestByChannel(
		Centre, FQuat::Identity, ECC_WorldStatic, FCollisionShape::MakeCapsule(Radius, HalfHeight), Params);
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
	FCollisionQueryParams Params(SCENE_QUERY_STAT(JadgSight), false);
	return !World->LineTraceTestByChannel(ToWorld(From), ToWorld(To), ECC_WorldStatic, Params);
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
	if (Navigation == nullptr)
	{
		return std::nullopt;
	}
	const FVector Start = ToWorld(Query.mover.base);
	const FVector End = ToWorld(Query.destination);
	UNavigationPath* Path = Navigation->FindPathToLocationSynchronously(World, Start, End);
	if (Path == nullptr || !Path->IsValid() || Path->IsPartial() || Path->PathPoints.Num() < 2)
	{
		return std::nullopt;
	}
	const float Length = static_cast<float>(Path->GetPathLength()) / CentimetersPerMeter;
	if (Query.budget >= 0.0f && Length > Query.budget + 1e-3f)
	{
		return std::nullopt;
	}
	core::Route Result;
	Result.length = Length;
	for (int32 Index = 1; Index < Path->PathPoints.Num(); ++Index)
	{
		Result.points.push_back(FromWorld(Path->PathPoints[Index]));
	}
	if (OverlapsBlocking(Result.points.back(), Query))
	{
		return std::nullopt;
	}
	return Result;
}

std::vector<core::Destination> FJadgCombatSpace::candidates(const core::RouteQuery& Query) const
{
	std::vector<core::Destination> Result;
	Result.push_back({Query.mover.base, {}});
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (Navigation == nullptr || Query.budget < 0.0f)
	{
		return Result;
	}
	const int32 Steps = static_cast<int32>(std::ceil(Query.budget / CandidateStep));
	const float Radius = Query.mover.radius * CentimetersPerMeter;
	for (int32 Row = -Steps; Row <= Steps; ++Row)
	{
		for (int32 Column = -Steps; Column <= Steps; ++Column)
		{
			if (Row == 0 && Column == 0)
			{
				continue;
			}
			const core::Meters3 Flat{Query.mover.base.x + static_cast<float>(Column) * CandidateStep,
				Query.mover.base.y + static_cast<float>(Row) * CandidateStep, Query.mover.base.z};
			if (core::groundDistance(Flat, Query.mover.base) > Query.budget + 1e-3f)
			{
				continue;
			}
			FNavLocation OnMesh;
			if (!Navigation->ProjectPointToNavigation(ToWorld(Flat), OnMesh, FVector(Radius / 2.0f, Radius / 2.0f, 300.0)))
			{
				continue;
			}
			const core::Meters3 Point = FromWorld(OnMesh.Location);
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
	}
	return Result;
}
