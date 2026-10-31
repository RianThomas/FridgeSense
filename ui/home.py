import streamlit as st

from core import db, stats
from ui import charts
from ui.common import esc, goto, pantry_items, top_bar, unique_names, uid

# name, key in targets/totals, unit, kind  (order follows the wireframe)
RINGS = [
    ("Calories", "calories", "kcal", "limit"),
    ("Protein", "protein", "g", "goal"),
    ("Sugar", "sugar", "g", "limit"),
    ("Sodium", "sodium", "mg", "limit"),
    ("Cholesterol", "cholesterol", "mg", "limit"),
    ("Fat", "fat", "g", "limit"),
]


def _go(page):
    goto(page)


def _search_urgent(names):
    st.session_state["recipe_tags"] = names
    st.session_state["recipe_note"] = "Searching for recipes that use ingredients that need to be used now!"
    goto("Recipes")


def render():
    top_bar()

    meals = db.list_meals(uid())
    profile = db.get_profile(uid())
    targets = stats.targets_for(profile)
    totals = stats.today_totals(meals)
    life = stats.lifetime(meals)

    st.markdown('<p class="fs-muted fs-center" style="margin-bottom:0.2rem;">'
                'Eaten today, out of your daily target</p>', unsafe_allow_html=True)
    st.markdown(
        charts.ring_grid([charts.ring(name, totals[key], targets[key], unit, kind)
                          for name, key, unit, kind in RINGS]),
        unsafe_allow_html=True)

    st.markdown(
        '<div class="fs-impact">'
        f'<div class="fs-impact-item"><div class="fs-impact-num">{life["food_saved_lbs"]:g} lbs</div>'
        '<div class="fs-impact-label">You saved this much food!</div></div>'
        f'<div class="fs-impact-item"><div class="fs-impact-num">${life["money_saved"]:,.2f}</div>'
        '<div class="fs-impact-label">You saved this much money!/div></div>'
        '</div>', unsafe_allow_html=True)

    st.write("")
    st.write("")
    _next_step(profile, meals)


def _next_step(profile, meals):
    """Every page ends by saying what to do next."""
    items = pantry_items()
    urgent = [i for i in items if i["ripeness"] == "Priority"]
    box = st.container(border=True)
    with box:
        if not items:
            st.markdown("**Your pantry is looking empty.** Take a photo of your fridge and Fridge Sense will help you out!")
            st.button("Upload a photo", type="primary", key="home_cta_upload",
                      icon=":material/upload:", on_click=_go, args=("Upload",))
        elif urgent:
            names = unique_names(urgent)
            st.markdown(f"**You have {len(urgent)} item{'s' if len(urgent) != 1 else ''} that need to be used soon! Here they are: ** "
                        f"{esc(', '.join(names[:4]))}.")
            st.button("Find me recipes for them", type="primary", key="home_cta_recipes",
                      icon=":material/restaurant_menu:", on_click=_search_urgent, args=(names,))
        elif profile is None:
            st.markdown("**These totals use an average person.** Add your own age, height and weight to get targets that help you!")
            st.button("Set my nutrition goals", type="primary", key="home_cta_goals",
                      icon=":material/monitor_heart:", on_click=_go, args=("Diet Plan",))
        else:
            st.markdown("**You're all caught up for now. ** What are we eating next?")
            st.button("Browse recipes", type="primary", key="home_cta_browse",
                      icon=":material/restaurant_menu:", on_click=_go, args=("Recipes",))
        if profile is None and (items and urgent):
            st.caption("These are for an average person. Set up your account and you own profile for more!")
