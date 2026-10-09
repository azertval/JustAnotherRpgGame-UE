// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Combat/CombatTransition.h"
#include "Core/Gameplay/Quest.h"
#include "Core/Gameplay/WorldFlags.h"
#include "Core/Levels/Level.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Math/DeterministicRandom.h"
#include "Core/Rpg/CharacterOptions.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Check.h"
#include "Core/Rpg/Dialogue.h"
#include "Core/Rpg/Inventory.h"
#include "Core/Rpg/Party.h"
#include "Core/Resources/ScenePlace.h"
#include "Core/Rpg/Skill.h"
#include "Core/World/ExplorationSession.h"
#include "Core/World/LightSource.h"
#include "Core/World/WorldClock.h"
#include "Core/World/WorldTravel.h"

#include <cstdint>
#include <filesystem>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "Game/JadgExplorationState.h"

#include "Bridge/JadgPaths.h"
#include "JustAnotherRpgGame.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"

namespace
{
	/// Le groupe préformé, dans l'ordre de « Nouvelle partie » (D-28, LOT-138).
	const std::vector<std::string> StartingParty{"heros-brawler", "heros-priest", "heros-scoundrel", "heros-mage"};

	/// Ce que le HUD garde à l'écran d'une annonce, en secondes.
	constexpr double NoticeSeconds = 5.0;

	std::string ToUtf8(const FString& Text)
	{
		return std::string(TCHAR_TO_UTF8(*Text));
	}

}

/**
 * Celui qui parle au PNJ : le meneur, par sa fiche (`core::CharacterListener`), et ce que le PNJ
 * demande au jeu — une rencontre, la fin de la démo —, noté pour qui saura l'ouvrir.
 */
class FJadgPartyListener final : public core::DialogueListener
{
public:
	FJadgPartyListener(const core::CharacterSheet& Sheet, core::Inventory& Inventory, const core::ExperienceTable& Experience,
		const core::SkillCatalog& Skills, TArray<FString>& InAsked)
		: Speaker(Sheet, Inventory, Experience, Skills), Asked(InAsked)
	{
	}

	[[nodiscard]] bool speaks(std::string_view LanguageId) const override { return Speaker.speaks(LanguageId); }
	[[nodiscard]] std::vector<core::Modifier> skillModifiers(std::string_view SkillId) const override
	{
		return Speaker.skillModifiers(SkillId);
	}
	void receiveItem(std::string_view ItemId, int Quantity) override { Speaker.receiveItem(ItemId, Quantity); }
	void startEncounter(std::string_view EncounterId) override
	{
		Asked.Add(TEXT("encounter:") + FJadgPaths::ToFString(std::string(EncounterId)));
	}
	void endDemo(std::string_view Ending) override
	{
		Asked.Add(TEXT("ending:") + FJadgPaths::ToFString(std::string(Ending)));
	}

private:
	core::CharacterListener Speaker;
	TArray<FString>& Asked;
};

UJadgExploration::FState::~FState() = default;

