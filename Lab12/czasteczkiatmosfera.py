import bpy
import random
import math

# --- Stałe konfiguracyjne ---
NAZWA_KOLEKCJI = "Pyl"
NAZWA_MATERIALU = "Pyl_Mat"

LICZBA_CZASTECZEK = 50
KLATKA_START = 1
KLATKA_KONIEC = 125

CZAS_ZYCIA_MIN = 40
CZAS_ZYCIA_MAX = 80

SREDNICA_CZASTECZKI = 0.04
ZAKRES_EMISJI_XY = (-2.0, 2.0)      # X i Y wokół rośliny
WYSOKOSC_EMISJI_Z = (0.0, 2.5)      # Z (wysokość)
PREDKOSC_DRIFTU = 0.02
SILA_WIATRU_X = 0.005
AMPLITUDA_UNOSZENIA = 0.3
CZESTOSC_UNOSZENIA = 0.1

SEED = 42

class Czasteczka:
    """
    Bazowa klasa reprezentująca jedną cząsteczkę pyłu.
    Zarządza stanem logicznym oraz tworzeniem klatek kluczowych (keyframes).
    """

    KLATKI_NARODZIN = 10  # Liczba klatek na fazę narodzin/śmierci (fade-in / fade-out)

    def __init__(self, indeks, klatka_narodzin, czas_zycia,
                 pozycja_start, predkosc_drift, faza_unoszenia):
        self.indeks = indeks
        self.klatka_narodzin = klatka_narodzin
        self.czas_zycia = czas_zycia
        self.klatka_smierci = klatka_narodzin + czas_zycia
        self.pozycja_start = pozycja_start
        self.predkosc_drift = predkosc_drift
        self.faza_unoszenia = faza_unoszenia
        self.obj = None

    def stworz(self, kolekcja, material, bazowy_mesh=None):
        """
        Dodaje obiekt cząsteczki do sceny.
        Wspiera współdzielenie meshu (Linked Duplicate) w celu optymalizacji wydajności.
        """
        if bazowy_mesh:
            # Optymalizacja (Linked Duplicate): współdzielimy jeden mesh dla wszystkich cząsteczek
            self.obj = bpy.data.objects.new(name=f"Czasteczka_{self.indeks:03d}", object_data=bazowy_mesh)
            kolekcja.objects.link(self.obj)
        else:
            # Klasyczny fallback: osobna sfera dla każdego obiektu
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=SREDNICA_CZASTECZKI,
                location=self.pozycja_start,
                segments=8, ring_count=4
            )
            self.obj = bpy.context.active_object
            self.obj.name = f"Czasteczka_{self.indeks:03d}"
            kolekcja.objects.link(self.obj)
            if self.obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(self.obj)

        # Przypisanie współdzielonego materiału
        if self.obj.data.materials:
            self.obj.data.materials[0] = material
        else:
            self.obj.data.materials.append(material)

    def aktualna_pozycja(self, klatka):
        """Oblicza pozycję cząsteczki w danej klatce animacji."""
        t = klatka - self.klatka_narodzin
        x = self.pozycja_start[0] + self.predkosc_drift[0] * t + SILA_WIATRU_X * t
        y = self.pozycja_start[1] + self.predkosc_drift[1] * t
        
        # Unoszenie sinusoidalne
        z_base = self.pozycja_start[2] + AMPLITUDA_UNOSZENIA * math.sin(
            t * CZESTOSC_UNOSZENIA + self.faza_unoszenia
        )
        
        # Extra credit: Kolizja z ziemią (z=0) z lekkim tłumieniem i odbiciem
        min_z = 0.05
        if z_base < min_z:
            z = min_z + abs(z_base - min_z) * 0.5
        else:
            z = z_base
            
        return (x, y, z)

    def aktualna_skala(self, klatka):
        """Wyznacza skalę cząsteczki (cykl życia: narodziny -> życie -> śmierć)."""
        wiek = klatka - self.klatka_narodzin
        if wiek < self.KLATKI_NARODZIN:
            return wiek / self.KLATKI_NARODZIN
        elif wiek > self.czas_zycia - self.KLATKI_NARODZIN:
            return (self.czas_zycia - wiek) / self.KLATKI_NARODZIN
        else:
            return 1.0

    def wstaw_keyframes(self):
        """Wstawia klatki kluczowe dla położenia i skali."""
        if self.obj is None:
            return
            
        # Zapewnienie niewidoczności przed narodzinami i po śmierci
        self.obj.scale = (0.0, 0.0, 0.0)
        self.obj.keyframe_insert("scale", frame=max(self.klatka_narodzin - 1, KLATKA_START))
        self.obj.keyframe_insert("scale", frame=min(self.klatka_smierci + 1, KLATKA_KONIEC))

        for klatka in range(self.klatka_narodzin, self.klatka_smierci + 1):
            if klatka < KLATKA_START or klatka > KLATKA_KONIEC:
                continue
            self.obj.location = self.aktualna_pozycja(klatka)
            s = self.aktualna_skala(klatka)
            self.obj.scale = (s, s, s)
            
            self.obj.keyframe_insert("location", frame=klatka)
            self.obj.keyframe_insert("scale", frame=klatka)


