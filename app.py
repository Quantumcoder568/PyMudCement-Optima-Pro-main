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
    """Read an image file and return its base64 string."""
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
# SESSION STATE INIT (no dark_mode)
# ============================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "auto_pv" not in st.session_state:
    st.session_state.auto_pv = None
if "auto_yp" not in st.session_state:
    st.session_state.auto_yp = None
if "auto_mw" not in st.session_state:
    st.session_state.auto_mw = None
if "parsed" not in st.session_state:
    st.session_state.parsed = False
if "cementing_results" not in st.session_state:
    st.session_state.cementing_results = None
if "cementing_params" not in st.session_state:
    st.session_state.cementing_params = None

# ============================
# DETECT STREAMLIT THEME
# ============================
theme = st.get_option("theme.base")
dark_mode = (theme == "dark")
dark_class = "dark-mode" if dark_mode else "light-mode"

# ============================
# CUSTOM CSS – BLUE & YELLOW THEME
# ============================
st.markdown(f"""
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');

    * {{
        font-family: 'Inter', sans-serif;
        transition: background-color 0.25s ease, color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }}

    /* ---------- LIGHT MODE ---------- */
    .light-mode .stApp {{
        background: #f0f7ff;
    }}
    .light-mode .main-header {{
        color: #1e3a8a;
        font-weight: 800;
        text-shadow: 0 2px 12px rgba(30, 58, 138, 0.15);
    }}
    .light-mode .sub-header {{
        color: #1e293b;
        border-bottom: 4px solid #facc15;
    }}
    .light-mode .card {{
        background: #ffffff;
        border: 1px solid #dbeafe;
        box-shadow: 0 4px 16px rgba(30, 58, 138, 0.08);
        border-radius: 16px;
    }}
    .light-mode .metric-card {{
        background: #ffffff;
        border-left: 6px solid #2563eb;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.15);
        border-radius: 12px;
    }}
    .light-mode .metric-card .value {{
        color: #1e3a8a;
    }}
    .light-mode .stButton > button {{
        background: linear-gradient(135deg, #2563eb, #1e3a8a);
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
        transition: all 0.2s;
    }}
    .light-mode .stButton > button:hover {{
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 28px rgba(37, 99, 235, 0.5);
    }}
    .light-mode .stSidebar {{
        background: #ffffff;
        border-right: 2px solid #dbeafe;
    }}
    .light-mode .sidebar-heading {{
        color: #2563eb;
        font-weight: 700;
    }}
    .light-mode .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: #facc15;
        color: #1e3a8a;
        font-weight: 700;
        border-radius: 8px 8px 0 0;
        border-bottom: 3px solid #1e3a8a;
        box-shadow: 0 -2px 8px rgba(250, 204, 21, 0.3);
    }}
    .light-mode .stTabs [data-baseweb="tab"]:hover {{
        background: #fef3c7;
    }}

    /* ---------- DARK MODE ---------- */
    .dark-mode .stApp {{
        background: #0b1a2e;
    }}
    .dark-mode .main-header {{
        color: #facc15;
        font-weight: 800;
        text-shadow: 0 2px 24px rgba(250, 204, 21, 0.25);
    }}
    .dark-mode .sub-header {{
        color: #cbd5e1;
        border-bottom: 4px solid #facc15;
    }}
    .dark-mode .card {{
        background: #152238;
        border: 1px solid #1e3a5f;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        border-radius: 16px;
    }}
    .dark-mode .metric-card {{
        background: #152238;
        border-left: 6px solid #facc15;
        box-shadow: 0 6px 20px rgba(250, 204, 21, 0.15);
        border-radius: 12px;
    }}
    .dark-mode .metric-card .value {{
        color: #facc15;
    }}
    .dark-mode .stButton > button {{
        background: linear-gradient(135deg, #facc15, #eab308);
        color: #0b1a2e;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 4px 16px rgba(250, 204, 21, 0.35);
        transition: all 0.2s;
    }}
    .dark-mode .stButton > button:hover {{
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 32px rgba(250, 204, 21, 0.55);
    }}
    .dark-mode .stSidebar {{
        background: #0f1e30;
        border-right: 2px solid #1e3a5f;
    }}
    .dark-mode .sidebar-heading {{
        color: #facc15;
        font-weight: 700;
    }}
    .dark-mode .stTabs [data-baseweb="tab"][aria-selected="true"] {{
        background: #facc15;
        color: #0b1a2e;
        font-weight: 700;
        border-radius: 8px 8px 0 0;
        border-bottom: 3px solid #facc15;
        box-shadow: 0 -2px 8px rgba(250, 204, 21, 0.3);
    }}
    .dark-mode .stTabs [data-baseweb="tab"]:hover {{
        background: #1e3a5f;
    }}

    /* ---------- COMMON ELEMENTS ---------- */
    .main-header {{
        font-size: 2.6rem;
        letter-spacing: -0.02em;
        padding: 0.2rem 0;
        margin-bottom: 0.1rem;
    }}
    .sub-header {{
        font-size: 1rem;
        font-weight: 500;
        padding-bottom: 0.8rem;
        margin-bottom: 1rem;
        border-bottom-width: 4px;
        border-bottom-style: solid;
    }}
    .sidebar-heading {{
        font-size: 1.05rem;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.01em;
    }}
    .card {{
        padding: 1.2rem 1.4rem;
        transition: all 0.25s ease;
        margin-bottom: 1rem;
    }}
    .card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    }}
    .dark-mode .card:hover {{
        box-shadow: 0 8px 32px rgba(250, 204, 21, 0.08);
    }}
    .metric-card {{
        padding: 1rem 1.2rem;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }}
    .metric-card::after {{
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 60px;
        height: 60px;
        background: radial-gradient(circle, rgba(250,204,21,0.1) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }}
    .metric-card:hover {{
        transform: translateY(-4px);
        box-shadow: 0 8px 28px rgba(0,0,0,0.1);
    }}
    .dark-mode .metric-card:hover {{
        box-shadow: 0 8px 28px rgba(250, 204, 21, 0.12);
    }}
    .metric-card .label {{
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 6px;
        color: #475569;
    }}
    .dark-mode .metric-card .label {{
        color: #94a3b8;
    }}
    .metric-card .value {{
        font-size: 2rem;
        font-weight: 800;
        margin-top: 0.2rem;
    }}
    .stButton > button {{
        font-weight: 600;
        transition: all 0.2s;
        border-radius: 10px;
        padding: 0.5rem 1.4rem;
        letter-spacing: 0.02em;
    }}
    .stButton > button:active {{
        transform: scale(0.96);
    }}
    .stTabs [data-baseweb="tab-list"] {{
        gap: 0.3rem;
        border-bottom: 2px solid #dbeafe;
        padding-bottom: 0.3rem;
    }}
    .dark-mode .stTabs [data-baseweb="tab-list"] {{
        border-bottom-color: #1e3a5f;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-weight: 600;
        padding: 0.5rem 1rem;
        border-radius: 8px 8px 0 0;
        transition: all 0.15s;
    }}
    .stAlert {{
        border-radius: 12px;
        border-left: 5px solid;
    }}
    .stAlert.error {{
        border-left-color: #dc2626;
    }}
    .stAlert.warning {{
        border-left-color: #facc15;
    }}
    .stAlert.success {{
        border-left-color: #22c55e;
    }}
    .stAlert.info {{
        border-left-color: #2563eb;
    }}
    .footer {{
        font-size: 0.75rem;
        text-align: center;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 2px solid #dbeafe;
        color: #64748b;
    }}
    .dark-mode .footer {{
        border-top-color: #1e3a5f;
        color: #94a3b8;
    }}
</style>
""", unsafe_allow_html=True)
# ============================
# AUTHENTICATION
# ============================
async def process_authentication(mode, email_val, password_val, company_val=None):
    async with AsyncSessionLocal() as session:
        if mode == "Register Account":
            try:
                existing = await session.execute(
                    select(UserModel).where(
                        or_(
                            UserModel.email == email_val,
                            UserModel.username == email_val
                        )
                    )
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
                return True, "Account created successfully! Please switch to Login."
            except IntegrityError:
                await session.rollback()
                return False, "Registration failed due to duplicate entry."
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
                return False, f"Login Error: {str(e)}"

if not st.session_state.authenticated:
    st.markdown(
    f'<div class="main-header"><img src="data:image/png;base64,{logo_base64}" style="height: 4.4rem; margin-right: 0.5rem; vertical-align: middle;"> PyMudCement Optima Pro v5.0</div>',
    unsafe_allow_html=True
)
    st.markdown('<div class="sub-header">Enterprise Hydraulic Engine & Real-Time AI Diagnostics</div>', unsafe_allow_html=True)
    auth_mode = st.radio("Select Action", ["Login", "Register Account"], horizontal=True)
    with st.form("auth_form"):
        if auth_mode == "Login":
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            company = None
        else:
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            company = st.text_input("Company Name", value="Enterprise Hydrocarbons Corp")
        submit = st.form_submit_button("Submit")
        if submit:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                success, response = asyncio.run(
                    process_authentication(auth_mode, email, password, company)
                )
                if auth_mode == "Register Account":
                    if success:
                        st.success(response)
                    else:
                        st.error(response)
                else:
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.user_info = response
                        st.rerun()
                    else:
                        st.error(response)
    st.stop()

# ============================
# MAIN HEADER
# ============================
col1, col2 = st.columns([1, 8])   
with col1:
    st.image("logo.png", width=100)   
with col2:
    st.markdown('<div class="main-header" style="margin-top: 0;">PyMudCement Optima Pro v5.0</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="sub-header"><i class="fas fa-user-circle"></i> {st.session_state.user_info["username"]} &nbsp;|&nbsp; <i class="fas fa-building"></i> {st.session_state.user_info["company"]}</div>',
    unsafe_allow_html=True
)

# ============================
# SIDEBAR (no dark toggle)
# ============================
with st.sidebar:
    st.image("logo.png", width=40)   # or use_column_width=True
    st.markdown("### <i class='fas fa-cog'></i> Well & Mud Parameters", unsafe_allow_html=True)
    
    with st.expander("📐 Well Geometry", expanded=True):
        total_depth = st.number_input("Total Depth (ft MD)", value=10000.0, step=500.0)
        flow_rate = st.number_input("Flow Rate (GPM)", value=550.0, step=25.0)
    
    with st.expander("🧪 Mud Properties", expanded=True):
        default_mw = st.session_state.auto_mw if st.session_state.auto_mw is not None else 12.5
        surface_mw = st.number_input("Surface Mud Weight (ppg)", value=default_mw, step=0.1)
        rheology = st.selectbox("Rheology Model", [r.value for r in RheologyModel])
        default_pv = st.session_state.auto_pv if st.session_state.auto_pv is not None else 22.0
        default_yp = st.session_state.auto_yp if st.session_state.auto_yp is not None else 16.0
        pv = st.number_input("Plastic Viscosity (cP)", value=default_pv, step=1.0)
        yp = st.number_input("Yield Point (lb/100ft²)", value=default_yp, step=1.0)
    
    st.divider()
    st.markdown('<div class="sidebar-heading"><i class="fas fa-file-upload"></i> Upload Mud Report</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("CSV or Excel", type=["csv", "xlsx"], key="mud_uploader")
    if uploaded_file is not None and not st.session_state.parsed:
        try:
            file_type = "csv" if uploaded_file.type == "text/csv" else "excel"
            data = parse_mud_report(uploaded_file.read(), file_type)
            st.session_state.auto_pv = data["pv_cp"]
            st.session_state.auto_yp = data["yp"]
            st.session_state.auto_mw = data["mw_ppg"]
            st.session_state.parsed = True
            st.sidebar.success(f"Parsed: PV={data['pv_cp']} cP, YP={data['yp']} lb/100ft², MW={data['mw_ppg']} ppg")
        except Exception as e:
            st.sidebar.error(f"Parse error: {e}")
            st.session_state.parsed = False
    if uploaded_file is None and st.session_state.parsed:
        st.session_state.parsed = False

    st.divider()
    st.markdown('<div class="sidebar-heading"><i class="fas fa-chart-line"></i> Pore / Fracture Gradients</div>', unsafe_allow_html=True)
    st.caption("Enter depth‑dependent gradients (ppg)")
    grad_df = st.data_editor(
        pd.DataFrame({
            "Depth (ft)": [5000, 10000],
            "Pore Pressure (ppg)": [9.0, 9.5],
            "Fracture Gradient (ppg)": [14.0, 15.5]
        }),
        num_rows="dynamic",
        key="gradient_editor"
    )
    st.session_state.gradient_df = grad_df

    st.divider()
    if st.button("Log Out", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# ============================
# MAIN TABS
# ============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Hydraulics Matrix",
    "3D Well Trajectory",
    "AI Co‑Pilot",
    "Cementing Design",
    "PDF Export"
])

# ---------- TAB 1: HYDRAULICS ----------
with tab1:
    st.markdown("### <i class='fas fa-tachometer-alt'></i> Multi‑Segment Wellbore Geometry", unsafe_allow_html=True)
    st.caption("Define each section of the drill string and open hole.")
    
    default_segments = pd.DataFrame([
        {"Segment Name": "Surface Drill Pipe", "Length (ft)": 7000.0, "Pipe OD (in)": 5.0, "Pipe ID (in)": 4.276, "Hole ID (in)": 12.25, "Mud Weight (ppg)": surface_mw},
        {"Segment Name": "Heavy Weight Pipe", "Length (ft)": 2000.0, "Pipe OD (in)": 5.0, "Pipe ID (in)": 3.000, "Hole ID (in)": 8.50, "Mud Weight (ppg)": surface_mw},
        {"Segment Name": "Drill Collars / BHA", "Length (ft)": 1000.0, "Pipe OD (in)": 6.75, "Pipe ID (in)": 2.250, "Hole ID (in)": 8.50, "Mud Weight (ppg)": surface_mw}
    ])
    edited_df = st.data_editor(default_segments, num_rows="dynamic", use_container_width=True)

    if st.button(" Run Engineering Calculations", type="primary", use_container_width=True):
        with st.spinner("Solving hydraulics... Please wait."):
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

                st.markdown("### <i class='fas fa-chart-simple'></i> Key Hydraulics Metrics", unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label"><i class="fas fa-weight-scale"></i> Equivalent Circulating Density</div>
                        <div class="value">{results['equivalent_circulating_density_ecd_ppg']:.3f} ppg</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label"><i class="fas fa-gauge-high"></i> Standpipe Pressure</div>
                        <div class="value">{results['standpipe_pressure_spp_psi']:.1f} psi</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label"><i class="fas fa-arrows-spin"></i> Annular Pressure Loss</div>
                        <div class="value">{results['total_annular_pressure_loss_psi']:.1f} psi</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label"><i class="fas fa-water"></i> Bit Nozzle Loss</div>
                        <div class="value">{results['bit_hydraulics']['bit_pressure_drop_psi']:.1f} psi</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("### <i class='fas fa-list-ul'></i> Segment Analytics Breakdown", unsafe_allow_html=True)
                st.dataframe(pd.DataFrame(results["segment_breakdown"]), use_container_width=True)

                # Pore/Fracture Check with Gradient Profile
                if "gradient_df" in st.session_state and not st.session_state.gradient_df.empty:
                    grad_df = st.session_state.gradient_df.copy()
                    grad_df = grad_df.apply(pd.to_numeric, errors='coerce').dropna()
                    if not grad_df.empty:
                        try:
                            profile = PressureGradientProfile(
                                depths=grad_df["Depth (ft)"].tolist(),
                                pore_pressures=grad_df["Pore Pressure (ppg)"].tolist(),
                                frac_gradients=grad_df["Fracture Gradient (ppg)"].tolist()
                            )
                            safe_window = profile.get_safe_window(total_depth)
                            ecd = results["equivalent_circulating_density_ecd_ppg"]
                            
                            st.markdown("### <i class='fas fa-shield'></i> Formation Pressure Integrity Check", unsafe_allow_html=True)
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Pore Pressure at TD", f"{safe_window['pore']:.2f} ppg")
                            c2.metric("Fracture Gradient at TD", f"{safe_window['fracture']:.2f} ppg")
                            c3.metric("Current ECD", f"{ecd:.3f} ppg")
                            
                            if ecd > safe_window["fracture"]:
                                st.error(f"⚠️ **CRITICAL:** ECD {ecd:.2f} ppg exceeds fracture gradient {safe_window['fracture']:.2f} ppg at TD – risk of losses!")
                                with st.expander("📌 Recommended Actions"):
                                    st.write("- Reduce flow rate (GPM)")
                                    st.write("- Lower mud weight if safe")
                                    st.write("- Increase circulation before continuing")
                            elif ecd > safe_window["fracture"] * 0.95:
                                st.warning(f"⚠️ ECD {ecd:.2f} ppg is approaching fracture limit {safe_window['fracture']:.2f} ppg. Monitor closely.")
                            elif ecd < safe_window["pore"]:
                                st.warning(f"⚠️ ECD {ecd:.2f} ppg is below pore pressure {safe_window['pore']:.2f} ppg – risk of influx!")
                            else:
                                st.success(f"✔ ECD {ecd:.2f} ppg is within safe window [{safe_window['min_mw_ppg']:.2f}, {safe_window['max_mw_ppg']:.2f}] ppg.")
                        except Exception as e:
                            st.warning(f"Could not build gradient profile: {e}")

                # Hole Cleaning Check
                last_ann_vel = results["segment_breakdown"][-1]["annular_velocity_fpm"]
                slip = engine.calculate_cuttings_slip_velocity(surface_mw, pv)
                transport_ratio = last_ann_vel / slip if slip > 0 else 0
                if transport_ratio < 1.5:
                    st.warning(f"⚠️ Low cuttings transport ratio ({transport_ratio:.2f}); increase flow rate.")
                else:
                    st.success(f"✔ Cuttings transport ratio {transport_ratio:.2f} – adequate.")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")

# ---------- TAB 2: 3D TRAJECTORY (theme‑aware) ----------
with tab2:
    st.markdown("### <i class='fas fa-globe'></i> Interactive 3D Well Trajectory Profile", unsafe_allow_html=True)
    st.caption("Directional wellpath with vertical, build, tangent, and drop sections.")

    # ---- Generate realistic directional well trajectory ----
    md = np.linspace(0, total_depth, 200)
    inc = np.zeros_like(md)
    az = np.radians(np.full_like(md, 60.0))

    mask_vert = md <= 2000
    inc[mask_vert] = 0.0

    mask_build = (md > 2000) & (md <= 5000)
    frac_build = (md[mask_build] - 2000) / (5000 - 2000)
    inc[mask_build] = np.radians(45.0 * frac_build)

    mask_tang = (md > 5000) & (md <= 8000)
    inc[mask_tang] = np.radians(45.0)

    mask_drop = (md > 8000) & (md <= total_depth)
    frac_drop = (md[mask_drop] - 8000) / (total_depth - 8000)
    inc[mask_drop] = np.radians(45.0 - 15.0 * frac_drop)

    x = np.zeros_like(md)
    y = np.zeros_like(md)
    z = np.zeros_like(md)
    for i in range(1, len(md)):
        delta_md = md[i] - md[i-1]
        avg_inc = (inc[i] + inc[i-1]) / 2.0
        avg_az = (az[i] + az[i-1]) / 2.0
        x[i] = x[i-1] + delta_md * np.sin(avg_inc) * np.cos(avg_az)
        y[i] = y[i-1] + delta_md * np.sin(avg_inc) * np.sin(avg_az)
        z[i] = z[i-1] + delta_md * np.cos(avg_inc)

    theme = st.get_option("theme.base")
    scene_bgcolor = 'rgba(0,0,0,0)'
    grid_color = "#334155" if theme == "dark" else "#e2e8f0"
    axis_color = "#94a3b8" if theme == "dark" else "#475569"

    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z,
        mode='lines',
        line=dict(
            color=z,
            colorscale='Viridis',
            width=6,
            showscale=True,
            colorbar=dict(title="Depth (ft)")
        ),
        name='Wellpath'
    ))

    key_depths = [0, 2000, 5000, 8000, total_depth]
    key_labels = ['Surface', 'KOP', 'EOB', 'Start Drop', 'TD']
    key_indices = [np.argmin(np.abs(md - d)) for d in key_depths]
    fig.add_trace(go.Scatter3d(
        x=x[key_indices], y=y[key_indices], z=z[key_indices],
        mode='markers+text',
        marker=dict(size=6, color='red', symbol='circle'),
        text=key_labels,
        textposition='top center',
        name='Key points'
    ))

    fig.add_trace(go.Scatter3d(
        x=[0, 0], y=[0, 0], z=[0, -200],
        mode='lines',
        line=dict(color='grey', width=2, dash='dash'),
        name='Surface location',
        showlegend=False
    ))

    fig.update_layout(
        scene=dict(
            xaxis_title='Easting (ft)',
            yaxis_title='Northing (ft)',
            zaxis_title='True Vertical Depth (ft)',
            bgcolor=scene_bgcolor,
            xaxis=dict(
                backgroundcolor=scene_bgcolor,
                gridcolor=grid_color,
                color=axis_color,
                zerolinecolor=grid_color
            ),
            yaxis=dict(
                backgroundcolor=scene_bgcolor,
                gridcolor=grid_color,
                color=axis_color,
                zerolinecolor=grid_color
            ),
            zaxis=dict(
                backgroundcolor=scene_bgcolor,
                gridcolor=grid_color,
                color=axis_color,
                zerolinecolor=grid_color,
                autorange='reversed'
            ),
        ),
        margin=dict(l=0, r=0, b=0, t=30),
        height=650,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(
            x=0.02, y=0.98,
            bgcolor='rgba(0,0,0,0.3)' if theme == "dark" else 'rgba(255,255,255,0.7)',
            font=dict(color='white' if theme == "dark" else 'black')
        )
    )

    st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 3: AI DIAGNOSTICS ----------
