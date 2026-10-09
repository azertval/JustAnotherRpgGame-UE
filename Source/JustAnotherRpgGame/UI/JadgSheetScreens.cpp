// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// La fiche et le groupe : groupe et nouvelle partie, personnage, équipement, journal (LOT-1020).

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/HorizontalBox.h"
#include "Components/Image.h"
#include "Components/Overlay.h"
#include "Components/ProgressBar.h"
#include "Components/ScrollBox.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/UniformGridPanel.h"
#include "Components/VerticalBox.h"
#include "Game/JadgExploration.h"
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

	FText Signed(int32 Value)
	{
		return FText::FromString(FString::Printf(TEXT("%+d"), Value));
	}

	/// Le texte d'une clé faite d'un préfixe et d'un identifiant ; l'identifiant s'il manque.
	FText Named(const FString& Prefix, const FString& Id)
	{
		// Les clés écrivent un identifiant à tirets avec des soulignés (`rpg.skill.animal_handling`).
		for (const FString& Wanted : {Prefix + Id, Prefix + Id.Replace(TEXT("-"), TEXT("_"))})
		{
			if (FJadgTexts::Has(FJadgTexts::Language(), Wanted) || FJadgTexts::Has(TEXT("fr"), Wanted))
			{
				return FJadgTexts::Get(Wanted);
			}
		}
		return FText::FromString(Id);
	}

	/// Le membre qu'un écran de fiche montre : son argument, ou le meneur.
	FString MemberOf(const UJadgScreen& Screen, const UJadgExploration& Game)
	{
		FString Wanted;
		if (!Screen.Argument.Split(TEXT("#"), &Wanted, nullptr))
		{
			Wanted = Screen.Argument;
		}
		const TArray<FJadgMember> Members = Game.Members();
		for (const FJadgMember& Member : Members)
		{
			if (Member.Id == Wanted)
			{
				return Member.Id;
			}
		}
		return Members.IsEmpty() ? FString() : Members[0].Id;
	}

	/// Un médaillon de valeur (`medallion/derived-stat`) : la valeur au centre, le libellé dessous.
	UWidget* Medallion(FJadgUi& Ui, FName Piece, float Side, const FText& Value, const FText& Label)
	{
		UVerticalBox* Column = Ui.Column();
		UOverlay* Disc = Ui.Layers();
		FJadgUi::Add(Disc, Ui.Image(Piece, NAME_None, FVector2D(Side, Side)));
		FJadgUi::Add(Disc, Ui.Text(Value, TEXT("display"), TEXT("section"), TEXT("text"), false, ETextJustify::Center), HAlign_Center, VAlign_Center);
		FJadgUi::Add(Column, Ui.Sized(Disc, Side, Side), FMargin(0.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Column, Ui.Text(Label, TEXT("title"), TEXT("caption"), TEXT("text"), false, ETextJustify::Center), FMargin(0.0f, 2.0f), 0.0f,
			HAlign_Center);
		return Column;
	}

	/// Le choix d'un membre, en haut d'un écran de fiche : un onglet par membre.
	UWidget* MemberTabs(FJadgUi& Ui, UJadgScreen& Screen, const UJadgExploration& Game, const FString& Shown)
	{
		UHorizontalBox* Row = Ui.Row();
		for (const FJadgMember& Member : Game.Members())
		{
			const FString Id = Member.Id;
			const EJadgScreen Kind = Screen.Kind;
			UJadgButton* Tab = Ui.Button(TEXT("tab/segment"), FText::FromString(Member.Name), [&Screen, Id, Kind]
			{
				if (AJadgHud* Manager = Screen.Hud())
				{
					Manager->Open(Kind, Id);
				}
			}, Id == Shown ? TEXT("surfaceAlt") : TEXT("text"), true, TEXT("caption"));
			if (Id == Shown)
			{
				FButtonStyle Look = Tab->GetStyle();
				Look.SetNormal(UJadgStyle::Get().Brush(TEXT("tab/segment"), TEXT("active")));
				Tab->SetStyle(Look);
			}
			FJadgUi::Add(Row, Ui.Sized(Tab, 270.0f, 50.0f), FMargin(2.0f, 0.0f));
		}
		return Row;
	}
}

