// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Les tests du créateur de personnage (LOT-1015, D-63) : une fiche d'apparence pose un personnage
// dans le moteur — corps, clips, taille, armes —, et le créateur Mutable construit par
// `JadgBuildCharacterCreator` commute le corps. Sans fenêtre ni processeur graphique :
//
//     UnrealEditor-Cmd.exe <projet>.uproject -ExecCmds="Automation RunTests Jadg.Personnages; Quit" -nullrhi
//
// Les règles de lecture des fiches sont testées hors du moteur (`test_appearance.cpp`,
// `test_character_creator.cpp`) ; ici on vérifie que le moteur en fait un personnage.

// Core avant le moteur.
#include "Core/Rpg/Appearance.h"
#include "Core/Rpg/CharacterCreator.h"

#include "Animation/AnimSequence.h"
#include "Bridge/JadgPaths.h"
#include "Characters/JadgAppearance.h"
#include "Characters/JadgWalker.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Engine.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "Game/JadgGameInstance.h"
#include "Game/JadgGameMode.h"
#include "GameFramework/WorldSettings.h"
#include "Misc/AutomationTest.h"
#include "Misc/PackageName.h"
#include "MuCO/CustomizableObject.h"
#include "MuCO/CustomizableSkeletalComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags PersonnagesFlags = EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::EngineFilter;

	/// Une partie neuve sous l'instance du jeu, et son monde vide (comme `JadgExplorationTests`).
	struct FGame
	{
		UJadgGameInstance* Instance = nullptr;
		UWorld* World = nullptr;
		bool bPlaying = false;

		FGame()
		{
			static int32 Count = 0;
			Instance = NewObject<UJadgGameInstance>(GEngine);
			Instance->InitializeStandalone(*FString::Printf(TEXT("JadgPersonnages%d"), ++Count));
			World = Instance->GetWorld();
		}

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

	core::CharacterCreator Humanoid()
	{
		return core::readCharacterCreator(FJadgPaths::ToPath(FJadgPaths::ElementsDir()) / "Assets" / "Characters" / "humanoid.json").creator;
	}
} // namespace

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgPersonnagesCreateurTest, "Jadg.Personnages.Createur", PersonnagesFlags)

