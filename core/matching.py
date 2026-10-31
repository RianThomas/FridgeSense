"""Ingredient-name matching between recipes and the pantry.

Recipes say "baby spinach leaves", the pantry says "Spinach". This does a
word-based comparison after a light singularisation. It is deliberately
simple and has known limits: it will not know that "scallions" and "green
onions" are the same thing, and it only blocks the most common false
friends (coconut milk vs milk, peanut butter vs butter) with a short list.
"""
import re

# Words that turn an ingredient into a different thing when added in front.
DISTINCT_MODIFIERS = {
    "coconut", "almond", "soy", "oat", "peanut", "cashew", "cream", "sweet",
    "butter", "buttermilk", "condensed", "evaporated", "ice", "sour",
}

# Things Spoonacular and the sample recipes treat as always-on-hand.
STAPLES = {"salt", "pepper", "black pepper", "water", "oil", "olive oil",
           "vegetable oil", "cooking spray", "ice"}


def _singular(word):
    if len(word) > 3 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("oes"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def norm(name):
    """Lower-case, drop brackets/punctuation, singularise each word."""
    text = re.sub(r"\(.*?\)", " ", str(name or "").lower())
    text = re.sub(r"[^a-z0-9\s-]", " ", text)
    return " ".join(_singular(w) for w in text.split())


def _contains_phrase(big, small):
    n = len(small)
    return n > 0 and any(big[i:i + n] == small for i in range(len(big) - n + 1))


def names_match(a, b):
    wa, wb = norm(a).split(), norm(b).split()
    if not wa or not wb:
        return False
    if wa == wb:
        return True
    for big, small in ((wa, wb), (wb, wa)):
        if _contains_phrase(big, small):
            extra = set(big) - set(small)
            if not (extra & DISTINCT_MODIFIERS):
                return True
    return False


def is_staple(name):
    return norm(name) in {norm(s) for s in STAPLES}


def split_used_missing(recipe_names, available_names, ignore_staples=True):
    """-> (used, missing) lists of the recipe's own ingredient names."""
    used, missing, seen = [], [], set()
    for name in recipe_names:
        key = norm(name)
        if not key or key in seen:
            continue
        seen.add(key)
        if any(names_match(name, have) for have in available_names):
            used.append(name)
        elif not (ignore_staples and is_staple(name)):
            missing.append(name)
    return used, missing


def find_pantry_item(ingredient_name, pantry_items):
    """Best pantry row for a recipe ingredient (exact words first)."""
    exact = [i for i in pantry_items if norm(i["name"]) == norm(ingredient_name)]
    if exact:
        return exact[0]
    for item in pantry_items:
        if names_match(ingredient_name, item["name"]):
            return item
    return None
