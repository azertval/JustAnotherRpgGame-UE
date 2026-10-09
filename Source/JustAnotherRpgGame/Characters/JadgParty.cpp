// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/World/FollowTrail.h"

#include <vector>

#include "Characters/JadgParty.h"

#include "Characters/JadgWalker.h"
#include "Combat/JadgCombat.h"
#include "Components/CapsuleComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Game/JadgExploration.h"
#include "GameFramework/PlayerController.h"
#include "JustAnotherRpgGame.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/CommandLine.h"
#include "Misc/PackageName.h"
#include "NavigationSystem.h"
#include "Player/JadgCameraPawn.h"
#include "UObject/Package.h"
#include "World/JadgDayLight.h"
#include "World/JadgMapFrame.h"

namespace
{
	/// L'étiquette d'un acteur du décor qui montre une entité de la carte de Core : `JadgEntity:e7`.
	const FString EntityTagPrefix(TEXT("JadgEntity:"));

	/// Le côté d'une case, en centimètres, sur une carte du moteur sans carte de Core.
	constexpr double DefaultCell = 150.0;

	/// Un suiveur reçoit un nouvel ordre quand son point de la trace a bougé d'autant, en cases.
	constexpr float ReorderCells = 0.2f;

	/// Un suiveur à moins de cette distance de son point n'y est pas renvoyé, en centimètres.
	constexpr double CloseEnough = 20.0;

	/// La distance à laquelle le meneur s'arrête de ce qu'il va solliciter, en cases : dans la
	/// portée de Core (`core::INTERACTION_REACH_CELLS`, 1,5 case), hors de la case de la cible.
	constexpr double ApproachCells = 1.0;

	/// Les trames où le combat de l'arène se remonte, le temps que son maillage de navigation soit prêt.
	constexpr int32 MountTries = 600;
}

struct AJadgParty::FState
{
	core::FollowTrail Trail;
	/// Le point de la trace vers lequel chaque suiveur a été envoyé, par rang.
	TArray<FVector2D> Ordered;
};

AJadgParty::AJadgParty()
{
	PrimaryActorTick.bCanEverTick = true;
	// Après les personnages : la case du meneur lue ici est celle de la trame.
	PrimaryActorTick.TickGroup = TG_PostPhysics;
}

AJadgParty* AJadgParty::Find(const UWorld* World)
{
	for (TActorIterator<AJadgParty> It(World); It; ++It)
	{
		return *It;
	}
	return nullptr;
}

AJadgWalker* AJadgParty::Leader() const
{
	return Members.IsEmpty() ? nullptr : Members[0].Get();
}

FVector2D AJadgParty::CellOf(const FVector& World) const
{
	return Frame != nullptr ? Frame->ToCell(World) : FVector2D(World.X, World.Y) / DefaultCell;
}

FVector AJadgParty::WorldOf(const FVector2D& Cell, double Height) const
{
	FVector Point = Frame != nullptr ? Frame->ToWorld(Cell) : FVector(Cell.X * DefaultCell, Cell.Y * DefaultCell, 0.0);
	Point.Z = Height;
	return Point;
}

bool AJadgParty::OnNavigation(const FVector& Point, FVector& OutGround) const
{
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
	FNavLocation Found;
	if (Navigation != nullptr && Navigation->ProjectPointToNavigation(Point, Found, FVector(200.0, 200.0, 400.0)))
	{
		OutGround = Found.Location;
		return true;
	}
	return false;
}

