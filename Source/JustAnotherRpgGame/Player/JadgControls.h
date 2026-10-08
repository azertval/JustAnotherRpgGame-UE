// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "InputCoreTypes.h"
#include "UObject/Object.h"

#include "JadgControls.generated.h"

/// Une touche d'une commande : la commande par son nom, la touche, et pour un axe son échelle.
USTRUCT()
struct FJadgBinding
{
	GENERATED_BODY()

	UPROPERTY()
	FName Command;

	UPROPERTY()
	FKey Key;

	UPROPERTY()
	float Scale = 1.0f;
};

/**
 * @brief Les commandes du jeu et leurs touches, lues dans `Config/DefaultGame.ini` (LOT-1016).
 *
 * Une commande est **nommée**, dissociée de sa touche (`EX-CTRL-010`) : le contrôleur du joueur
 * en fait une action d'Enhanced Input au lancement, sans asset ni Blueprint, et une touche se
 * change dans le fichier texte. Au clavier et à la souris (la manette est retirée depuis le
 * 2 octobre 2026).
 *
 * | Commande | Nature | Effet | Touches livrées |
 * |---|---|---|---|
 * | `Walk` | geste | le meneur marche vers le point cliqué ; sur un PNJ, il va lui parler | clic gauche |
 * | `Interact` | geste | le meneur sollicite ce qu'il a à portée ; en dialogue, « continuer » ; dans l'arène vide, revenir | F |
 * | `NextLeader` | geste | passe la main au suivant du groupe (`EX-EXP-014`) | Tab |
 * | `Recenter` | geste | ramène la caméra sur le meneur | Début |
 * | `Choice1` … `Choice6` | geste | donne la réponse de ce rang, en dialogue | 1 … 6 |
 * | `Turn`, `Tilt` | axe, degrés par seconde | tourne, incline la caméra | A / E, R / V |
 * | `Look` | tenue | tant qu'elle est tenue, la souris tourne et incline la caméra | C, clic droit |
 * | `LookTurn`, `LookTilt` | axe, degrés par unité de souris | la souris, sous `Look` | souris |
 * | `Zoom` | axe, crans | rapproche (positif) ou éloigne la caméra | molette |
 * | `PanForward`, `PanRight` | axe, centimètres par seconde | déplace le point visé, ce qui détache la caméra du meneur | Z / S, D / Q, flèches |
 */
UCLASS(config = Game, defaultconfig)
class UJadgControls : public UObject
{
	GENERATED_BODY()

public:
	UPROPERTY(config)
	TArray<FJadgBinding> Bindings;

	/// Ce par quoi un cran de molette multiplie la distance de la caméra : moins de 1 rapproche.
	UPROPERTY(config)
	float ZoomStep = 0.88f;

	/// Vrai si la commande se lit comme une valeur tenue (un axe), faux si c'est un geste.
	static bool IsAxis(FName Command);

	/// Vrai si @p Command est une commande du jeu (la table ci-dessus).
	static bool IsKnown(FName Command);

	/// Le nom de la première touche de @p Command, pour une invite ; vide si elle n'en a pas.
	static FString KeyLabel(FName Command);

	/// La première touche de @p Command ; invalide si elle n'en a pas.
	static FKey KeyOf(FName Command);
};
