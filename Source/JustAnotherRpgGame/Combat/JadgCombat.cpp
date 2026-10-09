// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Combat/Arena.h"
#include "Core/Combat/Attack.h"
#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/CombatState.h"
#include "Core/Combat/CombatTransition.h"
#include "Core/Combat/Contestants.h"
#include "Core/Combat/Encounter.h"
#include "Core/Combat/EnemyAi.h"
#include "Core/Combat/MapEncounter.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/Equipment.h"
#include "Core/Rpg/Inventory.h"
#include "Core/World/WorldTravel.h"
#include "Game/JadgExplorationState.h"

#include <algorithm>
#include <deque>
#include <filesystem>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <vector>

#include "Combat/JadgCombat.h"

#include "Bridge/JadgPaths.h"
#include "Characters/JadgParty.h"
#include "Characters/JadgWalker.h"
#include "Combat/JadgCombatSpace.h"
#include "Components/CapsuleComponent.h"
#include "DrawDebugHelpers.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "JustAnotherRpgGame.h"
#include "Misc/Paths.h"
#include "NavigationSystem.h"
#include "Player/JadgCameraPawn.h"
#include "Player/JadgPlayerController.h"
#include "World/JadgMapFrame.h"

namespace
{
	/// Ce qui reste à l'écran une fois l'issue connue, avant le retour, en secondes.
	constexpr double BannerSeconds = 2.5;
	/// Une marche qui n'arrive pas se pose au bout d'autant, en secondes, plus le temps du trajet.
	constexpr double WalkGrace = 3.0;
	/// Une figurine est arrivée à un point de son chemin à moins de cette distance, en centimètres.
	constexpr double Arrived = 25.0;
	/// Le temps d'un coup reçu sans geste qui le porte (un jet contre la mort), en secondes.
	constexpr double ReactionSeconds = 0.4;

	std::string ToUtf8(const FString& Text)
	{
		return std::string(TCHAR_TO_UTF8(*Text));
	}

	int32 IdOf(core::CombatantId Id)
	{
		return static_cast<int32>(static_cast<std::uint32_t>(Id));
	}

	core::CombatantId CoreId(int32 Id)
	{
		return static_cast<core::CombatantId>(static_cast<std::uint32_t>(Id));
	}

	/// Un geste en file : ce que Core a déjà résolu, que la figurine montre.
	struct FCue
	{
		enum class EKind : uint8
		{
			Walk,
			Strike,
			Hurt,
			Fall,
		};
		EKind Kind = EKind::Walk;
		core::CombatantId Actor{};
		core::CombatantId Target{};
		/// `Walk` : les points du chemin, en repère du monde.
		TArray<FVector> Points;
		/// `Strike` : le clip (`attack`, `cast`).
		FName Clip;
		/// `Fall` : la mort, pas seulement la chute.
		bool bDead = false;
	};
}

struct AJadgCombat::FState
{
	std::shared_ptr<FJadgCombatSpace> Space;
	std::unique_ptr<core::ArenaSession> Session;
	core::EncounterCatalog Encounters;
	core::Bestiary Bestiary;
	core::BehaviorCatalog Behaviors;
	core::ItemCatalog Items;
	core::EquipmentCatalog Equipment;
	core::EncumbranceRules Encumbrance;

	/// Les figurines, par combattant.
	std::map<core::CombatantId, TWeakObjectPtr<AJadgWalker>> Walkers;
	/// La fiche de chaque héros (`heros-brawler`) et sa classe.
	std::map<core::CombatantId, std::string> Sheets;
	std::map<core::CombatantId, std::string> Classes;

	std::deque<FCue> Cues;
	/// Le geste en cours : son départ, et où il en est.
	std::optional<FCue> Current;
	double CurrentSince = 0.0;
	int32 CurrentPoint = 0;
	bool bImpactDone = false;
	double CurrentLength = 0.0;

	/// Ce que les tours de l'IA ont coûté en tout, décisions comprises, et le pire d'entre eux.
	int32 AiTurns = 0;
	double AiMilliseconds = 0.0;
	double WorstAiMilliseconds = 0.0;
};

AJadgCombat::AJadgCombat()
{
	PrimaryActorTick.bCanEverTick = true;
	// Après le groupe et les personnages : les positions lues ici sont celles de la trame.
	PrimaryActorTick.TickGroup = TG_PostPhysics;
}

AJadgCombat* AJadgCombat::Find(const UWorld* World)
{
	for (TActorIterator<AJadgCombat> It(World); It; ++It)
	{
		return *It;
	}
	return nullptr;
}

