"""
Генератор спрайта метеорита для «Космо-Резонанс».
Создаёт assets/specials/meteor.png — оранжевый шар с хвостом.
"""
import os
import math
from PIL import Image, ImageDraw, ImageFilter

SIZE = 256
CX = SIZE // 2
CY = SIZE // 2
OUTPUT_DIR = "assets/specials"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def make_meteor():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # === Хвост (длинный, вверх-вправо) ===
    tail = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    td = ImageDraw.Draw(tail)

    # Хвост — треугольник от центра вверх-вправо
    layers = [
        (60, (255, 240, 180, 220)),
        (50, (255, 200, 80, 180)),
        (40, (255, 140, 40, 140)),
        (28, (255, 80, 20, 100)),
    ]
    for length, color in layers:
        pts = [
            (CX + 20, CY - 30),
            (CX - 20, CY + 20),
            (CX + length + 70, CY - length - 40),
        ]
        td.polygon(pts, fill=color)

    tail = tail.filter(ImageFilter.GaussianBlur(12))
    img = Image.alpha_composite(img, tail)

    # === Внешнее свечение ===
    glow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([CX - 75, CY - 75, CX + 75, CY + 75],
               fill=(255, 140, 40, 180))
    glow = glow.filter(ImageFilter.GaussianBlur(25))
    img = Image.alpha_composite(img, glow)

    # === Основной шар (тёмно-оранжевый с текстурой) ===
    disc = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    dd = ImageDraw.Draw(disc)

    # Градиент от центра
    for r in range(65, 0, -1):
        t = r / 65
        # Центр ярче, край темнее
        cr = int(255 - t * 50)
        cg = int(180 - t * 100)
        cb = int(60 - t * 30)
        alpha = 255
        d = ImageDraw.Draw(disc)
        d.ellipse([CX - r, CY - r, CX + r, CY + r],
                  fill=(cr, cg, cb, alpha))

    img = Image.alpha_composite(img, disc)

    # === Кратеры (тёмные пятна) ===
    craters = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    cd = ImageDraw.Draw(craters)
    import random
    random.seed(42)
    for _ in range(8):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, 45)
        cx = CX + math.cos(angle) * dist
        cy = CY + math.sin(angle) * dist
        r = random.uniform(4, 10)
        # Тёмное пятно
        cd.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=(60, 20, 10, 150))
    craters = craters.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, craters)

    # === Яркие раскалённые точки ===
    hot = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hot)
    random.seed(123)
    for _ in range(12):
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, 55)
        hx = CX + math.cos(angle) * dist
        hy = CY + math.sin(angle) * dist
        r = random.uniform(2, 4)
        hd.ellipse([hx - r, hy - r, hx + r, hy + r],
                   fill=(255, 240, 180, 200))
    hot = hot.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, hot)

    # === Чёткий контур ===
    outline = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    od = ImageDraw.Draw(outline)
    od.ellipse([CX - 65, CY - 65, CX + 65, CY + 65],
               outline=(255, 180, 60, 255), width=3)
    img = Image.alpha_composite(img, outline)

    # === Блик сверху-слева ===
    hl = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    hd2 = ImageDraw.Draw(hl)
    hd2.ellipse([CX - 40, CY - 45, CX - 15, CY - 20],
                fill=(255, 255, 220, 220))
    hl = hl.filter(ImageFilter.GaussianBlur(6))
    img = Image.alpha_composite(img, hl)

    img.save(os.path.join(OUTPUT_DIR, "meteor.png"))
    print("✓ meteor.png")


if __name__ == "__main__":
    print("🌠 Генерация метеорита...\n")
    make_meteor()
    print("\n🎉 Готово!")