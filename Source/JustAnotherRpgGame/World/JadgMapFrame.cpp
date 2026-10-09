// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "World/JadgMapFrame.h"

#include "Components/SceneComponent.h"

AJadgMapFrame::AJadgMapFrame()
{
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Origin"));
}

FVector AJadgMapFrame::ToWorld(const FVector2D& Cell) const
{
	return GetActorLocation() + (East * Cell.X + South * Cell.Y) * CellSize;
}

FVector2D AJadgMapFrame::ToCell(const FVector& World) const
{
	const FVector Offset = World - GetActorLocation();
	return FVector2D(FVector::DotProduct(Offset, East), FVector::DotProduct(Offset, South)) / CellSize;
}

int32 AJadgMapFrame::StoreyAt(double WorldZ) const
{
	// Un demi-mètre sous le sol d'un étage, on y est déjà : le haut d'une rampe ou d'un escalier.
	constexpr double Tolerance = 50.0;
	int32 Storey = 0;
	for (int32 Index = 1; Index < StoreyHeights.Num(); ++Index)
	{
		if (WorldZ - GetActorLocation().Z >= StoreyHeights[Index] - Tolerance)
		{
			Storey = Index;
		}
	}
	return Storey;
}

double AJadgMapFrame::StoreyZ(int32 Storey) const
{
	return GetActorLocation().Z + (StoreyHeights.IsValidIndex(Storey) ? StoreyHeights[Storey] : 0.0);
}

FString AJadgMapFrame::MapPackage(const FString& InLevelId)
{
	return TEXT("/Game/Maps/Levels/") + InLevelId;
}
