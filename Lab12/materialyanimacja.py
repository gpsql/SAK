import bpy
import math

# --- Stałe konfiguracyjne ---
NAZWA_MATERIALU = "Roslina_Bioluminescencja"
NAZWA_MATERIALU_STARA = "Mat_Bioluminescence"  # Nazwa z pliku roslina_ozywiona11.blend
NAZWA_NODE_EMISSION = "Emission"

KLATKA_START = 1
KLATKA_KONIEC = 125
KLATKA_PAK_START = 30
KLATKA_PAK_KONIEC = 90

# Kolory emisji (RGBA)
KOLOR_START = (0.0, 0.7, 1.0, 1.0)   # Chłodny błękit
KOLOR_KONIEC = (0.2, 1.0, 0.4, 1.0)  # Ciepły zielony

def clamp(val, min_val, max_val):
    """Pomocnicza funkcja do ograniczania wartości."""
    return max(min_val, min(max_val, val))

def lerp(a, b, t):
    """Pomocnicza funkcja do interpolacji liniowej."""
    return a + (b - a) * t

def znajdz_node(mat, nazwa, typ_zapasowy=None):
    """
    Zwraca węzeł w materiale po jego nazwie. 
    W razie braku szuka po typie jako fallback.
    Zwraca czytelny błąd w przypadku niepowodzenia.
    """
    node = mat.node_tree.nodes.get(nazwa)
    if node is None and typ_zapasowy:
        for n in mat.node_tree.nodes:
            if n.type == typ_zapasowy:
                print(f"Nie znaleziono węzła o nazwie '{nazwa}', używam '{n.name}' (typ {typ_zapasowy}).")
                return n
    if node is None:
        dostepne = [n.name for n in mat.node_tree.nodes]
        raise KeyError(f"Węzeł '{nazwa}' nie istnieje w '{mat.name}'. Dostępne węzły: {dostepne}")
    return node

def wyczysc_animacje_materialu(mat):
    """
    Usuwa animacje (F-Curves) z drzewa węzłów materiału.
    Zapewnia idempotencję skryptu.
    """
    if mat.node_tree.animation_data and mat.node_tree.animation_data.action:
        mat.node_tree.animation_data.action = None
        print(f"Wyczyszczono istniejącą animację w materialu: {mat.name}")

def pulsuj_emission(mat, min_str=0.5, max_str_bazowy=2.0, max_str_pik=6.0, okres=25):
    """
    Animuje pulsowanie sinusoidalne siły emisji (Emission Strength) przez 125 klatek.
    Amplituda wzmacnia się płynnie w przedziale otwierania pąka (klatki 30..90)
    za pomocą funkcji smoothstep (zaawansowana interpolacja nieliniowa).
    """
    emission = znajdz_node(mat, NAZWA_NODE_EMISSION, typ_zapasowy='EMISSION')
    sciezka = f'nodes["{emission.name}"].inputs["Strength"].default_value'

    for klatka in range(KLATKA_START, KLATKA_KONIEC + 1):
        # Zaawansowana synchronizacja: płynne narastanie piku (smoothstep) zamiast liniowego
        t_val = clamp((klatka - KLATKA_PAK_START) / (KLATKA_PAK_KONIEC - KLATKA_PAK_START), 0.0, 1.0)
        s = t_val * t_val * (3.0 - 2.0 * t_val)  # Smoothstep
        max_str = lerp(max_str_bazowy, max_str_pik, s)

        srednia = (min_str + max_str) / 2.0
        amplituda = (max_str - min_str) / 2.0
        t = (klatka - KLATKA_START) * (2 * math.pi / okres)
        
        emission.inputs["Strength"].default_value = srednia + amplituda * math.sin(t)
        mat.node_tree.keyframe_insert(data_path=sciezka, frame=klatka)
    print("Pomyślnie zanimowano pulsowanie Emission Strength.")

def animuj_kolor_emisji(mat):
    """
    Animuje zmianę koloru emisji od chłodnego błękitu do ciepłego zielonego.
    Klatka startowa to niebieski, klatka końcowa to zielony.
    """
    emission = znajdz_node(mat, NAZWA_NODE_EMISSION, typ_zapasowy='EMISSION')
    sciezka = f'nodes["{emission.name}"].inputs["Color"].default_value'

    # Klatka startowa
    emission.inputs["Color"].default_value = KOLOR_START
    mat.node_tree.keyframe_insert(data_path=sciezka, frame=KLATKA_START)
    
    # Klatka końcowa
    emission.inputs["Color"].default_value = KOLOR_KONIEC
    mat.node_tree.keyframe_insert(data_path=sciezka, frame=KLATKA_KONIEC)
    print("Pomyślnie zanimowano zmianę koloru emisji.")

