// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Core/Combat/EnemyAi.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <set>
#include <span>
#include <string>
#include <utility>

#include "Core/Combat/AreaOfEffect.h"
#include "Core/Combat/CombatCounters.h"
#include "Core/Combat/CombatSpace.h"
#include "Core/Combat/Flanking.h"
#include "Core/Data/JsonDocument.h"
#include "Core/Rpg/Bestiary.h"
#include "Core/Rpg/ClassCapacities.h"

namespace core {
namespace {

constexpr int SANS_GARDE_DE_VERSION = 0;
// Une case de 1,50 m vaut, au taux `approachPerTile`, un point de degat : 800 unites d'esperance.
constexpr long long UNITES_PAR_POINT = 800;
// Un pourcentage de profil plein : la valeur d'une frappe est une esperance fois un pourcentage.
constexpr long long POURCENT_PLEIN = 100;

// Ce que valent, en points de degats, les gestes d'un sort qui ne blessent pas (LOT-142). Le
// Guide du Maitre ne chiffre pas un compagnon rendu au combat : ce sont des decisions nommees,
// calees pour qu'un allie a terre passe avant une attaque moyenne, et un allie debout apres.
constexpr long long RELEVER = 10;
constexpr long long STABILISER = 3;
constexpr long long RAMENER = 20;
constexpr long long BENIR = 3;
// Un allie pris dans la sphere d'un sort compte double, en moins.
constexpr long long ALLIE_TOUCHE = 2;

// @p points points de degats, dans l'unite des valeurs de frappe.
[[nodiscard]] constexpr long long enValeur(long long points) noexcept {
    return points * UNITES_PAR_POINT * POURCENT_PLEIN;
}

// --- Donnee -----------------------------------------------------------------------------------

[[nodiscard]] std::string lireTexte(const nlohmann::json& objet, const char* champ) {
    const auto trouve = objet.find(champ);
    return (trouve != objet.end() && trouve->is_string()) ? trouve->get<std::string>()
                                                          : std::string{};
}

[[nodiscard]] int lireEntier(const nlohmann::json& objet, const char* champ, int defaut) {
    const auto trouve = objet.find(champ);
    return (trouve != objet.end() && trouve->is_number_integer()) ? trouve->get<int>() : defaut;
}

[[nodiscard]] bool lireBooleen(const nlohmann::json& objet, const char* champ, bool defaut) {
    const auto trouve = objet.find(champ);
    return (trouve != objet.end() && trouve->is_boolean()) ? trouve->get<bool>() : defaut;
}

// --- Des --------------------------------------------------------------------------------------

// Les faces d'un d20 qui touchent : un 1 rate toujours, un 20 et le seuil critique touchent.
[[nodiscard]] int facesQuiTouchent(int requis, int seuilCritique) noexcept {
    int faces = 0;
    for (int face = 2; face <= 20; ++face) {
        if (face >= requis || face >= seuilCritique) {
            ++faces;
        }
    }
    return faces;
}

// Une chance d'un de sur vingt, en quatre-centiemes, selon la posture.
[[nodiscard]] int chanceSelonPosture(int faces, RollStance posture) noexcept {
    switch (posture) {
        case RollStance::Advantage:
            return CHANCE_SCALE - ((20 - faces) * (20 - faces));
        case RollStance::Disadvantage:
            return faces * faces;
        case RollStance::Normal:
            break;
    }
    return faces * 20;
}

// Les degats moyens en demi-points (un de a f faces vaut (f + 1) / 2), et la part des des seuls.
[[nodiscard]] std::pair<long long, long long> degatsMoyens(const AttackProfile& profil) noexcept {
    long long total = 0;
    long long des = 0;
    for (const DamageClause& clause : profil.damage) {
        const long long moyenneDes =
            static_cast<long long>(clause.dice.count) * (clause.dice.faces + 1);
        total += std::max(0LL, moyenneDes + (2LL * clause.dice.modifier));
        des += moyenneDes;
    }
    return {total, des};
}

// --- Geometrie --------------------------------------------------------------------------------

// Une longueur en centimetres entiers : l'IA compte en entiers (LOT-23), et un centimetre est
// plus fin que tout ce que le reseau de l'espace distingue.
[[nodiscard]] long long centimetres(float metres) noexcept {
    return std::llround(static_cast<double>(metres) * 100.0);
}

// Une case de 1,50 m, en centimetres : le taux `approachPerTile` se paie par case.
constexpr long long CENTIMETRES_PAR_CASE = 150;

[[nodiscard]] std::string pointTexte(Meters3 point) {
    std::array<char, 48> texte{};
    std::snprintf(texte.data(), texte.size(), "%.2f,%.2f", static_cast<double>(point.x),
                  static_cast<double>(point.y));
    return texte.data();
}

[[nodiscard]] bool memePoint(Meters3 a, Meters3 b) noexcept {
    return groundDistance(a, b) <= 1e-3f;
}

// Un combattant place, tel que l'IA le lit.
struct Present {
    CombatantId id{};
    const Combatant* combattant = nullptr;
    Volume volume;
    const std::vector<AttackProfile>* attaques = nullptr;
};

// Ce que l'IA sait evaluer pour un combattant a un instant : les menaces sur une place, les
// attaques d'opportunite d'un chemin, les attaques possibles depuis une place. Tout est lu de la
// session, rien n'est ecrit.
class Evaluateur {
public:
    Evaluateur(const ArenaSession& session, CombatantId acteur, const BehaviorProfile& profil)
        : _session(session), _combat(session.combat()), _espace(_combat.space()), _profil(profil) {
        _moi.id = acteur;
        _moi.combattant = _combat.find(acteur);
        const std::optional<Volume> volume = _combat.volumeOf(acteur);
        if (_moi.combattant == nullptr || !volume.has_value()) {
            return;
        }
        _moi.volume = *volume;
        _moi.attaques = session.attacks(acteur);
        // Ce que les capacites de classe ajoutent aux attaques (LOT-142) : l'IA les compte comme
        // le jet les jouera.
        const std::span<const Capacity> capacites = session.capacitiesOf(acteur);
        _bonusDeCapacites = attackModifiersFrom(capacites);
        _desDeCapacites = extraDamageFrom(capacites);
        _valide = true;
        for (const CombatantId id : _combat.combatants()) {
            const Combatant* c = _combat.find(id);
            const std::optional<Volume> place = _combat.volumeOf(id);
            if (c == nullptr || !place.has_value()) {
                continue;
            }
            Present present{
                .id = id, .combattant = c, .volume = *place, .attaques = session.attacks(id)};
            _places.push_back(present);
            // Un ennemi a terre n'est ni une menace ni un obstacle au choix : une cible, si le
            // profil l'acheve et que l'on meurt dans ce combat (LOT-137).
            if (id != acteur && c->status == CombatantStatus::Down && _combat.lethal() &&
                c->profile.side != _moi.combattant->profile.side && profil.finishDowned > 0) {
                _aTerre.push_back(present);
            }
            // Les allies hors de combat : qu'un soin releve, qu'un sort ramene (LOT-142).
            if (id != acteur && c->profile.side == _moi.combattant->profile.side) {
                if (c->status == CombatantStatus::Down) {
                    _alliesATerre.push_back(present);
                } else if (c->status == CombatantStatus::Dead) {
                    _alliesMorts.push_back(present);
                }
            }
            if (id == acteur || c->status != CombatantStatus::Standing) {
                continue;
            }
            (c->profile.side == _moi.combattant->profile.side ? _allies : _ennemis)
                .push_back(present);
        }
        for (const Present& ennemi : _ennemis) {
            _mobilite.push_back(destinationsDe(ennemi));
        }
        // L'IA repartit ses coups (LOT-139) : un ennemi a terre ne se finit que si aucun ennemi
        // debout ne menace l'acteur au contact -- s'acharner sur un blesse pendant qu'un autre
        // frappe, c'est ce que le critere du lot interdit. Decision nommee : le Guide du Maitre
        // ne dit rien d'achever (LOT-137, D10).
        if (!_aTerre.empty() && menacesImmediates(_moi.volume.base) > 0) {
            _aTerre.clear();
        }
    }