void AJadgParty::BeginPlay()
{
	Super::BeginPlay();

	State = MakeShared<FState>();
	Exploration = GetGameInstance() != nullptr ? GetGameInstance()->GetSubsystem<UJadgExploration>() : nullptr;
	for (TActorIterator<AJadgMapFrame> It(GetWorld()); It; ++It)
	{
		Frame = *It;
		break;
	}
	for (TActorIterator<AJadgWalker> It(GetWorld()); It; ++It)
	{
		if (It->PartyRank >= 0)
		{
			Members.Add(*It);
		}
	}
	Members.Sort([](const AJadgWalker& A, const AJadgWalker& B) { return A.PartyRank < B.PartyRank; });

	if (Frame != nullptr && Exploration != nullptr && InArena())
	{
		// L'arène : sa carte de Core est celle du combat, pas de l'exploration, qui garde la carte
		// quittée. Le combat pose chacun.
		bLinedUp = true;
		bCombatPending = !BeginCombat();
		FollowWithCamera();
		UE_LOG(LogJadg, Display, TEXT("[Groupe] %d membre(s) dans l'arène « %s »"), Members.Num(), *Frame->LevelId);
		return;
	}
	if (Frame != nullptr && Exploration != nullptr)
	{
		if (Exploration->EnterMap(Frame->LevelId, Frame->LevelsRoot))
		{
			GatherEntities();
			PlaceParty(Exploration->HeroCell());
		}
		else
		{
			// Une carte de Core qui ne se lit pas : la carte du moteur se joue sans elle.
			Frame = nullptr;
		}
	}
	if (Frame == nullptr)
	{
		// Sans carte de Core, le groupe reste où la scène le pose ; posé sur un seul point (une
		// arène vide), il se range comme à une arrivée.
		bLinedUp = Members.Num() < 2 || FVector::Dist2D(Members[0]->Feet(), Members[1]->Feet()) > 10.0;
	}
	ResetTrail();
	FollowWithCamera();
	UE_LOG(LogJadg, Display, TEXT("[Groupe] %d membre(s), %d entité(s) montrée(s), carte de Core « %s »"), Members.Num(),
		EntityActors.Num(), Frame != nullptr ? *Frame->LevelId : TEXT(""));
}

bool AJadgParty::BeginCombat()
{
	FString Wanted;
	if (Exploration->Encounter().IsEmpty() && FParse::Value(FCommandLine::Get(), TEXT("JadgRencontre="), Wanted))
	{
		Exploration->EngageEncounter(Wanted);
	}
	if (Exploration->Encounter().IsEmpty())
	{
		UE_LOG(LogJadg, Warning, TEXT("[Groupe] l'arène s'ouvre sans rencontre engagée : rien ne s'y joue"));
		return true;
	}
	uint64 Seed = 1;
	FParse::Value(FCommandLine::Get(), TEXT("JadgSeed="), Seed);
	AJadgCombat* Combat = AJadgCombat::Find(GetWorld());
	if (Combat == nullptr)
	{
		Combat = GetWorld()->SpawnActor<AJadgCombat>();
	}
	FString Error;
	if (Combat == nullptr || !Combat->Mount(Exploration->Encounter(), Seed, true, false, Error))
	{
		// Le maillage de navigation de l'arène se construit après son lancement : on réessaie.
		if (++CombatTries < MountTries)
		{
			return false;
		}
		UE_LOG(LogJadg, Error, TEXT("[Groupe] le combat « %s » ne se monte pas : %s ; la rencontre est quittée"), *Exploration->Encounter(), *Error);
		Exploration->LeaveEncounter();
		return true;
	}
	UE_LOG(LogJadg, Display, TEXT("[Groupe] combat monté à la tentative %d"), CombatTries + 1);
	// Une capture de l'arène fige le combat sur son déploiement.
	FString Ignored;
	Combat->SetPaused(FParse::Value(FCommandLine::Get(), TEXT("JadgCapture="), Ignored));
	return true;
}

