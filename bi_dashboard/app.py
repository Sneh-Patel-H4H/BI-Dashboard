"""
Conversational BI & Decision-Support Dashboard
Entry point — run with: streamlit run app.py
"""

import os

from dotenv import load_dotenv

load_dotenv()  # loads .env when running locally

import streamlit as st  # noqa: E402  (must come after load_dotenv)

# Streamlit Cloud stores secrets in st.secrets, not in env vars.
# Bridge them into os.environ so all modules can use os.getenv() uniformly.
try:
    if "ANTHROPIC_API_KEY" in st.secrets:
        os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]
except Exception:
    pass  # st.secrets not available (e.g. running locally without secrets configured)

# ---------------------------------------------------------------------------
# Page configuration — must be the first Streamlit call
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="BI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
        /* Background */
        .main { background-color: #F8F9FA; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF;
            border-right: 1px solid #E9ECEF;
        }

        /* Metric cards — Streamlit built-in st.metric */
        [data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E9ECEF;
            border-radius: 8px;
            padding: 16px 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }
        [data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #2C3E50 !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 13px !important;
            color: #7F8C8D !important;
        }

        /* Primary button */
        .stButton > button[kind="primary"] {
            background-color: #2E75B6;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #235d8e;
        }

        /* Hide Streamlit footer */
        footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

_DEFAULTS = {
    "raw_df": None,
    "schema": None,
    "kpis": None,
    "sector": None,
    "sector_confidence": None,
    "org_type": None,
    "org_confidence": None,
    "dataset_description": None,
    "selected_kpis": [],
    "chat_history": [],
    "file_name": None,
    "upload_complete": False,
    "discovery_complete": False,
    "data_quality_notes": [],
    "selected_nav": "📤 Upload Data",
    "pending_question": None,
}

for _key, _val in _DEFAULTS.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("## 📊 BI Dashboard")
    st.markdown("---")

    nav_options = ["📤 Upload Data", "📊 Dashboard", "💬 Ask the Data"]

    # Guard: prevent navigating to Dashboard/Chat before data is ready
    disabled_map = {
        "📊 Dashboard": not st.session_state.discovery_complete,
        "💬 Ask the Data": not st.session_state.discovery_complete,
    }

    selected_nav = st.radio(
        "Navigate",
        nav_options,
        key="selected_nav",
        label_visibility="collapsed",
    )

    # Soft redirect if page is not yet accessible
    if disabled_map.get(selected_nav, False):
        st.warning("Please upload and analyse a file first.")
        selected_nav = "📤 Upload Data"
        st.session_state.selected_nav = "📤 Upload Data"

    # ---- File info panel ---------------------------------------------------
    if st.session_state.upload_complete and st.session_state.file_name:
        st.markdown("---")
        st.markdown(f"**Loaded file**  \n`{st.session_state.file_name}`")
        if st.session_state.sector:
            st.caption(f"Sector: {st.session_state.sector}")

        if st.button("🔄 Upload New File", use_container_width=True):
            # Reset all session state cleanly
            for key in list(st.session_state.keys()):
                if key not in ("selected_nav",):
                    del st.session_state[key]
            st.session_state.selected_nav = "📤 Upload Data"
            st.rerun()

    # ---- Footer ------------------------------------------------------------
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#95A5A6;font-size:12px;'>✨ Powered by Claude AI</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Page routing
# ---------------------------------------------------------------------------

if selected_nav == "📤 Upload Data":
    if not st.session_state.upload_complete:
        from ui.upload_page import render
        render()
    elif not st.session_state.discovery_complete:
        from ui.discovery_page import render
        render()
    else:
        st.success("Your data is loaded and ready!")
        st.info("Use the sidebar to navigate to your **Dashboard** or **Ask the Data**.")

elif selected_nav == "📊 Dashboard":
    from ui.dashboard_page import render
    render()

elif selected_nav == "💬 Ask the Data":
    from ui.chat_page import render
    render()
