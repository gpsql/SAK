import bpy
for k in bpy.types.__dict__.keys():
    if "Compos" in k:
        print(k)
