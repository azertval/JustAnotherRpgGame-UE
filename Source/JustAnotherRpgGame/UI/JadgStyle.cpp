// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Ui/UiStyle.h"

#include <string>

#include "UI/JadgStyle.h"

#include "Bridge/JadgPaths.h"
#include "Engine/FontFace.h"
#include "Engine/Texture2D.h"
#include "Fonts/CompositeFont.h"
#include "ImageUtils.h"
#include "UObject/Package.h"
#include "UObject/StrongObjectPtr.h"
#include "JustAnotherRpgGame.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "Styling/CoreStyle.h"

namespace
{
	const TCHAR* const KitRoot = TEXT("/Game/UI/Kit/");
	const TCHAR* const FontRoot = TEXT("/Game/UI/Fonts/");

	/// L'objet d'un paquet du projet, s'il existe : aucun avertissement de chargement s'il manque.
	template <typename T>
	T* LoadIfPresent(const FString& Package)
	{
		if (!FPackageName::DoesPackageExist(Package))
		{
			return nullptr;
		}
		return LoadObject<T>(nullptr, *(Package + TEXT(".") + FPackageName::GetShortName(Package)));
	}
}

UJadgStyle& UJadgStyle::Get()
{
	static TStrongObjectPtr<UJadgStyle> Instance;
	if (!Instance.IsValid())
	{
		Instance.Reset(NewObject<UJadgStyle>(GetTransientPackage(), UJadgStyle::StaticClass(), FName(TEXT("JadgStyle"))));
		Instance->Load();
	}
	return *Instance.Get();
}

void UJadgStyle::Load()
{
	const FString File = FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Assets"), TEXT("UI"), TEXT("style.json"));
	const core::UiStyleResult Read = core::loadUiStyle(FJadgPaths::ToPath(File));
	for (const std::string& Error : Read.errors)
	{
		Problems.Add(FJadgPaths::ToFString(Error));
		UE_LOG(LogJadg, Error, TEXT("[Style] %s"), *Problems.Last());
	}
	const core::UiStyle& Style = Read.style;
	for (const auto& [Role, Value] : Style.colours)
	{
		const FColor Srgb(static_cast<uint8>(FMath::RoundToInt(Value.red * 255.0f)), static_cast<uint8>(FMath::RoundToInt(Value.green * 255.0f)),
			static_cast<uint8>(FMath::RoundToInt(Value.blue * 255.0f)), static_cast<uint8>(FMath::RoundToInt(Value.alpha * 255.0f)));
		Colours.Add(FName(FJadgPaths::ToFString(Role)), FLinearColor(Srgb));
	}
	for (const auto& [Role, Value] : Style.sizes)
	{
		Sizes.Add(FName(FJadgPaths::ToFString(Role)), Value);
	}
	for (const auto& [Role, Value] : Style.spacing)
	{
		Spacing.Add(FName(FJadgPaths::ToFString(Role)), Value);
	}
	int32 Found = 0;
	for (const auto& [Id, Described] : Style.pieces)
	{
		FPiece& Piece = Pieces.Add(FName(FJadgPaths::ToFString(Id)));
		Piece.Id = FJadgPaths::ToFString(Id);
		Piece.Size = FVector2D(Described.width, Described.height);
		if (Described.margins.has_value())
		{
			Piece.bStretch = true;
			Piece.Margin = FMargin(static_cast<float>(Described.margins->left) / Described.width, static_cast<float>(Described.margins->top) / Described.height,
				static_cast<float>(Described.margins->right) / Described.width, static_cast<float>(Described.margins->bottom) / Described.height);
		}
		for (const std::string& State : Described.states)
		{
			Piece.States.Add(FJadgPaths::ToFString(State));
		}
		const TArray<FString> Paths = Piece.States.IsEmpty() ? TArray<FString>{Piece.Id} : [&Piece]
		{
			TArray<FString> Each;
			for (const FString& State : Piece.States)
			{
				Each.Add(Piece.Id + TEXT("/") + State);
			}
			return Each;
		}();
		for (const FString& Path : Paths)
		{
			if (UTexture2D* Loaded = LoadIfPresent<UTexture2D>(KitRoot + Path))
			{
				Textures.Add(Path, Loaded);
				++Found;
			}
		}
	}
	for (const auto& [Role, FontFile] : Style.fonts)
	{
		const FString Stem = FPaths::GetBaseFilename(FJadgPaths::ToFString(FontFile));
		if (UFontFace* Face = LoadIfPresent<UFontFace>(FontRoot + Stem))
		{
			Faces.Add(Face);
			TSharedRef<FCompositeFont> Composite = MakeShared<FCompositeFont>();
			FTypefaceEntry& Entry = Composite->DefaultTypeface.Fonts.Add_GetRef(FTypefaceEntry(TEXT("Regular")));
			Entry.Font = FFontData(Face);
			Fonts.Add(FName(FJadgPaths::ToFString(Role)), Composite);
		}
	}
	UE_LOG(LogJadg, Display, TEXT("[Style] %s : %d couleur(s), %d pièce(s), %d image(s) du kit trouvée(s), %d police(s) sur %d"), *File,
		Colours.Num(), Pieces.Num(), Found, Fonts.Num(), static_cast<int32>(Style.fonts.size()));
}

