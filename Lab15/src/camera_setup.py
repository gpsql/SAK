import bpy
import math

# ─────────────────────────────────────────────────────────
# POV camera setup (first-person walk)
# ─────────────────────────────────────────────────────────

def setup_pov_camera():
    """Creates a first-person camera with walk animation."""

    path_name = "POV_Path"
    base_name = "POV_Base"
    cam_name = "POV_Camera"

    # 1. Create path (curve)
    if path_name not in bpy.data.objects:
        curve_data = bpy.data.curves.new(name=path_name, type='CURVE')
        curve_data.dimensions = '3D'
        spline = curve_data.splines.new('BEZIER')
        spline.bezier_points.add(1)

        # Walk length ~20 meters forward
        spline.bezier_points[0].co = (0, 0, 0.5)
        spline.bezier_points[1].co = (0, 20, 0.5)

        for bp in spline.bezier_points:
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'

        curve_data.use_path = True
        curve_data.path_duration = 192  # 8 seconds

        path_obj = bpy.data.objects.new(path_name, curve_data)
        bpy.context.collection.objects.link(path_obj)
    else:
        path_obj = bpy.data.objects[path_name]

    # 2. Create Base (empty) that follows the path
    if base_name not in bpy.data.objects:
        base_obj = bpy.data.objects.new(base_name, None)
        base_obj.empty_display_type = 'ARROWS'
        base_obj.empty_display_size = 1.0
        bpy.context.collection.objects.link(base_obj)
    else:
        base_obj = bpy.data.objects[base_name]

    for c in base_obj.constraints:
        base_obj.constraints.remove(c)

    fp = base_obj.constraints.new(type='FOLLOW_PATH')
    fp.target = path_obj
    fp.use_curve_follow = True
    fp.forward_axis = 'FORWARD_Y'
    fp.up_axis = 'UP_Z'
    fp.use_fixed_location = True

    # Animate movement (0 -> 1 over 192 frames)
    if base_obj.animation_data:
        base_obj.animation_data_clear()

    base_obj.animation_data_create()
    base_obj.animation_data.action = bpy.data.actions.new(name="POV_Walk")

    fp.offset_factor = 0.0
    fp.keyframe_insert(data_path="offset_factor", frame=1)
    fp.offset_factor = 1.0
    fp.keyframe_insert(data_path="offset_factor", frame=192)

    # Set linear interpolation
    action = base_obj.animation_data.action

    def get_fcurves(act):
        res = []
        if hasattr(act, 'fcurves'):
            res.extend(act.fcurves)
        elif hasattr(act, 'layers'):
            for layer in act.layers:
                for strip in layer.strips:
                    if hasattr(strip, 'fcurves'):
                        res.extend(strip.fcurves)
        return res

    for fc in get_fcurves(action):
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

    # 3. Create Camera
    if cam_name not in bpy.data.objects:
        cam_data = bpy.data.cameras.new(cam_name)
        cam_obj = bpy.data.objects.new(cam_name, cam_data)
        bpy.context.collection.objects.link(cam_obj)
    else:
        cam_obj = bpy.data.objects[cam_name]
        cam_data = cam_obj.data

    # Wide-angle lens for more immersion
    cam_data.lens = 28.0
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 5.0
    cam_data.dof.aperture_fstop = 2.8

    cam_obj.parent = base_obj

    # Place camera at human eye height (1.7m from ground)
    # Path is at Z=0.5, local Z=1.2 -> total 1.7
    cam_obj.location = (0, 0, 1.2)
    cam_obj.rotation_euler = (math.radians(90), 0, 0)

    bpy.context.scene.camera = cam_obj

    # 4. Add procedural head bobbing
    if cam_obj.animation_data:
        cam_obj.animation_data_clear()

    cam_obj.animation_data_create()
    action_cam = bpy.data.actions.new(name="Camera_Shake")
    cam_obj.animation_data.action = action_cam

    cam_obj.keyframe_insert(data_path="location", index=0, frame=1)      # X (left/right)
    cam_obj.keyframe_insert(data_path="location", index=2, frame=1)      # Z (up/down)
    cam_obj.keyframe_insert(data_path="rotation_euler", index=1, frame=1) # Y (roll)
    cam_obj.keyframe_insert(data_path="rotation_euler", index=0, frame=1) # X (pitch)

    for fc in get_fcurves(action_cam):
        # Vertical steps (Z location)
        if fc.data_path == "location" and fc.array_index == 2:
            mod = fc.modifiers.new(type='NOISE')
            mod.scale = 3.5
            mod.strength = 0.04
            mod.offset = 1.0
            mod.phase = 0.0

        # Body sway left-right (X location)
        elif fc.data_path == "location" and fc.array_index == 0:
            mod = fc.modifiers.new(type='NOISE')
            mod.scale = 7.0
            mod.strength = 0.03
            mod.offset = 2.0
            mod.phase = 45.0

        # Head tilt left-right (Y rotation)
        elif fc.data_path == "rotation_euler" and fc.array_index == 1:
            mod = fc.modifiers.new(type='NOISE')
            mod.scale = 8.0
            mod.strength = 0.02
            mod.offset = 3.0
            mod.phase = 90.0

        # Head tilt forward-backward (X rotation)
        elif fc.data_path == "rotation_euler" and fc.array_index == 0:
            mod = fc.modifiers.new(type='NOISE')
            mod.scale = 5.0
            mod.strength = 0.01
            mod.offset = 4.0
            mod.phase = 180.0

    print("  POV camera set up!")
    print("  Base: 'POV_Base', Path: 'POV_Path'")
    print("  Procedural head bobbing noise added")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  CAMERA SETUP (POV)")
    print("="*50)
    setup_pov_camera()
    print("\n  DONE!")
    print("  Next steps:")
    print("  1. Select 'POV_Path' in Outliner")
    print("  2. Enter Edit Mode (Tab)")
    print("  3. Align the path along your street")
    print("  4. Press Numpad 0 to switch to camera view")
    print("  5. Press Space to play and check the head bobbing")
    print("="*50)
