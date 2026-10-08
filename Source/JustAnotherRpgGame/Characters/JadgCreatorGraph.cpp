// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Characters/JadgCreatorGraph.h"

#if WITH_EDITOR

#include "Bridge/JadgPaths.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraph/EdGraphSchema.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/AssetUserData.h"
#include "FileHelpers.h"
#include "JustAnotherRpgGame.h"
#include "Materials/MaterialInterface.h"
#include "Misc/PackageName.h"
#include "Misc/SecureHash.h"
#include "MuCO/CustomizableObject.h"
#include "MuCOE/EdGraphSchema_CustomizableObject.h"
#include "Factories/Factory.h"
#include "UObject/Package.h"
#include "UObject/SavePackage.h"
#include "UObject/UnrealType.h"
#include "UObject/LinkerLoad.h"

namespace
{
	using PC = UEdGraphSchema_CustomizableObject;
	constexpr const TCHAR* NodeModule = TEXT("/Script/CustomizableObjectEditor.");

	/// L'empreinte de la description, écrite dans une donnée d'utilisateur de l'asset pour ne pas
	/// reconstruire ce qui n'a pas changé.
	FString DescriptionHash(const core::CharacterCreator& Creator)
	{
		FString Texte = FJadgPaths::ToFString(Creator.asset + "|" + Creator.component + "|" + Creator.skeleton);
		for (const auto& [Nom, Chemin] : Creator.bodies)
		{
			Texte += FJadgPaths::ToFString("|" + Nom + "=" + Chemin);
		}
		return FMD5::HashAnsiString(*Texte);
	}

	UClass* NodeClass(const TCHAR* Name, FString& OutError)
	{
		UClass* Class = FindObject<UClass>(nullptr, *(FString(NodeModule) + Name));
		if (Class == nullptr)
		{
			OutError = FString::Printf(TEXT("classe de nœud introuvable : %s"), Name);
		}
		return Class;
	}

	UEdGraphNode* AddNode(UEdGraph& Graph, const TCHAR* ClassName, FString& OutError)
	{
		UClass* Class = NodeClass(ClassName, OutError);
		if (Class == nullptr)
		{
			return nullptr;
		}
		UEdGraphNode* Node = NewObject<UEdGraphNode>(&Graph, Class, NAME_None, RF_Transactional);
		Graph.AddNode(Node, false, false);
		Node->CreateNewGuid();
		Node->PostPlacedNewNode();
		Node->AllocateDefaultPins();
		return Node;
	}

	/// Écrit une propriété par son texte (`ImportText`), ce qui vaut pour une chaîne, un nom, un
	/// objet (par son chemin), un tableau de structures.
	bool SetProperty(UEdGraphNode& Node, const TCHAR* Name, const FString& Text, FString& OutError)
	{
		FProperty* Property = Node.GetClass()->FindPropertyByName(Name);
		if (Property == nullptr)
		{
			OutError = FString::Printf(TEXT("%s : propriété %s introuvable"), *Node.GetClass()->GetName(), Name);
			return false;
		}
		void* Value = Property->ContainerPtrToValuePtr<void>(&Node);
		if (Property->ImportText_Direct(*Text, Value, &Node, PPF_None) == nullptr)
		{
			OutError = FString::Printf(TEXT("%s.%s : « %s » refusé"), *Node.GetClass()->GetName(), Name, *Text);
			return false;
		}
		return true;
	}

	UEdGraphPin* FindPin(UEdGraphNode& Node, EEdGraphPinDirection Direction, const FName& Category, const FName& Name)
	{
		for (UEdGraphPin* Pin : Node.Pins)
		{
			if (Pin->Direction != Direction)
			{
				continue;
			}
			if (!Name.IsNone() && Pin->PinName == Name)
			{
				return Pin;
			}
			if (Name.IsNone() && Pin->PinType.PinCategory == Category && Pin->LinkedTo.Num() == 0)
			{
				return Pin;
			}
		}
		return nullptr;
	}

	FString PinList(const UEdGraphNode& Node)
	{
		FString Liste;
		for (const UEdGraphPin* Pin : Node.Pins)
		{
			Liste += FString::Printf(TEXT(" [%s %s:%s]"), Pin->Direction == EGPD_Input ? TEXT("in") : TEXT("out"),
				*Pin->PinType.PinCategory.ToString(), *Pin->PinName.ToString());
		}
		return Liste;
	}

