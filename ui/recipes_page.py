"""Recipes: ingredient-tag search, card grid, saved recipes, recipe detail with
meal score, and the Cook This Meal flow."""
import streamlit as st

import scoring
from core import db, demo, matching, services, shelf_life, stats, units
from ui.common import chip, esc, goto, pantry_items, top_bar, unique_names, uid

URGENCY = shelf_life.RIPENESS_ORDER
NUTRITION_ROWS = [("Calories", "calories", "kcal"), ("Fat", "fat", "g"), ("Carbs", "carbs", "g"),
                  ("Protein", "protein", "g"), ("Fiber", "fiber", "g"), ("Sugar", "sugar", "g"),
                  ("Sodium", "sodium", "mg"), ("Cholesterol", "cholesterol", "mg")]


# ---- small helpers -----------------------------------------------------------

def _join(words):
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _unique(seq):
    seen, out = set(), []
    for s in seq:
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


def _used_pantry_items(stub, items):
    found = []
    for name in stub.get("used_names", []):
        item = matching.find_pantry_item(name, items)
        if item is not None and item["id"] not in {f["id"] for f in found}:
            found.append(item)
    return found


def _urgency_key(stub, items):
    used = _used_pantry_items(stub, items)
    levels = [URGENCY[i["ripeness"]] for i in used]
    return (min(levels) if levels else 3,
            -sum(1 for lv in levels if lv == 0),
            len(stub.get("missing_names", [])))


def _why(stub, items):
    used = _used_pantry_items(stub, items)
    urgent = _unique([i["name"].lower() for i in used if i["ripeness"] == "Priority"])
    soon = _unique([i["name"].lower() for i in used if i["ripeness"] == "Moderate"])
    if urgent:
        return f"Uses {_join(urgent)}, which should be used soon."
    if soon:
        return f"Uses {_join(soon)}, which needs using in the next few days."
    return None


def _decorate(stub):
    """Fill in the placeholder look for recipes without a photo."""
    sample = demo.get_recipe(stub["id"]) if stub["id"] < 0 else None
    return {"emoji": "🍽️", "bg": "#E6EFE8", **({"emoji": sample["emoji"], "bg": sample["bg"]} if sample else {}), **stub}


def _photo(stub, hero=False):
    if stub.get("image"):
        st.image(stub["image"], width="stretch")
    else:
        stub = _decorate(stub)
        st.markdown(f'<div class="fs-photo{" hero" if hero else ""}" style="background:{esc(stub["bg"])};">'
                    f'{esc(stub["emoji"])}</div>', unsafe_allow_html=True)


def _open(stub):
    keep = ("id", "title", "image", "emoji", "bg", "used_names", "missing_names")
    st.session_state["recipe_stub"] = {k: stub[k] for k in keep if k in stub}


def _back():
    st.session_state.pop("recipe_stub", None)


def _toggle_save(recipe_id, title, image):
    if recipe_id in {r["id"] for r in db.list_saved(uid())}:
        db.unsave_recipe(uid(), recipe_id)
    else:
        db.save_recipe(uid(), recipe_id, title, image)


def _heart(recipe_id, title, image, key, saved):
    st.button("♥" if saved else "♡", key=key, type="primary" if saved else "secondary",
              help="Remove from saved recipes" if saved else "Save this recipe",
              on_click=_toggle_save, args=(recipe_id, title, image))


# ---- list --------------------------------------------------------------------

def _card(stub, prefix, saved_ids, items, show_counts=True):
    with st.container(border=True):
        _photo(stub)
        st.markdown(f'<div class="fs-recipe-name">{esc(stub["title"])}</div>', unsafe_allow_html=True)
        used, missing = len(stub.get("used_names", [])), len(stub.get("missing_names", []))
        if show_counts and (used or missing):
            st.caption(f"Uses {used} from your pantry · Missing {missing}")
        why = _why(stub, items) if show_counts else None
        if show_counts:   # always drawn, so cards in one row line up
            st.markdown(f'<div class="fs-why">{esc(why or "")}</div>', unsafe_allow_html=True)
        open_col, heart_col = st.columns([4, 1])
        open_col.button("View recipe", key=f"rec_open_{prefix}_{stub['id']}", width="stretch",
                        on_click=_open, args=(stub,))
        with heart_col:
            _heart(stub["id"], stub["title"], stub.get("image"), f"rec_heart_{prefix}_{stub['id']}",
                   stub["id"] in saved_ids)


def _grid(stubs, prefix, saved_ids, items, show_counts=True, per_row=3):
    for start in range(0, len(stubs), per_row):
        cols = st.columns(per_row)
        for col, stub in zip(cols, stubs[start:start + per_row]):
            with col:
                _card(stub, prefix, saved_ids, items, show_counts)


