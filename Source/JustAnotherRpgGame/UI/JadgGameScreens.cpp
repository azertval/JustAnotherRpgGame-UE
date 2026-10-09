// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Le jeu : le HUD d'exploration, le dialogue, l'interface du combat (LOT-1020).

#include "Blueprint/WidgetTree.h"
#include "Combat/JadgCombat.h"
#include "Components/Border.h"
#include "Components/ButtonSlot.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/HorizontalBox.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/ProgressBar.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Game/JadgExploration.h"
#include "Player/JadgControls.h"
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

	/// L'invite d'une famille d'entités, par sa clé (`core::knownInteractableKinds`).
	FText PromptFor(const FString& Kind)
	{
		return FJadgTexts::Has(FJadgTexts::Language(), Kind) || FJadgTexts::Has(TEXT("fr"), Kind) ? FJadgTexts::Get(Kind)
																							  : Key(TEXT("interaction.default"));
	}

	FText Fraction(int32 Value, int32 Of)
	{
		return FText::FromString(FString::Printf(TEXT("%d / %d"), Value, Of));
	}

	/// Le cadran du jour à l'heure @p Minutes : jour, crépuscule ou nuit.
	FString DialFor(float Minutes)
	{
		const float Hours = Minutes / 60.0f;
		return Hours >= 7.0f && Hours < 18.0f ? TEXT("day") : Hours >= 18.0f && Hours < 21.0f ? TEXT("dusk") : TEXT("night");
	}
}

// --- Le HUD d'exploration -----------------------------------------------------------------------

void UJadgHudScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	// Le lieu, en haut à gauche, sur sa plaque.
	Place = Ui.Text(FText::GetEmpty(), TEXT("title"), TEXT("section"), TEXT("goldLight"));
	FJadgUi::Place(Root, Ui.Piece(TEXT("plate/title-black"), Place, FMargin(100.0f, 10.0f, 130.0f, 10.0f)), FVector2D(22.0f, 20.0f));

	// La carte et l'heure, en haut à droite.
	UHorizontalBox* Corner = Ui.Row();
	Dial = Ui.Icon(TEXT("ornament/day-dial/day"), FVector2D(48.0f, 48.0f));
	FJadgUi::Add(Corner, Dial, FMargin(0.0f, 0.0f, 8.0f, 0.0f));
	Clock = Ui.Text(FText::GetEmpty(), TEXT("title"), TEXT("section"), TEXT("textOnPanel"));
	FJadgUi::Add(Corner, Clock, FMargin(0.0f, 0.0f, 24.0f, 0.0f));
	UJadgButton* MapButton = Ui.Button(TEXT("button/default"), Key(TEXT("hud.map")), [this]
	{
		if (AJadgHud* Manager = Hud())
		{
			Manager->Open(EJadgScreen::Map);
		}
	}, TEXT("textOnPanel"), false);
	FJadgUi::Add(Corner, Ui.Sized(MapButton, 225.0f, 56.0f));
	FJadgUi::Place(Root, Corner, FVector2D(-22.0f, 20.0f), FVector2D::ZeroVector, FVector2D(1.0f, 0.0f), FVector2D(1.0f, 0.0f));

	// L'annonce, en haut au centre ; la rencontre, au centre ; l'invite, en bas au centre.
	Notice = Ui.Text(FText::GetEmpty(), TEXT("title"), TEXT("section"), TEXT("goldLight"), true, ETextJustify::Center);
	Notice->SetShadowOffset(FVector2D(2.0f, 2.0f));
	FJadgUi::Place(Root, Notice, FVector2D(0.0f, 110.0f), FVector2D(1100.0f, 0.0f), FVector2D(0.5f, 0.0f), FVector2D(0.5f, 0.0f))
		->SetAutoSize(true);
	Encounter = Ui.Text(FText::GetEmpty(), TEXT("display"), TEXT("screenTitle"), TEXT("goldLight"), false, ETextJustify::Center);
	Encounter->SetShadowOffset(FVector2D(2.0f, 2.0f));
	FJadgUi::Place(Root, Encounter, FVector2D(0.0f, 0.0f), FVector2D::ZeroVector, FVector2D(0.5f, 0.4f), FVector2D(0.5f, 0.5f));
	Prompt = Ui.Text(FText::GetEmpty(), TEXT("label"), TEXT("section"), TEXT("textOnPanel"), false, ETextJustify::Center);
	Prompt->SetShadowOffset(FVector2D(2.0f, 2.0f));
	FJadgUi::Place(Root, Prompt, FVector2D(0.0f, -230.0f), FVector2D::ZeroVector, FVector2D(0.5f, 1.0f), FVector2D(0.5f, 1.0f));

	// Le groupe, en bas à gauche : portrait, nom, points de vie, le meneur en tête.
	UVerticalBox* Party = Ui.Column();
	Members = Ui.Row();
	FJadgUi::Add(Party, Members);
	const FText NextKey = FText::FromString(UJadgControls::KeyLabel(TEXT("NextLeader")));
	FJadgUi::Add(Party, Ui.Text(FJadgTexts::Format(TEXT("hud.next_leader"), {NextKey}), TEXT("body"), TEXT("caption"), TEXT("textOnPanelMuted"),
						 false, ETextJustify::Center),
		FMargin(0.0f, 4.0f, 0.0f, 0.0f), 0.0f, HAlign_Center);
	FJadgUi::Place(Root, Ui.Piece(TEXT("frame/panel-dark"), Party, FMargin(28.0f, 22.0f, 28.0f, 16.0f)), FVector2D(22.0f, -22.0f),
		FVector2D::ZeroVector, FVector2D(0.0f, 1.0f), FVector2D(0.0f, 1.0f));
	FillMembers(Ui);

	// Les écrans, en bas à droite.
	UHorizontalBox* Nav = Ui.Row();
	const TArray<TPair<const TCHAR*, EJadgScreen>> Screens = {
		{TEXT("hud.character"), EJadgScreen::Character},
		{TEXT("hud.equipment"), EJadgScreen::Equipment},
		{TEXT("hud.journal"), EJadgScreen::Journal},
		{TEXT("hud.party"), EJadgScreen::Party},
		{TEXT("hud.menu"), EJadgScreen::Pause},
	};
	for (const TPair<const TCHAR*, EJadgScreen>& Entry : Screens)
	{
		const EJadgScreen Target = Entry.Value;
		UJadgButton* Go = Ui.Button(TEXT("button/default"), Key(Entry.Key), [this, Target]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->Open(Target);
			}
		}, TEXT("textOnPanel"), false);
		FJadgUi::Add(Nav, Ui.Sized(Go, 232.0f, 56.0f), FMargin(2.0f, 0.0f));
	}
	FJadgUi::Place(Root, Ui.Piece(TEXT("frame/subpanel-dark"), Nav, FMargin(18.0f, 14.0f)), FVector2D(-22.0f, -22.0f), FVector2D::ZeroVector,
		FVector2D(1.0f, 1.0f), FVector2D(1.0f, 1.0f));
}

