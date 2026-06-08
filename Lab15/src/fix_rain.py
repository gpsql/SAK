import bpy

# ─────────────────────────────────────────────────────────
# Rain fix (make rain visible at night)
# ─────────────────────────────────────────────────────────

def safe_set(socket, value):
    try:
        socket.default_value = value
    except (TypeError, ValueError):
        if hasattr(value, '__len__') and len(value) == 4:
            try:
                socket.default_value = value[:3]
            except Exception:
                pass
        elif hasattr(value, '__len__') and len(value) == 3:
            try:
                socket.default_value = (*value, 1.0)
            except Exception:
                pass

def fix_rain_visibility():
    # 1. Fix drop material
    # Restore glass (water) properties, remove emission.
    # The scene has enough light so emission is not needed.
    mat = bpy.data.materials.get("Rain_Material")
    if mat and mat.use_nodes:
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if 'Transmission Weight' in bsdf.inputs:
                bsdf.inputs['Transmission Weight'].default_value = 1.0
            elif 'Transmission' in bsdf.inputs:
                bsdf.inputs['Transmission'].default_value = 1.0

            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value = 0.0
            if 'Emission Color' in bsdf.inputs:
                safe_set(bsdf.inputs['Emission Color'], (0, 0, 0, 1))
            elif 'Emission' in bsdf.inputs:
                safe_set(bsdf.inputs['Emission'], (0, 0, 0, 1))

            safe_set(bsdf.inputs['Base Color'], (0.9, 0.95, 1.0, 1.0))
            bsdf.inputs['Roughness'].default_value = 0.02

            if 'Alpha' in bsdf.inputs:
                bsdf.inputs['Alpha'].default_value = 1.0

            if hasattr(mat, 'blend_method'):
                mat.blend_method = 'BLEND'
            if hasattr(mat, 'shadow_method'):
                mat.shadow_method = 'NONE'

    # 2. Restore drop size in particle system
    emitter = bpy.data.objects.get("Rain_Emitter")
    if emitter and len(emitter.particle_systems) > 0:
        ps = emitter.particle_systems[0]
        ps.settings.particle_size = 0.2   # Thin, small drops
        ps.settings.count = 50000         # More drops for density

    print("  Rain material fixed: emission removed, glass restored")
    print("  Drop size reduced, density increased")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  RAIN FIX")
    print("="*50)
    fix_rain_visibility()
    print("\n  DONE!")
    print("  Try rendering 1 frame (F12) now.")
    print("  Drops should look like bright white streaks.")
    print("="*50)
