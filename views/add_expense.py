from datetime import date

import streamlit as st

from db import add_entry, get_categories, get_current_balance
from theme import POSITIVE, TEXT
from utils import format_currency


@st.dialog("Entry saved")
def _saved_dialog(item, signed_amount, category_name, entry_date, current_user, payment_method=None):
    st.write(f"**{item}**")
    caption = f"{category_name} \u00b7 {entry_date}"
    if payment_method:
        caption += f" \u00b7 {payment_method}"
    st.caption(caption)
    color = POSITIVE if signed_amount > 0 else TEXT
    st.markdown(
        f"<p style='font-family:\"JetBrains Mono\", monospace; font-size:26px; "
        f"font-weight:500; color:{color}; margin: 8px 0 18px;'>"
        f"{'+' if signed_amount > 0 else '-'}{format_currency(abs(signed_amount), current_user)}</p>",
        unsafe_allow_html=True,
    )
    if st.button("Done", use_container_width=True):
        st.rerun()


def render(current_user: str):
    st.metric("Current balance", format_currency(get_current_balance(current_user), current_user))

    categories = get_categories()

    with st.form("add_entry_form", clear_on_submit=True):
        item = st.text_input("Item")
        entry_date = st.date_input("Date", value=date.today())
        cat_row = st.selectbox(
            "Category",
            options=list(categories.itertuples()),
            format_func=lambda r: r.name,
        )
        direction = st.radio("Type", ["Expense", "Income"], horizontal=True)

        payment_method = None
        if current_user == "jpy":
            payment_method = st.radio("Payment Method", ["Card", "Cash"], horizontal=True)

        currency_symbol = "\u00a5" if current_user == "jpy" else "Rp"
        raw_amount = st.number_input(
            f"Amount ({currency_symbol})",
            min_value=0,
            step=1000,
            value=None,
            placeholder="0",
        )
        note = st.text_input("Note (optional)")
        submitted = st.form_submit_button("Save")

        if submitted:
            if not item or not raw_amount:
                st.error("Fill in item and amount.")
            else:
                signed = raw_amount if direction == "Income" else -raw_amount
                add_entry(item, entry_date, cat_row.id, signed, current_user, note, payment_method)
                _saved_dialog(item, signed, cat_row.name, entry_date, current_user, payment_method)