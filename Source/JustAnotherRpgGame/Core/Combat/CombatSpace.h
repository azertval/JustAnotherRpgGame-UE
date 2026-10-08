// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

/**
 * @file Core/Combat/CombatSpace.h
 * @brief L'espace de combat **en mètres** : volumes, allonge, zones, abri, tenaille, hauteur, et
 *        l'interface que le moteur implémente (`LOT-1017`, D-50).
 *
 * ## Le Manuel compte en mètres
 *
 * La grille n'était qu'une façon de les dessiner (`LOT-19`). Ici une créature est un **cylindre**
 * posé au sol — le centre de sa base, son rayon, sa hauteur —, une portée est une distance, une
 * zone une forme géométrique, et la carte est ce que le moteur en dit par `core::CombatSpace` :
 * navigation, rayons, hauteur du sol. Les règles qui n'ont pas besoin de la carte — l'allonge, les
 * formes, la tenaille, l'avantage de hauteur — sont des fonctions libres, exactes, testées sans
 * moteur.
 *
 * ## Les données restent en cases
 *
 * Le corpus écrit « 6 cases », « 9 m » ; une case vaut 1,50 m (`core::METERS_PER_TILE`), et la
 * conversion est `core::metersFromTiles`. Aucune grille n'apparaît à l'écran.
 *
 * ## Les décisions de ce lot (8 octobre 2026)
 *
 * - **L'allonge** au corps à corps est 1,50 m, mesurée entre les **bords** des cylindres, en
 *   trois dimensions : deux créatures de taille M dont les centres sont à 2,9 m se touchent
 *   (rayons de 0,75 m chacun, 1,4 m de jour), à 3,1 m non.
 * - **La hauteur d'une créature** est le côté de son emprise : le Manuel donne à une créature un
 *   espace **cubique** (« Taille des créatures »), 1,50 m pour M, 3 m pour G.
 * - **La tenaille** (règle optionnelle du Guide, « côtés ou angles opposés ») devient un angle :
 * les deux attaquants prennent la cible en tenaille si l'angle qu'ils forment **au centre de la
 * cible** est d'au moins 135°. C'est la valeur exacte où la règle de la ligne des centres du Guide,
 * jouée sur les huit cases adjacentes, bascule : deux cases adjacentes font 135° au moins quand la
 *   ligne traverse deux côtés opposés, 90° au plus sinon (`test_combat_space.cpp` le vérifie).
 * - **L'avantage de hauteur** : l'attaquant a l'avantage si sa base est au moins **1,50 m** —
 *   une case — au-dessus de celle de la cible, et rien d'autre : pas de bonus de dégâts ni de
 *   portée, ce que le Manuel ne donne pas.
 * - **Les zones** : la sphère et le cylindre sont exacts en trois dimensions ; le cône, la ligne
 *   et le cube se posent dans le plan horizontal et touchent ce qui est à moins de leur taille en
 *   hauteur de leur origine. Une créature est **dans** la zone si son volume la croise, pas si son
 *   centre y est.
 * - **L'abri** garde la méthode du Guide : des lignes depuis le meilleur point de l'attaquant vers
 *   quatre points du bord de la cible, étagés sur sa hauteur. Une ou deux lignes coupées par la
 *   carte : abri
 *   partiel ; trois : important ; quatre : total. Un corps interposé abrite selon sa nature, dès
 *   qu'il coupe une ligne.
 */

#include <cmath>
#include <optional>
#include <span>
#include <vector>

#include "Core/Combat/CombatTypes.h"
#include "Core/Rpg/RpgEnums.h"
#include "Core/Rpg/Scale.h"

namespace core {

/// @brief Un point du monde en mètres : `x` et `y` au sol, `z` la hauteur.
struct Meters3 {
    float x = 0.0f;
    float y = 0.0f;
    float z = 0.0f;

