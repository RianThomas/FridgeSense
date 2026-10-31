import streamlit as st

st.set_page_config(page_title="Fridge Sense", page_icon="🥬", layout="wide",
                   initial_sidebar_state="auto")

from core import db  # noqa: E402
from ui import (common, diet_plan, history, home, login, pantry, recipes_page,  # noqa: E402
                theme, upload)

db.init_db()

st.session_state.setdefault("user", None)
st.session_state.setdefault("sb_collapsed", False)
if not st.session_state.get("page"):
    st.session_state["page"] = "Home" if st.session_state["user"] else "Login"

signed_in = st.session_state["user"] is not None
if not signed_in:
    st.session_state["page"] = "Login"
elif st.session_state["page"] == "Login":
    st.session_state["page"] = "Home"

PAGES = {
    "Login": login,
    "Home": home,
    "Upload": upload,
    "Pantry": pantry,
    "Recipes": recipes_page,
    "Diet Plan": diet_plan,
    "History": history,
}

theme.inject(collapsed=st.session_state["sb_collapsed"])
common.render_sidebar()
PAGES[st.session_state["page"]].render()

_stub = st.session_state.get("recipe_stub") or {}
common.scroll_to_top_on_view_change(
    f'{st.session_state["page"]}|{_stub.get("id")}|{bool(st.session_state.get("cook_result"))}')
