// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "UI/JadgLoadingScreen.h"

#include "Bridge/JadgPaths.h"
#include "Brushes/SlateDynamicImageBrush.h"
#include "Dom/JsonObject.h"
#include "Fonts/CompositeFont.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/FileManager.h"
#include "JustAnotherRpgGame.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "MoviePlayer.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Styling/CoreStyle.h"
#include "UI/JadgTexts.h"
#include "Widgets/Images/SImage.h"
#include "Widgets/Images/SThrobber.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

FString FJadgLoadingScreen::NextMap;
int32 FJadgLoadingScreen::Shown = 0;

namespace
{
	/// Ce qu'une carte montre : le nom de son lieu (clé de texte) et ses illustrations.
	struct FPlace
	{
		FString NameKey;
		TArray<FString> Images;
	};

	FPlace PlaceOf(const FString& MapId)
	{
		FPlace Place;
		FString Json;
		const FString Assets = FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Assets"));
		TSharedPtr<FJsonObject> Root;
		if (!FFileHelper::LoadFileToString(Json, *FPaths::Combine(Assets, TEXT("UI/loading.json")))
			|| !FJsonSerializer::Deserialize(TJsonReaderFactory<>::Create(Json), Root) || !Root.IsValid())
		{
			UE_LOG(LogJadg, Warning, TEXT("[Chargement] UI/loading.json ne se lit pas : écran sans illustration"));
			return Place;
		}
		const TSharedPtr<FJsonObject>* Maps = nullptr;
		const TSharedPtr<FJsonObject>* Entry = nullptr;
		if (!(Root->TryGetObjectField(TEXT("maps"), Maps) && (*Maps)->TryGetObjectField(MapId, Entry)))
		{
			Root->TryGetObjectField(TEXT("default"), Entry);
		}
		if (Entry != nullptr)
		{
			(*Entry)->TryGetStringField(TEXT("place"), Place.NameKey);
			const TArray<TSharedPtr<FJsonValue>>* Images = nullptr;
			if ((*Entry)->TryGetArrayField(TEXT("images"), Images))
			{
				for (const TSharedPtr<FJsonValue>& Image : *Images)
				{
					Place.Images.Add(FPaths::Combine(Assets, Image->AsString()));
				}
			}
		}
		return Place;
	}

	/// La taille d'une image PNG, lue dans son en-tête : le cadre en garde les proportions.
	FVector2D PngSize(const FString& File)
	{
		TArray<uint8> Head;
		TUniquePtr<FArchive> Reader(IFileManager::Get().CreateFileReader(*File));
		if (!Reader.IsValid() || Reader->TotalSize() < 24)
		{
			return FVector2D(1920.0, 1080.0);
		}
		Head.SetNumUninitialized(24);
		Reader->Serialize(Head.GetData(), 24);
		auto Big = [&Head](int32 At) { return (Head[At] << 24) | (Head[At + 1] << 16) | (Head[At + 2] << 8) | Head[At + 3]; };
		return FVector2D(Big(16), Big(20));
	}

	/// Une police du jeu, lue sur son fichier : l'écran se dessine aussi sur le fil du lecteur de
	/// films, sans objet du moteur.
	FSlateFontInfo Font(const TCHAR* File, float Size)
	{
		static TMap<FString, TSharedPtr<const FCompositeFont>> Fonts;
		TSharedPtr<const FCompositeFont>& Found = Fonts.FindOrAdd(File);
		if (!Found.IsValid())
		{
			const FString Path = FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Assets/Fonts"), File);
			Found = MakeShared<FStandaloneCompositeFont>(NAME_None, Path, EFontHinting::Default, EFontLoadingPolicy::LazyLoad);
		}
		return FSlateFontInfo(Found, Size);
	}

