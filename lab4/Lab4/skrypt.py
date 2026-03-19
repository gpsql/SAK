import bpy
import math
import os

def czysc_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def stworz_lodyge(wysokosc=2.0, x=0, y=0):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.1, 
        depth=wysokosc, 
        location=(x, y, wysokosc / 2.0)
    )
    lodyga = bpy.context.active_object
    lodyga.name = "Lodyga"
    
    mat = bpy.data.materials.get("Lodyga")
    if not mat:
        mat = bpy.data.materials.new(name="Lodyga")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.2, 0.1, 0.05, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.8
            bsdf.inputs["Roughness"].default_value = 0.4
    lodyga.data.materials.append(mat)
    return lodyga

def stworz_liscie(wysokosc=2.0, liczba_lisci=3, promien_lisci=0.3, x=0, y=0):
    mat = bpy.data.materials.get("Lisc")
    if not mat:
        mat = bpy.data.materials.new(name="Lisc")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (0.0, 0.6, 0.4, 1.0)
            bsdf.inputs["Metallic"].default_value = 0.5
            bsdf.inputs["Roughness"].default_value = 0.3
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (0.0, 0.8, 0.6, 1.0)
                bsdf.inputs["Emission Strength"].default_value = 1.0
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = (0.0, 0.8, 0.6, 1.0)
                if "Emission Strength" in bsdf.inputs:
                    bsdf.inputs["Emission Strength"].default_value = 1.0
                    
    liscie = []
    angle_step = 2 * math.pi / liczba_lisci
    for i in range(liczba_lisci):
        angle = i * angle_step
        r_offset = 0.15
        lx = x + r_offset * math.cos(angle)
        ly = y + r_offset * math.sin(angle)
        lz = wysokosc - 0.1
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(lx, ly, lz))
        lisc = bpy.context.active_object
        lisc.name = "Lisc"
        
        lisc.scale = (promien_lisci, promien_lisci * 0.4, 0.05)
        lisc.rotation_euler = (0, math.radians(45), angle)
        lisc.data.materials.append(mat)
        liscie.append(lisc)
    return liscie

def stworz_korzenie(liczba_korzeni=4, x=0, y=0):
    mat = bpy.data.materials.get("Lodyga")
    korzenie = []
    if liczba_korzeni <= 0: return korzenie
    
    angle_step = 2 * math.pi / liczba_korzeni
    for i in range(liczba_korzeni):
        angle = i * angle_step
        r_offset = 0.12
        kx = x + r_offset * math.cos(angle)
        ky = y + r_offset * math.sin(angle)
        kz = 0.05
        
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(kx, ky, kz))
        korzen = bpy.context.active_object
        korzen.name = "Korzen"
        
        korzen.scale = (0.2, 0.08, 0.08)
        korzen.rotation_euler = (0, math.radians(-30), angle)
        if mat:
            korzen.data.materials.append(mat)
        korzenie.append(korzen)
    return korzenie

def stworz_rosline(wysokosc=2.0, liczba_lisci=3, promien_lisci=0.3, liczba_korzeni=4, offset_x=0.0):
    stworz_lodyge(wysokosc, offset_x, 0)
    stworz_liscie(wysokosc, liczba_lisci, promien_lisci, offset_x, 0)
    stworz_korzenie(liczba_korzeni, offset_x, 0)


if __name__ == "__main__":
    czysc_scene()
    
    stworz_rosline(wysokosc=1.5, liczba_lisci=3, promien_lisci=0.4, liczba_korzeni=3, offset_x=-2.0)
    stworz_rosline(wysokosc=2.5, liczba_lisci=4, promien_lisci=0.5, liczba_korzeni=4, offset_x=0.0)
    stworz_rosline(wysokosc=3.5, liczba_lisci=5, promien_lisci=0.7, liczba_korzeni=5, offset_x=2.0)
    
    bpy.ops.object.light_add(type='SUN', location=(3, -3, 5))
    slonce = bpy.context.active_object
    slonce.data.energy = 3.0
    slonce.rotation_euler = (math.radians(45), 0, math.radians(45))
    
    bpy.ops.object.camera_add(location=(0, -7, 2))
    kamera = bpy.context.active_object
    kamera.rotation_euler = (math.radians(80), 0, 0)
    bpy.context.scene.camera = kamera
    
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lab04_render.png")
    scene.render.filepath = out_path
    scene.render.image_settings.file_format = 'PNG'
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    
    bpy.ops.render.render(write_still=True)
    print("Render zapisany:", out_path)