bool AJadgCombat::Mount(const FString& EncounterId, uint64 Seed, bool bFigures, bool bHeroesByAi, FString& OutError)
{
	UGameInstance* Instance = GetGameInstance();
	UJadgExploration* Exploration = Instance != nullptr ? Instance->GetSubsystem<UJadgExploration>() : nullptr;
	AJadgMapFrame* Frame = nullptr;
	for (TActorIterator<AJadgMapFrame> It(GetWorld()); It; ++It)
	{
		Frame = *It;
		break;
	}
	if (Exploration == nullptr || Frame == nullptr)
	{
		OutError = TEXT("il manque l'exploration ou le repère de la carte d'arène");
		return false;
	}
	bFiguresShown = bFigures;
	bMounted = false;
	State = MakeShared<FState>();
	FState& S = *State;

	// Le contenu : rencontres, bestiaire, comportements, objets pour la CA des héros.
	const std::filesystem::path Rpg = FJadgPaths::RpgRoot();
	S.Encounters = core::loadEncounters(Rpg / "encounters");
	S.Bestiary = core::loadBestiary(Rpg / "creatures");
	S.Behaviors = core::loadBehaviors(Rpg / "rules" / "behaviors.json");
	S.Items = core::loadItems(Rpg / "items");
	S.Equipment = core::loadEquipment(Rpg / "weapons", Rpg / "armors");
	S.Encumbrance = core::loadEncumbranceRules(Rpg / "rules" / "encumbrance.json");
	const core::Encounter* Encounter = S.Encounters.find(ToUtf8(EncounterId));
	if (Encounter == nullptr)
	{
		OutError = FString::Printf(TEXT("rencontre inconnue : %s"), *EncounterId);
		return false;
	}

	// La carte de Core de l'arène : celle que nomme le repère, dans son dossier puis ceux du jeu.
	std::vector<std::filesystem::path> Dirs;
	if (!Frame->LevelsRoot.IsEmpty())
	{
		Dirs.push_back(FJadgPaths::ToPath(FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), Frame->LevelsRoot))));
	}
	Dirs.push_back(FJadgPaths::ToPath(FJadgPaths::ElementsDir()) / "Levels");
	const core::LevelLoadResult Loaded = core::WorldTravel::directoriesLoader(Dirs)(ToUtf8(Frame->LevelId));
	if (!Loaded.ok())
	{
		OutError = FString::Printf(TEXT("la carte d'arène « %s » ne se lit pas : %s"), *Frame->LevelId, *FJadgPaths::ToFString(Loaded.error));
		return false;
	}
	const core::Level& Map = *Loaded.level;
	const std::optional<core::GridPosition> Trigger = core::encounterTriggerOn(Map, Encounter->id);
	const std::vector<core::GridPosition> Deployment = core::partyDeploymentOn(Map);
	if (!Trigger.has_value() || Deployment.empty())
	{
		OutError = TEXT("la carte d'arène n'a ni marqueur de rencontre ni point d'entrée du groupe");
		return false;
	}
	const core::MapEncounterResult Prepared =
		core::prepareMapEncounter(Map, ToUtf8(Frame->LevelId), *Encounter, *Trigger, Deployment, core::ExplorationSnapshot{}, "");
	if (!Prepared.ok())
	{
		OutError = FJadgPaths::ToFString(Prepared.issue);
		return false;
	}
	const core::MapEncounterSetup& Setup = *Prepared.setup;

	// Le groupe de l'exploration, le meneur en tête, tel que ses fiches le disent.
	UJadgExploration::FState& Party = Exploration->CoreState();
	const core::HeroCatalogs Catalogs{.options = &Party.Options,
		.experience = &Party.Experience,
		.rules = &Party.Rules,
		.items = &S.Items,
		.equipment = &S.Equipment,
		.encumbrance = &S.Encumbrance};
	std::vector<core::HeroContestantSource> Sources;
	std::vector<std::string> SheetIds;
	for (const std::string& Member : Party.Party.members())
	{
		const auto Found = Party.Sheets.find(Member);
		if (Found != Party.Sheets.end())
		{
			Sources.push_back(core::heroContestantSource(Found->second, Catalogs));
			SheetIds.push_back(Member);
		}
	}
	core::EncounterBout Composed = core::boutForEncounter(Setup, Sources, S.Bestiary, S.Behaviors, Seed);
	if (!Composed.bout.has_value())
	{
		OutError = FJadgPaths::ToFString(Composed.issue);
		return false;
	}
	core::ArenaBout& Bout = *Composed.bout;
	if (bHeroesByAi)
	{
		for (std::size_t Rank = 0; Rank < Sources.size() && Rank < Bout.contestants.size(); ++Rank)
		{
			Bout.contestants[Rank].behavior = core::behaviorOfClass(Sources[Rank].sheet.classId);
		}
	}

	// L'espace du moteur, rapporté au coin de la zone de combat : la session joue sur la zone.
	S.Space = std::make_shared<FJadgCombatSpace>(GetWorld(), Frame, FVector2D(Setup.zone.origin.column, Setup.zone.origin.row));
	S.Session = std::make_unique<core::ArenaSession>(Setup.battlefield, S.Space);
	S.Session->setOpportunityPolicy(core::aiOpportunityPolicy(S.Behaviors));
	const core::ArenaMount Mounted = S.Session->mount(Bout);
	if (Mounted.allies.empty() || Mounted.enemies.empty())
	{
		OutError = FString::Printf(TEXT("le montage est refusé : %d allié(s), %d ennemi(s), %d refus"), static_cast<int32>(Mounted.allies.size()),
			static_cast<int32>(Mounted.enemies.size()), static_cast<int32>(Mounted.refusals.size()));
		return false;
	}
	for (const core::MountRefusal& Refusal : Mounted.refusals)
	{
		UE_LOG(LogJadg, Warning, TEXT("[Combat] refusé au montage : %s en (%d ; %d)"), *FJadgPaths::ToFString(Refusal.who),
			Refusal.position.column, Refusal.position.row);
	}
	// Chaque héros enrôlé retrouve sa fiche par son nom : un refus décale les rangs.
	for (const core::CombatantId Id : Mounted.allies)
	{
		const core::Combatant* Fighter = S.Session->combat().find(Id);
		for (std::size_t Rank = 0; Fighter != nullptr && Rank < Sources.size(); ++Rank)
		{
			if (Sources[Rank].sheet.name == Fighter->profile.name)
			{
				S.Sheets[Id] = SheetIds[Rank];
				S.Classes[Id] = Sources[Rank].sheet.classId;
			}
		}
	}

	// Les figurines : les héros de la scène, par leur fiche ; les adversaires, posés ici.
	if (bFiguresShown)
	{
		TMap<FString, AJadgWalker*> Heroes;
		if (const AJadgParty* Group = AJadgParty::Find(GetWorld()))
		{
			for (AJadgWalker* Member : Group->GetMembers())
			{
				Heroes.Add(Member->Appearance, Member);
			}
		}
		for (const auto& [Id, SheetId] : S.Sheets)
		{
			if (AJadgWalker** Found = Heroes.Find(FJadgPaths::ToFString(SheetId)))
			{
				S.Walkers[Id] = *Found;
			}
		}
		const std::filesystem::path Appearances = Rpg / "appearances";
		std::size_t Index = 0;
		for (const core::CombatantId Id : Mounted.enemies)
		{
			const std::string CreatureId = Index < Setup.run.placements.size() ? Setup.run.placements[Index].creatureId : std::string();
			++Index;
			std::error_code Ignored;
			const bool bHasSheet = !CreatureId.empty() && std::filesystem::is_regular_file(Appearances / (CreatureId + ".json"), Ignored);
			AJadgWalker* Walker = GetWorld()->SpawnActorDeferred<AJadgWalker>(AJadgWalker::StaticClass(), FTransform::Identity, nullptr, nullptr,
				ESpawnActorCollisionHandlingMethod::AlwaysSpawn);
			if (Walker == nullptr)
			{
				continue;
			}
			// Sans fiche d'apparence, le pantin (LOT-1015) tient la place de la créature.
			Walker->Appearance = bHasSheet ? FJadgPaths::ToFString(CreatureId) : FString(TEXT("pantin"));
			Walker->FinishSpawning(FTransform::Identity);
			Spawned.Add(Walker);
			S.Walkers[Id] = Walker;
		}
		// Chacun debout sur sa base, tourné vers le camp d'en face.
		const FVector TriggerWorld = S.Space->ToWorld(core::tileCenter(core::mapToZone(Setup.zone, *Trigger)));
		const FVector PartyWorld = S.Space->ToWorld(core::tileCenter(core::mapToZone(Setup.zone, Deployment.front())));
		for (const auto& [Id, Weak] : S.Walkers)
		{
			AJadgWalker* Walker = Weak.Get();
			const std::optional<core::Meters3> Base = S.Session->combat().positionOf(Id);
			if (Walker == nullptr || !Base.has_value())
			{
				continue;
			}
			const core::Combatant* Fighter = S.Session->combat().find(Id);
			const FVector Toward = (Fighter->profile.side == core::CombatSide::Allies ? TriggerWorld : PartyWorld) - S.Space->ToWorld(*Base);
			Walker->SetInCombat(true);
			Walker->StandOn(S.Space->ToWorld(*Base), Toward.Rotation().Yaw);
		}
	}

	// Ce que la figurine montre : les pas, les gestes, les coups et les chutes.
	FState* const Held = State.Get();
	S.Session->setMoveObserver([this, Held](core::CombatantId Mover, const core::Route& Path)
	{
		FCue Cue;
		Cue.Kind = FCue::EKind::Walk;
		Cue.Actor = Mover;
		for (const core::Meters3& Point : Path.points)
		{
			Cue.Points.Add(Held->Space->ToWorld(Point));
		}
		Held->Cues.push_back(MoveTemp(Cue));
	});
	S.Session->setActionObserver([Held](const core::ArenaActionNotice& Notice)
	{
		if (Notice.phase != core::ArenaActionPhase::Begin)
		{
			return;
		}
		FCue Cue;
		Cue.Kind = FCue::EKind::Strike;
		Cue.Actor = Notice.actor;
		Cue.Target = Notice.target;
		Cue.Clip = Notice.spell.empty() ? FName(TEXT("attack")) : FName(TEXT("cast"));
		Held->Cues.push_back(MoveTemp(Cue));
	});
	core::CombatState& Combat = S.Session->combat();
	Combat.subscribe(core::CombatHook::AttackDeclared, [Held](core::CombatState& Fight, const core::CombatEvent& Event)
	{
		// L'attaque du combattant actif est déjà en file par l'observateur d'action ; celle d'un
		// autre est une attaque d'opportunité.
		if (Event.combatant.has_value() && Event.target.has_value() && Fight.activeCombatant() != Event.combatant)
		{
			FCue Cue;
			Cue.Kind = FCue::EKind::Strike;
			Cue.Actor = *Event.combatant;
			Cue.Target = *Event.target;
			Cue.Clip = TEXT("attack");
			Held->Cues.push_back(MoveTemp(Cue));
		}
	});
	Combat.subscribe(core::CombatHook::DamageTaken, [Held](core::CombatState&, const core::CombatEvent& Event)
	{
		if (Event.combatant.has_value() && Event.hitPointsAfter > 0)
		{
			FCue Cue;
			Cue.Kind = FCue::EKind::Hurt;
			Cue.Target = *Event.combatant;
			Held->Cues.push_back(MoveTemp(Cue));
		}
	});
	const auto Falls = [Held](bool bDead)
	{
		return [Held, bDead](core::CombatState&, const core::CombatEvent& Event)
		{
			if (Event.combatant.has_value())
			{
				FCue Cue;
				Cue.Kind = FCue::EKind::Fall;
				Cue.Target = *Event.combatant;
				Cue.bDead = bDead;
				Held->Cues.push_back(MoveTemp(Cue));
			}
		};
	};
	Combat.subscribe(core::CombatHook::CombatantDowned, Falls(false));
	Combat.subscribe(core::CombatHook::CombatantDied, Falls(true));

	if (!S.Session->start())
	{
		OutError = TEXT("le combat ne commence pas");
		return false;
	}
	bMounted = true;
	UE_LOG(LogJadg, Display, TEXT("[Combat] « %s » monté sur « %s », graine %llu : %d allié(s), %d adversaire(s), zone %s"), *EncounterId,
		*Frame->LevelId, Seed, static_cast<int32>(Mounted.allies.size()), static_cast<int32>(Mounted.enemies.size()),
		*FJadgPaths::ToFString(Setup.zone.name));
	for (const std::string& Note : Setup.notes)
	{
		UE_LOG(LogJadg, Display, TEXT("[Combat] %s"), *FJadgPaths::ToFString(Note));
	}
	return true;
}

