// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "UI/JadgHud.h"

#include "CanvasItem.h"
#include "Combat/JadgCombat.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/GameInstance.h"
#include "Engine/Texture2D.h"
#include "Game/JadgExploration.h"
#include "ImageUtils.h"
#include "TextureResource.h"
#include "Player/JadgControls.h"

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

UTexture2D* AJadgHud::PortraitOf(const FString& File)
{
	if (File.IsEmpty())
	{
		return nullptr;
	}
	if (const TObjectPtr<UTexture2D>* Known = Portraits.Find(File))
	{
		return Known->Get();
	}
	UTexture2D* Read = FImageUtils::ImportFileAsTexture2D(File);
	Portraits.Add(File, Read);
	return Read;
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
	const FString InteractKey = TEXT("[") + UJadgControls::KeyLabel(TEXT("Interact")) + TEXT("]  ");
	const float Width = Canvas->SizeX;
	const float Height = Canvas->SizeY;
	// Les tailles sont écrites pour 1080 lignes et suivent la définition.
	const float Unit = Height / 1080.0f;
	const float Scale = 1.5f * Unit;
	const float Margin = 24.0f * Unit;

	if (DrawCombat(Unit))
	{
		return;
	}

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
		if (!Exploration->Encounter().IsEmpty())
		{
			// La bascule vers le combat, le temps que l'arène s'ouvre.
			const FString Title = TEXT("Rencontre : ") + Exploration->Encounter();
			Write(Title, (Width - Measure(Title, Scale * 1.3f)) / 2.0f, Height * 0.40f, Gold, Scale * 1.3f);
		}
		else if (Exploration->Target(Cell, Key))
		{
			const FString Prompt = InteractKey + PromptFor(Key);
			Write(Prompt, (Width - Measure(Prompt, Scale)) / 2.0f, Height * 0.82f, Ink, Scale);
		}
		return;
	}

	// Le dialogue : un bandeau en bas de l'écran.
	const float Top = Height * 0.72f;
	const float Edge = Width * 0.14f;
	const float Whole = Width * 0.72f;
	FCanvasTileItem Back(FVector2D(Edge - Margin, Top - Margin), FVector2D(Whole + 2.0f * Margin, Height - Top), Panel);
	Back.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Back);

	// Le portrait de qui parle, à gauche du texte, s'il en a un.
	float Left = Edge;
	if (const UTexture2D* Face = PortraitOf(Exploration->SpeakerPortrait()))
	{
		const float Side = Height - Top - Margin;
		FCanvasTileItem Picture(FVector2D(Edge, Top), Face->GetResource(), FVector2D(Side, Side), FLinearColor::White);
		Picture.BlendMode = SE_BLEND_Translucent;
		Canvas->DrawItem(Picture);
		Left += Side + Margin;
	}
	const float Inner = Whole - (Left - Edge);

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

bool AJadgHud::DrawCombat(float Unit)
{
	AJadgCombat* Combat = AJadgCombat::Find(GetWorld());
	if (Combat == nullptr || !Combat->IsMounted())
	{
		return false;
	}
	const float Width = Canvas->SizeX;
	const float Height = Canvas->SizeY;
	const float Scale = 1.3f * Unit;
	const float Margin = 24.0f * Unit;
	const FLinearColor Foe(1.0f, 0.55f, 0.45f);
	const int32 Active = Combat->ActiveId();

	// Les deux camps, le combattant actif marqué.
	float Y = Margin;
	Y += Write(FString::Printf(TEXT("Round %d"), Combat->Round()), Margin, Y, Gold, Scale);
	for (const FJadgFighter& Fighter : Combat->Fighters())
	{
		const FString State = Fighter.bDead ? TEXT("  mort") : !Fighter.bStanding ? TEXT("  à terre") : TEXT("");
		const FString Line = FString::Printf(TEXT("%s%s   %d / %d%s"), Fighter.Id == Active ? TEXT("> ") : TEXT("   "), *Fighter.Name,
			Fighter.HitPoints, Fighter.MaxHitPoints, *State);
		Y += Write(Line, Margin, Y, Fighter.Id == Active ? Gold : Fighter.bAlly ? Ink : Foe, Scale);
	}

	// L'issue, au centre.
	const FString Outcome = Combat->Outcome();
	if (!Outcome.IsEmpty())
	{
		Write(Outcome, (Width - Measure(Outcome, Scale * 2.0f)) / 2.0f, Height * 0.38f, Gold, Scale * 2.0f);
	}

	// Le tour, en bas : un bandeau.
	const float Top = Height * 0.74f;
	FCanvasTileItem Back(FVector2D(0.0f, Top - Margin * 0.5f), FVector2D(Width, Height - Top + Margin * 0.5f), Panel);
	Back.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Back);
	const float Left = Margin;
	const float Right = Width * 0.55f;
	Y = Top;
	FString Who;
	for (const FJadgFighter& Fighter : Combat->Fighters())
	{
		if (Fighter.Id == Active)
		{
			Who = Fighter.Name;
		}
	}
	if (Combat->IsPlayerTurn())
	{
		Y += Write(FString::Printf(TEXT("À vous : %s — %.1f m de déplacement"), *Who, Combat->MovementLeft()), Left, Y, Gold, Scale * 1.1f);
		FString TargetLine = TEXT("Cible : aucune (clic sur un adversaire)");
		for (const FJadgFighter& Fighter : Combat->Fighters())
		{
			if (Fighter.Id == Combat->TargetId())
			{
				TargetLine = FString::Printf(TEXT("Cible : %s, %d / %d — %s"), *Fighter.Name, Fighter.HitPoints, Fighter.MaxHitPoints,
					*Combat->TargetCircumstances());
			}
		}
		Y += Write(TargetLine, Left, Y, Ink, Scale);
		const TArray<FString> Capacities = Combat->Capacities();
		for (int32 Index = 0; Index < Capacities.Num(); ++Index)
		{
			const bool bChosen = Combat->CapacityRank() == Index + 1;
			Y += Write(FString::Printf(TEXT("%s%d. %s"), bChosen ? TEXT("> ") : TEXT("   "), Index + 1, *Capacities[Index]), Left, Y,
				bChosen ? Gold : Dim, Scale);
		}
		const FString CapacityKeys = Capacities.IsEmpty() ? FString()
			: FString::Printf(TEXT("[1-%d] capacité, [%s] la lancer   "), Capacities.Num(), *UJadgControls::KeyLabel(TEXT("Capacity")));
		const FString Keys = FString::Printf(TEXT("[clic] cible ou destination   [%s] attaquer   %s[%s] fin du tour"),
			*UJadgControls::KeyLabel(TEXT("Attack")), *CapacityKeys, *UJadgControls::KeyLabel(TEXT("EndTurn")));
		Y += Write(Keys, Left, Y, Dim, Scale * 0.9f);
		if (!Combat->Refusal().IsEmpty())
		{
			Y += Write(Combat->Refusal(), Left, Y, Foe, Scale);
		}
	}
	else if (Outcome.IsEmpty())
	{
		Y += Write(FString::Printf(TEXT("Tour de %s"), *Who), Left, Y, Ink, Scale * 1.1f);
	}

	// Le journal, à droite du bandeau.
	float J = Top;
	for (const FString& Line : Combat->Journal(8))
	{
		J += Write(Line, Right, J, Dim, Scale * 0.85f);
	}
	return true;
}