void AJadgParty::GatherEntities()
{
	for (const FJadgEntity& Entity : Exploration->Entities())
	{
		EntityCells.Add(Entity.Id, Entity.Cell);
	}
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		FString Id;
		if (const AJadgWalker* Walker = Cast<AJadgWalker>(*It))
		{
			Id = Walker->EntityId;
		}
		for (const FName& Tag : It->Tags)
		{
			const FString Text = Tag.ToString();
			if (Text.StartsWith(EntityTagPrefix))
			{
				Id = Text.RightChop(EntityTagPrefix.Len());
			}
		}
		if (Id.IsEmpty())
		{
			continue;
		}
		const FIntPoint* Cell = EntityCells.Find(Id);
		if (Cell == nullptr)
		{
			UE_LOG(LogJadg, Error, TEXT("[Groupe] %s montre l'entité « %s », que la carte « %s » n'a pas"), *It->GetName(), *Id,
				*Frame->LevelId);
			continue;
		}
		EntityIds.Add(Id);
		EntityActors.Add(*It);
		// Un personnage se tient sur la case de son entité : c'est Core qui dit où.
		if (AJadgWalker* Walker = Cast<AJadgWalker>(*It))
		{
			const FVector Centre = Frame->ToWorld(FVector2D(Cell->X + 0.5, Cell->Y + 0.5));
			FVector Ground = Centre;
			OnNavigation(Centre, Ground);
			Walker->StandOn(Ground, Walker->GetActorRotation().Yaw);
		}
	}

	AJadgDayLight* DayLight = nullptr;
	for (TActorIterator<AJadgDayLight> It(GetWorld()); It; ++It)
	{
		DayLight = *It;
		break;
	}
	const TArray<FJadgLamp> Lamps = Exploration->Lamps();
	if (DayLight != nullptr)
	{
		for (const FJadgLamp& Lamp : Lamps)
		{
			const FVector Foot = Frame->ToWorld(Lamp.Cell);
			DayLight->AddLamp(Foot + FVector(0.0, 0.0, Lamp.HeightMetres * 100.0), Lamp.Colour, Lamp.RadiusMetres * 100.0f,
				Lamp.Intensity, Lamp.bAlways);
		}
	}
	else if (!Lamps.IsEmpty())
	{
		UE_LOG(LogJadg, Warning, TEXT("[Groupe] %d lumière(s) sur la carte, aucun AJadgDayLight pour les porter"), Lamps.Num());
	}
	RefreshEntities();
}

void AJadgParty::PlaceParty(const FVector2D& LeaderCell)
{
	AJadgWalker* Head = Leader();
	if (Head == nullptr)
	{
		return;
	}
	FVector Ground = WorldOf(LeaderCell, Frame != nullptr ? Frame->GetActorLocation().Z : Head->Feet().Z);
	// Sans maillage de navigation sous le meneur, la file ne peut pas encore se ranger : tout le
	// groupe attend sur son point, et `Tick` y revient.
	bLinedUp = OnNavigation(Ground, Ground);
	const float Yaw = Head->GetActorRotation().Yaw;
	Head->StandOn(Ground, Yaw);

	// Les suiveurs se rangent dans le dos du meneur, à une case l'un de l'autre, tant que le
	// maillage de navigation porte ; au-delà ils attendent sur le dernier point qui portait.
	const FVector Back = -FRotator(0.0f, Yaw, 0.0f).Vector();
	const double Spacing = core::FollowTrail::SPACING_CELLS * (Frame != nullptr ? Frame->CellSize : DefaultCell);
	FVector Last = Ground;
	bool bStacked = !bLinedUp;
	for (int32 Rank = 1; Rank < Members.Num(); ++Rank)
	{
		FVector Spot;
		if (OnNavigation(Ground + Back * Spacing * Rank, Spot))
		{
			Last = Spot;
		}
		bStacked = bStacked || FVector::Dist2D(Last, Ground) < 1.0;
		Members[Rank]->StandOn(Last, Yaw);
	}
	// Des personnages posés sur un même point ne se repoussent pas : la dérive déplacerait le meneur
	// de la case que Core lui donne. Leurs capsules se bloquent de nouveau une fois écartés (`Tick`).
	SetStacked(bStacked);
}

