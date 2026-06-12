"""
Lab 13 – Eksport sceny biomechanicznej do biomech13.glb
========================================================
Uruchamiać w Blender: Scripting → Run Script

Zakres eksportu: roślina (Lab07/08) + pająk (Lab10) + reprezentatywne
cząsteczki z kolekcji "Pyl" (Lab12). Animacje shaderów i cząsteczek
Blendera NIE pojadą do .glb – zostaną jako VideoTexture w Lab14.

Przed eksportem skrypt wykonuje:
  1. Apply All Transforms (scale → 1,1,1 dla wszystkich obiektów)
  2. Ustawia czytelne nazwy obiektów (pod raycaster Lab14)
  3. Eksportuje do folderu Lab13/ obok pliku .blend

Dlaczego Apply Scale przed eksportem?
  obj.scale = (2,0,2,0,2,0) w Blenderze oznacza, że wierzchołki
  w danych meshu są w "oryginalnych" jednostkach. Three.js/silniki gier
  oczekują danych już przetransformowanych (scale=1,1,1). Bez Apply Scale
  model może być 100× za duży/mały lub mieć odwrócone normalne.

Dlaczego +Y Up w eksporterze?
  Blender używa osi Z jako "góry" (Z-up). Three.js / WebGL używa Y-up.
  Opcja "Y Up" w eksporterze obraca cały model o -90° X, żeby Z-up
  Blendera odpowiadał Y-up Three.js. Bez tego model "leży na boku".
"""

import bpy
import os
import math

# ─────────────────────────────────────────────────────────────────────────────
# KONFIGURACJA
# ─────────────────────────────────────────────────────────────────────────────

# Katalog Lab13 – folder obok tego pliku .blend
BLEND_DIR = os.path.dirname(bpy.data.filepath)
LAB13_DIR = os.path.join(BLEND_DIR, '..', 'Lab13')
OUTPUT_PATH = os.path.join(LAB13_DIR, 'biomech13.glb')

# Maksymalna liczba cząsteczek do eksportu (ograniczenie rozmiaru pliku)
MAX_CZASTECZKI = 12

# Kolekcje do eksportu (nazwy kolekcji z Lab07/08/10/12)
KOLEKCJE_EKSPORT = [
    'Roslina',       # Lab07/08 – roślina biomechaniczna
    'Pajak',         # Lab10 – pająk
    'Pyl',           # Lab12 – cząsteczki pyłu
    'Scene',         # fallback – główna kolekcja
    'Collection',    # fallback – domyślna kolekcja Blendera
]

# ─────────────────────────────────────────────────────────────────────────────
# POMOCNICZE: NAZEWNICTWO
# ─────────────────────────────────────────────────────────────────────────────

def nadaj_czytelna_nazwe(obj):
    """
    Nadaje obiektowi czytelną, opisową nazwę (potrzebne pod raycaster Lab14).
    Jeśli obiekt nie ma nazwy lub ma nazwę domyślną, generujemy opisową.
    """
    name = obj.name.strip()
    
    # Już mamy dobrą nazwę
    if any(keyword in name.lower() for keyword in [
        'roslina', 'plant', 'lodygla', 'lisc', 'pak', 'kwiat', 'korzen',
        'pajak', 'spider', 'noga', 'oko', 'tulów', 'odwłok',
        'czasteczka', 'pyl', 'spory', 'swietlik',
        'ground', 'podloze', 'teren',
    ]):
        return name  # nazwa już jest opisowa

    # Generujemy nazwę na podstawie typu obiektu i kolekcji
    collections = [c.name for c in obj.users_collection]
    
    if obj.type == 'MESH':
        col_prefix = collections[0].replace(' ', '_') if collections else 'Mesh'
        obj.name = f'{col_prefix}_{obj.type}_{obj.name}'
    
    return obj.name


def loguj_hierarchie():
    """Wypisuje hierarchię sceny do konsoli – diagnostyka przed eksportem."""
    print('\n=== HIERARCHIA SCENY DO EKSPORTU ===')
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            kolekcje = [c.name for c in obj.users_collection]
            scale_ok = all(abs(s - 1.0) < 0.01 for s in obj.scale)
            print(f'  [MESH] {obj.name:40s} | skala: {tuple(round(s,3) for s in obj.scale)} {"✓" if scale_ok else "⚠ UWAGA: Apply Scale!"}')


# ─────────────────────────────────────────────────────────────────────────────
# APPLY TRANSFORMS
# ─────────────────────────────────────────────────────────────────────────────

