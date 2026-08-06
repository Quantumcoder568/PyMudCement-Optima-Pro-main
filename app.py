import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from database import init_db, AsyncSessionLocal, UserModel
from auth import get_password_hash, verify_password
from physics import DrillingHydraulicsEngine, WellSegment, NozzleInput, RheologyModel
from cementing_engine import PrimaryCementingInput, CementingEngine
from pdf_generator import generate_pdf_payload
from mud_parser import parse_mud_report
from gradients import PressureGradientProfile
from benchmarks import compare_cementing_results
import base64
from pathlib import Path


def get_base64_image(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


logo_base64 = get_base64_image("logo.png")
asyncio.run(init_db())

# ============================
# PAGE CONFIG
# ============================
st.set_page_config(
    page_title="PyMudCement Optima Pro v5.0",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================
# SESSION STATE INIT
# ============================
defaults = {
    "authenticated": False,
    "user_info": None,
    "auto_pv": None,
    "auto_yp": None,
    "auto_mw": None,
    "parsed": False,
    "cementing_results": None,
    "cementing_params": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================
# MASTER CSS — COCKPIT DARK THEME
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Reset & Base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], .stApp {
    background: #080D1A !important;
    color: #D0DCF0 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0D1525; }
::-webkit-scrollbar-thumb { background: #1E3A6E; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #2E6FD9; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }
.block-container {
    padding: 1.5rem 2rem !important;
    max-width: 100% !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #060C18 !important;
    border-right: 1px solid #0F2044 !important;
    padding-top: 0 !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stNumberInput label {
    color: #7A92B4 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] .stSelectbox select,
[data-testid="stSidebar"] [data-baseweb="select"] {
    background: #0D1525 !important;
    border: 1px solid #1A3A6E !important;
    color: #D0DCF0 !important;
    border-radius: 6px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] {
    background: #0D1525 !important;
}

/* ── Sidebar Logo Band ── */
.sidebar-logo-band {
    background: linear-gradient(135deg, #0A1F40 0%, #061028 100%);
    border-bottom: 1px solid #0F2044;
    padding: 1.1rem 1.2rem 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
}
.sidebar-logo-band .app-name {
    font-size: 0.85rem;
    font-weight: 700;
    color: #E2EAF8;
    line-height: 1.2;
}
.sidebar-logo-band .app-ver {
    font-size: 0.65rem;
    color: #2E6FD9;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.06em;
}

/* ── Sidebar Section Headers ── */
.sidebar-section {
    padding: 0.55rem 1.2rem 0.25rem;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #2E6FD9;
    border-left: 2px solid #2E6FD9;
    margin: 1rem 0.8rem 0.4rem;
    background: rgba(46, 111, 217, 0.05);
    border-radius: 0 4px 4px 0;
}

/* ── Sidebar Divider ── */
[data-testid="stSidebar"] hr {
    border-color: #0F2044 !important;
    margin: 0.8rem 0 !important;
}

/* ── Expanders in Sidebar ── */
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background: transparent !important;
    border: none !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    color: #7A92B4 !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── Top Bar ── */
.topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.8rem 0 1.2rem;
    border-bottom: 1px solid #0F2044;
    margin-bottom: 1.5rem;
}
.topbar-left {
    display: flex;
    align-items: center;
    gap: 1rem;
}
.topbar-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: #E2EAF8;
    letter-spacing: -0.02em;
}
.topbar-title span {
    color: #2E6FD9;
}
.topbar-badge {
    font-size: 0.62rem;
    font-family: 'JetBrains Mono', monospace;
    background: rgba(46, 111, 217, 0.15);
    color: #2E6FD9;
    border: 1px solid rgba(46, 111, 217, 0.3);
    padding: 0.15rem 0.5rem;
    border-radius: 3px;
    letter-spacing: 0.08em;
    font-weight: 600;
}
.topbar-user {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    background: #0D1525;
    border: 1px solid #1A3A6E;
    padding: 0.4rem 0.9rem;
    border-radius: 6px;
}
.topbar-user .user-name {
    font-size: 0.8rem;
    font-weight: 600;
    color: #D0DCF0;
}
.topbar-user .user-company {
    font-size: 0.68rem;
    color: #4A6A9A;
}
.topbar-dot {
    width: 8px; height: 8px;
    background: #22C55E;
    border-radius: 50%;
    box-shadow: 0 0 6px #22C55E;
    flex-shrink: 0;
}

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background: #0D1525 !important;
    border: 1px solid #0F2044 !important;
    border-radius: 8px !important;
    padding: 0.3rem !important;
    gap: 0.2rem !important;
}
[data-baseweb="tab"] {
    background: transparent !important;
    color: #4A6A9A !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
    letter-spacing: 0.03em !important;
    border-radius: 5px !important;
    border: none !important;
    padding: 0.5rem 1.1rem !important;
    transition: all 0.18s ease !important;
}
[data-baseweb="tab"]:hover {
    background: rgba(46, 111, 217, 0.08) !important;
    color: #8AAEDE !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: #1A3A6E !important;
    color: #E2EAF8 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.4) !important;
}
[data-baseweb="tab-highlight"] { display: none !important; }
[data-baseweb="tab-border"] { display: none !important; }

/* ── Metric Cards ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1.2rem 0;
}
.kpi-card {
    background: #0D1525;
    border: 1px solid #0F2044;
    border-left: 3px solid #2E6FD9;
    border-radius: 8px;
    padding: 1rem 1.1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.kpi-card:hover {
    border-left-color: #5A9AF5;
    box-shadow: 0 0 20px rgba(46, 111, 217, 0.12);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 80px; height: 80px;
    background: radial-gradient(circle at 100% 0%, rgba(46,111,217,0.06) 0%, transparent 65%);
}
.kpi-card .kpi-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #4A6A9A;
    margin-bottom: 0.5rem;
}
.kpi-card .kpi-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.65rem;
    font-weight: 600;
    color: #A8C4F0;
    line-height: 1;
}
.kpi-card .kpi-unit {
    font-size: 0.7rem;
    color: #4A6A9A;
    margin-top: 0.2rem;
}
.kpi-card.amber { border-left-color: #F5C842; }
.kpi-card.amber .kpi-value { color: #F5C842; }
.kpi-card.green { border-left-color: #22C55E; }
.kpi-card.green .kpi-value { color: #22C55E; }

/* ── Section Headers ── */
.section-head {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 1.5rem 0 0.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #0F2044;
}
.section-head .dot {
    width: 3px; height: 1.1rem;
    background: #2E6FD9;
    border-radius: 2px;
    flex-shrink: 0;
}
.section-head h3 {
    font-size: 0.85rem;
    font-weight: 700;
    color: #A8C4F0;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── Data Tables ── */
[data-testid="stDataFrame"] {
    border: 1px solid #0F2044 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] table {
    background: #0D1525 !important;
}
[data-testid="stDataFrame"] th {
    background: #060C18 !important;
    color: #4A6A9A !important;
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid #0F2044 !important;
    padding: 0.6rem 0.8rem !important;
}
[data-testid="stDataFrame"] td {
    background: #0D1525 !important;
    color: #D0DCF0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
    border-bottom: 1px solid #090F1E !important;
    padding: 0.5rem 0.8rem !important;
}
[data-testid="stDataFrame"] tr:hover td {
    background: #111D35 !important;
}

/* ── Data Editor ── */
[data-testid="stDataEditor"] {
    border: 1px solid #0F2044 !important;
    border-radius: 8px !important;
}

/* ── Buttons ── */
.stButton > button {
    background: #1A3A6E !important;
    color: #A8C4F0 !important;
    border: 1px solid #2E6FD9 !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.04em !important;
    padding: 0.55rem 1.4rem !important;
    transition: all 0.18s ease !important;
    font-family: 'Inter', sans-serif !important;
}
.stButton > button:hover {
    background: #2E6FD9 !important;
    color: #E2EAF8 !important;
    box-shadow: 0 0 16px rgba(46, 111, 217, 0.35) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }
[data-testid="baseButton-primary"] {
    background: linear-gradient(135deg, #1A3A6E 0%, #2E6FD9 100%) !important;
    color: #E2EAF8 !important;
    border: none !important;
    box-shadow: 0 2px 12px rgba(46, 111, 217, 0.3) !important;
}
[data-testid="baseButton-primary"]:hover {
    box-shadow: 0 4px 20px rgba(46, 111, 217, 0.5) !important;
    transform: translateY(-2px) !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    border: 1px solid !important;
    font-size: 0.82rem !important;
}
.stSuccess { background: rgba(34, 197, 94, 0.07) !important; border-color: rgba(34,197,94,0.3) !important; color: #86EFAC !important; }
.stWarning { background: rgba(245, 200, 66, 0.07) !important; border-color: rgba(245,200,66,0.3) !important; color: #FDE68A !important; }
.stError   { background: rgba(239, 68, 68, 0.07) !important; border-color: rgba(239,68,68,0.3) !important; color: #FCA5A5 !important; }
.stInfo    { background: rgba(46, 111, 217, 0.07) !important; border-color: rgba(46,111,217,0.3) !important; color: #93C5FD !important; }

/* ── Inputs ── */
.stTextInput input, .stNumberInput input, .stSelectbox select,
[data-baseweb="select"] > div {
    background: #0D1525 !important;
    border: 1px solid #1A3A6E !important;
    color: #D0DCF0 !important;
    border-radius: 6px !important;
    font-size: 0.85rem !important;
}
.stTextInput input:focus, .stNumberInput input:focus {
    border-color: #2E6FD9 !important;
    box-shadow: 0 0 0 2px rgba(46,111,217,0.2) !important;
    outline: none !important;
}
.stTextInput label, .stNumberInput label, .stSelectbox label {
    color: #4A6A9A !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

/* ── st.metric override ── */
[data-testid="metric-container"] {
    background: #0D1525 !important;
    border: 1px solid #0F2044 !important;
    border-left: 3px solid #2E6FD9 !important;
    border-radius: 8px !important;
    padding: 0.8rem 1rem !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #4A6A9A !important;
    font-size: 0.68rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #A8C4F0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.4rem !important;
    font-weight: 600 !important;
}
[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.72rem !important;
}

/* ── Auth Page ── */
.auth-wrap {
    max-width: 420px;
    margin: 5vh auto 0;
    padding: 2.5rem;
    background: #0D1525;
    border: 1px solid #1A3A6E;
    border-radius: 12px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.5);
}
.auth-logo-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 1.5rem;
}
.auth-app-name {
    font-size: 1.15rem;
    font-weight: 800;
    color: #E2EAF8;
}
.auth-app-sub {
    font-size: 0.7rem;
    color: #4A6A9A;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.05em;
}
.auth-divider {
    height: 1px;
    background: #0F2044;
    margin: 1.2rem 0;
}

/* ── Radio Buttons ── */
[data-testid="stRadio"] label {
    color: #7A92B4 !important;
    font-size: 0.82rem !important;
}
[data-testid="stRadio"] [data-testid="radio-button"] {
    accent-color: #2E6FD9 !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] { color: #2E6FD9 !important; }

/* ── Upload ── */
[data-testid="stFileUploader"] {
    background: #0D1525 !important;
    border: 1px dashed #1A3A6E !important;
    border-radius: 8px !important;
    padding: 0.8rem !important;
}
[data-testid="stFileUploader"] label {
    color: #4A6A9A !important;
    font-size: 0.72rem !important;
}

/* ── Footer ── */
.app-footer {
    text-align: center;
    font-size: 0.68rem;
    color: #1E3A6E;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.06em;
    padding: 2rem 0 1rem;
    border-top: 1px solid #0B1425;
    margin-top: 2rem;
}

/* ── Tag Pills ── */
.tag-pill {
    display: inline-block;
    font-size: 0.65rem;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    letter-spacing: 0.06em;
    padding: 0.12rem 0.5rem;
    border-radius: 3px;
    margin-right: 0.3rem;
}
.tag-blue { background: rgba(46,111,217,0.15); color: #5A9AF5; border: 1px solid rgba(46,111,217,0.25); }
.tag-amber { background: rgba(245,200,66,0.12); color: #F5C842; border: 1px solid rgba(245,200,66,0.25); }
.tag-green { background: rgba(34,197,94,0.1); color: #4ADE80; border: 1px solid rgba(34,197,94,0.2); }
.tag-red { background: rgba(239,68,68,0.1); color: #F87171; border: 1px solid rgba(239,68,68,0.2); }

/* ── Additive Cards ── */
.additive-card {
    background: #0D1525;
    border: 1px solid #0F2044;
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
}
.additive-card .add-name {
    font-weight: 700;
    font-size: 0.82rem;
    color: #D0DCF0;
    margin-bottom: 0.2rem;
}
.additive-card .add-desc {
    font-size: 0.74rem;
    color: #4A6A9A;
    line-height: 1.4;
}
</style>
""", unsafe_allow_html=True)


# ============================
# AUTHENTICATION
# ============================
async def process_authentication(mode, email_val, password_val, company_val=None):
    async with AsyncSessionLocal() as session:
        if mode == "Register":
            try:
                existing = await session.execute(
                    select(UserModel).where(or_(
                        UserModel.email == email_val,
                        UserModel.username == email_val
                    ))
                )
                if existing.scalar_one_or_none():
                    return False, "Email already registered."
                hashed_pw = get_password_hash(password_val)
                new_user = UserModel(
                    username=email_val,
                    email=email_val,
                    hashed_password=hashed_pw,
                    company_name=company_val or "Enterprise Hydrocarbons Corp"
                )
                session.add(new_user)
                await session.commit()
                return True, "Account created. Switch to Login."
            except IntegrityError:
                await session.rollback()
                return False, "Registration failed — duplicate entry."
            except Exception as e:
                await session.rollback()
                return False, f"Error: {str(e)}"
        else:
            try:
                result = await session.execute(
                    select(UserModel).where(UserModel.email == email_val)
                )
                user = result.scalar_one_or_none()
                if user and verify_password(password_val, user.hashed_password):
                    return True, {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "company": user.company_name
                    }
                return False, "Invalid email or password."
            except Exception as e:
                return False, f"Login error: {str(e)}"


# ---- Login screen ----
if not st.session_state.authenticated:
    st.markdown(f"""
    <div class="auth-wrap">
        <div class="auth-logo-row">
            <img src="data:image/png;base64,{logo_base64}" style="height:44px;">
            <div>
                <div class="auth-app-name">PyMudCement Optima Pro</div>
                <div class="auth-app-sub">v5.0 · Enterprise Hydraulic Platform</div>
            </div>
        </div>
        <div class="auth-divider"></div>
    </div>
    """, unsafe_allow_html=True)

    # Center column trick
    _, center, _ = st.columns([1, 2, 1])
    with center:
        auth_mode = st.radio("", ["Login", "Register"], horizontal=True, label_visibility="collapsed")
        with st.form("auth_form", border=False):
            st.text_input("Email address", key="auth_email", placeholder="engineer@company.com")
            st.text_input("Password", type="password", key="auth_password", placeholder="••••••••")
            if auth_mode == "Register":
                st.text_input("Company name", key="auth_company", value="Enterprise Hydrocarbons Corp")
            submitted = st.form_submit_button(
                "Sign in" if auth_mode == "Login" else "Create account",
                use_container_width=True,
                type="primary"
            )
            if submitted:
                email = st.session_state.auth_email
                pwd = st.session_state.auth_password
                company = st.session_state.get("auth_company", None)
                if not email or not pwd:
                    st.error("Email and password are required.")
                else:
                    ok, resp = asyncio.run(process_authentication(auth_mode, email, pwd, company))
                    if auth_mode == "Register":
                        st.success(resp) if ok else st.error(resp)
                    else:
                        if ok:
                            st.session_state.authenticated = True
                            st.session_state.user_info = resp
                            st.rerun()
                        else:
                            st.error(resp)
    st.stop()


# ============================
# SIDEBAR
# ============================
with st.sidebar:
    st.markdown(f"""
    <div class="sidebar-logo-band">
        <img src="data:image/png;base64,{logo_base64}" style="height:32px;flex-shrink:0;">
        <div>
            <div class="app-name">PyMudCement Optima Pro</div>
            <div class="app-ver">v5.0 · ENTERPRISE</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Well Geometry</div>', unsafe_allow_html=True)
    total_depth = st.number_input("Total depth (ft MD)", value=10000.0, step=500.0)
    flow_rate = st.number_input("Flow rate (GPM)", value=550.0, step=25.0)

    st.markdown('<div class="sidebar-section">Mud Properties</div>', unsafe_allow_html=True)
    default_mw = st.session_state.auto_mw if st.session_state.auto_mw is not None else 12.5
    surface_mw = st.number_input("Mud weight (ppg)", value=default_mw, step=0.1)
    rheology = st.selectbox("Rheology model", [r.value for r in RheologyModel])
    default_pv = st.session_state.auto_pv if st.session_state.auto_pv is not None else 22.0
    default_yp = st.session_state.auto_yp if st.session_state.auto_yp is not None else 16.0
    pv = st.number_input("Plastic viscosity (cP)", value=default_pv, step=1.0)
    yp = st.number_input("Yield point (lb/100ft²)", value=default_yp, step=1.0)

    st.markdown('<div class="sidebar-section">Mud Report Upload</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("CSV or Excel", type=["csv", "xlsx"], key="mud_uploader", label_visibility="collapsed")
    if uploaded_file is not None and not st.session_state.parsed:
        try:
            file_type = "csv" if uploaded_file.type == "text/csv" else "excel"
            data = parse_mud_report(uploaded_file.read(), file_type)
            st.session_state.auto_pv = data["pv_cp"]
            st.session_state.auto_yp = data["yp"]
            st.session_state.auto_mw = data["mw_ppg"]
            st.session_state.parsed = True
            st.success(f"PV={data['pv_cp']} cP · YP={data['yp']} · MW={data['mw_ppg']} ppg")
        except Exception as e:
            st.error(f"Parse error: {e}")
            st.session_state.parsed = False
    if uploaded_file is None and st.session_state.parsed:
        st.session_state.parsed = False

    st.markdown('<div class="sidebar-section">Pore / Fracture Gradients</div>', unsafe_allow_html=True)
    grad_df = st.data_editor(
        pd.DataFrame({
            "Depth (ft)": [5000, 10000],
            "Pore Pressure (ppg)": [9.0, 9.5],
            "Fracture Gradient (ppg)": [14.0, 15.5]
        }),
        num_rows="dynamic",
        key="gradient_editor",
        use_container_width=True
    )
    st.session_state.gradient_df = grad_df

    st.divider()
    if st.button("Sign out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()


# ============================
# TOP BAR
# ============================
uinfo = st.session_state.user_info
st.markdown(f"""
<div class="topbar">
    <div class="topbar-left">
        <img src="data:image/png;base64,{logo_base64}" style="height:34px;">
        <div class="topbar-title">PyMud<span>Cement</span> Optima Pro</div>
        <span class="topbar-badge">v5.0</span>
    </div>
    <div class="topbar-user">
        <div class="topbar-dot"></div>
        <div>
            <div class="user-name">{uinfo["username"]}</div>
            <div class="user-company">{uinfo["company"]}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================
# MAIN TABS
# ============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚙  Hydraulics",
    "🌐  3D Trajectory",
    "🤖  AI Co-Pilot",
    "🏗  Cementing",
    "📄  PDF Export"
])


# ─────────────────────────────────────────────
# TAB 1 — HYDRAULICS
# ─────────────────────────────────────────────
with tab1:
    st.markdown("""
    <div class="section-head">
        <div class="dot"></div><h3>Multi-Segment Wellbore Geometry</h3>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Define each section of the drill string and open hole. Values persist across reruns.")

    default_segments = pd.DataFrame([
        {"Segment Name": "Surface Drill Pipe", "Length (ft)": 7000.0, "Pipe OD (in)": 5.0,
         "Pipe ID (in)": 4.276, "Hole ID (in)": 12.25, "Mud Weight (ppg)": surface_mw},
        {"Segment Name": "Heavy Weight Pipe", "Length (ft)": 2000.0, "Pipe OD (in)": 5.0,
         "Pipe ID (in)": 3.000, "Hole ID (in)": 8.50, "Mud Weight (ppg)": surface_mw},
        {"Segment Name": "Drill Collars / BHA", "Length (ft)": 1000.0, "Pipe OD (in)": 6.75,
         "Pipe ID (in)": 2.250, "Hole ID (in)": 8.50, "Mud Weight (ppg)": surface_mw},
    ])
    edited_df = st.data_editor(default_segments, num_rows="dynamic", use_container_width=True)

    if st.button("▶  Run Engineering Calculations", type="primary", use_container_width=True):
        with st.spinner("Solving hydraulics..."):
            try:
                engine = DrillingHydraulicsEngine(
                    surface_mud_weight_ppg=surface_mw,
                    flow_rate_gpm=flow_rate,
                    total_depth_ft=total_depth,
                    plastic_viscosity_cp=pv,
                    yield_point_lb_100ft2=yp,
                    rheology_model=RheologyModel(rheology)
                )
                for _, row in edited_df.iterrows():
                    engine.add_segment(WellSegment(
                        name=str(row["Segment Name"]),
                        length_ft=float(row["Length (ft)"]),
                        pipe_od_in=float(row["Pipe OD (in)"]),
                        pipe_id_in=float(row["Pipe ID (in)"]),
                        hole_id_in=float(row["Hole ID (in)"]),
                        mud_weight_ppg=float(row["Mud Weight (ppg)"]),
                        viscosity_cp=pv,
                        yield_point_lb_100ft2=yp
                    ))
                engine.add_nozzle(NozzleInput(size_in_32nds=12))
                engine.add_nozzle(NozzleInput(size_in_32nds=12))
                engine.add_nozzle(NozzleInput(size_in_32nds=12))
                results = engine.solve()
                st.session_state.latest_results = results

                # KPI Cards
                ecd = results['equivalent_circulating_density_ecd_ppg']
                spp = results['standpipe_pressure_spp_psi']
                apl = results['total_annular_pressure_loss_psi']
                bit = results['bit_hydraulics']['bit_pressure_drop_psi']
                st.markdown(f"""
                <div class="kpi-grid">
                    <div class="kpi-card {'amber' if ecd > 14 else ''}">
                        <div class="kpi-label">Equiv. Circ. Density</div>
                        <div class="kpi-value">{ecd:.3f}</div>
                        <div class="kpi-unit">ppg</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Standpipe Pressure</div>
                        <div class="kpi-value">{spp:.0f}</div>
                        <div class="kpi-unit">psi</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Annular Pressure Loss</div>
                        <div class="kpi-value">{apl:.0f}</div>
                        <div class="kpi-unit">psi</div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-label">Bit Nozzle Loss</div>
                        <div class="kpi-value">{bit:.0f}</div>
                        <div class="kpi-unit">psi</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Segment breakdown
                st.markdown("""
                <div class="section-head">
                    <div class="dot"></div><h3>Segment Analytics Breakdown</h3>
                </div>
                """, unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(results["segment_breakdown"]), use_container_width=True)

                # Gradient check
                if "gradient_df" in st.session_state and not st.session_state.gradient_df.empty:
                    gdf = st.session_state.gradient_df.copy()
                    gdf = gdf.apply(pd.to_numeric, errors='coerce').dropna()
                    if not gdf.empty:
                        try:
                            profile = PressureGradientProfile(
                                depths=gdf["Depth (ft)"].tolist(),
                                pore_pressures=gdf["Pore Pressure (ppg)"].tolist(),
                                frac_gradients=gdf["Fracture Gradient (ppg)"].tolist()
                            )
                            sw = profile.get_safe_window(total_depth)
                            st.markdown("""
                            <div class="section-head">
                                <div class="dot"></div><h3>Formation Pressure Integrity</h3>
                            </div>
                            """, unsafe_allow_html=True)
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Pore Pressure @ TD", f"{sw['pore']:.2f} ppg")
                            c2.metric("Fracture Gradient @ TD", f"{sw['fracture']:.2f} ppg")
                            c3.metric("Current ECD", f"{ecd:.3f} ppg")
                            if ecd > sw["fracture"]:
                                st.error(f"CRITICAL — ECD {ecd:.2f} ppg exceeds fracture gradient {sw['fracture']:.2f} ppg. Risk of fluid losses.")
                                with st.expander("Recommended actions"):
                                    st.write("• Reduce flow rate (GPM)")
                                    st.write("• Lower mud weight if wellbore security permits")
                                    st.write("• Circulate bottoms-up before resuming")
                            elif ecd > sw["fracture"] * 0.95:
                                st.warning(f"ECD {ecd:.2f} ppg approaching fracture limit {sw['fracture']:.2f} ppg — monitor closely.")
                            elif ecd < sw["pore"]:
                                st.warning(f"ECD {ecd:.2f} ppg below pore pressure {sw['pore']:.2f} ppg — risk of influx.")
                            else:
                                st.success(f"ECD {ecd:.2f} ppg within safe window [{sw['min_mw_ppg']:.2f}, {sw['max_mw_ppg']:.2f}] ppg.")
                        except Exception as e:
                            st.warning(f"Could not build gradient profile: {e}")

                # Hole cleaning
                last_vel = results["segment_breakdown"][-1]["annular_velocity_fpm"]
                slip = engine.calculate_cuttings_slip_velocity(surface_mw, pv)
                tr = last_vel / slip if slip > 0 else 0
                if tr < 1.5:
                    st.warning(f"Low cuttings transport ratio ({tr:.2f}) — increase flow rate.")
                else:
                    st.success(f"Cuttings transport ratio {tr:.2f} — adequate hole cleaning.")

            except Exception as e:
                st.error(f"Execution error: {str(e)}")


# ─────────────────────────────────────────────
# TAB 2 — 3D TRAJECTORY
# ─────────────────────────────────────────────
with tab2:
    st.markdown("""
    <div class="section-head">
        <div class="dot"></div><h3>Interactive 3D Well Trajectory</h3>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Directional wellpath — vertical, build, tangent, and drop sections rendered from survey geometry.")

    md = np.linspace(0, total_depth, 200)
    inc = np.zeros_like(md)
    az = np.radians(np.full_like(md, 60.0))

    inc[md <= 2000] = 0.0
    mask_build = (md > 2000) & (md <= 5000)
    inc[mask_build] = np.radians(45.0 * (md[mask_build] - 2000) / 3000)
    mask_tang = (md > 5000) & (md <= 8000)
    inc[mask_tang] = np.radians(45.0)
    mask_drop = (md > 8000) & (md <= total_depth)
    inc[mask_drop] = np.radians(45.0 - 15.0 * (md[mask_drop] - 8000) / (total_depth - 8000))

    x, y, z = np.zeros_like(md), np.zeros_like(md), np.zeros_like(md)
    for i in range(1, len(md)):
        dm = md[i] - md[i - 1]
        ai = (inc[i] + inc[i - 1]) / 2
        aa = (az[i] + az[i - 1]) / 2
        x[i] = x[i - 1] + dm * np.sin(ai) * np.cos(aa)
        y[i] = y[i - 1] + dm * np.sin(ai) * np.sin(aa)
        z[i] = z[i - 1] + dm * np.cos(ai)

    key_depths = [0, 2000, 5000, 8000, total_depth]
    key_labels = ["Surface", "KOP", "EOB", "Start Drop", "TD"]
    key_idx = [np.argmin(np.abs(md - d)) for d in key_depths]

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z, mode='lines',
        line=dict(color=z, colorscale='Blues', width=6, showscale=True,
                  colorbar=dict(title="TVD (ft)", tickfont=dict(color="#7A92B4", size=10),
                                titlefont=dict(color="#7A92B4", size=11))),
        name='Wellpath'
    ))
    fig.add_trace(go.Scatter3d(
        x=x[key_idx], y=y[key_idx], z=z[key_idx],
        mode='markers+text',
        marker=dict(size=6, color='#F5C842', symbol='circle',
                    line=dict(color='#0D1525', width=1)),
        text=key_labels, textposition='top center',
        textfont=dict(color="#F5C842", size=10),
        name='Key Points'
    ))
    fig.update_layout(
        scene=dict(
            xaxis_title='Easting (ft)', yaxis_title='Northing (ft)', zaxis_title='TVD (ft)',
            bgcolor='rgba(0,0,0,0)',
            xaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='#0F2044',
                       color='#4A6A9A', zerolinecolor='#0F2044'),
            yaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='#0F2044',
                       color='#4A6A9A', zerolinecolor='#0F2044'),
            zaxis=dict(backgroundcolor='rgba(0,0,0,0)', gridcolor='#0F2044',
                       color='#4A6A9A', zerolinecolor='#0F2044', autorange='reversed'),
        ),
        margin=dict(l=0, r=0, b=0, t=20),
        height=640,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            x=0.02, y=0.98,
            bgcolor='rgba(13,21,37,0.85)',
            bordercolor='#1A3A6E', borderwidth=1,
            font=dict(color='#A8C4F0', size=11)
        )
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────
# TAB 3 — AI CO-PILOT
# ─────────────────────────────────────────────
with tab3:
    st.markdown("""
    <div class="section-head">
        <div class="dot"></div><h3>AI Real-Time Drilling Assistant</h3>
    </div>
    """, unsafe_allow_html=True)

    if "latest_results" in st.session_state:
        res = st.session_state.latest_results
        ecd = res["equivalent_circulating_density_ecd_ppg"]
        spp = res["standpipe_pressure_spp_psi"]
        apl = res["total_annular_pressure_loss_psi"]

        status = "CRITICAL" if ecd > 15.0 else "NOMINAL"
        status_color = "#F87171" if status == "CRITICAL" else "#4ADE80"
        st.markdown(f"""
        <div style="background:#0D1525;border:1px solid #0F2044;border-left:3px solid {status_color};
                    border-radius:8px;padding:1.1rem 1.3rem;margin-bottom:1rem;">
            <span class="tag-pill" style="background:rgba(0,0,0,0.3);
                  color:{status_color};border:1px solid {status_color}30;">
                SYSTEM STATUS · {status}
            </span>
            <div style="margin-top:0.6rem;font-size:0.82rem;color:#D0DCF0;line-height:1.6;">
        """, unsafe_allow_html=True)
        if status == "CRITICAL":
            st.markdown(f"""
            <b>ECD {ecd:.2f} ppg exceeds structural fracture threshold (15.0 ppg).</b>
            Risk of severe fluid losses detected. Immediate corrective action required.
            </div></div>
            """, unsafe_allow_html=True)
            with st.expander("Recommended actions"):
                st.write("1. Reduce pump SPM to lower annular velocity and dynamic pressure drop.")
                st.write("2. Perform mud dilution to reduce Plastic Viscosity.")
                st.write("3. Notify company man — consider staging run.")
        else:
            st.markdown(f"""
            Operating gradient within dynamic pore-fracture window.
            Hydraulics, hole cleaning transport, and nozzle velocities within specification.
            </div></div>
            """, unsafe_allow_html=True)
            st.success("All hydraulic parameters nominal. No corrective action required.")

        st.markdown("""
        <div class="section-head" style="margin-top:1.5rem;">
            <div class="dot"></div><h3>Live Telemetry Summary</h3>
        </div>
        """, unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("ECD", f"{ecd:.3f} ppg")
        c2.metric("Standpipe Pressure", f"{spp:.0f} psi")
        c3.metric("Annular Pressure Loss", f"{apl:.0f} psi")
    else:
        st.info("Run the hydraulics matrix on the **Hydraulics** tab to activate AI telemetry.")


# ─────────────────────────────────────────────
# TAB 4 — CEMENTING
# ─────────────────────────────────────────────
with tab4:
    st.markdown("""
    <div class="section-head">
        <div class="dot"></div><h3>Primary Cementing & P&A Plug Design</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")
    with col1:
        st.markdown('<p style="font-size:0.7rem;color:#4A6A9A;text-transform:uppercase;letter-spacing:.08em;font-weight:700;margin-bottom:.6rem;">Casing & Hole</p>', unsafe_allow_html=True)
        hole_dia = st.number_input("Hole diameter (in)", value=8.5, min_value=4.0, step=0.5)
        casing_od = st.number_input("Casing OD (in)", value=7.0, min_value=2.0, step=0.5)
        casing_id = st.number_input("Casing ID (in)", value=6.276, min_value=1.0, step=0.1)
        interval_ft = st.number_input("Cemented interval (ft)", value=5000.0, step=100.0)
        washout_pct = st.number_input("Washout factor (%)", value=15.0, step=1.0)
    with col2:
        st.markdown('<p style="font-size:0.7rem;color:#4A6A9A;text-transform:uppercase;letter-spacing:.08em;font-weight:700;margin-bottom:.6rem;">Slurry & Conditions</p>', unsafe_allow_html=True)
        lead_dens = st.number_input("Lead slurry density (ppg)", value=12.5, step=0.1)
        tail_dens = st.number_input("Tail slurry density (ppg)", value=15.8, step=0.1)
        spacer_dens = st.number_input("Spacer density (ppg)", value=11.0, step=0.1)
        disp_dens = st.number_input("Displacement fluid density (ppg)", value=10.0, step=0.1)
        tail_length = st.number_input("Tail slurry length (ft)", value=500.0, step=50.0)
        bht = st.number_input("BHT (°F)", value=180.0, step=5.0)
        shoe_track = st.number_input("Shoe track length (ft)", value=40.0, step=5.0)

    if st.button("▶  Run Cementing Design", key="cement_btn", type="primary", use_container_width=True):
        with st.spinner("Designing cement job..."):
            try:
                params = PrimaryCementingInput(
                    hole_diameter_in=hole_dia, casing_od_in=casing_od, casing_id_in=casing_id,
                    interval_length_ft=interval_ft, washout_factor_pct=washout_pct,
                    shoe_track_length_ft=shoe_track, lead_slurry_density_ppg=lead_dens,
                    tail_slurry_density_ppg=tail_dens, spacer_density_ppg=spacer_dens,
                    displacement_fluid_density_ppg=disp_dens, tail_slurry_length_ft=tail_length,
                    bht_fahrenheit=bht
                )
                engine = CementingEngine()
                result = engine.design_primary_job(params)
                st.session_state.cementing_results = result
                st.session_state.cementing_params = {
                    "casing_od": casing_od, "hole_dia": hole_dia, "interval_ft": interval_ft
                }

                st.markdown("""
                <div class="section-head">
                    <div class="dot"></div><h3>Cementing Job Volumes</h3>
                </div>
                """, unsafe_allow_html=True)
                cols = st.columns(4)
                cols[0].metric("Lead Slurry", f"{result['lead_slurry_volume_bbl']:.2f} bbl")
                cols[1].metric("Tail Slurry", f"{result['tail_slurry_volume_bbl']:.2f} bbl")
                cols[2].metric("Spacer", f"{result['spacer_volume_bbl']:.2f} bbl")
                cols[3].metric("Displacement", f"{result['displacement_volume_bbl']:.2f} bbl")
                st.metric("Plug Bumping Pressure", f"{result['recommended_plug_bumping_pressure_psi']:.1f} psi")

                st.markdown("""
                <div class="section-head" style="margin-top:1.2rem;">
                    <div class="dot"></div><h3>Suggested Additives</h3>
                </div>
                """, unsafe_allow_html=True)
                for add in result["suggested_additives"]:
                    cat_class = "tag-blue"
                    st.markdown(f"""
                    <div class="additive-card">
                        <div style="flex:1;">
                            <div class="add-name">{add['name']}
                                <span class="tag-pill {cat_class}" style="margin-left:.4rem;">{add['category']}</span>
                            </div>
                            <div class="add-desc">{add['description']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("""
                <div class="section-head" style="margin-top:1.2rem;">
                    <div class="dot"></div><h3>P&A / Abandonment Plug Design</h3>
                </div>
                """, unsafe_allow_html=True)
                with st.expander("Design an abandonment plug"):
                    plug_len = st.number_input("Plug length (ft)", value=200.0, step=50.0, key="plug_len")
                    plug_dens = st.number_input("Plug slurry density (ppg)", value=15.0, step=0.1, key="plug_dens")
                    mud_dens = st.number_input("Mud density in hole (ppg)", value=12.0, step=0.1, key="mud_dens")
                    if st.button("Calculate plug", key="plug_btn"):
                        pr = engine.design_abandonment_plug(
                            hole_dia_in=hole_dia, plug_length_ft=plug_len,
                            slurry_density_ppg=plug_dens, mud_density_ppg=mud_dens
                        )
                        c1, c2, c3 = st.columns(3)
                        c1.metric("Plug Volume", f"{pr['plug_volume_bbl']:.2f} bbl")
                        c2.metric("Cement Sacks", f"{pr['cement_sacks_required']} sk")
                        c3.metric("Hydrostatic Gain", f"{pr['net_hydrostatic_gain_psi']:.1f} psi")

            except Exception as e:
                st.error(f"Cementing calculation error: {e}")

    if st.button("📊  Compare with Industry Benchmarks", key="bench_btn"):
        if st.session_state.cementing_results and st.session_state.cementing_params:
            result = st.session_state.cementing_results
            params = st.session_state.cementing_params
            comp = compare_cementing_results(result, params["casing_od"], params["hole_dia"], params["interval_ft"])
            st.markdown("""
            <div class="section-head">
                <div class="dot"></div><h3>Industry Benchmark Comparison</h3>
            </div>
            """, unsafe_allow_html=True)
            if "error" in comp:
                st.warning(comp["error"])
            else:
                st.caption(comp.get("description", ""))
                c1, c2 = st.columns(2)
                c1.metric("Lead Slurry", f"{comp['lead_slurry']['software']:.2f} bbl",
                          f"{comp['lead_slurry']['deviation_pct']:.1f}% vs industry")
                c2.metric("Tail Slurry", f"{comp['tail_slurry']['software']:.2f} bbl",
                          f"{comp['tail_slurry']['deviation_pct']:.1f}% vs industry")
                st.metric("Spacer Volume", f"{comp['spacer']['software']:.2f} bbl",
                          f"{comp['spacer']['deviation_pct']:.1f}% vs industry")
                if abs(comp['lead_slurry']['deviation_pct']) > 15 or abs(comp['tail_slurry']['deviation_pct']) > 15:
                    st.warning("Deviation >15% from industry standards — review design assumptions.")
        else:
            st.warning("Run cementing design first.")


# ─────────────────────────────────────────────
# TAB 5 — PDF EXPORT
# ─────────────────────────────────────────────
with tab5:
    st.markdown("""
    <div class="section-head">
        <div class="dot"></div><h3>Export Compliance Report</h3>
    </div>
    """, unsafe_allow_html=True)

    if "latest_results" in st.session_state:
        ecd = st.session_state.latest_results["equivalent_circulating_density_ecd_ppg"]
        severity = "RED" if ecd >= 15.0 else "GREEN"
        st.markdown(f"""
        <div style="background:#0D1525;border:1px solid #0F2044;border-radius:8px;padding:1rem 1.2rem;margin-bottom:1.2rem;">
            <div style="font-size:0.7rem;color:#4A6A9A;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.4rem;">Report Preview</div>
            <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
                <div><span style="color:#4A6A9A;font-size:.75rem;">Well</span>
                     <div style="color:#D0DCF0;font-size:.85rem;font-weight:600;">Deepwater Wilcox Target</div></div>
                <div><span style="color:#4A6A9A;font-size:.75rem;">Rig</span>
                     <div style="color:#D0DCF0;font-size:.85rem;font-weight:600;">Rig-05 Executive</div></div>
                <div><span style="color:#4A6A9A;font-size:.75rem;">Company</span>
                     <div style="color:#D0DCF0;font-size:.85rem;font-weight:600;">{uinfo['company']}</div></div>
                <div><span style="color:#4A6A9A;font-size:.75rem;">Status</span>
                     <div><span class="tag-pill {'tag-green' if severity=='GREEN' else 'tag-red'}">{severity}</span></div></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("⬇  Generate & Download PDF Report", type="primary", use_container_width=True):
            with st.spinner("Building PDF..."):
                project_meta = {
                    "name": "Deepwater Wilcox Target",
                    "rig_name": "Rig-05 Executive",
                    "company": uinfo["company"]
                }
                diag_meta = {
                    "severity": severity,
                    "matched_hazard": "Formation Fracturing Risk" if ecd >= 15.0 else "None",
                    "detailed_diagnosis": f"Operating ECD is {ecd:.2f} ppg."
                }
                cement_data = st.session_state.get("cementing_results", None)
                pdf_buffer = generate_pdf_payload(
                    project_meta,
                    st.session_state.latest_results,
                    diag_meta,
                    engineer_name=uinfo["username"],
                    cementing_results=cement_data
                )
                st.download_button(
                    label="📥  Download PDF Document",
                    data=pdf_buffer,
                    file_name=f"PyMudCement_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    else:
        st.info("Complete hydraulics calculations on the **Hydraulics** tab before generating a report.")


# ============================
# FOOTER
# ============================
st.markdown("""
<div class="app-footer">
    © 2026 PyMudCement Optima Pro v5.0 &nbsp;·&nbsp; Enterprise Hydraulic Engine &nbsp;·&nbsp; All rights reserved
</div>
""", unsafe_allow_html=True)