    [[nodiscard]] bool valide() const noexcept {
        return _valide;
    }
    [[nodiscard]] const Present& moi() const noexcept {
        return _moi;
    }
    [[nodiscard]] const std::vector<Present>& ennemis() const noexcept {
        return _ennemis;
    }

    // Le volume de l'acteur pose en @p ancre, au sol de l'espace.
    [[nodiscard]] Volume volumeEn(Meters3 ancre) const {
        Volume ici = _moi.volume;
        ici.base = {ancre.x, ancre.y, _espace.groundHeight(ancre.x, ancre.y)};
        return ici;
    }

    // Les corps qui abritent entre deux combattants : tous les places, sauf les deux, l'acteur
    // compte a sa place supposee.
    [[nodiscard]] std::vector<Volume> corps(CombatantId a, CombatantId b,
                                            Meters3 ancreActeur) const {
        std::vector<Volume> liste;
        for (const Present& p : _places) {
            if (p.id == a || p.id == b) {
                continue;
            }
            liste.push_back(p.id == _moi.id ? volumeEn(ancreActeur) : p.volume);
        }
        return liste;
    }

    // Le nombre d'ennemis debout qui peuvent frapper l'ancre **au contact** sans bouger. Un tireur
    // ne compte pas : sa portee couvre l'arene, et la cle anti-suicide n'interdirait plus rien
    // d'autre que d'approcher ; il pese dans `menace`.
    [[nodiscard]] int menacesImmediates(Meters3 ancre) const {
        int total = 0;
        const Volume ici = volumeEn(ancre);
        for (const Present& ennemi : _ennemis) {
            if (ennemi.attaques == nullptr) {
                continue;
            }
            const float ecart = edgeDistance(ennemi.volume, ici);
            const bool frappe = std::ranges::any_of(*ennemi.attaques, [&](const AttackProfile& a) {
                return a.kind == AttackKind::Melee && profileReaches(a, ecart);
            });
            if (frappe && hasLineOfSight(_espace, ennemi.volume, ici)) {
                ++total;
            }
        }
        return total;
    }

    // Les degats attendus au prochain round sur l'ancre, en huit-centiemes : chaque ennemi qui peut
    // y frapper, en marchant puis au contact, ou a distance depuis sa portee plus sa vitesse, avec
    // sa meilleure attaque, contre la CA de l'acteur.
    [[nodiscard]] long long menace(Meters3 ancre, bool esquive) const {
        long long total = 0;
        const Volume ici = volumeEn(ancre);
        const RollStance posture = esquive ? RollStance::Disadvantage : RollStance::Normal;
        const int ca = _moi.combattant->profile.armorClass;
        for (std::size_t i = 0; i < _ennemis.size(); ++i) {
            const Present& ennemi = _ennemis[i];
            if (ennemi.attaques == nullptr) {
                continue;
            }
            long long pire = 0;
            for (const AttackProfile& attaque : *ennemi.attaques) {
                if (attaque.kind == AttackKind::Melee) {
                    const bool atteint = std::ranges::any_of(_mobilite[i], [&](Meters3 depuis) {
                        Volume la = ennemi.volume;
                        la.base = depuis;
                        return withinTiles(edgeDistance(la, ici), attaque.reach);
                    });
                    if (atteint) {
                        pire = std::max(pire, expectedDamage(attaque, ca, posture));
                    }
                    continue;
                }
                const int portee = attaque.range.has_value() ? attaque.range->maximum : 1;
                if (!withinTiles(edgeDistance(ennemi.volume, ici),
                                 portee + ennemi.combattant->profile.movement)) {
                    continue;
                }
                // Sans abri : un tireur qui marche trouve sa place, et compter l'abri de chaque
                // place contre chaque tireur doublait le cout d'un tour pour une nuance de deux
                // points.
                pire = std::max(pire, expectedDamage(attaque, ca, posture));
            }
            total += pire;
        }
        return total;
    }

    // Les attaques d'opportunite que provoque le chemin jusqu'a la destination, en huit-centiemes.
    [[nodiscard]] long long opportunites(const Destination& destination) const {
        if (destination.route.points.empty()) {
            return 0;
        }
        std::vector<Meters3> points{_moi.volume.base};
        points.insert(points.end(), destination.route.points.begin(),
                      destination.route.points.end());
        long long total = 0;
        std::set<CombatantId> deja;
        const int ca = _moi.combattant->profile.armorClass;
        for (std::size_t pas = 0; pas + 1 < points.size(); ++pas) {
            const Volume avant = volumeEn(points[pas]);
            const Volume apres = volumeEn(points[pas + 1]);
            for (const Present& ennemi : _ennemis) {
                if (deja.contains(ennemi.id) || ennemi.attaques == nullptr ||
                    ennemi.combattant->economy.remaining(REACTION_RESOURCE) <= 0) {
                    continue;
                }
                const auto coup =
                    std::ranges::find(*ennemi.attaques, AttackKind::Melee, &AttackProfile::kind);
                if (coup == ennemi.attaques->end()) {
                    continue;
                }
                if (withinTiles(edgeDistance(avant, ennemi.volume), coup->reach) &&
                    !withinTiles(edgeDistance(apres, ennemi.volume), coup->reach) &&
                    hasLineOfSight(_espace, avant, ennemi.volume)) {
                    deja.insert(ennemi.id);
                    total += expectedDamage(*coup, ca, RollStance::Normal);
                }
            }
        }
        return total;
    }

    // Une attaque evaluee depuis une ancre.
    struct Frappe {
        CombatantId cible{};
        std::size_t indice = 0;
        int requis = 0;
        RollStance posture = RollStance::Normal;
        std::vector<std::string> circonstances;
        // L'esperance, deja ponderee par le profil, en huit-centiemes de point fois cent.
        long long valeur = 0;
    };

    // Toutes les attaques valides depuis l'ancre, par cible puis par indice d'attaque.
    [[nodiscard]] std::vector<Frappe> frappes(Meters3 ancre) const {
        std::vector<Frappe> liste;
        if (_moi.attaques == nullptr) {
            return liste;
        }
        const Volume ici = volumeEn(ancre);
        // Un ennemi qui voit l'acteur a une case gene le tir : une fois par ancre, pas par cible.
        std::optional<bool> auContact;
        std::vector<const Present*> visees;
        visees.reserve(_ennemis.size() + _aTerre.size());
        for (const Present& cible : _ennemis) {
            visees.push_back(&cible);
        }
        for (const Present& cible : _aTerre) {
            visees.push_back(&cible);
        }
        for (const Present* visee : visees) {
            const Present& cible = *visee;
            const float distance = edgeDistance(ici, cible.volume);
            const bool uneAPortee = std::ranges::any_of(
                *_moi.attaques,
                [&](const AttackProfile& a) { return profileReaches(a, distance); });
            if (!uneAPortee || !hasLineOfSight(_espace, ici, cible.volume)) {
                continue;
            }
            const std::vector<Volume> abris = corps(_moi.id, cible.id, ancre);
            const Cover abri = coverFrom(_espace, ici, cible.volume, abris);
            const int ca = cible.combattant->profile.armorClass + coverBonus(abri);
            const long long pourcent = cible.combattant->status == CombatantStatus::Down
                                           ? _profil.finishDowned
                                           : pourcentContre(cible);

            for (std::size_t i = 0; i < _moi.attaques->size(); ++i) {
                if (!profileReaches((*_moi.attaques)[i], distance)) {
                    continue;
                }
                // L'attaque telle que la session la jettera : le bonus au jet des capacites de
                // classe (Hit the Mark) s'y ajoute (LOT-142).
                AttackProfile attaque = (*_moi.attaques)[i];
                attaque.modifiers.insert(attaque.modifiers.end(), _bonusDeCapacites.begin(),
                                         _bonusDeCapacites.end());
                Frappe frappe{.cible = cible.id, .indice = i, .circonstances = {}};
                const RollStance posture =
                    postureDe(attaque, cible, ancre, distance, auContact, frappe);
                if (abri != Cover::None) {
                    frappe.circonstances.emplace_back(coverLabel(abri));
                }
                frappe.posture = posture;
                frappe.requis = requiredRoll(ca, attackBonusOf(attaque));
                frappe.valeur =
                    (expectedDamage(attaque, ca, frappe.posture) +
                     desDeCapacites(attaque, cible, ca, frappe.posture, frappe.circonstances)) *
                    pourcent;
                liste.push_back(std::move(frappe));
            }
        }
        return liste;
    }

