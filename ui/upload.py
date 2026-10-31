"""Upload page: photo in, editable table of detected foods out, then
"Add to Pantry" (which leads to the Recipes page, as the wireframe says)."""
import hashlib
import os

import streamlit as st

from core import db, services, shelf_life
from ui import item_table
from ui.common import esc, goto, top_bar, uid

PREFIX = "up"


def _rows():
    return st.session_state.setdefault("upload_rows", [])


def _new_row(name, amount=1.0, unit="Piece", storage="Fridge", ripeness=None):
    st.session_state["upload_next"] = st.session_state.get("upload_next", 0) + 1
    return {
        "rid": st.session_state["upload_next"],
        "name": name,
        "amount": float(amount),
        "unit": unit,
        "storage": storage,
        "ripeness": ripeness or shelf_life.default_ripeness(name, storage),
    }


def _add_detected(foods):
    rows = _rows()
    for name, count in foods:
        existing = next((r for r in rows if r["name"].lower() == name.lower() and r["unit"] == "Piece"), None)
        if existing is not None:
            key = f"{PREFIX}_amount_{existing['rid']}"
            st.session_state[key] = float(st.session_state.get(key, existing["amount"])) + count
        else:
            rows.append(_new_row(name, amount=count))


def _delete(rid):
    st.session_state["upload_rows"] = [r for r in _rows() if r["rid"] != rid]


def _commit_new_row():
    """Typing a name into the blank last row and pressing Enter adds it."""
    name = (st.session_state.get("up_blank") or "").strip()
    if name:
        _rows().append(_new_row(name))
    st.session_state["up_blank"] = ""


def _process_image(data, filename):
    signature = hashlib.sha1(data).hexdigest()
    if st.session_state.get("upload_sig") == signature:
        return
    st.session_state["upload_sig"] = signature
    suffix = os.path.splitext(filename or "")[1] or ".jpg"
    with st.spinner("Looking for food in your photo..."):
        result = services.detect_foods(data, suffix)
    _add_detected(result["foods"])
    st.session_state["upload_note"] = result["note"]


def _save_to_pantry():
    saved = 0
    for row in _rows():
        k = lambda f: st.session_state.get(f"{PREFIX}_{f}_{row['rid']}", row[f])  # noqa: E731
        name = str(k("name")).strip()
        if not name:
            continue
        storage, ripeness = k("storage"), k("ripeness")
        db.add_pantry_item(
            uid(), name, float(k("amount")), k("unit"), storage,
            shelf_life.expiry_for_ripeness(ripeness, name, storage))
        saved += 1
    return saved


def render():
    top_bar("Upload images")

    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("**Upload image from device**")
            uploaded = st.file_uploader("Choose a photo", type=["jpg", "jpeg", "png", "webp"],
                                        label_visibility="collapsed", key="up_file")
    with right:
        with st.container(border=True):
            st.markdown("**Take picture of pantry**")
            if st.session_state.get("show_camera"):
                shot = st.camera_input("Take a picture", label_visibility="collapsed", key="up_camera")
            else:
                shot = None
                st.caption("Your browser will ask permission to use the camera.")
                if st.button("Open camera", icon=":material/photo_camera:", key="up_open_camera"):
                    st.session_state["show_camera"] = True
                    st.rerun()

    if uploaded is not None:
        _process_image(uploaded.getvalue(), uploaded.name)
    if shot is not None:
        _process_image(shot.getvalue(), "camera.jpg")

    note = st.session_state.get("upload_note")
    if note:
        st.info(note, icon=":material/info:")

    st.write("")
    item_table.header()
    rows = _rows()
    for r in rows:
        item_table.row(PREFIX, r["rid"], name=r["name"], ripeness=r["ripeness"],
                       storage=r["storage"], amount=r["amount"], unit=r["unit"],
                       on_delete=_delete)

    # Blank last row for anything the model missed.
    name_col, hint_col = st.columns([3.2, 8.4], vertical_alignment="center")
    name_col.text_input("Add a food", key="up_blank", placeholder="Add a food we missed",
                        label_visibility="collapsed", on_change=_commit_new_row)
    hint_col.markdown('<span class="fs-muted">Press Enter to add it to the list.</span>',
                      unsafe_allow_html=True)

    if not rows:
        st.caption("Detected foods will appear here. You can also type them into the last row.")

    st.write("")
    _, action = st.columns([3, 1])
    with action:
        if st.button("Add to Pantry", type="primary", width="stretch", key="up_save",
                     disabled=not rows):
            saved = _save_to_pantry()
            if saved:
                for key in [k for k in st.session_state if k.startswith(f"{PREFIX}_")]:
                    del st.session_state[key]
                for key in ("upload_rows", "upload_sig", "upload_note", "show_camera", "recipe_tags"):
                    st.session_state.pop(key, None)
                goto("Recipes")
                st.session_state["recipe_note"] = (
                    f"Added {saved} item{'s' if saved != 1 else ''} to your pantry. "
                    "Here are recipes you can make with them.")
                st.rerun()
            else:
                st.warning("Give each food a name before adding it to your pantry.")
