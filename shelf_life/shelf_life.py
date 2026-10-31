import csv
from datetime import datetime, timedelta

shelf_life = {}

with open("shelf_life.csv", "r") as file:
    reader = csv.DictReader(file)

    for row in reader:
        food = row["food"].lower()

        shelf_life[food] = {
            "fridge": int(row["fridge_days"]) if row["fridge_days"] else None,
            "pantry": int(row["pantry_days"]) if row["pantry_days"] else None,
            "freezer": int(row["freezer_days"]) if row["freezer_days"] else None
        }


def get_shelf_life(food, storage):

    food = food.lower()
    storage = storage.lower()

    if food not in shelf_life:
        return None

    return shelf_life[food][storage]


def get_expiration(food, storage, date_added):

    days = get_shelf_life(food, storage)

    if days is None:
        return None

    expiration = date_added + timedelta(days=days)

    return expiration


def get_priority(food, storage, date_added, expiration_date=None):

    if expiration_date is None:
        expiration_date = get_expiration(food, storage, date_added)

    if expiration_date is None:
        return "Moderate"

    today = datetime.today().date()
    days_left = (expiration_date - today).days

    if days_left <= 2:
        return "Priority"

    elif days_left <= 7:
        return "Moderate"

    else:
        return "Safe"