// --- Le groupe ----------------------------------------------------------------------------------

void UJadgPartyScreen::Reopen()
{
	if (AJadgHud* Manager = Hud())
	{
		Manager->Open(Kind, Chosen);
	}
}

void UJadgPartyScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	UJadgExploration* Game = Exploration();
	const bool bNewGame = Kind == EJadgScreen::NewGame;
	UCanvasPanel* Content = Page(Ui, Root, Key(bNewGame ? TEXT("party.new_game") : TEXT("party.title")), true);
	if (Game == nullptr)
	{
		return;
	}
	const TArray<FJadgMember> Members = Game->Members();
	Chosen = MemberOf(*this, *Game);

	// L'ordre de marche : une carte par membre, le meneur en tête.
	UVerticalBox* Column = Ui.Column();
	FJadgUi::Add(Column, Section(Ui, Key(TEXT("party.order")), true), FMargin(0.0f, 0.0f, 0.0f, 20.0f), 0.0f, HAlign_Left);
	UHorizontalBox* Cards = Ui.Row();
	for (int32 Index = 0; Index < Members.Num(); ++Index)
	{
		const FJadgMember& Member = Members[Index];
		FJadgSheetView Sheet;
		Game->Sheet(Member.Id, Sheet);
		UVerticalBox* Card = Ui.Column();
		FJadgUi::Add(Card, Ui.Image(TEXT("medallion/portrait-round"), TEXT("empty"), FVector2D(180.0f, 180.0f)), FMargin(0.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Card, Ui.Text(FText::FromString(Member.Name), TEXT("title"), TEXT("body"), TEXT("text"), true, ETextJustify::Center),
			FMargin(0.0f, 6.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Card,
			Ui.Text(FJadgTexts::Format(TEXT("party.class_level"), {Named(TEXT("rpg.class."), Sheet.ClassId), FText::AsNumber(Sheet.Level)}),
				TEXT("lore"), TEXT("body"), TEXT("textMuted"), false, ETextJustify::Center),
			FMargin(0.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Card,
			Ui.Text(FJadgTexts::Format(TEXT("party.stats"),
						{FText::AsNumber(Sheet.HitPoints), FText::AsNumber(Sheet.ArmorClass), FText::AsNumber(FMath::RoundToInt32(Sheet.SpeedMetres))}),
				TEXT("body"), TEXT("caption"), TEXT("text"), false, ETextJustify::Center),
			FMargin(0.0f, 4.0f), 0.0f, HAlign_Center);
		const FText Rank = Index == 0 ? Key(TEXT("party.leader")) : FJadgTexts::Format(TEXT("party.rank"), {FText::AsNumber(Index + 1)});
		FJadgUi::Add(Card, Ui.Text(Rank, TEXT("title"), TEXT("caption"), Index == 0 ? TEXT("gem") : TEXT("textMuted"), false, ETextJustify::Center),
			FMargin(0.0f, 4.0f), 0.0f, HAlign_Center);
		const FString Id = Member.Id;
		UJadgButton* Pick = Ui.Button(TEXT("button/chip"), Key(TEXT("party.choose")), [this, Id]
		{
			Chosen = Id;
			Reopen();
		}, Id == Chosen ? TEXT("goldLight") : TEXT("textOnPanel"), true, TEXT("caption"));
		if (Id == Chosen)
		{
			FButtonStyle Look = Pick->GetStyle();
			Look.SetNormal(UJadgStyle::Get().Brush(TEXT("button/chip"), TEXT("selected")));
			Pick->SetStyle(Look);
		}
		FJadgUi::Add(Card, Ui.Sized(Pick, 200.0f, 44.0f), FMargin(0.0f, 10.0f), 0.0f, HAlign_Center);
		const FName Frame = Id == Chosen ? TEXT("frame/subpanel-parchment") : TEXT("frame/subpanel-parchment");
		FJadgUi::Add(Cards, Ui.Sized(Ui.Piece(Frame, Card, FMargin(24.0f, 24.0f), Id == Chosen ? TEXT("normal") : TEXT("empty")), 400.0f, 470.0f),
			FMargin(8.0f, 0.0f));
	}
	FJadgUi::Add(Column, Cards, FMargin(0.0f), 0.0f, HAlign_Center);

	// Les gestes sur le membre choisi.
	UHorizontalBox* Foot = Ui.Row();
	const auto Act = [this, &Ui, Foot](const TCHAR* Label, FName Piece, TFunction<void()> Action)
	{
		FJadgUi::Add(Foot, Ui.Sized(Ui.Button(Piece, Key(Label), MoveTemp(Action)), 280.0f, 56.0f), FMargin(8.0f, 0.0f));
	};
	Act(TEXT("party.lead"), TEXT("button/primary"), [this]
	{
		if (UJadgExploration* Here = Exploration())
		{
			Here->SetLeader(Chosen);
		}
		Reopen();
	});
	if (bNewGame)
	{
		Act(TEXT("party.start"), TEXT("button/apply"), [this]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->StartNewGame(Chosen);
			}
		});
	}
	else
	{
		Act(TEXT("party.forward"), TEXT("button/default"), [this]
		{
			if (UJadgExploration* Here = Exploration())
			{
				Here->MoveMember(Chosen, -1);
			}
			Reopen();
		});
		Act(TEXT("party.backward"), TEXT("button/default"), [this]
		{
			if (UJadgExploration* Here = Exploration())
			{
				Here->MoveMember(Chosen, 1);
			}
			Reopen();
		});
		Act(TEXT("party.sheet"), TEXT("button/secondary"), [this]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->Open(EJadgScreen::Character, Chosen);
			}
		});
	}
	FJadgUi::Add(Column, Foot, FMargin(0.0f, 40.0f, 0.0f, 0.0f), 0.0f, HAlign_Center);
	FJadgUi::Add(Column, Ui.Text(Key(bNewGame ? TEXT("party.new_game_hint") : TEXT("party.hint")), TEXT("body"), TEXT("caption"), TEXT("textMuted"), true,
							 ETextJustify::Center),
		FMargin(0.0f, 24.0f, 0.0f, 0.0f), 0.0f, HAlign_Center);
	FJadgUi::Fill(Content, Column);
}