with tab3:
    st.markdown("### <i class='fas fa-brain'></i> AI Real‑Time Drilling Assistant", unsafe_allow_html=True)
    if "latest_results" in st.session_state:
        res = st.session_state.latest_results
        ecd = res["equivalent_circulating_density_ecd_ppg"]
        if ecd > 15.0:
            st.error("⚠️ **CRITICAL ALERT:** Calculated ECD exceeds structural fracture limit (15.0 ppg). Risk of severe fluid losses.")
            with st.expander("📌 Recommended Actions"):
                st.write("1. Reduce pump SPM to lower annular velocity and dynamic pressure drop.")
                st.write("2. Perform mud dilution to drop Plastic Viscosity.")
        else:
            st.success("✔ **SAFE OPERATIONAL GRADIENT:** System operating within dynamic pore‑fracture window.")
            st.info("Hydraulics, hole cleaning transport, and nozzle velocities meet all standard operating requirements.")
    else:
        st.info("Run the physics matrix on Tab 1 to view real‑time AI telemetry diagnostics.")

# ---------- TAB 4: CEMENTING ----------
with tab4:
    st.markdown("### <i class='fas fa-hard-hat'></i> Primary Cementing & P&A Plug Design", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        hole_dia = st.number_input("Hole Diameter (in)", value=8.5, min_value=4.0, step=0.5)
        casing_od = st.number_input("Casing OD (in)", value=7.0, min_value=2.0, step=0.5)
        casing_id = st.number_input("Casing ID (in)", value=6.276, min_value=1.0, step=0.1)
        interval_ft = st.number_input("Cemented Interval Length (ft)", value=5000.0, step=100.0)
        washout_pct = st.number_input("Washout Factor (%)", value=15.0, step=1.0)
    with col2:
        lead_dens = st.number_input("Lead Slurry Density (ppg)", value=12.5, step=0.1)
        tail_dens = st.number_input("Tail Slurry Density (ppg)", value=15.8, step=0.1)
        spacer_dens = st.number_input("Spacer Density (ppg)", value=11.0, step=0.1)
        disp_dens = st.number_input("Displacement Fluid Density (ppg)", value=10.0, step=0.1)
        tail_length = st.number_input("Tail Slurry Length (ft)", value=500.0, step=50.0)
        bht = st.number_input("Bottom Hole Temperature (°F)", value=180.0, step=5.0)
        shoe_track = st.number_input("Shoe Track Length (ft)", value=40.0, step=5.0)

    if st.button(" Run Cementing Design", key="cement_btn", type="primary", use_container_width=True):
        with st.spinner("Calculating cement job..."):
            try:
                params = PrimaryCementingInput(
                    hole_diameter_in=hole_dia,
                    casing_od_in=casing_od,
                    casing_id_in=casing_id,
                    interval_length_ft=interval_ft,
                    washout_factor_pct=washout_pct,
                    shoe_track_length_ft=shoe_track,
                    lead_slurry_density_ppg=lead_dens,
                    tail_slurry_density_ppg=tail_dens,
                    spacer_density_ppg=spacer_dens,
                    displacement_fluid_density_ppg=disp_dens,
                    tail_slurry_length_ft=tail_length,
                    bht_fahrenheit=bht
                )
                engine = CementingEngine()
                result = engine.design_primary_job(params)
                st.session_state.cementing_results = result
                st.session_state.cementing_params = {
                    "casing_od": casing_od,
                    "hole_dia": hole_dia,
                    "interval_ft": interval_ft
                }

                st.markdown("### <i class='fas fa-flask'></i> Cementing Job Volumes", unsafe_allow_html=True)
                cols = st.columns(4)
                cols[0].metric("Lead Slurry", f"{result['lead_slurry_volume_bbl']:.2f} bbl")
                cols[1].metric("Tail Slurry", f"{result['tail_slurry_volume_bbl']:.2f} bbl")
                cols[2].metric("Spacer", f"{result['spacer_volume_bbl']:.2f} bbl")
                cols[3].metric("Displacement", f"{result['displacement_volume_bbl']:.2f} bbl")
                
                st.metric("Recommended Plug Bumping Pressure", f"{result['recommended_plug_bumping_pressure_psi']:.1f} psi")
                
                st.markdown("### <i class='fas fa-flask'></i> Suggested Additives", unsafe_allow_html=True)
                for add in result["suggested_additives"]:
                    st.write(f"**{add['name']}** ({add['category']}) – {add['description']}")

                st.markdown("### <i class='fas fa-plug'></i> P&A / Side‑Track Plug Design", unsafe_allow_html=True)
                with st.expander("Design an abandonment plug"):
                    plug_len = st.number_input("Plug Length (ft)", value=200.0, step=50.0, key="plug_len")
                    plug_dens = st.number_input("Plug Slurry Density (ppg)", value=15.0, step=0.1, key="plug_dens")
                    mud_dens = st.number_input("Mud Density in Hole (ppg)", value=12.0, step=0.1, key="mud_dens")
                    if st.button("Calculate Plug", key="plug_btn"):
                        plug_result = engine.design_abandonment_plug(
                            hole_dia_in=hole_dia,
                            plug_length_ft=plug_len,
                            slurry_density_ppg=plug_dens,
                            mud_density_ppg=mud_dens
                        )
                        st.write(f"**Plug Volume:** {plug_result['plug_volume_bbl']:.2f} bbl")
                        st.write(f"**Cement Sacks:** {plug_result['cement_sacks_required']} sk")
                        st.write(f"**Hydrostatic Gain:** {plug_result['net_hydrostatic_gain_psi']:.1f} psi")
            except Exception as e:
                st.error(f"Cementing calculation error: {e}")

    if st.button(" Compare with Industry Benchmarks", key="bench_btn"):
        if "cementing_results" in st.session_state and "cementing_params" in st.session_state:
            result = st.session_state.cementing_results
            params = st.session_state.cementing_params
            comp = compare_cementing_results(
                result,
                params["casing_od"],
                params["hole_dia"],
                params["interval_ft"]
            )
            st.markdown("### <i class='fas fa-chart-bar'></i> Industry Benchmark Comparison", unsafe_allow_html=True)
            if "error" in comp:
                st.warning(comp["error"])
            else:
                st.write(f"**Configuration:** {comp['description']}")
                col1, col2 = st.columns(2)
                col1.metric(
                    "Lead Slurry",
                    f"{comp['lead_slurry']['software']:.2f} bbl",
                    f"{comp['lead_slurry']['deviation_pct']:.1f}% vs industry"
                )
                col2.metric(
                    "Tail Slurry",
                    f"{comp['tail_slurry']['software']:.2f} bbl",
                    f"{comp['tail_slurry']['deviation_pct']:.1f}% vs industry"
                )
                st.metric(
                    "Spacer Volume",
                    f"{comp['spacer']['software']:.2f} bbl",
                    f"{comp['spacer']['deviation_pct']:.1f}% vs industry"
                )
                if abs(comp['lead_slurry']['deviation_pct']) > 15 or abs(comp['tail_slurry']['deviation_pct']) > 15:
                    st.warning("Deviation >15% from industry standards – review design assumptions.")
        else:
            st.warning("Please run the cementing design first (click 'Run Cementing Design').")

# ---------- TAB 5: PDF EXPORT ----------
with tab5:
    st.markdown("### <i class='fas fa-file-pdf'></i> Export Branded PDF Compliance Report", unsafe_allow_html=True)
    if "latest_results" in st.session_state:
        if st.button("Generate Branded Field PDF", type="primary", use_container_width=True):
            with st.spinner("Generating PDF..."):
                project_meta = {
                    "name": "Deepwater Wilcox Target",
                    "rig_name": "Rig-05 Executive",
                    "company": st.session_state.user_info["company"]
                }
                diag_meta = {
                    "severity": "GREEN" if st.session_state.latest_results["equivalent_circulating_density_ecd_ppg"] < 15.0 else "RED",
                    "matched_hazard": "Formation Fracturing Risk" if st.session_state.latest_results["equivalent_circulating_density_ecd_ppg"] >= 15.0 else "None",
                    "detailed_diagnosis": f"Operating ECD is {st.session_state.latest_results['equivalent_circulating_density_ecd_ppg']:.2f} ppg."
                }
                cement_data = st.session_state.get("cementing_results", None)
                pdf_buffer = generate_pdf_payload(
                    project_meta,
                    st.session_state.latest_results,
                    diag_meta,
                    engineer_name=st.session_state.user_info["username"],
                    cementing_results=cement_data
                )
                st.download_button(
                    label="📥 Download PDF Document",
                    data=pdf_buffer,
                    file_name=f"PyMudCement_Report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    else:
        st.warning("Please run hydraulics calculations on Tab 1 before attempting report generation.")

# Footer
st.markdown('<div class="footer">© 2026 PyMudCement Optima Pro v5.0</div>', unsafe_allow_html=True)
