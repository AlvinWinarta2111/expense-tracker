import streamlit as st
import pandas as pd
from supabase import create_client, Client


@st.cache_resource
def get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def get_categories(include_archived: bool = False) -> pd.DataFrame:
    sb = get_client()
    q = sb.table("categories").select("*").order("sort_order")
    if not include_archived:
        q = q.eq("archived", False)
    res = q.execute()
    return pd.DataFrame(res.data)


def add_entry(item: str, entry_date, category_id: int, amount: float, note: str = ""):
    sb = get_client()
    sb.table("entries").insert(
        {
            "item": item,
            "entry_date": str(entry_date),
            "category_id": category_id,
            "amount": amount,
            "note": note,
        }
    ).execute()


def get_entries(start=None, end=None) -> pd.DataFrame:
    sb = get_client()
    q = (
        sb.table("entries")
        .select("*, categories(name,is_income,color)")
        .order("entry_date")
        .order("id")
    )
    if start:
        q = q.gte("entry_date", str(start))
    if end:
        q = q.lte("entry_date", str(end))
    res = q.execute()
    df = pd.DataFrame(res.data)
    if df.empty:
        return df
    df["category_name"] = df["categories"].apply(lambda c: c["name"] if c else None)
    df["is_income"] = df["categories"].apply(lambda c: c["is_income"] if c else None)
    df = df.drop(columns=["categories"])
    df["running_balance"] = df["amount"].cumsum()
    return df


def get_current_balance() -> float:
    df = get_entries()
    if df.empty:
        return 0.0
    return float(df["amount"].sum())


def delete_entries(ids: list):
    if not ids:
        return
    sb = get_client()
    sb.table("entries").delete().in_("id", ids).execute()


def update_entry(entry_id: int, item: str, entry_date, category_id: int, amount: float, note: str = ""):
    sb = get_client()
    sb.table("entries").update(
        {
            "item": item,
            "entry_date": str(entry_date),
            "category_id": category_id,
            "amount": amount,
            "note": note,
        }
    ).eq("id", entry_id).execute()