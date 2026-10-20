#include "Scene/JadgArenaPhysicsBuild.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/StaticMesh.h"
#include "StaticMeshResources.h"
#include "PhysicsEngine/PhysicsAsset.h"
#include "PhysicsEngine/SkeletalBodySetup.h"
#include "PhysicsEngine/PhysicsConstraintTemplate.h"
#include "UObject/Package.h"
#include "Misc/PackageName.h"
#if WITH_EDITOR
#include "Rendering/SkeletalMeshModel.h"
#include "Rendering/SkeletalMeshLODModel.h"
#include "ClothingAssetFactory.h"
#include "ClothingAsset.h"
#include "ChaosCloth/ChaosClothConfig.h"
#include "AssetRegistry/AssetRegistryModule.h"
#endif

UPhysicsAsset* UJadgArenaPhysicsBuild::BuildBodies(USkeletalMesh* Mesh, const FString& PackagePath, bool bAnchorRoot, const FString& JointMode,FVector JointAxis)
{
#if WITH_EDITOR
 if (!Mesh || !Mesh->GetImportedModel() || Mesh->GetImportedModel()->LODModels.IsEmpty()) return nullptr;
 UPackage* Package=CreatePackage(*PackagePath);
 UPhysicsAsset* Asset=FindObject<UPhysicsAsset>(Package,*FPackageName::GetLongPackageAssetName(PackagePath));
 if (!Asset) { Asset=NewObject<UPhysicsAsset>(Package,*FPackageName::GetLongPackageAssetName(PackagePath),RF_Public|RF_Standalone); FAssetRegistryModule::AssetCreated(Asset); }
 Asset->SkeletalBodySetups.Empty(); Asset->ConstraintSetup.Empty(); Asset->CollisionDisableTable.Empty();
 const FReferenceSkeleton& Ref=Mesh->GetRefSkeleton();
 TArray<FTransform> World; TArray<FBox> Bounds;
 for(int32 Bone=0;Bone<Ref.GetNum();++Bone) {
  const int32 Parent=Ref.GetParentIndex(Bone);
  World.Add(Parent<0?Ref.GetRefBonePose()[Bone]:Ref.GetRefBonePose()[Bone]*World[Parent]);
  Bounds.Add(FBox(ForceInit));
 }
 for(const FSkelMeshSection& Section:Mesh->GetImportedModel()->LODModels[0].Sections)
  for(const FSoftSkinVertex& Vertex:Section.SoftVertices) {
   const int32 Bone=Section.BoneMap[Vertex.InfluenceBones[0]];
   Bounds[Bone]+=World[Bone].InverseTransformPosition(FVector(Vertex.Position));
  }
 TMap<int32,int32> BodyForBone;
 for(int32 Bone=0;Bone<Ref.GetNum();++Bone) {
  if (!Bounds[Bone].IsValid && Bone!=0) continue;
  auto* Body=NewObject<USkeletalBodySetup>(Asset,NAME_None,RF_Transactional);
  Body->BoneName=Ref.GetBoneName(Bone);
  UE_LOG(LogTemp,Display,TEXT("AOF_BODY %s bone=%s valid=%d"),*Mesh->GetName(),*Body->BoneName.ToString(),Bounds[Bone].IsValid);
  Body->PhysicsType=(bAnchorRoot && Bone==0)?PhysType_Kinematic:PhysType_Simulated;
  Body->CollisionTraceFlag=CTF_UseSimpleAsComplex;
  FVector Center=Bounds[Bone].IsValid?Bounds[Bone].GetCenter():FVector::ZeroVector;
  FVector Size=Bounds[Bone].IsValid?Bounds[Bone].GetSize():FVector(3);
  Size=Size.ComponentMax(FVector(1.5));
  FKBoxElem Box;Box.Center=Center;Box.X=Size.X;Box.Y=Size.Y;Box.Z=Size.Z;
  if(JointMode==TEXT("cloth")) {
   // Small anchor only; a full sheet box would intersect the simulated fabric.
   FKSphereElem Anchor;Anchor.Center=FVector::ZeroVector;Anchor.Radius=1.0f;Body->AggGeom.SphereElems.Add(Anchor);
  } else Body->AggGeom.BoxElems.Add(Box);
  Body->DefaultInstance.LinearDamping=.15f;Body->DefaultInstance.AngularDamping=.4f;
  Body->DefaultInstance.bUseCCD=true;
  Body->DefaultInstance.PositionSolverIterationCount=16;Body->DefaultInstance.VelocitySolverIterationCount=8;
  Body->InvalidatePhysicsData(); Body->CreatePhysicsMeshes();
  BodyForBone.Add(Bone,Asset->SkeletalBodySetups.Add(Body));
 }
 for(int32 Bone=1;Bone<Ref.GetNum();++Bone) {
  int32 Parent=Ref.GetParentIndex(Bone);
  while(Parent>=0 && !BodyForBone.Contains(Parent)) Parent=Ref.GetParentIndex(Parent);
  if(Parent<0 || !BodyForBone.Contains(Bone)) continue;
  auto* Constraint=NewObject<UPhysicsConstraintTemplate>(Asset,NAME_None,RF_Transactional);
  FConstraintInstance& C=Constraint->DefaultInstance;
  C.JointName=Ref.GetBoneName(Bone); C.ConstraintBone1=Ref.GetBoneName(Bone); C.ConstraintBone2=Ref.GetBoneName(Parent);
  // Imported bone origins are authored joint pivots, in centimetres after import.
  const FTransform Joint(FRotationMatrix::MakeFromX(JointAxis.GetSafeNormal()).ToQuat(),World[Bone].GetLocation());
  C.SetRefFrame(EConstraintFrame::Frame1,Joint.GetRelativeTransform(World[Bone]));
  C.SetRefFrame(EConstraintFrame::Frame2,Joint.GetRelativeTransform(World[Parent]));
  C.SetLinearXLimit(LCM_Locked,0);C.SetLinearYLimit(LCM_Locked,0);C.SetLinearZLimit(LCM_Locked,0);
  C.SetAngularSwing1Limit(ACM_Limited,JointMode==TEXT("chain")?65.f:0.f);
  C.SetAngularSwing2Limit(JointMode==TEXT("chain")?ACM_Limited:ACM_Locked,JointMode==TEXT("chain")?65.f:0.f);
  C.SetAngularTwistLimit(ACM_Limited,JointMode==TEXT("chain")?45.f:105.f);
  if(JointMode==TEXT("slider")) { C.SetLinearXLimit(LCM_Limited,FMath::Min(150.f,Bounds[Bone].GetSize().GetMax()*.5f)); C.SetAngularTwistLimit(ACM_Locked,0); }
  C.SetDisableCollision(true);
  Asset->DisableCollision(BodyForBone[Bone],BodyForBone[Parent]);
  Asset->ConstraintSetup.Add(Constraint);
 }
 Asset->UpdateBodySetupIndexMap(); Asset->UpdateBoundsBodiesArray(); Asset->SetPreviewMesh(Mesh);
 Mesh->SetPhysicsAsset(Asset); Asset->MarkPackageDirty(); Mesh->MarkPackageDirty();
 return Asset;
#else
 return nullptr;
#endif
}

