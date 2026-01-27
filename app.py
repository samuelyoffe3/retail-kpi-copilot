import streamlit as st
import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
import io
import logging
import os
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
BRANCH_MAP = {
    "S23": "11qDguX2-nq7_SpcuWNabQ8pDwGLgu-Q7",
    "S24": "1rs9fgtnTy0eR33xuCLphLHoqNpVY3Y4D",
    "S25": "1B-4Wl7WTlZ4UP-b6eIJ_EXNyrR60L6aY",
    "S26": "1GRlBu4PP6u521gptXRjuUHR-YRWCMkWb",
    "S28": "1MO7WlNkE9unkUELtQ7y8Nb6p5PxyHCAr",
    "S29": "1kdXNThYh_2IfubiQqZ5jgupGn4Ce3cEV",
    "S30": "1TTGUCnTQid3IF2PwO0cLbQpHmoAE84hW",
    "S31": "1Y0Nf0H2VBsI52aWmOTE645eiBayJSG1K",
    "S32": "1HT4_c4rEvcW_o5NhYkpPZiDVFfp4_0dK",
    "S33": "1RCNav8WObEcko6yXYTnR3EolzN99F8ZL",
    "S34": "1vTCKurdrGdPkgRMjGv0pdlXcWUKXy9C6",
    "S35": "1o-wrKAaEkUOnjrYZbMeFgarOjwmkN0Eg",
    "S36": "1xlmzl3pt_WLFEUDxdscO0Hli0S_PL2nk",
    "S38": "1eE-kkRLNm9PJKDskbYifMIqs8FTbZbzQ",
    "S39": "1mLtvm546GV5ge5XbvxoocSgfv_Bq08pG",
    "S40": "1hqy84v9evWG3lu3Ke4cI9bfCjRsKTiJr",
    "S41": "1TAl-oiBzooVfqtANbPC4qwJr8cLr8NRz",
    "S42": "1Ahn8moXdkpdNRN4SoyFJR87VAMc2hxNt",
    "S43": "1z-RyWXdbR3T_Ur0C83CScMk3yMOa0rx6",
    "S44": "1fdbqztjh5spim09YxvFKPf1ujhBp--gg",
    "S82": "1AvdMWQJjiJ8g8X5aNoFiQF80Z8jgZiCA",
    "S83": "1BxIBvacWUBnt2j5wQbqaglACD0NjA6CJ",
    "S84": "1kRVay_vhKCEvA1HIvu2FYufXN8hGUdG5",
    "S85": "1hLBmFMnb3r_K4xRyGlEE71fIk6fwc7OL"
}

APP_TITLE = "Retail KPI Copilot"


def get_drive_service():
    """Authenticates and returns the Google Drive service (Render ENV first, then Streamlit secrets)."""
    try:
        # 1) Production (Render)
        raw = os.getenv("GCP_SERVICE_ACCOUNT_JSON")
        if raw:
            service_account_info = json.loads(raw)
        else:
            # 2) Local dev (Streamlit secrets.toml)
            service_account_info = dict(st.secrets["gcp_service_account"])

        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        return build("drive", "v3", credentials=credentials)

    except Exception as e:
        logger.error(f"Failed to create Drive service: {e}")
        st.error("Failed to authenticate with Google Drive. Please check your secrets configuration.")
        st.error(f"Drive auth error details: {e}")
        return None
def get_gemini_credentials():
    """Loads Gemini/Vertex service account JSON from Render ENV first, then Streamlit secrets."""
    raw = os.getenv("GEMINI_SERVICE_ACCOUNT_JSON")
    if raw:
        info = json.loads(raw)
    else:
        info = dict(st.secrets["gemini_service_account"])
    return service_account.Credentials.from_service_account_info(info), info


