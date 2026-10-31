"""Daily totals, lifetime impact numbers and the profile -> targets bridge."""
from datetime import date

from nutrition import nutrients as nutrients_api

LBS_PER_SAVED_INGREDIENT = 0.33
AT_RISK = {"Priority", "Moderate"}

NUTRIENT_KEYS = ["calories", "protein", "sugar", "sodium", "cholesterol", "fat", "fiber", "carbs"]

DEFAULT_PROFILE = {
    "age": 30, "height_in": 67.0, "weight_lb": 150.0,
    "sex": "Other", "activity": "moderate", "goal": "maintain",
}


def estimate_impact(used_ripeness, recipe_total_cost):
    if not used_ripeness:
        return 0, 0.0, 0.0
    saved = sum(1 for r in used_ripeness if r in AT_RISK)
    lbs = round(saved * LBS_PER_SAVED_INGREDIENT, 2)
    money = round((recipe_total_cost or 0.0) * saved / len(used_ripeness), 2)
    return saved, lbs, money


def profile_or_default(profile):
    return {**DEFAULT_PROFILE, **(profile or {})}


def targets_for(profile):
    p = profile_or_default(profile)
    return nutrients_api.get_daily_targets(
        height=p["height_in"] * 2.54,
        weight=p["weight_lb"] * 0.453592,
        age=p["age"], sex=p["sex"], activity=p["activity"], goal=p["goal"])


def targets_list(profile):
    t = targets_for(profile)
    return [t["calories"], t["protein"], t["fiber"], t["sugar"], t["sodium"], t["cholesterol"]]


def today_totals(meals, today=None):
    today = today or date.today()
    totals = {k: 0.0 for k in NUTRIENT_KEYS}
    for meal in meals:
        if meal["cooked_on"] == today:
            for key in NUTRIENT_KEYS:
                totals[key] += float(meal["nutrition"].get(key, 0) or 0)
    return totals


def lifetime(meals):
    count = len(meals)
    return {
        "meals": count,
        "ingredients_saved": sum(m["ingredients_saved"] for m in meals),
        "food_saved_lbs": round(sum(m["food_saved_lbs"] for m in meals), 1),
        "money_saved": round(sum(m["money_saved"] for m in meals), 2),
        "avg_score": round(sum(m["score"] for m in meals) / count) if count else 0,
    }