bool AJadgCombat::IsMounted() const
{
	return bMounted && State.IsValid() && State->Session != nullptr;
}

bool AJadgCombat::IsOver() const
{
	return IsMounted() && State->Session->combat().phase() == core::CombatPhase::Ended;
}

bool AJadgCombat::IsBusy() const
{
	return IsMounted() && (State->Current.has_value() || !State->Cues.empty());
}

int32 AJadgCombat::ActiveId() const
{
	if (!IsMounted())
	{
		return 0;
	}
	const std::optional<core::CombatantId> Active = State->Session->combat().activeCombatant();
	return Active.has_value() ? IdOf(*Active) : 0;
}

int32 AJadgCombat::Round() const
{
	return IsMounted() ? State->Session->combat().round() : 0;
}

bool AJadgCombat::IsPlayerTurn() const
{
	if (!IsMounted() || IsOver() || IsBusy())
	{
		return false;
	}
	const int32 Active = ActiveId();
	const core::Combatant* Fighter = Active != 0 ? State->Session->combat().find(CoreId(Active)) : nullptr;
	return Fighter != nullptr && Fighter->status == core::CombatantStatus::Standing
		&& State->Session->behaviorOf(CoreId(Active)).empty();
}

FString AJadgCombat::Outcome() const
{
	if (!IsMounted())
	{
		return FString();
	}
	const std::optional<core::CombatOutcome> Issue = State->Session->outcome();
	if (!Issue.has_value())
	{
		return FString();
	}
	return *Issue == core::CombatOutcome::Victory ? TEXT("Victoire") : *Issue == core::CombatOutcome::Flight ? TEXT("Fuite") : TEXT("Défaite");
}

