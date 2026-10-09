// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "UI/JadgHud.h"

#include "Blueprint/UserWidget.h"
#include "Combat/JadgCombat.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Game/JadgExploration.h"
#include "Game/JadgGameInstance.h"
#include "GameFramework/PlayerController.h"
#include "JustAnotherRpgGame.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "UI/JadgScreens.h"

namespace
{
	/// Les couches d'UMG : le jeu, la conversation, puis les pages.
	constexpr int32 GroundLayer = 0;
	constexpr int32 TalkLayer = 10;
	constexpr int32 PageLayer = 20;

	/// Vrai si le jeu est lancé par un automate : ni menu du titre, ni pause d'une page qu'il n'ouvre pas.
	bool LaunchedByAutomaton()
	{
		const TCHAR* Line = FCommandLine::Get();
		FString Ignored;
		for (const TCHAR* Flag : {TEXT("JadgCapture="), TEXT("JadgParcours="), TEXT("JadgParcoursCombat="), TEXT("JadgEcrans=")})
		{
			if (FParse::Value(Line, Flag, Ignored))
			{
				return true;
			}
		}
		return FParse::Param(Line, TEXT("JadgSansTitre"));
	}
}

AJadgHud::AJadgHud()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bTickEvenWhenPaused = true;
	SetTickableWhenPaused(true);
}

AJadgHud* AJadgHud::Of(const UWorld* World)
{
	const APlayerController* Player = World != nullptr ? World->GetFirstPlayerController() : nullptr;
	return Player != nullptr ? Cast<AJadgHud>(Player->GetHUD()) : nullptr;
}

void AJadgHud::BeginPlay()
{
	Super::BeginPlay();
	Ground = Create(EJadgScreen::Hud, FString(), GroundLayer);

	UJadgGameInstance* Instance = Cast<UJadgGameInstance>(GetGameInstance());
	if (Instance != nullptr && !Instance->bTitleShown && !LaunchedByAutomaton() && !GIsAutomationTesting)
	{
		Instance->bTitleShown = true;
		Open(EJadgScreen::Title);
	}
}

void AJadgHud::EndPlay(const EEndPlayReason::Type Reason)
{
	for (UJadgScreen* Screen : Stack)
	{
		Remove(Screen);
	}
	Stack.Reset();
	Remove(Talk);
	Remove(Ground);
	Talk = nullptr;
	Ground = nullptr;
	Super::EndPlay(Reason);
}

UJadgScreen* AJadgHud::Create(EJadgScreen Kind, const FString& Argument, int32 Layer)
{
	APlayerController* Player = GetOwningPlayerController();
	UClass* Class = JadgScreenClass(Kind);
	if (Player == nullptr || Class == nullptr)
	{
		return nullptr;
	}
	UJadgScreen* Screen = CreateWidget<UJadgScreen>(Player, Class);
	Screen->Kind = Kind;
	Screen->Argument = Argument;
	if (!Screen->IsModal())
	{
		Screen->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
	}
	Screen->AddToViewport(Layer);
	return Screen;
}

void AJadgHud::Remove(UJadgScreen* Screen)
{
	if (Screen != nullptr)
	{
		Screen->RemoveFromParent();
	}
}

UJadgScreen* AJadgHud::Open(EJadgScreen Kind, const FString& Argument)
{
	for (int32 Index = 0; Index < Stack.Num(); ++Index)
	{
		if (Stack[Index] != nullptr && Stack[Index]->Kind == Kind)
		{
			// Déjà ouverte : elle repasse en haut, avec son argument du moment.
			UJadgScreen* Known = Stack[Index];
			Stack.RemoveAt(Index);
			Remove(Known);
			break;
		}
	}
	UJadgScreen* Screen = Create(Kind, Argument, PageLayer + Stack.Num());
	if (Screen != nullptr)
	{
		Stack.Add(Screen);
		UE_LOG(LogJadg, Display, TEXT("[Écrans] ouvert : %s"), *UEnum::GetValueAsString(Kind));
	}
	ApplyInputMode();
	return Screen;
}

void AJadgHud::Toggle(EJadgScreen Kind)
{
	if (Top() != nullptr && Top()->Kind == Kind)
	{
		Close(Top());
	}
	else
	{
		Open(Kind);
	}
}

void AJadgHud::Close(UJadgScreen* Screen)
{
	const int32 Index = Stack.Find(Screen);
	if (Index == INDEX_NONE)
	{
		return;
	}
	while (Stack.Num() > Index)
	{
		UJadgScreen* Leaving = Stack.Pop();
		UE_LOG(LogJadg, Display, TEXT("[Écrans] fermé : %s"), *UEnum::GetValueAsString(Leaving->Kind));
		Remove(Leaving);
	}
	ApplyInputMode();
}

