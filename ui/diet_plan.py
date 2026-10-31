from datetime import date

import streamlit as st

from core import db, stats
from ui.common import esc, top_bar, uid

ACTIVITY = ["sedentary", "light", "moderate", "high"]
GOALS = ["lose weight", "maintain", "gain muscle"]
SEXES = ["Male", "Female", "Other"]

TARGET_ROWS = [("Calories", "calories", "kcal"), ("Protein", "protein", "g"), ("Fiber", "fiber", "g"),
               ("Sugar", "sugar", "g"), ("Sodium", "sodium", "mg"), ("Cholesterol", "cholesterol", "mg"),
               ("Fat", "fat", "g")]


def render():
    top_bar("Your nutrition goals")

    stored = db.get_profile(uid())
    p = stats.profile_or_default(stored)
    feet, inches = divmod(round(p["height_in"]), 12)

    with st.form("profile_form"):
        a, b, c, d = st.columns(4)
        age = a.number_input("Age", min_value=10, max_value=100, value=int(p["age"]), step=1)
        ft = b.number_input("Height (ft)", min_value=3, max_value=7, value=int(feet), step=1)
        inch = c.number_input("Height (in)", min_value=0, max_value=11, value=int(inches), step=1)
        weight = d.number_input("Weight (lb)", min_value=60.0, max_value=500.0,
                                value=float(p["weight_lb"]), step=1.0, format="%g")
        e, f, g = st.columns(3)
        sex = e.selectbox("Sex", SEXES, index=SEXES.index(p["sex"]) if p["sex"] in SEXES else 2)
        activity = f.selectbox("Activity level", ACTIVITY, index=ACTIVITY.index(p["activity"]),
                               format_func=str.capitalize)
        goal = g.selectbox("Goal", GOALS, index=GOALS.index(p["goal"]), format_func=str.capitalize)
        saved = st.form_submit_button("Save goals", type="primary")
    if saved:
        db.save_profile(uid(), int(age), float(ft * 12 + inch), float(weight), sex, activity, goal)
        st.success("Goals saved. Your Home rings and meal scores now use these targets.")
        stored = db.get_profile(uid())
    if stored is None:
        st.caption("Until you save your details, targets use a general profile.")
    st.caption("Targets use the Mifflin-St Jeor equation, which is designed for adults. "
               "Treat them as a starting point, not medical advice.")

    targets = stats.targets_for(stored)
    st.markdown("#### Daily targets")
    for chunk in (TARGET_ROWS[:4], TARGET_ROWS[4:]):
        cols = st.columns(4)
        for col, (label, key, unit) in zip(cols, chunk):
            col.markdown(f'<div class="fs-card" style="margin-bottom:0.9rem;"><div class="fs-muted">{label}</div>'
                         f'<div class="fs-impact-num" style="font-size:1.8rem;">{targets[key]:,.0f} '
                         f'<span class="fs-muted" style="font-size:1rem;">{unit}</span></div></div>',
                         unsafe_allow_html=True)

    meals = db.list_meals(uid())
    today = [m for m in meals if m["cooked_on"] == date.today()]
    totals = stats.today_totals(meals)
    st.markdown("#### Today's progress")
    for label, key, unit in TARGET_ROWS:
        pct = totals[key] / targets[key] if targets[key] else 0
        st.progress(min(pct, 1.0), text=f"{label}: {totals[key]:,.0f} of {targets[key]:,.0f} {unit} ({pct:.0%})")

    st.markdown("#### Today's meals")
    if not today:
        st.markdown('<span class="fs-muted">No meals logged today. Cook a recipe to see it here.</span>',
                    unsafe_allow_html=True)
    for m in today:
        st.markdown(f"**{esc(m['title'])}** · score {m['score']} · {m['nutrition'].get('calories', 0):,.0f} kcal",
                    unsafe_allow_html=True)
