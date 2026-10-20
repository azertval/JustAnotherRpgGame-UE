// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core before Unreal: inspect the same live map and arrival contract as exploration.
#include "Game/JadgExplorationState.h"

#include "Capture/JadgDemoWalkthrough.h"

#include "Characters/JadgParty.h"
#include "Characters/JadgWalker.h"
#include "Bridge/JadgPaths.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
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
#include "World/JadgMapFrame.h"

namespace
{
	const TCHAR* const Martpart = TEXT("central-empire/capital/martpart");
	const TCHAR* const Arenarea = TEXT("central-empire/capital/arenarea");
	const TCHAR* const ArenaOfFate = TEXT("central-empire/capital/arenarea/arena-of-fate");

	/// Entity identities remain stable when a district moves or changes scale.
	struct FLeg
	{
		const TCHAR* Map;
		const TCHAR* Entity;
		const TCHAR* Type;
		const TCHAR* Opens;
		const TCHAR* Arrival;
		const TCHAR* AwayFrom;
		const TCHAR* What;
	};

	// No synthetic self-portals between floors: the Arena has continuous physical stairs.
	const FLeg Legs[] = {
		{Martpart, TEXT("e1"), TEXT("npc"), nullptr, nullptr, nullptr,
			TEXT("Martpart : de Market Gate aux étals, auprès de la mère")},
		{Martpart, TEXT("e4"), TEXT("portal"), Arenarea, TEXT("from-martpart"), nullptr,
			TEXT("Martpart : Stravian Avenue, vers Arenarea")},
		{Arenarea, TEXT("e4"), TEXT("portal"), ArenaOfFate, TEXT("from-arenarea"), nullptr,
			TEXT("Arenarea : le parvis vers le vestibule des vestiaires")},
		{ArenaOfFate, TEXT("e21"), TEXT("spawnPoint"), nullptr, nullptr, TEXT("e23"),
			TEXT("l'Arena of Fate : court passage physique dans le vestibule")},
		{ArenaOfFate, TEXT("e23"), TEXT("portal"), Arenarea, TEXT("from-arena-of-fate"), nullptr,
			TEXT("l'Arena of Fate : du vestibule au parvis d'Arenarea")},
		{Arenarea, TEXT("e2"), TEXT("portal"), Martpart, TEXT("from-arenarea"), nullptr,
			TEXT("Arenarea : Herofate Avenue, retour à Martpart")},
	};
	constexpr int32 LegCount = UE_ARRAY_COUNT(Legs);

	/// Trames laissées à la carte pour s'ouvrir : le maillage de navigation, les matières.
	constexpr int32 OpeningFrames = 120;
	/// Une étape sans suite au-delà de cette durée arrête le parcours, en secondes.
	constexpr double LegSeconds = 600.0;
	/// Un meneur arrêté avant son but reçoit l'ordre de nouveau, autant de fois au plus.
	constexpr int32 MaxOrders = 6;
	/// Un lieu de passage est atteint à moins de cette distance de sa case, en cases.
	constexpr double ArrivedCells = 0.9;
	constexpr double TerrainArrivalHeightToleranceCm = 25.0;
	/// Les anciennes cartes sans terrain local gardent leurs sols et leur marge de projection.
	constexpr double LegacyArrivalHeightToleranceCm = 75.0;
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
	TArray<FString> GTransitions;
	int32 GStartedAtLeg = 0;
	int32 GOrderedLeg = INDEX_NONE;

	const core::MapEntity* FindEntity(const core::Level& Map, const TCHAR* Id)
	{
		for (const core::MapEntity& Entity : Map.entities())
		{
			if (Entity.id == TCHAR_TO_UTF8(Id))
			{
				return &Entity;
			}
		}
		return nullptr;
	}

	FString EntityText(const core::MapEntity& Entity, const char* Key)
	{
		const auto Found = Entity.properties.find(Key);
		const std::string* Text = Found != Entity.properties.end() ? std::get_if<std::string>(&Found->second) : nullptr;
		return Text != nullptr ? FJadgPaths::ToFString(*Text) : FString{};
	}