FString UJadgArenaPhysicsBuild::BuildCloth(USkeletalMesh* Mesh,float MaxDistanceCm,bool bPinTop)
{
#if WITH_EDITOR
 if(!Mesh || !Mesh->GetImportedModel()) return TEXT("ERROR: missing mesh");
 if(!Mesh->GetMeshClothingAssets().IsEmpty()) {
  auto* Existing=Cast<UClothingAssetCommon>(Mesh->GetMeshClothingAssets()[0]);
  if(!Existing)return TEXT("ERROR: unsupported cloth asset");
  FScopedSkeletalMeshPostEditChange ScopedChange(Mesh);
  auto& Model=Mesh->GetImportedModel()->LODModels[0];
  const int32 OriginalIndex=Model.Sections[0].OriginalDataSectionIndex;
  Existing->UnbindFromSkeletalMesh(Mesh,0,0);
  Existing->PostUpdateAllAssets();
  if(!Existing->BindToSkeletalMesh(Mesh,0,0,0))return TEXT("ERROR: rebind");
  auto& User=Model.UserSectionsData.FindOrAdd(OriginalIndex);
  User.CorrespondClothAssetIndex=0;User.ClothingData.AssetGuid=Existing->GetAssetGuid();User.ClothingData.AssetLodIndex=0;
  Mesh->MarkPackageDirty();return TEXT("BOUND_WITH_PERSISTENT_SECTION");
 }
 FSkeletalMeshClothBuildParams Params;Params.AssetName=Mesh->GetName()+TEXT("_Cloth");Params.LodIndex=0;Params.SourceSection=0;Params.bRemoveFromMesh=false;Params.PhysicsAsset=Mesh->GetPhysicsAsset();
 UClothingAssetFactory* Factory=NewObject<UClothingAssetFactory>();
 UClothingAssetCommon* Cloth=Cast<UClothingAssetCommon>(Factory->CreateFromSkeletalMesh(Mesh,Params));
 if(!Cloth || Cloth->LodData.IsEmpty()) return TEXT("ERROR: extraction");
 auto& Lod=Cloth->LodData[0];auto& Physical=Lod.PhysicalMeshData;
 FPointWeightMap Mask(Physical.Vertices.Num());Mask.Name=TEXT("Attachment_MaxDistance");Mask.CurrentTarget=(uint8)EWeightMapTargetCommon::MaxDistance;Mask.bEnabled=true;
 FBox Bounds(ForceInit);for(auto P:Physical.Vertices)Bounds+=FVector(P);
 int32 Pinned=0;
 for(int32 I=0;I<Physical.Vertices.Num();++I) {
  // Red vertex channel is authored as mobility: zero at stitched attachments.
  const float Free=Physical.VertexColors.IsValidIndex(I)?Physical.VertexColors[I].R/255.f:(Physical.Vertices[I].Z<Bounds.Max.Z-2?1.f:0.f);
  Mask.Values[I]=MaxDistanceCm*Free;Pinned+=(Free<.001f);
 }
 if(Pinned<2) return TEXT("ERROR: missing attachment weights");
 Lod.PointWeightMaps.Empty();Lod.PointWeightMaps.Add(Mask);Cloth->ApplyParameterMasks(true,true);
 UChaosClothConfig* Config=Cloth->GetClothConfig<UChaosClothConfig>();
 if(!Config) { Config=NewObject<UChaosClothConfig>(Cloth);Cloth->ClothConfigs.Add(Config->GetClass()->GetFName(),Config); }
 Config->Density=.35f;Config->EdgeStiffnessWeighted={.9f,.9f};Config->BendingStiffnessWeighted={.08f,.08f};Config->AreaStiffnessWeighted={.9f,.9f};
 Config->DampingCoefficient=.08f;Config->CollisionThickness=.6f;Config->FrictionCoefficient=.4f;
 Config->bUseSelfCollisions=true;Config->SelfCollisionThickness=.6f;Config->bUseCCD=true;
 Config->Drag={.08f,.08f};Config->Lift={.03f,.03f};Config->GravityScale=1;
 Cloth->InvalidateAllCachedData();Mesh->AddClothingAsset(Cloth);
 FScopedSkeletalMeshPostEditChange ScopedChange(Mesh);
 if(!Cloth->BindToSkeletalMesh(Mesh,0,0,0))return TEXT("ERROR: binding");
 auto& Model=Mesh->GetImportedModel()->LODModels[0];auto& User=Model.UserSectionsData.FindOrAdd(Model.Sections[0].OriginalDataSectionIndex);
 User.CorrespondClothAssetIndex=0;User.ClothingData.AssetGuid=Cloth->GetAssetGuid();User.ClothingData.AssetLodIndex=0;
 Mesh->PostEditChange();Mesh->MarkPackageDirty();
 return FString::Printf(TEXT("OK vertices=%d pinned=%d"),Physical.Vertices.Num(),Pinned);
#else
 return TEXT("ERROR: editor only");
#endif
}

bool UJadgArenaPhysicsBuild::BuildRigidCollision(UStaticMesh* Mesh)
{
#if WITH_EDITOR
 if(!Mesh || !Mesh->GetRenderData() || Mesh->GetRenderData()->LODResources.IsEmpty())return false;
 Mesh->CreateBodySetup();auto* Body=Mesh->GetBodySetup();Body->RemoveSimpleCollision();
 FKConvexElem Hull;const auto& Positions=Mesh->GetRenderData()->LODResources[0].VertexBuffers.PositionVertexBuffer;
 for(uint32 I=0;I<Positions.GetNumVertices();++I)Hull.VertexData.Add(FVector(Positions.VertexPosition(I)));
 if(Hull.VertexData.Num()<4)return false;
 Hull.UpdateElemBox();Body->AggGeom.ConvexElems.Add(Hull);Body->CollisionTraceFlag=CTF_UseSimpleAndComplex;
 Body->DefaultInstance.bUseCCD=true;Body->InvalidatePhysicsData();Body->CreatePhysicsMeshes();Mesh->MarkPackageDirty();return true;
#else
 return false;
#endif
}
