// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgWalkthrough.generated.h"

class AJadgParty;
class UJadgExploration;

/**
 * @brief Joue la quête « Des pommes pour l'arène » sur les deux cartes d'essai, dans le jeu lancé,
 *        sans personne (LOT-1016).
 *
 * Le mode de jeu crée cet acteur quand la ligne de commande porte `-JadgParcours=<dossier>` :
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject /Game/Maps/Levels/essai/etals -game -RenderOffscreen
 *         -ResX=1920 -ResY=1080 -ForceRes -JadgParcours=<dossier> -JadgSeed=1
 *
 * Il ne triche pas : il donne au groupe les ordres qu'un joueur donne (`AJadgParty::OrderInteract`,
 * `OrderWalk`) et au dialogue les réponses qu'un joueur choisit (`UJadgExploration::ChooseById`).
 * Le meneur marche sur le maillage de navigation, les portails ouvrent la carte du moteur de la
 * carte cible, le HUD dessine le dialogue. L'acteur renaît à chaque carte et retrouve où il en est
 * dans ce que le jeu sait : la carte courante et la valeur de `quete.pommes`.
 *
 * | Où | Quête | Ordre |
 * |---|---|---|
 * | étals | inconnue | marcher près de la mère, capturer l'invite et le contour, interagir (la touche) ; accepter |
 * | étals | acceptée | marcher jusqu'au portail de l'est |
 * | parvis | acceptée | entrer dans la zone du parvis : le garde parle ; plaider (jet de Persuasion) |
 * | parvis | enfant libéré | revenir au portail de l'ouest |
 * | étals | enfant libéré | aller parler à la mère (le clic) ; la quête est rendue |
 *
 * Chaque réplique est capturée avant sa réponse (`parcours-NN.png`, HUD compris), et
 * `parcours.json` relève les étapes et leur instant. `-JadgSeed` fixe la graine du jet : l'issue
 * d'une graine est celle que `Jadg.Exploration.QueteDesPommes` relève.
 *
 * Il quitte le jeu : code 0 quand la mère a retrouvé l'enfant, 1 si le parcours s'arrête avant
 * (un jet raté, un ordre sans suite au bout de `StallSeconds`).
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

	FString OutputDir;
	/// L'état pour lequel un ordre a déjà été donné : « carte|quête ».
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

	void Order(AJadgParty& Party, const FString& Map, const FString& Quest);
	void Answer();
	void Note(const FString& What) const;
	void Finish(int32 ExitCode, const FString& Reason);
};
