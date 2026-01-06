import pandas as pd
import streamlit as st

# Hebrew to Internal Column Mapping for Items
COLUMN_MAP = {
    "תאור פרמטר 12 למוצר": "category_param12",
    "כמות פריטים": "units",
    "שם מוכרן": "seller_name",
    "סכום לתשלום כולל מעם": "revenue",
    "מספר עסקאות": "transactions"
}

SELLER_ID_ALIASES = ["מוכרן", "מספר מוכרן", "קוד מוכרן"]

# Required: Category, Units, Seller Name. 
# Revenue/Transactions are optional (fill with 0 if missing).
REQUIRED_COLUMNS = ["category_param12", "units", "seller_name"] 

def load_and_normalize_items(file_content):
    """
    Loads items data from a bytes buffer (Excel), normalizes column names.
    """
    try:
        df = pd.read_excel(file_content, engine='calamine')
        
        # 1. Normalize Seller ID
        found_seller_id_col = None
        for alias in SELLER_ID_ALIASES:
            if alias in df.columns:
                found_seller_id_col = alias
                break
        
        if found_seller_id_col:
            df = df.rename(columns={found_seller_id_col: "seller_id"})
        else:
            st.error(f"שגיאה: עמודת מס' מוכרן חסרה בקובץ ITEMS (חיפשנו: {SELLER_ID_ALIASES})")
            return None

        # 2. Check Missing Columns (Required Only)
        # We check locally against the mapped names if we were to map them...
        # But pandas rename doesn't fail if key missing, it just stays same.
        # So we check raw names.
        
        # Invert map to check raw names
        RAW_REQUIRED = []
        for internal in REQUIRED_COLUMNS:
            # find raw key for internal
            for raw, inter in COLUMN_MAP.items():
                if inter == internal:
                    RAW_REQUIRED.append(raw)
                    break 

        missing_cols = [col for col in RAW_REQUIRED if col not in df.columns]
        if missing_cols:
            error_msg = f"שגיאה: העמודות הבאות חסרות בקובץ ITEMS: {', '.join(missing_cols)}"
            st.error(error_msg)
            return None

        # 3. Rename
        df = df.rename(columns=COLUMN_MAP)

        # 4. Fill Missing Optional Columns
        if "revenue" not in df.columns:
            df["revenue"] = 0.0
        if "transactions" not in df.columns:
            df["transactions"] = 0

        # 5. Cleanup
        df['units'] = pd.to_numeric(df['units'], errors='coerce').fillna(0)
        df['revenue'] = pd.to_numeric(df['revenue'], errors='coerce').fillna(0)
        # Ensure category is string
        df['category_param12'] = df['category_param12'].astype(str)

        return df

    except Exception as e:
        st.error(f"שגיאה בטעינת קובץ פריטים: {e}")
        return None
