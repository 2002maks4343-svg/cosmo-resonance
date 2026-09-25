"""
Генератор иконок бустеров для «Космо-Резонанс».
"""
import os
import math
from PIL import Image, ImageDraw, ImageFilter

SIZE = 128
CX = SIZE // 2
CY = SIZE // 2
OUTPUT_DIR = "assets/boosters"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def draw_glowing(draw_func, color, glow_color, width=5, glow_blur=8):
    """Рисует фигуру с неоновым свечением."""
    glow_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_img)
    draw_func(gd, glow_color + (200,), width + 6)
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(glow_blur))

    main_img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    md = ImageDraw.Draw(main_img)
    draw_func(md, color + (255,), width)

    return Image.alpha_composite(glow_img, main_img)


# ---------- МОЛОТ (красивый) ----------

def make_hammer():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    def draw_shape(d, color, width):
        # Рукоятка — длинная диагональная линия
        d.line([(38, 100), (80, 55)], fill=color, width=width + 2)

        # Голова — большой прямоугольник сверху с двумя концами
        # Верхняя часть (боёк)
        d.rounded_rectangle(
            [60, 22, 108, 52],
            radius=6, outline=color, width=width,
        )
        # Нижний выступ (противовес)
        d.rounded_rectangle(
            [62, 48, 88, 62],
            radius=4, outline=color, width=width,
        )

    img = draw_glowing(draw_shape,
                       color=(230, 245, 255),
                       glow_color=(120, 200, 255),
                       width=5, glow_blur=8)

    # Заливка головы — голубая
    fill = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fill)
    fd.rounded_rectangle([66, 28, 102, 46], radius=4, fill=(140, 210, 255, 130))
    fd.rounded_rectangle([66, 50, 84, 58], radius=3, fill=(140, 210, 255, 100))
    fill = fill.filter(ImageFilter.GaussianBlur(2))
    img = Image.alpha_composite(img, fill)

    img.save(os.path.join(OUTPUT_DIR, "hammer.png"))
    print("✓ hammer.png")


# ---------- ПЕРЕМЕШИВАНИЕ ----------

def make_shuffle():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    def draw_shape(d, color, width):
        d.arc([25, 30, 103, 98], start=180, end=340, fill=color, width=width)
        d.arc([25, 30, 103, 98], start=0, end=160, fill=color, width=width)

        d.line([(100, 55), (110, 62), (100, 69)], fill=color, width=width)
        d.line([(28, 73), (18, 66), (28, 59)], fill=color, width=width)

    img = draw_glowing(draw_shape,
                       color=(220, 255, 230),
                       glow_color=(80, 255, 140),
                       width=5, glow_blur=8)

    img.save(os.path.join(OUTPUT_DIR, "shuffle.png"))
    print("✓ shuffle.png")


# ---------- РАКЕТА ----------

def make_rocket():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    def draw_shape(d, color, width):
        body_pts = [(CX, 15), (CX - 18, 70), (CX + 18, 70)]
        d.polygon(body_pts, outline=color)
        d.line([(CX - 18, 70), (CX + 18, 70)], fill=color, width=width)

        d.ellipse([CX - 8, 38, CX + 8, 54], outline=color, width=width)

        d.polygon([
            (CX - 14, 75),
            (CX, 105),
            (CX + 14, 75),
        ], outline=color)

        d.polygon([(CX - 18, 60), (CX - 28, 75), (CX - 18, 75)], outline=color)
        d.polygon([(CX + 18, 60), (CX + 28, 75), (CX + 18, 75)], outline=color)

    img = draw_glowing(draw_shape,
                       color=(255, 220, 220),
                       glow_color=(255, 100, 80),
                       width=5, glow_blur=9)

    flame = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    fd = ImageDraw.Draw(flame)
    fd.polygon([(CX - 8, 78), (CX, 100), (CX + 8, 78)], fill=(255, 200, 80, 220))
    flame = flame.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, flame)

    img.save(os.path.join(OUTPUT_DIR, "rocket.png"))
    print("✓ rocket.png")


# ---------- +3 ХОДА (вместо заморозки) ----------

def make_freeze():
    """Иконка «+3» — просто цифры, без снежинки."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    def draw_shape(d, color, width):
        # Плюс
        d.line([(30, 64), (55, 64)], fill=color, width=width + 3)
        d.line([(42, 52), (42, 76)], fill=color, width=width + 3)
        # Тройка — из трёх сегментов
        # Верхняя дуга
        d.arc([65, 30, 105, 64], start=270, end=90, fill=color, width=width)
        # Нижняя дуга
        d.arc([65, 64, 105, 98], start=270, end=90, fill=color, width=width)

    # Цвета — голубые, как «лёд»
    img = draw_glowing(draw_shape,
                       color=(230, 250, 255),
                       glow_color=(80, 200, 255),
                       width=6, glow_blur=10)

    img.save(os.path.join(OUTPUT_DIR, "freeze.png"))
    print("✓ freeze.png (+3)")


# ---------- ДВОЙНЫЕ ОЧКИ ----------

def make_double():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    def star_points(cx, cy, outer_r, inner_r, n=5):
        pts = []
        for i in range(n * 2):
            r = outer_r if i % 2 == 0 else inner_r
            angle = math.radians(-90 + i * 180 / n)
            pts.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
        return pts

    def draw_shape(d, color, width):
        big_pts = star_points(CX - 12, CY - 6, 32, 14)
        d.polygon(big_pts, outline=color)
        small_pts = star_points(CX + 30, CY + 25, 18, 8)
        d.polygon(small_pts, outline=color)

    img = draw_glowing(draw_shape,
                       color=(255, 240, 200),
                       glow_color=(255, 200, 60),
                       width=4, glow_blur=9)

    core = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    cd = ImageDraw.Draw(core)
    cd.ellipse([CX - 20, CY - 14, CX - 4, CY + 2], fill=(255, 250, 220, 220))
    core = core.filter(ImageFilter.GaussianBlur(5))
    img = Image.alpha_composite(img, core)

    img.save(os.path.join(OUTPUT_DIR, "double.png"))
    print("✓ double.png")


# ---------- Запуск ----------

if __name__ == "__main__":
    print("✨ Генерация иконок бустеров...\n")
    make_hammer()
    make_shuffle()
    make_rocket()
    make_freeze()
    make_double()
    print(f"\n🎉 Готово! Иконки в папке: {OUTPUT_DIR}")