/// La description du créateur se lit dans le moteur ; chaque corps et chaque clip qu'elle nomme est
/// un asset du poste (posé par `import_mannequin_unreal.py`), et son objet personnalisable est
/// construit (`JadgBuildCharacterCreator`) avec le paramètre `Body` et ses options.
bool FJadgPersonnagesCreateurTest::RunTest(const FString& Parameters)
{
	const core::CharacterCreator Creator = Humanoid();
	if (!TestFalse(TEXT("la description humanoid se lit"), Creator.id.empty()))
	{
		return false;
	}
	for (const auto& [Option, Chemin] : Creator.bodies)
	{
		TestNotNull(*FString::Printf(TEXT("corps %s"), *FJadgPaths::ToFString(Option)),
			LoadObject<USkeletalMesh>(nullptr, *FJadgPaths::ToFString(Chemin)));
	}
	for (const auto& [Nom, Chemin] : Creator.clips)
	{
		TestNotNull(*FString::Printf(TEXT("clip %s"), *FJadgPaths::ToFString(Nom)), LoadObject<UAnimSequence>(nullptr, *FJadgPaths::ToFString(Chemin)));
	}
	TestEqual(TEXT("six clips"), static_cast<int32>(Creator.clips.size()), 6);

	UCustomizableObject* Object = LoadObject<UCustomizableObject>(nullptr, *FJadgPaths::ToFString(Creator.asset));
	if (!TestNotNull(TEXT("l'objet personnalisable construit par le commandlet"), Object))
	{
		return false;
	}
	TArray<FString> Options;
	const int32 Count = Object->GetEnumParameterNumValues(TEXT("Body"));
	for (int32 Index = 0; Index < Count; ++Index)
	{
		Options.Add(Object->GetEnumParameterValue(TEXT("Body"), Index));
	}
	for (const auto& [Option, Chemin] : Creator.bodies)
	{
		TestTrue(*FString::Printf(TEXT("option %s du paramètre Body"), *FJadgPaths::ToFString(Option)), Options.Contains(FJadgPaths::ToFString(Option)));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgPersonnagesFicheTest, "Jadg.Personnages.Fiche", PersonnagesFlags)

/// Une fiche d'apparence pose un personnage : le corps de la fiche, les six clips, la taille à
/// l'échelle, l'arme de la main principale à son socket ; une fiche inconnue est refusée.
bool FJadgPersonnagesFicheTest::RunTest(const FString& Parameters)
{
	FGame Game;
	UWorld* World = Game.World;
	AJadgWalker* Grom = World->SpawnActor<AJadgWalker>(FVector(0.0, 0.0, 100.0), FRotator::ZeroRotator);
	Grom->Appearance = TEXT("heros-brawler");
	AJadgWalker* Helga = World->SpawnActor<AJadgWalker>(FVector(300.0, 0.0, 100.0), FRotator::ZeroRotator);
	Helga->Appearance = TEXT("heros-priest");
	Game.Play();
	Game.Tick(2);

	const core::CharacterCreator Creator = Humanoid();
	const core::Appearance FicheGrom = core::readAppearance(FJadgPaths::RpgRoot() / "appearances" / "heros-brawler.json").appearance;
	const core::Appearance FicheHelga = core::readAppearance(FJadgPaths::RpgRoot() / "appearances" / "heros-priest.json").appearance;

	// Le corps : le maillage de référence du créateur est posé dès le lancement ; l'instance
	// Mutable, asynchrone, le remplace par le corps assemblé quand elle est prête.
	TestNotNull(TEXT("Grom a un maillage"), Grom->GetMesh()->GetSkeletalMeshAsset());
	TestTrue(TEXT("Grom vient du créateur"), Grom->bFromCreator);
	TestNotNull(TEXT("Grom porte le composant Mutable"), Grom->FindComponentByClass<UCustomizableSkeletalComponent>());

	// Les clips et l'instant d'impact.
	TestEqual(TEXT("six clips sur Grom"), Grom->Clips.Num(), 6);
	TestNotNull(TEXT("le repos joue"), Grom->IdleClip.Get());
	TestNotNull(TEXT("la marche joue"), Grom->WalkClip.Get());
	TestEqual(TEXT("l'impact de l'attaque"), Grom->ClipKeys.FindRef(TEXT("attack")), FicheGrom.clipKeys.at("attack"));
	TestTrue(TEXT("l'attaque se joue une fois"), Grom->PlayOnce(TEXT("attack")));
	TestFalse(TEXT("un clip inconnu ne se joue pas"), Grom->PlayOnce(TEXT("danse")));

	// La taille : Helga est plus petite que Grom, chacun à l'échelle de sa fiche.
	TestEqual(TEXT("l'échelle de Grom"), static_cast<float>(Grom->GetActorScale3D().Z), FicheGrom.height / Creator.referenceHeight, 0.001f);
	TestEqual(TEXT("l'échelle de Helga"), static_cast<float>(Helga->GetActorScale3D().Z), FicheHelga.height / Creator.referenceHeight, 0.001f);
	TestTrue(TEXT("Helga est plus petite"), Helga->GetActorScale3D().Z < Grom->GetActorScale3D().Z);
	TestEqual(TEXT("Grom reste debout au sol"), Grom->Feet().Z, static_cast<double>(100.0f - Grom->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight()), 1.0);

	// Les armes : une pour Grom (la hache), deux pour Helga (marteau et bouclier), aux sockets.
	TestEqual(TEXT("Grom tient une arme"), Grom->Weapons.Num(), 1);
	TestEqual(TEXT("Helga tient deux pièces"), Helga->Weapons.Num(), 2);
	if (Grom->Weapons.Num() == 1)
	{
		TestEqual(TEXT("la hache est à la main droite"), Grom->Weapons[0]->GetAttachSocketName(), FName(*FJadgPaths::ToFString(Creator.sockets.at("main-hand"))));
	}

	// Une fiche inconnue est refusée, avec sa raison.
	AddExpectedError(TEXT("nulle-part"), EAutomationExpectedErrorFlags::Contains, 1);
	AJadgWalker* Inconnu = World->SpawnActor<AJadgWalker>(FVector(600.0, 0.0, 100.0), FRotator::ZeroRotator);
	FString Erreur;
	TestFalse(TEXT("une fiche absente est refusée"), JadgAppearance::Apply(*Inconnu, TEXT("nulle-part"), Erreur));
	TestTrue(TEXT("la raison nomme la fiche"), Erreur.Contains(TEXT("nulle-part")));
	UE_LOG(LogTemp, Error, TEXT("%s"), *Erreur);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgPersonnagesModificationTest, "Jadg.Personnages.FicheModifiee", PersonnagesFlags)

/// Changer la fiche change le personnage, sans geste dans l'éditeur : la même fiche lue avec un
/// autre corps, une autre taille, une autre arme donne un autre personnage.
bool FJadgPersonnagesModificationTest::RunTest(const FString& Parameters)
{
	const core::Appearance Base = core::readAppearance(FJadgPaths::RpgRoot() / "appearances" / "heros-scoundrel.json").appearance;
	const core::AppearanceReadResult Variante = core::parseAppearance(
		R"({"id":"heros-scoundrel","name":"Nessa","source":"tanares","creator":"humanoid","body":"quinn","head":"quinn",
		    "height":1.95,"weapons":{"off-hand":"Weapons/dagger"}})",
		"variante");
	if (!TestTrue(TEXT("la variante se lit"), Variante.ok()))
	{
		return false;
	}
	TestNotEqual(TEXT("un autre corps"), Variante.appearance.body, Base.body);
	TestNotEqual(TEXT("une autre taille"), Variante.appearance.height, Base.height);
	const core::CharacterCreator Creator = Humanoid();
	TestTrue(TEXT("le corps de la variante est une option du créateur"), Creator.bodies.count(Variante.appearance.body) == 1);
	UCustomizableObject* Object = LoadObject<UCustomizableObject>(nullptr, *FJadgPaths::ToFString(Creator.asset));
	if (TestNotNull(TEXT("l'objet personnalisable"), Object))
	{
		bool bConnu = false;
		for (int32 Index = 0; Index < Object->GetEnumParameterNumValues(TEXT("Body")); ++Index)
		{
			bConnu |= Object->GetEnumParameterValue(TEXT("Body"), Index) == FJadgPaths::ToFString(Variante.appearance.body);
		}
		TestTrue(TEXT("le créateur sait faire ce corps"), bConnu);
	}
	return true;
}

#endif
