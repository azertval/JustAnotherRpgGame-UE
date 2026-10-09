// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "World/JadgPrefab.h"

#include "Components/SceneComponent.h"

AJadgPrefab::AJadgPrefab()
{
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Origin"));
	RootComponent->SetMobility(EComponentMobility::Static);
}
