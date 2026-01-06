import streamlit as st

def render(kpis):
    """
    Renders the Monthly Dashboard Tab (Tab 1) UI.
    Updated for Mobile-First, RTL, and Clean Design.
    """
    if not kpis:
        st.warning("אין נתונים להצגה.")
        return

    # Check for unconfigured target
    if kpis['target'] == 0:
        st.warning("שים לב: יעד חודשי לא מוגדר (מוצג כ-0).")

    # --- CSS Styles ---
    st.markdown("""
        <style>
        /* General RTL */
        .rtl-container {
            direction: rtl;
            text-align: right;
        }
        
        /* Metric Card Style */
        .kpi-card {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
            text-align: right;
            direction: rtl;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        
        .kpi-label {
            color: #757575; /* Gray */
            font-size: 0.85rem;
            font-weight: 500;
            margin-bottom: 5px;
        }
        
        .kpi-value {
            color: #212121; /* Dark Black */
            font-size: 1.4rem;
            font-weight: 700;
        }
        
        .kpi-subtext {
            color: #9e9e9e;
            font-size: 0.75rem;
            margin-top: 2px;
        }

        /* Color Modifiers */
        .val-green { color: #2e7d32 !important; } /* Green */
        .val-orange { color: #f57c00 !important; } /* Orange */
        .val-red { color: #d32f2f !important; } /* Red */
        
        /* Section Header */
        .section-header {
            color: #1565c0; /* Blue Heading */
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 20px;
            margin-bottom: 10px;
            text-align: right;
            direction: rtl;
            border-bottom: 2px solid #e3f2fd;
            padding-bottom: 5px;
        }
        
        /* Insight Box */
        .insight-box {
            background-color: #e3f2fd; /* Light Blue BG */
            color: #0d47a1;
            padding: 15px;
            border-radius: 8px;
            text-align: right;
            direction: rtl;
            border-right: 4px solid #1976d2;
            margin-top: 10px;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Data Prep ---
    target = kpis['target']
    actual = kpis['actual_to_date']
    pct_achieved = (actual / target * 100) if target > 0 else 0
    
    avg_daily_actual = kpis['avg_daily']
    avg_daily_required = kpis['required_daily']
    
    proj_amount = kpis['projected_amount']
    proj_pct = kpis['projected_percent']

    # --- Helper Functions ---
    def fmt_nis(val):
        return f"₪{val:,.0f}" # 1,234 (no decimals)

    def fmt_pct(val):
        return f"{val:.1f}%"

    def card_html(label, value, subtext="", color_class=""):
        return f"""
        <div class='kpi-card'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value {color_class}'>{value}</div>
            <div class='kpi-subtext'>{subtext}</div>
        </div>
        """

    # --- SECTION A: סטטוס חודשי ---
    st.markdown("<div class='section-header'>סטטוס חודשי</div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(card_html("יעד חודשי", fmt_nis(target)), unsafe_allow_html=True)
    
    with c2:
        st.markdown(card_html("מכירות עד היום", fmt_nis(actual)), unsafe_allow_html=True)
        
    with c3:
        # pct achieved logic (no color required here by requirements, but let's keep it clean)
        st.markdown(card_html("אחוז מהיעד", fmt_pct(pct_achieved)), unsafe_allow_html=True)


    # --- SECTION B: קצב ותחזית ---
    st.markdown("<div class='section-header'>קצב ותחזית</div>", unsafe_allow_html=True)
    
    c4, c5, c6 = st.columns(3)
    
    with c4:
        st.markdown(card_html("ממוצע יומי בפועל", fmt_nis(avg_daily_actual)), unsafe_allow_html=True)
        
    with c5:
        st.markdown(card_html("ממוצע יומי נדרש", fmt_nis(avg_daily_required)), unsafe_allow_html=True)
        
    with c6:
        # Color Logic for Projection
        p_color = "val-red"
        if proj_pct >= 100:
            p_color = "val-green"
        elif proj_pct >= 95:
            p_color = "val-orange"
            
        sub = f"צפי סיום: {fmt_pct(proj_pct)}"
        st.markdown(card_html("תחזית סיום חודש", fmt_nis(proj_amount), sub, p_color), unsafe_allow_html=True)


    # --- SECTION C: מה עושים היום ---
    st.markdown("<div class='section-header'>מה עושים היום</div>", unsafe_allow_html=True)
    
    if proj_pct >= 100:
        insight = "אנחנו בקצב טוב. לשמור על יציבות ולדחוף משלים בעסקאות."
    else:
        insight = f"אנחנו מתחת לקצב. היום צריך לשאוף לקצב יומי של {fmt_nis(avg_daily_required)} כדי להתקרב ליעד."
        
    st.markdown(f"<div class='insight-box'>{insight}</div>", unsafe_allow_html=True)
