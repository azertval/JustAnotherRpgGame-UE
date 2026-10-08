// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"

#include "JadgHud.generated.h"

class UFont;

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
 * | en bas | le dialogue : qui parle, le jet qui vient d'être joué, la réplique, les réponses numérotées |
 *
 * Il ne tient aucun état : tout est lu, à chaque trame, dans `UJadgExploration`.
 */
UCLASS()
class AJadgHud : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

private:
	/// Écrit @p Text en (X, Y) ; rend la hauteur de la ligne.
	float Write(const FString& Text, float X, float Y, const FLinearColor& Colour, float Scale) const;

	/// Écrit @p Text à partir de (X, Y), replié à @p Width ; rend la hauteur occupée.
	float WriteWrapped(const FString& Text, float X, float Y, float Width, const FLinearColor& Colour, float Scale) const;

	float Measure(const FString& Text, float Scale) const;
};
