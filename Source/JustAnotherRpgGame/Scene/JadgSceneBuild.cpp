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
#include "LandscapeComponent.h"
#include "LandscapeEditLayer.h"
#include "LandscapeInfo.h"
#include "LandscapeLayerInfoObject.h"
#include "LandscapeEditTypes.h"
#include "LandscapeProxy.h"
#include "LandscapeSubsystem.h"
#include "LandscapeUtils.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpression.h"
#include "Materials/MaterialExpressionComponentMask.h"
#include "Materials/MaterialExpressionConstant.h"
#include "Materials/MaterialExpressionLandscapeLayerSample.h"
#include "Materials/MaterialExpressionMaterialFunctionCall.h"
#include "Materials/MaterialExpressionTextureCoordinate.h"
#include "Materials/MaterialExpressionVertexColor.h"
#include "Materials/MaterialExpressionWorldPosition.h"
#include "Materials/MaterialFunction.h"
#include "Materials/MaterialInterface.h"
#include "AssetCompilingManager.h"
#include "ShaderCompiler.h"
#include "RenderingThread.h"
#include "Misc/App.h"
#include "WorldPartition/WorldPartition.h"
#include "WorldPartition/WorldPartitionRuntimeHash.h"
#include "WorldPartition/RuntimeHashSet/RuntimePartitionLHGrid.h"
#include "WorldPartition/RuntimeHashSet/WorldPartitionRuntimeHashSet.h"
#endif

UObject* UJadgSceneBuild::WorldPartitionRuntimeHash(UObject* WorldContextObject)
{
#if WITH_EDITOR
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	return World && World->GetWorldPartition() ? World->GetWorldPartition()->RuntimeHash.Get() : nullptr;
#else
	return nullptr;
#endif
}

bool UJadgSceneBuild::SetWorldPartitionStreaming(UObject* WorldContextObject, bool bEnabled)
{
#if WITH_EDITOR
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	if (UWorldPartition* Partition = World ? World->GetWorldPartition() : nullptr)
	{
		Partition->Modify();
		Partition->SetEnableStreaming(bEnabled);
		return Partition->IsStreamingEnabled() == bEnabled;
	}
#endif
	return false;
}

bool UJadgSceneBuild::IsWorldPartitionStreaming(UObject* WorldContextObject)
{
#if WITH_EDITOR
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	return World && World->GetWorldPartition() && World->GetWorldPartition()->IsStreamingEnabled();
#else
	return false;
#endif
}

bool UJadgSceneBuild::AddRuntimePartition(UObject* WorldContextObject, FName Name, int32 CellSize, int32 LoadingRange)
{
#if WITH_EDITOR
	UWorld* World = GEngine->GetWorldFromContextObject(WorldContextObject, EGetWorldErrorMode::LogAndReturnNull);
	UWorldPartitionRuntimeHashSet* Hash = World && World->GetWorldPartition()
		? Cast<UWorldPartitionRuntimeHashSet>(World->GetWorldPartition()->RuntimeHash.Get()) : nullptr;
	if (Hash == nullptr || Name.IsNone() || CellSize <= 0 || LoadingRange <= 0)
	{
		return false;
	}
	// Les champs de la grille sont protégés : écrits par réflexion, comme les écrit l'éditeur.
	auto SetField = [](UObject* Object, const TCHAR* Field, auto Value)
	{
		using FValue = decltype(Value);
		if (FProperty* Property = Object->GetClass()->FindPropertyByName(Field))
		{
			*Property->ContainerPtrToValuePtr<FValue>(Object) = Value;
			return true;
		}
		return false;
	};
	FArrayProperty* Partitions = CastField<FArrayProperty>(Hash->GetClass()->FindPropertyByName(TEXT("RuntimePartitions")));
	if (Partitions == nullptr)
	{
		return false;
	}
	Hash->Modify();
	TArray<FRuntimePartitionDesc>& Descs = *Partitions->ContainerPtrToValuePtr<TArray<FRuntimePartitionDesc>>(Hash);
	FRuntimePartitionDesc* Desc = Descs.FindByPredicate([Name](const FRuntimePartitionDesc& D) { return D.Name == Name; });
	if (Desc == nullptr)
	{
		Desc = &Descs.AddDefaulted_GetRef();
		Desc->Name = Name;
		Desc->Class = URuntimePartitionLHGrid::StaticClass();
		Desc->MainLayer = NewObject<URuntimePartitionLHGrid>(Hash, NAME_None, RF_Transactional);
		Desc->MainLayer->SetDefaultValues();
	}
	URuntimePartition* Layer = Desc->MainLayer;
	return Layer && SetField(Layer, TEXT("Name"), Name) && SetField(Layer, TEXT("CellSize"), uint32(CellSize))
		&& SetField(Layer, TEXT("LoadingRange"), LoadingRange) && SetField(Layer, TEXT("bBlockOnSlowStreaming"), false);
#else
	return false;
#endif
}

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