	bool Link(const UEdGraphSchema& Schema, UEdGraphNode& From, const FName& OutCategory, const FName& OutName, UEdGraphNode& To,
		const FName& InCategory, const FName& InName, FString& OutError)
	{
		UEdGraphPin* Out = FindPin(From, EGPD_Output, OutCategory, OutName);
		UEdGraphPin* In = FindPin(To, EGPD_Input, InCategory, InName);
		if (Out == nullptr || In == nullptr)
		{
			OutError = FString::Printf(TEXT("broche introuvable : %s(%s/%s)%s -> %s(%s/%s)%s"), *From.GetClass()->GetName(),
				*OutCategory.ToString(), *OutName.ToString(), *PinList(From), *To.GetClass()->GetName(), *InCategory.ToString(),
				*InName.ToString(), *PinList(To));
			return false;
		}
		if (!Schema.TryCreateConnection(Out, In))
		{
			OutError = FString::Printf(TEXT("liaison refusée par le schéma : %s.%s -> %s.%s"), *From.GetClass()->GetName(),
				*Out->PinName.ToString(), *To.GetClass()->GetName(), *In->PinName.ToString());
			return false;
		}
		return true;
	}

	UEdGraph* SourceGraph(UCustomizableObject& Object)
	{
		FObjectProperty* Property = CastField<FObjectProperty>(Object.GetClass()->FindPropertyByName(TEXT("Source")));
		return Property ? Cast<UEdGraph>(Property->GetObjectPropertyValue_InContainer(&Object)) : nullptr;
	}

	UEdGraphNode* RootNode(UEdGraph& Graph, FString& OutError)
	{
		UClass* ObjectClass = NodeClass(TEXT("CustomizableObjectNodeObject"), OutError);
		for (UEdGraphNode* Node : Graph.Nodes)
		{
			if (ObjectClass != nullptr && Node->IsA(ObjectClass))
			{
				return Node;
			}
		}
		OutError = TEXT("le graphe n'a pas de nœud Objet racine");
		return nullptr;
	}

	/// Un corps : maillage -> sections -> maillage squelettique -> objet -> composant.
	UEdGraphNode* BodyComponent(UEdGraph& Graph, const UEdGraphSchema& Schema, const FString& Option, const FString& MeshPath,
		const FString& ComponentName, FString& OutError)
	{
		USkeletalMesh* Mesh = LoadObject<USkeletalMesh>(nullptr, *MeshPath);
		if (Mesh == nullptr)
		{
			OutError = FString::Printf(TEXT("corps %s : maillage introuvable %s"), *Option, *MeshPath);
			return nullptr;
		}
		UEdGraphNode* MeshNode = AddNode(Graph, TEXT("CustomizableObjectNodeSkeletalMesh"), OutError);
		if (MeshNode == nullptr || !SetProperty(*MeshNode, TEXT("SkeletalMesh"), Mesh->GetPathName(), OutError))
		{
			return nullptr;
		}
		MeshNode->ReconstructNode();

		UEdGraphNode* Make = AddNode(Graph, TEXT("CONodeSkeletalMeshMake_V2"), OutError);
		if (Make == nullptr)
		{
			return nullptr;
		}
		const int32 Sections = Mesh->GetMaterials().Num();
		for (int32 Section = 0; Section < Sections; ++Section)
		{
			UEdGraphNode* SectionNode = AddNode(Graph, TEXT("CONodeSkeletalMeshSection"), OutError);
			if (SectionNode == nullptr)
			{
				return nullptr;
			}
			if (UMaterialInterface* Material = Mesh->GetMaterials()[Section].MaterialInterface)
			{
				if (!SetProperty(*SectionNode, TEXT("Material"), Material->GetPathName(), OutError))
				{
					return nullptr;
				}
				SectionNode->ReconstructNode();
			}
			const FName MeshPin(*FString::Printf(TEXT("LOD 0 - Section %d - Mesh"), Section));
			if (!Link(Schema, *MeshNode, PC::PC_Mesh, MeshPin, *SectionNode, PC::PC_Mesh, NAME_None, OutError) ||
				!Link(Schema, *SectionNode, PC::PC_MeshSection, NAME_None, *Make, PC::PC_MeshSection, TEXT("LOD 0"), OutError))
			{
				return nullptr;
			}
		}

		UEdGraphNode* ObjectMake = AddNode(Graph, TEXT("CONodeSkeletalMeshObjectMake"), OutError);
		UEdGraphNode* Component = ObjectMake ? AddNode(Graph, TEXT("CONodeComponentSkeletalMesh"), OutError) : nullptr;
		if (Component == nullptr)
		{
			return nullptr;
		}
		if (!SetProperty(*Component, TEXT("ComponentName"), ComponentName, OutError) ||
			!SetProperty(*Component, TEXT("ReferenceSkeletalMesh"), Mesh->GetPathName(), OutError))
		{
			return nullptr;
		}
		Component->ReconstructNode();
		if (!Link(Schema, *Make, PC::PC_SkeletalMesh, NAME_None, *ObjectMake, PC::PC_SkeletalMesh, NAME_None, OutError) ||
			!Link(Schema, *ObjectMake, PC::PC_SkeletalMesh_Passthrough, NAME_None, *Component, PC::PC_SkeletalMesh_Passthrough,
				NAME_None, OutError))
		{
			return nullptr;
		}
		return Component;
	}

