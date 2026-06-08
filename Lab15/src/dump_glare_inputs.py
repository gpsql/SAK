import bpy
tree = bpy.data.node_groups.new(name="TestTree", type="CompositorNodeTree")
glare = tree.nodes.new(type="CompositorNodeGlare")
with open("/Users/artur/BlenderProjects/City3D/glare_inputs.txt", "w") as f:
    for i in glare.inputs:
        f.write(f"INPUT: {i.name}\n")
    for prop in dir(glare):
        f.write(f"PROP: {prop}\n")