// --- Le personnage ------------------------------------------------------------------------------

void UJadgCharacterScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	UJadgExploration* Game = Exploration();
	UCanvasPanel* Content = Page(Ui, Root, Key(TEXT("sheet.title")), true);
	FJadgSheetView Sheet;
	if (Game == nullptr || !Game->Sheet(MemberOf(*this, *Game), Sheet))
	{
		return;
	}
	FJadgUi::Place(Content, MemberTabs(Ui, *this, *Game, Sheet.Id), FVector2D(0.0f, -50.0f), FVector2D::ZeroVector, FVector2D(0.5f, 0.0f),
		FVector2D(0.5f, 0.0f));

	// À gauche : les six caractéristiques autour du portrait, les valeurs dérivées dessous.
	UCanvasPanel* Left = Ui.Canvas();
	FJadgUi::Place(Left, Ui.Image(TEXT("medallion/portrait-round"), TEXT("empty"), FVector2D(250.0f, 250.0f)), FVector2D(160.0f, 120.0f),
		FVector2D(250.0f, 250.0f));
	const TArray<FVector2D> Around = {{40.0f, 10.0f}, {390.0f, 10.0f}, {0.0f, 200.0f}, {430.0f, 200.0f}, {80.0f, 380.0f}, {350.0f, 380.0f}};
	for (int32 Index = 0; Index < Sheet.Abilities.Num() && Index < Around.Num(); ++Index)
	{
		const FJadgAbilityView& Ability = Sheet.Abilities[Index];
		const FText Label = FText::FromString(Named(TEXT("sheet.ability."), Ability.Id).ToString() + TEXT(" ") + Signed(Ability.Modifier).ToString());
		FJadgUi::Place(Left, Medallion(Ui, TEXT("medallion/ability"), 130.0f, FText::AsNumber(Ability.Score), Label), Around[Index],
			FVector2D(140.0f, 170.0f));
	}
	UHorizontalBox* Derived = Ui.Row();
	FJadgUi::Add(Derived, Medallion(Ui, TEXT("medallion/derived-stat"), 104.0f, FText::AsNumber(Sheet.ArmorClass), Key(TEXT("sheet.armor_class"))),
		FMargin(10.0f, 0.0f));
	FJadgUi::Add(Derived, Medallion(Ui, TEXT("medallion/derived-stat"), 104.0f, Signed(Sheet.Initiative), Key(TEXT("sheet.initiative"))),
		FMargin(10.0f, 0.0f));
	FJadgUi::Add(Derived,
		Medallion(Ui, TEXT("medallion/derived-stat"), 104.0f, FText::FromString(FString::Printf(TEXT("%.0f m"), Sheet.SpeedMetres)), Key(TEXT("sheet.speed"))),
		FMargin(10.0f, 0.0f));
	FJadgUi::Add(Derived, Medallion(Ui, TEXT("medallion/derived-stat"), 104.0f, Signed(Sheet.Proficiency), Key(TEXT("sheet.proficiency"))),
		FMargin(10.0f, 0.0f));
	FJadgUi::Add(Derived, Medallion(Ui, TEXT("medallion/derived-stat"), 104.0f, FText::AsNumber(Sheet.PassivePerception), Key(TEXT("sheet.passive"))),
		FMargin(10.0f, 0.0f));
	FJadgUi::Place(Left, Derived, FVector2D(0.0f, 600.0f));
	FJadgUi::Place(Content, Left, FVector2D(0.0f, 30.0f), FVector2D(600.0f, 800.0f));

	// Au centre : l'identité, les points de vie, l'expérience, la signature.
	UVerticalBox* Middle = Ui.Column();
	FJadgUi::Add(Middle, Section(Ui, Key(TEXT("sheet.identity")), true), FMargin(0.0f, 0.0f, 0.0f, 20.0f), 0.0f, HAlign_Center);
	FJadgUi::Add(Middle, Field(Ui, Key(TEXT("sheet.name")), FText::FromString(Sheet.Name)), FMargin(0.0f, 6.0f));
	FJadgUi::Add(Middle, Field(Ui, Key(TEXT("sheet.class")), Named(TEXT("rpg.class."), Sheet.ClassId)), FMargin(0.0f, 6.0f));
	FJadgUi::Add(Middle, Field(Ui, Key(TEXT("sheet.level")), FText::AsNumber(Sheet.Level)), FMargin(0.0f, 6.0f));
	FJadgUi::Add(Middle, Field(Ui, Key(TEXT("sheet.background")), Named(TEXT("rpg.background."), Sheet.BackgroundId)), FMargin(0.0f, 6.0f));
	FJadgUi::Add(Middle, Field(Ui, Key(TEXT("sheet.species")), Named(TEXT("rpg.species."), Sheet.SpeciesId)), FMargin(0.0f, 6.0f));
	const auto Bar = [&](const TCHAR* Label, const FText& Value, float Share, FName Colour)
	{
		UHorizontalBox* Line = Ui.Row();
		UTextBlock* Tag = Ui.Text(Key(Label), TEXT("label"), TEXT("caption"), TEXT("textOnPanel"));
		FJadgUi::Add(Line, Ui.Sized(Ui.Piece(TEXT("plate/field-tag"), Tag, FMargin(14.0f, 8.0f, 40.0f, 8.0f)), 210.0f, 0.0f));
		FJadgUi::Add(Line, Ui.Text(Value, TEXT("label"), TEXT("body"), TEXT("text"), false, ETextJustify::Right), FMargin(0.0f), 1.0f);
		FJadgUi::Add(Middle, Line, FMargin(0.0f, 30.0f, 0.0f, 6.0f));
		FJadgUi::Add(Middle, Ui.Sized(Ui.Gauge(Share, Colour), 0.0f, 28.0f));
	};
	Bar(TEXT("sheet.hit_points"), FText::FromString(FString::Printf(TEXT("%d / %d"), Sheet.HitPoints, Sheet.MaxHitPoints)),
		Sheet.MaxHitPoints > 0 ? static_cast<float>(Sheet.HitPoints) / Sheet.MaxHitPoints : 0.0f, TEXT("gem"));
	Bar(TEXT("sheet.experience"), FText::FromString(FString::Printf(TEXT("%d / —"), Sheet.Experience)), 0.0f, TEXT("goldLight"));
	UOverlay* Seal = Ui.Layers();
	FJadgUi::Add(Seal, Ui.Image(TEXT("ornament/wax-seal")), HAlign_Left, VAlign_Center, FMargin(30.0f, 0.0f));
	FJadgUi::Add(Seal, Ui.Text(FText::FromString(Sheet.Name), TEXT("signature"), TEXT("screenTitle"), TEXT("text"), false, ETextJustify::Right), HAlign_Right,
		VAlign_Center, FMargin(30.0f, 0.0f));
	FJadgUi::Add(Middle, Ui.Sized(Ui.Piece(TEXT("frame/subpanel-parchment"), Seal, FMargin(20.0f), TEXT("normal")), 0.0f, 180.0f),
		FMargin(0.0f, 50.0f, 0.0f, 0.0f));
	FJadgUi::Place(Content, Middle, FVector2D(640.0f, 30.0f), FVector2D(560.0f, 800.0f));

	// À droite : les compétences, la maîtrise marquée, le bonus au jet.
	UVerticalBox* Right = Ui.Column();
	FJadgUi::Add(Right, Section(Ui, Key(TEXT("sheet.skills")), true), FMargin(0.0f, 0.0f, 0.0f, 14.0f), 0.0f, HAlign_Center);
	for (const FJadgSkillView& Skill : Sheet.Skills)
	{
		UHorizontalBox* Line = Ui.Row();
		FJadgUi::Add(Line, Ui.Image(TEXT("control/pip"), Skill.bProficient ? TEXT("filled") : TEXT("empty"), FVector2D(20.0f, 20.0f)),
			FMargin(0.0f, 0.0f, 10.0f, 0.0f));
		FJadgUi::Add(Line, Ui.Icon(TEXT("icon/skill/") + Skill.Id.Replace(TEXT("_"), TEXT("-")), FVector2D(30.0f, 30.0f)), FMargin(0.0f, 0.0f, 10.0f, 0.0f));
		FJadgUi::Add(Line, Ui.Text(Named(TEXT("rpg.skill."), Skill.Id), TEXT("body"), TEXT("body"), TEXT("text")), FMargin(0.0f), 1.0f);
		UTextBlock* Bonus = Ui.Text(Signed(Skill.Bonus), TEXT("label"), TEXT("caption"), TEXT("text"), false, ETextJustify::Center);
		FJadgUi::Add(Line, Ui.Sized(Ui.Piece(TEXT("control/value-box"), Bonus, FMargin(6.0f, 2.0f)), 60.0f, 30.0f));
		FJadgUi::Add(Right, Line, FMargin(0.0f, 2.0f));
	}
	FJadgUi::Place(Content, Right, FVector2D(1240.0f, 30.0f), FVector2D(488.0f, 820.0f));
}