    // Un sort evalue depuis une ancre (LOT-142).
    struct Lancer {
        CombatantId cible{};
        std::size_t indice = 0;
        // Deja ponderee, dans l'unite des frappes.
        long long valeur = 0;
        // Ce que le journal dit du geste : « soigne X », « blesse X ».
        std::string raison;
    };

    /**
     * Tous les sorts de l'action qui valent quelque chose depuis l'ancre : ceux qui blessent un
     * ennemi debout, soignent ou relevent un allie, ramenent un mort, benissent le groupe. Les
     * sorts d'action bonus se jouent apres l'action (`lancerBonus`).
     */
    [[nodiscard]] std::vector<Lancer> lancers(Meters3 ancre) const {
        std::vector<Lancer> liste;
        const std::vector<ArenaSpell>* const sorts = _session.spells(_moi.id);
        if (sorts == nullptr) {
            return liste;
        }
        std::optional<bool> auContact;
        for (std::size_t i = 0; i < sorts->size(); ++i) {
            const ArenaSpell& sort = (*sorts)[i];
            if (!sort.available() || sort.bonusAction) {
                continue;
            }
            switch (sort.mechanism) {
                case SpellMechanism::AttackRoll:
                case SpellMechanism::AutoHit:
                case SpellMechanism::SavingThrow:
                    for (const Present& cible : _ennemis) {
                        const long long valeur = blessure(sort, ancre, cible, auContact);
                        if (valeur > 0) {
                            liste.push_back({.cible = cible.id,
                                             .indice = i,
                                             .valeur = valeur,
                                             .raison = "blesse " + nom(cible.id)});
                        }
                    }
                    break;
                case SpellMechanism::Healing:
                    soins(sort, i, ancre, liste);
                    break;
                case SpellMechanism::Stabilize:
                    for (const Present& allie : _alliesATerre) {
                        if (!stable(allie.id) && aPortee(sort, ancre, allie)) {
                            liste.push_back({.cible = allie.id,
                                             .indice = i,
                                             .valeur = enValeur(STABILISER),
                                             .raison = "stabilise " + nom(allie.id)});
                        }
                    }
                    break;
                case SpellMechanism::Revive:
                    for (const Present& mort : _alliesMorts) {
                        if (ramenable(sort, mort) && aPortee(sort, ancre, mort)) {
                            liste.push_back({.cible = mort.id,
                                             .indice = i,
                                             .valeur = enValeur(RAMENER),
                                             .raison = "ramene " + nom(mort.id)});
                        }
                    }
                    break;
                case SpellMechanism::Effect:
                    benir(sort, i, ancre, liste);
                    break;
            }
        }
        return liste;
    }

    /**
     * Le sort d'action bonus a lancer depuis la place ou l'on est : celui qui blesse le plus un
     * ennemi debout (*arme spirituelle*), ou rien. L'arme deja invoquee frappe sans lancer : on
     * la propose meme sans lancer restant, la session tranche.
     */
    [[nodiscard]] std::optional<Lancer> lancerBonus() const {
        const std::vector<ArenaSpell>* const sorts = _session.spells(_moi.id);
        if (sorts == nullptr || _moi.combattant->economy.remaining(BONUS_ACTION_RESOURCE) <= 0) {
            return std::nullopt;
        }
        std::optional<Lancer> meilleur;
        std::optional<bool> auContact;
        for (std::size_t i = 0; i < sorts->size(); ++i) {
            const ArenaSpell& sort = (*sorts)[i];
            const bool armeInvoquee =
                std::ranges::any_of(_session.effects(), [&](const ArenaEffect& effet) {
                    return effet.bearer == _moi.id &&
                           effet.kind == SpellEffectKind::SpiritualWeapon &&
                           effet.source == sort.name;
                });
            if (!sort.bonusAction || sort.target != SpellTarget::Enemy ||
                (!sort.available() && !armeInvoquee)) {
                continue;
            }
            for (const Present& cible : _ennemis) {
                const long long valeur = blessure(sort, _moi.volume.base, cible, auContact);
                if (valeur > 0 && (!meilleur.has_value() || valeur > meilleur->valeur)) {
                    meilleur = Lancer{.cible = cible.id,
                                      .indice = i,
                                      .valeur = valeur,
                                      .raison = "blesse " + nom(cible.id)};
                }
            }
        }
        return meilleur;
    }

    // Le poids de la menace pour l'acteur : plus lourd s'il est ensanglante.
    [[nodiscard]] long long poidsMenace() const noexcept {
        return isBloodied(_moi.combattant->profile) ? _profil.threatWhenBloodied
                                                    : _profil.threatTaken;
    }

private:
    /**
     * L'esperance des des qu'une capacite ajoute a la touche (*Sneak Attack*), en
     * huit-centiemes, aux conditions du jet reel (`ArenaSession::hookCapacities`) : un allie
     * debout au contact de la cible, et pas deja jouee ce tour. Le critique double les des.
     */
    [[nodiscard]] long long desDeCapacites(const AttackProfile& attaque, const Present& cible,
                                           int ca, RollStance posture,
                                           std::vector<std::string>& circonstances) const {
        if (_desDeCapacites.empty() || attaque.damage.empty()) {
            return 0;
        }
        const std::string proprietaire = std::to_string(static_cast<std::uint32_t>(_moi.id));
        const long long touche =
            hitChance(requiredRoll(ca, attackBonusOf(attaque)), posture, attaque.criticalThreshold);
        const long long critique = criticalChance(attaque.criticalThreshold, posture);
        long long total = 0;
        for (const NamedExtraDamage& supplement : _desDeCapacites) {
            if (supplement.allyAdjacentToTarget &&
                std::ranges::none_of(_allies, [&](const Present& allie) {
                    return adjacentGap(edgeDistance(allie.volume, cible.volume));
                })) {
                continue;
            }
            if (supplement.oncePerTurn && _combat.counters().value(CounterScope::Turn, proprietaire,
                                                                   supplement.capacityId) > 0) {
                continue;
            }
            const long long des =
                static_cast<long long>(supplement.dice.count) * (supplement.dice.faces + 1);
            total += (touche + critique) * des;
            circonstances.push_back(supplement.source);
        }
        return total;
    }

    [[nodiscard]] std::string nom(CombatantId id) const {
        const Combatant* c = _combat.find(id);
        return (c == nullptr ? std::string("?") : c->profile.name) + " #" +
               std::to_string(static_cast<std::uint32_t>(id));
    }

    // Vrai si le sort atteint @p cible depuis l'ancre : a portee, en vue.
    [[nodiscard]] bool aPortee(const ArenaSpell& sort, Meters3 ancre, const Present& cible) const {
        const Volume ici = volumeEn(ancre);
        return profileReaches(sort.attack, edgeDistance(ici, cible.volume)) &&
               hasLineOfSight(_espace, ici, cible.volume);
    }

    // L'esperance d'un sort a sauvegarde sur @p creature, en huit-centiemes : la chance qu'elle
    // rate fois les degats, et la moitie a la reussite si le sort le dit.
    [[nodiscard]] static long long sauvegardeAttendue(const ArenaSpell& sort,
                                                      const Combatant& creature) {
        const Ability caracteristique = sort.save.value_or(Ability::Dexterity);
        const int bonus = creature.profile.savingThrows[static_cast<std::size_t>(caracteristique)];
        const long long reussite =
            static_cast<long long>(std::clamp(21 - (sort.saveDc - bonus), 0, 20)) * 20;
        const long long ratee = CHANCE_SCALE - reussite;
        const long long moyens = degatsMoyens(sort.attack).first;
        const long long moitie = sort.saveEffect == SaveEffect::Half ? reussite * moyens / 2 : 0;
        return (ratee * moyens) + moitie;
    }

