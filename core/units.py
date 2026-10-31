"""Unit handling for pantry amounts.

The pantry uses the units from the wireframe: Piece, lbs, oz, cups, tbsp,
tsp, g. Recipes use whatever Spoonacular sends ("tablespoons", "cloves",
"large", ""). Within weight or within volume we can convert exactly. A
weight cannot be converted to a volume without knowing the food's density,
so those cases use the documented fallbacks in compute_deduction().
"""

PANTRY_UNITS = ["Piece", "lbs", "oz", "cups", "tbsp", "tsp", "g"]

_ALIASES = {
    "cups": ("cup", "cups", "c"),
    "tbsp": ("tbsp", "tbsps", "tablespoon", "tablespoons", "tbs", "tbl"),
    "tsp": ("tsp", "tsps", "teaspoon", "teaspoons"),
    "ml": ("ml", "milliliter", "milliliters", "millilitre", "millilitres"),
    "l": ("l", "liter", "liters", "litre", "litres"),
    "oz": ("oz", "ounce", "ounces"),
    "lbs": ("lb", "lbs", "pound", "pounds"),
    "g": ("g", "gram", "grams", "gr"),
    "kg": ("kg", "kilogram", "kilograms"),
}
_LOOKUP = {alias: canon for canon, aliases in _ALIASES.items() for alias in aliases}

# Everything in a group is expressed in one base unit for conversion.
_VOLUME_IN_TSP = {"tsp": 1.0, "tbsp": 3.0, "cups": 48.0, "ml": 0.202884, "l": 202.884}
_WEIGHT_IN_G = {"g": 1.0, "oz": 28.3495, "lbs": 453.592, "kg": 1000.0}

# Fallback share of a pantry item assumed used when units can't be converted.
FALLBACK_FRACTION = 0.25


def normalize_unit(unit):
    """Canonical unit name; anything unrecognised counts as 'Piece'."""
    key = str(unit or "").strip().lower().rstrip(".")
    return _LOOKUP.get(key, "Piece")


def format_quantity(amount, unit):
    """Readable amount for display: '1 cup', '2 cups', '1 piece', '3 pieces', '8 oz'."""
    one = abs(float(amount) - 1) < 1e-9
    label = str(unit or "").strip()
    canon = normalize_unit(label)
    if canon == "Piece":
        label = "piece" if one else "pieces"
    elif one and canon in ("cups", "lbs"):
        label = {"cups": "cup", "lbs": "lb"}[canon]
    return f"{amount:g} {label}".strip()


def unit_group(unit):
    canon = normalize_unit(unit)
    if canon in _VOLUME_IN_TSP:
        return "volume"
    if canon in _WEIGHT_IN_G:
        return "weight"
    return "piece"


def convert(amount, from_unit, to_unit):
    """Convert within one group; raises ValueError across groups."""
    a, b = normalize_unit(from_unit), normalize_unit(to_unit)
    group = unit_group(a)
    if group != unit_group(b):
        raise ValueError(f"cannot convert {a} to {b}")
    if group == "piece":
        return float(amount)
    table = _VOLUME_IN_TSP if group == "volume" else _WEIGHT_IN_G
    return float(amount) * table[a] / table[b]


def compute_deduction(pantry_amount, pantry_unit, recipe_amount, recipe_unit):
    """How much of a pantry item a recipe uses, in the pantry's own unit.

    - same group (weight/weight, volume/volume): exact conversion
    - both counted (pieces): the recipe's count (at least 1)
    - pantry counted but recipe in weight/volume: 1 piece
    - pantry in weight/volume but recipe counted or other group: 25% of
      what's on hand (an assumption; flagged to the user after cooking)
    Never more than what's on hand.
    """
    pantry_amount = float(pantry_amount or 0)
    if pantry_amount <= 0:
        return 0.0
    try:
        r_amount = float(recipe_amount or 0)
    except (TypeError, ValueError):
        r_amount = 0.0

    p_group = unit_group(pantry_unit)
    r_group = unit_group(recipe_unit)

    if p_group == r_group and p_group != "piece" and r_amount > 0:
        used = convert(r_amount, recipe_unit, pantry_unit)
    elif p_group == "piece" and r_group == "piece":
        used = max(1.0, r_amount)
    elif p_group == "piece":
        used = 1.0
    else:
        used = FALLBACK_FRACTION * pantry_amount

    return round(min(pantry_amount, max(used, 0.0)), 2)
