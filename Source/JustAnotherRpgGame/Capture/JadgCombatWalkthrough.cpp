// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgCombatWalkthrough.h"

#include "Characters/JadgParty.h"
#include "Characters/JadgWalker.h"
#include "Combat/JadgCombat.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Game/JadgExploration.h"
#include "HAL/FileManager.h"
#include "InputKeyEventArgs.h"
#include "JustAnotherRpgGame.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Player/JadgControls.h"
#include "Player/JadgPlayerController.h"
#include "ShaderCompiler.h"
#include "UObject/Package.h"
#include "UnrealClient.h"

namespace
{
	const TCHAR* const Forecourt = TEXT("essai/parvis");
	const TCHAR* const Encounter = TEXT("arene-bandits");
	/// Le maître d'arène, sur le plan du parvis (`build_essai_maps.py`).
	const FIntPoint MasterCell(12, 7);

	constexpr int32 OpeningFrames = 90;
	constexpr int32 LineFrames = 45;
	constexpr double StallSeconds = 90.0;
	constexpr double ClickTolerance = 112.0;

	/// Ce qui survit au changement de carte.
	TArray<FString> GSteps;
	int32 GShots = 0;
	bool GEngaged = false;
	bool GPreviewShot = false;
	bool GDeploymentShot = false;
	bool GOutcomeShot = false;
	FString GOutcome;
	FVector2D GHeroBefore = FVector2D::ZeroVector;
	FVector2D GHeroPlaced = FVector2D::ZeroVector;
	TArray<FString> GJournal;
	FString GCandidates;
	int32 GHeroTurns = 0;

	/// Le plan du tour en cours de geste.
	TOptional<FVector> GMoveTo;
	FName GAction;
	int32 GTarget = 0;
	int32 GRank = 0;

	FViewport* GameViewport()
	{
		return GEngine->GameViewport != nullptr ? GEngine->GameViewport->Viewport : nullptr;
	}

	FString Quote(const FString& Text)
	{
		return TEXT("\"") + Text.Replace(TEXT("\\"), TEXT("\\\\")).Replace(TEXT("\""), TEXT("\\\"")) + TEXT("\"");
	}
}

AJadgCombatWalkthrough::AJadgCombatWalkthrough()
{
	PrimaryActorTick.bCanEverTick = true;
	// Après le combat : ce qui se lit ici est l'état de la trame.
	PrimaryActorTick.TickGroup = TG_PostUpdateWork;
}

void AJadgCombatWalkthrough::BeginPlay()
{
	Super::BeginPlay();
	FParse::Value(FCommandLine::Get(), TEXT("JadgParcoursCombat="), OutputDir);
	OutputDir = FPaths::ConvertRelativePathToFull(OutputDir);
	IFileManager::Get().MakeDirectory(*OutputDir, true);
	Exploration = GetGameInstance() != nullptr ? GetGameInstance()->GetSubsystem<UJadgExploration>() : nullptr;
	Player = Cast<AJadgPlayerController>(GetWorld()->GetFirstPlayerController());
	StateSince = FPlatformTime::Seconds();
	Note(FString::Printf(TEXT("carte du moteur %s"), *GetWorld()->GetOutermost()->GetName()));
	const AJadgParty* Party = AJadgParty::Find(GetWorld());
	if (GEngaged && Exploration != nullptr && Party != nullptr && !Party->InArena())
	{
		// Le retour : où le groupe pose son meneur, avant toute trame.
		const FVector2D Placed = Party != nullptr && Party->Leader() != nullptr ? Party->CellOf(Party->Leader()->Feet()) : FVector2D::ZeroVector;
		GHeroPlaced = Placed;
		Note(FString::Printf(TEXT("retour : meneur posé en (%.2f ; %.2f)"), Placed.X, Placed.Y));
	}
}

