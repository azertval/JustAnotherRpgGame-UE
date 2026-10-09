// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Blueprint/UserWidget.h"
#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "UI/JadgWidgets.h"

#include "JadgScreen.generated.h"

class AJadgCombat;
class AJadgHud;
class UCanvasPanel;
class UJadgExploration;

/// Les écrans du jeu (LOT-1020). Le C++ ne connaît d'eux que ce nom (`EX-IHM-090`).
UENUM()
enum class EJadgScreen : uint8
{
	/// Le HUD d'exploration, posé sur le jeu.
	Hud,
	/// Le dialogue, posé sur le jeu tant qu'une conversation est ouverte.
	Dialogue,
	/// L'interface du combat, posée sur l'arène tant qu'un combat est monté.
	Combat,
	/// Le menu du titre : continuer, nouvelle partie, options, quitter.
	Title,
	/// Le menu du mercenaire, ouvert du jeu : reprendre, options, quitter vers le titre.
	Pause,
	Options,
	/// Le groupe, en choix du meneur d'une nouvelle partie (D-37).
	NewGame,
	/// Le groupe à quatre : ordre de marche, meneur.
	Party,
	/// La fiche du personnage.
	Character,
	/// L'inventaire et l'équipement.
	Equipment,
	/// Le journal des quêtes.
	Journal,
	/// La carte du monde : l'atlas illustré et ses lieux.
	Map,
	/// La fin de la démonstration.
	Ending,
	/// La mort du groupe.
	Death,
	/// Le menu de débogage (F9).
	Debug,
};

/**
 * @brief Un écran du jeu en UMG, construit par C++ (LOT-1020) : aucun Widget Blueprint.
 *
 * Chaque écran est une classe fille qui construit son arbre dans `Build`, avec le constructeur
 * d'écran (`FJadgUi`) et le style (`UJadgStyle`), et qui relit le jeu dans `Refresh`, à chaque
 * trame : un écran n'a pas d'état à lui, il montre la partie (`EX-IHM-091`).
 *
 * **Le châssis** (`EX-IHM-090`) : tous s'ouvrent et se ferment par le gestionnaire (`AJadgHud`),
 * se parcourent au clavier (les flèches et Tab entre les boutons, Entrée pour valider, Échap pour
 * revenir) et à la souris ; l'élément focalisé porte la marque du kit (`EX-IHM-071`). Une page
 * (`IsModal`) couvre le jeu et prend le clavier ; un écran posé sur le jeu (HUD, dialogue, combat)
 * laisse passer les clics et les touches à la scène.
 */
UCLASS(Abstract)
class UJadgScreen : public UUserWidget
{
	GENERATED_BODY()

public:
	/// Ce qu'est l'écran : le gestionnaire le pose à sa création.
	EJadgScreen Kind = EJadgScreen::Hud;

	/// Un paramètre de l'ouverture : la voie d'une fin, le membre d'une fiche.
	FString Argument;

	/// Vrai : une page qui couvre le jeu et prend le clavier ; faux : posé sur le jeu.
	virtual bool IsModal() const { return true; }

	/// Une touche, du clavier ou injectée : vrai si l'écran l'a prise. Échap ferme une page.
	virtual bool HandleKey(const FKey& Key);

	/// Relit le jeu tout de suite, sans attendre la trame (les tests).
	void Update() { Refresh(); }

	/// Ferme l'écran (une page) par le gestionnaire.
	void Close();

	/// Les boutons de l'écran, dans l'ordre de leur création.
	const TArray<TObjectPtr<UJadgButton>>& Buttons() const { return ButtonList; }

	/// Le bouton de libellé @p Label, dans la langue affichée ; rien s'il n'y en a pas.
	UJadgButton* FindButton(const FText& Label) const;

	/// Le widget à focaliser à l'ouverture : le premier bouton focalisable, ou l'écran.
	UWidget* FirstFocus() const;

	/// Les textes affichés par l'écran, pour les tests (fr et en) et le parcours.
	TArray<FString> VisibleTexts() const;

	AJadgHud* Hud() const;
	UJadgExploration* Exploration() const;
	AJadgCombat* Combat() const;

protected:
	/// Construit l'arbre de l'écran sur le canevas @p Root, aux pixels de conception (1920 × 1080).
	virtual void Build(FJadgUi& Ui, UCanvasPanel* Root) PURE_VIRTUAL(UJadgScreen::Build, );

	/// Relit le jeu, à chaque trame.
	virtual void Refresh() {}

	/**
	 * @brief Le châssis d'une page : le voile sur la scène, la page (parchemin ou panneau sombre)
	 *        en plein écran, la plaque de titre ; rend le canevas du contenu, entre les marges.
	 */
	UCanvasPanel* Page(FJadgUi& Ui, UCanvasPanel* Root, const FText& Title, bool bParchment);

	/// Un bandeau de section (`plate/section-banner`) à son titre.
	UWidget* Section(FJadgUi& Ui, const FText& Title, bool bOnParchment) const;

	/// Une ligne « étiquette — valeur » sur parchemin (la plaque `plate/field-tag` et le filet).
	UWidget* Field(FJadgUi& Ui, const FText& Label, const FText& Value) const;

	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
	virtual FReply NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent) override;

	UPROPERTY()
	TArray<TObjectPtr<UJadgButton>> ButtonList;

	/// Le canevas d'une page faite par `Page` : son pied y reçoit « Retour ».
	UPROPERTY()
	TObjectPtr<UCanvasPanel> PageRoot;
};
