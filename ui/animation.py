"""Анимации исчезновения и падения."""
from kivy.clock import Clock
from engine.match import find_all_matches
from engine.board import has_any_move, reshuffle_board


FADE_DURATION = 0.22
FALL_DURATION = 0.28


def start_fade(widget, found_matches, preferred_cell=None):
    """Запускает анимацию. preferred_cell — точка свайпа."""
    pre_grid = [row[:] for row in widget.board.grid]

    widget.fading = []
    for group in found_matches:
        for (r, c) in group["cells"]:
            widget.fading.append({
                "cell": (r, c),
                "progress": 0.0,
                "tex_idx": pre_grid[r][c],
            })

    created = widget.board.process_matches(preferred_cell=preferred_cell)
    if created:
        for s in created:
            print(f"   ✨ Создана: {s}")

    widget.animating = True
    Clock.schedule_once(lambda dt: _start_fall_phase(widget), FADE_DURATION)
    Clock.schedule_interval(lambda dt: _animate_fade(widget, dt), 1 / 60)


def _animate_fade(widget, dt):
    if not widget.fading:
        Clock.unschedule(lambda d: _animate_fade(widget, d))
        return False
    all_done = True
    step = dt / FADE_DURATION
    for f in widget.fading:
        f["progress"] += step
        if f["progress"] < 1.0:
            all_done = False
        else:
            f["progress"] = 1.0
    widget.redraw_dynamic()
    if all_done:
        Clock.unschedule(lambda d: _animate_fade(widget, d))
    return True


def _start_fall_phase(widget):
    widget.fading = []
    old_grid = [row[:] for row in widget.board.grid]
    widget.board.apply_gravity()
    new_grid = widget.board.grid

    widget.fall_offsets = {}
    for c in range(widget.board.cols):
        old_col = [old_grid[r][c] for r in range(widget.board.rows)]
        new_col = [new_grid[r][c] for r in range(widget.board.rows)]
        old_nonempty = [v for v in old_col if v is not None]

        for r in range(widget.board.rows):
            idx_from_bottom = widget.board.rows - 1 - r
            if idx_from_bottom >= len(old_nonempty):
                widget.fall_offsets[(r, c)] = -8
            else:
                old_r = widget.board.rows - 1 - idx_from_bottom
                if old_r != r:
                    widget.fall_offsets[(r, c)] = old_r - r

    widget._fall_start_offsets = dict(widget.fall_offsets)
    widget._fall_progress = 0.0
    Clock.schedule_interval(lambda dt: _animate_fall(widget, dt), 1 / 60)


def _animate_fall(widget, dt):
    widget._fall_progress += dt / FALL_DURATION
    p = min(widget._fall_progress, 1.0)
    eased = 1 - (1 - p) ** 3
    for key in list(widget.fall_offsets.keys()):
        start = widget._fall_start_offsets[key]
        widget.fall_offsets[key] = start * (1 - eased)
    widget.redraw_dynamic()
    if p >= 1.0:
        Clock.unschedule(lambda d: _animate_fall(widget, d))
        widget.fall_offsets = {}
        _check_cascade(widget)
    return True


def _check_cascade(widget):
    found = find_all_matches(
        widget.board.grid, widget.board.rows, widget.board.cols
    )
    if not found:
        # Проверяем, есть ли ходы
        if not has_any_move(widget.board):
            print("⚠ Нет ходов — автоматическая перемешка")
            reshuffle_board(widget.board)
            widget.redraw_dynamic()
        widget.animating = False
        widget.update_hud()
        widget.check_level_end()
        return
    start_fade(widget, found, preferred_cell=None)