// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Scene/JadgSceneBuild.h"

#include "Components/InstancedStaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Volume.h"
#include "EngineUtils.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationSystem.h"

#if WITH_EDITOR
#include "ActorFactories/ActorFactory.h"
#include "Builders/CubeBuilder.h"
#include "Landscape.h"
#include "LandscapeInfo.h"
#include "LandscapeLayerInfoObject.h"
#include "LandscapeProxy.h"
#include "LandscapeUtils.h"
#include "Materials/MaterialInterface.h"
#endif

AActor* UJadgSceneBuild::SpawnActor(UObject* WorldContextObject, TSubclassOf<AActor> ActorClass, const FTransform& Transform)
{
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	if (World == nullptr || ActorClass == nullptr)
	{
		return nullptr;
	}
	FActorSpawnParameters Parameters;
	Parameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	return World->SpawnActor<AActor>(ActorClass, Transform, Parameters);
}

AVolume* UJadgSceneBuild::SpawnBoxVolume(UObject* WorldContextObject, TSubclassOf<AVolume> VolumeClass, FVector Centre, FVector Size)
{
#if WITH_EDITOR
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	if (World == nullptr || VolumeClass == nullptr)
	{
		return nullptr;
	}
	AVolume* Volume = World->SpawnActor<AVolume>(VolumeClass, FTransform(Centre));
	if (Volume == nullptr)
	{
		return nullptr;
	}
	UCubeBuilder* Builder = NewObject<UCubeBuilder>();
	Builder->X = Size.X;
	Builder->Y = Size.Y;
	Builder->Z = Size.Z;
	UActorFactory::CreateBrushForVolumeActor(Volume, Builder);
	return Volume;
#else
	return nullptr;
#endif
}

AActor* UJadgSceneBuild::SpawnInstances(UObject* WorldContextObject, UStaticMesh* Mesh, const TArray<FTransform>& Transforms)
{
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	if (World == nullptr || Mesh == nullptr)
	{
		return nullptr;
	}
	FActorSpawnParameters Parameters;
	Parameters.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AActor* Actor = World->SpawnActor<AActor>(AActor::StaticClass(), FTransform::Identity, Parameters);
	if (Actor == nullptr)
	{
		return nullptr;
	}
	// Un composant ajouté hors du constructeur se déclare à l'acteur, sans quoi la carte sauvée le perd.
	UInstancedStaticMeshComponent* Instances = NewObject<UInstancedStaticMeshComponent>(Actor, TEXT("Instances"));
	Instances->SetMobility(EComponentMobility::Static);
	Instances->SetStaticMesh(Mesh);
	Actor->SetRootComponent(Instances);
	Actor->AddInstanceComponent(Instances);
	Instances->RegisterComponent();
	Instances->AddInstances(Transforms, false, true);
	return Actor;
}

