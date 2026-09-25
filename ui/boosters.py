"""Логика бустеров."""
import random
import os
from kivy.graphics.texture import Texture
from PIL import Image as PILImage


# Все бустеры: id, иконка PNG, название
BOOSTERS = [
    {"id": "hammer", "icon_file": "hammer.png", "name": "МОЛОТ"},
    {"id": "shuffle", "icon_file": "shuffle.png", "name": "ПЕРЕМЕШ."},
    {"id": "rocket", "icon_file": "rocket.png", "name": "РАКЕТА"},
    {"id": "freeze", "icon_file": "freeze.png", "name": "ЗАМОРОЗКА"},
    {"id": "double", "icon_file": "double.png", "name": "×2"},
]

ASSETS_DIR = "assets/boosters"
START_COUNT = 3
NEEDS_TARGET = {"hammer", "rocket"}


def load_booster_textures():
    textures = {}
    for b in BOOSTERS:
        path = os.path.join(ASSETS_DIR, b["icon_file"])
        if not os.path.exists(path):
            print(f"⚠ Файл не найден: {path}")
            continue
        pil_img = PILImage.open(path).convert("RGBA")
        tex = Texture.create(size=pil_img.size, colorfmt="rgba")
        tex.blit_buffer(pil_img.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
        tex.flip_vertical()
        textures[b["id"]] = tex
    return textures


def init_boosters(game):
    """Инициализирует счётчики бустеров — берём из progress игрока."""
    # Пытаемся взять из progress
    from kivy.app import App
    app = App.get_running_app()

    if app is not None and hasattr(app, "progress"):
        progress_boosters = app.progress.get("boosters", {})
        game.boosters = {}
        for b in BOOSTERS:
            game.boosters[b["id"]] = progress_boosters.get(b["id"], START_COUNT)
    else:
        # Фолбэк — 3 каждого
        game.boosters = {b["id"]: START_COUNT for b in BOOSTERS}

    game.pending_booster = None
    game.booster_textures = load_booster_textures()


def _save_boosters_to_progress(game):
    """Сохраняет текущее количество бустеров в progress."""
    from kivy.app import App
    from save import progress as prog

    app = App.get_running_app()
    if app is None:
        return

    if "boosters" not in app.progress:
        app.progress["boosters"] = {}
    app.progress["boosters"] = dict(game.boosters)
    prog.save_progress(app.progress)


def use_booster(game, booster_id):
    """Активирует бустер по id."""
    if game.boosters.get(booster_id, 0) <= 0:
        print(f"⚠ Бустер {booster_id} закончился")
        return False

    if game.animating or game.level_done:
        return False

    if booster_id in NEEDS_TARGET:
        game.pending_booster = booster_id
        print(f"🎯 Бустер {booster_id}: тапни по полю")
        return True

    if booster_id == "shuffle":
        _apply_shuffle(game)
    elif booster_id == "freeze":
        _apply_freeze(game)
    elif booster_id == "double":
        _apply_double(game)

    game.boosters[booster_id] -= 1
    _save_boosters_to_progress(game)
    game.update_hud()
    return True


def apply_booster_on_cell(game, booster_id, r, c):
    """Применяет бустер к клетке (r, c)."""
    if game.boosters.get(booster_id, 0) <= 0:
        return

    if booster_id == "hammer":
        _apply_hammer(game, r, c)
    elif booster_id == "rocket":
        _apply_rocket(game, r, c)

    game.boosters[booster_id] -= 1
    _save_boosters_to_progress(game)
    game.pending_booster = None
    game.update_hud()


# ---------- Мгновенные ----------

def _apply_shuffle(game):
    from engine.match import is_special
    normal_cells = []
    normal_values = []
    for r in range(game.board.rows):
        for c in range(game.board.cols):
            v = game.board.grid[r][c]
            if v is not None and not is_special(v):
                normal_cells.append((r, c))
                normal_values.append(v)

    random.shuffle(normal_values)

    for (r, c), v in zip(normal_cells, normal_values):
        game.board.grid[r][c] = v

    print("🔄 Перемешано")
    game.redraw_dynamic()


def _apply_freeze(game):
    game.moves_left += 3
    print(f"❄ +3 хода, теперь {game.moves_left}")


def _apply_double(game):
    game.double_score_turns = 5
    print(f"✦ ×2 очки на {game.double_score_turns} ходов")


# ---------- По клетке ----------

def _apply_hammer(game, r, c):
    if not (0 <= r < game.board.rows and 0 <= c < game.board.cols):
        return
    if game.board.grid[r][c] is None:
        return
    print(f"⚒ Молот по ({r},{c})")
    cells = {(r, c)}
    game._explode_cells(cells)


def _apply_rocket(game, r, c):
    if not (0 <= r < game.board.rows and 0 <= c < game.board.cols):
        return
    print(f"⇉ Ракета по ({r},{c}) — весь ряд")
    cells = {(r, c2) for c2 in range(game.board.cols)}
    game._explode_cells(cells)