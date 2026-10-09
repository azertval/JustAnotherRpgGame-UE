// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "InputCoreTypes.h"

#include "JadgScreensTour.generated.h"

class AJadgPlayerController;
class AJadgHud;
class UJadgButton;
class UJadgExploration;

/**
 * @brief Le tour des écrans (LOT-1020) : chaque écran ouvert, parcouru au clavier et à la souris,
 *        capturé, refermé — dans le jeu lancé, sans personne.
 *
 * Le mode de jeu le crée quand la ligne de commande porte `-JadgEcrans=<dossier>` :
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject /Game/Maps/Levels/essai/etals -game -RenderOffscreen
 *         -ResX=1920 -ResY=1080 -ForceRes -JadgEcrans=<dossier>
 *
 * Comme au parcours (`AJadgWalkthrough`), les touches du **jeu** sont injectées dans le contrôleur
 * du joueur (`G`, `P`, `I`, `J`, `M`, `F9`, `Échap`, `Tab`) ; dans une page, qui a pris le clavier,
 * les touches et les clics sont injectés dans l'application Slate (`ProcessKeyDownEvent`,
 * `ProcessMouseButtonDownEvent`), au centre du bouton visé : le chemin du clavier et de la souris
 * du joueur. Chaque geste est jugé à son effet (la page ouverte, le focus déplacé, le meneur
 * changé, la langue changée…).
 *
 * Sur la carte d'arène avec une rencontre (`-JadgRencontre=`), il attend le tour du joueur, fige le
 * combat et capture son interface. Sinon il fait le tour de tous les écrans, en français, puis
 * passe le jeu en anglais par l'écran Options (et rend au poste son fichier d'options à la fin).
 *
 * Les captures (`<écran>.png`, interface comprise) et `ecrans.json` (les étapes, leur effet) vont
 * dans le dossier. Code 0 si chaque geste a eu son effet, 1 sinon.
 */
UCLASS()
class AJadgScreensTour : public AActor
{
	GENERATED_BODY()

public:
	AJadgScreensTour();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	struct FStep
	{
		FString Name;
		TFunction<bool()> Act;
	};

	UPROPERTY()
	TObjectPtr<AJadgPlayerController> Player;

	UPROPERTY()
	TObjectPtr<UJadgExploration> Exploration;

	TArray<FStep> Steps;
	int32 Current = 0;
	int32 Wait = 0;
	int32 Frames = 0;
	int32 StepFrames = 0;
	FString OutputDir;
	FString PendingShot;
	FString SavedOptions;
	bool bHadOptions = false;
	TArray<FString> Log;
	TArray<FString> Shots;
	FKey Held;
	FString FirstLeader;

	AJadgHud* Hud() const;
	void Then(const FString& Name, TFunction<bool()> Act);
	/// Une touche du jeu, pressée puis relâchée à la trame suivante, dans le contrôleur du joueur.
	void GameKey(const FKey& Key);
	/// Une touche dans l'application Slate : la page focalisée la reçoit.
	void SlateKey(const FKey& Key);
	/// Un clic gauche injecté au centre du bouton ; faux s'il n'a pas de géométrie.
	bool Click(UJadgButton* Button);
	/// Le bouton de libellé @p Label de l'écran du haut (ou du jeu), de rang @p Rank parmi ses homonymes.
	UJadgButton* Find(const FString& LabelKey, int32 Rank = 0) const;
	/// Le bouton qui a le focus du clavier dans la page du haut ; rien sinon.
	UJadgButton* Focused() const;
	/// Demande la capture @p Name, interface comprise ; vrai quand elle est écrite.
	bool Shot(const FString& Name);
	void Note(const FString& Line);
	void Finish(int32 Code);
	void TourScreens();
	void TourCombat();
};
