// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

using System.IO;
using UnrealBuildTool;

/// <summary>
/// Le module du jeu : la bibliothèque des règles (`Core/`, sans une ligne du moteur) et le code
/// qui la relie à Unreal (LOT-1014).
///
/// Core vit **dans** ce module (`Source/JustAnotherRpgGame/Core/`) plutôt que dans un module à
/// part : dans une construction d'éditeur, chaque module est une DLL, et un module séparé aurait
/// exigé une macro d'export sur chacune des classes de Core — c'est-à-dire la réécriture que la
/// passation interdit. Les sources se compilent telles quelles ; leurs inclusions
/// (`"Core/Rpg/Party.h"`) se résolvent depuis la racine du module.
/// </summary>
public class JustAnotherRpgGame : ModuleRules
{
	public JustAnotherRpgGame(ReadOnlyTargetRules Target) : base(Target)
	{
		// Pas d'en-tête précompilé partagé ni de compilation unitaire : l'un et l'autre
		// injecteraient les en-têtes du moteur (et ses macros `check`, `verify`, `ensure`) dans
		// les unités de Core, qui n'en veulent pas. Chaque .cpp inclut ce qu'il utilise.
		PCHUsage = PCHUsageMode.NoPCHs;
		bUseUnity = false;

		// Core lit son JSON avec nlohmann, qui signale par exception ; `Core/Ecs/World.h` range
		// ses composants par `typeid`. Le moteur compile sans l'un ni l'autre par défaut.
		bEnableExceptions = true;
		bUseRTTI = true;
		CppStandard = CppStandardVersion.Cpp20;

		// Core compile sous /W4 /WX dans sa construction CMake ; le moteur classe deux familles
		// d'avertissements en erreurs que Core n'a jamais eu à respecter. Avertissements, pas
		// erreurs, le temps de la passation.
		CppCompileWarningSettings.ShadowVariableWarningLevel = WarningLevel.Warning;
		CppCompileWarningSettings.UndefinedIdentifierWarningLevel = WarningLevel.Warning;

		// Racine d'inclusion de Core : "Core/<Module>/<Fichier>.h", jamais un nom seul.
		PublicIncludePaths.Add(ModuleDirectory);
		// nlohmann/json (en-tête unique, v3.11.3, MIT) : vendu dans Source/ThirdParty, en chemin
		// système pour que ses avertissements ne remontent pas.
		PublicSystemIncludePaths.Add(Path.Combine(ModuleDirectory, "..", "ThirdParty", "nlohmann", "include"));

		// Le numéro de version a une seule source, `VERSION.txt` à la racine du dépôt : la
		// construction CMake des tests de Core lit le même fichier.
		string VersionFile = Path.GetFullPath(Path.Combine(ModuleDirectory, "..", "..", "VERSION.txt"));
		ExternalDependencies.Add(VersionFile);
		PublicDefinitions.Add("JADG_VERSION=\"" + File.ReadAllText(VersionFile).Trim() + "\"");

		// AIModule et NavigationSystem : la marche au clic sur le maillage de navigation (LOT-1012) ;
		// RenderCore et RHI : les temps de trame que la mesure de cadence relève.
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput", "AIModule", "NavigationSystem", "RenderCore", "RHI" });

		PrivateDependencyModuleNames.AddRange(new string[] { });

		// La brosse d'un volume ne se dessine que par l'éditeur (Scene/JadgSceneBuild).
		if (Target.bBuildEditor)
		{
			PrivateDependencyModuleNames.Add("UnrealEd");
		}
	}
}
