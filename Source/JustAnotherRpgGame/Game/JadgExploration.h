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
	/// L'étage de l'entité (format v5, D-51) ; 0, le rez.
	int32 Storey = 0;
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
	/// L'étage de la lumière (format v5, D-51) ; 0, le rez.
	int32 Storey = 0;
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

/// L'issue d'une rencontre, telle que le combat la rend (`core::CombatOutcome`).
enum class EJadgOutcome : uint8
{
	Victory,
	Flight,
	Defeat,
};

/// Un membre du groupe, pour le HUD.
struct FJadgMember
{
	FString Id;
	FString Name;
	int32 HitPoints = 0;
	int32 MaxHitPoints = 0;
};

/// Une caractéristique de la fiche, pour l'écran Personnage (LOT-1020).
struct FJadgAbilityView
{
	/// L'identifiant de la caractéristique : `strength`, `dexterity`…
	FString Id;
	int32 Score = 0;
	int32 Modifier = 0;
};

/// Une compétence de la fiche : son bonus au jet, et si la fiche la maîtrise.
struct FJadgSkillView
{
	FString Id;
	int32 Bonus = 0;
	bool bProficient = false;
};

/// La fiche d'un membre du groupe, telle que les écrans la montrent (LOT-1020).
struct FJadgSheetView
{
	FString Id;
	FString Name;
	FString ClassId;
	FString SpeciesId;
	FString BackgroundId;
	int32 Level = 1;
	int32 Experience = 0;
	int32 HitPoints = 0;
	int32 MaxHitPoints = 0;
	int32 ArmorClass = 0;
	int32 Initiative = 0;
	int32 Proficiency = 0;
	int32 PassivePerception = 10;
	float SpeedMetres = 0.0f;
	TArray<FJadgAbilityView> Abilities;
	TArray<FJadgSkillView> Skills;
};

/// Un objet porté : sur soi (son emplacement) ou dans le sac.
struct FJadgItemView
{
	/// L'emplacement (`main-hand`…) ; vide dans le sac.
	FString Slot;
	FString Id;
	/// Le nom du catalogue ; l'identifiant si aucun catalogue ne le porte.
	FString Name;
	int32 Quantity = 1;
	int32 WeightGrams = 0;
};

/// Ce qu'un membre porte, pour l'écran Équipement (LOT-1020).
struct FJadgInventoryView
{
	TArray<FJadgItemView> Equipped;
	TArray<FJadgItemView> Backpack;
	int32 PurseCopper = 0;
	int32 CarriedGrams = 0;
	int32 CapacityGrams = 0;
};

/// Une quête commencée, pour le journal (LOT-1020).
struct FJadgQuestView
{
	FString Id;
	FString Title;
	/// `active`, `succeeded` ou `failed`.
	FString Status;
	/// Les textes des étapes atteintes, dans l'ordre du récit : la dernière est l'objectif.
	TArray<FString> Steps;
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

	/// L'étage où se tient le meneur, que Core connaît (D-51) : 0, le rez.
	int32 HeroStorey() const;

	/**
	 * @brief L'étage où le moteur a mené le meneur, pour les pas suivants (`Step`) : ce qui n'est
	 *        pas à cet étage ne se sollicite, ne se franchit ni ne se déclenche (D-51, LOT-1018).
	 */
	void SetStorey(int32 Storey) { CarriedStorey = Storey; }

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
	/// Le membre du groupe qui parle pour lui : le meneur à l'ouverture (D-28, D-37) ; vide hors dialogue.
	FString DialogueSpeaker() const;
	/// Fait parler @p MemberId pour le groupe : ses langues et ses modificateurs jouent (D-28).
	bool SetDialogueSpeaker(const FString& MemberId);
	/// Passe la parole au membre suivant (@p Direction 1) ou précédent (-1), dans l'ordre de marche.
	void NextDialogueSpeaker(int32 Direction);
	/// Donne la réponse de rang @p Index ; referme la conversation si elle se termine.
	void Choose(int32 Index);
	/// Donne la réponse d'identifiant @p ChoiceId (les tests) ; faux si elle n'est pas proposée.
	bool ChooseById(const FString& ChoiceId);
	/// Ouvre le dialogue @p DialogueId sans aller trouver son PNJ : une capture, un test (LOT-1020).
	void TalkTo(const FString& DialogueId) { OpenDialogue(DialogueId); }
	/// La graine du prochain jet de dialogue ; 0 : un compteur de la partie.
	void SetSeed(uint64 Seed);
	/// Ce que le dernier dialogue a demandé au jeu : `encounter:<id>`, `ending:<voie>`.
	const TArray<FString>& Requests() const { return Asked; }
	/// La fin de partie qu'un dialogue vient de demander (`ending:<voie>`), une fois : l'écran de
	/// fin la prend (LOT-1020) ; vide sinon.
	FString TakeEnding()
	{
		FString Taken = MoveTemp(Ending);
		Ending.Reset();
		return Taken;
	}

