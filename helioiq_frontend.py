import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# =====================================================================
# 1. CONFIGURATION & HELIOIQ COLOUR PALETTE CONSTANTS
# =====================================================================
API_BASE_URL = os.getenv("HELIOIQ_API_URL", "http://127.0.0.1:8000").rstrip("/")

# HelioIQ Colour Palette Guide constants
PALETTE = {
    "BLACK": "#000000",          
    "MIDNIGHT_NAVY": "#000914",  
    "WHITE": "#FFFFFF",          
    "ELECTRIC_CYAN": "#1FC3FF",  
    "STEEL_BLUE": "#16324F",     
    "MUTED_GREY": "#8CA3B8",     
    "ICE_BLUE": "#B8EDFF",       
    "SOFT_WHITE": "#EAF2F8",     
    "GREEN": "#35D07F",          
    "AMBER": "#FFC857",          
    "RED": "#FF5D6C",            
}

# The sidebar keeps the numbers to maintain correct vertical ordering
PAGES = [
    "01 Home / Dashboard",
    "02 Dataset Management",
    "03 Model Lab",
    "04 Performance Analysis",
    "05 Anomaly Detection",
    "06 What-if Simulator",
    "07 Models & Workspaces",
]

WORKSPACE_REGEX = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


# =====================================================================
# 2. PAGE SETUP & THEME-AWARE CSS (USING NATIVE CONTAINERS)
# =====================================================================
st.set_page_config(
    page_title="HelioIQ | Solar PV Performance Intelligence",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_helioiq_css() -> None:
    """
    Styles native Streamlit bordered containers, metrics, sidebar tiles, and buttons
    using the HelioIQ colour palette while supporting Light and Dark modes.
    """
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, .stApp { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
    .block-container { padding-top: 1.4rem !important; padding-bottom: 3rem !important; max-width: 1420px !important; }
    h1, h2, h3, h4, h5, h6 { font-family: 'Inter', sans-serif !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
    
    /* Native Bordered Containers (Bento Grid Cards) */
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: color-mix(in srgb, var(--secondary-background-color) 90%, __MIDNIGHT_NAVY__ 10%) !important; border: 1px solid color-mix(in srgb, __STEEL_BLUE__ 75%, var(--text-color) 25%) !important; border-radius: 10px !important; padding: 0.35rem !important; transition: border-color 0.2s ease, box-shadow 0.2s ease !important; }
    [data-testid="stVerticalBlockBorderWrapper"]:hover { border-color: __ELECTRIC_CYAN__ !important; box-shadow: 0 4px 18px rgba(31, 195, 255, 0.08) !important; }
    
    /* Metric Containers */
    [data-testid="stMetric"] { background-color: color-mix(in srgb, var(--secondary-background-color) 90%, __MIDNIGHT_NAVY__ 10%) !important; border: 1px solid color-mix(in srgb, __STEEL_BLUE__ 75%, var(--text-color) 25%) !important; border-radius: 10px !important; padding: 0.9rem 1.1rem !important; }
    [data-testid="stMetricLabel"] { color: __MUTED_GREY__ !important; font-size: 0.78rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.04em !important; }
    [data-testid="stMetricValue"] { font-weight: 800 !important; font-size: 1.45rem !important; }
    
    /* Sidebar Navigation Grid Tiles */
    [data-testid="stSidebar"] { border-right: 1px solid color-mix(in srgb, __STEEL_BLUE__ 75%, var(--text-color) 25%) !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] { display: grid !important; grid-template-columns: 1fr !important; gap: 0.4rem !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label { background-color: color-mix(in srgb, var(--secondary-background-color) 88%, __MIDNIGHT_NAVY__ 12%) !important; border: 1px solid color-mix(in srgb, __STEEL_BLUE__ 70%, var(--text-color) 30%) !important; border-radius: 8px !important; padding: 0.6rem 0.85rem !important; margin: 0 !important; cursor: pointer !important; transition: all 0.16s ease !important; width: 100% !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label p { font-size: 0.88rem !important; font-weight: 600 !important; margin: 0 !important; color: var(--text-color) !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:hover { border-color: __ICE_BLUE__ !important; background-color: rgba(31, 195, 255, 0.08) !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { border-color: __ELECTRIC_CYAN__ !important; border-left: 4px solid __ELECTRIC_CYAN__ !important; background-color: rgba(31, 195, 255, 0.14) !important; }
    [data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: __ELECTRIC_CYAN__ !important; font-weight: 700 !important; }
    
    /* Primary Buttons */
    .stButton > button, .stFormSubmitButton > button { background-color: __ELECTRIC_CYAN__ !important; color: __MIDNIGHT_NAVY__ !important; border: 1px solid __ELECTRIC_CYAN__ !important; font-weight: 700 !important; font-size: 0.88rem !important; border-radius: 8px !important; padding: 0.5rem 1.1rem !important; transition: all 0.16s ease !important; }
    .stButton > button *, .stFormSubmitButton > button * { color: __MIDNIGHT_NAVY__ !important; font-weight: 700 !important; background: transparent !important; }
    .stButton > button:hover, .stFormSubmitButton > button:hover { background-color: __ICE_BLUE__ !important; border-color: __ICE_BLUE__ !important; color: __BLACK__ !important; box-shadow: 0 4px 12px rgba(31, 195, 255, 0.25) !important; }
    .stButton > button:disabled, .stFormSubmitButton > button:disabled { background-color: rgba(22, 50, 79, 0.35) !important; border-color: rgba(140, 163, 184, 0.3) !important; color: __MUTED_GREY__ !important; opacity: 0.6 !important; box-shadow: none !important; }
    .stButton > button:disabled *, .stFormSubmitButton > button:disabled * { color: __MUTED_GREY__ !important; }
    
    /* Status Badges */
    .status-badge { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.25rem 0.7rem; border-radius: 999px; font-size: 0.76rem; font-weight: 700; letter-spacing: 0.03em; }
    .status-healthy { background-color: rgba(53, 208, 127, 0.15); color: __GREEN__ !important; border: 1px solid __GREEN__; }
    .status-caution { background-color: rgba(255, 200, 87, 0.15); color: __AMBER__ !important; border: 1px solid __AMBER__; }
    .status-investigate { background-color: rgba(255, 93, 108, 0.15); color: __RED__ !important; border: 1px solid __RED__; }
    .status-neutral { background-color: rgba(31, 195, 255, 0.12); color: __ELECTRIC_CYAN__ !important; border: 1px solid __STEEL_BLUE__; }
    </style>
    """
    
    for key, hex_code in PALETTE.items():
        css = css.replace(f"__{key}__", hex_code)
        
    st.markdown(css, unsafe_allow_html=True)


# =====================================================================
# 3. SESSION STATE INITIALISATION
# =====================================================================
def init_session_state() -> None:
    defaults = {
        "current_page": PAGES[0],
        "health_data": None,
        "active_workspace": None,
        "active_model_version": None,
        "known_workspaces": [],
        "last_validation_result": None,
        "last_training_result": None,
        "last_historical_result": None,
        "last_summary_result": None,
        "last_anomaly_result": None,
        "last_whatif_result": None,
        "whatif_reset_counter": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def navigate_to(page_name: str, workspace: Optional[str] = None, version: Optional[str] = None) -> None:
    if workspace:
        st.session_state["active_workspace"] = workspace
        if workspace not in st.session_state["known_workspaces"]:
            st.session_state["known_workspaces"].append(workspace)
    if version:
        st.session_state["active_model_version"] = str(version)
    st.session_state["current_page"] = page_name
    st.rerun()


# =====================================================================
# 4. API COMMUNICATION & NATIVE ERROR DISPLAY
# =====================================================================
def format_form_value(val: Any) -> str:
    """Format form values cleanly so integer floats like 2.0 are sent as '2' if whole."""
    if isinstance(val, (dict, list)):
        return json.dumps(val)
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val)


def sanitize_api_message(msg: str) -> str:
    """Strip raw Python/dictionary syntax from API messages for a cleaner UI."""
    text = str(msg)
    text = text.replace("config.plant['location']", "Plant Location Override")
    text = text.replace("config.plant['rated_power_kw']", "Rated Capacity (kW) Setting")
    text = text.replace("PowerOptions(rated_power_w=...)", "Power Options JSON (Rated Power)")
    text = text.replace("prepare_pv_data(..., include_power=True)", "dataset preparation config")
    text = text.replace("dc_power_derived_total_w", "Derived DC Power")
    text = text.replace("dc_power", "Measured DC Power")
    return text


def api_call(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    timeout: int = 120,
) -> Tuple[bool, int, Any]:
    """Centralised HTTP helper for HelioIQ API."""
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    cleaned_data = None
    if data:
        cleaned_data = {
            k: format_form_value(v)
            for k, v in data.items()
            if v is not None and v != ""
        }
    cleaned_params = {
        k: format_form_value(v)
        for k, v in (params or {}).items()
        if v is not None and v != ""
    }

    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            params=cleaned_params or None,
            data=cleaned_data,
            files=files,
            json=json_body,
            timeout=timeout,
        )
    except requests.exceptions.ConnectionError:
        return (
            False,
            0,
            f"Cannot connect to HelioIQ API at {API_BASE_URL}. Ensure Uvicorn is running (uvicorn app.main:app --reload).",
        )
    except requests.exceptions.Timeout:
        return (
            False,
            0,
            f"Request to {endpoint} timed out after {timeout}s. Try a smaller date window or sample CSV.",
        )
    except requests.exceptions.RequestException as exc:
        return False, 0, f"Network error calling {endpoint}: {exc}"

    try:
        payload = response.json()
    except ValueError:
        payload = {"detail": response.text or f"HTTP {response.status_code}"}

    if 200 <= response.status_code < 300:
        return True, response.status_code, payload
    return False, response.status_code, payload


def render_api_error(status_code: int, payload: Any, context: str = "API Request") -> None:
    """Renders API errors using native Streamlit containers and alerts."""
    detail = payload.get("detail", payload) if isinstance(payload, dict) else str(payload)

    with st.container(border=True):
        st.error(f"■ **{context} Failed** {f'(HTTP {status_code})' if status_code else '(Network Error)'}")

        if isinstance(detail, list):
            for item in detail:
                if isinstance(item, dict):
                    loc = " → ".join(str(x) for x in item.get("loc", []))
                    msg = item.get("msg", str(item))
                    st.markdown(f"- **{loc}**: {sanitize_api_message(msg)}" if loc else f"- {sanitize_api_message(msg)}")
                else:
                    st.markdown(f"- {sanitize_api_message(item)}")
        elif isinstance(detail, dict):
            msg = detail.get("message") or detail.get("error") or detail.get("detail")
            if msg:
                st.write(sanitize_api_message(msg))
            st.json(detail)
        else:
            st.write(sanitize_api_message(detail))

        if status_code == 0:
            st.caption("💡 **Troubleshooting:** Verify the FastAPI server is running in your first terminal at http://127.0.0.1:8000.")
        elif status_code == 404:
            st.caption("💡 **Troubleshooting (404):** Train a model first and use the exact workspace and version returned by the API.")
        elif status_code == 422:
            st.caption("💡 **Troubleshooting (422):** Check whether your CSV matches the selected Dataset Profile ('trieste_q2' vs 'generic'), or check required columns, dates, and JSON configuration.")
        elif status_code == 503:
            st.caption("💡 **Troubleshooting (503):** The API could not load HelioIQ_Backend. Check HELIOIQ_BACKEND_PATH and restart Uvicorn.")


def render_status_pill(status_val: Any) -> None:
    """Render a single-line status badge with icon + text label."""
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

    html = f'<div style="margin-bottom:0.75rem;"><span class="status-badge {cls}">{sym} {raw.upper()} ({tag})</span></div>'
    st.markdown(html, unsafe_allow_html=True)


# =====================================================================
# 5. SHARED UI & PLOTLY CHART HELPERS
# =====================================================================
def apply_helioiq_plotly_theme(fig: go.Figure, title: str, xaxis_title: str, yaxis_title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        font=dict(family="Inter, Segoe UI, sans-serif"),
        xaxis=dict(
            title=dict(text=xaxis_title),
            gridcolor="rgba(22, 50, 79, 0.55)",
            linecolor=PALETTE["STEEL_BLUE"],
            zerolinecolor=PALETTE["STEEL_BLUE"],
        ),
        yaxis=dict(
            title=dict(text=yaxis_title),
            gridcolor="rgba(22, 50, 79, 0.55)",
            linecolor=PALETTE["STEEL_BLUE"],
            zerolinecolor=PALETTE["STEEL_BLUE"],
        ),
        legend=dict(bordercolor=PALETTE["STEEL_BLUE"], borderwidth=1),
        hovermode="x unified",
        margin=dict(l=50, r=30, t=55, b=50),
    )
    return fig


def render_top_bar() -> None:
    """Consistent top bar using a native bordered container and single-line badge."""
    ok, _, health = api_call("GET", "/health", timeout=5)
    if ok and isinstance(health, dict):
        st.session_state["health_data"] = health
        api_status = str(health.get("status", "unknown"))
        backend_info = health.get("backend", {})
        backend_avail = backend_info.get("available") if isinstance(backend_info, dict) else None
        if api_status.lower() == "ok" and backend_avail is not False:
            badge_html = '<span class="status-badge status-healthy">● API & BACKEND ONLINE</span>'
        else:
            badge_html = f'<span class="status-badge status-caution">▲ API {api_status.upper()} (DEGRADED)</span>'
    else:
        st.session_state["health_data"] = None
        badge_html = '<span class="status-badge status-investigate">■ API OFFLINE</span>'

    ws_html = ""
    if st.session_state.get("active_workspace"):
        ver = st.session_state.get("active_model_version") or "latest"
        ws_html = f'<span class="status-badge status-neutral" style="margin-right:0.5rem;">◆ WORKSPACE: {st.session_state["active_workspace"]} ({ver})</span>'

    with st.container(border=True):
        c_left, c_right = st.columns([3, 2])
        with c_left:
            st.markdown(
                f'<div style="padding:0.2rem 0;"><span style="font-size:1.35rem; font-weight:800; letter-spacing:0.04em;">HELIO<span style="color:{PALETTE["ELECTRIC_CYAN"]};">IQ</span></span> <span style="color:{PALETTE["MUTED_GREY"]}; margin-left:0.75rem; font-size:0.9rem;">Know what your system should do. Know when it doesn\'t.</span></div>',
                unsafe_allow_html=True,
            )
        with c_right:
            st.markdown(
                f'<div style="text-align:right; padding:0.25rem 0;">{ws_html}{badge_html}</div>',
                unsafe_allow_html=True,
            )


def render_common_dataset_options(prefix: str) -> Tuple[str, Optional[float], Optional[str], Optional[str]]:
    """Shared dataset configuration controls in a clean 2-column grid without backtick code pills."""
    col1, col2 = st.columns(2)
    with col1:
        dataset_type = st.selectbox(
            "Dataset Profile",
            options=["trieste_q2", "generic"],
            index=0,
            key=f"{prefix}_dataset",
            help="Select 'trieste_q2' for the Trieste dataset or 'generic' for custom CSV column schemas.",
        )
    with col2:
        specify_utc = st.checkbox(
            "Specify Fixed UTC Offset (Hours)",
            value=False,
            key=f"{prefix}_specify_utc",
            help="Enable when computing solar-position features. Do not guess the UTC offset.",
        )
        utc_offset = None
        if specify_utc:
            utc_offset = st.number_input(
                "UTC Offset (Hours)",
                min_value=-12.0,
                max_value=14.0,
                value=1.0,
                step=0.5,
                key=f"{prefix}_utc_offset",
            )

    with st.expander("Advanced Backend Configuration (Optional Column Map & Power Options JSON)", expanded=False):
        st.caption("Optional JSON strings passed directly to the backend without frontend modification.")
        g1, g2 = st.columns(2)
        with g1:
            c_map = st.text_area(
                "Column Map JSON",
                placeholder='{"timestamp": "DateTime", "irradiance": "POA"}',
                height=72,
                key=f"{prefix}_colmap",
            )
        with g2:
            p_opts = st.text_area(
                "Power Options JSON",
                placeholder='{"dc_scaling": 1.0, "rated_power_w": 10000}',
                height=72,
                key=f"{prefix}_poweropts",
            )
    return dataset_type, utc_offset, c_map.strip() or None, p_opts.strip() or None


def build_multipart_file(uploaded_file: Any) -> Dict[str, Tuple[str, bytes, str]]:
    uploaded_file.seek(0)
    return {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}


def validate_json_string(raw_text: Optional[str], field_label: str) -> bool:
    if not raw_text:
        return True
    try:
        json.loads(raw_text)
        return True
    except ValueError as exc:
        st.error(f"Invalid JSON in {field_label}: {exc}")
        return False


def extract_rows_from_payload(payload: Dict[str, Any]) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    candidate_keys = [
        "rows",
        "predictions",
        "data",
        "records",
        "timeseries",
        "series",
        "results",
        "anomalies",
        "flagged_rows",
        "periods",
        "flagged_periods",
        "windows",
        "events",
    ]
    for key in candidate_keys:
        val = payload.get(key)
        if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
            return val, key
    for key, val in payload.items():
        if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
            return val, key
    return None, None


# =====================================================================
# 6. PAGE IMPLEMENTATIONS (01 TO 07)
# =====================================================================

# ---------------------------------------------------------------------
# PAGE 01: HOME / DASHBOARD 
# ---------------------------------------------------------------------
def page_home() -> None:
    st.caption("OVERVIEW & TELEMETRY")
    st.markdown("## Home / Dashboard")

    with st.container(border=True):
        c_welcome, c_url = st.columns([4, 1])
        with c_welcome:
            st.markdown("#### Solar PV Performance Intelligence Platform")
            st.write(
                "HelioIQ estimates expected solar PV power under observed environmental conditions, "
                "compares expected power with observed or defensibly derived power, flags persistent "
                "deviations for investigation, and supports hypothetical what-if simulation."
            )
        with c_url:
            st.caption("CONNECTED API")
            st.code(API_BASE_URL, language=None)

    col_h1, col_h2 = st.columns([4, 1])
    with col_h1:
        st.markdown("### Live API & Backend Connection")
    with col_h2:
        if st.button("↻ Refresh Status", use_container_width=True):
            st.rerun()

    ok, status_code, health_payload = api_call("GET", "/health", timeout=8)
    if ok and isinstance(health_payload, dict):
        st.session_state["health_data"] = health_payload
        status_str = str(health_payload.get("status", "unknown"))
        backend_obj = health_payload.get("backend", {})
        backend_avail = backend_obj.get("available") if isinstance(backend_obj, dict) else health_payload.get("backend_available")

        m1, m2, m3 = st.columns(3)
        m1.metric("API HTTP Status", f"{status_code} OK")
        m2.metric("Service Status", status_str.upper())
        m3.metric("Backend Engine", "Available (Loaded)" if backend_avail else "Degraded / Unavailable")

        with st.expander("View Raw Health Response Payload", expanded=False):
            st.json(health_payload)
    else:
        render_api_error(status_code, health_payload, context="GET /health Check")

    st.markdown("---")

    st.caption("APPLICATION MODULES")
    st.markdown("### Core Workflow & Analysis Grid")

    modules = [
        ("MODULE 02 • STEP 1", "1. Validate Dataset", "Upload a solar PV CSV file, verify schema compatibility, and inspect data quality reports.", "Open Dataset Management →", "02 Dataset Management", "mod_2"),
        ("MODULE 03 • STEP 2", "2. Train Models", "Train and compare Linear Regression and Random Forest models on chronological hold-out splits.", "Open Model Lab →", "03 Model Lab", "mod_3"),
        ("MODULE 04 • STEP 3", "3. Analyse Performance", "Compare expected model power against observed or derived DC power across time-series windows.", "Open Performance Analysis →", "04 Performance Analysis", "mod_4"),
        ("MODULE 05 • DIAGNOSTICS", "4. Anomaly Detection", "Identify persistent deviations and flag potential underperformance periods for investigation.", "Open Anomaly Detection →", "05 Anomaly Detection", "mod_5"),
        ("MODULE 06 • SCENARIOS", "5. What-if Simulator", "Adjust irradiance and temperature parameters to run hypothetical model re-predictions.", "Open What-if Simulator →", "06 What-if Simulator", "mod_6"),
        ("MODULE 07 • REGISTRY", "6. Models & Workspaces", "Browse saved model versions and inspect evaluation metadata for known workspaces.", "Open Models & Workspaces →", "07 Models & Workspaces", "mod_7"),
    ]

    row1 = st.columns(3)
    for idx in range(3):
        tag, title, desc, btn_label, target, key = modules[idx]
        with row1[idx]:
            with st.container(border=True, height=215):
                st.caption(tag)
                st.markdown(f"#### {title}")
                st.write(desc)
            if st.button(btn_label, key=key, use_container_width=True):
                navigate_to(target)

    row2 = st.columns(3)
    for idx in range(3, 6):
        tag, title, desc, btn_label, target, key = modules[idx]
        with row2[idx - 3]:
            with st.container(border=True, height=215):
                st.caption(tag)
                st.markdown(f"#### {title}")
                st.write(desc)
            if st.button(btn_label, key=key, use_container_width=True):
                navigate_to(target)

    st.markdown("---")
    st.caption("SESSION TELEMETRY")
    st.markdown("### Current Session Context & Latest API Results")
    col_ctx1, col_ctx2 = st.columns(2)

    with col_ctx1:
        with st.container(border=True, height=165):
            st.caption("ACTIVE MODEL REGISTRY")
            if st.session_state.get("active_workspace"):
                st.markdown("#### Active Workspace & Model")
                st.write(f"**Workspace:** `{st.session_state['active_workspace']}` | **Version:** `{st.session_state.get('active_model_version') or 'latest'}`")
            else:
                st.markdown("#### No Active Workspace / Model Yet")
                st.write("No model has been trained or queried in this session yet. Train a model in **03 Model Lab** or query **07 Models & Workspaces**.")

    with col_ctx2:
        with st.container(border=True, height=165):
            st.caption("DATA QUALITY CACHE")
            if st.session_state.get("last_validation_result"):
                st.markdown("#### Latest Dataset Validation Available")
                st.write("A validation response was received from `/datasets/validate` during this session.")
            else:
                st.markdown("#### No Dataset Validated Yet")
                st.write("Uploads are processed temporarily per request. Start in **02 Dataset Management** to validate your CSV.")


# ---------------------------------------------------------------------
# PAGE 02: DATASET MANAGEMENT
# ---------------------------------------------------------------------
def page_dataset_management() -> None:
    st.caption("DATA INGESTION & QUALITY")
    st.markdown("## Dataset Management")
    st.info(
        "**Scientific & Workflow Note:** CSV uploads use `multipart/form-data` and are processed temporarily per request. "
        "For the Trieste dataset (`trieste_q2`), the power target is **derived DC power**, not measured AC grid output."
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload Solar PV Dataset (CSV)",
            type=["csv"],
            help="Supported format: Comma-separated values (.csv) compatible with trieste_q2 or generic schemas.",
            key="validate_csv_uploader",
        )

        dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options("validate")

        if uploaded_file is not None:
            with st.expander("Raw CSV Source Preview (Unmodified Text View — First 10 Rows)", expanded=False):
                st.caption("Displayed strictly as raw strings without type coercion, rounding, or mutation.")
                try:
                    uploaded_file.seek(0)
                    preview_df = pd.read_csv(uploaded_file, nrows=10, dtype=str, keep_default_na=False)
                    st.dataframe(preview_df, use_container_width=True)
                except Exception as exc:
                    st.warning(f"Could not render local text preview: {exc}")

        validate_clicked = st.button(
            "Validate Dataset",
            disabled=(uploaded_file is None),
            use_container_width=True,
        )

    if validate_clicked and uploaded_file is not None:
        if not validate_json_string(col_map, "Column Map JSON") or not validate_json_string(power_opts, "Power Options JSON"):
            return

        form_data = {
            "dataset": dataset_type,
            "utc_offset_hours": utc_offset,
            "column_map": col_map,
            "power_options": power_opts,
        }

        with st.status("Sending CSV to API for validation...", expanded=True) as status_box:
            st.write(f"Uploading **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB) with profile **{dataset_type}**...")
            ok, status_code, payload = api_call(
                "POST",
                "/datasets/validate",
                data=form_data,
                files=build_multipart_file(uploaded_file),
            )
            if ok and isinstance(payload, dict):
                st.session_state["last_validation_result"] = payload
                status_box.update(label=f"Validation response received (HTTP {status_code})", state="complete", expanded=False)
            else:
                st.session_state["last_validation_result"] = None
                status_box.update(label=f"Validation failed (HTTP {status_code or 'Network Error'})", state="error", expanded=True)
                render_api_error(status_code, payload, context="POST /datasets/validate")

    result = st.session_state.get("last_validation_result")
    if isinstance(result, dict):
        st.markdown("---")
        st.markdown("### Validation Output")

        is_valid = result.get("valid", result.get("is_valid", result.get("status") == "ok"))
        status_label = "VALID" if is_valid is True else ("INVALID" if is_valid is False else str(result.get("status", "COMPLETED")))
        render_status_pill(status_label)

        metric_candidates = [
            ("Row Count", result.get("row_count", result.get("n_rows", result.get("rows")))),
            ("Column Count", result.get("column_count", result.get("n_columns"))),
            ("Dataset Profile", result.get("dataset", result.get("dataset_type", dataset_type))),
            ("Target Column", result.get("target_column", result.get("target"))),
        ]
        present_metrics = [(label, val) for label, val in metric_candidates if isinstance(val, (int, float, str))]
        if present_metrics:
            cols = st.columns(len(present_metrics))
            for idx, (label, val) in enumerate(present_metrics):
                cols[idx].metric(label, str(val))

        errors = result.get("errors", result.get("validation_errors", []))
        warnings = result.get("warnings", result.get("validation_warnings", []))

        if errors:
            with st.container(border=True):
                st.error(f"■ **Validation Errors ({len(errors) if isinstance(errors, list) else 1})**")
                for err in (errors if isinstance(errors, list) else [errors]):
                    st.markdown(f"- {sanitize_api_message(err)}")

        if warnings:
            with st.container(border=True):
                st.warning(f"▲ **Validation Warnings ({len(warnings) if isinstance(warnings, list) else 1})**")
                for warn in (warnings if isinstance(warnings, list) else [warnings]):
                    st.markdown(f"- {sanitize_api_message(warn)}")

        schema_info = result.get("schema", result.get("columns", result.get("column_details")))
        if schema_info is not None:
            with st.container(border=True):
                st.markdown("#### Returned Schema / Columns")
                if isinstance(schema_info, list):
                    if len(schema_info) > 0 and isinstance(schema_info[0], dict):
                        st.dataframe(pd.DataFrame(schema_info), use_container_width=True)
                    else:
                        st.dataframe(pd.DataFrame({"Column": schema_info}), use_container_width=True)
                elif isinstance(schema_info, dict):
                    st.json(schema_info)

        quality_info = result.get("quality", result.get("data_quality", result.get("summary", result.get("cleaning_summary"))))
        if quality_info is not None:
            with st.container(border=True):
                st.markdown("#### Data Quality Summary")
                
                if isinstance(quality_info, dict):
                    q_rows = quality_info.get("rows", "an unspecified number of")
                    q_start = quality_info.get("start", "an unknown start date")
                    q_end = quality_info.get("end", "an unknown end date")
                    q_target = quality_info.get("observed_power_column")
                    
                    summary_md = f"This dataset spans from **{q_start}** to **{q_end}** with a total of **{q_rows}** recorded intervals."
                    if q_target:
                         summary_md += f" The system successfully detected `{q_target}` as the primary power target."
                    else:
                         summary_md += " ⚠️ **No power target was automatically detected.** You must explicitly provide a Target Column Override when training."
                         
                    dupes = quality_info.get("duplicate_timestamps")
                    if dupes:
                        summary_md += f" Note: Found **{dupes}** duplicate timestamps."
                        
                    st.markdown(summary_md)
                    st.caption("Raw Quality Dictionary Metrics:")
                    st.json(quality_info)
                elif isinstance(quality_info, list):
                    st.dataframe(pd.DataFrame(quality_info), use_container_width=True)

        with st.expander("Full API Response JSON (/datasets/validate)", expanded=False):
            st.json(result)

        with st.container(border=True):
            st.markdown("#### What to Do Next")
            st.markdown(
                "1. If validation errors were flagged above, fix the missing columns, dataset profile (`trieste_q2` vs `generic`), or configuration JSON and re-validate.\n"
                "2. Once valid, proceed to **03 Model Lab** to train Linear Regression and Random Forest models, or go to **04 Performance Analysis** if you already have a saved workspace model."
            )
            n1, n2 = st.columns(2)
            with n1:
                if st.button("Proceed to 03 Model Lab →", use_container_width=True):
                    navigate_to("03 Model Lab")
            with n2:
                if st.button("Proceed to 04 Performance Analysis →", use_container_width=True):
                    navigate_to("04 Performance Analysis")


# ---------------------------------------------------------------------
# PAGE 03: MODEL LAB
# ---------------------------------------------------------------------
def page_model_lab() -> None:
    st.caption("MACHINE LEARNING & EVALUATION")
    st.markdown("## Model Lab")
    st.info(
        "**Model Evaluation Guardrail:** Each training request trains and evaluates Linear Regression and Random Forest models "
        "on a chronological hold-out split (latest observations held out for evaluation) and saves a new model version in the workspace."
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload Training CSV",
            type=["csv"],
            key="train_csv_uploader",
            help="CSV file containing environmental features and target power observations.",
        )

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            default_ws = st.session_state.get("active_workspace") or "trieste_demo"
            workspace = st.text_input(
                "Workspace Name (Required)",
                value=default_ws,
                max_chars=64,
                help="Letters, numbers, underscore (_), or hyphen (-); maximum 64 characters.",
            ).strip()
        with col_w2:
            test_fraction = st.number_input(
                "Chronological Hold-out Test Fraction",
                min_value=0.05,
                max_value=0.50,
                value=0.20,
                step=0.05,
                help="Default 0.2. The latest chronological portion of the dataset is held out for evaluation.",
            )

        dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options("train")

        with st.expander("Optional Target & Feature Overrides", expanded=False):
            st.caption("Only populate these fields if you know the backend's exact expected column names.")
            t1, t2 = st.columns(2)
            with t1:
                target_col = st.text_input("Target Column Override", value="").strip()
            with t2:
                features_raw = st.text_input("Features Override (comma-separated or JSON list)", value="").strip()

        train_clicked = st.button(
            "Train Models",
            disabled=(uploaded_file is None or not workspace),
            use_container_width=True,
        )

    if train_clicked and uploaded_file is not None:
        if not WORKSPACE_REGEX.match(workspace):
            st.error("Workspace must contain only letters, numbers, underscores, or hyphens (1–64 characters).")
            return
        if not validate_json_string(col_map, "Column Map JSON") or not validate_json_string(power_opts, "Power Options JSON"):
            return

        form_data = {
            "workspace": workspace,
            "dataset": dataset_type,
            "utc_offset_hours": utc_offset,
            "test_fraction": test_fraction,
            "target": target_col or None,
            "features": features_raw or None,
            "column_map": col_map,
            "power_options": power_opts,
        }
        with st.status("Training models via API...", expanded=True) as status_box:
            st.write(f"Uploading **{uploaded_file.name}** and training Random Forest & Linear Regression models...")
            ok, status_code, payload = api_call(
                "POST",
                "/models/train",
                data=form_data,
                files=build_multipart_file(uploaded_file),
                timeout=300,
            )

        if ok and isinstance(payload, dict):
            st.session_state["last_training_result"] = payload
            ret_ws = payload.get("workspace", workspace)
            ret_ver = payload.get("version", payload.get("model_version", "latest"))
            st.session_state["active_workspace"] = ret_ws
            st.session_state["active_model_version"] = str(ret_ver)
            if ret_ws not in st.session_state["known_workspaces"]:
                st.session_state["known_workspaces"].append(ret_ws)
        else:
            render_api_error(status_code, payload, context="POST /models/train")

    train_res = st.session_state.get("last_training_result")
    if isinstance(train_res, dict):
        st.markdown("---")
        st.markdown("### Training & Evaluation Results")
        render_status_pill("SUCCESS")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Workspace", str(train_res.get("workspace", st.session_state.get("active_workspace", "—"))))
        c2.metric("Saved Version", str(train_res.get("version", train_res.get("model_version", "latest"))))
        c3.metric(
            "Selected / Best Model",
            str(train_res.get("selected_model", train_res.get("best_model", train_res.get("default_model", "See table")))),
        )
        c4.metric(
            "Target Definition",
            str(train_res.get("target", train_res.get("target_column", "Derived DC / Power Target"))),
        )

        eval_info = (
            train_res.get("evaluation")
            or train_res.get("split")
            or train_res.get("holdout")
            or train_res.get("test_split")
            or train_res.get("data_split")
        )
        holdout_fields = {
            k: train_res[k]
            for k in [
                "train_rows",
                "test_rows",
                "n_train",
                "n_test",
                "test_fraction",
                "train_start",
                "train_end",
                "test_start",
                "test_end",
                "holdout_start",
                "holdout_end",
            ]
            if k in train_res and train_res[k] is not None
        }
        if isinstance(eval_info, dict):
            holdout_fields.update(eval_info)

        if holdout_fields:
            st.markdown("#### Held-out Evaluation Split Details")
            st.caption("Observations held out chronologically for model evaluation (as reported by the API):")
            st.dataframe(pd.DataFrame([holdout_fields]), use_container_width=True)

        model_rows = []
        raw_models = train_res.get("models", train_res.get("metrics", train_res.get("model_metrics", train_res.get("results"))))

        if isinstance(raw_models, dict):
            for m_name, m_data in raw_models.items():
                if isinstance(m_data, dict):
                    nested_metrics = m_data.get("metrics", m_data)
                    if isinstance(nested_metrics, dict):
                        row = {"Model": m_name}
                        row.update({k: v for k, v in nested_metrics.items() if isinstance(v, (int, float, str))})
                        model_rows.append(row)
        elif isinstance(raw_models, list):
            for item in raw_models:
                if isinstance(item, dict):
                    m_name = item.get("model", item.get("name", item.get("model_type", "Model")))
                    nested_metrics = item.get("metrics", item)
                    row = {"Model": m_name}
                    if isinstance(nested_metrics, dict):
                        row.update({k: v for k, v in nested_metrics.items() if isinstance(v, (int, float, str))})
                    model_rows.append(row)

        if model_rows:
            st.markdown("#### Linear Regression vs. Random Forest Comparison")
            comp_df = pd.DataFrame(model_rows)

            for col in list(comp_df.columns):
                if col.lower() in ("r2", "r_squared", "r2_score"):
                    if comp_df[col].isna().all():
                        comp_df.drop(columns=[col], inplace=True)

            st.dataframe(comp_df, use_container_width=True)

            mae_col = next((c for c in comp_df.columns if c.lower() in ("mae", "test_mae", "mean_absolute_error")), None)
            rmse_col = next((c for c in comp_df.columns if c.lower() in ("rmse", "test_rmse", "root_mean_squared_error")), None)

            if mae_col or rmse_col:
                fig = go.Figure()
                if mae_col:
                    fig.add_trace(
                        go.Bar(
                            x=comp_df["Model"],
                            y=pd.to_numeric(comp_df[mae_col], errors="coerce"),
                            name=f"MAE ({mae_col})",
                            marker_color=PALETTE["ELECTRIC_CYAN"],
                        )
                    )
                if rmse_col:
                    fig.add_trace(
                        go.Bar(
                            x=comp_df["Model"],
                            y=pd.to_numeric(comp_df[rmse_col], errors="coerce"),
                            name=f"RMSE ({rmse_col})",
                            marker_color=PALETTE["ICE_BLUE"],
                        )
                    )
                fig.update_layout(barmode="group")
                apply_helioiq_plotly_theme(
                    fig,
                    title="Held-out Evaluation Error Comparison (Lower is Better)",
                    xaxis_title="Trained Model Architecture",
                    yaxis_title="Error Magnitude (Target Power Units)",
                )
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)

        with st.expander("Full API Response JSON (/models/train)", expanded=False):
            st.json(train_res)


# ---------------------------------------------------------------------
# PAGE 04: PERFORMANCE ANALYSIS
# ---------------------------------------------------------------------
def page_performance_analysis() -> None:
    st.caption("HISTORICAL TELEMETRY & RESIDUALS")
    st.markdown("## Performance Analysis")
    st.info(
        "**Scientific Guardrails:**\n"
        "- **Derived DC Power ≠ Measured AC Power:** For the Trieste dataset, calculated DC targets represent derived DC power, not verified grid-delivered AC production.\n"
        "- **Predictions are Estimates:** Expected power is model output under observed environmental conditions, not ground truth."
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload Analysis CSV (Required per request)",
            type=["csv"],
            key="perf_csv_uploader",
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            workspace = st.text_input(
                "Workspace",
                value=st.session_state.get("active_workspace") or "trieste_demo",
                key="perf_ws",
            ).strip()
        with c2:
            version = st.text_input(
                "Model Version",
                value=st.session_state.get("active_model_version") or "latest",
                key="perf_ver",
            ).strip()
        with c3:
            group_by = st.selectbox(
                "Summary Aggregation",
                options=["", "day", "month"],
                format_func=lambda x: "None (Overall only)" if x == "" else f"Group by {x.capitalize()}",
                key="perf_groupby",
            )

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            start_window = st.text_input("Start Date/Time (Optional)", placeholder="YYYY-MM-DD", key="perf_start").strip()
        with d2:
            end_window = st.text_input("End Date/Time (Optional)", placeholder="YYYY-MM-DD", key="perf_end").strip()
        with d3:
            include_rows = st.checkbox("Include Per-Row Predictions", value=True, key="perf_inc_rows")
        with d4:
            max_rows = st.number_input("Max Returned Rows", min_value=10, max_value=50000, value=2000, step=100, key="perf_max_rows")

        dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options("perf")

        run_perf = st.button(
            "Run Historical Predictions & Performance Summary",
            disabled=(uploaded_file is None or not workspace),
            use_container_width=True,
        )

    if run_perf and uploaded_file is not None:
        if not validate_json_string(col_map, "Column Map JSON") or not validate_json_string(power_opts, "Power Options JSON"):
            return

        common_form = {
            "workspace": workspace,
            "version": version or "latest",
            "dataset": dataset_type,
            "utc_offset_hours": utc_offset,
            "start": start_window or None,
            "end": end_window or None,
            "include_rows": include_rows,
            "max_rows": int(max_rows),
            "column_map": col_map,
            "power_options": power_opts,
        }

        with st.status("Generating historical predictions and performance summary...", expanded=True):
            st.write("Calling `/predictions/historical`...")
            ok_hist, code_hist, payload_hist = api_call(
                "POST",
                "/predictions/historical",
                data=common_form,
                files=build_multipart_file(uploaded_file),
                timeout=180,
            )
            st.write("Calling `/performance/summary`...")
            summary_form = dict(common_form)
            if group_by:
                summary_form["group_by"] = group_by
            ok_sum, code_sum, payload_sum = api_call(
                "POST",
                "/performance/summary",
                data=summary_form,
                files=build_multipart_file(uploaded_file),
                timeout=180,
            )

        if ok_hist and isinstance(payload_hist, dict):
            st.session_state["last_historical_result"] = payload_hist
            st.session_state["active_workspace"] = workspace
            st.session_state["active_model_version"] = version or "latest"
        else:
            render_api_error(code_hist, payload_hist, context="POST /predictions/historical")

        if ok_sum and isinstance(payload_sum, dict):
            st.session_state["last_summary_result"] = payload_sum
        else:
            render_api_error(code_sum, payload_sum, context="POST /performance/summary")

    hist_res = st.session_state.get("last_historical_result")
    sum_res = st.session_state.get("last_summary_result")

    if isinstance(sum_res, dict):
        st.markdown("---")
        st.markdown("### Aggregate Performance Summary")
        metrics_block = sum_res.get("summary", sum_res.get("metrics", sum_res))
        if isinstance(metrics_block, dict):
            scalar_items = [(k, v) for k, v in metrics_block.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)]
            if scalar_items:
                cols = st.columns(min(4, len(scalar_items)))
                for idx, (k, v) in enumerate(scalar_items[:8]):
                    val_str = f"{v:,.3f}" if isinstance(v, float) else str(v)
                    cols[idx % len(cols)].metric(k.replace("_", " ").title(), val_str)

        grouped_rows, grp_key = extract_rows_from_payload(sum_res)
        if grouped_rows:
            st.markdown(f"#### Grouped Performance Breakdown ({grp_key})")
            st.dataframe(pd.DataFrame(grouped_rows), use_container_width=True)

        with st.expander("Full /performance/summary JSON Response", expanded=False):
            st.json(sum_res)

    if isinstance(hist_res, dict):
        st.markdown("---")
        st.markdown("### Expected vs. Observed / Derived Target Power")

        unit_label = hist_res.get("units", hist_res.get("power_unit", hist_res.get("unit", "W / kW (as defined by dataset)")))
        target_def = (
            "Derived DC Power Target (Trieste Calculated DC — Not Measured AC)"
            if dataset_type == "trieste_q2"
            else str(hist_res.get("target_column", hist_res.get("target", "Observed / Derived Target Power")))
        )

        rows, _ = extract_rows_from_payload(hist_res)
        if rows:
            df = pd.DataFrame(rows)
            time_col = next(
                (c for c in df.columns if any(t in c.lower() for t in ["time", "date", "timestamp", "dt", "period"])),
                df.columns[0],
            )
            exp_col = next(
                (c for c in df.columns if any(k in c.lower() for k in ["expected", "predicted", "prediction", "y_pred", "model_power", "pred"])),
                None,
            )
            obs_col = next(
                (c for c in df.columns if any(k in c.lower() for k in ["observed", "derived", "actual", "target", "y_true", "dc_power", "power_dc"]) and c != exp_col),
                None,
            )
            res_col = next(
                (c for c in df.columns if any(k in c.lower() for k in ["residual", "error", "deviation", "diff", "delta"])),
                None,
            )

            time_range_str = f"{df[time_col].iloc[0]} to {df[time_col].iloc[-1]}" if len(df) > 0 else "N/A"
            st.caption(f"**Target Definition:** {target_def} | **Units:** {unit_label} | **Displayed Time Range:** {time_range_str} ({len(df)} observations)")

            if exp_col or obs_col:
                fig_ts = go.Figure()
                if obs_col:
                    fig_ts.add_trace(
                        go.Scatter(
                            x=df[time_col],
                            y=pd.to_numeric(df[obs_col], errors="coerce"),
                            mode="lines",
                            name=f"Observed / Derived Target ({obs_col})",
                            line=dict(color=PALETTE["MUTED_GREY"], width=1.8),
                        )
                    )
                if exp_col:
                    fig_ts.add_trace(
                        go.Scatter(
                            x=df[time_col],
                            y=pd.to_numeric(df[exp_col], errors="coerce"),
                            mode="lines",
                            name=f"Expected Power — Model Estimate ({exp_col})",
                            line=dict(color=PALETTE["ELECTRIC_CYAN"], width=2.2),
                        )
                    )
                apply_helioiq_plotly_theme(
                    fig_ts,
                    title=f"Expected vs. {target_def} ({time_range_str})",
                    xaxis_title=f"Timestamp ({time_col})",
                    yaxis_title=f"Power ({unit_label})",
                )
                st.plotly_chart(fig_ts, theme="streamlit", use_container_width=True)

            if res_col:
                fig_res = go.Figure()
                fig_res.add_trace(
                    go.Scatter(
                        x=df[time_col],
                        y=pd.to_numeric(df[res_col], errors="coerce"),
                        mode="lines",
                        name=f"Residual / Deviation ({res_col})",
                        line=dict(color=PALETTE["ICE_BLUE"], width=1.6),
                        fill="tozeroy",
                        fillcolor="rgba(22, 50, 79, 0.35)",
                    )
                )
                apply_helioiq_plotly_theme(
                    fig_res,
                    title=f"Returned Residual / Error Series ({res_col})",
                    xaxis_title=f"Timestamp ({time_col})",
                    yaxis_title=f"Residual ({unit_label})",
                )
                st.plotly_chart(fig_res, theme="streamlit", use_container_width=True)

            with st.expander("Inspect Returned Historical Prediction Rows", expanded=False):
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No per-row series returned in this response. Ensure 'Include Per-Row Predictions' is enabled to plot time-series points.")

        with st.expander("Full /predictions/historical JSON Response", expanded=False):
            st.json(hist_res)


# ---------------------------------------------------------------------
# PAGE 05: ANOMALY DETECTION
# ---------------------------------------------------------------------
def page_anomaly_detection() -> None:
    st.caption("DEVIATION DIAGNOSTICS")
    st.markdown("## Anomaly Detection")
    st.warning(
        "**Investigation Guardrail:** Flagged periods indicate **potential underperformance requiring investigation**, "
        "not confirmed inverter, panel, or equipment faults. Thresholds are prototype defaults and have not been calibrated against labelled real faults."
    )

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload CSV for Anomaly Analysis",
            type=["csv"],
            key="anom_csv_uploader",
        )

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            workspace = st.text_input(
                "Workspace",
                value=st.session_state.get("active_workspace") or "trieste_demo",
                key="anom_ws",
            ).strip()
        with c2:
            version = st.text_input(
                "Model Version",
                value=st.session_state.get("active_model_version") or "latest",
                key="anom_ver",
            ).strip()
        with c3:
            start_win = st.text_input("Start Window (Optional)", placeholder="YYYY-MM-DD", key="anom_start").strip()
        with c4:
            end_win = st.text_input("End Window (Optional)", placeholder="YYYY-MM-DD", key="anom_end").strip()

        include_rows = st.checkbox("Include Row-Level Anomaly Details", value=True, key="anom_inc_rows")
        dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options("anom")

        run_anom = st.button(
            "Analyse Potential Anomalies",
            disabled=(uploaded_file is None or not workspace),
            use_container_width=True,
        )

    if run_anom and uploaded_file is not None:
        if not validate_json_string(col_map, "Column Map JSON") or not validate_json_string(power_opts, "Power Options JSON"):
            return

        form_data = {
            "workspace": workspace,
            "version": version or "latest",
            "dataset": dataset_type,
            "utc_offset_hours": utc_offset,
            "start": start_win or None,
            "end": end_win or None,
            "include_rows": include_rows,
            "column_map": col_map,
            "power_options": power_opts,
        }
        with st.spinner("Analysing persistent deviations via POST /anomalies/analyze..."):
            ok, status_code, payload = api_call(
                "POST",
                "/anomalies/analyze",
                data=form_data,
                files=build_multipart_file(uploaded_file),
                timeout=180,
            )

        if ok and isinstance(payload, dict):
            st.session_state["last_anomaly_result"] = payload
        else:
            render_api_error(status_code, payload, context="POST /anomalies/analyze")

    anom_res = st.session_state.get("last_anomaly_result")
    if isinstance(anom_res, dict):
        st.markdown("---")
        st.markdown("### Potential Underperformance & Deviation Summary")

        summary_obj = anom_res.get("summary", anom_res)
        overall_status = (
            anom_res.get("status")
            or (summary_obj.get("status") if isinstance(summary_obj, dict) else None)
            or anom_res.get("severity")
        )
        anom_count = (
            anom_res.get("anomaly_count")
            if "anomaly_count" in anom_res
            else (
                summary_obj.get("anomaly_count", summary_obj.get("flagged_count", summary_obj.get("n_anomalies")))
                if isinstance(summary_obj, dict)
                else None
            )
        )

        if overall_status is not None:
            render_status_pill(overall_status)
        elif isinstance(anom_count, int):
            render_status_pill("NORMAL (0 FLAGGED)" if anom_count == 0 else f"{anom_count} FLAGGED FOR INVESTIGATION")

        if isinstance(summary_obj, dict):
            scalars = [(k, v) for k, v in summary_obj.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)]
            if scalars:
                cols = st.columns(min(4, len(scalars)))
                for idx, (k, v) in enumerate(scalars[:8]):
                    val_str = f"{v:,.3f}" if isinstance(v, float) else str(v)
                    cols[idx % len(cols)].metric(k.replace("_", " ").title(), val_str)

        for key_candidate, title_label in [
            ("flagged_periods", "Flagged Time Periods for Investigation"),
            ("periods", "Flagged Time Periods for Investigation"),
            ("events", "Flagged Deviation Events"),
            ("anomalies", "Flagged Observations / Anomalies"),
            ("rows", "Analysed Observations"),
        ]:
            records = anom_res.get(key_candidate)
            if isinstance(records, list) and len(records) > 0 and isinstance(records[0], dict):
                st.markdown(f"#### {title_label} ({len(records)} records)")
                df_records = pd.DataFrame(records)
                st.dataframe(df_records, use_container_width=True)

                time_col = next((c for c in df_records.columns if any(t in c.lower() for t in ["time", "date", "start", "timestamp"])), None)
                dev_col = next((c for c in df_records.columns if any(d in c.lower() for d in ["deviation", "residual", "error", "deficit", "diff"])), None)
                if time_col and dev_col:
                    fig_anom = go.Figure()
                    fig_anom.add_trace(
                        go.Scatter(
                            x=df_records[time_col],
                            y=pd.to_numeric(df_records[dev_col], errors="coerce"),
                            mode="lines+markers",
                            name=f"Deviation ({dev_col})",
                            line=dict(color=PALETTE["AMBER"], width=1.8),
                            marker=dict(color=PALETTE["RED"], size=6, symbol="diamond"),
                        )
                    )
                    apply_helioiq_plotly_theme(
                        fig_anom,
                        title=f"Flagged Potential Underperformance Deviations ({dev_col})",
                        xaxis_title=f"Time ({time_col})",
                        yaxis_title=f"Deviation ({dev_col})",
                    )
                    st.plotly_chart(fig_anom, theme="streamlit", use_container_width=True)
                break

        with st.container(border=True):
            st.markdown("#### Investigation Prompt")
            st.write(
                "Review flagged timestamps against local irradiance sensor cleaning logs, shading conditions, "
                "curtailment schedules, or data logger dropouts before scheduling field maintenance. "
                "Do not treat statistical deviation flags alone as confirmed hardware failure."
            )

        with st.expander("Full /anomalies/analyze JSON Response", expanded=False):
            st.json(anom_res)


# ---------------------------------------------------------------------
# PAGE 06: WHAT-IF SIMULATOR
# ---------------------------------------------------------------------
def page_whatif_simulator() -> None:
    st.caption("HYPOTHETICAL SCENARIO MODELLING")
    st.markdown("## What-if Simulator")
    st.info(
        "**Simulation Guardrail:** What-if outputs are **hypothetical statistical model re-predictions** under adjusted scenario inputs. "
        "They are not physical PV simulations or a guarantee of real-world energy production."
    )

    reset_key = st.session_state["whatif_reset_counter"]

    with st.container(border=True):
        uploaded_file = st.file_uploader(
            "Upload Baseline CSV for Simulation",
            type=["csv"],
            key=f"whatif_csv_{reset_key}",
        )

        c1, c2 = st.columns(2)
        with c1:
            workspace = st.text_input(
                "Workspace",
                value=st.session_state.get("active_workspace") or "trieste_demo",
                key=f"whatif_ws_{reset_key}",
            ).strip()
        with c2:
            version = st.text_input(
                "Model Version",
                value=st.session_state.get("active_model_version") or "latest",
                key=f"whatif_ver_{reset_key}",
            ).strip()

        st.markdown("#### Scenario Input Controls")
        st.caption("Adjust environmental scenario parameters with explicit units and validated ranges.")

        s1, s2, s3 = st.columns(3)
        with s1:
            irradiance_factor = st.number_input(
                "Irradiance Multiplier (ratio [×])",
                min_value=0.0,
                max_value=2.0,
                value=1.10,
                step=0.05,
                key=f"whatif_irr_factor_{reset_key}",
                help="E.g. 1.10 = +10% solar irradiance (W/m²). Validated range: 0.0× to 2.0×.",
            )
        with s2:
            irradiance_delta = st.number_input(
                "Irradiance Offset (W/m²)",
                min_value=-1000.0,
                max_value=1000.0,
                value=0.0,
                step=25.0,
                key=f"whatif_irr_delta_{reset_key}",
                help="Additive change to irradiance in W/m².",
            )
        with s3:
            temp_delta = st.number_input(
                "Temperature Offset (°C)",
                min_value=-30.0,
                max_value=30.0,
                value=0.0,
                step=1.0,
                key=f"whatif_temp_delta_{reset_key}",
                help="Additive shift to ambient/module temperature in °C.",
            )

        with st.expander("Custom Scenario JSON Override (Optional)", expanded=False):
            custom_scenario_json = st.text_area(
                "Scenario JSON",
                value="",
                placeholder='{"irradiance_scale": 1.1, "temperature_delta_c": 2.0}',
                key=f"whatif_custom_json_{reset_key}",
            ).strip()

        dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options(f"whatif_{reset_key}")

        btn_col1, btn_col2 = st.columns([3, 1])
        with btn_col1:
            run_sim = st.button(
                "Run Simulation",
                disabled=(uploaded_file is None or not workspace),
                use_container_width=True,
            )
        with btn_col2:
            if st.button("Reset Scenario Controls", use_container_width=True):
                st.session_state["whatif_reset_counter"] += 1
                st.session_state["last_whatif_result"] = None
                st.rerun()

    if run_sim and uploaded_file is not None:
        if (
            not validate_json_string(custom_scenario_json, "Scenario JSON")
            or not validate_json_string(col_map, "Column Map JSON")
            or not validate_json_string(power_opts, "Power Options JSON")
        ):
            return

        scenario_dict = {
            "irradiance_factor": irradiance_factor,
            "irradiance_scale": irradiance_factor,
            "irradiance_delta": irradiance_delta,
            "temperature_delta": temp_delta,
            "temperature_delta_c": temp_delta,
        }
        if custom_scenario_json:
            parsed_custom = json.loads(custom_scenario_json)
            if isinstance(parsed_custom, dict):
                scenario_dict.update(parsed_custom)

        form_data = {
            "workspace": workspace,
            "version": version or "latest",
            "dataset": dataset_type,
            "utc_offset_hours": utc_offset,
            "irradiance_factor": irradiance_factor,
            "irradiance_scale": irradiance_factor,
            "irradiance_delta": irradiance_delta,
            "temperature_delta": temp_delta,
            "temperature_delta_c": temp_delta,
            "scenario": json.dumps(scenario_dict),
            "adjustments": json.dumps(scenario_dict),
            "column_map": col_map,
            "power_options": power_opts,
        }

        with st.spinner("Running hypothetical what-if simulation via POST /simulations/what-if..."):
            ok, status_code, payload = api_call(
                "POST",
                "/simulations/what-if",
                data=form_data,
                files=build_multipart_file(uploaded_file),
                timeout=180,
            )

        if ok and isinstance(payload, dict):
            st.session_state["last_whatif_result"] = payload
        else:
            render_api_error(status_code, payload, context="POST /simulations/what-if")

    sim_res = st.session_state.get("last_whatif_result")
    if isinstance(sim_res, dict):
        st.markdown("---")
        st.markdown("### Hypothetical Simulation Output (Not a Real-World Production Guarantee)")
        render_status_pill("HYPOTHETICAL SIMULATION")

        summary_block = sim_res.get("summary", sim_res.get("comparison", sim_res.get("metrics", sim_res)))
        if isinstance(summary_block, dict):
            scalars = [(k, v) for k, v in summary_block.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)]
            if scalars:
                cols = st.columns(min(4, len(scalars)))
                for idx, (k, v) in enumerate(scalars[:8]):
                    val_str = f"{v:,.3f}" if isinstance(v, float) else str(v)
                    cols[idx % len(cols)].metric(k.replace("_", " ").title(), val_str)

        rows, _ = extract_rows_from_payload(sim_res)
        if rows:
            df_sim = pd.DataFrame(rows)
            time_col = next((c for c in df_sim.columns if any(t in c.lower() for t in ["time", "date", "timestamp"])), df_sim.columns[0])
            base_col = next((c for c in df_sim.columns if any(b in c.lower() for b in ["baseline", "expected", "original", "base"])), None)
            hyp_col = next((c for c in df_sim.columns if any(h in c.lower() for h in ["simulated", "what_if", "whatif", "hypothetical", "scenario_power"])), None)

            if base_col or hyp_col:
                fig_sim = go.Figure()
                if base_col:
                    fig_sim.add_trace(
                        go.Scatter(
                            x=df_sim[time_col],
                            y=pd.to_numeric(df_sim[base_col], errors="coerce"),
                            mode="lines",
                            name=f"Baseline Expected Power ({base_col})",
                            line=dict(color=PALETTE["MUTED_GREY"], width=1.8, dash="dot"),
                        )
                    )
                if hyp_col:
                    fig_sim.add_trace(
                        go.Scatter(
                            x=df_sim[time_col],
                            y=pd.to_numeric(df_sim[hyp_col], errors="coerce"),
                            mode="lines",
                            name=f"Hypothetical Simulated Output ({hyp_col})",
                            line=dict(color=PALETTE["ELECTRIC_CYAN"], width=2.2),
                        )
                    )
                apply_helioiq_plotly_theme(
                    fig_sim,
                    title="Hypothetical What-if Prediction vs. Baseline Model Estimate",
                    xaxis_title=f"Timestamp ({time_col})",
                    yaxis_title="Power (Dataset Target Units)",
                )
                st.plotly_chart(fig_sim, theme="streamlit", use_container_width=True)

            with st.expander("Inspect Returned Simulation Rows", expanded=False):
                st.dataframe(df_sim, use_container_width=True)

        with st.expander("Full /simulations/what-if JSON Response", expanded=False):
            st.json(sim_res)


# ---------------------------------------------------------------------
# PAGE 07: MODELS & WORKSPACES
# ---------------------------------------------------------------------
def page_models_workspaces() -> None:
    st.caption("MODEL REGISTRY & VERSIONING")
    st.markdown("## Models & Workspaces")
    st.info(
        "**API Architecture Note:** The HelioIQ API does not expose a global workspace-discovery endpoint. "
        "Enter a known workspace name below (or select one used earlier in this session) to query model versions and details."
    )

    known_ws = st.session_state.get("known_workspaces", [])
    with st.container(border=True):
        col_w1, col_w2 = st.columns([2, 1])
        with col_w1:
            default_ws = st.session_state.get("active_workspace") or (known_ws[0] if known_ws else "trieste_demo")
            workspace_input = st.text_input(
                "Enter Known Workspace Name",
                value=default_ws,
                max_chars=64,
            ).strip()
        with col_w2:
            if known_ws:
                selected_session_ws = st.selectbox(
                    "Or Pick Session Workspace",
                    options=["(use text input)"] + known_ws,
                )
                if selected_session_ws != "(use text input)":
                    workspace_input = selected_session_ws

        fetch_versions = st.button(
            f"List Versions in Workspace ({workspace_input or 'workspace'})",
            disabled=not workspace_input,
            use_container_width=True,
        )

    if fetch_versions and workspace_input:
        ok, status_code, payload = api_call("GET", f"/models/{workspace_input}")
        if ok:
            st.session_state["workspace_versions_payload"] = payload
            st.session_state["active_workspace"] = workspace_input
            if workspace_input not in st.session_state["known_workspaces"]:
                st.session_state["known_workspaces"].append(workspace_input)
        else:
            render_api_error(status_code, payload, context=f"GET /models/{workspace_input}")

    ws_payload = st.session_state.get("workspace_versions_payload")
    version_options = ["latest"]

    if ws_payload is not None:
        st.markdown("---")
        st.markdown(f"### Returned Model Versions for `{st.session_state.get('active_workspace')}`")

        if isinstance(ws_payload, dict):
            v_list = ws_payload.get("versions", ws_payload.get("models", ws_payload.get("items", [])))
            if isinstance(v_list, list):
                if len(v_list) > 0 and isinstance(v_list[0], dict):
                    df_v = pd.DataFrame(v_list)
                    st.dataframe(df_v, use_container_width=True)
                    ver_col = next((c for c in df_v.columns if "version" in c.lower() or "id" in c.lower()), df_v.columns[0])
                    version_options.extend([str(v) for v in df_v[ver_col].tolist() if str(v) not in version_options])
                else:
                    st.dataframe(pd.DataFrame({"Version": v_list}), use_container_width=True)
                    version_options.extend([str(v) for v in v_list if str(v) not in version_options])
            else:
                st.json(ws_payload)
        elif isinstance(ws_payload, list):
            st.dataframe(pd.DataFrame(ws_payload), use_container_width=True)

        with st.expander("Raw GET /models/{workspace} Response", expanded=False):
            st.json(ws_payload)

    st.markdown("---")
    st.markdown("### Inspect Specific Model Version")
    with st.container(border=True):
        v_col1, v_col2 = st.columns([3, 1])
        with v_col1:
            version_to_query = st.text_input(
                "Version Identifier (use 'latest' for newest)",
                value=version_options[-1] if len(version_options) > 1 else "latest",
            ).strip()
        with v_col2:
            st.write("")
            inspect_btn = st.button(
                "Get Version Details",
                disabled=not (workspace_input and version_to_query),
                use_container_width=True,
            )

    if inspect_btn and workspace_input and version_to_query:
        ok_v, code_v, payload_v = api_call("GET", f"/models/{workspace_input}/{version_to_query}")
        if ok_v and isinstance(payload_v, dict):
            st.session_state["version_detail_payload"] = payload_v
            st.session_state["active_workspace"] = workspace_input
            st.session_state["active_model_version"] = str(payload_v.get("version", version_to_query))
        else:
            render_api_error(code_v, payload_v, context=f"GET /models/{workspace_input}/{version_to_query}")

    ver_detail = st.session_state.get("version_detail_payload")
    if isinstance(ver_detail, dict):
        st.markdown("#### Returned Model Version Metadata")
        scalar_fields = {k: v for k, v in ver_detail.items() if isinstance(v, (int, float, str, bool))}
        if scalar_fields:
            st.dataframe(pd.DataFrame([scalar_fields]), use_container_width=True)

        st.json(ver_detail)

        st.markdown("#### Use Selected Model In:")
        nav1, nav2 = st.columns(2)
        selected_ws = st.session_state.get("active_workspace") or workspace_input
        selected_ver = st.session_state.get("active_model_version") or version_to_query
        with nav1:
            if st.button(
                f"Open 04 Performance Analysis ({selected_ws} / {selected_ver}) →",
                use_container_width=True,
            ):
                navigate_to("04 Performance Analysis", workspace=selected_ws, version=selected_ver)
        with nav2:
            if st.button(
                f"Open 06 What-if Simulator ({selected_ws} / {selected_ver}) →",
                use_container_width=True,
            ):
                navigate_to("06 What-if Simulator", workspace=selected_ws, version=selected_ver)


# =====================================================================
# 7. APPLICATION SHELL & SIDEBAR NAVIGATION GRID
# =====================================================================
def main() -> None:
    inject_helioiq_css()
    init_session_state()

    with st.sidebar:
        st.markdown(
            f'<div style="padding:0.2rem 0 0.8rem 0; border-bottom:1px solid {PALETTE["STEEL_BLUE"]}; margin-bottom:0.8rem;"><div style="font-size:1.5rem; font-weight:800; letter-spacing:0.04em;">HELIO<span style="color:{PALETTE["ELECTRIC_CYAN"]};">IQ</span></div><div style="color:{PALETTE["MUTED_GREY"]}; font-size:0.8rem;">Solar PV Performance Intelligence</div></div>',
            unsafe_allow_html=True,
        )
        st.caption("MODULE NAVIGATION GRID")

        selected_page = st.radio(
            "APPLICATION NAVIGATION",
            options=PAGES,
            index=PAGES.index(st.session_state["current_page"]),
            label_visibility="collapsed",
        )
        if selected_page != st.session_state["current_page"]:
            st.session_state["current_page"] = selected_page
            st.rerun()

        st.markdown("---")
        with st.container(border=True):
            st.caption("STATUS LEGEND")
            st.markdown(
                f'<div style="font-size:0.8rem; line-height:1.8;"><span style="color:{PALETTE["GREEN"]}; font-weight:700;">● Healthy / Normal</span><br/><span style="color:{PALETTE["AMBER"]}; font-weight:700;">▲ Watch / Caution</span><br/><span style="color:{PALETTE["RED"]}; font-weight:700;">■ Investigate Deviation</span></div>',
                unsafe_allow_html=True,
            )
            st.caption("API GATEWAY")
            st.code(API_BASE_URL, language=None)

    # Persistent Top Bar
    render_top_bar()

    # Route to selected page
    active = st.session_state["current_page"]
    if active == PAGES[0]:
        page_home()
    elif active == PAGES[1]:
        page_dataset_management()
    elif active == PAGES[2]:
        page_model_lab()
    elif active == PAGES[3]:
        page_performance_analysis()
    elif active == PAGES[4]:
        page_anomaly_detection()
    elif active == PAGES[5]:
        page_whatif_simulator()
    elif active == PAGES[6]:
        page_models_workspaces()


if __name__ == "__main__":
    main()
