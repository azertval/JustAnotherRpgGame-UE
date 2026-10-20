// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "JadgWitnessReview.generated.h"

class AJadgParty;
class FJsonValue;
class ULevel;
class UStaticMeshComponent;

/** Local review actor, placed only in regenerated Arena maps. No global camera/gameplay changes.
 * Tagged static components stop blocking the camera probe, and are hidden only when
 * their real collision geometry intersects the camera-to-target segment. Actors
 * tagged JadgWitnessSupport:<id> follow cut JadgWitnessSurface:<id> components.
 * These dependents need no occluder tag or camera ray intersection. Physics,
 * hidden shadows and indirect lighting remain. This first proof uses a hard cut.
 * -JadgWitnessWalk=<file.json> additionally walks RoutePoints on the real navigation
 * mesh, then retraces the route. Points are ground positions in world centimetres.
 */
UCLASS()
class AJadgWitnessReview : public AActor
{
	GENERATED_BODY()

public:
	AJadgWitnessReview();

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	TArray<FVector> RoutePoints;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	bool bWalkReturn = true;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	float PointTolerance = 60.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	float HeightTolerance = 25.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	float LegTimeout = 90.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	float StartupTimeout = 120.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	float SampleInterval = 0.25f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	bool bEnableCutaway = true;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	bool bIgnoreCameraCollision = true;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	bool bKeepHiddenShadows = true;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	bool bKeepHiddenIndirectLighting = true;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness")
	FName OccluderTag = TEXT("JadgWitnessOccluder");

	// Opt-in per map actor: Recast's config-backed values can reset on loading.
	// Applied after this world's streaming levels arrive; no SaveConfig or CDO edit.
	UPROPERTY(EditAnywhere, Category = "Jadg|Witness|Navigation")
	bool bFineNavigation = false;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness|Navigation", meta = (ClampMin = "1.0"))
	float NavigationCellSize = 5.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness|Navigation", meta = (ClampMin = "1.0"))
	float NavigationCellHeight = 2.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness|Navigation", meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float NavigationElevationRatio = 1.0f;

	// Sentinels preserve the current map values until an explicit profile is set.
	UPROPERTY(EditAnywhere, Category = "Jadg|Witness|Navigation", meta = (ClampMin = "0.0"))
	float NavigationTileSize = 0.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness|Navigation", meta = (ClampMin = "0.0"))
	float NavigationAverageLayers = 0.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness|Navigation", meta = (ClampMin = "-1.0"))
	float NavigationMaxSimplificationError = -1.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg|Witness|Navigation", meta = (ClampMin = "0"))
	int32 NavigationMaxSearchNodes = 0;

	UFUNCTION(BlueprintCallable, Category = "Jadg|Witness|Navigation")
	bool PrepareFineNavigation();

	// Includes native fields which Unreal's Python API does not expose.
	UFUNCTION(BlueprintCallable, Category = "Jadg|Witness|Navigation")
	FString GetNavigationSettingsJson() const;

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

	// Incremental refresh: keep initial snapshots for already registered components.
	// Also callable by the automation test, without constructing a player camera.
	// With a level, only that level's actors are scanned (a streamed World Partition cell).
	void GatherOccluders(ULevel* Only = nullptr);
	void UpdateCutaway(const FVector& Camera, const FVector& Target);
	void RestoreOccluders();

private:
	friend class FJadgWitnessCutawayTest;

	struct FOccluder
	{
		TWeakObjectPtr<UStaticMeshComponent> Component;
		ECollisionResponse CameraResponse = ECR_Block;
		ECollisionResponse VisibilityResponse = ECR_Block;
		bool bHidden = false;
		bool bHiddenShadow = false;
		bool bHiddenIndirect = false;
		bool bCut = false;
		bool bDirect = false;
		TArray<FName> SurfaceIds;
		TArray<FName> SupportIds;
	};
	TArray<FOccluder> Occluders;
	FDelegateHandle LevelAddedHandle;
	FDelegateHandle LevelRemovingHandle;
	TArray<FVector> WalkPoints;
	TArray<TSharedPtr<FJsonValue>> Samples;
	TArray<TSharedPtr<FJsonValue>> Reached;
	FString ReportFile;
	FVector PreviousFeet = FVector::ZeroVector;
	double Started = 0.0;
	double LegStarted = 0.0;
	double LastSample = 0.0;
	double LastOrder = 0.0;
	int32 PointIndex = 0;
	int32 Orders = 0;
	int32 CutEvents = 0;
	bool bWalking = false;
	bool bDone = false;
	bool bNavigationRefreshPending = true;
	int32 FineNavigationBuilds = 0;

	void OnLevelAdded(ULevel* Level, UWorld* World);
	void OnLevelRemoving(ULevel* Level, UWorld* World);
	void RestoreOccluder(FOccluder& Saved);
	bool NavigationWaitTimedOut(double Now) const;
	void StartWalk(AJadgParty& Party);
	void TickWalk(AJadgParty& Party, float DeltaSeconds);
	void Sample(const AJadgParty& Party, bool bReached);
	void Finish(int32 ExitCode, const FString& Reason);
};