def _list_view():
    top_bar()
    note = st.session_state.pop("recipe_note", None)
    if note:
        st.success(note, icon=":material/check_circle:")

    items = pantry_items()
    if "recipe_tags" not in st.session_state:
        ordered = sorted(items, key=lambda i: (URGENCY[i["ripeness"]], i["expires_on"]))
        st.session_state["recipe_tags"] = unique_names(ordered)
    tags = st.session_state["recipe_tags"]
    options = _unique(unique_names(items) + list(tags))
    st.multiselect("Search by ingredients", options, key="recipe_tags", accept_new_options=True,
                   placeholder="Search by ingredients", label_visibility="collapsed",
                   help="Remove a tag with its x, or type another ingredient and press Enter.")
    tags = list(st.session_state["recipe_tags"])

    saved = db.list_saved(uid())
    saved_ids = {r["id"] for r in saved}
    urgent_names = unique_names([i for i in items if i["ripeness"] == "Priority"])

    if not tags:
        st.markdown('<div class="fs-card fs-center"><b>Add an ingredient to search.</b><br>'
                    '<span class="fs-muted">Type one above, or add food to your pantry first.</span></div>',
                    unsafe_allow_html=True)
    else:
        with st.spinner("Finding recipes..."):
            result = services.search_recipes(tags, urgent_names)
        if result["note"]:
            st.caption(result["note"])
        recipes = sorted(result["recipes"], key=lambda r: _urgency_key(r, items))
        if not recipes:
            st.markdown('<div class="fs-card fs-center"><b>No recipes found for these ingredients.</b><br>'
                        '<span class="fs-muted">Try removing a tag to widen the search.</span></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="fs-muted" style="margin:0.6rem 0 0.8rem;">'
                        f'{len(recipes)} recipe{"s" if len(recipes) != 1 else ""}, with the ones that use '
                        f'your Priority items first</div>', unsafe_allow_html=True)
            _grid(recipes, "r", saved_ids, items)

    st.divider()
    st.markdown("### Saved recipes")
    if not saved:
        st.markdown('<span class="fs-muted">Tap the heart on a recipe to keep it here.</span>',
                    unsafe_allow_html=True)
    else:
        _grid([dict(r) for r in saved], "s", saved_ids, items, show_counts=False)


# ---- detail ------------------------------------------------------------------

def _nutrition_panel(nutrition):
    rows = "".join(f'<div class="fs-nutri-row"><span>{label}</span>'
                   f'<span>{nutrition.get(key, 0):,.0f} {unit}</span></div>'
                   for label, key, unit in NUTRITION_ROWS)
    st.markdown(f'<div class="fs-card"><b>Nutrition</b> <span class="fs-muted">per serving</span>{rows}</div>',
                unsafe_allow_html=True)


def _score_panel(detail, nutrition, score, breakdown):
    ratings = "".join(
        f'<div class="fs-rating"><span>{esc(k)}</span><b class="{esc(v.split()[0])}">{esc(v)}</b></div>'
        for k, v in breakdown.items())
    st.markdown(f'<div class="fs-card"><div class="fs-muted">Meal score</div>'
                f'<div class="fs-score">{score}<small> /100</small></div>'
                f'<div style="margin-top:0.6rem;">{ratings}</div></div>', unsafe_allow_html=True)
    with st.spinner("Writing a short explanation..."):
        text = services.explain_score(detail["title"], nutrition, score, breakdown)
    st.markdown(f'<div class="fs-card" style="margin-top:0.7rem;">{esc(text)}</div>', unsafe_allow_html=True)


def _cook(detail, nutrition, score):
    """Record the meal, take the ingredients out of the pantry, store the impact."""
    pantry = pantry_items()
    remaining = {p["id"]: p["amount"] for p in pantry}
    removed, used_ripeness, counted = [], [], set()
    for ing in detail["ingredients"]:
        if matching.is_staple(ing["name"]):
            continue
        item = matching.find_pantry_item(ing["name"], pantry)
        if item is None:
            continue
        available = remaining[item["id"]]
        taken = units.compute_deduction(available, item["unit"], ing["amount"], ing["unit"])
        remaining[item["id"]] = round(available - taken, 2)
        if item["id"] not in counted:
            counted.add(item["id"])
            used_ripeness.append(item["ripeness"])
        removed.append({"name": item["name"], "amount": taken, "unit": item["unit"]})
    for item in pantry:
        left = remaining[item["id"]]
        if left == item["amount"]:
            continue
        if left <= 0.005:
            db.delete_pantry_item(uid(), item["id"])
        else:
            db.update_pantry_item(uid(), item["id"], amount=left)

    cost = (detail.get("price_per_serving") or 0.0) * (detail.get("servings") or 1)
    saved, lbs, money = stats.estimate_impact(used_ripeness, cost)
    names = _unique([r["name"] for r in removed])
    db.add_meal(uid(), detail["id"], detail["title"], detail.get("image"), score, nutrition,
                names, saved, lbs, money)
    st.session_state["cook_result"] = {"title": detail["title"], "removed": removed,
                                       "count": len(names), "lbs": lbs, "money": money}
    st.session_state.pop("recipe_stub", None)