    // Ce que vaut un sort qui blesse, lance depuis l'ancre sur @p cible ; 0 s'il ne l'atteint
    // pas. Une sphere pese chaque creature qu'elle prend, les allies en moins.
    [[nodiscard]] long long blessure(const ArenaSpell& sort, Meters3 ancre, const Present& cible,
                                     std::optional<bool>& auContact) const {
        if (!aPortee(sort, ancre, cible)) {
            return 0;
        }
        const long long pourcent = pourcentContre(cible);
        const Volume ici = volumeEn(ancre);
        const float distance = edgeDistance(ici, cible.volume);
        switch (sort.mechanism) {
            case SpellMechanism::AttackRoll: {
                const std::vector<Volume> abris = corps(_moi.id, cible.id, ancre);
                const Cover abri = coverFrom(_espace, ici, cible.volume, abris);
                const int ca = cible.combattant->profile.armorClass + coverBonus(abri);
                Frappe trace{.cible = cible.id, .circonstances = {}};
                const RollStance posture =
                    postureDe(sort.attack, cible, ancre, distance, auContact, trace);
                return expectedDamage(sort.attack, ca, posture) * sort.projectiles * pourcent;
            }
            case SpellMechanism::AutoHit:
                return CHANCE_SCALE * degatsMoyens(sort.attack).first * sort.projectiles * pourcent;
            case SpellMechanism::SavingThrow:
                break;
            case SpellMechanism::Effect:
            case SpellMechanism::Healing:
            case SpellMechanism::Stabilize:
            case SpellMechanism::Revive:
                return 0;
        }
        if (sort.areaRadiusMeters <= 0.0f) {
            return sauvegardeAttendue(sort, *cible.combattant) * pourcent;
        }
        // La sphere se centre sur la cible (ArenaSession::castSavingThrow) : tout ce qu'elle
        // prend compte, le lanceur a sa place supposee.
        const Meters3 centre = centerOf(cible.volume);
        const Effect sphere{.shape = AreaShape::Sphere,
                            .origin = centre,
                            .toward = centre,
                            .size = sort.areaRadiusMeters,
                            .width = METERS_PER_TILE};
        const std::vector<CombatantId> pris = combatantsInArea(_combat, sphere);
        long long total = 0;
        for (const CombatantId id : pris) {
            const Combatant* creature = _combat.find(id);
            if (id == _moi.id || creature == nullptr ||
                (creature->status != CombatantStatus::Standing &&
                 creature->status != CombatantStatus::Down)) {
                continue;
            }
            const long long attendu = sauvegardeAttendue(sort, *creature);
            if (creature->profile.side == _moi.combattant->profile.side) {
                total -= ALLIE_TOUCHE * POURCENT_PLEIN * attendu;
            } else if (creature->status == CombatantStatus::Standing) {
                total += _profil.damageDealt * attendu;
            }
        }
        if (shapeHits(sphere, ici)) {
            total -= ALLIE_TOUCHE * POURCENT_PLEIN * sauvegardeAttendue(sort, *_moi.combattant);
        }
        return total;
    }

    // Les soins d'un sort : un allie ensanglante (soi compris), borne a ce qui lui manque ; un
    // allie a terre, releve.
    void soins(const ArenaSpell& sort, std::size_t indice, Meters3 ancre,
               std::vector<Lancer>& liste) const {
        if (!sort.healing.has_value() || sort.target == SpellTarget::Enemy) {
            return;
        }
        const Dice& des = *sort.healing;
        const long long moyenne = std::max(
            0LL, (static_cast<long long>(des.count) * (des.faces + 1)) + (2LL * des.modifier));
        const auto soigner = [&](const Present& allie, bool soiMeme) {
            const CombatantProfile& profil = allie.combattant->profile;
            if (!isBloodied(profil) || (!soiMeme && !aPortee(sort, ancre, allie))) {
                return;
            }
            const long long manque = 2LL * (profil.maximumHitPoints - profil.currentHitPoints);
            liste.push_back({.cible = allie.id,
                             .indice = indice,
                             .valeur = CHANCE_SCALE * std::min(moyenne, manque) * POURCENT_PLEIN,
                             .raison = "soigne " + nom(allie.id)});
        };
        if (sort.target != SpellTarget::Self) {
            for (const Present& allie : _allies) {
                soigner(allie, false);
            }
            for (const Present& allie : _alliesATerre) {
                if (aPortee(sort, ancre, allie)) {
                    liste.push_back(
                        {.cible = allie.id,
                         .indice = indice,
                         .valeur = (CHANCE_SCALE * moyenne * POURCENT_PLEIN) + enValeur(RELEVER),
                         .raison = "releve " + nom(allie.id)});
                }
            }
        }
        soigner(_moi, true);
    }

    // *Benediction* : l'acteur et les allies debout a portee, jusqu'au nombre de cibles du sort,
    // quand il ne se concentre sur rien.
    void benir(const ArenaSpell& sort, std::size_t indice, Meters3 ancre,
               std::vector<Lancer>& liste) const {
        if (!sort.effect.has_value() || sort.effect->kind != SpellEffectKind::Bless) {
            return;
        }
        const bool concentre =
            std::ranges::any_of(_session.effects(), [&](const ArenaEffect& effet) {
                return effet.caster == _moi.id && effet.concentration;
            });
        if (concentre) {
            return;
        }
        long long benis = 1;
        for (const Present& allie : _allies) {
            if (benis < sort.maxTargets && aPortee(sort, ancre, allie)) {
                ++benis;
            }
        }
        liste.push_back({.cible = _moi.id,
                         .indice = indice,
                         .valeur = enValeur(BENIR) * benis,
                         .raison = "benit " + std::to_string(benis) + " allie(s)"});
    }

    [[nodiscard]] bool stable(CombatantId id) const {
        const std::vector<CombatCondition> etats = _session.conditionsOf(id);
        return std::ranges::find(etats, CombatCondition::Stable) != etats.end();
    }

    [[nodiscard]] bool ramenable(const ArenaSpell& sort, const Present& mort) const {
        return sort.revival.has_value() && mort.combattant->diedAtRound.has_value() &&
               _combat.round() - *mort.combattant->diedAtRound <= sort.revival->withinRounds;
    }

    // Le pourcentage du profil contre @p cible : les degats, plus une cible ensanglantee, les
    // allies a son contact, et un allie ensanglante a proteger.
    [[nodiscard]] long long pourcentContre(const Present& cible) const {
        int allieAuContact = 0;
        bool allieEnsanglante = false;
        for (const Present& allie : _allies) {
            if (adjacentGap(edgeDistance(allie.volume, cible.volume))) {
                ++allieAuContact;
                allieEnsanglante = allieEnsanglante || isBloodied(allie.combattant->profile);
            }
        }
        long long pourcent = _profil.damageDealt;
        if (isBloodied(cible.combattant->profile)) {
            pourcent += _profil.bloodiedTarget;
        }
        pourcent += static_cast<long long>(_profil.focusFire) * allieAuContact;
        if (allieEnsanglante) {
            pourcent += _profil.protectBloodiedAlly;
        }
        return pourcent;
    }

    // Les sources d'avantage et de desavantage d'une attaque depuis l'ancre, notees dans
    // @p frappe, et la posture qu'elles donnent. @p auContact est calcule au premier tir.
    [[nodiscard]] RollStance postureDe(const AttackProfile& attaque, const Present& cible,
                                       Meters3 ancre, float distance,
                                       std::optional<bool>& auContact, Frappe& frappe) const {
        const Volume ici = volumeEn(ancre);
        int avantages = 0;
        int desavantages = 0;
        // Manuel, annexe A : ce que la session ajoutera au jet (LOT-137).
        if (cible.combattant->status == CombatantStatus::Down) {
            ++avantages;
            frappe.circonstances.emplace_back("cible inconsciente");
        }
        if (cible.combattant->prone || cible.combattant->status == CombatantStatus::Down) {
            if (adjacentGap(distance)) {
                ++avantages;
                frappe.circonstances.emplace_back("cible a terre au contact");
            } else {
                ++desavantages;
                frappe.circonstances.emplace_back("cible a terre a distance");
            }
        }
        if (attaque.kind == AttackKind::Melee && _session.bout().flanking &&
            isFlankedFrom(_combat, _moi.id, ancre, cible.id)) {
            ++avantages;
            frappe.circonstances.emplace_back("prise en tenaille");
        }
        // La hauteur, comme la session la comptera (core::attackCircumstances, LOT-1017).
        if (hasHighGround(ici, cible.volume)) {
            ++avantages;
            frappe.circonstances.emplace_back("hauteur");
        }
        if (attaque.kind == AttackKind::Ranged) {
            if (attaque.range.has_value() && !withinTiles(distance, attaque.range->normal)) {
                ++desavantages;
                frappe.circonstances.emplace_back("longue portee");
            }
            if (!auContact.has_value()) {
                auContact = ennemiAuContact(ancre);
            }
            if (*auContact) {
                ++desavantages;
                frappe.circonstances.emplace_back("tir au contact d'un ennemi");
            }
        }
        if (_session.isDodging(cible.id) && hasLineOfSight(_espace, cible.volume, ici)) {
            ++desavantages;
            frappe.circonstances.emplace_back("esquive de la cible");
        }
        return rollStance(avantages, desavantages);
    }

