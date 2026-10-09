// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgDemoWalkthrough.generated.h"

class AJadgParty;
class UJadgExploration;

/**
 * @brief Marche la démo de carte en carte, dans le jeu lancé, sans personne — **par les ordres du
 *        joueur** (LOT-1022).
 *
 * Le mode de jeu crée cet acteur quand la ligne de commande porte `-JadgParcoursDemo=<dossier>` :
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject /Game/Maps/Levels/central-empire/capital/martpart -game
 *         -RenderOffscreen -ResX=1920 -ResY=1080 -ForceRes -JadgParcoursDemo=<dossier>
 *
 * Il enchaîne les étapes de la démo par ses portails, chacune un ordre de marche donné au groupe
 * vers un portail (`AJadgParty::OrderWalk`, le geste du clic au sol, vers un but qui n'est pas
 * toujours à l'écran ; un portail dans le plein se franchit à son contact) ; l'acteur renaît à
 * chaque carte et reprend à l'étape où il en est :
 *
 * | Carte | Portail | Fin de l'étape |
 * |---|---|---|
 * | Martpart | — (la place des étals, auprès de la mère) | le meneur y est |
 * | Martpart | Stravian Avenue (`e4`) | Arenarea s'ouvre |
 * | Arenarea | l'escalier de l'arène (`e4`) | l'Arena of Fate s'ouvre, au vestibule des vestiaires (étage 1) |
 * | Arena of Fate | la porte du triomphe, des vestiaires (`e20`) | le groupe au sable (étage 0) |
 * | Arena of Fate | la porte du triomphe, du sable (`e2`) | le groupe aux vestiaires (étage 1) |
 * | Arena of Fate | la descente des catacombes (`e25`) | le groupe aux catacombes (étage 2) |
 * | Arena of Fate | la remontée des catacombes (`e33`) | le groupe à la prison (étage 1) |
 * | Arena of Fate | l'escalier du parvis (`e23`) | Arenarea s'ouvre |
 * | Arenarea | Herofate Avenue (`e2`) | Martpart s'ouvre : la démo est faite |
 *
 * Un meneur arrêté avant son but reçoit l'ordre de nouveau, `MaxOrders` fois au plus. Chaque étape
 * finie est capturée (`demo-NN.png`), et `parcours.json` relève les étapes, leur instant et la
 * durée de chacune, et l'**ouverture** de chaque carte : de la dernière trame de la carte quittée
 * à la première de la suivante.
 *
 * `-JadgDemoEtape=<rang>` reprend la démo à une étape, le jeu lancé sur la carte de cette étape.
 *
 * Il quitte le jeu : code 0 de retour à Martpart, 1 dès qu'une étape reste sans suite
 * `LegSeconds`, qu'une carte s'ouvre hors de l'ordre de la démo ou qu'une rencontre s'engage.
 */
UCLASS()
class AJadgDemoWalkthrough : public AActor
{
	GENERATED_BODY()

public:
	AJadgDemoWalkthrough();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY()
	TObjectPtr<UJadgExploration> Exploration;

	FString OutputDir;
	FString PendingFile;
	int32 Frames = 0;
	int32 Orders = 0;
	bool bOrdered = false;
	bool bShooting = false;
	bool bDone = false;

	void Order(AJadgParty& Party);
	bool LegDone(const AJadgParty& Party) const;
	void Shoot(const FString& What);
	void Note(const FString& What) const;
	void Finish(int32 ExitCode, const FString& Reason);
};
