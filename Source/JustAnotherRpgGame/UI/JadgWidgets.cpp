// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "UI/JadgWidgets.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/ButtonSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/OverlaySlot.h"
#include "Components/ProgressBar.h"
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "UI/JadgStyle.h"

// --- Le bouton --------------------------------------------------------------------------------

TSharedRef<SWidget> UJadgButton::RebuildWidget()
{
	OnClicked.AddUniqueDynamic(this, &UJadgButton::HandleClicked);
	return Super::RebuildWidget();
}

void UJadgButton::HandleClicked()
{
	Activate();
}

void UJadgButton::Activate()
{
	if (GetIsEnabled() && Action)
	{
		// Une copie : le geste peut reconstruire l'écran, donc détruire ce bouton.
		const TFunction<void()> Gesture = Action;
		Gesture();
	}
}

void UJadgButton::SyncFocus()
{
	if (FocusMark != nullptr)
	{
		FocusMark->SetVisibility(HasKeyboardFocus() ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Hidden);
	}
}

void UJadgButton::SetLabel(const FText& Text)
{
	Label = Text;
	if (LabelBlock != nullptr)
	{
		LabelBlock->SetText(Text);
	}
}

// --- Le constructeur --------------------------------------------------------------------------

UTextBlock* FJadgUi::Text(const FText& Value, FName FontRole, FName SizeRole, FName ColourRole, bool bWrap, ETextJustify::Type Justify) const
{
	UTextBlock* Block = Tree->ConstructWidget<UTextBlock>();
	Block->SetText(Value);
	Block->SetFont(UJadgStyle::Get().Font(FontRole, SizeRole));
	Block->SetColorAndOpacity(FSlateColor(UJadgStyle::Get().Colour(ColourRole)));
	Block->SetAutoWrapText(bWrap);
	Block->SetJustification(Justify);
	return Block;
}

UBorder* FJadgUi::Piece(FName PieceId, UWidget* Content, const FMargin& Padding, FName State) const
{
	UBorder* Frame = Tree->ConstructWidget<UBorder>();
	Frame->SetBrush(UJadgStyle::Get().Brush(PieceId, State));
	Frame->SetPadding(Padding);
	if (Content != nullptr)
	{
		Frame->SetContent(Content);
	}
	return Frame;
}

UImage* FJadgUi::Image(FName PieceId, FName State, FVector2D Size) const
{
	UImage* Picture = Tree->ConstructWidget<UImage>();
	FSlateBrush Brush = UJadgStyle::Get().Brush(PieceId, State);
	if (!Size.IsZero())
	{
		Brush.ImageSize = Size;
	}
	Picture->SetBrush(Brush);
	return Picture;
}

UImage* FJadgUi::Icon(const FString& KitPath, const FVector2D& Size) const
{
	UImage* Picture = Tree->ConstructWidget<UImage>();
	Picture->SetBrush(UJadgStyle::Get().Image(KitPath, Size));
	return Picture;
}

UBorder* FJadgUi::Flat(FName ColourRole, UWidget* Content, const FMargin& Padding) const
{
	UBorder* Frame = Tree->ConstructWidget<UBorder>();
	FSlateBrush Brush;
	Brush.DrawAs = ESlateBrushDrawType::Image;
	Brush.TintColor = FSlateColor(UJadgStyle::Get().Colour(ColourRole));
	Frame->SetBrush(Brush);
	Frame->SetPadding(Padding);
	if (Content != nullptr)
	{
		Frame->SetContent(Content);
	}
	return Frame;
}

UJadgButton* FJadgUi::Button(FName PieceId, const FText& Label, TFunction<void()> Action, FName LabelColour, bool bFocusable,
	FName SizeRole) const
{
	const UJadgStyle& Style = UJadgStyle::Get();
	UJadgButton* Made = Tree->ConstructWidget<UJadgButton>();
	Made->Action = MoveTemp(Action);
	Made->Label = Label;
	Made->SetFocusable(bFocusable);

	// Les états du kit : survol et enfoncé quand la pièce les a, sinon ce qui en tient lieu.
	const auto StateOr = [&Style, PieceId](std::initializer_list<const TCHAR*> Wanted)
	{
		for (const TCHAR* State : Wanted)
		{
			if (Style.HasState(PieceId, State))
			{
				return FName(State);
			}
		}
		return FName();
	};
	FButtonStyle Look;
	Look.SetNormal(Style.Brush(PieceId, StateOr({TEXT("normal")})));
	Look.SetHovered(Style.Brush(PieceId, StateOr({TEXT("hover"), TEXT("active"), TEXT("selected"), TEXT("normal")})));
	Look.SetPressed(Style.Brush(PieceId, StateOr({TEXT("pressed"), TEXT("active"), TEXT("selected"), TEXT("normal")})));
	Look.SetDisabled(Style.Brush(PieceId, StateOr({TEXT("disabled"), TEXT("normal")})));
	Look.SetNormalPadding(FMargin(0.0f));
	Look.SetPressedPadding(FMargin(0.0f));
	Made->SetStyle(Look);

	if (!Label.IsEmpty())
	{
		UHorizontalBox* Line = Row();
		UImage* Mark = Image(TEXT("control/focus-fleuron"), NAME_None, FVector2D(20.0f, 20.0f));
		Mark->SetVisibility(ESlateVisibility::Hidden);
		Add(Line, Mark, FMargin(0.0f, 0.0f, 6.0f, 0.0f));
		UTextBlock* Caption = Text(Label, TEXT("label"), SizeRole, LabelColour, false, ETextJustify::Center);
		Add(Line, Caption);
		Made->SetContent(Line);
		if (UPanelSlot* Slot = Line->Slot)
		{
			if (UButtonSlot* ButtonSlot = Cast<UButtonSlot>(Slot))
			{
				ButtonSlot->SetHorizontalAlignment(HAlign_Center);
				ButtonSlot->SetVerticalAlignment(VAlign_Center);
				ButtonSlot->SetPadding(FMargin(24.0f, 4.0f));
			}
		}
		Made->FocusMark = Mark;
		Made->LabelBlock = Caption;
	}
	if (Buttons != nullptr)
	{
		Buttons->Add(Made);
	}
	return Made;
}