    // Vrai si un ennemi qui voit l'acteur se tient a une case de l'ancre.
    [[nodiscard]] bool ennemiAuContact(Meters3 ancre) const {
        const Volume ici = volumeEn(ancre);
        return std::ranges::any_of(_ennemis, [&](const Present& e) {
            return adjacentGap(edgeDistance(ici, e.volume)) &&
                   hasLineOfSight(_espace, e.volume, ici);
        });
    }

    // Les places d'ou un ennemi peut frapper au prochain round : la sienne et celles qu'il
    // atteint.
    [[nodiscard]] std::vector<Meters3> destinationsDe(const Present& ennemi) const {
        std::vector<Meters3> liste;
        for (const Destination& d : _combat.destinationsFor(
                 ennemi.id,
                 metersFromTiles(static_cast<float>(ennemi.combattant->profile.movement)))) {
            liste.push_back(d.point);
        }
        if (liste.empty()) {
            liste.push_back(ennemi.volume.base);
        }
        return liste;
    }

    const ArenaSession& _session;
    const CombatState& _combat;
    const CombatSpace& _espace;
    const BehaviorProfile& _profil;
    bool _valide = false;
    Present _moi;
    std::vector<Present> _places;
    std::vector<Present> _allies;
    std::vector<Present> _ennemis;
    /// Les ennemis a terre que le profil acheve (LOT-137) : des cibles, jamais des menaces.
    std::vector<Present> _aTerre;
    /// Le bonus au jet et les des a la touche que les capacites de l'acteur donnent (LOT-142).
    std::vector<Modifier> _bonusDeCapacites;
    std::vector<NamedExtraDamage> _desDeCapacites;
    /// Les allies a terre et les allies morts : ce que soignent et ramenent les sorts (LOT-142).
    std::vector<Present> _alliesATerre;
    std::vector<Present> _alliesMorts;
    std::vector<std::vector<Meters3>> _mobilite;
};

// L'ordre d'un candidat : moins d'exces de menace, puis attaquer, puis avancer vers l'ennemi,
// puis le score, puis le moins de deplacement. Un candidat ne remplace le meilleur que s'il le
// bat strictement : a egalite, le premier examine reste. « Avancer » est une cle et non un
// poids : la menace d'un round entier pese plus que quelques metres d'approche, et une IA qui ne
// peut pas attaquer resterait hors de portee — ou reculerait — a jamais. Le deplacement departage
// les places equivalentes : sans lui, la premiere examinee l'emportait.
struct Cle {
    int exces = 0;
    bool attaque = false;
    bool progresse = false;
    long long score = 0;
    /// En centimetres.
    long long deplacement = 0;

