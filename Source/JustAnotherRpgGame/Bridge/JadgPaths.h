// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <filesystem>
#include <string>

#include "CoreMinimal.h"

/**
 * @brief Où sont les données de contenu, et comment passer d'une chaîne du moteur à une chaîne
 *        de Core.
 *
 * Les données restent en JSON sous `Source/Elements/` (D-52, LOT-1014) : aucune `DataTable`, aucun
 * `.uasset` de données. Core les lit par `std::filesystem::path` ; le moteur ne fait que lui dire
 * où elles sont.
 */
struct FJadgPaths
{
	/// `<projet>/Source/Elements`, en chemin absolu du moteur (séparateurs `/`).
	static FString ElementsDir();

	/// `<projet>/Source/Elements/Rpg`, prêt pour les lecteurs de Core.
	static std::filesystem::path RpgRoot();

	/// Un chemin du moteur vers un chemin de Core (UTF-16 → chemin natif).
	static std::filesystem::path ToPath(const FString& EnginePath);

	/// Une chaîne UTF-8 de Core vers une chaîne du moteur.
	static FString ToFString(const std::string& Utf8);
};
