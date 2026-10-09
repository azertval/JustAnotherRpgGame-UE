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
#include "NavigationSystem.h"
#include "ShaderCompiler.h"
#include "UObject/Package.h"
#include "UnrealClient.h"

namespace
{
	const TCHAR* const Martpart = TEXT("central-empire/capital/martpart");
	const TCHAR* const Arenarea = TEXT("central-empire/capital/arenarea");
	const TCHAR* const ArenaOfFate = TEXT("central-empire/capital/arenarea/arena-of-fate");

	/// Une étape : sur quelle carte, vers quel portail (le centre de sa case, à son étage), et ce qu'il
	/// ouvre : une autre carte, ou un autre étage de la même (`Arrives`, l'étage où le groupe arrive) ;
	/// `Arrives` à -1 : un lieu de passage, atteint à moins de `ArrivedCells`.
	struct FLeg
	{
		const TCHAR* Map;
		double Column;
		double Row;
		int32 Storey;
		const TCHAR* Opens;
		int32 Arrives;
		const TCHAR* What;
	};

	// Les cases des portails sont celles des descriptions de carte : Martpart (e4), Arenarea (e4,
	// e2), l'Arena of Fate (e20, e2, e25, e33, e23 — les portails de la v4 entre ses niveaux).
	const FLeg Legs[] = {
		{Martpart, 30.5, 34.5, 0, nullptr, -1, TEXT("Martpart : de Market Gate à la place des étals, auprès de la mère")},
		{Martpart, 8.5, 0.5, 0, Arenarea, 0, TEXT("Martpart : le portail de Stravian Avenue, vers Arenarea")},
		{Arenarea, 65.5, 33.5, 0, ArenaOfFate, 1, TEXT("Arenarea : l'escalier de l'arène, vers le vestibule des vestiaires")},
		{ArenaOfFate, 4.5, 12.5, 1, nullptr, 0, TEXT("l'Arena of Fate : des vestiaires au sable, par la porte du triomphe")},
		{ArenaOfFate, 4.5, 12.5, 0, nullptr, 1, TEXT("l'Arena of Fate : du sable aux vestiaires, par la porte du triomphe")},
		{ArenaOfFate, 22.5, 4.5, 1, nullptr, 2, TEXT("l'Arena of Fate : de la prison aux catacombes, par leur descente")},
		{ArenaOfFate, 22.5, 6.5, 2, nullptr, 1, TEXT("l'Arena of Fate : des catacombes à la prison")},
		{ArenaOfFate, 16.5, 21.5, 1, Arenarea, 0, TEXT("l'Arena of Fate : du vestibule à Arenarea, par l'escalier du parvis")},
		{Arenarea, 116.5, 86.5, 0, Martpart, 0, TEXT("Arenarea : le portail de Herofate Avenue, retour à Martpart")},
	};
	constexpr int32 LegCount = UE_ARRAY_COUNT(Legs);

	/// Trames laissées à la carte pour s'ouvrir : le maillage de navigation, les matières.
	constexpr int32 OpeningFrames = 120;
	/// Une étape sans suite au-delà de cette durée arrête le parcours, en secondes.
	constexpr double LegSeconds = 240.0;
	/// Un meneur arrêté avant son but reçoit l'ordre de nouveau, autant de fois au plus.
	constexpr int32 MaxOrders = 6;
	/// Un lieu de passage est atteint à moins de cette distance de sa case, en cases.
	constexpr double ArrivedCells = 2.0;
	/// Trames laissées à un ordre avant de juger que le meneur s'est arrêté.
	constexpr int32 OrderFrames = 60;

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
		// `-JadgDemoEtape=<rang>` reprend la démo à une étape, lancée sur sa carte.
		FParse::Value(FCommandLine::Get(), TEXT("JadgDemoEtape="), GLeg);
		GLeg = FMath::Clamp(GLeg, 0, LegCount - 1);
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
	if (Leg.Arrives < 0)
	{
		return FVector2D::Distance(Exploration->HeroCell(), FVector2D(Leg.Column, Leg.Row)) < ArrivedCells;
	}
	// Un portail de la même carte : l'étape est faite quand le groupe est à l'étage où il mène.
	return Exploration->HeroStorey() == Leg.Arrives;
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
	// Le maillage de navigation d'une grande carte se construit après son ouverture (Martpart :
	// une marche donnée avant s'arrête où il s'arrête encore).
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	const bool bCompiling = (GShaderCompilingManager != nullptr && GShaderCompilingManager->IsCompiling())
		|| (Navigation != nullptr && Navigation->IsNavigationBuildInProgress());
	if (!bDone && Frames % 600 == 0)
	{
		// Le pouls du parcours : une carte qui s'ouvre lentement se voit ici, pas dans le silence.
		UE_LOG(LogJadg, Display, TEXT("[Démo] trame %d, %.1f ms, shaders ou maillage de navigation en construction : %s"), Frames,
			DeltaSeconds * 1000.0f, bCompiling ? TEXT("oui") : TEXT("non"));
	}
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
		Shoot(Leg.Arrives < 0 ? FString(Leg.What) : FString::Printf(TEXT("le meneur à l'étage %d de l'Arena of Fate"), Leg.Arrives));
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
