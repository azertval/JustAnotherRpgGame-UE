// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/World/Atlas.h
 * @brief Chargement de l'atlas des régions et du graphe de cartes (`LOT-37`, `EX-CNT-010`).
 */

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace core {

/**
 * @brief Les cinq notes de l'encart « Regional Statistics » (`EX-CNT-060`).
 *
 * Fermée, et **ordonnée du plus bas au plus haut** : une note se compare, et c'est tout l'intérêt
 * de la typer. `monsterPresence >= RegionGrade::High` doit vouloir dire quelque chose, sinon
 * autant garder la chaîne du livre.
 *
 * Les valeurs coïncident avec l'énumération de `region.schema.json` ; `test_atlas.cpp` le vérifie
 * (`EX-CNT-011`).
 */
enum class RegionGrade : std::uint8_t {
    VeryLow = 0,
    Low,
    Normal,
    High,
    VeryHigh,
};

/// @brief Nombre de notes — pour les parcours exhaustifs et les contrôles de couverture.
inline constexpr std::size_t kRegionGradeCount = 5;

/**
 * @brief Une appréciation d'un axe : une note, et la portée où elle vaut.
 *
 * La portée est **vide** dans la région uniforme, et c'est le cas courant. Elle porte « north »,
 * « underground » quand le livre distingue : le Benênet impérial est « Low (south), High (north) »,
 * et rien n'autorise à en faire une valeur unique.
 */
struct RegionAppraisal {
    RegionGrade grade = RegionGrade::Normal;
    /// Portée, telle que le livre l'écrit. Vide si l'appréciation vaut pour toute la région.
    std::string scope;
};

/**
 * @brief Un axe de statistique régionale : une ou plusieurs appréciations (`EX-CNT-061`).
 *
 * Jamais vide — le schéma l'exige. `grade()` rend la première, pour le code qui ne modélise pas
 * les portées ; `appraisals` reste là pour celui qui les modélise.
 */
struct RegionStatistic {
    std::vector<RegionAppraisal> appraisals;

    /// @brief La note principale : celle de la première appréciation.
    [[nodiscard]] RegionGrade grade() const {
        return appraisals.empty() ? RegionGrade::Normal : appraisals.front().grade;
    }

    /// @brief Vrai si la région n'est pas uniforme sur cet axe.
    [[nodiscard]] bool varies() const {
        return appraisals.size() > 1;
    }
};

/// @brief Les sept axes, dans l'ordre où le livre les imprime.
enum class RegionAxis : std::uint8_t {
    CitizenFreedom = 0,
    CrimeAndViolence,
    EconomicProsperity,
    GovernmentCorruption,
    MagicAccess,
    MonsterPresence,
    PoliticalStability,
};

/// @brief Nombre d'axes.
inline constexpr std::size_t kRegionAxisCount = 7;

/// @brief La part d'une espèce dans la population d'une région.
struct RegionSpeciesShare {
    /// Clé d'espèce, en **anglais** et au singulier. Voir la note de `loadAtlas`.
    std::string species;
    /// Le mot du livre, tel qu'il l'écrit — « summer elves ».
    std::string label;
    int percent = 0;
};

/**
 * @brief La population d'une région.
 *
 * `total` est **approximatif dans la source** (« Around 2,300,000 ») et absent si le livre n'en
 * donne pas : d'où l'`optional`, qui distingue « pas de chiffre » de « zéro habitant ».
 */
struct RegionPopulation {
    std::optional<int> total;
    std::vector<RegionSpeciesShare> species;
    /// La part que le livre range sous « others ». Absente s'il n'en donne pas.
    std::optional<int> otherPercent;
};

/// @brief Un lieu nommé d'une région : un nœud terminal du graphe, une carte à créer.
struct Location {
    std::string id;
    std::string name;
    std::string source;
    /// Identifiant de la région qui le porte. Jamais vide.
    std::string region;
    /// Le texte du livre. Vide pour une entrée qu'il ne fait que nommer.
    std::string description;
};

/**
 * @brief Une région : un nœud du graphe de cartes.
 *
 * `neighbors` porte les arêtes et `locations` les cartes à créer — c'est le branchement direct sur
 * le `LOT-09`, et la raison d'être de ce catalogue.
 */
struct Region {
    std::string id;
    std::string name;
    std::string source;
    std::string government;
    std::string faction;
    RegionPopulation population;
    /// Les sept axes, indexés par `core::RegionAxis`.
    std::array<RegionStatistic, kRegionAxisCount> statistics;
    std::vector<std::string> neighbors;
    std::vector<std::string> locations;

    /// @brief L'axe demandé.
    [[nodiscard]] const RegionStatistic& statistic(RegionAxis axis) const {
        return statistics[static_cast<std::size_t>(axis)];
    }
};

/**
 * @brief L'atlas chargé, et ce qui n'a pas pu l'être.
 *
 * Les deux ensemble, comme pour le bestiaire : un atlas dont un lieu sur quatre-vingt-quatorze est
 * illisible reste jouable, et le refuser en bloc rendrait le monde inaccessible pour une virgule.
 */
struct Atlas {
    /// Les régions chargées, triées par identifiant.
    std::vector<Region> regions;
    /// Les lieux chargés, triés par identifiant.
    std::vector<Location> locations;
    /// Un message par fichier refusé, nommant le fichier et la raison.
    std::vector<std::string> errors;

    /// @brief La région portant cet identifiant, ou `nullptr`.
    [[nodiscard]] const Region* findRegion(std::string_view id) const;
    /// @brief Le lieu portant cet identifiant, ou `nullptr`.
    [[nodiscard]] const Location* findLocation(std::string_view id) const;

    /**
     * @brief Les régions que l'on ne peut pas atteindre depuis `from` en suivant `neighbors`
     *        (`EX-CNT-062`).
     *
     * Vide sur un atlas sain. Ce n'est pas un contrôle de plus pour le plaisir : une région
     * injoignable est du contenu que personne ne verra jamais, et rien d'autre ne le signale —
     * le jeu se lance, la région existe, elle n'est simplement au bout d'aucun trajet.
     */
    [[nodiscard]] std::vector<std::string> unreachableFrom(std::string_view from) const;
};

/**
 * @brief Charge l'atlas — `regions/` et `locations/` sous le dossier donné.
 *
 * Les deux dossiers sont **balayés**, jamais énumérés dans le code : le `LOT-80` ajoutera des
 * lieux, et une liste écrite ici les rendrait invisibles.
 *
 * @note **Les clés d'espèce sont en anglais** et ne pointent pas vers le catalogue d'espèces du
 *       `LOT-36`, qui est en français et n'en couvre que la moitié — ni géant, ni gobelinoïde, ni
 *       kemet, ni merfolk, ni orc, ni soulborn n'y existent. La correspondance est le travail du
 *       `LOT-39` ; la fabriquer à moitié ici donnerait un champ vrai une fois sur deux, ce qui est
 *       pire qu'un champ dont on sait qu'il ne pointe nulle part.
 *
 * @param directory Dossier de l'atlas (`Source/Elements/World`).
 * @return L'atlas et la liste des échecs. Ne lève jamais (`EX-NFR-040`). Un dossier absent produit
 *         une erreur, pas un atlas vide : un monde vide se confondrait avec un monde non installé.
 */
[[nodiscard]] Atlas loadAtlas(const std::filesystem::path& directory);

/// @brief Le nom d'une note, tel que le schéma l'écrit (`veryLow`, `normal`, …).
[[nodiscard]] std::string_view regionGradeName(RegionGrade grade);

/// @brief La note portant ce nom de schéma, ou `std::nullopt`.
[[nodiscard]] std::optional<RegionGrade> regionGradeFromName(std::string_view name);

/// @brief Le nom d'un axe, tel que le schéma l'écrit (`citizenFreedom`, …).
[[nodiscard]] std::string_view regionAxisName(RegionAxis axis);

}  // namespace core
