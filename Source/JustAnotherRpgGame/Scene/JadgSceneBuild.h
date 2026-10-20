// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"

#include "JadgSceneBuild.generated.h"

class AVolume;
class UMaterialFunctionInterface;
class UMaterialInterface;
class UMaterial;
class UMaterialExpression;
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
	 * @param bWeightBlended Faux pour des couches que la matière lit comme des masques indépendants
	 *        (`LandscapeLayerSample`) : leurs poids ne se normalisent pas entre eux.
	 * @return Le terrain, ou rien si les tailles ne s'accordent pas.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static AActor* SpawnLandscape(UObject* WorldContextObject, FVector Location, FVector Scale, int32 QuadsX, int32 QuadsY,
		const TArray<int32>& Heights, const TArray<FString>& LayerNames, const TArray<uint8>& Weights, UMaterialInterface* Material,
		const FString& LayerFolder, bool bWeightBlended = true);

	/**
	 * @brief Les couches de terrain qu'une matière attend (ses `LandscapeLayerBlend`, `LayerWeight`,
	 *        `LayerSample`), par leur nom : une matière de paysage d'un pack se peint par les noms
	 *        qu'elle déclare, que Python ne lit pas. Fonction d'éditeur.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static TArray<FString> LandscapeLayerNames(UMaterialInterface* Material);

	/** Finish the GPU edit-layer merge before saving a UE 5.8 Landscape. Requires rendering. */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static bool FinalizeLandscapeLayers(AActor* Landscape);

	/** Name the imported edit layer and stack empty edit layers above it, so hand sculpting and
	 * painting stay separate from the generated relief and survive its regeneration. Editor only. */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static bool NameLandscapeEditLayers(AActor* Landscape, const FString& BaseLayer, const TArray<FString>& ExtraLayers);

	/** Read native paint weights at a world point, in the supplied layer order (editor audit). */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static TArray<float> LandscapeWeightsAt(AActor* Landscape, FVector Location, const TArray<FString>& LayerNames);

	/**
	 * @brief Porte au `Landscape` un graphe écrit pour le Mesh Terrain — une matière ou une fonction
	 *        de matière, @p MaterialOrFunction, toujours une copie de celle du pack :
	 *        - chaque lecture de canal (`MeshPartitionChannelSample`) devient une couche de paysage du
	 *          même nom (`LandscapeLayerSample`) ;
	 *        - les coordonnées du Mesh Terrain (`MeshPartitionTexcoord`) deviennent celles du maillage
	 *          (sortie « uv ») et la position dans le monde, en centimètres (sortie « uv [unit] ») ;
	 *        - ce qui reste de nœuds du Mesh Terrain est retiré.
	 *        Ces nœuds vivent dans un module d'éditeur : le jeu lancé ne compile pas une matière qui
	 *        les garde. Le reste du graphe ne change pas ; le script recompile ensuite. Fonction d'éditeur.
	 *        Avec @p bVertexLayers, les canaux Material B–E se lisent dans RGBA des sommets,
	 *        pour prolonger les mêmes couches sur le décor périphérique non parcourable.
	 * @return Les noms des canaux devenus couches, sans doublon.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static TArray<FString> PortMeshTerrainGraph(UObject* MaterialOrFunction, bool bVertexLayers = false);

	/**
	 * @brief Dans le graphe de @p MaterialOrFunction, fait appeler @p To[i] là où @p From[i] l'était :
	 *        une copie portée appelle les copies portées des fonctions du pack. Fonction d'éditeur.
	 * @return Le nombre d'appels redirigés.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static int32 RetargetFunctionCalls(UObject* MaterialOrFunction, const TArray<UMaterialFunctionInterface*>& From,
		const TArray<UMaterialFunctionInterface*>& To);

	/**
	 * @brief Construit la représentation Nanite d'un terrain qui la demande (`bEnableNanite`, réglé
	 *        par le script) : sans elle, le déplacement de sa matière ne se rend pas. Fonction d'éditeur.
	 * @return Vrai si le terrain porte ses composants Nanite après la construction.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static bool BuildLandscapeNanite(AActor* Landscape);

	/** True only when the proxy has a current native Nanite representation. */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static bool IsLandscapeNaniteCurrent(AActor* Landscape);

	/**
	 * @brief Relit sur la matière de chaque composant d'un terrain les types d'herbe qu'elle fait
	 *        pousser : le composant les garde en cache, et une matière qui n'en a plus laisse sans
	 *        cela une référence vers l'ancien type. Fonction d'éditeur.
	 * @return Le nombre de types d'herbe que le terrain cite encore, -1 si l'acteur n'en est pas un.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static int32 RefreshLandscapeGrass(AActor* Landscape);

	/** Native access to World Partition fields which Python cannot inspect or edit. */
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static UObject* WorldPartitionRuntimeHash(UObject* WorldContextObject);

	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static bool SetWorldPartitionStreaming(UObject* WorldContextObject, bool bEnabled);

	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static bool IsWorldPartitionStreaming(UObject* WorldContextObject);

	/**
	 * @brief Ajoute au hachage `WorldPartitionRuntimeHashSet` une partition de grille @p Name
	 *        (cellules de @p CellSize cm, chargées à @p LoadingRange cm), sans HLOD ; les acteurs
	 *        dont le `RuntimeGrid` vaut @p Name y vont. Python ne peut ni construire la description
	 *        d'une partition ni nommer sa grille. Fonction d'éditeur.
	 * @return Vrai si la partition existe (déjà présente : ses réglages sont mis à jour).
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static bool AddRuntimePartition(UObject* WorldContextObject, FName Name, int32 CellSize, int32 LoadingRange);

	/**
	 * @brief Construit le maillage de navigation du monde, puis rend le rang des points de
	 *        @p Points qu'aucun chemin ne relie à @p Start. Fonction d'éditeur.
	 * @return Les rangs des points inatteignables ; `[-1]` si @p Start n'est pas sur le maillage.
	 */
	UFUNCTION(BlueprintCallable, Category = "Jadg", meta = (WorldContext = "WorldContextObject"))
	static TArray<int32> UnreachablePoints(UObject* WorldContextObject, FVector Start, const TArray<FVector>& Points);

	/// Nanite Displacement is a hidden material property, unavailable to Python's enum.
	/// Connect output zero of an expression belonging to the same material. Editor only.
	UFUNCTION(BlueprintCallable, Category = "Jadg")
	static bool ConnectMaterialDisplacement(UMaterial* Material, UMaterialExpression* Expression);
};
