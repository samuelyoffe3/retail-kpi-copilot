import streamlit as st
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
import os
import json

# --- Helper: Init Vertex AI ---
def init_vertex_ai():
    """Initializes Vertex AI with secrets."""
    try:
        # 1. Try Environment Variable (Render Production)
        env_creds = os.getenv("GEMINI_SERVICE_ACCOUNT_JSON")
        if env_creds:
            info = json.loads(env_creds)
            gemini_creds = service_account.Credentials.from_service_account_info(info)
            project_id = info.get("project_id")
            
            if not project_id:
               return False, "project_id missing in JSON"
               
            vertexai.init(project=project_id, credentials=gemini_creds)
            return True, ""

        # 2. Fallback to Streamlit Secrets (Local Dev)
        if "gemini_service_account" not in st.secrets:
            return False, "Secrets section [gemini_service_account] not found nor GEMINI_SERVICE_ACCOUNT_JSON env var."
            
        gemini_creds = service_account.Credentials.from_service_account_info(
            st.secrets["gemini_service_account"]
        )
        
        project_id = st.secrets["gemini_service_account"]["project_id"]
        
        vertexai.init(project=project_id, credentials=gemini_creds)
        return True, ""
    except Exception as e:
        return False, str(e)

# --- Helper: Call Gemini ---
def call_gemini(prompt):
    success, msg = init_vertex_ai()
    if not success:
        return f"System Error: {msg}"
    
    try:
        model = GenerativeModel("gemini-2.0-flash-exp") # או gemini-1.5-pro, לבחירתך
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- Data Summarization (UPDATED) ---
def summarize_data(kpis, df_sellers, df_top_qty, df_top_amt, items_df):
    """
    Creates a text summary of the store data for the AI.
    """
    summary = []
    
    # 1. Store KPIs
    if kpis:
        summary.append("--- STORE KPIS ---")
        summary.append(f"Target: {kpis.get('target', 0):,.0f}")
        summary.append(f"Actual to Date: {kpis.get('actual_to_date', 0):,.0f}")
        summary.append(f"Avg Daily: {kpis.get('avg_daily', 0):,.0f}")
        summary.append(f"Required Daily: {kpis.get('required_daily', 0):,.0f}")
        summary.append(f"Projected Finish: {kpis.get('projected_amount', 0):,.0f}")
        summary.append(f"Projected Percent: {kpis.get('projected_percent', 0):.1f}%")
        summary.append(f"Days left: {kpis.get('days_in_month', 30) - kpis.get('elapsed_days', 0)}")
    
    # 2. General Seller Stats (Bonus Logic)
    gen_seller_units = 0
    gen_seller_sales = 0
    if items_df is not None and not items_df.empty:
        # Search for "מוכרן כללי" or similar
        gen_seller = items_df[items_df['seller_name'].str.contains("מוכרן כללי", na=False)]
        gen_seller_units = gen_seller['units'].sum()
        if 'revenue' in gen_seller.columns:
            gen_seller_sales = gen_seller['revenue'].sum()
    
    summary.append(f"General Seller Units ('מוכרן כללי'): {gen_seller_units}")
    summary.append(f"General Seller Sales (Revenue): {gen_seller_sales}")

    # 3. Sellers Table
    if not df_sellers.empty:
        summary.append("\n--- TOP SELLERS ---")
        # Take top 10 for brevity
        for index, row in df_sellers.head(10).iterrows():
            summary.append(
                f"Seller: {row['שם מוכר']} | Sales: {row['מכירות']:,.0f} | "
                f"Txns: {row['מספר עסקאות']} | Avg Ticket: {row['ממוצע עסקה']:.0f} | "
                f"Avg Items: {row['ממוצע פריטים לעסקה']:.1f} | Complement Ratio: {row['יחס מוצר משלים לעסקה']:.2f}"
            )
            
    # 4. Top Products (QTY) - "The volume drivers"
    if not df_top_qty.empty:
        summary.append("\n--- TOP PRODUCTS BY QTY (Volume) ---")
        for i, row in df_top_qty.iterrows():
            summary.append(f"{row['תיאור מוצר']}: {row['כמות']} units")

    # 5. Top Products (AMOUNT) - "The money makers" (NEW SECTION)
    if not df_top_amt.empty:
        summary.append("\n--- TOP PRODUCTS BY REVENUE (Value) ---")
        for i, row in df_top_amt.iterrows():
            # מניח שיש עמודת 'מכירות' או דומה, תתאים אם צריך
            sales_val = row.get('מכירות', row.get('סכום', 0)) 
            summary.append(f"{row['תיאור מוצר']}: {sales_val:,.0f} NIS")

    return "\n".join(summary)


