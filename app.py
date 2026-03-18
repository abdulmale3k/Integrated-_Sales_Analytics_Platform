"""
SME Sales Analytics Platform - ULTIMATE EDITION
================================================
A stunning, modern analytics dashboard with full navigation
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from sidebar import create_sidebar  # <-- Importing your new custom sidebar

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SME Analytics Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ULTIMATE CSS ---
st.markdown("""
<style>
    /* ===== GOOGLE FONTS ===== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
    
    /* ===== CSS VARIABLES ===== */
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-tertiary: #1a1a25;
        --bg-card: rgba(255, 255, 255, 0.03);
        --bg-card-hover: rgba(255, 255, 255, 0.06);
        --text-primary: #ffffff;
        --text-secondary: #8b8b9e;
        --text-muted: #5a5a6e;
        --accent-purple: #8b5cf6;
        --accent-blue: #3b82f6;
        --accent-cyan: #06b6d4;
        --accent-green: #10b981;
        --accent-orange: #f59e0b;
        --accent-pink: #ec4899;
        --accent-red: #ef4444;
        --gradient-purple: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
        --gradient-blue: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
        --gradient-green: linear-gradient(135deg, #10b981 0%, #06b6d4 100%);
        --gradient-orange: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
        --gradient-pink: linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%);
        --gradient-mesh: 
            radial-gradient(at 40% 20%, rgba(139, 92, 246, 0.15) 0px, transparent 50%),
            radial-gradient(at 80% 0%, rgba(6, 182, 212, 0.1) 0px, transparent 50%),
            radial-gradient(at 0% 50%, rgba(236, 72, 153, 0.1) 0px, transparent 50%),
            radial-gradient(at 80% 50%, rgba(59, 130, 246, 0.1) 0px, transparent 50%),
            radial-gradient(at 0% 100%, rgba(16, 185, 129, 0.1) 0px, transparent 50%);
        --shadow-glow-purple: 0 0 30px rgba(139, 92, 246, 0.4);
        --shadow-glow-blue: 0 0 30px rgba(59, 130, 246, 0.4);
        --border-radius-sm: 8px;
        --border-radius: 16px;
        --border-radius-lg: 24px;
        --transition-fast: 0.15s ease;
        --transition-normal: 0.3s ease;
    }
    
    /* ===== ANIMATED BACKGROUND ===== */
    .stApp {
        background: var(--bg-primary);
        background-image: var(--gradient-mesh);
        background-attachment: fixed;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: 
            radial-gradient(circle at 20% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 40%),
            radial-gradient(circle at 80% 20%, rgba(6, 182, 212, 0.08) 0%, transparent 40%);
        animation: float 20s ease-in-out infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes float {
        0%, 100% { transform: translate(0, 0) rotate(0deg); }
        50% { transform: translate(-1%, 2%) rotate(-3deg); }
    }
    
    /* Hide Streamlit (Added stSidebarNav to hide default menu) */
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stSidebarNav"] { display: none !important; }
    
    /* ===== MAIN CONTAINER ===== */
    .block-container {
        padding: 2rem 3rem 4rem 3rem !important;
        max-width: 100% !important;
        position: relative;
        z-index: 1;
    }
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    [data-testid="stSidebar"]::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--gradient-purple);
    }
    
    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }
    
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span {
        color: var(--text-secondary) !important;
    }
    
    /* ===== TYPOGRAPHY ===== */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }
    
    h1 {
        font-size: 2.75rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 3s ease-in-out infinite;
        background-size: 200% 100%;
    }
    
    @keyframes shimmer {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    p, span, label, li {
        color: var(--text-secondary) !important;
    }
    
    /* ===== METRIC CARDS ===== */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .metric-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        position: relative;
        overflow: hidden;
        transition: var(--transition-normal);
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: var(--gradient-purple);
    }
    
    .metric-card::after {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%);
        transform: translate(30%, -30%);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(139, 92, 246, 0.4);
        box-shadow: var(--shadow-glow-purple);
    }
    
    .metric-card.blue::before { background: var(--gradient-blue); }
    .metric-card.green::before { background: var(--gradient-green); }
    .metric-card.orange::before { background: var(--gradient-orange); }
    
    .metric-icon {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        margin-bottom: 1rem;
        background: rgba(139, 92, 246, 0.15);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: var(--text-primary);
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 500;
    }
    
    .metric-change {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: 999px;
        margin-top: 0.5rem;
    }
    
    .metric-change.positive {
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
    }
    
    .metric-change.negative {
        background: rgba(239, 68, 68, 0.15);
        color: var(--accent-red);
    }
    
    /* ===== STATUS BADGE ===== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: rgba(16, 185, 129, 0.15);
        color: var(--accent-green);
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    
    .status-badge::before {
        content: '';
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--accent-green);
        animation: pulse-dot 2s infinite;
    }
    
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(1.2); }
    }
    
    /* ===== GLASS CARD ===== */
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        transition: var(--transition-normal);
    }
    
    .glass-card:hover {
        background: var(--bg-card-hover);
        border-color: rgba(139, 92, 246, 0.3);
    }
    
    /* ===== STREAMLIT OVERRIDES ===== */
    
    [data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: var(--border-radius) !important;
        padding: 1.25rem !important;
    }
    
    [data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }
    [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-family: 'JetBrains Mono', monospace !important; }
    
    .stButton > button {
        background: var(--gradient-purple) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--border-radius-sm) !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: var(--transition-normal) !important;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(139, 92, 246, 0.5) !important;
    }
    
    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 2px dashed rgba(139, 92, 246, 0.3) !important;
        border-radius: var(--border-radius) !important;
        padding: 2rem !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--accent-purple) !important;
        background: var(--bg-card-hover) !important;
    }
    
    .stSelectbox > div > div {
        background: var(--bg-card) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: var(--border-radius-sm) !important;
    }
    
    [data-testid="stDataFrame"] {
        background: var(--bg-card) !important;
        border-radius: var(--border-radius) !important;
    }
    
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border-radius: var(--border-radius-sm) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: var(--border-radius) !important;
        padding: 0.5rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        border-radius: var(--border-radius-sm) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-purple) !important;
        color: white !important;
    }
    
    .stAlert { background: var(--bg-card) !important; border-radius: var(--border-radius-sm) !important; }
    .stSuccess { border-left: 3px solid var(--accent-green) !important; }
    .stWarning { border-left: 3px solid var(--accent-orange) !important; }
    .stError { border-left: 3px solid var(--accent-red) !important; }
    .stInfo { border-left: 3px solid var(--accent-blue) !important; }
    
    hr { border-color: rgba(255, 255, 255, 0.05) !important; }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: var(--bg-secondary); }
    ::-webkit-scrollbar-thumb { background: var(--gradient-purple); border-radius: 4px; }
    
    /* ===== ANIMATIONS ===== */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in-up { animation: fadeInUp 0.5s ease-out forwards; }
    .delay-1 { animation-delay: 0.1s; opacity: 0; }
    .delay-2 { animation-delay: 0.2s; opacity: 0; }
    .delay-3 { animation-delay: 0.3s; opacity: 0; }
    .delay-4 { animation-delay: 0.4s; opacity: 0; }
    .delay-5 { animation-delay: 0.5s; opacity: 0; }
    
    /* ===== RESPONSIVE ===== */
    @media (max-width: 768px) {
        .block-container { padding: 1rem !important; }
        h1 { font-size: 2rem !important; }
        .metric-grid { grid-template-columns: 1fr 1fr; }
    }