void UJadgExploration::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	State = MakeShared<FState>();
	const std::filesystem::path Elements = FJadgPaths::ToPath(FJadgPaths::ElementsDir());
	const std::filesystem::path Rpg = FJadgPaths::RpgRoot();
	const auto Report = [this](const std::vector<std::string>& Found, const TCHAR* What)
	{
		for (const std::string& Error : Found)
		{
			Errors.Add(FString::Printf(TEXT("%s : %s"), What, *FJadgPaths::ToFString(Error)));
		}
	};

	State->LevelDirs = {Elements / "Levels"};
	// Le chargeur relit la liste des dossiers à chaque carte : une scène peut en ajouter un.
	// L'état possède la session, qui possède ce chargeur : il le désigne sans le retenir.
	FState* const Held = State.Get();
	State->Session = std::make_unique<core::ExplorationSession>([Held](std::string_view MapId)
	{
		return core::WorldTravel::directoriesLoader(Held->LevelDirs)(MapId);
	});

	State->Dialogues = core::loadDialogues(Elements / "World" / "dialogues");
	Report(State->Dialogues.errors, TEXT("dialogues"));
	core::QuestCatalog Quests = core::loadQuests(Elements / "World" / "quests");
	Report(Quests.errors, TEXT("quêtes"));
	Report(core::validateFlagUses(Quests, State->Dialogues), TEXT("drapeaux"));
	State->Session->setQuests(MoveTemp(Quests));

	State->Difficulty = core::loadDifficultyScale(Rpg / "rules" / "difficulty.json");
	Report(State->Difficulty.errors, TEXT("difficultés"));
	State->Options = core::loadCharacterOptions(Rpg);
	Report(State->Options.errors, TEXT("options de personnage"));
	State->Rules = core::loadCharacterCreationRules(Rpg / "rules" / "character-creation.json");
	Report(State->Rules.errors, TEXT("règles de création"));
	State->Experience = core::loadExperienceTable(Rpg / "rules" / "experience.json");
	Report(State->Experience.errors, TEXT("table d'expérience"));
	State->Skills = core::loadSkills(Rpg / "skills");
	Report(State->Skills.errors, TEXT("compétences"));

	const core::PartyCandidates Candidates = core::loadPartyCandidates(Rpg / "characters");
	Report(Candidates.errors, TEXT("fiches du groupe"));
	State->Party = core::defaultParty(Candidates.candidates, StartingParty);
	for (const core::PartyCandidate& Candidate : Candidates.candidates)
	{
		if (!State->Party.contains(Candidate.id))
		{
			continue;
		}
		core::LoadedCharacterSheet Loaded =
			core::loadCharacterSheet(Candidate.file, State->Options, State->Rules, State->Experience);
		Report(Loaded.errors, *FJadgPaths::ToFString(Candidate.id));
		State->Sheets.emplace(Candidate.id, MoveTemp(Loaded));
	}

	// Le catalogue des textes : « clé = valeur », une par ligne ; son lecteur se décide au LOT-1020.
	TArray<FString> Lines;
	const FString Catalogue = FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Localization"), TEXT("fr.lang"));
	if (FFileHelper::LoadFileToStringArray(Lines, *Catalogue))
	{
		for (const FString& Line : Lines)
		{
			FString Key;
			FString Value;
			if (!Line.TrimStart().StartsWith(TEXT("#")) && Line.Split(TEXT("="), &Key, &Value))
			{
				Texts.Add(Key.TrimStartAndEnd(), Value.TrimStartAndEnd());
			}
		}
	}
	else
	{
		Errors.Add(FString::Printf(TEXT("textes : %s ne se lit pas"), *Catalogue));
	}

	for (const FString& Error : Errors)
	{
		UE_LOG(LogJadg, Error, TEXT("[Exploration] %s"), *Error);
	}
	UE_LOG(LogJadg, Display, TEXT("[Exploration] %d dialogue(s), %d quête(s), groupe de %d, %d texte(s)"),
		static_cast<int32>(State->Dialogues.dialogues.size()), static_cast<int32>(State->Session->quests().quests.size()),
		static_cast<int32>(State->Party.size()), Texts.Num());
}

void UJadgExploration::Deinitialize()
{
	State.Reset();
	Super::Deinitialize();
}

// --- La carte ---------------------------------------------------------------------------------

bool UJadgExploration::EnterMap(const FString& LevelId, const FString& LevelsRoot)
{
	if (!LevelsRoot.IsEmpty())
	{
		const std::filesystem::path Root =
			FJadgPaths::ToPath(FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), LevelsRoot)));
		bool bKnown = false;
		for (const std::filesystem::path& Dir : State->LevelDirs)
		{
			bKnown = bKnown || Dir == Root;
		}
		if (!bKnown)
		{
			// Devant les cartes du jeu : une scène d'essai joue les siennes.
			State->LevelDirs.insert(State->LevelDirs.begin(), Root);
		}
	}
	const std::string Wanted = ToUtf8(LevelId);
	if (State->Session->map() != nullptr && State->Session->mapId() == Wanted)
	{
		return true;
	}
	if (!State->Session->start(Wanted, ""))
	{
		UE_LOG(LogJadg, Error, TEXT("[Exploration] la carte « %s » ne se lit pas"), *LevelId);
		return false;
	}
	State->Session->setFollowers(0);
	UE_LOG(LogJadg, Display, TEXT("[Exploration] carte « %s », meneur en (%.1f ; %.1f)"), *LevelId,
		State->Session->heroPoint().column, State->Session->heroPoint().row);
	return true;
}