TArray<FJadgFighter> AJadgCombat::Fighters() const
{
	TArray<FJadgFighter> Out;
	if (!IsMounted())
	{
		return Out;
	}
	const core::CombatState& Combat = State->Session->combat();
	for (const core::CombatantId Id : Combat.combatants())
	{
		const core::Combatant* Fighter = Combat.find(Id);
		FJadgFighter& Added = Out.AddDefaulted_GetRef();
		Added.Id = IdOf(Id);
		Added.Name = FJadgPaths::ToFString(Fighter->profile.name);
		Added.bAlly = Fighter->profile.side == core::CombatSide::Allies;
		Added.bStanding = Fighter->status == core::CombatantStatus::Standing;
		Added.bDead = Fighter->status == core::CombatantStatus::Dead;
		Added.HitPoints = Fighter->profile.currentHitPoints;
		Added.MaxHitPoints = Fighter->profile.maximumHitPoints;
		Added.Walker = WalkerOf(Added.Id);
	}
	return Out;
}

TOptional<FVector> AJadgCombat::PositionOf(int32 Id) const
{
	if (!IsMounted())
	{
		return {};
	}
	const std::optional<core::Meters3> Base = State->Session->combat().positionOf(CoreId(Id));
	return Base.has_value() ? TOptional<FVector>(State->Space->ToWorld(*Base)) : TOptional<FVector>();
}

AJadgWalker* AJadgCombat::WalkerOf(int32 Id) const
{
	if (!IsMounted())
	{
		return nullptr;
	}
	const auto Found = State->Walkers.find(CoreId(Id));
	return Found != State->Walkers.end() ? Found->second.Get() : nullptr;
}

float AJadgCombat::MovementLeft() const
{
	return IsMounted() ? State->Session->combat().movementLeft() : 0.0f;
}

TArray<FString> AJadgCombat::Capacities() const
{
	TArray<FString> Out;
	const int32 Active = ActiveId();
	const std::vector<core::ArenaSpell>* Spells = Active != 0 ? State->Session->spells(CoreId(Active)) : nullptr;
	if (Spells == nullptr)
	{
		return Out;
	}
	for (const core::ArenaSpell& Spell : *Spells)
	{
		const FString Uses = Spell.uses < 0 ? FString(TEXT("à volonté")) : FString::Printf(TEXT("%d lancer(s)"), Spell.uses);
		Out.Add(FString::Printf(TEXT("%s (%s%s)"), *FJadgPaths::ToFString(Spell.name), *Uses, Spell.bonusAction ? TEXT(", action bonus") : TEXT("")));
	}
	return Out;
}

FString AJadgCombat::TargetCircumstances() const
{
	const int32 Active = ActiveId();
	if (!IsMounted() || Active == 0 || Target == 0)
	{
		return FString();
	}
	const std::vector<core::AttackProfile>* Attacks = State->Session->attacks(CoreId(Active));
	if (Attacks == nullptr || Attacks->empty())
	{
		return FString();
	}
	const core::CombatState& Combat = State->Session->combat();
	FString Text;
	for (const core::AttackProfile& Profile : *Attacks)
	{
		if (core::checkTarget(Combat, CoreId(Active), CoreId(Target), Profile) != core::TargetCheck::Valid)
		{
			continue;
		}
		// Celles de l'espace (la hauteur, le corps à corps) et celles de la session (l'esquive, la tenaille).
		const std::optional<core::Volume> From = Combat.volumeOf(CoreId(Active));
		const std::optional<core::Volume> To = Combat.volumeOf(CoreId(Target));
		std::vector<std::string> For;
		std::vector<std::string> Against;
		if (From.has_value() && To.has_value() && core::hasHighGround(*From, *To))
		{
			For.push_back("hauteur");
		}
		const core::AttackCircumstances Session = State->Session->circumstancesAgainst(CoreId(Active), CoreId(Target), Profile);
		For.insert(For.end(), Session.advantages.begin(), Session.advantages.end());
		Against.insert(Against.end(), Session.disadvantages.begin(), Session.disadvantages.end());
		Text = FString::Printf(TEXT("%s à portée"), *FJadgPaths::ToFString(Profile.label));
		for (const std::string& Item : For)
		{
			Text += TEXT(" · avantage : ") + FJadgPaths::ToFString(Item);
		}
		for (const std::string& Item : Against)
		{
			Text += TEXT(" · désavantage : ") + FJadgPaths::ToFString(Item);
		}
		return Text;
	}
	return TEXT("hors de portée d'ici");
}