    [[nodiscard]] bool operator==(const Meters3&) const = default;
};

/// @brief La distance au sol entre deux points, hauteur ignorée.
[[nodiscard]] inline float groundDistance(Meters3 a, Meters3 b) noexcept {
    return std::hypot(b.x - a.x, b.y - a.y);
}

/// @brief La distance en trois dimensions.
[[nodiscard]] inline float distance(Meters3 a, Meters3 b) noexcept {
    return std::sqrt((b.x - a.x) * (b.x - a.x) + (b.y - a.y) * (b.y - a.y) +
                     (b.z - a.z) * (b.z - a.z));
}

/// @brief L'allonge au corps à corps du Manuel : 1,50 m.
inline constexpr float MELEE_REACH_METERS = METERS_PER_TILE;

/// @brief L'écart de hauteur qui donne l'avantage : une case.
inline constexpr float HEIGHT_ADVANTAGE_METERS = METERS_PER_TILE;

/// @brief L'angle, au centre de la cible, à partir duquel deux attaquants la prennent en tenaille.
inline constexpr float FLANKING_ANGLE_DEGREES = 135.0f;

/// @brief Le rayon du cylindre d'une créature : la moitié du côté de son emprise.
[[nodiscard]] constexpr float creatureRadius(CreatureSize size) noexcept {
    return static_cast<float>(footprintSide(size)) * METERS_PER_TILE / 2.0f;
}

/// @brief La hauteur du cylindre d'une créature : le côté de son emprise (un espace cubique).
[[nodiscard]] constexpr float creatureHeight(CreatureSize size) noexcept {
    return static_cast<float>(footprintSide(size)) * METERS_PER_TILE;
}

/// @brief Un combattant dans l'espace : un cylindre posé au sol.
struct Volume {
    /// Le centre de la base, au sol.
    Meters3 base;
    float radius = creatureRadius(CreatureSize::Medium);
    float height = creatureHeight(CreatureSize::Medium);

    [[nodiscard]] bool operator==(const Volume&) const = default;
};

/// @brief Le volume d'une créature de taille @p size posée en @p base.
[[nodiscard]] constexpr Volume volumeOf(Meters3 base, CreatureSize size) noexcept {
    return {.base = base, .radius = creatureRadius(size), .height = creatureHeight(size)};
}

/// @brief Le centre du volume, à mi-hauteur : d'où l'on regarde, et ce que l'on vise.
[[nodiscard]] inline Meters3 centerOf(const Volume& volume) noexcept {
    return {volume.base.x, volume.base.y, volume.base.z + volume.height / 2.0f};
}

/**
 * @brief La distance entre les **bords** de deux volumes, en trois dimensions : 0 s'ils se
 *        touchent ou se recouvrent.
 */
[[nodiscard]] float edgeDistance(const Volume& a, const Volume& b) noexcept;

/// @brief Vrai si @p target est à @p reach mètres au plus du bord de @p attacker.
[[nodiscard]] inline bool inReach(const Volume& attacker, const Volume& target,
                                  float reach = MELEE_REACH_METERS) noexcept {
    return edgeDistance(attacker, target) <= reach + 1e-4f;
}

/// @brief Vrai si les deux volumes se recouvrent : ils ne peuvent pas se tenir là tous les deux.
[[nodiscard]] bool overlap(const Volume& a, const Volume& b) noexcept;

/**
 * @brief Vrai si @p a et @p b prennent @p target en tenaille par leur position seule : l'angle
 *        qu'ils forment au centre de la cible atteint `FLANKING_ANGLE_DEGREES`.
 *
 * La géométrie seule : ni l'allonge, ni la vue, ni l'état des créatures (`LOT-23` les vérifie).
 */
[[nodiscard]] bool flanksByAngle(Meters3 a, Meters3 b, Meters3 target) noexcept;

/// @brief Vrai si @p attacker a l'avantage de la hauteur sur @p target.
[[nodiscard]] inline bool hasHighGround(const Volume& attacker, const Volume& target) noexcept {
    return attacker.base.z - target.base.z >= HEIGHT_ADVANTAGE_METERS - 1e-4f;
}

/**
 * @brief Une zone d'effet posée dans l'espace. Les tailles sont en **mètres**
 *        (`core::metersFromTiles` pour celles écrites en cases).
 */
struct Effect {
    AreaShape shape = AreaShape::Sphere;
    /// Le point d'origine : le centre d'une sphère, le sommet d'un cône, le milieu d'une face du
    /// cube, le début d'une ligne.
    Meters3 origin;
    /// Un point vers lequel s'étendent le cône, le cube et la ligne ; ignoré par la sphère et le
    /// cylindre. Confondu avec l'origine, la zone est vide : sans direction, rien ne s'étend.
    Meters3 toward;
    /// Rayon (sphère, cylindre), longueur (cône, ligne) ou arête (cube), en mètres.
    float size = METERS_PER_TILE;
    /// Largeur d'une ligne, hauteur d'un cylindre, en mètres. Ignorée par les autres formes.
    float width = METERS_PER_TILE;
};

/// @brief Vrai si le volume croise la zone — un bord suffit.
[[nodiscard]] bool shapeHits(const Effect& effect, const Volume& volume) noexcept;

/// @brief Les indices des volumes que la zone croise, par indice croissant.
[[nodiscard]] std::vector<std::size_t> volumesInEffect(const Effect& effect,
                                                       std::span<const Volume> volumes);

/// @brief Vrai si le segment @p from — @p to traverse le cylindre @p volume.
[[nodiscard]] bool segmentCrosses(Meters3 from, Meters3 to, const Volume& volume) noexcept;

/// @brief Un chemin au sol : ses points, départ exclu et arrivée incluse, et sa longueur.
struct Route {
    std::vector<Meters3> points;
    float length = 0.0f;
};

/**
 * @brief Ce que l'espace doit savoir pour tracer un chemin.
 */
struct RouteQuery {
    /// Qui se déplace, à sa place actuelle.
    Volume mover;
    Meters3 destination;
    /// Les mètres de déplacement disponibles ; au-delà, pas de chemin. Négatif : sans limite.
    float budget = -1.0f;
    Locomotion locomotion = Locomotion::Walk;
    /// Les volumes qu'on ne traverse pas — les ennemis (Manuel, « Se déplacer au milieu d'autres
    /// créatures ») — et ceux où l'on ne peut pas finir.
    std::span<const Volume> blocking;
    /// Les volumes qu'on traverse mais qui comptent pour du terrain difficile — les alliés.
    std::span<const Volume> passable;
};

/**
 * @brief L'espace d'une rencontre : ce que la carte oppose au déplacement, à la vue, et où est le
 *        sol.
 *
 * Deux implémentations : `core::SimulatedSpace` (un plan, des boîtes, des plateaux ; les tests et
 * la simulation de la série) et celle du moteur (maillage de navigation, rayons, EQS ; `LOT-1017`,
 * sous-lot 3). Les règles — `core::CombatState`, l'attaque, les zones, l'IA — ne voient que cette
 * interface, et ne savent pas laquelle répond.
 *
 * Toutes les réponses sont **déterministes** pour un même espace et une même question : la
 * simulation le garantit par construction ; le moteur n'a pas à l'être pour que les tests tiennent,
 * puisque les tests jouent sur la simulation (décision du lot, 8 octobre 2026).
 */
class CombatSpace {
public:
    virtual ~CombatSpace() = default;