FString UJadgExploration::MapId() const
{
	return State->Session->map() != nullptr ? FJadgPaths::ToFString(State->Session->mapId()) : FString();
}

FVector2D UJadgExploration::HeroCell() const
{
	const core::CellPoint Point = State->Session->heroPoint();
	return FVector2D(Point.column, Point.row);
}

void UJadgExploration::PlaceHero(const FVector2D& Cell)
{
	State->Session->placeHero(core::CellPoint{static_cast<float>(Cell.X), static_cast<float>(Cell.Y)});
}

TArray<FJadgEvent> UJadgExploration::Step(const FVector2D* LeaderCell, bool bInteract, float Seconds)
{
	TArray<FJadgEvent> Out;
	core::ExplorationSession& Session = *State->Session;
	if (Session.map() == nullptr)
	{
		// Une carte du moteur sans carte de Core (la porte) : l'heure du monde passe quand même.
		Session.clock().advance(Seconds);
		return Out;
	}

	core::ExplorationIntent Intent;
	Intent.interact = bInteract;
	if (LeaderCell != nullptr)
	{
		Intent.carried = core::CellPoint{static_cast<float>(LeaderCell->X), static_cast<float>(LeaderCell->Y)};
	}
	for (const core::ExplorationEvent& Event : Session.update(Intent, Seconds))
	{
		FJadgEvent& Added = Out.AddDefaulted_GetRef();
		Added.Value = FJadgPaths::ToFString(Event.value);
		Added.Cell = FIntPoint(Event.cell.column, Event.cell.row);
		switch (Event.kind)
		{
		case core::ExplorationEventKind::MapEntered:
			Added.Kind = EJadgEventKind::MapEntered;
			break;
		case core::ExplorationEventKind::PortalLocked:
			Added.Kind = EJadgEventKind::PortalLocked;
			Announce(TEXT("Ce passage est fermé pour l'instant."));
			break;
		case core::ExplorationEventKind::PortalBroken:
			Added.Kind = EJadgEventKind::PortalBroken;
			UE_LOG(LogJadg, Error, TEXT("[Exploration] portail sans issue vers « %s »"), *Added.Value);
			break;
		case core::ExplorationEventKind::PortalSealed:
			Added.Kind = EJadgEventKind::PortalSealed;
			Announce(TEXT("Ce passage est condamné."));
			break;
		case core::ExplorationEventKind::Dialogue:
			Added.Kind = EJadgEventKind::Dialogue;
			break;
		case core::ExplorationEventKind::Encounter:
			Added.Kind = EJadgEventKind::Encounter;
			Engage(Added.Value);
			break;
		case core::ExplorationEventKind::Interacted:
			Added.Kind = EJadgEventKind::Interacted;
			// Core ne dit que la famille : ce qu'un coffre contient vient avec l'inventaire à l'écran.
			Announce(Added.Value == TEXT("chest") ? TEXT("Le coffre est ouvert.")
				: Added.Value == TEXT("sign") ? TEXT("Vous lisez le panneau.") : TEXT("C'est fait."));
			break;
		case core::ExplorationEventKind::QuestAdvanced:
		{
			Added.Kind = EJadgEventKind::QuestAdvanced;
			// « <quête>/<étape> » : l'entrée du journal que l'étape ouvre.
			FString Quest;
			FString Stage;
			if (Added.Value.Split(TEXT("/"), &Quest, &Stage))
			{
				Announce(Text(FJadgPaths::ToFString(core::questStepKey(ToUtf8(Quest), ToUtf8(Stage)))));
			}
			break;
		}
		}
	}
	// Après la boucle : ouvrir une conversation gèle la carte, et un événement suivant du même pas
	// (une étape de quête) a déjà été rendu.
	for (const FJadgEvent& Event : Out)
	{
		if (Event.Kind == EJadgEventKind::Dialogue && !InDialogue())
		{
			OpenDialogue(Event.Value);
		}
	}
	return Out;
}

