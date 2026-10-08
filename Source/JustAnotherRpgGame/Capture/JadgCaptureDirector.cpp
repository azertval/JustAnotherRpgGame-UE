// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgCaptureDirector.h"

#include "Capture/JadgShot.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerController.h"
#include "HAL/FileManager.h"
#include "JustAnotherRpgGame.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Player/JadgCameraPawn.h"
#include "RHI.h"
#include "RenderTimer.h"
#include "ShaderCompiler.h"
#include "UnrealClient.h"
#include "World/JadgDayLight.h"

namespace
{
	// La caméra de la mesure fait un tour en dix secondes : « caméra en mouvement » (LOT-1012).
	constexpr float MeasureDegreesPerSecond = 36.0f;
	// Trames laissées de côté au début d'une mesure, le temps que le changement d'heure se pose.
	constexpr int32 MeasureWarmupFrames = 60;

	bool ShadersCompiling()
	{
		return GShaderCompilingManager != nullptr && GShaderCompilingManager->IsCompiling();
	}

	FString HourSlug(const FString& Hour)
	{
		return Hour.Replace(TEXT(":"), TEXT(""));
	}
}

AJadgCaptureDirector::AJadgCaptureDirector()
{
	PrimaryActorTick.bCanEverTick = true;
}

void AJadgCaptureDirector::BeginPlay()
{
	Super::BeginPlay();

	const TCHAR* CommandLine = FCommandLine::Get();
	FParse::Value(CommandLine, TEXT("JadgCapture="), OutputDir);
	OutputDir = FPaths::ConvertRelativePathToFull(OutputDir);
	FString HourList = TEXT("12:00,22:00");
	FParse::Value(CommandLine, TEXT("JadgHours="), HourList, false);
	HourList.ParseIntoArray(Hours, TEXT(","));
	FParse::Value(CommandLine, TEXT("JadgSettle="), SettleFrames);
	FParse::Value(CommandLine, TEXT("JadgMeasure="), MeasureSeconds);

	if (const APlayerController* Player = GetWorld()->GetFirstPlayerController())
	{
		View = Cast<AJadgCameraPawn>(Player->GetPawn());
	}
	for (TActorIterator<AJadgDayLight> It(GetWorld()); It; ++It)
	{
		DayLight = *It;
		break;
	}
	for (TActorIterator<AJadgShot> It(GetWorld()); It; ++It)
	{
		Shots.Add(*It);
	}
	// L'ordre des acteurs d'une carte n'est pas celui de la description : leur rang l'est.
	Shots.Sort([](const AJadgShot& A, const AJadgShot& B) { return A.Order < B.Order; });

	// La cadence se mesure sans plafond.
	GEngine->Exec(GetWorld(), TEXT("t.MaxFPS 0"));
	GEngine->Exec(GetWorld(), TEXT("r.VSync 0"));
}

void AJadgCaptureDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	++FramesInStep;
	SecondsInStep += DeltaSeconds;

	switch (Phase)
	{
	case EPhase::Opening:
		OpenSeconds = FPlatformTime::Seconds() - GStartTime;
		UE_LOG(LogJadg, Display, TEXT("[Capture] première trame de la carte %.2f s après le lancement"), OpenSeconds);
		if (View == nullptr || DayLight == nullptr || Shots.IsEmpty() || Hours.IsEmpty() || OutputDir.IsEmpty())
		{
			Finish(1, TEXT("il manque la caméra du joueur, l'acteur du jour, un cadrage, une heure ou le dossier de sortie"));
			return;
		}
		IFileManager::Get().MakeDirectory(*OutputDir, true);
		BeginShot();
		break;

	case EPhase::Settling:
		if (FramesInStep >= SettleFrames && !ShadersCompiling())
		{
			FScreenshotRequest::RequestScreenshot(PendingFile, false, false);
			Phase = EPhase::Writing;
			FramesInStep = 0;
		}
		break;

	case EPhase::Writing:
		if (!FScreenshotRequest::IsScreenshotRequested() && FPaths::FileExists(PendingFile))
		{
			UE_LOG(LogJadg, Display, TEXT("[Capture] %s"), *PendingFile);
			Written.Add(FPaths::GetCleanFilename(PendingFile));
			if (++ShotIndex >= Shots.Num())
			{
				ShotIndex = 0;
				++HourIndex;
			}
			if (HourIndex < Hours.Num())
			{
				BeginShot();
			}
			else if (MeasureSeconds > 0.0f)
			{
				HourIndex = 0;
				BeginMeasure();
			}
			else
			{
				Finish(0);
			}
		}
		else if (FramesInStep > 600)
		{
			Finish(1, FString::Printf(TEXT("%s n'a pas été écrit"), *PendingFile));
		}
		break;

	case EPhase::Measuring:
		Frame(*Shots[0], SecondsInStep * MeasureDegreesPerSecond);
		if (FramesInStep > MeasureWarmupFrames)
		{
			FSample Sample;
			Sample.Frame = DeltaSeconds * 1000.0f;
			Sample.Game = FPlatformTime::ToMilliseconds(GGameThreadTime);
			Sample.Render = FPlatformTime::ToMilliseconds(GRenderThreadTime);
			Sample.Gpu = FPlatformTime::ToMilliseconds(RHIGetGPUFrameCycles());
			Measures.Last().Samples.Add(Sample);
		}
		if (SecondsInStep >= MeasureSeconds + 2.0f)
		{
			if (++HourIndex < Hours.Num())
			{
				BeginMeasure();
			}
			else
			{
				Finish(0);
			}
		}
		break;

	case EPhase::Done:
		break;
	}
}

