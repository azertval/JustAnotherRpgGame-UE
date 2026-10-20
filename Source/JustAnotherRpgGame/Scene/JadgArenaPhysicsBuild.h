#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "JadgArenaPhysicsBuild.generated.h"
class USkeletalMesh;
class UStaticMesh;
class UPhysicsAsset;
/** Reproducible editor construction of cloth and articulated prop physics. */
UCLASS()
class UJadgArenaPhysicsBuild : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable, Category="Jadg|Arena")
 static bool BuildRigidCollision(UStaticMesh* Mesh);
 UFUNCTION(BlueprintCallable, Category="Jadg|Arena")
 static UPhysicsAsset* BuildBodies(USkeletalMesh* Mesh, const FString& PackagePath, bool bAnchorRoot, const FString& JointMode, FVector JointAxis);
 UFUNCTION(BlueprintCallable, Category="Jadg|Arena")
 static FString BuildCloth(USkeletalMesh* Mesh, float MaxDistanceCm, bool bPinTop);
};
