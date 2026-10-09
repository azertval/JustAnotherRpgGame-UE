// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgCombat.generated.h"

class AJadgMapFrame;
class AJadgWalker;
class FJadgCombatSpace;

/// Un combattant tel que le HUD et le parcours le lisent.
struct FJadgFighter
{
	int32 Id = 0;
	FString Name;
	bool bAlly = false;
	bool bStanding = true;
	bool bDead = false;
	int32 HitPoints = 0;
	int32 MaxHitPoints = 0;
	/// La figurine, ou rien (un combat monté sans figurines : les tests).
	AJadgWalker* Walker = nullptr;
};

/// Le tour que l'IA jouerait à la place du joueur : ce que le parcours du combat traduit en clics.
struct FJadgPlan
{
	/// Où aller avant l'action, en repère du monde ; rien : rester.
	TOptional<FVector> MoveTo;
	/// `attack`, `cast`, ou `end` (rien d'autre que le joueur sache faire au clavier).
	FName Action;
	int32 TargetId = 0;
	/// Pour `cast` : le rang du sort parmi ceux du combattant, à partir de 1.
	int32 SpellRank = 0;
	FString Summary;
};

/**
 * @brief Le combat **joué** dans la carte d'arène du moteur (LOT-1017, sous-lot 3).
 *
 * Le groupe (`AJadgParty`) le crée quand il entre dans l'arène avec une rencontre engagée
 * (`UJadgExploration::Encounter`). Tout ce qui est règle est Core :
 *
 * | Temps | Ce qui le fait |
 * |---|---|
 * | le montage | `core::prepareMapEncounter` sur la carte de Core de l'arène (zone de combat, points d'entrée `arenaEntry`, marqueur `encounter`), `core::boutForEncounter`, `core::ArenaSession` sur l'espace du moteur (`FJadgCombatSpace`) |
 * | l'initiative et les tours | `core::ArenaSession::start`, `endTurn` |
 * | le tour du joueur | le clic : sur un combattant, la cible ; au sol, la destination (la place candidate la plus proche, ou la plus avancée vers le point si le budget n'y va pas) ; les touches `Attack`, `Capacity` et `EndTurn`, les chiffres pour choisir la capacité |
 * | le tour de l'IA | `core::playTurn` (`EnemyAi`), sur les candidats de l'EQS |
 * | l'issue | `core::endEncounter` par `UJadgExploration::ResolveEncounter`, les points de vie et les lancers écrits sur les fiches, le retour à la carte quittée |
 *
 * **Ce que le moteur montre** suit Core sans rien décider : chaque pas (`MoveObserver`) devient une
 * marche de la figurine, point après point, par `AAIController::MoveToLocation` ; chaque attaque ou
 * sort (`ActionObserver`, l'attaque d'opportunité par le crochet `AttackDeclared`) un clip joué une
 * fois, le coup reçu ou la chute de la cible à l'**instant d'impact** du clip (`ClipKeys`), puis le
 * repos. Les gestes s'enchaînent dans une file : le combat de Core est déjà résolu quand la figurine
 * commence à marcher, comme dans l'écran de combat de l'ancien moteur.
 *
 * **L'aperçu de travail**, dessiné par des lignes de débogage le temps du tour du joueur : le chemin
 * vers le point sous le pointeur (vert s'il est dans le budget, rouge sinon) et les attaques
 * d'opportunité qu'il provoquerait, la portée restante (un cercle), les cibles atteignables d'ici
 * (un cercle jaune, la cible choisie en blanc). Le HUD (`AJadgHud`) en écrit le texte : le
 * combattant actif, les mètres qui restent, la cible et ses circonstances (hauteur, tenaille), le
 * compte des capacités, le journal. L'interface finale est le LOT-1020.
 */
UCLASS()
class AJadgCombat : public AActor
{
	GENERATED_BODY()

public:
	AJadgCombat();

	/// Le combat de la carte, ou rien.
	static AJadgCombat* Find(const UWorld* World);

