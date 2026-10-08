// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"

#include "JadgWalker.generated.h"

class UAnimSequence;

/**
 * @brief Un personnage lié qui marche sur le maillage de navigation et se tient au repos
 *        (LOT-1012).
 *
 * Deux clips, joués directement par le composant de maillage, sans graphe d'animation ni
 * Blueprint : `IdleClip` à l'arrêt, `WalkClip` en marche. Le clip de marche de la chaîne des
 * personnages couvre une distance fixe par cycle (`WalkSpeed`, 3 m/s : une case de 1,5 m en
 * 0,5 s, `Planning/standards/personnages-3d.md`) ; il est joué au prorata de la vitesse réelle,
 * pour que le pied posé ne glisse pas pendant l'accélération.
 *
 * `Patrol` fait tourner le personnage entre des points, en boucle : c'est ce qui montre le lion
 * marcher sans joueur. Un personnage `bPlayable` attend l'ordre du joueur (`WalkTo`).
 */
UCLASS()
class AJadgWalker : public ACharacter
{
	GENERATED_BODY()

public:
	AJadgWalker();

	UPROPERTY(EditAnywhere, Category = "Jadg")
	TObjectPtr<UAnimSequence> IdleClip;

	UPROPERTY(EditAnywhere, Category = "Jadg")
	TObjectPtr<UAnimSequence> WalkClip;

	/// La vitesse que le clip de marche représente, en centimètres par seconde.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	float WalkSpeed = 300.0f;

	/// Celui que le joueur mène.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	bool bPlayable = false;

	/// Les points d'une ronde, en repère du monde ; vide : le personnage attend.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	TArray<FVector> Patrol;

	/// Envoie le personnage vers un point du maillage de navigation.
	void WalkTo(const FVector& Destination);

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	bool bWalking = false;
	int32 PatrolIndex = 0;

	void Play(UAnimSequence* Clip);
};