    [[nodiscard]] bool meilleureQue(const Cle& autre) const noexcept {
        if (exces != autre.exces) {
            return exces < autre.exces;
        }
        if (attaque != autre.attaque) {
            return attaque;
        }
        if (progresse != autre.progresse) {
            return progresse;
        }
        if (score != autre.score) {
            return score > autre.score;
        }
        return deplacement < autre.deplacement;
    }
};

[[nodiscard]] std::string nomDe(const CombatState& combat, CombatantId id) {
    const Combatant* c = combat.find(id);
    return (c == nullptr ? std::string("?") : c->profile.name) + " #" +
           std::to_string(static_cast<std::uint32_t>(id));
}

// Le chemin le plus court jusqu'au contact d'un ennemi : la cible d'une approche.
struct Approche {
    CombatantId cible{};
    Route chemin;
};

// Une seule exploration, sans limite de budget : la place la plus proche, par le chemin, a une
// case d'un ennemi debout (LOT-1017 : les candidats de l'espace, au lieu des cases voisines). A
// longueur egale, le premier ennemi, puis la premiere place.
[[nodiscard]] std::optional<Approche> approcheLaPlusCourte(const CombatState& combat,
                                                           const Evaluateur& eval) {
    const Present& moi = eval.moi();
    for (const Present& ennemi : eval.ennemis()) {
        if (adjacentGap(edgeDistance(moi.volume, ennemi.volume))) {
            return Approche{.cible = ennemi.id, .chemin = {}};
        }
    }
    std::optional<Approche> meilleure;
    for (const Destination& place : combat.destinationsFor(moi.id, -1.0f)) {
        if (place.route.points.empty()) {
            continue;
        }
        const Volume la = eval.volumeEn(place.point);
        for (const Present& ennemi : eval.ennemis()) {
            if (!adjacentGap(edgeDistance(la, ennemi.volume))) {
                continue;
            }
            if (!meilleure.has_value() ||
                centimetres(place.route.length) < centimetres(meilleure->chemin.length)) {
                meilleure = Approche{.cible = ennemi.id, .chemin = place.route};
            }
            break;
        }
    }
    return meilleure;
}

// Le reste du chemin d'approche depuis une destination, en centimetres : exact sur le chemin,
// estime ailleurs par l'ecart a la cible au-dela du contact, plus le detour que le chemin impose.
[[nodiscard]] long long resteDApproche(const CombatState& combat, const Evaluateur& eval,
                                       const Approche& approche, const Destination& place) {
    const Present& moi = eval.moi();
    const long long total = centimetres(approche.chemin.length);
    const bool depart = place.route.points.empty();
    const bool surLeChemin = std::ranges::any_of(
        approche.chemin.points, [&](Meters3 p) { return memePoint(p, place.point); });
    if (depart || surLeChemin) {
        return std::max(0LL, total - centimetres(place.route.length));
    }
    const std::optional<Volume> cible = combat.volumeOf(approche.cible);
    if (!cible.has_value()) {
        return total;
    }
    const auto auDelaDuContact = [&](const Volume& depuis) {
        return std::max(0LL, centimetres(edgeDistance(depuis, *cible)) - CENTIMETRES_PAR_CASE);
    };
    const long long direct = auDelaDuContact(moi.volume);
    const long long detour = std::max(0LL, total - direct);
    return auDelaDuContact(eval.volumeEn(place.point)) + detour;
}

// Le point le plus loin du chemin d'approche ou l'on peut finir parmi @p places : jusqu'ou une
// approche va.
[[nodiscard]] const Destination* plusLoinSurLeChemin(const Route& chemin,
                                                     const std::vector<Destination>& places) {
    for (auto it = chemin.points.rbegin(); it != chemin.points.rend(); ++it) {
        const auto trouve = std::ranges::find_if(places, [&](const Destination& d) {
            return !d.route.points.empty() && memePoint(d.point, *it);
        });
        if (trouve != places.end()) {
            return &*trouve;
        }
    }
    return nullptr;
}

[[nodiscard]] std::string_view nomDePosture(RollStance posture) noexcept {
    switch (posture) {
        case RollStance::Advantage:
            return ", avantage";
        case RollStance::Disadvantage:
            return ", desavantage";
        case RollStance::Normal:
            break;
    }
    return "";
}

// Le cout d'approche de @p resteCm centimetres, au taux du profil par case.
[[nodiscard]] long long coutDApproche(const BehaviorProfile& profile, long long resteCm) {
    return static_cast<long long>(profile.approachPerTile) * UNITES_PAR_POINT * resteCm /
           CENTIMETRES_PAR_CASE;
}

}  // namespace

// --- Ce que la table sait ---------------------------------------------------------------------

int attackBonusOf(const AttackProfile& profile) noexcept {
    int bonus = 0;
    for (const Modifier& modificateur : profile.modifiers) {
        bonus += modificateur.value;
    }
    return bonus;
}

int hitChance(int required, RollStance stance, int criticalThreshold) noexcept {
    return chanceSelonPosture(facesQuiTouchent(required, criticalThreshold), stance);
}

int criticalChance(int criticalThreshold, RollStance stance) noexcept {
    const int seuil = std::clamp(criticalThreshold, 2, 20);
    return chanceSelonPosture(21 - seuil, stance);
}

long long expectedDamage(const AttackProfile& profile, int armorClass, RollStance stance) noexcept {
    const int requis = requiredRoll(armorClass, attackBonusOf(profile));
    const long long touche =
        chanceSelonPosture(facesQuiTouchent(requis, profile.criticalThreshold), stance);
    const long long critique = criticalChance(profile.criticalThreshold, stance);
    const auto [moyens, des] = degatsMoyens(profile);
    return (touche * moyens) + (critique * des);
}

// --- Les profils --------------------------------------------------------------------------------

const BehaviorProfile* BehaviorCatalog::find(std::string_view id) const {
    const auto trouve = std::ranges::find(profiles, id, &BehaviorProfile::id);
    return trouve == profiles.end() ? nullptr : &*trouve;
}

BehaviorCatalog loadBehaviors(const std::filesystem::path& file) {
    BehaviorCatalog catalogue;
    const JsonDocument document = readJsonObjectFromFile(file, SANS_GARDE_DE_VERSION);
    if (!document.ok()) {
        catalogue.errors.push_back(document.message);
        return catalogue;
    }
    const std::string fichier = file.filename().string();
    const nlohmann::json& racine = document.root;
    const auto profils = racine.find("profiles");
    if (profils == racine.end() || !profils->is_array()) {
        catalogue.errors.push_back(fichier + " : aucune liste « profiles ».");
        return catalogue;
    }
    const BehaviorProfile defaut;
    for (const nlohmann::json& entree : *profils) {
        if (!entree.is_object()) {
            continue;
        }
        BehaviorProfile profil{
            .id = lireTexte(entree, "id"),
            .name = lireTexte(entree, "name"),
            .damageDealt = lireEntier(entree, "damageDealt", defaut.damageDealt),
            .bloodiedTarget = lireEntier(entree, "bloodiedTarget", defaut.bloodiedTarget),
            .focusFire = lireEntier(entree, "focusFire", defaut.focusFire),
            .protectBloodiedAlly =
                lireEntier(entree, "protectBloodiedAlly", defaut.protectBloodiedAlly),
            .threatTaken = lireEntier(entree, "threatTaken", defaut.threatTaken),
            .threatWhenBloodied =
                lireEntier(entree, "threatWhenBloodied", defaut.threatWhenBloodied),
            .opportunityTaken = lireEntier(entree, "opportunityTaken", defaut.opportunityTaken),
            .approachPerTile = lireEntier(entree, "approachPerTile", defaut.approachPerTile),
            .toleratedThreats = lireEntier(entree, "toleratedThreats", defaut.toleratedThreats),
            .opportunityMaximumRoll =
                lireEntier(entree, "opportunityMaximumRoll", defaut.opportunityMaximumRoll),
            .dodgeWhenThreatened =
                lireBooleen(entree, "dodgeWhenThreatened", defaut.dodgeWhenThreatened),
            .retreatAfterAttack =
                lireBooleen(entree, "retreatAfterAttack", defaut.retreatAfterAttack),
            .finishDowned = lireEntier(entree, "finishDowned", defaut.finishDowned)};
        if (profil.id.empty()) {
            catalogue.errors.push_back(fichier + " : profil sans identifiant.");
            continue;
        }
        if (catalogue.find(profil.id) != nullptr) {
            catalogue.errors.push_back(fichier + " : profil « " + profil.id + " » en double.");
            continue;
        }
        catalogue.profiles.push_back(std::move(profil));
    }
    catalogue.defaultBehavior = lireTexte(racine, "default");
    if (catalogue.find(catalogue.defaultBehavior) == nullptr) {
        catalogue.errors.push_back(fichier + " : profil par defaut « " + catalogue.defaultBehavior +
                                   " » inconnu.");
    }
    const auto regles = racine.find("assignments");
    if (regles != racine.end() && regles->is_array()) {
        for (const nlohmann::json& entree : *regles) {
            if (!entree.is_object()) {
                continue;
            }
            BehaviorAssignment regle{.behavior = lireTexte(entree, "behavior"),
                                     .trait = lireTexte(entree, "trait"),
                                     .creature = lireTexte(entree, "creature"),
                                     .ranged = lireBooleen(entree, "ranged", false)};
            if (catalogue.find(regle.behavior) == nullptr) {
                catalogue.errors.push_back(fichier + " : attribution vers le profil inconnu « " +
                                           regle.behavior + " ».");
                continue;
            }
            if (regle.trait.empty() && regle.creature.empty() && !regle.ranged) {
                catalogue.errors.push_back(fichier + " : attribution sans condition vers « " +
                                           regle.behavior + " ».");
                continue;
            }
            catalogue.assignments.push_back(std::move(regle));
        }
    }
    return catalogue;
}

std::string behaviorFor(const Creature& creature, const BehaviorCatalog& catalog) {
    const CreatureAttacks attaques = attacksFor(creature);
    long long auContact = 0;
    long long aDistance = 0;
    for (const AttackProfile& attaque : attaques.attacks) {
        const long long moyens = degatsMoyens(attaque).first;
        if (attaque.kind == AttackKind::Melee) {
            auContact = std::max(auContact, moyens);
        } else if (attaque.range.has_value()) {
            aDistance = std::max(aDistance, moyens);
        }
    }
    const bool tireur = aDistance > 0 && aDistance >= auContact;
    for (const BehaviorAssignment& regle : catalog.assignments) {
        const bool trait = regle.trait.empty() ||
                           std::ranges::find(creature.traits, regle.trait, &CreatureTrait::name) !=
                               creature.traits.end();
        const bool laCreature = regle.creature.empty() || regle.creature == creature.id;
        const bool distance = !regle.ranged || tireur;
        if (trait && laCreature && distance) {
            return regle.behavior;
        }
    }
    return catalog.defaultBehavior;
}

// --- Le tour ----------------------------------------------------------------------------------

namespace {

// Les menaces au-dela de ce que le profil tolere.
[[nodiscard]] int excesDe(const BehaviorProfile& profile, int menaces) noexcept {
    return std::max(0, menaces - profile.toleratedThreats);
}

// La destination, ou rien si c'est la place de depart.
[[nodiscard]] std::optional<Meters3> versOuRester(const Destination& place) {
    return place.route.points.empty() ? std::nullopt : std::optional<Meters3>(place.point);
}

// Attaquer @p frappe depuis @p place, avec la ligne de journal qui le dit.
[[nodiscard]] TurnPlan planAttaque(const CombatState& combat, const BehaviorProfile& profile,
                                   const Present& moi, const Destination& place,
                                   const Evaluateur::Frappe& frappe, int menaces, long long cout) {
    TurnPlan candidat{.actor = moi.id,
                      .moveTo = versOuRester(place),
                      .action = TurnAction::Attack,
                      .target = frappe.cible,
                      .attackIndex = frappe.indice,
                      .dashTo = std::nullopt,
                      .requiredRoll = frappe.requis,
                      .stance = frappe.posture,
                      .immediateThreats = menaces,
                      .score = frappe.valeur - cout,
                      .summary = {}};
    std::string raisons;
    for (const std::string& c : frappe.circonstances) {
        raisons.append(", ").append(c);
    }
    candidat.summary = "ia " + profile.id + " " + nomDe(combat, moi.id) + " : attaque " +
                       nomDe(combat, frappe.cible) + " avec " +
                       (*moi.attaques)[frappe.indice].label + " depuis " + pointTexte(place.point) +
                       " (jet requis " + std::to_string(frappe.requis) +
                       std::string(nomDePosture(frappe.posture)) + raisons + ")";
    return candidat;
}

// Finir le deplacement en @p place sans attaquer, ou tenir sa place si c'est le depart.
[[nodiscard]] TurnPlan planTenir(const CombatState& combat, const BehaviorProfile& profile,
                                 CombatantId actor, const std::optional<Approche>& approche,
                                 const Destination& place, int menaces, long long score) {
    const std::optional<Meters3> vers = versOuRester(place);
    const std::string qui = "ia " + profile.id + " " + nomDe(combat, actor);
    const std::string cible =
        approche.has_value() ? " vers " + nomDe(combat, approche->cible) : std::string();

    TurnPlan tenir{.actor = actor,
                   .moveTo = vers,
                   .action = TurnAction::Wait,
                   .target = std::nullopt,
                   .dashTo = std::nullopt,
                   .immediateThreats = menaces,
                   .score = score,
                   .summary = {}};
    tenir.summary = qui + (vers.has_value() ? " : avance en " + pointTexte(place.point) + cible
                                            : std::string(" : tient sa place"));
    return tenir;
}

// Se precipiter : la vitesse une seconde fois, jusqu'au plus loin du chemin d'approche.
template <typename Proposer>
void proposerCourse(const CombatState& combat, const BehaviorProfile& profile,
                    const Evaluateur& eval, const Approche& approche, long long resteOrigine,
                    const Proposer& proposer) {
    if (approche.chemin.points.empty()) {
        return;
    }
    const Present& moi = eval.moi();
    const CombatantId actor = moi.id;
    const std::vector<Destination> loin = combat.destinationsFor(
        actor, combat.movementLeft() +
                   metersFromTiles(static_cast<float>(moi.combattant->profile.movement)));
    const Destination* but = plusLoinSurLeChemin(approche.chemin, loin);
    if (but == nullptr) {
        return;
    }
    const int menaces = eval.menacesImmediates(but->point);
    const long long reste =
        std::max(0LL, centimetres(approche.chemin.length) - centimetres(but->route.length));
    TurnPlan course{
        .actor = actor,
        .moveTo = std::nullopt,
        .action = TurnAction::Dash,
        .target = std::nullopt,
        .dashTo = but->point,
        .immediateThreats = menaces,
        .score = -coutDApproche(profile, reste) -
                 (eval.poidsMenace() * eval.menace(but->point, false)) -
                 (static_cast<long long>(profile.opportunityTaken) * eval.opportunites(*but)),
        .summary = {}};
    course.summary = "ia " + profile.id + " " + nomDe(combat, actor) + " : se precipite en " +
                     pointTexte(but->point) + " vers " + nomDe(combat, approche.cible);
    const long long scoreCourse = course.score;
    proposer({.exces = excesDe(profile, menaces),
              .attaque = false,
              .progresse = reste < resteOrigine,
              .score = scoreCourse,
              .deplacement = centimetres(but->route.length)},
             std::move(course));
}

// Reculer apres avoir frappe : vers une place moins menacee, si elle bat strictement la sienne.
// A menace egale, la moins loin : on ne file pas jusqu'au premier coin de la salle.
void reculerApresAttaque(ArenaSession& session, CombatantId actif, const BehaviorProfile& profil) {
    const CombatState& combat = session.combat();
    const Evaluateur eval(session, actif, profil);
    const std::vector<Destination> places = combat.destinations();
    if (!eval.valide() || places.empty()) {
        return;
    }
    const long long poids = eval.poidsMenace();
    const auto cleEn = [&](const Destination& place) {
        return Cle{
            .exces = std::max(0, eval.menacesImmediates(place.point) - profil.toleratedThreats),
            .attaque = false,
            .progresse = false,
            .score = (-poids * eval.menace(place.point, false)) -
                     (static_cast<long long>(profil.opportunityTaken) * eval.opportunites(place)),
            .deplacement = centimetres(place.route.length)};
    };
    Cle meilleure = cleEn(places.front());
    std::optional<Meters3> recul;
    for (std::size_t i = 1; i < places.size(); ++i) {
        const Cle cle = cleEn(places[i]);
        if (cle.meilleureQue(meilleure)) {
            meilleure = cle;
            recul = places[i].point;
        }
    }
    if (recul.has_value()) {
        session.note("ia " + profil.id + " " + nomDe(combat, actif) + " : recule en " +
                     pointTexte(*recul));
        static_cast<void>(session.move(*recul));
    }
}

// Les attaques que l'action *Attaquer* a laissees (Extra Attack, LOT-132) : chacune sur la
// meilleure frappe depuis la place ou l'on est, sans bouger (LOT-142). S'arrete quand il n'en
// reste plus, ou qu'aucune cible n'est a portee.
void attaquesSupplementaires(ArenaSession& session, CombatantId actif,
                             const BehaviorProfile& profil) {
    const CombatState& combat = session.combat();
    for (int garde = 0; garde < 4; ++garde) {
        const Combatant* moi = combat.find(actif);
        if (combat.phase() != CombatPhase::TurnActive || combat.activeCombatant() != actif ||
            moi == nullptr || moi->economy.remaining(EXTRA_ATTACK_RESOURCE) <= 0) {
            return;
        }
        const Evaluateur eval(session, actif, profil);
        const std::optional<Meters3> ici = combat.positionOf(actif);
        if (!eval.valide() || !ici.has_value()) {
            return;
        }
        const std::vector<Evaluateur::Frappe> frappes = eval.frappes(*ici);
        const auto meilleure = std::ranges::max_element(
            frappes, {}, [](const Evaluateur::Frappe& frappe) { return frappe.valeur; });
        if (meilleure == frappes.end()) {
            return;
        }
        if (session.attack(meilleure->cible, meilleure->indice).result != ArenaActionResult::Done) {
            return;
        }
    }
}

// Le sort d'action bonus, apres l'action (LOT-142) : l'arme spirituelle sur l'ennemi qu'elle
// blesse le plus.
void lancerLeSortBonus(ArenaSession& session, CombatantId actif, const BehaviorProfile& profil) {
    const Evaluateur eval(session, actif, profil);
    if (!eval.valide()) {
        return;
    }
    const std::optional<Evaluateur::Lancer> lancer = eval.lancerBonus();
    if (!lancer.has_value()) {
        return;
    }
    session.note("ia " + profil.id + " " + nomDe(session.combat(), actif) + " : action bonus, " +
                 (*session.spells(actif))[lancer->indice].name + ", " + lancer->raison);
    static_cast<void>(session.castSpell(lancer->cible, lancer->indice));
}

}  // namespace

TurnPlan planTurn(const ArenaSession& session, CombatantId actor, const BehaviorProfile& profile) {
    const CombatState& combat = session.combat();
    TurnPlan plan{.actor = actor,
                  .moveTo = std::nullopt,
                  .target = std::nullopt,
                  .dashTo = std::nullopt,
                  .summary = {}};
    const Evaluateur eval(session, actor, profile);
    if (!eval.valide() || combat.activeCombatant() != actor) {
        plan.summary = "ia " + profile.id + " " + nomDe(combat, actor) + " : attend";
        return plan;
    }
    // Les places ou finir le deplacement, la sienne en tete (core::CombatSpace::candidates).
    const std::vector<Destination> ancres = combat.destinations();
    if (ancres.empty()) {
        plan.summary = "ia " + profile.id + " " + nomDe(combat, actor) + " : attend";
        return plan;
    }
    const Present& moi = eval.moi();
    const bool action = moi.combattant->economy.remaining(ACTION_RESOURCE) > 0;
    const long long poidsMenace = eval.poidsMenace();

    std::optional<Cle> meilleure;
    const auto proposer = [&](const Cle& cle, TurnPlan candidat) {
        if (!meilleure.has_value() || cle.meilleureQue(*meilleure)) {
            meilleure = cle;
            plan = std::move(candidat);
        }
    };
    const auto exces = [&](int menaces) { return excesDe(profile, menaces); };

    // Ce qu'une place coute, calcule une fois : les deux familles de candidats le relisent.
    struct Cout {
        int menaces = 0;
        long long menace = 0;
        long long opportunites = 0;
    };
    std::vector<Cout> couts;
    couts.reserve(ancres.size());
    for (const Destination& place : ancres) {
        couts.push_back({.menaces = eval.menacesImmediates(place.point),
                         .menace = poidsMenace * eval.menace(place.point, false),
                         .opportunites = static_cast<long long>(profile.opportunityTaken) *
                                         eval.opportunites(place)});
    }

    // Attaquer : chaque place, chaque cible, chaque attaque.
    for (std::size_t indice = 0; action && indice < ancres.size(); ++indice) {
        const Destination& place = ancres[indice];
        const std::vector<Evaluateur::Frappe> frappes = eval.frappes(place.point);
        if (frappes.empty()) {
            continue;
        }
        const int menaces = couts[indice].menaces;
        const long long cout = couts[indice].menace + couts[indice].opportunites;
        for (const Evaluateur::Frappe& frappe : frappes) {
            TurnPlan candidat = planAttaque(combat, profile, moi, place, frappe, menaces, cout);
            const long long scoreCandidat = candidat.score;
            proposer({.exces = exces(menaces),
                      .attaque = true,
                      .progresse = true,
                      .score = scoreCandidat,
                      .deplacement = centimetres(place.route.length)},
                     std::move(candidat));
        }
    }

    // Lancer un sort : chaque place, chaque sort, chaque cible (LOT-142). C'est agir, comme
    // attaquer : la cle « attaque » le range avec les frappes, et le score les departage.
    for (std::size_t indice = 0; action && indice < ancres.size(); ++indice) {
        const Destination& place = ancres[indice];
        const std::vector<Evaluateur::Lancer> lancers = eval.lancers(place.point);
        if (lancers.empty()) {
            continue;
        }
        const int menaces = couts[indice].menaces;
        const long long cout = couts[indice].menace + couts[indice].opportunites;
        for (const Evaluateur::Lancer& lancer : lancers) {
            TurnPlan candidat{.actor = actor,
                              .moveTo = versOuRester(place),
                              .action = TurnAction::Cast,
                              .target = lancer.cible,
                              .spellIndex = lancer.indice,
                              .dashTo = std::nullopt,
                              .immediateThreats = menaces,
                              .score = lancer.valeur - cout,
                              .summary = {}};
            candidat.summary = "ia " + profile.id + " " + nomDe(combat, actor) + " : lance " +
                               (*session.spells(actor))[lancer.indice].name + ", " + lancer.raison +
                               ", depuis " + pointTexte(place.point);
            const long long scoreCandidat = candidat.score;
            proposer({.exces = exces(menaces),
                      .attaque = true,
                      .progresse = true,
                      .score = scoreCandidat,
                      .deplacement = centimetres(place.route.length)},
                     std::move(candidat));
        }
    }

    // Sans attaque : s'approcher, se precipiter, esquiver, ou tenir. Un candidat « progresse »
    // s'il laisse moins de chemin jusqu'a l'ennemi que la place de depart.
    const std::optional<Approche> approche = approcheLaPlusCourte(combat, eval);
    const long long resteOrigine = approche.has_value() ? centimetres(approche->chemin.length) : 0;
    for (std::size_t indice = 0; indice < ancres.size(); ++indice) {
        const Destination& place = ancres[indice];
        const int menaces = couts[indice].menaces;
        const long long reste =
            approche.has_value() ? resteDApproche(combat, eval, *approche, place) : 0;
        const bool progresse = reste < resteOrigine;
        const long long deplacement = centimetres(place.route.length);
        const long long opportunites = couts[indice].opportunites;
        const long long base = -coutDApproche(profile, reste);

        const TurnPlan tenir = planTenir(combat, profile, actor, approche, place, menaces,
                                         base - couts[indice].menace - opportunites);
        proposer({.exces = exces(menaces),
                  .attaque = false,
                  .progresse = progresse,
                  .score = tenir.score,
                  .deplacement = deplacement},
                 tenir);

        if (action && profile.dodgeWhenThreatened && menaces > 0) {
            TurnPlan esquive = tenir;
            esquive.action = TurnAction::Dodge;
            esquive.score = base - (poidsMenace * eval.menace(place.point, true)) - opportunites;
            esquive.summary += ", esquive";
            const long long scoreEsquive = esquive.score;
            proposer({.exces = exces(menaces),
                      .attaque = false,
                      .progresse = progresse,
                      .score = scoreEsquive,
                      .deplacement = deplacement},
                     std::move(esquive));
        }
        if (action && opportunites > 0) {
            TurnPlan desengage = tenir;
            desengage.action = TurnAction::Disengage;
            desengage.score = base - couts[indice].menace;
            desengage.summary += ", en se desengageant";
            const long long scoreDesengage = desengage.score;
            proposer({.exces = exces(menaces),
                      .attaque = false,
                      .progresse = progresse,
                      .score = scoreDesengage,
                      .deplacement = deplacement},
                     std::move(desengage));
        }
    }

    if (action && approche.has_value()) {
        proposerCourse(combat, profile, eval, *approche, resteOrigine, proposer);
    }
    return plan;
}

bool shouldTakeOpportunity(const ArenaSession& session, CombatantId reactor, CombatantId mover,
                           const BehaviorProfile& profile) {
    const std::vector<AttackProfile>* attaques = session.attacks(reactor);
    const Combatant* fuyard = session.combat().find(mover);
    if (attaques == nullptr || fuyard == nullptr) {
        return false;
    }
    const auto coup = std::ranges::find(*attaques, AttackKind::Melee, &AttackProfile::kind);
    return coup != attaques->end() &&
           requiredRoll(fuyard->profile.armorClass, attackBonusOf(*coup)) <=
               profile.opportunityMaximumRoll;
}

OpportunityPolicy aiOpportunityPolicy(const BehaviorCatalog& catalog) {
    return [&catalog](const ArenaSession& session, CombatantId reactor, CombatantId mover) {
        const std::string& id = session.behaviorOf(reactor);
        if (id.empty()) {
            return true;
        }
        const BehaviorProfile* profil = catalog.find(id);
        return profil == nullptr || shouldTakeOpportunity(session, reactor, mover, *profil);
    };
}

bool playTurn(ArenaSession& session, const BehaviorCatalog& catalog) {
    CombatState& combat = session.combat();
    const std::optional<CombatantId> actif = combat.activeCombatant();
    if (!actif.has_value() || combat.phase() != CombatPhase::TurnActive) {
        return false;
    }
    const BehaviorProfile* profil = catalog.find(session.behaviorOf(*actif));
    if (profil == nullptr) {
        return false;
    }
    const auto toujoursLui = [&] {
        return combat.phase() == CombatPhase::TurnActive && combat.activeCombatant() == actif;
    };
    const TurnPlan plan = planTurn(session, *actif, *profil);
    session.note(plan.summary);

    if (plan.action == TurnAction::Disengage) {
        static_cast<void>(session.disengage());
    }
    if (plan.moveTo.has_value() && toujoursLui()) {
        // Un deplacement refuse se dit : sans cette ligne, une IA qui « ne bouge pas » ne laisse
        // aucune trace de ce qu'elle a voulu, et l'audit ne peut pas distinguer un plan qui tient
        // sa place d'un pas que la grille a refuse (LOT-118).
        if (const MoveOutcome pas = session.move(*plan.moveTo); pas.result != MoveResult::Moved) {
            session.note("deplacement refuse vers " + pointTexte(*plan.moveTo));
        }
    }
    switch (plan.action) {
        case TurnAction::Attack:
            if (toujoursLui() && plan.target.has_value()) {
                static_cast<void>(session.attack(*plan.target, plan.attackIndex));
            }
            attaquesSupplementaires(session, *actif, *profil);
            break;
        case TurnAction::Cast:
            if (toujoursLui() && plan.target.has_value()) {
                static_cast<void>(session.castSpell(*plan.target, plan.spellIndex));
            }
            break;
        case TurnAction::Dash:
            if (toujoursLui() && session.dash() && plan.dashTo.has_value()) {
                static_cast<void>(session.move(*plan.dashTo));
            }
            break;
        case TurnAction::Dodge:
            if (toujoursLui()) {
                static_cast<void>(session.dodge());
            }
            break;
        case TurnAction::Disengage:
        case TurnAction::Wait:
            break;
    }

    if (toujoursLui()) {
        lancerLeSortBonus(session, *actif, *profil);
    }
    if (plan.action == TurnAction::Attack && profil->retreatAfterAttack && toujoursLui()) {
        reculerApresAttaque(session, *actif, *profil);
    }
    if (toujoursLui()) {
        static_cast<void>(session.endTurn());
    }
    return true;
}

}  // namespace core
