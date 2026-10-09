// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Player/JadgPlayerController.h"

#include "Characters/JadgParty.h"
#include "Characters/JadgWalker.h"
#include "Combat/JadgCombat.h"
#include "Engine/GameInstance.h"
#include "Engine/LocalPlayer.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Game/JadgExploration.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"
#include "JustAnotherRpgGame.h"
#include "Player/JadgCameraPawn.h"
#include "Player/JadgControls.h"
#include "UI/JadgHud.h"

namespace
{
	const FName WalkCommand(TEXT("Walk"));
	const FName InteractCommand(TEXT("Interact"));
	const FName NextLeaderCommand(TEXT("NextLeader"));
	const FName RecenterCommand(TEXT("Recenter"));
	const FName LookCommand(TEXT("Look"));
	const FName LookTurnCommand(TEXT("LookTurn"));
	const FName LookTiltCommand(TEXT("LookTilt"));
	const FName TurnCommand(TEXT("Turn"));
	const FName TiltCommand(TEXT("Tilt"));
	const FName ZoomCommand(TEXT("Zoom"));
	const FName PanForwardCommand(TEXT("PanForward"));
	const FName PanRightCommand(TEXT("PanRight"));
	const FName AttackCommand(TEXT("Attack"));
	const FName CapacityCommand(TEXT("Capacity"));
	const FName EndTurnCommand(TEXT("EndTurn"));
	const FString ChoicePrefix(TEXT("Choice"));

	/// Les commandes qui ouvrent un écran (LOT-1020), et l'écran de chacune.
	const TMap<FName, EJadgScreen>& ScreenCommands()
	{
		static const TMap<FName, EJadgScreen> Table = {
			{TEXT("Menu"), EJadgScreen::Pause},
			{TEXT("Party"), EJadgScreen::Party},
			{TEXT("Sheet"), EJadgScreen::Character},
			{TEXT("Inventory"), EJadgScreen::Equipment},
			{TEXT("Journal"), EJadgScreen::Journal},
			{TEXT("Map"), EJadgScreen::Map},
			{TEXT("Debug"), EJadgScreen::Debug},
		};
		return Table;
	}
}

bool UJadgControls::IsAxis(FName Command)
{
	return Command == LookCommand || Command == LookTurnCommand || Command == LookTiltCommand || Command == TurnCommand
		|| Command == TiltCommand || Command == ZoomCommand || Command == PanForwardCommand || Command == PanRightCommand;
}

bool UJadgControls::IsKnown(FName Command)
{
	const FString Name = Command.ToString();
	const bool bChoice = Name.StartsWith(ChoicePrefix) && Name.Len() == ChoicePrefix.Len() + 1 && Name[ChoicePrefix.Len()] >= TEXT('1')
		&& Name[ChoicePrefix.Len()] <= TEXT('9');
	return bChoice || IsAxis(Command) || Command == WalkCommand || Command == InteractCommand || Command == NextLeaderCommand
		|| Command == RecenterCommand || Command == AttackCommand || Command == CapacityCommand || Command == EndTurnCommand
		|| ScreenCommands().Contains(Command);
}

FKey UJadgControls::KeyOf(FName Command)
{
	for (const FJadgBinding& Binding : GetDefault<UJadgControls>()->Bindings)
	{
		if (Binding.Command == Command)
		{
			return Binding.Key;
		}
	}
	return FKey();
}

FString UJadgControls::KeyLabel(FName Command)
{
	const FKey Key = KeyOf(Command);
	return Key.IsValid() ? Key.GetDisplayName(false).ToString() : FString();
}

AJadgPlayerController::AJadgPlayerController()
{
	bShowMouseCursor = true;
	bEnableClickEvents = false;
	bEnableMouseOverEvents = false;
}

void AJadgPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent);
	if (Input == nullptr)
	{
		UE_LOG(LogJadg, Error, TEXT("[Commandes] le composant d'entrée n'est pas celui d'Enhanced Input (Config/DefaultInput.ini)"));
		return;
	}
	Context = NewObject<UInputMappingContext>(this, TEXT("JadgControls"));
	for (const FJadgBinding& Binding : GetDefault<UJadgControls>()->Bindings)
	{
		if (Binding.Command.IsNone() || !Binding.Key.IsValid())
		{
			UE_LOG(LogJadg, Error, TEXT("[Commandes] touche refusée : commande « %s », touche « %s »"), *Binding.Command.ToString(),
				*Binding.Key.ToString());
			continue;
		}
		const bool bAxis = UJadgControls::IsAxis(Binding.Command);
		TObjectPtr<UInputAction>& Action = Actions.FindOrAdd(Binding.Command);
		if (Action == nullptr)
		{
			Action = NewObject<UInputAction>(this, Binding.Command);
			Action->ValueType = bAxis ? EInputActionValueType::Axis1D : EInputActionValueType::Boolean;
			if (bAxis)
			{
				Input->BindAction(Action, ETriggerEvent::Triggered, this, &AJadgPlayerController::OnAxis);
			}
			else
			{
				Input->BindAction(Action, ETriggerEvent::Started, this, &AJadgPlayerController::OnPressed);
			}
		}
		FEnhancedActionKeyMapping& Mapping = Context->MapKey(Action, Binding.Key);
		if (bAxis && Binding.Scale != 1.0f)
		{
			UInputModifierScalar* Scalar = NewObject<UInputModifierScalar>(Context);
			Scalar->Scalar = FVector(Binding.Scale);
			Mapping.Modifiers.Add(Scalar);
		}
	}
}

void AJadgPlayerController::BeginPlay()
{
	Super::BeginPlay();

	if (const ULocalPlayer* Local = GetLocalPlayer())
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>())
		{
			if (Context != nullptr)
			{
				Subsystem->AddMappingContext(Context, 0);
			}
		}
	}

	FInputModeGameAndUI Mode;
	Mode.SetHideCursorDuringCapture(false);
	SetInputMode(Mode);
}

void AJadgPlayerController::OnAxis(const FInputActionInstance& Instance)
{
	if (const UInputAction* Action = Instance.GetSourceAction())
	{
		Axes.FindOrAdd(Action->GetFName()) = Instance.GetValue().Get<float>();
	}
}

void AJadgPlayerController::OnPressed(const FInputActionInstance& Instance)
{
	if (const UInputAction* Action = Instance.GetSourceAction())
	{
		Press(Action->GetFName());
	}
}

float AJadgPlayerController::Axis(FName Command) const
{
	const float* Value = Axes.Find(Command);
	return Value != nullptr ? *Value : 0.0f;
}

void AJadgPlayerController::PlayerTick(float DeltaSeconds)
{
	// Les entrées de la trame se lisent dans l'appel hérité : les axes sont à jour ensuite.
	Axes.Reset();
	Super::PlayerTick(DeltaSeconds);

	AJadgCameraPawn* View = Cast<AJadgCameraPawn>(GetPawn());
	if (View == nullptr)
	{
		return;
	}

	float Turn = Axis(TurnCommand) * DeltaSeconds;
	float Tilt = Axis(TiltCommand) * DeltaSeconds;
	if (Axis(LookCommand) > 0.0f)
	{
		// La souris donne un déplacement, pas une vitesse : il ne se multiplie pas par la durée.
		Turn += Axis(LookTurnCommand);
		Tilt += Axis(LookTiltCommand);
	}
	if (Turn != 0.0f) { View->AddYaw(Turn); }
	if (Tilt != 0.0f) { View->AddPitch(Tilt); }

	const float Notches = Axis(ZoomCommand);
	if (Notches != 0.0f)
	{
		View->Zoom(FMath::Pow(GetDefault<UJadgControls>()->ZoomStep, Notches));
	}
	View->Pan(FVector2D(Axis(PanForwardCommand), Axis(PanRightCommand)) * DeltaSeconds);
}

