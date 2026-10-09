// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Les premiers tests d'automatisation du moteur (LOT-1014) : ce que le socle doit tenir pour que
// tout lot suivant s'y pose. Ils tournent sans fenêtre ni processeur graphique :
//
//     UnrealEditor-Cmd.exe <projet>.uproject -ExecCmds="Automation RunTests Jadg.Socle; Quit" -nullrhi
//
// c'est-à-dire `scripts/build.ps1 -Unreal`. Les règles elles-mêmes sont testées hors du moteur
// (GoogleTest, `Source/Test/Unit/Core`) ; ici se vérifie que le moteur lit les mêmes fichiers et
// en tire les mêmes valeurs.

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Data/GameOptions.h"
#include "Core/Rpg/CharacterOptions.h"
#include "Core/Rpg/CharacterSheet.h"
#include "Core/Rpg/Equipment.h"
#include "Core/Rpg/Inventory.h"
#include "Core/Rpg/Party.h"

#include <array>
#include <filesystem>
#include <string>
#include <vector>

#include "Bridge/JadgOptions.h"
#include "Bridge/JadgPaths.h"
#include "Capture/JadgShot.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Game/JadgGameInstance.h"
#include "Game/JadgGameMode.h"
#include "GameFramework/WorldSettings.h"
#include "HAL/IConsoleManager.h"
#include "Misc/App.h"
#include "Misc/AutomationTest.h"
#include "Player/JadgCameraPawn.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags SocleFlags = EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::EngineFilter;

	/// Ce que la page du livre imprime pour une fiche pré-tirée — les mêmes valeurs que
	/// `Source/Test/Unit/Core/Rpg/test_premade_characters.cpp`, qui en vérifie le détail.
	struct FPrintedSheet
	{
		const char* File;
		const char* Species;
		const char* Background;
		std::array<int, 6> Abilities;
		int HitPoints;
		int ArmorClass;
		float SpeedMeters;
	};

	const FPrintedSheet PrintedSheets[] = {
		{"heros-brawler", "demi-orc", "dragon-hunter", {16, 13, 16, 10, 12, 8}, 15, 14, 9.0f},
		{"heros-mage", "elfe-d-automne", "cartographer", {8, 15, 15, 16, 12, 10}, 8, 12, 9.0f},
		{"heros-priest", "nain-des-collines", "community-leader", {13, 12, 16, 10, 16, 8}, 12, 17, 7.5f},
		{"heros-scoundrel", "humain", "undercover", {9, 16, 15, 10, 14, 14}, 10, 14, 9.0f},
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgSocleEmptyMapTest, "Jadg.Socle.CarteVide", SocleFlags)

/// Une carte vide s'ouvre sous l'instance du jeu, son mode de jeu la fait jouer, un acteur s'y crée.
bool FJadgSocleEmptyMapTest::RunTest(const FString& Parameters)
{
	// L'instance du jeu crée son monde vide, comme au lancement : elle lit les options au passage.
	UJadgGameInstance* Instance = NewObject<UJadgGameInstance>(GEngine);
	Instance->InitializeStandalone(TEXT("JadgSocleCarteVide"));
	UWorld* World = Instance->GetWorld();
	if (!TestNotNull(TEXT("le monde de la carte vide"), World))
	{
		return false;
	}

	// Le mode de jeu que les cartes du dépôt désignent (`build_level.py`).
	World->GetWorldSettings()->DefaultGameMode = AJadgGameMode::StaticClass();
	const FURL Url;
	World->SetGameMode(Url);
	World->InitializeActorsForPlay(Url);
	World->BeginPlay();

	TestTrue(TEXT("la carte a commencé à jouer"), World->HasBegunPlay());
	const AJadgGameMode* Mode = Cast<AJadgGameMode>(World->GetAuthGameMode());
	if (TestNotNull(TEXT("le mode de jeu de la carte est celui du jeu"), Mode))
	{
		TestTrue(TEXT("son pion est la caméra libre"), Mode->DefaultPawnClass == AJadgCameraPawn::StaticClass());
	}
	const AJadgShot* Shot = World->SpawnActor<AJadgShot>();
	if (TestNotNull(TEXT("un cadrage créé dans la carte"), Shot))
	{
		TestTrue(TEXT("le cadrage a commencé à jouer"), Shot->HasActorBegunPlay());
	}

	World->EndPlay(EEndPlayReason::Quit);
	Instance->Shutdown();
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgSoclePartyTest, "Jadg.Socle.GroupePreforme", SocleFlags)

