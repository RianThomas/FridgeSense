"""One place that decides "live service or sample data?".

Each public function returns real results when its key/model is configured
and reachable, and sample data (with a note the UI shows) otherwise. A failed
live call never raises into a page. Live calls are cached with
st.cache_data so Streamlit's reruns don't spend Spoonacular or Gemini quota;
failures are raised inside the cached function so they are not cached.
"""
import importlib.util
import os
import tempfile
from collections import Counter

import streamlit as st

import ai
import model as model_backend
from core import demo
from recipe import recipes as recipe_api


# ---- what is configured ------------------------------------------------------

def live_recipes():
    return recipe_api.has_key()


def live_ai():
    return ai.has_key()


def live_detector():
    return (model_backend.weights_available()
            and importlib.util.find_spec("ultralytics") is not None)


def sample_parts():
    """Which features are running on sample data right now, in plain words."""
    parts = []
    if not live_recipes():
        parts.append("recipes")
    if not live_detector():
        parts.append("food detection")
    if not live_ai():
        parts.append("meal explanations")
    return parts


def sample_note():
    parts = sample_parts()
    if not parts:
        return None
    joined = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return f"Using sample data for {joined}."


# ---- recipe search -----------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def _search_live(tags, number):
    return recipe_api.find_recipes(list(tags), number=number)


def search_recipes(tags, priority_tags=()):
    """-> {"recipes": [...], "source": "live"|"sample"|"none", "note": str|None}"""
    tags = [t.strip() for t in tags if t and t.strip()]
    if not tags:
        return {"recipes": [], "source": "none", "note": None}
    if not live_recipes():
        return {"recipes": demo.search(tags), "source": "sample",
                "note": "Showing sample recipes. Add SPOON_API to your .env file to search Spoonacular."}
    try:
        found = list(_search_live(tuple(sorted(tags)), 12))
        urgent = [t for t in priority_tags if t in tags]
        if urgent and set(urgent) != set(tags):
            # A second, narrower search so recipes built around the urgent
            # foods aren't crowded out by better overall matches.
            seen = {r["id"] for r in found}
            found += [r for r in _search_live(tuple(sorted(urgent)), 6) if r["id"] not in seen]
        return {"recipes": found, "source": "live", "note": None}
    except Exception as exc:  # noqa: BLE001
        return {"recipes": demo.search(tags), "source": "sample",
                "note": f"Couldn't reach Spoonacular ({type(exc).__name__}). Showing sample recipes instead."}


# ---- recipe detail -----------------------------------------------------------

@st.cache_data(ttl=86400, show_spinner=False)
def _details_live(recipe_id):
    details = recipe_api.get_recipe_details(recipe_id)
    if details is None:
        raise RuntimeError("Spoonacular details request failed")
    return details


@st.cache_data(ttl=86400, show_spinner=False)
def _nutrition_live(recipe_id):
    nutrition = recipe_api.get_nutrition_for_recipe(recipe_id)
    if nutrition is None:
        raise RuntimeError("Spoonacular nutrition request failed")
    return nutrition


def get_detail(stub):
    """Full detail for one recipe. `nutrition` is None if it couldn't be loaded.
    -> dict with: id, title, image, emoji, bg, minutes, servings,
       price_per_serving, ingredients, steps, nutrition, source, note"""
    rid = stub["id"]
    if rid < 0:
        recipe = demo.get_recipe(rid)
        if recipe is not None:
            return {**recipe, "image": None, "source": "sample", "note": None}
    if not live_recipes():
        return {"id": rid, "title": stub["title"], "image": stub.get("image"), "emoji": "🍽️",
                "bg": "#E6EFE8", "minutes": None, "servings": None, "price_per_serving": 0.0,
                "ingredients": [], "steps": [], "nutrition": None, "source": "sample",
                "note": "Add SPOON_API to your .env file to load this recipe."}
    try:
        details = dict(_details_live(rid))
        details.update(emoji="🍽️", bg="#E6EFE8", source="live", note=None)
    except Exception as exc:  # noqa: BLE001
        return {"id": rid, "title": stub["title"], "image": stub.get("image"), "emoji": "🍽️",
                "bg": "#E6EFE8", "minutes": None, "servings": None, "price_per_serving": 0.0,
                "ingredients": [], "steps": [], "nutrition": None, "source": "live",
                "note": f"Couldn't load this recipe ({type(exc).__name__}). Try again in a moment."}
    try:
        details["nutrition"] = dict(_nutrition_live(rid))
    except Exception as exc:  # noqa: BLE001
        details["nutrition"] = None
        details["note"] = f"Couldn't load nutrition ({type(exc).__name__}). Try again in a moment."
    return details


# ---- score explanation -------------------------------------------------------

def plain_explanation(score, breakdown):
    """Deterministic fallback sentence built from the factor ratings."""
    strong = [k.lower() for k, v in breakdown.items() if v == "Excellent"]
    weak = [k.lower() for k, v in breakdown.items() if v in ("Needs work", "Moderate")]
    parts = [f"This meal scores {score} out of 100 against your daily targets."]
    if strong:
        parts.append(f"It does best on {_join(strong)}.")
    if weak:
        parts.append(f"{_join(weak).capitalize()} could be better.")
    return " ".join(parts)


def _join(words):
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


@st.cache_data(ttl=86400, show_spinner=False)
def _explain_live(title, nutrition_items, score, breakdown_items):
    return ai.get_score_explanation(title, dict(nutrition_items), score, dict(breakdown_items))


def explain_score(title, nutrition, score, breakdown):
    if not live_ai():
        return plain_explanation(score, breakdown)
    rounded = tuple(sorted((k, round(v)) for k, v in nutrition.items()))
    return _explain_live(title, rounded, score, tuple(sorted(breakdown.items())))


# ---- food detection ----------------------------------------------------------

@st.cache_resource(show_spinner="Loading the food detector...")
def _yolo():
    return model_backend.load_model()


def detect_foods(image_bytes, suffix=".jpg"):
    """-> {"foods": [(name, count), ...], "source": "live"|"sample", "note": str|None}"""
    if live_detector():
        path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix or ".jpg") as tmp:
                tmp.write(image_bytes)
                path = tmp.name
            results = model_backend.predict_image(_yolo(), path)
            _, foods = model_backend.ingredients_from_results(results)
            counts = Counter(f.strip().title() for f in foods)
            return {"foods": list(counts.items()), "source": "live", "note": None}
        except Exception as exc:  # noqa: BLE001
            return {"foods": list(demo.SAMPLE_DETECTIONS), "source": "sample",
                    "note": f"Detection failed ({type(exc).__name__}), so these are sample results."}
        finally:
            if path and os.path.exists(path):
                os.unlink(path)
    return {"foods": list(demo.SAMPLE_DETECTIONS), "source": "sample",
            "note": "These are sample results. Put your trained best.pt in the model folder "
                    "and the app will detect the foods in your photo instead."}
