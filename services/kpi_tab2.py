import pandas as pd
import numpy as np

def get_seller_table(sales_df, items_df):
    """
    Builds the seller performance table.
    """
    if sales_df is None or sales_df.empty:
        return pd.DataFrame()

    # --- 1. Valid Transactions per Seller (from SALES) ---
    # Group by [transaction_id, seller_id] -> sum(line_amount)
    # Filter net_amount > 0
    txn_groups = sales_df.groupby(['transaction_id', 'seller_id'])['line_amount'].sum()
    valid_txns = txn_groups[txn_groups > 0].reset_index()
    
    # Count valid transactions per seller
    seller_txns_count = valid_txns.groupby('seller_id').size().rename('transactions')
    
    # Sum valid transaction amounts per seller (Net Sales)
    seller_sales_amount = valid_txns.groupby('seller_id')['line_amount'].sum().rename('sales')

    # --- 2. Seller Units (Average Items Denominator) ---
    # Sum positive qty only
    pos_qty_df = sales_df[sales_df['qty'] > 0]
    seller_units = pos_qty_df.groupby('seller_id')['qty'].sum().rename('total_units')
    
    # --- 3. Complement Numerator (from ITEMS) ---
    # Exclude categories: "הנעלה", "ביגוד", "הנה", "מתכל"
    if items_df is not None and not items_df.empty:
        def is_excluded(cat):
            cat = str(cat).strip().replace('"', '').replace("'", "")
            if cat == "הנעלה" or cat == "ביגוד":
                return True
            if "הנה" in cat: # Catches הנה"ח etc
                return True
            if "מתכל" in cat:
                return True
            return False

        # Filter items
        valid_items_mask = ~items_df['category_param12'].apply(is_excluded)
        complement_df = items_df[valid_items_mask]
        seller_complement_units = complement_df.groupby('seller_id')['units'].sum().rename('complement_units')
    else:
        seller_complement_units = pd.Series(dtype=float)

    # --- 4. Merge Everything ---
    # We use sales_df to get unique seller names mapping
    seller_names = sales_df[['seller_id', 'seller_name']].drop_duplicates('seller_id').set_index('seller_id')['seller_name']
    
    # Base is sellers who have sales
    df = pd.DataFrame(index=seller_sales_amount.index)
    df = df.join(seller_names).join(seller_sales_amount).join(seller_txns_count).join(seller_units).join(seller_complement_units)
    
    # Fill NAs
    df['sales'] = df['sales'].fillna(0)
    df['transactions'] = df['transactions'].fillna(0)
    df['total_units'] = df['total_units'].fillna(0)
    df['complement_units'] = df['complement_units'].fillna(0)

    # Calculate Averages and Ratios
    # Avoid division by zero
    df['avg_transaction'] = df.apply(lambda x: x['sales'] / x['transactions'] if x['transactions'] > 0 else 0, axis=1)
    df['avg_items'] = df.apply(lambda x: x['total_units'] / x['transactions'] if x['transactions'] > 0 else 0, axis=1)
    df['complement_ratio'] = df.apply(lambda x: x['complement_units'] / x['transactions'] if x['transactions'] > 0 else 0, axis=1)

    # Format and Select Columns
    # Need to match strict output columns:
    # "שם מוכר", "מכירות", "מספר עסקאות", "ממוצע עסקה", "ממוצע פריטים לעסקה", "יחס מוצר משלים לעסקה"
    
    result = df.reset_index()
    result = result.rename(columns={
        "seller_name": "שם מוכר",
        "sales": "מכירות",
        "transactions": "מספר עסקאות",
        "avg_transaction": "ממוצע עסקה",
        "avg_items": "ממוצע פריטים לעסקה",
        "complement_ratio": "יחס מוצר משלים לעסקה"
    })
    
    # Sort
    result = result.sort_values("מכירות", ascending=False)
    
    return result[[
        "שם מוכר", "מכירות", "מספר עסקאות", "ממוצע עסקה", "ממוצע פריטים לעסקה", "יחס מוצר משלים לעסקה"
    ]]


def get_top_products_qty(sales_df):
    """
    Top 5 products by Quantity (qty > 0).
    """
    if sales_df is None or sales_df.empty:
        return pd.DataFrame()
        
    # Filter positive quantity
    df = sales_df[sales_df['qty'] > 0]
    
    # Group
    grouped = df.groupby('product_desc')['qty'].sum().reset_index()
    
    # Top 5
    top5 = grouped.sort_values('qty', ascending=False).head(5)
    
    # Rename
    top5 = top5.rename(columns={"product_desc": "תיאור מוצר", "qty": "כמות"})
    
    return top5


def get_top_products_amount(sales_df):
    """
    Top 5 products by Amount (sum line_amount).
    """
    if sales_df is None or sales_df.empty:
        return pd.DataFrame()
        
    # Group (use all lines, netting happens naturally by summation here or usually just sum amount)
    # Prompt says: "amount_sum = sum(line_amount)"
    grouped = sales_df.groupby('product_desc')['line_amount'].sum().reset_index()
    
    # Top 5
    top5 = grouped.sort_values('line_amount', ascending=False).head(5)
    
    # Rename
    top5 = top5.rename(columns={"product_desc": "תיאור מוצר", "line_amount": "סכום"})
    
    return top5
