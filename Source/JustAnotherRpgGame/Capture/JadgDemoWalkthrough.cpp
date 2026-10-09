// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgDemoWalkthrough.h"

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
#include "UObject/Package.h"
#include "UnrealClient.h"

namespace
{
	const TCHAR* const Martpart = TEXT("central-empire/capital/martpart");
	const TCHAR* const Arenarea = TEXT("central-empire/capital/arenarea");
	const TCHAR* const ArenaOfFate = TEXT("central-empire/capital/arenarea/arena-of-fate");

	/// Une étape : sur quelle carte, vers quelle case (son centre) de quel étage, et la carte qu'elle
	/// ouvre (un portail) ou rien (un escalier : l'étape finit quand le meneur est arrivé).
	struct FLeg
	{
		const TCHAR* Map;
		double Column;
		double Row;
		int32 Storey;
		const TCHAR* Opens;
		const TCHAR* What;
	};

	// Les cases des portails et des points d'arrivée sont celles des descriptions de carte : Martpart
	// (e4), Arenarea (e4, e2), l'Arena of Fate (le sable, le pied de l'escalier des catacombes, e23).
	const FLeg Legs[] = {
		{Martpart, 8.5, 0.5, 0, Arenarea, TEXT("Martpart : le portail de Stravian Avenue, vers Arenarea")},
		{Arenarea, 65.5, 33.5, 0, ArenaOfFate, TEXT("Arenarea : l'escalier de l'arène, vers l'Arena of Fate")},
		{ArenaOfFate, 9.5, 12.5, 0, nullptr, TEXT("l'Arena of Fate : du vestibule au sable, par l'escalier de la porte du triomphe")},
		{ArenaOfFate, 22.5, 8.5, 2, nullptr, TEXT("l'Arena of Fate : du sable aux catacombes, par la prison et son puits")},
		{ArenaOfFate, 16.5, 21.5, 1, Arenarea, TEXT("l'Arena of Fate : des catacombes à l'escalier du parvis, vers Arenarea")},
		{Arenarea, 116.5, 86.5, 0, Martpart, TEXT("Arenarea : le portail de Herofate Avenue, retour à Martpart")},
	};
	constexpr int32 LegCount = UE_ARRAY_COUNT(Legs);

	/// Trames laissées à la carte pour s'ouvrir : le maillage de navigation, les matières.
	constexpr int32 OpeningFrames = 120;
	/// Une étape sans suite au-delà de cette durée arrête le parcours, en secondes.
	constexpr double LegSeconds = 240.0;
	/// Un meneur arrêté avant son but reçoit l'ordre de nouveau, autant de fois au plus.
	constexpr int32 MaxOrders = 6;
	/// Trames laissées à un ordre avant de juger que le meneur s'est arrêté.
	constexpr int32 OrderFrames = 60;
	/// Le meneur est arrivé à moins de cette distance de la case visée, en cases.
	constexpr double ArrivedCells = 1.5;

	/// Ce qui survit au changement de carte : le parcours est un seul processus.
	TArray<FString> GSteps;
	int32 GShots = 0;
	int32 GLeg = 0;
	double GLegSince = 0.0;
	int32 GLastOrderFrame = 0;
	/// La dernière trame de la carte quittée : l'ouverture d'une carte se mesure d'elle à la
	/// première trame de la suivante (le portail franchi, la carte chargée, le monde lancé).
	double GLastFrame = 0.0;
	FString GLastWorld;
	TArray<FString> GOpenings;
}

AJadgDemoWalkthrough::AJadgDemoWalkthrough()
{
	PrimaryActorTick.bCanEverTick = true;
}