</style>
""", unsafe_allow_html=True)


# --- CONSTANTS ---
REQUIRED_COLUMNS = ["order_date", "product_name", "quantity", "unit_price"]
OPTIONAL_COLUMNS = ["transaction_id", "customer_id"]

COLUMN_ALIASES = {
    "order_date": ["InvoiceDate", "invoice_date", "date", "Order Date", "order_date", "Date", "TransactionDate"],
    "product_name": ["Description", "description", "Product Name", "product_name", "Item", "ProductName"],
    "quantity": ["Quantity", "quantity", "qty", "Qty", "Count", "Units"],
    "unit_price": ["UnitPrice", "unit_price", "Price", "price", "Cost", "Unit Price"],
    "transaction_id": ["InvoiceNo", "invoice_no", "Invoice", "OrderID", "TransactionID", "Order ID"],
    "customer_id": ["CustomerID", "customer_id", "Customer ID", "Customer", "ClientID"]
}


# --- HELPER FUNCTIONS ---

def init_session_state():
    defaults = {
        'data': None, 'raw_df': None, 'last_file': None,
        'final_mapping': {}, 'basket_rules': None,
        'model_results': None, 'pdf_buffer': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(show_spinner=False)
def load_data(file):
    try:
        if file.name.endswith('.csv'):
            for enc in ['utf-8', 'ISO-8859-1', 'cp1252']:
                try:
                    file.seek(0)
                    return pd.read_csv(file, encoding=enc)
                except:
                    continue
        elif file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file)
    except Exception as e:
        st.error(f"Error: {e}")
    return None


def auto_detect_columns(columns):
    mapping, missing, found_optional = {}, [], []
    lower_cols = {c.lower().strip(): c for c in columns}
    
    for target in REQUIRED_COLUMNS:
        found = False
        for alias in COLUMN_ALIASES.get(target, []):
            if alias.lower() in lower_cols:
                mapping[target] = lower_cols[alias.lower()]
                found = True
                break
        if not found:
            missing.append(target)
    
    for target in OPTIONAL_COLUMNS:
        for alias in COLUMN_ALIASES.get(target, []):
            if alias.lower() in lower_cols:
                mapping[target] = lower_cols[alias.lower()]
                found_optional.append(target)
                break
    
    return mapping, missing, found_optional


def process_data(df_raw, mapping):
    try:
        df = df_raw.rename(columns={v: k for k, v in mapping.items()})
        df = df[[k for k in mapping.keys() if k in df.columns]].copy()
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
        df['total_value'] = df['quantity'] * df['unit_price']
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        df = df[(df['quantity'] > 0) & (df['unit_price'] > 0)].dropna(subset=['order_date'])
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def get_greeting():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning", "☀️"
    elif hour < 18:
        return "Good afternoon", "🌤️"
    else:
        return "Good evening", "🌙"


def render_metric_card(icon, value, label, change=None, color=""):
    change_html = ""
    if change is not None:
        cls = "positive" if change >= 0 else "negative"
        arrow = "↑" if change >= 0 else "↓"
        change_html = f'<div class="metric-change {cls}">{arrow} {abs(change):.1f}%</div>'
    
    return f"""
    <div class="metric-card {color} fade-in-up">
        <div class="metric-icon">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {change_html}
    </div>
    """


# --- MAIN APPLICATION ---

def main():
    init_session_state()
    
    # === SIDEBAR ===
    create_sidebar()
    
    # === MAIN CONTENT ===
    if st.session_state['data'] is None:
        show_upload_interface()
    else:
        show_data_ready_interface()


def show_upload_interface():
    greeting, emoji = get_greeting()
    
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0;" class="fade-in-up">
        <div style="font-size: 1rem; color: var(--text-secondary); margin-bottom: 0.5rem;">{emoji} {greeting}</div>
        <h1>SME Analytics Platform</h1>
        <p style="font-size: 1.1rem; color: var(--text-secondary); max-width: 600px; margin: 0 auto;">
            Transform your sales data into actionable insights with AI-powered analytics
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        <div class="glass-card fade-in-up delay-1">
            <h3 style="margin: 0 0 0.5rem 0;">📁 Upload Your Data</h3>
            <p style="margin: 0;">Drag and drop your CSV or Excel file to begin</p>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader("Upload", type=['csv', 'xlsx', 'xls'], label_visibility="collapsed")
        
        if uploaded_file:
            process_uploaded_file(uploaded_file)
    
    with col2:
        st.markdown("""
        <div class="glass-card fade-in-up delay-2">
            <h3 style="margin: 0 0 1rem 0;">📋 Required Columns</h3>
            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span>📅</span><span style="color: var(--text-secondary);">Order Date</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span>📦</span><span style="color: var(--text-secondary);">Product Name</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span>🔢</span><span style="color: var(--text-secondary);">Quantity</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span>💰</span><span style="color: var(--text-secondary);">Unit Price</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        sample = pd.DataFrame({
            'InvoiceDate': ['2024-01-01'], 'Description': ['Product A'],
            'Quantity': [5], 'UnitPrice': [10.99], 'InvoiceNo': ['INV001']
        })
        st.download_button("📥 Sample CSV", sample.to_csv(index=False), "sample.csv", use_container_width=True)


