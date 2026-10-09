// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"

/**
 * @brief Les textes du jeu dans le système de texte du moteur (LOT-1020).
 *
 * Chaque catalogue `Source/Elements/Localization/<langue>.lang` (`core::parseTextCatalog`) devient
 * une **table de chaînes** du moteur, `Jadg.<langue>`, enregistrée au premier appel ; un texte se
 * prend en `FText` par sa clé dans la table de la langue choisie (`FText::FromStringTable`), et
 * ses trous `%1`, `%2` s'écrivent `{0}`, `{1}` (`core::toEngineFormat`) pour `FText::Format`.
 *
 * Une clé absente de la langue choisie se prend dans le français, la langue de référence ; absente
 * des deux, l'écran affiche la clé elle-même — elle se voit, au lieu de disparaître.
 *
 * Changer de langue (l'écran Options, `interface.language`) change la table où se prennent les
 * textes : les écrans se reconstruisent (`AJadgHud::RebuildScreens`).
 */
struct FJadgTexts
{
	/// Les langues dont le dépôt porte un catalogue, dans l'ordre où l'écran Options les propose.
	static const TArray<FString>& Languages();

	/// La langue choisie : « fr » tant que rien n'a été réglé.
	static FString Language();

	/// Choisit la langue @p Code ; sans effet si elle n'a pas de catalogue.
	static void SetLanguage(const FString& Code);

	/// Le texte de la clé @p Key dans la langue choisie.
	static FText Get(const FString& Key);

	/// Le texte de la clé @p Key, ses trous remplis dans l'ordre.
	static FText Format(const FString& Key, const TArray<FText>& Arguments);

	/// Le texte de la clé @p Key dans la langue @p Code, sans regarder la langue choisie (les tests).
	static FText In(const FString& Code, const FString& Key);

	/// Vrai si la clé existe dans le catalogue de la langue @p Code.
	static bool Has(const FString& Code, const FString& Key);

	/// Le nombre de textes du catalogue de la langue @p Code ; 0 s'il ne s'est pas lu.
	static int32 Count(const FString& Code);
};

/// Raccourci des écrans : le texte d'une clé.
inline FText JadgText(const TCHAR* Key)
{
	return FJadgTexts::Get(Key);
}
