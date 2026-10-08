// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgWalkthrough.h"

#include "Characters/JadgParty.h"
#include "Characters/JadgWalker.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Game/JadgExploration.h"
#include "HAL/FileManager.h"
#include "JustAnotherRpgGame.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "ShaderCompiler.h"
#include "UnrealClient.h"

namespace
{
	const TCHAR* const Stalls = TEXT("essai/etals");
	const TCHAR* const Forecourt = TEXT("essai/parvis");
	const TCHAR* const QuestFlag = TEXT("quete.pommes");

	/// Trames laissées à la carte pour s'ouvrir : le maillage de navigation, les matières.
	constexpr int32 OpeningFrames = 90;
	/// Trames laissées à une réplique avant sa capture : le HUD l'a dessinée, l'image est posée.
	constexpr int32 LineFrames = 45;
	/// Au-delà, un ordre resté sans suite arrête le parcours, en secondes.
	constexpr double StallSeconds = 45.0;

	/// Ce qui survit au changement de carte : le parcours est un seul processus.
	TArray<FString> GSteps;
	int32 GShots = 0;
}

AJadgWalkthrough::AJadgWalkthrough()
{
	PrimaryActorTick.bCanEverTick = true;
}

void AJadgWalkthrough::BeginPlay()
{
	Super::BeginPlay();
	FParse::Value(FCommandLine::Get(), TEXT("JadgParcours="), OutputDir);
	OutputDir = FPaths::ConvertRelativePathToFull(OutputDir);
	IFileManager::Get().MakeDirectory(*OutputDir, true);
	Exploration = GetGameInstance() != nullptr ? GetGameInstance()->GetSubsystem<UJadgExploration>() : nullptr;
	StateSince = FPlatformTime::Seconds();
	if (Exploration != nullptr)
	{
		Note(FString::Printf(TEXT("carte %s"), *Exploration->MapId()));
	}
}

void AJadgWalkthrough::Note(const FString& What) const
{
	const double Now = FPlatformTime::Seconds() - GStartTime;
	// Le texte entre dans du JSON : seuls la barre oblique inverse et le guillemet y sont protégés.
	const FString Quoted = What.Replace(TEXT("\\"), TEXT("\\\\")).Replace(TEXT("\""), TEXT("\\\""));
	GSteps.Add(FString::Printf(TEXT("{\"seconds\": %.1f, \"step\": \"%s\"}"), Now, *Quoted));
	UE_LOG(LogJadg, Display, TEXT("[Parcours] %.1f s : %s"), Now, *What);
}

void AJadgWalkthrough::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	AJadgParty* Party = AJadgParty::Find(GetWorld());
	const bool bCompiling = GShaderCompilingManager != nullptr && GShaderCompilingManager->IsCompiling();
	if (bDone || ++Frames < OpeningFrames || bCompiling)
	{
		return;
	}
	if (Exploration == nullptr || Party == nullptr || Party->Leader() == nullptr)
	{
		Finish(1, TEXT("il manque l'exploration, le groupe ou son meneur"));
		return;
	}
	if (Exploration->InDialogue())
	{
		Answer();
		return;
	}
	ShotLine.Reset();
	FramesInLine = 0;
	if (Exploration->Requests().Contains(TEXT("ending:parole")))
	{
		Note(TEXT("la mère a retrouvé l'enfant : la quête est rendue"));
		Finish(0, FString());
		return;
	}

	const FString Map = Exploration->MapId();
	const FString Quest = Exploration->Flag(QuestFlag);
	const FString Now = Map + TEXT("|") + Quest;
	if (Now != Ordered)
	{
		Ordered = Now;
		StateSince = FPlatformTime::Seconds();
		Order(*Party, Map, Quest);
	}
	else if (FPlatformTime::Seconds() - StateSince > StallSeconds)
	{
		Finish(1, FString::Printf(TEXT("sans suite depuis %.0f s : carte %s, quête %s"), StallSeconds, *Map, *Quest));
	}
	else if (bApproaching && !Party->Leader()->IsWalking())
	{
		// Posté près de la mère : l'invite et le contour se capturent, puis la touche d'interaction.
		FIntPoint Cell;
		FString Prompt;
		if (!Exploration->Target(Cell, Prompt))
		{
			return;
		}
		if (!bPromptShot)
		{
			bPromptShot = true;
			PendingFile = FPaths::Combine(OutputDir, FString::Printf(TEXT("parcours-%02d.png"), ++GShots));
			IFileManager::Get().Delete(*PendingFile, false, true, true);
			FScreenshotRequest::RequestScreenshot(PendingFile, false, false);
			Note(TEXT("à portée de la mère : invite et contour"));
		}
		else if (!FScreenshotRequest::IsScreenshotRequested() && FPaths::FileExists(PendingFile))
		{
			bApproaching = false;
			Note(TEXT("touche : interagir"));
			Party->Interact();
		}
	}
}

