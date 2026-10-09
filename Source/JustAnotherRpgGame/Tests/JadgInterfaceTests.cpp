// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Les tests d'automatisation de l'interface (LOT-1020) : le style, les textes en deux langues, et
// chaque écran construit, parcouru, refermé. Sans fenêtre ni processeur graphique :
//
//     UnrealEditor-Cmd.exe <projet>.uproject -ExecCmds="Automation RunTests Jadg.Interface; Quit" -nullrhi
//
// Le parcours des écrans dans le jeu lancé, touches et clics injectés comme au parcours de la
// quête, est le tour des écrans (`AJadgScreensTour`, `build.ps1 -Unreal -Ecrans`). Ici, chaque
// écran se construit sous l'instance du jeu, et ses gestes se jouent par ses boutons.

#include "Blueprint/UserWidget.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "Game/JadgExploration.h"
#include "Game/JadgGameInstance.h"
#include "Misc/AutomationTest.h"
#include "UI/JadgScreens.h"
#include "UI/JadgStyle.h"
#include "UI/JadgTexts.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags InterfaceFlags = EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::EngineFilter;

	/// Une partie neuve sous l'instance du jeu, comme au lancement.
	struct FGame
	{
		UJadgGameInstance* Instance = nullptr;
		UJadgExploration* Exploration = nullptr;

		FGame()
		{
			static int32 Count = 0;
			Instance = NewObject<UJadgGameInstance>(GEngine);
			Instance->InitializeStandalone(*FString::Printf(TEXT("JadgInterface%d"), ++Count));
			Exploration = Instance->GetSubsystem<UJadgExploration>();
		}

		~FGame()
		{
			UWorld* World = Instance->GetWorld();
			Instance->Shutdown();
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
		}

		/// L'écran @p Kind construit : son arbre d'UMG, et le widget Slate qu'il rend.
		UJadgScreen* Build(EJadgScreen Kind, const FString& Argument = FString()) const
		{
			UJadgScreen* Screen = CreateWidget<UJadgScreen>(Instance, JadgScreenClass(Kind));
			Screen->Kind = Kind;
			Screen->Argument = Argument;
			Screen->TakeWidget();
			return Screen;
		}
	};

	bool Shows(const UJadgScreen& Screen, const FText& Text)
	{
		return Screen.VisibleTexts().Contains(Text.ToString());
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgInterfaceStyleTest, "Jadg.Interface.Style", InterfaceFlags)

/**
 * @brief Le style se lit ; une pièce du kit est un 9-patch, ou l'aplat des jetons sans le kit.
 */
bool FJadgInterfaceStyleTest::RunTest(const FString& Parameters)
{
	UJadgStyle& Style = UJadgStyle::Get();
	TestTrue(TEXT("le style se lit sans erreur"), Style.Errors().IsEmpty());
	TestTrue(TEXT("le style décrit les pièces du kit"), Style.PieceCount() > 50);
	TestEqual(TEXT("le panneau sombre a sa taille de conception"), Style.PieceSize(TEXT("frame/panel-dark")), FVector2D(512.0f, 512.0f));
	TestEqual(TEXT("le titre d'écran est à 36 pixels"), Style.Size(TEXT("screenTitle")), 36);
	const FSlateBrush Panel = Style.Brush(TEXT("frame/panel-dark"));
	if (Style.TexturesFound() > 0)
	{
		TestEqual(TEXT("avec le kit, le panneau est un 9-patch"), Panel.DrawAs.GetValue(), ESlateBrushDrawType::Box);
		TestTrue(TEXT("ses marges sont celles du cahier (112 sur 512)"), FMath::IsNearlyEqual(Panel.Margin.Left, 112.0f / 512.0f));
	}
	else
	{
		AddInfo(TEXT("le kit UI n'est pas importé sur ce poste : l'aplat des jetons est vérifié"));
		TestEqual(TEXT("sans le kit, le panneau est l'aplat des jetons"), Panel.DrawAs.GetValue(), ESlateBrushDrawType::RoundedBox);
	}
	TestTrue(TEXT("le bouton par défaut a un état de survol"), Style.HasState(TEXT("button/default"), TEXT("hover")));
	TestTrue(TEXT("une police existe pour chaque rôle, au moins celle du moteur"), Style.Font(TEXT("title"), TEXT("body")).HasValidFont());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgInterfaceTextsTest, "Jadg.Interface.Textes", InterfaceFlags)

