// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#include "Capture/JadgLandscapeStreamingProbe.h"

#include "Player/JadgCameraPawn.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/PlatformMemory.h"
#include "HAL/PlatformMisc.h"
#include "HAL/PlatformTime.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "WorldPartition/WorldPartition.h"
#include "WorldPartition/WorldPartitionSubsystem.h"

AJadgLandscapeStreamingProbe::AJadgLandscapeStreamingProbe()
{
	PrimaryActorTick.bCanEverTick = true;
}

void AJadgLandscapeStreamingProbe::BeginPlay()
{
	Super::BeginPlay();
	FString Route, Text;
	FParse::Value(FCommandLine::Get(), TEXT("JadgLandscapeStreaming="), Route);
	Output = FPaths::Combine(FPaths::GetPath(Route), TEXT("streaming-performance.json"));
	TSharedPtr<FJsonObject> Json;
	if (!FFileHelper::LoadFileToString(Text, *Route) || !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Text), Json) || !Json)
	{
		Finish(TEXT("Cannot read streaming route"));
		return;
	}
	if (!GetWorld()->GetWorldPartition() || !GetWorld()->GetWorldPartition()->IsStreamingEnabled())
	{
		Finish(TEXT("World Partition streaming is not enabled"));
		return;
	}
	auto Point = [](const TArray<TSharedPtr<FJsonValue>>& Values) {
		return FVector(Values[0]->AsNumber(), Values[1]->AsNumber(), Values[2]->AsNumber()) * 100.;
	};
	for (const auto& Value : Json->GetArrayField(TEXT("stops")))
	{
		const auto Row = Value->AsObject();
		Stops.Add({Row->GetStringField(TEXT("name")), Point(Row->GetArrayField(TEXT("target")))});
	}
	for (const auto& Value : Json->GetArrayField(TEXT("travel"))) Travel.Add(Point(Value->AsArray()));
	if (Stops.IsEmpty() || Travel.Num() < 2) Finish(TEXT("Incomplete streaming route"));
	LastTick = FPlatformTime::Seconds();
}

void AJadgLandscapeStreamingProbe::NextStop()
{
	++StopIndex;
	Frames.Reset();
	StableFrames = PendingFrames = PeakLevels = 0;
	GroundProbes = MissingGroundProbes = 0;
	LastGroundProbe = 0;
	ReadySeconds = -1;
	WorstLoadFrameMs = 0;
	bMeasuring = false;
	StageStart = FPlatformTime::Seconds();
	if (StopIndex >= Stops.Num())
	{
		bTravelling = true;
		View->SetView(Travel[0], 35, 35, 8000);
	}
	else View->SetView(Stops[StopIndex].Target, 35, 35, 8000);
}

bool AJadgLandscapeStreamingProbe::HasGround(const FVector& Target, bool bCheckHeight) const
{
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CapitalStreamingGround), true);
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
		if (It->GetClass()->GetName() == TEXT("InstancedFoliageActor")) Params.AddIgnoredActor(*It);
	FHitResult Hit;
	if (!GetWorld()->LineTraceSingleByChannel(Hit, Target + FVector(0,0,30000), Target - FVector(0,0,10000), ECC_Visibility, Params)
		|| !Hit.GetActor()) return false;
	const FString Kind = Hit.GetActor()->GetClass()->GetName();
	return (Kind == TEXT("LandscapeStreamingProxy") || Kind == TEXT("Landscape"))
		&& (!bCheckHeight || FMath::Abs(Hit.ImpactPoint.Z - (Target.Z-100.)) < 20.);
}

