// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Widgets/SWidget.h"

/**
 * @brief L'écran de chargement : l'illustration de référence du lieu, son nom, ce qui se prépare et
 *        un indicateur qui tourne — le joueur voit que la carte se charge et que le jeu n'a pas
 *        planté (demande de l'auteur du 20 octobre 2026).
 *
 * Deux temps, le même écran :
 *
 * - **pendant le chargement de la carte**, quand le fil du jeu est pris : le lecteur de films du
 *   moteur le dessine sur son propre fil (`Install`, `OnPrepareLoadingScreen`, hors éditeur) ;
 * - **après**, tant que le monde n'est pas prêt — cellules World Partition chargées, navigation
 *   prête, images revenues à une cadence normale : le HUD le garde par-dessus le jeu
 *   (`AJadgHud`), aussi dans l'éditeur (Play In Editor).
 *
 * Les illustrations et le nom de chaque lieu sont dans `Source/Elements/Assets/UI/loading.json`
 * (`scripts/assetsGeneration/prepare_loading_screens.py`, découpées dans la planche du lieu), lues
 * sur le disque : l'écran ne dépend d'aucun asset du moteur. D'un chargement à l'autre, les
 * illustrations d'un lieu viennent tour à tour.
 */
class FJadgLoadingScreen
{
public:
	/// Branche l'écran sur le lecteur de films du moteur (au lancement, une fois ; hors éditeur).
	static void Install();

	/// La carte de Core que le prochain chargement ouvre (son illustration) ; à défaut, la carte de
	/// lancement du jeu.
	static void SetNextMap(const FString& MapId);

	/// L'écran pour une carte de Core, son état lu à chaque image.
	static TSharedRef<SWidget> Make(const FString& MapId, TAttribute<FText> Status);

	/// Le chargement fini : le suivant montre l'illustration suivante du lieu.
	static void Advance();

private:
	static FString NextMap;
	static int32 Shown;
};