void AJadgHud::CloseAll()
{
	if (!Stack.IsEmpty())
	{
		Close(Stack[0]);
	}
}

UJadgScreen* AJadgHud::Top() const
{
	return Stack.IsEmpty() ? nullptr : Stack.Last().Get();
}

UJadgScreen* AJadgHud::Find(EJadgScreen Kind) const
{
	for (UJadgScreen* Screen : Stack)
	{
		if (Screen != nullptr && Screen->Kind == Kind)
		{
			return Screen;
		}
	}
	if (Talk != nullptr && Talk->Kind == Kind)
	{
		return Talk;
	}
	return Ground != nullptr && Ground->Kind == Kind ? Ground.Get() : nullptr;
}

void AJadgHud::RebuildScreens()
{
	TArray<TPair<EJadgScreen, FString>> Pages;
	for (UJadgScreen* Screen : Stack)
	{
		Pages.Emplace(Screen->Kind, Screen->Argument);
		Remove(Screen);
	}
	Stack.Reset();
	if (Ground != nullptr)
	{
		const EJadgScreen Kind = Ground->Kind;
		Remove(Ground);
		Ground = Create(Kind, FString(), GroundLayer);
	}
	if (Talk != nullptr)
	{
		Remove(Talk);
		Talk = Create(EJadgScreen::Dialogue, FString(), TalkLayer);
	}
	for (const TPair<EJadgScreen, FString>& Page : Pages)
	{
		if (UJadgScreen* Screen = Create(Page.Key, Page.Value, PageLayer + Stack.Num()))
		{
			Stack.Add(Screen);
		}
	}
	ApplyInputMode();
}

void AJadgHud::ApplyInputMode()
{
	APlayerController* Player = GetOwningPlayerController();
	if (Player == nullptr)
	{
		return;
	}
	if (UJadgScreen* Page = Top())
	{
		FInputModeUIOnly Mode;
		Mode.SetWidgetToFocus(Page->FirstFocus()->TakeWidget());
		Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
		Player->SetInputMode(Mode);
		UGameplayStatics::SetGamePaused(this, true);
	}
	else
	{
		FInputModeGameAndUI Mode;
		Mode.SetHideCursorDuringCapture(false);
		Player->SetInputMode(Mode);
		UGameplayStatics::SetGamePaused(this, false);
	}
}

void AJadgHud::StartNewGame(const FString& LeaderId)
{
	UJadgExploration* Exploration = GetGameInstance()->GetSubsystem<UJadgExploration>();
	Exploration->Restart();
	Exploration->SetLeader(LeaderId);
	CloseAll();
	// La carte du moteur se rouvre : la partie neuve y entre par l'entrée de la carte.
	UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this, false)));
}

void AJadgHud::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	UJadgExploration* Exploration = GetGameInstance() != nullptr ? GetGameInstance()->GetSubsystem<UJadgExploration>() : nullptr;
	if (Exploration == nullptr)
	{
		return;
	}

	// Le jeu : le combat dès qu'il est monté, le HUD d'exploration sinon.
	AJadgCombat* Fight = AJadgCombat::Find(GetWorld());
	const EJadgScreen Wanted = Fight != nullptr && Fight->IsMounted() ? EJadgScreen::Combat : EJadgScreen::Hud;
	if (Ground == nullptr || Ground->Kind != Wanted)
	{
		Remove(Ground);
		Ground = Create(Wanted, FString(), GroundLayer);
	}

	// La conversation, tant qu'elle est ouverte.
	if (Exploration->InDialogue() && Talk == nullptr)
	{
		Talk = Create(EJadgScreen::Dialogue, FString(), TalkLayer);
	}
	else if (!Exploration->InDialogue() && Talk != nullptr)
	{
		Remove(Talk);
		Talk = nullptr;
	}

	// Ce que le jeu demande : la fin qu'un dialogue a écrite, la mort du groupe.
	const FString Ending = Exploration->TakeEnding();
	if (!Ending.IsEmpty())
	{
		Open(EJadgScreen::Ending, Ending);
	}
	if (Fight != nullptr && Fight->IsMounted() && Fight->OutcomeCode() == 2 && !Fight->IsBusy() && !bDeathShown && !LaunchedByAutomaton())
	{
		bDeathShown = true;
		Open(EJadgScreen::Death);
	}
}
