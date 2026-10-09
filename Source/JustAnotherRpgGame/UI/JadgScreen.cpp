// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "UI/JadgScreen.h"

#include "Blueprint/WidgetTree.h"
#include "Combat/JadgCombat.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Game/JadgExploration.h"
#include "GameFramework/PlayerController.h"
#include "UI/JadgHud.h"
#include "UI/JadgStyle.h"
#include "UI/JadgTexts.h"

TSharedRef<SWidget> UJadgScreen::RebuildWidget()
{
	if (WidgetTree == nullptr)
	{
		WidgetTree = NewObject<UWidgetTree>(this, TEXT("WidgetTree"), RF_Transient);
	}
	if (WidgetTree->RootWidget == nullptr)
	{
		ButtonList.Reset();
		UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Root"));
		WidgetTree->RootWidget = Root;
		FJadgUi Ui{WidgetTree, &ButtonList};
		Build(Ui, Root);
		if (PageRoot != nullptr && IsModal() && Kind != EJadgScreen::Ending && Kind != EJadgScreen::Death)
		{
			// Le pied de toute page : « Retour », pour la souris comme pour le clavier (Échap).
			UJadgButton* Back = Ui.Button(TEXT("button/back"), FJadgTexts::Get(TEXT("options.back")), [this] { Close(); });
			FJadgUi::Place(PageRoot, Ui.Sized(Back, 260.0f, 64.0f), FVector2D(64.0f, -40.0f), FVector2D::ZeroVector, FVector2D(0.0f, 1.0f),
				FVector2D(0.0f, 1.0f));
		}
		if (!IsModal())
		{
			// Posé sur le jeu : seuls les boutons arrêtent la souris, le reste va à la scène.
			Root->SetVisibility(ESlateVisibility::SelfHitTestInvisible);
		}
	}
	return Super::RebuildWidget();
}

void UJadgScreen::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Refresh();
	for (UJadgButton* Button : ButtonList)
	{
		if (Button != nullptr)
		{
			Button->SyncFocus();
		}
	}
}

FReply UJadgScreen::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	return HandleKey(InKeyEvent.GetKey()) ? FReply::Handled() : Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

bool UJadgScreen::HandleKey(const FKey& Key)
{
	if (IsModal() && Key == EKeys::Escape)
	{
		Close();
		return true;
	}
	return false;
}

void UJadgScreen::Close()
{
	if (AJadgHud* Manager = Hud())
	{
		Manager->Close(this);
	}
}

UJadgButton* UJadgScreen::FindButton(const FText& Label) const
{
	for (UJadgButton* Button : ButtonList)
	{
		if (Button != nullptr && Button->Label.EqualTo(Label))
		{
			return Button;
		}
	}
	return nullptr;
}

UWidget* UJadgScreen::FirstFocus() const
{
	for (UJadgButton* Button : ButtonList)
	{
		if (Button != nullptr && Button->GetIsEnabled() && Button->GetIsFocusable() && Button->GetVisibility() != ESlateVisibility::Collapsed)
		{
			return Button;
		}
	}
	return const_cast<UJadgScreen*>(this);
}

TArray<FString> UJadgScreen::VisibleTexts() const
{
	TArray<FString> Out;
	if (WidgetTree != nullptr)
	{
		WidgetTree->ForEachWidget([&Out](UWidget* Widget)
		{
			if (const UTextBlock* Block = Cast<UTextBlock>(Widget))
			{
				const ESlateVisibility Shown = Block->GetVisibility();
				if (Shown != ESlateVisibility::Collapsed && Shown != ESlateVisibility::Hidden && !Block->GetText().IsEmpty())
				{
					Out.Add(Block->GetText().ToString());
				}
			}
		});
	}
	return Out;
}

AJadgHud* UJadgScreen::Hud() const
{
	const APlayerController* Player = GetOwningPlayer();
	return Player != nullptr ? Cast<AJadgHud>(Player->GetHUD()) : nullptr;
}

UJadgExploration* UJadgScreen::Exploration() const
{
	const UGameInstance* Instance = GetGameInstance();
	return Instance != nullptr ? Instance->GetSubsystem<UJadgExploration>() : nullptr;
}

AJadgCombat* UJadgScreen::Combat() const
{
	AJadgCombat* Found = AJadgCombat::Find(GetWorld());
	return Found != nullptr && Found->IsMounted() ? Found : nullptr;
}

UCanvasPanel* UJadgScreen::Page(FJadgUi& Ui, UCanvasPanel* Root, const FText& Title, bool bParchment)
{
	// Le voile, puis la page : le parchemin relié, ou le grand panneau sombre.
	PageRoot = Root;
	FJadgUi::Fill(Root, Ui.Flat(TEXT("scrim")));
	UBorder* Sheet = Ui.Piece(bParchment ? FName(TEXT("frame/panel-parchment")) : FName(TEXT("frame/panel-dark")), nullptr,
		FMargin(0.0f), bParchment ? FName(TEXT("bound")) : NAME_None);
	FJadgUi::Fill(Root, Sheet, FMargin(24.0f, 24.0f, 24.0f, 24.0f));

	// La plaque de titre, au centre du haut, en capitales romaines.
	UTextBlock* Heading = Ui.Text(Title, TEXT("display"), TEXT("screenTitle"), TEXT("textOnPanel"), false, ETextJustify::Center);
	UBorder* Plate = Ui.Piece(TEXT("plate/title-black"), Heading, FMargin(120.0f, 14.0f, 120.0f, 14.0f));
	FJadgUi::Place(Root, Plate, FVector2D(0.0f, 30.0f), FVector2D::ZeroVector, FVector2D(0.5f, 0.0f), FVector2D(0.5f, 0.0f));

	UCanvasPanel* Content = Ui.Canvas();
	FJadgUi::Fill(Root, Content, FMargin(96.0f, 140.0f, 96.0f, 80.0f));
	return Content;
}

UWidget* UJadgScreen::Section(FJadgUi& Ui, const FText& Title, bool bOnParchment) const
{
	UTextBlock* Caption = Ui.Text(Title, TEXT("title"), TEXT("section"), bOnParchment ? TEXT("surfaceAlt") : TEXT("panelEdge"), false,
		ETextJustify::Center);
	return Ui.Piece(TEXT("plate/section-banner"), Caption, FMargin(64.0f, 8.0f, 64.0f, 8.0f));
}

UWidget* UJadgScreen::Field(FJadgUi& Ui, const FText& Label, const FText& Value) const
{
	UHorizontalBox* Line = Ui.Row();
	UTextBlock* Tag = Ui.Text(Label, TEXT("label"), TEXT("caption"), TEXT("textOnPanel"));
	FJadgUi::Add(Line, Ui.Sized(Ui.Piece(TEXT("plate/field-tag"), Tag, FMargin(14.0f, 8.0f, 40.0f, 8.0f)), 210.0f, 0.0f));
	UTextBlock* Written = Ui.Text(Value, TEXT("lore"), TEXT("body"), TEXT("text"));
	FJadgUi::Add(Line, Written, FMargin(18.0f, 0.0f, 0.0f, 0.0f), 1.0f);
	return Line;
}
