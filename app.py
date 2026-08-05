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
                f"text-align:center;'>Enter your password to continue</p>",
                unsafe_allow_html=True,
            )
            pw = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            submitted = st.form_submit_button("Log in", use_container_width=True)
        if submitted:
            if pw == st.secrets.get("APP_PASSWORD", ""):
                st.session_state.authed = True
                st.rerun()
            else:
                st.error("Wrong password")


if not st.session_state.authed:
    show_login()
    st.stop()

top_l, top_r = st.columns([5, 1])
with top_l:
    render_page_header("Expense Monitoring System")
with top_r:
    st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
    if st.button("Log out", use_container_width=True):
        st.session_state.authed = False
        st.rerun()

st.write("")
tab_home, tab_add, tab_analytics = st.tabs(["Home", "Add expense", "Analytics"])
with tab_home:
    home.render()
with tab_add:
    add_expense.render()
with tab_analytics:
    analytics.render()