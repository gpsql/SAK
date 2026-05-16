import bpy
import math
import os


KATALOG_PROJEKTU = os.path.dirname(os.path.abspath(__file__))
SCIEZKA_LAB07 = os.path.join(KATALOG_PROJEKTU, "roslina_lab08.blend")
SCIEZKA_WYJSCIOWA_BLEND = os.path.join(KATALOG_PROJEKTU, "roslina_ozywiona11.blend")
SCIEZKA_WYJSCIOWA_MP4 = os.path.join(KATALOG_PROJEKTU, "roslina_ozywiona11.mp4")
KATALOG_KLATEK = os.path.join(KATALOG_PROJEKTU, "render_klatki_11")
NAZWA_KOLEKCJI = "Roslina_Hero"

KLATKA_START = 1
KLATKA_KONIEC = 125
FPS = 25


def wyczysc_animacje(obj):
    """Usuwa akcję animacji z obiektu, żeby ponowne uruchomienie skryptu było idempotentne."""
    if obj.animation_data and obj.animation_data.action:
        obj.animation_data.action = None


def usun_domyslne_obiekty():
    """Czyści startową scenę Blendera przed pierwszym importem assetu."""
    if NAZWA_KOLEKCJI in bpy.data.collections:
        return

    for obj in list(bpy.context.scene.objects):
        obj.select_set(True)
    bpy.ops.object.delete()


def importuj_rosline(sciezka_blend, nazwa_kolekcji):
    """
    Importuje kolekcję z innego pliku .blend.
    Po wywołaniu obiekty są dodane do bieżącej sceny.
    """
    if not os.path.exists(sciezka_blend):
        raise FileNotFoundError(f"Nie znaleziono pliku assetu: {sciezka_blend}")

    sciezka_kolekcji = os.path.join(sciezka_blend, "Collection", nazwa_kolekcji)
    bpy.ops.wm.append(
        filepath=sciezka_kolekcji,
        directory=os.path.join(sciezka_blend, "Collection"),
        filename=nazwa_kolekcji,
    )

    kolekcja = bpy.data.collections.get(nazwa_kolekcji)
    if kolekcja and kolekcja.name not in [c.name for c in bpy.context.scene.collection.children]:
        bpy.context.scene.collection.children.link(kolekcja)


def animuj_lisc(obj, faza, czestosc=0.05, amplituda=0.3,
                klatka_start=KLATKA_START, klatka_koniec=KLATKA_KONIEC):
    """
    Wstawia keyframes na rotation_euler.y dla obiektu liścia.
    Krzywa sinusoidalna z indywidualną fazą.
    """
    wyczysc_animacje(obj)
    rotacja_bazowa_y = obj.rotation_euler[1]

    for klatka in range(klatka_start, klatka_koniec + 1):
        kat = rotacja_bazowa_y + amplituda * math.sin(klatka * czestosc + faza)
        obj.rotation_euler[1] = kat
        obj.keyframe_insert(data_path="rotation_euler", frame=klatka, index=1)


def animuj_wszystkie_liscie(prefixy_nazw=("Roslina_Lisc", "RoslinaLisc"),
                            czestosc=0.05, amplituda=0.3):
    """
    Znajduje wszystkie liście po prefixie nazwy i animuje każdy z indywidualną fazą.
    """
    liscie = [
        obj for obj in bpy.data.objects
        if obj.type == "MESH" and any(obj.name.startswith(prefix) for prefix in prefixy_nazw)
    ]
    liscie.sort(key=lambda obj: obj.name)

    for i, lisc in enumerate(liscie):
        faza_lisc = i * (2 * math.pi / max(len(liscie), 1))
        animuj_lisc(lisc, faza=faza_lisc, czestosc=czestosc, amplituda=amplituda)

    print(f"Zaanimowano {len(liscie)} liści: {[obj.name for obj in liscie]}")


def animuj_pak(nazwa_obj="Roslina_Pak", klatka_start=30, klatka_koniec=90,
               skala_min=0.1, skala_max=1.0):
    """Animuje otwieranie pąka przez skalowanie od skala_min do skala_max."""
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
    print(f"Zaanimowano pąk: {obj.name}")


def przygotuj_rig_rosliny(nazwa_rig="Roslina_Rig", nazwa_kolekcji=NAZWA_KOLEKCJI):
    """Tworzy wspólny parent dla całej rośliny, żeby pąk i liście kołysały się razem."""
    rig = bpy.data.objects.get(nazwa_rig)
    if rig is None:
        rig = bpy.data.objects.new(nazwa_rig, None)
        bpy.context.scene.collection.objects.link(rig)

    rig.empty_display_type = "PLAIN_AXES"
    rig.empty_display_size = 0.5
    rig.location = (0.0, 0.0, 0.0)
    rig.rotation_euler = (0.0, 0.0, 0.0)
    rig.scale = (1.0, 1.0, 1.0)

    kolekcja = bpy.data.collections.get(nazwa_kolekcji)
    obiekty = list(kolekcja.objects) if kolekcja else []
    for obj in obiekty:
        if obj == rig or obj.type in {"CAMERA", "LIGHT"}:
            continue
        macierz_swiata = obj.matrix_world.copy()
        obj.parent = rig
        obj.matrix_world = macierz_swiata

    return rig