/// Le groupe préformé de D-28 : quatre fiches lues dans le moteur, valeur pour valeur.
bool FJadgSoclePartyTest::RunTest(const FString& Parameters)
{
	const std::filesystem::path Rpg = FJadgPaths::RpgRoot();
	const auto Report = [this](const std::vector<std::string>& Errors, const TCHAR* What)
	{
		for (const std::string& Error : Errors)
		{
			AddError(FString::Printf(TEXT("%s : %s"), What, *FJadgPaths::ToFString(Error)));
		}
	};

	const core::CharacterOptions Options = core::loadCharacterOptions(Rpg);
	Report(Options.errors, TEXT("options de personnage"));
	const core::CharacterCreationRules Rules = core::loadCharacterCreationRules(Rpg / "rules" / "character-creation.json");
	Report(Rules.errors, TEXT("règles de création"));
	const core::ExperienceTable Experience = core::loadExperienceTable(Rpg / "rules" / "experience.json");
	Report(Experience.errors, TEXT("table d'expérience"));
	const core::EquipmentCatalog Equipment = core::loadEquipment(Rpg / "weapons", Rpg / "armors");
	const core::ItemCatalog Items = core::loadItems(Rpg / "items");
	const core::EncumbranceRules Encumbrance = core::loadEncumbranceRules(Rpg / "rules" / "encumbrance.json");
	const core::ItemLookup Lookup{.items = &Items, .equipment = &Equipment};

	const core::PartyCandidates Candidates = core::loadPartyCandidates(Rpg / "characters");
	Report(Candidates.errors, TEXT("fiches du groupe"));
	TestEqual(TEXT("le groupe préformé compte quatre fiches"), static_cast<int32>(Candidates.candidates.size()), 4);

	static const TCHAR* const AbilityNames[] = {TEXT("FOR"), TEXT("DEX"), TEXT("CON"), TEXT("INT"), TEXT("SAG"), TEXT("CHA")};
	for (const FPrintedSheet& Printed : PrintedSheets)
	{
		const FString Who = FJadgPaths::ToFString(Printed.File);
		const core::LoadedCharacterSheet Loaded =
			core::loadCharacterSheet(Rpg / "characters" / (std::string(Printed.File) + ".json"), Options, Rules, Experience);
		Report(Loaded.errors, *Who);
		const core::CharacterSheet& Sheet = Loaded.sheet;

		TestEqual(*(Who + TEXT(" : niveau")), Sheet.level, 1);
		TestEqual(*(Who + TEXT(" : espèce")), FJadgPaths::ToFString(Sheet.speciesId), FJadgPaths::ToFString(Printed.Species));
		TestEqual(*(Who + TEXT(" : historique")), FJadgPaths::ToFString(Sheet.backgroundId), FJadgPaths::ToFString(Printed.Background));
		for (int32 Index = 0; Index < 6; ++Index)
		{
			TestEqual(*FString::Printf(TEXT("%s : %s"), *Who, AbilityNames[Index]), Sheet.abilities[Index], Printed.Abilities[Index]);
		}
		TestEqual(*(Who + TEXT(" : points de vie")), Sheet.maximumHitPoints, Printed.HitPoints);
		TestEqual(*(Who + TEXT(" : classe d'armure")),
			core::derivedStatsFor(Sheet, Loaded.inventory, Lookup, Rules, Encumbrance).armorClass, Printed.ArmorClass);
		TestEqual(*(Who + TEXT(" : vitesse (m)")), Sheet.speedMeters, Printed.SpeedMeters);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgSocleOptionsTest, "Jadg.Socle.Options", SocleFlags)

/// Les options du jeu se lisent dans leur fichier texte et atteignent le moteur.
bool FJadgSocleOptionsTest::RunTest(const FString& Parameters)
{
	core::GameOptions Options;
	TestEqual(TEXT("les options se lisent sans erreur"), FJadgOptions::Read(Options), 0);

	IConsoleVariable* Scale = IConsoleManager::Get().FindConsoleVariable(TEXT("r.ScreenPercentage"));
	IConsoleVariable* Shadows = IConsoleManager::Get().FindConsoleVariable(TEXT("sg.ShadowQuality"));
	if (!TestNotNull(TEXT("r.ScreenPercentage"), Scale) || !TestNotNull(TEXT("sg.ShadowQuality"), Shadows))
	{
		return false;
	}
	// Le test rend au moteur ce qu'il y a trouvé : il tourne aussi dans l'éditeur de l'auteur.
	const float ScaleBefore = Scale->GetFloat();
	const int32 ShadowsBefore = Shadows->GetInt();
	const float VolumeBefore = FApp::GetVolumeMultiplier();

	// Des valeurs que le fichier d'usine ne porte pas : une option lue et non appliquée se verrait.
	Options.renderScalePercent = 75;
	Options.shadowQuality = 1;
	Options.volumePercent = 40;
	FJadgOptions::Apply(Options);
	TestEqual(TEXT("l'échelle de rendu atteint r.ScreenPercentage"), Scale->GetFloat(), 75.0f);
	TestEqual(TEXT("la qualité des ombres atteint sg.ShadowQuality"), Shadows->GetInt(), 1);
	TestEqual(TEXT("le volume atteint l'application"), FApp::GetVolumeMultiplier(), 0.4f);

	Scale->Set(ScaleBefore, ECVF_SetByGameSetting);
	Shadows->Set(ShadowsBefore, ECVF_SetByGameSetting);
	FApp::SetVolumeMultiplier(VolumeBefore);
	return true;
}

#endif // WITH_DEV_AUTOMATION_TESTS
