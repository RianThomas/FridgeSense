"""Shelf life, ripeness and use-by dates.

Ripeness is one of three words: Priority (use within ~2 days), Moderate
(within ~5), Safe (longer). It is stored as a use-by date and re-derived from
that date every day, so a "Safe" item turns "Moderate" and then "Priority" as
time passes without anyone editing it.

Where the shelf-life numbers come from, in order:
  1. data/shelf_life.csv if it exists (see README for the columns)
  2. the small built-in table below
  3. a default by storage place
The built-in numbers are rough, conservative rules of thumb for the common
foods the detector knows, not an authoritative source. Drop your own CSV in
data/ and it takes over automatically.
"""

import csv
import os
import re
from datetime import date, timedelta

from core.matching import norm

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_PATH = os.path.join(DATA_DIR, "shelf_life.csv")

STORAGES = ["Fridge", "Pantry", "Freezer"]
RIPENESS_LEVELS = ["Priority", "Moderate", "Safe"]
RIPENESS_ORDER = {"Priority": 0, "Moderate": 1, "Safe": 2}

DEFAULT_DAYS = {"Fridge": 7, "Pantry": 30, "Freezer": 120}

# name: (fridge days, pantry days, freezer days)
BUILTIN = {
    # fruit
    "apple": (28, 7, 240), "banana": (7, 5, 90), "orange": (21, 7, 120),
    "lemon": (28, 10, 120), "lime": (28, 10, 120), "grape": (7, 2, 270),
    "strawberry": (5, 1, 270), "blueberry": (10, 2, 270),
    "raspberry": (3, 1, 270), "avocado": (5, 3, 120), "pear": (7, 4, 240),
    "peach": (5, 3, 240), "mango": (5, 3, 240), "pineapple": (5, 3, 240),
    "watermelon": (5, 3, 180),
    # vegetables
    "tomato": (7, 5, 60), "cucumber": (7, 3, 30), "lettuce": (7, 1, 30),
    "spinach": (5, 1, 270), "kale": (7, 2, 270), "broccoli": (7, 2, 270),
    "cauliflower": (7, 2, 270), "carrot": (28, 7, 270), "celery": (14, 2, 270),
    "potato": (28, 35, 270), "sweet potato": (21, 21, 270), "onion": (60, 30, 240),
    "garlic": (60, 60, 240), "bell pepper": (10, 3, 270), "pepper": (10, 3, 270),
    "mushroom": (5, 1, 270), "zucchini": (7, 3, 270), "cabbage": (21, 3, 270),
    "corn": (5, 1, 270), "pea": (5, 1, 365), "green bean": (7, 2, 270),
    "scallion": (7, 2, 90), "basil": (5, 1, 90),
    # dairy and eggs
    "milk": (7, 1, 90), "egg": (35, 2, 365), "cheese": (28, 1, 180),
    "yogurt": (14, 1, 60), "butter": (90, 2, 270), "cream": (7, 1, 90),
    # meat, fish, protein
    "chicken": (2, 1, 270), "ground beef": (2, 1, 120), "beef": (4, 1, 270),
    "steak": (4, 1, 270), "pork": (4, 1, 180), "bacon": (7, 1, 30),
    "sausage": (2, 1, 60), "turkey": (2, 1, 270), "ham": (5, 1, 60),
    "fish": (2, 1, 180), "salmon": (2, 1, 180), "shrimp": (2, 1, 180),
    "tofu": (7, 1, 150),
    # bread and dry goods
    "bread": (7, 5, 90), "bagel": (7, 5, 90), "tortilla": (21, 7, 180),
    "rice": (365, 365, 365), "pasta": (365, 365, 365), "oat": (365, 365, 365),
    "flour": (365, 180, 365), "cereal": (180, 180, 180),
    "bean": (730, 730, 730), "lentil": (730, 730, 730),
    "peanut butter": (180, 90, 365), "jam": (180, 30, 365),
    "honey": (730, 730, 730), "sugar": (730, 730, 730), "juice": (7, 1, 270),
    "leftover": (4, 1, 90),
}

_UNIT_DAYS = (("year", 365), ("month", 30), ("week", 7), ("day", 1))
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def parse_days(text):
    """'5', '3-5 days', '2 weeks', '1 month' -> days (lower end of a range)."""
    s = str(text if text is not None else "").strip().lower()
    numbers = [float(n) for n in _NUMBER.findall(s)]
    if not numbers:
        return None
    per = 1
    for word, days in _UNIT_DAYS:
        if word in s:
            per = days
            break
    return max(1, round(min(numbers) * per))


