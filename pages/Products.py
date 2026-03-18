"""
Product Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sidebar import create_sidebar  # <--- Importing your custom sidebar

st.set_page_config(page_title="Products", page_icon="📦", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Hide Streamlit default menus */
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stSidebarNav"] { display: none !important; }
    
    .block-container { padding: 2rem 3rem !important; }
    
    h1, h2, h3 { color: #ffffff !important; }
    h1 { background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    p, span, label { color: #a0a0a0 !important; }
    
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px;
        padding: 1rem 1.5rem;
    }
    
    [data-testid="stMetricLabel"] { color: #a0a0a0 !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    
    .stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 0.5rem; }
    .stTabs [data-baseweb="tab"] { color: #a0a0a0; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; }
    
    hr { border-color: rgba(255,255,255,0.1) !important; }
</style>
""", unsafe_allow_html=True)

CHART_THEME = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'font': {'color': '#a0a0a0'},
    'xaxis': {'gridcolor': 'rgba(255,255,255,0.1)'},
    'yaxis': {'gridcolor': 'rgba(255,255,255,0.1)'},
}


def main():
    # === SIDEBAR ===
    create_sidebar()  # <--- Injecting the custom sidebar here
    
    st.markdown("<h1>📦 Product Analysis</h1>", unsafe_allow_html=True)
    st.caption("Deep dive into your product performance")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded.")
        st.stop()
    
    df = st.session_state['data']
    
    products = df.groupby('product_name').agg({
        'total_value': 'sum',
        'quantity': 'sum',
        'unit_price': 'mean'
    }).reset_index()
    products.columns = ['Product', 'Revenue', 'Quantity', 'Avg Price']
    products = products.sort_values('Revenue', ascending=False)
    products['Revenue %'] = products['Revenue'] / products['Revenue'].sum() * 100
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🏆 Top Product", products.iloc[0]['Product'][:25] + "...")
    with col2:
        st.metric("💰 Top Revenue", f"£{products.iloc[0]['Revenue']:,.0f}")
    with col3:
        st.metric("📊 Market Share", f"{products.iloc[0]['Revenue %']:.1f}%")
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Rankings", "📈 Pareto", "🔍 Search"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            n = st.slider("Top N products:", 5, 30, 10)
            
            top = products.head(n)
            fig = px.bar(
                top, x='Revenue', y='Product', orientation='h',
                color='Revenue', color_continuous_scale=['#6366f1', '#8b5cf6']
            )
            
            # --- THE FIX IS RIGHT HERE ---
            fig.update_layout(**CHART_THEME, height=max(350, n*30), showlegend=False, coloraxis_showscale=False)
            fig.update_yaxes(categoryorder='total ascending')
            # -----------------------------
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Performance Table")
            display = products.head(n).copy()
            display['Revenue'] = display['Revenue'].apply(lambda x: f"£{x:,.2f}")
            display['Quantity'] = display['Quantity'].apply(lambda x: f"{x:,.0f}")
            display['Avg Price'] = display['Avg Price'].apply(lambda x: f"£{x:.2f}")
            display['Revenue %'] = display['Revenue %'].apply(lambda x: f"{x:.1f}%")
            st.dataframe(display, use_container_width=True, hide_index=True, height=400)
    
    with tab2:
        st.markdown("### Pareto Analysis (80/20 Rule)")
        
        cumsum = products['Revenue'].cumsum() / products['Revenue'].sum() * 100
        n_80 = (cumsum <= 80).sum()
        
        st.info(f"**{n_80}** products ({n_80/len(products)*100:.1f}%) generate **80%** of revenue")
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(range(min(100, len(products)))), y=products['Revenue'].head(100), marker_color='#6366f1', name='Revenue'))
        fig.add_trace(go.Scatter(x=list(range(min(100, len(products)))), y=cumsum.head(100), line=dict(color='#f59e0b', width=3), name='Cumulative %', yaxis='y2'))
        fig.add_hline(y=80, line_dash="dash", line_color="#ef4444", annotation_text="80%", yref='y2')
        fig.update_layout(**CHART_THEME, height=400, yaxis2=dict(overlaying='y', side='right', range=[0,100], gridcolor='rgba(0,0,0,0)'), legend=dict(orientation='h', y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### Search Products")
        search = st.text_input("🔍", placeholder="Search product name...")
        
        if search:
            results = products[products['Product'].str.contains(search, case=False, na=False)]
            if len(results):
                st.success(f"Found {len(results)} products")
                st.dataframe(results, use_container_width=True, hide_index=True)
            else:
                st.warning("No products found")
    
    st.markdown("---")
    st.download_button("📥 Download Product Data", products.to_csv(index=False), "products.csv", "text/csv")


if __name__ == "__main__":
    main()
else:
    main()