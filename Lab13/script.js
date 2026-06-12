/**
 * Lab 13 – Biomech World | Three.js + glTF 2.0
 * ================================================
 * Pipeline: Blender (Lab07 roślina + Lab10 pająk + Lab12 cząsteczki) → .glb → Three.js
 *
 * Architektura:
 *  1. init()          – WebGLRenderer, Scene, PerspectiveCamera
 *  2. setupLights()   – Three-Point (Key + Fill + Rim) + Ambient
 *  3. loadModel()     – GLTFLoader async/await z try/catch + fallback proceduralny
 *  4. buildFallback() – Proceduralna scena (gdy brak biomech13.glb):
 *                        roślina, pająk, 3 typy cząsteczek (jak Lab12)
 *  5. fitCamera()     – Box3: automatyczne kadrowanie kamery na modelu
 *  6. animate()       – requestAnimationFrame + THREE.Clock (delta-time)
 *
 * Uruchamiać WYŁĄCZNIE przez Live Server (nie przez file://) – blokada CORS!
 */

import * as THREE            from 'three';
import { OrbitControls }     from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader }        from 'three/addons/loaders/GLTFLoader.js';

// ─────────────────────────────────────────────────────────────────────────────
// 1. RENDERER, SCENA, KAMERA
// ─────────────────────────────────────────────────────────────────────────────

/** @type {THREE.WebGLRenderer} */
const renderer = new THREE.WebGLRenderer({
  canvas:    document.getElementById('canvas'),
  antialias: true,
  alpha:     false,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);

// Poprawne zarządzanie kolorem – wymagane dla fizycznie poprawnych renderów
// outputColorSpace: konwertuje wynik renderingu do przestrzeni sRGB (standard monitorów)
// toneMapping: ACESFilmic symuluje odpowiedź filmową (naturalne kolory, nie "wypalone")
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping      = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.2;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type    = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x010a0f);

// Lekka mgła atmosferyczna – nawiązanie do klimatu Lab12 (ciemne tło świata)
scene.fog = new THREE.FogExp2(0x010a0f, 0.055);

// Kamera perspektywiczna
// fov=60°, near=0.01, far=200 – dopasowane do skali sceny
const camera = new THREE.PerspectiveCamera(
  60,
  window.innerWidth / window.innerHeight,
  0.01,
  200,
);
camera.position.set(4, 3, 6);

// ─────────────────────────────────────────────────────────────────────────────
// 2. ORBIT CONTROLS
// ─────────────────────────────────────────────────────────────────────────────

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping  = true;   // Płynne "wtłumianie" ruchu (inertia)
controls.dampingFactor  = 0.06;
controls.minDistance    = 1.5;    // Nie bliżej niż 1.5 jednostki
controls.maxDistance    = 40;     // Nie dalej niż 40 jednostek
controls.target.set(0, 1, 0);    // Punkt orbity: środek sceny (ok. wysokość rośliny)
controls.update();

// ─────────────────────────────────────────────────────────────────────────────
// 3. OŚWIETLENIE THREE-POINT + AMBIENT
//    Nawiązanie do setupu z Lab 08 (roslina_lab08.blend)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * setupLights() – Buduje zestaw świateł Three-Point:
 *   Key   – główne, ciepłe, z cieniami
 *   Fill  – wypełniające, chłodniejsze, bez cieni
 *   Rim   – konturowe, nawiązuje do bioluminescencji rośliny (zielono-cyjan)
 *   Ambient – bardzo słabe, żeby cienie nie były kompletnie czarne
 */
