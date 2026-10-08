// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"

#include "JadgPlayerController.generated.h"

class AJadgWalker;

/**
 * @brief Les commandes de la porte : la caméra libre et la marche au clic (LOT-1012).
 *
 * | Commande | Effet |
 * |---|---|
 * | clic gauche | le héros marche vers le point cliqué, ramené sur le maillage de navigation |
 * | clic droit maintenu + souris, ou A / E | tourner la caméra |
 * | clic droit maintenu + souris (vertical), ou R / F | incliner, entre les bornes |
 * | molette | zoom |
 * | Z Q S D ou flèches | déplacer le point visé (détache la caméra du héros) |
 * | Espace | revenir au héros |
 *
 * Les touches sont lues à l'état, dans `PlayerTick` : la porte n'a ni table d'entrées ni asset
 * d'action. Les commandes du jeu — rebindables, à la manette — sont le LOT-1016.
 */
UCLASS()
class AJadgPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AJadgPlayerController();

	virtual void BeginPlay() override;
	virtual void PlayerTick(float DeltaSeconds) override;

private:
	UPROPERTY()
	TObjectPtr<AJadgWalker> Hero;

	void OrderWalk();
};