	bool Populate(UCustomizableObject& Object, const core::CharacterCreator& Creator, FString& OutError)
	{
		UEdGraph* Graph = SourceGraph(Object);
		if (Graph == nullptr)
		{
			OutError = TEXT("l'objet personnalisable n'a pas de graphe source");
			return false;
		}
		const UEdGraphSchema* Schema = Graph->GetSchema();
		UEdGraphNode* Root = RootNode(*Graph, OutError);
		if (Root == nullptr || !SetProperty(*Root, TEXT("ObjectName"), FJadgPaths::ToFString(Creator.id), OutError))
		{
			return false;
		}

		// Le paramètre de choix du corps, et le commutateur de composants qu'il pilote.
		FString Values = TEXT("(");
		for (const auto& [Option, Chemin] : Creator.bodies)
		{
			Values += FString::Printf(TEXT("(Name=\"%s\"),"), *FJadgPaths::ToFString(Option));
		}
		Values.RemoveFromEnd(TEXT(","));
		Values += TEXT(")");
		UEdGraphNode* Enum = AddNode(*Graph, TEXT("CustomizableObjectNodeEnumParameter"), OutError);
		if (Enum == nullptr || !SetProperty(*Enum, TEXT("ParameterName"), TEXT("Body"), OutError) ||
			!SetProperty(*Enum, TEXT("Values"), Values, OutError))
		{
			return false;
		}
		Enum->ReconstructNode();
		// Le commutateur ne reçoit sa catégorie de broches qu'au chargement d'un asset (fixup) : à la
		// création, on la lui donne avant de refaire ses broches.
		UEdGraphNode* Switch = AddNode(*Graph, TEXT("CustomizableObjectNodeComponentSwitch"), OutError);
		if (Switch == nullptr || !SetProperty(*Switch, TEXT("PinType"), PC::PC_Component.ToString(), OutError))
		{
			return false;
		}
		Switch->ReconstructNode();
		if (!Link(*Schema, *Enum, PC::PC_Enum, NAME_None, *Switch, PC::PC_Enum, TEXT("Switch Parameter"), OutError))
		{
			return false;
		}
		Switch->ReconstructNode();

		const FString ComponentName = FJadgPaths::ToFString(Creator.component);
		for (const auto& [Option, Chemin] : Creator.bodies)
		{
			UEdGraphNode* Component =
				BodyComponent(*Graph, *Schema, FJadgPaths::ToFString(Option), FJadgPaths::ToFString(Chemin), ComponentName, OutError);
			if (Component == nullptr ||
				!Link(*Schema, *Component, PC::PC_Component, TEXT("Component"), *Switch, PC::PC_Component,
					FName(*FJadgPaths::ToFString(Option)), OutError))
			{
				return false;
			}
		}
		return Link(*Schema, *Switch, PC::PC_Component, NAME_None, *Root, PC::PC_Component, TEXT("Components"), OutError);
	}
} // namespace