    /// @brief La hauteur du sol en un point ; ce sur quoi une base se pose.
    [[nodiscard]] virtual float groundHeight(float x, float y) const = 0;

    /// @brief Vrai si le volume tient là sans toucher la carte — ni mur, ni bord, ni, au sol,
    /// l'eau profonde.
    [[nodiscard]] virtual bool isClear(const Volume& volume,
                                       Locomotion locomotion = Locomotion::Walk) const = 0;

    /// @brief Vrai si rien de la carte n'arrête le segment @p from — @p to.
    [[nodiscard]] virtual bool lineOfSight(Meters3 from, Meters3 to) const = 0;

    /// @brief Le meilleur chemin, ou rien s'il n'y en a pas dans le budget.
    [[nodiscard]] virtual std::optional<Route> route(const RouteQuery& query) const = 0;

    /**
     * @brief Des positions où le mobile peut **finir** son déplacement dans le budget, départ
     *        compris, par ordre fixe : ce que l'IA examine (`LOT-23`) et ce que l'aperçu dessine.
     *
     * La simulation les échantillonne sur son pas ; le moteur les demande à EQS.
     */
    [[nodiscard]] virtual std::vector<Meters3> candidates(const RouteQuery& query) const = 0;
};

/**
 * @brief L'abri de @p target contre ce qui vient de @p attacker, sur @p space, les volumes
 *        @p interposed faisant corps.
 *
 * L'attaquant prend le point qui l'arrange parmi cinq (le centre et quatre points de son bord) ;
 * quatre lignes partent vers quatre points du bord de la cible, qui échantillonnent sa hauteur à
 * un, trois, cinq et sept huitièmes — un muret cache les bas, pas les hauts. Les lignes coupées
 * par la carte se comptent (`Cover::Half`, `Cover::ThreeQuarters`, `Cover::Total`) ; un corps
 * interposé qui coupe une ligne donne `Cover::Half`. Les abris ne s'additionnent pas.
 */
[[nodiscard]] Cover coverFrom(const CombatSpace& space, const Volume& attacker,
                              const Volume& target, std::span<const Volume> interposed = {});

/// @brief Le même abri contre un effet qui part d'un **point** — l'origine d'une zone.
[[nodiscard]] Cover coverFromPoint(const CombatSpace& space, Meters3 origin, const Volume& target,
                                   std::span<const Volume> interposed = {});

/// @brief Vrai si les deux volumes se voient depuis un point de l'un vers un point de l'autre.
[[nodiscard]] bool hasLineOfSight(const CombatSpace& space, const Volume& a, const Volume& b);

}  // namespace core
