// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/CombatTransition.h
 * @brief L'aller-retour exploration ↔ combat : ce qu'on met de côté, et ce qu'on retrouve
 *        (`LOT-18`, `EX-CBT-001`).
 */

#include <optional>
#include <string>
#include <string_view>
#include <vector>

#include "Core/Combat/Encounter.h"
#include "Core/Levels/GridPosition.h"
#include "Core/Levels/MapEntity.h"
#include "Core/Math/Vector2.h"

namespace core {

class WorldFlags;

/**
 * @brief L'état d'exploration mis de côté le temps d'un combat.
 *
 * ## Ce qu'il porte, et ce qu'il ne porte pas
 *
 * Il porte ce que **le combat modifie sans le vouloir** : le personnage se déplace sur la grille
 * tactique, la caméra le suit, et sans mémoire il reviendrait de son combat ailleurs qu'il ne
 * l'avait quitté — un pas de côté à chaque rencontre, invisible une fois, gênant au dixième.
 *
 * Il ne porte **pas** les points de vie. Le critère du lot dit « restituer exactement l'état
 * d'exploration, **aux PV près** » : les points de vie sont précisément ce que le combat a changé,
 * et les remettre à leur valeur d'avant annulerait le combat. Les inclure « pour être complet »
 * serait donc le bogue, pas la prudence.
 *
 * Il ne porte pas non plus les ennemis vaincus : cela ne se restitue pas, cela s'**acquiert**, et
 * c'est un drapeau de monde (`core::WorldFlags`) qui survit au rechargement de la carte.
 */
struct ExplorationSnapshot {
    /// Position du personnage, en unités monde.
    Vector2 playerPosition{};
    /// Orientation conservée : un personnage qui revient d'un combat regarde là où il regardait,
    /// et non vers une direction par défaut (`EX-EXP-004`).
    Vector2 playerFacing{1.0F, 0.0F};
    /// Position de la caméra, en unités monde.
    Vector2 cameraPosition{};
    /// Faux tant que rien n'a été relevé : restituer un instantané vide replacerait le personnage
    /// à l'origine de la carte, ce qui ressemble à une téléportation et non à une erreur.
    bool captured = false;
};

/// @brief Comment un combat se termine.
enum class CombatOutcome {
    /// Tous les ennemis sont hors de combat.
    Victory,
    /// Le joueur a rompu le contact. Les ennemis restent sur la carte.
    Flight,
    /// Le groupe est tombé.
    Defeat,
};

/**
 * @brief Une rencontre **engagée** : ce qu'on restituera, et ce qu'une victoire acquerra.
 *
 * Construite à l'entrée en combat, consommée à la sortie. C'est le seul objet que le mode combat
 * ait à garder, et il ne contient aucun widget, aucune entité, aucun pointeur de monde : c'est ce
 * qui rend l'aller-retour vérifiable sans fenêtre (`EX-NFR-010`).
 */
struct EncounterRun {
    ExplorationSnapshot exploration;
    std::string encounterId;
    /**
     * @brief Clé de drapeau de monde à poser **en cas de victoire**.
     *
     * Vide pour une rencontre qui doit pouvoir se reproduire — une zone de rencontre aléatoire.
     * Renseignée pour un ennemi posé sur la carte : `core::keyForEntity` la fabrique, et c'est
     * elle qui empêche l'ennemi vaincu de réapparaître au rechargement de la carte.
     */
    std::string defeatFlagKey;
    /// Où chaque combattant se dresse.
    std::vector<CombatantPlacement> placements;
    /// Recopié de la rencontre : une sortie par la fuite n'est pas toujours permise.
    bool escapable = true;
};

/**
 * @brief Engage @p encounter au point @p trigger, en mettant @p exploration de côté.
 *
 * @param encounter     La rencontre, telle que la donnée la décrit.
 * @param exploration   L'état d'exploration à retrouver ensuite.
 * @param trigger       La case du déclencheur : les combattants s'y placent relativement.
 * @param defeatFlagKey Le drapeau qu'une victoire acquerra, ou une chaîne vide.
 */
[[nodiscard]] EncounterRun beginEncounter(const Encounter& encounter,
                                          const ExplorationSnapshot& exploration,
                                          GridPosition trigger, std::string defeatFlagKey);

/**
 * @brief Termine @p run, et rend l'état d'exploration à restituer.
 *
 * **Seule une victoire acquiert le drapeau.** Une fuite ramène à l'exploration sans marquer
 * l'ennemi vaincu — sans quoi fuir suffirait à nettoyer une carte —, et une défaite non plus : le
 * groupe est tombé, l'ennemi est toujours là.
 *
 * @param run     La rencontre engagée.
 * @param outcome Comment elle s'est terminée.
 * @param flags   Les drapeaux de monde, où une victoire écrit.
 * @return L'état d'exploration à restituer, tel qu'il avait été relevé.
 */
[[nodiscard]] ExplorationSnapshot endEncounter(const EncounterRun& run, CombatOutcome outcome,
                                               WorldFlags& flags);

/**
 * @brief Vrai si cette rencontre a déjà été gagnée, et ne doit donc pas se redéclencher.
 *
 * Une clé **vide** n'est jamais acquise : c'est le cas d'une zone de rencontre, qui se redéclenche
 * par construction. Répondre « déjà nettoyée » pour une clé vide désactiverait toutes les zones du
 * jeu dès le premier combat gagné.
 */
[[nodiscard]] bool encounterAlreadyCleared(const WorldFlags& flags, std::string_view defeatFlagKey);

/// @brief Type de la couche `objects` qui déclenche une rencontre.
inline constexpr std::string_view ENCOUNTER_ENTITY_TYPE = "encounter";

/**
 * @brief Un déclencheur de rencontre relevé sur la carte : quoi engager, où, et ce qu'une victoire
 *        acquerra.
 */
struct EncounterTrigger {
    std::string encounterId;
    GridPosition position;
    /// Vide si la rencontre doit pouvoir se reproduire (une zone). Voir `EncounterRun`.
    std::string defeatFlagKey;
};

/**
 * @brief Lit @p entity comme un déclencheur de rencontre, s'il en est un.
 *
 * Deux natures de déclencheur, distinguées par la **donnée** et non par le type d'entité :
 *
 * - un ennemi **posé** sur la carte — il se combat une fois, et sa clé de drapeau le fait
 *   disparaître pour de bon (`core::keyForEntity`) ;
 * - une **zone** de rencontre (`respawns: true`) — elle se redéclenche, et n'a donc pas de clé.
 *
 * Confondre les deux se paierait dans les deux sens : un ennemi sans clé réapparaîtrait à chaque
 * passage, et une zone avec clé s'éteindrait au premier combat gagné.
 *
 * @param entity  L'entité de la couche `objects`.
 * @param mapName Le nom de la carte, qui ouvre la clé de drapeau — deux cartes ne se marchent
 *                jamais dessus.
 * @return Le déclencheur, ou `std::nullopt` si cette entité n'en est pas un.
 */
[[nodiscard]] std::optional<EncounterTrigger> encounterTriggerFor(const MapEntity& entity,
                                                                  std::string_view mapName);

}  // namespace core