FLinearColor UJadgStyle::Colour(FName Role) const
{
	const FLinearColor* Found = Colours.Find(Role);
	return Found != nullptr ? *Found : FLinearColor(1.0f, 0.0f, 1.0f);
}

int32 UJadgStyle::Size(FName SizeRole) const
{
	const int32* Found = Sizes.Find(SizeRole);
	return Found != nullptr ? *Found : 18;
}

float UJadgStyle::Space(FName Role) const
{
	const int32* Found = Spacing.Find(Role);
	return Found != nullptr ? static_cast<float>(*Found) : 8.0f;
}

FSlateFontInfo UJadgStyle::Font(FName FontRole, FName SizeRole) const
{
	const float Points = static_cast<float>(Size(SizeRole));
	if (const TSharedPtr<const FCompositeFont>* Found = Fonts.Find(FontRole))
	{
		return FSlateFontInfo(*Found, Points);
	}
	return FCoreStyle::GetDefaultFontStyle(FontRole == TEXT("lore") ? TEXT("Italic") : TEXT("Regular"), Points);
}

UTexture2D* UJadgStyle::Texture(const FString& KitPath) const
{
	if (const TObjectPtr<UTexture2D>* Found = Textures.Find(KitPath))
	{
		return Found->Get();
	}
	return nullptr;
}

FVector2D UJadgStyle::PieceSize(FName PieceId) const
{
	const FPiece* Piece = Pieces.Find(PieceId);
	return Piece != nullptr ? Piece->Size : FVector2D::ZeroVector;
}

bool UJadgStyle::HasState(FName PieceId, FName State) const
{
	const FPiece* Piece = Pieces.Find(PieceId);
	return Piece != nullptr && Piece->States.Contains(State.ToString());
}

FSlateBrush UJadgStyle::Brush(FName PieceId, FName State) const
{
	FSlateBrush Brush;
	const FPiece* Piece = Pieces.Find(PieceId);
	if (Piece == nullptr)
	{
		UE_LOG(LogJadg, Warning, TEXT("[Style] pièce inconnue : %s"), *PieceId.ToString());
		Brush.DrawAs = ESlateBrushDrawType::NoDrawType;
		return Brush;
	}
	FString Path = Piece->Id;
	if (!Piece->States.IsEmpty())
	{
		Path += TEXT("/") + (State.IsNone() || !Piece->States.Contains(State.ToString()) ? Piece->States[0] : State.ToString());
	}
	Brush.ImageSize = Piece->Size;
	if (UTexture2D* Loaded = Texture(Path))
	{
		Brush.SetResourceObject(Loaded);
		Brush.DrawAs = Piece->bStretch ? ESlateBrushDrawType::Box : ESlateBrushDrawType::Image;
		Brush.Margin = Piece->Margin;
		Brush.TintColor = FSlateColor(FLinearColor::White);
		return Brush;
	}
	// L'aplat des jetons (`EX-IHM-075`) : parchemin pour une page, panneau sombre sinon, filet d'or.
	const bool bParchment = Piece->Id.Contains(TEXT("parchment")) || Piece->Id.StartsWith(TEXT("tab/segment"));
	const bool bActive = State == TEXT("active") || State == TEXT("selected") || State == TEXT("hover");
	Brush.DrawAs = ESlateBrushDrawType::RoundedBox;
	Brush.TintColor = FSlateColor(bParchment ? Colour(TEXT("surface")) : bActive ? Colour(TEXT("gem")) : Colour(TEXT("panel")));
	Brush.OutlineSettings = FSlateBrushOutlineSettings(FVector4(6.0f, 6.0f, 6.0f, 6.0f),
		FSlateColor(bParchment ? Colour(TEXT("accent")) : Colour(TEXT("panelEdge"))), 2.0f);
	return Brush;
}

FSlateBrush UJadgStyle::Image(const FString& KitPath, const FVector2D& Size) const
{
	FSlateBrush Brush;
	Brush.ImageSize = Size;
	if (UTexture2D* Loaded = Texture(KitPath))
	{
		Brush.SetResourceObject(Loaded);
		return Brush;
	}
	if (UTexture2D* Loaded = LoadIfPresent<UTexture2D>(KitRoot + KitPath))
	{
		const_cast<UJadgStyle*>(this)->Textures.Add(KitPath, Loaded);
		Brush.SetResourceObject(Loaded);
		return Brush;
	}
	Brush.DrawAs = ESlateBrushDrawType::NoDrawType;
	return Brush;
}

FSlateBrush UJadgStyle::Picture(const FString& File, const FVector2D& Size)
{
	FSlateBrush Brush;
	Brush.ImageSize = Size;
	TObjectPtr<UTexture2D>* Known = Pictures.Find(File);
	UTexture2D* Read = Known != nullptr ? Known->Get() : nullptr;
	if (Known == nullptr && !File.IsEmpty())
	{
		Read = FImageUtils::ImportFileAsTexture2D(File);
		Pictures.Add(File, Read);
	}
	if (Read != nullptr)
	{
		Brush.SetResourceObject(Read);
	}
	else
	{
		Brush.DrawAs = ESlateBrushDrawType::NoDrawType;
	}
	return Brush;
}

int32 UJadgStyle::TexturesFound() const
{
	return Textures.Num();
}
