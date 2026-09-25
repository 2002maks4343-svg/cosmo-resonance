"""Экран магазина — покупка бустеров за звёзды."""
import os
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.graphics.texture import Texture
from kivy.core.text import Label as CoreLabel
from PIL import Image as PILImage

from save import progress as prog


# Бустеры и их цены
SHOP_ITEMS = [
    {"id": "hammer", "file": "hammer.png", "name": "МОЛОТ", "price": 3},
    {"id": "freeze", "file": "freeze.png", "name": "+3 ХОДА", "price": 5},
    {"id": "shuffle", "file": "shuffle.png", "name": "ПЕРЕМЕШ.", "price": 6},
    {"id": "rocket", "file": "rocket.png", "name": "РАКЕТА", "price": 8},
    {"id": "double", "file": "double.png", "name": "×2 ОЧКИ", "price": 10},
]

ASSETS_DIR = "assets/boosters"


class ShopScreen(Widget):
    """Экран магазина."""

    def __init__(self, app_ref, on_back, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = app_ref
        self.on_back = on_back

        self.bind(size=self._on_resize, pos=self._on_resize)

        # Загружаем иконки
        self.textures = {}
        for item in SHOP_ITEMS:
            path = os.path.join(ASSETS_DIR, item["file"])
            if os.path.exists(path):
                pil_img = PILImage.open(path).convert("RGBA")
                tex = Texture.create(size=pil_img.size, colorfmt="rgba")
                tex.blit_buffer(pil_img.tobytes(), colorfmt="rgba",
                                bufferfmt="ubyte")
                tex.flip_vertical()
                self.textures[item["id"]] = tex

        self.buy_areas = {}   # {booster_id: (x, y, w, h)}
        self.back_area = (0, 0, 0, 0)

        # Всплывающее сообщение
        self.message = ""
        self.message_timer = 0.0

        self._text_cache = {}
        self._draw_all()

    def _on_resize(self, *args):
        self._draw_all()

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

    # ---------- Отрисовка ----------

    def _draw_all(self):
        self.canvas.clear()

        w, h = self.width, self.height
        if w < 100 or h < 100:
            return

        # Фон
        with self.canvas:
            Color(0.02, 0.02, 0.06, 1)
            Rectangle(pos=(0, 0), size=(w, h))

        # Заголовок
        with self.canvas:
            Color(1, 1, 1, 1)
            self._draw_text_centered(
                "МАГАЗИН", w / 2, h * 0.92,
                font_size=40, color=(0.7, 0.9, 1.0, 1),
            )

        # Кнопка «Назад»
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

        # Баланс звёзд сверху
        stars = prog.available_stars(self.app_ref.progress)
        with self.canvas:
            Color(1, 0.9, 0.2, 1)
            # Звёздочка + число
            self._draw_text_centered(
                f"★ {stars}", w / 2, h * 0.85,
                font_size=26, color=(1, 0.9, 0.2, 1),
            )

        # Сетка товаров: 5 карточек
        # Разместим горизонтально, если места хватает, иначе вертикально
        n = len(SHOP_ITEMS)
        margin_x = 30
        margin_top = h * 0.22
        margin_bottom = h * 0.08

        avail_w = w - margin_x * 2
        avail_h = h - margin_top - margin_bottom

        # Горизонтально: 5 карточек
        card_w = min(160, avail_w / n - 10)
        card_h = min(300, avail_h)
        gap = (avail_w - card_w * n) / (n - 1) if n > 1 else 0
        start_x = margin_x
        card_y = margin_bottom

        self.buy_areas = {}

        for i, item in enumerate(SHOP_ITEMS):
            cx = start_x + i * (card_w + gap)
            self._draw_card(item, cx, card_y, card_w, card_h)

        # Сообщение
        if self.message:
            with self.canvas:
                Color(1, 0.9, 0.3, 1)
                self._draw_text_centered(
                    self.message, w / 2, h * 0.16,
                    font_size=20, color=(1, 0.9, 0.3, 1),
                )

    def _draw_card(self, item, x, y, cw, ch):
        """Рисует карточку бустера."""
        bid = item["id"]
        price = item["price"]

        count = prog.get_booster_count(self.app_ref.progress, bid)
        available = prog.available_stars(self.app_ref.progress)
        can_buy = available >= price

        # Фон карточки
        with self.canvas:
            Color(0.05, 0.08, 0.16, 1)
            Rectangle(pos=(x, y), size=(cw, ch))
            Color(0.4, 0.8, 1.0, 0.9)
            Line(rectangle=(x, y, cw, ch), width=2)

        # Иконка (сверху)
        tex = self.textures.get(bid)
        icon_size = min(cw - 30, 80)
        icon_x = x + (cw - icon_size) / 2
        icon_y = y + ch - icon_size - 20

        if tex is not None:
            with self.canvas:
                Color(1, 1, 1, 1)
                Rectangle(
                    texture=tex,
                    pos=(icon_x, icon_y),
                    size=(icon_size, icon_size),
                )

        # Название
        with self.canvas:
            Color(1, 1, 1, 1)
            self._draw_text_centered(
                item["name"], x + cw / 2, y + ch - 120,
                font_size=16, color=(0.85, 0.95, 1, 1),
            )
            self._draw_text_centered(
                f"есть: {count}", x + cw / 2, y + ch - 145,
                font_size=13, color=(0.6, 0.75, 0.9, 1),
            )

        # Цена
        with self.canvas:
            self._draw_text_centered(
                f"★ {price}", x + cw / 2, y + 75,
                font_size=22, color=(1, 0.9, 0.2, 1),
            )

        # Кнопка «КУПИТЬ» или «НЕ ХВАТАЕТ»
        btn_w = cw - 20
        btn_h = 40
        btn_x = x + 10
        btn_y = y + 20

        if can_buy:
            bg = (0.15, 0.55, 0.3, 1)
            border = (0.4, 1.0, 0.6, 1)
            label = "КУПИТЬ"
            label_color = (1, 1, 1, 1)
        else:
            bg = (0.3, 0.15, 0.15, 1)
            border = (0.6, 0.3, 0.3, 1)
            label = "НЕ ХВАТАЕТ"
            label_color = (0.7, 0.5, 0.5, 1)

        with self.canvas:
            Color(*bg)
            Rectangle(pos=(btn_x, btn_y), size=(btn_w, btn_h))
            Color(*border)
            Line(rectangle=(btn_x, btn_y, btn_w, btn_h), width=2)
            self._draw_text_centered(
                label, btn_x + btn_w / 2, btn_y + btn_h / 2 - 9,
                font_size=14, color=label_color,
            )

        self.buy_areas[bid] = (btn_x, btn_y, btn_w, btn_h)

    # ---------- Ввод ----------

    def on_touch_down(self, touch):
        # Назад
        bx, by, bw, bh = self.back_area
        if bx <= touch.x <= bx + bw and by <= touch.y <= by + bh:
            self.on_back()
            return True

        # Покупка
        for bid, (bx, by, bw, bh) in self.buy_areas.items():
            if bx <= touch.x <= bx + bw and by <= touch.y <= by + bh:
                self._try_buy(bid)
                return True

        return True

    def _try_buy(self, bid):
        item = next((x for x in SHOP_ITEMS if x["id"] == bid), None)
        if item is None:
            return
        price = item["price"]

        success = prog.buy_booster(self.app_ref.progress, bid, price)
        if success:
            self.message = f"Куплено: {item['name']}!"
            print(f"✅ Куплено {bid} за {price}★")
        else:
            self.message = "Не хватает звёзд!"
            print(f"❌ Не хватает звёзд для {bid}")

        self._draw_all()