def _load_csv(path):
    """Flexible loader: finds a name column and fridge/pantry/freezer or one
    generic days column by looking at the header text."""
    table = {}
    with open(path, newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if not headers:
            return table
        low = {h: h.lower() for h in headers}
        name_col = next((h for h in headers
                         if any(k in low[h] for k in ("food", "item", "name", "product"))),
                        headers[0])
        others = [h for h in headers if h != name_col]

        def pick(keys):
            return next((h for h in others if any(k in low[h] for k in keys)), None)

        cols = {
            "Fridge": pick(("fridge", "refriger")),
            "Pantry": pick(("pantry", "room", "counter")),
            "Freezer": pick(("freez",)),
        }
        taken = {c for c in cols.values() if c}
        generic = next((h for h in others if h not in taken
                        and any(k in low[h] for k in ("day", "life", "shelf", "expir"))), None)
        for row in reader:
            key = norm(row.get(name_col, ""))
            if not key:
                continue
            entry = {}
            for storage, col in cols.items():
                days = parse_days(row.get(col)) if col else None
                if days is None and generic:
                    days = parse_days(row.get(generic)) if storage != "Freezer" else None
                if days is not None:
                    entry[storage] = days
            if entry:
                table[key] = entry
    return table


def _builtin_table():
    return {norm(name): dict(zip(STORAGES, days)) for name, days in BUILTIN.items()}


_cache = {"table": None, "source": None, "mtime": None}


def _table():
    mtime = os.path.getmtime(CSV_PATH) if os.path.isfile(CSV_PATH) else None
    if _cache["table"] is None or _cache["mtime"] != mtime:
        table, source = None, "built-in table"
        if mtime is not None:
            try:
                loaded = _load_csv(CSV_PATH)
                if loaded:
                    table, source = loaded, f"data/shelf_life.csv ({len(loaded)} foods)"
            except (OSError, csv.Error, UnicodeDecodeError) as exc:
                print(f"Could not read {CSV_PATH}: {exc}")
        if table is None:
            table = _builtin_table()
        _cache.update(table=table, source=source, mtime=mtime)
    return _cache["table"]


def source():
    _table()
    return _cache["source"]


def _lookup(name):
    table = _table()
    key = norm(name)
    if key in table:
        return table[key]
    words = key.split()
    best = None
    for candidate, entry in table.items():
        cw = candidate.split()
        n = len(cw)
        inside = any(words[i:i + n] == cw for i in range(len(words) - n + 1))
        if inside and (best is None or n > best[0]):
            best = (n, entry)
    return best[1] if best else None


def shelf_days(name, storage="Fridge"):
    """Days a food keeps in the given place, from the best source available."""
    entry = _lookup(name) or {}
    if storage in entry:
        return entry[storage]
    # No number for this storage place: use the table's other places as a hint
    # before falling back to a flat default.
    if entry and storage != "Freezer":
        return min(entry.values())
    return DEFAULT_DAYS.get(storage, 7)


def ripeness_from_days(days_left):
    if days_left <= 2:
        return "Priority"
    if days_left <= 5:
        return "Moderate"
    return "Safe"


def ripeness_for(expires_on, today=None):
    today = today or date.today()
    return ripeness_from_days((expires_on - today).days)


def default_ripeness(name, storage="Fridge"):
    """First guess for a freshly scanned item (its age is unknown, so assume
    it is new): short-lived foods start higher up the urgency list."""
    days = shelf_days(name, storage)
    if days <= 3:
        return "Priority"
    if days <= 7:
        return "Moderate"
    return "Safe"


def expiry_for_ripeness(ripeness, name, storage="Fridge", today=None):
    """Use-by date implied by the ripeness the person picked."""
    today = today or date.today()
    shelf = shelf_days(name, storage)
    if ripeness == "Priority":
        days = min(2, shelf)
    elif ripeness == "Moderate":
        days = 4 if shelf <= 2 else max(3, min(5, shelf))
    else:
        days = max(shelf, 6)
    return today + timedelta(days=days)


def use_by_label(expires_on, today=None):
    today = today or date.today()
    delta = (expires_on - today).days
    if delta < 0:
        return "Past use-by"
    if delta == 0:
        return "Today"
    if delta == 1:
        return "Tomorrow"
    if delta <= 13:
        return f"In {delta} days"
    pattern = "%b %d" if expires_on.year == today.year else "%b %d, %Y"
    return expires_on.strftime(pattern).replace(" 0", " ")
