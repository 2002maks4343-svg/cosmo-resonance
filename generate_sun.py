"""
Генератор стилизованного солнца для «Космо-Резонанс».
Перезаписывает assets/specials/supernova.png.
"""
import os
import math
from PIL import Image, ImageDraw, ImageFilter

SIZE = 256
CX = SIZE // 2
CY = SIZE // 2
OUTPUT_DIR = "assets/specials"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def radial_gradient_smooth(size, inner_color, outer_color, radius):
    """Гладкий радиальный градиент."""
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    cx, cy = size[0] // 2, size[1] // 2

    # Рисуем через несколько концентрических кругов
    for r in range(int(radius), 0, -1):
        t = r / radius  # 1.0 → 0.0
        # Цвет между inner и outer
        cr = int(inner_color[0] * (1 - t) + outer_color[0] * t)
        cg = int(inner_color[1] * (1 - t) + outer_color[1] * t)
        cb = int(inner_color[2] * (1 - t) + outer_color[2] * t)
        alpha = int(255 * (1 - t ** 2))
        d = ImageDraw.Draw(img)
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=(cr, cg, cb, alpha))
    return img


def make_sun():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # === 1. Внешние кольца (стилизованные ореолы) ===
    ring1 = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rd1 = ImageDraw.Draw(ring1)
    rd1.ellipse([CX - 115, CY - 115, CX + 115, CY + 115],
                outline=(255, 140, 40, 90), width=6)
    img = Image.alpha_composite(img, ring1)

    ring2 = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rd2 = ImageDraw.Draw(ring2)
    rd2.ellipse([CX - 100, CY - 100, CX + 100, CY + 100],
                outline=(255, 180, 60, 150), width=5)
    img = Image.alpha_composite(img, ring2)

    # === 2. Лучи (8 крупных) ===
    rays = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(rays)

    n_rays = 8
    for i in range(n_rays):
        angle = (360 / n_rays) * i
        rad = math.radians(angle)
        dx = math.cos(rad)
        dy = math.sin(rad)
        px, py = -dy, dx

        # Внешняя точка луча
        outer_r = 108
        # Ширина у основания
        base_w = 14

        pts = [
            (CX + dx * outer_r, CY + dy * outer_r),
            (CX + px * base_w, CY + py * base_w),
            (CX - px * base_w, CY - py * base_w),
        ]
        rdraw.polygon(pts, fill=(255, 190, 70, 230))

    # Мягкое размытие лучей
    rays = rays.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, rays)

    # === 3. Основной диск — гладкий градиент ===
    disc = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)

    # Слой градиента от центра
    for r in range(70, 0, -1):
        t = r / 70
        # Ядро: почти белый центр → жёлто-оранжевый край
        cr = int(255 * (1 - t * 0.1))
        cg = int(255 - t * 70)
        cb = int(220 - t * 190)
        d = ImageDraw.Draw(disc)
        d.ellipse([CX - r, CY - r, CX + r, CY + r],
                  fill=(cr, cg, cb, 255))

    img = Image.alpha_composite(img, disc)

    # === 4. Чёткий контур диска ===
    outline = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    od = ImageDraw.Draw(outline)
    od.ellipse([CX - 70, CY - 70, CX + 70, CY + 70],
               outline=(255, 130, 30, 255), width=4)
    img = Image.alpha_composite(img, outline)

    # === 5. Большой мягкий ореол позади (для свечения) ===
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([CX - 110, CY - 110, CX + 110, CY + 110],
               fill=(255, 180, 60, 60))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(glow, img)

    # === 6. Яркая точка блика сверху-слева ===
    hl = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hl)
    hd.ellipse([CX - 45, CY - 50, CX - 15, CY - 20],
               fill=(255, 255, 255, 230))
    hl = hl.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img, hl)

    img.save(os.path.join(OUTPUT_DIR, "supernova.png"))
    print("✓ supernova.png (стилизованное солнце)")


if __name__ == "__main__":
    print("☀️ Генерация стилизованного солнца...\n")
    make_sun()
    print("\n🎉 Готово!")