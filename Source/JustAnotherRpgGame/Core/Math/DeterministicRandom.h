// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include <cstdint>

/**
 * @file Core/Math/DeterministicRandom.h
 * @brief Générateur pseudo-aléatoire déterministe, à graine explicite (jamais l'horloge,
 *        `EX-NFR-002`).
 */

namespace core {

/**
 * @brief Mélange (SplitMix64) un entier 64 bits en une valeur bien distribuée.
 *
 * Fonction pure et sans état : sert à combiner plusieurs valeurs reproductibles (graine de base,
 * numéro de pas, identifiant d'entité) en une graine unique par tirage, sans jamais lire
 * l'horloge système ni un générateur par défaut (`EX-NFR-002`).
 * @param value Valeur à mélanger.
 * @return La valeur mélangée.
 */
[[nodiscard]] constexpr std::uint64_t splitMix64(std::uint64_t value) noexcept {
    value = (value ^ (value >> 30)) * 0xBF58476D1CE4E5B9ULL;
    value = (value ^ (value >> 27)) * 0x94D049BB133111EBULL;
    return value ^ (value >> 31);
}

/**
 * @brief Combine une graine de base, un numéro de pas et un identifiant reproductible en une
 *        graine unique, propre à ce triplet.
 *
 * Reproductible quel que soit l'ordre ou le nombre d'appels : deux tirages faits pour le même
 * triplet (graine, pas, identifiant) produisent toujours la même graine dérivée, jamais
 * dépendante d'un compteur mutable partagé entre appels.
 * @param baseSeed Graine de base, explicite.
 * @param step     Numéro de pas de simulation courant.
 * @param entityId Identifiant reproductible (`core::Entity::index`, par exemple).
 * @return Une graine dérivée, propre à ce triplet.
 */
[[nodiscard]] constexpr std::uint64_t deriveSeed(std::uint64_t baseSeed, std::uint64_t step,
                                                 std::uint64_t entityId) noexcept {
    std::uint64_t seed = splitMix64(baseSeed);
    seed = splitMix64(seed ^ step);
    seed = splitMix64(seed ^ entityId);
    return seed;
}

/**
 * @brief Générateur pseudo-aléatoire léger (SplitMix64), à graine explicite.
 *
 * Aucune dépendance à `<random>` ni à l'horloge système : deux instances construites avec la
 * même graine produisent exactement la même suite de valeurs (`EX-NFR-002`). Utilisé par
 * `core::ParticleSystem`, où tout tirage doit rester reproductible d'une exécution à
 * l'autre pour une même séquence d'entrées.
 */
class DeterministicRandom {
public:
    /// @param seed Graine explicite (jamais issue de l'horloge ou d'un générateur par défaut).
    explicit DeterministicRandom(std::uint64_t seed) noexcept : _state(seed) {}

    /// @return Le prochain entier 32 bits de la suite.
    [[nodiscard]] std::uint32_t nextUInt32() noexcept {
        _state += 0x9E3779B97F4A7C15ULL;
        return static_cast<std::uint32_t>(splitMix64(_state) >> 32);
    }

    /// @return Le prochain flottant dans [0, 1[.
    [[nodiscard]] float nextFloat01() noexcept {
        constexpr float UINT32_RANGE = 4294967296.0f;  // 2^32
        return static_cast<float>(nextUInt32()) / UINT32_RANGE;
    }

    /**
     * @brief Prochain flottant dans [min, max].
     * @param min Borne inférieure.
     * @param max Borne supérieure ; si égale à `min`, renvoie exactement `min` (aucun tirage
     *            discriminant, utile pour une durée de vie ou une vitesse fixe).
     * @return La valeur tirée.
     */
    [[nodiscard]] float nextRange(float min, float max) noexcept {
        return min + nextFloat01() * (max - min);
    }

    /**
     * @brief Prochain entier dans **[min, max]**, bornes comprises, **sans biais modulo**.
     *
     * `nextUInt32() % n` est la forme évidente, et elle est fausse : 2³² n'est pas un multiple de
     * `n`, si bien que les `2³² mod n` premières valeurs sortent une fois de plus que les autres.
     * Sur un d20 le biais est d'environ un dix-millionième — négligeable —, mais il est
     * *systématique* et va toujours dans le même sens, et il rendrait indéfendable toute mesure de
     * distribution faite sur ce générateur. Le corriger coûte une boucle qui ne tourne
     * pratiquement jamais.
     *
     * La méthode est celle du **rejet** : on écarte la queue de l'intervalle qui dépasse le
     * dernier multiple complet de `n`. Le nombre d'itérations est fini avec probabilité 1, et sa
     * moyenne est inférieure à 2 pour tout `n` réaliste.
     *
     * @param min Borne inférieure, comprise.
     * @param max Borne supérieure, **comprise**. Si `max <= min`, renvoie `min` sans tirer — un
     *            intervalle vide n'est pas une erreur, c'est une valeur fixe.
     * @return L'entier tiré.
     */
    [[nodiscard]] int nextInt(int min, int max) noexcept {
        if (max <= min) {
            return min;
        }
        const std::uint32_t etendue = static_cast<std::uint32_t>(max - min) + 1U;
        // `2^32 mod etendue` : le nombre de valeurs en trop, celles qui n'ont pas de contrepartie
        // sur tout l'intervalle. On rejette la queue BASSE, `[0, reste[`, et non la haute.
        //
        // Rejeter la queue haute serait plus naturel à lire — « au-delà du dernier multiple
        // complet » — mais ce seuil vaut `2^32` quand `etendue` divise `2^32`, et `2^32` ne tient
        // pas dans un `std::uint32_t` : il retombe à 0, la condition devient toujours vraie, et la
        // boucle ne se termine jamais. Le défaut ne se voit que sur les **puissances de deux** :
        // un d6 et un d20 passent, un d8 bloque. C'est un test de rejouabilité sur 3d8 qui l'a
        // trouvé, pas une relecture.
        const std::uint32_t reste = (std::uint32_t{0} - etendue) % etendue;
        std::uint32_t tirage = nextUInt32();
        while (tirage < reste) {
            tirage = nextUInt32();
        }
        return min + static_cast<int>(tirage % etendue);
    }

private:
    std::uint64_t _state;
};

}  // namespace core
