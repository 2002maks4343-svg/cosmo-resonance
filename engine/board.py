"""
Игровое поле с динамическими размерами, дырками, льдом и метеоритом.
"""
import random
from engine.match import (
    find_all_matches, PLANET_TYPES,
    SUPERNOVA, BLACKHOLE, LIGHTNING_V, LIGHTNING_H,
    HOLE, METEOR,
    is_special, special_kind, base_planet_of_special, make_special,
    is_hole, is_meteor, is_ice, make_ice, base_planet_of_ice,
)


class Board:
    def __init__(self, rows=8, cols=8, holes=None, ice=None, meteor=None):
        self.rows = rows
        self.cols = cols
        self.score = 0

        self.holes = set() if holes is None else set(holes)
        self.ice_cells = set() if ice is None else set(ice)

        self.meteor = None
        if meteor is not None:
            mr, mc = meteor
            self.meteor = {"row": mr, "col": mc}

        self.colors_destroyed = {}
        self.ice_destroyed_count = 0
        self.meteor_done = False

        self.grid = [[None] * cols for _ in range(rows)]

        for (r, c) in self.holes:
            self.grid[r][c] = HOLE

        if self.meteor is not None:
            self.grid[self.meteor["row"]][self.meteor["col"]] = METEOR

        self.generate()

    # ---------- Генерация ----------

    def generate(self):
        if self.rows <= 4:
            self.planet_types = 4
        elif self.rows <= 6:
            self.planet_types = 5
        else:
            self.planet_types = 6

        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] in (HOLE, METEOR):
                    continue
                if self.grid[r][c] is not None:
                    continue
                self.grid[r][c] = self._safe_planet(r, c)

    def _safe_planet(self, r, c):
        banned = set()
        left1 = self._base_value(r, c - 1)
        left2 = self._base_value(r, c - 2)
        if c >= 2 and left1 == left2 and left1 is not None:
            banned.add(left1)
        up1 = self._base_value(r - 1, c)
        up2 = self._base_value(r - 2, c)
        if r >= 2 and up1 == up2 and up1 is not None:
            banned.add(up1)

        choices = [p for p in range(self.planet_types) if p not in banned]
        return random.choice(choices)

    def _base_value(self, r, c):
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return None
        v = self.grid[r][c]
        if v is None or v == HOLE or v == METEOR:
            return None
        if is_ice(v):
            return base_planet_of_ice(v)
        if is_special(v):
            return None
        return v

    # ---------- Свап ----------

    def swap(self, r1, c1, r2, c2):
        if abs(r1 - r2) + abs(c1 - c2) != 1:
            return False
        if self.grid[r1][c1] == HOLE or self.grid[r2][c2] == HOLE:
            return False

        self.grid[r1][c1], self.grid[r2][c2] = \
            self.grid[r2][c2], self.grid[r1][c1]
        self._update_meteor_pos(r1, c1, r2, c2)

        if find_all_matches(self.grid, self.rows, self.cols):
            return True

        self.grid[r1][c1], self.grid[r2][c2] = \
            self.grid[r2][c2], self.grid[r1][c1]
        self._update_meteor_pos(r1, c1, r2, c2)
        return False

    def _update_meteor_pos(self, r1, c1, r2, c2):
        if self.meteor is None:
            return
        if self.meteor["row"] == r1 and self.meteor["col"] == c1:
            self.meteor["row"] = r2
            self.meteor["col"] = c2
        elif self.meteor["row"] == r2 and self.meteor["col"] == c2:
            self.meteor["row"] = r1
            self.meteor["col"] = c1

    # ---------- Активация спецфигур ----------

    def _activate_specials(self, cells_to_remove, triggered_specials):
        queue = list(triggered_specials)
        processed = set()

        while queue:
            (r, c) = queue.pop()
            if (r, c) in processed:
                continue
            processed.add((r, c))
            if (r, c) not in cells_to_remove:
                continue

            val = self.grid[r][c]
            if not is_special(val):
                continue

            kind = special_kind(val)
            planet = base_planet_of_special(val)
            extra = set()

            if kind == "lightning_h":
                for cc in range(self.cols):
                    extra.add((r, cc))
            elif kind == "lightning_v":
                for rr in range(self.rows):
                    extra.add((rr, c))
            elif kind == "supernova":
                for rr in range(self.rows):
                    for cc in range(self.cols):
                        v = self.grid[rr][cc]
                        if v is None:
                            continue
                        base = (base_planet_of_special(v)
                                if is_special(v)
                                else base_planet_of_ice(v) if is_ice(v) else v)
                        if base == planet:
                            extra.add((rr, cc))
            elif kind == "blackhole":
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < self.rows and 0 <= cc < self.cols:
                            extra.add((rr, cc))

            for cell in extra:
                if self.grid[cell[0]][cell[1]] == HOLE:
                    continue
                if cell not in cells_to_remove:
                    cells_to_remove.add(cell)
                v = self.grid[cell[0]][cell[1]]
                if is_special(v) and cell not in processed:
                    queue.append(cell)

    def activate_at(self, r, c):
        cells = {(r, c)}
        if is_special(self.grid[r][c]):
            self._activate_specials(cells, [(r, c)])
        return cells

    def combine_specials(self, r1, c1, r2, c2):
        val1 = self.grid[r1][c1]
        val2 = self.grid[r2][c2]

        kind1 = special_kind(val1)
        kind2 = special_kind(val2)
        planet1 = base_planet_of_special(val1)
        planet2 = base_planet_of_special(val2)

        cells = {(r1, c1), (r2, c2)}
        pair = {kind1, kind2}

        if kind1 == "supernova" and kind2 == "supernova":
            for rr in range(self.rows):
                for cc in range(self.cols):
                    if self.grid[rr][cc] != HOLE:
                        cells.add((rr, cc))
            return cells

        if kind1 in ("lightning_h", "lightning_v") and \
           kind2 in ("lightning_h", "lightning_v"):
            for cc in range(self.cols):
                if self.grid[r2][cc] != HOLE:
                    cells.add((r2, cc))
            for rr in range(self.rows):
                if self.grid[rr][c2] != HOLE:
                    cells.add((rr, c2))
            return cells

        if kind1 == "blackhole" and kind2 == "blackhole":
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    rr, cc = r2 + dr, c2 + dc
                    if (0 <= rr < self.rows and 0 <= cc < self.cols
                            and self.grid[rr][cc] != HOLE):
                        cells.add((rr, cc))
            return cells

        if pair == {"blackhole", "lightning_h"}:
            for dr in range(-1, 2):
                rr = r2 + dr
                if 0 <= rr < self.rows:
                    for cc in range(self.cols):
                        if self.grid[rr][cc] != HOLE:
                            cells.add((rr, cc))
            return cells

        if pair == {"blackhole", "lightning_v"}:
            for dc in range(-1, 2):
                cc = c2 + dc
                if 0 <= cc < self.cols:
                    for rr in range(self.rows):
                        if self.grid[rr][cc] != HOLE:
                            cells.add((rr, cc))
            return cells

        if pair == {"lightning_h", "supernova"} or \
           pair == {"lightning_v", "supernova"}:
            target_planet = planet1 if kind1 == "supernova" else planet2
            lk = ("lightning_h" if "lightning_h" in pair else "lightning_v")
            new_specials = []
            for rr in range(self.rows):
                for cc in range(self.cols):
                    v = self.grid[rr][cc]
                    if v is None or is_special(v) or v == HOLE or v == METEOR:
                        continue
                    base = base_planet_of_ice(v) if is_ice(v) else v
                    if base == target_planet:
                        self.grid[rr][cc] = make_special(lk, target_planet)
                        new_specials.append((rr, cc))
            for (rr, cc) in new_specials:
                self._activate_specials(cells, [(rr, cc)])
            return cells

        if pair == {"blackhole", "supernova"}:
            target_planet = planet1 if kind1 == "supernova" else planet2
            new_specials = []
            for rr in range(self.rows):
                for cc in range(self.cols):
                    v = self.grid[rr][cc]
                    if v is None or is_special(v) or v == HOLE or v == METEOR:
                        continue
                    base = base_planet_of_ice(v) if is_ice(v) else v
                    if base == target_planet:
                        self.grid[rr][cc] = make_special("blackhole", target_planet)
                        new_specials.append((rr, cc))
            for (rr, cc) in new_specials:
                self._activate_specials(cells, [(rr, cc)])
            return cells

        self._activate_specials(cells, [(r1, c1), (r2, c2)])
        return cells

    # ---------- Обработка совпадений ----------

    def process_matches(self, preferred_cell=None):
        found = find_all_matches(self.grid, self.rows, self.cols)
        if not found:
            return []

        cells_to_remove = set()
        special_creations = {}

        for group in found:
            kind = group["kind"]
            cells = group["cells"]
            for cell in cells:
                cells_to_remove.add(cell)

            if kind != "normal":
                if preferred_cell is not None and preferred_cell in cells:
                    target = preferred_cell
                else:
                    target = random.choice(cells)

                r0, c0 = target
                base_planet = base_planet_of_special(self.grid[r0][c0])
                if is_ice(self.grid[r0][c0]):
                    base_planet = base_planet_of_ice(self.grid[r0][c0])
                special_creations[target] = make_special(kind, base_planet)
                print(f"✨ Создаём {kind} на {target}, планета={base_planet}")

        triggered = [cell for cell in cells_to_remove
                     if is_special(self.grid[cell[0]][cell[1]])]
        self._activate_specials(cells_to_remove, triggered)

        for group in found:
            kind = group["kind"]
            cells = group["cells"]
            base = len(cells) * 10
            multiplier = {"normal": 1,
                          "lightning_h": 2, "lightning_v": 2,
                          "supernova": 3, "blackhole": 2}[kind]
            self.score += base * multiplier

        for (r, c) in cells_to_remove:
            if (r, c) in special_creations:
                continue
            v = self.grid[r][c]
            if v == HOLE:
                continue
            self._register_destroyed(v)
            self.grid[r][c] = None

        created = []
        for (r, c), code in special_creations.items():
            self.grid[r][c] = code
            created.append({"cell": (r, c), "kind": special_kind(code)})

        return created

    def _register_destroyed(self, value):
        if value is None or value == HOLE or value == METEOR:
            return

        if is_ice(value):
            base = base_planet_of_ice(value)
            self.colors_destroyed[base] = self.colors_destroyed.get(base, 0) + 1
            self.ice_destroyed_count += 1
            return
        if is_special(value):
            base = base_planet_of_special(value)
            self.colors_destroyed[base] = self.colors_destroyed.get(base, 0) + 1
            return
        self.colors_destroyed[value] = self.colors_destroyed.get(value, 0) + 1

    # ---------- Гравитация ----------

    def apply_gravity(self):
        for c in range(self.cols):
            segments = []
            current_segment = []
            for r in range(self.rows):
                if self.grid[r][c] == HOLE:
                    if current_segment:
                        segments.append(current_segment)
                        current_segment = []
                else:
                    current_segment.append(r)
            if current_segment:
                segments.append(current_segment)

            new_col = [None] * self.rows
            for r in range(self.rows):
                if self.grid[r][c] == HOLE:
                    new_col[r] = HOLE

            for seg in segments:
                values = [self.grid[r][c] for r in seg
                          if self.grid[r][c] is not None]
                missing = len(seg) - len(values)
                new_values = [None] * missing + values
                for i, r in enumerate(seg):
                    new_col[r] = new_values[i]

            for r in range(self.rows):
                if new_col[r] is None:
                    new_col[r] = random.randint(0, self.planet_types - 1)

            for r in range(self.rows):
                self.grid[r][c] = new_col[r]

        self._apply_meteor_gravity()

    def _apply_meteor_gravity(self):
        if self.meteor is None or self.meteor_done:
            return

        mr = self.meteor["row"]
        mc = self.meteor["col"]

        while True:
            if mr + 1 >= self.rows:
                break
            below = self.grid[mr + 1][mc]
            if below is None:
                self.grid[mr][mc], self.grid[mr + 1][mc] = \
                    self.grid[mr + 1][mc], self.grid[mr][mc]
                mr += 1
            else:
                break

        self.meteor["row"] = mr
        self.meteor["col"] = mc

        if mr == self.rows - 1:
            self.meteor_done = True
            print("🌠 Метеорит достиг нижней строки!")

    def resolve_turn(self):
        all_specials = []
        while True:
            specials = self.process_matches()
            if not specials and not find_all_matches(self.grid, self.rows, self.cols):
                break
            all_specials.extend(specials)
            self.apply_gravity()
        return all_specials

    # ---------- Печать ----------

    def print_board(self):
        symbols = ["R", "B", "G", "Y", "P", "W"]
        special_mark = {SUPERNOVA: "+", BLACKHOLE: "@",
                        LIGHTNING_V: "|", LIGHTNING_H: "-"}

        print("   " + " ".join(f"{c:>2}" for c in range(self.cols)))
        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                v = self.grid[r][c]
                if v is None:
                    row.append(" .")
                elif v == HOLE:
                    row.append(" #")
                elif v == METEOR:
                    row.append(" M")
                elif is_ice(v):
                    base = base_planet_of_ice(v)
                    row.append(f"{symbols[base]}*")
                elif is_special(v):
                    base = v // 100 * 100
                    mark = special_mark.get(base, "?")
                    bp = base_planet_of_special(v)
                    row.append(f"{symbols[bp]}{mark}")
                else:
                    row.append(f" {symbols[v]}")
            print(f"{r:>2} " + " ".join(row))
        print(f"Очки: {self.score}\n")