	double ArrivalHeightTolerance(const UWorld* World)
	{
		for (TActorIterator<AJadgMapFrame> Frame(World); Frame; ++Frame)
		{
			return !Frame->TerrainHeights.IsEmpty() || !Frame->StoreyRegions.IsEmpty()
				? TerrainArrivalHeightToleranceCm : LegacyArrivalHeightToleranceCm;
		}
		return LegacyArrivalHeightToleranceCm;
	}
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
		GStartedAtLeg = GLeg;
		if (GLeg < 0 || GLeg >= LegCount)
		{
			Finish(1, TEXT("JadgDemoEtape est hors des étapes du parcours"));
			return;
		}
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
	ShotSince = FPlatformTime::Seconds();
}

bool AJadgDemoWalkthrough::ResolveTarget(FString& Error)
{
	const core::Level* Map = Exploration->CoreState().Session->map();
	if (Map == nullptr)
	{
		Error = TEXT("la carte courante de Core est absente");
		return false;
	}
	const FLeg& Leg = Legs[GLeg];
	const core::MapEntity* Entity = FindEntity(*Map, Leg.Entity);
	if (Entity == nullptr || Entity->type != TCHAR_TO_UTF8(Leg.Type))
	{
		Error = FString::Printf(TEXT("%s : entité %s absente ou type différent de %s"), Leg.Map, Leg.Entity, Leg.Type);
		return false;
	}
	TargetCell = FVector2D(Entity->position.column + 0.5, Entity->position.row + 0.5);
	TargetStorey = Entity->storey;
	if (Leg.Opens != nullptr)
	{
		if (EntityText(*Entity, "targetMap") != Leg.Opens || EntityText(*Entity, "arrival") != Leg.Arrival)
		{
			Error = FString::Printf(TEXT("le contrat du portail %s#%s a changé"), Leg.Map, Leg.Entity);
			return false;
		}
		const auto Sealed = Entity->properties.find("sealed");
		const bool* IsSealed = Sealed != Entity->properties.end() ? std::get_if<bool>(&Sealed->second) : nullptr;
		if (IsSealed != nullptr && *IsSealed)
		{
			Error = FString::Printf(TEXT("le portail %s#%s est condamné"), Leg.Map, Leg.Entity);
			return false;
		}
	}
	if (Leg.AwayFrom != nullptr)
	{
		const core::MapEntity* Portal = FindEntity(*Map, Leg.AwayFrom);
		if (Portal == nullptr || Portal->type != "portal" || Portal->storey != TargetStorey)
		{
			Error = TEXT("le passage du vestibule n'a pas son portail extérieur au même étage");
			return false;
		}
		FVector2D Inward = TargetCell - FVector2D(Portal->position.column + 0.5, Portal->position.row + 0.5);
		if (!Inward.Normalize())
		{
			Error = TEXT("le portail et l'arrivée du vestibule occupent la même case");
			return false;
		}
		TargetCell += Inward * 3.0; // 4.5 physical metres inside, on this storey.
	}
	if (!FMath::IsFinite(TargetCell.X) || !FMath::IsFinite(TargetCell.Y)
		|| TargetCell.X < 0.0 || TargetCell.Y < 0.0
		|| TargetCell.X >= Map->tileMap().width() || TargetCell.Y >= Map->tileMap().height()
		|| TargetStorey < 0 || (Map->storeys().empty() ? TargetStorey != 0
			: static_cast<std::size_t>(TargetStorey) >= Map->storeys().size()))
	{
		Error = TEXT("le but du parcours est hors de la grille ou de ses étages");
		return false;
	}
	bTargetReady = true;
	return true;
}

