// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "Commandlets/Commandlet.h"
#include "CoreMinimal.h"

#include "JadgImportFontsCommandlet.generated.h"

/**
 * @brief Importe les polices des écrans en faces de police du moteur (LOT-1020).
 *
 *     UnrealEditor-Cmd.exe <projet>.uproject -run=JadgImportFonts -unattended -nosplash -nullrhi
 *
 * Chaque police que nomme `Source/Elements/Assets/UI/style.json` (section `fonts`) devient
 * `/Game/UI/Fonts/<fichier sans extension>`, une `UFontFace` dont les octets sont ceux du fichier
 * (`InitializeFromBulkData`). L'importeur du moteur (`FontFileImportFactory`) demande une fenêtre et
 * s'arrête sans elle : ce commandlet fait la même chose sans. Une face dont les octets sont déjà
 * ceux du fichier n'est pas réécrite. Code 1 si une police manque ou ne s'enregistre pas.
 */
UCLASS()
class UJadgImportFontsCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	UJadgImportFontsCommandlet();
	virtual int32 Main(const FString& Params) override;
};