	// --- La rencontre -------------------------------------------------------------------------

	/**
	 * @brief La rencontre qu'un dialogue ou une interaction vient d'engager ; vide s'il n'y en a pas.
	 *
	 * C'est la **bascule vers le combat** : tant qu'elle tient, la carte est gelée et l'heure ne
	 * passe pas. Le combat se joue dans l'arène (`AJadgCombat`, LOT-1017), puis `ResolveEncounter`
	 * écrit son issue.
	 */
	FString Encounter() const { return EncounterId; }

	/// Engage la rencontre @p Id sans dialogue : une capture de l'arène en combat, un test.
	void EngageEncounter(const FString& Id) { Engage(Id); }

	/// Quitte la rencontre engagée, sans issue : la carte se dégèle (les tests de l'exploration).
	void LeaveEncounter();

	/**
	 * @brief Écrit l'issue de la rencontre engagée (`core::endEncounter`) : une victoire acquiert
	 *        `encounter/<id>/won`, que les dialogues et les quêtes lisent ; la carte se dégèle.
	 *
	 * Les points de vie et les lancers que le combat a laissés sont écrits sur les fiches par le
	 * combat lui-même, avant (`AJadgCombat`).
	 */
	void ResolveEncounter(EJadgOutcome Outcome);

	// --- Le groupe ----------------------------------------------------------------------------

	/// Les membres, le meneur en tête.
	TArray<FJadgMember> Members() const;
	/// Passe la main au suivant : le meneur va en queue (`core::Party::rotateLeader`).
	void RotateLeader();
	/// Fait de @p MemberId le meneur ; les autres gardent leur ordre (`core::Party::setLeader`, D-37).
	bool SetLeader(const FString& MemberId);
	/// Avance (@p Delta -1) ou recule (+1) @p MemberId dans l'ordre de marche.
	bool MoveMember(const FString& MemberId, int32 Delta);
	/// La fiche du membre @p MemberId ; faux s'il n'est pas du groupe.
	bool Sheet(const FString& MemberId, FJadgSheetView& Out) const;
	/// Ce que porte le membre @p MemberId ; faux s'il n'est pas du groupe.
	bool Inventory(const FString& MemberId, FJadgInventoryView& Out) const;

	// --- Le journal ---------------------------------------------------------------------------

	/// Les quêtes commencées, lues dans les drapeaux (`core::questProgress`).
	TArray<FJadgQuestView> Journal() const;

	// --- La partie ----------------------------------------------------------------------------

	/**
	 * @brief Une partie neuve : drapeaux, heure, groupe et fiches relus comme au lancement
	 *        (« Nouvelle partie », LOT-1020). La carte du moteur, elle, se rouvre par l'appelant.
	 */
	void Restart();

	/// Le nom de la carte courante, pour le HUD : `map.<identifiant>.name`, ou l'identifiant.
	FString MapName() const;

	// --- Les textes ---------------------------------------------------------------------------

	/// Le texte de la clé de traduction @p Key ; la clé elle-même s'il manque.
	FString Text(const FString& Key) const;

	/// Ce que le HUD annonce : un portail clos, une étape de quête. Vide passé son délai.
	FString Notice() const;

	/// L'état de Core (`Game/JadgExplorationState.h`, qui l'inclut avant le moteur) : hors de cet
	/// en-tête, qui ne doit pas montrer Core après le moteur.
	struct FState;
	FState& CoreState() const { return *State; }

private:
	TSharedPtr<FState> State;

	TArray<FString> Errors;
	TArray<FString> Asked;
	FString Portrait;
	FString EncounterId;
	FString Ending;
	FString NoticeText;
	double NoticeUntil = 0.0;
	/// L'étage où le moteur a mené le meneur ; -1 : il ne l'a pas dit.
	int32 CarriedStorey = -1;

	void Load();
	void Announce(const FString& Message);
	void OpenDialogue(const FString& DialogueId);
	void Engage(const FString& Id);
	void CloseDialogueIfEnded();
};
