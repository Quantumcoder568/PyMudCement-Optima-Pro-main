st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');

    * {
        font-family: 'Inter', sans-serif;
        transition: background-color 0.25s ease, color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }

    /* ---------- LIGHT THEME (body.light) ---------- */
    body.light .stApp {
        background: #f0f7ff !important;
        border: 4px solid #2563eb !important; /* test border – remove later */
    }
    body.light .main-header {
        color: #1e3a8a !important;
        font-weight: 800;
        text-shadow: 0 2px 12px rgba(30, 58, 138, 0.15);
    }
    body.light .sub-header {
        color: #1e293b !important;
        border-bottom: 4px solid #facc15 !important;
    }
    body.light .card {
        background: #ffffff;
        border: 1px solid #dbeafe;
        box-shadow: 0 4px 16px rgba(30, 58, 138, 0.08);
        border-radius: 16px;
    }
    body.light .metric-card {
        background: #ffffff;
        border-left: 6px solid #2563eb !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.15);
        border-radius: 12px;
    }
    body.light .metric-card .value {
        color: #1e3a8a !important;
    }
    body.light .stButton > button {
        background: linear-gradient(135deg, #2563eb, #1e3a8a) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
        transition: all 0.2s;
    }
    body.light .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 28px rgba(37, 99, 235, 0.5) !important;
    }
    body.light .stSidebar {
        background: #ffffff;
        border-right: 2px solid #dbeafe;
    }
    body.light .sidebar-heading {
        color: #2563eb !important;
        font-weight: 700;
    }
    body.light .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #facc15 !important;
        color: #1e3a8a !important;
        font-weight: 700 !important;
        border-radius: 8px 8px 0 0 !important;
        border-bottom: 3px solid #1e3a8a !important;
        box-shadow: 0 -2px 8px rgba(250, 204, 21, 0.3);
    }
    body.light .stTabs [data-baseweb="tab"]:hover {
        background: #fef3c7 !important;
    }
    body.light .stAlert {
        border-left: 5px solid !important;
    }
    body.light .stAlert.error {
        border-left-color: #dc2626 !important;
    }
    body.light .stAlert.warning {
        border-left-color: #facc15 !important;
    }
    body.light .stAlert.success {
        border-left-color: #22c55e !important;
    }
    body.light .stAlert.info {
        border-left-color: #2563eb !important;
    }

    /* ---------- DARK THEME (body.dark) ---------- */
    body.dark .stApp {
        background: #0b1a2e !important;
        border: 4px solid #facc15 !important; /* test border – remove later */
    }
    body.dark .main-header {
        color: #facc15 !important;
        font-weight: 800;
        text-shadow: 0 2px 24px rgba(250, 204, 21, 0.25);
    }
    body.dark .sub-header {
        color: #cbd5e1 !important;
        border-bottom: 4px solid #facc15 !important;
    }
    body.dark .card {
        background: #152238;
        border: 1px solid #1e3a5f;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
        border-radius: 16px;
    }
    body.dark .metric-card {
        background: #152238;
        border-left: 6px solid #facc15 !important;
        box-shadow: 0 6px 20px rgba(250, 204, 21, 0.15);
        border-radius: 12px;
    }
    body.dark .metric-card .value {
        color: #facc15 !important;
    }
    body.dark .stButton > button {
        background: linear-gradient(135deg, #facc15, #eab308) !important;
        color: #0b1a2e !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 16px rgba(250, 204, 21, 0.35) !important;
        transition: all 0.2s;
    }
    body.dark .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 32px rgba(250, 204, 21, 0.55) !important;
    }
    body.dark .stSidebar {
        background: #0f1e30;
        border-right: 2px solid #1e3a5f;
    }
    body.dark .sidebar-heading {
        color: #facc15 !important;
        font-weight: 700;
    }
    body.dark .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: #facc15 !important;
        color: #0b1a2e !important;
        font-weight: 700 !important;
        border-radius: 8px 8px 0 0 !important;
        border-bottom: 3px solid #facc15 !important;
        box-shadow: 0 -2px 8px rgba(250, 204, 21, 0.3);
    }
    body.dark .stTabs [data-baseweb="tab"]:hover {
        background: #1e3a5f !important;
    }
    body.dark .stAlert {
        border-left: 5px solid !important;
    }
    body.dark .stAlert.error {
        border-left-color: #dc2626 !important;
    }
    body.dark .stAlert.warning {
        border-left-color: #facc15 !important;
    }
    body.dark .stAlert.success {
        border-left-color: #22c55e !important;
    }
    body.dark .stAlert.info {
        border-left-color: #2563eb !important;
    }

    /* ---------- COMMON ELEMENTS ---------- */
    .main-header {
        font-size: 2.6rem;
        letter-spacing: -0.02em;
        padding: 0.2rem 0;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 1rem;
        font-weight: 500;
        padding-bottom: 0.8rem;
        margin-bottom: 1rem;
        border-bottom-width: 4px;
        border-bottom-style: solid;
    }
    .sidebar-heading {
        font-size: 1.05rem;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.01em;
    }
    .card {
        padding: 1.2rem 1.4rem;
        transition: all 0.25s ease;
        margin-bottom: 1rem;
    }
    .card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    }
    body.dark .card:hover {
        box-shadow: 0 8px 32px rgba(250, 204, 21, 0.08);
    }
    .metric-card {
        padding: 1rem 1.2rem;
        transition: all 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 60px;
        height: 60px;
        background: radial-gradient(circle, rgba(250,204,21,0.1) 0%, transparent 70%);
        border-radius: 50%;
        pointer-events: none;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 28px rgba(0,0,0,0.1);
    }
    body.dark .metric-card:hover {
        box-shadow: 0 8px 28px rgba(250, 204, 21, 0.12);
    }
    .metric-card .label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        display: flex;
        align-items: center;
        gap: 6px;
        color: #475569;
    }
    body.dark .metric-card .label {
        color: #94a3b8;
    }
    .metric-card .value {
        font-size: 2rem;
        font-weight: 800;
        margin-top: 0.2rem;
    }
    .stButton > button {
        font-weight: 600 !important;
        transition: all 0.2s;
        border-radius: 10px !important;
        padding: 0.5rem 1.4rem !important;
        letter-spacing: 0.02em;
    }
    .stButton > button:active {
        transform: scale(0.96);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.3rem;
        border-bottom: 2px solid #dbeafe;
        padding-bottom: 0.3rem;
    }
    body.dark .stTabs [data-baseweb="tab-list"] {
        border-bottom-color: #1e3a5f;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px 8px 0 0 !important;
        transition: all 0.15s;
    }
    .stAlert {
        border-radius: 12px !important;
    }
    .footer {
        font-size: 0.75rem;
        text-align: center;
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 2px solid #dbeafe;
        color: #64748b;
    }
    body.dark .footer {
        border-top-color: #1e3a5f;
        color: #94a3b8;
    }

    /* Override Streamlit's default metric styles */
    [data-testid="metric-container"] {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
    }
    [data-testid="metric-container"] .stMetric {
        background: transparent !important;
    }
    [data-testid="metric-container"] .stMetric > div:first-child {
        color: #475569 !important;
    }
    body.dark [data-testid="metric-container"] .stMetric > div:first-child {
        color: #94a3b8 !important;
    }
    [data-testid="metric-container"] .stMetric > div:last-child {
        color: #1e3a8a !important;
        font-weight: 700 !important;
    }
    body.dark [data-testid="metric-container"] .stMetric > div:last-child {
        color: #facc15 !important;
    }
</style>
""", unsafe_allow_html=True)
