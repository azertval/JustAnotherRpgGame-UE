// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgCaptureDirector.generated.h"

class AJadgCameraPawn;
class AJadgDayLight;
class AJadgShot;

/**
 * @brief Prend les captures d'une carte et mesure sa cadence, sans fenêtre et sans personne
 *        (LOT-1012).
 *
 * Le mode de jeu crée cet acteur quand la ligne de commande porte `-JadgCapture=<dossier>` :
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject /Game/Maps/Levels/porte-1012 -game -RenderOffscreen
 *         -ResX=1920 -ResY=1080 -ForceRes -JadgCapture=<dossier> -JadgHours=12:00,22:00
 *         -JadgMeasure=10
 *
 * Il passe **par la caméra du joueur** (`AJadgCameraPawn`), aux cadrages que la carte porte
 * (`AJadgShot`) : la capture est l'image que le joueur a, pas un rendu à part. Pour chaque heure
 * et chaque cadrage il règle l'heure, pose la vue, laisse `-JadgSettle` trames à l'éclairage pour
 * se stabiliser (Lumen accumule dans le temps), puis écrit `<cadrage>-<HHMM>.png`.
 *
 * Avec `-JadgMeasure=<secondes>` il fait ensuite tourner la caméra autour du premier cadrage, à
 * chaque heure, et relève chaque trame : durée, temps du fil de jeu, du fil de rendu et du
 * processeur graphique. `mesure.json` en donne la moyenne, la pire trame et le 1 % le plus lent,
 * avec le temps écoulé entre le lancement du processus et la première trame de la carte.
 *
 * `mesure.json` porte aussi la **mémoire graphique** à la fin du passage (celle du processus et
 * celle des textures, en flux ou non) et les **maillages** de la carte : leur nombre, leurs
 * triangles Nanite, la taille de leurs ressources et la plus grosse pièce (LOT-1019).
 *
 * `-JadgPost=<a,b…>` règle le post-traitement avant la première capture, pour comparer un rendu
 * avec et sans (LOT-1019, questions du standard 3D §8) : `contour` ajoute la passe du contour
 * sombre (`/Game/Scenes/Common/M_Contour`, écrite par `build_level.py`), `sans-contour` la
 * retire ; `sans-ao` coupe l'occlusion ambiante d'écran de Lumen ; `sans-halo` le halo
 * (`bloom`) ; `sans-ombres-lampes` les ombres portées des lampes (`JadgLamp`). Les options
 * appliquées sont écrites dans `mesure.json`.
 *
 * Il quitte ensuite le jeu : code 0, ou 1 si un cadrage, une heure ou un fichier manque.
 */
UCLASS()
class AJadgCaptureDirector : public AActor
{
	GENERATED_BODY()

public:
	AJadgCaptureDirector();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	enum class EPhase : uint8 { Opening, Settling, Writing, Measuring, Done };

	struct FSample
	{
		float Frame = 0.0f;
		float Game = 0.0f;
		float Render = 0.0f;
		float Gpu = 0.0f;
	};

	struct FMeasure
	{
		FString Hour;
		TArray<FSample> Samples;
	};

	UPROPERTY()
	TObjectPtr<AJadgCameraPawn> View;

	UPROPERTY()
	TObjectPtr<AJadgDayLight> DayLight;

	UPROPERTY()
	TArray<TObjectPtr<AJadgShot>> Shots;

	FString OutputDir;
	TArray<FString> Hours;
	int32 SettleFrames = 120;
	float MeasureSeconds = 0.0f;

	EPhase Phase = EPhase::Opening;
	int32 HourIndex = 0;
	int32 ShotIndex = 0;
	int32 FramesInStep = 0;
	float SecondsInStep = 0.0f;
	double OpenSeconds = 0.0;
	FString PendingFile;
	TArray<FString> Written;
	TArray<FMeasure> Measures;
	TArray<FString> PostApplied;

	bool ApplyPostOptions(const FString& Options);
	void Frame(const AJadgShot& Shot, float ExtraYaw = 0.0f);
	bool SetHour(const FString& Hour);
	void BeginShot();
	void BeginMeasure();
	void Finish(int32 ExitCode, const FString& Reason = FString());
	void WriteReport() const;
};
