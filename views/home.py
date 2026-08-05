import pandas as pd
import streamlit as st

from db import get_entries
from utils import format_rupiah


def render():
    df = get_entries()
    if df.empty:
        st.info("No entries yet. Head to Add Expense to log your first one.")
        return

    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["month"] = df["entry_date"].dt.to_period("M").astype(str)

    balance = df["amount"].sum()
    st.markdown(
        f"<p class='balance-label'>Current balance</p>"
        f"<p class='balance-value'>{format_rupiah(balance)}</p>",
        unsafe_allow_html=True,
    )

    this_period = pd.Period(pd.Timestamp.today(), freq="M")
    this_month = str(this_period)
    prev_month = str(this_period - 1)

    def month_stats(month):
        md = df[df["month"] == month]
        income = md[md["is_income"]]["amount"].sum()
        spent = -md[~md["is_income"]]["amount"].sum()
        return income, spent, income - spent

    def pct_delta(cur, prev):
        if not prev:
            return None
        return (cur - prev) / abs(prev) * 100

    income, spent, saved = month_stats(this_month)
    p_income, p_spent, p_saved = month_stats(prev_month)

    d_income = pct_delta(income, p_income)
    d_spent = pct_delta(spent, p_spent)
    d_saved = pct_delta(saved, p_saved)

    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Income this month",
        format_rupiah(income),
        delta=f"{d_income:+.0f}% vs last month" if d_income is not None else None,
    )
    c2.metric(
        "Spent this month",
        format_rupiah(spent),
        delta=f"{d_spent:+.0f}% vs last month" if d_spent is not None else None,
        delta_color="inverse",
    )
    c3.metric(
        "Saved this month",
        format_rupiah(saved),
        delta=f"{d_saved:+.0f}% vs last month" if d_saved is not None else None,
    )

    month_df = df[df["month"] == this_month]
    expenses = month_df[~month_df["is_income"]]
    if not expenses.empty:
        by_cat = expenses.groupby("category_name")["amount"].sum().abs()
        top_cat = by_cat.idxmax()
        st.caption(f"Biggest category this month: {top_cat} \u00b7 {format_rupiah(by_cat.max())}")

    st.write("")
