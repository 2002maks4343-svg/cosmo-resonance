"""Обработка свайпов и тапов."""
from ui.renderer import screen_to_cell


SWIPE_THRESHOLD = 20


def on_touch_down(widget, touch):
    if widget.animating or widget.level_done:
        return False
    if not widget.collide_point(*touch.pos):
        return False
    widget.touch_start = touch.pos
    return True


def on_touch_up(widget, touch):
    if widget.animating or widget.level_done or widget.touch_start is None:
        return False

    dx = touch.x - widget.touch_start[0]
    dy = touch.y - widget.touch_start[1]
    dist = (dx ** 2 + dy ** 2) ** 0.5
    start_cell = screen_to_cell(*widget.touch_start, widget)
    widget.touch_start = None

    if start_cell is None:
        return True

    rows = widget.board.rows
    cols = widget.board.cols

    if dist >= SWIPE_THRESHOLD:
        if abs(dx) > abs(dy):
            dc = 1 if dx > 0 else -1
            dr = 0
        else:
            dr = -1 if dy > 0 else 1
            dc = 0
        r1, c1 = start_cell
        r2, c2 = r1 + dr, c1 + dc
        if 0 <= r2 < rows and 0 <= c2 < cols:
            widget.try_swap(r1, c1, r2, c2)
        widget.selected_cell = None
    else:
        _handle_tap(widget, start_cell)

    widget.redraw_dynamic()
    return True


def _handle_tap(widget, cell):
    if widget.selected_cell is None:
        widget.selected_cell = cell
        return
    r1, c1 = widget.selected_cell
    r2, c2 = cell
    if (r1, c1) == (r2, c2):
        widget.selected_cell = None
        return
    if abs(r1 - r2) + abs(c1 - c2) == 1:
        widget.try_swap(r1, c1, r2, c2)
        widget.selected_cell = None
    else:
        widget.selected_cell = cell