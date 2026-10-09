// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgShot.generated.h"

/**
 * @brief Un cadrage de capture, posé dans la carte par le script qui la construit (LOT-1012).
 *
 * L'acteur est au **point visé** ; sa rotation est celle du regard (lacet, et tangage négatif
 * sous l'horizon) ; `Distance` est celle de la caméra au point visé. Les cadrages s'écrivent dans
 * la description de scène (`shots`) : la carte n'en garde que la sortie.
 */
UCLASS()
class AJadgShot : public AActor
{
	GENERATED_BODY()

public:
	AJadgShot();

	/// Le nom du cadrage, qui devient celui du fichier de capture.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	FString ShotId;

	/// Le rang du cadrage dans la description de scène : l'ordre des captures.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	int32 Order = 0;

	/// Distance de la caméra au point visé, en centimètres.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	float Distance = 2000.0f;

	/// L'étage que le cadrage regarde (`storey` du cadrage, LOT-1022) : les étages au-dessus de lui
	/// sont cachés le temps de sa capture ; -1 : tous restent montrés.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	int32 Storey = -1;
};
