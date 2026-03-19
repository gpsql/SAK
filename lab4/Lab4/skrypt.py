import bpy
import math
import os

#materialy:
def stworz_material_lodyga(nazwa="Lodyga"):
    #metaliczny brąz/miedź dla łodygi
    mat = bpy.data.materials.new(name=nazwa)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.55, 0.27, 0.07, 1.0)  # brąz
    bsdf.inputs["Metallic"].default_value = 0.9
    bsdf.inputs["Roughness"].default_value = 0.25
    return mat

def stworz_material_lisc(nazwa="Lisc"):
    #syntetyczna zieleń / cyan z lekką emisją
    mat = bpy.data.materials.new(name=nazwa)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.05, 0.85, 0.55, 1.0)  # cyan-zieleń
    bsdf.inputs["Metallic"].default_value = 0.3
    bsdf.inputs["Roughness"].default_value = 0.4
    #emisja- lekki poświat
    bsdf.inputs["Emission Color"].default_value = (0.05, 0.85, 0.55, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 0.3
    return mat

def stworz_material_korzen(nazwa="Korzen"):
    #ciemny metal/ rdza dla korzeni
    mat = bpy.data.materials.new(name=nazwa)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.25, 0.10, 0.05, 1.0)  # ciemna rdza
    bsdf.inputs["Metallic"].default_value = 0.7
    bsdf.inputs["Roughness"].default_value = 0.6
    return mat

#czesci rosliny:
def stworz_lodyge(wysokosc: float, mat: bpy.types.Material) -> bpy.types.Object:
    #cylinder-lodyge o podanej wysokosci
    bpy.ops.mesh.primitive_cylinder_add(
        radius=0.08,
        depth=1.0,
        location=(0, 0, wysokosc / 2)
    )
    obj = bpy.context.active_object
    obj.name = "Lodyga"
    obj.scale.z = wysokosc #skalowanie
    obj.data.materials.append(mat)
    return obj

def stworz_liscie(
    wysokosc: float,
    liczba_lisci: int,
    promien_lisci: float,
    mat: bpy.types.Material
) -> list:
    #liscie uzywajac instancingu, liscie wspoldzela jeden mesh
    obiekty = []
    #krok1: jeden bazowy lisc (wzorzec) 
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    baza = bpy.context.active_object
    baza.name = "Lisc_baza"
    baza.scale = (promien_lisci * 0.8, promien_lisci * 0.3, promien_lisci * 0.5)
    baza.data.materials.append(mat)
 
    #krok2: dla kazdego liscia – linked duplicate 
    for i in range(liczba_lisci):
        kat = (2 * math.pi / liczba_lisci) * i
        x = math.cos(kat) * promien_lisci * 1.4
        y = math.sin(kat) * promien_lisci * 1.4
        z = wysokosc * 0.85
 
        if i == 0:
            #pierwsza instancja to sam wzorzec- tylko ustawic pozycje
            instancja = baza
        else:
            #duplicate_linked= nowy obiekt, ale ten sam blok mesh
            bpy.ops.object.select_all(action='DESELECT')
            baza.select_set(True)
            bpy.context.view_layer.objects.active = baza
            bpy.ops.object.duplicate(linked=True)
            instancja = bpy.context.active_object
 
        instancja.name = f"Lisc_{i}"
        instancja.location = (x, y, z)
        instancja.rotation_euler = (
            math.radians(-20),
            math.radians(0),
            kat
        )
        obiekty.append(instancja)
 
    return obiekty
 
def stworz_korzenie(
    liczba_korzeni: int,
    mat: bpy.types.Material
) -> list:
    #tworzy korzenie rozłożone wokol podstawy łodygi
    obiekty = []
    for i in range(liczba_korzeni):
        kat = (2 * math.pi / liczba_korzeni) * i
        r = 0.35                 # odleglosc od osi
        x = math.cos(kat) * r
        y = math.sin(kat) * r
        z = 0.05                 # tuż przy ziemi
 
        bpy.ops.mesh.primitive_cube_add(location=(x, y, z))
        korzen = bpy.context.active_object
        korzen.name = f"Korzen_{i}"
 
        # Skala- cienki, wydluzony korzen
        korzen.scale = (0.06, 0.06, 0.12)
 
        # Rotacja – odchylenie na zewnątrz
        korzen.rotation_euler = (
            math.radians(30),
            0,
            kat
        )
 
        korzen.data.materials.append(mat)
        obiekty.append(korzen)
    return obiekty

