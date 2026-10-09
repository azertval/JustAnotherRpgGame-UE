// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Les tests de la chaîne de décor (LOT-1019) : une pièce installée par
// `scripts/assetsGeneration/import_scenery_unreal.py` est en Nanite, chaque matière est une
// instance de la matière parente du décor (utilisable en instances : la carte grise du LOT-1018),
// ses textures sont compressées par le moteur (BC7, BC5 pour le relief) et partagées entre pièces.
// Sans fenêtre ni processeur graphique :
//
//     UnrealEditor-Cmd.exe <projet>.uproject -ExecCmds="Automation RunTests Jadg.Decor; Quit" -nullrhi
//
// Les pièces lues sont hors Git (kits publiés, maîtres Meshy) : une pièce absente du poste est dite
// et sautée, comme le contrôle de la carte de la porte. La lecture des fiches et des matières d'un
// `.glb` est testée hors du moteur (`scripts/tests/test_scenery_sheets.py`).

#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstance.h"
#include "Misc/AutomationTest.h"
#include "UObject/Package.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	constexpr EAutomationTestFlags DecorFlags = EAutomationTestFlags_ApplicationContextMask | EAutomationTestFlags::EngineFilter;

	const TCHAR* ParentMaterials[] = {TEXT("/Game/Scenery/Common/M_Scenery"), TEXT("/Game/Scenery/Common/M_SceneryMasked")};
	const TCHAR* TexturesRoot = TEXT("/Game/Scenery/Textures/");

	/// Les pièces que la chaîne doit avoir installées : un maître Meshy (la façade témoin), une
	/// pièce du kit de l'Arena of Fate posée en instances, une pièce construite par script.
	const TCHAR* Pieces[] = {
		TEXT("/Game/Master/Scenery/arenarea-palazzo-terracotta/StaticMeshes/SM_Scenery_Arenarea_Palazzo_Terracotta"),
		TEXT("/Game/Kit/Regions/central-empire/capital/arenarea/arena-of-fate/af-sand-a/StaticMeshes/SM_af-sand-a"),
		TEXT("/Game/Kit/Built/colisee/col-sand/StaticMeshes/SM_col-sand"),
	};

	UStaticMesh* LoadPiece(FAutomationTestBase& Test, const TCHAR* Path)
	{
		UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, Path, nullptr, LOAD_NoWarn | LOAD_Quiet);
		if (Mesh == nullptr)
		{
			Test.AddInfo(FString::Printf(TEXT("%s absent du poste (kits, maîtres ou Colisée hors Git) : sauté"), Path));
		}
		return Mesh;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgDecorMatiereTest, "Jadg.Decor.Matiere", DecorFlags)

bool FJadgDecorMatiereTest::RunTest(const FString& Parameters)
{
	int32 Checked = 0;
	for (const TCHAR* Path : Pieces)
	{
		UStaticMesh* Mesh = LoadPiece(*this, Path);
		if (Mesh == nullptr)
		{
			continue;
		}
		++Checked;
		TestTrue(FString::Printf(TEXT("%s est en Nanite"), Path), Mesh->GetNaniteSettings().bEnabled);
		for (int32 Index = 0; Index < Mesh->GetStaticMaterials().Num(); ++Index)
		{
			UMaterialInterface* Material = Mesh->GetMaterial(Index);
			if (!TestNotNull(FString::Printf(TEXT("%s, matière %d"), Path, Index), Material))
			{
				continue;
			}
			UMaterial* Base = Material->GetMaterial();
			const FString BasePath = Base != nullptr ? Base->GetPackage()->GetName() : FString();
			TestTrue(FString::Printf(TEXT("%s : %s descend de la matière du décor (%s)"), Path, *Material->GetName(), *BasePath),
				BasePath == ParentMaterials[0] || BasePath == ParentMaterials[1]);
			if (Base != nullptr)
			{
				// Ce qui manquait à la matière glTF du moteur : posée en instances, elle cédait à la
				// matière par défaut dans le jeu lancé.
				TestTrue(TEXT("la matière parente sert en instances"), Base->GetUsageByFlag(MATUSAGE_InstancedStaticMeshes));
				TestTrue(TEXT("la matière parente sert en Nanite"), Base->GetUsageByFlag(MATUSAGE_Nanite));
			}
			const UMaterialInstance* Instance = Cast<UMaterialInstance>(Material);
			if (!TestNotNull(TEXT("une matière de pièce est une instance"), Instance))
			{
				continue;
			}
			for (const FTextureParameterValue& Value : Instance->TextureParameterValues)
			{
				const UTexture2D* Texture = Cast<UTexture2D>(Value.ParameterValue);
				if (Texture == nullptr)
				{
					continue;
				}
				const FString Name = Value.ParameterInfo.Name.ToString();
				TestTrue(FString::Printf(TEXT("%s : la texture %s est partagée (%s)"), Path, *Name, *Texture->GetPathName()),
					Texture->GetPathName().StartsWith(TexturesRoot));
				if (Name == TEXT("Normal"))
				{
					TestEqual(TEXT("le relief est en BC5"), static_cast<int32>(Texture->CompressionSettings.GetValue()), static_cast<int32>(TC_Normalmap));
				}
				else
				{
					TestEqual(FString::Printf(TEXT("%s en BC7"), *Name), static_cast<int32>(Texture->CompressionSettings.GetValue()), static_cast<int32>(TC_BC7));
					TestEqual(FString::Printf(TEXT("%s : sRGB pour la couleur seule"), *Name), static_cast<bool>(Texture->SRGB), Name == TEXT("BaseColor"));
				}
			}
		}
	}
	AddInfo(FString::Printf(TEXT("%d pièce(s) contrôlée(s) sur %d"), Checked, static_cast<int32>(UE_ARRAY_COUNT(Pieces))));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJadgDecorPartageTest, "Jadg.Decor.TexturesPartagees", DecorFlags)

bool FJadgDecorPartageTest::RunTest(const FString& Parameters)
{
	// Les trois sables de l'Arena of Fate portent les mêmes images : une seule instance de matière,
	// donc les mêmes trois textures, pour les trois pièces.
	const TCHAR* Sands[] = {
		TEXT("/Game/Kit/Regions/central-empire/capital/arenarea/arena-of-fate/af-sand-a/StaticMeshes/SM_af-sand-a"),
		TEXT("/Game/Kit/Regions/central-empire/capital/arenarea/arena-of-fate/af-sand-b/StaticMeshes/SM_af-sand-b"),
		TEXT("/Game/Kit/Regions/central-empire/capital/arenarea/arena-of-fate/af-sand-c/StaticMeshes/SM_af-sand-c"),
	};
	TArray<UStaticMesh*> Meshes;
	for (const TCHAR* Path : Sands)
	{
		if (UStaticMesh* Mesh = LoadPiece(*this, Path))
		{
			Meshes.Add(Mesh);
		}
	}
	if (Meshes.Num() < 2)
	{
		return true;
	}
	const UMaterialInterface* First = Meshes[0]->GetMaterial(0);
	for (const UStaticMesh* Mesh : Meshes)
	{
		TestTrue(FString::Printf(TEXT("%s partage l'instance de matière"), *Mesh->GetName()), Mesh->GetMaterial(0) == First);
	}
	return true;
}

#endif
