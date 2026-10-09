// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgScreensTour.h"

#include "Combat/JadgCombat.h"
#include "Bridge/JadgOptions.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "Game/JadgExploration.h"
#include "HAL/FileManager.h"
#include "InputKeyEventArgs.h"
#include "JustAnotherRpgGame.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Player/JadgPlayerController.h"
#include "UI/JadgHud.h"
#include "UI/JadgScreens.h"
#include "UI/JadgTexts.h"
#include "UnrealClient.h"

namespace
{
	FViewport* GameViewport()
	{
		return GEngine->GameViewport != nullptr ? GEngine->GameViewport->Viewport : nullptr;
	}

	/// Le plus long qu'un geste attende son effet, en trames.
	constexpr int32 StallFrames = 600;
}

AJadgScreensTour::AJadgScreensTour()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bTickEvenWhenPaused = true;
	SetTickableWhenPaused(true);
}

AJadgHud* AJadgScreensTour::Hud() const
{
	return AJadgHud::Of(GetWorld());
}

void AJadgScreensTour::BeginPlay()
{
	Super::BeginPlay();
	FParse::Value(FCommandLine::Get(), TEXT("JadgEcrans="), OutputDir);
	IFileManager::Get().MakeDirectory(*OutputDir, true);
	Player = Cast<AJadgPlayerController>(GetWorld()->GetFirstPlayerController());
	Exploration = GetGameInstance()->GetSubsystem<UJadgExploration>();
	bHadOptions = FFileHelper::LoadFileToString(SavedOptions, *FJadgOptions::PlayerFile());
	FString Encounter;
	if (FParse::Value(FCommandLine::Get(), TEXT("JadgRencontre="), Encounter))
	{
		TourCombat();
	}
	else
	{
		TourScreens();
	}
}

void AJadgScreensTour::Then(const FString& Name, TFunction<bool()> Act)
{
	Steps.Add({Name, MoveTemp(Act)});
}

void AJadgScreensTour::Note(const FString& Line)
{
	Log.Add(Line);
	UE_LOG(LogJadg, Display, TEXT("[Écrans] %s"), *Line);
}

void AJadgScreensTour::GameKey(const FKey& Key)
{
	Player->InputKey(FInputKeyEventArgs(GameViewport(), FInputDeviceId::CreateFromInternalId(0), Key, IE_Pressed, 0));
	Held = Key;
}

void AJadgScreensTour::SlateKey(const FKey& Key)
{
	FSlateApplication& App = FSlateApplication::Get();
	const uint32* Code = nullptr;
	const uint32* Character = nullptr;
	FInputKeyManager::Get().GetCodesFromKey(Key, Code, Character);
	const FKeyEvent Event(Key, FModifierKeysState(), App.GetUserIndexForKeyboard(), false, Character != nullptr ? *Character : 0,
		Code != nullptr ? *Code : 0);
	App.ProcessKeyDownEvent(Event);
	App.ProcessKeyUpEvent(Event);
}

bool AJadgScreensTour::Click(UJadgButton* Button)
{
	if (Button == nullptr)
	{
		return false;
	}
	const FGeometry Geometry = Button->GetCachedGeometry();
	const FVector2D Size = Geometry.GetAbsoluteSize();
	if (Size.X <= 0.0f || Size.Y <= 0.0f)
	{
		return false;
	}
	const FVector2D Centre = Geometry.GetAbsolutePositionAtCoordinates(FVector2D(0.5f, 0.5f));
	FSlateApplication& App = FSlateApplication::Get();
	const TSet<FKey> None;
	const TSet<FKey> Left = {EKeys::LeftMouseButton};
	const uint32 User = FSlateApplicationBase::CursorUserIndex;
	const uint32 Pointer = FSlateApplicationBase::CursorPointerIndex;
	App.SetCursorPos(Centre);
	App.ProcessMouseMoveEvent(FPointerEvent(User, Pointer, Centre, Centre, None, EKeys::Invalid, 0.0f, FModifierKeysState()));
	App.ProcessMouseButtonDownEvent(nullptr, FPointerEvent(User, Pointer, Centre, Centre, Left, EKeys::LeftMouseButton, 0.0f, FModifierKeysState()));
	App.ProcessMouseButtonUpEvent(FPointerEvent(User, Pointer, Centre, Centre, None, EKeys::LeftMouseButton, 0.0f, FModifierKeysState()));
	return true;
}