	class SJadgLoading : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SJadgLoading) {}
			SLATE_ARGUMENT(FString, Image)
			SLATE_ARGUMENT(FText, Place)
			SLATE_ATTRIBUTE(FText, Status)
		SLATE_END_ARGS()

		void Construct(const FArguments& Args)
		{
			const FSlateBrush* White = FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));
			if (!Args._Image.IsEmpty() && FPaths::FileExists(Args._Image))
			{
				Picture = MakeShared<FSlateDynamicImageBrush>(FName(*Args._Image), PngSize(Args._Image));
			}
			const FLinearColor Gold(0.86f, 0.68f, 0.36f);
			const FLinearColor Parchment(0.93f, 0.88f, 0.78f);
			TSharedRef<SOverlay> Stack = SNew(SOverlay)
				+ SOverlay::Slot()[SNew(SBorder).BorderImage(White).BorderBackgroundColor(FLinearColor::Black)];
			if (Picture.IsValid())
			{
				// L'illustration entière, sur un fond qui la reprend assombrie, à toutes les proportions.
				Stack->AddSlot()[SNew(SScaleBox).Stretch(EStretch::ScaleToFill)
					[SNew(SImage).Image(Picture.Get()).ColorAndOpacity(FLinearColor(0.16f, 0.14f, 0.12f))]];
				Stack->AddSlot().Padding(FMargin(48.0f, 36.0f, 48.0f, 150.0f))
					[SNew(SScaleBox).Stretch(EStretch::ScaleToFit)[SNew(SImage).Image(Picture.Get())]];
			}
			Stack->AddSlot().VAlign(VAlign_Bottom)
				[SNew(SBorder).BorderImage(White).BorderBackgroundColor(FLinearColor(0.0f, 0.0f, 0.0f, 0.78f))
					.Padding(FMargin(64.0f, 22.0f))
					[SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().FillWidth(1.0f).VAlign(VAlign_Center)
						[SNew(SVerticalBox)
							+ SVerticalBox::Slot().AutoHeight()
							[SNew(STextBlock).Text(Args._Place).Font(Font(TEXT("Cinzel-Bold.ttf"), 34.0f)).ColorAndOpacity(Gold)]
							+ SVerticalBox::Slot().AutoHeight().Padding(0.0f, 6.0f, 0.0f, 0.0f)
							[SNew(STextBlock).Text(Args._Status).Font(Font(TEXT("IMFellEnglish-Italic.ttf"), 22.0f)).ColorAndOpacity(Parchment)]]
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
						[SNew(SCircularThrobber).Radius(24.0f).NumPieces(8)]]];
			ChildSlot[Stack];
		}

	private:
		TSharedPtr<FSlateDynamicImageBrush> Picture;
	};
}

void FJadgLoadingScreen::Install()
{
	if (GIsEditor || !IsMoviePlayerEnabled())
	{
		return;
	}
	// À chaque chargement de carte (le premier compris), le lecteur demande son écran.
	GetMoviePlayer()->OnPrepareLoadingScreen().AddLambda([]
	{
		FLoadingScreenAttributes Attributes;
		Attributes.bAutoCompleteWhenLoadingCompletes = true;
		Attributes.bMoviesAreSkippable = false;
		Attributes.WidgetLoadingScreen = Make(NextMap, FJadgTexts::Get(TEXT("loading.status.map")));
		GetMoviePlayer()->SetupLoadingScreen(Attributes);
		UE_LOG(LogJadg, Display, TEXT("[Chargement] écran du lecteur de films prêt (%s)"), NextMap.IsEmpty() ? TEXT("lancement") : *NextMap);
	});
}

void FJadgLoadingScreen::Advance()
{
	++Shown;
}

void FJadgLoadingScreen::SetNextMap(const FString& MapId)
{
	NextMap = MapId;
}

TSharedRef<SWidget> FJadgLoadingScreen::Make(const FString& MapId, TAttribute<FText> Status)
{
	FString Id = MapId;
	if (Id.IsEmpty())
	{
		// Le lancement : la carte par défaut du jeu, par son nom court (la capitale).
		FString Default;
		GConfig->GetString(TEXT("/Script/EngineSettings.GameMapsSettings"), TEXT("GameDefaultMap"), Default, GEngineIni);
		Id = FPackageName::GetShortName(Default);
	}
	const FPlace Place = PlaceOf(Id);
	const FString Image = Place.Images.IsEmpty() ? FString() : Place.Images[Shown % Place.Images.Num()];
	// Le compte avance au temps de la carte (le HUD), pas à celui du lecteur : les deux temps d'un
	// même chargement montrent la même illustration.
	return SNew(SJadgLoading)
		.Image(Image)
		.Place(Place.NameKey.IsEmpty() ? FText::GetEmpty() : FJadgTexts::Get(Place.NameKey))
		.Status(Status);
}