def apply_transforms_all():
    """
    Zastosuj ("wpiecz") wszystkie transformacje dla wybranych obiektów mesh.
    
    Dlaczego to ważne?
    Wartości scale != (1,1,1) powodują:
      - Odwrócone normalne (scale ujemna)
      - Błędne rozmiary w Three.js
      - Problemy z kolizjami i raycastingiem
    
    Apply Transform (Ctrl+A) "wpieka" transformację w dane wierzchołków,
    resetując scale/location/rotation do wartości neutralnych.
    
    UWAGA: Cząsteczki z Lab12 używają Linked Duplicate (współdzielony mesh).
    Blender nie pozwala Apply Scale na multi-user mesh → najpierw make_single_user.
    """
    print('\n--- Stosowanie transformacji (Apply All) ---')

    bpy.ops.object.select_all(action='DESELECT')

    # Krok 1: make_single_user dla wszystkich mesh-ów
    # (naprawia błąd "Cannot apply to a multi user" przy Linked Duplicates)
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        if obj.data and obj.data.users > 1:
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            # Skopiuj dane meshu – każdy obiekt dostaje własną kopię
            obj.data = obj.data.copy()
            obj.select_set(False)
            print(f'  → Single-user: {obj.name}')

    bpy.ops.object.select_all(action='DESELECT')

    # Krok 2: Apply Transforms dla każdego obiektu
    count = 0
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        needs_apply = any(abs(s - 1.0) > 0.001 for s in obj.scale)

        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        try:
            bpy.ops.object.transform_apply(
                location=False,
                rotation=True,
                scale=True,
            )
            if needs_apply:
                print(f'  ✓ Apply: {obj.name}')
                count += 1
        except RuntimeError as e:
            print(f'  ⚠ Pominięto {obj.name}: {e}')

        obj.select_set(False)

    print(f'  Zastosowano transformacje dla {count} obiektów.')


# ─────────────────────────────────────────────────────────────────────────────
# SELEKCJA OBIEKTÓW DO EKSPORTU
# ─────────────────────────────────────────────────────────────────────────────

def wybierz_obiekty_do_eksportu():
    """
    Wybiera obiekty do eksportu:
      - Wszystkie mesh-y z kolekcji wymienionych w KOLEKCJE_EKSPORT
      - Limituje cząsteczki do MAX_CZASTECZKI (kontrola rozmiaru pliku)
      - Pomija obiekty "pomocnicze" (kamery render, rig bones itp.)
    
    Returns:
        int: liczba wybranych obiektów
    """
    bpy.ops.object.select_all(action='DESELECT')
    
    czasteczki_count = 0
    selected = []
    
    for obj in bpy.data.objects:
        if obj.type not in ('MESH', 'EMPTY'):
            continue
        
        # Filtruj po kolekcji
        obj_collections = {c.name for c in obj.users_collection}
        
        # Sprawdź czy należy do jednej z kolekcji eksportu
        nalezacy = any(
            any(kol.lower() in c.lower() or c.lower() in kol.lower() 
                for kol in KOLEKCJE_EKSPORT)
            for c in obj_collections
        )
        
        # Fallback: jeśli żadna kolekcja nie pasuje, bierzemy wszystkie mesh-y
        if not obj_collections or not nalezacy:
            # Sprawdź czy to nie jest obiekt pomocniczy
            if obj.hide_render or obj.hide_viewport:
                continue
            # Weź mesh jeśli należy do głównej sceny
            if 'czasteczka' in obj.name.lower() or 'pyl' in obj.name.lower():
                # Ograniczenie liczby cząsteczek
                if czasteczki_count >= MAX_CZASTECZKI:
                    continue
                czasteczki_count += 1
            nalezacy = True
        
        # Limitowanie cząsteczek
        if any(keyword in obj.name.lower() for keyword in ['czasteczka', 'pyl', 'spory', 'swietlik']):
            if czasteczki_count >= MAX_CZASTECZKI:
                print(f'  ⚠ Pomijam (limit cząsteczek): {obj.name}')
                continue
            czasteczki_count += 1
        
        if nalezacy:
            # Nadaj czytelną nazwę
            nadaj_czytelna_nazwe(obj)
            obj.select_set(True)
            selected.append(obj.name)
    
    print(f'\n--- Wybrano {len(selected)} obiektów do eksportu ---')
    for name in selected[:20]:  # Pokaż pierwsze 20
        print(f'  • {name}')
    if len(selected) > 20:
        print(f'  ... i {len(selected) - 20} więcej')
    
    return len(selected)


# ─────────────────────────────────────────────────────────────────────────────
# EKSPORT glTF 2.0
# ─────────────────────────────────────────────────────────────────────────────