def process_uploaded_file(uploaded_file):
    if st.session_state.get('last_file') != uploaded_file.name:
        with st.spinner('Loading...'):
            df_raw = load_data(uploaded_file)
            if df_raw is not None:
                st.session_state['raw_df'] = df_raw
                st.session_state['last_file'] = uploaded_file.name
    
    df_raw = st.session_state.get('raw_df')
    if df_raw is None:
        st.error("Failed to load file")
        return
    
    st.success(f"✅ Loaded **{len(df_raw):,}** rows × **{len(df_raw.columns)}** columns")
    
    with st.expander("👀 Preview"):
        st.dataframe(df_raw.head(10), use_container_width=True)
    
    st.markdown("---")
    
    detected, missing, _ = auto_detect_columns(df_raw.columns)
    
    st.markdown("### 🔗 Column Mapping")
    
    if not missing:
        st.success("🎉 All columns auto-detected!")
        final_mapping = detected
    else:
        st.warning(f"⚠️ Please map: **{', '.join(missing)}**")
        final_mapping = {}
        cols = st.columns(2)
        for i, target in enumerate(REQUIRED_COLUMNS + OPTIONAL_COLUMNS):
            options = ["-- Select --"] + list(df_raw.columns)
            default = options.index(detected[target]) if target in detected else 0
            with cols[i % 2]:
                sel = st.selectbox(f"{'🔴' if target in REQUIRED_COLUMNS else '🟢'} {target.replace('_', ' ').title()}", options, index=default, key=f"map_{target}")
                if sel != "-- Select --":
                    final_mapping[target] = sel
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if all(c in final_mapping for c in REQUIRED_COLUMNS):
            if st.button("🚀 Launch Dashboard", type="primary", use_container_width=True):
                with st.spinner("Processing..."):
                    df = process_data(df_raw, final_mapping)
                    if df is not None and len(df) > 0:
                        st.session_state['data'] = df
                        st.session_state['final_mapping'] = final_mapping
                        st.balloons()
                        st.rerun()
        else:
            st.button("🚀 Launch Dashboard", disabled=True, use_container_width=True)


