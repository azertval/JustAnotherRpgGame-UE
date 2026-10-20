"""Shared ambient reflection texture for the current Arena and capital districts."""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def sculpted_ambient_cube():
    """A neutral sky-to-ground gradient; the day cycle supplies its colour.

    The previous white cube offered the same reflection from every direction.
    This original analytic HDR has no painted sun or baked architectural shadow.
    Its upper sky, horizon and dark ground make curved metal and stone respond
    differently as the view moves. It is shared by the production districts.
    """
    import unreal

    package = "/Game/ArenaWickedWitness/Lighting/T_AmbientGradient_v1"
    if unreal.EditorAssetLibrary.does_asset_exist(package):
        return unreal.EditorAssetLibrary.load_asset(package)
    width, height = 256, 128
    pixels = bytearray()
    for y in range(height):
        elevation = math.cos(math.pi * (y + 0.5) / height)
        luminance = (0.42 + 0.90 * elevation ** 0.65 if elevation >= 0.0
                     else 0.08 + 0.34 * (1.0 + elevation) ** 3)
        mantissa, exponent = math.frexp(luminance)
        channel = min(255, int(mantissa * 256))
        pixels.extend(bytes((channel, channel, channel, exponent + 128)) * width)
    source = ROOT / "Intermediate/Jadg/T_AmbientGradient_v1.hdr"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(f"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y {height} +X {width}\n".encode() + pixels)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path, task.destination_name = package.rsplit("/", 1)
    task.automated = True
    task.replace_existing = True
    task.save = True
    task.set_editor_property("async_", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset(package)
    if not isinstance(texture, unreal.TextureCube):
        raise RuntimeError("The witness's generated HDR did not import as a TextureCube")
    return texture
