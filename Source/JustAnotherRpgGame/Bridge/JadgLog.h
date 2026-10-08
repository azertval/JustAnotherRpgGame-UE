// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @brief Le journal de Core dans celui du moteur.
 *
 * Core journalise par `JADG_LOG_*` vers `core::defaultLogger()` et ses sinks (console, fichier).
 * Dans le moteur, un sink de plus relaie chaque ligne vers `UE_LOG(LogJadg, ...)` au niveau
 * équivalent : une erreur de contenu lue par Core apparaît dans le journal de l'éditeur et dans
 * la sortie d'un commandlet, là où on la cherche.
 */
struct FJadgCoreLogBridge
{
	/// Ajoute le sink au journaliseur global de Core. Idempotent.
	static void Install();

	/// Retire tous les sinks du journaliseur global (celui du moteur compris).
	static void Uninstall();
};