def _detail_view(stub):
    top_bar()
    st.button("← Back to recipes", key="rec_back", on_click=_back)

    with st.spinner("Loading recipe..."):
        detail = services.get_detail(stub)
    items = pantry_items()
    saved_ids = {r["id"] for r in db.list_saved(uid())}

    title_col, heart_col = st.columns([8, 1], vertical_alignment="center")
    title_col.header(detail["title"])
    with heart_col:
        _heart(detail["id"], detail["title"], detail.get("image"), "rec_heart_detail",
               detail["id"] in saved_ids)
    meta = []
    if detail.get("minutes"):
        meta.append(f"{detail['minutes']} min")
    if detail.get("servings"):
        meta.append(f"{detail['servings']} servings")
    if detail.get("price_per_serving"):
        meta.append(f"${detail['price_per_serving']:.2f} per serving")
    if meta:
        st.caption(" · ".join(meta))
    if detail.get("note"):
        st.warning(detail["note"])

    with st.container(key="hero"):
        _photo(detail, hero=True)

    if detail["ingredients"]:
        names = [i["name"] for i in detail["ingredients"]]
        used, missing = matching.split_used_missing(names, [p["name"] for p in items])
    else:
        used, missing = stub.get("used_names", []), stub.get("missing_names", [])

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown("**Used ingredients**  \n<span class='fs-muted'>From your pantry</span>",
                    unsafe_allow_html=True)
        if used:
            lines = []
            for name in used:
                item = matching.find_pantry_item(name, items)
                tag = f" {chip(item['ripeness'])}" if item and item["ripeness"] != "Safe" else ""
                lines.append(f"<div style='padding:0.2rem 0;'>✓ {esc(name.capitalize())}{tag}</div>")
            st.markdown("".join(lines), unsafe_allow_html=True)
        else:
            st.caption("None of this recipe's ingredients matched your pantry.")
        st.write("")
        st.markdown("**Missing ingredients**  \n<span class='fs-muted'>You'd need to buy these</span>",
                    unsafe_allow_html=True)
        if missing:
            st.markdown("".join(f"<div style='padding:0.2rem 0;'>• {esc(n.capitalize())}</div>" for n in missing),
                        unsafe_allow_html=True)
        else:
            st.caption("Nothing. You have everything.")

    nutrition = detail.get("nutrition")
    with right:
        if nutrition is None:
            st.markdown('<div class="fs-card"><b>Nutrition isn\'t available right now.</b><br>'
                        '<span class="fs-muted">Without it this meal can\'t be scored or logged. '
                        'Reload in a moment to try again.</span></div>', unsafe_allow_html=True)
        else:
            _nutrition_panel(nutrition)

    if nutrition is not None:
        targets = stats.targets_list(db.get_profile(uid()))
        score = scoring.meal_score(nutrition, targets)
        breakdown = scoring.score_breakdown(nutrition, targets)
        with right:
            st.write("")
            _score_panel(detail, nutrition, score, breakdown)

        st.write("")
        if st.button("Cook This Meal", type="primary", width="stretch", key="rec_cook",
                     icon=":material/skillet:"):
            _cook(detail, nutrition, score)
            st.rerun()
        st.caption("Adds one serving to today's totals and takes the ingredients you used out of your pantry.")

    if detail.get("steps"):
        with st.expander("Steps"):
            for n, step in enumerate(detail["steps"], 1):
                st.markdown(f"{n}. {step}")


# ---- after cooking -------------------------------------------------------------

def _to_pantry():
    goto("Pantry")


def _cooked_view(result):
    top_bar()
    with st.container(border=True):
        st.markdown("### Meal recorded")
        st.markdown(f"**{esc(result['title'])}**. You used {result['count']} pantry "
                    f"ingredient{'s' if result['count'] != 1 else ''}.")
        a, b = st.columns(2)
        a.metric("Estimated food waste prevented", f"{result['lbs']:g} lbs")
        b.metric("Estimated money saved", f"${result['money']:,.2f}")
        if result["removed"]:
            st.markdown("**Taken out of your pantry**")
            for r in result["removed"]:
                st.markdown(f"- {esc(r['name'])}: {esc(units.format_quantity(r['amount'], r['unit']))}")
            st.caption("When a recipe's unit doesn't match your pantry's, we take out about a quarter "
                       "of what you have. Fix any amount in Pantry.")
        else:
            st.caption("None of the ingredients matched your pantry, so nothing was removed.")
    st.write("")
    c1, c2 = st.columns(2)
    c1.button("View your updated pantry", type="primary", width="stretch", key="rec_to_pantry",
              icon=":material/kitchen:", on_click=_to_pantry)
    c2.button("Back to recipes", width="stretch", key="rec_after_back",
              on_click=lambda: st.session_state.pop("cook_result", None))


def render():
    result = st.session_state.get("cook_result")
    stub = st.session_state.get("recipe_stub")
    if result:
        _cooked_view(result)
    elif stub:
        _detail_view(stub)
    else:
        _list_view()
