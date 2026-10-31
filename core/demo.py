"""Sample data, used automatically when a key or the trained model is missing.

Nothing here is real nutrition data for a real product: the recipe numbers
are plausible per-serving figures so the screens have something to show.
Recipe ids are negative so they can never collide with Spoonacular's.
"""
from core.matching import is_staple, names_match, norm, split_used_missing


def _ing(name, amount, unit=""):
    return {"name": name, "amount": amount, "unit": unit}


def _nut(calories, fat, carbs, sugar, cholesterol, sodium, protein, fiber):
    return {"calories": calories, "fat": fat, "carbs": carbs, "sugar": sugar,
            "cholesterol": cholesterol, "sodium": sodium, "protein": protein, "fiber": fiber}


RECIPES = [
    {"id": -1, "title": "Spinach and Cheese Omelet", "emoji": "🍳", "bg": "#F4E6A8",
     "minutes": 15, "servings": 2, "price_per_serving": 1.90,
     "ingredients": [_ing("eggs", 4), _ing("spinach", 2, "cups"), _ing("cheese", 0.25, "cups"),
                     _ing("butter", 1, "tbsp"), _ing("salt", 0.25, "tsp")],
     "steps": ["Whisk the eggs with a pinch of salt.",
               "Melt the butter in a pan over medium heat and wilt the spinach for one minute.",
               "Pour in the eggs and cook until the edges set.",
               "Add the cheese, fold the omelet in half and serve."],
     "nutrition": _nut(390, 29, 3, 1, 530, 520, 26, 1)},
    {"id": -2, "title": "Mushroom and Spinach Stir-Fry", "emoji": "🍄", "bg": "#E3D3BD",
     "minutes": 20, "servings": 2, "price_per_serving": 2.60,
     "ingredients": [_ing("mushrooms", 8, "oz"), _ing("spinach", 3, "cups"), _ing("rice", 1, "cups"),
                     _ing("soy sauce", 2, "tbsp"), _ing("garlic", 2), _ing("olive oil", 1, "tbsp")],
     "steps": ["Cook the rice according to the package.",
               "Sear the sliced mushrooms in hot oil until golden.",
               "Add garlic and spinach, then the soy sauce, and toss until wilted.",
               "Serve over the rice."],
     "nutrition": _nut(410, 9, 68, 4, 0, 780, 11, 4)},
    {"id": -3, "title": "Banana Oat Pancakes", "emoji": "🥞", "bg": "#F6DDA3",
     "minutes": 20, "servings": 2, "price_per_serving": 1.40,
     "ingredients": [_ing("bananas", 2), _ing("oats", 1, "cups"), _ing("eggs", 2),
                     _ing("milk", 0.5, "cups"), _ing("cinnamon", 1, "tsp")],
     "steps": ["Blend everything until smooth.",
               "Cook small rounds in a lightly oiled pan, about two minutes a side.",
               "Serve with sliced banana."],
     "nutrition": _nut(380, 9, 61, 18, 190, 120, 14, 7)},
    {"id": -4, "title": "Cheesy Egg Fried Rice", "emoji": "🍚", "bg": "#E9E2C3",
     "minutes": 15, "servings": 2, "price_per_serving": 1.70,
     "ingredients": [_ing("rice", 2, "cups"), _ing("eggs", 2), _ing("cheese", 0.5, "cups"),
                     _ing("scallions", 3), _ing("soy sauce", 1, "tbsp"), _ing("peas", 0.5, "cups")],
     "steps": ["Scramble the eggs in a hot pan and set aside.",
               "Fry the cooked rice and peas for three minutes.",
               "Stir in the eggs, soy sauce and scallions, then top with cheese."],
     "nutrition": _nut(540, 20, 61, 3, 260, 480, 22, 3)},
    {"id": -5, "title": "Apple Cinnamon Yogurt Bowl", "emoji": "🍎", "bg": "#F2C9C4",
     "minutes": 5, "servings": 1, "price_per_serving": 1.60,
     "ingredients": [_ing("apples", 2), _ing("yogurt", 1, "cups"), _ing("honey", 1, "tbsp"),
                     _ing("cinnamon", 0.5, "tsp"), _ing("oats", 0.25, "cups")],
     "steps": ["Dice the apples.", "Spoon yogurt into a bowl and top with apple, oats and cinnamon.",
               "Drizzle with honey."],
     "nutrition": _nut(420, 6, 78, 46, 20, 110, 17, 8)},
    {"id": -6, "title": "Chicken and Vegetable Skillet", "emoji": "🍗", "bg": "#F0D9B5",
     "minutes": 30, "servings": 4, "price_per_serving": 3.10,
     "ingredients": [_ing("chicken", 1, "lbs"), _ing("broccoli", 2, "cups"), _ing("carrots", 2),
                     _ing("onion", 1), _ing("garlic", 2), _ing("olive oil", 1, "tbsp")],
     "steps": ["Brown the chicken pieces in oil.", "Add onion, carrots and garlic and cook for five minutes.",
               "Add broccoli and a splash of water, cover and steam until tender."],
     "nutrition": _nut(330, 12, 14, 5, 95, 410, 40, 4)},
    {"id": -7, "title": "Tomato Basil Pasta", "emoji": "🍝", "bg": "#F3C7A6",
     "minutes": 25, "servings": 4, "price_per_serving": 1.80,
     "ingredients": [_ing("pasta", 8, "oz"), _ing("tomatoes", 4), _ing("garlic", 3),
                     _ing("basil", 0.25, "cups"), _ing("olive oil", 2, "tbsp"), _ing("parmesan", 0.25, "cups")],
     "steps": ["Boil the pasta.", "Soften garlic in oil, add chopped tomatoes and simmer ten minutes.",
               "Toss with the pasta, basil and parmesan."],
     "nutrition": _nut(430, 12, 66, 7, 8, 260, 14, 5)},
    {"id": -8, "title": "Veggie Scramble Wrap", "emoji": "🌯", "bg": "#DCE8C2",
     "minutes": 15, "servings": 2, "price_per_serving": 2.10,
     "ingredients": [_ing("eggs", 3), _ing("tortillas", 2), _ing("bell pepper", 1),
                     _ing("spinach", 1, "cups"), _ing("cheese", 0.25, "cups"), _ing("onion", 0.5)],
     "steps": ["Saute the pepper and onion.", "Add spinach and the beaten eggs and scramble.",
               "Fill the tortillas, sprinkle with cheese and roll up."],
     "nutrition": _nut(460, 21, 40, 5, 280, 640, 24, 6)},
    {"id": -9, "title": "Banana Milk Smoothie", "emoji": "🥛", "bg": "#EFE6C4",
     "minutes": 5, "servings": 2, "price_per_serving": 1.10,
     "ingredients": [_ing("bananas", 2), _ing("milk", 1, "cups"), _ing("yogurt", 0.5, "cups"),
                     _ing("honey", 1, "tsp")],
     "steps": ["Blend everything with a few ice cubes until smooth."],
     "nutrition": _nut(260, 4, 48, 33, 15, 90, 10, 3)},
    {"id": -10, "title": "Potato and Onion Frittata", "emoji": "🥔", "bg": "#EAD8B0",
     "minutes": 35, "servings": 4, "price_per_serving": 1.50,
     "ingredients": [_ing("potatoes", 2), _ing("eggs", 6), _ing("onion", 1),
                     _ing("cheese", 0.5, "cups"), _ing("olive oil", 1, "tbsp")],
     "steps": ["Slice and fry the potatoes and onion until soft.", "Pour over the beaten eggs and cheese.",
               "Cook gently, then finish under the broiler until set."],
     "nutrition": _nut(350, 20, 22, 2, 280, 250, 18, 3)},
]

