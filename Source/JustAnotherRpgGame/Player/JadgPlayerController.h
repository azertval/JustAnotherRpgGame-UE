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
 * @brief Les commandes du joueur : la caméra libre, la marche au clic, l'interaction, le meneur,
 *        les réponses d'un dialogue (LOT-1012, LOT-1016) ; en combat, la cible, la destination,
 *        l'attaque, la capacité, la fin du tour (LOT-1017).
 *
 * Les commandes et leurs touches sont dans `Config/DefaultGame.ini` (`UJadgControls`, qui en donne
 * la table). Au lancement, chaque commande devient une action d'Enhanced Input créée ici, dans un
 * contexte créé ici : ni asset d'action, ni table d'entrées, ni Blueprint.
 *
 * Le contrôleur ne décide de rien : il passe l'ordre au groupe (`AJadgParty`), à la caméra
 * (`AJadgCameraPawn`), à l'exploration (`UJadgExploration`) ou au combat (`AJadgCombat`).
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

	/**
	 * @brief Tient le pointeur en @p ScreenPosition, en pixels, à la place du curseur de la souris.
	 *
	 * Un jeu lancé hors écran n'a pas de curseur : le parcours (`AJadgWalkthrough`) dit où il
	 * clique, puis presse le bouton comme un joueur. Tout le reste du clic est celui du joueur.
	 */
	void PointAt(const FVector2D& ScreenPosition);

	/// Ce que le pointeur désigne dans la carte : sous le curseur, ou là où `PointAt` l'a posé.
	bool PointerHit(FHitResult& OutHit) const;

	/// Le nombre de commandes qui ont au moins une touche.
	int32 CommandCount() const { return Actions.Num(); }

private:
	UPROPERTY()
	TObjectPtr<UInputMappingContext> Context;

	UPROPERTY()
	TMap<FName, TObjectPtr<UInputAction>> Actions;

	TOptional<FVector2D> Pointer;

	/// La valeur de chaque axe pour la trame en cours.
	TMap<FName, float> Axes;

	void OnAxis(const FInputActionInstance& Instance);
	void OnPressed(const FInputActionInstance& Instance);
	float Axis(FName Command) const;
	void OrderUnderCursor();
};
