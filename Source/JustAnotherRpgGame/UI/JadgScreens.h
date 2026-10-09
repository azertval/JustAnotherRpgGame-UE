// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Types/SlateEnums.h"
#include "UI/JadgScreen.h"

#include "JadgScreens.generated.h"

class UCanvasPanel;
class UImage;
class UProgressBar;
class UTextBlock;
class UVerticalBox;
class UHorizontalBox;
class UScrollBox;
class UEditableTextBox;

/**
 * @file UI/JadgScreens.h
 * @brief Les écrans du jeu (LOT-1020), chacun une classe qui construit son arbre d'UMG en C++.
 *
 * Leur dessin est celui des écrans de l'ancien jeu, à la charte v2 (`interface-ihm.md`, §7 et §9) :
 * les fichiers d'écran sont `JadgGameScreens.cpp` (le jeu : HUD, dialogue, combat),
 * `JadgMenuScreens.cpp` (titre, menu du mercenaire, options, fins, débogage),
 * `JadgSheetScreens.cpp` (groupe, personnage, équipement, journal) et `JadgMapScreen.cpp` (carte).
 */

/// La classe de l'écran @p Kind.
UClass* JadgScreenClass(EJadgScreen Kind);

// --- Le jeu --------------------------------------------------------------------------------------

/// Le HUD d'exploration : le lieu, la carte, l'heure, le groupe, les écrans, l'annonce, l'invite.
UCLASS()
class UJadgHudScreen : public UJadgScreen
{
	GENERATED_BODY()

public:
	virtual bool IsModal() const override { return false; }

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
	virtual void Refresh() override;

private:
	UPROPERTY()
	TObjectPtr<UTextBlock> Place;
	UPROPERTY()
	TObjectPtr<UTextBlock> Clock;
	UPROPERTY()
	TObjectPtr<UImage> Dial;
	UPROPERTY()
	TObjectPtr<UTextBlock> Notice;
	UPROPERTY()
	TObjectPtr<UTextBlock> Prompt;
	UPROPERTY()
	TObjectPtr<UTextBlock> Encounter;
	UPROPERTY()
	TObjectPtr<UHorizontalBox> Members;

	FString Shown;
	FString DialShown;
	void FillMembers(FJadgUi& Ui);
};

/// Le dialogue (D-28) : qui parle, la réplique, le jet, les réponses, qui parle pour le groupe.
UCLASS()
class UJadgDialogueScreen : public UJadgScreen
{
	GENERATED_BODY()

public:
	virtual bool IsModal() const override { return false; }

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
	virtual void Refresh() override;

private:
	UPROPERTY()
	TObjectPtr<UTextBlock> Speaker;
	UPROPERTY()
	TObjectPtr<UImage> Portrait;
	UPROPERTY()
	TObjectPtr<UTextBlock> Line;
	UPROPERTY()
	TObjectPtr<UTextBlock> Check;
	UPROPERTY()
	TObjectPtr<UVerticalBox> Answers;
	UPROPERTY()
	TObjectPtr<UHorizontalBox> Voices;

	FString Shown;
	void FillAnswers();
};

/// L'interface du combat de groupe (LOT-140, LOT-1017) : initiative, tour, cible, capacités, fin du tour.
UCLASS()
class UJadgCombatScreen : public UJadgScreen
{
	GENERATED_BODY()

public:
	virtual bool IsModal() const override { return false; }

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
	virtual void Refresh() override;

private:
	UPROPERTY()
	TObjectPtr<UTextBlock> RoundText;
	UPROPERTY()
	TObjectPtr<UHorizontalBox> Order;
	UPROPERTY()
	TObjectPtr<UTextBlock> ActiveName;
	UPROPERTY()
	TObjectPtr<UProgressBar> ActiveLife;
	UPROPERTY()
	TObjectPtr<UTextBlock> Budget;
	UPROPERTY()
	TObjectPtr<UHorizontalBox> Slots;
	UPROPERTY()
	TObjectPtr<UTextBlock> TargetName;
	UPROPERTY()
	TObjectPtr<UTextBlock> TargetLine;
	UPROPERTY()
	TObjectPtr<UTextBlock> Status;
	UPROPERTY()
	TObjectPtr<UTextBlock> Outcome;
	UPROPERTY()
	TObjectPtr<UVerticalBox> Log;
	UPROPERTY()
	TObjectPtr<UWidget> LogPanel;

