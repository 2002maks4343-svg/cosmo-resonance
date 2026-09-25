"""Рисование поля, звёзд, планет и спецфигур."""
import os
import random
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.graphics.texture import Texture
from PIL import Image as PILImage
from engine.match import (
    is_special, base_planet_of_special, special_kind,
    is_hole, is_meteor, is_ice, base_planet_of_ice,
    HOLE, METEOR,
)


ASSETS_DIR = "assets/planets"
SPECIALS_DIR = "assets/specials"

PLANET_FILES = {
    0: "lava",
    1: "ice",
    2: "jungle",
    3: "desert",
    4: "gas",
    5: "moon",
}

SPECIAL_FILES = {
    "supernova": "supernova",
    "blackhole": "blackhole",
    "lightning_v": "lightning_v",
    "lightning_h": "lightning_h",
    "meteor": "meteor",
}


# ---------- Загрузка ----------

def _load_texture(path):
    pil_img = PILImage.open(path).convert("RGBA")
    tex = Texture.create(size=pil_img.size, colorfmt="rgba")
    tex.blit_buffer(pil_img.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
    tex.flip_vertical()
    return tex


def load_planet_textures():
    textures = {}
    for idx, name in PLANET_FILES.items():
        path = os.path.join(ASSETS_DIR, f"{name}.png")
        if not os.path.exists(path):
            print(f"⚠ Файл не найден: {path}")
            continue
        textures[idx] = _load_texture(path)
    return textures


def load_special_textures():
    textures = {}
    for kind, name in SPECIAL_FILES.items():
        path = os.path.join(SPECIALS_DIR, f"{name}.png")
        if not os.path.exists(path):
            print(f"⚠ Файл не найден: {path}")
            continue
        textures[kind] = _load_texture(path)
    return textures


def generate_stars(count=150, seed=7):
    random.seed(seed)
    return [
        (random.uniform(0, 1), random.uniform(0, 1),
         random.uniform(1, 2.5), random.uniform(0.3, 1.0))
        for _ in range(count)
    ]


# ---------- Геометрия ----------

def get_side_panel_width(widget):
    return 100


def get_grid_geometry(widget):
    """Поле между панелями (левая шире правой). Размер — из board."""
    margin = 10
    gap = 10
    left_panel = 150
    right_panel = 100

    # Берём размеры поля из board (rows, cols)
    rows = getattr(widget.board, "rows", 8)
    cols = getattr(widget.board, "cols", 8)

    left_edge = margin + left_panel + gap
    right_edge = widget.width - margin - right_panel - gap
    avail_w = right_edge - left_edge
    avail_h = widget.height - margin * 2
    grid_size = min(avail_w, avail_h)

    offset_x = left_edge + (avail_w - grid_size) / 2
    offset_y = margin + (avail_h - grid_size) / 2
    cell = grid_size / cols
    return offset_x, offset_y, grid_size, cell


def cell_to_xy(r, c, cell, offset_x, offset_y, padding=0, rows=8):
    """Координаты клетки (r, c) → нижний левый угол."""
    x = offset_x + c * cell + padding
    y = offset_y + (rows - 1 - r) * cell + padding
    return x, y


def screen_to_cell(x, y, widget):
    offset_x, offset_y, grid_size, cell = get_grid_geometry(widget)
    if not (offset_x <= x <= offset_x + grid_size):
        return None
    if not (offset_y <= y <= offset_y + grid_size):
        return None

    rows = getattr(widget.board, "rows", 8)
    cols = getattr(widget.board, "cols", 8)

    c = int((x - offset_x) // cell)
    r = rows - 1 - int((y - offset_y) // cell)
    if 0 <= r < rows and 0 <= c < cols:
        return (r, c)
    return None


# ---------- Отрисовка ----------

def draw_grid(canvas, widget):
    offset_x, offset_y, grid_size, cell = get_grid_geometry(widget)
    rows = getattr(widget.board, "rows", 8)
    cols = getattr(widget.board, "cols", 8)

    with canvas:
        # Подложка
        Color(0.04, 0.06, 0.12, 1)
        Rectangle(pos=(offset_x, offset_y), size=(grid_size, grid_size))

        # Сетка
        Color(0.3, 0.7, 1.0, 0.4)
        for c in range(cols + 1):
            x = offset_x + c * cell
            Line(points=[x, offset_y, x, offset_y + grid_size], width=1.0)
        for r in range(rows + 1):
            y = offset_y + r * cell
            Line(points=[offset_x, y, offset_x + grid_size, y], width=1.0)

        # Рамка
        Color(0.4, 0.8, 1.0, 1.0)
        Line(rectangle=(offset_x, offset_y, grid_size, grid_size), width=2.5)


def _draw_one_cell(group, r, c, value, planet_textures, special_textures,
                   offset_x, offset_y, cell, rows, offset_y_shift=0.0):
    """Рисует одну клетку — планету, спецфигуру, лёд или метеорит."""
    padding = cell * 0.12
    planet_size = cell - padding * 2
    x, y = cell_to_xy(r, c, cell, offset_x, offset_y, padding, rows)
    y -= offset_y_shift * cell

    # --- Дырка ---
    if value == HOLE:
        return  # ничего не рисуем

    # --- Метеорит ---
    if value == METEOR:
        tex = special_textures.get("meteor")
        if tex is not None:
            # Метеорит чуть больше обычной планеты
            m_size = cell * 0.95
            mx = x - (m_size - planet_size) / 2
            my = y - (m_size - planet_size) / 2
            group.add(Color(1, 1, 1, 1))
            group.add(Rectangle(texture=tex, pos=(mx, my),
                                size=(m_size, m_size)))
        return

    # --- Лёд (планета подо льдом) ---
    if is_ice(value):
        base_planet = base_planet_of_ice(value)
        tex = planet_textures.get(base_planet)
        if tex is not None:
            group.add(Color(1, 1, 1, 1))
            group.add(Rectangle(texture=tex, pos=(x, y),
                                size=(planet_size, planet_size)))
        # Ледяная рамка
        group.add(Color(0.7, 0.9, 1.0, 0.6))
        group.add(Rectangle(pos=(x, y), size=(planet_size, planet_size)))
        group.add(Color(0.9, 1.0, 1.0, 1.0))
        group.add(Line(rectangle=(x, y, planet_size, planet_size), width=3))
        # Внутренняя снежинка-«иней»
        group.add(Color(1, 1, 1, 0.5))
        group.add(Line(points=[
            x + planet_size * 0.3, y + planet_size * 0.3,
            x + planet_size * 0.7, y + planet_size * 0.7,
        ], width=2))
        group.add(Line(points=[
            x + planet_size * 0.7, y + planet_size * 0.3,
            x + planet_size * 0.3, y + planet_size * 0.7,
        ], width=2))
        return

    # --- Спецфигура ---
    if is_special(value):
        kind = special_kind(value)
        base_planet = base_planet_of_special(value)

        base_tex = planet_textures.get(base_planet)
        if base_tex is not None:
            group.add(Color(0.6, 0.6, 0.6, 0.6))
            group.add(Rectangle(texture=base_tex, pos=(x, y),
                                size=(planet_size, planet_size)))

        sp_tex = special_textures.get(kind)
        if sp_tex is not None:
            group.add(Color(1, 1, 1, 1))
            group.add(Rectangle(texture=sp_tex, pos=(x, y),
                                size=(planet_size, planet_size)))
        return

    # --- Обычная планета ---
    tex = planet_textures.get(value)
    if tex is not None:
        group.add(Color(1, 1, 1, 1))
        group.add(Rectangle(texture=tex, pos=(x, y),
                            size=(planet_size, planet_size)))


def draw_planets_to_group(group, widget, board, textures, fading, fall_offsets,
                          special_textures=None):
    offset_x, offset_y, grid_size, cell = get_grid_geometry(widget)
    rows = board.rows
    cols = board.cols
    padding = cell * 0.12
    planet_size = cell - padding * 2
    fading_cells = {f["cell"] for f in fading}

    if special_textures is None:
        special_textures = {}

    for r in range(rows):
        for c in range(cols):
            if (r, c) in fading_cells:
                continue
            value = board.grid[r][c]
            if value is None:
                continue
            shift = fall_offsets.get((r, c), 0.0)
            _draw_one_cell(group, r, c, value, textures,
                           special_textures, offset_x, offset_y, cell, rows,
                           shift)

    # Исчезающие
    for f in fading:
        r, c = f["cell"]
        p = f["progress"]
        scale = 1.0 - p * 0.85
        alpha = 1.0 - p
        x, y = cell_to_xy(r, c, cell, offset_x, offset_y, padding, rows)
        shrink = planet_size * (1 - scale) / 2
        x += shrink
        y += shrink
        size = planet_size * scale

        tex_idx = f["tex_idx"]

        if tex_idx == HOLE:
            continue

        if tex_idx == METEOR:
            tex = special_textures.get("meteor")
            if tex is None:
                continue
            group.add(Color(1, 1, 1, alpha))
            group.add(Rectangle(texture=tex, pos=(x, y), size=(size, size)))
            continue

        if is_ice(tex_idx):
            base_planet = base_planet_of_ice(tex_idx)
            base_tex = textures.get(base_planet)
            if base_tex is not None:
                group.add(Color(1, 1, 1, alpha))
                group.add(Rectangle(texture=base_tex, pos=(x, y), size=(size, size)))
            # Ледяная рамка
            group.add(Color(0.9, 1.0, 1.0, alpha))
            group.add(Line(rectangle=(x, y, size, size), width=2))
            continue

        if is_special(tex_idx):
            kind = special_kind(tex_idx)
            base_planet = base_planet_of_special(tex_idx)
            base_tex = textures.get(base_planet)
            if base_tex is not None:
                group.add(Color(1, 1, 1, alpha * 0.5))
                group.add(Rectangle(texture=base_tex, pos=(x, y), size=(size, size)))
            sp_tex = special_textures.get(kind)
            if sp_tex is not None:
                group.add(Color(1, 1, 1, alpha))
                group.add(Rectangle(texture=sp_tex, pos=(x, y), size=(size, size)))
            continue

        tex = textures.get(tex_idx)
        if tex is None:
            continue
        group.add(Color(1, 1, 1, alpha))
        group.add(Rectangle(texture=tex, pos=(x, y), size=(size, size)))


def draw_selection_to_group(group, widget, selected_cell):
    if not selected_cell:
        return
    offset_x, offset_y, grid_size, cell = get_grid_geometry(widget)
    rows = getattr(widget.board, "rows", 8)
    r, c = selected_cell
    x = offset_x + c * cell
    y = offset_y + (rows - 1 - r) * cell
    group.add(Color(1, 1, 0.3, 0.8))
    group.add(Line(rectangle=(x + 2, y + 2, cell - 4, cell - 4), width=3))