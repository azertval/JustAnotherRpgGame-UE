// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

// Core avant le moteur : ses en-têtes ne doivent voir aucune macro d'Unreal.
#include "Core/World/DayLight.h"

#include "World/JadgDayLight.h"

#include "Bridge/JadgPaths.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/LocalLightComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Engine/DirectionalLight.h"
#include "Engine/GameInstance.h"
#include "Engine/PointLight.h"
#include "Engine/SkyLight.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Game/JadgExploration.h"
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
		TEXT("Jadg.Time HH:MM règle l'heure du monde et la fige ; run la relance ; sans argument, l'écrit."),
		FConsoleCommandWithWorldAndArgsDelegate::CreateLambda([](const TArray<FString>& Args, UWorld* World)
		{
			AJadgDayLight* DayLight = FindDayLight(World);
			if (DayLight == nullptr)
			{
				UE_LOG(LogJadg, Warning, TEXT("Jadg.Time : aucun AJadgDayLight dans la carte"));
				return;
			}
			float Minutes = 0.0f;
			if (Args.Num() > 0 && Args[0] == TEXT("run"))
			{
				DayLight->SetRunning(true);
			}
			else if (Args.Num() > 0 && AJadgDayLight::ParseTime(Args[0], Minutes))
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

	float Asked = 0.0f;
	FString AskedText;
	if (FParse::Value(FCommandLine::Get(), TEXT("JadgTime="), AskedText) && ParseTime(AskedText, Asked))
	{
		SetMinutes(Asked);
	}
	else
	{
		Minutes = WorldMinutes();
		Apply();
	}
}

float AJadgDayLight::WorldMinutes() const
{
	const UGameInstance* Instance = GetGameInstance();
	const UJadgExploration* Exploration = Instance != nullptr ? Instance->GetSubsystem<UJadgExploration>() : nullptr;
	return Exploration != nullptr ? Exploration->Minutes() : Minutes;
}

void AJadgDayLight::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	// L'heure du monde passe ailleurs (`UJadgExploration`) : ici elle se lit, et ne s'applique que
	// si elle a bougé d'un centième de minute.
	const float Now = WorldMinutes();
	if (FMath::Abs(Now - Minutes) > 0.01f)
	{
		Minutes = Now;
		Apply();
	}
}

void AJadgDayLight::SetMinutes(float InMinutes)
{
	Minutes = FMath::Fmod(InMinutes, 1440.0f);
	if (Minutes < 0.0f)
	{
		Minutes += 1440.0f;
	}
	if (const UGameInstance* Instance = GetGameInstance())
	{
		if (UJadgExploration* Exploration = Instance->GetSubsystem<UJadgExploration>())
		{
			Exploration->SetMinutes(Minutes);
			// Une carte à heure fixe se montre à son heure, quelle que soit celle qu'on règle.
			Minutes = Exploration->Minutes();
		}
	}
	Apply();
}

void AJadgDayLight::SetRunning(bool bRunning)
{
	if (const UGameInstance* Instance = GetGameInstance())
	{
		if (UJadgExploration* Exploration = Instance->GetSubsystem<UJadgExploration>())
		{
			Exploration->SetClockRunning(bRunning);
		}
	}
}

ULocalLightComponent* AJadgDayLight::AddLamp(const FVector& Location, const FLinearColor& Colour, float Radius, float Scale, bool bAlways)
{
	APointLight* Lamp = GetWorld()->SpawnActorDeferred<APointLight>(APointLight::StaticClass(), FTransform(Location));
	if (Lamp == nullptr)
	{
		return nullptr;
	}
	UPointLightComponent* Component = Lamp->PointLightComponent;
	Component->SetMobility(EComponentMobility::Movable);
	Component->IntensityUnits = ELightUnits::Candelas;
	Component->Intensity = (bAlways ? FireCandelas : LampCandelas) * Scale;
	Component->LightColor = Colour.ToFColor(false);
	Component->AttenuationRadius = Radius;
	Component->CastShadows = !bAlways;
	Lamp->FinishSpawning(FTransform(Location));
	if (!bAlways && State.IsValid())
	{
		Lamp->Tags.Add(LampTag);
		State->Lamps.Add(Component, Component->Intensity);
		Apply();
	}
	return Component;
}

int32 AJadgDayLight::LampCount() const
{
	return State.IsValid() ? State->Lamps.Num() : 0;
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
