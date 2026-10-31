"""Session helpers, navigation, top bar and sidebar shared by every page."""
import html
import json
from datetime import date

import streamlit as st

from core import db, services, shelf_life

NAV = [
    ("Home", ":material/home:"),
    ("Upload", ":material/upload:"),
    ("Pantry", ":material/kitchen:"),
    ("Recipes", ":material/restaurant_menu:"),
    ("Diet Plan", ":material/monitor_heart:"),
    ("History", ":material/history:"),
]

# Keys that belong to one signed-in person and must not leak to the next.
_USER_KEYS = ("recipe_tags", "recipe_stub", "cook_result", "upload_rows", "upload_sig",
              "upload_note", "show_camera", "recipe_note")
_USER_PREFIXES = ("up_", "pan_", "rec_")


def esc(value):
    return html.escape(str(value), quote=True)


def user():
    return st.session_state.get("user")


def uid():
    return st.session_state["user"]["id"]


def clear_user_state():
    for key in list(st.session_state.keys()):
        if key in _USER_KEYS or key.startswith(_USER_PREFIXES):
            del st.session_state[key]


def goto(page):
    """For normal script flow; follow with st.rerun()."""
    st.session_state.page = page
    st.session_state.pop("recipe_stub", None)
    st.session_state.pop("cook_result", None)


def sign_in(person):
    clear_user_state()
    st.session_state.user = person
    st.session_state.page = "Home"


def sign_out():
    clear_user_state()
    st.session_state.user = None
    st.session_state.page = "Login"


def pantry_items():
    """Pantry rows with ripeness and a use-by label worked out for today."""
    today = date.today()
    items = db.list_pantry(uid())
    for item in items:
        item["ripeness"] = shelf_life.ripeness_for(item["expires_on"], today)
        item["use_by"] = shelf_life.use_by_label(item["expires_on"], today)
    return items


def chip(ripeness):
    return f'<span class="fs-chip {ripeness.lower()}">{esc(ripeness)}</span>'


def unique_names(items):
    seen, out = set(), []
    for item in items:
        key = item["name"].strip().lower()
        if key not in seen:
            seen.add(key)
            out.append(item["name"])
    return out


# ---- chrome ----------------------------------------------------------------

def _set_page(name):
    st.session_state.nav_clicks = st.session_state.get("nav_clicks", 0) + 1
    goto(name)


_CLOSE_SIDEBAR_JS = """<script>
(function () {
  var taps = __TAPS__;  // changes the script text after every menu tap
  if (window.innerWidth > 768) return;
  // Streamlit is still re-rendering the sidebar when this runs, so look for the close
  // button for up to a second instead of once.
  var tries = 0;
  (function attempt() {
    var el = document.querySelector('[data-testid="stSidebarCollapseButton"]');
    var btn = el && (el.tagName === 'BUTTON' ? el : el.querySelector('button'));
    if (btn) { btn.click(); return; }
    if (++tries < 10) setTimeout(attempt, 100);
  })();
})();
</script>"""


def _close_sidebar_on_phone():
    """On a phone the sidebar is an overlay that would stay open on top of the page after a
    tap on a menu item. The script text includes the number of menu taps so far, so it differs
    after every tap and Streamlit runs it again (an unchanged element is not re-run).
    Hidden by CSS; does nothing at desktop widths."""
    taps = int(st.session_state.get("nav_clicks", 0))
    with st.container(key="nav_closer"):
        st.html(_CLOSE_SIDEBAR_JS.replace("__TAPS__", str(taps)), unsafe_allow_javascript=True)


_SCROLL_TOP_JS = """<script>
(function () {
  var view = __VIEW__;  // changes the script text whenever the view changes
  var main = document.querySelector('[data-testid="stMain"]');
  if (main) main.scrollTo(0, 0);
})();
</script>"""


def scroll_to_top_on_view_change(view):
    """Streamlit keeps the scroll position when the app swaps one view for another, so a tap
    near the bottom of Pantry opens Recipes scrolled halfway down. `view` identifies what is on
    screen; the script text includes it, so it only runs (and scrolls to the top) when the view
    changes. Widgets that rerun the same view leave the scroll alone. Hidden by CSS."""
    with st.container(key="scroll_top"):
        st.html(_SCROLL_TOP_JS.replace("__VIEW__", json.dumps(str(view))), unsafe_allow_javascript=True)


def _toggle_sidebar():
    st.session_state.sb_collapsed = not st.session_state.get("sb_collapsed", False)


def render_sidebar():
    collapsed = st.session_state.get("sb_collapsed", False)
    active = st.session_state.get("page", "Home")
    with st.sidebar:
        st.markdown('<div class="fs-sb-brand">🥬<span class="t">Fridge Sense</span></div>',
                    unsafe_allow_html=True)
        if user():
            for name, icon in NAV:
                st.button(name, key=f"nav_{name}", icon=icon, width="stretch",
                          type="primary" if active == name else "secondary",
                          help=name if collapsed else None,
                          on_click=_set_page, args=(name,))
        else:
            st.button("Login", key="nav_Login", icon=":material/login:", width="stretch",
                      type="primary", help="Login" if collapsed else None)

        with st.container(key="sb_bottom"):
            label = "Expand" if collapsed else "Collapse"
            icon = ":material/left_panel_open:" if collapsed else ":material/left_panel_close:"
            st.button(label, key="sb_toggle", icon=icon, width="stretch",
                      help=f"{label} sidebar", on_click=_toggle_sidebar)
            note = services.sample_note()
            if note:
                st.markdown('<div class="fs-sb-note fs-muted" style="font-size:0.78rem;padding:0 0.4rem;">'
                            f'{esc(note)}</div>', unsafe_allow_html=True)
        if user():
            _close_sidebar_on_phone()


def top_bar(page_title=None):
    left, middle, right = st.columns([1, 2, 1], vertical_alignment="center")
    with middle:
        st.markdown('<div class="fs-brand-title">Fridge Sense</div>', unsafe_allow_html=True)
    with right:
        _, pop_col = st.columns([1, 2])
        with pop_col:
            with st.popover(user()["username"], icon=":material/account_circle:", width="stretch"):
                st.caption("Signed in")
                if st.button("Log out", key="logout", icon=":material/logout:", width="stretch"):
                    sign_out()
                    st.rerun()
    if page_title:
        st.markdown(f'<div class="fs-page-title">{esc(page_title)}</div>', unsafe_allow_html=True)
    else:
        st.write("")