void AJadgCombatWalkthrough::Note(const FString& What) const
{
	const double Now = FPlatformTime::Seconds() - GStartTime;
	GSteps.Add(FString::Printf(TEXT("{\"seconds\": %.1f, \"step\": %s}"), Now, *Quote(What)));
	UE_LOG(LogJadg, Display, TEXT("[Parcours du combat] %.1f s : %s"), Now, *What);
}

void AJadgCombatWalkthrough::Press(const FKey& Key, int32 ForFrames)
{
	Player->InputKey(FInputKeyEventArgs(GameViewport(), FInputDeviceId::CreateFromInternalId(0), Key, IE_Pressed, 0));
	FHeld& Added = Held.AddDefaulted_GetRef();
	Added.Key = Key;
	Added.Until = Frames + ForFrames;
}

void AJadgCombatWalkthrough::ReleaseDue()
{
	for (int32 Index = Held.Num() - 1; Index >= 0; --Index)
	{
		if (Held[Index].Until <= Frames)
		{
			Player->InputKey(FInputKeyEventArgs(GameViewport(), FInputDeviceId::CreateFromInternalId(0), Held[Index].Key, IE_Released, 0));
			Held.RemoveAt(Index);
		}
	}
}

bool AJadgCombatWalkthrough::PressCommand(const TCHAR* Command)
{
	const FKey Key = UJadgControls::KeyOf(Command);
	if (!Key.IsValid())
	{
		Finish(1, FString::Printf(TEXT("la commande %s n'a pas de touche"), Command));
		return false;
	}
	Note(FString::Printf(TEXT("touche %s : %s"), *Key.GetDisplayName(false).ToString(), Command));
	Press(Key);
	return true;
}

bool AJadgCombatWalkthrough::ClickPoint(const FVector& World, const TCHAR* What)
{
	FVector2D Screen;
	FHitResult Hit;
	if (!Player->ProjectWorldLocationToScreen(World, Screen))
	{
		Finish(1, FString::Printf(TEXT("%s n'est pas devant la caméra"), What));
		return false;
	}
	// Un combattant entre la caméra et le point le cache : le pointeur cherche, à quelques pixels,
	// un point du sol visible assez proche — ce que ferait un joueur.
	const AJadgCombat* Combat = AJadgCombat::Find(GetWorld());
	const auto OnGround = [&](const FVector2D& At)
	{
		Player->PointAt(At);
		if (!Player->PointerHit(Hit) || FVector::Dist2D(Hit.ImpactPoint, World) > ClickTolerance)
		{
			return false;
		}
		for (const FJadgFighter& Fighter : Combat != nullptr ? Combat->Fighters() : TArray<FJadgFighter>())
		{
			if (Fighter.Walker != nullptr && Fighter.Walker == Hit.GetActor())
			{
				return false;
			}
		}
		return true;
	};
	bool bFound = OnGround(Screen);
	for (int32 Ring = 1; Ring <= 6 && !bFound; ++Ring)
	{
		for (int32 Step = 0; Step < 8 && !bFound; ++Step)
		{
			const double Angle = Step * UE_DOUBLE_PI / 4.0;
			const FVector2D Shifted = Screen + FVector2D(FMath::Cos(Angle), FMath::Sin(Angle)) * (Ring * 8.0);
			if (OnGround(Shifted))
			{
				Screen = Shifted;
				bFound = true;
			}
		}
	}
	if (!bFound)
	{
		Finish(1, FString::Printf(TEXT("le pointeur en (%.0f ; %.0f) ne désigne pas %s"), Screen.X, Screen.Y, What));
		return false;
	}
	Note(FString::Printf(TEXT("clic au sol en (%.0f ; %.0f) : %s"), Screen.X, Screen.Y, What));
	Press(UJadgControls::KeyOf(TEXT("Walk")));
	return true;
}