void AJadgDemoWalkthrough::BeginPlay()
{
	Super::BeginPlay();
	FParse::Value(FCommandLine::Get(), TEXT("JadgParcoursDemo="), OutputDir);
	OutputDir = FPaths::ConvertRelativePathToFull(OutputDir);
	IFileManager::Get().MakeDirectory(*OutputDir, true);
	Exploration = GetGameInstance() != nullptr ? GetGameInstance()->GetSubsystem<UJadgExploration>() : nullptr;
	if (GLegSince == 0.0)
	{
		GLegSince = FPlatformTime::Seconds();
	}
	Note(FString::Printf(TEXT("carte du moteur %s"), *GetWorld()->GetOutermost()->GetName()));
}

void AJadgDemoWalkthrough::Note(const FString& What) const
{
	const double Now = FPlatformTime::Seconds() - GStartTime;
	// Le texte entre dans du JSON : seuls la barre oblique inverse et le guillemet y sont protégés.
	const FString Quoted = What.Replace(TEXT("\\"), TEXT("\\\\")).Replace(TEXT("\""), TEXT("\\\""));
	GSteps.Add(FString::Printf(TEXT("{\"seconds\": %.1f, \"step\": \"%s\"}"), Now, *Quoted));
	UE_LOG(LogJadg, Display, TEXT("[Démo] %.1f s : %s"), Now, *What);
}

void AJadgDemoWalkthrough::Shoot(const FString& What)
{
	PendingFile = FPaths::Combine(OutputDir, FString::Printf(TEXT("demo-%02d.png"), ++GShots));
	IFileManager::Get().Delete(*PendingFile, false, true, true);
	FScreenshotRequest::RequestScreenshot(PendingFile, false, false);
	Note(FString::Printf(TEXT("capture %02d : %s"), GShots, *What));
	bShooting = true;
}

bool AJadgDemoWalkthrough::LegDone(const AJadgParty& Party) const
{
	const FLeg& Leg = Legs[GLeg];
	return Exploration->HeroStorey() == Leg.Storey
		&& FVector2D::Distance(Exploration->HeroCell(), FVector2D(Leg.Column, Leg.Row)) < ArrivedCells;
}

void AJadgDemoWalkthrough::Order(AJadgParty& Party)
{
	const FLeg& Leg = Legs[GLeg];
	++Orders;
	GLastOrderFrame = Frames;
	bOrdered = true;
	Note(FString::Printf(TEXT("ordre %d au groupe : marcher vers (%.1f ; %.1f), étage %d — %s"), Orders, Leg.Column, Leg.Row,
		Leg.Storey, Leg.What));
	Party.OrderWalk(Party.PointOn(FVector2D(Leg.Column, Leg.Row), Leg.Storey));
}

