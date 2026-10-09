// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgPrefab.generated.h"

/**
 * @brief Un **préfabriqué** posé sur une carte (LOT-1018, LOT-130) : un acteur composé, dont les
 *        objets sont déclarés en texte (`Source/Elements/Editor/Prefabs/<lieu>/<nom>.json`).
 *
 * `scripts/maps/build_level.py` pose cet acteur à la place que la description de la carte lui donne
 * (`prefabs`), puis chacun de ses objets, attaché à lui. Le déplacer dans l'éditeur déplace le
 * préfabriqué entier ; `scripts/maps/read_level.py` relit sa place, jamais celle de ses objets :
 * un préfabriqué se retouche dans son fichier. Aucune logique de jeu.
 */
UCLASS()
class AJadgPrefab : public AActor
{
	GENERATED_BODY()

public:
	AJadgPrefab();

	/// Le préfabriqué, par son chemin sous `Editor/Prefabs/`, sans extension.
	UPROPERTY(VisibleAnywhere, Category = "Jadg")
	FString PrefabId;

	/// L'identifiant de cette pose dans la description de la carte (`prefabs[].id`).
	UPROPERTY(VisibleAnywhere, Category = "Jadg")
	FString InstanceId;
};
