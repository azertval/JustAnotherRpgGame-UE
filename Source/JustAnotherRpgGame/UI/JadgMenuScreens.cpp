// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Les menus : le titre, le menu du mercenaire, les options, les fins, le débogage (LOT-1020).

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Data/GameOptions.h"

#include "Bridge/JadgOptions.h"
#include "Bridge/JadgPaths.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/HorizontalBox.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Engine/World.h"
#include "Game/JadgExploration.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "UI/JadgHud.h"
#include "UI/JadgScreens.h"
#include "UI/JadgStyle.h"
#include "UI/JadgTexts.h"

namespace
{
	FText Key(const TCHAR* Name)
	{
		return FJadgTexts::Get(Name);
	}

	void Quit(UJadgScreen* Screen)
	{
		UKismetSystemLibrary::QuitGame(Screen, Screen->GetOwningPlayer(), EQuitPreference::Quit, false);
	}

	/// Le fond d'un menu : une scène peinte du kit, en plein écran ; un aplat sombre sans le kit.
	void Backdrop(FJadgUi& Ui, UCanvasPanel* Root, const FString& KitPath)
	{
		FJadgUi::Fill(Root, Ui.Flat(TEXT("panel")));
		FJadgUi::Fill(Root, Ui.Icon(KitPath, FVector2D(1920.0f, 1080.0f)));
	}

	/// Une colonne d'entrées de menu (`button/menu`), chacune son icône du kit.
	UVerticalBox* MenuColumn(FJadgUi& Ui, const TArray<TTuple<const TCHAR*, FString, TFunction<void()>>>& Entries)
	{
		UVerticalBox* Column = Ui.Column();
		for (const TTuple<const TCHAR*, FString, TFunction<void()>>& Entry : Entries)
		{
			UHorizontalBox* Line = Ui.Row();
			FJadgUi::Add(Line, Ui.Icon(Entry.Get<1>(), FVector2D(52.0f, 52.0f)), FMargin(0.0f, 0.0f, 10.0f, 0.0f));
			FJadgUi::Add(Line, Ui.Sized(Ui.Button(TEXT("button/menu"), FJadgTexts::Get(Entry.Get<0>()), Entry.Get<2>(), TEXT("textOnPanel"), true,
										   TEXT("section")),
								   420.0f, 72.0f));
			FJadgUi::Add(Column, Line, FMargin(0.0f, 6.0f));
		}
		return Column;
	}
}

// --- Le titre -----------------------------------------------------------------------------------

void UJadgTitleScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	Backdrop(Ui, Root, TEXT("background/menu-scene"));
	UOverlay* Logo = Ui.Layers();
	FJadgUi::Add(Logo, Ui.Image(TEXT("plate/logo"), NAME_None, FVector2D(640.0f, 400.0f)));
	FJadgUi::Add(Logo, Ui.Text(Key(TEXT("menu.title")), TEXT("display"), TEXT("display"), TEXT("goldLight"), true, ETextJustify::Center), HAlign_Center,
		VAlign_Center, FMargin(90.0f, 0.0f));
	FJadgUi::Place(Root, Ui.Sized(Logo, 640.0f, 400.0f), FVector2D(110.0f, 40.0f));
	UVerticalBox* Entries = MenuColumn(Ui, {
		MakeTuple(TEXT("menu.continue"), FString(TEXT("icon/menu/continue")), TFunction<void()>([this] { Close(); })),
		MakeTuple(TEXT("menu.new_game"), FString(TEXT("icon/menu/new-game")), TFunction<void()>([this]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->Open(EJadgScreen::NewGame);
			}
		})),
		MakeTuple(TEXT("menu.options"), FString(TEXT("icon/menu/options")), TFunction<void()>([this]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->Open(EJadgScreen::Options);
			}
		})),
		MakeTuple(TEXT("menu.quit"), FString(TEXT("icon/menu/quit")), TFunction<void()>([this] { Quit(this); })),
	});
	FJadgUi::Place(Root, Entries, FVector2D(150.0f, 470.0f));
	UTextBlock* Motto = Ui.Text(Key(TEXT("menu.motto")), TEXT("lore"), TEXT("section"), TEXT("textOnPanel"), false, ETextJustify::Center);
	FJadgUi::Place(Root, Ui.Piece(TEXT("plate/quote"), Motto, FMargin(64.0f, 10.0f)), FVector2D(0.0f, -40.0f), FVector2D::ZeroVector,
		FVector2D(0.5f, 1.0f), FVector2D(0.5f, 1.0f));
	UTextBlock* Version = Ui.Text(FText::FromString(TEXT(JADG_VERSION)), TEXT("body"), TEXT("caption"), TEXT("textOnPanelMuted"));
	FJadgUi::Place(Root, Version, FVector2D(-24.0f, -16.0f), FVector2D::ZeroVector, FVector2D(1.0f, 1.0f), FVector2D(1.0f, 1.0f));
}