void AJadgDemoWalkthrough::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const FString World = GetWorld()->GetOutermost()->GetName();
	const double Now = FPlatformTime::Seconds();
	if (World != GLastWorld && GLastFrame > 0.0)
	{
		GOpenings.Add(FString::Printf(TEXT("{\"map\": \"%s\", \"seconds\": %.2f}"), *World, Now - GLastFrame));
		Note(FString::Printf(TEXT("ouverture de %s : %.2f s de la dernière trame de la carte quittée à la première de celle-ci"),
			*World, Now - GLastFrame));
	}
	GLastWorld = World;
	GLastFrame = Now;
	const bool bCompiling = GShaderCompilingManager != nullptr && GShaderCompilingManager->IsCompiling();
	if (bDone || ++Frames < OpeningFrames || bCompiling)
	{
		return;
	}
	AJadgParty* Party = AJadgParty::Find(GetWorld());
	if (Exploration == nullptr || Party == nullptr || Party->Leader() == nullptr)
	{
		Finish(1, TEXT("il manque l'exploration, le groupe ou son meneur"));
		return;
	}
	if (!Exploration->Encounter().IsEmpty())
	{
		Finish(1, FString::Printf(TEXT("une rencontre s'est engagée : %s"), *Exploration->Encounter()));
		return;
	}
	if (bShooting)
	{
		if (FScreenshotRequest::IsScreenshotRequested() || !FPaths::FileExists(PendingFile))
		{
			return;
		}
		// L'étape est faite et capturée : la suivante commence ici.
		bShooting = false;
		bOrdered = false;
		Orders = 0;
		GLegSince = FPlatformTime::Seconds();
		if (++GLeg >= LegCount)
		{
			Note(TEXT("de retour à Martpart : la démo s'est enchaînée"));
			Finish(0, FString());
		}
		return;
	}
	if (GLeg >= LegCount)
	{
		Finish(0, FString());
		return;
	}

	const FLeg& Leg = Legs[GLeg];
	const FString Map = Exploration->MapId();
	if (Map != Leg.Map)
	{
		// Une étape qui passe un portail finit à l'ouverture de la carte qu'elle vise.
		if (Leg.Opens != nullptr && Map == Leg.Opens)
		{
			const FVector2D Cell = Exploration->HeroCell();
			Note(FString::Printf(TEXT("fait en %.0f s : %s ; arrivé en (%.1f ; %.1f), étage %d"), FPlatformTime::Seconds() - GLegSince,
				Leg.What, Cell.X, Cell.Y, Exploration->HeroStorey()));
			Shoot(FString::Printf(TEXT("l'arrivée sur %s"), *Map));
			return;
		}
		Finish(1, FString::Printf(TEXT("la carte %s s'ouvre hors de l'ordre de la démo (étape : %s)"), *Map, Leg.What));
		return;
	}
	if (Leg.Opens == nullptr && LegDone(*Party))
	{
		Party->Leader()->StopWalking();
		Note(FString::Printf(TEXT("fait en %.0f s : %s"), FPlatformTime::Seconds() - GLegSince, Leg.What));
		Shoot(FString::Printf(TEXT("le meneur à l'étage %d de l'Arena of Fate"), Leg.Storey));
		return;
	}
	if (FPlatformTime::Seconds() - GLegSince > LegSeconds)
	{
		const FVector2D Cell = Exploration->HeroCell();
		Finish(1, FString::Printf(TEXT("sans suite depuis %.0f s : %s ; le meneur en (%.1f ; %.1f), étage %d"), LegSeconds, Leg.What,
			Cell.X, Cell.Y, Exploration->HeroStorey()));
		return;
	}
	if (!bOrdered)
	{
		Order(*Party);
	}
	else if (Frames - GLastOrderFrame > OrderFrames && !Party->Leader()->IsWalking())
	{
		if (Orders >= MaxOrders)
		{
			const FVector2D Cell = Exploration->HeroCell();
			Finish(1, FString::Printf(TEXT("le meneur s'arrête en (%.1f ; %.1f), étage %d, après %d ordres : %s"), Cell.X, Cell.Y,
				Exploration->HeroStorey(), Orders, Leg.What));
			return;
		}
		Order(*Party);
	}
}

void AJadgDemoWalkthrough::Finish(int32 ExitCode, const FString& Reason)
{
	if (bDone)
	{
		return;
	}
	bDone = true;
	if (ExitCode != 0)
	{
		Note(FString::Printf(TEXT("arrêt : %s"), *Reason));
		UE_LOG(LogJadg, Error, TEXT("[Démo] %s"), *Reason);
	}
	FString Json = FString::Printf(TEXT("{\n  \"completed\": %s,\n  \"legs\": %d,\n  \"legsDone\": %d,\n  \"captures\": %d,\n  \"steps\": [\n    "),
		ExitCode == 0 ? TEXT("true") : TEXT("false"), LegCount, GLeg, GShots);
	Json += FString::Join(GSteps, TEXT(",\n    "));
	Json += TEXT("\n  ],\n  \"openings\": [\n    ");
	Json += FString::Join(GOpenings, TEXT(",\n    "));
	Json += TEXT("\n  ]\n}\n");
	const FString File = FPaths::Combine(OutputDir, TEXT("parcours.json"));
	FFileHelper::SaveStringToFile(Json, *File, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	UE_LOG(LogJadg, Display, TEXT("[Démo] %s"), *File);
	FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(ExitCode));
}
