import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
import numpy as np
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# --- CONFIGURATION ---
st.set_page_config(page_title="SME Analytics Platform", page_icon="📈", layout="wide")

# --- 1.Known Column Aliases ---
# The system looks for these names to auto-map columns
COLUMN_ALIASES = {
    "order_date": ["InvoiceDate", "date", "Order Date", "time", "Date"],
    "product_name": ["Description", "Product Name", "Item", "product_name"],
    "quantity": ["Quantity", "qty", "Count", "quantity"],
    "unit_price": ["UnitPrice", "Price", "Cost", "unit_price", "Unit Price"]
}
REQUIRED_TARGETS = list(COLUMN_ALIASES.keys())

# --- HELPER FUNCTIONS ---

def auto_detect_columns(columns):
    """Scans columns to automatically match them to system requirements."""
    mapping = {}
    missing = []
    lower_cols = {c.lower(): c for c in columns}
    
    for target in REQUIRED_TARGETS:
        found = False
        possible_names = COLUMN_ALIASES[target]
        for alias in possible_names:
            if alias.lower() in lower_cols:
                mapping[target] = lower_cols[alias.lower()]
                found = True
                break
        if not found:
            missing.append(target)
    return mapping, missing

@st.cache_data
def load_data(file):
    """Universal loader for CSV and Excel files."""
    if file.name.endswith('.csv'):
        try:
            return pd.read_csv(file)
        except UnicodeDecodeError:
            # Fallback for older CSV encodings
            return pd.read_csv(file, encoding='ISO-8859-1')
    elif file.name.endswith('.xlsx'):
        return pd.read_excel(file)
    return None

def generate_pdf(df, total_rev, total_orders):
    """Generates a PDF Report in memory."""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    p.setFont("Helvetica-Bold", 24)
    p.drawString(50, height - 50, "Sales Analytics Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 80, "Generated automatically by SME Analytics Platform")
    p.line(50, height - 90, width - 50, height - 90)
    
    # Summary
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 120, "Executive Summary:")
    
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 145, f"• Total Revenue: £{total_rev:,.2f}")
    p.drawString(50, height - 165, f"• Total Transactions: {total_orders}")
    
    # Dates
    start_date = df['order_date'].min().date()
    end_date = df['order_date'].max().date()
    p.drawString(50, height - 185, f"• Period: {start_date} to {end_date}")
    
    # Top Products
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 230, "Top 5 Performing Products:")
    
    top_5 = df.groupby('product_name')['total_value'].sum().sort_values(ascending=False).head(5)
    
    y_position = height - 255
    p.setFont("Helvetica", 12)
    for product, revenue in top_5.items():
        # Clean product name if it's too long
        clean_name = str(product)[:40] 
        p.drawString(70, y_position, f"- {clean_name}: £{revenue:,.2f}")
        y_position -= 20
        
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(50, 50, "Confidential - Internal Use Only")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer

# --- MAIN APPLICATION ---