TArray<FJadgEntity> UJadgExploration::Entities() const
{
	TArray<FJadgEntity> Out;
	if (const core::Level* Map = State->Session->map())
	{
		for (const core::MapEntity& Entity : Map->entities())
		{
			FJadgEntity& Added = Out.AddDefaulted_GetRef();
			Added.Id = FJadgPaths::ToFString(Entity.id);
			Added.Type = FJadgPaths::ToFString(Entity.type);
			Added.Cell = FIntPoint(Entity.position.column, Entity.position.row);
			Added.bPresent = State->Session->isPresent(Entity);
		}
	}
	return Out;
}

bool UJadgExploration::IsPresent(const FString& EntityId) const
{
	const core::MapEntity* Entity = State->Find(ToUtf8(EntityId));
	return Entity != nullptr && State->Session->isPresent(*Entity);
}

TArray<FJadgLamp> UJadgExploration::Lamps() const
{
	TArray<FJadgLamp> Out;
	if (const core::Level* Map = State->Session->map())
	{
		for (const core::MapEntity& Entity : Map->entities())
		{
			const std::optional<core::LightSource> Source = core::lightSourceOf(Entity);
			if (!Source.has_value())
			{
				continue;
			}
			FJadgLamp& Added = Out.AddDefaulted_GetRef();
			Added.EntityId = FJadgPaths::ToFString(Entity.id);
			Added.Cell = FVector2D(Source->column, Source->row);
			Added.Colour = FLinearColor(Source->emission.color.r, Source->emission.color.g, Source->emission.color.b);
			Added.RadiusMetres = Source->emission.radius;
			Added.HeightMetres = Source->emission.height;
			Added.Intensity = Source->emission.intensity;
			Added.bAlways = Source->emission.always;
		}
	}
	return Out;
}

bool UJadgExploration::Target(FIntPoint& OutCell, FString& OutPrompt) const
{
	const std::optional<core::Interactable> Found = State->Session->interactionTarget();
	if (!Found.has_value())
	{
		return false;
	}
	OutCell = FIntPoint(Found->position.column, Found->position.row);
	OutPrompt = FJadgPaths::ToFString(Found->promptKey);
	return true;
}

bool UJadgExploration::IsConsumed(const FString& EntityId) const
{
	const core::MapEntity* Entity = State->Find(ToUtf8(EntityId));
	if (Entity == nullptr)
	{
		return false;
	}
	for (const core::Interactable& Candidate : State->Session->interactables())
	{
		if (Candidate.position == Entity->position && Candidate.type == Entity->type)
		{
			return Candidate.isConsumable() && State->Session->flags().isSet(Candidate.consumedFlag);
		}
	}
	return false;
}

void UJadgExploration::Engage(const FString& Id)
{
	EncounterId = Id;
	State->Session->freeze(true);
	UE_LOG(LogJadg, Display, TEXT("[Exploration] rencontre « %s » engagée"), *Id);
}

void UJadgExploration::LeaveEncounter()
{
	if (!EncounterId.IsEmpty())
	{
		UE_LOG(LogJadg, Display, TEXT("[Exploration] rencontre « %s » quittée sans issue"), *EncounterId);
		EncounterId.Reset();
		State->Session->freeze(false);
	}
}

void UJadgExploration::ResolveEncounter(EJadgOutcome Outcome)
{
	if (EncounterId.IsEmpty())
	{
		return;
	}
	core::EncounterRun Run;
	Run.encounterId = ToUtf8(EncounterId);
	const core::CombatOutcome Issue = Outcome == EJadgOutcome::Victory ? core::CombatOutcome::Victory
		: Outcome == EJadgOutcome::Flight ? core::CombatOutcome::Flight : core::CombatOutcome::Defeat;
	// Le groupe revient où il était : la session d'exploration a gardé sa case, gelée.
	static_cast<void>(core::endEncounter(Run, Issue, State->Session->flags()));
	UE_LOG(LogJadg, Display, TEXT("[Exploration] rencontre « %s » : %s"), *EncounterId,
		Outcome == EJadgOutcome::Victory ? TEXT("victoire") : Outcome == EJadgOutcome::Flight ? TEXT("fuite") : TEXT("défaite"));
	EncounterId.Reset();
	State->Session->freeze(false);
}

