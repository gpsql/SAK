import bpy

tree = bpy.data.node_groups.new(name="TestTree", type="CompositorNodeTree")
glare = tree.nodes.new(type="CompositorNodeGlare")

print("PROPERTIES OF GLARE NODE:")
for p in dir(glare):
    print(p)