# --- Mode 1: Management Analysis (OPTIMIZED PROMPT) ---
def generate_management_analysis(kpis, df_sellers, df_top_qty, df_top_amt, items_df):
    data_summary = summarize_data(
        kpis, df_sellers, df_top_qty, df_top_amt, items_df
    )

    prompt = f"""
SYSTEM ROLE:
You are an expert Regional Retail Manager analyzing store performance.
You analyze store performance based on Sales, Transactions, Average Ticket, and Product Mix.
You connect "Who is selling" (Sellers data) with "What is being sold" (Top Qty vs Top Revenue items).

INPUT DATA:
{data_summary}

CRITICAL RULES:
1. "מוכרן כללי" is a **VIRTUAL BONUS BUDGET** (Not a person).
   - Calculation: (GeneralSellerRevenue / 1.18) * 0.01.
   - Output: If > 0, suggest a team reward. If 0, warn about lost budget.
2. METRICS: Use "Avg Ticket" (ממוצע עסקה) & "Tx Count" (כמות עסקאות). NO traffic/conversion talk.

ANALYSIS LOGIC (Mental Sandbox):
1. **Staff Diagnostics:**
   - High Tx + Low Avg Ticket = "Cashier Mode" (Moving volume, missing upsell).
   - Low Tx + High Avg Ticket = "Sniper" (Quality sales, low energy/initiative).
   - High Tx + High Avg Ticket = Star Performer.
2. **Product Forensics:**
   - Look at `Top Qty` items: Are they cheap accessories? If yes, this explains low Avg Ticket.
   - Look at `Top Revenue` items: Are these the strategic flagship products? If not, the focus is wrong.

OUTPUT STRUCTURE (Hebrew, Direct, Managerial):

1. תמונת מצב (Snapshot)
   - One sentence on Total Sales vs Targets.
   - Identification of the core problem: Is it Volume (not enough transactions) or Value (selling cheap items)?

2. ניתוח צוות (Staff Performance)
   - Compare specific employees.
   - *Example:* "דני מתפקד כקופאי - 100 עסקאות (גבוה) אבל ממוצע 80₪ (נמוך). הוא לא מציע מוצרים משלימים."
   - *Example:* "רונית מוכרת איכות - ממוצע 250₪, אבל חייבת להגביר קצב (רק 10 עסקאות)."

3. תמהיל מוצרים (Product Mix)
   - Compare what sells in Volume vs. what makes Money.
   - *Example:* "אנחנו מוכרים המון גרביים (Top Qty) אבל הנעליים היקרות (Top Revenue) לא זזות."

4. קופת בונוס ("מוכרן כללי")
   - State the calculated amount (Show the math: Revenue/1.18 * 0.01).
   - Suggest how to use it (or how to create it).

5. תוכנית פעולה (Action Plan)
   - 2 concrete instructions based on the data.
   - *Example:* "תדריך בוקר: פוקוס על המרת פריטי ה-Top Qty (הזולים) לפריטי ה-Top Amt (היקרים)."

TONE:
Short sentences. Assertive. Professional.
Every insight MUST have a number in parentheses.
"""
    return call_gemini(prompt)


# --- Mode 2: Team Message ---
def generate_team_message(topic, tone, kpis, df_sellers, df_top_qty, df_top_amt, items_df):
    data_summary = summarize_data(kpis, df_sellers, df_top_qty, df_top_amt, items_df)
    
    prompt = f"""
    You are a Store Manager writing a WhatsApp message to your team.
    
    OUTPUT LANGUAGE: Hebrew Only.
    TOPIC: {topic}
    TONE: {tone}
    
    DATA CONTEXT:
    {data_summary}
    
    RULES:
    - Message length: Medium (WhatsApp style).
    - Use emojis in good taste.
    - Include relevant numbers (e.g. % to target) if helpful.
    - No employee shaming.
    - No salary mentions.
    - Focus on the chosen Topic and Tone.
    """
    return call_gemini(prompt)