/**
 * @brief Les deux catalogues sont des tables de chaînes du moteur ; les trous se remplissent.
 */
bool FJadgInterfaceTextsTest::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("le français et l'anglais sont chargés"), FJadgTexts::Languages().Contains(TEXT("fr")) && FJadgTexts::Languages().Contains(TEXT("en")));
	TestEqual(TEXT("les deux catalogues ont autant de textes"), FJadgTexts::Count(TEXT("fr")), FJadgTexts::Count(TEXT("en")));
	TestEqual(TEXT("« Carte » en français"), FJadgTexts::In(TEXT("fr"), TEXT("hud.map")).ToString(), FString(TEXT("Carte")));
	TestEqual(TEXT("« Map » en anglais"), FJadgTexts::In(TEXT("en"), TEXT("hud.map")).ToString(), FString(TEXT("Map")));
	TestTrue(TEXT("le texte vient d'une table de chaînes"), FJadgTexts::In(TEXT("fr"), TEXT("hud.map")).IsFromStringTable());
	TestEqual(TEXT("une clé absente s'affiche telle quelle"), FJadgTexts::In(TEXT("en"), TEXT("aucune.cle")).ToString(), FString(TEXT("aucune.cle")));
	const FString Before = FJadgTexts::Language();
	FJadgTexts::SetLanguage(TEXT("en"));
	TestEqual(TEXT("les trous se remplissent (anglais)"),
		FJadgTexts::Format(TEXT("combat.round"), {FText::AsNumber(3)}).ToString(), FString(TEXT("Round 3")));
	FJadgTexts::SetLanguage(TEXT("fr"));
	TestEqual(TEXT("les trous se remplissent (français)"),
		FJadgTexts::Format(TEXT("hud.encounter"), {FText::FromString(TEXT("arene-bandits"))}).ToString(), FString(TEXT("Rencontre : arene-bandits")));
	FJadgTexts::SetLanguage(TEXT("xx"));
	TestEqual(TEXT("une langue sans catalogue est refusée"), FJadgTexts::Language(), FString(TEXT("fr")));
	FJadgTexts::SetLanguage(Before);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgInterfaceScreensTest, "Jadg.Interface.Ecrans", InterfaceFlags)

/**
 * @brief Chaque écran se construit sous l'instance du jeu, montre son titre, a ses boutons, et une
 *        page se ferme par Échap ; une fin ne ramène pas au jeu.
 */
