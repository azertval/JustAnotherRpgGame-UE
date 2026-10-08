// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

#include "JadgDayLight.generated.h"

class ADirectionalLight;
class ASkyLight;

/**
 * @brief Le cycle jour / nuit : l'heure du monde, lue dans `daylight.json` par Core, appliquée aux
 *        lumières du moteur (LOT-1012).
 *
 * La table est celle du LOT-1007, **telle quelle** : Core l'interpole (`core::DayLightTable`), cet
 * acteur n'en fait que la traduction.
 *
 * | Champ de la table | Ce qu'il règle ici |
 * |---|---|
 * | `sun`, `azimuth`, `elevation` | la couleur, l'intensité et la direction de la lumière dirigée (`Sun`) |
 * | `ambient` | la couleur de la lumière du ciel (`Sky`), dont la source est un cube blanc uniforme |
 * | `lamps` | l'intensité des lumières de nuit : toute lumière d'un acteur étiqueté `JadgLamp` |
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
 * Console : `Jadg.Time 22:00` règle l'heure ; `Jadg.Time` l'écrit.
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

	/// L'heure au lancement, en minutes depuis minuit.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	float StartMinutes = 720.0f;

	/// Minutes du monde par seconde réelle ; 0 : l'heure ne passe pas.
	UPROPERTY(EditAnywhere, Category = "Jadg")
	float MinutesPerSecond = 0.0f;

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

	/// Règle l'heure, en minutes depuis minuit (ramenée dans [0, 1440[), et l'applique.
	void SetMinutes(float Minutes);

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

	float Minutes = 720.0f;

	void Apply();
};
