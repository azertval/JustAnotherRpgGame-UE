// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Combat/CombatSpace.h"

#include <optional>
#include <vector>

#include "CoreMinimal.h"

class AJadgMapFrame;
class UWorld;

/**
 * @brief L'espace de combat du moteur (`core::CombatSpace`, LOT-1017) : le maillage de navigation
 *        pour les chemins et les budgets, les rayons pour la vue et le sol, un balayage pour la
 *        place libre.
 *
 * Les mètres de Core se rapportent au repère de la carte (`AJadgMapFrame` : le coin de la case
 * (0, 0), l'est et le sud) ; la hauteur est celle du monde au-dessus de ce repère. Les règles ne
 * voient que l'interface : ce qui vient du moteur est ici, et nulle part ailleurs dans Core.
 *
 * Ce que le moteur ne sait pas encore faire : exclure un volume (un ennemi) du maillage le temps
 * d'une requête. Les volumes `blocking` d'une requête ne sont donc pris en compte qu'à l'arrivée
 * (on ne finit pas dessus), pas sur le trajet ; un modificateur de navigation par combattant est
 * le chemin à prendre au sous-lot 3.
 */
class FJadgCombatSpace final : public core::CombatSpace
{
public:
	FJadgCombatSpace(UWorld* InWorld, const AJadgMapFrame* InFrame);

	/// Le point du monde d'un point de Core.
	[[nodiscard]] FVector ToWorld(core::Meters3 Point) const;
	/// Le point de Core d'un point du monde.
	[[nodiscard]] core::Meters3 FromWorld(const FVector& Point) const;

	[[nodiscard]] float groundHeight(float X, float Y) const override;
	[[nodiscard]] bool isClear(const core::Volume& Volume, core::Locomotion Locomotion) const override;
	[[nodiscard]] bool lineOfSight(core::Meters3 From, core::Meters3 To) const override;
	[[nodiscard]] std::optional<core::Route> route(const core::RouteQuery& Query) const override;
	[[nodiscard]] std::vector<core::Destination> candidates(const core::RouteQuery& Query) const override;

private:
	[[nodiscard]] bool OverlapsBlocking(core::Meters3 Point, const core::RouteQuery& Query) const;

	UWorld* World;
	const AJadgMapFrame* Frame;
};
