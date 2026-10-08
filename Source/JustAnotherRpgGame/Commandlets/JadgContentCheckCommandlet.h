// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"

#include "JadgContentCheckCommandlet.generated.h"

/**
 * @brief Lit les données de contenu par les lecteurs de Core, sans fenêtre, et sort en 1 à la
 *        première erreur.
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject -run=JadgContentCheck
 *
 * C'est le critère du LOT-1014 : « une partie se crée depuis les données de contenu : le groupe
 * préformé de D-28 a ses quatre fiches, valeur pour valeur, lues dans le moteur ». Le commandlet
 * charge les catalogues de `Rpg/`, construit les fiches de `Rpg/characters/` et écrit pour
 * chacune ce que la page imprimée porte : niveau, caractéristiques, points de vie, classe
 * d'armure. Les valeurs attendues restent dans les tests de Core (`test_premade_characters.cpp`) ;
 * ici on vérifie que le moteur lit les mêmes fichiers et obtient des fiches sans erreur.
 */
UCLASS()
class UJadgContentCheckCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	UJadgContentCheckCommandlet();

	virtual int32 Main(const FString& Params) override;
};
