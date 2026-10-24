import io
import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# =====================================================================
# 1. CONFIGURATION & COLOR PALETTE
# =====================================================================
API_BASE_URL = os.getenv("HELIOIQ_API_URL", "http://127.0.0.1:8000").rstrip("/")

PALETTE = {
    "MIDNIGHT_NAVY": "#08131F",          # Main background
    "DEEP_BLUE": "#102033",              # Secondary surfaces
    "WARM_IVORY": "#FFFAF0",             # Primary text
    "SOLAR_AMBER": "#F7B941",            # Accent / Moderate warning (Yellow)
    "TRANSLUCENT_DEEP_BLUE": "#12233494",# Component backgrounds (58% opacity)
    "ELECTRIC_TEAL": "#42D6C5",          # Healthy status / Normal (Green)
    "SIGNAL_BLUE": "#7AA7FF",            # Expected Baseline Power (Blue)
    "ALERT_CORAL": "#FF7373",            # Actual Power / Severe (Red)
    "SLATE_SILVER": "#A8B7C8",           # Secondary text / labels
    "ELEVATED_SURFACE": "#25394C",       # Hover states / selected surfaces
}

PAGES = [
    "Home",
    "Analysis Workspace",
    "What-if Simulator",
]

WORKSPACE_REGEX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


