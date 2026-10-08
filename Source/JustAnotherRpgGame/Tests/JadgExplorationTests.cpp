// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Les tests d'automatisation de l'exploration (LOT-1016) : ce que le moteur fait des règles de
// Core quand c'est lui qui déplace le meneur. Sans fenêtre ni processeur graphique, comme ceux du
// socle (`JadgSocleTests.cpp`) :
//
//     UnrealEditor-Cmd.exe <projet>.uproject -ExecCmds="Automation RunTests Jadg.Exploration; Quit" -nullrhi
//
// Les règles elles-mêmes — un portail se franchit en y arrivant, une réponse à jet disparaît une
// fois ratée — sont testées hors du moteur (`Source/Test/Unit/Core`). Aucun en-tête de Core ici :
// ces tests passent par le sous-système que le jeu emploie (`UJadgExploration`).

#include "Characters/JadgParty.h"
#include "Characters/JadgWalker.h"
#include "Components/LocalLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/StaticMesh.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Game/JadgExploration.h"
#include "Game/JadgGameInstance.h"
#include "Game/JadgGameMode.h"
#include "HAL/FileManager.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "NavMesh/NavMeshBoundsVolume.h"
#include "NavigationSystem.h"
#include "Player/JadgCameraPawn.h"
#include "Player/JadgControls.h"
#include "Scene/JadgSceneBuild.h"
#include "World/JadgDayLight.h"
#include "World/JadgMapFrame.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags ExplorationFlags = EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::EngineFilter;

	const TCHAR* const TrialLevels = TEXT("Source/Test/Fixtures/Exploration/Levels");
	const TCHAR* const Martpart = TEXT("central-empire/capital/martpart");
	const TCHAR* const Arenarea = TEXT("central-empire/capital/arenarea");
	const TCHAR* const Undercroft = TEXT("central-empire/capital/arenarea/arena-of-fate/undercroft");

	/// Une partie neuve sous l'instance du jeu, comme au lancement, et son monde vide.
	struct FGame
	{
		UJadgGameInstance* Instance = nullptr;
		UJadgExploration* Exploration = nullptr;
		UWorld* World = nullptr;
		bool bPlaying = false;

		FGame()
		{
			static int32 Count = 0;
			Instance = NewObject<UJadgGameInstance>(GEngine);
			Instance->InitializeStandalone(*FString::Printf(TEXT("JadgExploration%d"), ++Count));
			World = Instance->GetWorld();
			Exploration = Instance->GetSubsystem<UJadgExploration>();
		}

		/// Fait jouer le monde sous le mode de jeu du jeu : les acteurs déjà créés commencent.
		void Play()
		{
			World->GetWorldSettings()->DefaultGameMode = AJadgGameMode::StaticClass();
			const FURL Url;
			World->SetGameMode(Url);
			World->InitializeActorsForPlay(Url);
			World->BeginPlay();
			bPlaying = true;
		}

		void Tick(int32 Frames, float Seconds = 1.0f / 30.0f) const
		{
			for (int32 Frame = 0; Frame < Frames; ++Frame)
			{
				World->Tick(LEVELTICK_All, Seconds);
				++GFrameCounter;
			}
		}

		~FGame()
		{
			if (bPlaying)
			{
				World->EndPlay(EEndPlayReason::Quit);
			}
			Instance->Shutdown();
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}
	};

	FVector2D Centre(int32 Column, int32 Row)
	{
		return FVector2D(Column + 0.5, Row + 0.5);
	}

	bool Has(const TArray<FJadgEvent>& Events, EJadgEventKind Kind, const FString& Value)
	{
		return Events.ContainsByPredicate([&](const FJadgEvent& Event) { return Event.Kind == Kind && Event.Value == Value; });
	}

	/// Mène le meneur depuis @p From, par dixièmes de case dans la direction @p Direction, au plus
	/// @p Cells cases, jusqu'à l'événement attendu. Faux s'il ne vient pas.
	bool WalkUntil(UJadgExploration& Exploration, const FVector2D& From, const FVector2D& Direction, EJadgEventKind Kind,
		const FString& Value, int32 Cells = 3)
	{
		Exploration.PlaceHero(From);
		for (int32 Step = 1; Step <= Cells * 10; ++Step)
		{
			const FVector2D Here = From + Direction * (0.1 * Step);
			if (Has(Exploration.Step(&Here, false, 1.0f / 30.0f), Kind, Value))
			{
				return true;
			}
		}
		return false;
	}

	/// Le meneur en @p From se tourne vers @p Direction et interagit. Rend le dialogue ouvert.
	bool TalkFrom(UJadgExploration& Exploration, const FVector2D& From, const FVector2D& Direction, const FString& Dialogue)
	{
		Exploration.PlaceHero(From - Direction * 0.05);
		Exploration.Step(&From, false, 1.0f / 30.0f);
		return Has(Exploration.Step(&From, true, 1.0f / 30.0f), EJadgEventKind::Dialogue, Dialogue) && Exploration.InDialogue();
	}

	/// Le meneur en @p From se tourne vers @p Direction et sollicite ce qu'il a à portée. Vrai si
	/// l'interaction a eu lieu sur une entité de la famille @p Type.
	bool Use(UJadgExploration& Exploration, const FVector2D& From, const FVector2D& Direction, const FString& Type)
	{
		Exploration.PlaceHero(From - Direction * 0.05);
		Exploration.Step(&From, false, 1.0f / 30.0f);
		return Has(Exploration.Step(&From, true, 1.0f / 30.0f), EJadgEventKind::Interacted, Type);
	}

	/// Vrai si @p Point est dans le volume du cube du moteur que porte @p Block.
	bool Inside(const AStaticMeshActor& Block, const FVector& Point)
	{
		const FVector Local = Block.GetActorTransform().InverseTransformPosition(Point);
		return FMath::Abs(Local.X) < 50.0 && FMath::Abs(Local.Y) < 50.0 && FMath::Abs(Local.Z) < 50.0;
	}

	/// Un cube du moteur posé dans le monde, avant ou après son lancement.
	AStaticMeshActor* Block(UWorld* World, const FVector& Centre, const FRotator& Rotation, const FVector& Scale)
	{
		UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
		AStaticMeshActor* Actor = World->SpawnActor<AStaticMeshActor>(Centre, Rotation);
		if (Cube == nullptr || Actor == nullptr)
		{
			return nullptr;
		}
		Actor->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
		Actor->GetStaticMeshComponent()->SetStaticMesh(Cube);
		Actor->SetActorScale3D(Scale);
		return Actor;
	}

	/// Donne les réponses @p Answers, les répliques à une seule suite se passant d'elles-mêmes.
	/// Faux si une réponse n'est pas proposée ou si la conversation ne se termine pas.
	bool Converse(UJadgExploration& Exploration, const TArray<FString>& Answers)
	{
		int32 Next = 0;
		for (int32 Guard = 0; Guard < 20 && Exploration.InDialogue(); ++Guard)
		{
			const TArray<FJadgChoice> Offered = Exploration.Choices();
			if (Offered.Num() == 1 && Offered[0].Id == TEXT("continue"))
			{
				Exploration.Choose(0);
			}
			else if (!Answers.IsValidIndex(Next) || !Exploration.ChooseById(Answers[Next++]))
			{
				return false;
			}
		}
		return !Exploration.InDialogue() && Next == Answers.Num();
	}

	/// De Market Gate au garde du parvis : le début commun aux issues de la quête.
	bool ReachTheGuard(FAutomationTestBase& Test, UJadgExploration& Exploration, uint64 Seed)
	{
		bool bOk = Test.TestTrue(TEXT("Martpart se lit"), Exploration.EnterMap(Martpart, FString()));
		bOk &= Test.TestEqual(TEXT("la quête n'est pas connue"), Exploration.Flag(TEXT("quete.pommes")), FString(TEXT("inconnue")));
		bOk &= Test.TestTrue(TEXT("la mère interpelle"), TalkFrom(Exploration, Centre(28, 36), FVector2D(1.0, 0.0), TEXT("mere")));
		bOk &= Test.TestTrue(TEXT("accepter se dit"), Converse(Exploration, {TEXT("accepter")}));
		bOk &= Test.TestTrue(TEXT("la quête s'ouvre"),
			Has(Exploration.Step(nullptr, false, 1.0f / 30.0f), EJadgEventKind::QuestAdvanced, TEXT("pommes/acceptee")));
		bOk &= Test.TestTrue(TEXT("Stravian Avenue mène à Arenarea"),
			WalkUntil(Exploration, Centre(8, 1), FVector2D(0.0, -1.0), EJadgEventKind::MapEntered, Arenarea));
		// La graine du jet se fixe avant que le garde ne parle.
		Exploration.SetSeed(Seed);
		bOk &= Test.TestTrue(TEXT("le parvis déclenche le garde"),
			WalkUntil(Exploration, Centre(59, 37), FVector2D(1.0, 0.0), EJadgEventKind::Dialogue, TEXT("garde")));
		return bOk && Exploration.InDialogue();
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgExplorationTrialMapsTest, "Jadg.Exploration.CartesDEssai", ExplorationFlags)

