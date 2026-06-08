import bpy

# ─────────────────────────────────────────────────────────
# Render settings for Cycles (Mac Metal GPU)
# ─────────────────────────────────────────────────────────

def setup_render():
    scene = bpy.context.scene

    # 1. Render engine and GPU (Metal for Apple Silicon)
    scene.render.engine = 'CYCLES'

    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'METAL'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = True

    scene.cycles.device = 'GPU'

    # 2. Night scene optimisation
    # 128 samples + AI denoiser gives good quality without long wait
    scene.cycles.samples = 128
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'  # Works well on Mac

    # Limit bounces (night scene doesn't need many, saves render time)
    scene.cycles.max_bounces = 4
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 3
    scene.cycles.transmission_bounces = 4
    scene.cycles.volume_bounces = 0

    # 3. Volumetric settings (prevent endless render time)
    scene.cycles.volume_step_rate = 1.0
    scene.cycles.volume_max_steps = 256

    # 4. Cinematic look
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5

    # Color management
    scene.view_settings.look = 'High Contrast'

    # 5. Output: 1080p, 24 FPS, MP4
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100

    scene.frame_start = 1
    scene.frame_end = 192  # 8 seconds * 24 fps
    scene.render.fps = 24

    scene.render.image_settings.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'HIGH'

    scene.render.filepath = "//POV_NightCity_Render.mp4"

    print("  Engine: Cycles (Metal GPU)")
    print("  Samples: 128 + OpenImageDenoise")
    print("  Output: 1920x1080, 24 FPS, MP4")
    print("  Save path: next to project file as 'POV_NightCity_Render.mp4'")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  RENDER SETUP")
    print("="*50)
    setup_render()
    print("="*50)
