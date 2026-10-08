// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"

#include "JadgHud.generated.h"

class UFont;
class UTexture2D;

/**
 * @brief Le HUD minimal de l'exploration (LOT-1016) : ce qu'il faut lire pour jouer, dessiné sur
 *        le canevas du moteur. Le vrai HUD et les écrans sont le LOT-1020 (UMG).
 *
 * | Où | Quoi |
 * |---|---|
 * | en haut à gauche | le groupe, le meneur en tête : nom, points de vie |
 * | en haut à droite | l'heure du monde |
 * | en haut au centre | l'annonce du moment : un passage fermé, une étape de quête |
 * | en bas au centre | l'invite de ce que le meneur peut solliciter |
 * | en bas | le dialogue : le portrait de qui parle et son nom, le jet qui vient d'être joué, la réplique, les réponses numérotées |
 * | au centre | la rencontre engagée, dans l'arène vide, et la touche qui en ramène |
 *
 * Il ne tient aucun état : tout est lu, à chaque trame, dans `UJadgExploration`. Seuls les
 * portraits sont gardés : un portrait est une image du kit de son personnage (`portrait.png`), lue
 * une fois dans son fichier — rien n'en est importé dans le projet.
 */
UCLASS()
class AJadgHud : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

private:
	/// Les portraits déjà lus, par fichier ; un fichier illisible y garde une entrée vide.
	UPROPERTY()
	TMap<FString, TObjectPtr<UTexture2D>> Portraits;

	UTexture2D* PortraitOf(const FString& File);

	/// Écrit @p Text en (X, Y) ; rend la hauteur de la ligne.
	float Write(const FString& Text, float X, float Y, const FLinearColor& Colour, float Scale) const;

	/// Écrit @p Text à partir de (X, Y), replié à @p Width ; rend la hauteur occupée.
	float WriteWrapped(const FString& Text, float X, float Y, float Width, const FLinearColor& Colour, float Scale) const;

	float Measure(const FString& Text, float Scale) const;
};