UJadgButton* AJadgScreensTour::Find(const FString& LabelKey, int32 Rank) const
{
	const AJadgHud* Screens = Hud();
	UJadgScreen* Top = Screens != nullptr ? Screens->Top() : nullptr;
	if (Top == nullptr && Screens != nullptr)
	{
		Top = Screens->Find(EJadgScreen::Dialogue) != nullptr ? Screens->Find(EJadgScreen::Dialogue) : Screens->Find(EJadgScreen::Hud);
		Top = Top != nullptr ? Top : Screens->Find(EJadgScreen::Combat);
	}
	if (Top == nullptr)
	{
		return nullptr;
	}
	const FText Wanted = LabelKey.Contains(TEXT(".")) ? FJadgTexts::Get(LabelKey) : FText::FromString(LabelKey);
	int32 Seen = 0;
	for (UJadgButton* Button : Top->Buttons())
	{
		if (Button != nullptr && (Button->Label.EqualTo(Wanted) || (LabelKey.IsEmpty() && !Button->Label.IsEmpty())) && Seen++ == Rank)
		{
			return Button;
		}
	}
	return nullptr;
}

UJadgButton* AJadgScreensTour::Focused() const
{
	const AJadgHud* Screens = Hud();
	if (Screens == nullptr || Screens->Top() == nullptr)
	{
		return nullptr;
	}
	for (UJadgButton* Button : Screens->Top()->Buttons())
	{
		if (Button != nullptr && Button->HasKeyboardFocus())
		{
			return Button;
		}
	}
	return nullptr;
}

bool AJadgScreensTour::Shot(const FString& Name)
{
	const FString File = FPaths::Combine(OutputDir, Name + TEXT(".png"));
	if (PendingShot != File)
	{
		IFileManager::Get().Delete(*File);
		PendingShot = File;
		// L'interface comprise : les écrans d'UMG sont l'objet de la capture.
		FScreenshotRequest::RequestScreenshot(File, true, false);
		return false;
	}
	if (!FScreenshotRequest::IsScreenshotRequested() && FPaths::FileExists(File))
	{
		PendingShot.Reset();
		Shots.Add(Name + TEXT(".png"));
		Note(FString::Printf(TEXT("capture %s"), *Name));
		return true;
	}
	return false;
}