TArray<FString> AJadgCombat::Journal(int32 Count) const
{
	TArray<FString> Out;
	if (!IsMounted())
	{
		return Out;
	}
	const std::vector<std::string>& Lines = State->Session->journal();
	const int32 First = FMath::Max(0, static_cast<int32>(Lines.size()) - Count);
	for (int32 Index = First; Index < static_cast<int32>(Lines.size()); ++Index)
	{
		Out.Add(FJadgPaths::ToFString(Lines[static_cast<std::size_t>(Index)]));
	}
	return Out;
}

FString AJadgCombat::CandidateReport() const
{
	if (!IsMounted())
	{
		return FString();
	}
	const FState& S = *State;
	const FJadgCandidateTotals& T = S.Space->Totals();
	return FString::Printf(TEXT("{\"aiTurns\": %d, \"aiTurnMs\": %.1f, \"worstAiTurnMs\": %.1f, \"queries\": %d, \"eqsQueries\": %d, \"pointsPerQuery\": %.1f, \"keptPerQuery\": %.1f, \"queryMs\": %.2f, \"worstQueryMs\": %.2f, \"unlimitedQueries\": %d, \"unlimitedQueryMs\": %.2f, \"worstUnlimitedQueryMs\": %.2f}"),
		S.AiTurns, S.AiTurns > 0 ? S.AiMilliseconds / S.AiTurns : 0.0, S.WorstAiMilliseconds, T.Queries, T.EqsQueries,
		T.Queries > 0 ? static_cast<double>(T.Generated) / T.Queries : 0.0, T.Queries > 0 ? static_cast<double>(T.Kept) / T.Queries : 0.0,
		T.Queries > 0 ? T.Milliseconds / T.Queries : 0.0, T.WorstMilliseconds, T.UnlimitedQueries,
		T.UnlimitedQueries > 0 ? T.UnlimitedMilliseconds / T.UnlimitedQueries : 0.0, T.WorstUnlimitedMilliseconds);
}

// --- Le joueur ------------------------------------------------------------------------------

void AJadgCombat::Refuse(const FString& Why)
{
	LastRefusal = Why;
	UE_LOG(LogJadg, Display, TEXT("[Combat] refusé : %s"), *Why);
}

bool AJadgCombat::Click(const FHitResult& Hit)
{
	if (!IsPlayerTurn())
	{
		return false;
	}
	for (const auto& [Id, Weak] : State->Walkers)
	{
		if (Weak.Get() != nullptr && Weak.Get() == Hit.GetActor())
		{
			Select(IdOf(Id));
			return true;
		}
	}
	return MoveTo(Hit.ImpactPoint);
}

void AJadgCombat::Select(int32 Id)
{
	if (IsMounted() && State->Session->combat().find(CoreId(Id)) != nullptr)
	{
		Target = Id;
		LastRefusal.Reset();
	}
}

bool AJadgCombat::MoveTo(const FVector& World)
{
	if (!IsPlayerTurn())
	{
		return false;
	}
	core::ArenaSession& Session = *State->Session;
	const core::Meters3 Wanted = State->Space->FromWorld(World);
	// La place candidate la plus proche du point ; si le budget n'y mène pas, la plus avancée vers lui.
	const std::vector<core::Destination> Places = Session.combat().destinations();
	const core::Destination* Best = nullptr;
	float BestGap = 0.0f;
	for (const core::Destination& Place : Places)
	{
		const float Gap = core::groundDistance(Place.point, Wanted);
		if (Best == nullptr || Gap < BestGap)
		{
			Best = &Place;
			BestGap = Gap;
		}
	}
	if (Best == nullptr || Best->route.points.empty())
	{
		Refuse(TEXT("aucune place atteignable vers ce point"));
		return false;
	}
	const core::MoveOutcome Moved = Session.move(Best->point);
	if (Moved.result != core::MoveResult::Moved)
	{
		Refuse(TEXT("ce point n'est pas atteignable"));
		return false;
	}
	LastRefusal.Reset();
	return true;
}

bool AJadgCombat::Attack()
{
	if (!IsPlayerTurn())
	{
		return false;
	}
	if (Target == 0)
	{
		Refuse(TEXT("aucune cible : cliquer sur un adversaire"));
		return false;
	}
	core::ArenaSession& Session = *State->Session;
	const core::CombatantId Active = CoreId(ActiveId());
	const std::vector<core::AttackProfile>* Attacks = Session.attacks(Active);
	if (Attacks == nullptr)
	{
		return false;
	}
	for (std::size_t Index = 0; Index < Attacks->size(); ++Index)
	{
		if (core::checkTarget(Session.combat(), Active, CoreId(Target), (*Attacks)[Index]) == core::TargetCheck::Valid)
		{
			const core::ArenaAttack Done = Session.attack(CoreId(Target), Index);
			if (Done.result == core::ArenaActionResult::Done)
			{
				LastRefusal.Reset();
				return true;
			}
			Refuse(Done.result == core::ArenaActionResult::NoAction ? TEXT("l'action de ce tour est déjà prise") : TEXT("l'attaque est refusée"));
			return false;
		}
	}
	Refuse(TEXT("la cible est hors d'allonge et de portée, ou à l'abri total"));
	return false;
}

void AJadgCombat::SelectCapacity(int32 Rank)
{
	Capacity = Rank;
	LastRefusal.Reset();
}

bool AJadgCombat::Cast()
{
	if (!IsPlayerTurn())
	{
		return false;
	}
	core::ArenaSession& Session = *State->Session;
	const core::CombatantId Active = CoreId(ActiveId());
	const std::vector<core::ArenaSpell>* Spells = Session.spells(Active);
	if (Spells == nullptr || Capacity < 1 || Capacity > static_cast<int32>(Spells->size()))
	{
		Refuse(TEXT("aucune capacité choisie : un chiffre la choisit"));
		return false;
	}
	const core::ArenaSpell& Spell = (*Spells)[static_cast<std::size_t>(Capacity - 1)];
	const core::CombatantId On = Spell.target == core::SpellTarget::Self || Target == 0 ? Active : CoreId(Target);
	const core::ArenaAttack Done = Session.castSpell(On, static_cast<std::size_t>(Capacity - 1));
	if (Done.result != core::ArenaActionResult::Done)
	{
		Refuse(FString::Printf(TEXT("%s ne se lance pas sur cette cible"), *FJadgPaths::ToFString(Spell.name)));
		return false;
	}
	LastRefusal.Reset();
	return true;
}

