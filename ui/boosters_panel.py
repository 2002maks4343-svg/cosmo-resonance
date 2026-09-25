"""Правая панель бустеров (пока пустая заготовка)."""
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Line


class BoostersPanel(FloatLayout):
    """Правая вертикальная панель с 5 слотами."""

    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.size_hint = (None, None)

        with self.canvas.before:
            Color(0.15, 0.25, 0.45, 1)  # ЯРКИЙ синий — для теста
            self._panel_rect = Rectangle()
            Color(0.4, 0.8, 1.0, 1.0)
            self._panel_line = Line(width=2)

        self.title = Label(
            text="[b]АРТЕФАКТЫ[/b]",
            markup=True,
            halign="center",
            valign="middle",
            font_size="11sp",
            color=(1, 1, 1, 1),
            size_hint=(None, None),
        )
        self.add_widget(self.title)

        self.bind(size=self._redraw, pos=self._redraw)

    def _redraw(self, *args):
        w, h = self.size
        if w == 0 or h == 0:
            return

        self._panel_rect.pos = self.pos
        self._panel_rect.size = (w, h)
        self._panel_line.rectangle = (self.x, self.y, w, h)

        self.title.size = (w, 25)
        self.title.pos = (self.x, self.y + h - 25)
        self.title.text_size = (w, 25)

    def draw_slots(self):
        w, h = self.size
        if w == 0 or h == 0:
            return

        top = 30
        bottom = 10
        avail_h = h - top - bottom
        slot_size = min(w - 20, avail_h / 5 - 8)

        self.canvas.after.clear()
        with self.canvas.after:
            for i in range(5):
                y = self.y + h - top - (i + 1) * (slot_size + 6)
                x = self.x + (w - slot_size) / 2
                Color(0.1, 0.15, 0.25, 0.8)
                Rectangle(pos=(x, y), size=(slot_size, slot_size))
                Color(0.3, 0.6, 1.0, 0.6)
                Line(rectangle=(x, y, slot_size, slot_size), width=1.5)