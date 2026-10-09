// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/Ui/TextCatalog.h"

#include <string>

#include "UI/JadgTexts.h"

#include "Bridge/JadgPaths.h"
#include "Internationalization/StringTable.h"
#include "Internationalization/StringTableCore.h"
#include "Internationalization/StringTableRegistry.h"
#include "JustAnotherRpgGame.h"
#include "Misc/Paths.h"

namespace
{
	const FString Reference(TEXT("fr"));

	struct FCatalogues
	{
		TArray<FString> Codes;
		TMap<FString, FStringTableRef> Tables;
		FString Chosen = Reference;

		FCatalogues()
		{
			// Les deux langues du jeu ; une langue de plus, c'est un fichier de plus et un nom ici.
			for (const TCHAR* Code : {TEXT("fr"), TEXT("en")})
			{
				const FString File = FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Localization"), FString(Code) + TEXT(".lang"));
				const core::TextTable Read = core::loadTextCatalog(FJadgPaths::ToPath(File));
				if (Read.empty())
				{
					UE_LOG(LogJadg, Error, TEXT("[Textes] %s ne se lit pas"), *File);
					continue;
				}
				FStringTableRef Table = FStringTable::NewStringTable();
				Table->SetNamespace(TEXT("Jadg"));
				for (const auto& [Key, Value] : Read)
				{
#if WITH_EDITORONLY_DATA
					Table->SetSourceString(FJadgPaths::ToFString(Key), FJadgPaths::ToFString(core::toEngineFormat(Value)), FString());
#else
					Table->SetSourceString(FJadgPaths::ToFString(Key), FJadgPaths::ToFString(core::toEngineFormat(Value)));
#endif
				}
				const FName Id = TableId(Code);
				FStringTableRegistry::Get().UnregisterStringTable(Id);
				FStringTableRegistry::Get().RegisterStringTable(Id, Table);
				Tables.Add(Code, Table);
				Codes.Add(Code);
				UE_LOG(LogJadg, Display, TEXT("[Textes] %s : %d texte(s), table %s"), Code, static_cast<int32>(Read.size()), *Id.ToString());
			}
		}

		static FName TableId(const FString& Code)
		{
			return FName(*(TEXT("Jadg.") + Code));
		}

		bool Has(const FString& Code, const FString& Key) const
		{
			const FStringTableRef* Table = Tables.Find(Code);
			return Table != nullptr && (*Table)->FindEntry(Key).IsValid();
		}

		FText Get(const FString& Code, const FString& Key) const
		{
			if (Has(Code, Key))
			{
				return FText::FromStringTable(TableId(Code), Key);
			}
			if (Code != Reference && Has(Reference, Key))
			{
				return FText::FromStringTable(TableId(Reference), Key);
			}
			return FText::FromString(Key);
		}
	};

	FCatalogues& Catalogues()
	{
		static FCatalogues Loaded;
		return Loaded;
	}
}

const TArray<FString>& FJadgTexts::Languages()
{
	return Catalogues().Codes;
}

FString FJadgTexts::Language()
{
	return Catalogues().Chosen;
}

void FJadgTexts::SetLanguage(const FString& Code)
{
	if (Catalogues().Tables.Contains(Code))
	{
		Catalogues().Chosen = Code;
	}
}

FText FJadgTexts::Get(const FString& Key)
{
	return Catalogues().Get(Catalogues().Chosen, Key);
}

FText FJadgTexts::Format(const FString& Key, const TArray<FText>& Arguments)
{
	FFormatOrderedArguments Ordered;
	for (const FText& Argument : Arguments)
	{
		Ordered.Add(Argument);
	}
	return FText::Format(Get(Key), Ordered);
}

FText FJadgTexts::In(const FString& Code, const FString& Key)
{
	return Catalogues().Get(Code, Key);
}

bool FJadgTexts::Has(const FString& Code, const FString& Key)
{
	return Catalogues().Has(Code, Key);
}

int32 FJadgTexts::Count(const FString& Code)
{
	const FStringTableRef* Table = Catalogues().Tables.Find(Code);
	if (Table == nullptr)
	{
		return 0;
	}
	int32 Total = 0;
	(*Table)->EnumerateSourceStrings([&Total](const FString&, const FString&) { ++Total; return true; });
	return Total;
}
