"""SQLite storage: users, profiles, pantry, saved recipes and cooked meals.

One small file (data/fridgesense.db, or the path in FRIDGESENSE_DB). Every
function opens its own short-lived connection, which is the safe pattern
with Streamlit because each browser session runs in its own thread.
Every query that touches user data filters by user_id.
"""
import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime

from core.matching import norm
from core.units import normalize_unit

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "fridgesense.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER NOT NULL,
    height_in REAL NOT NULL,
    weight_lb REAL NOT NULL,
    sex TEXT NOT NULL,
    activity TEXT NOT NULL,
    goal TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pantry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    amount REAL NOT NULL,
    unit TEXT NOT NULL,
    storage TEXT NOT NULL,
    date_added TEXT NOT NULL,
    expires_on TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pantry_user ON pantry(user_id);
CREATE TABLE IF NOT EXISTS saved_recipes (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipe_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    image TEXT,
    PRIMARY KEY (user_id, recipe_id)
);
CREATE TABLE IF NOT EXISTS meals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipe_id INTEGER,
    title TEXT NOT NULL,
    image TEXT,
    cooked_on TEXT NOT NULL,
    cooked_at TEXT NOT NULL,
    score INTEGER NOT NULL,
    nutrition TEXT NOT NULL,
    ingredients TEXT NOT NULL,
    ingredients_saved INTEGER NOT NULL,
    food_saved_lbs REAL NOT NULL,
    money_saved REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_meals_user ON meals(user_id, cooked_on);
"""

PANTRY_FIELDS = {"name", "amount", "unit", "storage", "expires_on"}


def db_path():
    return os.environ.get("FRIDGESENSE_DB") or DEFAULT_PATH


@contextmanager
def connect():
    conn = sqlite3.connect(db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    folder = os.path.dirname(db_path())
    if folder:
        os.makedirs(folder, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


# ---- users ----------------------------------------------------------------

def create_user(username, password_hash, salt):
    """New user dict, or None if the username is taken."""
    try:
        with connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, salt, created_at) VALUES (?,?,?,?)",
                (username, password_hash, salt, datetime.now().isoformat(timespec="seconds")))
            return {"id": cur.lastrowid, "username": username}
    except sqlite3.IntegrityError:
        return None


def get_user(username):
    with connect() as conn:
        return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


# ---- profile --------------------------------------------------------------

def get_profile(user_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def save_profile(user_id, age, height_in, weight_lb, sex, activity, goal):
    with connect() as conn:
        conn.execute(
            """INSERT INTO profiles (user_id, age, height_in, weight_lb, sex, activity, goal)
               VALUES (?,?,?,?,?,?,?)
               ON CONFLICT(user_id) DO UPDATE SET age=excluded.age, height_in=excluded.height_in,
               weight_lb=excluded.weight_lb, sex=excluded.sex, activity=excluded.activity,
               goal=excluded.goal""",
            (user_id, age, height_in, weight_lb, sex, activity, goal))


# ---- pantry ---------------------------------------------------------------

def _pantry_row(row):
    item = dict(row)
    item["date_added"] = date.fromisoformat(item["date_added"])
    item["expires_on"] = date.fromisoformat(item["expires_on"])
    return item


def list_pantry(user_id):
    with connect() as conn:
        rows = conn.execute("SELECT * FROM pantry WHERE user_id = ? ORDER BY id",
                            (user_id,)).fetchall()
    return [_pantry_row(r) for r in rows]


def add_pantry_item(user_id, name, amount, unit, storage, expires_on, date_added=None):
    """Adds an item. If the same food is already stored in the same place and
    unit, the amounts are added and the earlier use-by date is kept."""
    name = name.strip()
    date_added = date_added or date.today()
    with connect() as conn:
        rows = conn.execute("SELECT * FROM pantry WHERE user_id = ? AND storage = ?",
                            (user_id, storage)).fetchall()
        for row in rows:
            if (norm(row["name"]) == norm(name)
                    and normalize_unit(row["unit"]) == normalize_unit(unit)):
                earlier = min(date.fromisoformat(row["expires_on"]), expires_on)
                conn.execute("UPDATE pantry SET amount = ?, expires_on = ? WHERE id = ?",
                             (row["amount"] + amount, earlier.isoformat(), row["id"]))
                return row["id"]
        cur = conn.execute(
            """INSERT INTO pantry (user_id, name, amount, unit, storage, date_added, expires_on)
               VALUES (?,?,?,?,?,?,?)""",
            (user_id, name, amount, unit, storage, date_added.isoformat(), expires_on.isoformat()))
        return cur.lastrowid


def update_pantry_item(user_id, item_id, **fields):
    fields = {k: v for k, v in fields.items() if k in PANTRY_FIELDS}
    if not fields:
        return
    if "expires_on" in fields:
        fields["expires_on"] = fields["expires_on"].isoformat()
    sets = ", ".join(f"{k} = ?" for k in fields)
    with connect() as conn:
        conn.execute(f"UPDATE pantry SET {sets} WHERE id = ? AND user_id = ?",
                     (*fields.values(), item_id, user_id))


def delete_pantry_item(user_id, item_id):
    with connect() as conn:
        conn.execute("DELETE FROM pantry WHERE id = ? AND user_id = ?", (item_id, user_id))


# ---- saved recipes --------------------------------------------------------

def save_recipe(user_id, recipe_id, title, image):
    with connect() as conn:
        conn.execute("INSERT OR REPLACE INTO saved_recipes (user_id, recipe_id, title, image) "
                     "VALUES (?,?,?,?)", (user_id, recipe_id, title, image))


def unsave_recipe(user_id, recipe_id):
    with connect() as conn:
        conn.execute("DELETE FROM saved_recipes WHERE user_id = ? AND recipe_id = ?",
                     (user_id, recipe_id))


def list_saved(user_id):
    with connect() as conn:
        rows = conn.execute("SELECT recipe_id AS id, title, image FROM saved_recipes "
                            "WHERE user_id = ? ORDER BY rowid DESC", (user_id,)).fetchall()
    return [dict(r) for r in rows]


# ---- meals ----------------------------------------------------------------

def add_meal(user_id, recipe_id, title, image, score, nutrition, ingredients,
             ingredients_saved, food_saved_lbs, money_saved):
    now = datetime.now()
    with connect() as conn:
        conn.execute(
            """INSERT INTO meals (user_id, recipe_id, title, image, cooked_on, cooked_at, score,
               nutrition, ingredients, ingredients_saved, food_saved_lbs, money_saved)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, recipe_id, title, image, now.date().isoformat(),
             now.isoformat(timespec="seconds"), int(score), json.dumps(nutrition),
             json.dumps(ingredients), int(ingredients_saved), float(food_saved_lbs),
             float(money_saved)))


def list_meals(user_id):
    """Newest first."""
    with connect() as conn:
        rows = conn.execute("SELECT * FROM meals WHERE user_id = ? ORDER BY id DESC",
                            (user_id,)).fetchall()
    meals = []
    for row in rows:
        meal = dict(row)
        meal["cooked_on"] = date.fromisoformat(meal["cooked_on"])
        meal["nutrition"] = json.loads(meal["nutrition"])
        meal["ingredients"] = json.loads(meal["ingredients"])
        meals.append(meal)
    return meals
