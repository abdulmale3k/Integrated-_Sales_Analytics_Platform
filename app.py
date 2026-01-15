"""
Sales Analytics Platform - Main Application

Integrates:
- Data Loader
- Schema Mapper
- Data Cleaner
- KPI Calculator
- Dashboard Charts
"""

import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# Import our modules (using silent versions for production)
from src.utils.data_loader import load_uci_dataset
from src.preprocessing.schema_mapper_silent import SchemaMapper
from src.preprocessing.data_cleaner import DataCleaner
from src.analytics.kpi_calculator import KPICalculator
from src.visualization.dashboard_charts import ChartBuilder

# ============================================================================
# CONFIGURATION & STYLING
# ============================================================================

st.set_page_config(
    page_title="Sales Analytics Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
with open('assets/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Helper function for KPI cards
def kpi_card(title, value, prefix="", suffix=""):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{title}</div>
        <div class="kpi-value">{prefix}{value}{suffix}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# SIDEBAR - DATA INGESTION
# ============================================================================

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=60)
    st.title("Data Controls")
    
    # Data Source Selection
    data_source = st.radio("Select Data Source", ["📦 Sample Data (UCI)", "📤 Upload CSV"])
    
    if data_source == "📦 Sample Data (UCI)":
        if st.button("Load Sample Data", type="primary", use_container_width=True):
            with st.spinner("Loading UCI Online Retail Dataset..."):
                df = load_uci_dataset(verbose=False)
                # Auto-process sample data
                mapper = SchemaMapper(df)
                df_mapped = mapper.apply_mapping(mapper.auto_detect_mapping())
                cleaner = DataCleaner(df_mapped)
                st.session_state['df_clean'] = cleaner.clean()
                st.success("Data Loaded Successfully!")
                st.rerun()
                
    else:
        uploaded_file = st.file_uploader("Upload Sales CSV", type=['csv'])
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.session_state['df_raw'] = df
            
            # Schema Mapping Interface
            st.markdown("---")
            st.subheader("📋 Column Mapping")
            
            mapper = SchemaMapper(df)
            auto_mapping = mapper.auto_detect_mapping()
            
            mapping = {}
            for canonical, info in mapper.CANONICAL_SCHEMA.items():
                auto = auto_mapping.get(canonical)
                options = ["-- Select --"] + df.columns.tolist()
                idx = options.index(auto) if auto in options else 0
                
                label = f"{canonical} {'🔴' if info['required'] else ''}"
                mapping[canonical] = st.selectbox(
                    label, options, index=idx, key=f"map_{canonical}"
                )
                if mapping[canonical] == "-- Select --":
                    mapping[canonical] = None

            if st.button("Process Data", type="primary"):
                is_valid, errors = mapper.validate_mapping(mapping)
                if is_valid:
                    df_mapped = mapper.apply_mapping(mapping)
                    cleaner = DataCleaner(df_mapped)
                    st.session_state['df_clean'] = cleaner.clean()
                    st.success("Data Processed!")
                    st.rerun()
                else:
                    st.error(f"Mapping Errors: {errors}")

    st.markdown("---")
    st.caption("v1.0 | Sales Analytics Pro")

# ============================================================================
# MAIN DASHBOARD
# ============================================================================

if 'df_clean' not in st.session_state:
    # LANDING PAGE (No Data)
    st.markdown("""
    <div style='text-align: center; padding: 50px;'>
        <h1>🚀 Welcome to Sales Analytics Pro</h1>
        <p style='font-size: 18px; color: #888;'>
            Upload your sales data to generate instant insights, trends, and forecasts.
        </p>
        <br>
        <p>👈 <b>Start by loading data from the sidebar!</b></p>
    </div>
    """, unsafe_allow_html=True)
    
else:
    # DATA IS LOADED - SHOW DASHBOARD
    df = st.session_state['df_clean']
    
    # Initialize Analytics Engines
    calculator = KPICalculator(df)
    chart_builder = ChartBuilder(df)
    
    # Headline Metrics
    metrics = calculator.get_headline_metrics()
    
    # Top Navigation
    selected = option_menu(
        menu_title=None,
        options=["Overview", "Product Trends", "Data Explorer"],
        icons=["speedometer2", "graph-up-arrow", "table"],
        orientation="horizontal",
    )
    
    # ------------------------------------------------------------------------
    # TAB 1: OVERVIEW
    # ------------------------------------------------------------------------
    if selected == "Overview":
        st.markdown("### 📊 Executive Summary")
        
        # KPI ROW
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            kpi_card("Total Revenue", f"{metrics['total_revenue']:,.0f}", "$")
        with col2:
            kpi_card("Total Orders", f"{metrics['total_orders']:,}")
        with col3:
            kpi_card("Avg Order Value", f"{metrics['avg_order_value']:,.2f}", "$")
        with col4:
            kpi_card("Customers", f"{metrics['total_customers']:,}")
            
        st.markdown("---")
        
        # CHARTS ROW 1
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.markdown("##### 💰 Revenue Over Time")
            monthly_df = calculator.get_monthly_sales()
            fig_rev = chart_builder.plot_revenue_trend(monthly_df)
            st.plotly_chart(fig_rev, use_container_width=True)
            
        with c2:
            st.markdown("##### 🏆 Top 5 Products")
            top_prods = calculator.get_top_products(limit=5)
            fig_top = chart_builder.plot_top_products(top_prods)
            st.plotly_chart(fig_top, use_container_width=True)
            
        # CHARTS ROW 2
        st.markdown("##### ⏰ Sales Activity")
        fig_hour = chart_builder.plot_hourly_sales()
        if fig_hour:
            st.plotly_chart(fig_hour, use_container_width=True)

    # ------------------------------------------------------------------------
    # TAB 2: PRODUCT TRENDS
    # ------------------------------------------------------------------------
    elif selected == "Product Trends":
        st.markdown("### 🛍️ Product Performance")
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("Product category analysis coming in Sprint 3!")
        with col2:
            # Re-use top products chart but bigger
            top_prods_all = calculator.get_top_products(limit=15)
            fig_all_prods = chart_builder.plot_top_products(top_prods_all)
            st.plotly_chart(fig_all_prods, use_container_width=True)

    # ------------------------------------------------------------------------
    # TAB 3: DATA EXPLORER
    # ------------------------------------------------------------------------
    elif selected == "Data Explorer":
        st.markdown("### 🔍 Raw Data View")
        
        with st.expander("Filter Options"):
            st.write("Filters coming soon...")
            
        st.dataframe(df, use_container_width=True)
        
        csv = df.to_csv(index=False)
        st.download_button("📥 Download Cleaned Data", csv, "clean_sales_data.csv")