AActor* UJadgSceneBuild::SpawnLandscape(UObject* WorldContextObject, FVector Location, FVector Scale, int32 QuadsX, int32 QuadsY,
	const TArray<int32>& Heights, const TArray<FString>& LayerNames, const TArray<uint8>& Weights, UMaterialInterface* Material,
	const FString& LayerFolder)
{
#if WITH_EDITOR
	constexpr int32 QuadsPerComponent = 63;
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	const int32 Vertices = (QuadsX + 1) * (QuadsY + 1);
	if (World == nullptr || QuadsX <= 0 || QuadsY <= 0 || QuadsX % QuadsPerComponent != 0 || QuadsY % QuadsPerComponent != 0
		|| Heights.Num() != Vertices || Weights.Num() != Vertices * LayerNames.Num())
	{
		UE_LOG(LogTemp, Error, TEXT("[Scene] terrain : %d x %d quads (multiples de %d), %d hauteurs pour %d sommets, %d poids pour %d couches"),
			QuadsX, QuadsY, QuadsPerComponent, Heights.Num(), Vertices, Weights.Num(), LayerNames.Num());
		return nullptr;
	}
	TArray<uint16> HeightData;
	HeightData.Reserve(Vertices);
	for (const int32 Height : Heights)
	{
		HeightData.Add(static_cast<uint16>(FMath::Clamp(Height, 0, 65535)));
	}
	TArray<FLandscapeImportLayerInfo> Layers;
	for (int32 Index = 0; Index < LayerNames.Num(); ++Index)
	{
		const FName Name(*LayerNames[Index]);
		const FString AssetName = TEXT("LI_") + LayerNames[Index];
		ULandscapeLayerInfoObject* Info = LoadObject<ULandscapeLayerInfoObject>(nullptr,
			*FString::Printf(TEXT("%s/%s.%s"), *LayerFolder, *AssetName, *AssetName), nullptr, LOAD_NoWarn | LOAD_Quiet);
		if (Info == nullptr)
		{
			Info = UE::Landscape::CreateTargetLayerInfo(Name, LayerFolder, AssetName);
		}
		if (Info == nullptr)
		{
			UE_LOG(LogTemp, Error, TEXT("[Scene] terrain : la couche %s n'a pas d'objet de couche sous %s"), *LayerNames[Index], *LayerFolder);
			return nullptr;
		}
		FLandscapeImportLayerInfo& Layer = Layers.Emplace_GetRef(Name);
		Layer.LayerInfo = Info;
		Layer.LayerData = TArray<uint8>(Weights.GetData() + Index * Vertices, Vertices);
	}

	ALandscape* Landscape = World->SpawnActor<ALandscape>(Location, FRotator::ZeroRotator);
	if (Landscape == nullptr)
	{
		return nullptr;
	}
	Landscape->LandscapeMaterial = Material;
	Landscape->SetActorRelativeScale3D(Scale);
	TMap<FGuid, TArray<uint16>> HeightDataPerLayers;
	HeightDataPerLayers.Add(FGuid(), MoveTemp(HeightData));
	TMap<FGuid, TArray<FLandscapeImportLayerInfo>> MaterialLayerDataPerLayers;
	MaterialLayerDataPerLayers.Add(FGuid(), Layers);
	Landscape->Import(FGuid::NewGuid(), 0, 0, QuadsX, QuadsY, 1, QuadsPerComponent, HeightDataPerLayers, nullptr,
		MaterialLayerDataPerLayers, ELandscapeImportAlphamapType::Additive, TArrayView<const FLandscapeLayer>());
	if (ULandscapeInfo* LandscapeInfo = Landscape->GetLandscapeInfo())
	{
		LandscapeInfo->UpdateLayerInfoMap(Landscape);
		for (const FLandscapeImportLayerInfo& Layer : Layers)
		{
			Landscape->AddTargetLayer(Layer.LayerName, FLandscapeTargetLayerSettings(Layer.LayerInfo));
			const int32 LayerIndex = LandscapeInfo->GetLayerInfoIndex(Layer.LayerName);
			if (LayerIndex != INDEX_NONE)
			{
				LandscapeInfo->Layers[LayerIndex].LayerInfoObj = Layer.LayerInfo;
			}
		}
	}
	return Landscape;
#else
	return nullptr;
#endif
}

TArray<int32> UJadgSceneBuild::UnreachablePoints(UObject* WorldContextObject, FVector Start, const TArray<FVector>& Points)
{
	TArray<int32> Unreachable;
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	if (World == nullptr)
	{
		Unreachable.Add(-1);
		return Unreachable;
	}
	if (FNavigationSystem::GetCurrent<UNavigationSystemV1>(World) == nullptr)
	{
		FNavigationSystem::AddNavigationSystemToWorld(*World, FNavigationSystemRunMode::EditorMode);
	}
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (Navigation == nullptr)
	{
		Unreachable.Add(-1);
		return Unreachable;
	}
	// Un monde d'éditeur garde la construction verrouillée tant qu'une carte se charge
	// (`AsyncLoadLock`) : on la libère, le temps de construire et de mesurer.
	Navigation->RemoveNavigationBuildLock(0xFF, UNavigationSystemV1::ELockRemovalRebuildAction::NoRebuild);
	// Les volumes de navigation ont reçu leur brosse après leur création : leurs bornes se relisent,
	// et le maillage de navigation du niveau est créé s'il n'existe pas encore.
	for (TActorIterator<ANavMeshBoundsVolume> It(World); It; ++It)
	{
		Navigation->OnNavigationBoundsUpdated(*It);
	}
	ANavigationData* NavData = Navigation->GetDefaultNavDataInstance(FNavigationSystem::Create);
	Navigation->Build();
	FNavLocation From;
	if (NavData == nullptr || !Navigation->ProjectPointToNavigation(Start, From, FVector(100.0, 100.0, 300.0)))
	{
		Unreachable.Add(-1);
		return Unreachable;
	}
	for (int32 Index = 0; Index < Points.Num(); ++Index)
	{
		FNavLocation To;
		bool bReached = Navigation->ProjectPointToNavigation(Points[Index], To, FVector(100.0, 100.0, 150.0));
		if (bReached)
		{
			const FPathFindingQuery Query(nullptr, *NavData, From.Location, To.Location);
			const FPathFindingResult Result = Navigation->FindPathSync(Query);
			bReached = Result.IsSuccessful() && !Result.IsPartial();
		}
		if (!bReached)
		{
			Unreachable.Add(Index);
		}
	}
	return Unreachable;
}