void AJadgScreensTour::Finish(int32 Code)
{
	// Le fichier d'options du poste est rendu tel qu'il était : le tour a changé la langue.
	if (bHadOptions)
	{
		FFileHelper::SaveStringToFile(SavedOptions, *FJadgOptions::PlayerFile(), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	}
	else
	{
		IFileManager::Get().Delete(*FJadgOptions::PlayerFile());
	}
	TSharedRef<FJsonObject> Report = MakeShared<FJsonObject>();
	Report->SetNumberField(TEXT("code"), Code);
	TArray<TSharedPtr<FJsonValue>> Lines;
	for (const FString& Line : Log)
	{
		Lines.Add(MakeShared<FJsonValueString>(Line));
	}
	Report->SetArrayField(TEXT("steps"), Lines);
	TArray<TSharedPtr<FJsonValue>> Files;
	for (const FString& File : Shots)
	{
		Files.Add(MakeShared<FJsonValueString>(File));
	}
	Report->SetArrayField(TEXT("captures"), Files);
	FString Text;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Text);
	FJsonSerializer::Serialize(Report, Writer);
	FFileHelper::SaveStringToFile(Text, *FPaths::Combine(OutputDir, TEXT("ecrans.json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	UE_LOG(LogJadg, Display, TEXT("[Écrans] fin du tour, code %d"), Code);
	FPlatformMisc::RequestExitWithStatus(false, static_cast<uint8>(Code));
	Steps.Reset();
}

void AJadgScreensTour::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	++Frames;
	if (Held.IsValid())
	{
		Player->InputKey(FInputKeyEventArgs(GameViewport(), FInputDeviceId::CreateFromInternalId(0), Held, IE_Released, 0));
		Held = FKey();
	}
	if (Wait > 0)
	{
		--Wait;
		return;
	}
	if (!Steps.IsValidIndex(Current))
	{
		if (!Steps.IsEmpty())
		{
			Finish(0);
		}
		return;
	}
	if (Steps[Current].Act())
	{
		++Current;
		StepFrames = 0;
		Wait = 6;
	}
	else if (++StepFrames > StallFrames)
	{
		Note(FString::Printf(TEXT("ÉCHEC : « %s » sans effet après %d trames"), *Steps[Current].Name, StallFrames));
		Finish(1);
	}
}

// --- Le tour des écrans -------------------------------------------------------------------------

void AJadgScreensTour::TourScreens()
{
	const auto Top = [this](EJadgScreen Kind)
	{
		return Hud() != nullptr && Hud()->Top() != nullptr && Hud()->Top()->Kind == Kind;
	};
	const auto Closed = [this] { return Hud() != nullptr && Hud()->Depth() == 0; };
	// Ouvre une page par la touche du jeu, la capture, déplace le focus au clavier, la ferme par Échap.
	const auto Page = [this, Top, Closed](const FString& Name, const FKey& Key, EJadgScreen Kind, TFunction<void()> Inside = nullptr)
	{
		Then(Name + TEXT(" : touche ") + Key.ToString(), [this, Key, Kind, Top]
		{
			if (StepFrames == 0)
			{
				GameKey(Key);
			}
			return Top(Kind);
		});
		Then(Name + TEXT(" : capture"), [this, Name] { return Shot(Name); });
		Then(Name + TEXT(" : le focus se déplace au clavier"), [this]
		{
			UJadgButton* Before = Focused();
			SlateKey(EKeys::Down);
			UJadgButton* After = Focused();
			Note(FString::Printf(TEXT("focus : « %s » puis « %s »"), Before != nullptr ? *Before->Label.ToString() : TEXT("—"),
				After != nullptr ? *After->Label.ToString() : TEXT("—")));
			return true;
		});
		if (Inside)
		{
			Inside();
		}
		Then(Name + TEXT(" : Échap ferme"), [this, Closed]
		{
			if (StepFrames == 0)
			{
				SlateKey(EKeys::Escape);
			}
			return Closed();
		});
	};

	Then(TEXT("la carte se pose"), [this] { return Frames > 120 && Hud() != nullptr; });
	Then(TEXT("midi"), [this]
	{
		FirstLeader = Exploration->Members()[0].Id;
		Exploration->SetMinutes(12.0f * 60.0f);
		return true;
	});
	Then(TEXT("hud : capture 12:00"), [this] { return Shot(TEXT("hud-1200")); });
	Then(TEXT("22 h"), [this]
	{
		Exploration->SetMinutes(22.0f * 60.0f);
		return true;
	});
	Then(TEXT("hud : capture 22:00"), [this] { return Shot(TEXT("hud-2200")); });
	Then(TEXT("midi encore"), [this]
	{
		Exploration->SetMinutes(12.0f * 60.0f);
		return true;
	});

	Page(TEXT("menu"), EKeys::Escape, EJadgScreen::Pause);

	// Le groupe : choisir le deuxième membre au clic, le faire meneur au clic.
	Page(TEXT("groupe"), EKeys::G, EJadgScreen::Party, [this]
	{
		Then(TEXT("groupe : clic sur le deuxième membre"), [this]
		{
			UJadgButton* Second = Find(TEXT("party.choose"), 1);
			const FString Wanted = Exploration->Members()[1].Id;
			if (StepFrames == 0 && !Click(Second))
			{
				return false;
			}
			const UJadgPartyScreen* Party = Cast<UJadgPartyScreen>(Hud()->Top());
			return Party != nullptr && Party->Chosen == Wanted;
		});
		Then(TEXT("groupe : clic sur Mener"), [this]
		{
			const FString Wanted = Cast<UJadgPartyScreen>(Hud()->Top())->Chosen;
			if (StepFrames == 0 && !Click(Find(TEXT("party.lead"))))
			{
				return false;
			}
			return Exploration->Members()[0].Id == Wanted;
		});
		Then(TEXT("groupe : capture du nouveau meneur"), [this] { return Shot(TEXT("groupe-meneur")); });
	});
	Then(TEXT("le premier meneur revient"), [this]
	{
		Exploration->SetLeader(FirstLeader);
		return true;
	});

	Page(TEXT("personnage"), EKeys::P, EJadgScreen::Character);
	Page(TEXT("equipement"), EKeys::I, EJadgScreen::Equipment);

	// Le dialogue : la mère, la parole passée au suivant par Tab, la réponse au clic.
	Then(TEXT("dialogue : la mère"), [this]
	{
		if (StepFrames == 0)
		{
			Exploration->TalkTo(TEXT("mere"));
		}
		return Hud()->Find(EJadgScreen::Dialogue) != nullptr;
	});
	Then(TEXT("dialogue : capture"), [this] { return Shot(TEXT("dialogue")); });
	Then(TEXT("dialogue : Tab donne la parole au suivant"), [this]
	{
		static FString Before;
		if (StepFrames == 0)
		{
			Before = Exploration->DialogueSpeaker();
			GameKey(EKeys::Tab);
		}
		return Exploration->DialogueSpeaker() != Before;
	});
	Then(TEXT("dialogue : capture de la voix"), [this] { return Shot(TEXT("dialogue-voix")); });
	Then(TEXT("dialogue : clic sur la première réponse"), [this]
	{
		static FString Before;
		if (StepFrames == 0)
		{
			Before = Exploration->Line();
			UJadgScreen* Talk = Hud()->Find(EJadgScreen::Dialogue);
			if (Talk == nullptr || Talk->Buttons().IsEmpty() || !Click(Talk->Buttons()[0]))
			{
				return false;
			}
		}
		return !Exploration->InDialogue() || Exploration->Line() != Before;
	});
	Then(TEXT("dialogue : jusqu'à la fin"), [this]
	{
		if (Exploration->InDialogue() && StepFrames % 20 == 0)
		{
			Exploration->Choose(0);
		}
		return !Exploration->InDialogue();
	});

	Page(TEXT("journal"), EKeys::J, EJadgScreen::Journal);

	// La carte : choisir un lieu au clic, l'ouvrir, remonter par Échap.
	Page(TEXT("carte"), EKeys::M, EJadgScreen::Map, [this]
	{
		Then(TEXT("carte : clic sur l'Empire central"), [this]
		{
			if (StepFrames == 0 && !Click(Find(TEXT("Central Empire"))))
			{
				return false;
			}
			const UJadgMapScreen* Map = Cast<UJadgMapScreen>(Hud()->Top());
			return Map != nullptr && Map->PlaceId == TEXT("central-empire");
		});
		Then(TEXT("carte : clic sur Ouvrir"), [this]
		{
			if (StepFrames == 0 && !Click(Find(TEXT("map.open"))))
			{
				return false;
			}
			const UJadgMapScreen* Map = Cast<UJadgMapScreen>(Hud()->Top());
			return Map != nullptr && Map->MapId == TEXT("central-empire");
		});
		Then(TEXT("carte : capture de la région"), [this] { return Shot(TEXT("carte-region")); });
		Then(TEXT("carte : Échap remonte au monde"), [this]
		{
			if (StepFrames == 0)
			{
				SlateKey(EKeys::Escape);
			}
			const UJadgMapScreen* Map = Cast<UJadgMapScreen>(Hud()->Top());
			return Map != nullptr && Map->MapId == TEXT("world");
		});
	});

	Page(TEXT("debogage"), EKeys::F9, EJadgScreen::Debug);

	// Les options : ouvertes du menu au clic, l'onglet des graphismes, puis l'anglais appliqué.
	Then(TEXT("options : le menu"), [this, Top]
	{
		if (StepFrames == 0)
		{
			GameKey(EKeys::Escape);
		}
		return Top(EJadgScreen::Pause);
	});
	Then(TEXT("options : clic sur Options"), [this, Top]
	{
		if (StepFrames == 0 && !Click(Find(TEXT("menu.options"))))
		{
			return false;
		}
		return Top(EJadgScreen::Options);
	});
	Then(TEXT("options : capture"), [this] { return Shot(TEXT("options")); });
	Then(TEXT("options : clic sur Graphismes"), [this] { return StepFrames > 0 || Click(Find(TEXT("options.tab.graphics"))); });
	Then(TEXT("options : capture des graphismes"), [this] { return Shot(TEXT("options-graphismes")); });
	Then(TEXT("options : clic sur Général"), [this] { return StepFrames > 0 || Click(Find(TEXT("options.tab.general"))); });
	Then(TEXT("options : la langue suivante au clic"), [this]
	{
		if (StepFrames == 0 && !Click(Find(TEXT("›"))))
		{
			return false;
		}
		const UJadgOptionsScreen* Options = Cast<UJadgOptionsScreen>(Hud()->Top());
		return Options != nullptr && Options->Language == TEXT("en");
	});
	Then(TEXT("options : clic sur Appliquer"), [this, Top]
	{
		if (StepFrames == 0 && !Click(Find(TEXT("options.apply"))))
		{
			return false;
		}
		return FJadgTexts::Language() == TEXT("en") && Top(EJadgScreen::Pause);
	});
	Then(TEXT("en anglais : capture du menu"), [this] { return Shot(TEXT("menu-en")); });
	Then(TEXT("en anglais : Échap"), [this, Closed]
	{
		if (StepFrames == 0)
		{
			SlateKey(EKeys::Escape);
		}
		return Closed();
	});
	Then(TEXT("en anglais : capture du HUD"), [this] { return Shot(TEXT("hud-en")); });
	Page(TEXT("personnage-en"), EKeys::P, EJadgScreen::Character);
	Then(TEXT("retour au français"), [this]
	{
		FJadgTexts::SetLanguage(TEXT("fr"));
		Hud()->RebuildScreens();
		return true;
	});

	// Le titre et la nouvelle partie (D-37), les fins.
	Then(TEXT("titre : ouvert"), [this, Top]
	{
		if (StepFrames == 0)
		{
			Hud()->Open(EJadgScreen::Title);
		}
		return Top(EJadgScreen::Title);
	});
	Then(TEXT("titre : capture"), [this] { return Shot(TEXT("titre")); });
	Then(TEXT("titre : clic sur Nouvelle partie"), [this, Top]
	{
		if (StepFrames == 0 && !Click(Find(TEXT("menu.new_game"))))
		{
			return false;
		}
		return Top(EJadgScreen::NewGame);
	});
	Then(TEXT("nouvelle partie : capture"), [this] { return Shot(TEXT("nouvelle-partie")); });
	Then(TEXT("nouvelle partie : tout se ferme"), [this, Closed]
	{
		Hud()->CloseAll();
		return Closed();
	});
	Then(TEXT("fin de la démo : ouverte"), [this, Top]
	{
		if (StepFrames == 0)
		{
			Hud()->Open(EJadgScreen::Ending, TEXT("parole"));
		}
		return Top(EJadgScreen::Ending);
	});
	Then(TEXT("fin de la démo : capture"), [this] { return Shot(TEXT("fin-demo")); });
	Then(TEXT("fin de la démo : Échap ne ramène pas au jeu"), [this, Top]
	{
		SlateKey(EKeys::Escape);
		return Top(EJadgScreen::Ending);
	});
	Then(TEXT("mort : ouverte"), [this, Top]
	{
		Hud()->CloseAll();
		Hud()->Open(EJadgScreen::Death);
		return Top(EJadgScreen::Death);
	});
	Then(TEXT("mort : capture"), [this] { return Shot(TEXT("mort")); });
	Then(TEXT("fin du tour"), [this]
	{
		Hud()->CloseAll();
		return true;
	});
}

void AJadgScreensTour::TourCombat()
{
	Then(TEXT("combat : le tour du joueur"), [this]
	{
		AJadgCombat* Fight = AJadgCombat::Find(GetWorld());
		return Fight != nullptr && Fight->IsMounted() && Fight->IsPlayerTurn() && Hud() != nullptr && Hud()->Find(EJadgScreen::Combat) != nullptr;
	});
	Then(TEXT("combat : figé"), [this]
	{
		AJadgCombat::Find(GetWorld())->SetPaused(true);
		Exploration->SetMinutes(12.0f * 60.0f);
		return true;
	});
	Then(TEXT("combat : capture"), [this] { return Shot(TEXT("combat")); });
	Then(TEXT("combat : clic sur Historique"), [this] { return StepFrames > 0 || Click(Find(TEXT("combat.history"))); });
	Then(TEXT("combat : capture de l'historique"), [this] { return Shot(TEXT("combat-historique")); });
}