bool AJadgCombatWalkthrough::ClickActor(const AActor* Target, const TCHAR* What)
{
	if (Target == nullptr)
	{
		Finish(1, FString::Printf(TEXT("%s n'a pas de figurine"), What));
		return false;
	}
	// Le centre de la capsule : une figurine tombée garde sa capsule debout.
	const FVector Origin = Target->GetActorLocation();
	FVector2D Screen;
	FHitResult Hit;
	if (!Player->ProjectWorldLocationToScreen(Origin, Screen))
	{
		Finish(1, FString::Printf(TEXT("%s n'est pas devant la caméra"), What));
		return false;
	}
	Player->PointAt(Screen);
	if (!Player->PointerHit(Hit) || Hit.GetActor() != Target)
	{
		Finish(1, FString::Printf(TEXT("le pointeur en (%.0f ; %.0f) ne désigne pas %s"), Screen.X, Screen.Y, What));
		return false;
	}
	Note(FString::Printf(TEXT("clic en (%.0f ; %.0f) sur %s"), Screen.X, Screen.Y, What));
	Press(UJadgControls::KeyOf(TEXT("Walk")));
	return true;
}

void AJadgCombatWalkthrough::Shoot(const FString& What)
{
	PendingFile = FPaths::Combine(OutputDir, FString::Printf(TEXT("combat-%02d.png"), ++GShots));
	IFileManager::Get().Delete(*PendingFile, false, true, true);
	FScreenshotRequest::RequestScreenshot(PendingFile, false, false);
	bShooting = true;
	Note(FString::Printf(TEXT("capture %02d : %s"), GShots, *What));
}

bool AJadgCombatWalkthrough::ShotWritten() const
{
	return !FScreenshotRequest::IsScreenshotRequested() && FPaths::FileExists(PendingFile);
}

void AJadgCombatWalkthrough::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (Player != nullptr)
	{
		ReleaseDue();
	}
	const bool bCompiling = GShaderCompilingManager != nullptr && GShaderCompilingManager->IsCompiling();
	if (bDone || ++Frames < OpeningFrames || bCompiling || Frames < ResumeAt)
	{
		return;
	}
	if (bShooting)
	{
		if (!ShotWritten())
		{
			return;
		}
		bShooting = false;
	}
	AJadgParty* Party = AJadgParty::Find(GetWorld());
	if (Exploration == nullptr || Party == nullptr || Player == nullptr)
	{
		Finish(1, TEXT("il manque l'exploration, le groupe ou le contrôleur du joueur"));
		return;
	}
	if (FPlatformTime::Seconds() - StateSince > StallSeconds)
	{
		Finish(1, FString::Printf(TEXT("rien de neuf depuis %.0f s"), StallSeconds));
		return;
	}
	if (AJadgCombat* Combat = AJadgCombat::Find(GetWorld()))
	{
		InArena(*Combat);
		return;
	}
	OnForecourt(*Party);
}