def eksportuj_glb(output_path, only_selected=True):
    """
    Eksportuje scenę do formatu glTF 2.0 (.glb – binary packed).
    
    Kluczowe opcje eksportera Blender → glTF:
    
      export_yup=True
        Obraca scenę, żeby Z-up Blendera → Y-up Three.js/WebGL.
        Bez tego model "leży na boku" w przeglądarce.
    
      export_apply=True
        Aplikuje modyfikatory geometrii (Subdivision Surface, Mirror itp.)
        przed eksportem. UWAGA: eksportuje "finalną" geometrię, nie editable.
        Ważne dla Subdivision Surface – redukuj poziomy przed eksportem!
    
      export_materials='EXPORT'
        Eksportuje materiały PBR (Principled BSDF → glTF PBR Material).
        Emission nodes → emissiveFactor w glTF.
    
      use_selection=True
        Eksportuje tylko zaznaczone obiekty (kontrolujemy selekcję powyżej).
    
      export_animations=False
        Animacje Blendera (keyframes shaderów i cząsteczek) NIE pojadą
        do glTF – wracają w Lab14 jako VideoTexture. Animowane transformacje
        (armature) można eksportować (True), ale tu nie mamy rigu.
    
    Dlaczego .glb a nie .gltf?
      .glb = "GL Binary" – wszystko (JSON + bufory + tekstury) w jednym
      pliku binarnym. Łatwiejsze do wczytania przez fetch() / GLTFLoader.
      .gltf = oddzielne pliki JSON + .bin + textury – wygodne do edycji.
      "JPG dla 3D" = glTF bo jest kompaktowy i powszechnie obsługiwany.
    """
    
    # Utwórz folder docelowy jeśli nie istnieje
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f'\n--- Eksport glTF 2.0 → {output_path} ---')
    
    bpy.ops.export_scene.gltf(
        filepath=output_path,
        
        # Format wyjściowy
        export_format='GLB',           # Binary packed (.glb)
        
        # Zakres eksportu
        use_selection=only_selected,   # Tylko zaznaczone obiekty
        use_visible=True,              # Tylko widoczne
        use_renderable=True,           # Tylko renderowalne
        
        # Transformacje
        export_yup=True,               # ← KLUCZOWE: Z-up Blender → Y-up Three.js
        export_apply=True,             # Aplikuj modyfikatory geometrii
        
        # Materiały
        export_materials='EXPORT',     # PBR: Principled BSDF → glTF PBR
        
        # Tekstury
        export_image_format='AUTO',    # PNG dla przezroczystości, JPG dla reszty
        
        # Animacje – wyłączone (wrócą w Lab14 jako VideoTexture)
        export_animations=False,
        
        # Kamera i oświetlenie – nie eksportujemy (Three.js ma własne)
        export_cameras=False,
        export_lights=False,
        
        # Dodatkowe dane geometrii
        export_normals=True,
        export_texcoords=True,
        export_tangents=False,         # Oszczędność rozmiaru pliku
        
        # Draco kompresja – opcjonalnie (wymaga pluginu w Three.js DRACOLoader)
        export_draco_mesh_compression_enable=False,
    )
    
    # Sprawdź rozmiar pliku
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / 1024 / 1024
        print(f'\n✓ Eksport zakończony pomyślnie!')
        print(f'  Plik: {output_path}')
        print(f'  Rozmiar: {size_mb:.2f} MB')
        
        if size_mb > 10:
            print('\n  ⚠ UWAGA: Plik > 10 MB!')
            print('  Przyczyny: za dużo cząsteczek lub nieuproszczony Subdivision Surface.')
            print('  Rozwiązanie: zmniejsz liczbę cząsteczek lub obniż Subdivision levels.')
        elif size_mb > 2:
            print('  ℹ Plik duży (>2 MB) – rozważ optymalizację.')
        else:
            print('  ✓ Rozmiar optymalny (< 2 MB).')
    else:
        print('\n✗ BŁĄD: Plik nie został utworzony!')


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print('=' * 60)
    print('Lab 13 – Eksport Biomech World → biomech13.glb')
    print('=' * 60)
    
    # Sprawdź czy plik .blend jest zapisany
    if not bpy.data.filepath:
        print('\n✗ BŁĄD: Plik .blend nie jest zapisany!')
        print('  Zapisz plik (Ctrl+S) i uruchom skrypt ponownie.')
        return
    
    # 1. Wyświetl aktualną hierarchię sceny
    loguj_hierarchie()
    
    # 2. Apply All Transforms (scale=1 dla wszystkich)
    apply_transforms_all()
    
    # 3. Wybierz obiekty do eksportu
    count = wybierz_obiekty_do_eksportu()
    
    if count == 0:
        print('\n⚠ Brak obiektów do eksportu!')
        print('  Sprawdź nazwy kolekcji w KOLEKCJE_EKSPORT.')
        print(f'  Szukam: {KOLEKCJE_EKSPORT}')
        print('  Eksportuję całą scenę jako fallback...')
        bpy.ops.object.select_all(action='SELECT')
    
    # 4. Eksport
    eksportuj_glb(OUTPUT_PATH, only_selected=(count > 0))
    
    print('\n=== GOTOWE ===')
    print(f'Skopiuj biomech13.glb do folderu Lab13/ i otwórz index.html przez Live Server.')


if __name__ == '__main__':
    main()
