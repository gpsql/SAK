import wave
import struct
import math

def generate_tone(filename, frequency, duration, volume=0.5, sample_rate=44100, wave_type="sine"):
    num_samples = int(duration * sample_rate)
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = float(i) / sample_rate
            if wave_type == "sine":
                value = math.sin(2.0 * math.pi * frequency * t)
            elif wave_type == "square":
                value = 1.0 if math.sin(2.0 * math.pi * frequency * t) > 0 else -1.0
            elif wave_type == "noise":
                import random
                value = random.uniform(-1.0, 1.0)
            
            # Fade out
            envelope = 1.0 - (i / num_samples)
            value = value * volume * envelope
            
            packed_value = struct.pack('h', int(value * 32767.0))
            wav_file.writeframes(packed_value)

if __name__ == "__main__":
    print("Generating sounds...")
    generate_tone("distract.wav", frequency=400, duration=0.2, volume=0.7, wave_type="noise")
    generate_tone("caught.wav", frequency=150, duration=0.8, volume=0.8, wave_type="square")
    generate_tone("win.wav", frequency=800, duration=1.0, volume=0.6, wave_type="sine")
    print("Done!")