void UJadgHudScreen::FillMembers(FJadgUi& Ui)
{
	Members->ClearChildren();
	const UJadgExploration* Game = Exploration();
	if (Game == nullptr)
	{
		return;
	}
	const TArray<FJadgMember> Party = Game->Members();
	for (int32 Index = 0; Index < Party.Num(); ++Index)
	{
		const FJadgMember& Member = Party[Index];
		UVerticalBox* Card = Ui.Column();
		FJadgUi::Add(Card, Ui.Image(TEXT("medallion/portrait-round"), TEXT("empty"), FVector2D(104.0f, 104.0f)), FMargin(0.0f), 0.0f, HAlign_Center);
		// Le meneur en or ; un nom trop long pour sa carte est coupé à son bord.
		UTextBlock* Label = Ui.Text(FText::FromString(Member.Name), TEXT("body"), TEXT("caption"), Index == 0 ? TEXT("goldLight") : TEXT("textOnPanel"),
			false, ETextJustify::Center);
		Label->SetClipping(EWidgetClipping::ClipToBounds);
		FJadgUi::Add(Card, Ui.Sized(Label, 136.0f, 0.0f), FMargin(0.0f, 2.0f), 0.0f, HAlign_Center);
		UOverlay* Life = Ui.Layers();
		const float Share = Member.MaxHitPoints > 0 ? static_cast<float>(Member.HitPoints) / Member.MaxHitPoints : 0.0f;
		FJadgUi::Add(Life, Ui.Gauge(Share, TEXT("gem")));
		FJadgUi::Add(Life, Ui.Text(Fraction(Member.HitPoints, Member.MaxHitPoints), TEXT("label"), TEXT("caption"), TEXT("textOnPanel"), false,
						   ETextJustify::Center),
			HAlign_Center, VAlign_Center);
		FJadgUi::Add(Card, Ui.Sized(Life, 116.0f, 24.0f), FMargin(0.0f, 2.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Members, Card, FMargin(6.0f, 0.0f));
	}
}

void UJadgHudScreen::Refresh()
{
	const UJadgExploration* Game = Exploration();
	if (Game == nullptr)
	{
		return;
	}
	Place->SetText(FText::FromString(Game->MapName()));
	const int32 Minutes = FMath::FloorToInt32(Game->Minutes());
	Clock->SetText(FText::FromString(FString::Printf(TEXT("%02d:%02d"), Minutes / 60 % 24, Minutes % 60)));
	const FString Phase = DialFor(Game->Minutes());
	if (Phase != DialShown)
	{
		DialShown = Phase;
		Dial->SetBrush(UJadgStyle::Get().Image(TEXT("ornament/day-dial/") + Phase, FVector2D(48.0f, 48.0f)));
	}
	Notice->SetText(FText::FromString(Game->Notice()));

	FIntPoint Cell;
	FString Family;
	const bool bTalking = Game->InDialogue();
	Encounter->SetText(Game->Encounter().IsEmpty() ? FText::GetEmpty()
												   : FJadgTexts::Format(TEXT("hud.encounter"), {FText::FromString(Game->Encounter())}));
	const bool bTarget = !bTalking && Game->Encounter().IsEmpty() && Game->Target(Cell, Family);
	Prompt->SetText(bTarget ? FJadgTexts::Format(TEXT("hud.prompt"), {FText::FromString(UJadgControls::KeyLabel(TEXT("Interact"))), PromptFor(Family)})
							: FText::GetEmpty());

	// Le groupe se refait quand il change : meneur, points de vie.
	FString Now;
	for (const FJadgMember& Member : Game->Members())
	{
		Now += FString::Printf(TEXT("%s:%d/%d;"), *Member.Id, Member.HitPoints, Member.MaxHitPoints);
	}
	if (Now != Shown)
	{
		Shown = Now;
		FJadgUi Ui{WidgetTree, &ButtonList};
		FillMembers(Ui);
	}
}

// --- Le dialogue --------------------------------------------------------------------------------

void UJadgDialogueScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	UCanvasPanel* Content = Page(Ui, Root, Key(TEXT("dialogue.title")), true);

	// À gauche : le portrait de qui parle, son nom.
	UVerticalBox* Left = Ui.Column();
	UOverlay* Frame = Ui.Layers();
	Portrait = Ui.Tree->ConstructWidget<UImage>();
	FJadgUi::Add(Frame, Ui.Flat(TEXT("panel")), HAlign_Fill, VAlign_Fill, FMargin(26.0f));
	FJadgUi::Add(Frame, Portrait, HAlign_Fill, VAlign_Fill, FMargin(26.0f));
	FJadgUi::Add(Frame, Ui.Image(TEXT("medallion/portrait-square"), TEXT("normal"), FVector2D(330.0f, 330.0f)));
	FJadgUi::Add(Left, Ui.Sized(Frame, 330.0f, 330.0f), FMargin(0.0f, 0.0f, 0.0f, 40.0f), 0.0f, HAlign_Center);
	Speaker = Ui.Text(FText::GetEmpty(), TEXT("lore"), TEXT("body"), TEXT("text"));
	UHorizontalBox* NameLine = Ui.Row();
	UTextBlock* Tag = Ui.Text(Key(TEXT("dialogue.name")), TEXT("label"), TEXT("caption"), TEXT("textOnPanel"));
	FJadgUi::Add(NameLine, Ui.Sized(Ui.Piece(TEXT("plate/field-tag"), Tag, FMargin(14.0f, 8.0f, 40.0f, 8.0f)), 180.0f, 0.0f));
	FJadgUi::Add(NameLine, Speaker, FMargin(18.0f, 0.0f, 0.0f, 0.0f), 1.0f);
	FJadgUi::Add(Left, NameLine);
	Check = Ui.Text(FText::GetEmpty(), TEXT("body"), TEXT("body"), TEXT("textMuted"), true);
	FJadgUi::Add(Left, Check, FMargin(0.0f, 24.0f, 0.0f, 0.0f));
	FJadgUi::Place(Content, Left, FVector2D(0.0f, 0.0f), FVector2D(560.0f, 760.0f));

	// À droite : la réplique, puis les réponses.
	UVerticalBox* Said = Ui.Column();
	FJadgUi::Add(Said, Section(Ui, Key(TEXT("dialogue.line")), true));
	Line = Ui.Text(FText::GetEmpty(), TEXT("lore"), TEXT("reading"), TEXT("text"), true);
	FJadgUi::Add(Said, Line, FMargin(12.0f, 16.0f), 1.0f);
	FJadgUi::Place(Content, Ui.Piece(TEXT("frame/subpanel-parchment"), Said, FMargin(36.0f, 28.0f), TEXT("normal")), FVector2D(640.0f, 0.0f),
		FVector2D(1088.0f, 330.0f));
	UVerticalBox* Replies = Ui.Column();
	FJadgUi::Add(Replies, Section(Ui, Key(TEXT("dialogue.answers")), true));
	Answers = Ui.Column();
	FJadgUi::Add(Replies, Answers, FMargin(0.0f, 12.0f, 0.0f, 0.0f), 1.0f);
	FJadgUi::Place(Content, Ui.Piece(TEXT("frame/subpanel-parchment"), Replies, FMargin(36.0f, 28.0f), TEXT("normal")), FVector2D(640.0f, 360.0f),
		FVector2D(1088.0f, 400.0f));

	// En bas : qui parle pour le groupe (D-28).
	UHorizontalBox* Bar = Ui.Row();
	FJadgUi::Add(Bar, Ui.Text(Key(TEXT("dialogue.voice")), TEXT("title"), TEXT("body"), TEXT("text")), FMargin(0.0f, 0.0f, 16.0f, 0.0f));
	Voices = Ui.Row();
	FJadgUi::Add(Bar, Voices);
	const FText Tab = FText::FromString(UJadgControls::KeyLabel(TEXT("NextLeader")));
	FJadgUi::Add(Bar, Ui.Text(FJadgTexts::Format(TEXT("dialogue.voice_keys"), {Tab}), TEXT("body"), TEXT("caption"), TEXT("textMuted")),
		FMargin(16.0f, 0.0f, 0.0f, 0.0f));
	FJadgUi::Place(Content, Bar, FVector2D(0.0f, 790.0f));
}