bool AJadgDemoWalkthrough::ValidateArrival(const AJadgParty& Party, FString& Error,
	FVector& ExpectedGround, double& HeightTolerance) const
{
	const FLeg& Leg = Legs[GLeg];
	const core::Level* Map = Exploration->CoreState().Session->map();
	if (GOrderedLeg != GLeg || Map == nullptr || Leg.Arrival == nullptr)
	{
		Error = TEXT("la carte a changé sans ordre de marche confirmé vers son portail");
		return false;
	}
	const auto Arrival = core::arrivalPointAt(*Map, TCHAR_TO_UTF8(Leg.Arrival));
	if (!Arrival.has_value())
	{
		Error = FString::Printf(TEXT("le point d'arrivée %s est absent"), Leg.Arrival);
		return false;
	}
	const int32 Storey = core::arrivalStoreyAt(*Map, TCHAR_TO_UTF8(Leg.Arrival));
	const FVector2D Cell(Arrival->column + 0.5, Arrival->row + 0.5);
	if (Exploration->HeroStorey() != Storey || FVector2D::Distance(Exploration->HeroCell(), Cell) > 1.0
		|| FVector2D::Distance(Party.CellOf(Party.Leader()->Feet()), Cell) > 1.0)
	{
		Error = FString::Printf(TEXT("l'arrivée physique ne correspond pas à %s, étage %d"), Leg.Arrival, Storey);
		return false;
	}
	// PointOn garde 50 cm de marge pour la projection navigation ; la preuve
	// compare les pieds au vrai sol local (terrain ou surface d'étage), en cm monde.
	ExpectedGround = Party.PointOn(Cell, Storey);
	ExpectedGround.Z -= 50.0;
	HeightTolerance = ArrivalHeightTolerance(GetWorld());
	const double ActualGround = Party.Leader()->Feet().Z;
	if (!FMath::IsFinite(ExpectedGround.Z) || !FMath::IsFinite(ActualGround)
		|| FMath::Abs(ActualGround - ExpectedGround.Z) > HeightTolerance)
	{
		Error = FString::Printf(TEXT("l'arrivée %s n'est pas sur son sol : pieds %.1f cm, attendu %.1f cm, tolérance %.0f cm"),
			Leg.Arrival, ActualGround, ExpectedGround.Z, HeightTolerance);
		return false;
	}
	return true;
}

bool AJadgDemoWalkthrough::LegDone(const AJadgParty& Party) const
{
	return bTargetReady && GOrderedLeg == GLeg && Exploration->HeroStorey() == TargetStorey
		&& FVector2D::Distance(Exploration->HeroCell(), TargetCell) < ArrivedCells
		&& FVector2D::Distance(Party.CellOf(Party.Leader()->Feet()), TargetCell) < ArrivedCells
		&& FMath::Abs(Party.Leader()->Feet().Z - Party.PointOn(TargetCell, TargetStorey).Z) < 100.0;
}

