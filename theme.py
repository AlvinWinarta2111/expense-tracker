import base64
from pathlib import Path

import streamlit as st

BG = "#0D0E10"
SURFACE = "#17181B"
SURFACE_2 = "#1F2023"
BORDER = "#2A2C30"
TEXT = "#F2F2F0"
TEXT_MUTED = "#8B8D93"
ACCENT = "#4F6FFF"
POSITIVE = "#5FD98A"
NEGATIVE = "#EF6461"

# background image lives at expense-tracker/Images/Page_BG.png
BG_IMAGE_PATH = Path(__file__).resolve().parent / "Images" / "Page_BG.png"
HEADER_IMAGE_PATH = Path(__file__).resolve().parent / "Images" / "Header_Banner.png"
# tune these to shift which part of the banner image shows through the
# short header bar - the source image is much less "wide" than the bar,
# so cover crops it hard; these pick which slice survives
HEADER_POSITION_X = "center"
HEADER_POSITION_Y = "40%"  # 0% = top of image, 100% = bottom of image
# 0 = image shows at full strength, 1 = fully hidden behind solid color
BG_OVERLAY_OPACITY = 0.50
# vertical anchor for the image; lower % = shows more of the top artwork
BG_POSITION_Y = "15%"

# one color per category, reused everywhere a category shows up
# (home KPIs, analytics chart, tables) so "Date" is always the same
# rose color no matter which page you're looking at
CATEGORY_COLORS = {
    "Income": POSITIVE,
    "Food & Beverages": "#F0A857",
    "Living Cost": "#5B9BD5",
    "Shopping": "#D883C0",
    "Transport": "#4FC3B0",
    "Life & Entertainment": "#9B8DE0",
    "Date": "#E8677A",
}


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500&family=JetBrains+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        [data-testid="stMetricValue"] {{
            font-family: 'JetBrains Mono', monospace !important;
            font-size: 20px !important;
            line-height: 1.35 !important;
            overflow: visible !important;
            white-space: normal !important;
        }}
        .balance-label {{
            color: {TEXT_MUTED};
            font-size: 13px;
            margin-bottom: 0;
        }}
        .balance-value {{
            color: {TEXT};
            font-size: 40px;
            font-weight: 500;
            margin-top: 0;
        }}

        [data-testid="stMetric"] {{
            background: {SURFACE};
            border: 0.5px solid {BORDER};
            border-radius: 10px;
            padding: 14px 14px;
            overflow: visible;
        }}

        [data-testid="stForm"] {{
            background: {SURFACE};
            border: 0.5px solid {BORDER};
            border-radius: 14px;
            padding: 32px 28px;
        }}

        .stTextInput input,
        .stNumberInput input,
        .stDateInput input,
        .stTextArea textarea {{
            background-color: {SURFACE_2} !important;
            border: 1px solid {BORDER} !important;
            color: {TEXT} !important;
        }}
        [data-baseweb="select"] > div {{
            background-color: {SURFACE_2} !important;
            border: 1px solid {BORDER} !important;
        }}
        [data-testid="stDateInput"] > div > div {{
            background-color: {SURFACE_2} !important;
            border: 1px solid {BORDER} !important;
        }}

        div.stButton > button, div.stFormSubmitButton > button {{
            background: {ACCENT};
            color: {TEXT};
            border: none;
            border-radius: 8px;
        }}
        div.stButton > button:hover, div.stFormSubmitButton > button:hover {{
            opacity: 0.9;
        }}

        .stTabs [data-baseweb="tab-list"] button {{
            border-radius: 8px 8px 0 0 !important;
            padding: 8px 18px !important;
        }}
        .stTabs button[aria-selected="true"] {{
            background-color: {SURFACE_2} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data
def _load_base64_image(path: Path):
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode()


def inject_background():
    """Applies Images/Page_BG.png as a full-page background with a dark
    overlay so text stays readable. Does nothing (no error) if the file
    hasn't been placed there yet."""
    encoded = _load_base64_image(BG_IMAGE_PATH)
    if encoded is None:
        return
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image:
                linear-gradient(rgba(13,14,16,{BG_OVERLAY_OPACITY}), rgba(13,14,16,{BG_OVERLAY_OPACITY})),
                url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center {BG_POSITION_Y};
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(title: str):
    """Top-of-page banner: Header_Banner.png as background with a
    left-to-right dark overlay so the title stays readable while the
    artwork on the right shows through."""
    encoded = _load_base64_image(HEADER_IMAGE_PATH)
    if encoded is None:
        st.markdown(f"<h1 style='color:{TEXT}; margin:0;'>{title}</h1>", unsafe_allow_html=True)
        return
    st.markdown(
        f"""
        <div style="
            background-image:
                linear-gradient(to right, rgba(13,14,16,0.6) 0%, rgba(13,14,16,0.15) 100%),
                url('data:image/png;base64,{encoded}');
            background-size: cover;
            background-position: {HEADER_POSITION_X} {HEADER_POSITION_Y};
            border-radius: 14px;
            padding: 0 28px;
            height: 96px;
            display: flex;
            align-items: center;
        ">
            <h1 style="margin:0; font-size:30px; font-weight:600; color:{TEXT};">{title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
