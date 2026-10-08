// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"

namespace core
{
	struct GameOptions;
}

/**
 * @brief Les options du jeu, du fichier texte au moteur (LOT-1014).
 *
 * Core lit le fichier (`core::loadGameOptions`, `Core/Data/GameOptions.h`) ; ce pont dit où il
 * est et applique ce qui est lu. Deux fichiers, lus l'un sur l'autre : celui du dépôt
 * (`Source/Elements/Options/options.json`, les valeurs d'usine), puis celui du poste
 * (`Saved/Options/options.json`), s'il existe.
 *
 * | Option | Atteint |
 * |---|---|
 * | échelle de rendu | `r.ScreenPercentage` |
 * | qualité des ombres | `sg.ShadowQuality` |
 * | volume | le multiplicateur de volume de l'application |
 * | définition, plein écran | la fenêtre du jeu, avant sa création |
 *
 * La définition ne s'applique que dans un jeu qui a une fenêtre à lui : ni dans l'éditeur, ni
 * dans un commandlet, ni sans processeur graphique. Une définition donnée sur la ligne de
 * commande (`-ResX`, `-ResY`) l'emporte : c'est le moteur qui la lit, à la création de la fenêtre.
 */
struct FJadgOptions
{
	/// Le fichier d'usine, suivi par le dépôt.
	static FString FactoryFile();

	/// Le fichier du poste, hors du dépôt. Peut ne pas exister.
	static FString PlayerFile();

	/**
	 * @brief Lit les options d'usine, puis celles du poste par-dessus.
	 * @return Le nombre d'erreurs de lecture, chacune journalisée ; un fichier d'usine absent en
	 *         est une, un fichier du poste absent n'en est pas une.
	 */
	static int32 Read(core::GameOptions& OutOptions);

	/// Applique les options au moteur (voir la table).
	static void Apply(const core::GameOptions& Options);
};
