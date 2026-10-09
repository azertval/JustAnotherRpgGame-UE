// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"

#include "JadgWalker.generated.h"

class UAnimSequence;
class UStaticMeshComponent;

/**
 * @brief Un personnage lié qui marche sur le maillage de navigation et se tient au repos
 *        (LOT-1012).
 *
 * Deux clips, joués directement par le composant de maillage, sans graphe d'animation ni
 * Blueprint : `IdleClip` à l'arrêt, `WalkClip` en marche. Le clip de marche de la chaîne des
 * personnages couvre une distance fixe par cycle (`WalkSpeed`, 3 m/s : une case de 1,5 m en
 * 0,5 s, `Planning/standards/personnages-3d.md`) ; il est joué au prorata de la vitesse réelle,
 * pour que le pied posé ne glisse pas pendant l'accélération.
 *
 * `Patrol` fait tourner le personnage entre des points, en boucle : c'est ce qui montre le lion
 * marcher sans joueur. Un membre du groupe (`PartyRank`) attend l'ordre du joueur ou suit le
 * meneur (`AJadgParty`, LOT-1016). Un personnage qui est une entité de la carte de Core
 * (`EntityId`, un PNJ) se pose sur la case de son entité et ne paraît que si elle est présente.
 *
 * **Les personnages se bloquent** (LOT-1017, dette du LOT-1016) : la capsule de chacun bloque
 * celle des autres, membres du groupe et PNJ ; l'évitement réciproque du mouvement (RVO du
 * `CharacterMovementComponent`) les fait s'écarter l'un de l'autre au lieu de se pousser, et un
 * meneur qui fait demi-tour contourne ses suiveurs. **En combat** (`SetInCombat`), c'est Core qui
 * tient l'espace — les volumes, l'allonge, les places où l'on finit — : la capsule ne bloque plus
 * les autres personnages et l'évitement se coupe, pour que la figurine suive exactement le chemin
 * que la règle a payé.
 */
UCLASS()
class AJadgWalker : public ACharacter
{
	GENERATED_BODY()

public:
	AJadgWalker();

	UPROPERTY(EditAnywhere, Category = "Jadg")
	TObjectPtr<UAnimSequence> IdleClip;

	UPROPERTY(EditAnywhere, Category = "Jadg")
	TObjectPtr<UAnimSequence> WalkClip;

	/// La vitesse que le clip de marche représente, en centimètres par seconde.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	float WalkSpeed = 300.0f;

	/// Le rang du personnage dans le groupe au lancement (0 : le meneur) ; négatif : il n'en est pas.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	int32 PartyRank = -1;

	/// L'entité de la carte de Core que ce personnage montre (`e5`) ; vide : aucune.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	FString EntityId;

	/// Les points d'une ronde, en repère du monde ; vide : le personnage attend.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	TArray<FVector> Patrol;

	/// La fiche d'apparence (`Rpg/appearances/<id>.json`, LOT-1015) qui pose le personnage au
	/// lancement : corps par le créateur, clips, taille, armes. Vide : le maillage et les deux
	/// clips ci-dessus sont ceux que la scène a posés.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	FString Appearance;

	/// Les clips du créateur, par nom (repos, marche, attaque, incantation, coup reçu, mort).
	UPROPERTY(VisibleAnywhere, Category = "Jadg")
	TMap<FName, TObjectPtr<UAnimSequence>> Clips;

	/// L'instant d'impact d'un clip, en secondes (`attack`, `cast`), lu dans la fiche.
	UPROPERTY(VisibleAnywhere, Category = "Jadg")
	TMap<FName, float> ClipKeys;

	/// Les armes tenues, une par main, accrochées à leur socket.
	UPROPERTY(VisibleAnywhere, Category = "Jadg")
	TArray<TObjectPtr<UStaticMeshComponent>> Weapons;

	/// Vrai si le corps vient de l'objet personnalisable Mutable (sinon, du maillage posé tel quel).
	bool bFromCreator = false;

	/// Joue une fois un clip du créateur (`attack`, `hit`…), puis revient au repos à sa fin. Faux
	/// s'il n'existe pas.
	bool PlayOnce(FName Clip);

	/// Joue une fois un clip et reste sur sa dernière pose (`death`) jusqu'à `ReturnToRest`.
	bool PlayAndHold(FName Clip);

	/// Revient au repos, quelle que soit la pose tenue.
	void ReturnToRest();

	/// Vrai tant qu'un clip joué une fois n'est pas fini, ou qu'une pose est tenue.
	bool IsPlayingOnce() const { return bHolding || OnceUntil > 0.0; }

	/// Vrai si une pose est tenue (`PlayAndHold`).
	bool IsHolding() const { return bHolding; }

	/// La durée d'un clip du créateur, en secondes ; 0 s'il n'existe pas.
	float ClipSeconds(FName Clip) const;

	/// L'instant d'impact d'un clip (`ClipKeys`), ou la moitié de sa durée s'il n'en a pas.
	float ImpactSeconds(FName Clip) const;

	/// Passe le personnage en combat, ou l'en sort (voir la description de la classe).
	void SetInCombat(bool bInCombat);

	/// La capsule bloque-t-elle les autres personnages ? Faux le temps qu'une file posée sur un
	/// seul point (le maillage de navigation pas encore prêt) se range : sinon ils se repoussent.
	void SetBlocksCharacters(bool bBlocks);

	/// Envoie le personnage vers un point du maillage de navigation ; il s'arrête à
	/// @p AcceptanceRadius centimètres du but.
	void WalkTo(const FVector& Destination, float AcceptanceRadius = 5.0f);

	/// Arrête la marche en cours.
	void StopWalking();

	/// Vrai tant qu'un ordre de marche est en cours.
	bool IsWalking() const;

	/// Pose le personnage debout sur @p Ground, un point du sol, tourné vers @p Yaw.
	void StandOn(const FVector& Ground, float Yaw);

	/// Le point du sol sous le personnage.
	FVector Feet() const;

	/// Dessine ou efface le contour qui désigne le personnage au joueur (profondeur personnalisée).
	void SetOutlined(bool bOutlined);

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	bool bWalking = false;
	int32 PatrolIndex = 0;
	/// L'instant (temps du monde) où le clip joué une fois s'achève ; 0 : aucun.
	double OnceUntil = 0.0;
	bool bHolding = false;

	void Play(UAnimSequence* Clip);
};
