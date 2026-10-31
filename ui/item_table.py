"""The editable food table used by both Upload and Pantry (the wireframes ask
for the same columns on both): Food, Current ripeness, Storage, Amount, Unit,
and a delete button per row."""
import streamlit as st

from core.shelf_life import RIPENESS_LEVELS, STORAGES
from core.units import PANTRY_UNITS

UPLOAD_WIDTHS = [3.2, 2, 1.8, 1.3, 1.5, 0.6]
PANTRY_WIDTHS = [3, 2, 1.5, 1.7, 1.3, 1.5, 0.6]


def header(show_use_by=False):
    labels = ["Food", "Current ripeness"] + (["Use by"] if show_use_by else []) + \
             ["Storage", "Amount", "Unit", ""]
    widths = PANTRY_WIDTHS if show_use_by else UPLOAD_WIDTHS
    for col, label in zip(st.columns(widths), labels):
        col.markdown(f'<div class="fs-th">{label}</div>', unsafe_allow_html=True)


def _pick(value, options, fallback):
    return value if value in options else fallback


def row(prefix, rid, *, name, ripeness, storage, amount, unit, use_by_html=None,
        sync=False, on_change=None, on_delete=None):
    """Draw one row. Widget values live in st.session_state under
    f"{prefix}_<field>_{rid}".

    The values passed in seed those keys the first time a row is drawn.
    sync=True re-writes them from the caller's data on every run: the Pantry
    does this because the database is the source of truth and an amount can
    change elsewhere (for example after cooking a meal).

    on_change(rid, field, key) is called when the person edits a cell; field
    is one of name, ripeness, storage, amount, unit.
    """
    keys = {f: f"{prefix}_{f}_{rid}" for f in ("name", "ripeness", "storage", "amount", "unit")}
    values = {
        "name": name,
        "ripeness": _pick(ripeness, RIPENESS_LEVELS, "Safe"),
        "storage": _pick(storage, STORAGES, "Fridge"),
        "amount": float(amount),
        "unit": _pick(unit, PANTRY_UNITS, "Piece"),
    }
    for field, key in keys.items():
        if sync or key not in st.session_state:
            st.session_state[key] = values[field]

    def hook(field):
        if on_change is None:
            return {}
        return {"on_change": on_change, "args": (rid, field, keys[field])}

    widths = PANTRY_WIDTHS if use_by_html is not None else UPLOAD_WIDTHS
    cols = st.columns(widths, vertical_alignment="center")
    cols[0].text_input("Food", key=keys["name"], label_visibility="collapsed", **hook("name"))
    cols[1].selectbox("Current ripeness", RIPENESS_LEVELS, key=keys["ripeness"],
                      label_visibility="collapsed", **hook("ripeness"))
    nxt = 2
    if use_by_html is not None:
        cols[nxt].markdown(use_by_html, unsafe_allow_html=True)
        nxt += 1
    cols[nxt].selectbox("Storage", STORAGES, key=keys["storage"],
                        label_visibility="collapsed", **hook("storage"))
    cols[nxt + 1].number_input("Amount", min_value=0.01, step=1.0, format="%g",
                               key=keys["amount"], label_visibility="collapsed", **hook("amount"))
    cols[nxt + 2].selectbox("Unit", PANTRY_UNITS, key=keys["unit"],
                            label_visibility="collapsed", **hook("unit"))
    if on_delete:
        cols[nxt + 3].button("✕", key=f"{prefix}_del_{rid}", help="Remove this row",
                             on_click=on_delete, args=(rid,))
    return keys
