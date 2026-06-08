# Night Thief (PGK Lab 15)

## Opis gry
Night Thief to gra zręcznościowa typu "stealth" (skradanka) w środowisku 2D. Gracz (niebieska kulka) musi przekraść się przez strzeżony poziom, zebrać wszystkie żółte artefakty, a następnie uciec do strefy "EXIT". Gracz musi unikać wzroku strażników, korzystać z ukryć, zarządzać staminą podczas sprintu oraz odwracać uwagę wrogów za pomocą rzucanych kamieni. Na mapie znajduje się też kamera monitoringu i zamek blokujący drogę do wyjścia.

## Technologia i uruchomienie
Projekt został napisany w języku **Python 3** z wykorzystaniem biblioteki **Raylib** (pakiet `pyray` / `raylib-python-cffi`).
Aby uruchomić grę:
1. Upewnij się, że masz zainstalowanego Pythona (wersja >= 3.8).
2. Zainstaluj bibliotekę Raylib: `pip install raylib`
3. Uruchom plik główny: `python main.py`
*(Dźwięki w grze generowane są za pomocą dołączonego skryptu `audio_generator.py` - pliki .wav są już w repozytorium).*

## Własny mechanizm wykraczający poza oryginał (Cechy unikalne)
1. **Prawdziwe Pole Widzenia (FOV) i System Hałasu**: W przeciwieństwie do prostego sprawdzania odległości, strażnicy i kamery używają stożkowego pola widzenia (obliczanego za pomocą iloczynu skalarnego), przez co gracz może zakraść się bezpiecznie od tyłu. Dodatkowo wdrożono system "sprintu" ze staminą — bieg podwaja prędkość, ale generuje hałas, który alarmuje pobliskich wrogów. 
2. **Zaawansowana maszyna stanów (FSM) z pamięcią i celami**: Strażnicy operują na 4 stanach (`PATROL`, `SUSPICIOUS`, `CHASE`, `RETURN`). Gdy usłyszą kamień lub bieg gracza, przechodzą w stan podejrzenia i idą sprawdzić konkretne źródło dźwięku, po czym samodzielnie wyznaczają ścieżkę powrotu do najbliższego punktu swojego patrolu.

*Wskazanie tego wymogu:* Powyższe mechaniki (zaawansowane FOV, Stamina, System Dźwięku) znacznie wykraczają poza prostą logikę przeciwników prezentowaną na zajęciach (np. w Asteroids), dając grze wymiar taktyczny.

## Czy gra jest klonem?
Projekt nie jest bezpośrednim klonem żadnej konkretnej gry. Czerpie jednak inspirację z klasycznych tytułów typu "stealth" z widokiem z góry (np. wczesne etapy *Metal Gear Solid* na PS1 lub *Hotline Miami* w wariancie bez przemocy), przekładając ich koncepcje na minimalistyczną oprawę 2D.

## Znane bugi i ograniczenia
- Mechanika rzutu kamieniem (prawy przycisk myszy) nie posiada zaawansowanej kolizji ze ścianami podczas lotu — kamień przelatuje nad przeszkodami i aktywuje się w miejscu kliknięcia. W realiach gry traktowane jest to jako rzut lobem "ponad ścianami".
- Strażnicy poruszają się w oparciu o wektory i prostą detekcję kolizji. Przy bardzo rzadkich, nienaturalnych układach geometrii mogą zachowywać się "sztywno" ślizgając się po ścianach.