/// Les deux cartes d'essai se lisent, leurs entités et leur lumière avec elles ; un coffre ne
/// s'ouvre qu'une fois, un panneau se relit ; celui qui parle a son portrait ; le portail de l'une
/// dépose au point d'arrivée de l'autre ; un dialogue engage une rencontre, qui gèle la carte.
bool FJadgExplorationTrialMapsTest::RunTest(const FString& Parameters)
{
	FGame Game;
	UJadgExploration& Exploration = *Game.Exploration;
	for (const FString& Error : Exploration.LoadErrors())
	{
		AddError(Error);
	}
	TestEqual(TEXT("le groupe préformé compte quatre membres"), Exploration.Members().Num(), 4);

	if (!TestTrue(TEXT("essai/etals se lit"), Exploration.EnterMap(TEXT("essai/etals"), TrialLevels)))
	{
		return false;
	}
	TestEqual(TEXT("le meneur est à l'entrée"), Exploration.HeroCell(), Centre(3, 8));
	TestEqual(TEXT("les entités de la carte"), Exploration.Entities().Num(), 7);
	TestEqual(TEXT("une lanterne"), Exploration.Lamps().Num(), 1);
	TestTrue(TEXT("la mère est à son étal"), Exploration.IsPresent(TEXT("e1")));
	TestFalse(TEXT("l'enfant n'y est pas encore"), Exploration.IsPresent(TEXT("e2")));

	// Le coffre (7, 6) ne s'ouvre qu'une fois ; le panneau (4, 9) se relit.
	TestFalse(TEXT("le coffre est fermé"), Exploration.IsConsumed(TEXT("e6")));
	TestTrue(TEXT("le coffre s'ouvre"), Use(Exploration, Centre(6, 6), FVector2D(1.0, 0.0), TEXT("chest")));
	TestTrue(TEXT("le coffre est ouvert"), Exploration.IsConsumed(TEXT("e6")));
	FIntPoint Aimed;
	FString Prompt;
	TestFalse(TEXT("un coffre ouvert n'est plus désigné"), Exploration.Target(Aimed, Prompt));
	TestFalse(TEXT("il ne s'ouvre pas deux fois"), Use(Exploration, Centre(6, 6), FVector2D(1.0, 0.0), TEXT("chest")));
	TestTrue(TEXT("le panneau se lit"), Use(Exploration, Centre(3, 9), FVector2D(1.0, 0.0), TEXT("sign")));
	TestTrue(TEXT("il se relit"), Use(Exploration, Centre(3, 9), FVector2D(1.0, 0.0), TEXT("sign")));
	TestFalse(TEXT("un panneau ne se consomme pas"), Exploration.IsConsumed(TEXT("e7")));

	// Celle qui parle a son portrait : celui de sa figurine, si les kits sont sur le poste.
	if (TestTrue(TEXT("la mère répond"), TalkFrom(Exploration, Centre(4, 2), FVector2D(-1.0, 0.0), TEXT("mere"))))
	{
		const FString Portrait = Exploration.SpeakerPortrait();
		if (Portrait.IsEmpty())
		{
			AddInfo(TEXT("pas de portrait : les kits ne sont pas sur ce poste"));
		}
		else
		{
			TestTrue(TEXT("le portrait est celui de la figurine de la mère"), Portrait.EndsWith(TEXT("/Characters/mother/portrait.png")));
			TestTrue(TEXT("le fichier du portrait existe"), IFileManager::Get().FileExists(*Portrait));
		}
		TestTrue(TEXT("refuser referme la conversation"), Converse(Exploration, {TEXT("refuser")}));
		TestTrue(TEXT("le portrait part avec elle"), Exploration.SpeakerPortrait().IsEmpty());
	}

	TestTrue(TEXT("le portail de l'est mène au parvis"),
		WalkUntil(Exploration, Centre(13, 5), FVector2D(1.0, 0.0), EJadgEventKind::MapEntered, TEXT("essai/parvis")));
	TestEqual(TEXT("la carte courante est le parvis"), Exploration.MapId(), FString(TEXT("essai/parvis")));
	TestEqual(TEXT("le meneur est au point d'arrivée"), Exploration.HeroCell(), Centre(2, 5));

	// La bascule vers le combat : le maître d'arène (12, 7) engage une rencontre, la carte se gèle.
	if (TestTrue(TEXT("le maître d'arène répond"), TalkFrom(Exploration, Centre(11, 7), FVector2D(1.0, 0.0), TEXT("maitre-arene"))))
	{
		TestTrue(TEXT("combattre se dit"), Converse(Exploration, {TEXT("combattre")}));
		TestEqual(TEXT("la rencontre est engagée"), Exploration.Encounter(), FString(TEXT("arene-bandits")));
		const float Hour = Exploration.Minutes();
		const FVector2D Away = Centre(9, 7);
		Exploration.Step(&Away, false, 60.0f);
		TestEqual(TEXT("l'heure ne passe pas pendant la rencontre"), Exploration.Minutes(), Hour);
		TestEqual(TEXT("la carte est gelée : le meneur n'y bouge pas"), Exploration.HeroCell(), Centre(11, 7));
		Exploration.LeaveEncounter();
		TestTrue(TEXT("la rencontre se quitte"), Exploration.Encounter().IsEmpty());
		Exploration.Step(&Away, false, 60.0f);
		TestEqual(TEXT("la carte reprend"), Exploration.HeroCell(), Away);
	}

	// Le passage du nord est condamné, celui de l'est attend que l'enfant soit libre.
	TestTrue(TEXT("le passage condamné ne s'ouvre pas"),
		WalkUntil(Exploration, Centre(7, 2), FVector2D(0.0, -1.0), EJadgEventKind::PortalSealed, FString()));
	TestTrue(TEXT("le passage de l'est est fermé"),
		WalkUntil(Exploration, Centre(13, 9), FVector2D(1.0, 0.0), EJadgEventKind::PortalLocked,
			TEXT("quest/pommes/step/enfant-libere")));
	TestEqual(TEXT("on est resté sur le parvis"), Exploration.MapId(), FString(TEXT("essai/parvis")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgExplorationAppleQuestTest, "Jadg.Exploration.QueteDesPommes", ExplorationFlags)

/// « Des pommes pour l'arène », hors combat, sur le contenu livré : la mère, le portail, le garde
/// et son jet de Persuasion, puis chacune des deux suites, une graine par issue.
bool FJadgExplorationAppleQuestTest::RunTest(const FString& Parameters)
{
	// L'issue du jet ne tient qu'à la graine : on cherche la première qui réussit et la première
	// qui échoue, chacune sur une partie neuve.
	bool bSpoken = false;
	bool bCondemned = false;
	for (uint64 Seed = 1; Seed <= 40 && !(bSpoken && bCondemned); ++Seed)
	{
		FGame Game;
		UJadgExploration& Exploration = *Game.Exploration;
		if (!ReachTheGuard(*this, Exploration, Seed))
		{
			return false;
		}
		const TArray<FJadgChoice> Offered = Exploration.Choices();
		const FJadgChoice* Persuade = Offered.FindByPredicate([](const FJadgChoice& Choice) { return Choice.Id == TEXT("convaincre"); });
		if (!TestNotNull(TEXT("le garde laisse plaider"), Persuade))
		{
			return false;
		}
		TestTrue(TEXT("la réponse annonce son jet"), !Persuade->Skill.IsEmpty() && Persuade->Dc > 0);
		Exploration.ChooseById(TEXT("convaincre"));
		const FString After = Exploration.Flag(TEXT("quete.pommes"));
		AddInfo(FString::Printf(TEXT("graine %llu : %s"), Seed, *After));

		if (After == TEXT("enfant-libere") && !bSpoken)
		{
			// La voie de la parole : le garde et l'enfant quittent le parvis, l'enfant rentre.
			bSpoken = true;
			TestTrue(TEXT("le garde prend congé"), Converse(Exploration, {}));
			TestTrue(TEXT("la quête dit l'enfant libre"),
				Has(Exploration.Step(nullptr, false, 1.0f / 30.0f), EJadgEventKind::QuestAdvanced, TEXT("pommes/enfant-libere")));
			TestFalse(TEXT("le garde a quitté le parvis"), Exploration.IsPresent(TEXT("e5")));
			TestFalse(TEXT("l'enfant aussi"), Exploration.IsPresent(TEXT("e6")));
			TestTrue(TEXT("Herofate Avenue ramène à Martpart"),
				WalkUntil(Exploration, Centre(116, 85), FVector2D(0.0, 1.0), EJadgEventKind::MapEntered, Martpart));
			TestTrue(TEXT("l'enfant est auprès de sa mère"), Exploration.IsPresent(TEXT("e2")));
			TestTrue(TEXT("la mère attend"), TalkFrom(Exploration, Centre(28, 36), FVector2D(1.0, 0.0), TEXT("mere")));
			TestTrue(TEXT("les retrouvailles"), Converse(Exploration, {TEXT("sourire")}));
			TestTrue(TEXT("la démo se clôt par la parole"), Exploration.Requests().Contains(TEXT("ending:parole")));
			TestTrue(TEXT("la quête est rendue"),
				Has(Exploration.Step(nullptr, false, 1.0f / 30.0f), EJadgEventKind::QuestAdvanced, TEXT("pommes/rendue")));
		}
		else if (After == TEXT("persuasion-echouee") && !bCondemned)
		{
			// La voie de l'arène, jusqu'à sa porte : la réponse ratée a disparu, il reste à endosser.
			bCondemned = true;
			TestFalse(TEXT("un jet raté ne se retente pas"),
				Exploration.Choices().ContainsByPredicate([](const FJadgChoice& Choice) { return Choice.Id == TEXT("convaincre"); }));
			TestFalse(TEXT("le jet s'annonce au joueur"), Exploration.LastCheck().IsEmpty());
			TestTrue(TEXT("endosser le crime"), Converse(Exploration, {TEXT("endosser")}));
			TestEqual(TEXT("condamné"), Exploration.Flag(TEXT("quete.pommes")), FString(TEXT("condamne")));
			TestTrue(TEXT("l'escalier de l'arène mène au vestiaire"),
				WalkUntil(Exploration, Centre(65, 34), FVector2D(0.0, -1.0), EJadgEventKind::MapEntered, Undercroft));
			TestEqual(TEXT("on arrive au vestibule"), Exploration.HeroCell(), Centre(16, 19));
		}
	}
	TestTrue(TEXT("une graine au moins réussit le jet de Persuasion"), bSpoken);
	TestTrue(TEXT("une graine au moins le rate"), bCondemned);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgExplorationClockTest, "Jadg.Exploration.HeureDuMonde", ExplorationFlags)

/// Une heure du monde par minute réelle ; réglée, elle se fige ; les lumières de nuit la suivent
/// et portent une ombre.
bool FJadgExplorationClockTest::RunTest(const FString& Parameters)
{
	FGame Game;
	UJadgExploration& Exploration = *Game.Exploration;
	TestEqual(TEXT("une partie neuve commence à 10 h"), Exploration.Minutes(), 600.0f);
	Exploration.Step(nullptr, false, 60.0f);
	TestEqual(TEXT("soixante secondes font une heure"), Exploration.Minutes(), 660.0f);

	AJadgDayLight* DayLight = Game.World->SpawnActor<AJadgDayLight>();
	Game.Play();
	if (!TestNotNull(TEXT("l'acteur du jour"), DayLight))
	{
		return false;
	}
	TestEqual(TEXT("l'acteur du jour lit l'heure du monde"), DayLight->GetMinutes(), 660.0f);

	const ULocalLightComponent* Lamp = DayLight->AddLamp(FVector(0.0, 0.0, 220.0), FLinearColor(1.0f, 0.75f, 0.48f), 600.0f, 1.0f, false);
	const ULocalLightComponent* Fire = DayLight->AddLamp(FVector(300.0, 0.0, 220.0), FLinearColor(1.0f, 0.75f, 0.48f), 600.0f, 1.0f, true);
	if (!TestNotNull(TEXT("une lumière de nuit"), Lamp) || !TestNotNull(TEXT("un feu"), Fire))
	{
		return false;
	}
	TestEqual(TEXT("seule la lumière de nuit suit l'heure"), DayLight->LampCount(), 1);
	TestTrue(TEXT("une lumière de nuit porte une ombre"), Lamp->CastShadows);
	TestFalse(TEXT("un feu n'en porte pas"), Fire->CastShadows);

	DayLight->SetMinutes(12.0f * 60.0f);
	TestEqual(TEXT("à midi la lumière de nuit est éteinte"), Lamp->Intensity, 0.0f);
	TestEqual(TEXT("le feu reste allumé"), Fire->Intensity, DayLight->FireCandelas);
	DayLight->SetMinutes(22.0f * 60.0f);
	TestEqual(TEXT("à 22 h elle est allumée"), Lamp->Intensity, DayLight->LampCandelas);

	// Réglée, l'heure est figée : une capture ne change pas de lumière en cours de route.
	Exploration.Step(nullptr, false, 60.0f);
	TestEqual(TEXT("l'heure réglée ne passe plus"), Exploration.Minutes(), 1320.0f);
	DayLight->SetRunning(true);
	Exploration.Step(nullptr, false, 60.0f);
	Game.Tick(1);
	TestEqual(TEXT("relancée, elle reprend"), DayLight->GetMinutes(), 1380.0f, 0.5f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgExplorationCameraTest, "Jadg.Exploration.Camera", ExplorationFlags)

/// La caméra tient ses bornes, et un mur entre elle et le point visé la rapproche.
bool FJadgExplorationCameraTest::RunTest(const FString& Parameters)
{
	FGame Game;
	AJadgCameraPawn* View = Game.World->SpawnActor<AJadgCameraPawn>(FVector(0.0, 0.0, 100.0), FRotator::ZeroRotator);
	AActor* Anchor = Game.World->SpawnActor<AActor>(AActor::StaticClass(), FTransform(FVector(0.0, 0.0, 100.0)));
	Game.Play();
	if (!TestNotNull(TEXT("la caméra"), View))
	{
		return false;
	}

	View->AddPitch(500.0f);
	TestEqual(TEXT("l'inclinaison s'arrête à sa borne haute"), View->GetViewPitch(), View->MaxPitch);
	View->AddPitch(-500.0f);
	TestEqual(TEXT("l'inclinaison s'arrête à sa borne basse"), View->GetViewPitch(), View->MinPitch);
	View->Zoom(0.0001f);
	TestEqual(TEXT("le zoom s'arrête à la distance la plus courte"), View->GetViewDistance(), View->MinDistance);
	View->Zoom(100000.0f);
	TestEqual(TEXT("le zoom s'arrête à la distance la plus longue"), View->GetViewDistance(), View->MaxDistance);
	View->AddYaw(725.0f);
	TestEqual(TEXT("la rotation est libre"), View->GetViewYaw(), 5.0f);

	// Sans décor, la caméra est au bout de son bras.
	View->SetView(FVector(0.0, 0.0, 100.0), 0.0f, 40.0f, 1600.0f);
	View->Follow(Anchor);
	Game.Tick(3);
	const FVector Target = View->GetActorLocation();
	TestTrue(TEXT("sans décor, la caméra est à sa distance"), FMath::IsNearlyEqual(FVector::Dist(View->GetCameraLocation(), Target), 1600.0, 5.0));

	// Un mur dressé entre le point visé et la caméra : elle passe devant lui.
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	AStaticMeshActor* Wall = Game.World->SpawnActor<AStaticMeshActor>(FVector(-600.0, 0.0, 600.0), FRotator::ZeroRotator);
	if (!TestNotNull(TEXT("le cube du moteur"), Cube) || !TestNotNull(TEXT("le mur"), Wall))
	{
		return false;
	}
	Wall->GetStaticMeshComponent()->SetMobility(EComponentMobility::Movable);
	Wall->GetStaticMeshComponent()->SetStaticMesh(Cube);
	Wall->SetActorScale3D(FVector(0.2, 30.0, 30.0));
	Game.Tick(3);
	const double Behind = FVector::Dist(View->GetCameraLocation(), Target);
	TestTrue(*FString::Printf(TEXT("un mur rapproche la caméra (%.0f cm)"), Behind), Behind < 800.0);
	TestTrue(TEXT("la caméra reste du côté du point visé"), View->GetCameraLocation().X > -600.0);

	// Un cadrage de capture vise à travers le décor.
	View->SetView(Target, 0.0f, 40.0f, 1600.0f);
	Game.Tick(3);
	TestTrue(TEXT("un cadrage traverse le mur"), FMath::IsNearlyEqual(FVector::Dist(View->GetCameraLocation(), Target), 1600.0, 5.0));

	// Le sol : un talus qui monte derrière le point visé, plus raide que le regard. La caméra, qui
	// serait dessous au bout de son bras, reste au-dessus.
	Wall->Destroy();
	const AStaticMeshActor* Bank = Block(Game.World, FVector(-800.0, 0.0, 750.0), FRotator(51.3, 180.0, 0.0), FVector(22.0, 30.0, 0.2));
	if (!TestNotNull(TEXT("le talus"), Bank))
	{
		return false;
	}
	TestTrue(TEXT("au bout de son bras, la caméra serait sous le talus"), Bank->GetActorTransform().InverseTransformPosition(View->GetCameraLocation()).Z < -50.0);
	View->Follow(Anchor);
	Game.Tick(3);
	const FVector OnBank = View->GetCameraLocation();
	TestTrue(*FString::Printf(TEXT("le talus rapproche la caméra (%.0f cm)"), FVector::Dist(OnBank, Target)), FVector::Dist(OnBank, Target) < 1200.0);
	TestFalse(TEXT("la caméra n'est pas dans le sol"), Inside(*Bank, OnBank));
	TestTrue(TEXT("la caméra est au-dessus du sol"), Bank->GetActorTransform().InverseTransformPosition(OnBank).Z > 50.0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgExplorationControlsTest, "Jadg.Exploration.Commandes", ExplorationFlags)

/// Les commandes se lisent dans leur fichier texte : chaque touche nomme une commande connue.
bool FJadgExplorationControlsTest::RunTest(const FString& Parameters)
{
	const UJadgControls* Controls = GetDefault<UJadgControls>();
	TestTrue(TEXT("des touches sont déclarées"), Controls->Bindings.Num() > 0);
	TSet<FName> Bound;
	for (const FJadgBinding& Binding : Controls->Bindings)
	{
		TestTrue(*FString::Printf(TEXT("« %s » est une commande du jeu"), *Binding.Command.ToString()), UJadgControls::IsKnown(Binding.Command));
		TestTrue(*FString::Printf(TEXT("la touche de « %s » existe"), *Binding.Command.ToString()), Binding.Key.IsValid());
		Bound.Add(Binding.Command);
	}
	for (const TCHAR* Needed : {TEXT("Walk"), TEXT("Interact"), TEXT("NextLeader"), TEXT("Recenter"), TEXT("Turn"), TEXT("Tilt"), TEXT("Zoom")})
	{
		TestTrue(*FString::Printf(TEXT("« %s » a une touche"), Needed), Bound.Contains(FName(Needed)));
	}
	TestTrue(TEXT("un cran de molette rapproche"), Controls->ZoomStep > 0.0f && Controls->ZoomStep < 1.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgExplorationPartyTest, "Jadg.Exploration.Groupe", ExplorationFlags)

/// Les quatre du groupe sur une carte d'essai : le meneur marche où on l'envoie, les autres le
/// suivent en file sans se chevaucher ni rester en arrière, et la main passe au suivant.
bool FJadgExplorationPartyTest::RunTest(const FString& Parameters)
{
	// Le monde de ce test reçoit son système de navigation avant son maillage : le moteur le dit.
	AddExpectedError(TEXT("Unable to find RecastNavMesh instance"), EAutomationExpectedErrorFlags::Contains, 0);
	FGame Game;
	UWorld* World = Game.World;

	// Un sol de 24 × 18 m, le coin de la case (0, 0) à l'origine, et son maillage de navigation.
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	AStaticMeshActor* Floor = World->SpawnActor<AStaticMeshActor>(FVector(1200.0, 900.0, -50.0), FRotator::ZeroRotator);
	if (!TestNotNull(TEXT("le cube du moteur"), Cube) || !TestNotNull(TEXT("le sol"), Floor))
	{
		return false;
	}
	Floor->GetStaticMeshComponent()->SetStaticMesh(Cube);
	Floor->SetActorScale3D(FVector(24.0, 18.0, 1.0));
	UJadgSceneBuild::SpawnBoxVolume(World, ANavMeshBoundsVolume::StaticClass(), FVector(1200.0, 900.0, 100.0), FVector(2400.0, 1800.0, 600.0));

	World->SpawnActor<AJadgDayLight>();
	AJadgMapFrame* Frame = World->SpawnActor<AJadgMapFrame>();
	Frame->LevelId = TEXT("essai/etals");
	Frame->LevelsRoot = TrialLevels;
	for (int32 Rank = 0; Rank < 4; ++Rank)
	{
		AJadgWalker* Walker = World->SpawnActor<AJadgWalker>(FVector(525.0, 1275.0, 100.0), FRotator::ZeroRotator);
		Walker->PartyRank = Rank;
	}
	Game.Play();

	// Un monde créé par programme n'a pas de système de navigation : une carte qui s'ouvre en a un.
	if (FNavigationSystem::GetCurrent<UNavigationSystemV1>(World) == nullptr)
	{
		FNavigationSystem::AddNavigationSystemToWorld(*World, FNavigationSystemRunMode::GameMode);
	}
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!TestNotNull(TEXT("le système de navigation du monde"), Navigation))
	{
		return false;
	}
	Navigation->Build();
	FNavLocation OnMesh;
	if (!TestTrue(TEXT("le sol porte un maillage de navigation"),
			Navigation->ProjectPointToNavigation(FVector(525.0, 1275.0, 0.0), OnMesh, FVector(100.0, 100.0, 300.0))))
	{
		return false;
	}

	// Le groupe a été créé avant le maillage, comme sur une carte qui s'ouvre : il se range dès que
	// le maillage porte.
	Game.Tick(2);
	AJadgParty* Party = AJadgParty::Find(World);
	if (!TestNotNull(TEXT("le groupe"), Party) || !TestEqual(TEXT("quatre membres"), Party->GetMembers().Num(), 4))
	{
		return false;
	}
	const AJadgWalker* First = Party->Leader();
	TestTrue(TEXT("le meneur est à l'entrée de la carte de Core"),
		FVector2D::Distance(Party->CellOf(First->Feet()), Centre(3, 8)) < 0.2);

	// Dix cases vers l'est, le long de la ligne 8.
	Party->OrderWalk(Frame->ToWorld(FVector2D(13.5, 8.5)));
	Game.Tick(30 * 9);
	const TArray<TObjectPtr<AJadgWalker>>& Members = Party->GetMembers();
	TestTrue(*FString::Printf(TEXT("le meneur est arrivé (%.2f ; %.2f)"), Party->CellOf(First->Feet()).X, Party->CellOf(First->Feet()).Y),
		FVector2D::Distance(Party->CellOf(First->Feet()), FVector2D(13.5, 8.5)) < 0.3);
	for (int32 Rank = 1; Rank < Members.Num(); ++Rank)
	{
		const FVector2D Cell = Party->CellOf(Members[Rank]->Feet());
		const FVector2D Wanted(13.5 - Rank, 8.5);
		TestTrue(*FString::Printf(TEXT("le suiveur %d est à %d case(s) derrière le meneur (%.2f ; %.2f)"), Rank, Rank, Cell.X, Cell.Y),
			FVector2D::Distance(Cell, Wanted) < 0.4);
	}
	for (int32 A = 0; A < Members.Num(); ++A)
	{
		for (int32 B = A + 1; B < Members.Num(); ++B)
		{
			const double Apart = FVector2D::Distance(Party->CellOf(Members[A]->Feet()), Party->CellOf(Members[B]->Feet()));
			TestTrue(*FString::Printf(TEXT("%d et %d ne se chevauchent pas (%.2f case)"), A, B, Apart), Apart > 0.6);
		}
	}
	TestTrue(TEXT("Core sait où est le meneur"), FVector2D::Distance(Game.Exploration->HeroCell(), Party->CellOf(First->Feet())) < 0.05);

	// La main passe : le deuxième mène, l'ancien meneur ferme la file.
	const AJadgWalker* Second = Members[1];
	const FString SecondName = Game.Exploration->Members()[1].Name;
	Party->RotateLeader();
	TestTrue(TEXT("le suivant mène"), Party->Leader() == Second);
	TestTrue(TEXT("l'ancien meneur ferme la file"), Party->GetMembers().Last() == First);
	TestEqual(TEXT("le groupe de Core a tourné avec lui"), Game.Exploration->Members()[0].Name, SecondName);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgExplorationStoreyTest, "Jadg.Exploration.Etage", ExplorationFlags)

/// Une terrasse à 1,2 m et sa rampe : le meneur y monte par le maillage de navigation, et la file
/// le suit en hauteur.
bool FJadgExplorationStoreyTest::RunTest(const FString& Parameters)
{
	AddExpectedError(TEXT("Unable to find RecastNavMesh instance"), EAutomationExpectedErrorFlags::Contains, 0);
	FGame Game;
	UWorld* World = Game.World;

	// Le sol jusqu'à X = 15 m, la terrasse au-delà, haute de 1,2 m, et une rampe de deux cases de
	// large (lignes 5 et 6) qui monte de X = 10,5 m à X = 15 m : 15 degrés.
	constexpr double Rise = 120.0;
	constexpr double RampStart = 1050.0;
	constexpr double RampEnd = 1500.0;
	const double Slope = FMath::RadiansToDegrees(FMath::Atan2(Rise, RampEnd - RampStart));
	const double Length = FMath::Sqrt(FMath::Square(RampEnd - RampStart) + FMath::Square(Rise));
	const FVector Normal = FRotator(Slope, 0.0, 0.0).RotateVector(FVector::UpVector);
	const AStaticMeshActor* Floor = Block(World, FVector(750.0, 900.0, -50.0), FRotator::ZeroRotator, FVector(15.0, 18.0, 1.0));
	const AStaticMeshActor* Terrace = Block(World, FVector(1950.0, 900.0, Rise - 50.0), FRotator::ZeroRotator, FVector(9.0, 18.0, 1.0));
	const AStaticMeshActor* Ramp = Block(World, FVector((RampStart + RampEnd) / 2.0, 900.0, Rise / 2.0) - Normal * 10.0,
		FRotator(Slope, 0.0, 0.0), FVector(Length / 100.0, 3.0, 0.2));
	if (!TestNotNull(TEXT("le sol"), Floor) || !TestNotNull(TEXT("la terrasse"), Terrace) || !TestNotNull(TEXT("la rampe"), Ramp))
	{
		return false;
	}
	UJadgSceneBuild::SpawnBoxVolume(World, ANavMeshBoundsVolume::StaticClass(), FVector(1200.0, 900.0, 150.0), FVector(2400.0, 1800.0, 700.0));

	World->SpawnActor<AJadgDayLight>();
	AJadgMapFrame* Frame = World->SpawnActor<AJadgMapFrame>();
	Frame->LevelId = TEXT("essai/etals");
	Frame->LevelsRoot = TrialLevels;
	for (int32 Rank = 0; Rank < 4; ++Rank)
	{
		AJadgWalker* Walker = World->SpawnActor<AJadgWalker>(FVector(525.0, 1275.0, 100.0), FRotator::ZeroRotator);
		Walker->PartyRank = Rank;
	}
	Game.Play();
	if (FNavigationSystem::GetCurrent<UNavigationSystemV1>(World) == nullptr)
	{
		FNavigationSystem::AddNavigationSystemToWorld(*World, FNavigationSystemRunMode::GameMode);
	}
	UNavigationSystemV1* Navigation = FNavigationSystem::GetCurrent<UNavigationSystemV1>(World);
	if (!TestNotNull(TEXT("le système de navigation du monde"), Navigation))
	{
		return false;
	}
	Navigation->Build();
	FNavLocation Up;
	if (!TestTrue(TEXT("la terrasse porte un maillage de navigation"),
			Navigation->ProjectPointToNavigation(FVector(2025.0, 900.0, Rise), Up, FVector(50.0, 50.0, 50.0))))
	{
		return false;
	}
	Game.Tick(2);

	AJadgParty* Party = AJadgParty::Find(World);
	if (!TestNotNull(TEXT("le groupe"), Party) || !TestEqual(TEXT("quatre membres"), Party->GetMembers().Num(), 4))
	{
		return false;
	}
	// De l'entrée (3, 8) à la terrasse : dix cases plus à l'est, par la rampe.
	Party->OrderWalk(Frame->ToWorld(FVector2D(13.5, 6.0)) + FVector(0.0, 0.0, Rise));
	Game.Tick(30 * 10);

	const TArray<TObjectPtr<AJadgWalker>>& Members = Party->GetMembers();
	TestTrue(*FString::Printf(TEXT("le meneur est sur la terrasse (%.2f ; %.2f)"), Party->CellOf(Members[0]->Feet()).X, Party->CellOf(Members[0]->Feet()).Y),
		FVector2D::Distance(Party->CellOf(Members[0]->Feet()), FVector2D(13.5, 6.0)) < 0.3);
	for (int32 Rank = 0; Rank < Members.Num(); ++Rank)
	{
		// La hauteur du sol sous chacun : zéro, la rampe, ou la terrasse.
		const FVector Feet = Members[Rank]->Feet();
		const double Ground = Rise * FMath::Clamp((Feet.X - RampStart) / (RampEnd - RampStart), 0.0, 1.0);
		TestTrue(*FString::Printf(TEXT("le membre %d a les pieds sur le sol (%.0f cm pour %.0f)"), Rank, Feet.Z, Ground), FMath::Abs(Feet.Z - Ground) < 15.0);
		TestTrue(*FString::Printf(TEXT("le membre %d a quitté le rez-de-chaussée (%.0f cm)"), Rank, Feet.Z), Feet.Z > 30.0);
		if (Rank > 0)
		{
			const double Apart = FVector2D::Distance(Party->CellOf(Feet), Party->CellOf(Members[Rank - 1]->Feet()));
			TestTrue(*FString::Printf(TEXT("%d suit %d à une case (%.2f)"), Rank, Rank - 1, Apart), Apart > 0.6 && Apart < 1.5);
		}
	}
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
