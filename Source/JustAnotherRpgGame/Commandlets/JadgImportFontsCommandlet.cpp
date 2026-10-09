// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Ui/UiStyle.h"

#include <string>

#include "Commandlets/JadgImportFontsCommandlet.h"

#include "Bridge/JadgPaths.h"
#include "Engine/FontFace.h"
#include "JustAnotherRpgGame.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Misc/Paths.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"

UJadgImportFontsCommandlet::UJadgImportFontsCommandlet()
{
	IsClient = false;
	IsServer = false;
	IsEditor = true;
	LogToConsole = true;
}

int32 UJadgImportFontsCommandlet::Main(const FString& Params)
{
#if WITH_EDITORONLY_DATA
	const FString Assets = FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Assets"));
	const core::UiStyleResult Style = core::loadUiStyle(FJadgPaths::ToPath(FPaths::Combine(Assets, TEXT("UI"), TEXT("style.json"))));
	if (!Style.ok())
	{
		UE_LOG(LogJadg, Error, TEXT("[Polices] style illisible : %s"), *FJadgPaths::ToFString(Style.errors.front()));
		return 1;
	}
	int32 Written = 0;
	int32 Kept = 0;
	for (const auto& [Role, Relative] : Style.style.fonts)
	{
		const FString Source = FPaths::Combine(Assets, FJadgPaths::ToFString(Relative));
		TArray<uint8> Bytes;
		if (!FFileHelper::LoadFileToArray(Bytes, *Source))
		{
			UE_LOG(LogJadg, Error, TEXT("[Polices] %s : %s ne se lit pas"), *FJadgPaths::ToFString(Role), *Source);
			return 1;
		}
		const FString PackageName = TEXT("/Game/UI/Fonts/") + FPaths::GetBaseFilename(Source);
		const FString Name = FPackageName::GetShortName(PackageName);
		UPackage* Package = CreatePackage(*PackageName);
		Package->FullyLoad();
		UFontFace* Face = FindObject<UFontFace>(Package, *Name);
		if (Face != nullptr && Face->FontFaceData->HasData() && Face->FontFaceData->GetData() == Bytes)
		{
			++Kept;
			continue;
		}
		if (Face == nullptr)
		{
			Face = NewObject<UFontFace>(Package, FName(*Name), RF_Public | RF_Standalone);
		}
		Face->InitializeFromBulkData(Source, EFontHinting::Default, Bytes.GetData(), Bytes.Num());
		const FString FileName = FPackageName::LongPackageNameToFilename(PackageName, FPackageName::GetAssetPackageExtension());
		FSavePackageArgs SaveArgs;
		SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
		if (!UPackage::SavePackage(Package, Face, *FileName, SaveArgs))
		{
			UE_LOG(LogJadg, Error, TEXT("[Polices] enregistrement refusé : %s"), *FileName);
			return 1;
		}
		++Written;
	}
	UE_LOG(LogJadg, Display, TEXT("[Polices] %d écrite(s), %d à jour"), Written, Kept);
	return 0;
#else
	return 1;
#endif
}
