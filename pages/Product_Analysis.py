"""
Product Analysis Page - ABC Inventory Classification
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from sidebar import create_sidebar

st.set_page_config(page_title="Product Analysis", page_icon="📦", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp { background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); }
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stSidebarNav"] { display: none !important; }
    .block-container { padding: 2rem 3rem !important; }
    
    h1, h2, h3 { color: #ffffff !important; }
    h1 { background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    p, span, label { color: #a0a0a0 !important; }
    
    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
</style>
""", unsafe_allow_html=True)

def main():
    create_sidebar()

    st.markdown("<h1>📦 ABC Inventory Analysis</h1>", unsafe_allow_html=True)
    st.caption("Automatically classify your products based on the 80/20 rule to optimize cash flow.")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please upload data on the Home page first.")
        st.stop()

    df = st.session_state['data']
    st.markdown("---")

    with st.spinner("Calculating cumulative revenue distribution..."):
        # 1. Calculate revenue per product and sort descending
        product_rev = df.groupby('product_name')['total_value'].sum().reset_index()
        product_rev = product_rev.sort_values(by='total_value', ascending=False)

        # 2. Calculate the cumulative percentage of revenue
        total_revenue = product_rev['total_value'].sum()
        product_rev['cumulative_rev'] = product_rev['total_value'].cumsum()
        product_rev['cumulative_pct'] = product_rev['cumulative_rev'] / total_revenue

        # 3. Assign A, B, or C categories
        def assign_abc(pct):
            if pct <= 0.80: return 'A-Grade (Top 80% of Revenue)'
            elif pct <= 0.95: return 'B-Grade (Next 15% of Revenue)'
            else: return 'C-Grade (Bottom 5% of Revenue)'

        product_rev['Category'] = product_rev['cumulative_pct'].apply(assign_abc)
        
        # Calculate summary stats for the metrics
        a_count = len(product_rev[product_rev['Category'] == 'A-Grade (Top 80% of Revenue)'])
        b_count = len(product_rev[product_rev['Category'] == 'B-Grade (Next 15% of Revenue)'])
        c_count = len(product_rev[product_rev['Category'] == 'C-Grade (Bottom 5% of Revenue)'])

    # --- UI LAYOUT ---
    st.markdown("### 📊 Inventory Health Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 A-Grade Products (The VIPs)", f"{a_count} Items", "Never let these go out of stock")
    col2.metric("🟡 B-Grade Products (Regulars)", f"{b_count} Items", "Maintain standard inventory")
    col3.metric("🔴 C-Grade Products (Dead Weight)", f"{c_count} Items", "Consider discounting/liquidating", delta_color="inverse")

    st.markdown("---")

    col_chart, col_table = st.columns([1.2, 1])

    with col_chart:
        st.markdown("### 📈 Revenue Distribution")
        # Draw a beautiful, dark-mode Pie Chart
        fig = px.pie(product_rev, names='Category', values='total_value', 
                     color='Category', template='plotly_dark',
                     color_discrete_map={'A-Grade (Top 80% of Revenue)':'#10b981', 
                                         'B-Grade (Next 15% of Revenue)':'#f59e0b', 
                                         'C-Grade (Bottom 5% of Revenue)':'#ef4444'},
                     hole=0.4) # Makes it a modern donut chart
        
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("### 🗄️ Product Action List")
        # Format the dataframe for display
        display_df = product_rev[['product_name', 'total_value', 'Category']].copy()
        display_df['total_value'] = display_df['total_value'].apply(lambda x: f"£{x:,.2f}")
        display_df.rename(columns={'product_name': 'Product', 'total_value': 'Revenue Generated'}, inplace=True)
        
        st.dataframe(display_df, use_container_width=True, height=400)

if __name__ == "__main__":
    main()