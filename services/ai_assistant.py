import streamlit as st

from google.oauth2 import service_account

# --- Helper: Init Vertex AI ---
def init_vertex_ai():
    """Initializes Vertex AI with secrets."""
    try:
        # 1. Try Environment Variable (Render Production)
        import os
        import json
        
        env_creds = os.getenv("GEMINI_SERVICE_ACCOUNT_JSON")
        if env_creds:
            info = json.loads(env_creds)
            gemini_creds = service_account.Credentials.from_service_account_info(info)
            project_id = info.get("project_id")
            
            if not project_id:
               return False, "project_id missing in JSON"
               

            import vertexai   
            vertexai.init(project=project_id, location="us-central1", credentials=gemini_creds)

            return True, ""

        # 2. Fallback to Streamlit Secrets (Local Dev)
        if "gemini_service_account" not in st.secrets:
            return False, "Secrets section [gemini_service_account] not found nor GEMINI_SERVICE_ACCOUNT_JSON env var."
            
        gemini_creds = service_account.Credentials.from_service_account_info(
            st.secrets["gemini_service_account"]
        )
        
        project_id = st.secrets["gemini_service_account"]["project_id"]
        
        import vertexai
        vertexai.init(project=project_id, location="us-central1", credentials=gemini_creds)
        return True, ""
    except Exception as e:
        return False, str(e)

# --- Helper: Call Gemini ---
def call_gemini(prompt):
    success, msg = init_vertex_ai()
    if not success:
        return f"System Error: {msg}"
    
    try:
        from vertexai.generative_models import GenerativeModel
        model = GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

# --- Data Summarization ---
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
        summary.append(f"Days left in month: {kpis.get('days_in_month', 30) - kpis.get('elapsed_days', 0)}")
    
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
            
    # 4. Top Products
    if not df_top_qty.empty:
        summary.append("\n--- TOP PRODUCTS (QTY) ---")
        for i, row in df_top_qty.iterrows():
            summary.append(f"{row['תיאור מוצר']}: {row['כמות']}")

    return "\n".join(summary)


# --- Mode 1: Management Analysis ---
def generate_management_analysis(kpis, df_sellers, df_top_qty, df_top_amt, items_df):
    data_summary = summarize_data(
        kpis, df_sellers, df_top_qty, df_top_amt, items_df
    )

    prompt = f"""
SYSTEM ROLE:
You are an expert Regional Retail Manager analyzing store performance.
You focus on "Basket Building" and "Transaction Volume" since we lack traffic data.
You are direct, sharp, and results-oriented.

INPUT DATA:
{data_summary}

CRITICAL RULES (ZERO TOLERANCE):
1. "מוכרן כללי" is **NOT A PERSON**. It is a **VIRTUAL BONUS BUDGET**.
   - NEVER refer to it as "he", "she", or "it performed well".
   - ONLY calculate its value: (GeneralSellerRevenue / 1.18) * 0.01.
   - Usage: If Value > 0 -> Suggest specific incentives (food, contest). If 0 -> Suggest how to create it.
2. NO "Conversion" or "Traffic" talk. Use **"Avg Ticket" (ממוצע עסקה)** and **"Transaction Count" (כמות עסקאות)** instead.

ANALYSIS PROTOCOL (Mental Sandbox):
Diagnose the staff based on this logic:
- High Tx Count + Low Avg Ticket = "Order Taker" (Cashier mindset, no upsell).
- Low Tx Count + High Avg Ticket = "Cherry Picker" (Ignoring small customers, or slow service).
- High Tx Count + High Avg Ticket = The Star Performer.

OUTPUT CONTRACT:
- Language: Hebrew (Managerial, Spoken, Short).
- Tone: No-nonsense.
- Evidence: Every insight must have a number. Ex: "ממוצע עסקה נמוך (150₪)".

STRUCTURE:

1. השורה התחתונה (Snapshot)
   - One sentence on Total Revenue vs Target.
   - Identify the biggest operational gap: Is it volume (Transactions) or value (Avg Ticket)?

2. ניתוח כוח אדם (Staff Diagnostics)
   - Compare employees based on Avg Ticket vs. Store Avg.
   - Who is just "standing at the register" (High Tx, Low Ticket)?
   - Who is selling well?
   - *Example:* "דני מעביר הרבה עסקאות (150) אבל הממוצע נמוך (80₪) - הוא מתפקד כקופאי."

3. קופת הבונוסים ("מוכרן כללי")
   - Calculate the pool amount available.
   - If > 0: "יש לנו בקופה X שקלים. בוא נזמין פיצה/נעשה תחרות יומית."
   - If 0: "הקופה ריקה. חייבים למכור על הכללי כדי לייצר אווירה."

4. תוכנית עבודה (Next Steps)
   - Give 2 clear instructions based on the diagnosis.
   - If Avg Ticket is low -> Focus on "Add-on at checkout" (מוצרי קופה).
   - If Tx Count is low -> Focus on "Approaching customers" (יוזמה).

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
