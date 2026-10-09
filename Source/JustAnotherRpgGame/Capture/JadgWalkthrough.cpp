// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgWalkthrough.h"

#include "Characters/JadgParty.h"
#include "Characters/JadgWalker.h"
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
#include "Player/JadgCameraPawn.h"
#include "Player/JadgControls.h"
#include "Player/JadgPlayerController.h"
#include "ShaderCompiler.h"
#include "UObject/Package.h"
#include "UnrealClient.h"

namespace
{
	const TCHAR* const Stalls = TEXT("essai/etals");
	const TCHAR* const Forecourt = TEXT("essai/parvis");
	const TCHAR* const QuestFlag = TEXT("quete.pommes");

	// Où se tiennent, sur les plans de `build_essai_maps.py`, ceux que le parcours sollicite.
	const FIntPoint MotherCell(3, 2);
	const FIntPoint MasterCell(12, 7);

	/// Trames laissées à la carte pour s'ouvrir : le maillage de navigation, les matières.
	constexpr int32 OpeningFrames = 90;
	/// Trames laissées à une réplique avant sa capture : le HUD l'a dessinée, l'image est posée.
	constexpr int32 LineFrames = 45;
	/// Au-delà, un geste resté sans suite arrête le parcours, en secondes.
	constexpr double StallSeconds = 45.0;
	/// Un clic au sol doit tomber à moins de cette distance du point visé, en centimètres.
	constexpr double ClickTolerance = 112.0;

	/// Ce qui survit au changement de carte : le parcours est un seul processus.
	TArray<FString> GSteps;
	int32 GShots = 0;
	bool GControlsDone = false;
	bool GEncounterDone = false;
	TWeakObjectPtr<AActor> GFirstLeader;
	TWeakObjectPtr<AActor> GLastLeader;

	FViewport* GameViewport()
	{
		return GEngine->GameViewport != nullptr ? GEngine->GameViewport->Viewport : nullptr;
	}
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
	Player = Cast<AJadgPlayerController>(GetWorld()->GetFirstPlayerController());
	View = Player != nullptr ? Cast<AJadgCameraPawn>(Player->GetPawn()) : nullptr;
	StateSince = FPlatformTime::Seconds();
	Note(FString::Printf(TEXT("carte du moteur %s"), *GetWorld()->GetOutermost()->GetName()));
}

void AJadgWalkthrough::Note(const FString& What) const
{
	const double Now = FPlatformTime::Seconds() - GStartTime;
	// Le texte entre dans du JSON : seuls la barre oblique inverse et le guillemet y sont protégés.
	const FString Quoted = What.Replace(TEXT("\\"), TEXT("\\\\")).Replace(TEXT("\""), TEXT("\\\""));
	GSteps.Add(FString::Printf(TEXT("{\"seconds\": %.1f, \"step\": \"%s\"}"), Now, *Quoted));
	UE_LOG(LogJadg, Display, TEXT("[Parcours] %.1f s : %s"), Now, *What);
}

// --- Les touches ------------------------------------------------------------------------------

void AJadgWalkthrough::Press(const FKey& Key, int32 ForFrames)
{
	Player->InputKey(FInputKeyEventArgs(GameViewport(), FInputDeviceId::CreateFromInternalId(0), Key, IE_Pressed, 0));
	FHeld& Added = Held.AddDefaulted_GetRef();
	Added.Key = Key;
	Added.Until = Frames + ForFrames;
}

void AJadgWalkthrough::Axis(const FKey& Key, float Delta)
{
	Player->InputKey(FInputKeyEventArgs(GameViewport(), FInputDeviceId::CreateFromInternalId(0), Key, Delta, 1.0f / 60.0f, 1, 0));
}

void AJadgWalkthrough::ReleaseDue()
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

bool AJadgWalkthrough::CommandKey(FName Command, int32 Rank, FKey& OutKey) const
{
	for (const FJadgBinding& Binding : GetDefault<UJadgControls>()->Bindings)
	{
		if (Binding.Command == Command && Rank-- == 0)
		{
			OutKey = Binding.Key;
			return true;
		}
	}
	return false;
}

bool AJadgWalkthrough::Expect(bool bHolds, const TCHAR* What)
{
	if (bHolds)
	{
		Note(FString::Printf(TEXT("commande : %s"), What));
	}
	else
	{
		Finish(1, FString::Printf(TEXT("commande sans effet : %s"), What));
	}
	return bHolds;
}

