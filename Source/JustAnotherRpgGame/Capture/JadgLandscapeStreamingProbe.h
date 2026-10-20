// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"
#include "GameFramework/Actor.h"
#include "JadgLandscapeStreamingProbe.generated.h"

class AJadgCameraPawn;

/** Opt-in, headless acceptance route for the capital's World Partition landscape. */
UCLASS()
class AJadgLandscapeStreamingProbe : public AActor
{
	GENERATED_BODY()
public:
	AJadgLandscapeStreamingProbe();
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
private:
	struct FStop { FString Name; FVector Target; };
	TArray<FStop> Stops;
	TArray<FVector> Travel;
	TArray<TSharedPtr<FJsonValue>> Results;
	TArray<double> Frames;
	UPROPERTY() TObjectPtr<AJadgCameraPawn> View;
	FString Output;
	int32 StopIndex = -1;
	int32 StableFrames = 0;
	int32 PendingFrames = 0;
	int32 PeakLevels = 0;
	int32 GroundProbes = 0;
	int32 MissingGroundProbes = 0;
	double LastGroundProbe = 0;
	double StageStart = 0;
	double LastTick = 0;
	double ReadySeconds = -1;
	double WorstLoadFrameMs = 0;
	bool bMeasuring = false;
	bool bTravelling = false;
	bool bFinished = false;
	void NextStop();
	bool HasGround(const FVector& Target, bool bCheckHeight) const;
	void Record(const FString& Name, bool bTravel);
	void Finish(const FString& Error = FString());
};
