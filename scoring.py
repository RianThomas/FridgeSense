import nutrition.nutrients as n
import recipe.recipes as r

def _per_meal(targets):
    return [max(t / 3, 1e-6) for t in targets]


def meal_score(nutrient_totals, targets):
    tar_cal, tar_protein, tar_fiber, tar_sugar, tar_sodium, tar_chol = _per_meal(targets)

    meal_cal = nutrient_totals["calories"]
    meal_protein = nutrient_totals["protein"]
    meal_fiber = nutrient_totals["fiber"]
    meal_sugar = nutrient_totals["sugar"]
    meal_sodium = nutrient_totals["sodium"]
    meal_chol = nutrient_totals["cholesterol"]

    score_raw = 65.0

    reward_protein = 20.0 * min(2.0, meal_protein / tar_protein)
    reward_fiber = 15.0 * min(2.0, meal_fiber / tar_fiber)

    penalty_sugar = 15.0 * (meal_sugar / tar_sugar)
    penalty_sodium = 12.0 * (meal_sodium / tar_sodium)
    penalty_cholesterol = 8.0 * (meal_chol / tar_chol)

    calorie_ratio = meal_cal / tar_cal
    if calorie_ratio > 1.25:          # Overeating
        penalty_calories = min(22.0, (calorie_ratio - 1.25) * 40.0)
    elif calorie_ratio < 0.55:        # Undereating
        penalty_calories = min(15.0, (0.55 - calorie_ratio) * 30.0)
    else:
        penalty_calories = 0.0

    score_final_raw = (score_raw + reward_protein + reward_fiber - penalty_sugar - penalty_sodium - penalty_cholesterol - penalty_calories)

    return max(0, min(100, round(score_final_raw)))


def _rate_high_good(value, target):
    ratio = value / target
    if ratio >= 1.0:
        return "Excellent"
    if ratio >= 0.7:
        return "Good"
    if ratio >= 0.4:
        return "Moderate"
    return "Needs work"


def _rate_low_good(value, target):
    ratio = value / target
    if ratio <= 0.7:
        return "Excellent"
    if ratio <= 1.0:
        return "Good"
    if ratio <= 1.3:
        return "Moderate"
    return "Needs work"


def score_breakdown(nutrient_totals, targets):
    tar_cal, tar_protein, tar_fiber, tar_sugar, tar_sodium, _ = _per_meal(targets)
    return {
        "Protein": _rate_high_good(nutrient_totals["protein"], tar_protein),
        "Fiber": _rate_high_good(nutrient_totals["fiber"], tar_fiber),
        "Calories": _rate_low_good(nutrient_totals["calories"], tar_cal),
        "Sugar": _rate_low_good(nutrient_totals["sugar"], tar_sugar),
        "Sodium": _rate_low_good(nutrient_totals["sodium"], tar_sodium),
    }
