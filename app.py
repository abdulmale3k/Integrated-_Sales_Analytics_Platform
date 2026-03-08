"""
SME Sales Analytics Platform
=============================
Main entry point - handles data upload and configuration.
Navigate using the sidebar to access different analytics modules.
"""

import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SME Analytics Platform",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- RESPONSIVE CSS ---
st.markdown("""
<style>
    /* Responsive container */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 100%;
    }
    
    [data-testid="stMetric"] {
        background-color: #262730; 
        border-radius: 10px;
        padding: 10px 15px;
        overflow: hidden;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    
    /* Better tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 5px;
        flex-wrap: wrap;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 0.9rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* Responsive columns */
    [data-testid="column"] {
        min-width: 120px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card styling */
    .nav-card {
        border-radius: 12px;
        padding: 1rem;
        color: white;
        margin-bottom: 0.8rem;
        min-height: 80px;
    }
    
    .nav-card h4 {
        margin: 0 0 5px 0;
        font-size: 1rem;
    }
    
    .nav-card p {
        margin: 0;
        font-size: 0.85rem;
        opacity: 0.9;
    }
    
    /* Upload area styling */
    [data-testid="stFileUploader"] {
        border: 2px dashed #667eea;
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Responsive adjustments for smaller screens */
    @media (max-width: 768px) {
        [data-testid="stMetricValue"] {
            font-size: 1rem !important;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.7rem !important;
        }
        .nav-card {
            min-height: 60px;
            padding: 0.8rem;
        }
        .nav-card h4 {
            font-size: 0.9rem;
        }
        .nav-card p {
            font-size: 0.75rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS ---
REQUIRED_COLUMNS = ["order_date", "product_name", "quantity", "unit_price"]
OPTIONAL_COLUMNS = ["transaction_id", "customer_id"]

COLUMN_ALIASES = {
    "order_date": [
        "InvoiceDate", "invoice_date", "date", "Order Date", "order_date",
        "Date", "TransactionDate", "transaction_date", "sale_date", "SaleDate"
    ],
    "product_name": [
        "Description", "description", "Product Name", "product_name",
        "Item", "item", "ProductName", "product", "Product", "ItemName"
    ],
    "quantity": [
        "Quantity", "quantity", "qty", "Qty", "Count", "count",
        "Units", "units", "Amount"
    ],
    "unit_price": [
        "UnitPrice", "unit_price", "Price", "price", "Cost", "cost",
        "Unit Price", "ItemPrice", "item_price", "SalePrice"
    ],
    "transaction_id": [
        "InvoiceNo", "invoice_no", "Invoice", "invoice", "OrderID", "order_id",
        "TransactionID", "transaction_id", "Order ID", "Transaction ID",
        "InvoiceNumber", "invoice_number", "OrderNumber"
    ],
    "customer_id": [
        "CustomerID", "customer_id", "Customer ID", "Customer", "customer",
        "ClientID", "client_id", "Client ID", "BuyerID"
    ]
}


# --- HELPER FUNCTIONS ---

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        'data': None,
        'raw_df': None,
        'last_file': None,
        'final_mapping': {},
        'basket_rules': None,
        'model_results': None,
        'data_loaded': False,
        'pdf_buffer': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_data(show_spinner=False)
def load_data(file):
    """Load CSV or Excel file with encoding fallbacks."""
    try:
        if file.name.endswith('.csv'):
            encodings = ['utf-8', 'ISO-8859-1', 'cp1252', 'latin1']
            for encoding in encodings:
                try:
                    file.seek(0)
                    return pd.read_csv(file, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode CSV")
        elif file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file)
        return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def auto_detect_columns(columns):
    """Auto-detect column mappings based on aliases."""
    mapping = {}
    missing = []
    found_optional = []
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
    """Clean and process the raw dataframe."""
    try:
        # Rename columns
        rename_map = {v: k for k, v in mapping.items()}
        df = df_raw.rename(columns=rename_map)
        
        # Keep mapped columns
        cols_to_keep = [k for k in mapping.keys() if k in df.columns]
        df = df[cols_to_keep].copy()
        
        # Convert types
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
        df['total_value'] = df['quantity'] * df['unit_price']
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        
        # Clean invalid data
        df = df[df['quantity'] > 0]
        df = df[df['unit_price'] > 0]
        df = df.dropna(subset=['order_date', 'quantity', 'unit_price'])
        
        return df
    
    except Exception as e:
        st.error(f"Processing error: {e}")
        return None


# --- MAIN APPLICATION ---

def main():
    init_session_state()
    
    # === SIDEBAR ===
    with st.sidebar:
        st.markdown("# 📈 SME Analytics")
        st.markdown("---")
        
        # Data status indicator
        if st.session_state['data'] is not None:
            st.success("✅ Data Loaded")
            df = st.session_state['data']
            st.caption(f"📊 {len(df):,} records")
            st.caption(f"📅 {df['order_date'].min().strftime('%Y-%m-%d')}")
            st.caption(f"→ {df['order_date'].max().strftime('%Y-%m-%d')}")
            
            st.markdown("---")
            
            if st.button("🗑️ Clear Data", use_container_width=True):
                for key in ['data', 'raw_df', 'basket_rules', 'model_results', 'pdf_buffer']:
                    st.session_state[key] = None
                st.session_state['data_loaded'] = False
                st.rerun()
        else:
            st.info("📁 No data loaded")
        
        st.markdown("---")
        st.markdown("### 🧭 Navigation")
        st.markdown("""
        Use the pages above to:
        1. 📊 **Dashboard** - Overview
        2. 📦 **Products** - Analysis
        3. 🛒 **Basket** - Associations
        4. 🤖 **Forecast** - AI
        5. 📄 **Reports** - PDFs
        """)
        
        st.markdown("---")
        st.caption("v2.0 | SME Analytics")
    
    # === MAIN CONTENT ===
    if st.session_state['data'] is None:
        show_upload_interface()
    else:
        show_data_ready_interface()


def show_upload_interface():
    """Display the data upload and mapping interface."""
    
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 1.5rem 0;">
        <h1>📈 SME Analytics Platform</h1>
        <p style="color: #666; font-size: 1rem;">
            Upload your sales data to get started with powerful analytics
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Upload section
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📁 Upload Your Data")
        
        uploaded_file = st.file_uploader(
            "Drag and drop or click to upload",
            type=['csv', 'xlsx', 'xls'],
            help="Supported formats: CSV, Excel (.xlsx, .xls)",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            process_uploaded_file(uploaded_file)
    
    with col2:
        st.markdown("### 📋 Expected Format")
        
        st.markdown("""
        **Required columns:**
        - 📅 Order Date
        - 📦 Product Name  
        - 🔢 Quantity
        - 💰 Unit Price
        
        **Optional columns:**
        - 🧾 Transaction ID
        - 👤 Customer ID
        """)
        
        # Sample data download
        sample_data = pd.DataFrame({
            'InvoiceDate': ['2024-01-01', '2024-01-01', '2024-01-02'],
            'Description': ['Product A', 'Product B', 'Product A'],
            'Quantity': [5, 3, 2],
            'UnitPrice': [10.99, 25.50, 10.99],
            'InvoiceNo': ['INV001', 'INV001', 'INV002']
        })
        
        st.download_button(
            "📥 Download Sample CSV",
            sample_data.to_csv(index=False),
            "sample_data.csv",
            "text/csv",
            use_container_width=True
        )


def process_uploaded_file(uploaded_file):
    """Process the uploaded file and handle column mapping."""
    
    # Load data
    if st.session_state.get('last_file') != uploaded_file.name:
        with st.spinner('Reading file...'):
            df_raw = load_data(uploaded_file)
            if df_raw is not None:
                st.session_state['raw_df'] = df_raw
                st.session_state['last_file'] = uploaded_file.name
    
    df_raw = st.session_state.get('raw_df')
    
    if df_raw is None:
        st.error("Failed to load file")
        return
    
    st.success(f"✅ Loaded {len(df_raw):,} rows × {len(df_raw.columns)} columns")
    
    # Preview
    with st.expander("👀 Preview Raw Data", expanded=False):
        st.dataframe(df_raw.head(10), use_container_width=True)
    
    st.markdown("---")
    
    # Auto-detect columns
    detected_map, missing_cols, found_optional = auto_detect_columns(df_raw.columns)
    
    # Mapping interface
    st.markdown("### 🔗 Column Mapping")
    
    if len(missing_cols) == 0:
        st.success("🎉 All required columns auto-detected!")
        
        # Show mapping
        mapping_data = [{"System Field": k, "Your Column": v} for k, v in detected_map.items()]
        st.dataframe(pd.DataFrame(mapping_data), use_container_width=True, hide_index=True)
        
        final_mapping = detected_map
    else:
        st.warning(f"⚠️ Please map these columns: **{', '.join(missing_cols)}**")
        
        final_mapping = {}
        cols = st.columns(2)
        
        for i, target in enumerate(REQUIRED_COLUMNS + OPTIONAL_COLUMNS):
            is_required = target in REQUIRED_COLUMNS
            options = ["-- Select --"] + list(df_raw.columns)
            default_idx = 0
            
            if target in detected_map:
                default_idx = options.index(detected_map[target])
            
            label = f"{'🔴' if is_required else '🟢'} {target.replace('_', ' ').title()}"
            
            with cols[i % 2]:
                selection = st.selectbox(
                    label,
                    options,
                    index=default_idx,
                    key=f"map_{target}"
                )
                if selection != "-- Select --":
                    final_mapping[target] = selection
    
    # Validate and process
    all_required = all(col in final_mapping for col in REQUIRED_COLUMNS)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if all_required:
            if st.button("🚀 Process & Continue", type="primary", use_container_width=True):
                with st.spinner("Processing data..."):
                    df_clean = process_data(df_raw, final_mapping)
                    
                    if df_clean is not None and len(df_clean) > 0:
                        st.session_state['data'] = df_clean
                        st.session_state['final_mapping'] = final_mapping
                        st.session_state['data_loaded'] = True
                        st.success(f"✅ Processed {len(df_clean):,} valid transactions!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("No valid data after processing. Check your column mappings.")
        else:
            st.button("🚀 Process & Continue", type="primary", use_container_width=True, disabled=True)
            st.caption("Please map all required columns (marked with 🔴)")


def show_data_ready_interface():
    """Show interface when data is loaded - prompt user to navigate."""
    
    df = st.session_state['data']
    
    # Calculate metrics
    total_revenue = df['total_value'].sum()
    total_orders = len(df)
    unique_products = df['product_name'].nunique()
    date_range = (df['order_date'].max() - df['order_date'].min()).days
    avg_order = total_revenue / total_orders if total_orders > 0 else 0
    
    # Header
    st.markdown("## 📊 Data Summary")
    
    # === METRICS IN 2 ROWS OF 2 COLUMNS ===
    
    # Row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="💰 Total Revenue",
            value=f"£{total_revenue:,.0f}"
        )
    
    with col2:
        st.metric(
            label="🧾 Transactions",
            value=f"{total_orders:,}"
        )
    
    # Row 2
    col3, col4 = st.columns(2)
    
    with col3:
        st.metric(
            label="📦 Unique Products",
            value=f"{unique_products:,}"
        )
    
    with col4:
        st.metric(
            label="📅 Days Covered",
            value=f"{date_range:,}"
        )
    
    st.markdown("---")
    
    # === NAVIGATION CARDS ===
    st.markdown("## 🧭 Choose Your Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="nav-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <h4>📊 Dashboard</h4>
            <p>KPIs, trends & revenue analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="nav-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <h4>🛒 Basket Analysis</h4>
            <p>Product associations & bundling</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="nav-card" style="background: linear-gradient(135deg, #654ea3 0%, #eaafc8 100%);">
            <h4>📄 Reports</h4>
            <p>Generate PDF reports</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="nav-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <h4>📦 Products</h4>
            <p>Product performance analysis</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="nav-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);">
            <h4>🤖 AI Forecast</h4>
            <p>ML-powered predictions</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation hint
    st.info("👈 **Use the sidebar** to navigate to different analysis pages")
    
    # Quick data preview
    with st.expander("👀 Preview Loaded Data"):
        st.dataframe(df.head(20), use_container_width=True)


# --- RUN APPLICATION ---
if __name__ == "__main__":
    main()