	/**
	 * @brief Monte la rencontre @p EncounterId sur la carte de Core que nomme le repère de la carte,
	 *        le groupe de l'exploration à ses points d'entrée, à la graine @p Seed, et lance le combat.
	 * @param bFigures Faux : aucune figurine n'est posée ni animée (les tests du moteur).
	 * @param bHeroesByAi Vrai : l'IA joue aussi les héros, avec le profil de leur classe.
	 * @return Faux, avec la raison, si la rencontre ne se monte pas.
	 */
	bool Mount(const FString& EncounterId, uint64 Seed, bool bFigures, bool bHeroesByAi, FString& OutError);

	/// Avance le combat d'une trame : les gestes en file, puis le tour suivant. `Tick` l'appelle.
	void Advance(float DeltaSeconds);

	/// Fige le combat (une capture : le déploiement reste tel quel).
	void SetPaused(bool bInPaused) { bPaused = bInPaused; }

	// --- Le joueur -----------------------------------------------------------------------------

	/// Le clic du joueur : un combattant devient la cible, un point du sol la destination.
	bool Click(const FHitResult& Hit);
	/// La destination @p World, comme un clic au sol.
	bool MoveTo(const FVector& World);
	/// Choisit la cible @p Id.
	void Select(int32 Id);
	/// Attaque la cible avec la première attaque qui l'atteint (touche `Attack`).
	bool Attack();
	/// Choisit la capacité de rang @p Rank (à partir de 1) parmi les sorts du combattant actif.
	void SelectCapacity(int32 Rank);
	/// Lance la capacité choisie sur la cible (touche `Capacity`).
	bool Cast();
	/// Termine le tour du joueur (touche `EndTurn`).
	bool EndTurn();

	// --- Ce qui se lit -------------------------------------------------------------------------

	bool IsMounted() const;
	/// Vrai si le combat est fini (l'issue est connue), même si la file montre encore ses gestes.
	bool IsOver() const;
	/// Vrai si l'issue est écrite et le retour demandé.
	bool IsResolved() const { return bResolved; }
	/// Vrai tant que des gestes sont en file ou en cours.
	bool IsBusy() const;
	/// Vrai si c'est au joueur de jouer et que rien n'est en cours.
	bool IsPlayerTurn() const;
	int32 ActiveId() const;
	int32 Round() const;
	FString Outcome() const;
	/// L'issue pour l'interface (LOT-1020) : -1 tant qu'elle n'est pas connue, 0 victoire, 1 fuite, 2 défaite.
	int32 OutcomeCode() const;
	TArray<FJadgFighter> Fighters() const;
	float MovementLeft() const;
	int32 TargetId() const { return Target; }
	int32 CapacityRank() const { return Capacity; }
	/// Les capacités du combattant actif : « nom (lancers) », dans l'ordre des rangs.
	TArray<FString> Capacities() const;
	/// Les circonstances d'une attaque du combattant actif sur la cible : avantages et désavantages.
	FString TargetCircumstances() const;
	/// Les @p Count dernières lignes du journal de Core.
	TArray<FString> Journal(int32 Count) const;
	/// La dernière chose refusée au joueur, en clair ; vide sinon.
	FString Refusal() const { return LastRefusal; }
	/// Les mesures des candidats de l'IA (sous-lot 2) : requêtes, points, millisecondes.
	FString CandidateReport() const;

	/// Le tour que l'IA jouerait pour le héros actif, avec le profil de sa classe.
	bool PlanForActive(FJadgPlan& OutPlan) const;

	/// La base du combattant @p Id dans le monde ; rien s'il n'est pas posé.
	TOptional<FVector> PositionOf(int32 Id) const;

	/// La figurine du combattant @p Id, ou rien.
	AJadgWalker* WalkerOf(int32 Id) const;

	virtual void Tick(float DeltaSeconds) override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

	struct FState;

private:
	TSharedPtr<FState> State;
	bool bPaused = false;
	bool bMounted = false;
	bool bFiguresShown = true;
	bool bResolved = false;
	double OverSince = -1.0;
	int32 Target = 0;
	int32 Capacity = 0;
	FString LastRefusal;
	int32 LastActive = 0;

	UPROPERTY()
	TArray<TObjectPtr<AJadgWalker>> Spawned;

	void ProcessCues(float DeltaSeconds);
	void NextTurn();
	void Resolve();
	void DrawPreview() const;
	void Refuse(const FString& Why);
	void SyncFigures();
};