bool FJadgInterfaceScreensTest::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		AddInfo(TEXT("pas d'application Slate : les écrans ne se construisent pas ici"));
		return true;
	}
	const FGame Game;
	const TArray<TPair<EJadgScreen, const TCHAR*>> Pages = {
		{EJadgScreen::Hud, TEXT("hud.map")},
		{EJadgScreen::Title, TEXT("menu.new_game")},
		{EJadgScreen::Pause, TEXT("menu.resume")},
		{EJadgScreen::Options, TEXT("options.apply")},
		{EJadgScreen::NewGame, TEXT("party.start")},
		{EJadgScreen::Party, TEXT("party.lead")},
		{EJadgScreen::Character, TEXT("sheet.identity")},
		{EJadgScreen::Equipment, TEXT("inventory.bag")},
		{EJadgScreen::Journal, TEXT("journal.quests")},
		{EJadgScreen::Map, TEXT("map.favourites")},
		{EJadgScreen::Ending, TEXT("end.demo.title")},
		{EJadgScreen::Death, TEXT("end.death.title")},
		{EJadgScreen::Debug, TEXT("debug.title")},
	};
	for (const TPair<EJadgScreen, const TCHAR*>& Page : Pages)
	{
		UJadgScreen* Screen = Game.Build(Page.Key);
		const FString Name = UEnum::GetValueAsString(Page.Key);
		const bool bButton = Screen->FindButton(FJadgTexts::Get(Page.Value)) != nullptr;
		TestTrue(Name + TEXT(" montre « ") + FJadgTexts::Get(Page.Value).ToString() + TEXT(" »"), bButton || Shows(*Screen, FJadgTexts::Get(Page.Value)));
		TestTrue(Name + TEXT(" a des boutons"), !Screen->Buttons().IsEmpty() || Page.Key == EJadgScreen::Death);
		if (Screen->IsModal())
		{
			TestTrue(Name + TEXT(" prend Échap"), Screen->HandleKey(EKeys::Escape));
			TestTrue(Name + TEXT(" a un bouton à focaliser"), Screen->FirstFocus() != Screen);
		}
		else
		{
			TestFalse(Name + TEXT(" laisse Échap au jeu"), Screen->HandleKey(EKeys::Escape));
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgInterfaceGesturesTest, "Jadg.Interface.Gestes", InterfaceFlags)

/**
 * @brief Les gestes des écrans atteignent le jeu : le meneur choisi au groupe, la voix d'un
 *        dialogue, la réponse donnée ; et l'écran Personnage s'affiche dans les deux langues.
 */
bool FJadgInterfaceGesturesTest::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		AddInfo(TEXT("pas d'application Slate : les écrans ne se construisent pas ici"));
		return true;
	}
	const FGame Game;
	const TArray<FJadgMember> Members = Game.Exploration->Members();
	if (!TestEqual(TEXT("le groupe préformé a quatre membres"), Members.Num(), 4))
	{
		return false;
	}

	// Le groupe : « Mener » sur le troisième membre en fait le meneur (D-37).
	UJadgPartyScreen* Party = Cast<UJadgPartyScreen>(Game.Build(EJadgScreen::Party, Members[2].Id));
	TestEqual(TEXT("le groupe s'ouvre sur le membre demandé"), Party->Chosen, Members[2].Id);
	if (UJadgButton* Lead = Party->FindButton(FJadgTexts::Get(TEXT("party.lead"))))
	{
		Lead->Activate();
	}
	TestEqual(TEXT("« Mener » fait le meneur"), Game.Exploration->Members()[0].Id, Members[2].Id);
	Game.Exploration->SetLeader(Members[0].Id);

	// Le dialogue : la voix passe au suivant, la réponse se donne au bouton.
	Game.Exploration->TalkTo(TEXT("mere"));
	if (TestTrue(TEXT("la mère parle"), Game.Exploration->InDialogue()))
	{
		const TArray<FJadgMember> Order = Game.Exploration->Members();
		TestEqual(TEXT("le meneur parle à l'ouverture (D-37)"), Game.Exploration->DialogueSpeaker(), Order[0].Id);
		Game.Exploration->NextDialogueSpeaker(1);
		TestEqual(TEXT("la parole passe au suivant (D-28)"), Game.Exploration->DialogueSpeaker(), Order[1].Id);
		TestTrue(TEXT("la voix se choisit par son identifiant"), Game.Exploration->SetDialogueSpeaker(Members[3].Id));
		UJadgScreen* Talk = Game.Build(EJadgScreen::Dialogue);
		Talk->Update();
		const FString Line = Game.Exploration->Line();
		if (TestTrue(TEXT("le dialogue montre ses réponses"), !Talk->Buttons().IsEmpty()))
		{
			Talk->Buttons()[0]->Activate();
			TestTrue(TEXT("la réponse au bouton fait avancer la conversation"), !Game.Exploration->InDialogue() || Game.Exploration->Line() != Line);
		}
	}

	// Les deux langues.
	const FString Before = FJadgTexts::Language();
	FJadgTexts::SetLanguage(TEXT("fr"));
	TestTrue(TEXT("la fiche en français"), Shows(*Game.Build(EJadgScreen::Character), FJadgTexts::In(TEXT("fr"), TEXT("sheet.identity"))));
	FJadgTexts::SetLanguage(TEXT("en"));
	UJadgScreen* English = Game.Build(EJadgScreen::Character);
	TestTrue(TEXT("la fiche en anglais"), Shows(*English, FJadgTexts::In(TEXT("en"), TEXT("sheet.identity"))));
	TestFalse(TEXT("la fiche en anglais ne montre pas le français"), Shows(*English, FJadgTexts::In(TEXT("fr"), TEXT("sheet.identity"))));
	FJadgTexts::SetLanguage(Before);
	return true;
}

#endif
