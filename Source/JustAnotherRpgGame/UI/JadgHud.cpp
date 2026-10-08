// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "UI/JadgHud.h"

#include "CanvasItem.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/GameInstance.h"
#include "Game/JadgExploration.h"

namespace
{
	const FLinearColor Ink(0.93f, 0.90f, 0.82f);
	const FLinearColor Gold(1.0f, 0.78f, 0.36f);
	const FLinearColor Dim(0.70f, 0.68f, 0.62f);
	const FLinearColor Panel(0.02f, 0.02f, 0.03f, 0.78f);

	/// L'invite d'une famille d'entités, par sa clé (`core::knownInteractableKinds`). Le catalogue
	/// des textes ne porte pas encore ces clés : elles y entrent avec l'interface (LOT-1020).
	FString PromptFor(const FString& Key)
	{
		if (Key == TEXT("interaction.npc")) { return TEXT("Parler"); }
		if (Key == TEXT("interaction.chest")) { return TEXT("Ouvrir"); }
		if (Key == TEXT("interaction.sign")) { return TEXT("Lire"); }
		return TEXT("Interagir");
	}
}

float AJadgHud::Measure(const FString& Text, float Scale) const
{
	float Width = 0.0f;
	float Height = 0.0f;
	Canvas->TextSize(GEngine->GetMediumFont(), Text, Width, Height, Scale, Scale);
	return Width;
}

float AJadgHud::Write(const FString& Text, float X, float Y, const FLinearColor& Colour, float Scale) const
{
	const UFont* Font = GEngine->GetMediumFont();
	FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), Font, Colour);
	Item.Scale = FVector2D(Scale, Scale);
	Item.EnableShadow(FLinearColor::Black);
	Canvas->DrawItem(Item);
	return Font->GetMaxCharHeight() * Scale * 1.25f;
}

float AJadgHud::WriteWrapped(const FString& Text, float X, float Y, float Width, const FLinearColor& Colour, float Scale) const
{
	TArray<FString> Words;
	Text.ParseIntoArray(Words, TEXT(" "));
	FString Line;
	float Used = 0.0f;
	for (const FString& Word : Words)
	{
		const FString Longer = Line.IsEmpty() ? Word : Line + TEXT(" ") + Word;
		if (!Line.IsEmpty() && Measure(Longer, Scale) > Width)
		{
			Used += Write(Line, X, Y + Used, Colour, Scale);
			Line = Word;
		}
		else
		{
			Line = Longer;
		}
	}
	if (!Line.IsEmpty())
	{
		Used += Write(Line, X, Y + Used, Colour, Scale);
	}
	return Used;
}

void AJadgHud::DrawHUD()
{
	Super::DrawHUD();

	const UGameInstance* Instance = GetGameInstance();
	const UJadgExploration* Exploration = Instance != nullptr ? Instance->GetSubsystem<UJadgExploration>() : nullptr;
	if (Canvas == nullptr || Exploration == nullptr || GEngine->GetMediumFont() == nullptr)
	{
		return;
	}
	const float Width = Canvas->SizeX;
	const float Height = Canvas->SizeY;
	// Les tailles sont écrites pour 1080 lignes et suivent la définition.
	const float Unit = Height / 1080.0f;
	const float Scale = 1.5f * Unit;
	const float Margin = 24.0f * Unit;

	// Le groupe, le meneur en tête.
	float Y = Margin;
	const TArray<FJadgMember> Members = Exploration->Members();
	for (int32 Index = 0; Index < Members.Num(); ++Index)
	{
		const FJadgMember& Member = Members[Index];
		const FString Line = FString::Printf(TEXT("%s%s   %d / %d"), Index == 0 ? TEXT("> ") : TEXT("   "), *Member.Name,
			Member.HitPoints, Member.MaxHitPoints);
		Y += Write(Line, Margin, Y, Index == 0 ? Gold : Ink, Scale);
	}

	// L'heure du monde.
	const int32 Minutes = FMath::FloorToInt32(Exploration->Minutes());
	const FString Clock = FString::Printf(TEXT("%02d:%02d"), Minutes / 60, Minutes % 60);
	Write(Clock, Width - Margin - Measure(Clock, Scale), Margin, Ink, Scale);

	// L'annonce du moment.
	const FString Notice = Exploration->Notice();
	if (!Notice.IsEmpty())
	{
		const float Wide = FMath::Min(Measure(Notice, Scale), Width * 0.6f);
		WriteWrapped(Notice, (Width - Wide) / 2.0f, Margin, Width * 0.6f, Gold, Scale);
	}

	if (!Exploration->InDialogue())
	{
		FIntPoint Cell;
		FString Key;
		if (Exploration->Target(Cell, Key))
		{
			const FString Prompt = TEXT("[Espace]  ") + PromptFor(Key);
			Write(Prompt, (Width - Measure(Prompt, Scale)) / 2.0f, Height * 0.82f, Ink, Scale);
		}
		return;
	}

	// Le dialogue : un bandeau en bas de l'écran.
	const float Top = Height * 0.72f;
	const float Left = Width * 0.14f;
	const float Inner = Width * 0.72f;
	FCanvasTileItem Back(FVector2D(Left - Margin, Top - Margin), FVector2D(Inner + 2.0f * Margin, Height - Top), Panel);
	Back.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Back);

	Y = Top;
	Y += Write(Exploration->Speaker(), Left, Y, Gold, Scale * 1.15f);
	const FString Check = Exploration->LastCheck();
	if (!Check.IsEmpty())
	{
		Y += Write(Check, Left, Y, Dim, Scale);
	}
	Y += WriteWrapped(Exploration->Line(), Left, Y, Inner, Ink, Scale) + Margin * 0.5f;

	const TArray<FJadgChoice> Choices = Exploration->Choices();
	for (int32 Index = 0; Index < Choices.Num(); ++Index)
	{
		const FJadgChoice& Choice = Choices[Index];
		FString Line = FString::Printf(TEXT("%d.  %s"), Index + 1, *Choice.Text);
		if (!Choice.Skill.IsEmpty())
		{
			Line += FString::Printf(TEXT("   (%s · DD %d)"), *Choice.Skill, Choice.Dc);
		}
		Y += WriteWrapped(Line, Left + Margin, Y, Inner - Margin, Ink, Scale);
	}
}