bool UJadgSceneBuild::ConnectMaterialDisplacement(UMaterial* Material, UMaterialExpression* Expression)
{
#if WITH_EDITOR
	if (Material == nullptr || Expression == nullptr || Expression->GetOuter() != Material)
	{
		return false;
	}
	Material->Modify();
	Material->GetEditorOnlyData()->Displacement.Connect(0, Expression);
	Material->PostEditChange();
	Material->MarkPackageDirty();
	return true;
#else
	return false;
#endif
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
	const FString& LayerFolder, bool bWeightBlended)
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
		// Un nom de couche peut porter une espace (« Material B ») ; un nom de paquet, non.
		const FString AssetName = TEXT("LI_") + LayerNames[Index].Replace(TEXT(" "), TEXT("_"));
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
		Info->SetBlendMethod(bWeightBlended ? ELandscapeTargetLayerBlendMethod::FinalWeightBlending
			: ELandscapeTargetLayerBlendMethod::None, false);
		Info->MarkPackageDirty();
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

TArray<FString> UJadgSceneBuild::LandscapeLayerNames(UMaterialInterface* Material)
{
	TArray<FString> Names;
#if WITH_EDITOR
	if (Material != nullptr)
	{
		for (const FName& Name : UE::Landscape::RetrieveTargetLayerNamesFromMaterial(Material, false))
		{
			Names.Add(Name.ToString());
		}
	}
#endif
	return Names;
}

bool UJadgSceneBuild::FinalizeLandscapeLayers(AActor* Actor)
{
#if WITH_EDITOR
	ALandscape* Landscape = Cast<ALandscape>(Actor);
	if (Landscape == nullptr || !FApp::CanEverRender())
	{
		return false;
	}
	FAssetCompilingManager::Get().FinishAllCompilation();
	if (GShaderCompilingManager != nullptr)
	{
		GShaderCompilingManager->FinishAllCompilation();
	}
	Landscape->RequestLayersContentUpdateForceAll();
	Landscape->ForceUpdateLayersContent();
	FlushRenderingCommands();
	Landscape->UpdateAllComponentMaterialInstances(true);
	Landscape->MarkPackageDirty();
	return true;
#else
	return false;
#endif
}

bool UJadgSceneBuild::NameLandscapeEditLayers(AActor* Actor, const FString& BaseLayer, const TArray<FString>& ExtraLayers)
{
#if WITH_EDITOR
	ALandscape* Landscape = Cast<ALandscape>(Actor);
	if (Landscape == nullptr || Landscape->GetEditLayersConst().Num() == 0)
	{
		return false;
	}
	if (ULandscapeEditLayerBase* Base = Landscape->GetEditLayer(0))
	{
		Base->SetName(FName(*BaseLayer), true);
	}
	for (const FString& Name : ExtraLayers)
	{
		if (Landscape->GetEditLayerConst(FName(*Name)) == nullptr && Landscape->CreateLayer(FName(*Name)) == INDEX_NONE)
		{
			UE_LOG(LogTemp, Error, TEXT("[Scene] terrain : la couche d'edition %s n'a pas ete creee"), *Name);
			return false;
		}
	}
	Landscape->MarkPackageDirty();
	return true;
#else
	return false;
#endif
}

