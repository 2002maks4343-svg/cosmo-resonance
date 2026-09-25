"""
Генератор спецфигур для «Космо-Резонанс».
Создаёт: сверхновая, чёрная дыра, молния вертикальная, молния горизонтальная.
"""
import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 256
CENTER = SIZE // 2
OUTPUT_DIR = "assets/specials"

os.makedirs(OUTPUT_DIR, exist_ok=True)
random.seed(42)
np.random.seed(42)


# ---------- Утилиты ----------

def radial_gradient_alpha(size, color_core, color_edge, radius, power=1.0):
    w, h = size
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    dist = np.clip(dist / radius, 0, 1) ** power
    alpha = (1 - dist) * 255
    alpha = np.clip(alpha, 0, 255).astype(np.uint8)

    core = np.array(color_core, dtype=float)
    edge = np.array(color_edge, dtype=float)
    rgb = core[None, None, :] * (1 - dist[..., None]) + edge[None, None, :] * dist[..., None]

    rgba = np.dstack([rgb.astype(np.uint8), alpha])
    return Image.fromarray(rgba, "RGBA")


def glow_layer(size, color, radius, blur=20, alpha=200):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = size[0] // 2, size[1] // 2
    d.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
              fill=(color[0], color[1], color[2], alpha))
    return layer.filter(ImageFilter.GaussianBlur(blur))


# ---------- СВЕРХНОВАЯ ----------

def make_supernova():
    """Сверхновая — яркая вспышка с лучами."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    rays = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)

    n_rays = 12
    for i in range(n_rays):
        angle = (360 / n_rays) * i + random.uniform(-8, 8)
        rad = math.radians(angle)
        length = random.uniform(85, 115)
        width = random.uniform(3, 6)
        dx = math.cos(rad)
        dy = math.sin(rad)
        px, py = -dy, dx
        pts = [
            (CENTER + dx * length, CENTER + dy * length),
            (CENTER + px * width, CENTER + py * width),
            (CENTER - px * width, CENTER - py * width),
        ]
        rd.polygon(pts, fill=(255, 230, 150, 200))

    rays = rays.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, rays)

    glow = glow_layer((SIZE, SIZE), (255, 200, 100), 70, blur=30, alpha=200)
    img = Image.alpha_composite(img, glow)

    mid = glow_layer((SIZE, SIZE), (255, 140, 60), 45, blur=20, alpha=220)
    img = Image.alpha_composite(img, mid)

    core = radial_gradient_alpha(
        (SIZE, SIZE),
        color_core=(255, 255, 255),
        color_edge=(255, 220, 130),
        radius=35,
        power=0.6,
    )
    img = Image.alpha_composite(img, core)

    img.save(os.path.join(OUTPUT_DIR, "supernova.png"))
    print("✓ supernova.png")


# ---------- ЧЁРНАЯ ДЫРА ----------

def make_blackhole():
    """Чёрная дыра — тёмный диск с аккреционным диском."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    glow = glow_layer((SIZE, SIZE), (120, 60, 220), 95, blur=25, alpha=150)
    img = Image.alpha_composite(img, glow)

    disk = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disk)

    for i, (w, h, color, alpha) in enumerate([
        (115, 30, (255, 180, 80), 230),
        (125, 36, (255, 120, 40), 200),
        (135, 42, (200, 60, 180), 170),
        (145, 50, (120, 40, 220), 140),
        (155, 58, (60, 20, 150), 100),
    ]):
        cx, cy = CENTER, CENTER
        dd.ellipse([cx - w, cy - h, cx + w, cy + h],
                   outline=color + (alpha,), width=4)
    disk = disk.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, disk)

    black = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bd = ImageDraw.Draw(black)
    bd.ellipse([CENTER - 48, CENTER - 48, CENTER + 48, CENTER + 48],
               fill=(0, 0, 0, 255))
    black = black.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, black)

    ring = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rgd = ImageDraw.Draw(ring)
    rgd.ellipse([CENTER - 48, CENTER - 48, CENTER + 48, CENTER + 48],
                outline=(255, 200, 100, 200), width=2)
    ring = ring.filter(ImageFilter.GaussianBlur(1.5))
    img = Image.alpha_composite(img, ring)

    img.save(os.path.join(OUTPUT_DIR, "blackhole.png"))
    print("✓ blackhole.png")


# ---------- МОЛНИИ ----------

def _draw_lightning_common(img, points, sparks_dirs=None):
    """Общая часть рисования молнии."""
    # Внешнее свечение
    glow = glow_layer((SIZE, SIZE), (100, 180, 255), 55, blur=25, alpha=170)
    img = Image.alpha_composite(img, glow)

    inner = glow_layer((SIZE, SIZE), (220, 240, 255), 30, blur=15, alpha=200)
    img = Image.alpha_composite(img, inner)

    # Зигзаг
    bolt = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    bd = ImageDraw.Draw(bolt)
    bd.line(points, fill=(180, 220, 255, 180), width=14, joint="curve")
    bd.line(points, fill=(220, 240, 255, 230), width=9, joint="curve")
    bd.line(points, fill=(255, 255, 255, 255), width=4, joint="curve")
    bolt = bolt.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, bolt)

    # Искры
    sparks = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sparks)
    for _ in range(8):
        ang = random.uniform(0, 2 * math.pi)
        dist = random.uniform(35, 70)
        sx = CENTER + math.cos(ang) * dist
        sy = CENTER + math.sin(ang) * dist
        r = random.uniform(2, 4)
        sd.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(220, 240, 255, 200))
    sparks = sparks.filter(ImageFilter.GaussianBlur(1.5))
    img = Image.alpha_composite(img, sparks)

    return img


def make_lightning_v():
    """Молния вертикальная — уничтожает столбец."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    points = [
        (CENTER, CENTER - 90),
        (CENTER - 18, CENTER - 35),
        (CENTER + 14, CENTER - 10),
        (CENTER - 14, CENTER + 20),
        (CENTER + 18, CENTER + 55),
        (CENTER, CENTER + 90),
    ]

    img = _draw_lightning_common(img, points)
    img.save(os.path.join(OUTPUT_DIR, "lightning_v.png"))
    print("✓ lightning_v.png")


def make_lightning_h():
    """Молния горизонтальная — уничтожает ряд."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # Те же точки, но с обменом X и Y — зигзаг идёт слева направо
    points = [
        (CENTER - 90, CENTER),
        (CENTER - 35, CENTER - 18),
        (CENTER - 10, CENTER + 14),
        (CENTER + 20, CENTER - 14),
        (CENTER + 55, CENTER + 18),
        (CENTER + 90, CENTER),
    ]

    img = _draw_lightning_common(img, points)
    img.save(os.path.join(OUTPUT_DIR, "lightning_h.png"))
    print("✓ lightning_h.png")


# ---------- Запуск ----------

if __name__ == "__main__":
    print("✨ Генерация спецфигур...\n")
    make_supernova()
    make_blackhole()
    make_lightning_v()
    make_lightning_h()
    print(f"\n🎉 Готово! Спецфигуры в папке: {OUTPUT_DIR}")