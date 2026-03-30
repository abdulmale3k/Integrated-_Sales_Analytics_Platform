"""
AI Data Assistant Page - Powered directly by Google Gemini
"""

import streamlit as st
import pandas as pd
import time
from sidebar import create_sidebar

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

st.set_page_config(page_title="AI Assistant", page_icon="💬", layout="wide")

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
    
    /* Chat specific styling */
    [data-testid="stChatMessage"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,0.05);
    }
    
    [data-testid="stChatInput"] {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(139, 92, 246, 0.5) !important;
        color: white !important;
    }
    
    hr { border-color: rgba(255,255,255,0.1) !important; }
</style>
""", unsafe_allow_html=True)

def main():
    create_sidebar()

    st.markdown("<h1>💬 AI Data Assistant</h1>", unsafe_allow_html=True)
    st.caption("Ask complex questions about your sales data in plain English.")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please upload data on the Home page first.")
        st.stop()
        
    if not GENAI_AVAILABLE:
        st.error("❌ Google Generative AI SDK is not installed. Please run `pip install google-generativeai` in your terminal.")
        st.stop()
        
    df = st.session_state['data']
    
# Pull the API key silently from the hidden secrets file
    api_key = st.secrets["GEMINI_API_KEY"]
    st.markdown("---")

    
    # --- INITIALIZE CHAT MEMORY ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "model", "content": f"Hello! My AI brain is online. I've analyzed your {len(df):,} records. Ask me anything, like *'What is our total revenue?'* or *'How can we increase sales on our slowest days?'*"}
        ]

    # --- DISPLAY CHAT HISTORY ---
    for message in st.session_state.messages:
        # Streamlit uses "assistant", Gemini uses "model". We map it here for the UI.
        role = "assistant" if message["role"] == "model" else "user"
        with st.chat_message(role):
            st.markdown(message["content"])

    # --- CHAT INPUT ---
    if prompt := st.chat_input("Ask a question about your data..."):
        
        # 1. Add user message to memory and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing your spreadsheet and generating strategy..."):
                try:
                    # Configure the Gemini API
                    genai.configure(api_key=api_key)
                    
                    # --- DYNAMIC MODEL SELECTION ---
                    available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    
                    if not available_models:
                        st.error("Your API key doesn't have access to any text generation models. Check your Google AI account.")
                        st.stop()
                        
                    best_model = next((name for name in available_models if 'flash' in name.lower()), available_models[0])
                    model = genai.GenerativeModel(best_model)
                    
                    # --- PRE-CALCULATE COMPREHENSIVE BUSINESS INTELLIGENCE ---
                    total_rev = df['total_value'].sum()
                    total_orders = len(df)
                    aov = total_rev / total_orders if total_orders > 0 else 0
                    
                    if not pd.api.types.is_datetime64_any_dtype(df['order_date']):
                        df['order_date'] = pd.to_datetime(df['order_date'])
                    
                    df['DayOfWeek'] = df['order_date'].dt.day_name()
                    dow_sales = df.groupby('DayOfWeek')['total_value'].sum().sort_values(ascending=False)
                    best_day = dow_sales.index[0]
                    worst_day = dow_sales.index[-1]
                    
                    top_rev_products = df.groupby('product_name')['total_value'].sum().nlargest(5).to_string()
                    top_vol_products = df.groupby('product_name')['quantity'].sum().nlargest(5).to_string()
                    bottom_products = df.groupby('product_name')['total_value'].sum().nsmallest(3).to_string()

                    # --- THE MEGA CONTEXT PAYLOAD ---
                    context = f"""
                    You are an elite SME Business Consultant and Senior Data Analyst. 
                    You are advising the owner of this business based on their historical sales data.
                    
                    YOUR RULES:
                    1. Be authoritative, strategic, and encouraging. 
                    2. If asked for advice, DO NOT say you lack data. Use the Business Intelligence Brief below to formulate highly specific, actionable strategies (e.g., "Since Saturday is your best day, run promotions then" or "Bundle your top volume product with a high-margin item").
                    3. Keep your answers formatting clean using bullet points and bold text for readability.
                    4. Always refer to the user as "you" and their business as "your business".
                    
                    === COMPREHENSIVE BUSINESS INTELLIGENCE BRIEF ===
                    
                    CORE KPIs:
                    - Total Revenue: £{total_rev:,.2f}
                    - Total Orders/Transactions: {total_orders:,}
                    - Average Order Value (AOV): £{aov:,.2f}
                    - Data Date Range: {df['order_date'].min().strftime('%Y-%m-%d')} to {df['order_date'].max().strftime('%Y-%m-%d')}
                    
                    TEMPORAL TRENDS:
                    - Best Performing Day: {best_day}
                    - Worst Performing Day: {worst_day}
                    - Sales by Day of Week:
                    {dow_sales.to_string()}
                    
                    PRODUCT HEALTH:
                    - Top 5 Products (By Revenue - The Money Makers):
                    {top_rev_products}
                    
                    - Top 5 Products (By Quantity Sold - The Crowd Pleasers):
                    {top_vol_products}
                    
                    - Bottom 3 Products (Slow Movers / Dead Stock):
                    {bottom_products}
                    
                    USER QUESTION: {prompt}
                    """
                    
                    # Get the response from Gemini
                    response_obj = model.generate_content(context)
                    response = response_obj.text
                    
                    st.markdown(response)
                    
                except Exception as e:
                    response = f"I ran into an error connecting to the AI: {str(e)}"
                    st.error(response)
        
        # 3. Add assistant response to memory
        st.session_state.messages.append({"role": "model", "content": response})

if __name__ == "__main__":
    main()