// --- Le menu du mercenaire ----------------------------------------------------------------------

void UJadgPauseScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	FJadgUi::Fill(Root, Ui.Flat(TEXT("scrim")));
	UVerticalBox* Column = Ui.Column();
	UTextBlock* Heading = Ui.Text(Key(TEXT("menu.pause")), TEXT("display"), TEXT("screenTitle"), TEXT("textOnPanel"), false, ETextJustify::Center);
	FJadgUi::Add(Column, Ui.Piece(TEXT("plate/title-garnet"), Heading, FMargin(160.0f, 22.0f)), FMargin(0.0f, 0.0f, 0.0f, 24.0f), 0.0f, HAlign_Center);
	UVerticalBox* Entries = MenuColumn(Ui, {
		MakeTuple(TEXT("menu.resume"), FString(TEXT("icon/menu/continue")), TFunction<void()>([this] { Close(); })),
		MakeTuple(TEXT("menu.options"), FString(TEXT("icon/menu/options")), TFunction<void()>([this]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->Open(EJadgScreen::Options);
			}
		})),
		MakeTuple(TEXT("menu.to_title"), FString(TEXT("icon/menu/load-game")), TFunction<void()>([this]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->CloseAll();
				Manager->Open(EJadgScreen::Title);
			}
		})),
		MakeTuple(TEXT("menu.quit"), FString(TEXT("icon/menu/quit")), TFunction<void()>([this] { Quit(this); })),
	});
	FJadgUi::Add(Column, Entries, FMargin(0.0f), 0.0f, HAlign_Center);
	FJadgUi::Place(Root, Ui.Piece(TEXT("frame/panel-dark"), Column, FMargin(90.0f, 70.0f)), FVector2D::ZeroVector, FVector2D::ZeroVector,
		FVector2D(0.5f, 0.5f), FVector2D(0.5f, 0.5f));
}

// --- Les options --------------------------------------------------------------------------------

void UJadgOptionsScreen::Load(bool bFactory)
{
	core::GameOptions Read;
	if (bFactory)
	{
		Read = core::GameOptions();
		const core::GameOptionsResult Factory = core::loadGameOptions(FJadgPaths::ToPath(FJadgOptions::FactoryFile()));
		Read = Factory.options;
	}
	else
	{
		FJadgOptions::Read(Read);
	}
	Width = Read.width;
	Height = Read.height;
	bFullscreen = Read.fullscreen;
	RenderScale = Read.renderScalePercent;
	Shadows = Read.shadowQuality;
	Volume = Read.volumePercent;
	Language = bFactory ? FJadgPaths::ToFString(Read.language) : FJadgTexts::Language();
}

void UJadgOptionsScreen::Apply()
{
	core::GameOptions Options;
	FJadgOptions::Read(Options);
	Options.width = Width;
	Options.height = Height;
	Options.fullscreen = bFullscreen;
	Options.renderScalePercent = RenderScale;
	Options.shadowQuality = Shadows;
	Options.volumePercent = Volume;
	Options.language = TCHAR_TO_UTF8(*Language);
	FJadgOptions::Apply(Options);
	FJadgOptions::Save(Options);
	if (Language != FJadgTexts::Language())
	{
		FJadgTexts::SetLanguage(Language);
		if (AJadgHud* Manager = Hud())
		{
			Manager->RebuildScreens();
		}
	}
}

void UJadgOptionsScreen::ShowValues()
{
	const auto Set = [this](const TCHAR* Name, const FText& Value)
	{
		if (const TObjectPtr<UTextBlock>* Found = Values.Find(Name))
		{
			(*Found)->SetText(Value);
		}
	};
	Set(TEXT("language"), Key(*(TEXT("options.language.") + Language)));
	Set(TEXT("resolution"), FText::FromString(FString::Printf(TEXT("%d × %d"), Width, Height)));
	Set(TEXT("fullscreen"), Key(bFullscreen ? TEXT("options.yes") : TEXT("options.no")));
	Set(TEXT("render"), FText::FromString(FString::Printf(TEXT("%d %%"), RenderScale)));
	Set(TEXT("shadows"), FText::AsNumber(Shadows));
	Set(TEXT("volume"), FText::FromString(FString::Printf(TEXT("%d %%"), Volume)));
}

void UJadgOptionsScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	Load(false);
	Backdrop(Ui, Root, TEXT("background/options-backdrop"));

	// À gauche : le titre et les onglets.
	UVerticalBox* Side = Ui.Column();
	UTextBlock* Heading = Ui.Text(Key(TEXT("menu.options")), TEXT("display"), TEXT("screenTitle"), TEXT("textOnPanel"), false, ETextJustify::Center);
	FJadgUi::Add(Side, Ui.Piece(TEXT("plate/title-garnet"), Heading, FMargin(160.0f, 22.0f)), FMargin(0.0f, 0.0f, 0.0f, 30.0f));
	UCanvasPanel* Pages = Ui.Canvas();
	const TArray<TPair<const TCHAR*, FString>> Names = {
		{TEXT("options.tab.general"), TEXT("icon/options-tab/general")},
		{TEXT("options.tab.graphics"), TEXT("icon/options-tab/graphics")},
		{TEXT("options.tab.audio"), TEXT("icon/options-tab/audio")},
	};
	for (int32 Index = 0; Index < Names.Num(); ++Index)
	{
		UHorizontalBox* Line = Ui.Row();
		FJadgUi::Add(Line, Ui.Icon(Names[Index].Value, FVector2D(48.0f, 48.0f)), FMargin(0.0f, 0.0f, 8.0f, 0.0f));
		FJadgUi::Add(Line, Ui.Sized(Ui.Button(TEXT("button/menu"), Key(Names[Index].Key), [this, Index]
		{
			for (int32 Other = 0; Other < Tabs.Num(); ++Other)
			{
				Tabs[Other]->SetVisibility(Other == Index ? ESlateVisibility::SelfHitTestInvisible : ESlateVisibility::Collapsed);
			}
		}, TEXT("textOnPanel"), true, TEXT("section")), 340.0f, 72.0f));
		FJadgUi::Add(Side, Line, FMargin(0.0f, 6.0f));
	}
	FJadgUi::Place(Root, Ui.Piece(TEXT("frame/panel-dark"), Side, FMargin(40.0f, 40.0f)), FVector2D(130.0f, 120.0f), FVector2D(470.0f, 820.0f));

	// Une ligne de réglage : son libellé, sa valeur, et ses deux gestes.
	const auto Setting = [this, &Ui](UVerticalBox* Into, const TCHAR* Label, FName Name, TFunction<void(int32)> Step)
	{
		UHorizontalBox* Line = Ui.Row();
		FJadgUi::Add(Line, Ui.Text(Key(Label), TEXT("body"), TEXT("body"), TEXT("textOnPanel")), FMargin(0.0f), 1.0f);
		const auto Arrow = [this, &Ui, Step](const TCHAR* Glyph, int32 Delta)
		{
			return Ui.Sized(Ui.Button(TEXT("button/round"), FText::FromString(Glyph), [this, Step, Delta]
			{
				Step(Delta);
				ShowValues();
			}, TEXT("goldLight"), true, TEXT("section")), 52.0f, 52.0f);
		};
		FJadgUi::Add(Line, Arrow(TEXT("‹"), -1));
		UTextBlock* Value = Ui.Text(FText::GetEmpty(), TEXT("label"), TEXT("body"), TEXT("textOnPanel"), false, ETextJustify::Center);
		Values.Add(Name, Value);
		FJadgUi::Add(Line, Ui.Sized(Ui.Piece(TEXT("control/combo"), Value, FMargin(18.0f, 8.0f, 50.0f, 8.0f), TEXT("normal")), 260.0f, 48.0f),
			FMargin(8.0f, 0.0f));
		FJadgUi::Add(Line, Arrow(TEXT("›"), 1));
		FJadgUi::Add(Into, Line, FMargin(0.0f, 10.0f));
	};
	const auto Tab = [&](const TCHAR* SectionKey)
	{
		UVerticalBox* Column = Ui.Column();
		FJadgUi::Add(Column, Section(Ui, Key(SectionKey), false), FMargin(0.0f, 0.0f, 0.0f, 16.0f), 0.0f, HAlign_Left);
		FJadgUi::Fill(Pages, Column);
		Tabs.Add(Column);
		return Column;
	};
	UVerticalBox* General = Tab(TEXT("options.section.language"));
	Setting(General, TEXT("options.language"), TEXT("language"), [this](int32 Delta)
	{
		const TArray<FString>& Codes = FJadgTexts::Languages();
		const int32 Here = FMath::Max(0, Codes.Find(Language));
		Language = Codes.IsEmpty() ? Language : Codes[(Here + Delta + Codes.Num()) % Codes.Num()];
	});
	UVerticalBox* Graphics = Tab(TEXT("options.section.display"));
	Setting(Graphics, TEXT("options.resolution"), TEXT("resolution"), [this](int32 Delta)
	{
		static const TArray<FIntPoint> Sizes = {{1280, 720}, {1600, 900}, {1920, 1080}, {2560, 1440}, {3840, 2160}};
		int32 Here = Sizes.IndexOfByKey(FIntPoint(Width, Height));
		Here = FMath::Clamp(Here == INDEX_NONE ? 2 : Here + Delta, 0, Sizes.Num() - 1);
		Width = Sizes[Here].X;
		Height = Sizes[Here].Y;
	});
	Setting(Graphics, TEXT("options.fullscreen"), TEXT("fullscreen"), [this](int32) { bFullscreen = !bFullscreen; });
	Setting(Graphics, TEXT("options.render_scale"), TEXT("render"), [this](int32 Delta) { RenderScale = FMath::Clamp(RenderScale + Delta * 25, 50, 200); });
	Setting(Graphics, TEXT("options.shadows"), TEXT("shadows"), [this](int32 Delta) { Shadows = FMath::Clamp(Shadows + Delta, 0, 4); });
	UVerticalBox* Audio = Tab(TEXT("options.section.audio"));
	Setting(Audio, TEXT("options.volume"), TEXT("volume"), [this](int32 Delta) { Volume = FMath::Clamp(Volume + Delta * 10, 0, 100); });
	for (int32 Index = 1; Index < Tabs.Num(); ++Index)
	{
		Tabs[Index]->SetVisibility(ESlateVisibility::Collapsed);
	}

	// À droite : la page, et au pied par défaut, annuler, appliquer.
	UVerticalBox* Body = Ui.Column();
	FJadgUi::Add(Body, Pages, FMargin(0.0f), 1.0f);
	UHorizontalBox* Foot = Ui.Row();
	FJadgUi::Add(Foot, Ui.Sized(Ui.Button(TEXT("button/primary"), Key(TEXT("options.defaults")), [this]
	{
		Load(true);
		ShowValues();
	}), 280.0f, 56.0f));
	FJadgUi::Add(Foot, Ui.Sized(nullptr, 1.0f, 1.0f), FMargin(0.0f), 1.0f);
	FJadgUi::Add(Foot, Ui.Sized(Ui.Button(TEXT("button/cancel"), Key(TEXT("options.cancel")), [this] { Close(); }), 280.0f, 56.0f),
		FMargin(12.0f, 0.0f));
	FJadgUi::Add(Foot, Ui.Sized(Ui.Button(TEXT("button/apply"), Key(TEXT("options.apply")), [this]
	{
		Apply();
		if (AJadgHud* Manager = Hud())
		{
			if (UJadgScreen* Top = Manager->Find(EJadgScreen::Options))
			{
				Top->Close();
			}
		}
	}), 280.0f, 56.0f));
	FJadgUi::Add(Body, Foot);
	FJadgUi::Place(Root, Ui.Piece(TEXT("frame/panel-dark"), Body, FMargin(60.0f, 56.0f)), FVector2D(640.0f, 150.0f), FVector2D(1160.0f, 820.0f));
	ShowValues();
}

