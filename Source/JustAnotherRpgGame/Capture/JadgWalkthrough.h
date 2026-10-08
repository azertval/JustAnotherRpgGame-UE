// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "InputCoreTypes.h"

#include "JadgWalkthrough.generated.h"

class AJadgCameraPawn;
class AJadgParty;
class AJadgPlayerController;
class UJadgExploration;

/**
 * @brief Joue la quête « Des pommes pour l'arène » sur les cartes d'essai, dans le jeu lancé, sans
 *        personne — **par les touches et les clics du joueur** (LOT-1016).
 *
 * Le mode de jeu crée cet acteur quand la ligne de commande porte `-JadgParcours=<dossier>` :
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject /Game/Maps/Levels/essai/etals -game -RenderOffscreen
 *         -ResX=1920 -ResY=1080 -ForceRes -JadgParcours=<dossier> -JadgSeed=1
 *
 * Il presse les touches que `Config/DefaultGame.ini` donne aux commandes, en les injectant dans le
 * contrôleur du joueur (`APlayerController::InputKey`) : elles passent par Enhanced Input, le
 * contexte et les actions du jeu, comme celles d'un clavier. Un clic est le bouton gauche pressé,
 * le pointeur posé sur ce qu'il vise (`AJadgPlayerController::PointAt`) — un jeu lancé hors écran
 * n'a pas de curseur ; le parcours vérifie d'abord que le pointeur désigne bien sa cible.
 *
 * **D'abord les commandes**, sur la première carte, chacune jugée à son effet : tourner (les deux
 * touches), tourner à la souris sous la touche tenue, incliner (les deux touches), la molette dans
 * les deux sens, passer la main quatre fois (le tour du groupe), déplacer le point visé puis
 * recentrer.
 *
 * **Puis la quête** ; l'acteur renaît à chaque carte et retrouve où il en est dans ce que le jeu
 * sait (la carte, `quete.pommes`, le coffre, la rencontre) :
 *
 * | Où | État | Geste |
 * |---|---|---|
 * | étals | quête inconnue | clic au sol près de la mère ; capture de l'invite et du contour ; touche d'interaction ; réponse au clavier |
 * | étals | quête acceptée | clic sur le coffre : le meneur y va et l'ouvre |
 * | étals | coffre ouvert | marche jusqu'au portail de l'est |
 * | parvis | quête acceptée | marche dans la zone du parvis : le garde parle ; plaider (jet de Persuasion) |
 * | parvis | enfant libéré | clic sur le maître d'arène ; « combattre » : l'arène vide s'ouvre |
 * | arène | rencontre engagée | capture ; touche d'interaction : retour au parvis |
 * | parvis | rencontre quittée | marche jusqu'au portail de l'ouest |
 * | étals | enfant libéré | clic sur la mère ; la quête est rendue |
 *
 * Les trois marches vers un portail ou une zone sont des ordres donnés au groupe
 * (`AJadgParty::OrderWalk`), pas des clics : leur but n'est pas toujours à l'écran.
 *
 * Chaque réplique est capturée avant sa réponse (`parcours-NN.png`, HUD compris), et
 * `parcours.json` relève les étapes et leur instant. `-JadgSeed` fixe la graine du jet : l'issue
 * d'une graine est celle que `Jadg.Exploration.QueteDesPommes` relève.
 *
 * Il quitte le jeu : code 0 quand la mère a retrouvé l'enfant, 1 dès qu'une commande n'a pas son
 * effet, qu'un clic ne désigne pas sa cible ou qu'un geste reste sans suite `StallSeconds`.
 */
UCLASS()
class AJadgWalkthrough : public AActor
{
	GENERATED_BODY()

public:
	AJadgWalkthrough();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY()
	TObjectPtr<UJadgExploration> Exploration;

	UPROPERTY()
	TObjectPtr<AJadgPlayerController> Player;

	UPROPERTY()
	TObjectPtr<AJadgCameraPawn> View;

	/// Une touche tenue, et la trame où elle se relâche.
	struct FHeld
	{
		FKey Key;
		int32 Until = 0;
	};
	TArray<FHeld> Held;

	FString OutputDir;
	/// L'état pour lequel un geste a déjà été fait.
	FString Ordered;
	/// La réplique déjà capturée, et le fichier attendu.
	FString ShotLine;
	FString PendingFile;
	int32 Frames = 0;
	int32 FramesInLine = 0;
	double StateSince = 0.0;
	bool bDone = false;
	/// Le meneur va se poster près de la mère pour la solliciter à la touche ; son invite capturée.
	bool bApproaching = false;
	bool bPromptShot = false;
	/// L'essai des commandes : son rang, la trame où il reprend, ce qu'il a relevé avant le geste.
	int32 ControlStep = 0;
	int32 ResumeAt = 0;
	float Before = 0.0f;
	int32 Taps = 0;
	/// Dans l'arène vide : la capture demandée, puis le retour.
	bool bArenaShot = false;

	void Press(const FKey& Key, int32 ForFrames = 2);
	void Axis(const FKey& Key, float Delta);
	void ReleaseDue();
	bool CommandKey(FName Command, int32 Rank, FKey& OutKey) const;

	/// Vrai tant que l'essai des commandes n'est pas fini ; il s'arrête en erreur à la première
	/// commande sans effet.
	bool TryControls(AJadgParty& Party);
	bool Expect(bool bHolds, const TCHAR* What);

	bool ClickGround(AJadgParty& Party, const FVector2D& Cell, const TCHAR* Where);
	bool ClickEntity(AJadgParty& Party, const FString& EntityId, const TCHAR* Who);
	FString EntityAt(const TCHAR* Type, const FIntPoint* Cell) const;
	void Shoot(const FString& What);
	bool ShotWritten() const;

	void Order(AJadgParty& Party, const FString& Map, const FString& Quest);
	void Answer();
	void Note(const FString& What) const;
	void Finish(int32 ExitCode, const FString& Reason);
};