# --- Extra Credit: Polimorfizm Klas Potomnych ---

class PylDrobny(Czasteczka):
    """Mniejsze, szybciej dryfujące drobiny pyłku."""
    def __init__(self, indeks, klatka_narodzin, czas_zycia, pozycja_start, predkosc_drift, faza_unoszenia):
        super().__init__(indeks, klatka_narodzin, czas_zycia, pozycja_start, predkosc_drift, faza_unoszenia)
        # Szybszy ruch poziomy
        self.predkosc_drift = (predkosc_drift[0] * 1.5, predkosc_drift[1] * 1.5)

    def aktualna_skala(self, klatka):
        # Drobny pyłek ma o połowę mniejszą skalę bazową
        return super().aktualna_skala(klatka) * 0.6


class SporyDuze(Czasteczka):
    """Większe zarodniki, unoszące się bardziej powoli i ociężale."""
    def __init__(self, indeks, klatka_narodzin, czas_zycia, pozycja_start, predkosc_drift, faza_unoszenia):
        super().__init__(indeks, klatka_narodzin, czas_zycia, pozycja_start, predkosc_drift, faza_unoszenia)
        # Wolniejszy ruch
        self.predkosc_drift = (predkosc_drift[0] * 0.6, predkosc_drift[1] * 0.6)

    def aktualna_skala(self, klatka):
        # Spory są 1.5 raza większe
        return super().aktualna_skala(klatka) * 1.5


class Swietliki(Czasteczka):
    """Świetliki wykonujące dynamiczny, lekko chaotyczny taniec w powietrzu."""
    def __init__(self, indeks, klatka_narodzin, czas_zycia, pozycja_start, predkosc_drift, faza_unoszenia):
        super().__init__(indeks, klatka_narodzin, czas_zycia, pozycja_start, predkosc_drift, faza_unoszenia)
        self.amplituda_swietlika = AMPLITUDA_UNOSZENIA * 1.6

    def aktualna_pozycja(self, klatka):
        t = klatka - self.klatka_narodzin
        # Dodatkowy chaotyczny ruch po spirali w płaszczyźnie XY
        x = self.pozycja_start[0] + self.predkosc_drift[0] * t + 0.15 * math.sin(t * 0.25) + SILA_WIATRU_X * t
        y = self.pozycja_start[1] + self.predkosc_drift[1] * t + 0.15 * math.cos(t * 0.25)
        
        z_base = self.pozycja_start[2] + self.amplituda_swietlika * math.sin(
            t * (CZESTOSC_UNOSZENIA * 1.4) + self.faza_unoszenia
        )
        
        # Odbicie od gruntu
        min_z = 0.05
        if z_base < min_z:
            z = min_z + abs(z_base - min_z) * 0.5
        else:
            z = z_base
            
        return (x, y, z)


# --- Funkcje Pomocnicze Systemu ---

def przygotuj_material(nazwa, kolor=(1.0, 0.95, 0.7, 1.0), sila=2.0):
    """
    Tworzy lub aktualizuje materiał oparty o Emission.
    Zapewnia poprawną konfigurację shaderów w Blenderze.
    """
    mat = bpy.data.materials.get(nazwa)
    if mat is None:
        mat = bpy.data.materials.new(name=nazwa)
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    # Czyszczenie węzłów
    for n in list(nodes):
        nodes.remove(n)

    output = nodes.new(type='ShaderNodeOutputMaterial')
    emission = nodes.new(type='ShaderNodeEmission')
    
    # Ustawienie wejść
    emission.inputs["Color"].default_value = kolor
    emission.inputs["Strength"].default_value = sila
    
    output.location = (200, 0)
    emission.location = (0, 0)
    
    links.new(emission.outputs[0], output.inputs[0])
    return mat