void AJadgParty::SetStacked(bool bStacked)
{
	bStackedNow = bStacked;
	for (const TObjectPtr<AJadgWalker>& Member : Members)
	{
		Member->SetBlocksCharacters(!bStacked);
	}
}

void AJadgParty::ResetTrail()
{
	std::vector<core::TrailPoint> Points;
	State->Ordered.Reset();
	for (const TObjectPtr<AJadgWalker>& Member : Members)
	{
		const FVector2D Cell = CellOf(Member->Feet());
		Points.emplace_back(static_cast<float>(Cell.X), static_cast<float>(Cell.Y));
		State->Ordered.Add(Cell);
	}
	State->Trail.reset(Points);
	State->Trail.keep((static_cast<float>(Members.Num()) + 1.0f) * core::FollowTrail::SPACING_CELLS);
}

void AJadgParty::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	AJadgWalker* Head = Leader();
	if (Exploration == nullptr || bTravelling)
	{
		return;
	}
	if (InArena())
	{
		if (bCombatPending)
		{
			bCombatPending = !BeginCombat();
		}
		// Le combat mène ; la carte quittée reste gelée tant que la rencontre tient.
		Exploration->Step(nullptr, false, DeltaSeconds);
		return;
	}

	if (!bLinedUp && Head != nullptr)
	{
		PlaceParty(CellOf(Head->Feet()));
		ResetTrail();
	}

	FVector2D Cell = FVector2D::ZeroVector;
	bool bInteract = bInteractAsked;
	bInteractAsked = false;
	if (Head != nullptr)
	{
		Cell = CellOf(Head->Feet());
		if (bPending)
		{
			// Le meneur sollicite ce qu'on lui a désigné dès qu'il l'a à portée ; arrivé sans
			// l'avoir, il sollicite ce que Core désigne là où il est.
			FIntPoint Aimed;
			FString Prompt;
			const bool bInReach = Exploration->Target(Aimed, Prompt) && Aimed == PendingCell;
			if (bInReach || !Head->IsWalking())
			{
				bInteract = true;
				bPending = false;
				Head->StopWalking();
			}
		}
	}

	if (!Exploration->Encounter().IsEmpty() && !Exploration->InDialogue())
	{
		// La bascule vers le combat : la carte d'arène (LOT-1017).
		if (FPackageName::DoesPackageExist(ArenaMap))
		{
			if (Head != nullptr)
			{
				Head->StopWalking();
			}
			Open(ArenaMap);
			return;
		}
		UE_LOG(LogJadg, Error, TEXT("[Groupe] la carte d'arène « %s » n'existe pas : la rencontre est quittée"), *ArenaMap);
		Exploration->LeaveEncounter();
	}

	const bool bOnCoreMap = Frame != nullptr && Head != nullptr;
	const TArray<FJadgEvent> Events = Exploration->Step(bOnCoreMap ? &Cell : nullptr, bInteract, DeltaSeconds);
	for (const FJadgEvent& Event : Events)
	{
		if (Event.Kind == EJadgEventKind::MapEntered)
		{
			Travel(Event.Value);
			return;
		}
	}
	if (Head == nullptr)
	{
		return;
	}
	if (Exploration->InDialogue())
	{
		Head->StopWalking();
		bPending = false;
	}

	State->Trail.record(core::TrailPoint{static_cast<float>(Cell.X), static_cast<float>(Cell.Y)});
	FollowLeader();
	if (bStackedNow)
	{
		bool bApart = true;
		for (int32 A = 0; A < Members.Num(); ++A)
		{
			for (int32 B = A + 1; B < Members.Num(); ++B)
			{
				const float Gap = Members[A]->GetCapsuleComponent()->GetScaledCapsuleRadius() + Members[B]->GetCapsuleComponent()->GetScaledCapsuleRadius();
				bApart = bApart && FVector::Dist2D(Members[A]->Feet(), Members[B]->Feet()) > Gap + 5.0;
			}
		}
		if (bApart)
		{
			SetStacked(false);
		}
	}
	if (Frame != nullptr)
	{
		RefreshEntities();
	}
}