TArray<float> UJadgSceneBuild::LandscapeWeightsAt(AActor* Actor, FVector Location, const TArray<FString>& LayerNames)
{
	TArray<float> Result;
#if WITH_EDITOR
	ALandscapeProxy* Landscape = Cast<ALandscapeProxy>(Actor);
	ULandscapeInfo* Info = Landscape != nullptr ? Landscape->GetLandscapeInfo() : nullptr;
	if (Info == nullptr)
	{
		return Result;
	}
	TInlineComponentArray<ULandscapeComponent*> Components(Landscape);
	for (ULandscapeComponent* Component : Components)
	{
		const FBox Bounds = Component->Bounds.GetBox();
		if (Location.X < Bounds.Min.X || Location.X > Bounds.Max.X || Location.Y < Bounds.Min.Y || Location.Y > Bounds.Max.Y)
		{
			continue;
		}
		for (const FString& Name : LayerNames)
		{
			const int32 Index = Info->GetLayerInfoIndex(FName(*Name));
			ULandscapeLayerInfoObject* Layer = Index != INDEX_NONE ? Info->Layers[Index].LayerInfoObj.Get() : nullptr;
			Result.Add(Layer != nullptr ? Component->GetLayerWeightAtLocation(Location, Layer) : -1.0f);
		}
		return Result;
	}
#endif
	return Result;
}

#if WITH_EDITOR
namespace
{
	/// Le graphe d'une matière ou d'une fonction de matière : ses nœuds, et qui les possède.
	FMaterialExpressionCollection* GraphOf(UObject* MaterialOrFunction)
	{
		if (UMaterial* Material = Cast<UMaterial>(MaterialOrFunction))
		{
			return &Material->GetExpressionCollection();
		}
		if (UMaterialFunction* Function = Cast<UMaterialFunction>(MaterialOrFunction))
		{
			return &Function->GetExpressionCollection();
		}
		return nullptr;
	}
}
#endif

