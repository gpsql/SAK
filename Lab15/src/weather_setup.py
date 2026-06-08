import bpy
import math

# ─────────────────────────────────────────────────────────
# Weather setup: Fog and Rain
# ─────────────────────────────────────────────────────────

def setup_fog():
    """Sets up volumetric fog in the World shader."""
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    world_out = nodes.get("World Output")
    if not world_out:
        world_out = nodes.new("ShaderNodeOutputWorld")

    vol_scatter = nodes.get("Volume Scatter")
    if not vol_scatter:
        vol_scatter = nodes.new("ShaderNodeVolumeScatter")

    # Light haze so it doesn't look like solid milk
    vol_scatter.inputs['Density'].default_value = 0.015
    # Light from lamps scatters around them (halos)
    vol_scatter.inputs['Anisotropy'].default_value = 0.7
    # Bluish night fog
    vol_scatter.inputs['Color'].default_value = (0.7, 0.8, 0.9, 1.0)

    if 'Volume' in world_out.inputs:
        links.new(vol_scatter.outputs['Volume'], world_out.inputs['Volume'])

    # Dark blue night sky
    bg = nodes.get("Background")
    if bg:
        bg.inputs['Color'].default_value = (0.01, 0.015, 0.03, 1.0)
        bg.inputs['Strength'].default_value = 0.1

    print("  Volumetric fog set up")


def setup_rain():
    """Creates a particle system for rain."""

    # 1. Create rain drop object (used as particle instance)
    drop_name = "RainDrop_Object"
    if drop_name not in bpy.data.objects:
        # Drop shape: elongated cone
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.01, depth=0.1, location=(0, 0, -10))
        drop = bpy.context.active_object
        drop.name = drop_name
        drop.scale = (1, 1, 8)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        drop.rotation_euler = (math.radians(90), 0, 0)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

        mat = bpy.data.materials.new(name="Rain_Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (0.8, 0.9, 1.0, 1.0)

            if 'Transmission Weight' in bsdf.inputs:  # Blender 4.0+
                bsdf.inputs['Transmission Weight'].default_value = 1.0
            elif 'Transmission' in bsdf.inputs:       # Blender 3.x
                bsdf.inputs['Transmission'].default_value = 1.0

            bsdf.inputs['Roughness'].default_value = 0.05
            if 'IOR' in bsdf.inputs:
                bsdf.inputs['IOR'].default_value = 1.33  # Water IOR

        drop.data.materials.append(mat)
        drop.hide_render = True
        drop.hide_viewport = True
    else:
        drop = bpy.data.objects[drop_name]

    # 2. Create rain emitter (cloud plane)
    emitter_name = "Rain_Emitter"
    if emitter_name in bpy.data.objects:
        print("  Rain emitter already exists — delete old one to recreate.")
        return bpy.data.objects[emitter_name]

    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 15))
    emitter = bpy.context.active_object
    emitter.name = emitter_name

    # Attach emitter to camera so the cloud follows us
    camera = bpy.context.scene.camera
    if camera:
        emitter.location = (camera.location.x, camera.location.y, camera.location.z + 12)
        copy_loc = emitter.constraints.new(type='COPY_LOCATION')
        copy_loc.target = camera
        copy_loc.use_z = False

    # 3. Configure particle system
    bpy.ops.object.particle_system_add()
    ps = emitter.particle_systems[0]
    ps.name = "Rain_System"
    pset = ps.settings

    pset.count = 25000       # Number of drops
    pset.frame_start = -50   # Start before frame 1 so rain is already falling
    pset.frame_end = 250     # End after 8 seconds of animation (192 frames)
    pset.lifetime = 100      # Drop fall duration

    # Physics
    pset.physics_type = 'NEWTON'
    pset.mass = 0.2
    pset.normal_factor = 0.0   # No spread from plane surface
    pset.factor_random = 0.2   # Slight random initial velocity

    # Render drops as object instances
    pset.render_type = 'OBJECT'
    pset.instance_object = drop
    pset.particle_size = 0.6
    pset.size_random = 0.5     # Variety from drizzle to large drops

    # Orient drops along velocity vector
    pset.use_rotations = True
    pset.rotation_mode = 'VEL'

    emitter.show_instancer_for_render = False
    emitter.show_instancer_for_viewport = False

    pset.display_method = 'RENDER'

    # Enable Motion Blur for realistic streaking drops
    bpy.context.scene.render.use_motion_blur = True
    bpy.context.scene.render.motion_blur_shutter = 0.5

    print("  Rain particle system created")
    return emitter


if __name__ == "__main__":
    print("\n" + "="*50)
    print("  WEATHER SETUP")
    print("="*50)

    setup_fog()
    setup_rain()

    print("\n  DONE!")
    print("  - Volumetric fog added to World")
    print("  - Rain emitter 'Rain_Emitter' created")
    print("  - Motion Blur enabled")
    print("")
    print("  (If drops look sparse — select Rain_Emitter, go to")
    print("   Particle Properties and increase Emission -> Number)")
    print("="*50)
