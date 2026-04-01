"""
Market Basket Analysis Page - FYP Optimized
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sidebar import create_sidebar  

st.set_page_config(page_title="Basket Analysis", page_icon="🛒", layout="wide")

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
    
    [data-testid="stMetric"] { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 1rem; }
    [data-testid="stMetricLabel"] { color: #a0a0a0 !important; font-size: 0.9rem !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.8rem !important;}
    
    .stTabs [data-baseweb="tab-list"] { background: rgba(255,255,255,0.05); border-radius: 12px; padding: 0.5rem; gap: 1rem; }
    .stTabs [data-baseweb="tab"] { color: #a0a0a0; border-radius: 8px; padding: 0.5rem 1rem; }
    .stTabs [aria-selected="true"] { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; }
    
    .stButton > button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; border: none !important; border-radius: 8px !important; transition: 0.3s; }
    .stButton > button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4); }
    
    hr { border-color: rgba(255,255,255,0.1) !important; }
    
    /* Custom Strategy Cards */
    .strategy-card { background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; }
    .strategy-title { color: white; font-weight: 600; font-size: 1.1rem; margin-bottom: 0.5rem; }
    .strategy-text { color: #d1d5db; font-size: 0.95rem; line-height: 1.5; }
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
    create_sidebar()
    
    st.markdown("<h1>🛒 Smart Bundling & Upselling</h1>", unsafe_allow_html=True)
    st.caption("Automatically discover which products your customers frequently buy together to build profitable bundles.")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please upload your dataset on the Home page.")
        st.stop()
    
    if not MLXTEND_AVAILABLE:
        st.error("❌ Required math library is missing. Run `pip install mlxtend` in your terminal.")
        st.stop()
    
    df = st.session_state['data']
    
    # --- SMART COLUMN DETECTION ---
    # Ensures the app doesn't crash if the column is named differently
    possible_id_cols = ['transaction_id', 'order_id', 'invoice_no', 'InvoiceNo', 'OrderID']
    order_col = next((col for col in possible_id_cols if col in df.columns), None)
    
    if not order_col:
        st.error("⚠️ Could not find a Transaction ID or Order ID column in your data. Please ensure your dataset has a column tracking individual orders.")
        st.stop()
        
    st.markdown("---")
    
    # --- ALGORITHM TUNING (HIDDEN FOR CLIENTS, ACCESSIBLE FOR PROFESSORS) ---
    with st.expander("⚙️ Advanced Technical Settings (Algorithm Tuning)"):
        st.markdown("<p style='font-size: 0.85rem;'>Adjust the hyperparameters for the Apriori pattern mining algorithm.</p>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            min_support = st.slider("Min Support (Frequency)", 0.005, 0.1, 0.02, 0.005, help="Minimum % of total transactions that must contain the itemset.")
        with col2:
            min_lift = st.slider("Min Lift (Correlation)", 1.0, 5.0, 1.2, 0.1, help="Values > 1 indicate the items are bought together more often than random chance.")
        with col3:
            max_rules = st.slider("Max Rules to Display", 5, 50, 15, 5)
            
        if st.button("🔄 Rerun Apriori Algorithm", type="primary", use_container_width=True):
            with st.spinner("Mining transaction patterns..."):
                rules = run_analysis(df, order_col, min_support, min_lift)
            
            if rules is not None and not rules.empty:
                st.session_state['basket_rules'] = rules
                st.success(f"✅ Optimization complete. Generated {len(rules)} association rules.")
            else:
                st.session_state['basket_rules'] = None
                st.warning("No patterns found with these strict thresholds. Try lowering the Min Support or Min Lift.")

    # --- AUTO-RUN IF NO RULES EXIST ---
    if st.session_state.get('basket_rules') is None:
        with st.spinner("Analyzing purchase behaviors..."):
            st.session_state['basket_rules'] = run_analysis(df, order_col, 0.02, 1.2)

    # --- RESULTS DISPLAY ---
    rules = st.session_state.get('basket_rules')
    
    if rules is not None and not rules.empty:
        # High-level metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("🛒 Valid Pairings Found", len(rules))
        col2.metric("🎯 Strongest Multiplier", f"{rules['lift'].max():.1f}x", help="The highest lift score found.")
        col3.metric("📈 Highest Match Rate", f"{rules['confidence'].max():.0%}", help="The highest confidence probability.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- THE TWO-FACED TABS ---
        tab_biz, tab_viz, tab_tech = st.tabs(["💡 Marketing Strategies", "🕸️ Interactive Network", "🔬 Raw Math (Apriori Data)"])
        
        with tab_biz:
            st.markdown("### Top Cross-Selling Opportunities")
            st.markdown("Based on historical data, here is exactly what you should recommend to your customers to increase Average Order Value.")
            
            # Display the top 5 most actionable rules
            for i, row in rules.head(5).iterrows():
                ant = ', '.join(list(row['antecedents']))
                cons = ', '.join(list(row['consequents']))
                lift_val = row['lift']
                conf_val = row['confidence']
                
                st.markdown(f"""
                <div class="strategy-card">
                    <div class="strategy-title">Strategy #{i+1}: The "{ant}" Upsell</div>
                    <div class="strategy-text">
                        When a customer adds <b>{ant}</b> to their cart, immediately recommend <b>{cons}</b>.<br>
                        <i>Why? Customers are <b>{lift_val:.1f} times more likely</b> to buy {cons} when buying {ant}, with a match probability of {conf_val:.0%}.</i>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        with tab_viz:
            st.markdown("### Product Association Map")
            st.caption("A visual representation of how your products are connected. Thicker clusters indicate strong buying relationships.")
            if NETWORKX_AVAILABLE:
                render_network(rules.head(max_rules))
            else:
                st.info("Please install networkx (`pip install networkx`) for visualization.")
                
        with tab_tech:
            st.markdown("### Association Rules Dataframe")
            st.caption("The raw output of the machine learning model. Useful for detailed statistical analysis.")
            
            display = rules.head(max_rules).copy()
            display['antecedents'] = display['antecedents'].apply(lambda x: ', '.join(list(x)))
            display['consequents'] = display['consequents'].apply(lambda x: ', '.join(list(x)))
            display = display[['antecedents', 'consequents', 'support', 'confidence', 'lift']]
            
            # Rename for slight clarity but keep technical terms
            display.columns = ['Antecedent (If)', 'Consequent (Then)', 'Support', 'Confidence', 'Lift']
            
            # Format numbers beautifully
            display['Support'] = display['Support'].apply(lambda x: f"{x:.3f}")
            display['Confidence'] = display['Confidence'].apply(lambda x: f"{x:.1%}")
            display['Lift'] = display['Lift'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(display, use_container_width=True, hide_index=True)
            
    elif rules is None:
         st.info("Click 'Rerun Apriori Algorithm' above to start mining patterns.")


@st.cache_data(show_spinner=False)
def run_analysis(df, order_col, min_support, min_lift):
    try:
        # Group by order and product
        basket = df.groupby([order_col, 'product_name'])['quantity'].sum().unstack().fillna(0)
        
        # FYP Optimization: Vectorized binary conversion (Much faster than applymap)
        basket_binary = (basket > 0).astype(int)
        
        # Filter out extreme outliers to prevent memory crashes
        min_trans = max(1, int(len(basket_binary) * 0.005))
        valid_products = basket_binary.sum()[basket_binary.sum() >= min_trans].index
        basket_binary = basket_binary[valid_products]
        
        if len(basket_binary.columns) < 2:
            return pd.DataFrame()
        
        # Run Apriori
        frequent = apriori(basket_binary, min_support=min_support, use_colnames=True, max_len=3)
        if len(frequent) == 0:
            return pd.DataFrame()
        
        # Generate Rules
        rules = association_rules(frequent, metric="lift", min_threshold=min_lift)
        return rules.sort_values('lift', ascending=False).reset_index(drop=True)
        
    except Exception as e:
        st.error(f"Algorithm Error: {e}")
        return pd.DataFrame()


def render_network(rules):
    G = nx.Graph()
    
    # Dictionary to hold the full names for the hover tooltips
    hover_data = {}
    
    for _, row in rules.iterrows():
        ant_full = list(row['antecedents'])[0]
        cons_full = list(row['consequents'])[0]
        
        # Create a smart short name (first 2-3 words) instead of a blind cutoff
        ant_short = ' '.join(ant_full.split()[:3])
        cons_short = ' '.join(cons_full.split()[:3])
        
        G.add_edge(ant_short, cons_short, weight=row['lift'])
        
        # Store the full name for the interactive hover effect
        hover_data[ant_short] = ant_full
        hover_data[cons_short] = cons_full
    
    if len(G.nodes()) == 0:
        return
    
    # Optimize layout: k brings nodes closer together so it doesn't look so empty
    pos = nx.spring_layout(G, k=0.8, iterations=50, seed=42)
    
    edge_x, edge_y = [], []
    for e in G.edges():
        x0, y0 = pos[e[0]]
        x1, y1 = pos[e[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    node_x = [pos[n][0] for n in G.nodes()]
    node_y = [pos[n][1] for n in G.nodes()]
    
    # Create dynamic node sizes and rich hover text
    node_sizes = []
    hover_texts = []
    for node in G.nodes():
        connections = G.degree(node)
        # FYP Mic Drop: Scale node size by how many connections it has!
        node_sizes.append(18 + (connections * 6)) 
        hover_texts.append(f"<b>{hover_data[node]}</b><br>Tied to {connections} other bundle items")
    
    fig = go.Figure()
    
    # Draw edges (Brighter purple, slightly thicker)
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', 
                             line=dict(width=1.5, color='rgba(139, 92, 246, 0.7)'), 
                             hoverinfo='none'))
                             
    # Draw nodes (Neon cyan to pop off the dark background, white text)
    fig.add_trace(go.Scatter(x=node_x, y=node_y, mode='markers+text', 
                             text=list(G.nodes()), textposition='top center', 
                             textfont=dict(size=13, color='#ffffff', family="Inter"), 
                             marker=dict(size=node_sizes, color='#06b6d4', line=dict(width=2, color='#ffffff')),
                             hoverinfo='text',
                             hovertext=hover_texts))
                             
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      showlegend=False, height=600, margin=dict(t=30, b=30, l=30, r=30),
                      xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), 
                      yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                      
    st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()