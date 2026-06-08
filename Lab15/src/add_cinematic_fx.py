import bpy

def setup_cinematic_compositor():
    scene = bpy.context.scene
    scene.use_nodes = True

    # In Blender 4.2+ and 5.x, node_tree was replaced by compositing_node_group
    if hasattr(scene, 'node_tree') and scene.node_tree:
        tree = scene.node_tree
    elif hasattr(scene, 'compositing_node_group') and scene.compositing_node_group:
        tree = scene.compositing_node_group
    else:
        if 'Compositing' not in bpy.data.node_groups:
            tree = bpy.data.node_groups.new(name="Compositing", type="CompositorNodeTree")
        else:
            tree = bpy.data.node_groups['Compositing']
        if hasattr(scene, 'compositing_node_group'):
            scene.compositing_node_group = tree

    for node in list(tree.nodes):
        tree.nodes.remove(node)

    # 1. Render Layers (input image)
    render_layers = tree.nodes.new(type="CompositorNodeRLayers")
    render_layers.location = (0, 0)

    # 2. Glare (bloom / glow)
    glare = tree.nodes.new(type="CompositorNodeGlare")
    glare.location = (300, 0)

    # Handle different Blender versions (5.x moved properties to node inputs)
    if hasattr(glare, 'glare_type'):
        glare.glare_type = 'FOG_GLOW'
        glare.quality = 'HIGH'
        glare.size = 6
        glare.threshold = 3.0  # Higher threshold = only brightest lights glow
        glare.mix = -0.9       # -1 is original, 0 is 50/50; keep effect subtle
    else:
        if 'Type' in glare.inputs:
            try: glare.inputs['Type'].default_value = 'FOG_GLOW'
            except: pass
        if 'Quality' in glare.inputs:
            try: glare.inputs['Quality'].default_value = 'HIGH'
            except: pass
        if 'Size' in glare.inputs:
            try: glare.inputs['Size'].default_value = 6
            except: pass
        if 'Threshold' in glare.inputs:
            try: glare.inputs['Threshold'].default_value = 3.0
            except: pass
        if 'Mix' in glare.inputs:
            try: glare.inputs['Mix'].default_value = -0.9
            except: pass

    # 3. Lens Distortion (chromatic aberration + film grain)
    lens_dist = tree.nodes.new(type="CompositorNodeLensdist")
    lens_dist.location = (600, 0)

    if 'Dispersion' in lens_dist.inputs:
        try: lens_dist.inputs['Dispersion'].default_value = 0.01
        except: pass

    if hasattr(lens_dist, 'use_project'):
        lens_dist.use_project = True
        lens_dist.use_jitter = True
    else:
        if 'Project' in lens_dist.inputs:
            try: lens_dist.inputs['Project'].default_value = True
            except: pass
        elif 'Use Project' in lens_dist.inputs:
            try: lens_dist.inputs['Use Project'].default_value = True
            except: pass

        if 'Jitter' in lens_dist.inputs:
            try: lens_dist.inputs['Jitter'].default_value = True
            except: pass
        elif 'Use Jitter' in lens_dist.inputs:
            try: lens_dist.inputs['Use Jitter'].default_value = True
            except: pass

    # 4. Composite (output)
    try:
        comp = tree.nodes.new(type="CompositorNodeComposite")
    except RuntimeError:
        # Blender 5.0+ uses NodeGroupOutput
        comp = tree.nodes.new(type="NodeGroupOutput")
        if not tree.interface.items_tree:
            tree.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')

    comp.location = (900, 0)

    links = tree.links

    if 'Image' in render_layers.outputs and 'Image' in glare.inputs:
        links.new(render_layers.outputs['Image'], glare.inputs['Image'])

    if 'Image' in glare.outputs and 'Image' in lens_dist.inputs:
        links.new(glare.outputs['Image'], lens_dist.inputs['Image'])

    out_name = 'Image' if 'Image' in comp.inputs else comp.inputs[0].name if len(comp.inputs) > 0 else None
    if out_name and 'Image' in lens_dist.outputs:
        links.new(lens_dist.outputs['Image'], comp.inputs[out_name])

    print("  Compositor configured:")
    print("    - Glare/Fog Glow effect added")
    print("    - Chromatic aberration added (Lens Distortion -> Dispersion)")
    print("    - Film grain added (Lens Distortion -> Jitter)")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  CINEMATIC POST-FX SETUP")
    print("="*50)
    setup_cinematic_compositor()
    print("\n  DONE!")
    print("  On the next render (F12) the compositor will apply grain,")
    print("  beautiful glow on bright objects and realistic lens distortion.")
    print("="*50)
