import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from db import delete_entries, get_categories, get_entries, update_entry
from theme import BORDER, CATEGORY_COLORS, NEGATIVE, SURFACE, TEXT, TEXT_MUTED
from utils import format_currency


@st.dialog("Delete entries?")
def _confirm_delete_dialog(ids, labels, current_user):
    st.write(f"You're about to delete {len(ids)} entr{'y' if len(ids) == 1 else 'ies'}:")
    for label in labels:
        st.write(f"- {label}")
    c1, c2 = st.columns(2)
    if c1.button("Cancel", use_container_width=True):
        st.rerun()
    if c2.button("Delete", use_container_width=True, type="primary"):
        delete_entries(ids, current_user)
        st.rerun()


@st.dialog("Edit entry")
def _edit_dialog(row, categories_df, current_user):
    new_item = st.text_input("Item", value=row["item"])
    new_date = st.date_input("Date", value=row["entry_date"].date())

    cat_names = categories_df["name"].tolist()
    current_cat_name = categories_df.loc[categories_df["id"] == row["category_id"], "name"].iloc[0]
    new_cat_name = st.selectbox("Category", cat_names, index=cat_names.index(current_cat_name))

    is_income_now = row["amount"] > 0
    direction = st.radio("Type", ["Expense", "Income"], index=1 if is_income_now else 0, horizontal=True)

    new_payment_method = None
    if current_user == "jpy":
        pm_options = ["Card", "Cash"]
        current_pm = row.get("payment_method") if row.get("payment_method") in pm_options else "Cash"
        new_payment_method = st.radio(
            "Payment Method", pm_options, index=pm_options.index(current_pm), horizontal=True
        )

    currency_symbol = "\u00a5" if current_user == "jpy" else "Rp"
    new_raw_amount = st.number_input(
        f"Amount ({currency_symbol})", min_value=0, step=1000, value=int(abs(row["amount"]))
    )
    new_note = st.text_input("Note", value=row.get("note") or "")

    if st.button("Save changes", use_container_width=True):
        new_cat_id = int(categories_df.loc[categories_df["name"] == new_cat_name, "id"].iloc[0])
        signed = new_raw_amount if direction == "Income" else -new_raw_amount
        update_entry(
            int(row["id"]), new_item, new_date, new_cat_id, signed, current_user, new_note, new_payment_method
        )
        st.rerun()


def render(current_user: str):
    is_jpy = current_user == "jpy"

    df = get_entries(current_user)
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
    c1.metric("Income", format_currency(income, current_user))
    c2.metric("Spent", format_currency(total_spent, current_user))
    c3.metric("Saved", format_currency(saved, current_user))

    separators = ".," if is_jpy else ",."

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
                text=[format_currency(v, current_user) for v in by_cat.values],
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
            separators=separators,
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
            text=[format_currency(v, current_user) for v in trend["income"]],
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
            text=[format_currency(v, current_user) for v in trend["spent"]],
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
        separators=separators,
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("All entries this month")

    if is_jpy:
        search_col, cat_col, pm_col, type_col = st.columns(4)
    else:
        search_col, cat_col, type_col = st.columns(3)
        pm_col = None

    with search_col:
        search_term = st.text_input(
            "Search", placeholder="Search by item...", label_visibility="collapsed"
        )
    with cat_col:
        cat_options = sorted(month_df["category_name"].dropna().unique())
        selected_cats = st.multiselect(
            "Category", cat_options, placeholder="All categories", label_visibility="collapsed"
        )
    pm_filter = "All"
    if is_jpy:
        with pm_col:
            pm_filter = st.selectbox(
                "Payment Method", ["All", "Card", "Cash"], label_visibility="collapsed"
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
    if is_jpy and pm_filter != "All":
        filtered = filtered[filtered["payment_method"] == pm_filter]
    if type_filter == "Income":
        filtered = filtered[filtered["is_income"]]
    elif type_filter == "Expense":
        filtered = filtered[~filtered["is_income"]]

    filtered = filtered.reset_index(drop=True)

    cols = ["entry_date", "item", "category_name"]
    names = ["Date", "Item", "Category"]
    if is_jpy:
        cols.append("payment_method")
        names.append("Payment Method")
    cols += ["amount", "running_balance"]
    names += ["Amount", "Running Balance"]

    display_df = filtered[cols].copy()
    display_df["entry_date"] = display_df["entry_date"].dt.strftime("%Y-%m-%d")
    display_df["amount"] = display_df["amount"].apply(lambda v: format_currency(v, current_user))
    display_df["running_balance"] = display_df["running_balance"].apply(
        lambda v: format_currency(v, current_user)
    )
    display_df.columns = names

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
            _edit_dialog(filtered.iloc[selected_rows[0]], categories_df, current_user)
    with action_r:
        if st.button(
            f"Delete selected ({len(selected_rows)})",
            disabled=not selected_rows,
            use_container_width=True,
        ):
            picked = filtered.iloc[selected_rows]
            _confirm_delete_dialog(picked["id"].tolist(), picked["item"].tolist(), current_user)