// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"

#include "JadgExploration.generated.h"

/// Ce qu'un pas d'exploration a produit : la traduction de `core::ExplorationEventKind`.
enum class EJadgEventKind : uint8
{
	MapEntered,
	PortalLocked,
	PortalBroken,
	PortalSealed,
	Dialogue,
	Encounter,
	Interacted,
	QuestAdvanced,
};

/// Un événement d'un pas, et la case où il a eu lieu.
struct FJadgEvent
{
	EJadgEventKind Kind = EJadgEventKind::MapEntered;
	FString Value;
	FIntPoint Cell = FIntPoint::ZeroValue;
};

/// Une entité de la carte courante, telle que Core la lit.
struct FJadgEntity
{
	FString Id;
	FString Type;
	FIntPoint Cell = FIntPoint::ZeroValue;
	bool bPresent = true;
};

/// Une source de lumière de la carte courante (`core::LightSource`), en cases et en mètres.
struct FJadgLamp
{
	FString EntityId;
	FVector2D Cell = FVector2D::ZeroVector;
	FLinearColor Colour = FLinearColor::White;
	float RadiusMetres = 6.0f;
	float HeightMetres = 2.2f;
	float Intensity = 1.0f;
	bool bAlways = false;
};

/// Une réponse proposée au joueur, texte résolu.
struct FJadgChoice
{
	FString Id;
	FString Text;
	/// Si la réponse mène à un jet : la compétence et le seuil ; vide et 0 sinon.
	FString Skill;
	int32 Dc = 0;
};

/// Un membre du groupe, pour le HUD.
struct FJadgMember
{
	FString Id;
	FString Name;
	int32 HitPoints = 0;
	int32 MaxHitPoints = 0;
};

/**
 * @brief L'exploration du jeu dans le moteur : la session de Core, gardée d'une carte à l'autre
 *        (LOT-1016).
 *
 * Core porte les règles — portails et points d'arrivée, drapeaux, quêtes, interactions à portée,
 * dialogues et leurs jets, heure du monde (`core::ExplorationSession`, `core::DialogueRunner`).
 * Le moteur porte le déplacement : le meneur marche sur le maillage de navigation, et ce
 * sous-système **constate** sa case à chaque pas (`Step`, `core::ExplorationIntent::carried`).
 *
 * Il vit avec l'instance du jeu : une carte du moteur qui s'ouvre (`OpenLevel`) retrouve la
 * session, ses drapeaux, son heure et son groupe tels qu'elle les a laissés.
 *
 * Aucun type de Core dans cet en-tête : il se lit après ceux du moteur. Les cases sont des
 * `FVector2D` (colonne, ligne), continues, le centre de la case (4, 2) en (4,5 ; 2,5).
 *
 * | Lu | Où |
 * |---|---|
 * | cartes | le dossier que la carte du moteur nomme (`LevelsRoot`), puis `Source/Elements/Levels` |
 * | dialogues, quêtes | `Source/Elements/World` |
 * | fiches, compétences, difficultés | `Source/Elements/Rpg` |
 * | textes | `Source/Elements/Localization/fr.lang` (le lecteur se décide au LOT-1020) |
 */