void AJadgCombatWalkthrough::OnForecourt(AJadgParty& Party)
{
	if (Exploration->MapId() != Forecourt)
	{
		if (Party.InArena())
		{
			// L'arène s'ouvre : le combat se monte à la première trame du groupe.
			return;
		}
		Finish(1, FString::Printf(TEXT("le parcours du combat commence au parvis, pas sur « %s »"), *Exploration->MapId()));
		return;
	}
	if (GEngaged)
	{
		// Le retour : l'issue écrite, le groupe là où il était.
		const FString Won = Exploration->Flag(TEXT("encounter/arene-bandits/won"));
		const FVector2D Now = Exploration->HeroCell();
		Note(FString::Printf(TEXT("retour au parvis : meneur en (%.2f ; %.2f), avant le combat (%.2f ; %.2f) ; encounter/arene-bandits/won = « %s »"),
			Now.X, Now.Y, GHeroBefore.X, GHeroBefore.Y, *Won));
		if (GOutcome != TEXT("Victoire") || Won != TEXT("1"))
		{
			Finish(1, FString::Printf(TEXT("le groupe n'a pas gagné : %s"), *GOutcome));
			return;
		}
		// Le meneur est posé là où Core l'avait gelé, et il y reste.
		if (FVector2D::Distance(GHeroPlaced, GHeroBefore) > 0.05 || FVector2D::Distance(Now, GHeroBefore) > 0.05)
		{
			Finish(1, TEXT("le groupe ne revient pas là où il était"));
			return;
		}
		Finish(0, FString());
		return;
	}
	if (Exploration->InDialogue())
	{
		// « Combattre » se donne au clavier, par son rang.
		if (Frames < ResumeAt + LineFrames)
		{
			return;
		}
		const TArray<FJadgChoice> Offered = Exploration->Choices();
		const int32 Rank = Offered.IndexOfByPredicate([](const FJadgChoice& Choice) { return Choice.Id == TEXT("combattre"); });
		if (Rank == INDEX_NONE)
		{
			if (Offered.Num() <= 1)
			{
				PressCommand(TEXT("Interact"));
				ResumeAt = Frames + 8;
				return;
			}
			Finish(1, FString::Printf(TEXT("le maître d'arène ne propose pas de combattre : « %s »"), *Exploration->Line()));
			return;
		}
		Shoot(FString::Printf(TEXT("%s : « %s »"), *Exploration->Speaker(), *Exploration->Line()));
		GHeroBefore = Exploration->HeroCell();
		PressCommand(*FString::Printf(TEXT("Choice%d"), Rank + 1));
		GEngaged = true;
		StateSince = FPlatformTime::Seconds();
		ResumeAt = Frames + 8;
		return;
	}
	if (!bAsked)
	{
		bAsked = true;
		FString Master;
		for (const FJadgEntity& Entity : Exploration->Entities())
		{
			if (Entity.Type == TEXT("npc") && Entity.Cell == MasterCell)
			{
				Master = Entity.Id;
			}
		}
		ClickActor(Party.EntityActor(Master), TEXT("le maître d'arène"));
		StateSince = FPlatformTime::Seconds();
		ResumeAt = Frames;
	}
}

void AJadgCombatWalkthrough::InArena(AJadgCombat& Combat)
{
	if (!Combat.IsMounted())
	{
		return;
	}
	if (!GDeploymentShot)
	{
		GDeploymentShot = true;
		Shoot(TEXT("l'arène : le déploiement, quatre héros contre les bandits"));
		StateSince = FPlatformTime::Seconds();
		return;
	}
	if (Combat.IsOver())
	{
		if (!GOutcomeShot && !Combat.IsBusy())
		{
			GOutcomeShot = true;
			GOutcome = Combat.Outcome();
			GJournal = Combat.Journal(100000);
			GCandidates = Combat.CandidateReport();
			Note(FString::Printf(TEXT("issue : %s au round %d, %d tour(s) de héros joués au clavier et à la souris"), *GOutcome, Combat.Round(), GHeroTurns));
			Shoot(FString::Printf(TEXT("l'issue : %s"), *GOutcome));
			StateSince = FPlatformTime::Seconds();
		}
		return;
	}
	if (Combat.IsPlayerTurn())
	{
		PlayHeroTurn(Combat);
	}
	else if (Combat.IsBusy() || Combat.ActiveId() != TurnOf)
	{
		// Les gestes se montrent, l'IA joue : le combat avance.
		StateSince = FPlatformTime::Seconds();
	}
}

