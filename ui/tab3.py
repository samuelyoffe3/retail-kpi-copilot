import streamlit as st
import pandas as pd
import altair as alt
from services import kpi_tab3

def render(items_df):
    """
    Renders Tab 3: Product Mix (תמהיל מוצרים).
    Final Version: Units Only, Chart First, Compact Table Second.
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
        
        /* Compact Table Style */
        .mix-row {
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #f5f5f5;
            direction: rtl;
            font-size: 0.95rem;
        }
        .mix-cat {
            flex: 2;
            font-weight: 500;
            color: #424242;
        }
        .mix-val {
            flex: 1;
            text-align: left; /* Align numbers to left for readability in RTL context sometimes, or keep right */
            text-align: left; 
            font-weight: 600;
            color: #212121;
        }
        .mix-pct {
            flex: 1;
            text-align: left;
            color: #757575;
            font-size: 0.85rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='text-align: right; direction: rtl;'>תמהיל מוצרים</h2>", unsafe_allow_html=True)

    if items_df is None or items_df.empty:
        st.info("אין נתוני פריטים להצגה.")
        return

    # --- CONTROL: Seller Selector ---
    # Default to "All Branch"
    all_sellers = sorted(list(items_df['seller_name'].unique()))
    options = ["כל הסניף"] + all_sellers
    
    # Simple selectbox
    selected_option = st.selectbox("בחר מוכר (אופציונלי):", options)
    
    # Map to service logic: service handles "הכל" or we interpret None.
    # We will pass specific name or 'None' if 'כל הסניף'
    seller_arg = selected_option if selected_option != "כל הסניף" else "הכל" 
    # Note: kpi_tab3.build_category_distribution line 86 checks: if seller_name and seller_name != "הכל"
    # So passing "הכל" is safe to get all data.

    # --- DATA PREP (Units Only) ---
    # 1. Distribution (for Chart & Compact Table)
    df_dist = kpi_tab3.build_category_distribution(items_df, metric="units", seller_name=seller_arg)
    
    if df_dist.empty:
        st.info("אין נתונים לקטגוריות הנבחרות.")
        return

    # --- 1. PIE CHART (Dominant) ---
    st.markdown("<div class='section-header'>התפלגות (כמות)</div>", unsafe_allow_html=True)
    
    base = alt.Chart(df_dist).encode(
        theta=alt.Theta("value", stack=True)
    )
    
    pie = base.mark_arc(outerRadius=100, innerRadius=40).encode(
        color=alt.Color("category", legend=alt.Legend(title="קטגוריה", orient='bottom', columns=2)),
        order=alt.Order("value", sort="descending"),
        tooltip=["category", "value"]
    )
    
    text = base.mark_text(radius=130).encode(
        text=alt.Text("value", format=".0f"),
        order=alt.Order("value", sort="descending"),
        color=alt.value("black")
    )
    
    st.altair_chart(pie + text, use_container_width=True)


    # --- 2. COMPACT BREAKDOWN TABLE ---
    # Calculate percentages
    total_val = df_dist['value'].sum()
    df_chart = df_dist.copy()
    df_chart['percent'] = (df_chart['value'] / total_val * 100) if total_val > 0 else 0
    
    st.markdown("<div style='margin-bottom: 10px;'></div>", unsafe_allow_html=True)
    
    # Render Header
    st.markdown("""
    <div class='mix-row' style='background-color:#f9f9f9; padding:5px; font-weight:bold;'>
        <div class='mix-cat'>קטגוריה</div>
        <div class='mix-pct'>אחוז</div>
        <div class='mix-val'>כמות</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render Rows
    for _, row in df_chart.iterrows():
        cat = row['category']
        val = int(row['value'])
        pct = f"{row['percent']:.1f}%"
        
        st.markdown(f"""
        <div class='mix-row'>
            <div class='mix-cat'>{cat}</div>
            <div class='mix-pct'>{pct}</div>
            <div class='mix-val'>{val}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown(f"""
    <div class='mix-row' style='border-top: 2px solid #eee; font-weight:bold;'>
        <div class='mix-cat'>סה"כ</div>
        <div class='mix-pct'>100%</div>
        <div class='mix-val'>{int(total_val)}</div>
    </div>
    """, unsafe_allow_html=True)


    # --- 3. EXPANDER: FULL PIVOT TABLE ---
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    with st.expander("הצג טבלה מלאה לפי עובדים"):
        # Always Units
        pivot = kpi_tab3.build_category_pivot(items_df, metric="units")
        if not pivot.empty:
             st.dataframe(pivot, use_container_width=True)
        else:
             st.info("אין נתונים בטבלה.")