bool AJadgWalkthrough::TryControls(AJadgParty& Party)
{
	if (Frames < ResumeAt)
	{
		return true;
	}
	// Chaque pas presse la touche que le fichier donne à la commande, puis le suivant juge l'effet.
	const auto Hold = [this](const TCHAR* Command, int32 Rank, int32 ForFrames)
	{
		FKey Key;
		if (!CommandKey(Command, Rank, Key))
		{
			Finish(1, FString::Printf(TEXT("la commande %s n'a pas de touche de rang %d"), Command, Rank + 1));
			return;
		}
		Press(Key, ForFrames);
		ResumeAt = Frames + ForFrames + 6;
	};
	switch (ControlStep++)
	{
	case 0:
		Before = View->GetViewYaw();
		Hold(TEXT("Turn"), 0, 20);
		break;
	case 1:
		Expect(View->GetViewYaw() != Before, TEXT("tourner, première touche"));
		Before = View->GetViewYaw();
		Hold(TEXT("Turn"), 1, 20);
		break;
	case 2:
		Expect(View->GetViewYaw() != Before, TEXT("tourner, seconde touche"));
		Before = View->GetViewYaw();
		Taps = 0;
		Hold(TEXT("Look"), 0, 16);
		ResumeAt = Frames + 3;
		break;
	case 3:
		// La touche tenue, la souris bouge six trames de suite.
		Axis(EKeys::MouseX, 30.0f);
		if (++Taps < 6)
		{
			--ControlStep;
		}
		else
		{
			ResumeAt = Frames + 16;
		}
		break;
	case 4:
		Expect(View->GetViewYaw() != Before, TEXT("tourner à la souris, la touche tenue"));
		Before = View->GetViewYaw();
		Axis(EKeys::MouseX, 30.0f);
		ResumeAt = Frames + 4;
		break;
	case 5:
		Expect(View->GetViewYaw() == Before, TEXT("la souris seule ne tourne pas"));
		Before = View->GetViewPitch();
		Hold(TEXT("Tilt"), 0, 20);
		break;
	case 6:
		Expect(View->GetViewPitch() > Before, TEXT("incliner, vers le haut"));
		Before = View->GetViewPitch();
		Hold(TEXT("Tilt"), 1, 20);
		break;
	case 7:
		Expect(View->GetViewPitch() < Before, TEXT("incliner, vers le bas"));
		Before = View->GetViewDistance();
		Axis(EKeys::MouseWheelAxis, 2.0f);
		ResumeAt = Frames + 6;
		break;
	case 8:
		Expect(View->GetViewDistance() < Before, TEXT("la molette rapproche"));
		Before = View->GetViewDistance();
		Axis(EKeys::MouseWheelAxis, -2.0f);
		ResumeAt = Frames + 6;
		break;
	case 9:
		Expect(View->GetViewDistance() > Before, TEXT("la molette éloigne"));
		GFirstLeader = Party.Leader();
		GLastLeader = Party.Leader();
		Taps = 0;
		Hold(TEXT("NextLeader"), 0, 2);
		break;
	case 10:
		// Quatre appuis font le tour du groupe (EX-EXP-014).
		if (!Expect(Party.Leader() != GLastLeader.Get(), TEXT("passer la main")))
		{
			break;
		}
		GLastLeader = Party.Leader();
		if (++Taps < 4)
		{
			--ControlStep;
			Hold(TEXT("NextLeader"), 0, 2);
		}
		break;
	case 11:
		Expect(Party.Leader() == GFirstLeader.Get(), TEXT("quatre appuis font le tour du groupe"));
		Hold(TEXT("PanForward"), 0, 15);
		break;
	case 12:
		Expect(View->GetFollowed() == nullptr, TEXT("déplacer le point visé détache la caméra"));
		Hold(TEXT("Recenter"), 0, 2);
		break;
	case 13:
		Expect(View->GetFollowed() == Party.Leader(), TEXT("recentrer ramène la caméra sur le meneur"));
		ResumeAt = Frames + 30;
		break;
	default:
		GControlsDone = true;
		StateSince = FPlatformTime::Seconds();
		return false;
	}
	return true;
}

// --- Les clics --------------------------------------------------------------------------------

