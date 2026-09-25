"""
Генератор реалистичных планет (NASA-стиль) для «Космо-Резонанс».
Использует шум Перлина для континентов и облаков.
"""
import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from perlin_noise import PerlinNoise

# --- Настройки ---
SIZE = 256
PLANET_R = 95
CENTER = SIZE // 2
OUTPUT_DIR = "assets/planets"

os.makedirs(OUTPUT_DIR, exist_ok=True)
random.seed(42)
np.random.seed(42)


# ---------- Маски ----------

def circle_mask(radius, center, blur=1):
    mask = Image.new("L", (SIZE, SIZE), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse(
        [center[0] - radius, center[1] - radius,
         center[0] + radius, center[1] + radius],
        fill=255
    )
    if blur:
        mask = mask.filter(ImageFilter.GaussianBlur(blur))
    return mask


def spherical_map(size):
    """
    Создаёт карту для сферической проекции.
    Возвращает: nx, ny (нормализованные координаты -1..1), mask (круг), z (глубина).
    """
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    nx = (xx - w / 2) / (w / 2)
    ny = (yy - h / 2) / (h / 2)
    r2 = nx ** 2 + ny ** 2
    mask = r2 <= 1.0
    z = np.sqrt(np.clip(1 - r2, 0, 1))
    return nx, ny, z, mask


# ---------- Генерация поверхности шумом ----------

def fractal_noise(width, height, scale=3.0, octaves=5, persistence=0.55):
    """Многослойный шум Перлина — даёт реалистичные континенты."""
    noise = PerlinNoise(octaves=octaves, seed=42)
    result = np.zeros((height, width))
    for y in range(height):
        for x in range(width):
            result[y][x] = noise([x / width * scale, y / height * scale])
    return result


def make_surface_texture(base_color, dark_color, light_color, scale=3.0,
                         sea_level=-0.1, has_clouds=False):
    """
    Создаёт текстуру поверхности с континентами и океанами.
    base_color — цвет суши
    dark_color — цвет океана
    light_color — цвет возвышенностей (горы/снег)
    """
    noise = fractal_noise(SIZE, SIZE, scale=scale, octaves=6, persistence=0.5)

    base = np.array(base_color, dtype=float)
    dark = np.array(dark_color, dtype=float)
    light = np.array(light_color, dtype=float)

    tex = np.zeros((SIZE, SIZE, 3), dtype=float)
    for y in range(SIZE):
        for x in range(SIZE):
            n = noise[y][x]
            if n < sea_level:
                # океан
                depth = np.clip((sea_level - n) * 2, 0, 1)
                tex[y, x] = base * (1 - depth) + dark * depth
            else:
                # суша
                height = np.clip((n - sea_level) * 1.5, 0, 1)
                tex[y, x] = base * (1 - height) + light * height

    # Облака (опционально)
    if has_clouds:
        cloud_noise = fractal_noise(SIZE, SIZE, scale=5.0, octaves=4, persistence=0.6)
        for y in range(SIZE):
            for x in range(SIZE):
                c = cloud_noise[y][x]
                if c > 0.15:
                    alpha = min((c - 0.15) * 2.5, 0.85)
                    tex[y, x] = tex[y, x] * (1 - alpha) + np.array([255, 255, 255]) * alpha

    return tex.astype(np.uint8)


# ---------- Сплющивание текстуры на сферу ----------

def apply_sphere_shading(texture_rgb, light=(0.4, 0.35)):
    """
    Накладывает светотень на текстуру — делает её объёмной сферой.
    Свет сверху-слева.
    """
    nx, ny, z, mask = spherical_map((SIZE, SIZE))

    # Вектор света
    lx, ly, lz = light[0], light[1], 0.8
    length = math.sqrt(lx ** 2 + ly ** 2 + lz ** 2)
    lx, ly, lz = lx / length, ly / length, lz / length

    # Нормали сферы
    nxs = np.where(mask, nx, 0)
    nys = np.where(mask, ny, 0)
    nzs = z

    # Диффузное освещение
    diffuse = nxs * lx + nys * ly + nzs * lz
    diffuse = np.clip(diffuse, 0, 1)
    # Атмосферный минимум — тёмная сторона не чёрная
    diffuse = 0.15 + 0.85 * diffuse

    # Зеркальный блик
    spec = np.clip(diffuse, 0, 1) ** 30

    # Тень по краю (лимб)
    limb = np.where(mask, z, 0) ** 0.35

    rgb = texture_rgb.astype(float)
    rgb *= diffuse[..., None] * limb[..., None]
    rgb += spec[..., None] * 200

    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    return rgb, mask


# ---------- Генерация планеты ----------

def make_planet(name, base_color, dark_color, light_color, glow_color,
                scale=3.0, sea_level=-0.1, has_clouds=False,
                has_ring=False, ring_color=(210, 220, 240, 180)):
    """Создаёт реалистичную планету."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # 1. Текстура поверхности
    texture = make_surface_texture(base_color, dark_color, light_color,
                                    scale=scale, sea_level=sea_level,
                                    has_clouds=has_clouds)

    # 2. Светотень (объём)
    shaded, mask = apply_sphere_shading(texture)

    # 3. Собираем планету
    planet = Image.fromarray(shaded, "RGB").convert("RGBA")
    planet.putalpha(circle_mask(PLANET_R, (CENTER, CENTER), blur=1))

    # 4. Атмосферное свечение по краю
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse(
        [CENTER - PLANET_R - 6, CENTER - PLANET_R - 6,
         CENTER + PLANET_R + 6, CENTER + PLANET_R + 6],
        fill=(glow_color[0], glow_color[1], glow_color[2], 150)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(12))
    img = Image.alpha_composite(img, glow)

    # 5. Кольцо — задняя половина
    ring = None
    if has_ring:
        ring = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        rd = ImageDraw.Draw(ring)
        for w in range(10):
            rd.ellipse(
                [CENTER - PLANET_R - 55 + w * 3,
                 CENTER - 22 + w * 2,
                 CENTER + PLANET_R + 55 - w * 3,
                 CENTER + 22 - w * 2],
                outline=ring_color, width=2
            )
        ring = ring.filter(ImageFilter.GaussianBlur(1))
        back = ring.crop((0, 0, SIZE, CENTER))
        img.paste(back, (0, 0), back)

    # 6. Планета
    img = Image.alpha_composite(img, planet)

    # 7. Передняя половина кольца
    if has_ring:
        front = ring.crop((0, CENTER, SIZE, SIZE))
        img.paste(front, (0, CENTER), front)

    # 8. Тень от кольца на планете (для газовой)
    if has_ring:
        ring_shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        rsd = ImageDraw.Draw(ring_shadow)
        rsd.ellipse(
            [CENTER - PLANET_R + 10, CENTER - 15,
             CENTER + PLANET_R - 10, CENTER + 15],
            fill=(0, 0, 0, 80)
        )
        ring_shadow = ring_shadow.filter(ImageFilter.GaussianBlur(6))
        ring_shadow.putalpha(Image.composite(
            ring_shadow.split()[3],
            Image.new("L", (SIZE, SIZE), 0),
            circle_mask(PLANET_R, (CENTER, CENTER))
        ))
        img = Image.alpha_composite(img, ring_shadow)

    # 9. Финальный блик
    highlight = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd = ImageDraw.Draw(highlight)
    hd.ellipse(
        [CENTER - PLANET_R + 25, CENTER - PLANET_R + 20,
         CENTER - PLANET_R + 55, CENTER - PLANET_R + 42],
        fill=(255, 255, 255, 120)
    )
    highlight = highlight.filter(ImageFilter.GaussianBlur(8))
    highlight.putalpha(Image.composite(
        highlight.split()[3],
        Image.new("L", (SIZE, SIZE), 0),
        circle_mask(PLANET_R, (CENTER, CENTER))
    ))
    img = Image.alpha_composite(img, highlight)

    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    img.save(path)
    print(f"✓ {name}.png")


# ---------- Запуск ----------

if __name__ == "__main__":
    print("🪐 Генерация реалистичных планет...\n")
    print("(это займёт ~1-2 минуты — шум Перлина считается долго)\n")

    # Лавовая — красно-оранжевая, без океанов
    make_planet(
        "lava",
        base_color=(200, 60, 30),
        dark_color=(60, 10, 5),
        light_color=(255, 200, 80),
        glow_color=(255, 90, 40),
        scale=4.0, sea_level=-0.5
    )

    # Ледяная — голубая с океанами и белыми шапками, с кольцом
    make_planet(
        "ice",
        base_color=(120, 180, 230),
        dark_color=(20, 60, 120),
        light_color=(240, 250, 255),
        glow_color=(120, 200, 255),
        scale=3.0, sea_level=0.0,
        has_ring=True, ring_color=(220, 235, 255, 180)
    )

    # Джунгли — зелёная с синими океанами и облаками
    make_planet(
        "jungle",
        base_color=(60, 140, 60),
        dark_color=(20, 60, 120),
        light_color=(220, 240, 180),
        glow_color=(90, 200, 120),
        scale=3.0, sea_level=-0.1,
        has_clouds=True
    )

    # Пустынная — песочная, без океанов
    make_planet(
        "desert",
        base_color=(220, 180, 100),
        dark_color=(120, 60, 20),
        light_color=(255, 230, 160),
        glow_color=(255, 200, 80),
        scale=3.5, sea_level=-0.4
    )

    # Газовая — фиолетовые полосы, с кольцом
    make_planet(
        "gas",
        base_color=(160, 110, 220),
        dark_color=(70, 30, 130),
        light_color=(230, 200, 255),
        glow_color=(190, 110, 255),
        scale=2.0, sea_level=-0.6,
        has_ring=True, ring_color=(200, 170, 255, 170)
    )

    # Лунная — серая с кратерами
    make_planet(
        "moon",
        base_color=(180, 180, 190),
        dark_color=(70, 70, 80),
        light_color=(230, 230, 240),
        glow_color=(200, 210, 240),
        scale=5.0, sea_level=-0.5
    )

    print(f"\n🎉 Готово! Планеты в папке: {OUTPUT_DIR}")