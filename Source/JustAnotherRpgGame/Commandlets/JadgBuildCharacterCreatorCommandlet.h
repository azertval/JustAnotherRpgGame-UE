// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"

#include "JadgBuildCharacterCreatorCommandlet.generated.h"

/**
 * @brief Construit le créateur de personnage — l'objet personnalisable Mutable — depuis sa
 *        description texte, sans fenêtre (LOT-1015, D-63, D-52).
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject -run=JadgBuildCharacterCreator [-JadgCreator=humanoid] [-JadgForce]
 *
 * Le graphe d'un objet personnalisable est un asset d'éditeur ; ses classes de nœuds sont privées
 * au plugin (Unreal 5.8.3). Le commandlet les retrouve **par réflexion** — classe par son chemin
 * (`/Script/CustomizableObjectEditor.…`), propriétés par leur nom, broches par leur nom ou leur
 * catégorie — et relie le graphe par le schéma du plugin, comme l'éditeur le ferait à la souris.
 * La description (`Source/Elements/Assets/Characters/<id>.json`) donne les corps ; chaque corps
 * devient un composant squelettique, et un paramètre de choix `Body` les commute.
 *
 * Rejoué sans changement de la description, le commandlet ne reconstruit rien (empreinte de la
 * description écrite dans l'asset) ; `-JadgForce` reconstruit. Sort en 1 à la première erreur.
 */
UCLASS()
class UJadgBuildCharacterCreatorCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	UJadgBuildCharacterCreatorCommandlet();

	virtual int32 Main(const FString& Params) override;
};
