import bpy

props = dir(bpy.context.scene)
with open("/Users/artur/BlenderProjects/City3D/scene_props.txt", "w") as f:
    for p in props:
        f.write(p + "\n")