void UJadgDialogueScreen::FillAnswers()
{
	UJadgExploration* Game = Exploration();
	FJadgUi Ui{WidgetTree, &ButtonList};
	ButtonList.Reset();
	Answers->ClearChildren();
	const TArray<FJadgChoice> Choices = Game->Choices();
	for (int32 Index = 0; Index < Choices.Num(); ++Index)
	{
		const FJadgChoice& Choice = Choices[Index];
		FText Text = FText::FromString(FString::Printf(TEXT("%d.  %s"), Index + 1, *Choice.Text));
		if (!Choice.Skill.IsEmpty())
		{
			Text = FText::FromString(Text.ToString() + TEXT("   (")
				+ FJadgTexts::Format(TEXT("dialogue.check.announce"), {FText::FromString(Choice.Skill), FText::AsNumber(Choice.Dc)}).ToString()
				+ TEXT(")"));
		}
		UJadgButton* Answer = Ui.Button(TEXT("control/ruled-line"), Text, [this, Index]
		{
			if (UJadgExploration* Talking = Exploration())
			{
				Talking->Choose(Index);
			}
		}, TEXT("text"), false);
		if (UButtonSlot* Content = Answer->GetContent() != nullptr ? Cast<UButtonSlot>(Answer->GetContent()->Slot) : nullptr)
		{
			Content->SetHorizontalAlignment(HAlign_Left);
		}
		if (Answer->LabelBlock != nullptr)
		{
			Answer->LabelBlock->SetFont(UJadgStyle::Get().Font(TEXT("body"), TEXT("body")));
			Answer->LabelBlock->SetJustification(ETextJustify::Left);
			Answer->LabelBlock->SetAutoWrapText(true);
		}
		FJadgUi::Add(Answers, Answer, FMargin(0.0f, 2.0f));
	}
	Voices->ClearChildren();
	const FString Voice = Game->DialogueSpeaker();
	for (const FJadgMember& Member : Game->Members())
	{
		const FString Id = Member.Id;
		UJadgButton* Pick = Ui.Button(TEXT("button/chip"), FText::FromString(Member.Name), [this, Id]
		{
			if (UJadgExploration* Talking = Exploration())
			{
				Talking->SetDialogueSpeaker(Id);
			}
		}, Id == Voice ? TEXT("goldLight") : TEXT("textOnPanel"), false, TEXT("caption"));
		Pick->LabelBlock->SetFont(UJadgStyle::Get().Font(TEXT("body"), TEXT("caption")));
		Pick->SetStyle([&] {
			FButtonStyle Look = Pick->GetStyle();
			if (Id == Voice)
			{
				Look.SetNormal(UJadgStyle::Get().Brush(TEXT("button/chip"), TEXT("selected")));
			}
			return Look;
		}());
		FJadgUi::Add(Voices, Ui.Sized(Pick, 230.0f, 44.0f), FMargin(4.0f, 0.0f));
	}
}

