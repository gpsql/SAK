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

def animuj_pak(prefix_nazwy="Roslina_Pak", klatka_start=30, klatka_koniec=90,
               skala_min=0.1, skala_max=1.0):
    """
    Asynchroniczne otwieranie wielu pąków (zadanie dla chętnych).
    """
    paki = [obj for obj in bpy.data.objects if obj.name.startswith(prefix_nazwy)]
    if not paki:
        print(f"Brak obiektów zaczynających się od '{prefix_nazwy}'. Pomijam animację pąka.")
        return

    for i, obj in enumerate(paki):
        wyczysc_animacje(obj)
        opoznienie = i * 10
        start = klatka_start + opoznienie
        koniec = klatka_koniec + opoznienie

        obj.scale = (skala_min, skala_min, skala_min)
        obj.keyframe_insert(data_path="scale", frame=KLATKA_START)
        obj.keyframe_insert(data_path="scale", frame=start)

        obj.scale = (skala_max, skala_max, skala_max)
        obj.keyframe_insert(data_path="scale", frame=koniec)
        obj.keyframe_insert(data_path="scale", frame=KLATKA_KONIEC)

def animuj_lodyge(nazwa_obj="Roslina_Lodyga", klatka_start=1, klatka_koniec=125):
    """
    Sinusoidalny ruch całej łodygi (zadanie dla chętnych).
    """
    obj = bpy.data.objects.get(nazwa_obj)
    if not obj:
        return
    wyczysc_animacje(obj)
    if obj.rotation_mode != 'XYZ':
        obj.rotation_mode = 'XYZ'
        
    rotacja_bazowa_y = obj.rotation_euler[1]
    amplituda = 0.05
    czestosc = 0.02
    for klatka in range(klatka_start, klatka_koniec + 1):
        obj.rotation_euler[1] = rotacja_bazowa_y + amplituda * math.sin(klatka * czestosc)
        obj.keyframe_insert(data_path="rotation_euler", frame=klatka, index=1)

def animuj_kamere(kamera, klatka_start=1, klatka_koniec=125, pozycja_start=(0, -8, 3), pozycja_koniec=(0, -4, 4)):
    """
    Animacja kamery przez kod (zadanie dla chętnych).
    """
    wyczysc_animacje(kamera)
    kamera.location = pozycja_start
    kamera.keyframe_insert(data_path="location", frame=klatka_start)
    kamera.location = pozycja_koniec
    kamera.keyframe_insert(data_path="location", frame=klatka_koniec)


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
    animuj_lodyge()
    
    kamera = bpy.context.scene.camera
    if kamera:
        animuj_kamere(kamera, klatka_start=KLATKA_START, klatka_koniec=KLATKA_KONIEC)
    
    # Save blend file
    bpy.ops.wm.save_as_mainfile(filepath="/Users/liputer/education/3 rok/SAK/Lab11/roslinaozywiona11.blend")
    print("Skrypt zakończony.")