# ---------- Проверка ходов и перемешка ----------

def has_any_move(board):
    """Проверяет, есть ли хоть один ход, дающий совпадение."""
    rows, cols = board.rows, board.cols
    grid = board.grid

    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                if _swap_makes_match(grid, r, c, r, c + 1, rows, cols):
                    return True
            if r + 1 < rows:
                if _swap_makes_match(grid, r, c, r + 1, c, rows, cols):
                    return True
    return False


def _swap_makes_match(grid, r1, c1, r2, c2, rows, cols):
    """Проверяет, даст ли этот свап совпадение."""
    v1 = grid[r1][c1]
    v2 = grid[r2][c2]
    if v1 in (HOLE, METEOR) or v2 in (HOLE, METEOR):
        return False
    if v1 is None or v2 is None:
        return False

    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    result = bool(find_all_matches(grid, rows, cols))
    grid[r1][c1], grid[r2][c2] = grid[r2][c2], grid[r1][c1]
    return result


def reshuffle_board(board):
    """Перемешивает обычные планеты. Метеорит, лёд, дырки — на месте."""
    rows, cols = board.rows, board.cols
    grid = board.grid

    positions = []
    values = []
    for r in range(rows):
        for c in range(cols):
            v = grid[r][c]
            if v is None or v == HOLE or v == METEOR:
                continue
            if is_ice(v):
                continue
            if is_special(v):
                continue
            positions.append((r, c))
            values.append(v)

    random.shuffle(values)
    for (r, c), v in zip(positions, values):
        grid[r][c] = v

    attempts = 0
    while not has_any_move(board) and attempts < 10:
        random.shuffle(values)
        for (r, c), v in zip(positions, values):
            grid[r][c] = v
        attempts += 1

    print(f"🔄 Перемешано (попыток: {attempts + 1})")
    return attempts + 1