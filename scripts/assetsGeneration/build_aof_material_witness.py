import bpy
from pathlib import Path
ROOT=Path('E:/JustAnotherRpgGame_UR/JustAnotherRpgGame')
OUT=ROOT/'Source/Elements/Assets/Built/aof-material-witness';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
nx,ny=64,32;verts=[];faces=[]
for j in range(ny+1):
 for i in range(nx+1):verts.append((-2+4*i/nx,0,2.5*j/ny))
for j in range(ny):
 for i in range(nx):
  k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
mesh=bpy.data.meshes.new('LayerWitness');mesh.from_pydata(verts,[],faces);mesh.update()
obj=bpy.data.objects.new('SM_AOF_LayerWitness',mesh);bpy.context.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj;obj.select_set(True)
uv=mesh.uv_layers.new(name='UVMap');col=mesh.color_attributes.new(name='COLOR_0',type='FLOAT_COLOR',domain='CORNER')
for poly in mesh.polygons:
 for li in poly.loop_indices:
  vi=mesh.loops[li].vertex_index;x,y,z=verts[vi];uv.data[li].uv=((x+2)/2,z/2)
  r=max(0,min(1,(x+1.8)/3.6));g=max(0,min(1,(z-.2)/2.1));col.data[li].color=(r,g,0,1)
mat=bpy.data.materials.new('Preview');mat.diffuse_color=(.5,.5,.5,1);obj.data.materials.append(mat)
bpy.ops.export_scene.gltf(filepath=str(OUT/'SM_AOF_LayerWitness.glb'),export_format='GLB',use_selection=True,export_texcoords=True,export_normals=True,export_tangents=True,export_vertex_color='NAME',export_vertex_color_name='COLOR_0',export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'LayerWitness.blend'))
print('WITNESS_COMPLETE')