JadgCreatorGraph::EBuild JadgCreatorGraph::Build(const core::CharacterCreator& Creator, bool bForce, FString& OutError)
{
	const FString AssetPath = FJadgPaths::ToFString(Creator.asset);
	const FString PackagePath = FPackageName::GetLongPackagePath(AssetPath);
	const FString AssetName = FPackageName::GetShortName(AssetPath);
	const FString Hash = DescriptionHash(Creator);

	const FString PackageName = PackagePath + TEXT("/") + AssetName;
	if (FPackageName::DoesPackageExist(PackageName))
	{
		if (UCustomizableObject* Existing = LoadObject<UCustomizableObject>(nullptr, *AssetPath))
		{
			const FString Stored = Existing->GetPackage()->GetMetaData().GetValue(Existing, TEXT("JadgDescriptionHash"));
			UE_LOG(LogJadg, Display, TEXT("[Createur] asset présent, empreinte %s, attendue %s"), *Stored, *Hash);
			if (!bForce && Stored == Hash)
			{
				return EBuild::Kept;
			}
			// On reconstruit à neuf : le paquet existant est écarté (renommé hors du chemin), pas
			// retouché ; son fichier est libéré pour que le nouveau s'enregistre à sa place.
			UPackage* OldPackage = Existing->GetPackage();
			ResetLoaders(OldPackage);
			Existing->Rename(nullptr, GetTransientPackage(), REN_DontCreateRedirectors | REN_NonTransactional);
			OldPackage->Rename(*(PackageName + TEXT("_Ancien")), nullptr, REN_DontCreateRedirectors | REN_NonTransactional);
			Existing->MarkAsGarbage();
		}
	}
	else if (UPackage* Stale = FindPackage(nullptr, *PackageName))
	{
		Stale->Rename(*(PackageName + TEXT("_Vide")), nullptr, REN_DontCreateRedirectors | REN_NonTransactional);
	}

	// La fonction de bibliothèque du plugin (`NewCustomizableObject`) synchronise l'explorateur de
	// contenu, qui n'existe pas sans fenêtre : on passe par la fabrique, comme elle, sans lui.
	UClass* FactoryClass = FindObject<UClass>(nullptr, TEXT("/Script/CustomizableObjectEditor.CustomizableObjectFactory"));
	UFactory* Factory = FactoryClass ? NewObject<UFactory>(GetTransientPackage(), FactoryClass) : nullptr;
	if (Factory == nullptr)
	{
		OutError = TEXT("fabrique CustomizableObjectFactory introuvable");
		return EBuild::Failed;
	}
	UPackage* Package = CreatePackage(*PackageName);
	Package->SetPackageFlags(PKG_NewlyCreated);
	Package->MarkAsFullyLoaded();
	UCustomizableObject* Object = Cast<UCustomizableObject>(Factory->FactoryCreateNew(
		UCustomizableObject::StaticClass(), Package, *AssetName, RF_Public | RF_Standalone, nullptr, GWarn));
	if (Object == nullptr)
	{
		OutError = FString::Printf(TEXT("création refusée : %s"), *AssetPath);
		return EBuild::Failed;
	}
	Package->MarkPackageDirty();
	if (!Populate(*Object, Creator, OutError))
	{
		return EBuild::Failed;
	}

	FCompileParams Compile;
	Compile.bAsync = false;
	Compile.bSkipIfCompiled = false;
	Compile.bSkipIfNotOutOfDate = false;
	Object->Compile(Compile);
	if (!Object->IsCompiled())
	{
		OutError = TEXT("la compilation synchrone n'a pas abouti (voir LogMutable)");
		return EBuild::Failed;
	}
	Object->GetPackage()->GetMetaData().SetValue(Object, TEXT("JadgDescriptionHash"), *Hash);

	const FString FileName = FPackageName::LongPackageNameToFilename(PackageName, FPackageName::GetAssetPackageExtension());
	FSavePackageArgs SaveArgs;
	SaveArgs.TopLevelFlags = RF_Public | RF_Standalone;
	if (!UPackage::SavePackage(Object->GetPackage(), Object, *FileName, SaveArgs))
	{
		OutError = FString::Printf(TEXT("enregistrement refusé : %s"), *FileName);
		return EBuild::Failed;
	}
	return EBuild::Built;
}

#endif
