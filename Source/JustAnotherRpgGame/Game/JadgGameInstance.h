// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Engine/GameInstance.h"

#include "JadgGameInstance.generated.h"

/**
 * @brief L'instance du jeu : ce qui se fait une fois, au lancement (LOT-1014).
 *
 * Elle lit les options du jeu dans leur fichier texte et les applique (`FJadgOptions`), avant
 * que le moteur ne crée la fenêtre. Déclarée dans `Config/DefaultEngine.ini`
 * (`GameInstanceClass`).
 */
UCLASS()
class UJadgGameInstance : public UGameInstance
{
	GENERATED_BODY()

public:
	virtual void Init() override;

	/// Vrai une fois le menu du titre montré : il ne s'ouvre qu'au lancement (LOT-1020).
	bool bTitleShown = false;
};