def main():
    st.title("📈 Integrated Sales Analytics Platform")
    
    # Initialize Session State
    if 'data' not in st.session_state:
        st.session_state['data'] = None

    # --- STEP 1: DATA INGESTION ---
    st.markdown("### Step 1: Data Ingestion")
    uploaded_file = st.file_uploader("Upload Sales Data (CSV or Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file is not None:
        try:
            with st.spinner('Reading file...'):
                # Load raw data but keep it in session so we don't reload on every click
                if 'raw_df' not in st.session_state or st.session_state.get('last_file') != uploaded_file.name:
                    st.session_state['raw_df'] = load_data(uploaded_file)
                    st.session_state['last_file'] = uploaded_file.name
                
                df_raw = st.session_state['raw_df']

            # Auto-Detect Logic
            detected_map, missing_cols = auto_detect_columns(df_raw.columns)
            final_mapping = {}
            
            # UI: Show Success or Manual Fallback
            if len(missing_cols) == 0:
                st.success("✅ Auto-detected dataset format.")
                final_mapping = detected_map
                process_button = st.button("Confirm & Process Data")
            else:
                st.warning(f"⚠️ Could not automatically find: {', '.join(missing_cols)}. Please map manually.")
                col1, col2 = st.columns(2)
                for i, target in enumerate(REQUIRED_TARGETS):
                    options = list(df_raw.columns)
                    default_idx = 0
                    if target in detected_map:
                        default_idx = options.index(detected_map[target])
                    
                    with col1 if i % 2 == 0 else col2:
                        final_mapping[target] = st.selectbox(
                            f"Map system field '{target}' to:",
                            options,
                            index=default_idx,
                            key=f"map_{target}"
                        )
                process_button = st.button("Process Data")

            # Processing Logic
            if process_button:
                with st.spinner('Cleaning data...'):
                    # 1. Rename
                    rename_map = {v: k for k, v in final_mapping.items()}
                    df_clean = df_raw.rename(columns=rename_map)
                    df_clean = df_clean[REQUIRED_TARGETS]
                    
                    # 2. Convert Types
                    df_clean['quantity'] = pd.to_numeric(df_clean['quantity'], errors='coerce')
                    df_clean['unit_price'] = pd.to_numeric(df_clean['unit_price'], errors='coerce')
                    
                    # 3. Calculate Revenue
                    df_clean['total_value'] = df_clean['quantity'] * df_clean['unit_price']
                    
                    # 4. Convert Dates
                    df_clean['order_date'] = pd.to_datetime(df_clean['order_date'], errors='coerce')
                    
                    # 5. Clean Data (Remove returns/missing dates)
                    df_clean = df_clean[df_clean['quantity'] > 0]
                    df_clean = df_clean[df_clean['unit_price'] > 0]
                    df_clean = df_clean.dropna(subset=['order_date'])
                    
                    # Save to Session State
                    st.session_state['data'] = df_clean
                    st.success(f"✅ Processed {len(df_clean)} valid transactions!")
                    st.rerun()

        except Exception as e:
            st.error(f"Error reading file: {e}")

    # --- STEP 2: DASHBOARD ---
    if st.session_state['data'] is not None:
        df = st.session_state['data']
        
        st.markdown("---")
        # Tabs Logic
        tab1, tab2, tab3 = st.tabs(["📊 Overview", "📦 Products", "🤖 AI Forecast"])
        
        # --- TAB 1: OVERVIEW & REPORT ---
        with tab1:
            # Calculate variables first so they exist for the PDF
            total_rev = df['total_value'].sum()
            total_orders = len(df)
            
            # Display Metrics
            col1, col2 = st.columns(2)
            col1.metric("Total Revenue", f"£{total_rev:,.2f}")
            col2.metric("Total Transactions", total_orders)
            
            # Trend Chart
            daily = df.groupby('order_date')['total_value'].sum().reset_index()
            st.plotly_chart(px.line(daily, x='order_date', y='total_value', title="Sales Trend"), use_container_width=True)
            
            st.markdown("---")
            # PDF Generation Button
            if st.button("📄 Generate PDF Report"):
                pdf_data = generate_pdf(df, total_rev, total_orders)
                st.download_button(
                    label="⬇️ Download Executive Summary",
                    data=pdf_data,
                    file_name="SME_Sales_Report.pdf",
                    mime="application/pdf"
                )

        # --- TAB 2: PRODUCTS ---
        with tab2:
            st.subheader("Top 10 Best-Selling Products")
            prod_sales = df.groupby('product_name')['total_value'].sum().reset_index()
            top_products = prod_sales.sort_values('total_value', ascending=False).head(10)
            
            fig = px.bar(top_products, x='total_value', y='product_name', orientation='h', title="Top 10 Products")
            fig.update_layout(yaxis=dict(autorange="reversed")) # Best product at top
            st.plotly_chart(fig, use_container_width=True)

        # --- TAB 3: AI FORECASTING ---
        with tab3:
            st.subheader("🔮 Revenue Forecasting (AI-Powered)")
            
            # Prepare Data (Resample to ensure continuous days)
            daily_data = df.groupby('order_date')['total_value'].sum().reset_index()
            daily_data = daily_data.set_index('order_date').resample('D').sum().reset_index()
            
            # Feature Engineering
            daily_data['day_index'] = np.arange(len(daily_data))
            daily_data['day_of_week'] = daily_data['order_date'].dt.dayofweek
            
            if len(daily_data) < 7:
                st.warning("⚠️ Need at least 7 days of data to detect weekly patterns.")
            else:
                # Train Model
                X = daily_data[['day_index', 'day_of_week']]
                y = daily_data['total_value']
                
                model = LinearRegression()
                model.fit(X, y)
                
                # Predict Future (30 Days)
                future_days = 30
                last_idx = daily_data['day_index'].max()
                last_date = daily_data['order_date'].max()
                
                future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, future_days + 1)]
                future_indices = np.arange(last_idx + 1, last_idx + future_days + 1)
                future_weekdays = [d.weekday() for d in future_dates]
                
                X_future = pd.DataFrame({
                    'day_index': future_indices,
                    'day_of_week': future_weekdays
                })
                
                future_pred = model.predict(X_future)
                future_pred = np.maximum(future_pred, 0) # No negative revenue
                
                # Combine & Visualize
                df_pred = pd.DataFrame({
                    'order_date': future_dates, 
                    'total_value': future_pred, 
                    'Type': 'Forecast'
                })
                daily_data['Type'] = 'Historical'
                
                # Focus on last 90 days + Forecast
                df_final = pd.concat([daily_data.tail(90), df_pred])
                
                fig_ai = px.line(df_final, x='order_date', y='total_value', color='Type', 
                                color_discrete_map={'Historical': 'steelblue', 'Forecast': 'limegreen'},
                                title="30-Day Revenue Forecast (With Weekly Seasonality)")
                
                st.plotly_chart(fig_ai, use_container_width=True)
                st.metric("Predicted Revenue (Next 30 Days)", f"£{df_pred['total_value'].sum():,.2f}")

if __name__ == "__main__":
    main()