// --- Les fins -----------------------------------------------------------------------------------

void UJadgEndScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	const bool bDeath = Kind == EJadgScreen::Death;
	UCanvasPanel* Content = Page(Ui, Root, Key(bDeath ? TEXT("end.death.title") : TEXT("end.demo.title")), !bDeath);
	UVerticalBox* Column = Ui.Column();
	FJadgUi::Add(Column, Ui.Image(bDeath ? FName(TEXT("ornament/crossed-crest")) : FName(TEXT("ornament/wax-seal"))), FMargin(0.0f, 60.0f, 0.0f, 30.0f),
		0.0f, HAlign_Center);
	const FText Said = bDeath ? Key(TEXT("end.death.text"))
							  : FJadgTexts::Format(TEXT("end.demo.text"), {FJadgTexts::Get(TEXT("ending.") + Argument)});
	FJadgUi::Add(Column, Ui.Text(Said, TEXT("lore"), TEXT("reading"), bDeath ? TEXT("textOnPanel") : TEXT("text"), true, ETextJustify::Center),
		FMargin(200.0f, 0.0f), 0.0f, HAlign_Fill);
	UHorizontalBox* Foot = Ui.Row();
	FJadgUi::Add(Foot, Ui.Sized(Ui.Button(TEXT("button/default"), Key(TEXT("menu.to_title")), [this]
	{
		if (AJadgHud* Manager = Hud())
		{
			Manager->CloseAll();
			Manager->Open(EJadgScreen::Title);
		}
	}), 320.0f, 56.0f), FMargin(12.0f, 0.0f));
	FJadgUi::Add(Foot, Ui.Sized(Ui.Button(TEXT("button/cancel"), Key(TEXT("menu.quit")), [this] { Quit(this); }), 320.0f, 56.0f), FMargin(12.0f, 0.0f));
	FJadgUi::Add(Column, Foot, FMargin(0.0f, 80.0f, 0.0f, 0.0f), 0.0f, HAlign_Center);
	FJadgUi::Fill(Content, Column);
}

