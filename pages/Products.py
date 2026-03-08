"""
Product Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Products", page_icon="📦", layout="wide")

# --- RESPONSIVE CSS ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
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
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def main():
    st.title("📦 Product Analysis")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please upload data from the Home page.")
        st.stop()
    
    df = st.session_state['data']
    
    # Aggregate product data
    products = df.groupby('product_name').agg({
        'total_value': 'sum',
        'quantity': 'sum',
        'unit_price': 'mean'
    }).reset_index()
    
    products.columns = ['Product', 'Revenue', 'Quantity', 'Avg Price']
    products = products.sort_values('Revenue', ascending=False)
    products['Revenue %'] = (products['Revenue'] / products['Revenue'].sum() * 100)
    
    # === METRICS (2 columns) ===
    col1, col2 = st.columns(2)
    
    with col1:
        top_product = products.iloc[0]['Product']
        if len(top_product) > 30:
            top_product = top_product[:27] + "..."
        st.metric("🏆 Top Product", top_product)
    
    with col2:
        st.metric("💰 Top Revenue", f"£{products.iloc[0]['Revenue']:,.2f}")
    
    st.markdown("---")
    
    # === TABS ===
    tab1, tab2, tab3 = st.tabs(["📊 Top Products", "📈 Pareto Analysis", "🔍 Search"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            n_products = st.slider("Show top N products:", 5, 30, 10)
            
            top_n = products.head(n_products).copy()
            top_n['Short Name'] = top_n['Product'].str[:25]
            
            fig = px.bar(
                top_n,
                x='Revenue',
                y='Short Name',
                orientation='h',
                color='Revenue',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(
                yaxis=dict(autorange="reversed"),
                showlegend=False,
                height=max(350, n_products * 28),
                coloraxis_showscale=False,
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis_title="Revenue (£)",
                yaxis_title=""
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**📋 Product Performance Table**")
            
            display = products.head(n_products).copy()
            display['Revenue'] = display['Revenue'].apply(lambda x: f"£{x:,.2f}")
            display['Quantity'] = display['Quantity'].apply(lambda x: f"{x:,.0f}")
            display['Avg Price'] = display['Avg Price'].apply(lambda x: f"£{x:.2f}")
            display['Revenue %'] = display['Revenue %'].apply(lambda x: f"{x:.1f}%")
            
            st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                height=max(350, n_products * 35)
            )
    
    with tab2:
        st.markdown("### 📈 Pareto Analysis (80/20 Rule)")
        
        cumsum = products['Revenue'].cumsum() / products['Revenue'].sum() * 100
        n_80 = (cumsum <= 80).sum()
        
        st.info(f"**{n_80}** products ({n_80/len(products)*100:.1f}%) generate **80%** of revenue")
        
        fig = go.Figure()
        
        # Show max 100 products for performance
        max_show = min(100, len(products))
        
        fig.add_trace(go.Bar(
            x=list(range(max_show)),
            y=products['Revenue'].head(max_show).values,
            name='Revenue',
            marker_color='steelblue'
        ))
        
        fig.add_trace(go.Scatter(
            x=list(range(max_show)),
            y=cumsum.head(max_show).values,
            name='Cumulative %',
            yaxis='y2',
            line=dict(color='red', width=2)
        ))
        
        fig.add_hline(
            y=80, line_dash="dash", line_color="orange",
            annotation_text="80% threshold", yref='y2'
        )
        
        fig.update_layout(
            xaxis_title="Products (ranked by revenue)",
            yaxis_title="Revenue (£)",
            yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 100]),
            height=400,
            showlegend=True,
            legend=dict(orientation='h', y=1.1),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown("### 🔍 Search Products")
        
        search = st.text_input("Search by product name:", "", placeholder="Enter product name...")
        
        if search:
            filtered = products[products['Product'].str.contains(search, case=False, na=False)]
            
            if len(filtered) > 0:
                st.success(f"Found {len(filtered)} products matching '{search}'")
                
                display = filtered.copy()
                display['Revenue'] = display['Revenue'].apply(lambda x: f"£{x:,.2f}")
                display['Quantity'] = display['Quantity'].apply(lambda x: f"{x:,.0f}")
                display['Avg Price'] = display['Avg Price'].apply(lambda x: f"£{x:.2f}")
                display['Revenue %'] = display['Revenue %'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(display, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No products found matching '{search}'")
        else:
            st.caption("Enter a search term to filter products")
    
    # Download button
    st.markdown("---")
    st.download_button(
        "📥 Download Product Data (CSV)",
        products.to_csv(index=False),
        "product_analysis.csv",
        "text/csv",
        use_container_width=False
    )


if __name__ == "__main__":
    main()
else:
    main()