// --- L'équipement -------------------------------------------------------------------------------

void UJadgEquipmentScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	UJadgExploration* Game = Exploration();
	UCanvasPanel* Content = Page(Ui, Root, Key(TEXT("inventory.title")), true);
	FJadgInventoryView Carried;
	FJadgSheetView Sheet;
	const FString Member = Game != nullptr ? MemberOf(*this, *Game) : FString();
	if (Game == nullptr || !Game->Inventory(Member, Carried) || !Game->Sheet(Member, Sheet))
	{
		return;
	}
	FJadgUi::Place(Content, MemberTabs(Ui, *this, *Game, Member), FVector2D(0.0f, -50.0f), FVector2D::ZeroVector, FVector2D(0.5f, 0.0f),
		FVector2D(0.5f, 0.0f));
	TArray<FJadgItemView> All = Carried.Equipped;
	All.Append(Carried.Backpack);
	Selected = FMath::Clamp(FCString::Atoi(*Argument.RightChop(Argument.Find(TEXT("#")) + 1)), -1, All.Num() - 1);
	if (!Argument.Contains(TEXT("#")))
	{
		Selected = All.IsEmpty() ? -1 : 0;
	}

	// Une case d'objet : le cadre du kit, le nom, la quantité ; le clic la choisit.
	const auto ItemCell = [this, &Ui, &All, Member](int32 Index, const FText& Empty)
	{
		const bool bFilled = All.IsValidIndex(Index);
		const FText Name = bFilled ? FText::FromString(All[Index].Name) : Empty;
		UJadgButton* Cell = Ui.Button(TEXT("slot/item"), FText::GetEmpty(), [this, Index, Member]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->Open(Kind, Member + TEXT("#") + FString::FromInt(Index));
			}
		}, TEXT("textOnPanel"), true);
		Cell->Label = Name;
		UOverlay* Face = Ui.Layers();
		FJadgUi::Add(Face, Ui.Text(Name, TEXT("body"), TEXT("caption"), TEXT("textOnPanel"), true, ETextJustify::Center), HAlign_Center, VAlign_Center,
			FMargin(10.0f));
		if (bFilled && All[Index].Quantity > 1)
		{
			FJadgUi::Add(Face, Ui.Piece(TEXT("slot/quantity-pip"), Ui.Text(FText::AsNumber(All[Index].Quantity), TEXT("label"), TEXT("caption"),
															   TEXT("textOnPanel")),
								   FMargin(8.0f, 0.0f)),
				HAlign_Right, VAlign_Bottom, FMargin(4.0f));
		}
		Cell->SetContent(Face);
		if (Index == Selected)
		{
			FButtonStyle Look = Cell->GetStyle();
			Look.SetNormal(UJadgStyle::Get().Brush(TEXT("slot/item"), TEXT("selected")));
			Cell->SetStyle(Look);
		}
		else if (bFilled && !All[Index].Slot.IsEmpty())
		{
			FButtonStyle Look = Cell->GetStyle();
			Look.SetNormal(UJadgStyle::Get().Brush(TEXT("slot/item"), TEXT("equipped")));
			Cell->SetStyle(Look);
		}
		return Ui.Sized(Cell, 116.0f, 116.0f);
	};

	// À gauche : ce qui est porté, et les valeurs dérivées.
	UVerticalBox* Left = Ui.Column();
	FJadgUi::Add(Left, Section(Ui, Key(TEXT("inventory.equipped")), true), FMargin(0.0f, 0.0f, 0.0f, 16.0f), 0.0f, HAlign_Center);
	UUniformGridPanel* Worn = Ui.Tree->ConstructWidget<UUniformGridPanel>();
	Worn->SetSlotPadding(FMargin(10.0f));
	for (int32 Index = 0; Index < 6; ++Index)
	{
		Worn->AddChildToUniformGrid(ItemCell(Index < Carried.Equipped.Num() ? Index : -1, FText::GetEmpty()), Index / 2, Index % 2);
	}
	FJadgUi::Add(Left, Worn, FMargin(0.0f), 0.0f, HAlign_Center);
	UHorizontalBox* Stats = Ui.Row();
	FJadgUi::Add(Stats, Medallion(Ui, TEXT("medallion/derived-stat"), 96.0f, FText::AsNumber(Sheet.ArmorClass), Key(TEXT("sheet.armor_class"))),
		FMargin(8.0f, 0.0f));
	FJadgUi::Add(Stats,
		Medallion(Ui, TEXT("medallion/derived-stat"), 96.0f, FText::FromString(FString::Printf(TEXT("%.0f m"), Sheet.SpeedMetres)), Key(TEXT("sheet.speed"))),
		FMargin(8.0f, 0.0f));
	FJadgUi::Add(Stats, Medallion(Ui, TEXT("medallion/derived-stat"), 96.0f, Signed(Sheet.Initiative), Key(TEXT("sheet.initiative"))), FMargin(8.0f, 0.0f));
	FJadgUi::Add(Left, Stats, FMargin(0.0f, 30.0f, 0.0f, 0.0f), 0.0f, HAlign_Center);
	FJadgUi::Place(Content, Left, FVector2D(0.0f, 30.0f), FVector2D(480.0f, 800.0f));

	// Au centre : le sac, la charge, la bourse.
	UVerticalBox* Middle = Ui.Column();
	FJadgUi::Add(Middle, Section(Ui, Key(TEXT("inventory.bag")), true), FMargin(0.0f, 0.0f, 0.0f, 16.0f), 0.0f, HAlign_Center);
	UUniformGridPanel* Bag = Ui.Tree->ConstructWidget<UUniformGridPanel>();
	Bag->SetSlotPadding(FMargin(8.0f));
	for (int32 Cell = 0; Cell < 20; ++Cell)
	{
		const int32 Index = Cell < Carried.Backpack.Num() ? Carried.Equipped.Num() + Cell : -1;
		Bag->AddChildToUniformGrid(ItemCell(Index, FText::GetEmpty()), Cell / 5, Cell % 5);
	}
	FJadgUi::Add(Middle, Bag, FMargin(0.0f), 0.0f, HAlign_Center);
	const float Kilos = Carried.CarriedGrams / 1000.0f;
	const float Capacity = Carried.CapacityGrams / 1000.0f;
	FJadgUi::Add(Middle,
		Ui.Text(FJadgTexts::Format(TEXT("inventory.weight"),
					{FText::FromString(FString::Printf(TEXT("%.1f kg"), Kilos)), FText::FromString(FString::Printf(TEXT("%.1f kg"), Capacity))}),
			TEXT("body"), TEXT("body"), TEXT("text")),
		FMargin(0.0f, 24.0f, 0.0f, 6.0f));
	FJadgUi::Add(Middle, Ui.Sized(Ui.Gauge(Capacity > 0.0f ? Kilos / Capacity : 0.0f, TEXT("panelEdge")), 0.0f, 24.0f));
	UTextBlock* Purse = Ui.Text(FJadgTexts::Format(TEXT("inventory.purse"), {FText::AsNumber(Carried.PurseCopper / 100)}), TEXT("title"), TEXT("body"),
		TEXT("goldLight"));
	FJadgUi::Add(Middle, Ui.Piece(TEXT("plate/section-bar"), Purse, FMargin(48.0f, 10.0f, 96.0f, 10.0f)), FMargin(0.0f, 24.0f, 0.0f, 0.0f), 0.0f,
		HAlign_Left);
	FJadgUi::Place(Content, Middle, FVector2D(520.0f, 30.0f), FVector2D(700.0f, 800.0f));

	// À droite : l'objet choisi.
	UVerticalBox* Right = Ui.Column();
	const bool bChosen = All.IsValidIndex(Selected);
	FJadgUi::Add(Right, Section(Ui, bChosen ? FText::FromString(All[Selected].Name) : Key(TEXT("inventory.none")), true), FMargin(0.0f, 0.0f, 0.0f, 16.0f),
		0.0f, HAlign_Center);
	if (bChosen)
	{
		const FJadgItemView& Item = All[Selected];
		FJadgUi::Add(Right, Field(Ui, Key(TEXT("inventory.slot")),
								Item.Slot.IsEmpty() ? Key(TEXT("inventory.in_bag")) : Named(TEXT("inventory.slot."), Item.Slot)),
			FMargin(0.0f, 6.0f));
		FJadgUi::Add(Right, Field(Ui, Key(TEXT("inventory.quantity")), FText::AsNumber(Item.Quantity)), FMargin(0.0f, 6.0f));
		FJadgUi::Add(Right, Field(Ui, Key(TEXT("inventory.item_weight")), FText::FromString(FString::Printf(TEXT("%.1f kg"), Item.WeightGrams / 1000.0f))),
			FMargin(0.0f, 6.0f));
	}
	FJadgUi::Place(Content, Right, FVector2D(1260.0f, 30.0f), FVector2D(468.0f, 800.0f));
}

