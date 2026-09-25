"""Модуль звука — воспроизведение музыки и эффектов."""
import os
from kivy.core.audio import SoundLoader


SOUNDS_DIR = "assets/sounds"
MUSIC_DIR = "assets/music"

_sounds = {}
_music_tracks = {}
_current_music = None
_current_key = None


def load_all():
    global _sounds, _music_tracks

    # Эффекты (WAV)
    files = {
        "swipe": "swipe.wav",
        "match": "match.wav",
        "special": "special.wav",
        "win": "win.wav",
        "lose": "lose.wav",
        "click": "click.wav",
    }

    for key, filename in files.items():
        path = os.path.join(SOUNDS_DIR, filename)
        if os.path.exists(path):
            snd = SoundLoader.load(path)
            if snd is not None:
                _sounds[key] = snd

    # Музыка (MP3)
    music_files = {
        "menu": "menu_music.mp3",
        "map": "map_music.mp3",
        "level": "level_music.mp3",
    }

    for key, filename in music_files.items():
        path = os.path.join(MUSIC_DIR, filename)
        if os.path.exists(path):
            snd = SoundLoader.load(path)
            if snd is not None:
                snd.loop = True
                snd.volume = 0.35
                _music_tracks[key] = snd
        else:
            print(f"⚠ Музыка не найдена: {path}")

    print(f"✅ Загружено звуков: {len(_sounds)}, музыки: {len(_music_tracks)}")


def play(key):
    snd = _sounds.get(key)
    if snd is not None:
        try:
            snd.stop()
        except Exception:
            pass
        snd.play()


def play_music(key):
    global _current_music, _current_key

    if _current_key == key and _current_music is not None:
        if _current_music.state == "play":
            return

    if _current_music is not None:
        try:
            _current_music.stop()
        except Exception:
            pass

    track = _music_tracks.get(key)
    if track is not None:
        try:
            track.play()
            _current_music = track
            _current_key = key
            print(f"🎵 Музыка: {key}")
        except Exception as e:
            print(f"⚠ Ошибка музыки: {e}")


def stop_music():
    global _current_music, _current_key
    if _current_music is not None:
        try:
            _current_music.stop()
        except Exception:
            pass
    _current_music = None
    _current_key = None


def set_music_volume(vol):
    for snd in _music_tracks.values():
        snd.volume = max(0.0, min(1.0, vol))