void AJadgLandscapeStreamingProbe::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (bFinished) return;
	const double Now = FPlatformTime::Seconds();
	const double Milliseconds = (Now - LastTick) * 1000.;
	LastTick = Now;
	if (!View)
	{
		const APlayerController* Controller = GetWorld()->GetFirstPlayerController();
		View = Controller ? Cast<AJadgCameraPawn>(Controller->GetPawn()) : nullptr;
		if (View) NextStop();
		return;
	}
	const bool Complete = GetWorld()->GetSubsystem<UWorldPartitionSubsystem>()->IsAllStreamingCompleted();
	PeakLevels = FMath::Max(PeakLevels, GetWorld()->GetLevels().Num());
	const double Elapsed = Now - StageStart;
	if (Elapsed > 120.) { Finish(TEXT("Streaming timeout")); return; }
	if (!bMeasuring)
	{
		WorstLoadFrameMs = FMath::Max(WorstLoadFrameMs, Milliseconds);
		const FVector Target = bTravelling ? Travel[0] : Stops[StopIndex].Target;
		const bool Ground = HasGround(Target, true);
		if (Complete && Ground && Elapsed > 0.5)
		{
			if (ReadySeconds < 0) ReadySeconds = Elapsed;
			if (++StableFrames >= 30 && Elapsed > 1.)
			{
				bMeasuring = true;
				StageStart = Now;
			}
		}
		else StableFrames = 0;
		return;
	}
	Frames.Add(Milliseconds);
	if (!Complete) ++PendingFrames;
	if (bTravelling)
	{
		// Authored points are 40 m apart; 16 m/s crosses several streaming cells.
		const double Segment = Elapsed * 16. / 40.;
		const int32 Index = FMath::FloorToInt(Segment);
		if (Index >= Travel.Num()-1)
		{
			Record(TEXT("continuous-travel"), true);
			Finish(MissingGroundProbes ? TEXT("Ground missing during continuous travel") : FString());
			return;
		}
		View->SetView(FMath::Lerp(Travel[Index], Travel[Index+1], Segment-Index), 35, 35, 8000);
		if (Now - LastGroundProbe >= 0.2)
		{
			LastGroundProbe = Now;
			++GroundProbes;
			if (!HasGround(View->GetActorLocation(), false)) ++MissingGroundProbes;
		}
	}
	else if (Elapsed >= 3.)
	{
		Record(Stops[StopIndex].Name, false);
		NextStop();
	}
}

void AJadgLandscapeStreamingProbe::Record(const FString& Name, bool bTravel)
{
	const auto Row = MakeShared<FJsonObject>();
	Row->SetStringField(TEXT("name"), Name);
	Row->SetBoolField(TEXT("continuous"), bTravel);
	Row->SetNumberField(TEXT("readySeconds"), ReadySeconds);
	Row->SetNumberField(TEXT("worstLoadFrameMs"), WorstLoadFrameMs);
	double Sum = 0;
	for (double Value : Frames) Sum += Value;
	Frames.Sort();
	Row->SetNumberField(TEXT("frames"), Frames.Num());
	Row->SetNumberField(TEXT("fps"), Frames.Num() * 1000. / FMath::Max(Sum, 0.001));
	Row->SetNumberField(TEXT("p99FrameMs"), Frames[FMath::Min(Frames.Num()-1, FMath::FloorToInt(Frames.Num()*.99))]);
	Row->SetNumberField(TEXT("worstFrameMs"), Frames.Last());
	Row->SetNumberField(TEXT("framesWithPendingStreaming"), PendingFrames);
	Row->SetNumberField(TEXT("peakLoadedLevels"), PeakLevels);
	Row->SetNumberField(TEXT("groundProbes"), GroundProbes);
	Row->SetNumberField(TEXT("missingGroundProbes"), MissingGroundProbes);
	Row->SetNumberField(TEXT("processMemoryMiB"), FPlatformMemory::GetStats().UsedPhysical/1048576.);
	int32 LandscapeProxies = 0, FoliageActors = 0;
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		const FString Class = It->GetClass()->GetName();
		LandscapeProxies += Class == TEXT("LandscapeStreamingProxy");
		FoliageActors += Class == TEXT("InstancedFoliageActor");
	}
	Row->SetNumberField(TEXT("loadedLandscapeProxies"), LandscapeProxies);
	Row->SetNumberField(TEXT("loadedFoliageActors"), FoliageActors);
	Results.Add(MakeShared<FJsonValueObject>(Row));
	UE_LOG(LogTemp, Display, TEXT("[CapitalStreaming] %s: %.1f fps, ready %.2f s, %d proxies"), *Name, Frames.Num()*1000./Sum, ReadySeconds, LandscapeProxies);
}

void AJadgLandscapeStreamingProbe::Finish(const FString& Error)
{
	bFinished = true;
	const auto Root = MakeShared<FJsonObject>();
	Root->SetStringField(TEXT("world"), GetWorld()->GetMapName());
	Root->SetStringField(TEXT("error"), Error);
	Root->SetBoolField(TEXT("worldPartition"), GetWorld()->GetWorldPartition() != nullptr);
	Root->SetArrayField(TEXT("measurements"), Results);
	FString Text;
	FJsonSerializer::Serialize(Root, TJsonWriterFactory<>::Create(&Text));
	const bool Saved = FFileHelper::SaveStringToFile(Text, *Output);
	UE_LOG(LogTemp, Display, TEXT("[CapitalStreaming] %s"), *Output);
	FPlatformMisc::RequestExitWithStatus(false, Error.IsEmpty() && Saved ? 0 : 1);
}
