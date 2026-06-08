import bpy
import math

# ─────────────────────────────────────────────────────────
# Road generation (wet asphalt with puddles and markings)
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

def setup_road():
    road_name = "Main_Road"

    # 1. Create road geometry (long plane)
    if road_name not in bpy.data.objects:
        # 10m wide, 200m long
        bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0))
        road = bpy.context.active_object
        road.name = road_name
        road.scale = (10, 200, 1)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    else:
        road = bpy.data.objects[road_name]

    # Offset road so cars travel along it
    # Car paths: path_fwd at X=0, path_rev at X=4 -> center at X=2
    road.location = (2.0, 0, 0.01)  # Slightly above Z=0 to avoid z-fighting

    # 2. Create procedural wet asphalt material
    mat_name = "Wet_Asphalt"
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    for n in nodes:
        nodes.remove(n)

    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    bsdf.location = (800, 0)

    out = nodes.new(type="ShaderNodeOutputMaterial")
    out.location = (1100, 0)
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

    tc = nodes.new(type="ShaderNodeTexCoord")
    tc.location = (-1000, 0)

    # Puddles and asphalt (Noise -> ColorRamp -> Roughness)
    noise_puddles = nodes.new(type="ShaderNodeTexNoise")
    noise_puddles.location = (-600, 200)
    noise_puddles.inputs['Scale'].default_value = 2.0
    noise_puddles.inputs['Detail'].default_value = 15.0
    noise_puddles.inputs['Roughness'].default_value = 0.6
    links.new(tc.outputs['Object'], noise_puddles.inputs['Vector'])

    ramp_rough = nodes.new(type="ShaderNodeValToRGB")
    ramp_rough.location = (-300, 200)
    ramp_rough.color_ramp.elements[0].position = 0.4
    ramp_rough.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)  # Puddles (glossy)
    ramp_rough.color_ramp.elements[1].position = 0.6
    ramp_rough.color_ramp.elements[1].color = (0.5, 0.5, 0.5, 1.0)  # Dry asphalt (rough)
    links.new(noise_puddles.outputs['Fac'], ramp_rough.inputs['Fac'])

    links.new(ramp_rough.outputs['Color'], bsdf.inputs['Roughness'])

    # Asphalt bump
    bump = nodes.new(type="ShaderNodeBump")
    bump.location = (400, -200)
    bump.inputs['Strength'].default_value = 0.2
    bump.inputs['Distance'].default_value = 0.1
    links.new(noise_puddles.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])

    # Asphalt base color
    safe_set(bsdf.inputs['Base Color'], (0.03, 0.03, 0.03, 1.0))

    # Road markings (procedural)
    sep_xyz = nodes.new(type="ShaderNodeSeparateXYZ")
    sep_xyz.location = (-600, -300)
    links.new(tc.outputs['Object'], sep_xyz.inputs['Vector'])

    # Center dashed line (separates lanes at X=0 and X=4, center X=2)
    # Road offset to X=2, so object-local center = X=0.

    # Line thickness (Math Absolute X < 0.1)
    math_abs = nodes.new(type="ShaderNodeMath")
    math_abs.operation = 'ABSOLUTE'
    math_abs.location = (-400, -300)
    links.new(sep_xyz.outputs['X'], math_abs.inputs[0])

    math_lt = nodes.new(type="ShaderNodeMath")
    math_lt.operation = 'LESS_THAN'
    math_lt.location = (-200, -300)
    math_lt.inputs[1].default_value = 0.1  # Line width
    links.new(math_abs.outputs['Value'], math_lt.inputs[0])

    # Dash length (Math Modulo Y)
    math_mod = nodes.new(type="ShaderNodeMath")
    math_mod.operation = 'MODULO'
    math_mod.location = (-400, -500)
    math_mod.inputs[1].default_value = 4.0  # One cycle length (line + gap)
    links.new(sep_xyz.outputs['Y'], math_mod.inputs[0])

    math_gt = nodes.new(type="ShaderNodeMath")
    math_gt.operation = 'GREATER_THAN'
    math_gt.location = (-200, -500)
    math_gt.inputs[1].default_value = 2.0  # Line length in meters
    links.new(math_mod.outputs['Value'], math_gt.inputs[0])

    # Intersection (Line AND Dash)
    math_and = nodes.new(type="ShaderNodeMath")
    math_and.operation = 'MULTIPLY'
    math_and.location = (0, -400)
    links.new(math_lt.outputs['Value'], math_and.inputs[0])
    links.new(math_gt.outputs['Value'], math_and.inputs[1])

    # Mix asphalt color with white marking color
    mix_color = nodes.new(type="ShaderNodeMixRGB")
    mix_color.location = (400, 200)
    safe_set(mix_color.inputs[1], (0.03, 0.03, 0.03, 1.0))  # Asphalt
    safe_set(mix_color.inputs[2], (0.8, 0.8, 0.8, 1.0))     # White marking
    links.new(math_and.outputs['Value'], mix_color.inputs[0])
    links.new(mix_color.outputs['Color'], bsdf.inputs['Base Color'])

    if len(road.data.materials) == 0:
        road.data.materials.append(mat)
    else:
        road.data.materials[0] = mat

    print(f"  Road '{road_name}' created (10x200m)")
    print(f"  Wet asphalt material with markings applied")
    return road

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  ROAD CREATION")
    print("="*50)
    setup_road()
    print("\n  DONE!")
    print("  Road 'Main_Road' added to scene.")
    print("  It has procedural 'Wet_Asphalt' material with puddles")
    print("  that will beautifully reflect night light from windows and cars.")
    print("="*50)
