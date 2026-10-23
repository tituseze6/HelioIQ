import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

# =====================================================================
# 1. CONFIGURATION & CONSTANTS
# =====================================================================
API_BASE_URL = os.getenv("HELIOIQ_API_URL", "http://127.0.0.1:8000").rstrip("/")

# HelioIQ Colour Palette Guide constants
PALETTE = {
    "BLACK": "#000000",          # Primary page background
    "MIDNIGHT_NAVY": "#000914",  # Secondary background (panels, cards, sidebar)
    "WHITE": "#FFFFFF",          # Primary text, key values, headings
    "ELECTRIC_CYAN": "#1FC3FF",  # Brand accent, active nav, primary actions/series
    "STEEL_BLUE": "#16324F",     # Borders, subtle dividers, secondary chart fills
    "MUTED_GREY": "#8CA3B8",     # Secondary text, axis ticks, timestamps, helper text
    "ICE_BLUE": "#B8EDFF",       # Hover states, soft highlights, pale cyan emphasis
    "SOFT_WHITE": "#EAF2F8",     # Alternative body text
    "GREEN": "#35D07F",          # Status: Normal / healthy
    "AMBER": "#FFC857",          # Status: Watch / caution
    "RED": "#FF5D6C",            # Status: Significant deviation / investigate
}

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
# 2. PAGE SETUP & VISUAL SYSTEM CSS
# =====================================================================
st.set_page_config(
    page_title="HelioIQ | Solar PV Performance Intelligence",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_helioiq_css() -> None:
    """Apply the HelioIQ Colour Palette Guide (80% dark, 15% content, 5% cyan accent)."""
    st.markdown(
        f"""
        <style>
        /* Main Canvas & App Background (#000000) */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
            background-color: {PALETTE['BLACK']} !important;
            color: {PALETTE['SOFT_WHITE']} !important;
        }}

        /* Sidebar & Secondary Containers (#000914) */
        [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
            background-color: {PALETTE['MIDNIGHT_NAVY']} !important;
            border-right: 1px solid {PALETTE['STEEL_BLUE']} !important;
        }}

        /* Typography */
        h1, h2, h3, h4, h5, h6, .helio-heading {{
            color: {PALETTE['WHITE']} !important;
            font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
            letter-spacing: -0.01em;
        }}
        p, li, span, div {{
            color: {PALETTE['SOFT_WHITE']};
        }}
        .helio-muted, small, .stCaption, [data-testid="stCaptionContainer"] {{
            color: {PALETTE['MUTED_GREY']} !important;
        }}

        /* Cards & Panels (#000914 with #16324F border) */
        .helio-card {{
            background-color: {PALETTE['MIDNIGHT_NAVY']};
            border: 1px solid {PALETTE['STEEL_BLUE']};
            border-radius: 8px;
            padding: 1.15rem 1.25rem;
            margin-bottom: 1rem;
        }}
        .helio-topbar {{
            background-color: {PALETTE['MIDNIGHT_NAVY']};
            border: 1px solid {PALETTE['STEEL_BLUE']};
            border-left: 4px solid {PALETTE['ELECTRIC_CYAN']};
            border-radius: 8px;
            padding: 0.9rem 1.25rem;
            margin-bottom: 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.75rem;
        }}
        .helio-guardrail {{
            background-color: {PALETTE['MIDNIGHT_NAVY']};
            border: 1px solid {PALETTE['STEEL_BLUE']};
            border-left: 4px solid {PALETTE['MUTED_GREY']};
            border-radius: 6px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            color: {PALETTE['SOFT_WHITE']};
            font-size: 0.9rem;
        }}

        /* Metric Containers */
        [data-testid="stMetric"] {{
            background-color: {PALETTE['MIDNIGHT_NAVY']};
            border: 1px solid {PALETTE['STEEL_BLUE']};
            border-radius: 8px;
            padding: 0.85rem 1rem;
        }}
        [data-testid="stMetricLabel"] {{
            color: {PALETTE['MUTED_GREY']} !important;
            font-size: 0.85rem !important;
        }}
        [data-testid="stMetricValue"] {{
            color: {PALETTE['WHITE']} !important;
            font-weight: 700 !important;
        }}

        /* Primary & Standard Buttons: Electric Cyan fill with Dark Text (#000914) for contrast */
        .stButton > button, .stFormSubmitButton > button {{
            background-color: {PALETTE['ELECTRIC_CYAN']} !important;
            color: {PALETTE['MIDNIGHT_NAVY']} !important;
            border: 1px solid {PALETTE['ELECTRIC_CYAN']} !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            padding: 0.45rem 1.1rem !important;
            transition: all 0.15s ease-in-out !important;
        }}
        .stButton > button *, .stFormSubmitButton > button * {{
            color: {PALETTE['MIDNIGHT_NAVY']} !important;
            font-weight: 700 !important;
        }}
        .stButton > button:hover, .stFormSubmitButton > button:hover {{
            background-color: {PALETTE['ICE_BLUE']} !important;
            border-color: {PALETTE['ICE_BLUE']} !important;
            color: {PALETTE['BLACK']} !important;
        }}
        .stButton > button:disabled, .stFormSubmitButton > button:disabled {{
            background-color: {PALETTE['STEEL_BLUE']} !important;
            border-color: {PALETTE['STEEL_BLUE']} !important;
            color: {PALETTE['MUTED_GREY']} !important;
            opacity: 0.65 !important;
        }}

        /* Inputs, Selectboxes, File Uploaders, Expanders */
        .stTextInput input, .stNumberInput input, .stTextArea textarea,
        [data-baseweb="select"] > div, [data-testid="stFileUploaderDropzone"] {{
            background-color: {PALETTE['MIDNIGHT_NAVY']} !important;
            color: {PALETTE['WHITE']} !important;
            border: 1px solid {PALETTE['STEEL_BLUE']} !important;
            border-radius: 6px !important;
        }}
        .stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus {{
            border-color: {PALETTE['ELECTRIC_CYAN']} !important;
            box-shadow: 0 0 0 1px {PALETTE['ELECTRIC_CYAN']} !important;
        }}
        [data-testid="stExpander"] {{
            background-color: {PALETTE['MIDNIGHT_NAVY']} !important;
            border: 1px solid {PALETTE['STEEL_BLUE']} !important;
            border-radius: 8px !important;
        }}

        /* Dividers */
        hr {{
            border-color: {PALETTE['STEEL_BLUE']} !important;
        }}

        /* Status Badges (Always pair colour with icon + explicit text label) */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }}
        .status-healthy {{
            background-color: rgba(53, 208, 127, 0.14);
            color: {PALETTE['GREEN']} !important;
            border: 1px solid {PALETTE['GREEN']};
        }}
        .status-caution {{
            background-color: rgba(255, 200, 87, 0.14);
            color: {PALETTE['AMBER']} !important;
            border: 1px solid {PALETTE['AMBER']};
        }}
        .status-investigate {{
            background-color: rgba(255, 93, 108, 0.14);
            color: {PALETTE['RED']} !important;
            border: 1px solid {PALETTE['RED']};
        }}
        .status-neutral {{
            background-color: rgba(31, 195, 255, 0.12);
            color: {PALETTE['ELECTRIC_CYAN']} !important;
            border: 1px solid {PALETTE['STEEL_BLUE']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =====================================================================
# 3. SESSION STATE INITIALISATION
# =====================================================================
def init_session_state() -> None:
    defaults = {
        "current_page": PAGES[0],
        "health_data": None,
        "active_workspace": None,       # Set only when confirmed/returned by API
        "active_model_version": None,   # Set only when confirmed/returned by API
        "known_workspaces": [],         # Workspaces confirmed via API during session
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
# 4. API COMMUNICATION & ERROR HANDLING
# =====================================================================
def api_call(
    method: str,
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    files: Optional[Dict[str, Any]] = None,
    json_body: Optional[Dict[str, Any]] = None,
    timeout: int = 120,
) -> Tuple[bool, int, Any]:
    """
    Centralised HTTP helper for HelioIQ API.
    - Never sets manual JSON content-type headers on multipart/form-data requests.
    - Parses error details cleanly across 404, 422, 503, and network failures.
    """
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    cleaned_data = None
    if data:
        cleaned_data = {
            k: (json.dumps(v) if isinstance(v, (dict, list)) else str(v))
            for k, v in data.items()
            if v is not None and v != ""
        }
    cleaned_params = {k: v for k, v in (params or {}).items() if v is not None and v != ""}

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
            f"Cannot connect to HelioIQ API at {API_BASE_URL}. Ensure Uvicorn is running (`uvicorn app.main:app --reload`).",
        )
    except requests.exceptions.Timeout:
        return (
            False,
            0,
            f"Request to {endpoint} timed out after {timeout}s. Large CSV uploads run synchronously; try a smaller date window or sample.",
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
    """Render readable, actionable error states using the API's `detail` field."""
    detail = payload.get("detail", payload) if isinstance(payload, dict) else str(payload)
    if isinstance(detail, list):
        formatted_items = []
        for item in detail:
            if isinstance(item, dict):
                loc = " -> ".join(str(x) for x in item.get("loc", []))
                msg = item.get("msg", str(item))
                formatted_items.append(f"- **{loc}**: {msg}" if loc else f"- {msg}")
            else:
                formatted_items.append(f"- {item}")
        detail_str = "\n".join(formatted_items)
    elif isinstance(detail, dict):
        detail_str = json.dumps(detail, indent=2)
    else:
        detail_str = str(detail)

    hint = ""
    if status_code == 0:
        hint = "Verify the FastAPI server is running at `http://127.0.0.1:8000`."
    elif status_code == 404:
        hint = "404 Not Found: Train a model first and use the exact workspace and version returned by the API."
    elif status_code == 422:
        hint = "422 Unprocessable Entity: Check required form fields, dataset type, date formats, JSON syntax, workspace characters, and required CSV columns."
    elif status_code == 503:
        hint = "503 Service Unavailable: The API could not load `HelioIQ_Backend`. Check `HELIOIQ_BACKEND_PATH` and restart Uvicorn."

    st.markdown(
        f"""
        <div class="helio-card" style="border-left: 4px solid {PALETTE['RED']};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="color:{PALETTE['WHITE']};">{context} Failed {f'(HTTP {status_code})' if status_code else ''}</strong>
                <span class="status-badge status-investigate">■ ERROR {status_code or 'NETWORK'}</span>
            </div>
            <div style="margin-top:0.6rem; color:{PALETTE['SOFT_WHITE']}; white-space:pre-wrap;">{detail_str}</div>
            {f'<div class="helio-muted" style="margin-top:0.5rem; font-size:0.85rem;">💡 <strong>Troubleshooting:</strong> {hint}</div>' if hint else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_status_badge(status_val: Any) -> str:
    """
    Map API status strings to Green / Amber / Red badges with non-colour indicators
    (icons + text labels) per the Colour Palette Guide accessibility rules.
    """
    raw = str(status_val or "unknown").strip()
    low = raw.lower()
    if any(k in low for k in ["ok", "healthy", "normal", "valid", "success", "low", "none", "pass"]):
        return f'<span class="status-badge status-healthy">● {raw.upper()} (NORMAL)</span>'
    if any(k in low for k in ["degraded", "watch", "caution", "warning", "warn", "medium", "moderate"]):
        return f'<span class="status-badge status-caution">▲ {raw.upper()} (WATCH)</span>'
    if any(k in low for k in ["error", "fail", "invalid", "high", "critical", "severe", "anomaly", "flagged", "investigate", "significant"]):
        return f'<span class="status-badge status-investigate">■ {raw.upper()} (INVESTIGATE)</span>'
    return f'<span class="status-badge status-neutral">◆ {raw.upper()}</span>'


# =====================================================================
# 5. SHARED UI & PLOTLY CHART HELPERS
# =====================================================================
def apply_helioiq_plotly_theme(fig: go.Figure, title: str, xaxis_title: str, yaxis_title: str) -> go.Figure:
    """Style Plotly charts strictly with the HelioIQ dark technical colour palette."""
    fig.update_layout(
        title=dict(text=title, font=dict(color=PALETTE["WHITE"], size=16)),
        paper_bgcolor=PALETTE["MIDNIGHT_NAVY"],
        plot_bgcolor=PALETTE["BLACK"],
        font=dict(color=PALETTE["SOFT_WHITE"], family="Inter, Segoe UI, sans-serif"),
        xaxis=dict(
            title=dict(text=xaxis_title, font=dict(color=PALETTE["MUTED_GREY"])),
            tickfont=dict(color=PALETTE["MUTED_GREY"]),
            gridcolor=PALETTE["STEEL_BLUE"],
            linecolor=PALETTE["STEEL_BLUE"],
            zerolinecolor=PALETTE["STEEL_BLUE"],
        ),
        yaxis=dict(
            title=dict(text=yaxis_title, font=dict(color=PALETTE["MUTED_GREY"])),
            tickfont=dict(color=PALETTE["MUTED_GREY"]),
            gridcolor=PALETTE["STEEL_BLUE"],
            linecolor=PALETTE["STEEL_BLUE"],
            zerolinecolor=PALETTE["STEEL_BLUE"],
        ),
        legend=dict(
            bgcolor="rgba(0, 9, 20, 0.85)",
            bordercolor=PALETTE["STEEL_BLUE"],
            borderwidth=1,
            font=dict(color=PALETTE["WHITE"]),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=PALETTE["MIDNIGHT_NAVY"],
            bordercolor=PALETTE["ELECTRIC_CYAN"],
            font=dict(color=PALETTE["WHITE"]),
        ),
        margin=dict(l=50, r=30, t=55, b=50),
    )
    return fig


def render_top_bar() -> None:
    """Render a consistent top bar across all pages showing tagline, API status, and active workspace."""
    ok, _, health = api_call("GET", "/health", timeout=5)
    if ok and isinstance(health, dict):
        st.session_state["health_data"] = health
        api_status = str(health.get("status", "unknown"))
        backend_info = health.get("backend", {})
        backend_avail = backend_info.get("available") if isinstance(backend_info, dict) else None
        if api_status.lower() == "ok" and backend_avail is not False:
            badge_html = '<span class="status-badge status-healthy">● API & BACKEND ONLINE</span>'
        else:
            badge_html = f'<span class="status-badge status-caution">▲ API {api_status.upper()} (BACKEND DEGRADED)</span>'
    else:
        st.session_state["health_data"] = None
        badge_html = '<span class="status-badge status-investigate">■ API OFFLINE</span>'

    ws_html = ""
    if st.session_state.get("active_workspace"):
        ver = st.session_state.get("active_model_version") or "latest"
        ws_html = (
            f'<span class="status-badge status-neutral">'
            f'WORKSPACE: {st.session_state["active_workspace"]} | VERSION: {ver}'
            f"</span>"
        )

    # Collapsed into a single line to guarantee Streamlit does not render a Markdown code block
    top_bar_html = (
        f'<div class="helio-topbar">'
        f'<div>'
        f'<span style="font-size:1.35rem; font-weight:800; color:{PALETTE["WHITE"]}; letter-spacing:0.04em;">HELIO<span style="color:{PALETTE["ELECTRIC_CYAN"]};">IQ</span></span>'
        f'<span class="helio-muted" style="margin-left:0.85rem; font-size:0.92rem;">Know what your system should do. Know when it doesn\'t.</span>'
        f'</div>'
        f'<div style="display:flex; gap:0.6rem; align-items:center; flex-wrap:wrap;">{ws_html}{badge_html}</div>'
        f'</div>'
    )
    
    st.markdown(top_bar_html, unsafe_allow_html=True)


def render_common_dataset_options(prefix: str) -> Tuple[str, Optional[float], Optional[str], Optional[str]]:
    """Shared optional dataset configuration controls supported by the API."""
    col1, col2 = st.columns(2)
    with col1:
        dataset_type = st.selectbox(
            "Dataset Profile (`dataset`)",
            options=["trieste_q2", "generic"],
            index=0,
            key=f"{prefix}_dataset",
            help="Use 'trieste_q2' (default) for the Trieste dataset or 'generic' for custom schemas.",
        )
    with col2:
        specify_utc = st.checkbox(
            "Specify Fixed UTC Offset (`utc_offset_hours`)",
            value=False,
            key=f"{prefix}_specify_utc",
            help="Required when computing solar-position features. Do not guess the offset.",
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

    with st.expander("Advanced Backend Configuration (`column_map` / `power_options` JSON)", expanded=False):
        st.caption("Optional JSON strings passed directly to the backend without frontend modification.")
        c_map = st.text_area(
            "Column Map JSON (`column_map`)",
            placeholder='{"timestamp": "DateTime", "irradiance": "POA"}',
            height=68,
            key=f"{prefix}_colmap",
        )
        p_opts = st.text_area(
            "Power Options JSON (`power_options`)",
            placeholder='{"dc_scaling": 1.0}',
            height=68,
            key=f"{prefix}_poweropts",
        )
    return dataset_type, utc_offset, c_map.strip() or None, p_opts.strip() or None


def build_multipart_file(uploaded_file: Any) -> Dict[str, Tuple[str, bytes, str]]:
    """Prepare the file tuple for `requests` multipart/form-data upload."""
    uploaded_file.seek(0)
    return {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}


def validate_json_string(raw_text: Optional[str], field_label: str) -> bool:
    if not raw_text:
        return True
    try:
        json.loads(raw_text)
        return True
    except ValueError as exc:
        st.error(f"Invalid JSON in `{field_label}`: {exc}")
        return False


def extract_rows_from_payload(payload: Dict[str, Any]) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Find the list of row records returned by the API without assuming a hard-coded key."""
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
    st.markdown("## 01 Home / Dashboard")
    st.markdown(
        f"""
        <div class="helio-card">
            <h3 style="margin-top:0;">Welcome to HelioIQ</h3>
            <p style="font-size:1.02rem; color:{PALETTE['SOFT_WHITE']}; margin-bottom:0.5rem;">
                HelioIQ estimates expected solar PV power under observed environmental conditions, compares expected power with observed or defensibly derived power, flags persistent deviations for investigation, and supports hypothetical what-if simulation.
            </p>
            <div class="helio-muted" style="font-size:0.88rem;">
                Connected API Base URL: <code>{API_BASE_URL}</code>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Live Health Check Section
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown("### Live API & Backend Connection (`GET /health`)")
    with col_h2:
        if st.button("Refresh Health Status", use_container_width=True):
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
        m3.metric("Backend Package Available", "Yes (Loaded)" if backend_avail else "No / Degraded")

        with st.expander("View Raw `/health` Response Payload", expanded=False):
            st.json(health_payload)
    else:
        render_api_error(status_code, health_payload, context="GET /health Check")

    st.markdown("---")

    # Quick Action Cards
    st.markdown("### Core Workflow Quick Actions")
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        st.markdown(
            """
            <div class="helio-card">
                <h4>1. Validate Dataset</h4>
                <p class="helio-muted">Upload a solar PV CSV file, verify schema compatibility, and inspect data quality reports.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Dataset Management →", key="qa_validate", use_container_width=True):
            navigate_to("02 Dataset Management")

    with qa2:
        st.markdown(
            """
            <div class="helio-card">
                <h4>2. Train Model</h4>
                <p class="helio-muted">Train Linear Regression and Random Forest models on held-out chronological windows.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Model Lab →", key="qa_train", use_container_width=True):
            navigate_to("03 Model Lab")

    with qa3:
        st.markdown(
            """
            <div class="helio-card">
                <h4>3. Analyse Performance</h4>
                <p class="helio-muted">Compare expected model power against observed or derived DC power over time.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Go to Performance Analysis →", key="qa_perf", use_container_width=True):
            navigate_to("04 Performance Analysis")

    # Shortcuts to Anomaly Analysis & What-if Simulator
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        if st.button("Shortcut: Anomaly Detection →", key="sc_anom", use_container_width=True):
            navigate_to("05 Anomaly Detection")
    with sc2:
        if st.button("Shortcut: What-if Simulator →", key="sc_sim", use_container_width=True):
            navigate_to("06 What-if Simulator")
    with sc3:
        if st.button("Shortcut: Models & Workspaces →", key="sc_ws", use_container_width=True):
            navigate_to("07 Models & Workspaces")

    st.markdown("---")

    # Current Workspace / Model & Latest Available Results (Only when returned by API)
    st.markdown("### Current Session Context & Latest API Results")
    col_ctx1, col_ctx2 = st.columns(2)

    with col_ctx1:
        if st.session_state.get("active_workspace"):
            st.markdown(
                f"""
                <div class="helio-card">
                    <h4>Active Workspace & Model</h4>
                    <p><strong>Workspace:</strong> <code>{st.session_state['active_workspace']}</code></p>
                    <p><strong>Latest Confirmed Version:</strong> <code>{st.session_state.get('active_model_version') or 'latest'}</code></p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="helio-card">
                    <h4>No Active Workspace / Model Yet</h4>
                    <p class="helio-muted">
                        No model has been trained or queried in this session yet. Train a new model in <strong>03 Model Lab</strong> or inspect an existing workspace in <strong>07 Models & Workspaces</strong>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_ctx2:
        if st.session_state.get("last_validation_result"):
            st.markdown(
                """
                <div class="helio-card">
                    <h4>Latest Dataset Validation Available</h4>
                    <p class="helio-muted">A dataset validation response was received from <code>POST /datasets/validate</code> during this session.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("Inspect Latest Validation Summary"):
                st.json(st.session_state["last_validation_result"])
        else:
            st.markdown(
                """
                <div class="helio-card">
                    <h4>No Dataset Validated Yet</h4>
                    <p class="helio-muted">
                        You have not uploaded and validated a CSV file yet. Note that the API processes uploads temporarily per request—start in <strong>02 Dataset Management</strong> to verify your file.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------
# PAGE 02: DATASET MANAGEMENT
# ---------------------------------------------------------------------
def page_dataset_management() -> None:
    st.markdown("## 02 Dataset Management")
    st.markdown(
        """
        <div class="helio-guardrail">
            <strong>Scientific & Workflow Note:</strong> CSV uploads use <code>multipart/form-data</code> and are processed temporarily per request. For the Trieste dataset (<code>trieste_q2</code>), the power target is <strong>derived DC power</strong>, not measured AC grid output.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Solar PV Dataset CSV (`file`)",
        type=["csv"],
        help="Supported format: Comma-separated values (.csv) compatible with `trieste_q2` or `generic` schemas.",
        key="validate_csv_uploader",
    )

    dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options("validate")

    # Non-mutating raw source preview
    if uploaded_file is not None:
        with st.expander("Raw CSV Source Preview (Unmodified Text View — First 10 Rows)", expanded=False):
            st.caption("Displayed strictly as raw strings (`dtype=str`) without type coercion, rounding, or mutation.")
            try:
                uploaded_file.seek(0)
                preview_df = pd.read_csv(uploaded_file, nrows=10, dtype=str, keep_default_na=False)
                st.dataframe(preview_df, use_container_width=True)
            except Exception as exc:
                st.warning(f"Could not render local text preview: {exc}")

    validate_clicked = st.button(
        "Validate Dataset (`POST /datasets/validate`)",
        disabled=(uploaded_file is None),
        use_container_width=True,
    )

    if validate_clicked and uploaded_file is not None:
        if not validate_json_string(col_map, "column_map") or not validate_json_string(power_opts, "power_options"):
            return

        form_data = {
            "dataset": dataset_type,
            "utc_offset_hours": utc_offset,
            "column_map": col_map,
            "power_options": power_opts,
        }
        with st.spinner("Validating dataset schema and quality via `POST /datasets/validate`..."):
            ok, status_code, payload = api_call(
                "POST",
                "/datasets/validate",
                data=form_data,
                files=build_multipart_file(uploaded_file),
            )

        if ok and isinstance(payload, dict):
            st.session_state["last_validation_result"] = payload
        else:
            render_api_error(status_code, payload, context="POST /datasets/validate")

    # Render returned validation results
    result = st.session_state.get("last_validation_result")
    if isinstance(result, dict):
        st.markdown("---")
        st.markdown("### Validation Output")

        is_valid = result.get("valid", result.get("is_valid", result.get("status") == "ok"))
        status_label = "VALID" if is_valid is True else ("INVALID" if is_valid is False else str(result.get("status", "COMPLETED")))
        st.markdown(
            f'<div style="margin-bottom:1rem;">Validation Status: {format_status_badge(status_label)}</div>',
            unsafe_allow_html=True,
        )

        # Top-level summary metrics when returned by API
        metric_candidates = [
            ("Row Count", result.get("row_count", result.get("n_rows", result.get("rows")))),
            ("Column Count", result.get("column_count", result.get("n_columns"))),
            ("Dataset Profile", result.get("dataset", result.get("dataset_type"))),
            ("Target Column", result.get("target_column", result.get("target"))),
        ]
        present_metrics = [(label, val) for label, val in metric_candidates if isinstance(val, (int, float, str))]
        if present_metrics:
            cols = st.columns(len(present_metrics))
            for idx, (label, val) in enumerate(present_metrics):
                cols[idx].metric(label, str(val))

        # Validation Errors & Warnings
        errors = result.get("errors", result.get("validation_errors", []))
        warnings = result.get("warnings", result.get("validation_warnings", []))

        if errors:
            st.markdown(
                f"""
                <div class="helio-card" style="border-left:4px solid {PALETTE['RED']};">
                    <h4>■ Validation Errors ({len(errors)})</h4>
                    <ul>{"".join(f"<li>{e}</li>" for e in (errors if isinstance(errors, list) else [errors]))}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if warnings:
            st.markdown(
                f"""
                <div class="helio-card" style="border-left:4px solid {PALETTE['AMBER']};">
                    <h4>▲ Validation Warnings ({len(warnings)})</h4>
                    <ul>{"".join(f"<li>{w}</li>" for w in (warnings if isinstance(warnings, list) else [warnings]))}</ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Schema / Columns & Data Quality Details
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            schema_info = result.get("schema", result.get("columns", result.get("column_details")))
            if schema_info is not None:
                st.markdown("#### Returned Schema / Columns")
                if isinstance(schema_info, list):
                    if len(schema_info) > 0 and isinstance(schema_info[0], dict):
                        st.dataframe(pd.DataFrame(schema_info), use_container_width=True)
                    else:
                        st.dataframe(pd.DataFrame({"Column": schema_info}), use_container_width=True)
                elif isinstance(schema_info, dict):
                    st.json(schema_info)

        with col_s2:
            quality_info = result.get("quality", result.get("data_quality", result.get("summary", result.get("cleaning_summary"))))
            if quality_info is not None:
                st.markdown("#### Data Quality Summary")
                if isinstance(quality_info, dict):
                    st.json(quality_info)
                elif isinstance(quality_info, list):
                    st.dataframe(pd.DataFrame(quality_info), use_container_width=True)

        with st.expander("Full API Response JSON (`/datasets/validate`)", expanded=False):
            st.json(result)

        # Clear guidance on what to do next
        st.markdown(
            f"""
            <div class="helio-card" style="border-left:4px solid {PALETTE['ELECTRIC_CYAN']};">
                <h4>What to Do Next</h4>
                <ol style="margin-bottom:0.5rem;">
                    <li>If validation errors were flagged above, fix the missing columns, timestamps, or configuration JSON and re-validate.</li>
                    <li>Once valid, proceed to <strong>03 Model Lab</strong> to train Linear Regression and Random Forest models on this dataset, or go to <strong>04 Performance Analysis</strong> if you already have a saved workspace model.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
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
    st.markdown("## 03 Model Lab")
    st.markdown(
        """
        <div class="helio-guardrail">
            <strong>Model Evaluation Guardrail:</strong> Each training request trains and evaluates models on a chronological hold-out split (latest observations held out for evaluation) and saves a new model version in the specified workspace.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Training CSV (`file`)",
        type=["csv"],
        key="train_csv_uploader",
        help="CSV file containing environmental features and target power observations.",
    )

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        default_ws = st.session_state.get("active_workspace") or "trieste_demo"
        workspace = st.text_input(
            "Workspace Name (`workspace` — required)",
            value=default_ws,
            max_chars=64,
            help="Letters, numbers, underscore (_), or hyphen (-); maximum 64 characters.",
        ).strip()
    with col_w2:
        test_fraction = st.number_input(
            "Chronological Hold-out Test Fraction (`test_fraction`)",
            min_value=0.05,
            max_value=0.50,
            value=0.20,
            step=0.05,
            help="Default 0.2. The latest chronological portion of the dataset is held out for evaluation.",
        )

    dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options("train")

    with st.expander("Optional Target & Feature Overrides (`target` / `features`)", expanded=False):
        st.caption("Only populate these fields if you know the backend's exact expected column names.")
        target_col = st.text_input("Target Column Override (`target`)", value="").strip()
        features_raw = st.text_input(
            "Features Override (`features` — comma-separated or JSON list)",
            value="",
        ).strip()

    train_clicked = st.button(
        "Train Models (`POST /models/train`)",
        disabled=(uploaded_file is None or not workspace),
        use_container_width=True,
    )

    if train_clicked and uploaded_file is not None:
        if not WORKSPACE_REGEX.match(workspace):
            st.error("Workspace must contain only letters, numbers, underscores, or hyphens (1–64 characters).")
            return
        if not validate_json_string(col_map, "column_map") or not validate_json_string(power_opts, "power_options"):
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
        with st.spinner("Training Linear Regression and Random Forest models via `POST /models/train`..."):
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

    # Render Training Output
    train_res = st.session_state.get("last_training_result")
    if isinstance(train_res, dict):
        st.markdown("---")
        st.markdown("### Training & Evaluation Results")
        st.markdown(
            f'<div style="margin-bottom:1rem;">Training Status: {format_status_badge("SUCCESS")}</div>',
            unsafe_allow_html=True,
        )

        # Summary header metrics
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

        # Clearly identify held-out evaluation observations if exposed by the API
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
            st.markdown(
                """
                <div class="helio-muted" style="margin-bottom:0.5rem;">
                    Observations held out chronologically for model evaluation (as reported by the API):
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.dataframe(pd.DataFrame([holdout_fields]), use_container_width=True)

        # Extract Model Comparison Metrics (Linear Regression vs Random Forest)
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

            # Filter out R2 if it is null or non-meaningful (e.g. NaN)
            for col in list(comp_df.columns):
                if col.lower() in ("r2", "r_squared", "r2_score"):
                    if comp_df[col].isna().all():
                        comp_df.drop(columns=[col], inplace=True)

            st.dataframe(comp_df, use_container_width=True)

            # Plot MAE and RMSE side-by-side in a chart
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
                st.plotly_chart(fig, use_container_width=True)

        with st.expander("Full API Response JSON (`/models/train`)", expanded=False):
            st.json(train_res)


# ---------------------------------------------------------------------
# PAGE 04: PERFORMANCE ANALYSIS
# ---------------------------------------------------------------------
def page_performance_analysis() -> None:
    st.markdown("## 04 Performance Analysis")
    st.markdown(
        """
        <div class="helio-guardrail">
            <strong>Scientific Guardrails:</strong>
            <ul style="margin-bottom:0;">
                <li><strong>Derived DC Power ≠ Measured AC Power:</strong> For the Trieste dataset, calculated DC targets represent derived DC power, not verified grid-delivered AC production.</li>
                <li><strong>Predictions are Estimates:</strong> Expected power is model output under observed environmental conditions, not ground truth.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload Analysis CSV (`file` — required per request)",
        type=["csv"],
        key="perf_csv_uploader",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        workspace = st.text_input(
            "Workspace (`workspace`)",
            value=st.session_state.get("active_workspace") or "trieste_demo",
            key="perf_ws",
        ).strip()
    with c2:
        version = st.text_input(
            "Model Version (`version`)",
            value=st.session_state.get("active_model_version") or "latest",
            key="perf_ver",
        ).strip()
    with c3:
        group_by = st.selectbox(
            "Summary Aggregation (`group_by`)",
            options=["", "day", "month"],
            format_func=lambda x: "None (Overall only)" if x == "" else f"Group by {x.capitalize()}",
            key="perf_groupby",
        )

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        start_window = st.text_input("Start Date/Time (`start` optional)", placeholder="YYYY-MM-DD", key="perf_start").strip()
    with d2:
        end_window = st.text_input("End Date/Time (`end` optional)", placeholder="YYYY-MM-DD", key="perf_end").strip()
    with d3:
        include_rows = st.checkbox("Include Per-Row Predictions (`include_rows`)", value=True, key="perf_inc_rows")
    with d4:
        max_rows = st.number_input("Max Returned Rows (`max_rows`)", min_value=10, max_value=50000, value=2000, step=100, key="perf_max_rows")

    dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options("perf")

    run_perf = st.button(
        "Run Historical Predictions & Performance Summary (`POST /predictions/historical` + `POST /performance/summary`)",
        disabled=(uploaded_file is None or not workspace),
        use_container_width=True,
    )

    if run_perf and uploaded_file is not None:
        if not validate_json_string(col_map, "column_map") or not validate_json_string(power_opts, "power_options"):
            return

        common_form = {
            "workspace": workspace,
            "version": version or "latest",
            "dataset": dataset_type,
            "utc_offset_hours": utc_offset,
            "start": start_window or None,
            "end": end_window or None,
            "include_rows": str(include_rows).lower(),
            "max_rows": int(max_rows),
            "column_map": col_map,
            "power_options": power_opts,
        }

        with st.spinner("Generating historical predictions (`/predictions/historical`) and summary (`/performance/summary`)..."):
            ok_hist, code_hist, payload_hist = api_call(
                "POST",
                "/predictions/historical",
                data=common_form,
                files=build_multipart_file(uploaded_file),
                timeout=180,
            )
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

    # 1. Render Performance Summary Metrics (`POST /performance/summary`)
    if isinstance(sum_res, dict):
        st.markdown("---")
        st.markdown("### Aggregate Performance Summary (`POST /performance/summary`)")
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
            st.markdown(f"#### Grouped Performance Breakdown (`{grp_key}`)")
            st.dataframe(pd.DataFrame(grouped_rows), use_container_width=True)

        with st.expander("Full `/performance/summary` JSON Response", expanded=False):
            st.json(sum_res)

    # 2. Render Historical Time-Series Chart & Residuals (`POST /predictions/historical`)
    if isinstance(hist_res, dict):
        st.markdown("---")
        st.markdown("### Expected vs. Observed / Derived Target Power (`POST /predictions/historical`)")

        # Determine units and target definition from API response
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
            st.markdown(
                f"""
                <div class="helio-muted" style="margin-bottom:0.6rem;">
                    <strong>Target Definition:</strong> {target_def} &nbsp;|&nbsp;
                    <strong>Units:</strong> {unit_label} &nbsp;|&nbsp;
                    <strong>Displayed Time Range:</strong> {time_range_str} ({len(df)} observations)
                </div>
                """,
                unsafe_allow_html=True,
            )

            if exp_col or obs_col:
                fig_ts = go.Figure()
                if obs_col:
                    fig_ts.add_trace(
                        go.Scatter(
                            x=df[time_col],
                            y=pd.to_numeric(df[obs_col], errors="coerce"),
                            mode="lines",
                            name=f"Observed / Derived Target ({obs_col})",
                            line=dict(color=PALETTE["WHITE"], width=1.8),
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
                st.plotly_chart(fig_ts, use_container_width=True)

            # Residual / Error visualisation ONLY where supported by returned data
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
                        fillcolor="rgba(22, 50, 79, 0.45)",
                    )
                )
                apply_helioiq_plotly_theme(
                    fig_res,
                    title=f"Returned Residual / Error Series ({res_col})",
                    xaxis_title=f"Timestamp ({time_col})",
                    yaxis_title=f"Residual ({unit_label})",
                )
                st.plotly_chart(fig_res, use_container_width=True)

            with st.expander("Inspect Returned Historical Prediction Rows", expanded=False):
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No per-row series returned in this response. Ensure `include_rows` is enabled to plot time-series points.")

        with st.expander("Full `/predictions/historical` JSON Response", expanded=False):
            st.json(hist_res)


# ---------------------------------------------------------------------
# PAGE 05: ANOMALY DETECTION
# ---------------------------------------------------------------------
def page_anomaly_detection() -> None:
    st.markdown("## 05 Anomaly Detection")
    st.markdown(
        f"""
        <div class="helio-guardrail" style="border-left-color:{PALETTE['AMBER']};">
            <strong>Investigation Guardrail:</strong> Flagged periods indicate <strong>potential underperformance requiring investigation</strong>, not confirmed inverter, panel, or equipment faults. Thresholds are prototype defaults and have not been calibrated against labelled real faults.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload CSV for Anomaly Analysis (`file`)",
        type=["csv"],
        key="anom_csv_uploader",
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        workspace = st.text_input(
            "Workspace (`workspace`)",
            value=st.session_state.get("active_workspace") or "trieste_demo",
            key="anom_ws",
        ).strip()
    with c2:
        version = st.text_input(
            "Model Version (`version`)",
            value=st.session_state.get("active_model_version") or "latest",
            key="anom_ver",
        ).strip()
    with c3:
        start_win = st.text_input("Start Window (`start` optional)", placeholder="YYYY-MM-DD", key="anom_start").strip()
    with c4:
        end_win = st.text_input("End Window (`end` optional)", placeholder="YYYY-MM-DD", key="anom_end").strip()

    include_rows = st.checkbox("Include Row-Level Anomaly Details (`include_rows`)", value=True, key="anom_inc_rows")
    dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options("anom")

    run_anom = st.button(
        "Analyse Potential Anomalies (`POST /anomalies/analyze`)",
        disabled=(uploaded_file is None or not workspace),
        use_container_width=True,
    )

    if run_anom and uploaded_file is not None:
        if not validate_json_string(col_map, "column_map") or not validate_json_string(power_opts, "power_options"):
            return

        form_data = {
            "workspace": workspace,
            "version": version or "latest",
            "dataset": dataset_type,
            "utc_offset_hours": utc_offset,
            "start": start_win or None,
            "end": end_win or None,
            "include_rows": str(include_rows).lower(),
            "column_map": col_map,
            "power_options": power_opts,
        }
        with st.spinner("Analysing persistent deviations via `POST /anomalies/analyze`..."):
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

        # Status badge using Green / Amber / Red with explicit icon + text label
        if overall_status is not None:
            st.markdown(
                f'<div style="margin-bottom:1rem;">API Reported Status: {format_status_badge(overall_status)}</div>',
                unsafe_allow_html=True,
            )
        elif isinstance(anom_count, int):
            inferred_badge = (
                '<span class="status-badge status-healthy">● 0 FLAGGED PERIODS (NORMAL)</span>'
                if anom_count == 0
                else f'<span class="status-badge status-investigate">■ {anom_count} FLAGGED FOR INVESTIGATION</span>'
            )
            st.markdown(f'<div style="margin-bottom:1rem;">Status: {inferred_badge}</div>', unsafe_allow_html=True)

        # Render all scalar summary metrics returned by the API
        if isinstance(summary_obj, dict):
            scalars = [(k, v) for k, v in summary_obj.items() if isinstance(v, (int, float, str)) and not isinstance(v, bool)]
            if scalars:
                cols = st.columns(min(4, len(scalars)))
                for idx, (k, v) in enumerate(scalars[:8]):
                    val_str = f"{v:,.3f}" if isinstance(v, float) else str(v)
                    cols[idx % len(cols)].metric(k.replace("_", " ").title(), val_str)

        # Flagged periods / events / rows tables
        for key_candidate, title_label in [
            ("flagged_periods", "Flagged Time Periods for Investigation"),
            ("periods", "Flagged Time Periods for Investigation"),
            ("events", "Flagged Deviation Events"),
            ("anomalies", "Flagged Observations / Anomalies"),
            ("rows", "Analysed Observations"),
        ]:
            records = anom_res.get(key_candidate)
            if isinstance(records, list) and len(records) > 0 and isinstance(records[0], dict):
                st.markdown(f"#### {title_label} (`{key_candidate}` — {len(records)} records)")
                df_records = pd.DataFrame(records)
                st.dataframe(df_records, use_container_width=True)

                # If time and deviation/power columns exist, visualise flagged points
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
                    st.plotly_chart(fig_anom, use_container_width=True)
                break

        st.markdown(
            f"""
            <div class="helio-card" style="border-left:4px solid {PALETTE['AMBER']};">
                <h4>Investigation Prompt</h4>
                <p style="margin-bottom:0;">
                    Review flagged timestamps against local irradiance sensor cleaning logs, shading conditions, curtailment schedules, or data logger dropouts before scheduling field maintenance. Do not treat statistical deviation flags alone as confirmed hardware failure.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Full `/anomalies/analyze` JSON Response", expanded=False):
            st.json(anom_res)


# ---------------------------------------------------------------------
# PAGE 06: WHAT-IF SIMULATOR
# ---------------------------------------------------------------------
def page_whatif_simulator() -> None:
    st.markdown("## 06 What-if Simulator")
    st.markdown(
        f"""
        <div class="helio-guardrail" style="border-left-color:{PALETTE['ELECTRIC_CYAN']};">
            <strong>Simulation Guardrail:</strong> What-if outputs are <strong>hypothetical statistical model re-predictions</strong> under adjusted scenario inputs. They are not physical PV simulations or a guarantee of real-world energy production.
        </div>
        """,
        unsafe_allow_html=True,
    )

    reset_key = st.session_state["whatif_reset_counter"]

    uploaded_file = st.file_uploader(
        "Upload Baseline CSV for Simulation (`file`)",
        type=["csv"],
        key=f"whatif_csv_{reset_key}",
    )

    c1, c2 = st.columns(2)
    with c1:
        workspace = st.text_input(
            "Workspace (`workspace`)",
            value=st.session_state.get("active_workspace") or "trieste_demo",
            key=f"whatif_ws_{reset_key}",
        ).strip()
    with c2:
        version = st.text_input(
            "Model Version (`version`)",
            value=st.session_state.get("active_model_version") or "latest",
            key=f"whatif_ver_{reset_key}",
        ).strip()

    st.markdown("#### Scenario Input Controls (`POST /simulations/what-if`)")
    st.caption("Adjust environmental scenario parameters with explicit units and validated ranges.")

    s1, s2, s3 = st.columns(3)
    with s1:
        irradiance_factor = st.number_input(
            "Irradiance Multiplier (`irradiance_factor` / `scale`, ratio [×])",
            min_value=0.0,
            max_value=2.0,
            value=1.10,
            step=0.05,
            key=f"whatif_irr_factor_{reset_key}",
            help="E.g. 1.10 = +10% solar irradiance (W/m²). Validated range: 0.0× to 2.0×.",
        )
    with s2:
        irradiance_delta = st.number_input(
            "Irradiance Offset (`irradiance_delta`, W/m²)",
            min_value=-1000.0,
            max_value=1000.0,
            value=0.0,
            step=25.0,
            key=f"whatif_irr_delta_{reset_key}",
            help="Additive change to irradiance in W/m².",
        )
    with s3:
        temp_delta = st.number_input(
            "Temperature Offset (`temperature_delta`, °C)",
            min_value=-30.0,
            max_value=30.0,
            value=0.0,
            step=1.0,
            key=f"whatif_temp_delta_{reset_key}",
            help="Additive shift to ambient/module temperature in °C.",
        )

    with st.expander("Custom / Exact Scenario JSON or Form Fields Override", expanded=False):
        st.caption(
            "If your specific model features use custom scenario JSON (`scenario` / `adjustments`), enter it below to pass directly to `POST /simulations/what-if`."
        )
        custom_scenario_json = st.text_area(
            "Scenario JSON (`scenario`)",
            value="",
            placeholder='{"irradiance_scale": 1.1, "temperature_delta_c": 2.0}',
            key=f"whatif_custom_json_{reset_key}",
        ).strip()

    dataset_type, utc_offset, col_map, power_opts = render_common_dataset_options(f"whatif_{reset_key}")

    btn_col1, btn_col2 = st.columns([3, 1])
    with btn_col1:
        run_sim = st.button(
            "Run Simulation (`POST /simulations/what-if`)",
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
            not validate_json_string(custom_scenario_json, "scenario")
            or not validate_json_string(col_map, "column_map")
            or not validate_json_string(power_opts, "power_options")
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

        with st.spinner("Running hypothetical what-if simulation via `POST /simulations/what-if`..."):
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
        st.markdown(
            '<div style="margin-bottom:1rem;"><span class="status-badge status-neutral">◆ HYPOTHETICAL SIMULATION RESULT</span></div>',
            unsafe_allow_html=True,
        )

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
                st.plotly_chart(fig_sim, use_container_width=True)

            with st.expander("Inspect Returned Simulation Rows", expanded=False):
                st.dataframe(df_sim, use_container_width=True)

        with st.expander("Full `/simulations/what-if` JSON Response", expanded=False):
            st.json(sim_res)


# ---------------------------------------------------------------------
# PAGE 07: MODELS & WORKSPACES
# ---------------------------------------------------------------------
def page_models_workspaces() -> None:
    st.markdown("## 07 Models & Workspaces")
    st.markdown(
        """
        <div class="helio-guardrail">
            <strong>API Architecture Note:</strong> The HelioIQ API does not expose a global workspace-discovery endpoint. Enter a known workspace name below (or select one used earlier in this session) to query <code>GET /models/{workspace}</code> and <code>GET /models/{workspace}/{version}</code>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    known_ws = st.session_state.get("known_workspaces", [])
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        default_ws = st.session_state.get("active_workspace") or (known_ws[0] if known_ws else "trieste_demo")
        workspace_input = st.text_input(
            "Enter Known Workspace Name (`workspace`)",
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
        f"List Versions in Workspace (`GET /models/{workspace_input or '{workspace}'}`)",
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

        with st.expander("Raw `GET /models/{workspace}` Response", expanded=False):
            st.json(ws_payload)

    st.markdown("---")
    st.markdown("### Inspect Specific Model Version (`GET /models/{workspace}/{version}`)")
    v_col1, v_col2 = st.columns([2, 1])
    with v_col1:
        version_to_query = st.text_input(
            "Version Identifier (`version` — use `latest` for newest)",
            value=version_options[-1] if len(version_options) > 1 else "latest",
        ).strip()
    with v_col2:
        st.write("")
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

        # Direct navigation to Performance Analysis and What-if Simulator for this model
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
# 7. APPLICATION SHELL & SIDEBAR NAVIGATION
# =====================================================================
def main() -> None:
    inject_helioiq_css()
    init_session_state()

    with st.sidebar:
        st.markdown(
            f"""
            <div style="padding:0.4rem 0 1rem 0; border-bottom:1px solid {PALETTE['STEEL_BLUE']}; margin-bottom:1rem;">
                <div style="font-size:1.5rem; font-weight:800; color:{PALETTE['WHITE']};">
                    HELIO<span style="color:{PALETTE['ELECTRIC_CYAN']};">IQ</span>
                </div>
                <div class="helio-muted" style="font-size:0.8rem; margin-top:0.2rem;">
                    Solar PV Performance Intelligence
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        selected_page = st.radio(
            "APPLICATION NAVIGATION",
            options=PAGES,
            index=PAGES.index(st.session_state["current_page"]),
        )
        if selected_page != st.session_state["current_page"]:
            st.session_state["current_page"] = selected_page
            st.rerun()

        st.markdown("---")
        st.markdown(
            f"""
            <div class="helio-muted" style="font-size:0.78rem; line-height:1.45;">
                <strong>API Endpoint:</strong><br/>
                <code>{API_BASE_URL}</code><br/><br/>
                <strong>Colour Legend:</strong><br/>
                <span style="color:{PALETTE['GREEN']};">● Healthy / Normal</span><br/>
                <span style="color:{PALETTE['AMBER']};">▲ Watch / Caution</span><br/>
                <span style="color:{PALETTE['RED']};">■ Investigate Deviation</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
