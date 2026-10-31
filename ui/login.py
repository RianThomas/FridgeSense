import streamlit as st

from core import auth
from ui.common import sign_in

AVATAR = (
    '<div class="fs-avatar"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
    'role="img" aria-label="Profile"><circle cx="12" cy="8" r="4"/>'
    '<path d="M4 21c0-4.4 3.6-7 8-7s8 2.6 8 7"/></svg></div>'
)


def render():
    _, middle, _ = st.columns([1, 1.4, 1])
    with middle:
        st.write("")
        st.markdown('<div class="fs-brand-title" style="font-size:2.6rem;">Fridge Sense</div>',
                    unsafe_allow_html=True)
        st.markdown(AVATAR, unsafe_allow_html=True)

        log_in, create = st.tabs(["Log in", "Create account"])

        with log_in:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submitted = st.form_submit_button("Log in", type="primary", width="stretch")
            if submitted:
                person, error = auth.login(username, password)
                if error:
                    st.error(error)
                else:
                    sign_in(person)
                    st.rerun()

        with create:
            with st.form("register_form"):
                new_user = st.text_input("Choose a username", key="reg_user",
                                         help="3 to 30 letters, numbers, dots, dashes or underscores.")
                new_pass = st.text_input("Choose a password", type="password", key="reg_pass",
                                         help="At least 8 characters.")
                confirm = st.text_input("Repeat the password", type="password", key="reg_confirm")
                created = st.form_submit_button("Create account", type="primary", width="stretch")
            if created:
                person, error = auth.register(new_user, new_pass, confirm)
                if error:
                    st.error(error)
                else:
                    sign_in(person)
                    st.rerun()

        st.markdown('<p class="fs-muted fs-center" style="margin-top:1rem;">'
                    'Accounts are stored in a database file on the computer running this app.</p>',
                    unsafe_allow_html=True)
