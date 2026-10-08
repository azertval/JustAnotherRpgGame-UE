// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"

class AJadgWalker;

/**
 * @brief Pose un personnage sur un acteur depuis sa fiche d'apparence (LOT-1015, D-63).
 *
 * La fiche (`Rpg/appearances/<id>.json`, lue par Core) et la description du créateur
 * (`Assets/Characters/<creator>.json`) donnent tout : le corps, choisi par le paramètre `Body` de
 * l'objet personnalisable Mutable (ou, si l'asset du créateur n'est pas construit sur le poste, le
 * maillage du corps posé directement), la taille (échelle de l'acteur par rapport à la taille de
 * référence du créateur), les six clips du moteur et leur instant d'impact, l'arme de chaque main
 * accrochée à son socket depuis les maîtres de `Master/Weapons`.
 */
namespace JadgAppearance
{
	/// Applique la fiche @p Id à @p Walker. Faux, avec la raison, si la fiche ou le créateur ne se lit pas.
	bool Apply(AJadgWalker& Walker, const FString& Id, FString& OutError);

	/// Vrai si l'objet personnalisable du créateur est construit sur le poste (sinon, le corps se pose tel quel).
	bool CreatorIsBuilt(const FString& CreatorId);
}
