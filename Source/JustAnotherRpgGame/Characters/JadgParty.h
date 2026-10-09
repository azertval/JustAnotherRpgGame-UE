// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Info.h"

#include "JadgParty.generated.h"

class AJadgMapFrame;
class AJadgWalker;
class UJadgExploration;

/**
 * @brief Le groupe sur la carte : le meneur que le joueur envoie, la file qui le suit, et le pas
 *        d'exploration que sa case fait faire à Core (LOT-1016).
 *
 * Créé par le mode de jeu au lancement de la carte, il rassemble les personnages que la scène
 * déclare du groupe (`AJadgWalker::PartyRank`), le meneur en tête.
 *
 * **Le meneur** marche sur le maillage de navigation du moteur, vers le point cliqué. **Les
 * suiveurs** mettent leurs pas dans les siens : la trace est celle de Core (`core::FollowTrail`),
 * chacun vise le point situé à `(rang) × SPACING_CELLS` cases derrière le meneur, et y va par le
 * maillage de navigation. La trace ne passe que par où le meneur est passé : un suiveur ne reste
 * pas derrière un coin de mur.
 *
 * **Le pas d'exploration** : à chaque trame, la case du meneur est donnée à `UJadgExploration`,
 * qui rend ce que Core en tire — un portail franchi (la carte du moteur de la carte cible
 * s'ouvre), un dialogue, une étape de quête. Sur une carte du moteur sans carte de Core, il ne
 * reste que la marche et l'heure.
 *
 * Il tient aussi ce que la carte de Core fait paraître : les PNJ présents ou non sous les
 * drapeaux, les lumières posées comme entité `light`, le contour de ce que le meneur peut
 * solliciter.
 *
 * **La bascule vers le combat** : une rencontre engagée (`UJadgExploration::Encounter`) ouvre la
 * carte d'arène (`ArenaMap`, `Config/DefaultGame.ini`). Dans l'arène, le groupe ne joue pas la
 * carte de Core de l'arène en exploration — la session d'exploration garde la carte quittée,
 * gelée — : il crée le combat (`AJadgCombat`, LOT-1017), qui monte la rencontre sur la carte de
 * Core que nomme le repère. À l'issue, le combat l'écrit et rouvre la carte quittée, le groupe là
 * où il était (`ReturnFromArena`). `-JadgRencontre=<id>` engage une rencontre au lancement de
 * l'arène elle-même : une capture de l'arène en combat.
 */
UCLASS(config = Game)
class AJadgParty : public AInfo
{
	GENERATED_BODY()

public:
	AJadgParty();

	/// La carte du moteur où se joue une rencontre engagée (LOT-1017).
	UPROPERTY(config)
	FString ArenaMap;

	/// Vrai si la carte en cours est la carte d'arène.
	bool InArena() const;

	/// Rouvre la carte que la rencontre a fait quitter ; le groupe y est là où il était.
	void ReturnFromArena();

	/// Le groupe de la carte, ou rien avant que le mode de jeu ne l'ait créé.
	static AJadgParty* Find(const UWorld* World);

	/// Le meneur, ou rien si la carte n'a aucun personnage du groupe.
	AJadgWalker* Leader() const;

	/// Les membres, le meneur en tête.
	const TArray<TObjectPtr<AJadgWalker>>& GetMembers() const { return Members; }

	/// Envoie le meneur vers @p Destination, ramené sur le maillage de navigation.
	void OrderWalk(const FVector& Destination);

	/// Envoie le meneur vers @p Target et le fait interagir dès qu'il l'a à portée.
	void OrderInteract(const AActor* Target);

	/// Le meneur interagit maintenant avec ce qu'il a à portée.
	void Interact();

	/// Passe la main au suivant : le meneur va en queue de file.
	void RotateLeader();

	/// Vrai si @p Actor montre une entité de la carte de Core que l'on peut désigner.
	bool IsEntity(const AActor* Actor) const;

	/// Ce qui montre une entité de la carte de Core (`e1`), ou rien.
	AActor* EntityActor(const FString& EntityId) const;

	/// Le point du monde de la position continue @p Cell, en cases, à la hauteur du meneur.
	FVector PointOf(const FVector2D& Cell) const;

	/// La position continue, en cases, d'un point du monde : la grille de la carte de Core, ou à
	/// défaut des cases de 1,5 m depuis l'origine du monde.
	FVector2D CellOf(const FVector& World) const;

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	UPROPERTY()
	TArray<TObjectPtr<AJadgWalker>> Members;

	UPROPERTY()
	TObjectPtr<AJadgMapFrame> Frame;

	UPROPERTY()
	TObjectPtr<UJadgExploration> Exploration;

	/// Ce qui montre une entité de la carte de Core : l'identifiant et l'acteur, rang pour rang.
	UPROPERTY()
	TArray<TObjectPtr<AActor>> EntityActors;

	TArray<FString> EntityIds;
	TMap<FString, FIntPoint> EntityCells;

	struct FState;
	/// La trace de Core : hors de l'en-tête, qui ne doit pas montrer Core après le moteur.
	TSharedPtr<FState> State;

	bool bInteractAsked = false;
	bool bPending = false;
	FIntPoint PendingCell = FIntPoint::ZeroValue;
	FString OutlinedId;
	bool bTravelling = false;
	/// Faux tant que la file n'a pas pu se ranger : le maillage de navigation d'une carte se
	/// construit après son lancement.
	bool bLinedUp = false;

	FVector WorldOf(const FVector2D& Cell, double Height) const;
	bool OnNavigation(const FVector& Point, FVector& OutGround) const;
	void GatherEntities();
	void PlaceParty(const FVector2D& LeaderCell);
	void ResetTrail();
	void Travel(const FString& MapId);
	void Open(const FString& Package);
	void FollowLeader();
	void RefreshEntities();
	void SetOutlined(const FString& EntityId, bool bOutlined);
	void FollowWithCamera() const;
	/// Monte le combat de la rencontre engagée ; faux tant que le maillage de navigation de l'arène
	/// n'est pas prêt (il se construit après le lancement de la carte), et le groupe réessaie.
	bool BeginCombat();
	bool bCombatPending = false;
	/// Vrai tant que des membres posés sur un même point ne se bloquent pas encore.
	bool bStackedNow = false;
	void SetStacked(bool bStacked);
	int32 CombatTries = 0;
};
