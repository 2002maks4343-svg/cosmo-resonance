"""Главный виджет игры."""
import math
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle, Line, Ellipse, InstructionGroup
from kivy.core.text import Label as CoreLabel
from kivy.clock import Clock
from kivy.app import App

from engine.board import Board, has_any_move, reshuffle_board
from engine.match import (find_all_matches, is_special, special_kind,
                          HOLE, METEOR)
from engine import level as lvl

from ui import renderer as r
from ui import animation
from ui import input_handler as inp
from ui import boosters as bst
from ui import sound
from ui.game_over import GameOverScreen


Window.clearcolor = (0.02, 0.02, 0.06, 1)

MOVES_TO_SCORE = 100
HINT_TIMEOUT = 20

LEFT_PANEL_WIDTH = 150
RIGHT_PANEL_WIDTH = 100
MARGIN = 10
GAP = 10

COL_PANEL_BG = (0.05, 0.08, 0.16, 1)
COL_PANEL_BORDER = (0.4, 0.8, 1.0, 1)
COL_DIVIDER = (0.3, 0.7, 1.0, 0.4)
COL_SLOT_BG = (0.08, 0.12, 0.22, 1)
COL_SLOT_BORDER = (0.3, 0.6, 1.0, 0.8)

COL_FINISH_BG = (0.15, 0.55, 0.3, 1)
COL_FINISH_BORDER = (0.4, 1.0, 0.6, 1)

COL_EXIT_BG = (0.55, 0.15, 0.2, 1)
COL_EXIT_BORDER = (1.0, 0.5, 0.5, 1)

COL_GOAL_DONE = (0.4, 1.0, 0.6, 1)
COL_GOAL_TODO = (0.85, 0.9, 1, 1)


