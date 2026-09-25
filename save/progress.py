"""Сохранение и загрузка прогресса игрока."""
import json
import os


SAVE_DIR = "save"
SAVE_FILE = os.path.join(SAVE_DIR, "progress.json")

# Инвентарь бустеров по умолчанию
DEFAULT_BOOSTERS = {
    "hammer": 3,
    "shuffle": 3,
    "rocket": 3,
    "freeze": 3,
    "double": 3,
}

DEFAULT_PROGRESS = {
    "unlocked_level": 1,
    "stars": {},
    "boosters": dict(DEFAULT_BOOSTERS),
}


def load_progress():
    os.makedirs(SAVE_DIR, exist_ok=True)
    if not os.path.exists(SAVE_FILE):
        return dict(DEFAULT_PROGRESS)
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "unlocked_level" not in data:
            data["unlocked_level"] = 1
        if "stars" not in data:
            data["stars"] = {}
        if "boosters" not in data:
            data["boosters"] = dict(DEFAULT_BOOSTERS)
        return data
    except Exception as e:
        print(f"⚠ Ошибка загрузки прогресса: {e}")
        return dict(DEFAULT_PROGRESS)


def save_progress(progress):
    os.makedirs(SAVE_DIR, exist_ok=True)
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ Ошибка сохранения прогресса: {e}")


def get_stars(progress, level_num):
    return progress.get("stars", {}).get(str(level_num), 0)


def total_stars(progress):
    """Всего звёзд у игрока (сумма по всем уровням)."""
    return sum(progress.get("stars", {}).values())


def complete_level(progress, level_num, stars):
    stars = max(0, min(3, stars))
    current = get_stars(progress, level_num)
    if stars > current:
        progress["stars"][str(level_num)] = stars
    if level_num + 1 > progress["unlocked_level"]:
        progress["unlocked_level"] = min(level_num + 1, 30)
    save_progress(progress)


# ---------- Бустеры ----------

def get_booster_count(progress, booster_id):
    return progress.get("boosters", {}).get(booster_id, 0)


def add_booster(progress, booster_id, count=1):
    if "boosters" not in progress:
        progress["boosters"] = dict(DEFAULT_BOOSTERS)
    progress["boosters"][booster_id] = \
        progress["boosters"].get(booster_id, 0) + count
    save_progress(progress)


def spend_stars(progress, amount):
    """Списывает звёзды (проверка снаружи)."""
    # Звёзды не списываются — они общий счёт.
    # Трата — виртуальная (мы просто проверяем total_stars >= amount).
    pass


def buy_booster(progress, booster_id, price):
    """Покупка бустера. Возвращает True, если успешно."""
    if total_stars(progress) < price:
        return False
    # Списываем звёзды — уменьшаем у последних уровней
    # Простое решение: ведём счётчик потраченных звёзд
    spent = progress.get("spent_stars", 0)
    progress["spent_stars"] = spent + price
    add_booster(progress, booster_id, 1)
    return True


def available_stars(progress):
    """Доступные звёзды = всего - потрачено."""
    total = total_stars(progress)
    spent = progress.get("spent_stars", 0)
    return max(0, total - spent)