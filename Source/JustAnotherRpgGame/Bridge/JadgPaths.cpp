// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Bridge/JadgPaths.h"

#include "Misc/Paths.h"

FString FJadgPaths::ElementsDir()
{
	return FPaths::ConvertRelativePathToFull(FPaths::Combine(FPaths::ProjectDir(), TEXT("Source"), TEXT("Elements")));
}

std::filesystem::path FJadgPaths::RpgRoot()
{
	return ToPath(ElementsDir()) / "Rpg";
}

std::filesystem::path FJadgPaths::ToPath(const FString& EnginePath)
{
	// TCHAR est wchar_t sous Windows : le chemin natif se construit sans conversion de contenu.
	return std::filesystem::path(std::wstring(TCHAR_TO_WCHAR(*EnginePath)));
}

FString FJadgPaths::ToFString(const std::string& Utf8)
{
	return FString(UTF8_TO_TCHAR(Utf8.c_str()));
}
