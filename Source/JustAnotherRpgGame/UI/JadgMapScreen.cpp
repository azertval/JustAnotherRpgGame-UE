// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// La carte : l'atlas illustré, ses lieux cliquables, leurs voisins, la recherche, les favoris
// (LOT-1020, `interface-ihm.md` §11).

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Ui/MapInteractions.h"
#include "Core/World/Atlas.h"

#include <string>

#include "Blueprint/WidgetTree.h"
#include "Bridge/JadgPaths.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/EditableTextBox.h"
#include "Components/HorizontalBox.h"
#include "Components/Image.h"
#include "Components/SizeBox.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Misc/Paths.h"
#include "UI/JadgHud.h"
#include "UI/JadgScreens.h"
#include "UI/JadgStyle.h"
#include "UI/JadgTexts.h"

namespace
{
	const FString World(TEXT("world"));

	struct FMapData
	{
		core::MapInteractions Zones;
		core::Atlas Atlas;

		FMapData()
		{
			Zones = core::loadMapInteractions(FJadgPaths::ToPath(FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Maps"), TEXT("map-interactions.json"))));
			Atlas = core::loadAtlas(FJadgPaths::ToPath(FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("World"))));
		}

		/// Le nom d'un lieu : celui de l'atlas, sinon son identifiant mis en mots.
		FString NameOf(const FString& Id) const
		{
			const std::string Wanted = TCHAR_TO_UTF8(*Id);
			if (const core::Region* Region = Atlas.findRegion(Wanted))
			{
				return FJadgPaths::ToFString(Region->name);
			}
			if (const core::Location* Place = Atlas.findLocation(Wanted))
			{
				return FJadgPaths::ToFString(Place->name);
			}
			if (Id == World)
			{
				return FJadgTexts::Get(TEXT("map.world")).ToString();
			}
			// Un lieu sans nom dans l'atlas : son identifiant, sans le préfixe de son parent ni la
			// marque `vtt` des relevés, mis en mots.
			FString Words = Id;
			const FString Parent = FJadgPaths::ToFString(Zones.parentOf(TCHAR_TO_UTF8(*Id)));
			if (!Parent.IsEmpty() && Words.StartsWith(Parent + TEXT("-")))
			{
				Words = Words.RightChop(Parent.Len() + 1);
			}
			Words.RemoveFromStart(TEXT("vtt-"));
			TArray<FString> Parts;
			Words.ParseIntoArray(Parts, TEXT("-"));
			for (FString& Part : Parts)
			{
				Part = Part.Left(1).ToUpper() + Part.RightChop(1);
			}
			return FString::Join(Parts, TEXT(" "));
		}

		FString DescriptionOf(const FString& Id) const
		{
			const std::string Wanted = TCHAR_TO_UTF8(*Id);
			if (const core::Location* Place = Atlas.findLocation(Wanted))
			{
				return FJadgPaths::ToFString(Place->description);
			}
			return FString();
		}

		TArray<FString> NeighboursOf(const FString& Id) const
		{
			TArray<FString> Out;
			if (const core::Region* Region = Atlas.findRegion(TCHAR_TO_UTF8(*Id)))
			{
				for (const std::string& Other : Region->neighbors)
				{
					Out.Add(FJadgPaths::ToFString(Other));
				}
			}
			return Out;
		}
	};

	const FMapData& Data()
	{
		static const FMapData Loaded;
		return Loaded;
	}

