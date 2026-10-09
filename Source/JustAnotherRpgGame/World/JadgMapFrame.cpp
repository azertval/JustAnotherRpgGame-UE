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
	return TEXT("/Game/Maps/Levels/") + InLevelId;
}
