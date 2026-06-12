# Lab 13 – Biomech World | Three.js + glTF 2.0

## Struktura projektu

```
Lab13/
├── index.html          ← Strona główna (importmap, HUD)
├── script.js           ← Logika Three.js (renderer, scena, animacja)
├── eksport_glb.py      ← Skrypt Blendera do eksportu biomech13.glb
├── biomech13.glb       ← [wygeneruj przez eksport_glb.py]
├── three_13.png        ← Zrzut ekranu sceny (wymaganie oddania)
├── Lab7/               ← roslina_lab08.blend (roślina)
├── Lab10/              ← lab10_pajak.blend (pająk)
└── Lab12/              ← swiatozywiony12.blend (cząsteczki)
```

## Jak uruchomić

### Opcja A – Z plikiem .glb z Blendera (zalecana)

1. Otwórz `Lab12/swiatozywiony12.blend` w Blenderze
2. Append pająka z `Lab10/lab10_pajak.blend` (File → Append → Object)
3. Przejdź do zakładki **Scripting** w Blenderze
4. Otwórz `eksport_glb.py` → kliknij **Run Script**
5. Plik `biomech13.glb` pojawi się w folderze `Lab13/`
6. Otwórz `index.html` w VS Code → **Live Server** (prawy klik → Open with Live Server)

> ⚠ NIE otwieraj przez podwójny klik (file://) – przeglądarka zablokuje fetch() błędem CORS!

### Opcja B – Tryb proceduralny (bez Blendera)

Jeśli `biomech13.glb` nie istnieje, `script.js` automatycznie:
- Buduje proceduralna scenę z rośliną, pająkiem i 50 cząsteczkami
- Wyświetla komunikat w panelu HUD

## Wymagania spełnione (ocena 5.0)

| Kryterium | Status |
|---|---|
| Uruchamianie przez Live Server bez błędów | ✅ |
| Wczytany model .glb (GLTFLoader + loadAsync) | ✅ |
| OrbitControls (obracanie myszą, zoom) | ✅ |
| 3 światła Three-Point (Key + Fill + Rim) + Ambient | ✅ |
| ACESFilmicToneMapping + SRGBColorSpace | ✅ |
| Apply All Transforms w Blenderze | ✅ (eksport_glb.py) |
| Obsługa błędu ładowania .glb (try/catch + div#status) | ✅ |
| Animacja własna – obrót modelu (delta × ROTATION_SPEED) | ✅ |
| Pulsowanie pąka rośliny (sinusoida + emissive) | ✅ |
| Funkcja fitCamera() z Box3 | ✅ |
| OrbitControls: enableDamping, minDistance, maxDistance | ✅ |
| Obsługa resize okna | ✅ |
| Czytelne nazwy obiektów (traverse + console.log) | ✅ |

## Architektura sceny

```
BiomechWorld (Group)
├── Ground (Mesh)
├── Roslina_Biomechaniczna (Group)       ← Lab07/08
│   ├── Lodygla_Rosliny (Mesh)
│   ├── Lisc_1..5 (Mesh ×5)
│   ├── Pak_Rosliny (Mesh) ← ANIMACJA PULSOWANIA
│   ├── Glow_Rosliny_1..4 (Mesh ×4)
│   └── Korzen_1..5 (Mesh ×5)
├── Pajak_Lab10 (Group)                  ← Lab10
│   ├── Pajak_Tułów (Mesh)
│   ├── Pajak_Odwłok (Mesh)
│   ├── Pajak_Noga_L1..4 / R1..4 (Mesh ×8)
│   ├── Pajak_Udo_L1..4 / R1..4 (Mesh ×8)
│   └── Pajak_Oko_L1..4 / R1..4 (Mesh ×8)
└── Czasteczki_Lab12 (Group)            ← Lab12
    ├── Czasteczka_PylDrobny_000..N
    ├── Czasteczka_SporyDuze_001..N
    └── Czasteczka_Swietlik_002..N
```

## Konwencje koordynatów

| System | Góra | Eksporter |
|---|---|---|
| Blender | Z-up | `export_yup=True` → obrót o -90°X |
| Three.js | Y-up | Domyślne (WebGL) |

## THREE.Clock vs Date.now()

`getDelta()` mierzy czas od **poprzedniej klatki** (delta-time).  
`getElapsedTime()` mierzy łączny czas od startu.  
Clock automatycznie pauzuje gdy karta jest w tle (performance.now()).