bool AJadgWalkthrough::ClickGround(AJadgParty& Party, const FVector2D& Cell, const TCHAR* Where)
{
	const FVector Wanted = Party.PointOf(Cell);
	FVector2D Screen;
	FHitResult Hit;
	if (!Player->ProjectWorldLocationToScreen(Wanted, Screen))
	{
		Finish(1, FString::Printf(TEXT("%s n'est pas devant la caméra"), Where));
		return false;
	}
	Player->PointAt(Screen);
	if (!Player->PointerHit(Hit) || FVector::Dist2D(Hit.ImpactPoint, Wanted) > ClickTolerance || Party.IsEntity(Hit.GetActor()))
	{
		Finish(1, FString::Printf(TEXT("le pointeur en (%.0f ; %.0f) ne désigne pas %s"), Screen.X, Screen.Y, Where));
		return false;
	}
	Note(FString::Printf(TEXT("clic au sol en (%.0f ; %.0f) : %s"), Screen.X, Screen.Y, Where));
	Press(UJadgControls::KeyOf(TEXT("Walk")));
	return true;
}

bool AJadgWalkthrough::ClickEntity(AJadgParty& Party, const FString& EntityId, const TCHAR* Who)
{
	const AActor* Target = Party.EntityActor(EntityId);
	if (Target == nullptr)
	{
		Finish(1, FString::Printf(TEXT("%s (%s) n'est pas sur la carte"), Who, *EntityId));
		return false;
	}
	FVector Origin;
	FVector Extent;
	Target->GetActorBounds(true, Origin, Extent);
	FVector2D Screen;
	FHitResult Hit;
	if (!Player->ProjectWorldLocationToScreen(Origin, Screen))
	{
		Finish(1, FString::Printf(TEXT("%s n'est pas devant la caméra"), Who));
		return false;
	}
	Player->PointAt(Screen);
	if (!Player->PointerHit(Hit) || Hit.GetActor() != Target)
	{
		Finish(1, FString::Printf(TEXT("le pointeur en (%.0f ; %.0f) ne désigne pas %s"), Screen.X, Screen.Y, Who));
		return false;
	}
	Note(FString::Printf(TEXT("clic en (%.0f ; %.0f) sur %s"), Screen.X, Screen.Y, Who));
	Press(UJadgControls::KeyOf(TEXT("Walk")));
	return true;
}

FString AJadgWalkthrough::EntityAt(const TCHAR* Type, const FIntPoint* Cell) const
{
	for (const FJadgEntity& Entity : Exploration->Entities())
	{
		if (Entity.Type == Type && (Cell == nullptr || Entity.Cell == *Cell))
		{
			return Entity.Id;
		}
	}
	return FString();
}

void AJadgWalkthrough::Shoot(const FString& What)
{
	PendingFile = FPaths::Combine(OutputDir, FString::Printf(TEXT("parcours-%02d.png"), ++GShots));
	IFileManager::Get().Delete(*PendingFile, false, true, true);
	FScreenshotRequest::RequestScreenshot(PendingFile, false, false);
	Note(FString::Printf(TEXT("capture %02d : %s"), GShots, *What));
}

bool AJadgWalkthrough::ShotWritten() const
{
	return !FScreenshotRequest::IsScreenshotRequested() && FPaths::FileExists(PendingFile);
}

// --- Le parcours ------------------------------------------------------------------------------

void AJadgWalkthrough::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	AJadgParty* Party = AJadgParty::Find(GetWorld());
	const bool bCompiling = GShaderCompilingManager != nullptr && GShaderCompilingManager->IsCompiling();
	if (Player != nullptr)
	{
		ReleaseDue();
	}
	if (bDone || ++Frames < OpeningFrames || bCompiling)
	{
		return;
	}
	if (Exploration == nullptr || Party == nullptr || Party->Leader() == nullptr || Player == nullptr || View == nullptr)
	{
		Finish(1, TEXT("il manque l'exploration, le groupe, son meneur, le contrôleur du joueur ou sa caméra"));
		return;
	}
	if (Frames < ResumeAt)
	{
		return;
	}

	if (!Exploration->Encounter().IsEmpty())
	{
		// La quête des pommes ne combat pas : le combat a son parcours (LOT-1017).
		Finish(1, FString::Printf(TEXT("une rencontre s'est engagée : %s"), *Exploration->Encounter()));
		return;
	}
	if (!GControlsDone)
	{
		TryControls(*Party);
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
	const bool bChestOpen = Map == Stalls && Exploration->IsConsumed(EntityAt(TEXT("chest"), nullptr));
	const FString Now = FString::Printf(TEXT("%s|%s|%d|%d"), *Map, *Quest, bChestOpen ? 1 : 0, GEncounterDone ? 1 : 0);
	if (Now != Ordered)
	{
		Ordered = Now;
		StateSince = FPlatformTime::Seconds();
		Order(*Party, Map, Quest);
	}
	else if (FPlatformTime::Seconds() - StateSince > StallSeconds)
	{
		Finish(1, FString::Printf(TEXT("sans suite depuis %.0f s : %s"), StallSeconds, *Now));
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
			Shoot(TEXT("à portée de la mère, l'invite et le contour"));
		}
		else if (ShotWritten())
		{
			bApproaching = false;
			Note(TEXT("touche : interagir"));
			Press(UJadgControls::KeyOf(TEXT("Interact")));
		}
	}
}