def init_vertex_ai_once():
    """Initialize Vertex AI once per session with enhanced error reporting."""
    if st.session_state.get("_vertex_inited"):
        return

    try:
        # 1. טעינת האישורים
        creds, info = get_gemini_credentials()
        project_id = info.get("project_id")
        
        if not project_id:
            st.error("❌ שגיאה: project_id חסר ב-Service Account JSON")
            return

        # 2. ייבוא הספרייה (בתוך הפונקציה כדי למנוע קריסה בעלייה)
        import vertexai
        
        # 3. אתחול ה-SDK
        vertexai.init(
            project=project_id,
            location=os.getenv("VERTEX_LOCATION", "us-central1"),
            credentials=creds
        )

        st.session_state["_vertex_inited"] = True
        logger.info(f"✅ Vertex AI initialized successfully for project: {project_id}")
        
    except Exception as e:
        st.error("⚠️ כשל בחיבור ל-AI של גוגל")
        st.exception(e) # מציג את פירוט השגיאה הטכנית למפתח
        logger.error(f"Vertex AI initialization failed: {e}")

def load_data(service, folder_id):
    """Searches for 'sales.xlsx' in the folder and returns a DataFrame."""
    try:
        # Search for the file in the specific folder
        query = f"name = 'sales.xlsx' and '{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if not files:
            st.warning("File 'sales.xlsx' not found in this branch's folder.")
            return None

        # Get the first matching file (assuming unique name per folder)
        file_id = files[0]['id']
        
        # Download the file content
        request = service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = request.execute()
        file_content.write(downloader)
        file_content.seek(0)
        
        # Read into Pandas DataFrame
        df = pd.read_excel(file_content, engine='calamine')
        return df

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        st.error(f"An error occurred while loading the data: {e}")
        return None

