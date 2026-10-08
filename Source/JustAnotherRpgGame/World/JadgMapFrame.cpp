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

FString AJadgMapFrame::MapPackage(const FString& InLevelId)
{
	return TEXT("/Game/Maps/Levels/") + InLevelId;
}
