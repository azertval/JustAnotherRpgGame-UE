#include "Scene/JadgArenaPhysicsWitness.h"
#include "Animation/SkeletalMeshActor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#if WITH_EDITOR
#include "ClothingSystemRuntimeTypes.h"
#endif
#include "EngineUtils.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonSerializer.h"
#include "Dom/JsonObject.h"

void AJadgArenaSimulatedAsset::BeginPlay()
{
 Super::BeginPlay();auto* Comp=GetSkeletalMeshComponent();
 Comp->SetComponentTickEnabled(true);Comp->VisibilityBasedAnimTickOption=EVisibilityBasedAnimTickOption::AlwaysTickPoseAndRefreshBones;
 Comp->bWaitForParallelClothTask=true;
 if(SimulateArticulation) {Comp->SetSimulatePhysics(true);Comp->SetAllBodiesPhysicsBlendWeight(1.f);Comp->bBlendPhysics=true;Comp->WakeAllRigidBodies();}
 Comp->RecreateClothingActors();
}

AJadgArenaPhysicsWitness::AJadgArenaPhysicsWitness()
{
 PrimaryActorTick.bCanEverTick=true;PrimaryActorTick.TickInterval=.5f;PrimaryActorTick.TickGroup=TG_PostPhysics;
}
void AJadgArenaPhysicsWitness::Tick(float DeltaSeconds)
{
 Super::Tick(DeltaSeconds);
#if WITH_EDITOR
 Elapsed+=DeltaSeconds;
 TArray<TSharedPtr<FJsonValue>> Rows;
 for(TActorIterator<ASkeletalMeshActor> It(GetWorld());It;++It) {
  if(!It->ActorHasTag(TEXT("AOF_PhysicsWitness")))continue;
  auto* Comp=It->GetSkeletalMeshComponent();FString Key=It->Tags[0].ToString();TArray<FVector> Samples;int32 ClothParticles=0;bool Finite=true;
  if(Elapsed<1)UE_LOG(LogTemp,Display,TEXT("AOF_SIM %s activeCloth=%d canCloth=%d tick=%d assets=%d"),*Key,Comp->GetSkeletalMeshAsset()->HasActiveClothingAssets(),Comp->CanSimulateClothing(),Comp->IsComponentTickEnabled(),Comp->GetSkeletalMeshAsset()->GetMeshClothingAssets().Num());
  if(Elapsed>=5 && Elapsed-DeltaSeconds<5 && Comp->IsAnySimulatingPhysics()) {
   Comp->WakeAllRigidBodies();Comp->AddImpulse(FVector(0,100,30),Comp->GetBoneName(Comp->GetNumBones()-1),true);
   Comp->AddAngularImpulseInRadians(FVector(1,1,1),Comp->GetBoneName(Comp->GetNumBones()-1),true);
  }
  for(int32 Bone=0;Bone<Comp->GetNumBones();++Bone)Samples.Add(Comp->GetBoneLocation(Comp->GetBoneName(Bone)));
  for(const auto& Entry:Comp->GetCurrentClothingData_GameThread()) {
   ClothParticles+=Entry.Value.Positions.Num();
   for(const FVector3f P:Entry.Value.Positions) { Finite&=!P.ContainsNaN(); Samples.Add(FVector(P)); }
  }
  auto* First=Initial.Find(Key);
  if(!First || First->Num()!=Samples.Num())Initial.Add(Key,Samples);
  else for(int32 I=0;I<Samples.Num();++I)MaximumMovement.FindOrAdd(Key)=FMath::Max(MaximumMovement.FindOrAdd(Key),FVector::Distance(Samples[I],(*First)[I]));
  auto Row=MakeShared<FJsonObject>();Row->SetStringField(TEXT("asset"),Key);Row->SetNumberField(TEXT("bones"),Comp->GetNumBones());Row->SetNumberField(TEXT("clothParticles"),ClothParticles);Row->SetBoolField(TEXT("finite"),Finite);Row->SetNumberField(TEXT("maxMovementCm"),MaximumMovement.FindRef(Key));Row->SetBoolField(TEXT("simulatingRigidBodies"),Comp->IsAnySimulatingPhysics());Rows.Add(MakeShared<FJsonValueObject>(Row));
 }
 auto Doc=MakeShared<FJsonObject>();Doc->SetNumberField(TEXT("seconds"),Elapsed);Doc->SetArrayField(TEXT("samples"),Rows);FString Text;auto Writer=TJsonWriterFactory<>::Create(&Text);FJsonSerializer::Serialize(Doc,Writer);
 FFileHelper::SaveStringToFile(Text,*(FPaths::ProjectSavedDir()/TEXT("Jadg/aof-extension/physics-runtime.json")));
#endif
}
