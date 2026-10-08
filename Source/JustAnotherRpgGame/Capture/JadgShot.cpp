// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "Capture/JadgShot.h"

AJadgShot::AJadgShot()
{
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Target"));
}
