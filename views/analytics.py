import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db import delete_entries, get_categories, get_entries, update_entry
from theme import BORDER, CATEGORY_COLORS, NEGATIVE, POSITIVE, SURFACE, TEXT, TEXT_MUTED
from utils import format_rupiah


@st.dialog("Delete entries?")
def _confirm_delete_dialog(ids, labels):
    st.write(f"You're about to delete {len(ids)} entr{'y' if len(ids) == 1 else 'ies'}:")
    for label in labels:
        st.write(f"- {label}")
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True):
        st.rerun()
    if c2.button("Delete", use_container_width=True, type="primary"):
        delete_entries(ids)
        st.rerun()


@st.dialog("Edit entry")
def _edit_dialog(row, categories_df):
    new_item = st.text_input("Item", value=row["item"])
    new_date = st.date_input("Date", value=row["entry_date"].date())

    cat_names = categories_df["name"].tolist()
    current_cat_name = categories_df.loc[categories_df["id"] == row["category_id"], "name"].iloc[0]
    new_cat_name = st.selectbox("Category", cat_names, index=cat_names.index(current_cat_name))

    is_income_now = row["amount"] > 0
    direction = st.radio("Type", ["Expense", "Income"], index=1 if is_income_now else 0, horizontal=True)
    new_raw_amount = st.number_input(
        "Amount (Rp)", min_value=0, step=1000, value=int(abs(row["amount"]))
    )
    new_note = st.text_input("Note", value=row.get("note") or "")

    if st.button("Save changes", use_container_width=True):
        new_cat_id = int(categories_df.loc[categories_df["name"] == new_cat_name, "id"].iloc[0])
        signed = new_raw_amount if direction == "Income" else -new_raw_amount
        update_entry(int(row["id"]), new_item, new_date, new_cat_id, signed, new_note)
        st.rerun()


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

    filtered = filtered.reset_index(drop=True)

    display_df = filtered[["entry_date", "item", "category_name", "amount", "running_balance"]].copy()
    display_df["entry_date"] = display_df["entry_date"].dt.strftime("%Y-%m-%d")
    display_df["amount"] = display_df["amount"].apply(format_rupiah)
    display_df["running_balance"] = display_df["running_balance"].apply(format_rupiah)
    display_df.columns = ["Date", "Item", "Category", "Amount", "Running Balance"]

    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        key="entries_table",
    )
    selected_rows = event.selection.rows if event and event.selection else []

    action_l, action_r, _spacer = st.columns([1, 1, 4])
    with action_l:
        if st.button(
            "Edit selected", disabled=len(selected_rows) != 1, use_container_width=True
        ):
            categories_df = get_categories()
            _edit_dialog(filtered.iloc[selected_rows[0]], categories_df)
    with action_r:
        if st.button(
            f"Delete selected ({len(selected_rows)})",
            disabled=not selected_rows,
            use_container_width=True,
        ):
            picked = filtered.iloc[selected_rows]
            _confirm_delete_dialog(picked["id"].tolist(), picked["item"].tolist())