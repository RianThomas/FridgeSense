"""Pantry page: the stored inventory as an editable table, with filters and the
"Search for recipes using Priority ingredients" button."""
import streamlit as st

from core import db, demo, shelf_life
from ui import item_table
from ui.common import esc, goto, pantry_items, top_bar, unique_names, uid

PREFIX = "pan"


def _on_change(item_id, field, key):
    value = st.session_state.get(key)
    item = next((i for i in db.list_pantry(uid()) if i["id"] == item_id), None)
    if item is None:
        return
    if field == "name":
        if str(value or "").strip():
            db.update_pantry_item(uid(), item_id, name=str(value).strip())
    elif field == "ripeness":
        db.update_pantry_item(uid(), item_id, expires_on=shelf_life.expiry_for_ripeness(
            value, item["name"], item["storage"]))
    elif field in ("storage", "unit"):
        db.update_pantry_item(uid(), item_id, **{field: value})
    elif field == "amount":
        try:
            if float(value) > 0:
                db.update_pantry_item(uid(), item_id, amount=float(value))
        except (TypeError, ValueError):
            pass


def _delete(item_id):
    db.delete_pantry_item(uid(), item_id)


def _commit_new():
    name = (st.session_state.get("pan_blank") or "").strip()
    if name:
        expires = shelf_life.expiry_for_ripeness(
            shelf_life.default_ripeness(name, "Fridge"), name, "Fridge")
        db.add_pantry_item(uid(), name, 1.0, "Piece", "Fridge", expires)
    st.session_state["pan_blank"] = ""


def _load_samples():
    from datetime import date, timedelta
    for name, amount, unit, storage, days in demo.SAMPLE_PANTRY:
        db.add_pantry_item(uid(), name, amount, unit, storage, date.today() + timedelta(days=days))


def _search_priority(names):
    st.session_state["recipe_tags"] = names
    st.session_state["recipe_note"] = "Searching with the ingredients that should be used soon."
    goto("Recipes")


def render():
    top_bar("Pantry")
    items = pantry_items()

    if not items:
        st.markdown('<div class="fs-card fs-center">'
                    '<b>Your pantry is empty.</b><br>'
                    '<span class="fs-muted">Upload a photo to fill it, or type foods into the last row below.</span>'
                    '</div>', unsafe_allow_html=True)
        st.write("")

    # Filters (the wireframe's "Filter" control)
    count_col, f_rip, f_sto, f_sort = st.columns([2.2, 1.6, 1.6, 1.8], vertical_alignment="bottom")
    count_col.markdown(f'<span class="fs-muted">{len(items)} item{"s" if len(items) != 1 else ""}</span>',
                       unsafe_allow_html=True)
    ripeness_filter = f_rip.selectbox("Ripeness", ["All"] + shelf_life.RIPENESS_LEVELS, key="pan_f_rip")
    storage_filter = f_sto.selectbox("Storage", ["All"] + shelf_life.STORAGES, key="pan_f_sto")
    sort_by = f_sort.selectbox("Sort by", ["Use by", "Name", "Amount"], key="pan_f_sort")

    shown = [i for i in items
             if (ripeness_filter == "All" or i["ripeness"] == ripeness_filter)
             and (storage_filter == "All" or i["storage"] == storage_filter)]
    if sort_by == "Name":
        shown.sort(key=lambda i: i["name"].lower())
    elif sort_by == "Amount":
        shown.sort(key=lambda i: -i["amount"])
    else:
        shown.sort(key=lambda i: (i["expires_on"], i["name"].lower()))

    st.write("")
    item_table.header(show_use_by=True)
    for item in shown:
        cls = item["ripeness"].lower()
        use_by = f'<span class="fs-useby {cls}">{esc(item["use_by"])}</span>'
        item_table.row(PREFIX, item["id"], name=item["name"], ripeness=item["ripeness"],
                       storage=item["storage"], amount=item["amount"], unit=item["unit"],
                       use_by_html=use_by, sync=True, on_change=_on_change, on_delete=_delete)

    if items and not shown:
        st.caption("Nothing matches these filters.")

    name_col, hint_col = st.columns([3, 9], vertical_alignment="center")
    name_col.text_input("Add a food", key="pan_blank", placeholder="Add a food",
                        label_visibility="collapsed", on_change=_commit_new)
    hint_col.markdown('<span class="fs-muted">Press Enter to add it to your pantry.</span>',
                      unsafe_allow_html=True)

    if not items:
        st.button("Fill with sample items", key="pan_samples", icon=":material/science:",
                  on_click=_load_samples,
                  help="Adds ten example foods so you can try the app without a photo.")

    st.write("")
    priority = unique_names([i for i in items if i["ripeness"] == "Priority"])
    _, middle, _ = st.columns([1, 2, 1])
    with middle:
        st.button("Search for recipes using Priority ingredients", type="primary", width="stretch",
                  key="pan_search", icon=":material/restaurant_menu:", disabled=not priority,
                  on_click=_search_priority, args=(priority,))
        if items and not priority:
            st.caption("Nothing is marked Priority right now. The Recipes page can search with everything in your pantry.")