void AJadgCaptureDirector::Frame(const AJadgShot& Shot, float ExtraYaw)
{
	const FRotator Look = Shot.GetActorRotation();
	View->SetView(Shot.GetActorLocation(), Look.Yaw + ExtraYaw, -Look.Pitch, Shot.Distance);
}

bool AJadgCaptureDirector::SetHour(const FString& Hour)
{
	float Minutes = 0.0f;
	if (!AJadgDayLight::ParseTime(Hour, Minutes))
	{
		Finish(1, FString::Printf(TEXT("« %s » n'est pas une heure (HH:MM)"), *Hour));
		return false;
	}
	DayLight->SetMinutes(Minutes);
	return true;
}

void AJadgCaptureDirector::BeginShot()
{
	if (!SetHour(Hours[HourIndex]))
	{
		return;
	}
	const AJadgShot& Shot = *Shots[ShotIndex];
	Frame(Shot);
	PendingFile = FPaths::Combine(OutputDir, FString::Printf(TEXT("%s-%s.png"), *Shot.ShotId, *HourSlug(Hours[HourIndex])));
	IFileManager::Get().Delete(*PendingFile, false, true, true);
	Phase = EPhase::Settling;
	FramesInStep = 0;
}

void AJadgCaptureDirector::BeginMeasure()
{
	if (!SetHour(Hours[HourIndex]))
	{
		return;
	}
	FMeasure& Measure = Measures.AddDefaulted_GetRef();
	Measure.Hour = Hours[HourIndex];
	Phase = EPhase::Measuring;
	FramesInStep = 0;
	SecondsInStep = 0.0f;
}

void AJadgCaptureDirector::Finish(int32 ExitCode, const FString& Reason)
{
	Phase = EPhase::Done;
	if (ExitCode != 0)
	{
		UE_LOG(LogJadg, Error, TEXT("[Capture] %s"), *Reason);
	}
	else
	{
		WriteReport();
	}
	FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(ExitCode));
}

void AJadgCaptureDirector::WriteReport() const
{
	FVector2D Size = FVector2D::ZeroVector;
	if (GEngine->GameViewport != nullptr)
	{
		GEngine->GameViewport->GetViewportSize(Size);
	}

	FString Json = TEXT("{\n");
	Json += FString::Printf(TEXT("  \"map\": \"%s\",\n"), *GetWorld()->GetMapName());
	Json += FString::Printf(TEXT("  \"resolution\": [%d, %d],\n"), FMath::RoundToInt32(Size.X), FMath::RoundToInt32(Size.Y));
	Json += FString::Printf(TEXT("  \"gpu\": \"%s\",\n"), *GRHIAdapterName.ReplaceCharWithEscapedChar());
	Json += FString::Printf(TEXT("  \"openSeconds\": %.2f,\n"), OpenSeconds);
	Json += TEXT("  \"captures\": [");
	for (int32 Index = 0; Index < Written.Num(); ++Index)
	{
		Json += FString::Printf(TEXT("%s\"%s\""), Index > 0 ? TEXT(", ") : TEXT(""), *Written[Index]);
	}
	Json += TEXT("],\n  \"measures\": [");
	for (int32 Index = 0; Index < Measures.Num(); ++Index)
	{
		const FMeasure& Measure = Measures[Index];
		TArray<float> Frames;
		FSample Sum;
		for (const FSample& Sample : Measure.Samples)
		{
			Frames.Add(Sample.Frame);
			Sum.Frame += Sample.Frame;
			Sum.Game += Sample.Game;
			Sum.Render += Sample.Render;
			Sum.Gpu += Sample.Gpu;
		}
		Frames.Sort();
		const int32 Count = FMath::Max(Frames.Num(), 1);
		const float Mean = Sum.Frame / Count;
		const float Worst = Frames.IsEmpty() ? 0.0f : Frames.Last();
		// Le 1 % le plus lent : la trame au 99e centile.
		const float Slow = Frames.IsEmpty() ? 0.0f : Frames[FMath::Min(Frames.Num() - 1, FMath::FloorToInt32(Frames.Num() * 0.99f))];
		Json += FString::Printf(
			TEXT("%s\n    {\"hour\": \"%s\", \"seconds\": %.1f, \"frames\": %d, \"fps\": %.1f, \"frameMs\": %.2f, \"p99FrameMs\": %.2f, \"worstFrameMs\": %.2f, \"gameMs\": %.2f, \"renderMs\": %.2f, \"gpuMs\": %.2f}"),
			Index > 0 ? TEXT(",") : TEXT(""), *Measure.Hour, Sum.Frame / 1000.0f, Frames.Num(),
			Mean > 0.0f ? 1000.0f / Mean : 0.0f, Mean, Slow, Worst, Sum.Game / Count, Sum.Render / Count, Sum.Gpu / Count);
	}
	Json += Measures.IsEmpty() ? TEXT("]\n}\n") : TEXT("\n  ]\n}\n");

	const FString File = FPaths::Combine(OutputDir, TEXT("mesure.json"));
	FFileHelper::SaveStringToFile(Json, *File, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	UE_LOG(LogJadg, Display, TEXT("[Capture] %s"), *File);
}
