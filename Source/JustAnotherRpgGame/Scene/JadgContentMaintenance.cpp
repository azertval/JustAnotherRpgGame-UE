#include "Scene/JadgContentMaintenance.h"
#if WITH_EDITOR
#include "WorldPartition/HLOD/HLODActor.h"
#include "WorldPartition/HLOD/HLODSourceActorsFromCell.h"
#endif
TArray<FString> UJadgContentMaintenance::HLODSourcePackages(AActor* Actor)
{
 TArray<FString> Result;
#if WITH_EDITOR
 if(auto* HLOD=Cast<AWorldPartitionHLOD>(Actor))
  if(auto* Sources=Cast<UWorldPartitionHLODSourceActorsFromCell>(HLOD->GetSourceActors()))
   for(const auto& Entry:Sources->GetActors())Result.Add(Entry.Package.ToString());
#endif
 return Result;
}
