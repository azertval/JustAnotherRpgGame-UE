// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

// Core avant le moteur.
#include "Core/Rpg/CharacterCreator.h"

#include "CoreMinimal.h"

#if WITH_EDITOR

/**
 * @brief Construit, par réflexion, le graphe de l'objet personnalisable Mutable d'un créateur
 *        (LOT-1015). Éditeur seulement : le graphe est une donnée d'éditeur.
 *
 * Le plugin Mutable (5.8.3) n'expose publiquement que la création de l'objet et sa compilation ;
 * les classes de nœuds sont privées. Elles sont des `UCLASS` : on les retrouve par leur chemin,
 * on crée les nœuds par `NewObject`, on écrit leurs propriétés par `ImportText`, on relie les
 * broches par le schéma du plugin, puis on compile de façon synchrone et on enregistre le paquet.
 */
namespace JadgCreatorGraph
{
	enum class EBuild
	{
		Built,
		Kept,
		Failed
	};

	/// Construit (ou garde, si l'empreinte de la description n'a pas changé) l'objet personnalisable.
	EBuild Build(const core::CharacterCreator& Creator, bool bForce, FString& OutError);
}

#endif
