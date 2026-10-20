// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "JadgDistrictLife.generated.h"

class AJadgWalker;
class UPointLightComponent;

/** Opt-in district population. Authored routes are metres converted by the map builder
 * into world centimetres. Residents use the existing Mutable appearance/animation
 * pipeline, and complete navigation paths, never teleports or decorative static meshes.
 * No resident is registered as a quest or combat entity. */
UCLASS()
class AJadgDistrictLife : public AActor
{
	GENERATED_BODY()

public:
	AJadgDistrictLife();

	UPROPERTY(EditAnywhere, Category = "Jadg|District")
	TArray<FVector> CrowdPoints;

	UPROPERTY(EditAnywhere, Category = "Jadg|District")
	TArray<int32> CrowdRouteLengths;

	UPROPERTY(EditAnywhere, Category = "Jadg|District")
	TArray<FString> CrowdAppearances;

	UPROPERTY(EditAnywhere, Category = "Jadg|District", meta = (ClampMin = "0", ClampMax = "32"))
	int32 CrowdCount = 12;

	UPROPERTY(EditAnywhere, Category = "Jadg|District")
	float ResidentWalkSpeed = 150.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|District")
	float NavigationStartupTimeout = 120.0f;

	UFUNCTION(BlueprintCallable, Category = "Jadg|District")
	FString GetLifeReportJson() const;

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	struct FResident
	{
		TWeakObjectPtr<AJadgWalker> Walker;
		TArray<FVector> Route;
		FVector PreviousFeet = FVector::ZeroVector;
		int32 Destination = 0;
		double WaitUntil = 0.0;
		double OrderedAt = 0.0;
		double TravelledCm = 0.0;
		int32 Reached = 0;
		int32 RejectedPaths = 0;
		int32 RequestedIndex = 0;
		bool bOrdered = false;
	};
	struct FFlameLight
	{
		TWeakObjectPtr<UPointLightComponent> Component;
		float BaseIntensity = 0.0f;
		float Phase = 0.0f;
	};
	TArray<FResident> Residents;
	TArray<FFlameLight> FlameLights;
	double StartedAt = 0.0;
	bool bPopulationReady = false;
	int32 RejectedRoutes = 0;
	int32 AppearanceFailures = 0;
	int32 SpawnFailures = 0;
	int32 SpawnCandidateRejections = 0;
	bool TryPopulate();
	void UpdateResident(FResident& Resident, double Now);
};