UProgressBar* FJadgUi::Gauge(float Fraction, FName FillColour) const
{
	const UJadgStyle& Style = UJadgStyle::Get();
	UProgressBar* Bar = Tree->ConstructWidget<UProgressBar>();
	FProgressBarStyle Look;
	Look.SetBackgroundImage(Style.Brush(TEXT("gauge/track")));
	FSlateBrush Fill = Style.Brush(TEXT("gauge/fill-sheen"));
	Fill.TintColor = FSlateColor(Style.Colour(FillColour));
	if (Fill.DrawAs == ESlateBrushDrawType::RoundedBox)
	{
		Fill.DrawAs = ESlateBrushDrawType::Image;
	}
	Look.SetFillImage(Fill);
	Look.SetMarqueeImage(Fill);
	Bar->SetWidgetStyle(Look);
	Bar->SetPercent(FMath::Clamp(Fraction, 0.0f, 1.0f));
	Bar->SetFillColorAndOpacity(FLinearColor::White);
	return Bar;
}

UVerticalBox* FJadgUi::Column() const
{
	return Tree->ConstructWidget<UVerticalBox>();
}

UHorizontalBox* FJadgUi::Row() const
{
	return Tree->ConstructWidget<UHorizontalBox>();
}

UOverlay* FJadgUi::Layers() const
{
	return Tree->ConstructWidget<UOverlay>();
}

UScrollBox* FJadgUi::Scroll() const
{
	return Tree->ConstructWidget<UScrollBox>();
}

UCanvasPanel* FJadgUi::Canvas() const
{
	return Tree->ConstructWidget<UCanvasPanel>();
}

USizeBox* FJadgUi::Sized(UWidget* Content, float Width, float Height) const
{
	USizeBox* Box = Tree->ConstructWidget<USizeBox>();
	if (Width > 0.0f)
	{
		Box->SetWidthOverride(Width);
	}
	if (Height > 0.0f)
	{
		Box->SetHeightOverride(Height);
	}
	if (Content != nullptr)
	{
		Box->SetContent(Content);
	}
	return Box;
}

void FJadgUi::Add(UVerticalBox* Box, UWidget* Child, const FMargin& Padding, float Fill, EHorizontalAlignment Align)
{
	UVerticalBoxSlot* Slot = Box->AddChildToVerticalBox(Child);
	Slot->SetPadding(Padding);
	Slot->SetHorizontalAlignment(Align);
	if (Fill > 0.0f)
	{
		FSlateChildSize Share(ESlateSizeRule::Fill);
		Share.Value = Fill;
		Slot->SetSize(Share);
	}
}

void FJadgUi::Add(UHorizontalBox* Box, UWidget* Child, const FMargin& Padding, float Fill, EVerticalAlignment Align)
{
	UHorizontalBoxSlot* Slot = Box->AddChildToHorizontalBox(Child);
	Slot->SetPadding(Padding);
	Slot->SetVerticalAlignment(Align);
	if (Fill > 0.0f)
	{
		FSlateChildSize Share(ESlateSizeRule::Fill);
		Share.Value = Fill;
		Slot->SetSize(Share);
	}
}

void FJadgUi::Add(UOverlay* Box, UWidget* Child, EHorizontalAlignment HAlign, EVerticalAlignment VAlign, const FMargin& Padding)
{
	UOverlaySlot* Slot = Box->AddChildToOverlay(Child);
	Slot->SetHorizontalAlignment(HAlign);
	Slot->SetVerticalAlignment(VAlign);
	Slot->SetPadding(Padding);
}

UCanvasPanelSlot* FJadgUi::Place(UCanvasPanel* Canvas, UWidget* Child, const FVector2D& Position, const FVector2D& Size, const FVector2D& Anchor,
	const FVector2D& Alignment)
{
	UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Child);
	Slot->SetAnchors(FAnchors(Anchor.X, Anchor.Y));
	Slot->SetAlignment(Alignment);
	Slot->SetPosition(Position);
	if (Size.IsZero())
	{
		Slot->SetAutoSize(true);
	}
	else
	{
		Slot->SetSize(Size);
	}
	return Slot;
}

UCanvasPanelSlot* FJadgUi::Fill(UCanvasPanel* Canvas, UWidget* Child, const FMargin& Inset)
{
	UCanvasPanelSlot* Slot = Canvas->AddChildToCanvas(Child);
	Slot->SetAnchors(FAnchors(0.0f, 0.0f, 1.0f, 1.0f));
	Slot->SetOffsets(Inset);
	return Slot;
}
