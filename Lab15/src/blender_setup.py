import bpy

# ─────────────────────────────────────────────────────────
# v5 — Rollback procedural windows + create light blocks
#       for manual placement
# ─────────────────────────────────────────────────────────


def cleanup_procedural_material():
    """Removes procedural material from all buildings and deletes it."""
    mat_name = "Procedural_Night_Windows"

    dark_mat = bpy.data.materials.get("Dark_Building")
    if not dark_mat:
        dark_mat = bpy.data.materials.new(name="Dark_Building")
        dark_mat.use_nodes = True
        bsdf = dark_mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = (0.025, 0.025, 0.03, 1.0)
            bsdf.inputs['Roughness'].default_value = 0.9

    restored = 0
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for i, slot in enumerate(obj.material_slots):
                if slot.material and slot.material.name == mat_name:
                    obj.data.materials[i] = dark_mat
                    restored += 1

    old_mat = bpy.data.materials.get(mat_name)
    if old_mat:
        bpy.data.materials.remove(old_mat)

    print(f"  Removed procedural material from {restored} slots")
    print(f"  Buildings are now dark-grey ('Dark_Building')")


def hide_roads():
    """Hides Blosm roads and terrain."""
    hidden = 0
    for obj in bpy.data.objects:
        name_lower = obj.name.lower()
        if any(kw in name_lower for kw in (
            "roads", "terrain", "highway", "footway",
            "path", "water", "forest", "vegetation"
        )):
            obj.hide_viewport = True
            obj.hide_render = True
            hidden += 1
    print(f"  Hidden roads/terrain objects: {hidden}")


def create_window_light(name, color, strength, size=(0.8, 1.2)):
    """
    Creates a glowing plane (window).

    Args:
        name:     object name
        color:    emission color (R, G, B)
        strength: emission strength
        size:     width x height in meters
    """
    if name in bpy.data.objects:
        print(f"  '{name}' already exists — skipping")
        return bpy.data.objects[name]

    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 5))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0], size[1], 1.0)

    mat = bpy.data.materials.new(name=f"Mat_{name}")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        try:
            bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        except (TypeError, ValueError):
            bsdf.inputs['Base Color'].default_value = color[:3]

        if 'Emission Color' in bsdf.inputs:
            try:
                bsdf.inputs['Emission Color'].default_value = (*color, 1.0)
            except (TypeError, ValueError):
                bsdf.inputs['Emission Color'].default_value = color[:3]
        elif 'Emission' in bsdf.inputs:
            try:
                bsdf.inputs['Emission'].default_value = (*color, 1.0)
            except (TypeError, ValueError):
                bsdf.inputs['Emission'].default_value = color[:3]

        if 'Emission Strength' in bsdf.inputs:
            bsdf.inputs['Emission Strength'].default_value = strength

    obj.data.materials.append(mat)

    print(f"  Created '{name}' | color: {color} | strength: {strength} | size: {size[0]}x{size[1]}m")
    return obj


def create_all_light_blocks():
    """
    Creates 3 types of window light blocks + 1 neon sign.
    All appear at the origin — user places them manually.
    """

    col_name = "Window_Lights"
    if col_name not in bpy.data.collections:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
    else:
        col = bpy.data.collections[col_name]

    lights = []

    # 1. Warm window (residential — yellow-orange light)
    obj = create_window_light(
        name="Window_Warm",
        color=(1.0, 0.6, 0.2),
        strength=8.0,
        size=(0.8, 1.2)
    )
    lights.append(obj)

    # 2. Cool window (office — white-blue light)
    obj = create_window_light(
        name="Window_Cool",
        color=(0.7, 0.85, 1.0),
        strength=6.0,
        size=(1.0, 1.0)
    )
    lights.append(obj)

    # 3. Neon sign (pink-purple)
    obj = create_window_light(
        name="Neon_Sign",
        color=(1.0, 0.1, 0.5),
        strength=15.0,
        size=(2.0, 0.5)
    )
    lights.append(obj)

    # 4. Shop sign (green)
    obj = create_window_light(
        name="Shop_Sign",
        color=(0.2, 1.0, 0.4),
        strength=12.0,
        size=(1.5, 0.4)
    )
    lights.append(obj)

    for obj in lights:
        for old_col in obj.users_collection:
            old_col.objects.unlink(obj)
        col.objects.link(obj)

    for i, obj in enumerate(lights):
        obj.location = (i * 3, 0, 5)

    print(f"  All light blocks placed in collection '{col_name}'")


# ══════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  v5: ROLLBACK + CREATE LIGHT BLOCKS")
    print("=" * 50)

    cleanup_procedural_material()
    hide_roads()
    create_all_light_blocks()

    print("\n" + "=" * 50)
    print("  DONE!")
    print("")
    print("  How to use:")
    print("  1. Open Outliner -> collection 'Window_Lights'")
    print("  2. Select desired light block (e.g. Window_Warm)")
    print("  3. Shift+D -> duplicate and place on building wall")
    print("  4. R -> rotate to align with wall")
    print("  5. S -> scale to desired size")
    print("")
    print("  Types:")
    print("    Window_Warm  — residential window (warm yellow)")
    print("    Window_Cool  — office (cool white)")
    print("    Neon_Sign    — neon sign (pink)")
    print("    Shop_Sign    — shop sign (green)")
    print("=" * 50)
