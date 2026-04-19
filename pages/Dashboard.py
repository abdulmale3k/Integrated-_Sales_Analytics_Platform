"""
Dashboard Page - Stunning Overview
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sidebar import create_sidebar  # <--- Importing your custom sidebar

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# --- STUNNING CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0f0f1a;
        --bg-secondary: #1a1a2e;
        --bg-card: rgba(255, 255, 255, 0.05);
        --text-primary: #ffffff;
        --text-secondary: #a0a0a0;
        --accent-primary: #6366f1;
        --gradient-1: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        --border-radius: 16px;
    }
    
    .stApp {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    /* Hide Streamlit default menus */
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stSidebarNav"] { display: none !important; }
    
    .block-container {
        padding: 2rem 3rem !important;
    }
    
    h1, h2, h3 { color: var(--text-primary) !important; }
    
    h1 {
        background: var(--gradient-1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    p, span, label { color: var(--text-secondary) !important; }
    
    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: var(--border-radius);
        padding: 1rem 1.5rem;
    }
    
    [data-testid="stMetricLabel"] { color: var(--text-secondary) !important; }
    [data-testid="stMetricValue"] { color: var(--text-primary) !important; font-weight: 600 !important; }
    
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card);
        border-radius: var(--border-radius);
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary);
        border-radius: 8px;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-1) !important;
        color: white !important;
    }
    
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    hr { border-color: rgba(255,255,255,0.1) !important; }
    
    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

# Chart theme
CHART_THEME = {
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    'font': {'color': '#a0a0a0', 'family': 'Inter'},
    'xaxis': {'gridcolor': 'rgba(255,255,255,0.1)', 'linecolor': 'rgba(255,255,255,0.1)'},
    'yaxis': {'gridcolor': 'rgba(255,255,255,0.1)', 'linecolor': 'rgba(255,255,255,0.1)'},
}


def calculate_metrics(df):
    """Calculate key metrics."""
    return {
        'total_rows': len(df),
        'date_range_days': (df['order_date'].max() - df['order_date'].min()).days,
        'unique_products': df['product_name'].nunique(),
        'total_revenue': df['total_value'].sum(),
        'avg_order_value': df['total_value'].mean(),
        'unique_customers': df['customer_id'].nunique() if 'customer_id' in df.columns else None
    }

# --- HELPER FUNCTION FOR EXPORT ---
@st.cache_data
def convert_df(df):
    """Converts the dataframe to CSV format safely without index."""
    return df.to_csv(index=False).encode('utf-8')


def main():
    # === SIDEBAR ===
    create_sidebar()  # <--- Injecting the custom sidebar here
    
    st.markdown("<h1>📊 Sales Dashboard</h1>", unsafe_allow_html=True)
    st.caption("Real-time overview of your sales performance")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please go to the **Home** page to upload your data.")
        st.stop()
    
    df = st.session_state['data']
    metrics = calculate_metrics(df)
    
    # === METRICS ROW ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💰 Revenue", f"£{metrics['total_revenue']:,.0f}")
    with col2:
        st.metric("🧾 Orders", f"{metrics['total_rows']:,}")
    with col3:
        st.metric("📦 Products", f"{metrics['unique_products']:,}")
    with col4:
        st.metric("💵 Avg Order", f"£{metrics['avg_order_value']:.2f}")
    
    st.markdown("---")
    
    # === TABS ===
    tab1, tab2, tab3 = st.tabs(["📈 Trends", "📅 Time Analysis", "📊 Breakdown"])
    
    with tab1:
        st.markdown("### Revenue Trend")
        
        agg = st.radio("Aggregate by:", ["Daily", "Weekly", "Monthly"], horizontal=True, label_visibility="collapsed")
        agg_map = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
        
        daily = df.groupby('order_date')['total_value'].sum().reset_index()
        daily = daily.set_index('order_date').resample(agg_map[agg]).sum().reset_index()
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily['order_date'],
            y=daily['total_value'],
            mode='lines',
            name='Revenue',
            line=dict(color='#6366f1', width=3),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)'
        ))
        
        if agg == "Daily" and len(daily) > 7:
            daily['MA'] = daily['total_value'].rolling(7).mean()
            fig.add_trace(go.Scatter(
                x=daily['order_date'],
                y=daily['MA'],
                mode='lines',
                name='7-Day MA',
                line=dict(color='#f59e0b', width=2, dash='dash')
            ))
        
        fig.update_layout(
            **CHART_THEME,
            height=400,
            margin=dict(l=0, r=0, t=20, b=0),
            legend=dict(orientation='h', y=1.1),
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Revenue by Day of Week")
            
            df_copy = df.copy()
            df_copy['dow'] = df_copy['order_date'].dt.day_name()
            order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dow = df_copy.groupby('dow')['total_value'].sum().reindex(order).fillna(0)
            
            fig = px.bar(
                x=dow.index, y=dow.values,
                color=dow.values,
                color_continuous_scale=['#6366f1', '#8b5cf6', '#a78bfa']
            )
            fig.update_layout(**CHART_THEME, height=300, showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Revenue by Month")
            
            df_copy = df.copy()
            df_copy['month'] = df_copy['order_date'].dt.to_period('M').astype(str)
            monthly = df_copy.groupby('month')['total_value'].sum().reset_index()
            
            fig = px.bar(
                monthly, x='month', y='total_value',
                color='total_value',
                color_continuous_scale=['#10b981', '#06b6d4', '#3b82f6']
            )
            fig.update_layout(**CHART_THEME, height=300, showlegend=False, coloraxis_showscale=False, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### Top 10 Products by Revenue")
        
        top = df.groupby('product_name')['total_value'].sum().sort_values(ascending=True).tail(10)
        
        fig = px.bar(
            x=top.values, y=top.index,
            orientation='h',
            color=top.values,
            color_continuous_scale=['#6366f1', '#8b5cf6']
        )
        fig.update_layout(**CHART_THEME, height=400, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === DATA QUALITY & EXPORT ROW ===
    st.markdown("### 📥 Data Management")
    
    # We use columns to put the Quality Summary and the Export option side by side (or stacked)
    with st.expander("🔍 Data Quality Summary"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Column Info**")
            info = pd.DataFrame({'Column': df.columns, 'Type': df.dtypes.astype(str), 'Non-Null': df.count().values})
            st.dataframe(info, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**Statistics**")
            st.dataframe(df.describe().round(2), use_container_width=True)
            
    with st.expander("💾 Export Cleaned Dataset"):
        st.write("Download your formatted, cleaned dataset. This file is ready to be loaded into Excel or any other Business Intelligence tool.")
        
        # Call the cached conversion function
        csv_data = convert_df(df)
        
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name="SME_Cleaned_Transactions.csv",
            mime="text/csv",
            use_container_width=True
        )


if __name__ == "__main__":
    main()
else:
    main()