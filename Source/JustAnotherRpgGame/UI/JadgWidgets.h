// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Components/Button.h"
#include "Components/SlateWrapperTypes.h"
#include "CoreMinimal.h"
#include "Framework/Text/TextLayout.h"
#include "Layout/Margin.h"

#include "JadgWidgets.generated.h"

class UBorder;
class UCanvasPanel;
class UCanvasPanelSlot;
class UHorizontalBox;
class UImage;
class UOverlay;
class UProgressBar;
class UScrollBox;
class USizeBox;
class UTextBlock;
class UVerticalBox;
class UWidget;
class UWidgetTree;

/**
 * @brief Un bouton des écrans (LOT-1020) : une pièce du kit dans ses états (repos, survol, enfoncé,
 *        désactivé), un libellé, et la marque du focus (`EX-IHM-071`).
 *
 * Son geste est une fonction du C++ (`Action`), pas un événement de Blueprint : le clic, la touche
 * Entrée sur le bouton focalisé et `Activate` (les tests, le parcours des écrans) le jouent tous.
 * La marque est le fleuron du kit (`control/focus-fleuron`), posé devant le libellé tant que le
 * bouton a le focus du clavier ; l'écran l'actualise à chaque trame (`SyncFocus`).
 */
UCLASS()
class UJadgButton : public UButton
{
	GENERATED_BODY()

public:
	/// Le geste du bouton.
	TFunction<void()> Action;

	/// Le libellé, pour les tests et le parcours ; vide pour un bouton sans texte.
	FText Label;

	/// Le bouton prend-il le focus du clavier ; à régler avant sa construction.
	void SetFocusable(bool bFocusable) { InitIsFocusable(bFocusable); }

	/// Joue le geste, comme un clic.
	void Activate();

	/// Montre la marque du focus si le bouton a le focus du clavier.
	void SyncFocus();

	/// Le fleuron du focus, posé par le constructeur d'écran ; peut manquer.
	UPROPERTY()
	TObjectPtr<UImage> FocusMark;

	/// Le texte du libellé, pour le changer sans reconstruire l'écran ; peut manquer.
	UPROPERTY()
	TObjectPtr<UTextBlock> LabelBlock;

	/// Change le libellé affiché.
	void SetLabel(const FText& Text);

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;

private:
	UFUNCTION()
	void HandleClicked();
};

/**
 * @brief Le constructeur des écrans : chaque fonction rend un widget d'UMG habillé par le style
 *        (`UJadgStyle`), créé dans l'arbre de l'écran. Aucun Widget Blueprint (LOT-1020).
 */
struct FJadgUi
{
	UWidgetTree* Tree = nullptr;
	/// Les boutons créés, dans l'ordre : l'écran les garde pour le focus et les tests.
	TArray<TObjectPtr<UJadgButton>>* Buttons = nullptr;

	/// Un texte : sa police (`title`, `label`, `body`, `lore`), sa taille, sa couleur (rôles du style).
	UTextBlock* Text(const FText& Value, FName FontRole, FName SizeRole, FName ColourRole, bool bWrap = false,
		ETextJustify::Type Justify = ETextJustify::Left) const;

	/// Une pièce du kit qui encadre @p Content, avec une réserve intérieure @p Padding.
	UBorder* Piece(FName PieceId, UWidget* Content, const FMargin& Padding = FMargin(0.0f), FName State = NAME_None) const;

	/// Une pièce du kit, seule, à la taille @p Size (zéro : sa taille de conception).
	UImage* Image(FName PieceId, FName State = NAME_None, FVector2D Size = FVector2D::ZeroVector) const;

	/// Une image du kit par son chemin (`icon/nav/map`), à la taille @p Size.
	UImage* Icon(const FString& KitPath, const FVector2D& Size) const;

	/// Un aplat d'une couleur du style.
	UBorder* Flat(FName ColourRole, UWidget* Content = nullptr, const FMargin& Padding = FMargin(0.0f)) const;

	/**
	 * @brief Un bouton du kit (`button/default`, `button/menu`, `tab/ribbon`…) et son libellé.
	 * @param bFocusable Faux pour un bouton posé sur le jeu (HUD, dialogue) : il ne prend pas le
	 *        clavier au jeu.
	 */
	UJadgButton* Button(FName PieceId, const FText& Label, TFunction<void()> Action, FName LabelColour = TEXT("textOnPanel"),
		bool bFocusable = true, FName SizeRole = TEXT("body")) const;

	/// Une jauge du kit (`gauge/track`) remplie à @p Fraction de la couleur @p FillColour.
	UProgressBar* Gauge(float Fraction, FName FillColour) const;

	UVerticalBox* Column() const;
	UHorizontalBox* Row() const;
	UOverlay* Layers() const;
	UScrollBox* Scroll() const;
	UCanvasPanel* Canvas() const;

	/// @p Content dans une boîte de taille @p Width × @p Height (0 : libre).
	USizeBox* Sized(UWidget* Content, float Width, float Height) const;

	/// Ajoute @p Child à une colonne ou à une ligne, avec sa réserve et sa part de remplissage.
	static void Add(UVerticalBox* Box, UWidget* Child, const FMargin& Padding = FMargin(0.0f), float Fill = 0.0f,
		EHorizontalAlignment Align = HAlign_Fill);
	static void Add(UHorizontalBox* Box, UWidget* Child, const FMargin& Padding = FMargin(0.0f), float Fill = 0.0f,
		EVerticalAlignment Align = VAlign_Center);
	static void Add(UOverlay* Box, UWidget* Child, EHorizontalAlignment HAlign = HAlign_Fill, EVerticalAlignment VAlign = VAlign_Fill,
		const FMargin& Padding = FMargin(0.0f));

	/**
	 * @brief Pose @p Child sur le canevas en (@p X, @p Y), en pixels de conception depuis l'ancre
	 *        @p Anchor (0 à 1 sur chaque axe), aligné par @p Alignment ; taille @p Size, ou la
	 *        sienne si zéro.
	 */
	static UCanvasPanelSlot* Place(UCanvasPanel* Canvas, UWidget* Child, const FVector2D& Position, const FVector2D& Size = FVector2D::ZeroVector,
		const FVector2D& Anchor = FVector2D::ZeroVector, const FVector2D& Alignment = FVector2D::ZeroVector);

	/// Étend @p Child à tout le canevas, moins @p Inset.
	static UCanvasPanelSlot* Fill(UCanvasPanel* Canvas, UWidget* Child, const FMargin& Inset = FMargin(0.0f));
};
