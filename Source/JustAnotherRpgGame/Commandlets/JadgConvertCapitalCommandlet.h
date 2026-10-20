// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
#pragma once

#include "Commandlets/Commandlet.h"
#include "JadgConvertCapitalCommandlet.generated.h"

/** Native WP conversion with restored transient foliage bases for UE 5.8. */
UCLASS()
class UJadgConvertCapitalCommandlet : public UCommandlet
{
	GENERATED_BODY()
public:
	UJadgConvertCapitalCommandlet();
	virtual int32 Main(const FString& Params) override;
};
