"""Экран победы/проигрыша с анимацией и звёздами."""
import math
import random
from kivy.graphics import Color, Rectangle, Line, Ellipse, InstructionGroup
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock

from ui import sound


ANIM_DURATION = 1.2
ANIM_FPS = 60

VICTORY_CORE = (0.3, 1.0, 0.5, 1)
DEFEAT_CORE = (0.7, 0.3, 1.0, 1)


class GameOverScreen:
    def __init__(self, game, victory):
        self.game = game
        self.victory = victory

        self._group = None
        self.btn_areas = {}

        self.progress = 0.0
        self.animation_done = False
        self.stars_shown = 0
        self.stars_timer = 0.0

        self.shards = []
        self.petals = []

        if not victory:
            self._prepare_shards()
        else:
            self._prepare_petals()

        self.earned_stars = game._calculate_stars() if victory else 0

        self.draw()
        self._start_animation()

        game.bind(size=self._on_resize, pos=self._on_resize)

        if victory:
            sound.play("win")
        else:
            sound.play("lose")

    def _prepare_shards(self):
        random.seed(42)
        for _ in range(40):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(0.4, 1.0)
            size = random.uniform(3, 8)
            self.shards.append({
                "angle": angle,
                "speed": speed,
                "size": size,
                "color": random.choice([
                    (0.6, 0.3, 1.0, 1),
                    (0.4, 0.5, 1.0, 1),
                    (0.8, 0.5, 1.0, 1),
                    (0.3, 0.3, 0.9, 1),
                ]),
            })

    def _prepare_petals(self):
        n = 16
        for i in range(n):
            angle = (360 / n) * i
            self.petals.append({
                "angle": angle,
                "length_factor": random.uniform(0.85, 1.15),
                "width_factor": random.uniform(0.8, 1.2),
            })

    def _start_animation(self):
        Clock.schedule_interval(self._animate, 1 / ANIM_FPS)

    def _animate(self, dt):
        if self.animation_done:
            self.stars_timer += dt
            new_shown = min(3, int(self.stars_timer / 0.3))
            if new_shown > self.stars_shown and self.victory:
                self.stars_shown = new_shown
                sound.play("match")
            self.draw()
            return True

        self.progress += dt / ANIM_DURATION
        if self.progress >= 1.0:
            self.progress = 1.0
            self.animation_done = True
            Clock.unschedule(self._animate)
            Clock.schedule_interval(self._animate, 1 / 30)
        self.draw()
        return True

    def draw(self):
        game = self.game
        w, h = game.width, game.height
        if w < 100 or h < 100:
            return

        if self._group is not None:
            game.canvas.after.remove(self._group)
        self._group = InstructionGroup()
        game.canvas.after.add(self._group)

        p = self.progress
        cx = w / 2
        cy = h * 0.82

        bg_alpha = 0.3 + 0.5 * p
        self._group.add(Color(0, 0, 0, bg_alpha))
        self._group.add(Rectangle(pos=(0, 0), size=(w, h)))

        if self.victory:
            self._draw_victory(cx, cy, w, h, p)
        else:
            self._draw_defeat(cx, cy, w, h, p)

        if self.animation_done:
            self._draw_ui(w, h)

    def _draw_victory(self, cx, cy, w, h, p):
        core_r = 30 + 25 * p
        glow_r = core_r * 2.0
        self._group.add(Color(0.3, 1.0, 0.5, 0.15))
        self._group.add(Ellipse(
            pos=(cx - glow_r, cy - glow_r),
            size=(glow_r * 2, glow_r * 2),
        ))

        for petal in self.petals:
            angle = math.radians(petal["angle"])
            dx = math.cos(angle)
            dy = math.sin(angle)
            petal_len = (40 + 50 * p) * petal["length_factor"]
            petal_w = 4 * petal["width_factor"]
            x1 = cx + dx * core_r * 0.6
            y1 = cy + dy * core_r * 0.6
            x2 = cx + dx * petal_len
            y2 = cy + dy * petal_len
            px, py = -dy, dx
            alpha = 0.6 + 0.4 * math.sin(p * 12 + petal["angle"])
            self._group.add(Color(0.1, 0.8, 0.3, alpha))
            self._group.add(Line(points=[
                x2, y2,
                x1 + px * petal_w, y1 + py * petal_w,
                x1 - px * petal_w, y1 - py * petal_w,
                x2, y2,
            ], width=2))

        self._group.add(Color(*VICTORY_CORE))
        self._group.add(Ellipse(
            pos=(cx - core_r, cy - core_r),
            size=(core_r * 2, core_r * 2),
        ))
        inner_r = core_r * 0.4
        self._group.add(Color(1, 1, 1, 0.8))
        self._group.add(Ellipse(
            pos=(cx - inner_r, cy - inner_r),
            size=(inner_r * 2, inner_r * 2),
        ))

    def _draw_defeat(self, cx, cy, w, h, p):
        if p < 0.4:
            pulse = 1.0 + 0.15 * math.sin(p * 40)
            planet_r = (40 + 25 * (p / 0.4)) * pulse
            self._group.add(Color(0.15, 0.05, 0.3, 1))
            self._group.add(Ellipse(
                pos=(cx - planet_r, cy - planet_r),
                size=(planet_r * 2, planet_r * 2),
            ))
            glow_r = planet_r * 1.3
            self._group.add(Color(0.6, 0.2, 1.0, 0.4))
            self._group.add(Line(circle=(cx, cy, glow_r), width=3))
        elif p < 0.5:
            flash_r = 40 + 150 * ((p - 0.4) / 0.1)
            alpha = 1.0 - (p - 0.4) / 0.1 * 0.7
            self._group.add(Color(1, 0.9, 1.0, alpha))
            self._group.add(Ellipse(
                pos=(cx - flash_r, cy - flash_r),
                size=(flash_r * 2, flash_r * 2),
            ))
        else:
            t = (p - 0.5) / 0.5
            max_dist = max(w, h) * 0.5
            for shard in self.shards:
                dist = max_dist * shard["speed"] * t
                sx = cx + math.cos(shard["angle"]) * dist
                sy = cy + math.sin(shard["angle"]) * dist
                alpha = 1.0 - t
                color = shard["color"]
                self._group.add(Color(color[0], color[1], color[2], alpha))
                size = shard["size"]
                self._group.add(Ellipse(
                    pos=(sx - size, sy - size),
                    size=(size * 2, size * 2),
                ))

    # ---------- UI ----------

    def _star_points(self, cx, cy, outer_r, inner_r, n=5):
        pts = []
        for i in range(n * 2):
            r = outer_r if i % 2 == 0 else inner_r
            angle = math.radians(-90 + i * 180 / n)
            pts.extend([cx + math.cos(angle) * r,
                        cy + math.sin(angle) * r])
        return pts

    def _draw_star(self, cx, cy, r, filled):
        if filled:
            self._group.add(Color(1, 0.85, 0.2, 1))
            pts = self._star_points(cx, cy, r, r * 0.45)
            self._group.add(Line(points=pts + [pts[0], pts[1]], width=4))
            self._group.add(Color(1, 0.9, 0.4, 0.5))
            self._group.add(Ellipse(
                pos=(cx - r * 0.5, cy - r * 0.5),
                size=(r, r),
            ))
        else:
            self._group.add(Color(0.4, 0.4, 0.5, 1))
            pts = self._star_points(cx, cy, r, r * 0.45)
            self._group.add(Line(points=pts + [pts[0], pts[1]], width=3))

    def _draw_ui(self, w, h):
        title_text = "ПОБЕДА!" if self.victory else "ПРОВАЛ"
        title_color = (0.4, 1.0, 0.6, 1) if self.victory else (1, 0.4, 0.4, 1)

        title_lbl = CoreLabel(text=title_text, font_size=64, color=title_color)
        title_lbl.refresh()
        tex = title_lbl.texture
        self._group.add(Color(1, 1, 1, 1))
        self._group.add(Rectangle(
            texture=tex,
            pos=(w / 2 - tex.width / 2, h * 0.65),
            size=(tex.width, tex.height),
        ))

        # Звёзды (только при победе)
        if self.victory:
            star_r = 30
            star_gap = 20
            total_w = star_r * 6 + star_gap * 2
            start_x = w / 2 - total_w / 2 + star_r

            for i in range(3):
                sx = start_x + i * (star_r * 2 + star_gap)
                sy = h * 0.53
                filled = (i < self.earned_stars and i < self.stars_shown)
                self._draw_star(sx, sy, star_r, filled)

        stats_text = (
            f"Очки: {self.game.board.score}\n"
            f"Использовано ходов: {self.game.level.get('moves', 30) - self.game.moves_left}"
        )
        stats_lbl = CoreLabel(
            text=stats_text, font_size=22, color=(0.85, 0.95, 1, 1),
        )
        stats_lbl.refresh()
        tex2 = stats_lbl.texture
        self._group.add(Color(1, 1, 1, 1))
        self._group.add(Rectangle(
            texture=tex2,
            pos=(w / 2 - tex2.width / 2, h * 0.36),
            size=(tex2.width, tex2.height),
        ))

        if self.victory:
            buttons_def = [
                ("retry", "ЗАНОВО"),
                ("next", "ДАЛЕЕ"),
                ("map", "К КАРТЕ"),
            ]
        else:
            buttons_def = [
                ("retry", "ЗАНОВО"),
                ("map", "К КАРТЕ"),
            ]

        n = len(buttons_def)
        btn_w = min(160, w / (n + 1))
        btn_h = 65
        gap = 15
        total_w = btn_w * n + gap * (n - 1)
        start_x = (w - total_w) / 2
        btn_y = h * 0.16

        for i, (name, label) in enumerate(buttons_def):
            bx = start_x + i * (btn_w + gap)
            self._group.add(Color(0.1, 0.15, 0.25, 1))
            self._group.add(Rectangle(pos=(bx, btn_y), size=(btn_w, btn_h)))
            self._group.add(Color(0.4, 0.8, 1.0, 1))
            self._group.add(Line(rectangle=(bx, btn_y, btn_w, btn_h), width=2))

            btn_lbl = CoreLabel(
                text=label, font_size=20, color=(0.9, 0.95, 1, 1),
            )
            btn_lbl.refresh()
            btex = btn_lbl.texture
            self._group.add(Color(1, 1, 1, 1))
            self._group.add(Rectangle(
                texture=btex,
                pos=(bx + btn_w / 2 - btex.width / 2,
                     btn_y + btn_h / 2 - btex.height / 2),
                size=(btex.width, btex.height),
            ))

            self.btn_areas[name] = (bx, btn_y, btn_w, btn_h)

    def _on_resize(self, *args):
        self.draw()

    def on_touch_down(self, touch):
        if not self.animation_done:
            return True
        for name, (bx, by, bw, bh) in self.btn_areas.items():
            if bx <= touch.x <= bx + bw and by <= touch.y <= by + bh:
                sound.play("click")
                self._handle_button(name)
                return True
        return True

    def _handle_button(self, name):
        if name == "retry":
            self.game.restart_level()
            self.dismiss()
        elif name == "next":
            self.dismiss()
            if self.game.on_next_level is not None:
                self.game.on_next_level()
        elif name == "map":
            self.dismiss()
            if self.game.on_level_complete is not None:
                self.game.on_level_complete()

    def dismiss(self):
        if self._group is not None:
            self.game.canvas.after.remove(self._group)
            self._group = None
        self.game.unbind(size=self._on_resize, pos=self._on_resize)
        self.game.game_over_screen = None