bool UJadgEndScreen::HandleKey(const FKey& Key)
{
	// Une fin ferme la partie : Échap ne ramène pas au jeu (`EX-IHM-091`).
	return Key == EKeys::Escape;
}

// --- Le débogage --------------------------------------------------------------------------------

void UJadgDebugScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	UVerticalBox* Column = Ui.Column();
	FJadgUi::Add(Column, Ui.Text(Key(TEXT("debug.title")), TEXT("title"), TEXT("section"), TEXT("goldLight")), FMargin(0.0f, 0.0f, 0.0f, 12.0f));
	Facts = Ui.Text(FText::GetEmpty(), TEXT("body"), TEXT("body"), TEXT("textOnPanel"), true);
	FJadgUi::Add(Column, Facts);
	UHorizontalBox* Hours = Ui.Row();
	for (const int32 Hour : {6, 12, 18, 22})
	{
		FJadgUi::Add(Hours, Ui.Sized(Ui.Button(TEXT("button/chip"), FText::FromString(FString::Printf(TEXT("%02d:00"), Hour)), [this, Hour]
		{
			if (UJadgExploration* Game = Exploration())
			{
				Game->SetMinutes(Hour * 60.0f);
			}
		}, TEXT("textOnPanel"), true, TEXT("caption")), 120.0f, 40.0f), FMargin(4.0f, 0.0f));
	}
	FJadgUi::Add(Column, Hours, FMargin(0.0f, 16.0f, 0.0f, 0.0f));
	FJadgUi::Add(Column, Ui.Sized(Ui.Button(TEXT("button/default"), Key(TEXT("debug.clock")), [this]
	{
		if (UJadgExploration* Game = Exploration())
		{
			Game->SetClockRunning(true);
		}
	}), 320.0f, 52.0f), FMargin(0.0f, 12.0f, 0.0f, 0.0f), 0.0f, HAlign_Left);
	FJadgUi::Place(Root, Ui.Sized(Ui.Piece(TEXT("frame/panel-dark"), Column, FMargin(56.0f, 48.0f)), 760.0f, 0.0f), FVector2D(-40.0f, 40.0f),
		FVector2D::ZeroVector, FVector2D(1.0f, 0.0f), FVector2D(1.0f, 0.0f));
}

void UJadgDebugScreen::Refresh()
{
	const UJadgExploration* Game = Exploration();
	if (Game == nullptr)
	{
		return;
	}
	const FVector2D Cell = Game->HeroCell();
	const int32 Minutes = FMath::FloorToInt32(Game->Minutes());
	const float Frame = GetWorld() != nullptr ? GetWorld()->GetDeltaSeconds() : 0.0f;
	Facts->SetText(FJadgTexts::Format(TEXT("debug.facts"),
		{FText::FromString(Game->MapId()), FText::FromString(FString::Printf(TEXT("%.1f ; %.1f"), Cell.X, Cell.Y)), FText::AsNumber(Game->HeroStorey()),
			FText::FromString(FString::Printf(TEXT("%02d:%02d"), Minutes / 60 % 24, Minutes % 60)),
			FText::FromString(Game->Encounter().IsEmpty() ? TEXT("—") : Game->Encounter()),
			FText::FromString(Frame > 0.0f ? FString::Printf(TEXT("%.0f"), 1.0f / Frame) : TEXT("—")),
			FText::AsNumber(UJadgStyle::Get().TexturesFound())}));
}
