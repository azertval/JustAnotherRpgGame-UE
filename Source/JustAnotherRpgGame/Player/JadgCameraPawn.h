// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"

#include "JadgCameraPawn.generated.h"

class UCameraComponent;
class USpringArmComponent;

/**
 * @brief La caméra de D-49 et D-56 : en perspective, libre en rotation, bornée en inclinaison,
 *        avec un zoom (LOT-1012).
 *
 * Le pion est le **point visé**, au sol ; la caméra le regarde au bout d'un bras. Tourner change
 * le lacet du bras, incliner son tangage entre `MinPitch` (vue rasante) et `MaxPitch` (vue
 * plongeante), zoomer sa longueur. Le pion suit un acteur (`Follow`) ou se déplace librement
 * (`Pan`), ce qui le détache.
 *
 * Les bornes se règlent en texte, dans `Config/DefaultGame.ini`
 * (`[/Script/JustAnotherRpgGame.JadgCameraPawn]`). Celles livrées sont celles de la porte, à
 * juger ; le LOT-1016 les arrête.
 */
UCLASS(config = Game)
class AJadgCameraPawn : public APawn
{
	GENERATED_BODY()

public:
	AJadgCameraPawn();

	/// Inclinaison la plus rasante, en degrés sous l'horizon.
	UPROPERTY(config, EditAnywhere, Category = "Jadg")
	float MinPitch = 15.0f;

	/// Inclinaison la plus plongeante, en degrés sous l'horizon.
	UPROPERTY(config, EditAnywhere, Category = "Jadg")
	float MaxPitch = 70.0f;

	/// Distance la plus courte et la plus longue de la caméra au point visé, en centimètres.
	UPROPERTY(config, EditAnywhere, Category = "Jadg")
	float MinDistance = 400.0f;

	UPROPERTY(config, EditAnywhere, Category = "Jadg")
	float MaxDistance = 4500.0f;

	/// La vue au lancement.
	UPROPERTY(config, EditAnywhere, Category = "Jadg")
	float StartPitch = 40.0f;

	UPROPERTY(config, EditAnywhere, Category = "Jadg")
	float StartDistance = 1600.0f;

	/// Hauteur visée au-dessus des pieds de l'acteur suivi, en centimètres.
	UPROPERTY(config, EditAnywhere, Category = "Jadg")
	float FollowHeight = 100.0f;

	void AddYaw(float Degrees);
	void AddPitch(float Degrees);
	/// Multiplie la distance : moins de 1 rapproche.
	void Zoom(float Factor);
	/// Déplace le point visé dans le plan du sol, relativement au regard ; détache du suivi.
	void Pan(const FVector2D& ForwardRight);

	void Follow(AActor* Actor);

	/// Pose la vue d'un coup : point visé, lacet du regard, inclinaison sous l'horizon, distance.
	/// Les bornes ne s'appliquent pas : c'est la voie des cadrages de capture.
	void SetView(const FVector& Target, float Yaw, float PitchBelowHorizon, float Distance);

	float GetViewYaw() const { return Yaw; }

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY(VisibleAnywhere, Category = "Jadg")
	TObjectPtr<USpringArmComponent> Arm;

	UPROPERTY(VisibleAnywhere, Category = "Jadg")
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY()
	TObjectPtr<AActor> Followed;

	float Yaw = 0.0f;
	float Pitch = 40.0f;
	float Distance = 1600.0f;

	void ApplyArm();
};
