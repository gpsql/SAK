import bpy
import math
import os

# Ścieżka do lab08 jako zastępstwo lab07, żeby mieć dostęp do rośliny
SCIEZKA_LAB07 = r"/Users/liputer/education/3 rok/SAK/Lab11/roslina_lab08.blend"
NAZWA_KOLEKCJI = "Roslina_Hero"

KLATKA_START = 1
KLATKA_KONIEC = 125
FPS = 25

def importuj_rosline(sciezka_blend, nazwa_kolekcji):
    """
    Importuje kolekcję z innego pliku .blend.
    Po wywołaniu obiekty są dodane do bieżącej sceny.
    """
    sciezka_kolekcji = os.path.join(sciezka_blend, "Collection", nazwa_kolekcji)
    bpy.ops.wm.append(
        filepath=sciezka_kolekcji,
        directory=os.path.join(sciezka_blend, "Collection"),
        filename=nazwa_kolekcji,
    )

def wyczysc_animacje(obj):
    """Usuwa wszystkie F-Curves z obiektu (jeśli istnieją)."""
    if obj.animation_data and obj.animation_data.action:
        obj.animation_data.action = None

def animuj_lisc(obj, faza, czestosc=0.05, amplituda=0.3, klatka_start=1, klatka_koniec=125):
    """
    Wstawia keyframes na rotation_euler.y dla obiektu liścia.
    Krzywa sinusoidalna z indywidualną fazą.
    """
    wyczysc_animacje(obj)  # idempotencja
    
    # Ensure Euler rotation
    if obj.rotation_mode != 'XYZ':
        obj.rotation_mode = 'XYZ'
        
    rotacja_bazowa_y = obj.rotation_euler[1]
    for klatka in range(klatka_start, klatka_koniec + 1):
        kat = rotacja_bazowa_y + amplituda * math.sin(klatka * czestosc + faza)
        obj.rotation_euler[1] = kat
        obj.keyframe_insert(data_path="rotation_euler", frame=klatka, index=1)

def animuj_wszystkie_liscie(prefix_nazwy="RoslinaLisc"):
    """
    Znajduje wszystkie obiekty zaczynające się od `prefix_nazwy`
    i animuje każdy z indywidualną fazą.
    """
    liscie = [obj for obj in bpy.data.objects if obj.name.startswith(prefix_nazwy)]
    for i, lisc in enumerate(liscie):
        faza_lisc = i * (2 * math.pi / max(len(liscie), 1))  # rozłożenie po pełnym okresie
        animuj_lisc(lisc, faza=faza_lisc, klatka_start=KLATKA_START, klatka_koniec=KLATKA_KONIEC)
    print(f"Zaanimowano {len(liscie)} liści.")

def animuj_pak(nazwa_obj="Roslina_Pak", klatka_start=30, klatka_koniec=90,
               skala_min=0.1, skala_max=1.0):
    obj = bpy.data.objects.get(nazwa_obj)
    if obj is None:
        print(f"Obiekt '{nazwa_obj}' nie istnieje. Pomijam animację pąka.")
        print(f"Dostępne obiekty: {[o.name for o in bpy.data.objects]}")
        return

    wyczysc_animacje(obj)

    obj.scale = (skala_min, skala_min, skala_min)
    obj.keyframe_insert(data_path="scale", frame=KLATKA_START)
    obj.keyframe_insert(data_path="scale", frame=klatka_start)

    obj.scale = (skala_max, skala_max, skala_max)
    obj.keyframe_insert(data_path="scale", frame=klatka_koniec)
    obj.keyframe_insert(data_path="scale", frame=KLATKA_KONIEC)

def ustaw_scene():
    bpy.context.scene.frame_start = KLATKA_START
    bpy.context.scene.frame_end = KLATKA_KONIEC
    bpy.context.scene.render.fps = FPS
    
    # Render .mp4 z włączonym Bloom
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    
    # Fallback if next is not available
    if not hasattr(bpy.context.scene.eevee, "use_bloom"):
        try:
             bpy.context.scene.eevee.use_bloom = True
        except:
             pass

def ustaw_kamere_i_swiatlo():
    # Sprawdz czy mamy kamere
    kamera = next((obj for obj in bpy.data.objects if obj.type == 'CAMERA'), None)
    if not kamera:
        bpy.ops.object.camera_add(location=(0, -8, 3), rotation=(math.radians(75), 0, 0))
        kamera = bpy.context.active_object
        kamera.name = "MainCamera"
    bpy.context.scene.camera = kamera

    # Sprawdz czy mamy swiatlo
    swiatla = [obj for obj in bpy.data.objects if obj.type == 'LIGHT']
    if not swiatla:
        bpy.ops.object.light_add(type='SUN', location=(5, -5, 5))
        swiatlo = bpy.context.active_object
        swiatlo.data.energy = 2.0
        
        bpy.ops.object.light_add(type='AREA', location=(-5, -5, 2))
        swiatlo2 = bpy.context.active_object
        swiatlo2.data.energy = 50.0

if __name__ == "__main__" or True:
    ustaw_scene()
    
    # Tylko jeśli nie ma kolekcji, zaimportuj
    if NAZWA_KOLEKCJI not in bpy.data.collections:
        importuj_rosline(SCIEZKA_LAB07, NAZWA_KOLEKCJI)
        
    ustaw_kamere_i_swiatlo()
    animuj_wszystkie_liscie()
    animuj_pak()
    
    # Save blend file
    bpy.ops.wm.save_as_mainfile(filepath="/Users/liputer/education/3 rok/SAK/Lab11/roslina_ozywiona11.blend")
    print("Skrypt zakończony.")
