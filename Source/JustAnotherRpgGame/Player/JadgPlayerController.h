// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"

#include "JadgPlayerController.generated.h"

class UInputAction;
class UInputMappingContext;
struct FInputActionInstance;

/**
 * @brief Les commandes du joueur en exploration : la caméra libre, la marche au clic,
 *        l'interaction, le meneur, les réponses d'un dialogue (LOT-1012, LOT-1016).
 *
 * Les commandes et leurs touches sont dans `Config/DefaultGame.ini` (`UJadgControls`, qui en donne
 * la table). Au lancement, chaque commande devient une action d'Enhanced Input créée ici, dans un
 * contexte créé ici : ni asset d'action, ni table d'entrées, ni Blueprint.
 *
 * Le contrôleur ne décide de rien : il passe l'ordre au groupe (`AJadgParty`), à la caméra
 * (`AJadgCameraPawn`) ou à l'exploration (`UJadgExploration`).
 */
UCLASS()
class AJadgPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AJadgPlayerController();

	virtual void BeginPlay() override;
	virtual void PlayerTick(float DeltaSeconds) override;
	virtual void SetupInputComponent() override;

	/// Joue le geste de la commande @p Command, comme si sa touche venait d'être pressée.
	void Press(FName Command);

	/// Le nombre de commandes qui ont au moins une touche.
	int32 CommandCount() const { return Actions.Num(); }

private:
	UPROPERTY()
	TObjectPtr<UInputMappingContext> Context;

	UPROPERTY()
	TMap<FName, TObjectPtr<UInputAction>> Actions;

	/// La valeur de chaque axe pour la trame en cours.
	TMap<FName, float> Axes;

	void OnAxis(const FInputActionInstance& Instance);
	void OnPressed(const FInputActionInstance& Instance);
	float Axis(FName Command) const;
	void OrderUnderCursor();
};