	FString Shown;
	FString SlotsShown;
	FString LogShown;
	void FillOrder();
	void FillSlots();
};

// --- Les menus ------------------------------------------------------------------------------------

/// Le menu du titre : continuer, nouvelle partie, options, quitter.
UCLASS()
class UJadgTitleScreen : public UJadgScreen
{
	GENERATED_BODY()

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
};

/// Le menu du mercenaire, ouvert du jeu (Échap, « Menu » du HUD) : reprendre, options, titre.
UCLASS()
class UJadgPauseScreen : public UJadgScreen
{
	GENERATED_BODY()

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
};

/// Les options : langue, affichage, rendu, son ; par défaut, annuler, appliquer (`EX-IHM-083`).
UCLASS()
class UJadgOptionsScreen : public UJadgScreen
{
	GENERATED_BODY()

public:
	/// Les réglages en cours d'édition, pas encore appliqués.
	int32 Width = 1920;
	int32 Height = 1080;
	bool bFullscreen = true;
	int32 RenderScale = 100;
	int32 Shadows = 3;
	int32 Volume = 100;
	FString Language;

	/// Applique et enregistre les réglages ; reconstruit les écrans si la langue change.
	void Apply();

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;

private:
	void Load(bool bFactory);
	void ShowValues();

	UPROPERTY()
	TArray<TObjectPtr<UWidget>> Tabs;
	UPROPERTY()
	TMap<FName, TObjectPtr<UTextBlock>> Values;
};

/// Une fin : la démonstration finie (une voie), ou la mort du groupe.
UCLASS()
class UJadgEndScreen : public UJadgScreen
{
	GENERATED_BODY()

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
	virtual bool HandleKey(const FKey& Key) override;
};

/// Le menu de débogage (F9) : la carte, la case, l'heure, les drapeaux ; régler l'heure.
UCLASS()
class UJadgDebugScreen : public UJadgScreen
{
	GENERATED_BODY()

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
	virtual void Refresh() override;

private:
	UPROPERTY()
	TObjectPtr<UTextBlock> Facts;
};

// --- La fiche et le groupe ------------------------------------------------------------------------

/// Le groupe à quatre : l'ordre de marche, le meneur ; en nouvelle partie, le choix du meneur (D-37).
UCLASS()
class UJadgPartyScreen : public UJadgScreen
{
	GENERATED_BODY()

public:
	/// Le membre choisi dans la liste.
	FString Chosen;

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;

private:
	void Reopen();
};

/// La fiche du personnage : caractéristiques, identité, points de vie, expérience, compétences.
UCLASS()
class UJadgCharacterScreen : public UJadgScreen
{
	GENERATED_BODY()

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
};

/// L'inventaire et l'équipement : ce que le membre porte, son sac, sa bourse, sa charge.
UCLASS()
class UJadgEquipmentScreen : public UJadgScreen
{
	GENERATED_BODY()

public:
	/// L'objet choisi : son rang (équipé d'abord, puis le sac) ; -1 aucun.
	int32 Selected = -1;

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
};

/// Le journal des quêtes : les quêtes commencées et leur état, la quête choisie et ses étapes.
UCLASS()
class UJadgJournalScreen : public UJadgScreen
{
	GENERATED_BODY()

public:
	int32 Selected = 0;

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
	virtual void Refresh() override;

private:
	int32 Seen = -1;
};

/// La carte : l'atlas illustré, ses lieux cliquables, leurs voisins, la recherche et les favoris.
UCLASS()
class UJadgMapScreen : public UJadgScreen
{
	GENERATED_BODY()

public:
	/// La carte montrée : son identifiant dans `world-maps.json` ; vide, celle du monde.
	FString MapId;
	/// Le lieu choisi ; vide aucun.
	FString PlaceId;
	/// Le texte de recherche.
	FString Query;

	/// Les favoris du joueur, gardés le temps de la partie.
	static TArray<FString>& Favourites();

protected:
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) override;
	virtual bool HandleKey(const FKey& Key) override;

private:
	void Reopen();

	UFUNCTION()
	void HandleSearch(const FText& Text, ETextCommit::Type Method);
};