def animuj_subsurface(mat):
    """
    Animuje współczynnik Subsurface Weight w pąku rosliny w klatkach 30..90.
    Pąk staje się bardziej 'organiczny' i 'żywy' wizualnie wraz z rozkwitem.
    """
    bsdf = znajdz_node(mat, "Principled BSDF", typ_zapasowy='BSDF_PRINCIPLED')
    
    # Wyszukanie odpowiedniego gniazda (kompatybilność z różnymi wersjami Blendera)
    input_name = "Subsurface Weight"
    if input_name not in bsdf.inputs:
        for inp in bsdf.inputs:
            if "Subsurface" in inp.name:
                input_name = inp.name
                break
                
    if input_name not in bsdf.inputs:
        print("Nie znaleziono wejścia Subsurface w Principled BSDF, pomijam.")
        return

    sciezka = f'nodes["{bsdf.name}"].inputs["{input_name}"].default_value'
    
    for klatka in range(KLATKA_START, KLATKA_KONIEC + 1):
        t_val = clamp((klatka - KLATKA_PAK_START) / (KLATKA_PAK_KONIEC - KLATKA_PAK_START), 0.0, 1.0)
        s = t_val * t_val * (3.0 - 2.0 * t_val)  # Smoothstep
        sub_weight = lerp(0.1, 0.8, s)
        
        bsdf.inputs[input_name].default_value = sub_weight
        mat.node_tree.keyframe_insert(data_path=sciezka, frame=klatka)
    print(f"Pomyślnie zanimowano {input_name} (Subsurface).")

def animuj_tlo_swiata():
    """
    Animuje tło świata w sposób zsynchronizowany z rośliną.
    Tło ściemnia się, gdy roślina świeci najmocniej (zwiększenie kontrastu).
    """
    world = bpy.data.worlds.get("World")
    if not world:
        # Próba pobrania pierwszego dostępnego świata
        if bpy.data.worlds:
            world = bpy.data.worlds[0]
            
    if not world:
        print("Brak świata w pliku .blend. Pomijam animację tła.")
        return

    world.use_nodes = True
    bg_node = None
    for n in world.node_tree.nodes:
        if n.type == 'BACKGROUND':
            bg_node = n
            break
            
    if not bg_node:
        print("Nie znaleziono węzła typu Background w świecie. Pomijam.")
        return
        
    sciezka = f'nodes["{bg_node.name}"].inputs["Color"].default_value'
    
    # Idempotencja dla animacji tła
    if world.node_tree.animation_data and world.node_tree.animation_data.action:
        world.node_tree.animation_data.action = None
        
    min_bg = 0.005  # Bardzo ciemne tło
    max_bg = 0.06   # Lekko rozjaśnione tło
    
    # Używamy tej samej formuły matematycznej co w pulsowaniu rośliny
    min_str = 0.5
    max_str_bazowy = 2.0
    max_str_pik = 6.0
    okres = 25
    
    for klatka in range(KLATKA_START, KLATKA_KONIEC + 1):
        t_val = clamp((klatka - KLATKA_PAK_START) / (KLATKA_PAK_KONIEC - KLATKA_PAK_START), 0.0, 1.0)
        s = t_val * t_val * (3.0 - 2.0 * t_val)
        max_str = lerp(max_str_bazowy, max_str_pik, s)

        srednia = (min_str + max_str) / 2.0
        amplituda = (max_str - min_str) / 2.0
        t = (klatka - KLATKA_START) * (2 * math.pi / okres)
        strength = srednia + amplituda * math.sin(t)
        
        # Jasność tła jest odwrotnie proporcjonalna do siły świecenia rośliny
        factor = clamp(strength / 9.0, 0.0, 1.0)
        bg_brightness = lerp(max_bg, min_bg, factor)
        
        # Nadajemy tłu głęboki odcień niebiesko-fioletowy
        world.node_tree.nodes[bg_node.name].inputs["Color"].default_value = (
            bg_brightness * 0.8, 
            bg_brightness * 0.8, 
            bg_brightness * 1.2, 
            1.0
        )
        world.node_tree.keyframe_insert(data_path=sciezka, frame=klatka)
    print("Pomyślnie zanimowano tło świata (kontrastowa synchronizacja).")

def main_materialy():
    # Sprawdzamy i ewentualnie zmieniamy nazwę ze starej na wymaganą
    mat = bpy.data.materials.get(NAZWA_MATERIALU)
    if mat is None:
        mat_stara = bpy.data.materials.get(NAZWA_MATERIALU_STARA)
        if mat_stara:
            mat_stara.name = NAZWA_MATERIALU
            mat = mat_stara
            print(f"Zmieniono nazwę materiału z '{NAZWA_MATERIALU_STARA}' na '{NAZWA_MATERIALU}' w celu zgodności z zadaniem.")
            
    if mat is None:
        print(f"Brak materiału '{NAZWA_MATERIALU}'. Dostępne materiały: {[m.name for m in bpy.data.materials]}")
        return
        
    wyczysc_animacje_materialu(mat)
    pulsuj_emission(mat)
    animuj_kolor_emisji(mat)
    animuj_subsurface(mat)
    animuj_tlo_swiata()
    print("=== Animacja materiałów zakończona sukcesem! ===")
    
    # Zapisujemy zmiany w pliku blend
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print("Plik blend został zapisany.")

if __name__ == "__main__":
    main_materialy()