bool AJadgCombat::EndTurn()
{
	if (!IsPlayerTurn())
	{
		return false;
	}
	Target = 0;
	Capacity = 0;
	LastRefusal.Reset();
	return State->Session->endTurn();
}

bool AJadgCombat::PlanForActive(FJadgPlan& OutPlan) const
{
	if (!IsPlayerTurn())
	{
		return false;
	}
	const core::CombatantId Active = CoreId(ActiveId());
	const auto Class = State->Classes.find(Active);
	const core::BehaviorProfile* Profile =
		State->Behaviors.find(core::behaviorOfClass(Class != State->Classes.end() ? Class->second : std::string()));
	if (Profile == nullptr)
	{
		return false;
	}
	const core::TurnPlan Plan = core::planTurn(*State->Session, Active, *Profile);
	OutPlan = FJadgPlan();
	OutPlan.Summary = FJadgPaths::ToFString(Plan.summary);
	if (Plan.moveTo.has_value())
	{
		OutPlan.MoveTo = State->Space->ToWorld(*Plan.moveTo);
	}
	else if (Plan.dashTo.has_value())
	{
		// Le joueur ne se précipite pas au clavier : il va aussi loin que son budget le mène, à la
		// place atteignable la plus proche du but de la course.
		const core::Destination* Best = nullptr;
		float BestGap = 0.0f;
		for (const core::Destination& Place : State->Session->combat().destinations())
		{
			const float Gap = core::groundDistance(Place.point, *Plan.dashTo);
			if (!Place.route.points.empty() && (Best == nullptr || Gap < BestGap))
			{
				Best = &Place;
				BestGap = Gap;
			}
		}
		if (Best != nullptr)
		{
			OutPlan.MoveTo = State->Space->ToWorld(Best->point);
		}
	}
	OutPlan.TargetId = Plan.target.has_value() ? IdOf(*Plan.target) : 0;
	OutPlan.Action = Plan.action == core::TurnAction::Attack ? FName(TEXT("attack"))
		: Plan.action == core::TurnAction::Cast ? FName(TEXT("cast")) : FName(TEXT("end"));
	OutPlan.SpellRank = static_cast<int32>(Plan.spellIndex) + 1;
	return true;
}

// --- La trame -------------------------------------------------------------------------------

void AJadgCombat::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	Advance(DeltaSeconds);
	if (IsPlayerTurn())
	{
		DrawPreview();
	}
}

void AJadgCombat::Advance(float DeltaSeconds)
{
	if (!IsMounted() || bPaused || bResolved)
	{
		return;
	}
	if (IsBusy())
	{
		ProcessCues(DeltaSeconds);
		return;
	}
	SyncFigures();
	if (IsOver())
	{
		const double Now = GetWorld()->GetTimeSeconds();
		if (OverSince < 0.0)
		{
			OverSince = Now;
			UE_LOG(LogJadg, Display, TEXT("[Combat] issue : %s, round %d"), *Outcome(), Round());
		}
		if (!bFiguresShown || Now - OverSince >= BannerSeconds)
		{
			Resolve();
		}
		return;
	}
	NextTurn();
}

void AJadgCombat::NextTurn()
{
	core::ArenaSession& Session = *State->Session;
	const std::optional<core::CombatantId> Active = Session.combat().activeCombatant();
	if (!Active.has_value())
	{
		return;
	}
	if (IdOf(*Active) != LastActive)
	{
		LastActive = IdOf(*Active);
		Target = 0;
		Capacity = 0;
		// La caméra suit le combattant dont c'est le tour.
		const APlayerController* Player = GetWorld()->GetFirstPlayerController();
		AJadgCameraPawn* View = Player != nullptr ? ::Cast<AJadgCameraPawn>(Player->GetPawn()) : nullptr;
		if (AJadgWalker* Walker = WalkerOf(LastActive); Walker != nullptr && View != nullptr)
		{
			View->Follow(Walker);
		}
	}
	const core::Combatant* Fighter = Session.combat().find(*Active);
	if (Fighter == nullptr || Fighter->status != core::CombatantStatus::Standing)
	{
		static_cast<void>(Session.endTurn());
		return;
	}
	if (Session.behaviorOf(*Active).empty())
	{
		// Le tour du joueur : on attend ses clics et ses touches.
		return;
	}
	const std::size_t Before = Session.journal().size();
	const double Start = FPlatformTime::Seconds();
	FState& S = *State;
	if (!core::playTurn(Session, S.Behaviors))
	{
		static_cast<void>(Session.endTurn());
	}
	const double Spent = (FPlatformTime::Seconds() - Start) * 1000.0;
	S.AiTurns += 1;
	S.AiMilliseconds += Spent;
	S.WorstAiMilliseconds = FMath::Max(S.WorstAiMilliseconds, Spent);
	const FJadgCandidateStats& Last = S.Space->LastStats();
	for (std::size_t Line = Before; Line < Session.journal().size(); ++Line)
	{
		UE_LOG(LogJadg, Display, TEXT("[Combat] %s"), *FJadgPaths::ToFString(Session.journal()[Line]));
	}
	UE_LOG(LogJadg, Display, TEXT("[Combat] tour de l'IA en %.0f ms (dernière requête de candidats : %d points, %d places, %.1f ms, %s)"), Spent,
		Last.Generated, Last.Kept, Last.Milliseconds, Last.bFromEqs ? TEXT("EQS") : TEXT("échantillonnage"));
}

