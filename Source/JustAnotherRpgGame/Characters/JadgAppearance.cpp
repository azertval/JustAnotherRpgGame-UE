// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur.
#include "Core/Data/JsonDocument.h"
#include "Core/Rpg/Appearance.h"
#include "Core/Rpg/CharacterCreator.h"

#include <string>

#include "Characters/JadgAppearance.h"

#include "Animation/AnimSequence.h"
#include "Bridge/JadgPaths.h"
#include "Characters/JadgWalker.h"
#include "Components/CapsuleComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "JustAnotherRpgGame.h"
#include "Misc/PackageName.h"
#include "MuCO/CustomizableObject.h"
#include "MuCO/CustomizableObjectInstance.h"
#include "MuCO/CustomizableSkeletalComponent.h"

namespace
{
	std::filesystem::path CreatorFile(const std::string& Id)
	{
		return FJadgPaths::ToPath(FJadgPaths::ElementsDir()) / "Assets" / "Characters" / (Id + ".json");
	}

	/// Le chemin de contenu d'une pièce au maître (`Weapons/brawler-axe`), lu dans le manifeste.
	FString MasterAsset(const std::string& PieceId)
	{
		const std::filesystem::path Manifest = FJadgPaths::ToPath(FJadgPaths::ElementsDir()) / "Assets" / "Master" / "manifest.json";
		const core::JsonDocument Document = core::readJsonObjectFromFile(Manifest, 0);
		if (!Document.ok())
		{
			return {};
		}
		const auto Pieces = Document.root.find("pieces");
		if (Pieces == Document.root.end() || !Pieces->is_array())
		{
			return {};
		}
		for (const auto& Piece : *Pieces)
		{
			if (Piece.value("id", std::string{}) == PieceId)
			{
				return FJadgPaths::ToFString(Piece.value("asset", std::string{}));
			}
		}
		return {};
	}

	template <class T>
	T* LoadContent(const std::string& Path)
	{
		const FString Asset = FJadgPaths::ToFString(Path);
		return Asset.IsEmpty() ? nullptr : LoadObject<T>(nullptr, *Asset);
	}
} // namespace

bool JadgAppearance::CreatorIsBuilt(const FString& CreatorId)
{
	const core::CharacterCreatorReadResult Creator = core::readCharacterCreator(CreatorFile(TCHAR_TO_UTF8(*CreatorId)));
	return Creator.ok() && FPackageName::DoesPackageExist(FJadgPaths::ToFString(Creator.creator.asset));
}

bool JadgAppearance::Apply(AJadgWalker& Walker, const FString& Id, FString& OutError)
{
	const core::AppearanceReadResult Fiche =
		core::readAppearance(FJadgPaths::RpgRoot() / "appearances" / (std::string(TCHAR_TO_UTF8(*Id)) + ".json"));
	if (!Fiche.ok())
	{
		OutError = FJadgPaths::ToFString(Fiche.message);
		return false;
	}
	const core::Appearance& Apparence = Fiche.appearance;
	const core::CharacterCreatorReadResult Lue = core::readCharacterCreator(CreatorFile(Apparence.creator));
	if (!Lue.ok())
	{
		OutError = FJadgPaths::ToFString(Lue.message);
		return false;
	}
	const core::CharacterCreator& Creator = Lue.creator;
	const auto Body = Creator.bodies.find(Apparence.body);
	if (Body == Creator.bodies.end())
	{
		OutError = FString::Printf(TEXT("%s : corps « %s » inconnu du créateur %s"), *Id, *FJadgPaths::ToFString(Apparence.body),
			*FJadgPaths::ToFString(Creator.id));
		return false;
	}

	USkeletalMeshComponent* Mesh = Walker.GetMesh();
	USkeletalMesh* BodyMesh = LoadContent<USkeletalMesh>(Body->second);
	if (BodyMesh == nullptr)
	{
		OutError = FString::Printf(TEXT("%s : maillage du corps introuvable : %s"), *Id, *FJadgPaths::ToFString(Body->second));
		return false;
	}

	// Le corps : par l'objet personnalisable s'il est construit, sinon le maillage tel quel.
	UCustomizableObject* Creator_CO = LoadContent<UCustomizableObject>(Creator.asset);
	if (Creator_CO != nullptr)
	{
		UCustomizableObjectInstance* Instance = NewObject<UCustomizableObjectInstance>(&Walker);
		Instance->SetObject(Creator_CO);
		Instance->SetEnumParameterSelectedOption(TEXT("Body"), FJadgPaths::ToFString(Apparence.body));
		UCustomizableSkeletalComponent* Customizable = NewObject<UCustomizableSkeletalComponent>(&Walker);
		Customizable->SetComponentName(FName(*FJadgPaths::ToFString(Creator.component)));
		Customizable->SetCustomizableObjectInstance(Instance);
		Customizable->SetupAttachment(Mesh);
		Customizable->RegisterComponent();
		Customizable->UpdateSkeletalMeshAsync(true);
		Walker.bFromCreator = true;
	}
	if (Mesh->GetSkeletalMeshAsset() == nullptr || Creator_CO == nullptr)
	{
		Mesh->SetSkeletalMeshAsset(BodyMesh);
	}

	// Le mannequin du moteur regarde vers +Y et a les pieds à l'origine ; l'acteur avance vers +X.
	const float Half = Walker.GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight();
	Mesh->SetRelativeLocationAndRotation(FVector(0.0, 0.0, -Half), FRotator(0.0f, -90.0f, 0.0f));

	// Les clips, et l'instant d'impact que le combat attend.
	Walker.Clips.Empty();
	for (const auto& [Nom, Chemin] : Creator.clips)
	{
		if (UAnimSequence* Clip = LoadContent<UAnimSequence>(Chemin))
		{
			Walker.Clips.Add(FName(*FJadgPaths::ToFString(Nom)), Clip);
		}
	}
	Walker.IdleClip = Walker.Clips.FindRef(TEXT("idle"));
	Walker.WalkClip = Walker.Clips.FindRef(TEXT("walk"));
	Walker.ClipKeys.Empty();
	for (const auto& [Nom, Key] : Apparence.clipKeys)
	{
		Walker.ClipKeys.Add(FName(*FJadgPaths::ToFString(Nom)), Key);
	}

	// La taille : l'acteur à l'échelle de sa fiche, debout au même point du sol.
	const FVector Feet = Walker.Feet();
	const float Scale = Creator.referenceHeight > 0.0F ? Apparence.height / Creator.referenceHeight : 1.0F;
	Walker.SetActorScale3D(FVector(Scale));
	Walker.StandOn(Feet, Walker.GetActorRotation().Yaw);

	// L'arme de chaque main, accrochée à son socket (D-63).
	for (const auto& [Main, Piece] : Apparence.weapons)
	{
		const auto Socket = Creator.sockets.find(Main);
		UStaticMesh* Weapon = Socket == Creator.sockets.end() ? nullptr : LoadObject<UStaticMesh>(nullptr, *MasterAsset(Piece));
		if (Weapon == nullptr)
		{
			UE_LOG(LogJadg, Warning, TEXT("%s : arme %s introuvable pour %s"), *Id, *FJadgPaths::ToFString(Piece),
				*FJadgPaths::ToFString(Main));
			continue;
		}
		UStaticMeshComponent* Held = NewObject<UStaticMeshComponent>(&Walker);
		Held->SetStaticMesh(Weapon);
		Held->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		Held->SetupAttachment(Mesh, FName(*FJadgPaths::ToFString(Socket->second)));
		Held->RegisterComponent();
		Walker.Weapons.Add(Held);
	}
	return true;
}
