"""
Market Basket Analysis Page
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sidebar import create_sidebar  # <--- Importing your custom sidebar

st.set_page_config(page_title="Basket Analysis", page_icon="🛒", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp { background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); }
    
    /* Hide Streamlit default menus */
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stSidebarNav"] { display: none !important; }
    
    .block-container { padding: 2rem 3rem !important; }
    
    h1, h2, h3 { color: #ffffff !important; }
    h1 { background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    p, span, label { color: #a0a0a0 !important; }
    
    [data-testid="stMetric"] { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 1rem; }
    [data-testid="stMetricLabel"] { color: #a0a0a0 !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    
    .stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.05); border-radius: 16px; padding: 0.5rem; }
    .stTabs [data-baseweb="tab"] { color: #a0a0a0; border-radius: 8px; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; }
    
    .stButton > button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; border: none !important; border-radius: 8px !important; }
    
    hr { border-color: rgba(255,255,255,0.1) !important; }
    .stAlert { background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.1) !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

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
    # === SIDEBAR ===
    create_sidebar()  # <--- Injecting the custom sidebar here
    
    st.markdown("<h1>🛒 Market Basket Analysis</h1>", unsafe_allow_html=True)
    st.caption("Discover hidden product associations")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded.")
        st.stop()
    
    if not MLXTEND_AVAILABLE:
        st.error("❌ Install mlxtend: `pip install mlxtend`")
        st.stop()
    
    df = st.session_state['data']
    
    if 'transaction_id' not in df.columns:
        st.warning("⚠️ Transaction ID required for basket analysis.")
        st.info("Re-upload data and map the Transaction ID column.")
        st.stop()
    
    st.markdown("---")
    
    # Parameters
    col1, col2, col3 = st.columns(3)
    with col1:
        min_support = st.slider("Min Support", 0.005, 0.1, 0.02, 0.005)
    with col2:
        min_lift = st.slider("Min Lift", 1.0, 5.0, 1.2, 0.1)
    with col3:
        max_rules = st.slider("Max Rules", 10, 100, 30, 10)
    
    if st.button("🔍 Run Analysis", type="primary", use_container_width=True):
        with st.spinner("Mining patterns..."):
            rules = run_analysis(df, min_support, min_lift)
        
        if rules is not None and len(rules) > 0:
            st.session_state['basket_rules'] = rules
            st.success(f"✅ Found {len(rules)} rules!")
            st.rerun()
        else:
            st.warning("No patterns found. Try lower thresholds.")
    
    if st.session_state.get('basket_rules') is not None:
        rules = st.session_state['basket_rules']
        
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📊 Rules", len(rules))
        col2.metric("📈 Avg Confidence", f"{rules['confidence'].mean():.0%}")
        col3.metric("🎯 Avg Lift", f"{rules['lift'].mean():.1f}x")
        col4.metric("🔝 Max Lift", f"{rules['lift'].max():.1f}x")
        
        st.markdown("---")
        
        tab1, tab2, tab3 = st.tabs(["📋 Rules", "🕸️ Network", "💡 Insights"])
        
        with tab1:
            display = rules.head(max_rules).copy()
            display['antecedents'] = display['antecedents'].apply(lambda x: ', '.join(list(x)[:2]))
            display['consequents'] = display['consequents'].apply(lambda x: ', '.join(list(x)[:2]))
            display = display[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
            display.columns = ['If Buys', 'Also Buys', 'Support', 'Confidence', 'Lift']
            display['Confidence'] = display['Confidence'].apply(lambda x: f"{x:.0%}")
            display['Lift'] = display['Lift'].apply(lambda x: f"{x:.2f}x")
            st.dataframe(display, use_container_width=True, hide_index=True)
        
        with tab2:
            if NETWORKX_AVAILABLE:
                render_network(rules.head(15))
            else:
                st.info("Install networkx for visualization")
        
        with tab3:
            for i, row in rules.head(3).iterrows():
                ant = ', '.join(list(row['antecedents']))[:40]
                cons = ', '.join(list(row['consequents']))[:40]
                st.info(f"🛒 **{ant}** → **{cons}** (Lift: {row['lift']:.1f}x, Confidence: {row['confidence']:.0%})")


@st.cache_data(show_spinner=False)
def run_analysis(_df, min_support, min_lift):
    try:
        df = _df.copy()
        basket = df.groupby(['transaction_id', 'product_name'])['quantity'].sum().unstack().fillna(0)
        basket_binary = basket.applymap(lambda x: 1 if x > 0 else 0)
        
        min_trans = max(1, int(len(basket_binary) * 0.01))
        valid = basket_binary.sum()[basket_binary.sum() >= min_trans].index
        basket_binary = basket_binary[valid]
        
        if len(basket_binary.columns) < 2:
            return None
        
        frequent = apriori(basket_binary, min_support=min_support, use_colnames=True, max_len=3)
        if len(frequent) == 0:
            return None
        
        rules = association_rules(frequent, metric="lift", min_threshold=min_lift)
        return rules.sort_values('lift', ascending=False)
    except:
        return None


def render_network(rules):
    G = nx.Graph()
    for _, row in rules.iterrows():
        for ant in row['antecedents']:
            for cons in row['consequents']:
                G.add_edge(str(ant)[:15], str(cons)[:15])
    
    if len(G.nodes()) == 0:
        return
    
    pos = nx.spring_layout(G, k=2, seed=42)
    
    edge_x, edge_y = [], []
    for e in G.edges():
        x0, y0 = pos[e[0]]
        x1, y1 = pos[e[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=1, color='#6366f1'), hoverinfo='none'))
    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text', text=list(G.nodes()), textposition='top center', textfont=dict(size=10, color='#a0a0a0'), marker=dict(size=20, color='#8b5cf6', line=dict(width=2, color='white'))))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, height=450, xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()