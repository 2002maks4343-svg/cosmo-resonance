"""
Поиск совпадений на игровом поле.

Специальные значения в клетках:
- None — пусто (падает)
- 0..5 — обычные планеты
- 100..105 — комета (уничтожает ряд)
- 200..205 — сверхновая (все планеты цвета)
- 300..305 — чёрная дыра (3×3)
- 400..405 — молния вертикальная (столбец)
- 500..505 — молния горизонтальная (ряд)
- 900 — дырка (пустая клетка поля, не падает, не матчится)
- 950 — метеорит (падает, не матчится)
- 960 — лёд (планета подо льдом — матчится как обычная)
"""
PLANET_TYPES = 6

# Спецфигуры
SUPERNOVA = 200
BLACKHOLE = 300
LIGHTNING_V = 400
LIGHTNING_H = 500

# Особые клетки
HOLE = 900        # дырка — на поле не появляется планета
METEOR = 950      # метеорит — падает, не матчится
ICE = 960         # лёд (используется как маска для планет, от 0 до 959)


def find_all_matches(board, rows, cols):
    """Находит все совпадения. Различает горизонтальные и вертикальные."""
    matches = []

    # --- Горизонтальные ---
    for r in range(rows):
        run_start = 0
        for c in range(1, cols + 1):
            same = (c < cols
                    and board[r][c] is not None
                    and board[r][c] == board[r][run_start]
                    and is_matchable(board[r][c]))
            if not same:
                run_len = c - run_start
                if (run_len >= 3
                        and is_matchable(board[r][run_start])):
                    group = [(r, x) for x in range(run_start, c)]
                    matches.append({"cells": group, "orientation": "h"})
                run_start = c

    # --- Вертикальные ---
    for c in range(cols):
        run_start = 0
        for r in range(1, rows + 1):
            same = (r < rows
                    and board[r][c] is not None
                    and board[r][c] == board[run_start][c]
                    and is_matchable(board[r][c]))
            if not same:
                run_len = r - run_start
                if (run_len >= 3
                        and is_matchable(board[run_start][c])):
                    group = [(x, c) for x in range(run_start, r)]
                    matches.append({"cells": group, "orientation": "v"})
                run_start = r

    merged = merge_groups(matches)

    result = []
    for group in merged:
        cells = set(group["cells"])
        orientations = group["orientations"]
        has_h = "h" in orientations
        has_v = "v" in orientations
        size = len(cells)

        if has_h and has_v:
            kind = "blackhole"
        elif size >= 5:
            kind = "supernova"
        elif size == 4:
            if "h" in orientations:
                kind = "lightning_v"
            else:
                kind = "lightning_h"
        else:
            kind = "normal"

        result.append({"cells": list(cells), "kind": kind})

    return result


def merge_groups(groups):
    merged = []
    used = [False] * len(groups)

    for i in range(len(groups)):
        if used[i]:
            continue
        current = set(groups[i]["cells"])
        orientations = {groups[i]["orientation"]}
        used[i] = True
        changed = True
        while changed:
            changed = False
            for j in range(len(groups)):
                if used[j]:
                    continue
                if current & set(groups[j]["cells"]):
                    current |= set(groups[j]["cells"])
                    orientations.add(groups[j]["orientation"])
                    used[j] = True
                    changed = True
        merged.append({"cells": list(current), "orientations": orientations})
    return merged


def is_matchable(value):
    """Может ли клетка участвовать в матче?"""
    if value is None:
        return False
    if value == HOLE:
        return False
    if value == METEOR:
        return False
    # Спецфигуры матчатся как базовые планеты (упрощение — не матчатся)
    if value >= 100 and value < HOLE:
        return False
    return True


def is_special(value):
    return value is not None and 100 <= value < 900


def special_kind(value):
    if value is None or value < 100 or value >= 900:
        return None
    base = value // 100 * 100
    if base == SUPERNOVA:
        return "supernova"
    if base == BLACKHOLE:
        return "blackhole"
    if base == LIGHTNING_V:
        return "lightning_v"
    if base == LIGHTNING_H:
        return "lightning_h"
    return None


def base_planet_of_special(value):
    if value is None or value < 100 or value >= 900:
        return value
    return value % 100


def make_special(kind, planet_idx):
    if kind == "supernova":
        return SUPERNOVA + planet_idx
    if kind == "blackhole":
        return BLACKHOLE + planet_idx
    if kind == "lightning_v":
        return LIGHTNING_V + planet_idx
    if kind == "lightning_h":
        return LIGHTNING_H + planet_idx
    return planet_idx


def is_hole(value):
    return value == HOLE


def is_meteor(value):
    return value == METEOR


def is_ice(value):
    return value is not None and 960 <= value < 1000


def make_ice(planet_idx):
    """Кодирует планету подо льдом: 960 + planet."""
    return 960 + planet_idx


def base_planet_of_ice(value):
    if is_ice(value):
        return value - 960
    return value