void AJadgPlayerController::Press(FName Command)
{
	AJadgParty* Party = AJadgParty::Find(GetWorld());
	UJadgExploration* Exploration = GetGameInstance() != nullptr ? GetGameInstance()->GetSubsystem<UJadgExploration>() : nullptr;
	const bool bTalking = Exploration != nullptr && Exploration->InDialogue();

	const FString Name = Command.ToString();
	if (const EJadgScreen* Screen = ScreenCommands().Find(Command))
	{
		// Un écran s'ouvre de l'exploration comme du combat ; la même touche le referme.
		if (AJadgHud* Screens = Cast<AJadgHud>(GetHUD()))
		{
			Screens->Toggle(*Screen);
		}
		return;
	}
	AJadgCombat* Combat = AJadgCombat::Find(GetWorld());
	if (Combat != nullptr && Combat->IsMounted())
	{
		// En combat, les gestes vont au combat (LOT-1017) ; la caméra reste au joueur.
		if (Name.StartsWith(ChoicePrefix))
		{
			Combat->SelectCapacity(FCString::Atoi(*Name.RightChop(ChoicePrefix.Len())));
		}
		else if (Command == WalkCommand)
		{
			FHitResult Hit;
			if (PointerHit(Hit))
			{
				Combat->Click(Hit);
			}
		}
		else if (Command == AttackCommand)
		{
			Combat->Attack();
		}
		else if (Command == CapacityCommand)
		{
			Combat->Cast();
		}
		else if (Command == EndTurnCommand)
		{
			Combat->EndTurn();
		}
		else if (Command == RecenterCommand)
		{
			AJadgCameraPawn* View = Cast<AJadgCameraPawn>(GetPawn());
			AJadgWalker* Active = Combat->WalkerOf(Combat->ActiveId());
			if (View != nullptr && Active != nullptr)
			{
				View->Follow(Active);
			}
		}
		return;
	}
	if (Name.StartsWith(ChoicePrefix))
	{
		if (bTalking)
		{
			Exploration->Choose(FCString::Atoi(*Name.RightChop(ChoicePrefix.Len())) - 1);
		}
	}
	else if (Command == InteractCommand)
	{
		if (bTalking)
		{
			// Une réplique à une seule suite se passe de la touche d'interaction : « continuer ».
			if (Exploration->Choices().Num() == 1)
			{
				Exploration->Choose(0);
			}
		}
		else if (Party != nullptr)
		{
			Party->Interact();
		}
	}
	else if (Command == WalkCommand)
	{
		if (!bTalking)
		{
			OrderUnderCursor();
		}
	}
	else if (Command == NextLeaderCommand)
	{
		if (bTalking)
		{
			// En dialogue, la parole passe au suivant du groupe (D-28).
			Exploration->NextDialogueSpeaker(1);
		}
		else if (Party != nullptr)
		{
			Party->RotateLeader();
		}
	}
	else if (Command == RecenterCommand)
	{
		AJadgCameraPawn* View = Cast<AJadgCameraPawn>(GetPawn());
		if (View != nullptr && Party != nullptr && Party->Leader() != nullptr)
		{
			View->Follow(Party->Leader());
		}
	}
}

void AJadgPlayerController::PointAt(const FVector2D& ScreenPosition)
{
	Pointer = ScreenPosition;
}

bool AJadgPlayerController::PointerHit(FHitResult& OutHit) const
{
	return Pointer.IsSet() ? GetHitResultAtScreenPosition(Pointer.GetValue(), ECC_Visibility, true, OutHit)
						   : GetHitResultUnderCursor(ECC_Visibility, true, OutHit);
}

void AJadgPlayerController::OrderUnderCursor()
{
	AJadgParty* Party = AJadgParty::Find(GetWorld());
	FHitResult Hit;
	if (Party == nullptr || !PointerHit(Hit))
	{
		return;
	}
	if (Party->IsEntity(Hit.GetActor()))
	{
		Party->OrderInteract(Hit.GetActor());
	}
	else
	{
		Party->OrderWalk(Hit.ImpactPoint);
	}
}
