// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"

#include "JadgGameMode.generated.h"

/**
 * @brief Le mode de jeu de la porte : la caméra libre pour pion, ses commandes pour contrôleur
 *        (LOT-1012).
 *
 * Avec `-JadgCapture=<dossier>` sur la ligne de commande, il crée le directeur de capture
 * (`AJadgCaptureDirector`), qui prend les images, mesure la cadence et quitte.
 */
UCLASS()
class AJadgGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AJadgGameMode();

	virtual void StartPlay() override;
};
