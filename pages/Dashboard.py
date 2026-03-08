"""
Dashboard Page - Overview and KPIs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# --- MINIMAL CSS ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.2rem !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def calculate_metrics(df):
    """Calculate key metrics from dataframe."""
    return {
        'total_rows': len(df),
        'date_range_days': (df['order_date'].max() - df['order_date'].min()).days,
        'unique_products': df['product_name'].nunique(),
        'total_revenue': df['total_value'].sum(),
        'avg_order_value': df['total_value'].mean(),
        'median_order_value': df['total_value'].median(),
        'min_date': df['order_date'].min(),
        'max_date': df['order_date'].max(),
        'unique_transactions': df['transaction_id'].nunique() if 'transaction_id' in df.columns else None,
        'unique_customers': df['customer_id'].nunique() if 'customer_id' in df.columns else None
    }


def main():
    st.title("📊 Sales Dashboard")
    
    # Check for data
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please go to the **Home** page to upload your data.")
        st.stop()
    
    df = st.session_state['data']
    metrics = calculate_metrics(df)
    
    # === TOP METRICS ===
    st.subheader("📈 Key Performance Indicators")
    
    # Row 1
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💰 Revenue", f"£{metrics['total_revenue']:,.0f}")
    
    with col2:
        st.metric("🧾 Orders", f"{metrics['total_rows']:,}")
    
    with col3:
        st.metric("📦 Products", f"{metrics['unique_products']:,}")
    
    # Row 2
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.metric("💵 Avg Order", f"£{metrics['avg_order_value']:.2f}")
    
    with col5:
        st.metric("📅 Period", f"{metrics['date_range_days']} days")
    
    with col6:
        if metrics.get('unique_customers'):
            st.metric("👥 Customers", f"{metrics['unique_customers']:,}")
        else:
            daily_avg = metrics['total_revenue'] / max(1, metrics['date_range_days'])
            st.metric("📈 Daily Avg", f"£{daily_avg:,.0f}")
    
    st.markdown("---")
    
    # === TREND CHART ===
    st.subheader("📈 Revenue Trend")
    
    # Aggregation selector
    agg_option = st.radio(
        "View by:",
        ["Daily", "Weekly", "Monthly"],
        horizontal=True,
        label_visibility="collapsed"
    )
    
    agg_map = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
    
    daily = df.groupby('order_date')['total_value'].sum().reset_index()
    daily = daily.set_index('order_date').resample(agg_map[agg_option]).sum().reset_index()
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=daily['order_date'],
        y=daily['total_value'],
        mode='lines+markers' if agg_option != "Daily" else 'lines',
        name=f'{agg_option} Revenue',
        line=dict(color='#3498db', width=2),
        marker=dict(size=6)
    ))
    
    # Add moving average for daily view
    if agg_option == "Daily" and len(daily) > 7:
        daily['MA_7'] = daily['total_value'].rolling(7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=daily['order_date'],
            y=daily['MA_7'],
            mode='lines',
            name='7-Day Average',
            line=dict(color='#e74c3c', width=2, dash='dash')
        ))
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Revenue (£)",
        hovermode='x unified',
        height=350,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # === TWO COLUMN CHARTS ===
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Revenue by Day of Week")
        
        df_copy = df.copy()
        df_copy['day_name'] = df_copy['order_date'].dt.day_name()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dow = df_copy.groupby('day_name')['total_value'].sum().reindex(day_order).fillna(0)
        
        fig_dow = px.bar(
            x=dow.index,
            y=dow.values,
            color=dow.values,
            color_continuous_scale='Blues',
            labels={'x': 'Day', 'y': 'Revenue (£)'}
        )
        fig_dow.update_layout(
            showlegend=False,
            height=280,
            xaxis_title="",
            yaxis_title="Revenue (£)",
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_dow, use_container_width=True)
    
    with col2:
        st.subheader("📆 Revenue by Month")
        
        df_copy = df.copy()
        df_copy['month'] = df_copy['order_date'].dt.to_period('M').astype(str)
        monthly = df_copy.groupby('month')['total_value'].sum().reset_index()
        
        fig_monthly = px.bar(
            monthly,
            x='month',
            y='total_value',
            color='total_value',
            color_continuous_scale='Greens',
            labels={'month': 'Month', 'total_value': 'Revenue (£)'}
        )
        fig_monthly.update_layout(
            showlegend=False,
            height=280,
            xaxis_title="",
            yaxis_title="Revenue (£)",
            xaxis_tickangle=-45,
            coloraxis_showscale=False,
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    st.markdown("---")
    
    # === DATA QUALITY SUMMARY ===
    with st.expander("🔍 Data Quality Summary", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📝 Column Information**")
            info_df = pd.DataFrame({
                'Column': df.columns,
                'Type': df.dtypes.astype(str).values,
                'Non-Null': df.count().values,
                'Null': df.isnull().sum().values
            })
            st.dataframe(info_df, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("**📊 Numerical Statistics**")
            desc = df.describe()
            st.dataframe(desc.round(2), use_container_width=True)


if __name__ == "__main__":
    main()
else:
    main()