#glowna funkcja rosliny
def stworz_rosline(
    wysokosc: float = 2.0,
    liczba_lisci: int = 3,
    promien_lisci: float = 0.3,
    liczba_korzeni: int = 4,
    przesuniecie_x: float = 0.0
) -> list:
    mat_lodyga = stworz_material_lodyga(f"Lodyga_{przesuniecie_x}")
    mat_lisc   = stworz_material_lisc(f"Lisc_{przesuniecie_x}")
    mat_korzen = stworz_material_korzen(f"Korzen_{przesuniecie_x}")
 
    czesci = []
 
    # lodyga
    lodyga = stworz_lodyge(wysokosc, mat_lodyga)
    lodyga.location.x = przesuniecie_x
    czesci.append(lodyga)
 
    # liscie
    for lisc in stworz_liscie(wysokosc, liczba_lisci, promien_lisci, mat_lisc):
        lisc.location.x += przesuniecie_x
        czesci.append(lisc)
 
    # korzenie
    for korzen in stworz_korzenie(liczba_korzeni, mat_korzen):
        korzen.location.x += przesuniecie_x
        czesci.append(korzen)
 
    return czesci

#scena
def przygotuj_scene():
    #Usuwa wszystkie domyslne obiekty przed generowaniem
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
 

def dodaj_oswietlenie():
    #Dodaje słońce i miękkie wypełnienie
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 8))
    slonce = bpy.context.active_object
    slonce.data.energy = 4.0
    slonce.rotation_euler = (math.radians(45), 0, math.radians(30))
 
    bpy.ops.object.light_add(type='AREA', location=(-3, 3, 5))
    wypelnienie = bpy.context.active_object
    wypelnienie.data.energy = 200
    wypelnienie.data.color = (0.6, 0.9, 1.0) #chłodne wypelnienie
 
 
def dodaj_kamere():
    #ustawia kamere patrzaca na srodek sceny
    bpy.ops.object.camera_add(location=(0, -14, 9))
    kamera = bpy.context.active_object
    kamera.rotation_euler = (
        math.radians(65),
        0,
        math.radians(0)
    )
    bpy.context.scene.camera = kamera
 
 
def renderuj(sciezka: str = "roslinaBiomechaniczna.png"):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'         #blender 5.x
    scene.render.resolution_x = 800
    scene.render.resolution_y = 600
    
    
    blend_dir = os.path.dirname(bpy.data.filepath)
    if not blend_dir:
        blend_dir = os.path.expanduser("~/Downloads")
    pelna_sciezka = os.path.join(blend_dir, sciezka)
 
    scene.render.filepath = pelna_sciezka
    scene.render.image_settings.file_format = 'PNG'
 
    bpy.ops.render.render(write_still=True)
    print(f"Render zapisany: {pelna_sciezka}")

#punkt wejscia
if __name__ == "__main__":
    #1 wczysc scene
    przygotuj_scene()
 
    #2 generuj trzy rosliny obok sieboe
    stworz_rosline(
        wysokosc=1.0,
        liczba_lisci=3,
        promien_lisci=0.18,
        liczba_korzeni=3,
        przesuniecie_x=-3.0 #mala-lewa
    )
 
    stworz_rosline(
        wysokosc=2.2,
        liczba_lisci=5,
        promien_lisci=0.30,
        liczba_korzeni=4,
        przesuniecie_x=0.0 #srednia-srodek
    )
 
    stworz_rosline(
        wysokosc=3.8,
        liczba_lisci=7,
        promien_lisci=0.45,
        liczba_korzeni=6,
        przesuniecie_x=3.5 #duza-prawa
    )
    
    #3 oswietlenie i kamera
    dodaj_oswietlenie()
    dodaj_kamere()
 
    #4 render
    renderuj("Roslina.png")