def animuj_rig_rosliny(nazwa_rig="Roslina_Rig", amplituda=0.05, czestosc=0.025):
    """Dodatkowe delikatne kołysanie całej rośliny dla wariantu rozszerzonego."""
    rig = przygotuj_rig_rosliny(nazwa_rig=nazwa_rig)
    wyczysc_animacje(rig)
    rotacja_bazowa_x = rig.rotation_euler[0]

    for klatka in range(KLATKA_START, KLATKA_KONIEC + 1):
        rig.rotation_euler[0] = rotacja_bazowa_x + amplituda * math.sin(klatka * czestosc)
        rig.keyframe_insert(data_path="rotation_euler", frame=klatka, index=0)
    print(f"Zaanimowano kołysanie całej rośliny: {rig.name}")


def ustaw_kamere_i_swiatlo():
    """Zapewnia kamerę, trójpunktowe światło i Bloom do renderu."""
    kamera = bpy.data.objects.get("PlantCamera") or bpy.data.objects.get("Camera")
    if kamera is None:
        bpy.ops.object.camera_add(location=(0.0, -8.0, 4.2), rotation=(math.radians(62), 0, 0))
        kamera = bpy.context.object
        kamera.name = "PlantCamera"
    bpy.context.scene.camera = kamera

    if bpy.data.objects.get("KeyLight") is None:
        bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.0, 5.0))
        key = bpy.context.object
        key.name = "KeyLight"
        key.data.energy = 450
        key.data.size = 4.0

    if bpy.data.objects.get("FillLight") is None:
        bpy.ops.object.light_add(type="AREA", location=(4.0, -3.0, 3.0))
        fill = bpy.context.object
        fill.name = "FillLight"
        fill.data.energy = 90
        fill.data.size = 5.0

    if bpy.data.objects.get("RimLight") is None:
        bpy.ops.object.light_add(type="POINT", location=(0.0, 3.5, 4.5))
        rim = bpy.context.object
        rim.name = "RimLight"
        rim.data.energy = 160

    bpy.context.scene.render.engine = "BLENDER_EEVEE"
    eevee = getattr(bpy.context.scene, "eevee", None)
    if eevee and hasattr(eevee, "use_bloom"):
        eevee.use_bloom = True
        eevee.bloom_intensity = 0.08

    ustaw_bloom_kompozytora()


def ustaw_bloom_kompozytora():
    """Dodaje efekt poświaty przez compositor, zgodny także z Blenderem 5.x."""
    scena = bpy.context.scene
    scena.use_nodes = True
    scena.render.use_compositing = True

    drzewo = getattr(scena, "node_tree", None)
    if drzewo is None:
        print("Compositor node_tree nie jest dostępny w tej wersji API; pomijam Bloom compositor.")
        return

    drzewo.nodes.clear()

    render_layers = drzewo.nodes.new(type="CompositorNodeRLayers")
    glare = drzewo.nodes.new(type="CompositorNodeGlare")
    composite = drzewo.nodes.new(type="CompositorNodeComposite")

    glare.glare_type = "FOG_GLOW"
    glare.quality = "MEDIUM"
    glare.threshold = 0.75
    glare.size = 6

    render_layers.location = (-300, 0)
    glare.location = (-60, 0)
    composite.location = (180, 0)

    drzewo.links.new(render_layers.outputs["Image"], glare.inputs["Image"])
    drzewo.links.new(glare.outputs["Image"], composite.inputs["Image"])


def ustaw_render():
    os.makedirs(KATALOG_KLATEK, exist_ok=True)
    bpy.context.scene.render.filepath = SCIEZKA_WYJSCIOWA_MP4
    try:
        bpy.context.scene.render.image_settings.file_format = "FFMPEG"
        bpy.context.scene.render.ffmpeg.format = "MPEG4"
        bpy.context.scene.render.ffmpeg.codec = "H264"
        bpy.context.scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    except TypeError:
        print("FFMPEG nie jest dostępny bezpośrednio w tej wersji Blendera; renderuję klatki PNG.")
        bpy.context.scene.render.image_settings.file_format = "PNG"
        bpy.context.scene.render.filepath = os.path.join(KATALOG_KLATEK, "roslina_ozywiona11_")
    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 720
    bpy.context.scene.render.film_transparent = False


def ustaw_scene():
    bpy.context.scene.frame_start = KLATKA_START
    bpy.context.scene.frame_end = KLATKA_KONIEC
    bpy.context.scene.render.fps = FPS
    ustaw_kamere_i_swiatlo()
    ustaw_render()


def zapisz_scene():
    bpy.ops.wm.save_as_mainfile(filepath=SCIEZKA_WYJSCIOWA_BLEND)
    print(f"Zapisano scenę: {SCIEZKA_WYJSCIOWA_BLEND}")


if __name__ == "__main__" or True:
    usun_domyslne_obiekty()
    if NAZWA_KOLEKCJI not in bpy.data.collections:
        importuj_rosline(SCIEZKA_LAB07, NAZWA_KOLEKCJI)
    przygotuj_rig_rosliny()
    ustaw_scene()
    animuj_wszystkie_liscie()
    animuj_pak()
    animuj_rig_rosliny()
    ustaw_scene()
    zapisz_scene()
    print("Skrypt zakończony.")