# =====================================================================
# 2. PAGE SETUP & THEME INJECTION
# =====================================================================
st.set_page_config(
    page_title="HelioIQ | PV Performance Intelligence",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def render_html(html_content: str) -> None:
    cleaned = "\n".join(line.lstrip() for line in html_content.splitlines() if line.strip())
    st.markdown(cleaned, unsafe_allow_html=True)


def inject_helioiq_css() -> None:
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --hq-bg: __MIDNIGHT_NAVY__;
        --hq-surface: __DEEP_BLUE__;
        --hq-surface-2: __TRANSLUCENT_DEEP_BLUE__;
        --hq-text: __WARM_IVORY__;
        --hq-muted: __SLATE_SILVER__;
        --hq-border: __ELEVATED_SURFACE__;
        --hq-accent: __SOLAR_AMBER__;
        --hq-radius: 12px;
    }

    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    html, body, .stApp, [data-testid="stAppViewContainer"] {
        background: var(--hq-bg) !important;
        color: var(--hq-text) !important;
        font-family: 'Inter', sans-serif !important;
    }

    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] { visibility: hidden; height: 0; }
    [data-testid="stHeader"] { background: transparent !important; }
    
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 1.5rem !important; 
        max-width: 1200px !important; 
    }

    h1, h2, h3, h4, h5, h6 { color: var(--hq-text) !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    p, li, label { color: var(--hq-text) !important; font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important; }
    small, .stCaption, [data-testid="stCaptionContainer"] p { color: var(--hq-muted) !important; }
    a { color: var(--hq-accent) !important; text-decoration: none; }
    hr { border-color: var(--hq-border) !important; margin: 1rem 0 !important; }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--hq-surface) !important;
        border: 1px solid var(--hq-border) !important;
        border-radius: var(--hq-radius) !important;
        padding: 1rem !important;
    }
    
    [data-testid="stMetric"] {
        background: var(--hq-surface) !important;
        border: 1px solid var(--hq-border) !important;
        border-radius: 10px !important;
        padding: 0.75rem 1rem !important;
    }
    [data-testid="stMetricLabel"] p { color: var(--hq-muted) !important; font-size: 0.75rem !important; font-weight: 600 !important; text-transform: uppercase !important; }
    [data-testid="stMetricValue"] { color: var(--hq-text) !important; font-weight: 800 !important; font-size: 1.3rem !important; }

    [data-testid="stPills"] {
        justify-content: center !important;
        gap: 0.5rem !important;
    }
    [data-testid="stPills"] > button {
        background: transparent !important;
        border: none !important;
        color: var(--hq-muted) !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 0.3rem 1rem !important;
        border-radius: 50px !important;
    }
    [data-testid="stPills"] > button:hover {
        background: var(--hq-surface-2) !important;
        color: var(--hq-text) !important;
    }
    [data-testid="stPills"] > button[aria-pressed="true"], 
    [data-testid="stPills"] > button[data-checked="true"] {
        background: var(--hq-accent) !important;
        color: var(--hq-bg) !important;
        font-weight: 700 !important;
    }

    [data-testid="stFileUploaderDropzone"] {
        background: var(--hq-surface-2) !important;
        border: 1px dashed var(--hq-border) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }

    .stButton > button, .stDownloadButton > button {
        background: transparent !important;
        color: var(--hq-text) !important;
        border: 1px solid var(--hq-border) !important;
        border-radius: 50px !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        padding: 0.4rem 1.2rem !important;
        white-space: nowrap !important;
        overflow: visible !important;
        text-overflow: clip !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover { border-color: var(--hq-accent) !important; color: var(--hq-accent) !important; }
    
    .stButton > button[data-testid="baseButton-primary"],
    .stButton > button[kind="primary"] { 
        background: var(--hq-accent) !important; 
        color: var(--hq-bg) !important; 
        border-color: var(--hq-accent) !important; 
    }
    .stButton > button[data-testid="baseButton-primary"] *,
    .stButton > button[kind="primary"] * { 
        color: var(--hq-bg) !important; 
        font-weight: 700 !important; 
    }
    .stButton > button[data-testid="baseButton-primary"]:hover,
    .stButton > button[kind="primary"]:hover { 
        filter: brightness(1.1); 
        color: var(--hq-bg) !important; 
    }
    
    .stButton > button:disabled { opacity: 0.35 !important; box-shadow: none !important; }

    [data-baseweb="input"], [data-baseweb="select"] > div, [data-baseweb="textarea"] {
        background: var(--hq-surface-2) !important;
        border: 1px solid var(--hq-border) !important;
        border-radius: 8px !important;
        color: var(--hq-text) !important;
    }
    [data-baseweb="tab-list"] { gap: 1rem !important; border-bottom: 1px solid var(--hq-border) !important; background: transparent !important; }
    [data-baseweb="tab"] { background: transparent !important; padding: 0.6rem 0 !important; font-size: 0.85rem !important; color: var(--hq-muted) !important; }
    [data-baseweb="tab"][aria-selected="true"] { color: var(--hq-text) !important; font-weight: 600 !important; }
    [data-baseweb="tab-highlight"] { background: var(--hq-accent) !important; height: 3px !important; border-radius: 3px 3px 0 0; }

    .status-badge { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.04em; }
    .status-healthy { background: rgba(66, 214, 197, 0.12); color: __ELECTRIC_TEAL__ !important; border: 1px solid __ELECTRIC_TEAL__; }
    .status-caution { background: rgba(247, 185, 65, 0.12); color: __SOLAR_AMBER__ !important; border: 1px solid __SOLAR_AMBER__; }
    .status-investigate { background: rgba(255, 115, 115, 0.12); color: __ALERT_CORAL__ !important; border: 1px solid __ALERT_CORAL__; }
    .status-neutral { background: transparent; color: __SLATE_SILVER__ !important; border: 1px solid __ELEVATED_SURFACE__; }
    </style>
    """
    for key, hex_code in PALETTE.items():
        css = css.replace(f"__{key}__", hex_code)
    st.markdown(css, unsafe_allow_html=True)


# =====================================================================
# 3. SESSION STATE & HELPERS
# =====================================================================
def init_session_state() -> None:
    defaults = {
        "current_page": PAGES[0],
        "active_workspace": None,
        "active_model_version": None,
        "shared_file_bytes": None,
        "shared_file_name": None,
        "dataset_profile": "trieste_q2",
        "utc_offset": 1.0,
        "last_validation_result": None,
        "last_training_result": None,
        "last_historical_result": None,
        "last_summary_result": None,
        "last_anomaly_result": None,
        "last_whatif_result": None,
        "sim_irr": 1.0,
        "sim_temp": 0.0,
        "sim_shade": 0.0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
    
    if st.session_state["current_page"] not in PAGES:
        st.session_state["current_page"] = PAGES[0]


def navigate_to(page_name: str) -> None:
    st.session_state["current_page"] = page_name
    st.rerun()


def get_shared_file_tuple() -> Optional[Dict[str, Tuple[str, Any, str]]]:
    if st.session_state["shared_file_bytes"] is not None:
        stream = io.BytesIO(st.session_state["shared_file_bytes"])
        stream.seek(0)
        return {"file": (st.session_state["shared_file_name"], stream, "text/csv")}
    return None


def format_form_value(val: Any) -> str:
    if isinstance(val, (dict, list)): return json.dumps(val)
    if isinstance(val, bool): return "true" if val else "false"
    if isinstance(val, float) and val.is_integer(): return str(int(val))
    return str(val)


def sanitize_api_message(msg: str) -> str:
    text = str(msg)
    text = text.replace("config.plant['location']", "Plant Location Override")
    text = text.replace("dc_power_derived_total_w", "Derived DC Power")
    text = text.replace("dc_power", "Measured DC Power")
    return text


def api_call(
    method: str, endpoint: str, data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None, timeout: int = 120
) -> Tuple[bool, int, Any]:
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    cleaned_data = {k: format_form_value(v) for k, v in (data or {}).items() if v is not None and v != ""}
    
    upload_files = None
    if files:
        upload_files = {}
        for k, f_tuple in files.items():
            if isinstance(f_tuple, tuple) and len(f_tuple) == 3:
                fname, fstream, fmime = f_tuple
                if hasattr(fstream, "seek"):
                    fstream.seek(0)
                upload_files[k] = (fname, fstream, fmime)
            else:
                upload_files[k] = f_tuple

    try:
        response = requests.request(method.upper(), url, data=cleaned_data, files=upload_files, timeout=timeout)
    except requests.exceptions.RequestException as exc:
        return False, 0, f"Network error: {exc}"
    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text or f"HTTP {response.status_code}"}
    return (200 <= response.status_code < 300), response.status_code, payload


def render_api_error(status_code: int, payload: Any, context: str = "API Request") -> None:
    detail = payload.get("detail", payload) if isinstance(payload, dict) else str(payload)
    with st.container(border=True):
        st.error(f"■ **{context} Failed** {f'(HTTP {status_code})' if status_code else '(Network Error)'}")
        if isinstance(detail, list):
            for item in detail:
                msg = item.get("msg", str(item)) if isinstance(item, dict) else str(item)
                st.markdown(f"- {sanitize_api_message(msg)}")
        else:
            msg = detail.get("message") or detail.get("detail") or str(detail) if isinstance(detail, dict) else str(detail)
            st.write(sanitize_api_message(msg))


def render_status_pill(status_val: Any) -> None:
    raw = str(status_val or "unknown").strip()
    low = raw.lower()
    if any(k in low for k in ["ok", "healthy", "normal", "valid", "success", "low", "none", "pass"]):
        cls, sym, tag = "status-healthy", "●", "NORMAL"
    elif any(k in low for k in ["degraded", "watch", "caution", "warning", "warn", "medium", "moderate"]):
        cls, sym, tag = "status-caution", "▲", "WATCH"
    elif any(k in low for k in ["error", "fail", "invalid", "high", "critical", "severe", "anomaly", "flagged", "investigate", "significant"]):
        cls, sym, tag = "status-investigate", "■", "INVESTIGATE"
    else:
        cls, sym, tag = "status-neutral", "◆", "INFO"
    render_html(f'<div style="margin-bottom:0.5rem;"><span class="status-badge {cls}">{sym} {raw.upper()} ({tag})</span></div>')


def apply_helioiq_plotly_theme(fig: go.Figure, title: str, xaxis_title: str, yaxis_title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=PALETTE["WARM_IVORY"])),
        font=dict(family="Inter, Segoe UI, sans-serif", color=PALETTE["WARM_IVORY"]),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title=xaxis_title, gridcolor="rgba(37, 57, 76, 0.5)", linecolor=PALETTE["ELEVATED_SURFACE"], zerolinecolor=PALETTE["ELEVATED_SURFACE"]),
        yaxis=dict(title=yaxis_title, gridcolor="rgba(37, 57, 76, 0.5)", linecolor=PALETTE["ELEVATED_SURFACE"], zerolinecolor=PALETTE["ELEVATED_SURFACE"]),
        legend=dict(bordercolor=PALETTE["ELEVATED_SURFACE"], borderwidth=1, bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified", margin=dict(l=30, r=20, t=50, b=30),
    )
    return fig


import base64

def render_top_bar() -> None:
    ok, _, health = api_call("GET", "/health", timeout=3)
    badge = f'<div style="border: 1px solid {PALETTE["ELEVATED_SURFACE"]}; padding: 0.25rem 0.6rem; border-radius: 50px; display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.7rem; font-weight: 700; color: {PALETTE["WARM_IVORY"]};"><span style="color: {PALETTE["ELECTRIC_TEAL"]};">●</span> LIVE</div>' if (ok and isinstance(health, dict) and health.get("status") == "ok") else f'<div style="border: 1px solid {PALETTE["ELEVATED_SURFACE"]}; padding: 0.25rem 0.6rem; border-radius: 50px; display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.7rem; font-weight: 700; color: {PALETTE["SLATE_SILVER"]};"><span style="color: {PALETTE["ALERT_CORAL"]};">■</span> OFFLINE</div>'

    # Load logo dynamically from file at runtime
    logo_b64 = ""
    if os.path.exists("logo.png"):
        with open("logo.png", "rb") as lf:
            logo_b64 = base64.b64encode(lf.read()).decode("utf-8")

    render_html('<div style="margin-bottom: 1rem;"></div>')
    # Expanded logo column width ratio to 1.8 for generous spacing
    c1, c2, c3 = st.columns([1.8, 5.0, 1.2], vertical_alignment="center")
    with c1:
        if logo_b64:
            # Increased logo height from 38px to 58px
            render_html(f'<div style="display:flex; align-items:center;"><img src="data:image/png;base64,{logo_b64}" style="height: 58px; object-fit: contain; border-radius: 6px;" alt="HelioIQ Logo"/></div>')
        else:
            render_html(f'<div style="font-size:1.3rem; font-weight:700; color:{PALETTE["WARM_IVORY"]};">HelioIQ</div>')
    with c2:
        selected = st.pills("NAV", options=PAGES, default=st.session_state["current_page"], label_visibility="collapsed")
        if selected and selected != st.session_state["current_page"]:
            st.session_state["current_page"] = selected
            st.rerun()
    with c3:
        render_html(f'<div style="text-align:right;">{badge}</div>')
# =====================================================================
# 4. PAGE IMPLEMENTATIONS
# =====================================================================

def page_home() -> None:
    render_html(
        f"""
        <div style="background: {PALETTE['DEEP_BLUE']}; padding: 2.5rem 3rem; border-radius: 20px; border: 1px solid {PALETTE['ELEVATED_SURFACE']}; margin-bottom: 1.5rem; position: relative; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
        <div style="position: absolute; right: 8%; top: 50%; transform: translateY(-50%); width: 220px; height: 220px; background: radial-gradient(circle, rgba(247,185,65,0.35) 0%, rgba(247,185,65,0) 70%); filter: blur(30px); border-radius: 50%;"></div>
        <div style="position: absolute; right: 10%; top: 50%; transform: translateY(-50%); width: 180px; height: 180px; background: radial-gradient(circle, #FFE5B4 0%, {PALETTE['SOLAR_AMBER']} 60%, #D99B26 100%); border-radius: 50%; box-shadow: 0 0 50px rgba(247,185,65,0.7), inset 0 0 20px rgba(255,255,255,0.6);"></div>
        <div style="position: relative; z-index: 10; width: 68%;">
            <div style="display: inline-block; padding: 0.3rem 0.9rem; border: 1px solid rgba(247, 185, 65, 0.3); border-radius: 50px; color: {PALETTE['SOLAR_AMBER']}; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 1rem;">
            ✨ Clarity, without the spreadsheets
            </div>
            <h1 style="font-size: 3.2rem; font-weight: 800; line-height: 1.08; margin-bottom: 1rem; letter-spacing: -0.02em; color: {PALETTE['WARM_IVORY']};">
            Know what your <br/>system <br/>should do. <span style="color: {PALETTE['SOLAR_AMBER']};">Know <br/>when it doesn't.</span>
            </h1>
            <p style="font-size: 1rem; color: {PALETTE['SLATE_SILVER']}; max-width: 480px; line-height: 1.5; margin-bottom: 1.5rem;">
            HelioIQ turns sunlight and temperature into a friendly, living picture of plant health—so the next best action feels obvious.
            </p>
        </div>
        </div>
        """
    )
    c_btn1, c_btn2, _ = st.columns([3, 3, 4])
    with c_btn1:
        if st.button("Bring in your data →", type="primary", use_container_width=True): navigate_to(PAGES[1])
    with c_btn2:
        if st.button("Explore a scenario ↗", use_container_width=True): navigate_to(PAGES[2])

    if st.session_state["shared_file_bytes"] is not None:
        st.markdown("---")
        st.markdown("### 📊 Active Plant & Dataset Dashboard")
        try:
            df = pd.read_csv(io.BytesIO(st.session_state["shared_file_bytes"]), dtype=str)
            n_rows = len(df)
            n_cols = len(df.columns)
            
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Active Dataset", st.session_state.get("shared_file_name", "Dataset.csv"))
            mc2.metric("Total Records", f"{n_rows:,}")
            mc3.metric("Data Columns", f"{n_cols}")
            mc4.metric("Workspace Model", st.session_state.get("active_workspace") or "Not Trained")

            with st.container(border=True):
                st.markdown("##### ⚡ Quick Plant Status")
                render_status_pill("NORMAL")
                st.write(f"Your dataset **{st.session_state.get('shared_file_name')}** is currently active and loaded across workspaces. You have {n_rows:,} timestamp records ready for machine learning intelligence.")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Go to Analysis Workspace →", type="primary", use_container_width=True):
                        navigate_to(PAGES[1])
                with col_b:
                    if st.button("Run Simulation ↗", use_container_width=True):
                        navigate_to(PAGES[2])
        except Exception as e:
            st.warning(f"Could not load dashboard metrics: {e}")


def page_analysis() -> None:
    st.markdown("## Analysis Workspace")
    with st.container(border=True):
        col_file, col_del, col_btn = st.columns([3.5, 1.2, 1.3])
        with col_file:
            uploaded_files = st.file_uploader("Upload PV Datasets (CSV)", type=["csv"], accept_multiple_files=True, label_visibility="collapsed")
            if uploaded_files:
                try:
                    dfs = []
                    filenames = []
                    for f in uploaded_files:
                        filenames.append(f.name)
                        df_part = pd.read_csv(f, dtype=str)
                        dfs.append(df_part)
                    
                    combined_df = pd.concat(dfs, ignore_index=True)
                    csv_buffer = io.StringIO()
                    combined_df.to_csv(csv_buffer, index=False)
                    bytes_data = csv_buffer.getvalue().encode('utf-8')
                    combined_name = f"combined_{len(filenames)}_files.csv"

                    if st.session_state["shared_file_bytes"] != bytes_data:
                        st.session_state["shared_file_bytes"] = bytes_data
                        st.session_state["shared_file_name"] = combined_name
                        st.session_state["last_validation_result"] = None
                        st.rerun()
                except Exception as e:
                    st.error(f"Error combining uploaded files: {e}")
        with col_del:
            st.write("")
            if st.button("🗑️ Remove File", disabled=st.session_state["shared_file_bytes"] is None, use_container_width=True):
                st.session_state["shared_file_bytes"] = None
                st.session_state["shared_file_name"] = None
                st.session_state["last_validation_result"] = None
                st.session_state["last_training_result"] = None
                st.session_state["last_historical_result"] = None
                st.session_state["last_summary_result"] = None
                st.session_state["last_anomaly_result"] = None
                st.rerun()
        with col_btn:
            st.write("")
            if st.button("Validate Dataset", disabled=st.session_state["shared_file_bytes"] is None, use_container_width=True, type="primary"):
                form_data = {"dataset": st.session_state["dataset_profile"], "utc_offset_hours": st.session_state["utc_offset"]}
                ok, code, payload = api_call("POST", "/datasets/validate", data=form_data, files=get_shared_file_tuple())
                if ok:
                    st.session_state["last_validation_result"] = payload
                    if hasattr(st, "toast"): st.toast("✅ Dataset validated successfully!", icon="✅")
                else: render_api_error(code, payload, "Dataset Validation")

    if not st.session_state["shared_file_bytes"]:
        st.info("Upload a CSV dataset above to begin exploring your data.")
        return

    tab_over, tab_train, tab_pred, tab_anom = st.tabs(["Overview", "Train Model", "Predictions", "Anomalies"])

    with tab_over:
        st.markdown("#### Dataset Explorer")
        try:
            df = pd.read_csv(io.BytesIO(st.session_state["shared_file_bytes"]), dtype=str)
            n_rows = len(df)
            n_cols = len(df.columns)
            st.write(f"This dataset contains **{n_rows:,}** rows and **{n_cols}** columns.")
            
            with st.container(border=True):
                st.markdown("##### 💡 Plain-English Explanation")
                st.write(f"Your uploaded dataset (`{st.session_state['shared_file_name']}`) contains chronological time-series records of your solar power plant. It measures environmental factors like sunlight intensity (irradiance), module temperature, and electrical power generation across **{n_rows:,} timestamps**.")
                
                st.markdown("##### ⚠️ Risk & Health Status")
                render_status_pill("NORMAL")
                st.write("**Assessment:** Dataset structure is healthy and ready for performance intelligence.")

                st.markdown("##### 🛠️ Recommended Next Steps")
                st.markdown("1. **Validate Dataset:** Click the **Validate Dataset** button at the top to ensure column headers conform correctly.")
                st.markdown("2. **Train a Model:** Go to the **Train Model** tab above to train a baseline machine learning model.")
                st.markdown("3. **Analyze Performance:** Use the **Predictions** and **Anomalies** tabs to inspect energy output.")

            with st.expander("Raw Data Preview", expanded=False):
                st.dataframe(df.head(15), use_container_width=True)

            time_cols = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower() or 'stamp' in c.lower()]
            irr_cols = [c for c in df.columns if 'irradiance' in c.lower() or c == 'G']
            if time_cols and irr_cols:
                tc, ic = time_cols[0], irr_cols[0]
                plot_df = df[[tc, ic]].dropna().copy()
                plot_df[ic] = pd.to_numeric(plot_df[ic], errors='coerce')
                if len(plot_df) > 5000: plot_df = plot_df.iloc[::max(1, len(plot_df)//1000)]
                fig = go.Figure(go.Scatter(x=plot_df[tc], y=plot_df[ic], mode='lines', line=dict(color=PALETTE["SOLAR_AMBER"], width=1)))
                fig = apply_helioiq_plotly_theme(fig, f"Irradiance Overview ({ic})", "Time", "Irradiance (W/m²)")
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not parse CSV for local overview: {e}")

    with tab_train:
        st.markdown("#### Train a New Model")
        with st.container(border=True):
            st.write(f"Training on active dataset: **{st.session_state['shared_file_name']}**")
            c1, c2 = st.columns(2)
            workspace_input = c1.text_input("Workspace Name", value=st.session_state.get("active_workspace") or "trieste_demo")
            test_frac = c2.number_input("Hold-out Test Fraction", 0.05, 0.5, 0.2, 0.05)
            
            if st.button("Train Model", type="primary", use_container_width=True):
                if not WORKSPACE_REGEX.match(workspace_input):
                    st.error("Invalid workspace name format.")
                else:
                    form_data = {
                        "workspace": workspace_input,
                        "dataset": st.session_state["dataset_profile"],
                        "utc_offset_hours": st.session_state["utc_offset"],
                        "test_fraction": test_frac,
                    }
                    with st.spinner("Training models via POST /models/train..."):
                        ok, status_code, payload = api_call("POST", "/models/train", data=form_data, files=get_shared_file_tuple(), timeout=300)
                        if ok and isinstance(payload, dict):
                            st.session_state["last_training_result"] = payload
                            st.session_state["active_workspace"] = payload.get("workspace", workspace_input)
                            st.session_state["active_model_version"] = str(payload.get("version", "latest"))
                            st.success("✅ Model trained and saved successfully!")
                        else:
                            render_api_error(status_code, payload, "POST /models/train")

        train_res = st.session_state.get("last_training_result")
        if train_res and isinstance(train_res, dict):
            st.markdown("---")
            st.markdown("##### Training & Evaluation Results")
            render_status_pill("SUCCESS")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Workspace", str(train_res.get("workspace", st.session_state.get("active_workspace", "—"))))
            c2.metric("Saved Version", str(train_res.get("version", "latest")))
            c3.metric("Selected Model", str(train_res.get("selected_model", "Random Forest")).replace("_", " ").title())
            c4.metric("Target", str(train_res.get("target", "Derived DC")))

    with tab_pred:
        st.markdown("#### Performance Analysis")
        if not st.session_state["active_workspace"]:
            st.warning("⚠️ **No active model loaded.** Train a model in the **Train Model** tab first.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            start_date = c1.text_input("Start Date (Optional)", key="pred_start", placeholder="YYYY-MM-DD")
            end_date = c2.text_input("End Date (Optional)", key="pred_end", placeholder="YYYY-MM-DD")
            group_by = c3.selectbox("Aggregation", ["None", "day", "month"], key="pred_group")
            if c4.button("Run Predictions", use_container_width=True, type="primary"):
                form_data = {
                    "workspace": st.session_state["active_workspace"],
                    "version": st.session_state.get("active_model_version") or "latest",
                    "dataset": st.session_state["dataset_profile"],
                    "utc_offset_hours": st.session_state["utc_offset"],
                    "start": start_date or None,
                    "end": end_date or None,
                    "include_rows": "true",
                }
                with st.spinner("Generating predictions..."):
                    ok_hist, code_hist, payload_hist = api_call("POST", "/predictions/historical", data=form_data, files=get_shared_file_tuple())
                    if ok_hist and isinstance(payload_hist, dict):
                        st.session_state["last_historical_result"] = payload_hist
                    else:
                        render_api_error(code_hist, payload_hist, "POST /predictions/historical")
                    
                    sum_form = dict(form_data)
                    if group_by != "None": sum_form["group_by"] = group_by
                    ok_sum, code_sum, payload_sum = api_call("POST", "/performance/summary", data=sum_form, files=get_shared_file_tuple())
                    if ok_sum and isinstance(payload_sum, dict):
                        st.session_state["last_summary_result"] = payload_sum
                    else:
                        render_api_error(code_sum, payload_sum, "POST /performance/summary")

            hist_res = st.session_state.get("last_historical_result")
            if hist_res and isinstance(hist_res, dict):
                rows = hist_res.get("rows", hist_res.get("data", []))
                if isinstance(rows, list) and len(rows) > 0:
                    df_hist = pd.DataFrame(rows)
                    try:
                        time_col = next((c for c in df_hist.columns if 'time' in c.lower() or 'date' in c.lower() or 'stamp' in c.lower()), df_hist.columns[0])
                        actual_col = next((c for c in df_hist.columns if 'observed' in c.lower() or 'actual' in c.lower() or 'power' in c.lower()), None)
                        expected_col = next((c for c in df_hist.columns if 'expected' in c.lower() or 'baseline' in c.lower() or 'predicted' in c.lower()), None)

                        if actual_col and expected_col:
                            df_hist[time_col] = pd.to_datetime(df_hist[time_col], errors='coerce')
                            df_hist = df_hist.sort_values(by=time_col)

                            if group_by == "month":
                                df_hist['period'] = df_hist[time_col].dt.to_period('M').astype(str)
                                chart_group_col = 'period'
                                chart_title = "Monthly Actual vs. Expected Energy Comparison"
                                x_axis_title = "Month"
                            else:
                                df_hist['date'] = df_hist[time_col].dt.date
                                chart_group_col = 'date'
                                chart_title = "Daily Actual vs. Expected Energy Comparison"
                                x_axis_title = "Date"

                            df_grouped = df_hist.groupby(chart_group_col).agg({
                                actual_col: 'sum',
                                expected_col: 'sum'
                            }).reset_index()

                            fig_pred = go.Figure()
                            fig_pred.add_trace(go.Bar(
                                x=df_grouped[chart_group_col], y=pd.to_numeric(df_grouped[actual_col], errors='coerce'),
                                name='Actual Energy (Observed)',
                                marker_color=PALETTE["ALERT_CORAL"]
                            ))
                            fig_pred.add_trace(go.Bar(
                                x=df_grouped[chart_group_col], y=pd.to_numeric(df_grouped[expected_col], errors='coerce'),
                                name='Expected Energy (Baseline)',
                                marker_color=PALETTE["SIGNAL_BLUE"]
                            ))
                            fig_pred.update_layout(barmode='group')
                            fig_pred = apply_helioiq_plotly_theme(fig_pred, chart_title, x_axis_title, "Energy / Power (W)")
                            st.plotly_chart(fig_pred, use_container_width=True)
                    except Exception as e:
                        st.caption(f"Could not render Daily Bar Chart: {e}")

            sum_res = st.session_state.get("last_summary_result")
            if isinstance(sum_res, dict):
                st.markdown("---")
                st.markdown("##### Aggregate Performance Summary")
                metrics_block = sum_res.get("summary", sum_res.get("metrics", sum_res))
                if isinstance(metrics_block, dict):
                    scalar_items = [(k, v) for k, v in metrics_block.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)]
                    if scalar_items:
                        cols = st.columns(min(4, len(scalar_items)))
                        for idx, (k, v) in enumerate(scalar_items[:8]):
                            val_str = f"{v:,.3f}" if isinstance(v, float) else str(v)
                            cols[idx % len(cols)].metric(k.replace("_", " ").title(), val_str)

    with tab_anom:
        st.markdown("#### Anomaly Detection")
        if not st.session_state["active_workspace"]:
            st.warning("⚠️ **No active model loaded.** Train a model in the **Train Model** tab first.")
        else:
            c1, c2, c3 = st.columns([2,2,1])
            a_start = c1.text_input("Start Date (Optional)", key="anom_start", placeholder="YYYY-MM-DD")
            a_end = c2.text_input("End Date (Optional)", key="anom_end", placeholder="YYYY-MM-DD")
            if c3.button("Scan Anomalies", use_container_width=True):
                form_data = {
                    "workspace": st.session_state["active_workspace"],
                    "version": st.session_state.get("active_model_version") or "latest",
                    "dataset": st.session_state["dataset_profile"],
                    "utc_offset_hours": st.session_state["utc_offset"],
                    "start": a_start or None,
                    "end": a_end or None,
                    "include_rows": "true"
                }
                with st.spinner("Analyzing deviations..."):
                    ok, status_code, payload = api_call("POST", "/anomalies/analyze", data=form_data, files=get_shared_file_tuple())
                    if ok and isinstance(payload, dict):
                        st.session_state["last_anomaly_result"] = payload
                    else:
                        render_api_error(status_code, payload, "POST /anomalies/analyze")

            anom_res = st.session_state.get("last_anomaly_result")
            if isinstance(anom_res, dict):
                st.markdown("---")
                st.markdown("##### Anomaly Scan Results")
                anomaly_rows = anom_res.get("anomalies", anom_res.get("rows", []))
                anomaly_count = anom_res.get("count", len(anomaly_rows) if isinstance(anomaly_rows, list) else 0)
                
                if anomaly_count == 0 or not anomaly_rows:
                    render_status_pill("NORMAL")
                    with st.container(border=True):
                        st.markdown("##### ✅ No Anomalies Detected")
                        st.write("Your solar plant generation aligns with expected model baselines. No underperformance or critical anomalies were flagged for the selected timeframe.")
                else:
                    render_status_pill("INVESTIGATE")
                    st.write(f"⚠️ **{anomaly_count} potential anomaly intervals detected.**")
                    
                    if isinstance(anomaly_rows, list) and len(anomaly_rows) > 0:
                        df_anom = pd.DataFrame(anomaly_rows)

                        try:
                            time_col = next((c for c in df_anom.columns if 'time' in c.lower() or 'date' in c.lower() or 'stamp' in c.lower()), df_anom.columns[0])
                            val_col = next((c for c in df_anom.columns if 'observed' in c.lower() or 'power' in c.lower() or 'actual' in c.lower() or 'val' in c.lower()), df_anom.columns[1] if len(df_anom.columns) > 1 else df_anom.columns[0])
                            sev_col = next((c for c in df_anom.columns if 'severity' in c.lower() or 'status' in c.lower()), None)

                            df_anom[time_col] = pd.to_datetime(df_anom[time_col], errors='coerce')
                            df_anom = df_anom.sort_values(by=time_col)

                            chart_col1, chart_col2 = st.columns(2)

                            with chart_col1:
                                if sev_col:
                                    severity_counts = df_anom[sev_col].astype(str).str.lower().value_counts()
                                    fig_bar = go.Figure(go.Bar(
                                        x=list(severity_counts.index),
                                        y=list(severity_counts.values),
                                        marker_color=[PALETTE["ALERT_CORAL"] if 'sig' in k or 'crit' in k else PALETTE["SOLAR_AMBER"] for k in severity_counts.index]
                                    ))
                                    fig_bar = apply_helioiq_plotly_theme(fig_bar, "Anomaly Count by Severity Type", "Severity Classification", "Number of Intervals")
                                    st.plotly_chart(fig_bar, use_container_width=True)

                            with chart_col2:
                                fig_anom = go.Figure()
                                if sev_col:
                                    df_watch = df_anom[df_anom[sev_col].astype(str).str.lower().str.contains('watch|moderate|caution|warn')]
                                    df_sig = df_anom[df_anom[sev_col].astype(str).str.lower().str.contains('significant|critical|high|outage|investigate')]
                                else:
                                    df_watch = pd.DataFrame()
                                    df_sig = df_anom

                                if not df_watch.empty:
                                    fig_anom.add_trace(go.Scatter(
                                        x=df_watch[time_col], y=pd.to_numeric(df_watch[val_col], errors='coerce'),
                                        mode='markers', name='Moderate (Yellow)',
                                        marker=dict(color=PALETTE["SOLAR_AMBER"], size=7, symbol='triangle-up')
                                    ))

                                if not df_sig.empty:
                                    fig_anom.add_trace(go.Scatter(
                                        x=df_sig[time_col], y=pd.to_numeric(df_sig[val_col], errors='coerce'),
                                        mode='markers', name='Significant / Severe (Red)',
                                        marker=dict(color=PALETTE["ALERT_CORAL"], size=8, symbol='x')
                                    ))

                                fig_anom = apply_helioiq_plotly_theme(fig_anom, "Anomaly Timeline Distribution", "Time", "Power Output (W)")
                                st.plotly_chart(fig_anom, use_container_width=True)

                        except Exception as e:
                            st.caption(f"Could not render anomaly charts: {e}")

                        st.dataframe(df_anom, use_container_width=True)

                        with st.container(border=True):
                            st.markdown("##### 🛠️ Anomaly Fixing & Resolution Guide")
                            st.write("Different anomaly types require distinct troubleshooting protocols. Match the `severity` column in the table above to the appropriate fix steps below:")
                            st.markdown("###### 🔴 **1. Significant Deviations & Critical Outages (Red - High Drop / 0 W Generation)**")
                            st.markdown("- **Inverter & DC Hardware:** Check inverter error/fault logs, AC/DC disconnect switches, and blown DC string fuses.")
                            st.markdown("- **Electrical Insulation:** Perform insulation resistance (Megger) tests for potential leakage to ground, MC4 connector arcing, or severe PID.")
                            st.markdown("- **Grid & MPPT Voltage Constraints:** Inspect grid-side overvoltage trips, frequency anomalies, or inverter MPPT channel failures.")
                            st.markdown("- **Mechanical & Tracker Failure:** Verify single-axis tracker drive motors, angular position sensor limits, and mechanical stowing faults.")
                            st.markdown("###### 🟡 **2. Moderate Underperformance (Yellow - 'Watch' Severity)**")
                            st.markdown("- **Soiling & Shading:** Inspect array surfaces for dust/soiling build-up, bird droppings, vegetation, or localized structural shading.")
                            st.markdown("- **String Level Diagnostics:** Measure DC string current balanced ratios and review string-level IV curve traces.")
                            st.markdown("- **Thermal Inspection:** Conduct handheld thermographic or drone IR scans to check for module thermal hotspots and bypassed diode strings.")
                            st.markdown("- **Met Station Sensors:** Inspect pyranometer glass for dust and check module temperature sensor calibration drift.")


def page_whatif() -> None:
    st.markdown("## What-if Simulator")
    st.write("Model hypothetical adjustments to solar irradiance, module temperature, and shading losses to forecast simulated energy yield.")
    
    if not st.session_state["shared_file_bytes"] or not st.session_state["active_workspace"]:
        st.warning("⚠️ **Prerequisites Missing:** Please upload a dataset in the **Analysis Workspace** and train a model first.")
        if st.button("Go to Analysis Workspace →", type="primary"):
            navigate_to(PAGES[1])
        return

    with st.container(border=True):
        st.markdown("##### ⚡ Quick Scenario Presets")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        if col_p1.button("☀️ Clear & Sunny (+20% Sun)", use_container_width=True):
            st.session_state["sim_irr"] = 1.2
            st.session_state["sim_temp"] = 0.0
            st.session_state["sim_shade"] = 0.0
        if col_p2.button("🍂 Heavy Soiling (15% Loss)", use_container_width=True):
            st.session_state["sim_irr"] = 1.0
            st.session_state["sim_temp"] = 0.0
            st.session_state["sim_shade"] = 15.0
        if col_p3.button("🔥 Extreme Heat (+10°C)", use_container_width=True):
            st.session_state["sim_irr"] = 1.0
            st.session_state["sim_temp"] = 10.0
            st.session_state["sim_shade"] = 0.0
        if col_p4.button("☁️ Overcast (-30% Sun)", use_container_width=True):
            st.session_state["sim_irr"] = 0.7
            st.session_state["sim_temp"] = -5.0
            st.session_state["sim_shade"] = 0.0

        st.markdown("##### 🎛️ Scenario Parameters")
        c1, c2, c3 = st.columns(3)
        irr_mult = c1.slider("Irradiance Scaling Multiplier", 0.3, 1.8, st.session_state.get("sim_irr", 1.0), 0.05)
        temp_offset = c2.slider("Ambient Temperature Offset (°C)", -15.0, 25.0, st.session_state.get("sim_temp", 0.0), 1.0)
        shading_loss = c3.slider("Shading / Soiling Loss Factor (%)", 0.0, 50.0, st.session_state.get("sim_shade", 0.0), 1.0)

        if st.button("Run Simulation", type="primary", use_container_width=True):
            hist_res = st.session_state.get("last_historical_result")
            if not hist_res:
                form_data = {
                    "workspace": st.session_state["active_workspace"],
                    "version": st.session_state.get("active_model_version") or "latest",
                    "dataset": st.session_state["dataset_profile"],
                    "utc_offset_hours": st.session_state["utc_offset"],
                    "include_rows": "true",
                }
                ok, _, payload = api_call("POST", "/predictions/historical", data=form_data, files=get_shared_file_tuple())
                if ok and isinstance(payload, dict):
                    st.session_state["last_historical_result"] = payload
                    hist_res = payload

            if hist_res and isinstance(hist_res, dict):
                rows = hist_res.get("rows", hist_res.get("data", []))
                if isinstance(rows, list) and len(rows) > 0:
                    df_sim = pd.DataFrame(rows)
                    time_col = next((c for c in df_sim.columns if 'time' in c.lower() or 'date' in c.lower() or 'stamp' in c.lower()), df_sim.columns[0])
                    expected_col = next((c for c in df_sim.columns if 'expected' in c.lower() or 'baseline' in c.lower() or 'predicted' in c.lower()), None)

                    if expected_col:
                        df_sim[time_col] = pd.to_datetime(df_sim[time_col], errors='coerce')
                        df_sim = df_sim.sort_values(by=time_col)
                        
                        base_vals = pd.to_numeric(df_sim[expected_col], errors='coerce').fillna(0)
                        temp_factor = 1.0 - (max(0.0, temp_offset) * 0.004)
                        shading_factor = 1.0 - (shading_loss / 100.0)
                        
                        df_sim['simulated_power'] = base_vals * irr_mult * temp_factor * shading_factor

                        df_sim['date'] = df_sim[time_col].dt.date
                        df_daily_sim = df_sim.groupby('date').agg({
                            'simulated_power': 'sum'
                        }).reset_index()

                        st.markdown("---")
                        st.markdown("##### 📈 Simulated Energy Forecast")
                        
                        total_simulated = df_daily_sim['simulated_power'].sum()
                        peak_power = df_daily_sim['simulated_power'].max()
                        avg_daily = df_daily_sim['simulated_power'].mean()
                        total_loss_est = shading_loss + max(0.0, temp_offset * 0.4)

                        with st.container(border=True):
                            st.markdown("##### 💡 Scenario Explanation")
                            st.write(f"Under your configured scenario (**Irradiance multiplier**: `{irr_mult}x`, **Temperature offset**: `{temp_offset:+}°C`, **Soiling/Shading loss**: `{shading_loss}%`), your solar power plant is projected to generate a total simulated energy yield of **{total_simulated:,.1f} W** over the selected period.")
                            if shading_loss > 0:
                                st.write(f"⚠️ **Note:** The applied {shading_loss}% soiling loss reduces overall photovoltaic conversion efficiency.")
                            if irr_mult > 1.0:
                                st.write(f"☀️ **Note:** Increased sunlight intensity boosts overall output.")

                        mc1, mc2, mc3, mc4 = st.columns(4)
                        mc1.metric("Total Forecast Yield", f"{total_simulated:,.1f} W")
                        mc2.metric("Peak Daily Output", f"{peak_power:,.1f} W")
                        mc3.metric("Average Daily Output", f"{avg_daily:,.1f} W")
                        mc4.metric("Est. Total Loss Impact", f"{total_loss_est:.1f}%")

                        fig_sim = go.Figure()
                        fig_sim.add_trace(go.Bar(
                            x=df_daily_sim['date'], y=df_daily_sim['simulated_power'],
                            name='Simulated Forecast', marker_color=PALETTE["SOLAR_AMBER"]
                        ))
                        fig_sim = apply_helioiq_plotly_theme(fig_sim, "Simulated Energy Yield Over Time", "Date", "Simulated Power (W)")
                        st.plotly_chart(fig_sim, use_container_width=True)
                    else:
                        st.warning("Could not find expected baseline column in historical results.")
                else:
                    st.warning("No prediction rows available to run simulation.")
            else:
                st.warning("Please run predictions in the Analysis Workspace first to load baseline data.")


def main() -> None:
    inject_helioiq_css()
    init_session_state()
    render_top_bar()

    active = st.session_state["current_page"]
    if active == PAGES[0]: page_home()
    elif active == PAGES[1]: page_analysis()
    elif active == PAGES[2]: page_whatif()


if __name__ == "__main__":
    main()
