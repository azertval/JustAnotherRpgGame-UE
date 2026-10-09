// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "InputCoreTypes.h"

#include "JadgCombatWalkthrough.generated.h"

class AJadgCombat;
class AJadgParty;
class AJadgPlayerController;
class AJadgWalker;
class UJadgExploration;

/**
 * @brief Joue le début de la série de l'arène dans le jeu lancé, sans personne, **par les touches
 *        et les clics du joueur** (LOT-1017) : la rencontre `arene-bandits` jusqu'à son issue.
 *
 * Le mode de jeu le crée quand la ligne de commande porte `-JadgParcoursCombat=<dossier>` :
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject /Game/Maps/Levels/essai/parvis -game -RenderOffscreen
 *         -ResX=1920 -ResY=1080 -ForceRes -JadgParcoursCombat=<dossier> -JadgSeed=1
 *
 * | Où | Geste |
 * |---|---|
 * | parvis | clic sur le maître d'arène ; « combattre » au clavier : la bascule ouvre l'arène |
 * | arène | capture du déploiement ; à chaque tour d'un héros, le tour que l'IA jouerait avec le profil de sa classe (`AJadgCombat::PlanForActive`), traduit en gestes : clic au sol sur la destination, clic sur la cible, `Attack` ou le chiffre de la capacité puis `Capacity`, `EndTurn` ; les tours des adversaires se jouent seuls |
 * | arène | capture du premier tour (l'aperçu dessiné), puis de l'issue |
 * | parvis | le groupe est revenu là où il était ; `encounter/arene-bandits/won` est posé |
 *
 * Un clic est vérifié avant d'être pressé : le pointeur doit désigner la cible voulue, ou le sol à
 * moins de 1,12 m du point visé. `-JadgSeed` fixe la graine du combat.
 *
 * Il écrit `parcours.json` (les étapes, leur instant, le journal du combat de Core, la mesure des
 * candidats de l'IA) et quitte : code 0 sur la victoire du groupe revenue au parvis, 1 sur une
 * défaite, un geste refusé, un clic qui ne désigne pas sa cible, ou rien de neuf pendant
 * `StallSeconds`.
 */
UCLASS()
class AJadgCombatWalkthrough : public AActor
{
	GENERATED_BODY()

public:
	AJadgCombatWalkthrough();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY()
	TObjectPtr<UJadgExploration> Exploration;

	UPROPERTY()
	TObjectPtr<AJadgPlayerController> Player;

	struct FHeld
	{
		FKey Key;
		int32 Until = 0;
	};
	TArray<FHeld> Held;

	FString OutputDir;
	FString PendingFile;
	int32 Frames = 0;
	int32 ResumeAt = 0;
	double StateSince = 0.0;
	bool bDone = false;
	/// Le tour du héros en cours de geste : son combattant, son round, et où en sont ses gestes.
	int32 TurnOf = 0;
	int32 TurnRound = 0;
	int32 TurnStep = 0;
	bool bShooting = false;
	bool bAsked = false;

	void Press(const FKey& Key, int32 ForFrames = 2);
	void ReleaseDue();
	bool PressCommand(const TCHAR* Command);
	bool ClickPoint(const FVector& World, const TCHAR* What);
	bool ClickActor(const AActor* Target, const TCHAR* What);
	void Shoot(const FString& What);
	bool ShotWritten() const;

	void OnForecourt(AJadgParty& Party);
	void InArena(AJadgCombat& Combat);
	void PlayHeroTurn(AJadgCombat& Combat);
	void Note(const FString& What) const;
	void Finish(int32 ExitCode, const FString& Reason);
};
