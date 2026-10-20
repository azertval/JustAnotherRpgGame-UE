#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Animation/SkeletalMeshActor.h"
#include "JadgArenaPhysicsWitness.generated.h"
/** Lightweight sandbox evidence; no gameplay dependency or Blueprint logic. */
UCLASS()
class AJadgArenaPhysicsWitness : public AActor
{
 GENERATED_BODY()
public:
 AJadgArenaPhysicsWitness();
 virtual void Tick(float DeltaSeconds) override;
private:
 float Elapsed=0;
 TMap<FString,TArray<FVector>> Initial;
 TMap<FString,double> MaximumMovement;
};

/** Reusable arena prop: enables physical pose blending and cloth on play. */
UCLASS()
class AJadgArenaSimulatedAsset : public ASkeletalMeshActor
{
 GENERATED_BODY()
public:
 UPROPERTY(EditAnywhere,Category="Arena") bool SimulateArticulation=false;
 virtual void BeginPlay() override;
};