void AJadgCombat::ProcessCues(float DeltaSeconds)
{
	FState& S = *State;
	const double Now = GetWorld()->GetTimeSeconds();
	if (!S.Current.has_value())
	{
		S.Current = MoveTemp(S.Cues.front());
		S.Cues.pop_front();
		S.CurrentSince = Now;
		S.CurrentPoint = 0;
		S.bImpactDone = false;
		S.CurrentLength = 0.0;
		const FCue& Cue = *S.Current;
		AJadgWalker* Actor = WalkerOf(IdOf(Cue.Actor));
		AJadgWalker* Victim = WalkerOf(IdOf(Cue.Target));
		switch (Cue.Kind)
		{
		case FCue::EKind::Walk:
			if (Actor != nullptr && !Cue.Points.IsEmpty())
			{
				Actor->WalkTo(Cue.Points[0], 10.0f);
				for (int32 Index = 0; Index < Cue.Points.Num(); ++Index)
				{
					S.CurrentLength += FVector::Dist2D(Index == 0 ? Actor->Feet() : Cue.Points[Index - 1], Cue.Points[Index]);
				}
			}
			break;
		case FCue::EKind::Strike:
			if (Actor != nullptr)
			{
				if (Victim != nullptr && Victim != Actor)
				{
					const FVector Toward = Victim->GetActorLocation() - Actor->GetActorLocation();
					Actor->SetActorRotation(FRotator(0.0f, Toward.Rotation().Yaw, 0.0f));
				}
				if (!Actor->PlayOnce(Cue.Clip))
				{
					Actor->PlayOnce(TEXT("attack"));
				}
				S.CurrentLength = FMath::Max(Actor->ClipSeconds(Cue.Clip), 0.6f);
			}
			break;
		case FCue::EKind::Hurt:
		case FCue::EKind::Fall:
			S.CurrentLength = ReactionSeconds;
			break;
		}
	}

	FCue& Cue = *S.Current;
	AJadgWalker* Actor = WalkerOf(IdOf(Cue.Actor));
	const double Elapsed = Now - S.CurrentSince;
	// Sans figurine (les tests), un geste est fait aussitôt.
	const bool bInstant = !bFiguresShown;
	bool bDone = bInstant;
	const auto React = [this](const FCue& Reaction)
	{
		AJadgWalker* Victim = WalkerOf(IdOf(Reaction.Target));
		if (Victim == nullptr)
		{
			return;
		}
		if (Reaction.Kind == FCue::EKind::Fall)
		{
			Victim->PlayAndHold(TEXT("death"));
		}
		else
		{
			Victim->PlayOnce(TEXT("hit"));
		}
	};
	switch (Cue.Kind)
	{
	case FCue::EKind::Walk:
		if (Actor == nullptr || Cue.Points.IsEmpty())
		{
			bDone = true;
			break;
		}
		if (FVector::Dist2D(Actor->Feet(), Cue.Points[S.CurrentPoint]) < Arrived || !Actor->IsWalking())
		{
			if (++S.CurrentPoint < Cue.Points.Num())
			{
				Actor->WalkTo(Cue.Points[S.CurrentPoint], 10.0f);
			}
			else
			{
				bDone = true;
			}
		}
		if (!bDone && Elapsed > S.CurrentLength / FMath::Max(Actor->WalkSpeed, 1.0f) + WalkGrace)
		{
			bDone = true;
		}
		if (bDone || bInstant)
		{
			// La figurine se pose sur la base que Core lui donne : le chemin payé est la vérité.
			const std::optional<core::Meters3> Base = S.Session->combat().positionOf(Cue.Actor);
			if (Base.has_value())
			{
				Actor->StandOn(S.Space->ToWorld(*Base), Actor->GetActorRotation().Yaw);
			}
		}
		break;
	case FCue::EKind::Strike:
	{
		const double Impact = Actor != nullptr ? Actor->ImpactSeconds(Cue.Clip) : 0.0;
		if (!S.bImpactDone && (bInstant || Elapsed >= Impact))
		{
			// À l'instant d'impact : les coups reçus et les chutes qui suivent ce geste.
			S.bImpactDone = true;
			while (!S.Cues.empty() && (S.Cues.front().Kind == FCue::EKind::Hurt || S.Cues.front().Kind == FCue::EKind::Fall))
			{
				React(S.Cues.front());
				S.Cues.pop_front();
			}
		}
		bDone = bDone || Actor == nullptr || Elapsed >= S.CurrentLength;
		break;
	}
	case FCue::EKind::Hurt:
	case FCue::EKind::Fall:
		if (Elapsed == 0.0 || bInstant)
		{
			React(Cue);
		}
		bDone = bDone || Elapsed >= S.CurrentLength;
		break;
	}
	if (bDone)
	{
		S.Current.reset();
	}
}

void AJadgCombat::SyncFigures()
{
	if (!bFiguresShown)
	{
		return;
	}
	// Un combattant relevé (un soin, *revigorer*) quitte la pose de sa chute.
	for (const auto& [Id, Weak] : State->Walkers)
	{
		AJadgWalker* Walker = Weak.Get();
		const core::Combatant* Fighter = State->Session->combat().find(Id);
		if (Walker != nullptr && Fighter != nullptr && Fighter->status == core::CombatantStatus::Standing && Walker->IsHolding())
		{
			// Seule la pose tenue (la chute) se quitte ici ; un geste en cours finit seul.
			Walker->ReturnToRest();
		}
	}
}

