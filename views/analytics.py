import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db import get_entries
from theme import BORDER, CATEGORY_COLORS, NEGATIVE, SURFACE, TEXT, TEXT_MUTED
from utils import format_rupiah


def render():
    df = get_entries()
    if df.empty:
        st.info("No entries yet. Add some from the Add Expense tab.")
        return

    df["entry_date"] = pd.to_datetime(df["entry_date"])
    df["month"] = df["entry_date"].dt.to_period("M").astype(str)

    months = sorted(df["month"].unique(), reverse=True)
    selected_month = st.selectbox(
        "Month",
        months,
        format_func=lambda m: pd.Period(m, freq="M").strftime("%b %Y"),
    )

    month_df = df[df["month"] == selected_month]
    expenses = month_df[~month_df["is_income"]]
    income = month_df[month_df["is_income"]]["amount"].sum()
    total_spent = -expenses["amount"].sum()
    saved = income - total_spent

    c1, c2, c3 = st.columns(3)
    c1.metric("Income", format_rupiah(income))
    c2.metric("Spent", format_rupiah(total_spent))
    c3.metric("Saved", format_rupiah(saved))

    if not expenses.empty:
        by_cat = expenses.groupby("category_name")["amount"].sum().abs().sort_values(ascending=True)
        pct = (by_cat / by_cat.sum() * 100).round(1)
        colors = [CATEGORY_COLORS.get(c, TEXT_MUTED) for c in by_cat.index]

        fig = go.Figure(
            go.Bar(
                x=by_cat.values,
                y=by_cat.index,
                orientation="h",
                marker_color=colors,
                customdata=pct.values,
                hovertemplate="<b>%{y}</b><br>" + "%{text}<br>%{customdata}% of spending<extra></extra>",
                text=[format_rupiah(v) for v in by_cat.values],
                textposition="outside",
                textfont=dict(color=TEXT, size=12),
            )
        )
        fig.update_layout(
            plot_bgcolor=SURFACE,
            paper_bgcolor=SURFACE,
            font=dict(color=TEXT, family="Inter"),
            margin=dict(l=0, r=90, t=10, b=10),
            xaxis=dict(showgrid=True, gridcolor=BORDER, zeroline=False, title=None),
            yaxis=dict(showgrid=False, title=None),
            height=320,
            hoverlabel=dict(bgcolor=TEXT, font_color="#0D0E10"),
            showlegend=False,
            separators=",.",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Trend across months")
    trend = (
        df.groupby("month")
        .apply(
            lambda g: pd.Series(
                {
                    "income": g[g["is_income"]]["amount"].sum(),
                    "spent": -g[~g["is_income"]]["amount"].sum(),
                }
            )
        )
        .reset_index()
    )
    trend["month_label"] = trend["month"].apply(lambda m: pd.Period(m, freq="M").strftime("%b %Y"))

    fig2 = go.Figure()
    fig2.add_trace(
        go.Scatter(
            x=trend["month_label"],
            y=trend["income"],
            name="Income",
            mode="lines+markers",
            line=dict(color=CATEGORY_COLORS["Income"], width=2),
            text=[format_rupiah(v) for v in trend["income"]],
            hovertemplate="%{text}<extra>Income</extra>",
        )
    )
    fig2.add_trace(
        go.Scatter(
            x=trend["month_label"],
            y=trend["spent"],
            name="Spent",
            mode="lines+markers",
            line=dict(color=NEGATIVE, width=2),
            text=[format_rupiah(v) for v in trend["spent"]],
            hovertemplate="%{text}<extra>Spent</extra>",
        )
    )
    fig2.update_layout(
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(color=TEXT, family="Inter"),
        margin=dict(l=0, r=0, t=10, b=10),
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=True, gridcolor=BORDER, title=None),
        legend=dict(orientation="h", y=1.15, font=dict(color=TEXT_MUTED)),
        hoverlabel=dict(bgcolor=TEXT, font_color="#0D0E10"),
        separators=",.",
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("All entries this month")

    search_col, cat_col, type_col = st.columns(3)
    with search_col:
        search_term = st.text_input(
            "Search", placeholder="Search by item...", label_visibility="collapsed"
        )
    with cat_col:
        cat_options = sorted(month_df["category_name"].dropna().unique())
        selected_cats = st.multiselect(
            "Category", cat_options, placeholder="All categories", label_visibility="collapsed"
        )
    with type_col:
        type_filter = st.selectbox(
            "Type", ["All", "Income", "Expense"], label_visibility="collapsed"
        )

    filtered = month_df.copy()
    if search_term:
        filtered = filtered[filtered["item"].str.contains(search_term, case=False, na=False)]
    if selected_cats:
        filtered = filtered[filtered["category_name"].isin(selected_cats)]
    if type_filter == "Income":
        filtered = filtered[filtered["is_income"]]
    elif type_filter == "Expense":
        filtered = filtered[~filtered["is_income"]]

    display_df = filtered[["entry_date", "item", "category_name", "amount", "running_balance"]].copy()
    display_df["entry_date"] = display_df["entry_date"].dt.strftime("%Y-%m-%d")
    display_df["amount"] = display_df["amount"].apply(format_rupiah)
    display_df["running_balance"] = display_df["running_balance"].apply(format_rupiah)
    display_df.columns = ["Date", "Item", "Category", "Amount", "Running Balance"]
    st.dataframe(display_df, use_container_width=True)
