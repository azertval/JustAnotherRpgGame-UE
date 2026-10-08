// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"

#include "JadgGameMode.generated.h"

/**
 * @brief Le mode de jeu de l'exploration : la caméra libre pour pion, ses commandes pour
 *        contrôleur, le HUD minimal (LOT-1012, LOT-1016).
 *
 * Au lancement de la carte il crée le groupe (`AJadgParty`), qui rassemble les personnages que la
 * scène déclare et joue la carte de Core si la carte du moteur en nomme une.
 *
 * Avec `-JadgCapture=<dossier>` sur la ligne de commande, il crée le directeur de capture
 * (`AJadgCaptureDirector`), qui prend les images, mesure la cadence et quitte. Avec
 * `-JadgParcours=<dossier>`, il crée le parcours (`AJadgWalkthrough`), qui joue la quête des pommes
 * sur les cartes essai.
 */
UCLASS()
class AJadgGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AJadgGameMode();

	virtual void StartPlay() override;
};