void AJadgCombat::DrawPreview() const
{
	UWorld* World = GetWorld();
	const FState& S = *State;
	const core::CombatState& Combat = S.Session->combat();
	const core::CombatantId Active = CoreId(ActiveId());
	const std::optional<core::Meters3> Base = Combat.positionOf(Active);
	if (!Base.has_value())
	{
		return;
	}
	const FVector Lift(0.0, 0.0, 6.0);
	const FVector Here = S.Space->ToWorld(*Base) + Lift;
	// La portée restante : un cercle au sol, du rayon des mètres qui restent.
	DrawDebugCircle(World, Here, Combat.movementLeft() * 100.0f, 64, FColor(90, 200, 255), false, -1.0f, 0, 3.0f, FVector(1, 0, 0), FVector(0, 1, 0),
		false);

	// Les cibles atteignables d'ici, et la cible choisie.
	const std::vector<core::AttackProfile>* Attacks = S.Session->attacks(Active);
	for (const core::CombatantId Other : Combat.combatants())
	{
		const core::Combatant* Fighter = Combat.find(Other);
		const std::optional<core::Meters3> There = Combat.positionOf(Other);
		if (Other == Active || Fighter == nullptr || !There.has_value() || Fighter->profile.side == Combat.find(Active)->profile.side
			|| Fighter->status == core::CombatantStatus::Dead)
		{
			continue;
		}
		bool bReachable = false;
		for (std::size_t Index = 0; Attacks != nullptr && Index < Attacks->size() && !bReachable; ++Index)
		{
			bReachable = core::checkTarget(Combat, Active, Other, (*Attacks)[Index]) == core::TargetCheck::Valid;
		}
		const FVector Foot = S.Space->ToWorld(*There) + Lift;
		if (IdOf(Other) == Target)
		{
			DrawDebugCircle(World, Foot, 95.0f, 32, FColor::White, false, -1.0f, 0, 5.0f, FVector(1, 0, 0), FVector(0, 1, 0), false);
		}
		if (bReachable)
		{
			DrawDebugCircle(World, Foot, 80.0f, 32, FColor(255, 210, 60), false, -1.0f, 0, 4.0f, FVector(1, 0, 0), FVector(0, 1, 0), false);
		}
	}

	// Le chemin vers le point sous le pointeur, et ce qu'il provoquerait.
	const AJadgPlayerController* Player = ::Cast<AJadgPlayerController>(World->GetFirstPlayerController());
	FHitResult Hit;
	if (Player == nullptr || !Player->PointerHit(Hit))
	{
		return;
	}
	const core::Meters3 Wanted = S.Space->FromWorld(Hit.ImpactPoint);
	const std::optional<core::Route> Path = Combat.routeTo(Wanted);
	if (!Path.has_value())
	{
		DrawDebugLine(World, Here, Hit.ImpactPoint + Lift, FColor(220, 60, 60), false, -1.0f, 0, 3.0f);
		return;
	}
	FVector From = Here;
	for (const core::Meters3& Point : Path->points)
	{
		const FVector To = S.Space->ToWorld(Point) + Lift;
		DrawDebugLine(World, From, To, FColor(80, 230, 110), false, -1.0f, 0, 4.0f);
		From = To;
	}
	for (const core::CombatantId Reactor : S.Session->previewOpportunities(Wanted))
	{
		if (const std::optional<core::Meters3> There = Combat.positionOf(Reactor))
		{
			DrawDebugCircle(World, S.Space->ToWorld(*There) + Lift, 110.0f, 32, FColor(230, 40, 40), false, -1.0f, 0, 5.0f, FVector(1, 0, 0),
				FVector(0, 1, 0), false);
		}
	}
}

// --- L'issue --------------------------------------------------------------------------------

void AJadgCombat::Resolve()
{
	bResolved = true;
	UGameInstance* Instance = GetGameInstance();
	UJadgExploration* Exploration = Instance != nullptr ? Instance->GetSubsystem<UJadgExploration>() : nullptr;
	const std::optional<core::CombatOutcome> Issue = State->Session->outcome();
	if (Exploration == nullptr || !Issue.has_value())
	{
		return;
	}
	// Les fiches gardent ce que le combat a laissé, comme l'écran de rencontre du LOT-139 : debout,
	// ses points de vie (au moins 1) ; à terre, 1 ; ses lancers restants. Une défaite ne laisse
	// rien (l'écran de fin est au LOT-1020) ; un mort garde sa fiche telle quelle — l'enterrement
	// du LOT-139 n'est pas porté (fiche du LOT-1017, ce qui reste).
	if (*Issue != core::CombatOutcome::Defeat)
	{
		UJadgExploration::FState& Party = Exploration->CoreState();
		for (const auto& [Id, SheetId] : State->Sheets)
		{
			const core::Combatant* Fighter = State->Session->combat().find(Id);
			const auto Sheet = Party.Sheets.find(SheetId);
			if (Fighter == nullptr || Sheet == Party.Sheets.end() || Fighter->status == core::CombatantStatus::Dead)
			{
				continue;
			}
			core::CharacterSheet& Written = Sheet->second.sheet;
			Written.currentHitPoints =
				Fighter->status == core::CombatantStatus::Down ? 1 : FMath::Max(1, Fighter->profile.currentHitPoints);
			if (const std::vector<core::ArenaSpell>* Spells = State->Session->spells(Id))
			{
				for (const core::ArenaSpell& Spell : *Spells)
				{
					for (core::KnownSpell& Known : Written.knownSpells)
					{
						if (Known.spellId == Spell.id && Known.perDay > 0 && Spell.uses >= 0)
						{
							Known.remaining = Spell.uses;
						}
					}
				}
			}
		}
	}
	Exploration->ResolveEncounter(*Issue == core::CombatOutcome::Victory ? EJadgOutcome::Victory
		: *Issue == core::CombatOutcome::Flight ? EJadgOutcome::Flight : EJadgOutcome::Defeat);
	if (bFiguresShown)
	{
		if (AJadgParty* Group = AJadgParty::Find(GetWorld()))
		{
			Group->ReturnFromArena();
		}
	}
}

void AJadgCombat::EndPlay(const EEndPlayReason::Type Reason)
{
	if (State.IsValid())
	{
		// L'espace tient un acteur du monde (le demandeur de l'EQS) : il part avec le combat.
		State->Session.reset();
		State->Space.reset();
	}
	Super::EndPlay(Reason);
}