SAMPLE_DETECTIONS = [("Apple", 3), ("Banana", 3), ("Milk", 1), ("Spinach", 1), ("Eggs", 6)]

# name, amount, unit, storage, days until use-by
SAMPLE_PANTRY = [
    ("Spinach", 1, "Piece", "Fridge", 1),
    ("Mushrooms", 8, "oz", "Fridge", 2),
    ("Bananas", 3, "Piece", "Pantry", 4),
    ("Milk", 1, "Piece", "Fridge", 4),
    ("Eggs", 8, "Piece", "Fridge", 20),
    ("Cheese", 1, "Piece", "Fridge", 10),
    ("Apples", 4, "Piece", "Fridge", 18),
    ("Tomatoes", 3, "Piece", "Fridge", 6),
    ("Rice", 2, "cups", "Pantry", 300),
    ("Onion", 2, "Piece", "Pantry", 40),
]


def get_recipe(recipe_id):
    return next((r for r in RECIPES if r["id"] == recipe_id), None)


def search(tags):
    """Sample recipes that use at least one of the tags, best match first."""
    results = []
    for recipe in RECIPES:
        names = [i["name"] for i in recipe["ingredients"]]
        used, missing = split_used_missing(names, tags)
        if used:
            results.append({
                "id": recipe["id"], "title": recipe["title"], "image": None,
                "emoji": recipe["emoji"], "bg": recipe["bg"],
                "used_names": used, "missing_names": missing,
            })
    results.sort(key=lambda r: (-len(r["used_names"]), len(r["missing_names"]), r["title"]))
    return results