// --- Le journal ---------------------------------------------------------------------------------

void UJadgJournalScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	UJadgExploration* Game = Exploration();
	UCanvasPanel* Content = Page(Ui, Root, Key(TEXT("journal.title")), true);
	if (Game == nullptr)
	{
		return;
	}
	const TArray<FJadgQuestView> Quests = Game->Journal();
	Seen = Quests.Num();
	Selected = FMath::Clamp(FCString::Atoi(*Argument), 0, FMath::Max(0, Quests.Num() - 1));

	// À gauche : les quêtes commencées, leur état.
	UVerticalBox* Left = Ui.Column();
	FJadgUi::Add(Left, Section(Ui, Key(TEXT("journal.quests")), true), FMargin(0.0f, 0.0f, 0.0f, 16.0f), 0.0f, HAlign_Center);
	if (Quests.IsEmpty())
	{
		FJadgUi::Add(Left, Ui.Text(Key(TEXT("journal.empty")), TEXT("lore"), TEXT("body"), TEXT("textMuted"), true));
	}
	for (int32 Index = 0; Index < Quests.Num(); ++Index)
	{
		const FText Line = FText::FromString(Quests[Index].Title + TEXT("  —  ") + Key(*(TEXT("journal.status.") + Quests[Index].Status)).ToString());
		UJadgButton* Pick = Ui.Button(TEXT("control/ruled-line"), Line, [this, Index]
		{
			if (AJadgHud* Manager = Hud())
			{
				Manager->Open(Kind, FString::FromInt(Index));
			}
		}, Index == Selected ? TEXT("gem") : TEXT("text"), true);
		FJadgUi::Add(Left, Ui.Sized(Pick, 0.0f, 56.0f), FMargin(0.0f, 2.0f));
	}
	FJadgUi::Place(Content, Ui.Piece(TEXT("frame/subpanel-parchment"), Left, FMargin(36.0f, 30.0f), TEXT("normal")), FVector2D(0.0f, 20.0f),
		FVector2D(640.0f, 800.0f));

	// À droite : la quête choisie, ses étapes ; la dernière est l'objectif du moment.
	UVerticalBox* Right = Ui.Column();
	if (Quests.IsValidIndex(Selected))
	{
		const FJadgQuestView& Quest = Quests[Selected];
		FJadgUi::Add(Right, Section(Ui, FText::FromString(Quest.Title), true), FMargin(0.0f, 0.0f, 0.0f, 16.0f), 0.0f, HAlign_Center);
		FJadgUi::Add(Right, Ui.Text(Key(TEXT("journal.objectives")), TEXT("title"), TEXT("body"), TEXT("text")), FMargin(0.0f, 0.0f, 0.0f, 8.0f));
		for (int32 Step = 0; Step < Quest.Steps.Num(); ++Step)
		{
			const bool bCurrent = Step == Quest.Steps.Num() - 1 && Quest.Status == TEXT("active");
			UHorizontalBox* Line = Ui.Row();
			FJadgUi::Add(Line, Ui.Image(TEXT("control/pip"), bCurrent ? TEXT("empty") : TEXT("filled"), FVector2D(22.0f, 22.0f)),
				FMargin(0.0f, 4.0f, 12.0f, 0.0f), 0.0f, VAlign_Top);
			FJadgUi::Add(Line, Ui.Text(FText::FromString(Quest.Steps[Step]), bCurrent ? TEXT("body") : TEXT("lore"), TEXT("body"),
								   bCurrent ? TEXT("text") : TEXT("textMuted"), true),
				FMargin(0.0f), 1.0f);
			FJadgUi::Add(Right, Line, FMargin(0.0f, 6.0f));
		}
	}
	FJadgUi::Place(Content, Ui.Piece(TEXT("frame/subpanel-parchment"), Right, FMargin(40.0f, 30.0f), TEXT("normal")), FVector2D(680.0f, 20.0f),
		FVector2D(1048.0f, 800.0f));
}

void UJadgJournalScreen::Refresh()
{
	// Une quête qui commence pendant qu'on lit le journal s'y voit sans le fermer (`EX-IHM-090`).
	const UJadgExploration* Game = Exploration();
	if (Game != nullptr && Seen >= 0 && Game->Journal().Num() != Seen)
	{
		Seen = -1;
		if (AJadgHud* Manager = Hud())
		{
			Manager->Open(Kind, Argument);
		}
	}
}
