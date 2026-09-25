"""HUD — левая панель со счётом, целью и ходами."""
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.graphics import Color, Rectangle, Line


class HUD(FloatLayout):
    """Левая вертикальная панель: ОЧКИ / ЦЕЛЬ / ХОДЫ."""

    def __init__(self, game, **kwargs):
        super().__init__(**kwargs)
        self.game = game
        self.size_hint = (None, None)

        with self.canvas.before:
            Color(0.15, 0.25, 0.45, 1)  # ЯРКИЙ синий — для теста
            self._panel_rect = Rectangle()
            Color(0.4, 0.8, 1.0, 1.0)
            self._panel_line = Line(width=2)

        common = dict(
            markup=True,
            halign="center",
            valign="middle",
            font_size="13sp",
            color=(1, 1, 1, 1),
            size_hint=(None, None),
        )
        self.label_score = Label(**common)
        self.label_target = Label(**common)
        self.label_moves = Label(**common)
        self.add_widget(self.label_score)
        self.add_widget(self.label_target)
        self.add_widget(self.label_moves)

        self.bind(size=self._update_layout, pos=self._update_layout)

    def update_texts(self):
        self.label_score.text = f"[b]ОЧКИ[/b]\n{self.game.board.score}"
        self.label_target.text = (
            f"[b]ЦЕЛЬ[/b]\n{self.game.board.score}/{self.game.target_score}"
        )
        self.label_moves.text = f"[b]ХОДЫ[/b]\n{self.game.moves_left}"

    def _update_layout(self, *args):
        w, h = self.size
        if w == 0 or h == 0:
            return

        self._panel_rect.pos = self.pos
        self._panel_rect.size = (w, h)
        self._panel_line.rectangle = (self.x, self.y, w, h)

        third = h / 3

        self.label_score.size = (w, third)
        self.label_score.pos = (self.x, self.y + third * 2)
        self.label_score.text_size = (w, third)

        self.label_target.size = (w, third)
        self.label_target.pos = (self.x, self.y + third)
        self.label_target.text_size = (w, third)

        self.label_moves.size = (w, third)
        self.label_moves.pos = (self.x, self.y)
        self.label_moves.text_size = (w, third)