import recipe.recipes as r

MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "high": 1.725
}

def get_bmr(height, weight, age, sex):
    base = (10 * weight) + (6.25 * height) - (5 * age)

    if sex == "Male":
        return base + 5
    if sex == "Female":
        return base - 161

    return (2 * base + 5 - 161)/2

def get_daily_val(height, weight, age, sex, activity, goal):
    daily_calories = 0
    bmr = get_bmr(height, weight, age, sex)
    bmr *= MULTIPLIERS.get(activity, 1.2)
    
    if goal == "lose weight":
        daily_calories = max(1200, bmr - 500)
    elif goal == "gain muscle":
        daily_calories += 300
    else:
        daily_calories = bmr
    
    daily_protein = max(45, weight * 1.6)
    daily_fiber = max(18, 14 * (bmr / 1000))
    daily_sugar = bmr * 0.1 / 4

    if activity == "sedentary":
        daily_sodium = 2300
    else:
        daily_sodium = 2400
    
    daily_cholestrol = 300

    return [daily_calories, daily_protein, daily_fiber, daily_sugar, daily_sodium, daily_cholestrol]

def get_daily_targets(height, weight, age, sex, activity, goal):
    cal, protein, fiber, sugar, sodium, chol = get_daily_val(height, weight, age, sex, activity, goal)
    return {
        "calories": cal,
        "protein": protein,
        "fiber": fiber,
        "sugar": sugar,
        "sodium": sodium,
        "cholesterol": chol,
        "fat": 0.30 * cal / 9,
    }

    
nutrients = {}

def nutrition(id):
    for item in id:
        nutrition = r.search_nutrition(item)
        # Calories, Fat, Carbs, Sugar, Cholesterol, Sodium, Protein, Fiber
        nutrients[id] = ([nutrition["nutrients"][0]["amount"], nutrition["nutrients"][1]["amount"], nutrition["nutrients"][3]["amount"], nutrition["nutrients"][5]["amount"], nutrition["nutrients"][6]["amount"], nutrition["nutrients"][7]["amount"], nutrition["nutrients"][10]["amount"],nutrition["nutrients"][15]["amount"]])
    
def calories(id):
    return nutrients[id][0]

def fat(id):
    return nutrients[id][1]

def carbs(id):
    return nutrients[id][2]

def sugar(id):
    return nutrients[id][3]

def cholestrol(id):
    return nutrients[id][4]

def sodium(id):
    return nutrients[id][5]

def protein(id):
    return nutrients[id][6]

def fiber(id):
    return nutrients[id][7]