void AJadgCombatWalkthrough::PlayHeroTurn(AJadgCombat& Combat)
{
	if (Combat.ActiveId() != TurnOf || Combat.Round() != TurnRound)
	{
		TurnOf = Combat.ActiveId();
		TurnRound = Combat.Round();
		TurnStep = 0;
		StateSince = FPlatformTime::Seconds();
	}
	FString Who;
	for (const FJadgFighter& Fighter : Combat.Fighters())
	{
		if (Fighter.Id == TurnOf)
		{
			Who = Fighter.Name;
		}
	}
	switch (TurnStep++)
	{
	case 0:
	{
		FJadgPlan Plan;
		if (!Combat.PlanForActive(Plan))
		{
			Finish(1, TEXT("le tour du héros n'a pas de plan"));
			return;
		}
		++GHeroTurns;
		GMoveTo = Plan.MoveTo;
		GAction = Plan.Action;
		GTarget = Plan.TargetId;
		GRank = Plan.SpellRank;
		Note(FString::Printf(TEXT("round %d, tour de %s : %s"), TurnRound, *Who, *Plan.Summary));
		if (GMoveTo.IsSet())
		{
			// Le pointeur sur la destination : l'aperçu y trace le chemin.
			FVector2D Screen;
			if (Player->ProjectWorldLocationToScreen(GMoveTo.GetValue(), Screen))
			{
				Player->PointAt(Screen);
			}
			if (!GPreviewShot)
			{
				GPreviewShot = true;
				ResumeAt = Frames + 10;
				Shoot(FString::Printf(TEXT("l'aperçu du tour de %s : chemin, portée restante, cibles"), *Who));
			}
		}
		break;
	}
	case 1:
		if (GMoveTo.IsSet())
		{
			ClickPoint(GMoveTo.GetValue(), TEXT("la destination du tour"));
			ResumeAt = Frames + 6;
		}
		break;
	case 2:
		if (GAction == TEXT("attack") || GAction == TEXT("cast"))
		{
			AJadgWalker* Victim = Combat.WalkerOf(GTarget);
			if (GTarget == TurnOf || Victim == nullptr)
			{
				// Un sort sur soi : la cible est le lanceur.
				Combat.Select(GTarget);
				break;
			}
			ClickActor(Victim, TEXT("la cible"));
			ResumeAt = Frames + 6;
		}
		break;
	case 3:
		if (GAction == TEXT("attack"))
		{
			PressCommand(TEXT("Attack"));
			ResumeAt = Frames + 6;
		}
		else if (GAction == TEXT("cast"))
		{
			PressCommand(*FString::Printf(TEXT("Choice%d"), GRank));
			ResumeAt = Frames + 4;
		}
		break;
	case 4:
		if (GAction == TEXT("cast"))
		{
			PressCommand(TEXT("Capacity"));
			ResumeAt = Frames + 6;
		}
		break;
	default:
		if (!Combat.Refusal().IsEmpty())
		{
			Note(TEXT("refus : ") + Combat.Refusal());
		}
		PressCommand(TEXT("EndTurn"));
		ResumeAt = Frames + 6;
		TurnStep = 0;
		TurnOf = 0;
		break;
	}
}

void AJadgCombatWalkthrough::Finish(int32 ExitCode, const FString& Reason)
{
	if (bDone)
	{
		return;
	}
	bDone = true;
	if (ExitCode != 0)
	{
		Note(FString::Printf(TEXT("arrêt : %s"), *Reason));
		UE_LOG(LogJadg, Error, TEXT("[Parcours du combat] %s"), *Reason);
	}
	uint64 Seed = 1;
	FParse::Value(FCommandLine::Get(), TEXT("JadgSeed="), Seed);
	TArray<FString> Lines;
	for (const FString& Line : GJournal)
	{
		Lines.Add(Quote(Line));
	}
	FString Json = FString::Printf(TEXT("{\n  \"completed\": %s,\n  \"encounter\": \"%s\",\n  \"seed\": %llu,\n  \"outcome\": %s,\n  \"heroTurns\": %d,\n  \"captures\": %d,\n  \"candidates\": %s,\n  \"steps\": [\n    "),
		ExitCode == 0 ? TEXT("true") : TEXT("false"), Encounter, Seed, *Quote(GOutcome), GHeroTurns, GShots,
		GCandidates.IsEmpty() ? TEXT("null") : *GCandidates);
	Json += FString::Join(GSteps, TEXT(",\n    "));
	Json += TEXT("\n  ],\n  \"journal\": [\n    ");
	Json += FString::Join(Lines, TEXT(",\n    "));
	Json += TEXT("\n  ]\n}\n");
	const FString File = FPaths::Combine(OutputDir, TEXT("parcours.json"));
	FFileHelper::SaveStringToFile(Json, *File, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	UE_LOG(LogJadg, Display, TEXT("[Parcours du combat] %s"), *File);
	FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(ExitCode));
}