function setupLights() {
  // KEY LIGHT – główne oświetlenie, ciepła biel (jak słońce zza mgły)
  const keyLight = new THREE.DirectionalLight(0xfff5e0, 2.8);
  keyLight.position.set(5, 8, 5);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(2048, 2048);
  keyLight.shadow.camera.near = 0.5;
  keyLight.shadow.camera.far  = 40;
  keyLight.shadow.camera.left   = -8;
  keyLight.shadow.camera.right  =  8;
  keyLight.shadow.camera.top    =  8;
  keyLight.shadow.camera.bottom = -8;
  keyLight.shadow.bias = -0.0004;
  keyLight.name = 'KeyLight';
  scene.add(keyLight);

  // FILL LIGHT – chłodny błękit, wypełnia cienie
  const fillLight = new THREE.DirectionalLight(0xa8d4ff, 0.9);
  fillLight.position.set(-5, 3, -3);
  fillLight.name = 'FillLight';
  scene.add(fillLight);

  // RIM LIGHT – bioluminescencja (jak w Lab12: kolor #00ffcc cyjan)
  const rimLight = new THREE.DirectionalLight(0x00ffcc, 1.6);
  rimLight.position.set(0, 2, -8);
  rimLight.name = 'RimLight';
  scene.add(rimLight);

  // AMBIENT – bardzo słabe, globalne oświetlenie otoczenia
  const ambient = new THREE.AmbientLight(0x0a1520, 0.6);
  ambient.name = 'AmbientLight';
  scene.add(ambient);

  // Debugowanie świateł: odkomentuj poniższe linie w razie problemów z orientacją
  // scene.add(new THREE.DirectionalLightHelper(keyLight, 1, 0xffff00));
  // scene.add(new THREE.DirectionalLightHelper(fillLight, 0.5, 0x88aaff));
  // scene.add(new THREE.DirectionalLightHelper(rimLight, 0.5, 0x00ffcc));
  // scene.add(new THREE.AxesHelper(2));
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. GLTFLoader – WCZYTANIE MODELU
// ─────────────────────────────────────────────────────────────────────────────

/** Referencja do głównego obiektu sceny (glTF lub proceduralny) */
let sceneRoot = null;

/** Referencja do mesh-a "pąk rośliny" – do animacji pulsowania */
let budMesh = null;

/** Licznik mesh-y w scenie */
let meshCount = 0;

/**
 * Rekurencyjnie liczy mesh-y w hierarchii Object3D.
 * Używa metody traverse – przechodzi przez wszystkie węzły.
 * @param {THREE.Object3D} root
 * @returns {number}
 */
function countMeshes(root) {
  let count = 0;
  root.traverse(obj => { if (obj.isMesh) count++; });
  return count;
}

/**
 * Szuka mesh-a po nazwie (case-insensitive, częściowe dopasowanie).
 * Potrzebne do: znalezienia pąka rośliny pod animację pulsowania.
 * @param {THREE.Object3D} root
 * @param {string} namePart
 * @returns {THREE.Mesh|null}
 */
function findMeshByName(root, namePart) {
  let found = null;
  root.traverse(obj => {
    if (obj.isMesh && obj.name.toLowerCase().includes(namePart.toLowerCase())) {
      found = obj;
    }
  });
  return found;
}

/**
 * fitCamera() – Automatyczne ustawienie kamery na bounding box modelu.
 * Wymaganie 5.0: "funkcja centrująca kamerę z Box3 – kamera ustawia się
 * automatycznie na podstawie bounding box modelu."
 *
 * THREE.Box3.setFromObject() oblicza oś-wyrównany box (AABB) całego modelu.
 * getCenter() zwraca środek, getSize() zwraca wymiary.
 *
 * @param {THREE.Object3D} object
 */
function fitCamera(object) {
  const box    = new THREE.Box3().setFromObject(object);
  const center = box.getCenter(new THREE.Vector3());
  const size   = box.getSize(new THREE.Vector3());

  const maxDim  = Math.max(size.x, size.y, size.z);
  const fovRad  = camera.fov * (Math.PI / 180);
  const camDist = (maxDim / 2) / Math.tan(fovRad / 2) * 1.8;

  // Przesuń punkt orbity do środka modelu
  controls.target.copy(center);

  // Ustaw kamerę w górze i na prawo od środka, w odległości camDist
  camera.position.set(
    center.x + camDist * 0.6,
    center.y + camDist * 0.5,
    center.z + camDist,
  );

  // Dopasuj zakresy kamery
  camera.near = maxDim * 0.01;
  camera.far  = maxDim * 10;
  camera.updateProjectionMatrix();

  // OrbitControls: limity na podstawie rozmiaru modelu
  controls.minDistance = maxDim * 0.3;
  controls.maxDistance = maxDim * 8;
  controls.update();
}

/**
 * loadModel() – Asynchroniczne wczytanie biomech13.glb przez GLTFLoader.
 *
 * Dlaczego async/await a nie callbacks?
 * loadAsync() zwraca Promise – async/await jest czytelniejsze i lepiej
 * integruje się z try/catch niż zagnieżdżone callbacki.
 *
 * Obsługa błędu: div#status pokazuje komunikat z przyczyną awarii.
 * Fallback: jeśli .glb nie istnieje, budujemy scenę proceduralnie.
 */
async function loadModel() {
  const statusEl = document.getElementById('status');
  const lsLabel  = document.getElementById('ls-label');

  try {
    lsLabel.textContent = 'Wczytywanie biomech13.glb…';
    statusEl.textContent = 'Wczytywanie biomech13.glb…';
    statusEl.className = '';

    const loader = new GLTFLoader();

    // loadAsync – wersja promisowa GLTFLoader.load()
    // Wymagane przez zadanie: "użyj async/await – sprawdź loadAsync"
    const gltf = await loader.loadAsync('biomech13.glb');

    sceneRoot = gltf.scene;

    // Włącz cienie dla wszystkich mesh-y
    sceneRoot.traverse(obj => {
      if (obj.isMesh) {
        obj.castShadow    = true;
        obj.receiveShadow = true;
        // Wypisz nazwy obiektów – przygotowanie pod raycaster w Lab14
        console.log(`[MESH] name="${obj.name}" | material="${obj.material?.name || 'brak'}"`);
      }
    });

    scene.add(sceneRoot);
    fitCamera(sceneRoot);

    // Szukamy pąka rośliny do animacji pulsowania
    budMesh = findMeshByName(sceneRoot, 'pak')
           || findMeshByName(sceneRoot, 'bud')
           || findMeshByName(sceneRoot, 'kwiat');

    meshCount = countMeshes(sceneRoot);
    document.getElementById('stat-meshes').textContent = meshCount;
    statusEl.textContent = `✓ Wczytano model! ${meshCount} mesh-y`;
    statusEl.className = 'ok';

  } catch (err) {
    // Błąd ładowania – komunikat na overlay
    console.warn('[Lab13] Nie wczytano biomech13.glb:', err.message);
    statusEl.textContent = `⚠ Brak biomech13.glb – tryb proceduralny`;
    statusEl.className = 'error';

    // FALLBACK: budujemy scenę proceduralnie
    lsLabel.textContent = 'Generowanie sceny proceduralnej…';
    buildFallbackScene();
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. FALLBACK – PROCEDURALNA SCENA BIOMECHY
//    Odwzorowuje: roślinę (Lab07/08), pająka (Lab10),
//    3 typy cząsteczek – PylDrobny, SporyDuze, Swietliki (Lab12)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * buildFallbackScene() – proceduralna replika biomechanicznego świata.
 * Struktura obiektów naśladuje hierarchię, jaką miałby eksport z Blendera.
 * Każdy obiekt ma czytelną nazwę (name) – gotowe pod raycaster w Lab14.
 */
function buildFallbackScene() {
  sceneRoot = new THREE.Group();
  sceneRoot.name = 'BiomechWorld';

  // --- PODŁOŻE ---
  const groundGeo = new THREE.PlaneGeometry(20, 20, 32, 32);
  const groundMat = new THREE.MeshStandardMaterial({
    color:     0x061208,
    roughness: 0.95,
    metalness: 0.05,
  });
  const ground = new THREE.Mesh(groundGeo, groundMat);
  ground.name = 'Ground';
  ground.rotation.x = -Math.PI / 2;
  ground.receiveShadow = true;
  sceneRoot.add(ground);

  // --- ROŚLINA BIOMECHANICZNA (Lab07/08) ---
  buildPlant(sceneRoot);

  // --- PAJĄK (Lab10) ---
  buildSpider(sceneRoot);

  // --- CZĄSTECZKI (Lab12: PylDrobny, SporyDuze, Swietliki) ---
  buildParticles(sceneRoot);

  scene.add(sceneRoot);
  fitCamera(sceneRoot);

  meshCount = countMeshes(sceneRoot);
  document.getElementById('stat-meshes').textContent = meshCount;
  document.getElementById('status').textContent = `✓ Scena proceduralna (${meshCount} mesh-y)`;
  document.getElementById('status').className = 'ok';

  // Wypisz hierarchię do konsoli – Lab14 raycaster
  console.log('[Lab13] Hierarchia sceny (traverse):');
  sceneRoot.traverse(obj => {
    if (obj.isMesh) {
      console.log(`  [MESH] name="${obj.name}"`);
    }
  });
}

/* ---- Materiały wspólne ---- */

function makeMat(color, emissive = 0x000000, emissiveIntensity = 0, roughness = 0.5, metalness = 0.1) {
  return new THREE.MeshStandardMaterial({ color, emissive, emissiveIntensity, roughness, metalness });
}

/* ── Roślina ─────────────────────────────────────────────────────────────── */

function buildPlant(parent) {
  const plantGroup = new THREE.Group();
  plantGroup.name = 'Roslina_Biomechaniczna';

  // Pień / łodyga (cylindryczna, lekko organiczna)
  const stemGeo = new THREE.CylinderGeometry(0.06, 0.12, 2.4, 10, 6, false);
  // Deformacja wierzchołków – lekkie skrzywienie
  const stemPos = stemGeo.attributes.position;
  for (let i = 0; i < stemPos.count; i++) {
    const y = stemPos.getY(i);
    stemPos.setX(i, stemPos.getX(i) + Math.sin(y * 2.1) * 0.07);
    stemPos.setZ(i, stemPos.getZ(i) + Math.cos(y * 1.7) * 0.05);
  }
  stemGeo.computeVertexNormals();
  const stemMesh = new THREE.Mesh(stemGeo, makeMat(0x1a3a10, 0x00aa44, 0.3));
  stemMesh.name = 'Lodygla_Rosliny';
  stemMesh.position.y = 1.2;
  stemMesh.castShadow = true;
  plantGroup.add(stemMesh);

  // 5 gałęzi liściowych
  const leafAngles = [0, 72, 144, 216, 288];
  leafAngles.forEach((deg, i) => {
    const rad = (deg * Math.PI) / 180;
    const leafGeo = new THREE.ConeGeometry(0.35 - i * 0.02, 0.9, 6, 1);
    const leafMat = makeMat(
      new THREE.Color().setHSL(0.35 - i * 0.01, 0.7, 0.18),
      0x00cc66, 0.25 + i * 0.05,
    );
    const leaf = new THREE.Mesh(leafGeo, leafMat);
    leaf.name = `Lisc_${i + 1}`;
    const h = 0.6 + i * 0.35;
    leaf.position.set(Math.cos(rad) * 0.55, h, Math.sin(rad) * 0.55);
    leaf.rotation.z = Math.cos(rad) * 0.5;
    leaf.rotation.x = Math.sin(rad) * 0.5;
    leaf.castShadow = true;
    plantGroup.add(leaf);
  });

  // Pąk (górna część – główny obiekt do animacji pulsowania)
  const budGeo = new THREE.SphereGeometry(0.22, 12, 10);
  const budMat = makeMat(0x002a10, 0x00ffcc, 1.4, 0.3, 0.2);
  const bud = new THREE.Mesh(budGeo, budMat);
  bud.name = 'Pak_Rosliny';          // ← findMeshByName('pak') znajdzie ten mesh
  bud.position.y = 2.55;
  bud.castShadow = true;
  plantGroup.add(bud);
  budMesh = bud;  // zapisujemy referencję globalną

  // Mniejsze bąbelki bioluminescencyjne na łodydze
  [0.5, 1.0, 1.7, 2.1].forEach((y, i) => {
    const radius = 0.06 - i * 0.008;
    const glowGeo = new THREE.SphereGeometry(radius, 8, 6);
    const glowMat = makeMat(0x001a0d, 0x00ffaa, 2.0 + i * 0.5);
    const glow = new THREE.Mesh(glowGeo, glowMat);
    glow.name = `Glow_Rosliny_${i + 1}`;
    const angle = i * 1.5;
    glow.position.set(Math.cos(angle) * 0.12, y, Math.sin(angle) * 0.12);
    plantGroup.add(glow);
  });

  // Korzeń (organiczne rozgałęzienia)
  for (let r = 0; r < 5; r++) {
    const angle = (r / 5) * Math.PI * 2;
    const rootGeo = new THREE.CylinderGeometry(0.02, 0.04, 0.4 + Math.random() * 0.2, 4);
    const rootMesh = new THREE.Mesh(rootGeo, makeMat(0x0d200a, 0x004422, 0.1));
    rootMesh.name = `Korzen_${r + 1}`;
    rootMesh.position.set(Math.cos(angle) * 0.25, 0.15, Math.sin(angle) * 0.25);
    rootMesh.rotation.z = Math.cos(angle) * 0.6;
    rootMesh.rotation.x = Math.sin(angle) * 0.6;
    rootMesh.receiveShadow = true;
    plantGroup.add(rootMesh);
  }

  plantGroup.position.set(0, 0, 0);
  parent.add(plantGroup);
}

/* ── Pająk (Lab10) ────────────────────────────────────────────────────────── */

function buildSpider(parent) {
  const spiderGroup = new THREE.Group();
  spiderGroup.name = 'Pajak_Lab10';
  spiderGroup.position.set(2.2, 0.35, 1.5);

  // Ciało (tułów + odwłok)
  const bodyMat = makeMat(0x1a0a06, 0x441100, 0.3, 0.4, 0.5);

  const thoraxGeo = new THREE.SphereGeometry(0.18, 10, 8);
  const thorax = new THREE.Mesh(thoraxGeo, bodyMat);
  thorax.name = 'Pajak_Tulów';
  thorax.scale.set(1, 0.8, 1.1);
  thorax.castShadow = true;
  spiderGroup.add(thorax);

  const abdomenGeo = new THREE.SphereGeometry(0.25, 10, 8);
  const abdomen = new THREE.Mesh(abdomenGeo, makeMat(0x0d0503, 0x660a00, 0.2, 0.35, 0.6));
  abdomen.name = 'Pajak_Odwłok';
  abdomen.position.set(-0.4, 0, 0);
  abdomen.scale.set(1.1, 0.85, 0.95);
  abdomen.castShadow = true;
  spiderGroup.add(abdomen);

  // 8 nóg (4 strony × 2)
  const legMat = makeMat(0x2a1006, 0x330800, 0.15, 0.6, 0.4);
  const legAngles = [-0.4, -0.1, 0.1, 0.4];
  [1, -1].forEach(side => {
    legAngles.forEach((zRot, i) => {
      const legGeo = new THREE.CylinderGeometry(0.018, 0.012, 0.6, 5);
      const leg    = new THREE.Mesh(legGeo, legMat);
      leg.name     = `Pajak_Noga_${side > 0 ? 'L' : 'R'}${i + 1}`;

      // Udo
      const thighGeo = new THREE.CylinderGeometry(0.022, 0.016, 0.35, 5);
      const thigh    = new THREE.Mesh(thighGeo, legMat);
      thigh.name     = `Pajak_Udo_${side > 0 ? 'L' : 'R'}${i + 1}`;
      thigh.position.set(side * 0.18, 0.06, (i - 1.5) * 0.14);
      thigh.rotation.z = side * (0.6 + i * 0.08);
      thigh.rotation.x = zRot;
      thigh.castShadow = true;
      spiderGroup.add(thigh);

      // Goleń
      leg.position.set(side * (0.38 + i * 0.04), -0.15, (i - 1.5) * 0.22);
      leg.rotation.z = side * (1.1 + i * 0.1);
      leg.rotation.x = zRot * 1.4;
      leg.castShadow = true;
      spiderGroup.add(leg);
    });
  });

  // Oczy (8 małych sfer, świecące)
  const eyeMat = makeMat(0x000000, 0xff2200, 3.0);
  [-1, 1].forEach(side => {
    [0, 1, 2, 3].forEach(i => {
      const eyeGeo = new THREE.SphereGeometry(0.025, 6, 4);
      const eye    = new THREE.Mesh(eyeGeo, eyeMat);
      eye.name     = `Pajak_Oko_${side > 0 ? 'L' : 'R'}${i + 1}`;
      eye.position.set(0.14, 0.1 + i * 0.04, side * (0.05 + i * 0.03));
      spiderGroup.add(eye);
    });
  });

  spiderGroup.rotation.y = -0.7;
  parent.add(spiderGroup);
}

/* ── Cząsteczki – Lab12 (PylDrobny, SporyDuze, Swietliki) ─────────────────── */

/** Dane jednej cząsteczki do animacji w pętli renderowania */
const particles = [];

/**
 * Trzy typy cząsteczek z Lab12:
 *  0 = PylDrobny  – małe, szybkie, kolor miodowo-żółty
 *  1 = SporyDuze  – duże, wolne, kolor żółto-zielony
 *  2 = Swietliki  – chaotyczne, cyjanowy blask (bioluminescencja)
 */
function buildParticles(parent) {
  const particleGroup = new THREE.Group();
  particleGroup.name = 'Czasteczki_Lab12';

  const matDrobny   = new THREE.MeshStandardMaterial({ color: 0xfff0a0, emissive: 0xffcc44, emissiveIntensity: 1.5, roughness: 0.4 });
  const matSpory    = new THREE.MeshStandardMaterial({ color: 0xf0ff80, emissive: 0xaaff00, emissiveIntensity: 2.5, roughness: 0.3 });
  const matSwietlik = new THREE.MeshStandardMaterial({ color: 0x80ffee, emissive: 0x00ffcc, emissiveIntensity: 5.0, roughness: 0.1 });

  const mats = [matDrobny, matSpory, matSwietlik];
  const baseGeo = new THREE.SphereGeometry(0.04, 8, 4);

  const TOTAL = 50;
  for (let i = 0; i < TOTAL; i++) {
    const typ  = i % 3;
    const mesh = new THREE.Mesh(baseGeo, mats[typ]);

    // Nazwy zgodne z Lab12 (PylDrobny_00x / SporyDuze_00x / Swietliki_00x)
    const typNames = ['PylDrobny', 'SporyDuze', 'Swietlik'];
    mesh.name = `Czasteczka_${typNames[typ]}_${String(i).padStart(3, '0')}`;

    // Losowa pozycja startowa (ZAKRES_EMISJI_XY ±2, WYSOKOSC_EMISJI_Z 0..2.5)
    const px = (Math.random() - 0.5) * 4;
    const py = Math.random() * 2.5;
    const pz = (Math.random() - 0.5) * 4;
    mesh.position.set(px, py, pz);

    // Losowa skala bazowa
    const sBase = typ === 0 ? 0.6 : (typ === 1 ? 1.5 : 1.0);
    mesh.scale.setScalar(sBase);

    particleGroup.add(mesh);

    // Dane animacji (bez keyframes Blendera – tu używamy delta-time w pętli)
    particles.push({
      mesh,
      typ,
      basePos:    new THREE.Vector3(px, py, pz),
      driftX:     (Math.random() - 0.5) * 0.015 * (typ === 0 ? 1.5 : typ === 1 ? 0.6 : 1.0),
      driftZ:     (Math.random() - 0.5) * 0.015,
      phase:      Math.random() * Math.PI * 2,
      phaseX:     Math.random() * Math.PI * 2,  // tylko Swietliki – chaotyczny ruch
      sBase,
      windX:      0.005,
      born:       Math.random() * 8,   // offset czasu narodzin
      lifespan:   6 + Math.random() * 4,
    });
  }

  parent.add(particleGroup);
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. ANIMACJA WŁASNA W PĘTLI (delta-time z THREE.Clock)
//
// Wymaganie 5.0:
//  - Obrót modelu wokół Y skalowany przez delta → stała prędkość niezależna od FPS
//  - Pulsowanie pąka rośliny (sinusoida)
//  - Animacja cząsteczek (drift + unoszenie)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * THREE.Clock
 * getDelta()       – czas od ostatniego wywołania getDelta() [sekundy]
 * getElapsedTime() – łączny czas od startu [sekundy]
 *
 * Dlaczego Clock zamiast Date.now()?
 * Clock jest zsynchronizowany z wewnętrzną logiką Three.js,
 * automatycznie pauzuje gdy strona jest w tle (autoStart=true),
 * getDelta() gwarantuje pomiar od POPRZEDNIEJ KLATKI (nie od startu).
 */
const clock = new THREE.Clock();

/** Prędkość obrotu całej sceny [rad/s] */
const ROTATION_SPEED = 0.12;

/** Prędkość pulsowania pąka [Hz] */
const BUD_PULSE_FREQ = 1.1;

/**
 * animateParticles(elapsed) – aktualizuje pozycje i skale cząsteczek.
 * Naśladuje logikę klas Lab12: PylDrobny (szybki drift),
 * SporyDuze (wolny, większy), Swietliki (chaotyczny taniec spiralny).
 *
 * @param {number} elapsed – łączny czas w sekundach
 */
function animateParticles(elapsed) {
  for (const p of particles) {
    const t = (elapsed - p.born) % p.lifespan;
    if (t < 0) continue;  // cząsteczka jeszcze nie "narodzona"

    const lifeNorm = t / p.lifespan;

    // Cykl życia: fade-in (0..0.1) → życie (0.1..0.9) → fade-out (0.9..1.0)
    let scale;
    if      (lifeNorm < 0.1) scale = lifeNorm / 0.1;
    else if (lifeNorm > 0.9) scale = (1 - lifeNorm) / 0.1;
    else                     scale = 1.0;
    p.mesh.scale.setScalar(p.sBase * scale * 0.1);

    // Pozycja – drift + unoszenie sinusoidalne
    const WIND_X = 0.005;
    let nx = p.basePos.x + p.driftX * t * 60 + WIND_X * t * 60;
    let nz = p.basePos.z + p.driftZ * t * 60;
    let ny;

    if (p.typ === 2) {
      // Swietliki – chaotyczny taniec spiralny (jak klasa Swietliki w Lab12)
      nx += 0.15 * Math.sin(t * 0.25 + p.phaseX);
      nz += 0.15 * Math.cos(t * 0.25 + p.phaseX);
      ny = p.basePos.y + 0.48 * Math.sin(t * 0.14 + p.phase);
    } else {
      // PylDrobny i SporyDuze – standardowe unoszenie sinusoidalne
      ny = p.basePos.y + 0.3 * Math.sin(t * 0.1 + p.phase);
    }

    // Kolizja z ziemią
    if (ny < 0.05) ny = 0.05 + Math.abs(ny - 0.05) * 0.5;

    p.mesh.position.set(nx, ny, nz);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. OBSŁUGA RESIZE OKNA
// ─────────────────────────────────────────────────────────────────────────────

/**
 * onResize() – aktualizuje renderer i kamerę przy zmianie rozmiaru okna.
 * Wymaganie 5.0: "Resize window obsłużone – scena dostosowuje się."
 */
function onResize() {
  const w = window.innerWidth;
  const h = window.innerHeight;

  camera.aspect = w / h;
  camera.updateProjectionMatrix();

  renderer.setSize(w, h);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
}

window.addEventListener('resize', onResize);

// ─────────────────────────────────────────────────────────────────────────────
// 8. PĘTLA RENDEROWANIA
// ─────────────────────────────────────────────────────────────────────────────

/**
 * animate() – główna pętla renderująca.
 * requestAnimationFrame wywołuje animate() przed każdą klatką przeglądarki.
 *
 * Użycie delta-time (getDelta) zamiast stałych wartości:
 * → obrót 0.12 rad/s × delta = stała prędkość niezależna od FPS.
 */
function animate() {
  requestAnimationFrame(animate);

  const delta   = clock.getDelta();          // czas od ostatniej klatki [s]
  const elapsed = clock.getElapsedTime();    // łączny czas [s]

  // 1. Powolny obrót całej sceny wokół osi Y
  if (sceneRoot) {
    sceneRoot.rotation.y += ROTATION_SPEED * delta;
  }

  // 2. Pulsowanie pąka rośliny – sinusoida skalująca mesh
  // Wymaga znalezionej referencji budMesh (findMeshByName / budMesh z buildPlant)
  if (budMesh) {
    const pulse = 1 + 0.12 * Math.sin(elapsed * BUD_PULSE_FREQ * Math.PI * 2);
    budMesh.scale.setScalar(pulse);

    // Pulsowanie emisji – "bioluminescencja" (Lab12: pulsuj_emission)
    if (budMesh.material && budMesh.material.emissiveIntensity !== undefined) {
      budMesh.material.emissiveIntensity = 1.0 + 2.0 * Math.abs(Math.sin(elapsed * BUD_PULSE_FREQ * Math.PI));
    }
  }

  // 3. Animacja cząsteczek
  animateParticles(elapsed);

  // 4. OrbitControls z enableDamping – wymaga update() w każdej klatce
  controls.update();

  // 5. Render
  renderer.render(scene, camera);
}

// ─────────────────────────────────────────────────────────────────────────────
// 9. MAIN – inicjalizacja
// ─────────────────────────────────────────────────────────────────────────────

async function main() {
  setupLights();

  await loadModel();

  // Ukryj loading screen po załadowaniu sceny
  const ls = document.getElementById('loading-screen');
  ls.classList.add('fade-out');
  setTimeout(() => ls.remove(), 1200);

  // Uruchom pętlę renderującą
  animate();
}

main();
