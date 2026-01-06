import pandas as pd
import numpy as np

# Whitelist Categories (Exact)
WHITELIST_CATEGORIES = [
    "הנעלה",
    "ביגוד",
    "גרביים",
    "תיקים",
    "כדורים",
    "כובעים",
    "ציוד ותכשירי ניקוי",
    "תחתונים"
]

def clean_category(cat):
    """Normalize category string."""
    if not isinstance(cat, str):
        return ""
    return cat.strip().replace('"', '').replace("'", "")

def filter_whitelist(df):
    """Keeps only rows with whitelisted categories."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    df = df.copy()
    df['clean_cat'] = df['category_param12'].apply(clean_category)
    return df[df['clean_cat'].isin(WHITELIST_CATEGORIES)]

def build_category_pivot(items_df, metric="units"):
    """
    Builds a pivot table: Row=Seller, Col=Category, Val=Sum(Metric).
    Adds 'Total' column and sorts.
    """
    if items_df is None or items_df.empty:
        return pd.DataFrame()

    # Filter
    df = filter_whitelist(items_df)
    if df.empty:
        return pd.DataFrame()

    # Pivot
    # metric should be 'units' or 'revenue'
    pivot = df.pivot_table(
        index='seller_name', 
        columns='clean_cat', 
        values=metric, 
        aggfunc='sum', 
        fill_value=0
    )

    # Ensure all whitelist columns exist (even if 0)
    for cat in WHITELIST_CATEGORIES:
        if cat not in pivot.columns:
            pivot[cat] = 0

    # Sort columns by Whitelist order (optional, but good for consistency)
    pivot = pivot[WHITELIST_CATEGORIES]

    # Add Total Column
    pivot['סה"כ פריטים'] = pivot.sum(axis=1)

    # Sort Rows by Total descending
    pivot = pivot.sort_values('סה"כ פריטים', ascending=False)

    # ADD TOTAL ROW
    # Sum all columns
    total_row = pivot.sum(axis=0)
    pivot.loc['סה"כ'] = total_row

    return pivot

def build_category_distribution(items_df, metric="units", seller_name=None):
    """
    Aggregates data for Pie Chart.
    """
    if items_df is None or items_df.empty:
        return pd.DataFrame()

    # Filter Whitelist
    df = filter_whitelist(items_df)
    
    # Filter by Seller if specific one selected (and not 'All')
    if seller_name and seller_name != "הכל":
        df = df[df['seller_name'] == seller_name]
    
    if df.empty:
        return pd.DataFrame(columns=['category', 'value'])

    # Group
    dist = df.groupby('clean_cat')[metric].sum().reset_index()
    dist.columns = ['category', 'value']
    
    # Sort by value
    dist = dist.sort_values('value', ascending=False)
    
    return dist
