import streamlit as st
from services import ai_assistant
from datetime import datetime

def render(kpis, df_sellers, df_top_qty, df_top_amt, items_df):
    """
    Renders the AI Assistant Tab (Tab 4).
    Production-ready: Cached results, Copy buttons, WhatsApp style.
    """
    # --- CSS Styles ---
    st.markdown("""
        <style>
        .rtl-container {
            direction: rtl;
            text-align: right;
        }
        
        /* Analysis Box Style */
        .analysis-box {
            background-color: #fdfdfd;
            border: 1px solid #e0e0e0;
            border-right: 4px solid #1565c0; /* Blue accent on right for RTL */
            border-radius: 4px;
            padding: 20px;
            margin-bottom: 15px;
            direction: rtl;
            text-align: right;
            font-size: 0.95rem;
            line-height: 1.6;
            color: #212121;
        }
        
        /* WhatsApp Bubble Style */
        .whatsapp-bubble {
            background-color: #dcf8c6; /* Classic WhatsApp Light Green */
            border-radius: 7px;
            padding: 15px;
            color: #111;
            font-family: sans-serif;
            direction: rtl;
            text-align: right;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            margin-bottom: 10px;
            margin-top: 10px;
            border-bottom-left-radius: 0; /* Tail effect simulation */
        }
        
        .timestamp {
            font-size: 0.75rem;
            color: #757575;
            margin-top: 5px;
            text-align: left; /* Keep timestamp left or right? Right fits RTL */
            text-align: right;
            direction: rtl;
        }
        
        .helper-text {
            color: #616161;
            font-size: 0.9rem;
            margin-bottom: 10px;
            text-align: right;
            direction: rtl;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: right; direction: rtl;'>תובנות ופעולות</h3>", unsafe_allow_html=True)
    
    # Use tabs for clear separation
    tab_analysis, tab_message = st.tabs(["מחולל ניתוח ניהולי", "מחולל הודעה לצוות"])
    
    # --- TAB A: MANAGEMENT ANALYSIS ---
    with tab_analysis:
        st.markdown("<div class='helper-text'>עוזר אישי מסכם מה קורה בסניף ומה עושים הלאה.</div>", unsafe_allow_html=True)
        
        if st.button("צור ניתוח נתונים", type="primary"):
            with st.spinner("מנתח נתונים ומבצע חשיבה ניהולית..."):
                try:
                    result = ai_assistant.generate_management_analysis(
                        kpis, df_sellers, df_top_qty, df_top_amt, items_df
                    )
                    
                    if "Error" in result:
                        st.error("לא הצלחתי לייצר כרגע (שגיאת חיבור). נסה שוב בעוד רגע.")
                    else:
                        # Save to session state
                        st.session_state['ai_analysis_text'] = result
                        st.session_state['ai_analysis_time'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                except Exception as e:
                     st.error("אירעה שגיאה בייצור הדוח.")

        # Render Result from State
        if 'ai_analysis_text' in st.session_state:
            analysis_text = st.session_state['ai_analysis_text']
            gen_time = st.session_state.get('ai_analysis_time', '')
            
            # Display Results
            st.markdown(f"**תוצאה (נוצר ב-{gen_time}):**")
            st.markdown(analysis_text) # Render standard markdown
            
            st.markdown("---")
            st.caption("העתק את הטקסט:")
            st.code(analysis_text, language="text") # Provides Copy Button

    # --- TAB B: TEAM MESSAGE ---
    with tab_message:
        st.markdown("<div class='helper-text'>ניסוח הודעה מהירה לצוות בוואטסאפ.</div>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        with c1:
             topic = st.selectbox("נושא:", 
                ["יעד וקצב", "דחיפה למוצרים משלימים", "סיכום יום", "תחרות פנימית"]
            )
        with c2:
            tone = st.selectbox("טון:", 
                ["מפרגן", "חד וענייני", "הומוריסטי", "מוכיר תודה", "רציני"]
            )
            
        if st.button("צור הודעה לצוות", type="primary"):
            with st.spinner("מנסח הודעה לצוות..."):
                try:
                    msg_result = ai_assistant.generate_team_message(
                        topic, tone, kpis, df_sellers, df_top_qty, df_top_amt, items_df
                    )
                    
                    if "Error" in msg_result:
                         st.error("לא הצלחתי לייצר הודעה כרגע. נסה שוב.")
                    else:
                        st.session_state['ai_message_text'] = msg_result
                        st.session_state['ai_message_time'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                except Exception:
                    st.error("שגיאה כללית בניסוח ההודעה.")
        
        # Render Message from State
        if 'ai_message_text' in st.session_state:
            msg_text = st.session_state['ai_message_text']
            msg_time = st.session_state.get('ai_message_time', '')
            
            # WhatsApp Bubble Look
            st.markdown(f"""
            <div class='whatsapp-bubble'>
                {msg_text.replace(chr(10), '<br>')}
                <div class='timestamp'>{msg_time}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption("העתק להדבקה בוואטסאפ:")
            st.code(msg_text, language="text") # Copy Button
