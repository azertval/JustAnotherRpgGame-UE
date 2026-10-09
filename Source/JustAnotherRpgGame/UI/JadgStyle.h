// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Fonts/SlateFontInfo.h"
#include "Styling/SlateBrush.h"
#include "UObject/Object.h"

#include "JadgStyle.generated.h"

class UFontFace;
class UTexture2D;

/**
 * @brief Le style des écrans, lu au lancement dans `Source/Elements/Assets/UI/style.json`
 *        (`core::loadUiStyle`, LOT-1020) : couleurs, polices, tailles, pièces du kit `UI`.
 *
 * Les grandeurs du fichier sont écrites à la définition de conception (1920 × 1080) : les écrans
 * les posent telles quelles, et l'échelle d'UMG (la règle « côté le plus court » du moteur, 1 à
 * 1080 lignes) les suit à la fenêtre — le facteur réel de la charte v2 (`EX-IHM-070`). Les polices
 * sont à 72 points par pouce (`Config/DefaultEngine.ini`) : une taille vaut des pixels.
 *
 * | Ce qu'il donne | D'où |
 * |---|---|
 * | une image du kit | `/Game/UI/Kit/<pièce>[/<état>]`, importée par `scripts/assetsGeneration/import_ui_unreal.py` |
 * | une police | `/Game/UI/Fonts/<fichier>`, la face importée par le même script, mise en police composite ici |
 *
 * Une pièce absente — le kit n'est pas sur le poste, ou pas importé — retombe sur un aplat des
 * couleurs du fichier cerclé d'or (`EX-IHM-075`) ; une police absente, sur celle du moteur
 * (`EX-IHM-052`). Aucun écran ne dépend d'un binaire pour s'afficher.
 *
 * Un objet unique, gardé de la collecte, chargé au premier appel de `Get`.
 */
UCLASS()
class UJadgStyle : public UObject
{
	GENERATED_BODY()

public:
	static UJadgStyle& Get();

	/// La couleur du rôle @p Role (`panel`, `text`…), en espace linéaire ; magenta si le rôle manque.
	FLinearColor Colour(FName Role) const;

	/// La police du rôle @p FontRole (`title`, `body`…) à la taille du rôle @p SizeRole (`body`…).
	FSlateFontInfo Font(FName FontRole, FName SizeRole) const;

	/// La taille du rôle @p SizeRole, en pixels de conception.
	int32 Size(FName SizeRole) const;

	/// L'écart du rôle @p Role (`small`, `medium`, `large`), en pixels de conception.
	float Space(FName Role) const;

	/// La pièce @p PieceId (`frame/panel-dark`) dans l'état @p State : 9-patch si elle a des marges.
	FSlateBrush Brush(FName PieceId, FName State = NAME_None) const;

	/// La taille de conception de la pièce @p PieceId ; zéro si le style ne la connaît pas.
	FVector2D PieceSize(FName PieceId) const;

	/// Vrai si la pièce @p PieceId a un état @p State.
	bool HasState(FName PieceId, FName State) const;

	/// Une image du kit par son chemin sans extension (`icon/nav/map`), de taille @p Size ; un
	/// aplat transparent si elle manque.
	FSlateBrush Image(const FString& KitPath, const FVector2D& Size) const;

	/// Une image lue dans un fichier du disque (un portrait de PNJ), gardée une fois lue.
	FSlateBrush Picture(const FString& File, const FVector2D& Size);

	/// Le nombre d'images du kit trouvées dans le projet, et de pièces que le style décrit.
	int32 TexturesFound() const;
	int32 PieceCount() const { return Pieces.Num(); }

	/// Les erreurs de lecture du style ; vide s'il s'est lu.
	const TArray<FString>& Errors() const { return Problems; }

private:
	struct FPiece
	{
		FString Id;
		FVector2D Size = FVector2D::ZeroVector;
		bool bStretch = false;
		FMargin Margin;
		TArray<FString> States;
	};

	UPROPERTY()
	TMap<FString, TObjectPtr<UTexture2D>> Textures;

	UPROPERTY()
	TArray<TObjectPtr<UFontFace>> Faces;

	UPROPERTY()
	TMap<FString, TObjectPtr<UTexture2D>> Pictures;

	TMap<FName, TSharedPtr<const struct FCompositeFont>> Fonts;
	TMap<FName, FLinearColor> Colours;
	TMap<FName, int32> Sizes;
	TMap<FName, int32> Spacing;
	TMap<FName, FPiece> Pieces;
	TArray<FString> Problems;

	void Load();
	UTexture2D* Texture(const FString& KitPath) const;
};
