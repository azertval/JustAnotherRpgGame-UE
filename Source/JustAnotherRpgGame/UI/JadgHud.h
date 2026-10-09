// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "UI/JadgScreen.h"

#include "JadgHud.generated.h"

/**
 * @brief Le gestionnaire des écrans (LOT-1020) : il remplace le HUD de canevas du LOT-1016.
 *
 * Trois couches, de bas en haut :
 *
 * | Couche | Écran | Quand |
 * |---|---|---|
 * | le jeu | le HUD d'exploration, ou l'interface du combat | toujours ; le combat dès qu'il est monté |
 * | la conversation | le dialogue | tant qu'une conversation est ouverte (`UJadgExploration::InDialogue`) |
 * | les pages | une **pile** : menu, options, fiche, groupe, carte, fins… | ouvertes par une commande, un bouton ou le jeu |
 *
 * Une page ouverte met le jeu en pause et prend le clavier (`FInputModeUIOnly`, le premier bouton
 * focalisé) ; la dernière refermée le rend à la scène (`FInputModeGameAndUI`, comme au LOT-1016).
 * Le jeu ouvre lui-même ce qu'il demande : le dialogue, le combat, la fin qu'un dialogue écrit
 * (`UJadgExploration::TakeEnding`), la mort du groupe (une défaite).
 *
 * Au lancement d'une partie jouée par un joueur, le menu du titre s'ouvre ; jamais quand le jeu est
 * lancé par un parcours, une capture ou le tour des écrans (`-JadgParcours`, `-JadgCapture`,
 * `-JadgEcrans`…), ni quand la ligne de commande porte `-JadgSansTitre`.
 */
UCLASS()
class AJadgHud : public AHUD
{
	GENERATED_BODY()

public:
	AJadgHud();

	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;
	virtual void Tick(float DeltaSeconds) override;

	/// Le gestionnaire du joueur de @p World, ou rien.
	static AJadgHud* Of(const UWorld* World);

	/// Ouvre la page @p Kind sur la pile (une seule fois : déjà ouverte, elle passe en haut).
	UJadgScreen* Open(EJadgScreen Kind, const FString& Argument = FString());

	/// Ouvre la page @p Kind, ou la ferme si elle est en haut de la pile.
	void Toggle(EJadgScreen Kind);

	/// Ferme @p Screen (une page de la pile) et tout ce qui est au-dessus.
	void Close(UJadgScreen* Screen);

	/// Ferme toutes les pages.
	void CloseAll();

	/// La page en haut de la pile, ou rien.
	UJadgScreen* Top() const;

	/// L'écran @p Kind s'il est à l'écran : une page, le dialogue, le HUD ou le combat.
	UJadgScreen* Find(EJadgScreen Kind) const;

	/// Le nombre de pages ouvertes.
	int32 Depth() const { return Stack.Num(); }

	/// Reconstruit chaque écran : après un changement de langue.
	void RebuildScreens();

	/// Lance une partie neuve avec le meneur @p LeaderId (D-37) : la partie se relit, la carte se rouvre.
	void StartNewGame(const FString& LeaderId);

private:
	UPROPERTY()
	TArray<TObjectPtr<UJadgScreen>> Stack;

	UPROPERTY()
	TObjectPtr<UJadgScreen> Ground;

	UPROPERTY()
	TObjectPtr<UJadgScreen> Talk;

	bool bDeathShown = false;

	UJadgScreen* Create(EJadgScreen Kind, const FString& Argument, int32 Layer);
	void Remove(UJadgScreen* Screen);
	void ApplyInputMode();
};