UCLASS()
class UJadgExploration : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/// Les erreurs de lecture du contenu, relevées au lancement ; vide si tout se lit.
	const TArray<FString>& LoadErrors() const { return Errors; }

	// --- La carte -----------------------------------------------------------------------------

	/**
	 * @brief La carte du moteur qui s'ouvre joue la carte de Core @p LevelId.
	 *
	 * Si la session y est déjà — on y arrive par un portail —, rien ne change. Sinon elle y entre
	 * par l'entrée de la carte : c'est le lancement, ou une carte ouverte à la main.
	 * @param LevelsRoot Dossier de cartes propre à la scène, relatif au projet ; vide : aucun.
	 * @return Faux si la carte ne se lit pas.
	 */
	bool EnterMap(const FString& LevelId, const FString& LevelsRoot);

	/// L'identifiant de la carte courante de Core ; vide sans carte.
	FString MapId() const;

	/// La position du meneur que Core connaît, en cases.
	FVector2D HeroCell() const;

	/// Pose le meneur sans qu'il soit arrivé nulle part (`core::ExplorationSession::placeHero`).
	void PlaceHero(const FVector2D& Cell);

	/**
	 * @brief Un pas : le meneur est en @p LeaderCell (rien : il n'y a pas de carte de Core), et
	 *        interagit si @p bInteract.
	 *
	 * Un événement `Dialogue` ouvre la conversation ici même : la carte se gèle jusqu'à sa fin.
	 * L'heure du monde avance, sauf en dialogue.
	 */
	TArray<FJadgEvent> Step(const FVector2D* LeaderCell, bool bInteract, float Seconds);

	/// Les entités de la carte courante, présentes ou non.
	TArray<FJadgEntity> Entities() const;

	/// Vrai si l'entité @p EntityId de la carte courante est présente sous les drapeaux.
	bool IsPresent(const FString& EntityId) const;

	/// Les sources de lumière posées comme entité `light` sur la carte courante.
	TArray<FJadgLamp> Lamps() const;

	/// La case de ce que le meneur solliciterait maintenant, et sa clé d'invite.
	bool Target(FIntPoint& OutCell, FString& OutPrompt) const;

	/// Vrai si l'entité @p EntityId ne se sollicite qu'une fois et l'a été : un coffre ouvert.
	bool IsConsumed(const FString& EntityId) const;

	/// La valeur d'un drapeau déclaré à valeurs, ou « 1 » / vide pour un fait posé ou non.
	FString Flag(const FString& Key) const;

	// --- L'heure ------------------------------------------------------------------------------

	/// L'heure à montrer, en minutes depuis minuit : l'heure fixe de la carte si elle en a une.
	float Minutes() const;

	/// Règle l'heure du monde et la **fige** : une capture, une commande de console.
	void SetMinutes(float InMinutes);

	/// Relance ou fige l'heure du monde.
	void SetClockRunning(bool bRunning);

	// --- Le dialogue --------------------------------------------------------------------------

	bool InDialogue() const;
	FString Speaker() const;
	/// Le fichier du portrait de celui qui parle (`<figurine>/portrait.png`, la figurine étant celle
	/// que son entité nomme) ; vide s'il n'en a pas — pas de figurine, ou les kits absents du poste.
	FString SpeakerPortrait() const { return Portrait; }
	FString Line() const;
	/// Le jet joué par le dernier geste, écrit pour le joueur ; vide s'il n'y en a pas eu.
	FString LastCheck() const;
	TArray<FJadgChoice> Choices() const;
	/// Donne la réponse de rang @p Index ; referme la conversation si elle se termine.
	void Choose(int32 Index);
	/// Donne la réponse d'identifiant @p ChoiceId (les tests) ; faux si elle n'est pas proposée.
	bool ChooseById(const FString& ChoiceId);
	/// La graine du prochain jet de dialogue ; 0 : un compteur de la partie.
	void SetSeed(uint64 Seed);
	/// Ce que le dernier dialogue a demandé au jeu : `encounter:<id>`, `ending:<voie>`.
	const TArray<FString>& Requests() const { return Asked; }

	// --- La rencontre -------------------------------------------------------------------------

	/**
	 * @brief La rencontre qu'un dialogue ou une interaction vient d'engager ; vide s'il n'y en a pas.
	 *
	 * C'est la **bascule vers le combat** : tant qu'elle tient, la carte est gelée et l'heure ne
	 * passe pas. Le combat lui-même est le LOT-1017 ; d'ici là le groupe attend dans l'arène vide,
	 * et `LeaveEncounter` le ramène, sans victoire ni défaite.
	 */
	FString Encounter() const { return EncounterId; }

	/// Quitte la rencontre engagée, sans issue : la carte se dégèle.
	void LeaveEncounter();

	// --- Le groupe ----------------------------------------------------------------------------

	/// Les membres, le meneur en tête.
	TArray<FJadgMember> Members() const;
	/// Passe la main au suivant : le meneur va en queue (`core::Party::rotateLeader`).
	void RotateLeader();

	// --- Les textes ---------------------------------------------------------------------------

	/// Le texte de la clé de traduction @p Key ; la clé elle-même s'il manque.
	FString Text(const FString& Key) const;

	/// Ce que le HUD annonce : un portail clos, une étape de quête. Vide passé son délai.
	FString Notice() const;

private:
	struct FState;
	/// L'état de Core : hors de l'en-tête, qui ne doit pas montrer Core après le moteur.
	TSharedPtr<FState> State;

	TArray<FString> Errors;
	TArray<FString> Asked;
	TMap<FString, FString> Texts;
	FString Portrait;
	FString EncounterId;
	FString NoticeText;
	double NoticeUntil = 0.0;

	void Announce(const FString& Message);
	void OpenDialogue(const FString& DialogueId);
	void Engage(const FString& Id);
	void CloseDialogueIfEnded();
};
