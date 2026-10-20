// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#include "Commandlets/JadgConvertCapitalCommandlet.h"

#if WITH_EDITOR
#include "Commandlets/WorldPartitionConvertCommandlet.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "InstancedFoliageActor.h"
#endif

UJadgConvertCapitalCommandlet::UJadgConvertCapitalCommandlet()
{
	IsClient = false;
	IsServer = false;
	IsEditor = true;
	LogToConsole = true;
}

int32 UJadgConvertCapitalCommandlet::Main(const FString& Params)
{
#if WITH_EDITOR
	// The stock converter copies serialized FFoliageInstances directly into new
	// grid actors. BaseComponent is transient and is null after loading; the 5.8
	// foliage editor filter dereferences it. Restore it from the saved base cache
	// before partitioning. Heights, transforms, meshes and source maps are unchanged.
	const FDelegateHandle Handle = FWorldDelegates::OnPostWorldInitialization.AddLambda(
		[](UWorld* World, const UWorld::InitializationValues)
		{
			int32 Restored = 0;
			for (TActorIterator<AInstancedFoliageActor> It(World); It; ++It)
			{
				AInstancedFoliageActor* Actor = *It;
				Actor->ForEachFoliageInfo([&](UFoliageType*, FFoliageInfo& Info)
				{
					for (FFoliageInstance& Instance : Info.Instances)
					{
						const auto Base = Actor->InstanceBaseCache.GetInstanceBasePtr(Instance.BaseId);
						UPrimitiveComponent* Component = Cast<UPrimitiveComponent>(Base.Get());
						if (!Component)
						{
							UE_LOG(LogTemp, Fatal, TEXT("[CapitalConvert] Missing foliage base %d in %s"), Instance.BaseId, *Actor->GetPathName());
						}
						Instance.BaseComponent = Component;
						++Restored;
					}
					return true;
				});
			}
			UE_LOG(LogTemp, Display, TEXT("[CapitalConvert] Restored %d transient foliage bases"), Restored);
		});
	UWorldPartitionConvertCommandlet* Converter = NewObject<UWorldPartitionConvertCommandlet>();
	Converter->AddToRoot();
	const int32 Result = Converter->Main(Params);
	Converter->RemoveFromRoot();
	FWorldDelegates::OnPostWorldInitialization.Remove(Handle);
	return Result;
#else
	return 1;
#endif
}
