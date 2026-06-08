import bpy
import math

# ─────────────────────────────────────────────────────────
# Cars with headlights, animated on curves
# Run SEPARATELY from blender_setup.py
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


def make_emission_mat(name, color, strength):
    """Creates an emissive material."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        safe_set(bsdf.inputs['Base Color'], (*color, 1.0))
        if 'Emission Color' in bsdf.inputs:
            safe_set(bsdf.inputs['Emission Color'], (*color, 1.0))
        elif 'Emission' in bsdf.inputs:
            safe_set(bsdf.inputs['Emission'], (*color, 1.0))
        if 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Strength'].default_value = strength
    return mat


def make_body_mat(name, color):
    """Creates a dark glossy car body material."""
    mat = bpy.data.materials.get(name)
    if mat:
        return mat
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        safe_set(bsdf.inputs['Base Color'], (*color, 1.0))
        bsdf.inputs['Roughness'].default_value = 0.3
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = 0.4
    return mat


def create_car(name, body_color=(0.02, 0.02, 0.03)):
    """
    Creates a simple low-poly car with headlights and taillights.
    Car faces +Y (forward).
    Dimensions: ~4.2m length x 1.8m width x 1.5m height.
    """
    if name in bpy.data.objects:
        print(f"  '{name}' already exists — skipping")
        return bpy.data.objects[name]

    mat_body = make_body_mat(f"Car_Body_{name}", body_color)
    mat_headlight = make_emission_mat("Car_Headlight", (1.0, 0.95, 0.8), 30.0)
    mat_taillight = make_emission_mat("Car_Taillight", (1.0, 0.05, 0.02), 15.0)
    mat_glass = make_body_mat("Car_Glass", (0.05, 0.08, 0.12))

    objects = []

    # Lower body
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.45))
    body = bpy.context.active_object
    body.name = f"{name}_body"
    body.scale = (1.8, 4.2, 0.9)
    body.data.materials.append(mat_body)
    objects.append(body)

    # Cabin (upper)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.3, 1.2))
    cabin = bpy.context.active_object
    cabin.name = f"{name}_cabin"
    cabin.scale = (1.5, 2.4, 0.6)
    cabin.data.materials.append(mat_glass)
    objects.append(cabin)

    # Headlights (front — white/yellow)
    # Body ends at Y=2.1, place lights at 2.11
    for x_offset in [-0.65, 0.65]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x_offset, 2.11, 0.6))
        hl = bpy.context.active_object
        hl.name = f"{name}_headlight"
        hl.rotation_euler = (math.radians(-90), 0, 0)
        hl.scale = (0.35, 0.2, 1)
        hl.data.materials.append(mat_headlight)
        objects.append(hl)

    # Taillights (rear — red)
    # Body starts at Y=-2.1, place lights at -2.11
    for x_offset in [-0.65, 0.65]:
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x_offset, -2.11, 0.7))
        tl = bpy.context.active_object
        tl.name = f"{name}_taillight"
        tl.rotation_euler = (math.radians(90), 0, 0)
        tl.scale = (0.45, 0.15, 1)
        tl.data.materials.append(mat_taillight)
        objects.append(tl)

    # Join all parts into one object
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()

    car = bpy.context.active_object
    car.name = name

    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    print(f"  Car '{name}' created")
    return car


def create_car_path(name, length=80.0, direction='Y'):
    """
    Creates a straight curve (path) for car animation.
    User can edit shape in Edit Mode.

    Args:
        name:      curve name
        length:    path length in meters
        direction: 'Y' or 'X' — road direction
    """
    if name in bpy.data.objects:
        print(f"  Path '{name}' already exists — skipping")
        return bpy.data.objects[name]

    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(3)  # 4 points total

    half = length / 2.0
    positions = [
        (-half, 0, 0),
        (-half / 3, 0, 0),
        (half / 3, 0, 0),
        (half, 0, 0),
    ]

    if direction == 'Y':
        positions = [(0, p[0], p[2]) for p in positions]

    for i, bp in enumerate(spline.bezier_points):
        bp.co = positions[i]
        bp.handle_left_type = 'AUTO'
        bp.handle_right_type = 'AUTO'

    curve_data.use_path = True
    curve_data.path_duration = 192  # 8 seconds at 24fps

    curve_obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(curve_obj)

    print(f"  Path '{name}' created (length: {length}m)")
    return curve_obj


def animate_car_on_path(car, path, duration_frames=192, offset=0, use_fixed_location=False):
    """
    Attaches a car to a path with animation.

    Args:
        car:             car object
        path:            curve object (path)
        duration_frames: frames to travel the entire path
        offset:          start offset (0..1) so cars are staggered
        use_fixed_location: if True, car stays still while offset animates
    """
    for c in car.constraints:
        car.constraints.remove(c)

    fp = car.constraints.new(type='FOLLOW_PATH')
    fp.target = path
    fp.use_curve_follow = True
    fp.forward_axis = 'FORWARD_Y'
    fp.up_axis = 'UP_Z'

    path_data = path.data
    path_data.use_path = True
    path_data.path_duration = duration_frames

    fp.use_fixed_location = True
    fp.offset_factor = 0.0

    start_val = offset
    end_val = offset + 1.0

    fp.offset_factor = start_val
    fp.keyframe_insert(data_path="offset_factor", frame=1)

    fp.offset_factor = end_val
    fp.keyframe_insert(data_path="offset_factor", frame=duration_frames)

    # Make animation linear (no easing)
    # Compatible with Blender 3.x / 4.x (fcurves API changed)
    try:
        if car.animation_data and car.animation_data.action:
            action = car.animation_data.action
            if hasattr(action, 'fcurves'):
                fcurves = action.fcurves
            elif hasattr(action, 'layers') and len(action.layers) > 0:
                fcurves = []
                for layer in action.layers:
                    for strip in layer.strips:
                        if hasattr(strip, 'fcurves'):
                            fcurves.extend(strip.fcurves)
            else:
                fcurves = []

            for fc in fcurves:
                if "offset_factor" in fc.data_path:
                    for kp in fc.keyframe_points:
                        kp.interpolation = 'LINEAR'
    except Exception as e:
        print(f"  Could not set linear interpolation: {e}")

    print(f"  '{car.name}' animated on '{path.name}' (offset: {offset:.1f})")


# ══════════════════════════════════════════════════════════
# SCENE SETUP
# ══════════════════════════════════════════════════════════
def setup_cars():
    """
    Creates several cars on parallel roads.
    User moves paths (curves) to their streets.
    """

    col_name = "Cars"
    if col_name not in bpy.data.collections:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    else:
        col = bpy.data.collections[col_name]

    # Two roads: forward and reverse
    path_fwd = create_car_path("CarPath_Forward", length=100, direction='Y')
    path_rev = create_car_path("CarPath_Reverse", length=100, direction='Y')
    path_rev.location.x = 4.0

    # Lane 1: driving forward (toward camera)
    car1 = create_car("Car_Dark_1", body_color=(0.015, 0.015, 0.02))
    car2 = create_car("Car_Silver_1", body_color=(0.15, 0.15, 0.17))

    # Lane 2: driving backward (away from camera)
    car3 = create_car("Car_Red_1", body_color=(0.15, 0.01, 0.01))
    car4 = create_car("Car_Dark_2", body_color=(0.01, 0.01, 0.015))

    # Animation with different offsets so cars are staggered
    animate_car_on_path(car1, path_fwd, duration_frames=192, offset=0.0)
    animate_car_on_path(car2, path_fwd, duration_frames=192, offset=-0.3)

    # Lane 2 goes in reverse direction (offset from 1 to 0)
    animate_car_on_path(car3, path_rev, duration_frames=192, offset=1.0)
    animate_car_on_path(car4, path_rev, duration_frames=192, offset=0.6)

    all_objs = [path_fwd, path_rev, car1, car2, car3, car4]
    for obj in all_objs:
        for old_col in obj.users_collection:
            old_col.objects.unlink(obj)
        col.objects.link(obj)

    print(f"  All cars and paths in collection '{col_name}'")


# ══════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  CREATING ANIMATED CARS")
    print("=" * 50)

    setup_cars()

    print("\n" + "=" * 50)
    print("  DONE!")
    print("")
    print("  Next steps:")
    print("  1. In Outliner, expand 'Cars' collection")
    print("  2. Select 'CarPath_Forward' -> G -> move to your street")
    print("  3. Select 'CarPath_Reverse' -> G -> to the parallel lane")
    print("  4. Edit Mode (Tab) on path -> move points along road shape")
    print("  5. Space -> play animation and check")
    print("")
    print("  Cars:")
    print("    Car_Dark_1   + Car_Silver_1  -> lane 1 (forward)")
    print("    Car_Red_1    + Car_Dark_2    -> lane 2 (reverse)")
    print("")
    print("  Need more cars? Duplicate (Shift+D) and")
    print("  assign them the same Follow Path constraint.")
    print("=" * 50)
