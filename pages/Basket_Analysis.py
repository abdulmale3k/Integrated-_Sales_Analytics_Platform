"""
Market Basket Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Basket Analysis", page_icon="🛒", layout="wide")

# --- RESPONSIVE CSS ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    [data-testid="stMetric"] {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px 15px;
        overflow: hidden;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Check for mlxtend
try:
    from mlxtend.frequent_patterns import apriori, association_rules
    MLXTEND_AVAILABLE = True
except ImportError:
    MLXTEND_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False


def main():
    st.title("🛒 Market Basket Analysis")
    st.caption("Discover which products are frequently bought together")
    
    # Check data
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please upload data from the Home page.")
        st.stop()
    
    # Check library
    if not MLXTEND_AVAILABLE:
        st.error("❌ MLxtend library required. Install with: `pip install mlxtend`")
        st.stop()
    
    df = st.session_state['data']
    
    # Check for transaction ID
    if 'transaction_id' not in df.columns:
        st.warning("⚠️ Transaction ID not found in data.")
        st.info("""
        **Market Basket Analysis requires transaction-level data.**
        
        To enable this feature:
        1. Go back to the **Home** page
        2. Re-upload your data
        3. Map the **Transaction ID** column (Invoice Number, Order ID, etc.)
        """)
        st.stop()
    
    st.markdown("---")
    
    # === PARAMETERS ===
    st.markdown("### ⚙️ Analysis Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        min_support = st.slider(
            "Min Support",
            min_value=0.005,
            max_value=0.1,
            value=0.02,
            step=0.005,
            help="Minimum frequency of item combinations (lower = more results)"
        )
    
    with col2:
        min_lift = st.slider(
            "Min Lift",
            min_value=1.0,
            max_value=5.0,
            value=1.2,
            step=0.1,
            help="Minimum lift value (>1 = positive association)"
        )
    
    with col3:
        max_rules = st.slider(
            "Max Rules to Show",
            min_value=10,
            max_value=100,
            value=30,
            step=10
        )
    
    # === RUN ANALYSIS ===
    if st.button("🔍 Run Analysis", type="primary", use_container_width=True):
        with st.spinner("Mining association patterns... This may take a moment."):
            rules = run_basket_analysis(df, min_support, min_lift)
        
        if rules is not None and len(rules) > 0:
            st.session_state['basket_rules'] = rules
            st.success(f"✅ Found {len(rules)} association rules!")
            st.rerun()
        else:
            st.warning("No patterns found. Try lowering the Min Support or Min Lift values.")
    
    # === DISPLAY RESULTS ===
    if st.session_state.get('basket_rules') is not None and len(st.session_state['basket_rules']) > 0:
        rules = st.session_state['basket_rules']
        
        st.markdown("---")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Rules Found", f"{len(rules):,}")
        
        with col2:
            st.metric("📈 Avg Confidence", f"{rules['confidence'].mean():.0%}")
        
        with col3:
            st.metric("🎯 Avg Lift", f"{rules['lift'].mean():.1f}x")
        
        with col4:
            st.metric("🔝 Max Lift", f"{rules['lift'].max():.1f}x")
        
        st.markdown("---")
        
        # Tabs for results
        tab1, tab2, tab3 = st.tabs(["📋 Rules Table", "🕸️ Network", "💡 Insights"])
        
        with tab1:
            display_rules_table(rules.head(max_rules))
        
        with tab2:
            if NETWORKX_AVAILABLE:
                display_network(rules.head(20))
            else:
                st.info("Install networkx for network visualization: `pip install networkx`")
        
        with tab3:
            display_insights(rules)


@st.cache_data(show_spinner=False)
def run_basket_analysis(_df, min_support, min_lift):
    """Run apriori algorithm and generate association rules."""
    try:
        df = _df.copy()
        
        # Create basket format
        basket = df.groupby(['transaction_id', 'product_name'])['quantity'].sum().unstack().fillna(0)
        
        # Convert to binary (bought or not)
        basket_binary = basket.applymap(lambda x: 1 if x > 0 else 0)
        
        # Filter rare products (must appear in at least 1% of transactions)
        min_trans = max(1, int(len(basket_binary) * 0.01))
        product_counts = basket_binary.sum()
        valid_products = product_counts[product_counts >= min_trans].index
        basket_binary = basket_binary[valid_products]
        
        if len(basket_binary.columns) < 2:
            return None
        
        # Generate frequent itemsets
        frequent = apriori(
            basket_binary,
            min_support=min_support,
            use_colnames=True,
            max_len=3
        )
        
        if len(frequent) == 0:
            return None
        
        # Generate rules
        rules = association_rules(frequent, metric="lift", min_threshold=min_lift)
        rules = rules.sort_values('lift', ascending=False)
        
        return rules
    
    except Exception as e:
        st.error(f"Analysis error: {str(e)}")
        return None


def display_rules_table(rules):
    """Display association rules as a formatted table."""
    st.markdown("### 📋 Association Rules")
    
    display = rules.copy()
    display['antecedents'] = display['antecedents'].apply(
        lambda x: ', '.join([str(i)[:30] for i in list(x)])
    )
    display['consequents'] = display['consequents'].apply(
        lambda x: ', '.join([str(i)[:30] for i in list(x)])
    )
    
    display = display[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
    display.columns = ['If Customer Buys', 'They Also Buy', 'Support', 'Confidence', 'Lift']
    
    display['Support'] = display['Support'].apply(lambda x: f"{x:.3f}")
    display['Confidence'] = display['Confidence'].apply(lambda x: f"{x:.0%}")
    display['Lift'] = display['Lift'].apply(lambda x: f"{x:.2f}x")
    
    st.dataframe(display, use_container_width=True, hide_index=True)
    
    # Explanation
    with st.expander("ℹ️ Understanding the Metrics"):
        st.markdown("""
        | Metric | Description |
        |--------|-------------|
        | **Support** | How frequently the items appear together (0-1) |
        | **Confidence** | Probability of buying B given A was bought |
        | **Lift** | How much more likely B is bought with A vs alone (>1 = positive association) |
        """)


def display_network(rules):
    """Display product association network."""
    st.markdown("### 🕸️ Product Relationship Network")
    
    if len(rules) < 2:
        st.info("Not enough rules for network visualization")
        return
    
    G = nx.Graph()
    
    for _, row in rules.iterrows():
        for ant in row['antecedents']:
            for cons in row['consequents']:
                G.add_edge(str(ant)[:20], str(cons)[:20], weight=row['lift'])
    
    if len(G.nodes()) == 0:
        st.info("No connections to display")
        return
    
    # Layout
    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
    
    # Edges
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    # Nodes
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1, color='#888'),
        hoverinfo='none'
    ))
    
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=list(G.nodes()),
        textposition='top center',
        textfont=dict(size=9),
        marker=dict(
            size=20,
            color='#1f77b4',
            line=dict(width=2, color='white')
        ),
        hoverinfo='text'
    ))
    
    fig.update_layout(
        showlegend=False,
        height=450,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=0, r=0, t=10, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_insights(rules):
    """Display actionable insights from association rules."""
    st.markdown("### 💡 Actionable Recommendations")
    
    if len(rules) == 0:
        st.info("No rules to generate insights from")
        return
    
    for idx, row in rules.head(5).iterrows():
        ant = ', '.join([str(x)[:35] for x in list(row['antecedents'])])
        cons = ', '.join([str(x)[:35] for x in list(row['consequents'])])
        
        st.info(f"""
        **Bundle Opportunity #{idx + 1}**
        
        🛒 Customers buying **{ant}** are **{row['lift']:.1f}x** more likely to buy **{cons}**
        
        📊 Confidence: {row['confidence']:.0%} | Support: {row['support']:.3f}
        
        💡 *Consider creating a promotional bundle or cross-sell recommendation*
        """)
    
    st.markdown("---")
    st.markdown("""
    **How to use these insights:**
    - 🏷️ **Bundling:** Create product bundles with high-lift associations
    - 📧 **Email Marketing:** Recommend consequent products to customers who bought antecedent products
    - 🏪 **Store Layout:** Place associated products near each other
    - 💻 **Website:** Show "Frequently bought together" recommendations
    """)


if __name__ == "__main__":
    main()
else:
    main()