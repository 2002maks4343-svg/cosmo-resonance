"""
Генератор звуков для «Космо-Резонанс».
Создаёт 6 WAV-файлов в assets/sounds/.
"""
import os
import wave
import math
import numpy as np

SAMPLE_RATE = 44100
OUTPUT_DIR = "assets/sounds"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_wav(filename, samples):
    """Сохраняет numpy-массив в WAV."""
    path = os.path.join(OUTPUT_DIR, filename)
    samples = np.clip(samples, -1.0, 1.0)
    samples_int = (samples * 32767).astype(np.int16)

    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes(samples_int.tobytes())
    print(f"✓ {filename}")


def envelope(n, attack=0.01, decay=0.1, sustain=0.7, release=0.3):
    """Простая ADSR-огибающая."""
    total = n
    a = int(total * attack)
    d = int(total * decay)
    s = int(total * sustain)
    r = total - a - d - s

    env = np.zeros(total)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0:
        env[a:a + d] = np.linspace(1, 0.7, d)
    if s > 0:
        env[a + d:a + d + s] = 0.7
    if r > 0:
        env[a + d + s:] = np.linspace(0.7, 0, r)
    return env


def tone(freq, duration, wave_type="sine", volume=0.5):
    """Генерирует один тон."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    if wave_type == "sine":
        wave_data = np.sin(2 * math.pi * freq * t)
    elif wave_type == "square":
        wave_data = np.sign(np.sin(2 * math.pi * freq * t))
    elif wave_type == "saw":
        wave_data = 2 * (t * freq - np.floor(t * freq + 0.5))
    elif wave_type == "triangle":
        wave_data = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1

    return wave_data * volume


def make_sound_swipe():
    """Свайп — короткий восходящий свист."""
    duration = 0.12
    n = int(SAMPLE_RATE * duration)
    freq = np.linspace(600, 1200, n)
    phase = 2 * math.pi * np.cumsum(freq) / SAMPLE_RATE
    wave_data = np.sin(phase) * 0.4
    env = envelope(n, 0.05, 0.1, 0.5, 0.4)
    save_wav("swipe.wav", wave_data * env)


def make_sound_match():
    """Совпадение — приятный дзынь (2 тона)."""
    duration = 0.25
    tone1 = tone(880, duration, "sine", 0.4)
    tone2 = tone(1320, duration, "sine", 0.3)
    combined = tone1 + tone2
    n = len(combined)
    env = envelope(n, 0.02, 0.15, 0.5, 0.4)
    save_wav("match.wav", combined * env)


def make_sound_special():
    """Спецфигура — мощный взрыв (шум + тон)."""
    duration = 0.4
    n = int(SAMPLE_RATE * duration)
    noise = np.random.normal(0, 0.3, n)
    freq = np.linspace(400, 100, n)
    phase = 2 * math.pi * np.cumsum(freq) / SAMPLE_RATE
    low = np.sin(phase) * 0.5
    combined = noise * 0.4 + low * 0.6
    env = envelope(n, 0.01, 0.3, 0.4, 0.5)
    save_wav("special.wav", combined * env)


def make_sound_win():
    """Победа — восходящий аккорд (3 тона)."""
    duration = 0.8
    tone1 = tone(523, duration, "sine", 0.3)   # C
    tone2 = tone(659, duration, "sine", 0.3)   # E
    tone3 = tone(784, duration, "sine", 0.3)   # G
    combined = tone1 + tone2 + tone3
    n = len(combined)
    env = envelope(n, 0.02, 0.2, 0.5, 0.4)
    save_wav("win.wav", combined * env)


def make_sound_lose():
    """Провал — нисходящий тон."""
    duration = 0.7
    n = int(SAMPLE_RATE * duration)
    freq = np.linspace(400, 150, n)
    phase = 2 * math.pi * np.cumsum(freq) / SAMPLE_RATE
    wave_data = np.sin(phase) * 0.5
    env = envelope(n, 0.05, 0.2, 0.5, 0.5)
    save_wav("lose.wav", wave_data * env)


def make_sound_click():
    """Клик по кнопке — короткий щелчок."""
    duration = 0.08
    tone1 = tone(1000, duration, "square", 0.25)
    env = envelope(n=len(tone1), attack=0.01, decay=0.2,
                   sustain=0.3, release=0.5)
    save_wav("click.wav", tone1 * env)


if __name__ == "__main__":
    print("🔊 Генерация звуков...\n")
    make_sound_swipe()
    make_sound_match()
    make_sound_special()
    make_sound_win()
    make_sound_lose()
    make_sound_click()
    print(f"\n🎉 Готово! Звуки в: {OUTPUT_DIR}")