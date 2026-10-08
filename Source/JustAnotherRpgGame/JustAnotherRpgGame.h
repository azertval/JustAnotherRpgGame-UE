// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

/// Catégorie de journal du jeu côté moteur ; les messages de Core y sont redirigés par
/// `FJadgCoreLogBridge` (voir Bridge/JadgLog.h).
DECLARE_LOG_CATEGORY_EXTERN(LogJadg, Log, All);

/**
 * @brief Le module principal du jeu.
 *
 * Au démarrage : branche le journaliseur de Core sur celui du moteur et écrit la version de Core,
 * preuve que la bibliothèque des règles est compilée dans le module (LOT-1014).
 */
class FJustAnotherRpgGameModule : public FDefaultGameModuleImpl
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
