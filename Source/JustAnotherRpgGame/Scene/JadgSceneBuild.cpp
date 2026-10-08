// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Scene/JadgSceneBuild.h"

#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Volume.h"

#if WITH_EDITOR
#include "ActorFactories/ActorFactory.h"
#include "Builders/CubeBuilder.h"
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
