import streamlit as st
import pandas as pd

def render(df_sellers, df_top_qty, df_top_amount):
    """
    Renders Tab 2: Team & Sales (צוות ומכירות).
    Polished for Mobile-First, RTL, and Readability.
    """
    # --- CSS Styles ---
    st.markdown("""
        <style>
        .rtl-container {
            direction: rtl;
            text-align: right;
        }
        .section-header {
            color: #1565c0;
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 25px;
            margin-bottom: 10px;
            text-align: right;
            direction: rtl;
            border-bottom: 1px solid #eee;
            padding-bottom: 5px;
        }
        
        /* Seller Card Style */
        .seller-card {
            background-color: #fff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            direction: rtl;
            text-align: right;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        .seller-name {
            font-size: 1rem;
            font-weight: 700;
            color: #212121;
            margin-bottom: 4px;
        }
        .seller-row {
            display: flex;
            justify-content: space-between;
            color: #424242;
            font-size: 0.85rem;
            margin-bottom: 2px;
        }
        .seller-highlight {
            color: #1565c0; /* Blue */
            font-weight: 600;
            font-size: 0.85rem;
            margin-top: 4px;
        }
        
        /* Compact List Style */
        .compact-list-row {
            display: flex;
            justify-content: space-between;
            padding: 6px 0;
            border-bottom: 1px solid #f5f5f5;
            direction: rtl;
            font-size: 0.9rem;
        }
        .list-name {
            flex: 2;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding-left: 10px;
        }
        .list-val {
            flex: 1;
            text-align: left;
            font-weight: 600;
            color: #424242;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: right; direction: rtl;'>צוות ומכירות</h2>", unsafe_allow_html=True)

    if df_sellers.empty:
        st.info("אין נתונים להצגה.")
        return

    # --- CONTROLS ---
    c1, c2, c3 = st.columns([2, 2, 1])
    
    with c1:
        # Sort Options
        sort_opts = {
            "מכירות": "מכירות",
            "מספר עסקאות": "מספר עסקאות",
            "יחס מוצר משלים": "יחס מוצר משלים לעסקה"
        }
        # Reverse mapping for dataframe sort
        sort_col_map = {v: k for k, v in sort_opts.items()}
        
        sort_choice = st.selectbox("מיון לפי", list(sort_opts.keys()))
        sort_col = sort_opts[sort_choice]
        
    with c2:
        search_term = st.text_input("חיפוש מוכר", "")
        
    with c3:
        # View Toggle (Default to True/Cards for mobile feel)
        card_view = st.toggle("תצוגת כרטיסים", value=True)

    # --- FILTER & SORT ---
    df_display = df_sellers.copy()
    
    # Search
    if search_term:
        df_display = df_display[df_display['שם מוכר'].astype(str).str.contains(search_term, case=False)]
    
    # Sort (Always Descending for these metrics)
    if sort_col in df_display.columns:
        df_display = df_display.sort_values(sort_col, ascending=False)

    # --- SELLER LIST RENDER ---
    st.markdown("<div class='section-header'>ביצועי עובדים</div>", unsafe_allow_html=True)
    
    if card_view:
        # CARD VIEW (Mobile First)
        for _, row in df_display.iterrows():
            # Format values
            sales = f"₪{row['מכירות']:,.0f}"
            txns = int(row['מספר עסקאות'])
            avg_t = f"₪{row['ממוצע עסקה']:,.0f}"
            avg_i = f"{row['ממוצע פריטים לעסקה']:.1f}"
            ratio = f"{row['יחס מוצר משלים לעסקה']:.2f}"
            
            st.markdown(f"""
            <div class='seller-card'>
                <div class='seller-name'>{row['שם מוכר']}</div>
                <div class='seller-row'>
                    <span>מכירות: <b>{sales}</b></span>
                    <span>עסקאות: <b>{txns}</b></span>
                </div>
                <div class='seller-row'>
                    <span>ממוצע עסקה: <b>{avg_t}</b></span>
                    <span>ממוצע פריטים: <b>{avg_i}</b></span>
                </div>
                <div class='seller-highlight'>יחס משלים: {ratio}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # TABLE VIEW (Desktop)
        # Format for display
        tbl = df_display.copy()
        
        # Format columns (Strings for display)
        tbl["מכירות"] = tbl["מכירות"].apply(lambda x: f"₪{x:,.0f}")
        tbl["ממוצע עסקה"] = tbl["ממוצע עסקה"].apply(lambda x: f"₪{x:,.0f}")
        tbl["מספר עסקאות"] = tbl["מספר עסקאות"].apply(lambda x: int(x))
        tbl["ממוצע פריטים לעסקה"] = tbl["ממוצע פריטים לעסקה"].apply(lambda x: f"{x:.1f}")
        tbl["יחס מוצר משלים לעסקה"] = tbl["יחס מוצר משלים לעסקה"].apply(lambda x: f"{x:.2f}")

        st.dataframe(
            tbl, 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "שם מוכר": st.column_config.TextColumn("שם מוכר"),
                # Adjust column widths or labels if strictly needed, 
                # but dataframe is usually okay.
            }
        )

    # --- TOP 5 LISTS ---
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    
    col_q, col_a = st.columns(2)
    
    def render_compact_list(title, df, label_col, val_col, fmt_func):
        html = f"<div class='section-header'>{title}</div>"
        if df.empty:
            html += "<div style='text-align:right'>אין נתונים</div>"
        else:
            for _, row in df.head(5).iterrows():
                val = fmt_func(row[val_col])
                name = row[label_col]
                # Construct HTML without indentation to avoid Markdown code block interpretation
                html += f"<div class='compact-list-row'><div class='list-name' title='{name}'>{name}</div><div class='list-val'>{val}</div></div>"
        return html

    with col_q:
        html = render_compact_list(
            "טופ 5 לפי כמות", 
            df_top_qty, 
            "תיאור מוצר", 
            "כמות", 
            lambda x: f"{int(x)}"
        )
        st.markdown(html, unsafe_allow_html=True)

    with col_a:
        html = render_compact_list(
            "טופ 5 לפי סכום", 
            df_top_amount, 
            "תיאור מוצר", 
            "סכום", 
            lambda x: f"₪{x:,.0f}"
        )
        st.markdown(html, unsafe_allow_html=True)