def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    # Login Logic
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.selected_branch = None

    if not st.session_state.logged_in:
        st.subheader("Login")
        branch_options = list(BRANCH_MAP.keys()) + ["DEMO"]
        selected_branch = st.selectbox("Select Branch", branch_options)
        password = st.text_input("Enter Password", type="password")
        
        if st.button("Login"):
            if selected_branch == "DEMO" or password == "2410":
                st.session_state.logged_in = True
                st.session_state.selected_branch = selected_branch
                st.rerun()
            else:
                st.error("Incorrect password.")
        return

    # --- Authenticated App Flow ---
    selected_branch = st.session_state.selected_branch
    
    # --- SIDEBAR LAYOUT ---
    st.sidebar.markdown(f"### סניף: {selected_branch}")
    
    # Target Input
    if 'target_amount' not in st.session_state:
        st.session_state.target_amount = 500000.0

    target = st.sidebar.number_input(
        "יעד חודשי", 
        min_value=0.0, 
        value=st.session_state.target_amount, 
        step=1000.0
    )
    st.session_state.target_amount = target
    
    if target == 0:
        st.sidebar.warning("חובה להגדיר יעד חודשי")
        
    st.sidebar.markdown("---")

    # Data Loading (Auto-load)
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
    
    # Reload Button (Manual Refresh)
    if st.session_state.data_loaded:
        if st.sidebar.button("רענן נתונים"):
            st.session_state.data_loaded = False
            st.rerun()

    # Determine if we need to load/reload data
    if not st.session_state.data_loaded:
        if selected_branch == "DEMO":
            with st.spinner("טוען נתוני DEMO..."):
                try:
                    import os
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    sales_path = os.path.join(base_dir, "APPDEMO", "sales_demo.xlsx")
                    items_path = os.path.join(base_dir, "APPDEMO", "items_demo.xlsx")
                    
                    from services.load_sales import load_and_normalize_sales
                    from services.load_items import load_and_normalize_items
                    
                    # Read using calamine engine as per requirements.txt and existing code
                    with open(sales_path, "rb") as f:
                        df_sales = load_and_normalize_sales(io.BytesIO(f.read()))
                    with open(items_path, "rb") as f:
                        df_items = load_and_normalize_items(io.BytesIO(f.read()))
                    
                    if df_sales is not None and df_items is not None:
                        st.session_state.sales_df = df_sales
                        st.session_state.items_df = df_items
                        st.session_state.data_loaded = True
                        st.rerun()
                except Exception as e:
                    st.error(f"שגיאה בטעינת נתוני DEMO: {e}")
            return

        folder_id = BRANCH_MAP.get(selected_branch)
        if not folder_id:
             st.error("Branch configuration error.")
             return

        with st.spinner("טוען נתונים... (Loading Data)"):
            service = get_drive_service()
            if service:
                # 1. Download Files
                sales_stream = get_file_stream(service, folder_id, 'sales.xlsx')
                items_stream = get_file_stream(service, folder_id, 'items.xlsx')
                
                # 2. validation
                if not sales_stream or not items_stream:
                     st.error("שגיאה: לא נמצאו קבצי נתונים בתיקיית הסניף. נדרש: sales.xlsx ו-items.xlsx")
                     return
                
                # 3. Process
                from services.load_sales import load_and_normalize_sales
                from services.load_items import load_and_normalize_items
                
                df_sales = load_and_normalize_sales(sales_stream)
                df_items = load_and_normalize_items(items_stream)
                
                if df_sales is not None and df_items is not None:
                     st.session_state.sales_df = df_sales
                     st.session_state.items_df = df_items
                     st.session_state.data_loaded = True
                     st.rerun() 
                else:
                     st.error("Failed to process data files.")
            else:
                 st.error("Failed to connect to Google Drive.")
        return # Stop execution until data is loaded

    # --- MAIN NAVIGATION & RENDER ---
    if st.session_state.data_loaded:
         st.sidebar.success("נטען: sales.xlsx, items.xlsx")
         st.sidebar.markdown("---")
         
         # NAVIGATION MENU
         NAV_OPTIONS = {
             "מצב החנות": "status",
             "צוות ומכירות": "team",
             "תמהיל מוצרים": "mix",
             "תובנות ופעולות": "ai"
         }
         
         selected_nav = st.sidebar.radio("ניווט", list(NAV_OPTIONS.keys()))
         page_key = NAV_OPTIONS[selected_nav]

         sales_df = st.session_state.sales_df
         items_df = st.session_state.items_df
         target_amount = st.session_state.target_amount
         
         # --- SHARED CALCS ---
         from services.kpi_tab1 import calculate_kpis
         from services import kpi_tab2
         
         kpis = calculate_kpis(sales_df, target=target_amount)
         df_sellers = kpi_tab2.get_seller_table(sales_df, items_df)
         df_top_qty = kpi_tab2.get_top_products_qty(sales_df) 
         df_top_amt = kpi_tab2.get_top_products_amount(sales_df)
         
         # --- PAGE ROUTING ---
         if page_key == "status":
             from ui import tab1
             # Page Title (Matches Nav)
             st.markdown(f"<h2 style='text-align: right; direction: rtl;'>{selected_nav}</h2>", unsafe_allow_html=True)
             tab1.render(kpis)

         elif page_key == "team":
             from ui import tab2
             st.markdown(f"<h2 style='text-align: right; direction: rtl;'>{selected_nav}</h2>", unsafe_allow_html=True)
             tab2.render(df_sellers, df_top_qty, df_top_amt)
             
         elif page_key == "mix":
             from ui import tab3
             st.markdown(f"<h2 style='text-align: right; direction: rtl;'>{selected_nav}</h2>", unsafe_allow_html=True)
             tab3.render(items_df)
             
         elif page_key == "ai":
             from ui import tab4
             st.markdown(
                 f"<h2 style='text-align: right; direction: rtl;'>{selected_nav}</h2>",
                 unsafe_allow_html=True
             )

             try:
                 init_vertex_ai_once()
             except Exception as e:
                 st.error("שגיאת חיבור ל-AI (Vertex/Gemini). בדוק ENV והרשאות.")
                 st.error(str(e))
                 return

             tab4.render(
                 kpis,
                 df_sellers,
                 df_top_qty,
                 df_top_amt,
                 items_df
             )


def get_file_stream(service, folder_id, filename):
    """Helper to get BytesIO stream of a file from Drive."""
    try:
        query = f"name = '{filename}' and '{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        files = results.get('files', [])

        if not files:
            st.warning(f"קובץ '{filename}' לא נמצא בתיקייה.")
            return None

        file_id = files[0]['id']
        request = service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = request.execute()
        file_content.write(downloader)
        file_content.seek(0)
        return file_content
    except Exception as e:
        logger.error(f"Error downloading {filename}: {e}")
        st.error(f"שגיאה בהורדת הקובץ: {e}")
        return None



if __name__ == "__main__":
    main()
