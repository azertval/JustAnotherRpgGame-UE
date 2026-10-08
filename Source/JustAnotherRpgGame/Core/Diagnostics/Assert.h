// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <functional>

/**
 * @file Core/Diagnostics/Assert.h
 * @brief Assertions du projet : vérifient préconditions et invariants (bugs).
 */

namespace core {

/// Signature d'un gestionnaire d'échec d'assertion.
using AssertionHandler =
    std::function<void(const char* condition, const char* message, const char* file, int line)>;

/**
 * @brief Remplace le gestionnaire d'échec d'assertion (utile pour les tests).
 * @param handler Nouveau gestionnaire ; un gestionnaire nul rend l'échec silencieux.
 */
void setAssertionHandler(AssertionHandler handler);

/**
 * @brief Invoque le gestionnaire d'échec d'assertion courant.
 * @param condition Texte de la condition ayant échoué.
 * @param message   Message explicatif.
 * @param file      Fichier source.
 * @param line      Ligne source.
 */
void handleAssertionFailure(const char* condition, const char* message, const char* file, int line);

}  // namespace core

/**
 * @def JADG_ASSERT
 * @brief Vérifie une précondition. Active en Debug, sans effet en Release.
 *
 * En Debug, si la condition est fausse, le gestionnaire d'assertion courant est
 * appelé. En Release (`NDEBUG`), la macro ne produit aucune instruction et la
 * condition n'est pas évaluée.
 */
#ifdef NDEBUG
#define JADG_ASSERT(condition, message) ((void)0)
#else
// La branche vide plutot qu'un `if (!(condition))` : une condition composee (`a && b`) ne se
// lit plus, une fois niee par la macro, comme une expression a simplifier par De Morgan.
#define JADG_ASSERT(condition, message)                                              \
    do {                                                                             \
        if (static_cast<bool>(condition)) {                                          \
        } else {                                                                     \
            ::core::handleAssertionFailure(#condition, message, __FILE__, __LINE__); \
        }                                                                            \
    } while (false)
#endif
