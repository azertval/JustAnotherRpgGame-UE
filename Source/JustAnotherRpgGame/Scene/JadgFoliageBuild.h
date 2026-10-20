// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#pragma once

#include "Kismet/BlueprintFunctionLibrary.h"
#include "JadgFoliageBuild.generated.h"

/** Editor-only planting bridge; every instance retains its real Landscape base. */
UCLASS()
class UJadgFoliageBuild : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()
public:
	/** Returns planted count, or -1 for invalid inputs/out-of-bounds placement. */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static int32 PlantOnLandscape(AActor* Surface, UObject* FoliageTypeAsset, const TArray<FTransform>& Transforms);

	/** Project candidate roots onto their native Landscape collision; -1 on missing bases.
	 * In inspection mode, returns the number of roots more than 2 cm from the ground. */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static int32 GroundFoliageRoots(AActor* FoliageActor, const TArray<FVector>& Candidates, bool bApply, int32& OutChecked);
};
