import bpy
with open("compositor_nodes.txt", "w") as f:
    for k in dir(bpy.types):
        if "CompositorNode" in k:
            f.write(k + "\n")