FString UJadgExploration::Flag(const FString& Key) const
{
	const core::WorldFlags& Flags = State->Session->flags();
	const std::string Name = ToUtf8(Key);
	if (const std::optional<std::string> Value = Flags.value(Name); Value.has_value() && !Value->empty())
	{
		return FJadgPaths::ToFString(*Value);
	}
	return Flags.isSet(Name) ? TEXT("1") : FString();
}

// --- L'heure ----------------------------------------------------------------------------------

float UJadgExploration::Minutes() const
{
	return State->Session->shownMinutes();
}

void UJadgExploration::SetMinutes(float InMinutes)
{
	State->Session->clock().setMinutes(InMinutes);
	State->Session->clock().setRunning(false);
}

void UJadgExploration::SetClockRunning(bool bRunning)
{
	State->Session->clock().setRunning(bRunning);
}

// --- Le dialogue ------------------------------------------------------------------------------

void UJadgExploration::OpenDialogue(const FString& DialogueId)
{
	const core::DialogueGraph* Graph = State->Dialogues.find(ToUtf8(DialogueId));
	core::LoadedCharacterSheet* Leader = State->Leader();
	if (Graph == nullptr || Leader == nullptr)
	{
		UE_LOG(LogJadg, Error, TEXT("[Exploration] dialogue « %s » : graphe ou meneur absent"), *DialogueId);
		return;
	}
	Asked.Reset();
	// Le portrait de celui qui parle : la figurine du PNJ présent qui porte ce dialogue.
	Portrait.Reset();
	if (const core::Level* Map = State->Session->map())
	{
		const std::filesystem::path Assets = FJadgPaths::ToPath(FJadgPaths::ElementsDir()) / "Assets";
		for (const core::MapEntity& Entity : Map->entities())
		{
			const auto Spoken = Entity.properties.find(std::string(core::NPC_DIALOGUE_PROPERTY));
			const auto Figure = Entity.properties.find(std::string(core::NPC_FIGURE_PROPERTY));
			const std::string* Name = Spoken != Entity.properties.end() ? std::get_if<std::string>(&Spoken->second) : nullptr;
			const std::string* Slug = Figure != Entity.properties.end() ? std::get_if<std::string>(&Figure->second) : nullptr;
			if (Entity.type != core::NPC_ENTITY_TYPE || Name == nullptr || *Name != Graph->id || Slug == nullptr
				|| !State->Session->isPresent(Entity))
			{
				continue;
			}
			const std::string Folder = core::figureDirectory(core::resolveFigures(Assets, ""), *Slug);
			const std::filesystem::path File = Assets / Folder / "portrait.png";
			std::error_code Ignored;
			if (!Folder.empty() && std::filesystem::is_regular_file(File, Ignored))
			{
				Portrait = FString(File.wstring().c_str()).Replace(TEXT("\\"), TEXT("/"));
			}
			break;
		}
	}
	++State->Conversations;
	const std::uint64_t Seed = State->NextSeed != 0 ? State->NextSeed : State->Conversations;
	State->NextSeed = 0;
	State->Random = std::make_unique<core::DeterministicRandom>(Seed);
	State->Listener =
		std::make_unique<FJadgPartyListener>(Leader->sheet, Leader->inventory, State->Experience, State->Skills, Asked);
	State->Runner = std::make_unique<core::DialogueRunner>(
		*Graph, State->Session->flags(), *State->Listener, State->Difficulty, *State->Random);
	State->Session->freeze(true);
	if (State->Runner->start() == core::DialogueState::Refused)
	{
		Announce(TEXT("Vous n'avez aucune langue en commun."));
	}
	CloseDialogueIfEnded();
}

void UJadgExploration::CloseDialogueIfEnded()
{
	if (State->Runner != nullptr && State->Runner->state() != core::DialogueState::AwaitingChoice)
	{
		State->Runner.reset();
		State->Listener.reset();
		State->Random.reset();
		State->Session->freeze(false);
		Portrait.Reset();
		for (const FString& Request : Asked)
		{
			// L'écran de fin est posé ici, le LOT-1020 l'ouvre ; une rencontre engage la bascule.
			UE_LOG(LogJadg, Display, TEXT("[Exploration] le dialogue demande : %s"), *Request);
			FString Id;
			if (Request.Split(TEXT("encounter:"), nullptr, &Id))
			{
				Engage(Id);
			}
		}
	}
}

