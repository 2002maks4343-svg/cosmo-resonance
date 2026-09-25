"""Загрузка уровней и проверка целей."""
import json
import os


LEVELS_FILE = "data/levels.json"

# Кэш уровней (чтобы не перечитывать JSON каждый раз)
_LEVELS_CACHE = None


def load_levels():
    """Загружает все уровни из JSON."""
    global _LEVELS_CACHE
    if _LEVELS_CACHE is not None:
        return _LEVELS_CACHE

    if not os.path.exists(LEVELS_FILE):
        print(f"⚠ Не найден файл уровней: {LEVELS_FILE}")
        return []

    try:
        with open(LEVELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        _LEVELS_CACHE = data.get("levels", [])
        print(f"✅ Загружено уровней: {len(_LEVELS_CACHE)}")
        return _LEVELS_CACHE
    except Exception as e:
        print(f"⚠ Ошибка загрузки уровней: {e}")
        return []


def get_level(num):
    """Возвращает описание уровня по номеру (1-based)."""
    levels = load_levels()
    for lvl in levels:
        if lvl.get("num") == num:
            return lvl
    # Фолбэк — дефолтный уровень
    print(f"⚠ Уровень {num} не найден, использую дефолт")
    return {
        "num": num,
        "rows": 8, "cols": 8,
        "goals": [{"type": "score", "target": 1000}],
        "moves": 30,
        "holes": [], "ice": [], "meteor": None,
    }


# ---------- Описание целей для HUD ----------

COLOR_NAMES = {
    0: "КРАСНЫЕ",
    1: "СИНИЕ",
    2: "ЗЕЛЁНЫЕ",
    3: "ЖЁЛТЫЕ",
    4: "ФИОЛЕТ",
    5: "БЕЛЫЕ",
}


def describe_goal(goal, game_state):
    """
    Возвращает словарь для HUD:
    {"label": "...", "current": X, "target": Y, "done": bool}
    """
    gtype = goal["type"]

    if gtype == "score":
        cur = game_state["score"]
        tgt = goal["target"]
        return {
            "label": "ОЧКИ",
            "current": cur,
            "target": tgt,
            "done": cur >= tgt,
        }

    elif gtype == "color":
        color = goal["color"]
        cur = game_state["colors_destroyed"].get(color, 0)
        tgt = goal["count"]
        return {
            "label": COLOR_NAMES.get(color, f"ЦВЕТ{color}"),
            "current": cur,
            "target": tgt,
            "done": cur >= tgt,
        }

    elif gtype == "ice":
        cur = game_state["ice_left"]
        return {
            "label": "ЛЁД",
            "current": cur,
            "target": 0,
            "done": cur <= 0,
        }

    elif gtype == "meteor":
        done = game_state["meteor_done"]
        return {
            "label": "МЕТЕОРИТ",
            "current": "✔" if done else "...",
            "target": "",
            "done": done,
        }

    return {"label": "?", "current": 0, "target": 0, "done": False}


def all_goals_done(level, game_state):
    """Проверяет, все ли цели выполнены."""
    for goal in level.get("goals", []):
        info = describe_goal(goal, game_state)
        if not info["done"]:
            return False
    return True