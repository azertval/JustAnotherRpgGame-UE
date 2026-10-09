// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "JadgSceneBuild.generated.h"

class AVolume;
class UMaterialInterface;
class UStaticMesh;

/**
 * @brief Ce que le script de construction d'une scène ne peut pas faire en Python (LOT-1012).
 *
 * `scripts/maps/build_level.py` règle tous les acteurs d'une carte par l'API Python du
 * moteur. Deux gestes lui échappent sans fenêtre :
 *
 * - **créer un acteur** : la voie de l'éditeur (`EditorActorSubsystem`) passe par une vue de
 *   niveau, qu'un éditeur sans fenêtre n'a pas, et la création directe dans un monde n'est pas
 *   exposée à Python ;
 * - **donner sa forme à un volume** : un volume créé par programme n'a pas de brosse — donc pas
 *   d'étendue, et un volume de navigation sans étendue ne produit aucun maillage ; l'éditeur la
 *   dessine d'ordinaire au moment où l'on pose le volume à la main.
 *
 * Le format de carte du LOT-1018 (`scripts/maps/build_level.py`) en ajoute trois :
 *
 * - **poser N fois un maillage** dans un seul acteur (les pièces d'une couche de la v4 migrée, un
 *   dallage) : un composant d'instances ne s'ajoute pas à un acteur depuis Python ;
 * - **créer un terrain** (`ALandscape`) depuis ses hauteurs et ses couches de matière, que le
 *   script régénère depuis la description : l'import d'un Landscape n'est exposé qu'au C++ ;
 * - **contrôler le maillage de navigation** du niveau construit : les points qu'on n'atteint pas.
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

	/**
	 * @brief Un acteur qui porte @p Mesh une fois par transformation de @p Transforms, dans un
	 *        composant d'instances statique, sa collision prise sur le maillage.
	 * @return L'acteur, ou rien sans monde ni maillage.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static AActor* SpawnInstances(UObject* WorldContextObject, UStaticMesh* Mesh, const TArray<FTransform>& Transforms);

	/**
	 * @brief Crée un terrain (`ALandscape`) de @p QuadsX × @p QuadsY quads, des composants de 63
	 *        quads d'une section. Fonction d'éditeur.
	 * @param Location Le coin du terrain, dans le monde ; @p Scale, l'échelle de l'acteur (le côté
	 *        d'un quad en X et Y, en centimètres ; en Z, 100 donne 256 m de dénivelé).
	 * @param Heights  (QuadsX + 1) × (QuadsY + 1) hauteurs, ligne par ligne, 32 768 au niveau de
	 *        l'acteur.
	 * @param LayerNames Les couches de matière, dans l'ordre de @p Weights : pour chacune,
	 *        (QuadsX + 1) × (QuadsY + 1) poids de 0 à 255, à la suite.
	 * @param LayerFolder Le dossier de contenu où vivent les objets de couche (`LI_<couche>`), créés
	 *        s'ils n'existent pas.
	 * @return Le terrain, ou rien si les tailles ne s'accordent pas.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static AActor* SpawnLandscape(UObject* WorldContextObject, FVector Location, FVector Scale, int32 QuadsX, int32 QuadsY,
		const TArray<int32>& Heights, const TArray<FString>& LayerNames, const TArray<uint8>& Weights, UMaterialInterface* Material,
		const FString& LayerFolder);

	/**
	 * @brief Construit le maillage de navigation du monde, puis rend le rang des points de
	 *        @p Points qu'aucun chemin ne relie à @p Start. Fonction d'éditeur.
	 * @return Les rangs des points inatteignables ; `[-1]` si @p Start n'est pas sur le maillage.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static TArray<int32> UnreachablePoints(UObject* WorldContextObject, FVector Start, const TArray<FVector>& Points);
};
