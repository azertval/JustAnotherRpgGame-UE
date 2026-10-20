#pragma once
#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "JadgContentMaintenance.generated.h"
/** Editor helpers for dependency-aware Content maintenance. */
UCLASS()
class UJadgContentMaintenance : public UBlueprintFunctionLibrary
{
 GENERATED_BODY()
public:
 UFUNCTION(BlueprintCallable, Category="Jadg|Content")
 static TArray<FString> HLODSourcePackages(AActor* Actor);
};
