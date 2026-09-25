"""Главное меню — солнце в центре, кнопки в форме X."""
import math
import os
import random
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.graphics.texture import Texture
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock
from PIL import Image as PILImage


class MenuScreen(Widget):
    """Экран главного меню."""

    def __init__(self, on_play, on_shop, on_settings, on_exit, **kwargs):
        super().__init__(**kwargs)
        self.on_play = on_play
        self.on_shop = on_shop
        self.on_settings = on_settings
        self.on_exit = on_exit

        self.bind(size=self._on_resize, pos=self._on_resize)

        self.pulse = 0.0
        Clock.schedule_interval(self._pulse_tick, 0.05)

        self.stars = self._generate_stars()
        self.sun_tex = self._load_texture("assets/specials/supernova.png")

        # Кнопки — в форме X (4 диагонали)
        self.buttons = [
            {"id": "play", "label": "ИГРАТЬ", "angle": 135},
            {"id": "shop", "label": "МАГАЗИН", "angle": 45},
            {"id": "exit", "label": "ВЫХОД", "angle": 225},
            {"id": "settings", "label": "НАСТРОЙКИ", "angle": 315},
        ]
        self.btn_areas = {}

        self._text_cache = {}
        self._draw_all()

    def _pulse_tick(self, dt):
        self.pulse += dt
        self._draw_all()

    def _generate_stars(self):
        random.seed(7)
        return [
            (random.uniform(0, 1), random.uniform(0, 1),
             random.uniform(1, 2.5), random.uniform(0.3, 1.0))
            for _ in range(180)
        ]

    def _load_texture(self, path):
        if not os.path.exists(path):
            print(f"⚠ Файл не найден: {path}")
            return None
        pil_img = PILImage.open(path).convert("RGBA")
        tex = Texture.create(size=pil_img.size, colorfmt="rgba")
        tex.blit_buffer(pil_img.tobytes(), colorfmt="rgba", bufferfmt="ubyte")
        tex.flip_vertical()
        return tex

    def _get_text_label(self, text, font_size, color=(0.9, 0.95, 1, 1)):
        key = (text, font_size, color)
        if key in self._text_cache:
            return self._text_cache[key]
        lbl = CoreLabel(
            text=text, font_size=font_size, color=color, outline_width=0,
        )
        lbl.refresh()
        self._text_cache[key] = lbl
        return lbl

    def _draw_text_centered(self, text, cx, y_bottom, font_size, color):
        lbl = self._get_text_label(text, font_size, color)
        tex = lbl.texture
        Rectangle(
            texture=tex,
            pos=(cx - tex.width / 2, y_bottom),
            size=(tex.width, tex.height),
        )

    def _on_resize(self, *args):
        self._draw_all()

    def _draw_all(self):
        self.canvas.clear()

        w, h = self.width, self.height
        if w < 100 or h < 100:
            return

        cx = w / 2
        cy = h * 0.50

        # Звёзды фона
        with self.canvas:
            for (x, y, size, alpha) in self.stars:
                Color(1, 1, 1, alpha)
                Ellipse(pos=(x * w, y * h), size=(size, size))

        # Заголовок
        with self.canvas:
            Color(1, 1, 1, 1)
            self._draw_text_centered(
                "КОСМО-РЕЗОНАНС",
                w / 2, h * 0.91,
                font_size=42,
                color=(0.7, 0.9, 1.0, 1),
            )

        # Солнце в центре
        sun_size = min(w, h) * 0.30
        pulse_factor = 1.0 + 0.05 * math.sin(self.pulse * 4)
        sun_display_size = sun_size * pulse_factor

        glow_r = sun_display_size * 0.85
        glow_alpha = 0.25 + 0.10 * math.sin(self.pulse * 4)
        with self.canvas:
            Color(1, 0.6, 0.2, glow_alpha)
            Ellipse(
                pos=(cx - glow_r, cy - glow_r),
                size=(glow_r * 2, glow_r * 2),
            )

        if self.sun_tex is not None:
            with self.canvas:
                Color(1, 1, 1, 1)
                Rectangle(
                    texture=self.sun_tex,
                    pos=(cx - sun_display_size / 2, cy - sun_display_size / 2),
                    size=(sun_display_size, sun_display_size),
                )

        # Кнопки по диагоналям (X-образно)
        # Радиус орбиты — так, чтобы кнопки были на диагонали 45°
        # На диагонали расстояние по X и Y одинаково
        # Чем больше радиус — тем дальше от центра
        orbit_r = min(w, h) * 0.30
        btn_r = min(w, h) * 0.078

        self.btn_areas = {}

        for b in self.buttons:
            angle = math.radians(b["angle"])
            bx = cx + math.cos(angle) * orbit_r
            by = cy + math.sin(angle) * orbit_r

            with self.canvas:
                Color(0.05, 0.1, 0.2, 0.95)
                Ellipse(pos=(bx - btn_r, by - btn_r),
                        size=(btn_r * 2, btn_r * 2))
                Color(0.4, 0.8, 1.0, 1)
                Line(circle=(bx, by, btn_r), width=3)
                Color(0.4, 0.8, 1.0, 0.15)
                Ellipse(pos=(bx - btn_r * 0.85, by - btn_r * 0.85),
                        size=(btn_r * 1.7, btn_r * 1.7))

            with self.canvas:
                Color(1, 1, 1, 1)
                font_size = 15 if len(b["label"]) <= 8 else 11
                self._draw_text_centered(
                    b["label"],
                    bx, by - (font_size * 0.6),
                    font_size=font_size,
                    color=(0.9, 0.95, 1, 1),
                )

            self.btn_areas[b["id"]] = (bx - btn_r, by - btn_r,
                                       btn_r * 2, btn_r * 2)

    def on_touch_down(self, touch):
        for bid, (bx, by, bw, bh) in self.btn_areas.items():
            if bx <= touch.x <= bx + bw and by <= touch.y <= by + bh:
                if bid == "play":
                    self.on_play()
                elif bid == "shop":
                    self.on_shop()
                elif bid == "settings":
                    self.on_settings()
                elif bid == "exit":
                    self.on_exit()
                return True
        return True