class CosmoGame(FloatLayout):
    def __init__(self, level_num=1, on_back_to_menu=None,
                 on_level_complete=None, on_next_level=None, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self._on_resize, pos=self._on_resize)

        self.level_num = level_num
        self.on_back_to_menu = on_back_to_menu
        self.on_level_complete = on_level_complete
        self.on_next_level = on_next_level

        self.level = lvl.get_level(level_num)
        print(f"🎮 Загружен уровень {level_num}: "
              f"{self.level['rows']}×{self.level['cols']}, "
              f"цели={self.level.get('goals', [])}")

        self.board = Board(
            rows=self.level["rows"],
            cols=self.level["cols"],
            holes=self.level.get("holes", []),
            ice=self.level.get("ice", []),
            meteor=self.level.get("meteor"),
        )

        if not has_any_move(self.board):
            print("⚠ На поле нет ходов при старте, перемешиваем...")
            reshuffle_board(self.board)

        self.moves_left = self.level.get("moves", 30)

        self.textures = r.load_planet_textures()
        self.special_textures = r.load_special_textures()
        self.stars = r.generate_stars()

        self.touch_start = None
        self.selected_cell = None

        self.level_done = False
        self.game_over_screen = None
        self.exit_popup_active = False

        self.double_score_turns = 0

        # Таймер подсказки
        self.hint_timer = 0.0
        self.hint_active = False
        self.hint_cells = None
        Clock.schedule_interval(self._hint_tick, 0.5)

        bst.init_boosters(self)

        self.animating = False
        self.fading = []
        self.fall_offsets = {}
        self._fall_start_offsets = {}
        self._fall_progress = 0.0

        self._text_cache = {}

        self._hud_layer = InstructionGroup()
        self.canvas.add(self._hud_layer)

        self._planet_layer = InstructionGroup()
        self.canvas.add(self._planet_layer)

        self._popup_layer = InstructionGroup()
        self.canvas.after.add(self._popup_layer)

        self._draw_background()
        self._draw_hud()
        self.redraw_dynamic()

    def _on_resize(self, *args):
        self._draw_background()
        self._draw_hud()
        self.redraw_dynamic()

    # ---------- Подсказка ----------

    def _hint_tick(self, dt):
        if (self.animating or self.level_done
                or self.exit_popup_active):
            self.hint_timer = 0.0
            self.hint_active = False
            return

        self.hint_timer += dt
        if self.hint_timer >= HINT_TIMEOUT and not self.hint_active:
            move = self._find_any_move()
            if move is not None:
                self.hint_cells = move
                self.hint_active = True
                print(f"💡 Подсказка: {move}")
                self.redraw_dynamic()

    def _reset_hint(self):
        self.hint_timer = 0.0
        self.hint_active = False
        self.hint_cells = None

    def _find_any_move(self):
        grid = self.board.grid
        rows = self.board.rows
        cols = self.board.cols

        for r in range(rows):
            for c in range(cols):
                if c + 1 < cols:
                    if self._swap_test(r, c, r, c + 1):
                        return ((r, c), (r, c + 1))
                if r + 1 < rows:
                    if self._swap_test(r, c, r + 1, c):
                        return ((r, c), (r + 1, c))
        return None

    def _swap_test(self, r1, c1, r2, c2):
        grid = self.board.grid
        v1 = grid[r1][c1]
        v2 = grid[r2][c2]
        if v1 in (HOLE, METEOR) or v2 in (HOLE, METEOR):
            return False
        if v1 is None or v2 is None:
            return False
        grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
        result = bool(find_all_matches(grid, self.board.rows, self.board.cols))
        grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
        return result

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

    # ---------- Состояние ----------

    def _game_state(self):
        return {
            "score": self.board.score,
            "colors_destroyed": self.board.colors_destroyed,
            "ice_left": self._ice_count_left(),
            "meteor_done": self.board.meteor_done,
        }

    def _ice_count_left(self):
        from engine.match import is_ice
        count = 0
        for r in range(self.board.rows):
            for c in range(self.board.cols):
                if is_ice(self.board.grid[r][c]):
                    count += 1
        return count

    def _can_finish(self):
        goals = self.level.get("goals", [])
        state = self._game_state()
        return all(lvl.describe_goal(g, state)["done"] for g in goals)

    # ---------- Геометрия ----------

    def _grid_geometry(self):
        w, h = self.width, self.height
        left_edge = MARGIN + LEFT_PANEL_WIDTH + GAP
        right_edge = w - MARGIN - RIGHT_PANEL_WIDTH - GAP
        avail_w = right_edge - left_edge
        avail_h = h - MARGIN * 2
        grid_size = min(avail_w, avail_h)
        grid_x = left_edge + (avail_w - grid_size) / 2
        grid_y = MARGIN + (avail_h - grid_size) / 2
        return grid_x, grid_y, grid_size

    def _get_right_panel_layout(self):
        w, h = self.width, self.height
        grid_x, grid_y, grid_size = self._grid_geometry()
        panel_h = grid_size
        right_x = w - RIGHT_PANEL_WIDTH - MARGIN

        panel_top = grid_y + panel_h
        title_y = panel_top - 22

        btn_w = RIGHT_PANEL_WIDTH - 24
        btn_h = 40
        btn_x = right_x + 12
        btn_y = panel_top - 80

        slots_top = panel_top - 100
        side_pad = 12
        bottom_pad = 10
        avail_v = slots_top - grid_y - bottom_pad
        slot_size = min(RIGHT_PANEL_WIDTH - side_pad * 2,
                        (avail_v - 4 * 8) / 5)
        total_h = slot_size * 5 + 8 * 4
        slots_start_y = grid_y + (avail_v - total_h) / 2 + bottom_pad

        slots = {}
        for i, b in enumerate(bst.BOOSTERS):
            sy = slots_start_y + (4 - i) * (slot_size + 8)
            sx = right_x + (RIGHT_PANEL_WIDTH - slot_size) / 2
            slots[b["id"]] = (sx, sy, slot_size, slot_size)

        return {
            "right_x": right_x,
            "panel_h": panel_h,
            "title_y": title_y,
            "btn": (btn_x, btn_y, btn_w, btn_h),
            "slots": slots,
        }

    def _get_action_button_area(self):
        return self._get_right_panel_layout()["btn"]

    def _get_popup_layout(self):
        w, h = self.width, self.height
        popup_w = min(500, w * 0.7)
        popup_h = min(280, h * 0.5)
        popup_x = (w - popup_w) / 2
        popup_y = (h - popup_h) / 2

        btn_w = 150
        btn_h = 55
        btn_gap = 20
        btn_y = popup_y + 30
        btn1_x = popup_x + popup_w / 2 - btn_w - btn_gap / 2
        btn2_x = popup_x + popup_w / 2 + btn_gap / 2

        return {
            "popup": (popup_x, popup_y, popup_w, popup_h),
            "btn_yes": (btn1_x, btn_y, btn_w, btn_h),
            "btn_no": (btn2_x, btn_y, btn_w, btn_h),
        }

    # ---------- ФОН ----------

    def _draw_background(self):
        self.canvas.before.clear()
        self.canvas.clear()

        w, h = self.width, self.height
        if w < 100 or h < 100:
            return

        with self.canvas.before:
            for (x, y, size, alpha) in self.stars:
                Color(1, 1, 1, alpha)
                Ellipse(pos=(x * w, y * h), size=(size, size))

        r.draw_grid(self.canvas, self)

        self._hud_layer = InstructionGroup()
        self.canvas.add(self._hud_layer)

        self._planet_layer = InstructionGroup()
        self.canvas.add(self._planet_layer)

    # ---------- HUD ----------

    def _draw_hud(self):
        self._hud_layer.clear()

        w, h = self.width, self.height
        if w < 100 or h < 100:
            return

        grid_x, grid_y, grid_size = self._grid_geometry()
        panel_h = grid_size
        third = panel_h / 3

        layout = self._get_right_panel_layout()
        right_x = layout["right_x"]

        # Левая панель
        self._hud_layer.add(Color(*COL_PANEL_BG))
        self._hud_layer.add(Rectangle(
            pos=(MARGIN, grid_y), size=(LEFT_PANEL_WIDTH, panel_h)))
        self._hud_layer.add(Color(*COL_PANEL_BORDER))
        self._hud_layer.add(Line(
            rectangle=(MARGIN, grid_y, LEFT_PANEL_WIDTH, panel_h), width=2))

        self._hud_layer.add(Color(*COL_DIVIDER))
        for i in range(1, 3):
            yy = grid_y + third * i
            self._hud_layer.add(Line(
                points=[MARGIN + 8, yy,
                        MARGIN + LEFT_PANEL_WIDTH - 8, yy], width=1))

        # Правая панель
        self._hud_layer.add(Color(*COL_PANEL_BG))
        self._hud_layer.add(Rectangle(
            pos=(right_x, grid_y), size=(RIGHT_PANEL_WIDTH, panel_h)))
        self._hud_layer.add(Color(*COL_PANEL_BORDER))
        self._hud_layer.add(Line(
            rectangle=(right_x, grid_y, RIGHT_PANEL_WIDTH, panel_h), width=2))

        # Слоты бустеров
        for bid, (sx, sy, sw, sh) in layout["slots"].items():
            count = self.boosters.get(bid, 0)
            if count > 0:
                self._hud_layer.add(Color(*COL_SLOT_BG))
            else:
                self._hud_layer.add(Color(0.05, 0.05, 0.1, 0.6))
            self._hud_layer.add(Rectangle(pos=(sx, sy), size=(sw, sh)))
            self._hud_layer.add(Color(*COL_SLOT_BORDER))
            self._hud_layer.add(Line(
                rectangle=(sx, sy, sw, sh), width=1.5))

        cx_left = MARGIN + LEFT_PANEL_WIDTH / 2

        # Номер уровня
        title_lbl = self._get_text_label(
            f"УРОВЕНЬ {self.level_num}", 16, (0.4, 0.9, 1.0, 1))
        tex = title_lbl.texture
        self._hud_layer.add(Color(1, 1, 1, 1))
        self._hud_layer.add(Rectangle(
            texture=tex,
            pos=(cx_left - tex.width / 2, grid_y + panel_h - 28),
            size=(tex.width, tex.height),
        ))

        self._hud_layer.add(Color(0.3, 0.7, 1.0, 0.5))
        self._hud_layer.add(Line(
            points=[MARGIN + 10, grid_y + panel_h - 42,
                    MARGIN + LEFT_PANEL_WIDTH - 10,
                    grid_y + panel_h - 42],
            width=1))

        # Цели
        goals = self.level.get("goals", [])
        state = self._game_state()
        goal_infos = [lvl.describe_goal(g, state) for g in goals]

        lbl = self._get_text_label("ЦЕЛИ", 16, (0.55, 0.75, 0.95, 1))
        tex = lbl.texture
        self._hud_layer.add(Color(1, 1, 1, 1))
        self._hud_layer.add(Rectangle(
            texture=tex,
            pos=(cx_left - tex.width / 2,
                 grid_y + third * 2 + third * 0.55),
            size=(tex.width, tex.height),
        ))

        goal_y = grid_y + third * 2 + third * 0.20
        line_h = 22
        for info in goal_infos:
            if info["target"] == "":
                text = f"{info['label']}: {info['current']}"
            else:
                text = f"{info['label']}: {info['current']}/{info['target']}"
            color = COL_GOAL_DONE if info["done"] else COL_GOAL_TODO
            gl = self._get_text_label(text, 14, color)
            gtex = gl.texture
            self._hud_layer.add(Color(1, 1, 1, 1))
            self._hud_layer.add(Rectangle(
                texture=gtex,
                pos=(cx_left - gtex.width / 2, goal_y),
                size=(gtex.width, gtex.height),
            ))
            goal_y -= line_h

        # Очки
        lbl = self._get_text_label("ОЧКИ", 18, (0.55, 0.75, 0.95, 1))
        tex = lbl.texture
        self._hud_layer.add(Color(1, 1, 1, 1))
        self._hud_layer.add(Rectangle(
            texture=tex,
            pos=(cx_left - tex.width / 2,
                 grid_y + third + third * 0.62),
            size=(tex.width, tex.height),
        ))

        lbl = self._get_text_label(str(self.board.score), 34, (0.9, 0.95, 1, 1))
        tex = lbl.texture
        self._hud_layer.add(Color(1, 1, 1, 1))
        self._hud_layer.add(Rectangle(
            texture=tex,
            pos=(cx_left - tex.width / 2,
                 grid_y + third + third * 0.15),
            size=(tex.width, tex.height),
        ))

        # Ходы
        lbl = self._get_text_label("ХОДЫ", 18, (0.55, 0.75, 0.95, 1))
        tex = lbl.texture
        self._hud_layer.add(Color(1, 1, 1, 1))
        self._hud_layer.add(Rectangle(
            texture=tex,
            pos=(cx_left - tex.width / 2, grid_y + third * 0.62),
            size=(tex.width, tex.height),
        ))

        lbl = self._get_text_label(str(self.moves_left), 34, (0.9, 0.95, 1, 1))
        tex = lbl.texture
        self._hud_layer.add(Color(1, 1, 1, 1))
        self._hud_layer.add(Rectangle(
            texture=tex,
            pos=(cx_left - tex.width / 2, grid_y + third * 0.15),
            size=(tex.width, tex.height),
        ))

        # Бустеры
        lbl = self._get_text_label("БУСТЕРЫ", 13, (0.55, 0.75, 0.95, 1))
        tex = lbl.texture
        self._hud_layer.add(Color(1, 1, 1, 1))
        self._hud_layer.add(Rectangle(
            texture=tex,
            pos=(right_x + RIGHT_PANEL_WIDTH / 2 - tex.width / 2,
                 layout["title_y"]),
            size=(tex.width, tex.height),
        ))

        for bid, (sx, sy, sw, sh) in layout["slots"].items():
            count = self.boosters.get(bid, 0)
            tex = self.booster_textures.get(bid)
            if tex is not None:
                icon_size = sw * 0.75
                icon_x = sx + (sw - icon_size) / 2
                icon_y = sy + (sh - icon_size) / 2 + 4
                if count > 0:
                    self._hud_layer.add(Color(1, 1, 1, 1))
                else:
                    self._hud_layer.add(Color(0.4, 0.4, 0.4, 0.6))
                self._hud_layer.add(Rectangle(
                    texture=tex,
                    pos=(icon_x, icon_y),
                    size=(icon_size, icon_size),
                ))
            cnt_color = ((0.6, 0.85, 1, 1) if count > 0
                         else (0.4, 0.4, 0.5, 1))
            cnt_lbl = self._get_text_label(f"x{count}", 14, cnt_color)
            cnt_tex = cnt_lbl.texture
            self._hud_layer.add(Color(1, 1, 1, 1))
            self._hud_layer.add(Rectangle(
                texture=cnt_tex,
                pos=(sx + sw / 2 - cnt_tex.width / 2, sy + 2),
                size=(cnt_tex.width, cnt_tex.height),
            ))

        # Кнопка действия
        if not self.level_done:
            bx, by, bw, bh = layout["btn"]
            can_finish = self._can_finish()

            if can_finish:
                bg_color = COL_FINISH_BG
                border_color = COL_FINISH_BORDER
                label = "ФИНИШ"
            else:
                bg_color = COL_EXIT_BG
                border_color = COL_EXIT_BORDER
                label = "ВЫХОД"

            self._hud_layer.add(Color(*bg_color))
            self._hud_layer.add(Rectangle(pos=(bx, by), size=(bw, bh)))
            self._hud_layer.add(Color(*border_color))
            self._hud_layer.add(Line(
                rectangle=(bx, by, bw, bh), width=2))

            lbl = self._get_text_label(label, 18, (1, 1, 1, 1))
            tex = lbl.texture
            self._hud_layer.add(Color(1, 1, 1, 1))
            self._hud_layer.add(Rectangle(
                texture=tex,
                pos=(bx + bw / 2 - tex.width / 2, by + bh / 2 - 10),
                size=(tex.width, tex.height),
            ))

    # ---------- Попап ----------

    def _draw_exit_popup(self):
        self._popup_layer.clear()

        if not self.exit_popup_active:
            return

        w, h = self.width, self.height
        layout = self._get_popup_layout()

        px, py, pw, ph = layout["popup"]
        yx, yy, yw, yh = layout["btn_yes"]
        nx, ny, nw, nh = layout["btn_no"]

        self._popup_layer.add(Color(0, 0, 0, 0.75))
        self._popup_layer.add(Rectangle(pos=(0, 0), size=(w, h)))

        self._popup_layer.add(Color(*COL_PANEL_BG))
        self._popup_layer.add(Rectangle(pos=(px, py), size=(pw, ph)))
        self._popup_layer.add(Color(*COL_PANEL_BORDER))
        self._popup_layer.add(Line(rectangle=(px, py, pw, ph), width=3))

        title_lbl = self._get_text_label(
            "ВЫЙТИ ИЗ УРОВНЯ?", 28, (1, 0.7, 0.7, 1))
        tex = title_lbl.texture
        self._popup_layer.add(Color(1, 1, 1, 1))
        self._popup_layer.add(Rectangle(
            texture=tex,
            pos=(px + pw / 2 - tex.width / 2, py + ph - 70),
            size=(tex.width, tex.height),
        ))

        sub_lbl = self._get_text_label(
            "Прогресс уровня будет потерян", 18, (0.85, 0.9, 1, 1))
        tex2 = sub_lbl.texture
        self._popup_layer.add(Color(1, 1, 1, 1))
        self._popup_layer.add(Rectangle(
            texture=tex2,
            pos=(px + pw / 2 - tex2.width / 2, py + ph - 120),
            size=(tex2.width, tex2.height),
        ))

        self._popup_layer.add(Color(*COL_EXIT_BG))
        self._popup_layer.add(Rectangle(pos=(yx, yy), size=(yw, yh)))
        self._popup_layer.add(Color(*COL_EXIT_BORDER))
        self._popup_layer.add(Line(rectangle=(yx, yy, yw, yh), width=2))

        yes_lbl = self._get_text_label("ДА, ВЫЙТИ", 18, (1, 1, 1, 1))
        tex3 = yes_lbl.texture
        self._popup_layer.add(Color(1, 1, 1, 1))
        self._popup_layer.add(Rectangle(
            texture=tex3,
            pos=(yx + yw / 2 - tex3.width / 2,
                 yy + yh / 2 - tex3.height / 2),
            size=(tex3.width, tex3.height),
        ))

        self._popup_layer.add(Color(0.15, 0.4, 0.25, 1))
        self._popup_layer.add(Rectangle(pos=(nx, ny), size=(nw, nh)))
        self._popup_layer.add(Color(0.4, 1.0, 0.6, 1))
        self._popup_layer.add(Line(rectangle=(nx, ny, nw, nh), width=2))

        no_lbl = self._get_text_label("ОТМЕНА", 18, (1, 1, 1, 1))
        tex4 = no_lbl.texture
        self._popup_layer.add(Color(1, 1, 1, 1))
        self._popup_layer.add(Rectangle(
            texture=tex4,
            pos=(nx + nw / 2 - tex4.width / 2,
                 ny + nh / 2 - tex4.height / 2),
            size=(tex4.width, tex4.height),
        ))

    # ---------- Планеты + подсказка ----------

    def redraw_dynamic(self):
        self._planet_layer.clear()
        r.draw_planets_to_group(
            self._planet_layer, self, self.board, self.textures,
            self.fading, self.fall_offsets,
            special_textures=self.special_textures
        )
        r.draw_selection_to_group(self._planet_layer, self, self.selected_cell)

        if self.hint_active and self.hint_cells is not None:
            offset_x, offset_y, grid_size, cell = r.get_grid_geometry(self)
            rows = self.board.rows
            pulse = 0.5 + 0.5 * math.sin(self.hint_timer * 4)

            with self._planet_layer:
                Color(1, 0.9, 0.2, 0.5 + 0.5 * pulse)
                for (r_row, c_col) in self.hint_cells:
                    x, y = r.cell_to_xy(r_row, c_col, cell,
                                        offset_x, offset_y, 4, rows)
                    Line(
                        rectangle=(x, y, cell - 8, cell - 8),
                        width=4,
                    )

    def redraw(self, *args):
        self._draw_background()
        self._draw_hud()
        self.redraw_dynamic()

    def update_hud(self):
        self._draw_hud()

    # ---------- Ввод ----------

    def on_touch_down(self, touch):
        if not self.hint_active:
            self._reset_hint()

        if self.game_over_screen is not None:
            return self.game_over_screen.on_touch_down(touch)

        if self.exit_popup_active:
            layout = self._get_popup_layout()
            yx, yy, yw, yh = layout["btn_yes"]
            nx, ny, nw, nh = layout["btn_no"]

            if yx <= touch.x <= yx + yw and yy <= touch.y <= yy + yh:
                sound.play("click")
                print("🚪 Выход на карту")
                self.exit_popup_active = False
                self._draw_exit_popup()
                if self.on_level_complete is not None:
                    self.on_level_complete()
                return True

            if nx <= touch.x <= nx + nw and ny <= touch.y <= ny + nh:
                sound.play("click")
                print("↩ Отмена выхода")
                self.exit_popup_active = False
                self._draw_exit_popup()
                return True

            return True

        if not self.level_done:
            bx, by, bw, bh = self._get_action_button_area()
            if bx <= touch.x <= bx + bw and by <= touch.y <= by + bh:
                sound.play("click")
                if self._can_finish():
                    self._finish_level()
                else:
                    print("❓ Показать попап выхода")
                    self.exit_popup_active = True
                    self._draw_exit_popup()
                return True

        layout = self._get_right_panel_layout()
        for bid, (bx2, by2, bw2, bh2) in layout["slots"].items():
            if (bx2 <= touch.x <= bx2 + bw2
                    and by2 <= touch.y <= by2 + bh2):
                sound.play("click")
                bst.use_booster(self, bid)
                return True

        if self.pending_booster is not None:
            cell = r.screen_to_cell(touch.x, touch.y, self)
            if cell is not None:
                rr, cc = cell
                bst.apply_booster_on_cell(self, self.pending_booster, rr, cc)
                return True
            else:
                self.pending_booster = None
                return True

        return inp.on_touch_down(self, touch)

    def on_touch_up(self, touch):
        if self.game_over_screen is not None:
            return True
        if self.exit_popup_active:
            return True
        if self.pending_booster is not None:
            return True
        return inp.on_touch_up(self, touch)

    # ---------- Ход ----------

    def try_swap(self, r1, c1, r2, c2):
        self._reset_hint()

        val_at_source = self.board.grid[r1][c1]
        val_at_target = self.board.grid[r2][c2]

        spec_source = is_special(val_at_source)
        spec_target = is_special(val_at_target)

        # Звук свайпа
        sound.play("swipe")

        if spec_source and spec_target:
            print(f"💥 КОМБО")
            self.board.grid[r1][c1], self.board.grid[r2][c2] = \
                self.board.grid[r2][c2], self.board.grid[r1][c1]
            self.board._update_meteor_pos(r1, c1, r2, c2)
            self.moves_left -= 1
            self._tick_double_score()
            cells = self.board.combine_specials(r2, c2, r1, c1)
            self._explode_cells(cells)
            return

        if spec_source or spec_target:
            self.board.grid[r1][c1], self.board.grid[r2][c2] = \
                self.board.grid[r2][c2], self.board.grid[r1][c1]
            self.board._update_meteor_pos(r1, c1, r2, c2)

            if spec_source:
                spec_r, spec_c = r2, c2
            else:
                spec_r, spec_c = r1, c1

            self.moves_left -= 1
            self._tick_double_score()
            cells = self.board.activate_at(spec_r, spec_c)
            self._explode_cells(cells)
            return

        success = self.board.swap(r1, c1, r2, c2)
        if not success:
            print(f"❌ Свап ({r1},{c1})↔({r2},{c2}) — нет совпадений")
            return

        self.moves_left -= 1
        self._tick_double_score()
        print(f"✅ Свап ({r1},{c1})↔({r2},{c2}) | ходов: {self.moves_left}")
        found = find_all_matches(self.board.grid,
                                 self.board.rows, self.board.cols)
        animation.start_fade(self, found, preferred_cell=(r2, c2))

    def _tick_double_score(self):
        if self.double_score_turns > 0:
            self.double_score_turns -= 1

    def _explode_cells(self, cells):
        pre_grid = [row[:] for row in self.board.grid]

        self.fading = []
        for (r, c) in cells:
            if (0 <= r < self.board.rows and 0 <= c < self.board.cols
                    and self.board.grid[r][c] is not None):
                self.fading.append({
                    "cell": (r, c),
                    "progress": 0.0,
                    "tex_idx": pre_grid[r][c],
                })

        mult = 2 if self.double_score_turns > 0 else 1
        self.board.score += len(cells) * 15 * mult

        for (r, c) in cells:
            if 0 <= r < self.board.rows and 0 <= c < self.board.cols:
                v = self.board.grid[r][c]
                self.board._register_destroyed(v)
                self.board.grid[r][c] = None

        # Звук спецфигуры/взрыва
        sound.play("special")

        self.animating = True
        self.update_hud()
        Clock.schedule_once(
            lambda dt: animation._start_fall_phase(self),
            animation.FADE_DURATION,
        )
        Clock.schedule_interval(
            lambda dt: animation._animate_fade(self, dt), 1 / 60
        )

    # ---------- Конец уровня ----------

    def _finish_level(self):
        if self.level_done:
            return

        print("🛑 Игрок нажал «ФИНИШ»")
        bonus = self.moves_left * MOVES_TO_SCORE
        print(f"💰 Конвертация: {self.moves_left} × "
              f"{MOVES_TO_SCORE} = {bonus}")
        self.board.score += bonus
        self.moves_left = 0
        self.level_done = True

        stars = self._calculate_stars()
        app = App.get_running_app()
        if app is not None:
            from save import progress as prog
            prog.complete_level(app.progress, self.level_num, stars)
        self.update_hud()
        self._show_game_over(victory=True)

    def check_level_end(self):
        if self.level_done:
            return
        if self.animating:
            return

        goals = self.level.get("goals", [])
        state = self._game_state()
        all_done = all(lvl.describe_goal(g, state)["done"] for g in goals)

        out_of_moves = (self.moves_left <= 0)

        if out_of_moves:
            self.level_done = True
            if all_done:
                print(f"🎉 УРОВЕНЬ ПРОЙДЕН!")
                stars = self._calculate_stars()
                app = App.get_running_app()
                if app is not None:
                    from save import progress as prog
                    prog.complete_level(app.progress, self.level_num, stars)
                self._show_game_over(victory=True)
            else:
                print(f"❌ ПРОВАЛ (цели не выполнены)")
                self._show_game_over(victory=False)

    def _calculate_stars(self):
        target = None
        for g in self.level.get("goals", []):
            if g["type"] == "score":
                target = g["target"]
                break
        if target is None:
            target = 1000

        ratio = self.board.score / target
        if ratio >= 1.7:
            return 3
        elif ratio >= 1.3:
            return 2
        elif ratio >= 1.0:
            return 1
        return 0

    def _show_game_over(self, victory):
        if self.game_over_screen is not None:
            return
        self.game_over_screen = GameOverScreen(game=self, victory=victory)

    def restart_level(self):
        self.board = Board(
            rows=self.level["rows"],
            cols=self.level["cols"],
            holes=self.level.get("holes", []),
            ice=self.level.get("ice", []),
            meteor=self.level.get("meteor"),
        )

        if not has_any_move(self.board):
            print("⚠ На поле нет ходов, перемешиваем...")
            reshuffle_board(self.board)

        self.moves_left = self.level.get("moves", 30)
        self.level_done = False
        self.animating = False
        self.fading = []
        self.fall_offsets = {}
        self.selected_cell = None
        self.touch_start = None
        self.double_score_turns = 0
        self.exit_popup_active = False
        self._reset_hint()
        self._draw_exit_popup()
        bst.init_boosters(self)
        self.update_hud()
        self.redraw_dynamic()
        print("🔄 Уровень перезапущен")