	FText Key(const TCHAR* Name)
	{
		return FJadgTexts::Get(Name);
	}
}

TArray<FString>& UJadgMapScreen::Favourites()
{
	static TArray<FString> Kept;
	return Kept;
}

void UJadgMapScreen::Reopen()
{
	if (AJadgHud* Manager = Hud())
	{
		Manager->Open(Kind, MapId + TEXT("|") + PlaceId + TEXT("|") + Query);
	}
}

bool UJadgMapScreen::HandleKey(const FKey& Key)
{
	// Échap remonte d'un niveau, puis ferme la carte.
	if (Key == EKeys::Escape && MapId != World)
	{
		const FString Parent = FJadgPaths::ToFString(Data().Zones.parentOf(TCHAR_TO_UTF8(*MapId)));
		PlaceId = MapId;
		MapId = Parent.IsEmpty() ? World : Parent;
		Reopen();
		return true;
	}
	return Super::HandleKey(Key);
}

void UJadgMapScreen::Build(FJadgUi& Ui, UCanvasPanel* Root)
{
	TArray<FString> Parts;
	Argument.ParseIntoArray(Parts, TEXT("|"), false);
	MapId = Parts.IsValidIndex(0) && !Parts[0].IsEmpty() ? Parts[0] : World;
	PlaceId = Parts.IsValidIndex(1) ? Parts[1] : FString();
	Query = Parts.IsValidIndex(2) ? Parts[2] : FString();
	const FMapData& Map = Data();

	// Le fond : le parchemin, puis l'illustration au centre, à ses proportions (1536 × 1024).
	FJadgUi::Fill(Root, Ui.Piece(TEXT("frame/panel-parchment"), nullptr, FMargin(0.0f), TEXT("plain")));
	const FVector2D Area(1620.0f, 1080.0f);
	UCanvasPanel* Plate = Ui.Canvas();
	FJadgUi::Place(Root, Plate, FVector2D(150.0f, 0.0f), Area);
	const FString Image = FJadgPaths::ToFString(Map.Zones.imageOf(TCHAR_TO_UTF8(*MapId)));
	UImage* Illustration = Ui.Tree->ConstructWidget<UImage>();
	Illustration->SetBrush(UJadgStyle::Get().Picture(FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Assets"), Image), Area));
	FJadgUi::Place(Plate, Illustration, FVector2D::ZeroVector, Area);

	// Les bannières des lieux dessinés ici : le clic ouvre le lieu s'il a sa carte, le choisit sinon.
	for (const core::MapZone* Zone : Map.Zones.childrenOf(TCHAR_TO_UTF8(*MapId)))
	{
		const FString Id = FJadgPaths::ToFString(Zone->id);
		const bool bOpens = !Map.Zones.imageOf(Zone->id).empty();
		const bool bChosen = Id == PlaceId;
		UJadgButton* Banner = Ui.Button(TEXT("button/chip"), FText::FromString(Map.NameOf(Id)), [this, Id]
		{
			PlaceId = Id;
			Reopen();
		}, bChosen ? TEXT("goldLight") : Zone->neighbour ? TEXT("textOnPanelMuted") : TEXT("textOnPanel"), true, TEXT("caption"));
		if (bChosen)
		{
			FButtonStyle Look = Banner->GetStyle();
			Look.SetNormal(UJadgStyle::Get().Brush(TEXT("button/chip"), TEXT("selected")));
			Banner->SetStyle(Look);
		}
		UHorizontalBox* Line = Ui.Row();
		FJadgUi::Add(Line, Ui.Icon(bOpens ? TEXT("icon/poi/city") : TEXT("icon/poi/point-of-interest"), FVector2D(34.0f, 34.0f)), FMargin(0.0f, 0.0f, 4.0f, 0.0f));
		FJadgUi::Add(Line, Ui.Sized(Banner, FMath::Max(150.0f, Zone->label[2] * Area.X + 40.0f), 38.0f));
		FJadgUi::Place(Plate, Line, FVector2D(Zone->label[0] * Area.X - 38.0f, Zone->label[1] * Area.Y));
	}

	// En haut à gauche : où l'on est, et ce qu'on y a choisi.
	UVerticalBox* Info = Ui.Column();
	FJadgUi::Add(Info, Ui.Text(FText::FromString(Map.NameOf(MapId)), TEXT("display"), TEXT("section"), TEXT("goldLight")));
	FJadgUi::Add(Info, Ui.Text(Key(MapId == World ? TEXT("map.world_subtitle") : TEXT("map.places")), TEXT("lore"), TEXT("caption"), TEXT("textOnPanel")),
		FMargin(0.0f, 0.0f, 0.0f, 12.0f));
	if (!PlaceId.IsEmpty())
	{
		FJadgUi::Add(Info, Ui.Text(FText::FromString(Map.NameOf(PlaceId)), TEXT("title"), TEXT("body"), TEXT("panelEdge")));
		const FString Description = Map.DescriptionOf(PlaceId);
		if (!Description.IsEmpty())
		{
			FJadgUi::Add(Info, Ui.Text(FText::FromString(Description.Left(320)), TEXT("lore"), TEXT("caption"), TEXT("textOnPanel"), true),
				FMargin(0.0f, 6.0f));
		}
		UHorizontalBox* Acts = Ui.Row();
		if (!Map.Zones.imageOf(TCHAR_TO_UTF8(*PlaceId)).empty())
		{
			FJadgUi::Add(Acts, Ui.Sized(Ui.Button(TEXT("button/primary"), Key(TEXT("map.open")), [this]
			{
				MapId = PlaceId;
				PlaceId.Reset();
				Reopen();
			}), 180.0f, 48.0f), FMargin(0.0f, 0.0f, 8.0f, 0.0f));
		}
		const bool bFavourite = Favourites().Contains(PlaceId);
		FJadgUi::Add(Acts, Ui.Sized(Ui.Button(TEXT("button/secondary"), Key(bFavourite ? TEXT("map.unfavourite") : TEXT("map.favourite")), [this, bFavourite]
		{
			if (bFavourite)
			{
				Favourites().Remove(PlaceId);
			}
			else
			{
				Favourites().AddUnique(PlaceId);
			}
			Reopen();
		}), 220.0f, 48.0f));
		FJadgUi::Add(Info, Acts, FMargin(0.0f, 10.0f));
		const TArray<FString> Neighbours = Map.NeighboursOf(PlaceId);
		if (!Neighbours.IsEmpty())
		{
			FJadgUi::Add(Info, Ui.Text(Key(TEXT("map.neighbours")), TEXT("title"), TEXT("caption"), TEXT("panelEdge")), FMargin(0.0f, 6.0f, 0.0f, 2.0f));
			FJadgUi::Add(Info, Ui.Text(FText::FromString(FString::JoinBy(Neighbours, TEXT(" · "), [&Map](const FString& Id) { return Map.NameOf(Id); })),
								   TEXT("body"), TEXT("caption"), TEXT("textOnPanel"), true));
		}
	}
	FJadgUi::Place(Root, Ui.Sized(Ui.Piece(TEXT("frame/subpanel-dark"), Info, FMargin(34.0f, 26.0f)), 520.0f, 0.0f), FVector2D(30.0f, 30.0f));

	// En haut à droite : la recherche et ses résultats, puis les favoris.
	UVerticalBox* Side = Ui.Column();
	UEditableTextBox* Search = Ui.Tree->ConstructWidget<UEditableTextBox>();
	Search->SetHintText(Key(TEXT("map.search")));
	Search->SetText(FText::FromString(Query));
	Search->OnTextCommitted.AddUniqueDynamic(this, &UJadgMapScreen::HandleSearch);
	FJadgUi::Add(Side, Ui.Sized(Search, 0.0f, 48.0f));
	if (!Query.IsEmpty())
	{
		int32 Shown = 0;
		TSet<FString> Seen;
		for (const core::MapZone& Zone : Map.Zones.zones)
		{
			const FString Id = FJadgPaths::ToFString(Zone.id);
			if (Zone.neighbour || Seen.Contains(Id) || !Map.NameOf(Id).Contains(Query) || Shown >= 8)
			{
				continue;
			}
			Seen.Add(Id);
			++Shown;
			const FString Parent = FJadgPaths::ToFString(Zone.parent);
			FJadgUi::Add(Side, Ui.Sized(Ui.Button(TEXT("control/ruled-line"), FText::FromString(Map.NameOf(Id)), [this, Id, Parent]
			{
				MapId = Parent;
				PlaceId = Id;
				Reopen();
			}, TEXT("textOnPanel"), true, TEXT("caption")), 0.0f, 40.0f));
		}
	}
	FJadgUi::Add(Side, Ui.Text(Key(TEXT("map.favourites")), TEXT("title"), TEXT("caption"), TEXT("panelEdge")), FMargin(0.0f, 14.0f, 0.0f, 4.0f));
	for (const FString& Id : Favourites())
	{
		const FString Parent = FJadgPaths::ToFString(Map.Zones.parentOf(TCHAR_TO_UTF8(*Id)));
		FJadgUi::Add(Side, Ui.Sized(Ui.Button(TEXT("control/ruled-line"), FText::FromString(TEXT("★ ") + Map.NameOf(Id)), [this, Id, Parent]
		{
			MapId = Parent.IsEmpty() ? World : Parent;
			PlaceId = Id;
			Reopen();
		}, TEXT("textOnPanel"), true, TEXT("caption")), 0.0f, 40.0f));
	}
	FJadgUi::Place(Root, Ui.Sized(Ui.Piece(TEXT("frame/subpanel-dark"), Side, FMargin(30.0f, 24.0f)), 440.0f, 0.0f), FVector2D(-30.0f, 30.0f),
		FVector2D::ZeroVector, FVector2D(1.0f, 0.0f), FVector2D(1.0f, 0.0f));

	// En bas : remonter, fermer, et l'aide des touches.
	UHorizontalBox* Foot = Ui.Row();
	if (MapId != World)
	{
		FJadgUi::Add(Foot, Ui.Sized(Ui.Button(TEXT("button/back"), Key(TEXT("map.up")), [this] { HandleKey(EKeys::Escape); }), 240.0f, 60.0f),
			FMargin(0.0f, 0.0f, 12.0f, 0.0f));
	}
	FJadgUi::Add(Foot, Ui.Sized(Ui.Button(TEXT("button/default"), Key(TEXT("map.close")), [this] { Close(); }), 220.0f, 56.0f), FMargin(0.0f, 0.0f, 20.0f, 0.0f));
	FJadgUi::Add(Foot, Ui.Text(Key(TEXT("map.hint")), TEXT("body"), TEXT("caption"), TEXT("textOnPanel")));
	FJadgUi::Place(Root, Ui.Piece(TEXT("plate/status-bar"), Foot, FMargin(30.0f, 10.0f, 70.0f, 10.0f)), FVector2D(30.0f, -24.0f), FVector2D::ZeroVector,
		FVector2D(0.0f, 1.0f), FVector2D(0.0f, 1.0f));
}

void UJadgMapScreen::HandleSearch(const FText& Text, ETextCommit::Type Method)
{
	if (Method == ETextCommit::OnEnter)
	{
		Query = Text.ToString();
		Reopen();
	}
}