void UJadgDialogueScreen::Refresh()
{
	UJadgExploration* Game = Exploration();
	if (Game == nullptr || !Game->InDialogue())
	{
		return;
	}
	Speaker->SetText(FText::FromString(Game->Speaker()));
	Line->SetText(FText::FromString(Game->Line()));
	Check->SetText(FText::FromString(Game->LastCheck()));
	FSlateBrush Face = UJadgStyle::Get().Picture(Game->SpeakerPortrait(), FVector2D(278.0f, 278.0f));
	Portrait->SetBrush(Face);

	// Les réponses et les voix se refont quand la réplique ou la voix change.
	FString Now = Game->Line() + TEXT("|") + Game->DialogueSpeaker();
	for (const FJadgChoice& Choice : Game->Choices())
	{
		Now += TEXT("|") + Choice.Id;
	}
	if (Now != Shown)
	{
		Shown = Now;
		FillAnswers();
	}
}

// --- Le combat ----------------------------------------------------------------------------------

void UJadgCombatScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	// En haut à gauche : l'historique, qui montre et cache le journal.
	UJadgButton* History = Ui.Button(TEXT("button/default"), Key(TEXT("combat.history")), [this]
	{
		if (LogPanel != nullptr)
		{
			LogPanel->SetVisibility(LogPanel->IsVisible() ? ESlateVisibility::Collapsed : ESlateVisibility::SelfHitTestInvisible);
		}
	}, TEXT("textOnPanel"), false);
	FJadgUi::Place(Root, Ui.Sized(History, 200.0f, 56.0f), FVector2D(22.0f, 20.0f));
	Log = Ui.Column();
	LogPanel = Ui.Piece(TEXT("frame/subpanel-dark"), Log, FMargin(28.0f, 24.0f));
	FJadgUi::Place(Root, Ui.Sized(LogPanel, 560.0f, 0.0f), FVector2D(22.0f, 90.0f));

	// En haut au centre : le round et l'ordre d'initiative.
	UVerticalBox* Top = Ui.Column();
	RoundText = Ui.Text(FText::GetEmpty(), TEXT("title"), TEXT("body"), TEXT("goldLight"), false, ETextJustify::Center);
	FJadgUi::Add(Top, RoundText, FMargin(0.0f), 0.0f, HAlign_Center);
	Order = Ui.Row();
	FJadgUi::Add(Top, Order, FMargin(0.0f, 4.0f, 0.0f, 0.0f), 0.0f, HAlign_Center);
	FJadgUi::Place(Root, Ui.Piece(TEXT("frame/subpanel-dark"), Top, FMargin(30.0f, 14.0f)), FVector2D(0.0f, 16.0f), FVector2D::ZeroVector,
		FVector2D(0.5f, 0.0f), FVector2D(0.5f, 0.0f));

	// En haut à droite : la fiche et les options.
	UHorizontalBox* Corner = Ui.Row();
	for (const TPair<const TCHAR*, EJadgScreen>& Entry :
		TArray<TPair<const TCHAR*, EJadgScreen>>{{TEXT("hud.character"), EJadgScreen::Character}, {TEXT("menu.options"), EJadgScreen::Options}})
	{
		const EJadgScreen Target = Entry.Value;
		FJadgUi::Add(Corner, Ui.Sized(Ui.Button(TEXT("button/default"), Key(Entry.Key), [this, Target]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->Open(Target);
			}
		}, TEXT("textOnPanel"), false), 232.0f, 56.0f), FMargin(2.0f, 0.0f));
	}
	FJadgUi::Place(Root, Corner, FVector2D(-22.0f, 20.0f), FVector2D::ZeroVector, FVector2D(1.0f, 0.0f), FVector2D(1.0f, 0.0f));

	// À droite : la cible et ses circonstances.
	UVerticalBox* Aim = Ui.Column();
	TargetName = Ui.Text(FText::GetEmpty(), TEXT("title"), TEXT("body"), TEXT("textOnPanel"));
	FJadgUi::Add(Aim, TargetName);
	TargetLine = Ui.Text(FText::GetEmpty(), TEXT("body"), TEXT("body"), TEXT("textOnPanel"), true);
	FJadgUi::Add(Aim, TargetLine, FMargin(0.0f, 6.0f, 0.0f, 0.0f));
	FJadgUi::Place(Root, Ui.Sized(Ui.Piece(TEXT("frame/subpanel-dark"), Aim, FMargin(30.0f, 22.0f)), 420.0f, 0.0f), FVector2D(-22.0f, 0.0f),
		FVector2D::ZeroVector, FVector2D(1.0f, 0.42f), FVector2D(1.0f, 0.5f));

	// Au centre : ce qui se passe, et l'issue.
	Status = Ui.Text(FText::GetEmpty(), TEXT("body"), TEXT("body"), TEXT("textOnPanel"), false, ETextJustify::Center);
	Status->SetShadowOffset(FVector2D(2.0f, 2.0f));
	FJadgUi::Place(Root, Status, FVector2D(0.0f, -250.0f), FVector2D::ZeroVector, FVector2D(0.5f, 1.0f), FVector2D(0.5f, 1.0f));
	Outcome = Ui.Text(FText::GetEmpty(), TEXT("display"), TEXT("display"), TEXT("goldLight"), false, ETextJustify::Center);
	Outcome->SetShadowOffset(FVector2D(3.0f, 3.0f));
	FJadgUi::Place(Root, Outcome, FVector2D::ZeroVector, FVector2D::ZeroVector, FVector2D(0.5f, 0.38f), FVector2D(0.5f, 0.5f));

	// En bas : le combattant actif, son budget, ses actions, la fin du tour.
	UHorizontalBox* Bar = Ui.Row();
	UVerticalBox* Who = Ui.Column();
	FJadgUi::Add(Who, Ui.Image(TEXT("medallion/portrait-round"), TEXT("empty"), FVector2D(116.0f, 116.0f)), FMargin(0.0f), 0.0f, HAlign_Center);
	ActiveName = Ui.Text(FText::GetEmpty(), TEXT("body"), TEXT("body"), TEXT("textOnPanel"), false, ETextJustify::Center);
	FJadgUi::Add(Who, ActiveName, FMargin(0.0f, 2.0f), 0.0f, HAlign_Center);
	ActiveLife = Ui.Gauge(1.0f, TEXT("gem"));
	FJadgUi::Add(Who, Ui.Sized(ActiveLife, 140.0f, 20.0f), FMargin(0.0f), 0.0f, HAlign_Center);
	FJadgUi::Add(Bar, Ui.Sized(Who, 220.0f, 0.0f));
	UVerticalBox* Middle = Ui.Column();
	Budget = Ui.Text(FText::GetEmpty(), TEXT("title"), TEXT("body"), TEXT("goldLight"), false, ETextJustify::Center);
	FJadgUi::Add(Middle, Budget, FMargin(0.0f, 0.0f, 0.0f, 10.0f), 0.0f, HAlign_Center);
	Slots = Ui.Row();
	FJadgUi::Add(Middle, Slots, FMargin(0.0f), 0.0f, HAlign_Center);
	FJadgUi::Add(Bar, Middle, FMargin(16.0f, 0.0f), 1.0f);
	UVerticalBox* Ending = Ui.Column();
	UJadgButton* EndTurn = Ui.Button(TEXT("button/cancel"), Key(TEXT("combat.end_turn")), [this]
	{
		if (AJadgCombat* Fight = Combat())
		{
			Fight->EndTurn();
		}
	}, TEXT("textOnPanel"), false);
	FJadgUi::Add(Ending, Ui.Sized(EndTurn, 240.0f, 56.0f));
	FJadgUi::Add(Ending,
		Ui.Text(FJadgTexts::Format(TEXT("combat.end_turn_key"), {FText::FromString(UJadgControls::KeyLabel(TEXT("EndTurn")))}), TEXT("body"),
			TEXT("caption"), TEXT("textOnPanelMuted"), false, ETextJustify::Center),
		FMargin(0.0f, 8.0f), 0.0f, HAlign_Center);
	FJadgUi::Add(Bar, Ending);
	FJadgUi::Place(Root, Ui.Sized(Ui.Piece(TEXT("frame/panel-dark"), Bar, FMargin(44.0f, 30.0f)), 1340.0f, 290.0f), FVector2D(0.0f, -10.0f),
		FVector2D::ZeroVector, FVector2D(0.5f, 1.0f), FVector2D(0.5f, 1.0f));
}