bool UJadgExploration::InDialogue() const
{
	return State->Runner != nullptr;
}

FString UJadgExploration::Speaker() const
{
	return InDialogue() ? Text(FJadgPaths::ToFString(core::dialogueSpeakerKey(State->Runner->graph().id))) : FString();
}

FString UJadgExploration::Line() const
{
	return InDialogue() ? Text(FJadgPaths::ToFString(State->Runner->lineKey())) : FString();
}

FString UJadgExploration::LastCheck() const
{
	if (!InDialogue() || !State->Runner->lastCheck().has_value())
	{
		return FString();
	}
	const core::DialogueCheck& Check = *State->Runner->lastCheck();
	const FString Skill = Text(TEXT("rpg.skill.") + FJadgPaths::ToFString(Check.skill));
	if (Check.alreadyFailed)
	{
		return FString::Printf(TEXT("%s : déjà tenté, sans succès"), *Skill);
	}
	const bool bSuccess = Check.result.total >= Check.result.target;
	return FString::Printf(TEXT("%s : %d (dé %d) contre DD %d — %s"), *Skill, Check.result.total, Check.result.keptDie,
		Check.result.target, bSuccess ? TEXT("réussi") : TEXT("raté"));
}

TArray<FJadgChoice> UJadgExploration::Choices() const
{
	TArray<FJadgChoice> Out;
	if (InDialogue())
	{
		for (const core::AvailableChoice& Choice : State->Runner->choices())
		{
			FJadgChoice& Added = Out.AddDefaulted_GetRef();
			Added.Id = FJadgPaths::ToFString(Choice.id);
			Added.Text = Text(FJadgPaths::ToFString(Choice.textKey));
			Added.Dc = Choice.checkDc;
			if (!Choice.checkSkill.empty())
			{
				Added.Skill = Text(TEXT("rpg.skill.") + FJadgPaths::ToFString(Choice.checkSkill));
			}
		}
	}
	return Out;
}

void UJadgExploration::Choose(int32 Index)
{
	const TArray<FJadgChoice> Offered = Choices();
	if (Offered.IsValidIndex(Index))
	{
		ChooseById(Offered[Index].Id);
	}
}

bool UJadgExploration::ChooseById(const FString& ChoiceId)
{
	if (!InDialogue() || State->Runner->choose(ToUtf8(ChoiceId)) != core::ChoiceResult::Advanced)
	{
		return false;
	}
	CloseDialogueIfEnded();
	return true;
}

void UJadgExploration::SetSeed(uint64 Seed)
{
	State->NextSeed = Seed;
}

// --- Le groupe --------------------------------------------------------------------------------

TArray<FJadgMember> UJadgExploration::Members() const
{
	TArray<FJadgMember> Out;
	for (const std::string& Id : State->Party.members())
	{
		const auto Found = State->Sheets.find(Id);
		if (Found == State->Sheets.end())
		{
			continue;
		}
		FJadgMember& Added = Out.AddDefaulted_GetRef();
		Added.Id = FJadgPaths::ToFString(Id);
		Added.Name = FJadgPaths::ToFString(Found->second.sheet.name);
		Added.HitPoints = Found->second.sheet.currentHitPoints;
		Added.MaxHitPoints = Found->second.sheet.maximumHitPoints;
	}
	return Out;
}

void UJadgExploration::RotateLeader()
{
	State->Party.rotateLeader();
}

// --- Les textes -------------------------------------------------------------------------------

FString UJadgExploration::Text(const FString& Key) const
{
	const FString* Found = Texts.Find(Key);
	return Found != nullptr ? *Found : Key;
}

void UJadgExploration::Announce(const FString& Message)
{
	NoticeText = Message;
	NoticeUntil = FPlatformTime::Seconds() + NoticeSeconds;
	UE_LOG(LogJadg, Display, TEXT("[Exploration] %s"), *Message);
}

FString UJadgExploration::Notice() const
{
	return FPlatformTime::Seconds() < NoticeUntil ? NoticeText : FString();
}
