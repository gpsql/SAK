# Lab 15 — Night City POV Animation

## Scene Description

A first-person (POV) walk through a rainy night city — streets with neon signs,
passing cars with headlights, and wet asphalt reflecting city lights.
The mood is cinematic and atmospheric: dark, moody, with glowing colors cutting through the fog.

## How to Open and Render

1. Open `assets/scena.blend` in Blender 4.x or later.
2. Run scripts from `src/` in the Blender Python console in order:
   - `blender_setup.py` — creates building light blocks
   - `road_setup.py` — generates wet asphalt road with markings
   - `camera_setup.py` — sets up POV camera with head bobbing
   - `cars_setup.py` — creates animated cars with headlights
   - `weather_setup.py` — adds volumetric fog and rain particles
   - `render_setup.py` — configures Cycles render settings (Metal GPU, 1080p, MP4)
   - `add_cinematic_fx.py` — sets up compositor (Glare, Lens Distortion)
3. Press `F12` to render a single frame preview, or `Ctrl+F12` to render the full animation.
4. Output will be saved next to the `.blend` file as `POV_NightCity_Render.mp4`.

## Python Script Description

| Script | Description | Key Parameters |
|--------|-------------|----------------|
| `blender_setup.py` | Creates window and neon light blocks for manual placement | `strength` (emission), `color`, `size` |
| `camera_setup.py` | POV camera on Follow Path with procedural head bobbing | `path_duration` (192 frames), `lens` (28mm), `dof.focus_distance` |
| `cars_setup.py` | Low-poly cars animated along Bezier curves | `body_color`, `duration_frames`, `offset` |
| `weather_setup.py` | Volumetric fog (World Volume Scatter) + rain particle system | `density` (fog), `count` (rain drops), `particle_size` |
| `render_setup.py` | Cycles render: Metal GPU, 128 samples, OIDN denoiser | `samples`, `max_bounces`, `resolution_x/y` |
| `add_cinematic_fx.py` | Compositor: Glare (Fog Glow) + Lens Distortion | `threshold`, `mix`, `dispersion` |
| `fix_rain.py` | Fixes rain material for night visibility | `particle_size`, `count` |

## External Assets Used

| Asset | Source | License |
|-------|--------|---------|
| Building geometry | Blender Kit (built-in Blender 4.x) | CC0 / Free |
| HDRI Night Sky | [Poly Haven](https://polyhaven.com/hdris) — category: Night | CC0 |
| Asphalt textures | [Poly Haven Textures](https://polyhaven.com/textures) — search: asphalt, wet | CC0 |

> All external assets are CC0 (public domain) — no attribution required,
> but listed here per project requirements.

## Known Bugs and Limitations

- **Rain visibility**: In Eevee, rain drops may not be visible without running `fix_rain.py`. Use Cycles for best results.
- **Car paths**: After running `cars_setup.py`, manually move `CarPath_Forward` and `CarPath_Reverse` curves to align with the actual street in your scene.
- **POV path**: `POV_Path` starts at the world origin — move and reshape it in Edit Mode to walk along your street.
- **Motion Blur**: Enabled by default for realistic rain streaks. Increases render time slightly.
- **Render time**: ~2-5 min/frame on Apple M-series GPU with 128 samples. Full 192-frame animation ≈ 6-16 hours.
