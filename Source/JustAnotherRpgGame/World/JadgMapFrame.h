// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgMapFrame.generated.h"

/**
 * @brief Ce qui relie une carte du moteur à une carte de Core : laquelle, et où est sa grille
 *        (LOT-1016).
 *
 * Les portails, les points d'arrivée, les PNJ et les lumières d'une carte sont des données de
 * Core, posées sur des **cases** de 1,5 m. Cet acteur dit où tombe la case (0, 0) dans la carte
 * du moteur et ce que deviennent ses axes ; il est posé par le script qui construit la scène
 * (`scripts/maps/build_level.py`, depuis l'origine de la description v5), qui mesure le repère
 * au lieu de le supposer. Une carte du moteur sans cet acteur ne joue aucune carte de Core : la
 * porte du LOT-1012.
 *
 * La carte du moteur d'une carte de Core se nomme d'après elle : `/Game/Maps/Levels/<LevelId>`
 * (`MapPackage`). C'est ce qu'un portail ouvre ; le script refuse une description qui s'en écarte.
 */
UCLASS()
class AJadgMapFrame : public AActor
{
	GENERATED_BODY()

public:
	AJadgMapFrame();

	/// La carte de Core, par son identifiant (`essai/etals`, `central-empire/capital/arenarea`).
	UPROPERTY(EditAnywhere, Category = "Jadg")
	FString LevelId;

	/// Le dossier où cette carte se lit avant ceux du jeu, relatif au projet ; vide : aucun.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	FString LevelsRoot;

	/// Le côté d'une case, en centimètres.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	float CellSize = 150.0f;

	/// La direction des colonnes croissantes et celle des lignes croissantes, dans le moteur.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	FVector East = FVector(1.0, 0.0, 0.0);

	UPROPERTY(EditAnywhere, Category = "Jadg")
	FVector South = FVector(0.0, 1.0, 0.0);

	/**
	 * La hauteur du sol de chaque étage praticable par rapport à l'acteur, en centimètres, le rez en
	 * tête à 0, un sous-sol en dessous (format de carte v5, D-51, LOT-1018, LOT-1022) ; vide pour une
	 * carte d'un seul niveau. Posée par `scripts/maps/build_level.py` depuis les étages de la
	 * description (`storeys`).
	 */
	UPROPERTY(EditAnywhere, Category = "Jadg")
	TArray<float> StoreyHeights;

	/**
	 * Le niveau de chargement de chaque étage, dans l'ordre de `StoreyHeights` : le paquet du niveau
	 * que `build_level.py` construit pour lui (`<carte>-etage-<nom>`), toujours chargé avec la carte
	 * (D-51, LOT-1022) ; vide pour une carte d'un seul niveau.
	 */
	UPROPERTY(EditAnywhere, Category = "Jadg")
	TArray<FString> StoreyLevels;

	/// L'étage d'un point du monde : le plus haut dont le sol est sous lui, à un demi-mètre près.
	int32 StoreyAt(double WorldZ) const;

	/**
	 * Montre ou cache le niveau de chargement d'un étage (`StoreyLevels`) : caché, il quitte le monde
	 * — ni rendu, ni collision —, mais reste chargé. Rend faux si l'étage n'a pas de niveau.
	 */
	bool ShowStorey(int32 Storey, bool bVisible) const;

	/// La hauteur, dans le monde, du sol de l'étage @p Storey ; celle de l'acteur hors des étages.
	double StoreyZ(int32 Storey) const;

	/// Le point du monde d'une position continue en cases ; le coin de la case (0, 0) est l'acteur.
	FVector ToWorld(const FVector2D& Cell) const;

	/// La position continue, en cases, d'un point du monde (sa hauteur ne compte pas).
	FVector2D ToCell(const FVector& World) const;

	/// Le chemin de la carte du moteur qui joue la carte de Core @p LevelId.
	static FString MapPackage(const FString& InLevelId);
};
