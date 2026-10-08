// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/World/DayLight.h"

#include "World/JadgDayLight.h"

#include "Bridge/JadgPaths.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/LocalLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/SkyLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "JustAnotherRpgGame.h"

namespace
{
	const FName LampTag(TEXT("JadgLamp"));

	FLinearColor ToLinear(const core::LightColor& Color)
	{
		// Les couleurs de la table sont des facteurs de lumière : elles s'appliquent telles quelles.
		return FLinearColor(Color.r, Color.g, Color.b);
	}

	AJadgDayLight* FindDayLight(UWorld* World)
	{
		for (TActorIterator<AJadgDayLight> It(World); It; ++It)
		{
			return *It;
		}
		return nullptr;
	}

	FAutoConsoleCommandWithWorldAndArgs GTimeCommand(
		TEXT("Jadg.Time"),
		TEXT("Jadg.Time HH:MM règle l'heure du monde ; sans argument, l'écrit."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			AJadgDayLight* DayLight = FindDayLight(World);
			if (DayLight == nullptr)
			{
				UE_LOG(LogJadg, Warning, TEXT("Jadg.Time : aucun AJadgDayLight dans la carte"));
				return;
			}
			float Minutes = 0.0f;
			if (Args.Num() > 0 && AJadgDayLight::ParseTime(Args[0], Minutes))
			{
				DayLight->SetMinutes(Minutes);
			}
			const int32 Now = FMath::FloorToInt32(DayLight->GetMinutes());
			UE_LOG(LogJadg, Display, TEXT("Heure du monde : %02d:%02d"), Now / 60, Now % 60);
		}));
}

struct AJadgDayLight::FState
{
	core::DayLightTable Table;
	/// L'intensité que chaque lampe porte dans la carte : `lamps` la multiplie.
	TMap<TWeakObjectPtr<ULocalLightComponent>, float> Lamps;
};

AJadgDayLight::AJadgDayLight()
{
	PrimaryActorTick.bCanEverTick = true;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
}

bool AJadgDayLight::ParseTime(const FString& Text, float& OutMinutes)
{
	FString Hours;
	FString Mins;
	if (!Text.Split(TEXT(":"), &Hours, &Mins) || !Hours.IsNumeric() || !Mins.IsNumeric())
	{
		return false;
	}
	OutMinutes = FCString::Atof(*Hours) * 60.0f + FCString::Atof(*Mins);
	return true;
}

void AJadgDayLight::BeginPlay()
{
	Super::BeginPlay();

	State = MakeShared<FState>();
	const FString File = FPaths::Combine(FJadgPaths::ElementsDir(), TEXT("Assets"), TableFile);
	core::DayLightTableResult Read = core::readDayLightTableFile(FJadgPaths::ToPath(File));
	if (Read.ok())
	{
		State->Table = MoveTemp(Read.table);
	}
	else
	{
		UE_LOG(LogJadg, Error, TEXT("%s : %s ; la table d'usine la remplace"), *File, *FJadgPaths::ToFString(Read.message));
		State->Table = core::DayLightTable::factory();
	}

	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		if (!It->ActorHasTag(LampTag))
		{
			continue;
		}
		TInlineComponentArray<ULocalLightComponent*> Lights(*It);
		for (ULocalLightComponent* Light : Lights)
		{
			State->Lamps.Add(Light, Light->Intensity);
		}
	}

	float Minutes0 = StartMinutes;
	FString Asked;
	if (FParse::Value(FCommandLine::Get(), TEXT("JadgTime="), Asked))
	{
		ParseTime(Asked, Minutes0);
	}
	SetMinutes(Minutes0);
}

void AJadgDayLight::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (MinutesPerSecond != 0.0f)
	{
		SetMinutes(Minutes + MinutesPerSecond * DeltaSeconds);
	}
}

void AJadgDayLight::SetMinutes(float InMinutes)
{
	Minutes = FMath::Fmod(InMinutes, 1440.0f);
	if (Minutes < 0.0f)
	{
		Minutes += 1440.0f;
	}
	Apply();
}

void AJadgDayLight::Apply()
{
	if (!State.IsValid())
	{
		return;
	}
	const core::DayLight Light = State->Table.sample(Minutes);

	if (Sun != nullptr)
	{
		UDirectionalLightComponent* Component = Sun->GetComponent();
		const FLinearColor Colour = ToLinear(Light.sun);
		const float Peak = FMath::Max3(Colour.R, Colour.G, Colour.B);
		// π lux sur une surface blanche rend un blanc à l'exposition 1.
		Component->SetIntensity(UE_PI * Peak * SunScale);
		Component->SetLightColor(Peak > 0.0f ? Colour / Peak : FLinearColor::White, false);
		const FVector ToSun = East * Light.toSun[0] + Up * Light.toSun[1] + South * Light.toSun[2];
		Sun->SetActorRotation((-ToSun).Rotation());
	}

	if (Sky != nullptr)
	{
		USkyLightComponent* Component = Sky->GetLightComponent();
		const FLinearColor Colour = ToLinear(Light.ambient);
		const float Peak = FMath::Max3(Colour.R, Colour.G, Colour.B);
		Component->SetIntensity(Peak * AmbientScale);
		Component->SetLightColor(Peak > 0.0f ? Colour / Peak : FLinearColor::White);
	}

	for (const TPair<TWeakObjectPtr<ULocalLightComponent>, float>& Lamp : State->Lamps)
	{
		if (ULocalLightComponent* Component = Lamp.Key.Get())
		{
			Component->SetIntensity(Lamp.Value * Light.lamps);
		}
	}
}