void AJadgDemoWalkthrough::Order(AJadgParty& Party)
{
	const FLeg& Leg = Legs[GLeg];
	++Orders;
	GLastOrderFrame = Frames;
	bOrdered = true;
	GOrderedLeg = GLeg;
	Note(FString::Printf(TEXT("ordre %d au groupe : marcher vers %s (%.1f ; %.1f), étage %d — %s"), Orders, Leg.Entity,
		TargetCell.X, TargetCell.Y, TargetStorey, Leg.What));
	Party.OrderWalk(Party.PointOn(TargetCell, TargetStorey));
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
	if (!bDone && GLegSince > 0.0 && Now - GLegSince > LegSeconds)
	{
		Finish(1, FString::Printf(TEXT("l'étape %d reste bloquée après %.0f s (chargement, marche ou capture)"), GLeg, LegSeconds));
		return;
	}
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
	if (!Exploration->LoadErrors().IsEmpty() || Exploration->InDialogue())
	{
		Finish(1, !Exploration->LoadErrors().IsEmpty()
			? FString::Join(Exploration->LoadErrors(), TEXT("; "))
			: TEXT("un dialogue inattendu a suspendu le parcours physique"));
		return;
	}
	if (bShooting)
	{
		if (FScreenshotRequest::IsScreenshotRequested() || !FPaths::FileExists(PendingFile))
		{
			if (Now - ShotSince > 45.0)
			{
				Finish(1, TEXT("la capture de l'étape n'a pas été écrite"));
			}
			return;
		}
		// L'étape est faite et capturée : la suivante commence ici.
		bShooting = false;
		bOrdered = false;
		bTargetReady = false;
		GOrderedLeg = INDEX_NONE;
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
	// Core changes map before OpenLevel finishes loading. Wait for the actual
	// destination world: never capture the source world as a successful arrival.
	if (World != AJadgMapFrame::MapPackage(Map))
	{
		return;
	}
	if (Map != Leg.Map)
	{
		// Une étape qui passe un portail finit à l'ouverture de la carte qu'elle vise.
		if (Leg.Opens != nullptr && Map == Leg.Opens)
		{
			FString Error;
			FVector ExpectedGround;
			double HeightTolerance = 0.0;
			if (!ValidateArrival(*Party, Error, ExpectedGround, HeightTolerance))
			{
				Finish(1, Error);
				return;
			}
			const FVector2D Cell = Exploration->HeroCell();
			const FVector Feet = Party->Leader()->Feet();
			GTransitions.Add(FString::Printf(
				TEXT("{\"from\":\"%s\",\"portal\":\"%s\",\"to\":\"%s\",\"arrival\":\"%s\",\"storey\":%d,\"cell\":[%.3f,%.3f],\"feetWorldCm\":[%.3f,%.3f,%.3f],\"expectedGroundWorldCm\":[%.3f,%.3f,%.3f],\"arrivalHeightErrorCm\":%.3f,\"arrivalHeightToleranceCm\":%.1f,\"physicalArrival\":true}"),
				Leg.Map, Leg.Entity, *Map, Leg.Arrival, Exploration->HeroStorey(), Cell.X, Cell.Y,
				Feet.X, Feet.Y, Feet.Z, ExpectedGround.X, ExpectedGround.Y, ExpectedGround.Z,
				FMath::Abs(Feet.Z - ExpectedGround.Z), HeightTolerance));
			Note(FString::Printf(TEXT("fait en %.0f s : %s ; arrivé en (%.1f ; %.1f), étage %d"), FPlatformTime::Seconds() - GLegSince,
				Leg.What, Cell.X, Cell.Y, Exploration->HeroStorey()));
			Shoot(FString::Printf(TEXT("l'arrivée sur %s"), *Map));
			return;
		}
		Finish(1, FString::Printf(TEXT("la carte %s s'ouvre hors de l'ordre de la démo (étape : %s)"), *Map, Leg.What));
		return;
	}
	if (!bTargetReady)
	{
		FString Error;
		if (!ResolveTarget(Error))
		{
			Finish(1, Error);
			return;
		}
	}
	if (Leg.Opens == nullptr && LegDone(*Party))
	{
		Party->Leader()->StopWalking();
		Note(FString::Printf(TEXT("fait en %.0f s : %s"), FPlatformTime::Seconds() - GLegSince, Leg.What));
		Shoot(Leg.What);
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
	FString FinalReason = Reason;
	if (ExitCode == 0 && (GLeg < LegCount || (GStartedAtLeg == 0 && GTransitions.Num() != 4)))
	{
		ExitCode = 1;
		FinalReason = TEXT("les étapes ou les quatre transferts physiques ne sont pas tous confirmés");
	}
	if (ExitCode != 0)
	{
		Note(FString::Printf(TEXT("arrêt : %s"), *FinalReason));
		UE_LOG(LogJadg, Error, TEXT("[Démo] %s"), *FinalReason);
	}
	FString Json = FString::Printf(TEXT("{\n  \"completed\": %s,\n  \"fullRoundTrip\": %s,\n  \"startedAtLeg\": %d,\n  \"reason\": \"%s\",\n  \"legs\": %d,\n  \"legsDone\": %d,\n  \"captures\": %d,\n  \"steps\": [\n    "),
		ExitCode == 0 ? TEXT("true") : TEXT("false"),
		ExitCode == 0 && GStartedAtLeg == 0 && GTransitions.Num() == 4 ? TEXT("true") : TEXT("false"),
		GStartedAtLeg, *FinalReason.ReplaceCharWithEscapedChar(), LegCount, GLeg, GShots);
	Json += FString::Join(GSteps, TEXT(",\n    "));
	Json += TEXT("\n  ],\n  \"openings\": [\n    ");
	Json += FString::Join(GOpenings, TEXT(",\n    "));
	Json += TEXT("\n  ],\n  \"portalTransitions\": [\n    ");
	Json += FString::Join(GTransitions, TEXT(",\n    "));
	Json += TEXT("\n  ]\n}\n");
	const FString File = FPaths::Combine(OutputDir, TEXT("parcours.json"));
	FFileHelper::SaveStringToFile(Json, *File, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	UE_LOG(LogJadg, Display, TEXT("[Démo] %s"), *File);
	FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(ExitCode));
}
