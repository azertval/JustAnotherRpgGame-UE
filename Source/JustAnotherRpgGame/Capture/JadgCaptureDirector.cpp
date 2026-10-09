// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgCaptureDirector.h"

#include "AssetCompilingManager.h"
#include "Capture/JadgShot.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/PointLight.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "Engine/Texture.h"
#include "Materials/MaterialInterface.h"
#include "RHIStats.h"
#include "UObject/UObjectIterator.h"
#include "GameFramework/HUD.h"
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

	// La passe du contour sombre, écrite par `build_level.py` (LOT-1019) ; l'étiquette des lampes.
	const TCHAR* ContourMaterial = TEXT("/Game/Scenes/Common/M_Contour.M_Contour");
	const FName LampTag(TEXT("JadgLamp"));

	bool ShadersCompiling()
	{
		return GShaderCompilingManager != nullptr && GShaderCompilingManager->IsCompiling();
	}

	// Une texture importée par la chaîne de décor se compresse pour le jeu à son premier
	// chargement : tant qu'elle se construit, le moteur dessine une texture par défaut (LOT-1019,
	// la première capture de l'Arena of Fate texturée sortait avec un sable noir).
	bool AssetsCompiling()
	{
#if WITH_EDITOR
		return FAssetCompilingManager::Get().GetNumRemainingAssets() > 0;
#else
		return false;
#endif
	}

	double MiB(uint64 Bytes)
	{
		return static_cast<double>(Bytes) / (1024.0 * 1024.0);
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
		// Une capture se compare à sa référence : l'heure et le groupe écrits par le HUD la
		// feraient changer d'une minute à l'autre. `-JadgHud` les y laisse.
		if (AHUD* Hud = Player->GetHUD(); Hud != nullptr && !FParse::Param(CommandLine, TEXT("JadgHud")))
		{
			Hud->bShowHUD = false;
		}
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

	FString PostOptions;
	if (FParse::Value(CommandLine, TEXT("JadgPost="), PostOptions, false) && !ApplyPostOptions(PostOptions))
	{
		// L'erreur est dite ; la première trame arrête le passage.
		OutputDir.Empty();
	}
}

