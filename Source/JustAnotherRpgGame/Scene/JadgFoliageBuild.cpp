// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#include "Scene/JadgFoliageBuild.h"

#if WITH_EDITOR
#include "Engine/World.h"
#include "FoliageType.h"
#include "InstancedFoliageActor.h"
#include "Landscape.h"
#include "LandscapeComponent.h"
#include "LandscapeHeightfieldCollisionComponent.h"
#endif

int32 UJadgFoliageBuild::PlantOnLandscape(AActor* Surface, UObject* FoliageTypeAsset, const TArray<FTransform>& Transforms)
{
#if WITH_EDITOR
	ALandscape* Landscape = Cast<ALandscape>(Surface);
	UFoliageType* Type = Cast<UFoliageType>(FoliageTypeAsset);
	if (Landscape == nullptr || Type == nullptr || Landscape->GetWorld() == nullptr)
	{
		return -1;
	}
	TInlineComponentArray<ULandscapeComponent*> Components(Landscape);
	TArray<FFoliageInstance> Instances;
	Instances.Reserve(Transforms.Num());
	for (const FTransform& Transform : Transforms)
	{
		const FVector Point = Transform.GetLocation();
		ULandscapeComponent* Base = nullptr;
		for (ULandscapeComponent* Component : Components)
		{
			const FBox Box = Component->Bounds.GetBox();
			if (Point.X >= Box.Min.X - 0.1 && Point.X <= Box.Max.X + 0.1 &&
				Point.Y >= Box.Min.Y - 0.1 && Point.Y <= Box.Max.Y + 0.1)
			{
				Base = Component;
				break;
			}
		}
		// Validate all placements before mutating the level. UE 5.8's unbased
		// AddInstances path dereferences null in FoliageEdit's base-class filter.
		if (Base == nullptr)
		{
			return -1;
		}
		FFoliageInstance& Instance = Instances.AddDefaulted_GetRef();
		Instance.Location = Point;
		Instance.Rotation = Transform.GetRotation().Rotator();
		Instance.DrawScale3D = FVector3f(Transform.GetScale3D());
		Instance.BaseComponent = Base;
	}
	AInstancedFoliageActor* Actor = AInstancedFoliageActor::Get(Landscape->GetWorld(), true, Landscape->GetLevel());
	if (Actor == nullptr)
	{
		return -1;
	}
	FFoliageInfo* Info = nullptr;
	UFoliageType* LocalType = Actor->AddFoliageType(Type, &Info);
	if (LocalType == nullptr || Info == nullptr)
	{
		return -1;
	}
	TArray<const FFoliageInstance*> Pointers;
	Pointers.Reserve(Instances.Num());
	for (const FFoliageInstance& Instance : Instances)
	{
		Pointers.Add(&Instance);
	}
	Info->AddInstances(LocalType, Pointers);
	Actor->MarkPackageDirty();
	return Instances.Num();
#else
	return -1;
#endif
}

int32 UJadgFoliageBuild::GroundFoliageRoots(AActor* FoliageActor, const TArray<FVector>& Candidates, bool bApply, int32& OutChecked)
{
	OutChecked = 0;
#if WITH_EDITOR
	AInstancedFoliageActor* Actor = Cast<AInstancedFoliageActor>(FoliageActor);
	if (Actor == nullptr) return -1;
	TSet<FIntPoint> Keys;
	for (const FVector& Point : Candidates)
		Keys.Add(FIntPoint(FMath::RoundToInt(Point.X), FMath::RoundToInt(Point.Y)));
	int32 Changed = 0;
	bool Valid = true;
	Actor->ForEachFoliageInfo([&](UFoliageType*, FFoliageInfo& Info)
	{
		TArray<int32> Indices;
		TArray<double> Heights;
		for (int32 Index = 0; Index < Info.Instances.Num(); ++Index)
		{
			const FFoliageInstance& Instance = Info.Instances[Index];
			const FVector Point = Instance.Location;
			if (!Keys.Contains(FIntPoint(FMath::RoundToInt(Point.X), FMath::RoundToInt(Point.Y)))) continue;
			++OutChecked;
			const ULandscapeComponent* Base = Cast<ULandscapeComponent>(Actor->InstanceBaseCache.GetInstanceBasePtr(Instance.BaseId).Get());
			ULandscapeHeightfieldCollisionComponent* Collision = Base ? Base->GetCollisionComponent() : nullptr;
			FHitResult Hit;
			FCollisionQueryParams Params(SCENE_QUERY_STAT(CapitalFoliageGround), true);
			if (!Collision || !Collision->LineTraceComponent(Hit, Point + FVector(0,0,10000), Point - FVector(0,0,10000), Params))
			{
				Valid = false;
				continue;
			}
			const double Height = Hit.ImpactPoint.Z - 1.; // Root sits 1 cm into the soil.
			if (FMath::Abs(Point.Z - Height) > (bApply ? 0.5 : 2.))
			{
				Indices.Add(Index);
				Heights.Add(Height);
			}
		}
		Changed += Indices.Num();
		if (bApply && !Indices.IsEmpty())
		{
			Info.PreMoveInstances(Indices);
			for (int32 I = 0; I < Indices.Num(); ++I) Info.Instances[Indices[I]].Location.Z = Heights[I];
			Info.PostMoveInstances(Indices, true);
			Actor->MarkPackageDirty();
		}
		return true;
	});
	return Valid ? Changed : -1;
#else
	return -1;
#endif
}