def show_data_ready_interface():
    df = st.session_state['data']
    greeting, emoji = get_greeting()
    
    total_revenue = df['total_value'].sum()
    total_orders = len(df)
    unique_products = df['product_name'].nunique()
    avg_order = total_revenue / total_orders
    
    st.markdown(f"""
    <div class="fade-in-up" style="margin-bottom: 1.5rem;">
        <div style="font-size: 0.9rem; color: var(--text-secondary);">{emoji} {greeting}</div>
        <h1 style="margin: 0;">Analytics Dashboard</h1>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics
    st.markdown(f"""
    <div class="metric-grid">
        {render_metric_card("💰", f"£{total_revenue:,.0f}", "Total Revenue", 12.5, "")}
        {render_metric_card("🧾", f"{total_orders:,}", "Transactions", 8.3, "blue")}
        {render_metric_card("📦", f"{unique_products:,}", "Products", -2.1, "green")}
        {render_metric_card("💵", f"£{avg_order:.2f}", "Avg Order", 5.7, "orange")}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation Section
    st.markdown("""
    <h2 style="text-align: center; margin-bottom: 0.5rem;">🧭 Explore Analytics</h2>
    <p style="text-align: center; color: var(--text-secondary); margin-bottom: 1.5rem;">Choose a module to dive deeper</p>
    """, unsafe_allow_html=True)
    
    # Navigation Cards with ACTUAL BUTTONS
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="glass-card fade-in-up delay-1" style="text-align: center; padding: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">📊</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Dashboard</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">KPIs, trends & insights</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Dashboard →", key="btn_dash", use_container_width=True):
            st.switch_page("pages/Dashboard.py")
    
    with col2:
        st.markdown("""
        <div class="glass-card fade-in-up delay-2" style="text-align: center; padding: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">📦</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Products</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">Performance & rankings</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Products →", key="btn_prod", use_container_width=True):
            st.switch_page("pages/Products.py")
    
    with col3:
        st.markdown("""
        <div class="glass-card fade-in-up delay-3" style="text-align: center; padding: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">🛒</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Basket Analysis</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">Product associations</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Basket →", key="btn_basket", use_container_width=True):
            st.switch_page("pages/Basket_Analysis.py")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col4, col5 = st.columns(2)
    
    with col4:
        st.markdown("""
        <div class="glass-card fade-in-up delay-4" style="text-align: center; padding: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">🤖</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">AI Forecast</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">ML-powered predictions</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open AI Forecast →", key="btn_ai", use_container_width=True):
            st.switch_page("pages/AI_Forecasting.py")
    
    with col5:
        st.markdown("""
        <div class="glass-card fade-in-up delay-5" style="text-align: center; padding: 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 1rem;">📄</div>
            <div style="font-size: 1.1rem; font-weight: 600; color: white; margin-bottom: 0.5rem;">Reports</div>
            <div style="font-size: 0.8rem; color: var(--text-secondary);">Generate PDF reports</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Open Reports →", key="btn_reports", use_container_width=True):
            st.switch_page("pages/Reports.py")
    
    st.markdown("---")
    
    with st.expander("👀 Data Preview"):
        st.dataframe(df.head(20), use_container_width=True)


if __name__ == "__main__":
    main()