void AJadgParty::FollowLeader()
{
	for (int32 Rank = 1; Rank < Members.Num(); ++Rank)
	{
		AJadgWalker* Member = Members[Rank];
		const core::TrailPoint Point = State->Trail.pointBehind(static_cast<float>(Rank) * core::FollowTrail::SPACING_CELLS);
		const FVector2D Wanted(Point.x, Point.y);
		if (FVector2D::Distance(Wanted, State->Ordered[Rank]) < ReorderCells)
		{
			continue;
		}
		State->Ordered[Rank] = Wanted;
		const FVector Feet = Member->Feet();
		FVector Goal = WorldOf(Wanted, Feet.Z);
		if (FVector::Dist2D(Goal, Feet) > CloseEnough && OnNavigation(Goal, Goal))
		{
			Member->WalkTo(Goal, 10.0f);
		}
	}
}

void AJadgParty::OrderWalk(const FVector& Destination)
{
	AJadgWalker* Head = Leader();
	if (Head == nullptr || (Exploration != nullptr && Exploration->InDialogue()))
	{
		return;
	}
	// Le point cliqué peut être un mur ou un toit : il est ramené sur le maillage de navigation.
	FVector Ground;
	if (OnNavigation(Destination, Ground))
	{
		bPending = false;
		Head->WalkTo(Ground);
	}
}

AActor* AJadgParty::EntityActor(const FString& EntityId) const
{
	const int32 Index = EntityIds.IndexOfByKey(EntityId);
	return Index != INDEX_NONE ? EntityActors[Index].Get() : nullptr;
}

FVector AJadgParty::PointOf(const FVector2D& Cell) const
{
	const AJadgWalker* Head = Leader();
	return WorldOf(Cell, Head != nullptr ? Head->Feet().Z : 0.0);
}

bool AJadgParty::IsEntity(const AActor* Actor) const
{
	return Actor != nullptr && EntityActors.Contains(Actor);
}

void AJadgParty::OrderInteract(const AActor* Target)
{
	AJadgWalker* Head = Leader();
	const int32 Index = EntityActors.IndexOfByKey(Target);
	if (Head == nullptr || Frame == nullptr || Index == INDEX_NONE || Exploration->InDialogue())
	{
		return;
	}
	const FIntPoint Cell = EntityCells[EntityIds[Index]];
	const FVector Feet = Head->Feet();
	const FVector There = WorldOf(FVector2D(Cell.X + 0.5, Cell.Y + 0.5), Feet.Z);
	FVector Toward = Feet - There;
	Toward.Z = 0.0;
	FVector Ground;
	if (OnNavigation(There + Toward.GetSafeNormal() * ApproachCells * Frame->CellSize, Ground))
	{
		Head->WalkTo(Ground, 10.0f);
	}
	bPending = true;
	PendingCell = Cell;
}

void AJadgParty::Interact()
{
	bInteractAsked = true;
}

void AJadgParty::RotateLeader()
{
	if (Members.Num() < 2 || Exploration == nullptr || Exploration->InDialogue())
	{
		return;
	}
	// Le meneur va en queue (EX-EXP-014) ; l'ordre du groupe de Core suit.
	const TObjectPtr<AJadgWalker> Former = Members[0];
	Members.RemoveAt(0);
	Members.Add(Former);
	Former->StopWalking();
	Exploration->RotateLeader();
	if (Frame != nullptr)
	{
		Exploration->PlaceHero(CellOf(Members[0]->Feet()));
	}
	bPending = false;
	ResetTrail();
	FollowWithCamera();
}

