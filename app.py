from pathlib import Path

import streamlit as st
from PIL import Image

from theme import TEXT, TEXT_MUTED, inject_background, inject_css, render_page_header
from views import add_expense, analytics, home

ICON_PATH = Path(__file__).resolve().parent / "Images" / "app_icon.png"
app_icon = Image.open(ICON_PATH) if ICON_PATH.exists() else "💰"

st.set_page_config(page_title="EMS", page_icon=app_icon, layout="wide")

if "authed" not in st.session_state:
    st.session_state.authed = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

inject_css()
inject_background()


def show_login():
    st.markdown("<div style='height:14vh;'></div>", unsafe_allow_html=True)
    _left, center, _right = st.columns([1, 1, 1])
    with center:
        with st.form("login_form"):
            st.markdown(
                f"<h2 style='margin:0 0 4px; color:{TEXT}; font-size:24px; "
                f"font-weight:600; text-align:center;'>Expense Monitoring System</h2>"
                f"<p style='margin:0 0 20px; color:{TEXT_MUTED}; font-size:13px; "
                f"text-align:center;'>Choose your account and enter your password</p>",
                unsafe_allow_html=True,
            )
            users = list(st.secrets["users"].keys())
            username = st.selectbox("User", users, format_func=lambda u: u.capitalize())
            pw = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            if st.secrets["users"].get(username) == pw:
                st.session_state.authed = True
                st.session_state.current_user = username
                st.rerun()
            else:
                st.error("Wrong password")


if not st.session_state.authed:
    show_login()
    st.stop()

current_user = st.session_state.current_user

top_l, top_r = st.columns([5, 1])
with top_l:
    render_page_header("Expense Monitoring System")
with top_r:
    st.markdown(
        f"<div style='height:10px;'></div><p style='text-align:right; color:{TEXT_MUTED}; "
        f"font-size:12px; margin:0 0 6px;'>Logged in as {current_user.capitalize()}</p>",
        unsafe_allow_html=True,
    )
    if st.button("Log out", use_container_width=True):
        st.session_state.authed = False
        st.session_state.current_user = None
        st.rerun()

st.write("")
tab_home, tab_add, tab_analytics = st.tabs(["Home", "Add expense", "Analytics"])
with tab_home:
    home.render(current_user)
with tab_add:
    add_expense.render(current_user)
with tab_analytics:
    analytics.render(current_user)