def przygotuj_kolekcje(nazwa=NAZWA_KOLEKCJI):
    """
    Tworzy nową kolekcję lub czyści istniejącą.
    Zapewnia pełną idempotencję (brak duplikowania obiektów przy wielokrotnym uruchomieniu).
    Czyści również nieużywane meshe w pamięci Blendera.
    """
    kolekcja = bpy.data.collections.get(nazwa)
    if kolekcja:
        print(f"Kolekcja '{nazwa}' już istnieje. Czyszczenie starych obiektów...")
        for obj in list(kolekcja.objects):
            mesh = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            # Czyszczenie meshu z pamięci jeśli nie ma innych użytkowników
            if mesh and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
    else:
        kolekcja = bpy.data.collections.new(nazwa)
        bpy.context.scene.collection.children.link(kolekcja)
        print(f"Utworzono nową kolekcję '{nazwa}'.")
    return kolekcja

def generuj_czasteczki(liczba=LICZBA_CZASTECZEK):
    """
    Generuje cząsteczki falami (batchami po 10 cząsteczek co 12 klatek).
    Stosuje polimorfizm przypisując różne klasy cząsteczek.
    """
    czasteczki = []
    klatek_na_fale = 12
    czasteczek_na_fale = 10

    for indeks in range(liczba):
        fala = indeks // czasteczek_na_fale
        klatka_narodzin = KLATKA_START + fala * klatek_na_fale
        if klatka_narodzin >= KLATKA_KONIEC:
            break
            
        czas_zycia = random.randint(CZAS_ZYCIA_MIN, CZAS_ZYCIA_MAX)
        pozycja = (
            random.uniform(*ZAKRES_EMISJI_XY),
            random.uniform(*ZAKRES_EMISJI_XY),
            random.uniform(*WYSOKOSC_EMISJI_Z),
        )
        drift = (
            random.uniform(-PREDKOSC_DRIFTU, PREDKOSC_DRIFTU),
            random.uniform(-PREDKOSC_DRIFTU, PREDKOSC_DRIFTU),
        )
        faza = random.uniform(0, 2 * math.pi)
        
        # Podział na klasy z użyciem polimorfizmu dla różnorodności wizualnej
        typ_los = indeks % 3
        if typ_los == 0:
            czasteczki.append(PylDrobny(
                indeks=indeks, klatka_narodzin=klatka_narodzin, czas_zycia=czas_zycia,
                pozycja_start=pozycja, predkosc_drift=drift, faza_unoszenia=faza
            ))
        elif typ_los == 1:
            czasteczki.append(SporyDuze(
                indeks=indeks, klatka_narodzin=klatka_narodzin, czas_zycia=czas_zycia,
                pozycja_start=pozycja, predkosc_drift=drift, faza_unoszenia=faza
            ))
        else:
            czasteczki.append(Swietliki(
                indeks=indeks, klatka_narodzin=klatka_narodzin, czas_zycia=czas_zycia,
                pozycja_start=pozycja, predkosc_drift=drift, faza_unoszenia=faza
            ))
            
    return czasteczki

def main_czasteczki():
    random.seed(SEED)
    bpy.context.scene.frame_start = KLATKA_START
    bpy.context.scene.frame_end = KLATKA_KONIEC

    # Współdzielone materiały (instanced materials)
    mat_drobny = przygotuj_material("Pyl_Mat_Drobny", kolor=(1.0, 0.9, 0.6, 1.0), sila=1.5)
    mat_spory = przygotuj_material("Pyl_Mat_Spory", kolor=(0.95, 1.0, 0.5, 1.0), sila=2.5)
    mat_swietlik = przygotuj_material("Pyl_Mat_Swietlik", kolor=(0.4, 1.0, 0.8, 1.0), sila=5.0)

    kolekcja = przygotuj_kolekcje()

    # Optymalizacja (Linked Duplicate): Tworzymy jeden mesh bazowy
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=SREDNICA_CZASTECZKI,
        location=(0, 0, 0),
        segments=8, ring_count=4
    )
    temp_obj = bpy.context.active_object
    baza_mesh = temp_obj.data
    baza_mesh.name = "Pyl_Mesh_Wspolny"
    # Usuwamy obiekt pomocniczy, sam mesh zostaje w pamięci Blendera
    bpy.data.objects.remove(temp_obj, do_unlink=True)

    # Generowanie instancji cząsteczek
    czasteczki = generuj_czasteczki()
    for c in czasteczki:
        # Przypisujemy odpowiedni materiał w zależności od klasy cząsteczki
        if isinstance(c, PylDrobny):
            material = mat_drobny
        elif isinstance(c, SporyDuze):
            material = mat_spory
        else:
            material = mat_swietlik
            
        c.stworz(kolekcja, material, bazowy_mesh=baza_mesh)
        c.wstaw_keyframes()
        
    print(f"Wygenerowano pomyślnie {len(czasteczki)} cząsteczek z udostępnionym meshem.")
    
    # Zapisujemy zmiany w pliku blend
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print("Plik blend został zapisany z nowym systemem cząsteczek.")

if __name__ == "__main__":
    main_czasteczki()