void AJadgWalkthrough::Order(AJadgParty& Party, const FString& Map, const FString& Quest)
{
	// La mère est l'entité e1 de la carte des étals (`build_essai_maps.py`).
	const auto TalkToMother = [&]()
	{
		const AActor* Mother = Party.EntityActor(TEXT("e1"));
		if (Mother == nullptr)
		{
			Finish(1, TEXT("la mère (e1) n'est pas sur la carte"));
			return;
		}
		Note(TEXT("ordre : aller parler à la mère"));
		Party.OrderInteract(Mother);
	};
	const auto WalkTo = [&](double Column, double Row, const TCHAR* Where)
	{
		Note(FString::Printf(TEXT("ordre : marcher vers %s"), Where));
		Party.OrderWalk(Party.PointOf(FVector2D(Column, Row)));
	};

	if (Map == Stalls && Quest == TEXT("inconnue"))
	{
		// La mère est en (3, 2) : le meneur se poste à l'est, sur la case voisine.
		WalkTo(4.5, 2.5, TEXT("le côté de la mère"));
		bApproaching = true;
	}
	else if (Map == Stalls && Quest == TEXT("acceptee"))
	{
		WalkTo(15.5, 5.5, TEXT("le portail de l'est"));
	}
	else if (Map == Forecourt && Quest == TEXT("acceptee"))
	{
		// La graine du jet de Persuasion se fixe avant que le garde ne parle.
		uint64 Seed = 0;
		if (FParse::Value(FCommandLine::Get(), TEXT("JadgSeed="), Seed))
		{
			Exploration->SetSeed(Seed);
		}
		WalkTo(6.5, 4.5, TEXT("la zone du parvis"));
	}
	else if (Map == Forecourt && Quest == TEXT("enfant-libere"))
	{
		WalkTo(0.5, 5.5, TEXT("le portail de l'ouest"));
	}
	else if (Map == Stalls && Quest == TEXT("enfant-libere"))
	{
		TalkToMother();
	}
	else
	{
		Finish(1, FString::Printf(TEXT("le parcours n'a pas de suite ici : carte %s, quête %s"), *Map, *Quest));
	}
}

void AJadgWalkthrough::Answer()
{
	// Chaque réplique est capturée, HUD compris, avant sa réponse.
	const FString Line = Exploration->Line();
	if (Line != ShotLine)
	{
		if (++FramesInLine < LineFrames)
		{
			return;
		}
		ShotLine = Line;
		PendingFile = FPaths::Combine(OutputDir, FString::Printf(TEXT("parcours-%02d.png"), ++GShots));
		IFileManager::Get().Delete(*PendingFile, false, true, true);
		FScreenshotRequest::RequestScreenshot(PendingFile, false, false);
		Note(FString::Printf(TEXT("%s : « %s »"), *Exploration->Speaker(), *Line));
		if (!Exploration->LastCheck().IsEmpty())
		{
			Note(Exploration->LastCheck());
		}
		return;
	}
	if (FScreenshotRequest::IsScreenshotRequested() || !FPaths::FileExists(PendingFile))
	{
		if (++FramesInLine > LineFrames + 600)
		{
			Finish(1, FString::Printf(TEXT("%s n'a pas été écrit"), *PendingFile));
		}
		return;
	}
	FramesInLine = 0;

	const TArray<FJadgChoice> Offered = Exploration->Choices();
	for (const TCHAR* Wanted : {TEXT("accepter"), TEXT("convaincre"), TEXT("sourire"), TEXT("continue")})
	{
		if (Offered.ContainsByPredicate([Wanted](const FJadgChoice& Choice) { return Choice.Id == Wanted; }))
		{
			Note(FString::Printf(TEXT("réponse : %s"), Wanted));
			Exploration->ChooseById(Wanted);
			return;
		}
	}
	Finish(1, FString::Printf(TEXT("aucune réponse du parcours à « %s » (quête %s)"), *Line, *Exploration->Flag(QuestFlag)));
}

void AJadgWalkthrough::Finish(int32 ExitCode, const FString& Reason)
{
	bDone = true;
	if (ExitCode != 0)
	{
		UE_LOG(LogJadg, Error, TEXT("[Parcours] %s"), *Reason);
	}
	FString Json = FString::Printf(TEXT("{\n  \"completed\": %s,\n  \"captures\": %d,\n  \"steps\": [\n    "),
		ExitCode == 0 ? TEXT("true") : TEXT("false"), GShots);
	Json += FString::Join(GSteps, TEXT(",\n    "));
	Json += TEXT("\n  ]\n}\n");
	const FString File = FPaths::Combine(OutputDir, TEXT("parcours.json"));
	FFileHelper::SaveStringToFile(Json, *File, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	UE_LOG(LogJadg, Display, TEXT("[Parcours] %s"), *File);
	FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(ExitCode));
}
