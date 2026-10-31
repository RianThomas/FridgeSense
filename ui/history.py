import streamlit as st

from core import db, stats
from ui.common import esc, top_bar, uid
from ui.recipes_page import NUTRITION_ROWS


def render():
    top_bar("Meal history")
    meals = db.list_meals(uid())
    life = stats.lifetime(meals)

    cols = st.columns(4)
    cols[0].metric("Total meals", life["meals"])
    cols[1].metric("Ingredients saved", life["ingredients_saved"],
                   help="Ingredients that were Priority or Moderate when you cooked with them.")
    cols[2].metric("Estimated food waste prevented", f"{life['food_saved_lbs']:g} lbs")
    cols[3].metric("Estimated money saved", f"${life['money_saved']:,.2f}")
    st.write("")

    if not meals:
        st.markdown('<div class="fs-card fs-center"><b>No meals yet.</b><br>'
                    '<span class="fs-muted">Open a recipe and choose Cook This Meal to start your history.</span></div>',
                    unsafe_allow_html=True)
        return

    for meal in meals:
        date_text = meal["cooked_on"].strftime("%B %d").replace(" 0", " ")
        with st.expander(f"{meal['title']}  ·  {date_text}  ·  Score {meal['score']}"):
            left, right = st.columns(2)
            with left:
                st.markdown("**Used from your pantry**")
                if meal["ingredients"]:
                    for name in meal["ingredients"]:
                        st.markdown(f"- {name}")
                else:
                    st.caption("Nothing matched the pantry.")
                st.caption(f"Estimated saved: {meal['food_saved_lbs']:g} lbs and ${meal['money_saved']:,.2f}")
            with right:
                st.markdown("**Nutrition per serving**")
                for label, key, unit in NUTRITION_ROWS:
                    st.markdown(f"{label}: {meal['nutrition'].get(key, 0):,.0f} {unit}")
