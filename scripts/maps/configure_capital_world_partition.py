#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Valentin Eloy
# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
"""Configure and audit the converted capital; never alter district source maps.

Produces /Game/Capitale/Ressources/Metropole/HLOD/HLOD_Paysage and the final
/Game/Capitale/Cartes/Capitale external actor packages.
"""
from pathlib import Path
from array import array
import json
import sys
import time
import unreal as u

# Archived generator: the current construction world must not be overwritten.
if __name__ == "__main__":
    raise RuntimeError("Generateur historique archive apres nettoyage. Ouvrir /Game/Capitale/Cartes/Capitale ; restauration explicite requise pour regenerer les anciens essais.")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'scripts/assetsGeneration'))
from import_scenery_unreal import command_line_option  # noqa: E402

OUT = ROOT/'Saved/Jadg/capital-landscape-districts/world-partition'
PACKAGE = '/Game/Capitale/Cartes/Capitale'
AL = u.EditorAssetLibrary
WP = u.WorldPartitionBlueprintLibrary
LAYERS = ('Pelouse', 'Prairie', 'HerbeSauvage', 'Terre', 'Sable', 'Roche', 'Pavage')
SOURCE_TILES = {}


def minimap(world, verify):
    desc = next(d for d in WP.get_actor_descs() if d.native_class.get_name() == 'WorldPartitionMiniMap')
    WP.load_actors([desc.guid])
    actor = u.find_object(None, str(desc.actor_path))
    if not verify:
        actor.set_editor_property('WorldUnitsPerPixel', 1000)
        actor.set_editor_property('BuilderCellSize', 100800)
        actor.set_editor_property('CaptureWarmupFrames', 8)
        if not u.EditorLoadingAndSavingUtils.save_packages([actor.get_package()], False):
            raise RuntimeError('Minimap settings failed to save')
        return
    texture = actor.get_editor_property('MiniMapTexture')
    if texture is None:
        raise RuntimeError('World Partition overview missing')
    task = u.AssetExportTask()
    task.object = texture
    task.filename = str(OUT/'apercu-world-partition.png')
    task.automated = True
    task.replace_identical = True
    task.exporter = u.TextureExporterPNG()
    if not u.Exporter.run_asset_export_task(task):
        raise RuntimeError('World Partition overview export failed')
    report = dict(texture=texture.get_path_name(),
                  dimensions=[texture.blueprint_get_size_x(), texture.blueprint_get_size_y()],
                  metresPerPixel=actor.get_editor_property('WorldUnitsPerPixel')/100,
                  builderCell_m=actor.get_editor_property('BuilderCellSize')/100)
    (OUT/'minimap.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print('CAPITAL_MINIMAP_OK', report, flush=True)


def check_ground(world, actor, component):
    center = u.SystemLibrary.get_component_bounds(component)[0]
    x, y = round(center.x/400)*4, round(center.y/400)*4
    tx, ty = int((x+5040)//1008), int((y+6048)//1008)
    name = f't{tx:02d}_{ty:02d}'
    if name not in SOURCE_TILES:
        folder = OUT.parent/'tiles'/name
        heights = array('H')
        heights.frombytes((folder/'heights.r16').read_bytes())
        SOURCE_TILES[name] = heights, (folder/'weights.r8').read_bytes()
    heights, paint = SOURCE_TILES[name]
    ix, iy = int((x+5040-tx*1008)/4), int((y+6048-ty*1008)/4)
    index = iy*253+ix
    z = (heights[index]-32768)/128
    weights = list(u.JadgSceneBuild.landscape_weights_at(actor, u.Vector(x*100, y*100, z*100), list(LAYERS)))
    expected = [paint[k*253*253+index]/255 for k in range(7)]
    ignored = [a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
               if isinstance(a, u.InstancedFoliageActor)]
    hit = u.SystemLibrary.line_trace_single(world, u.Vector(x*100, y*100, 30000),
        u.Vector(x*100, y*100, -5000), u.TraceTypeQuery.ECC_VISIBILITY, True,
        ignored, u.DrawDebugTrace.NONE, True)
    values = hit.to_tuple() if hit else None
    actual = values[5].z/100 if values and values[0] else None
    return dict(tile=name, xy=[x, y], expectedHeight=z, height=actual,
                paintError=max(abs(a-b) for a, b in zip(weights, expected)) if len(weights) == 7 else 1,
                collisionPassed=actual is not None and abs(actual-z) <= .04)


def main():
    inspect_only = command_line_option('CapitalWP') == 'audit'
    OUT.mkdir(parents=True, exist_ok=True)
    world = u.EditorLoadingAndSavingUtils.load_map(PACKAGE)
    if world is None:
        raise RuntimeError('World Partition map missing')
    mode = command_line_option('CapitalWP')
    if mode in ('minimap', 'minimap_audit'):
        minimap(world, mode == 'minimap_audit')
        return
    settings = world.get_world_settings()
    partition = settings.get_editor_property('world_partition')
    if partition is None:
        raise RuntimeError('The capital is not a World Partition world')
    runtime_hash = u.JadgSceneBuild.world_partition_runtime_hash(world)
    if not inspect_only:
        if not u.JadgSceneBuild.set_world_partition_streaming(world, True):
            raise RuntimeError('Cannot enable World Partition streaming')
        grids = runtime_hash.get_editor_property('grids')
        if len(grids) != 1:
            raise RuntimeError('Expected one runtime grid')
        grid = grids[0]
        grid.set_editor_property('GridName', 'Capital')
        grid.set_editor_property('CellSize', 50400)
        grid.set_editor_property('LoadingRange', 151200)
        grid.set_editor_property('bBlockOnSlowStreaming', False)
        runtime_hash.set_editor_property('grids', [grid])
        hlod_path = '/Game/Capitale/Ressources/Metropole/HLOD/HLOD_Paysage'
        # Commandlets do not necessarily discover the engine template directory.
        u.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(
            ['/Engine/Maps/Templates/HLODs'], force_rescan=True)
        hlod = AL.load_asset(hlod_path) if AL.does_asset_exist(hlod_path) else AL.duplicate_asset(
            '/Engine/Maps/Templates/HLODs/HLODLayer_Instanced', hlod_path)
        if hlod is None:
            raise RuntimeError('HLOD layer creation failed')
        hlod.set_editor_property('parent_layer', None)
        # Bound each HLOD build to a 1 km cell instead of merging the whole city.
        hlod.set_editor_property('is_spatially_loaded', True)
        hlod.set_editor_property('cell_size', 100800)
        hlod.set_editor_property('loading_range', 604800)
        AL.save_loaded_asset(hlod)
        partition.set_editor_property('default_hlod_layer', hlod)
        # Grass is local detail; tree silhouettes are retained by the distant HLOD.
        for path in AL.list_assets('/Game/Capitale/Ressources/Arenarea/Foliage', recursive=True):
            ft = AL.load_asset(path)
            if isinstance(ft, u.FoliageType):
                ft.set_editor_property('include_in_hlod', False)
                AL.save_loaded_asset(ft)
        for name in ('cypres', 'ombrage'):
            ft = AL.load_asset('/Game/Capitale/Ressources/Metropole/Vegetation/FT_'+name)
            ft.set_editor_property('include_in_hlod', True)
            AL.save_loaded_asset(ft)
    descriptors = WP.get_actor_descs()
    errors, rows = [], []
    # Keep only one bounded batch of external actors explicitly loaded at a time.
    for start in range(0, len(descriptors), 32):
        group = descriptors[start:start+32]
        ids = [d.guid for d in group]
        WP.load_actors(ids)
        packages = set()
        for desc in group:
            actor = u.find_object(None, str(desc.actor_path))
            # Editor cell loaders intentionally filter HLODs. Inspect their saved
            # external packages directly, without altering their streaming flags.
            if actor is None and desc.native_class.get_name() == 'WorldPartitionHLOD':
                u.load_package(str(desc.actor_package))
                actor = u.find_object(None, str(desc.actor_path))
            if actor is None:
                errors.append('Cannot load '+str(desc.actor_path))
                continue
            kind = actor.get_class().get_name()
            spatial = kind in ('LandscapeStreamingProxy', 'InstancedFoliageActor') or 'CapitalWater' in [str(t) for t in actor.tags]
            if not inspect_only:
                # The converter inherits AlwaysLoaded from the workshop sublevels.
                # Reset it only in this final world; lighting and framing stay global.
                if kind != 'Landscape':
                    actor.set_editor_property('is_spatially_loaded', spatial)
                if spatial:
                    actor.set_editor_property('runtime_grid', 'Capital')
                    actor.set_editor_property('hlod_layer', hlod)
                    actor.set_editor_property('enable_auto_lod_generation', True)
                # OFPA actors have an external package distinct from their world outer.
                packages.add(actor.get_package())
            is_spatial = bool(actor.get_editor_property('is_spatially_loaded'))
            if spatial and not is_spatial:
                errors.append('Non-streaming landscape actor '+actor.get_actor_label())
            row = dict(label=actor.get_actor_label(), kind=kind, spatial=is_spatial)
            if isinstance(actor, u.LandscapeProxy):
                components = actor.get_components_by_class(u.LandscapeComponent)
                row['components'] = len(components)
                row['naniteComponents'] = len(actor.get_components_by_class(u.LandscapeNaniteComponent))
                if kind == 'Landscape' and components:
                    errors.append('Landscape was not partitioned '+actor.get_actor_label())
                if kind == 'LandscapeStreamingProxy':
                    if len(components) > 4:
                        errors.append('Landscape proxy exceeds 504 m cell '+actor.get_actor_label())
                    if not inspect_only and not u.JadgSceneBuild.is_landscape_nanite_current(actor):
                        if not u.JadgSceneBuild.build_landscape_nanite(actor):
                            raise RuntimeError('Nanite rebuild failed '+actor.get_actor_label())
                    row['naniteTriangles'] = sum(c.static_mesh.get_num_nanite_triangles()
                        for c in actor.get_components_by_class(u.LandscapeNaniteComponent) if c.static_mesh)
                    if inspect_only and row['naniteTriangles'] <= 0:
                        errors.append('Nanite representation missing '+actor.get_actor_label())
                    if inspect_only and not u.JadgSceneBuild.is_landscape_nanite_current(actor):
                        errors.append('Nanite representation is stale '+actor.get_actor_label())
                    if inspect_only and components:
                        row['groundCheck'] = check_ground(world, actor, components[0])
                        if not row['groundCheck']['collisionPassed'] or row['groundCheck']['paintError'] > .025:
                            errors.append('Converted ground or paint differs '+actor.get_actor_label())
            if isinstance(actor, u.InstancedFoliageActor):
                row['instances'] = sum(c.get_instance_count() for c in actor.get_components_by_class(u.InstancedStaticMeshComponent))
            if kind == 'WorldPartitionHLOD':
                meshes = [c for c in actor.get_components_by_class(u.StaticMeshComponent) if c.static_mesh]
                row['hlodMeshComponents'] = len(meshes)
                row['hlodTerrainMeshes'] = sum(c.static_mesh.get_path_name().startswith('/Game/__ExternalActors__/') for c in meshes)
                row['hlodInstances'] = sum(c.get_instance_count() for c in meshes if isinstance(c, u.InstancedStaticMeshComponent))
                if any('/Game/Bibliotheque/Scans/Megascans/Plants/' in c.static_mesh.get_path_name() for c in meshes):
                    errors.append('Local grass was included in distant HLOD '+actor.get_actor_label())
            if isinstance(actor, u.StaticMeshActor) and 'CapitalWater' not in [str(t) for t in actor.tags]:
                errors.append('Unexpected static actor '+actor.get_actor_label())
            rows.append(row)
        if packages and not u.EditorLoadingAndSavingUtils.save_packages(list(packages), True):
            raise RuntimeError('External actors failed to save')
        packages.clear()
        actor, components, meshes = None, [], []
        WP.unload_actors(ids)
        u.SystemLibrary.collect_garbage()
        print('CAPITAL_WP_BATCH', start, len(descriptors), flush=True)
    if not inspect_only and not u.EditorLoadingAndSavingUtils.save_map(world, PACKAGE):
        raise RuntimeError('World Partition settings failed to save')
    planned = sum(json.loads(p.read_text())['instances'] for p in OUT.parent.glob('Q*/03-foliage.json'))
    actual = sum(r.get('instances', 0) for r in rows)
    if actual != planned:
        errors.append(f'Converted foliage differs: {actual} / {planned}')
    grid_rows = [dict(name=str(g.get_editor_property('GridName')),
                      cell_m=g.get_editor_property('CellSize')/100,
                      loadingRadius_m=g.get_editor_property('LoadingRange')/100,
                      blockOnSlowStreaming=bool(g.get_editor_property('bBlockOnSlowStreaming')))
                 for g in runtime_hash.get_editor_property('grids')]
    if len(grid_rows) != 1 or grid_rows[0] != dict(name='Capital', cell_m=504, loadingRadius_m=1512, blockOnSlowStreaming=False):
        errors.append('Unexpected runtime grid settings')
    total_components = sum(r.get('components', 0) for r in rows)
    if total_components != 2288:
        errors.append(f'Landscape components differ: {total_components}/2288')
    if inspect_only and not any(r.get('hlodTerrainMeshes', 0) for r in rows):
        errors.append('Distant landscape HLODs missing')
    report = dict(package=PACKAGE, streaming=u.JadgSceneBuild.is_world_partition_streaming(world),
                  runtimeHash=runtime_hash.get_class().get_name(), grids=grid_rows, landscapeComponents=total_components,
                  actors=rows, foliageInstances=actual, expectedFoliageInstances=planned,
                  buildings=0, errors=errors, utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    (OUT/('audit.json' if inspect_only else 'configuration.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    if errors:
        raise RuntimeError('; '.join(errors[:10]))
    print('CAPITAL_WORLD_PARTITION_OK', len(rows), actual, flush=True)


if __name__ == '__main__':
    main()
