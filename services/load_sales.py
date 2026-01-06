import pandas as pd
import streamlit as st

# Hebrew to Internal Column Mapping
# Using a list of potential names for flexibility if needed, 
# but sticking to strict mapping where possible.
COLUMN_MAP = {
    "עסקה": "transaction_id",
    "תאריך": "date",
    "סה'כ לשורה": "line_amount",
    "כמות": "qty",
    "שם מוכרן": "seller_name",
    "תאור מוצר": "product_desc"
}

# Variable column names (handle "מוכרן" vs "מספר מוכרן")
SELLER_ID_ALIASEs = ["מוכרן", "מספר מוכרן"]

REQUIRED_COLUMNS = list(COLUMN_MAP.keys()) 
# Note: We will manually check for one of the seller_id aliases

def load_and_normalize_sales(file_content):
    """
    Loads sales data from a bytes buffer (Excel), normalizes column names,
    and performs basic type conversion.
    """
    try:
        # Load using Calamine engine for better compatibility
        df = pd.read_excel(file_content, engine='calamine')
        
        # 1. Normalize Seller ID column
        # Find which alias exists
        found_seller_id_col = None
        for alias in SELLER_ID_ALIASEs:
            if alias in df.columns:
                found_seller_id_col = alias
                break
        
        if found_seller_id_col:
            df = df.rename(columns={found_seller_id_col: "seller_id"})
        else:
            st.error(f"שגיאה: עמודת מס' מוכרן חסרה (חיפשנו: {SELLER_ID_ALIASEs})")
            return None

        # 2. Check for other required columns
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing_cols:
            error_msg = f"שגיאה: העמודות הבאות חסרות בקובץ SALES: {', '.join(missing_cols)}"
            st.error(error_msg)
            return None

        # 3. Rename remaining columns
        df = df.rename(columns=COLUMN_MAP)

        # 4. Type conversion
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df['line_amount'] = pd.to_numeric(df['line_amount'], errors='coerce').fillna(0)
        df['qty'] = pd.to_numeric(df['qty'], errors='coerce').fillna(0)
        
        # Drop rows with invalid dates (optional, but protects math)
        df = df.dropna(subset=['date'])

        return df

    except Exception as e:
        st.error(f"שגיאה בטעינת קובץ מכירות: {e}")
        return None
