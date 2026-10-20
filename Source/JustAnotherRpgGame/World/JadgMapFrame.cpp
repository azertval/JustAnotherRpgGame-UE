// SPDX-FileCopyrightText: 2026 Valentin Eloy
// SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0

#include "World/JadgMapFrame.h"

#include "Components/SceneComponent.h"
#include "Engine/LevelStreaming.h"
#include "Engine/World.h"

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
	// L'étage est le plus haut dont le sol est sous les pieds, dans l'ordre des hauteurs et non des
	// rangs : un sous-sol suit le rez dans la description (LOT-1022). Sous le plus bas, le plus bas.
	constexpr double Tolerance = 50.0;
	const double Height = WorldZ - GetActorLocation().Z;
	int32 Storey = INDEX_NONE;
	int32 Lowest = 0;
	for (int32 Index = 0; Index < StoreyHeights.Num(); ++Index)
	{
		if (Height >= StoreyHeights[Index] - Tolerance && (Storey == INDEX_NONE || StoreyHeights[Index] > StoreyHeights[Storey]))
		{
			Storey = Index;
		}
		if (StoreyHeights[Index] < StoreyHeights[Lowest])
		{
			Lowest = Index;
		}
	}
	return Storey != INDEX_NONE ? Storey : (StoreyHeights.IsEmpty() ? 0 : Lowest);
}

bool AJadgMapFrame::TerrainZAt(const FVector& World, double& Height) const
{
	if (TerrainWidth < 2 || TerrainHeight < 2 || TerrainSpacing.X <= 0.0 || TerrainSpacing.Y <= 0.0
		|| static_cast<int64>(TerrainWidth) * TerrainHeight != TerrainHeights.Num())
	{
		return false;
	}
	const FVector Offset = World - TerrainOrigin;
	const double X = FVector::DotProduct(Offset, East) / TerrainSpacing.X;
	const double Y = FVector::DotProduct(Offset, South) / TerrainSpacing.Y;
	if (!FMath::IsFinite(X) || !FMath::IsFinite(Y) || X < 0.0 || Y < 0.0 || X > TerrainWidth - 1 || Y > TerrainHeight - 1)
	{
		return false;
	}
	const int32 Column = FMath::Min(FMath::FloorToInt32(X), TerrainWidth - 2);
	const int32 Row = FMath::Min(FMath::FloorToInt32(Y), TerrainHeight - 2);
	const double U = X - Column;
	const double V = Y - Row;
	const int32 Index = Row * TerrainWidth + Column;
	const double A = TerrainHeights[Index];
	const double B = TerrainHeights[Index + 1];
	const double C = TerrainHeights[Index + TerrainWidth];
	const double D = TerrainHeights[Index + TerrainWidth + 1];
	const double Sample = FMath::Lerp(FMath::Lerp(A, B, U), FMath::Lerp(C, D, U), V);
	if (!FMath::IsFinite(Sample))
	{
		return false;
	}
	Height = Sample;
	return true;
}

double AJadgMapFrame::GroundZAt(const FVector& World, int32 Storey) const
{
	for (const FJadgStoreyRegion& Region : StoreyRegions)
	{
		if (Region.Storey == Storey && World.X >= Region.Minimum.X && World.X <= Region.Maximum.X
			&& World.Y >= Region.Minimum.Y && World.Y <= Region.Maximum.Y)
		{
			return Region.Minimum.Z;
		}
	}
	double Height = StoreyZ(Storey);
	if (Storey == 0)
	{
		TerrainZAt(World, Height);
	}
	return Height;
}

int32 AJadgMapFrame::StoreyAt(const FVector& World) const
{
	if (StoreyRegions.IsEmpty() && TerrainHeights.IsEmpty())
	{
		return StoreyAt(World.Z);
	}
	constexpr double Tolerance = 50.0;
	int32 Storey = 0;
	double Floor = -TNumericLimits<double>::Max();
	for (const FJadgStoreyRegion& Region : StoreyRegions)
	{
		if (World.X >= Region.Minimum.X && World.X <= Region.Maximum.X
			&& World.Y >= Region.Minimum.Y && World.Y <= Region.Maximum.Y
			&& World.Z >= Region.Minimum.Z - Tolerance && World.Z <= Region.Maximum.Z + Tolerance
			&& Region.Minimum.Z > Floor)
		{
			Storey = Region.Storey;
			Floor = Region.Minimum.Z;
		}
	}
	return Storey;
}

bool AJadgMapFrame::ShowStorey(int32 Storey, bool bVisible) const
{
	UWorld* World = GetWorld();
	if (World == nullptr || !StoreyLevels.IsValidIndex(Storey))
	{
		return false;
	}
	for (ULevelStreaming* Streaming : World->GetStreamingLevels())
	{
		if (Streaming != nullptr && Streaming->GetWorldAssetPackageName() == StoreyLevels[Storey])
		{
			Streaming->SetShouldBeLoaded(true);
			Streaming->SetShouldBeVisible(bVisible);
			World->FlushLevelStreaming(EFlushLevelStreamingType::Visibility);
			return true;
		}
	}
	return false;
}

double AJadgMapFrame::StoreyZ(int32 Storey) const
{
	return GetActorLocation().Z + (StoreyHeights.IsValidIndex(Storey) ? StoreyHeights[Storey] : 0.0);
}

FString AJadgMapFrame::MapPackage(const FString& InLevelId)
{
	// The terrain source ID remains stable; its editor world has a canonical location.
	if (InLevelId == TEXT("capital-landscape/paysage-capitale") || InLevelId == TEXT("Capitale"))
	{
		return TEXT("/Game/Capitale/Cartes/Capitale");
	}
	return TEXT("/Game/Maps/Levels/") + InLevelId;
}