TArray<FString> UJadgSceneBuild::PortMeshTerrainGraph(UObject* MaterialOrFunction, bool bVertexLayers)
{
	TArray<FString> Ported;
#if WITH_EDITOR
	FMaterialExpressionCollection* Graph = GraphOf(MaterialOrFunction);
	if (Graph == nullptr)
	{
		return Ported;
	}
	// Les nœuds du Mesh Terrain se reconnaissent par leur classe, sans dépendre de son plugin.
	const FString Family(TEXT("MaterialExpressionMeshPartition"));
	const FName ChannelSampleClass(TEXT("MaterialExpressionMeshPartitionChannelSample"));
	const FName TexcoordClass(TEXT("MaterialExpressionMeshPartitionTexcoord"));
	const auto Add = [Graph, MaterialOrFunction](UClass* Class, const UMaterialExpression* Like, int32 OffsetY) -> UMaterialExpression*
	{
		UMaterialExpression* Node = NewObject<UMaterialExpression>(MaterialOrFunction, Class, NAME_None, RF_Transactional);
		Node->MaterialExpressionEditorX = Like->MaterialExpressionEditorX;
		Node->MaterialExpressionEditorY = Like->MaterialExpressionEditorY + OffsetY;
		Node->UpdateMaterialExpressionGuid(true, true);
		Graph->AddExpression(Node);
		return Node;
	};
	// Pour chaque nœud remplacé : ce qui tient lieu de chacune de ses sorties.
	TMap<UMaterialExpression*, TArray<UMaterialExpression*>> Replacements;
	const TArray<TObjectPtr<UMaterialExpression>> Expressions(Graph->Expressions);
	for (UMaterialExpression* Expression : Expressions)
	{
		if (Expression == nullptr || !Expression->GetClass()->GetName().StartsWith(Family))
		{
			continue;
		}
		TArray<UMaterialExpression*>& Outputs = Replacements.Add(Expression);
		if (Expression->GetClass()->GetFName() == ChannelSampleClass)
		{
			const FNameProperty* Channel = FindFProperty<FNameProperty>(Expression->GetClass(), TEXT("Channel"));
			const FName Name = Channel != nullptr ? Channel->GetPropertyValue_InContainer(Expression) : NAME_None;
			if (bVertexLayers)
			{
				// Le prolongement visuel du paysage porte les mêmes recouvrements
				// B–E dans RGBA, exportés depuis les masques de sa bordure.
				const int32 ColorOutput = Name == TEXT("Material B") ? 1 : Name == TEXT("Material C") ? 2
					: Name == TEXT("Material D") ? 3 : Name == TEXT("Material E") ? 4 : INDEX_NONE;
				if (ColorOutput == INDEX_NONE)
				{
					// Les canaux non peints, dont RemoveAutoMaterial, restent à zéro.
					Outputs.Add(Add(UMaterialExpressionConstant::StaticClass(), Expression, 0));
				}
				else
				{
					UMaterialExpression* Color = Add(UMaterialExpressionVertexColor::StaticClass(), Expression, 0);
					UMaterialExpressionComponentMask* Mask = CastChecked<UMaterialExpressionComponentMask>(
						Add(UMaterialExpressionComponentMask::StaticClass(), Expression, 120));
					Mask->R = true;
					Mask->G = false;
					Mask->B = false;
					Mask->A = false;
					// Connect renseigne aussi le masque de sortie, notamment pour Alpha :
					// la sortie zéro de VertexColor ne contient que RGB.
					Mask->Input.Connect(ColorOutput, Color);
					Outputs.Add(Mask);
				}
			}
			else
			{
				UMaterialExpressionLandscapeLayerSample* Sample = CastChecked<UMaterialExpressionLandscapeLayerSample>(
					Add(UMaterialExpressionLandscapeLayerSample::StaticClass(), Expression, 0));
				Sample->ParameterName = Name;
				Sample->PreviewWeight = 0.f;
				Outputs.Add(Sample);
			}
			Ported.AddUnique(Name.ToString());
		}
		else if (Expression->GetClass()->GetFName() == TexcoordClass)
		{
			// « uv » : les coordonnées du maillage ; « uv [unit] » : la position dans le monde, à plat.
			Outputs.Add(Add(UMaterialExpressionTextureCoordinate::StaticClass(), Expression, 0));
			UMaterialExpression* Position = Add(UMaterialExpressionWorldPosition::StaticClass(), Expression, 120);
			UMaterialExpressionComponentMask* Flat = CastChecked<UMaterialExpressionComponentMask>(
				Add(UMaterialExpressionComponentMask::StaticClass(), Expression, 240));
			Flat->R = true;
			Flat->G = true;
			Flat->B = false;
			Flat->A = false;
			Flat->Input.Expression = Position;
			Outputs.Add(Flat);
		}
	}
	const auto Rewire = [&Replacements](FExpressionInput* Input)
	{
		if (Input == nullptr)
		{
			return;
		}
		if (const TArray<UMaterialExpression*>* Outputs = Replacements.Find(Input->Expression))
		{
			// Un nœud retiré sans équivalent laisse son entrée libre.
			Input->Expression = Outputs->IsValidIndex(Input->OutputIndex) ? (*Outputs)[Input->OutputIndex]
				: (Outputs->Num() > 0 ? (*Outputs)[0] : nullptr);
			Input->OutputIndex = 0;
		}
	};
	for (UMaterialExpression* Expression : Graph->Expressions)
	{
		for (FExpressionInputIterator It{ Expression }; It; ++It)
		{
			Rewire(It.Input);
		}
	}
	if (UMaterial* Material = Cast<UMaterial>(MaterialOrFunction))
	{
		for (int32 Property = 0; Property < MP_MAX; ++Property)
		{
			Rewire(Material->GetExpressionInputForProperty(static_cast<EMaterialProperty>(Property)));
		}
	}
	for (const TPair<UMaterialExpression*, TArray<UMaterialExpression*>>& Pair : Replacements)
	{
		Graph->RemoveExpression(Pair.Key);
	}
	MaterialOrFunction->MarkPackageDirty();
#endif
	return Ported;
}

