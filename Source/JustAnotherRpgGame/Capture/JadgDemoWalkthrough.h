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
 * vers un portail (`AJadgParty::OrderWalk`, le geste du clic au sol) ; l'acteur renaît à chaque
 * carte et reprend à l'étape où il en est. Les positions, étages et arrivées sont lus dans la
 * carte courante de Core, sans anciennes coordonnées fixées dans le parcours :
 *
 * | Carte | Portail | Fin de l'étape |
 * |---|---|---|
 * | Martpart | — (la place des étals, auprès de la mère) | le meneur y est |
 * | Martpart | Stravian Avenue (`e4`) | Arenarea s'ouvre |
 * | Arenarea | l'escalier de l'arène (`e4`) | l'Arena of Fate s'ouvre, au vestibule des vestiaires (étage 1) |
 * | Arena of Fate | — (4,5 m dans le vestibule depuis `e21`, à l'opposé de `e23`) | le meneur y marche au niveau des vestiaires |
 * | Arena of Fate | l'escalier du parvis (`e23`) | Arenarea s'ouvre |
 * | Arenarea | Herofate Avenue (`e2`) | Martpart s'ouvre : la démo est faite |
 *
 * Les quatre transferts passent par les vrais portails extérieurs. Aucun portail intérieur
 * supprimé ni placement artificiel du héros : le parcours physique de l'arène vérifie ses vrais
 * escaliers et ses sept niveaux séparément. Une arrivée doit correspondre à la carte, au point
 * d'arrivée nommé, à son étage et à l'altitude de son sol local, dans le monde effectivement
 * chargé. Le rapport donne les pieds et le sol attendu en centimètres monde, et leur écart Z.
 * Un meneur arrêté avant son but reçoit l'ordre de nouveau, `MaxOrders` fois au plus. Chaque étape
 * finie est capturée (`demo-NN.png`), et `parcours.json` relève les étapes, leur instant et la
 * durée de chacune, et l'**ouverture** de chaque carte : de la dernière trame de la carte quittée
 * à la première de la suivante.
 *
 * `-JadgDemoEtape=<rang>` reprend la démo à une étape, le jeu lancé sur la carte de cette étape.
 * Une reprise se signale dans le rapport ; seul un départ à l'étape 0 avec quatre transferts
 * confirmés constitue `fullRoundTrip`.
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
	bool bTargetReady = false;
	FVector2D TargetCell = FVector2D::ZeroVector;
	int32 TargetStorey = 0;
	double ShotSince = 0.0;

	bool ResolveTarget(FString& Error);
	bool ValidateArrival(const AJadgParty& Party, FString& Error, FVector& ExpectedGround, double& HeightTolerance) const;
	void Order(AJadgParty& Party);
	bool LegDone(const AJadgParty& Party) const;
	void Shoot(const FString& What);
	void Note(const FString& What) const;
	void Finish(int32 ExitCode, const FString& Reason);
};