void AJadgWalkthrough::Order(AJadgParty& Party, const FString& Map, const FString& Quest)
{
	const auto WalkTo = [&](double Column, double Row, const TCHAR* Where)
	{
		Note(FString::Printf(TEXT("ordre au groupe : marcher vers %s"), Where));
		Party.OrderWalk(Party.PointOf(FVector2D(Column, Row)));
	};

	if (Map == Stalls && Quest == TEXT("inconnue"))
	{
		// La mère est en (3, 2) : le meneur se poste à l'est, sur la case voisine.
		bApproaching = ClickGround(Party, FVector2D(4.5, 2.5), TEXT("le côté de la mère"));
	}
	else if (Map == Stalls && Quest == TEXT("acceptee") && !Exploration->IsConsumed(EntityAt(TEXT("chest"), nullptr)))
	{
		ClickEntity(Party, EntityAt(TEXT("chest"), nullptr), TEXT("le coffre"));
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
	else if (Map == Forecourt && Quest == TEXT("enfant-libere") && !GEncounterDone)
	{
		ClickEntity(Party, EntityAt(TEXT("npc"), &MasterCell), TEXT("le maître d'arène"));
	}
	else if (Map == Forecourt && Quest == TEXT("enfant-libere"))
	{
		WalkTo(0.5, 5.5, TEXT("le portail de l'ouest"));
	}
	else if (Map == Stalls && Quest == TEXT("enfant-libere"))
	{
		ClickEntity(Party, EntityAt(TEXT("npc"), &MotherCell), TEXT("la mère"));
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
		Shoot(FString::Printf(TEXT("%s : « %s »"), *Exploration->Speaker(), *Line));
		if (!Exploration->LastCheck().IsEmpty())
		{
			Note(Exploration->LastCheck());
		}
		return;
	}
	if (!ShotWritten())
	{
		if (++FramesInLine > LineFrames + 600)
		{
			Finish(1, FString::Printf(TEXT("%s n'a pas été écrit"), *PendingFile));
		}
		return;
	}
	FramesInLine = 0;

	// La réponse se donne au clavier : son rang, ou la touche d'interaction pour « continuer ».
	const TArray<FJadgChoice> Offered = Exploration->Choices();
	// Au maître d'arène, « attendre » : le combat a son parcours (`AJadgCombatWalkthrough`, LOT-1017).
	for (const TCHAR* Wanted : {TEXT("accepter"), TEXT("convaincre"), TEXT("sourire"), TEXT("attendre"), TEXT("continue")})
	{
		const int32 Rank = Offered.IndexOfByPredicate([Wanted](const FJadgChoice& Choice) { return Choice.Id == Wanted; });
		if (Rank == INDEX_NONE)
		{
			continue;
		}
		const bool bContinue = FCString::Strcmp(Wanted, TEXT("continue")) == 0;
		const FName Command = bContinue ? FName(TEXT("Interact")) : FName(*FString::Printf(TEXT("Choice%d"), Rank + 1));
		const FKey Key = UJadgControls::KeyOf(Command);
		if (!Key.IsValid())
		{
			Finish(1, FString::Printf(TEXT("la commande %s n'a pas de touche"), *Command.ToString()));
			return;
		}
		Note(FString::Printf(TEXT("touche %s : %s"), *Key.GetDisplayName(false).ToString(), Wanted));
		Press(Key);
		if (FCString::Strcmp(Wanted, TEXT("attendre")) == 0)
		{
			GEncounterDone = true;
		}
		// La touche se lit à la trame suivante : la réplique aura changé d'ici là.
		ResumeAt = Frames + 8;
		return;
	}
	Finish(1, FString::Printf(TEXT("aucune réponse du parcours à « %s » (quête %s)"), *Line, *Exploration->Flag(QuestFlag)));
}

void AJadgWalkthrough::Finish(int32 ExitCode, const FString& Reason)
{
	if (bDone)
	{
		return;
	}
	bDone = true;
	if (ExitCode != 0)
	{
		Note(FString::Printf(TEXT("arrêt : %s"), *Reason));
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