bool AJadgCaptureDirector::ApplyPostOptions(const FString& Options)
{
	APostProcessVolume* Volume = nullptr;
	for (TActorIterator<APostProcessVolume> It(GetWorld()); It; ++It)
	{
		if (It->bUnbound)
		{
			Volume = *It;
			break;
		}
	}
	TArray<FString> Names;
	Options.ParseIntoArray(Names, TEXT(","));
	for (const FString& Name : Names)
	{
		if (Name == TEXT("contour") || Name == TEXT("sans-contour"))
		{
			UMaterialInterface* Contour = LoadObject<UMaterialInterface>(nullptr, ContourMaterial);
			if (Volume == nullptr || Contour == nullptr)
			{
				UE_LOG(LogJadg, Error, TEXT("[Capture] %s : il faut le volume de post-traitement de la carte et %s (build_level.py)"), *Name, ContourMaterial);
				return false;
			}
			Volume->Settings.WeightedBlendables.Array.RemoveAll([Contour](const FWeightedBlendable& Blendable) { return Blendable.Object == Contour; });
			if (Name == TEXT("contour"))
			{
				Volume->Settings.WeightedBlendables.Array.Add(FWeightedBlendable(1.0f, Contour));
			}
		}
		else if (Name == TEXT("sans-ao"))
		{
			// Sous Lumen, l'occlusion d'écran est celle de sa collecte de lumière (ShortRangeAO) ;
			// l'occlusion d'écran classique est coupée aussi, au cas où Lumen serait éteint.
			GEngine->Exec(GetWorld(), TEXT("r.Lumen.ScreenProbeGather.ShortRangeAO 0"));
			GEngine->Exec(GetWorld(), TEXT("r.AmbientOcclusionLevels 0"));
		}
		else if (Name == TEXT("sans-halo"))
		{
			if (Volume == nullptr)
			{
				UE_LOG(LogJadg, Error, TEXT("[Capture] sans-halo : la carte n'a pas de volume de post-traitement"));
				return false;
			}
			Volume->Settings.bOverride_BloomIntensity = true;
			Volume->Settings.BloomIntensity = 0.0f;
		}
		else if (Name == TEXT("sans-ombres-lampes"))
		{
			for (TActorIterator<APointLight> It(GetWorld()); It; ++It)
			{
				if (It->Tags.Contains(LampTag))
				{
					It->PointLightComponent->SetCastShadows(false);
				}
			}
		}
		else
		{
			UE_LOG(LogJadg, Error, TEXT("[Capture] -JadgPost : « %s » inconnu (contour, sans-contour, sans-ao, sans-halo, sans-ombres-lampes)"), *Name);
			return false;
		}
		PostApplied.Add(Name);
	}
	return true;
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
		if (FramesInStep >= SettleFrames && !ShadersCompiling() && !AssetsCompiling())
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
	Json += FString::Printf(TEXT("  \"post\": \"%s\",\n"), *FString::Join(PostApplied, TEXT(",")));

	// La mémoire graphique à la fin du passage : celle du processus (budget du pilote), celle des
	// textures, en flux (mipmaps chargées selon la vue) ou non.
	FRHIMemoryStats Memory;
	RHIGetMemoryStats(Memory);
	FTextureMemoryStats Textures;
	RHIGetTextureMemoryStats(Textures);
	Json += FString::Printf(TEXT("  \"gpuMemoryMiB\": {\"used\": %.1f, \"texturesStreaming\": %.1f, \"texturesNonStreaming\": %.1f},\n"),
		MiB(Memory.UsedLocal), MiB(Textures.StreamingMemorySize), MiB(Textures.NonStreamingMemorySize));

	// Les maillages de la carte : chacun une fois, ses triangles Nanite, la taille de ses
	// ressources (l'estimation du moteur, `GetResourceSizeBytes`).
	TSet<UStaticMesh*> Meshes;
	for (TObjectIterator<UStaticMeshComponent> It; It; ++It)
	{
		if (It->GetWorld() == GetWorld() && It->GetStaticMesh() != nullptr)
		{
			Meshes.Add(It->GetStaticMesh());
		}
	}
	uint64 MeshBytes = 0;
	int64 Triangles = 0;
	const UStaticMesh* Largest = nullptr;
	int64 LargestTriangles = 0;
	for (UStaticMesh* Mesh : Meshes)
	{
		MeshBytes += Mesh->GetResourceSizeBytes(EResourceSizeMode::EstimatedTotal);
		const int64 Count = Mesh->GetNumNaniteTriangles() > 0 ? Mesh->GetNumNaniteTriangles() : Mesh->GetNumTriangles(0);
		Triangles += Count;
		if (Count > LargestTriangles)
		{
			LargestTriangles = Count;
			Largest = Mesh;
		}
	}
	// Les textures de ces maillages, chacune une fois : ce qu'elles tiennent en mémoire graphique à la
	// fin du passage (mipmaps chargées), et ce qu'elles tiendraient entières.
	TSet<const UTexture*> Used;
	for (const UStaticMesh* Mesh : Meshes)
	{
		for (const FStaticMaterial& Slot : Mesh->GetStaticMaterials())
		{
			if (Slot.MaterialInterface != nullptr)
			{
				TArray<UTexture*> SlotTextures;
				Slot.MaterialInterface->GetUsedTextures(SlotTextures);
				Used.Append(SlotTextures);
			}
		}
	}
	uint64 Resident = 0;
	uint64 Whole = 0;
	for (const UTexture* Texture : Used)
	{
		Resident += Texture->CalcTextureMemorySizeEnum(TMC_ResidentMips);
		Whole += Texture->CalcTextureMemorySizeEnum(TMC_AllMips);
	}
	Json += FString::Printf(TEXT("  \"meshTextures\": {\"count\": %d, \"residentMiB\": %.1f, \"allMipsMiB\": %.1f},\n"),
		Used.Num(), MiB(Resident), MiB(Whole));
	Json += FString::Printf(TEXT("  \"meshes\": {\"count\": %d, \"triangles\": %lld, \"resourceMiB\": %.1f, \"largest\": \"%s\", \"largestTriangles\": %lld},\n"),
		Meshes.Num(), Triangles, MiB(MeshBytes), Largest != nullptr ? *Largest->GetPathName() : TEXT(""), LargestTriangles);
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