void UJadgCombatScreen::FillOrder()
{
	AJadgCombat* Fight = Combat();
	FJadgUi Ui{WidgetTree, nullptr};
	Order->ClearChildren();
	for (const FJadgFighter& Fighter : Fight->Fighters())
	{
		UVerticalBox* Card = Ui.Column();
		const bool bActive = Fighter.Id == Fight->ActiveId();
		UOverlay* Face = Ui.Layers();
		FJadgUi::Add(Face, Ui.Image(TEXT("medallion/portrait-round"), TEXT("empty"), FVector2D(64.0f, 64.0f)));
		FJadgUi::Add(Face, Ui.Text(FText::FromString(Fighter.Name.Left(2)), TEXT("title"), TEXT("caption"), TEXT("text"), false, ETextJustify::Center),
			HAlign_Center, VAlign_Center);
		FJadgUi::Add(Card, Ui.Sized(Face, 64.0f, 64.0f), FMargin(0.0f), 0.0f, HAlign_Center);
		// L'actif en or, les alliés et les adversaires à leurs couleurs relevées (LOT-140), un mort grisé.
		UTextBlock* Name = Ui.Text(FText::FromString(Fighter.Name), TEXT("body"), TEXT("caption"),
			bActive ? TEXT("goldLight") : Fighter.bDead ? TEXT("textOnPanelMuted") : Fighter.bAlly ? TEXT("textAlly") : TEXT("textEnemy"), false,
			ETextJustify::Left);
		Name->SetClipping(EWidgetClipping::ClipToBounds);
		FJadgUi::Add(Card, Ui.Sized(Name, 92.0f, 0.0f), FMargin(0.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Order, Card, FMargin(3.0f, 0.0f));
	}
}

void UJadgCombatScreen::FillSlots()
{
	AJadgCombat* Fight = Combat();
	FJadgUi Ui{WidgetTree, &ButtonList};
	Slots->ClearChildren();
	const auto AddSlot = [&](const FString& Icon, const FText& Caption, const FText& Rank, bool bChosen, TFunction<void()> Action)
	{
		UVerticalBox* Cell = Ui.Column();
		UJadgButton* Pick = Ui.Button(TEXT("slot/action"), FText::GetEmpty(), MoveTemp(Action), TEXT("textOnPanel"), false);
		Pick->Label = Caption;
		UOverlay* Face = Ui.Layers();
		FJadgUi::Add(Face, Ui.Icon(Icon, FVector2D(56.0f, 56.0f)), HAlign_Center, VAlign_Center);
		Pick->SetContent(Face);
		if (bChosen)
		{
			FButtonStyle Look = Pick->GetStyle();
			Look.SetNormal(UJadgStyle::Get().Brush(TEXT("slot/action"), TEXT("active")));
			Pick->SetStyle(Look);
		}
		FJadgUi::Add(Cell, Ui.Sized(Pick, 80.0f, 80.0f), FMargin(0.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Cell, Ui.Text(Rank, TEXT("label"), TEXT("caption"), TEXT("goldLight"), false, ETextJustify::Center), FMargin(0.0f),
			0.0f, HAlign_Center);
		UTextBlock* Under = Ui.Text(Caption, TEXT("body"), TEXT("caption"), TEXT("textOnPanel"), true, ETextJustify::Center);
		Under->SetClipping(EWidgetClipping::ClipToBounds);
		FJadgUi::Add(Cell, Ui.Sized(Under, 110.0f, 0.0f), FMargin(0.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Slots, Cell, FMargin(6.0f, 0.0f));
	};
	AddSlot(TEXT("icon/action/melee"), FJadgTexts::Format(TEXT("combat.attack"), {FText::FromString(UJadgControls::KeyLabel(TEXT("Attack")))}),
		FText::FromString(UJadgControls::KeyLabel(TEXT("Attack"))), false,
		[this]
		{
			if (AJadgCombat* Here = Combat())
			{
				Here->Attack();
			}
		});
	const TArray<FString> Capacities = Fight->Capacities();
	for (int32 Index = 0; Index < Capacities.Num(); ++Index)
	{
		const int32 Rank = Index + 1;
		AddSlot(TEXT("icon/spell/magic-missile"), FText::FromString(Capacities[Index]), FText::AsNumber(Rank), Fight->CapacityRank() == Rank, [this, Rank]
		{
			if (AJadgCombat* Here = Combat())
			{
				// Le clic sur une capacité la choisit ; sur la capacité déjà choisie, il la lance.
				if (Here->CapacityRank() == Rank)
				{
					Here->Cast();
				}
				else
				{
					Here->SelectCapacity(Rank);
				}
			}
		});
	}
}

void UJadgCombatScreen::Refresh()
{
	AJadgCombat* Fight = Combat();
	if (Fight == nullptr)
	{
		return;
	}
	RoundText->SetText(FJadgTexts::Format(TEXT("combat.round"), {FText::AsNumber(Fight->Round())}));
	FString Now = FString::FromInt(Fight->ActiveId());
	const FJadgFighter* Active = nullptr;
	const FJadgFighter* Aimed = nullptr;
	const TArray<FJadgFighter> Fighters = Fight->Fighters();
	for (const FJadgFighter& Fighter : Fighters)
	{
		Now += FString::Printf(TEXT("|%d:%d:%d"), Fighter.Id, Fighter.HitPoints, Fighter.bDead ? 1 : 0);
		Active = Fighter.Id == Fight->ActiveId() ? &Fighter : Active;
		Aimed = Fighter.Id == Fight->TargetId() ? &Fighter : Aimed;
	}
	if (Now != Shown)
	{
		Shown = Now;
		FillOrder();
	}
	const FString SlotsNow = FString::FromInt(Fight->ActiveId()) + TEXT("|") + FString::FromInt(Fight->CapacityRank()) + TEXT("|")
		+ FString::Join(Fight->Capacities(), TEXT(";"));
	if (SlotsNow != SlotsShown)
	{
		SlotsShown = SlotsNow;
		FillSlots();
	}
	if (Active != nullptr)
	{
		ActiveName->SetText(FText::FromString(Active->Name));
		ActiveLife->SetPercent(Active->MaxHitPoints > 0 ? static_cast<float>(Active->HitPoints) / Active->MaxHitPoints : 0.0f);
	}
	Budget->SetText(FJadgTexts::Format(TEXT("combat.budget"), {FText::AsNumber(FMath::RoundToInt32(Fight->MovementLeft() * 10.0f) / 10.0f)}));
	if (Aimed != nullptr)
	{
		TargetName->SetText(FText::FromString(Aimed->Name));
		TargetLine->SetText(FJadgTexts::Format(TEXT("combat.target"),
			{Fraction(Aimed->HitPoints, Aimed->MaxHitPoints), FText::FromString(Fight->TargetCircumstances())}));
	}
	else
	{
		TargetName->SetText(Key(TEXT("combat.target_title")));
		TargetLine->SetText(Key(TEXT("combat.target_none")));
	}
	const FString Refused = Fight->Refusal();
	Status->SetText(!Refused.IsEmpty()		  ? FText::FromString(Refused)
					: Fight->IsBusy()		  ? Key(TEXT("combat.busy"))
					: !Fight->IsPlayerTurn() && Active != nullptr ? FJadgTexts::Format(TEXT("combat.enemy_turn"), {FText::FromString(Active->Name)})
											  : FText::GetEmpty());
	const int32 Code = Fight->OutcomeCode();
	Outcome->SetText(Code == 0 ? Key(TEXT("combat.victory")) : Code == 1 ? Key(TEXT("combat.flight")) : Code == 2 ? Key(TEXT("combat.defeat")) : FText::GetEmpty());

	const TArray<FString> Lines = Fight->Journal(10);
	const FString LogNow = FString::Join(Lines, TEXT("|"));
	if (LogNow != LogShown)
	{
		LogShown = LogNow;
		Log->ClearChildren();
		FJadgUi Ui{WidgetTree, nullptr};
		for (const FString& Entry : Lines)
		{
			FJadgUi::Add(Log, Ui.Text(FText::FromString(Entry), TEXT("body"), TEXT("caption"), TEXT("textOnPanel"), true));
		}
	}
}

// --- La table des écrans --------------------------------------------------------------------------

UClass* JadgScreenClass(EJadgScreen Kind)
{
	switch (Kind)
	{
	case EJadgScreen::Hud: return UJadgHudScreen::StaticClass();
	case EJadgScreen::Dialogue: return UJadgDialogueScreen::StaticClass();
	case EJadgScreen::Combat: return UJadgCombatScreen::StaticClass();
	case EJadgScreen::Title: return UJadgTitleScreen::StaticClass();
	case EJadgScreen::Pause: return UJadgPauseScreen::StaticClass();
	case EJadgScreen::Options: return UJadgOptionsScreen::StaticClass();
	case EJadgScreen::NewGame:
	case EJadgScreen::Party: return UJadgPartyScreen::StaticClass();
	case EJadgScreen::Character: return UJadgCharacterScreen::StaticClass();
	case EJadgScreen::Equipment: return UJadgEquipmentScreen::StaticClass();
	case EJadgScreen::Journal: return UJadgJournalScreen::StaticClass();
	case EJadgScreen::Map: return UJadgMapScreen::StaticClass();
	case EJadgScreen::Ending:
	case EJadgScreen::Death: return UJadgEndScreen::StaticClass();
	case EJadgScreen::Debug: return UJadgDebugScreen::StaticClass();
	}
	return nullptr;
}