void AJadgParty::Travel(const FString& MapId)
{
	if (Frame != nullptr && MapId == Frame->LevelId)
	{
		// Un portail qui ramène sur la même carte : le groupe se pose au point d'arrivée.
		PlaceParty(Exploration->HeroCell());
		ResetTrail();
		FollowWithCamera();
		return;
	}
	const FString Package = AJadgMapFrame::MapPackage(MapId);
	if (!FPackageName::DoesPackageExist(Package))
	{
		UE_LOG(LogJadg, Error, TEXT("[Groupe] la carte « %s » n'a pas de carte du moteur (%s) : construire sa scène"), *MapId,
			*Package);
		return;
	}
	UE_LOG(LogJadg, Display, TEXT("[Groupe] portail vers « %s »"), *MapId);
	Open(Package);
}

void AJadgParty::Open(const FString& Package)
{
	UE_LOG(LogJadg, Display, TEXT("[Groupe] carte du moteur : %s"), *Package);
	bTravelling = true;
	UGameplayStatics::OpenLevel(this, FName(*Package));
}

bool AJadgParty::InArena() const
{
	return !ArenaMap.IsEmpty() && GetWorld()->GetOutermost()->GetName() == ArenaMap;
}

void AJadgParty::ReturnFromArena()
{
	const FString MapId = Exploration != nullptr ? Exploration->MapId() : FString();
	const FString Package = AJadgMapFrame::MapPackage(MapId);
	if (MapId.IsEmpty() || !FPackageName::DoesPackageExist(Package))
	{
		UE_LOG(LogJadg, Warning, TEXT("[Groupe] pas de carte quittée où revenir (« %s ») : le groupe reste dans l'arène"), *MapId);
		return;
	}
	Open(Package);
}

void AJadgParty::RefreshEntities()
{
	for (int32 Index = 0; Index < EntityActors.Num(); ++Index)
	{
		AActor* Actor = EntityActors[Index];
		const bool bPresent = Exploration->IsPresent(EntityIds[Index]);
		if (Actor != nullptr && Actor->IsHidden() == bPresent)
		{
			Actor->SetActorHiddenInGame(!bPresent);
			Actor->SetActorEnableCollision(bPresent);
		}
	}

	// Le contour désigne ce que le meneur solliciterait maintenant.
	FString Wanted;
	FIntPoint Aimed;
	FString Prompt;
	if (Exploration->Target(Aimed, Prompt))
	{
		for (const FString& Id : EntityIds)
		{
			if (EntityCells[Id] == Aimed && Exploration->IsPresent(Id))
			{
				Wanted = Id;
				break;
			}
		}
	}
	if (Wanted != OutlinedId)
	{
		SetOutlined(OutlinedId, false);
		SetOutlined(Wanted, true);
		OutlinedId = Wanted;
	}
}

void AJadgParty::SetOutlined(const FString& EntityId, bool bOutlined)
{
	if (EntityId.IsEmpty())
	{
		return;
	}
	for (int32 Index = 0; Index < EntityActors.Num(); ++Index)
	{
		AActor* Actor = EntityActors[Index];
		if (Actor == nullptr || EntityIds[Index] != EntityId)
		{
			continue;
		}
		if (AJadgWalker* Walker = Cast<AJadgWalker>(Actor))
		{
			Walker->SetOutlined(bOutlined);
			continue;
		}
		TInlineComponentArray<UPrimitiveComponent*> Parts(Actor);
		for (UPrimitiveComponent* Part : Parts)
		{
			Part->SetRenderCustomDepth(bOutlined);
			Part->SetCustomDepthStencilValue(bOutlined ? 1 : 0);
		}
	}
}

void AJadgParty::FollowWithCamera() const
{
	AJadgWalker* Head = Leader();
	const APlayerController* Player = GetWorld()->GetFirstPlayerController();
	AJadgCameraPawn* View = Player != nullptr ? Cast<AJadgCameraPawn>(Player->GetPawn()) : nullptr;
	if (Head != nullptr && View != nullptr)
	{
		View->SetActorLocation(Head->GetActorLocation());
		View->Follow(Head);
	}
}
