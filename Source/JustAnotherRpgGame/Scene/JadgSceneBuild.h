// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "JadgSceneBuild.generated.h"

class AVolume;

/**
 * @brief Ce que le script de construction d'une scène ne peut pas faire en Python (LOT-1012).
 *
 * `scripts/maps/build_scene_unreal.py` règle tous les acteurs d'une carte par l'API Python du
 * moteur. Deux gestes lui échappent sans fenêtre :
 *
 * - **créer un acteur** : la voie de l'éditeur (`EditorActorSubsystem`) passe par une vue de
 *   niveau, qu'un éditeur sans fenêtre n'a pas, et la création directe dans un monde n'est pas
 *   exposée à Python ;
 * - **donner sa forme à un volume** : un volume créé par programme n'a pas de brosse — donc pas
 *   d'étendue, et un volume de navigation sans étendue ne produit aucun maillage ; l'éditeur la
 *   dessine d'ordinaire au moment où l'on pose le volume à la main.
 *
 * Ces fonctions font ce que fait l'éditeur, appelées par le script. Aucune logique de jeu.
 */
UCLASS()
class UJadgSceneBuild : public UBlueprintFunctionLibrary
{
	GENERATED_BODY()

public:
	/// Crée un acteur de la classe donnée dans le monde, où qu'il tombe.
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static AActor* SpawnActor(UObject* WorldContextObject, TSubclassOf<AActor> ActorClass, const FTransform& Transform);

	/**
	 * @brief Crée un volume en forme de boîte. Fonction d'éditeur : hors d'une construction
	 *        d'éditeur elle ne crée rien.
	 * @param Size Les trois côtés de la boîte, en centimètres.
	 * @return Le volume, ou rien s'il n'a pas pu être créé.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static AVolume* SpawnBoxVolume(UObject* WorldContextObject, TSubclassOf<AVolume> VolumeClass, FVector Centre, FVector Size);
};
