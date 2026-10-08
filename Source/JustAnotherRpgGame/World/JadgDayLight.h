// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgDayLight.generated.h"

class ADirectionalLight;
class ASkyLight;
class ULocalLightComponent;
class ULocalLightComponent;

/**
 * @brief Le cycle jour / nuit : l'heure du monde, lue dans `daylight.json` par Core, appliquée aux
 *        lumières du moteur (LOT-1012).
 *
 * La table est celle du LOT-1007, **telle quelle** : Core l'interpole (`core::DayLightTable`), cet
 * acteur n'en fait que la traduction.
 *
 * L'heure est celle du monde (`core::WorldClock`, une heure par minute réelle, D-45), tenue par
 * `UJadgExploration` et lue ici à chaque trame (LOT-1016) : elle passe avec l'exploration, se fige
 * pendant un dialogue, et une carte qui déclare une heure fixe se montre à cette heure.
 *
 * L'heure est celle du monde (`core::WorldClock`, une heure par minute réelle, D-45), tenue par
 * `UJadgExploration` et lue ici à chaque trame (LOT-1016) : elle passe avec l'exploration, se fige
 * pendant un dialogue, et une carte qui déclare une heure fixe se montre à cette heure.
 *
 * | Champ de la table | Ce qu'il règle ici |
 * |---|---|
 * | `sun`, `azimuth`, `elevation` | la couleur, l'intensité et la direction de la lumière dirigée (`Sun`) |
 * | `ambient` | la couleur de la lumière du ciel (`Sky`), dont la source est un cube blanc uniforme |
 * | `lamps` | l'intensité des lumières de nuit : toute lumière d'un acteur étiqueté `JadgLamp`, et celles que la carte de Core pose comme entité `light` (`AddLamp`) |
 *
 * `tint` et `shadow` réglaient les images du décor peint : plus rien ne s'y dresse (D-49).
 *
 * L'exposition de la scène est fixe et vaut 1 : une surface blanche sous une lumière dirigée de
 * π lux rend un blanc. `sun` et `ambient` sont donc des intensités, sans autre échelle.
 *
 * La direction du soleil est écrite par Core dans le repère d'un maillage posé (X, Y vers le haut,
 * Z) ; `East`, `Up` et `South` disent ce que ces trois axes deviennent dans le moteur. Ils sont
 * mesurés à l'import par le script qui construit la scène, pas supposés.
 *
 * Console : `Jadg.Time 22:00` règle l'heure et la fige ; `Jadg.Time run` la relance ; `Jadg.Time`
 * l'écrit. Ligne de commande : `-JadgTime=22:00`.
 */
UCLASS()
class AJadgDayLight : public AActor
{
	GENERATED_BODY()

public:
	AJadgDayLight();

	/// La table, relative au dossier des assets (`Source/Elements/Assets`).
	UPROPERTY(EditAnywhere, Category = "Jadg")
	FString TableFile = TEXT("Common/Lighting/daylight.json");

	/// L'intensité d'une lumière de nuit et d'un feu toujours allumé, en candelas, pour une
	/// exposition fixe de 1. Réglées par la description de scène (`lampCandelas`, `fireCandelas`).
	UPROPERTY(EditAnywhere, Category = "Jadg")
	float LampCandelas = 60.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg")
	float FireCandelas = 30.0f;

	/// Ce par quoi `sun` et `ambient` de la table sont multipliés. La table est écrite pour un
	/// rendu sans lumière indirecte : sous Lumen, moins de lumière du ciel et plus de soleil
	/// rendent le contraste que la lumière rebondie comble. Réglés par la description de scène.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	float SunScale = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg")
	float AmbientScale = 1.0f;

	UPROPERTY(EditAnywhere, Category = "Jadg")
	TObjectPtr<ADirectionalLight> Sun;

	UPROPERTY(EditAnywhere, Category = "Jadg")
	TObjectPtr<ASkyLight> Sky;

	/// Ce que deviennent, dans le moteur, les axes X, Y et Z d'un maillage posé.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	FVector East = FVector(1.0, 0.0, 0.0);

	UPROPERTY(EditAnywhere, Category = "Jadg")
	FVector Up = FVector(0.0, 0.0, 1.0);

	UPROPERTY(EditAnywhere, Category = "Jadg")
	FVector South = FVector(0.0, 1.0, 0.0);

	/// Règle l'heure du monde, en minutes depuis minuit (ramenée dans [0, 1440[), la fige et
	/// l'applique.
	void SetMinutes(float Minutes);

	/// Relance ou fige l'heure du monde.
	void SetRunning(bool bRunning);

	/**
	 * @brief Pose une source de lumière de la carte de Core (entité `light`).
	 *
	 * Une lumière de nuit porte une ombre et suit `lamps` ; une source toujours allumée (`bAlways`,
	 * un feu) éclaire sans ombre portée, à toute heure — comme celles que le script de scène pose.
	 * @param Radius La portée, en centimètres. @param Scale Ce par quoi son intensité est multipliée.
	 */
	ULocalLightComponent* AddLamp(const FVector& Location, const FLinearColor& Colour, float Radius, float Scale, bool bAlways);

	/// Le nombre de lumières de nuit que `lamps` règle.
	int32 LampCount() const;

	float GetMinutes() const { return Minutes; }

	/// Lit « HH:MM » ; faux si le texte n'est pas une heure.
	static bool ParseTime(const FString& Text, float& OutMinutes);

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

private:
	struct FState;
	/// La table de Core et l'intensité d'origine des lampes : hors de l'en-tête, qui ne doit pas
	/// montrer Core après le moteur.
	TSharedPtr<FState> State;

	/// L'heure appliquée, en minutes depuis minuit.
	float Minutes = 720.0f;

	/// L'heure du monde à montrer ; sans instance du jeu, celle qui est appliquée.
	float WorldMinutes() const;

	void Apply();
};