int32 UJadgSceneBuild::RetargetFunctionCalls(UObject* MaterialOrFunction, const TArray<UMaterialFunctionInterface*>& From,
	const TArray<UMaterialFunctionInterface*>& To)
{
	int32 Retargeted = 0;
#if WITH_EDITOR
	FMaterialExpressionCollection* Graph = GraphOf(MaterialOrFunction);
	if (Graph == nullptr || From.Num() != To.Num())
	{
		return 0;
	}
	for (UMaterialExpression* Expression : Graph->Expressions)
	{
		UMaterialExpressionMaterialFunctionCall* Call = Cast<UMaterialExpressionMaterialFunctionCall>(Expression);
		const int32 Index = Call != nullptr ? From.IndexOfByKey(Call->MaterialFunction.Get()) : INDEX_NONE;
		if (Index == INDEX_NONE || To[Index] == nullptr)
		{
			continue;
		}
		// La copie a les mêmes entrées et sorties que l'originale, dans le même ordre : l'appel garde
		// ses liaisons et ne change que de cible. (`SetMaterialFunction` les reconstruit par
		// identifiant, et une copie a les siens : des entrées se retrouvaient libres.)
		TArray<FFunctionExpressionInput> Inputs;
		TArray<FFunctionExpressionOutput> Outputs;
		To[Index]->GetInputsAndOutputs(Inputs, Outputs);
		if (Inputs.Num() != Call->FunctionInputs.Num() || Outputs.Num() != Call->FunctionOutputs.Num())
		{
			UE_LOG(LogTemp, Error, TEXT("[Scene] %s : la copie n'a pas les entrées et sorties de l'originale"), *To[Index]->GetName());
			continue;
		}
		Call->MaterialFunction = To[Index];
		for (int32 Slot = 0; Slot < Inputs.Num(); ++Slot)
		{
			Call->FunctionInputs[Slot].ExpressionInput = Inputs[Slot].ExpressionInput;
			Call->FunctionInputs[Slot].ExpressionInputId = Inputs[Slot].ExpressionInputId;
		}
		for (int32 Slot = 0; Slot < Outputs.Num(); ++Slot)
		{
			Call->FunctionOutputs[Slot].ExpressionOutput = Outputs[Slot].ExpressionOutput;
			Call->FunctionOutputs[Slot].ExpressionOutputId = Outputs[Slot].ExpressionOutputId;
		}
		++Retargeted;
	}
	if (Retargeted > 0)
	{
		MaterialOrFunction->MarkPackageDirty();
	}
#endif
	return Retargeted;
}

bool UJadgSceneBuild::IsLandscapeNaniteCurrent(AActor* Landscape)
{
#if WITH_EDITOR
	const ALandscapeProxy* Proxy = Cast<ALandscapeProxy>(Landscape);
	return Proxy && Proxy->IsNaniteEnabled() && Proxy->HasNaniteComponents() && Proxy->IsNaniteMeshUpToDate();
#else
	return false;
#endif
}

int32 UJadgSceneBuild::RefreshLandscapeGrass(AActor* Landscape)
{
#if WITH_EDITOR
	ALandscapeProxy* Proxy = Cast<ALandscapeProxy>(Landscape);
	if (Proxy == nullptr)
	{
		return -1;
	}
	TSet<ULandscapeGrassType*> Remaining;
	for (ULandscapeComponent* Component : Proxy->LandscapeComponents)
	{
		if (Component == nullptr)
		{
			continue;
		}
		Component->Modify();
		Component->UpdateGrassTypes(true);
		for (const TPair<FName, TObjectPtr<ULandscapeGrassType>>& Grass : Component->GetNamedGrassTypes())
		{
			if (Grass.Value != nullptr)
			{
				Remaining.Add(Grass.Value.Get());
			}
		}
	}
	return Remaining.Num();
#else
	return -1;
#endif
}

bool UJadgSceneBuild::BuildLandscapeNanite(AActor* Landscape)
{
#if WITH_EDITOR
	ALandscapeProxy* Proxy = Cast<ALandscapeProxy>(Landscape);
	UWorld* World = Proxy != nullptr ? Proxy->GetWorld() : nullptr;
	ULandscapeSubsystem* Subsystem = World != nullptr ? World->GetSubsystem<ULandscapeSubsystem>() : nullptr;
	if (Subsystem == nullptr || !Proxy->IsNaniteEnabled())
	{
		return false;
	}
	ALandscapeProxy* Proxies[] = { Proxy };
	Subsystem->BuildNanite(UE::Landscape::EBuildFlags::WriteFinalLog | UE::Landscape::EBuildFlags::ForceRebuild, Proxies);
	return Proxy->HasNaniteComponents();
#else
	return false;
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
