// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

/**
 * @file test_animation_clip.cpp
 * @brief Tests unitaires du modèle de clip d'animation (`core::AnimationClip`/`core::ClipSet`) :
 *        données pures, sans GPU ni fichier.
 */

#include <gtest/gtest.h>

#include "Core/Ecs/AnimationClip.h"

namespace {
core::AnimationClip makeClip(std::string name, std::vector<int> frames, float duration,
                             core::ClipEndMode endMode = core::ClipEndMode::Loop,
                             std::string next = {}) {
    core::AnimationClip clip;
    clip.name = std::move(name);
    clip.frames = std::move(frames);
    clip.frameDuration = duration;
    clip.endMode = endMode;
    clip.nextClip = std::move(next);
    return clip;
}
}  // namespace

/**
 * @brief Un clip ajouté au jeu se retrouve par son nom : `indexOf` rend un index valide et
 * `clipAt` rend bien ce clip. Le nom est la seule clé que manipulent les données d'animation, un
 * jeu qui ne saurait pas le résoudre ne servirait à rien.
 * \castest{<b>Un clip existant est résolu par son nom.</b><br/>
 * \tcat Unitaire · Clip d'animation<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * }
 */
TEST(AnimationClipTest, ClipExistantResoluParNom) {
    core::ClipSet clips;
    clips.addClip(makeClip("idle", {0, 1}, 0.5f));
    clips.addClip(makeClip("run", {2, 3, 4, 5}, 0.1f));

    EXPECT_EQ(clips.clipCount(), 2);
    ASSERT_GE(clips.indexOf("idle"), 0);
    ASSERT_GE(clips.indexOf("run"), 0);
    EXPECT_EQ(clips.clipAt(clips.indexOf("idle")).name, "idle");
    EXPECT_EQ(clips.clipAt(clips.indexOf("run")).name, "run");
}

/**
 * @brief Un nom inconnu rend `-1`, et un index hors bornes retombe **déterministement** sur le
 * premier clip au lieu de planter (`EX-NFR-040`) : les noms de clips viennent de fichiers de
 * données éditables, une faute de frappe doit dégrader l'animation, jamais l'exécution.
 * \castest{<b>Un nom inconnu ou un index hors bornes retombe sur le premier clip, sans
 * plantage.</b><br/>
 * \tcat Unitaire · Clip d'animation<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * }
 */
TEST(AnimationClipTest, ClipInexistantRepliDeterministe) {
    core::ClipSet clips;
    clips.addClip(makeClip("idle", {0, 1}, 0.5f));

    EXPECT_EQ(clips.indexOf("inconnu"), -1);
    // Un index hors bornes (celui renvoye par un nom absent, ou n'importe quel entier invalide)
    // ne plante pas et retombe sur le premier clip (EX-NFR-040).
    EXPECT_EQ(clips.clipAt(-1).name, "idle");
    EXPECT_EQ(clips.clipAt(42).name, "idle");
}

/**
 * @brief Un jeu de clips **vide** rend un clip par défaut non dégénéré : il porte au moins une
 * image, donc l'animation reste affichable. `clipAt` ne doit jamais renvoyer une référence
 * invalide, même quand aucun clip n'a été chargé.
 * \castest{<b>Un jeu de clips vide se replie sur un clip par défaut portant au moins une
 * image.</b><br/>
 * \tcat Unitaire · Clip d'animation<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * }
 */
TEST(AnimationClipTest, JeuVideRepliSurUnClipParDefaut) {
    const core::ClipSet clips;
    EXPECT_EQ(clips.clipCount(), 0);
    const core::AnimationClip& fallback = clips.clipAt(0);
    EXPECT_TRUE(fallback.name.empty());
    ASSERT_FALSE(fallback.frames.empty());
    EXPECT_EQ(fallback.frameDuration, 0.0f);
}

/**
 * @brief Un clip à **une seule image** est un clip valide : c'est la forme que prend tout état
 * statique (coffre ouvert, figurine au repos), qui n'a pas à être traité à part.
 * \castest{<b>Un clip d'une seule image est un clip valide.</b><br/>
 * \tcat Unitaire · Clip d'animation<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * }
 */
TEST(AnimationClipTest, ClipAUneSeuleImage) {
    core::ClipSet clips;
    clips.addClip(makeClip("jump", {6}, 0.1f));
    const core::AnimationClip& clip = clips.clipAt(clips.indexOf("jump"));
    EXPECT_EQ(clip.frames.size(), 1u);
}

/**
 * @brief La durée d'image est propre à **chaque** clip : un repos lent et une course rapide
 * coexistent dans le même jeu sans qu'une cadence globale ne les uniformise.
 * \castest{<b>Chaque clip garde sa propre durée d'image.</b><br/>
 * \tcat Unitaire · Clip d'animation<br/>
 * \tcrit Majeur<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * }
 */
TEST(AnimationClipTest, DureesInegalesEntreClips) {
    core::ClipSet clips;
    clips.addClip(makeClip("idle", {0, 1}, 0.5f));
    clips.addClip(makeClip("run", {2, 3, 4, 5}, 0.1f));

    EXPECT_FLOAT_EQ(clips.clipAt(clips.indexOf("idle")).frameDuration, 0.5f);
    EXPECT_FLOAT_EQ(clips.clipAt(clips.indexOf("run")).frameDuration, 0.1f);
}

/**
 * @brief Un clip joué **une seule fois** peut désigner le clip qui prend le relais, et ce nom se
 * résout bien dans le même jeu : c'est le mécanisme d'une transition (ouverture d'une porte) qui
 * s'arrête sur un état stable au lieu de boucler.
 * \castest{<b>Un clip joué une fois désigne un clip suivant, résolu dans le même jeu.</b><br/>
 * \tcat Unitaire · Clip d'animation<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * }
 */
TEST(AnimationClipTest, ClipJoueUneFoisAvecClipSuivant) {
    core::ClipSet clips;
    clips.addClip(makeClip("opening", {1, 2, 3, 4}, 0.06f, core::ClipEndMode::OneShot, "open"));
    clips.addClip(makeClip("open", {5}, 0.0f));

    const core::AnimationClip& opening = clips.clipAt(clips.indexOf("opening"));
    EXPECT_EQ(opening.endMode, core::ClipEndMode::OneShot);
    EXPECT_EQ(opening.nextClip, "open");
    EXPECT_GE(clips.indexOf(opening.nextClip), 0);
}

/**
 * @brief Ajouter un clip portant un nom déjà pris **remplace** l'existant à son index, sans en
 * créer un second : les index déjà distribués restent valides, et un catalogue rechargé à chaud
 * ne se met pas à enfler de doublons à chaque relecture.
 * \castest{<b>Ajouter un clip de même nom remplace l'existant, à index constant.</b><br/>
 * \tcat Unitaire · Clip d'animation<br/>
 * \tcrit Critique<br/>
 * \tetapes 1. Mettre en place le contexte du test (arrangement).<br/>2. Executer le scenario et
 * verifier les assertions.<br/>
 * }
 */
TEST(AnimationClipTest, AjouterUnClipDeMemeNomLeRemplace) {
    core::ClipSet clips;
    clips.addClip(makeClip("idle", {0}, 1.0f));
    const int firstIndex = clips.indexOf("idle");
    clips.addClip(makeClip("idle", {0, 1, 2}, 0.25f));

    EXPECT_EQ(clips.clipCount(), 1);
    EXPECT_EQ(clips.indexOf("idle"), firstIndex);
    EXPECT_EQ(clips.clipAt(firstIndex).frames.size(), 3u);
}
