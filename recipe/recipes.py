import requests
from dotenv import load_dotenv
import os

load_dotenv()

s_api = os.getenv("SPOON_API")
BASE = "https://api.spoonacular.com"
TIMEOUT = 15

titles = []
id = []
images = []
num_ing = []
used_ing = []
unused_ing = []
missing_ing = []
amounts = {}
names = []
instructions = []
steps = []
equipment = []
data = {}

def has_key():
    return bool(s_api)

def _get(path, params):
    params = dict(params, apiKey=s_api)
    response = requests.get(f"{BASE}{path}", params=params, timeout=TIMEOUT)
    if response.status_code == 200:
        return response.json()
    print(f"Error {response.status_code}: {response.text}")
    return None


def search_ingredients(ingredients, number=5):
    return _get("/recipes/findByIngredients", {"ingredients": ",".join(ingredients), "number": number, "ranking": 1})


def get_recipe_info(recipes):
    global titles, id, images, num_ing, used_ing, unused_ing, missing_ing
    titles = [recipe["title"] for recipe in recipes]
    id = [recipe["id"] for recipe in recipes]
    images = [recipe["image"] for recipe in recipes]
    num_ing = [[recipe["usedIngredientCount"] for recipe in recipes], [recipe["missedIngredientCount"] for recipe in recipes]]
    used_ing = [recipe["usedIngredients"] for recipe in recipes]
    unused_ing = [recipe["unusedIngredients"] for recipe in recipes]
    missing_ing = [recipe["missedIngredients"] for recipe in recipes]
    return titles, id, images, num_ing, used_ing, unused_ing, missing_ing


def get_titles():
    return titles

def get_id():
    return id

def get_image():
    return images

def get_num_ing():
    return num_ing

def get_used_ing():
    return used_ing

def get_unused_ing():
    return unused_ing

def get_missing_ing():
    return missing_ing

def get_ingred_names():
    for i in len(used_ing):
        name = []
        r = used_ing[i]
        for ing in r:
            name.append[ing["name"]]
        names.append(name)
    
def get_ingred_amounts():
    for i in len(used_ing):
        r = used_ing[i]
        ids = id[i]
        amount = {}
        for ing in r:
            amount[ing["name"]] = (ing["amount"], ing["unit"])
        amounts[ids] = amount

def get_ingred_weights(ingred_name, orig_amount, orig_unit):
    return _get("/recipes/convert", {"ingredientName": ingred_name, "sourceAmount": orig_amount, "sourceUnit": orig_unit, "targetUnit": "grams"})

def get_instructions(recipe_id):
    return _get(f"/recipes/{recipe_id}/analyzedInstructions", {"stepBreakdown": True})

def parse_instructions(recipe_id):
    global steps, equipment
    for block in get_instructions(recipe_id) or []:
        for step in block["steps"]:
            for equip in step.get("equipment", []):
                equipment.append(equip["name"])
            steps.append(step["step"])
    return steps, equipment

def get_equipment():
    return equipment

def get_steps():
    return steps

def search_nutrition(recipe_id):
    return _get(f"/recipes/{recipe_id}/nutritionWidget.json", {})

def get_other_data(recipe_id):
    return _get(f"/recipes/{recipe_id}/information", {"includeNutrition": False, "addWinePairing": False, "addTasteData": False})

def get_data(recipe_id):
    global data
    data = get_other_data(recipe_id) or {}
    return data

def get_cooking_time():
    return data.get("cookingMinutes")


def get_price_per_serving():
    return data.get("pricePerServing", 0) / 100


def get_serving_size():
    return data.get("servings")

def _to_float(value):
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    digits = "".join(ch for ch in str(value) if ch.isdigit() or ch in ".-")
    try:
        return float(digits)
    except ValueError:
        return 0.0

def find_recipes(ingredients, number=8):
    finding = search_ingredients(ingredients, number=number)
    if finding is None:
        raise RuntimeError("Spoonacular request failed")
    recipes = []
    for item in finding:
        recipes.append({
            "id": item["id"],
            "title": item["title"],
            "image": item.get("image"),
            "used_names": [i["name"] for i in item.get("usedIngredients", [])],
            "missing_names": [i["name"] for i in item.get("missedIngredients", [])],
        })
    return recipes

NUTRIENT_FIELDS = [
    ("calories", "Calories", 0),
    ("fat", "Fat", 1),
    ("carbs", "Carbohydrates", 3),
    ("sugar", "Sugar", 5),
    ("cholesterol", "Cholesterol", 6),
    ("sodium", "Sodium", 7),
    ("protein", "Protein", 10),
    ("fiber", "Fiber", 15),
]

def get_nutrition_for_recipe(recipe_id):
    resp = search_nutrition(recipe_id)
    if not resp:
        return None
    vals = resp.get("nutrients", [])
    by_name = {v.get("name"): v for v in vals if isinstance(v, dict)}
    nuts = {}
    for key, name, idx in NUTRIENT_FIELDS:
        if name in by_name:
            nuts[key] = _to_float(by_name[name].get("amount"))
        elif idx < len(vals):
            nuts[key] = _to_float(vals[idx].get("amount"))
        else:
            nuts[key] = 0.0
    return nuts

def get_recipe_details(recipe_id):
    info = get_other_data(recipe_id)
    if not info:
        return None
    steps_out = []
    for block in info.get("analyzedInstructions") or []:
        for step in block.get("steps", []):
            steps_out.append(step["step"])
    minutes = info.get("cookingMinutes") or info.get("readyInMinutes")
    return {
        "id": info.get("id", recipe_id),
        "title": info.get("title"),
        "image": info.get("image"),
        "minutes": minutes if minutes and minutes > 0 else None,
        "servings": info.get("servings"),
        "price_per_serving": (info.get("pricePerServing") or 0) / 100,
        "ingredients": [
            {"name": i.get("name", ""), "amount": i.get("amount", 0),"unit": i.get("unit", "")} for i in info.get("extendedIngredients", [])
        ],
        "steps": steps_out,
        "source_url": info.get("sourceUrl"),
    }

