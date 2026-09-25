"""Экран карты галактики — 30 звёзд на спирали."""
import math
import random
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse, InstructionGroup
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock

from save.progress import get_stars


TOTAL_LEVELS = 30

COL_BG = (0.02, 0.02, 0.06, 1)
COL_STAR_LOCKED = (0.35, 0.35, 0.45, 1)
COL_STAR_UNLOCKED = (0.4, 0.8, 1.0, 1)
COL_STAR_CURRENT = (1.0, 0.85, 0.2, 1)
COL_STAR_DONE = (0.4, 1.0, 0.6, 1)
COL_SPIRAL = (0.2, 0.5, 0.85, 0.5)
COL_TEXT = (0.9, 0.95, 1, 1)


class GalaxyMapScreen(Widget):
    """Экран карты галактики — оптимизированный."""

    def __init__(self, progress, on_level_selected, on_back, **kwargs):
        super().__init__(**kwargs)
        self.progress = progress
        self.on_level_selected = on_level_selected
        self.on_back = on_back

        self.bind(size=self._on_resize, pos=self._on_resize)

        self.pulse = 0.0

        # Фоновые звёзды
        random.seed(7)
        self.stars = [
            (random.uniform(0, 1), random.uniform(0, 1),
             random.uniform(1, 2.5), random.uniform(0.3, 1.0))
            for _ in range(150)
        ]

        self.level_positions = {}
        self.level_areas = {}
        self.back_area = (0, 0, 0, 0)

        self._text_cache = {}

        # Отдельный слой для пульсации текущего уровня
        self._pulse_layer = InstructionGroup()
        self.canvas.add(self._pulse_layer)

        # Рисуем статичный слой
        self._draw_static()
        # Запускаем пульсацию
        Clock.schedule_interval(self._pulse_tick, 0.05)

    def _pulse_tick(self, dt):
        """Перерисовываем только пульсацию текущей звезды."""
        self.pulse += dt
        self._draw_pulse_only()

    def _on_resize(self, *args):
        self._draw_static()
        self._draw_pulse_only()

    # ---------- Текст ----------

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

    # ---------- Позиции ----------

    def _compute_positions(self):
        w, h = self.width, self.height
        if w < 100 or h < 100:
            return

        cx = w / 2
        cy = h * 0.42

        r_outer = min(w, h) * 0.44
        r_inner = min(w, h) * 0.12

        positions = {}
        for i in range(TOTAL_LEVELS):
            level = i + 1
            t = i / (TOTAL_LEVELS - 1)

            radius = r_outer * (1 - t) + r_inner * t

            total_angle = math.pi * 2 * 2.0
            angle = t * total_angle

            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            positions[level] = (x, y)

        self.level_positions = positions

    # ---------- СТАТИЧНЫЙ СЛОЙ ----------

    def _draw_static(self):
        """Рисует всё, что не меняется — звёзды, спираль, уровни, UI."""
        self.canvas.clear()

        w, h = self.width, self.height
        if w < 100 or h < 100:
            return

        self._compute_positions()

        # 1. Звёзды фона
        with self.canvas:
            for (x, y, size, alpha) in self.stars:
                Color(1, 1, 1, alpha)
                Ellipse(pos=(x * w, y * h), size=(size, size))

        # 2. Спираль
        if self.level_positions:
            pts = []
            for level in range(1, TOTAL_LEVELS + 1):
                x, y = self.level_positions[level]
                pts.extend([x, y])
            with self.canvas:
                Color(*COL_SPIRAL)
                Line(points=pts, width=2)

        # 3. Заголовок
        with self.canvas:
            Color(1, 1, 1, 1)
            self._draw_text_centered(
                "ГАЛАКТИКА",
                w / 2, h * 0.92,
                font_size=36,
                color=(0.7, 0.9, 1.0, 1),
            )

        # 4. Кнопка «Назад»
        back_r = 35
        back_x = 50
        back_y = h - 50
        with self.canvas:
            Color(0.05, 0.1, 0.2, 0.95)
            Ellipse(pos=(back_x - back_r, back_y - back_r),
                    size=(back_r * 2, back_r * 2))
            Color(0.4, 0.8, 1.0, 1)
            Line(circle=(back_x, back_y, back_r), width=3)
            Color(1, 1, 1, 1)
            self._draw_text_centered(
                "<", back_x, back_y - 15,
                font_size=30, color=(0.9, 0.95, 1, 1),
            )
        self.back_area = (back_x - back_r, back_y - back_r,
                          back_r * 2, back_r * 2)

        # 5. Уровни-звёзды (кроме пульсирующего — его рисуем отдельно)
        self.level_areas = {}
        unlocked = self.progress.get("unlocked_level", 1)

        for level in range(1, TOTAL_LEVELS + 1):
            x, y = self.level_positions[level]
            stars = get_stars(self.progress, level)

            is_current = (level == unlocked and stars == 0)
            if is_current:
                # Пульсирующий уровень — рисуем в _draw_pulse_only
                self.level_areas[level] = (x, y, 16)
                continue

            if stars > 0:
                r = 16
                color = COL_STAR_DONE
            elif level <= unlocked:
                r = 16
                color = COL_STAR_UNLOCKED
            else:
                r = 14
                color = COL_STAR_LOCKED

            with self.canvas:
                # Свечение
                Color(color[0], color[1], color[2], 0.3)
                Ellipse(pos=(x - r * 1.5, y - r * 1.5),
                        size=(r * 3, r * 3))
                # Звезда
                Color(*color)
                pts = self._star_points(x, y, r, r * 0.45)
                Line(points=pts + [pts[0], pts[1]], width=2)
                # Центр
                Color(color[0], color[1], color[2], 0.4)
                Ellipse(pos=(x - r * 0.5, y - r * 0.5),
                        size=(r, r))

            # Номер
            with self.canvas:
                Color(1, 1, 1, 1)
                num_color = ((0.9, 0.95, 1, 1) if level <= unlocked
                             else (0.5, 0.5, 0.6, 1))
                self._draw_text_centered(
                    str(level),
                    x, y - 5,
                    font_size=12,
                    color=num_color,
                )

            # Звёздочки за уровень
            if stars > 0:
                for i in range(stars):
                    sx = x - 10 + i * 10
                    sy = y - r - 10
                    with self.canvas:
                        Color(1, 0.9, 0.2, 1)
                        star_pts = self._star_points(sx, sy, 4, 1.8)
                        Line(points=star_pts + [star_pts[0], star_pts[1]],
                             width=1.5)

            self.level_areas[level] = (x, y, r)

        # Восстанавливаем слой пульсации (canvas.clear() его удалил)
        self._pulse_layer = InstructionGroup()
        self.canvas.add(self._pulse_layer)
        self._draw_pulse_only()

    # ---------- ДИНАМИЧЕСКИЙ СЛОЙ (только пульсация) ----------

    def _draw_pulse_only(self):
        """Рисует только пульсирующую текущую звезду."""
        self._pulse_layer.clear()

        unlocked = self.progress.get("unlocked_level", 1)
        if unlocked not in self.level_positions:
            return

        # Определяем, есть ли пульсация (текущий уровень не пройден)
        stars = get_stars(self.progress, unlocked)
        if stars > 0:
            return  # уровень уже пройден — пульсации нет

        x, y = self.level_positions[unlocked]
        pulse = 1.0 + 0.15 * math.sin(self.pulse * 4)
        r = 16 * pulse
        color = COL_STAR_CURRENT

        # Свечение
        self._pulse_layer.add(Color(color[0], color[1], color[2], 0.4))
        self._pulse_layer.add(Ellipse(
            pos=(x - r * 1.6, y - r * 1.6),
            size=(r * 3.2, r * 3.2),
        ))
        # Звезда
        self._pulse_layer.add(Color(*color))
        pts = self._star_points(x, y, r, r * 0.45)
        self._pulse_layer.add(Line(
            points=pts + [pts[0], pts[1]], width=2,
        ))
        # Центр
        self._pulse_layer.add(Color(color[0], color[1], color[2], 0.4))
        self._pulse_layer.add(Ellipse(
            pos=(x - r * 0.5, y - r * 0.5),
            size=(r, r),
        ))

        # Номер поверх
        num_lbl = self._get_text_label(str(unlocked), 12, (0.3, 0.2, 0, 1))
        tex = num_lbl.texture
        self._pulse_layer.add(Color(1, 1, 1, 1))
        self._pulse_layer.add(Rectangle(
            texture=tex,
            pos=(x - tex.width / 2, y - 5),
            size=(tex.width, tex.height),
        ))

    def _star_points(self, cx, cy, outer_r, inner_r, n=5):
        pts = []
        for i in range(n * 2):
            r = outer_r if i % 2 == 0 else inner_r
            angle = math.radians(-90 + i * 180 / n)
            pts.extend([cx + math.cos(angle) * r,
                        cy + math.sin(angle) * r])
        return pts

    # ---------- Ввод ----------

    def on_touch_down(self, touch):
        bx, by, bw, bh = self.back_area
        if bx <= touch.x <= bx + bw and by <= touch.y <= by + bh:
            self.on_back()
            return True

        unlocked = self.progress.get("unlocked_level", 1)
        for level, (x, y, r) in self.level_areas.items():
            dist = math.hypot(touch.x - x, touch.y - y)
            if dist <= r + 8:
                if level <= unlocked:
                    print(f"▶ Уровень {level}")
                    self.on_level_selected(level)
                else:
                    print(f"🔒 Уровень {level} закрыт")
                return True

        return True