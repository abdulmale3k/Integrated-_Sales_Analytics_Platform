import streamlit as st

def create_sidebar():
    with st.sidebar:
        # 1. The Light/Dark Mode Toggle
        st.markdown("### 🎨 Theme Settings")
        dark_mode = st.toggle("🌙 Dark Mode", value=True)
        st.markdown("---")

        # 2. Define the CSS Variables based on the toggle state
        if dark_mode:
            theme_vars = """
            :root {
                --bg-primary: #0a0a0f;
                --bg-secondary: #12121a;
                --bg-card: rgba(255, 255, 255, 0.05);
                --text-primary: #ffffff;
                --text-secondary: #8b8b9e;
                --border-color: rgba(255, 255, 255, 0.1);
                --gradient-purple: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
                --gradient-mesh: 
                    radial-gradient(at 40% 20%, rgba(139, 92, 246, 0.15) 0px, transparent 50%),
                    radial-gradient(at 80% 0%, rgba(6, 182, 212, 0.1) 0px, transparent 50%),
                    radial-gradient(at 0% 50%, rgba(236, 72, 153, 0.1) 0px, transparent 50%),
                    radial-gradient(at 80% 50%, rgba(59, 130, 246, 0.1) 0px, transparent 50%);
                --border-radius: 16px;
                --header-gradient: linear-gradient(135deg, #ffffff 0%, #a78bfa 50%, #06b6d4 100%);
            }
            """
        else:
            theme_vars = """
            :root {
                --bg-primary: #f8fafc;
                --bg-secondary: #e2e8f0;
                --bg-card: rgba(0, 0, 0, 0.03);
                --text-primary: #0f172a;
                --text-secondary: #64748b;
                --border-color: rgba(0, 0, 0, 0.1);
                --gradient-purple: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
                --gradient-mesh: 
                    radial-gradient(at 40% 20%, rgba(139, 92, 246, 0.08) 0px, transparent 50%),
                    radial-gradient(at 80% 0%, rgba(6, 182, 212, 0.05) 0px, transparent 50%),
                    radial-gradient(at 0% 50%, rgba(236, 72, 153, 0.05) 0px, transparent 50%),
                    radial-gradient(at 80% 50%, rgba(59, 130, 246, 0.05) 0px, transparent 50%);
                --border-radius: 16px;
                --header-gradient: linear-gradient(135deg, #4c1d95 0%, #3b82f6 50%, #06b6d4 100%);
            }
            """

        # 3. Inject the Unified Global CSS
        st.markdown(f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');
            
            {theme_vars}
            
            /* 1. Safely hide extra fluff, but LEAVE HEADER ALONE */
            #MainMenu, footer {{ display: none !important; }}
            
            /* Make the native header transparent so it blends perfectly */
            [data-testid="stHeader"] {{ background-color: transparent !important; }}
            
            /* Ensure the toggle text/icon uses theme text color */
            [data-testid="stHeader"] * {{ color: var(--text-primary) !important; }}

            /* 2. Fix the Main Background */
            .stApp {{
                background-color: var(--bg-primary) !important;
                background-image: var(--gradient-mesh) !important;
                background-attachment: fixed !important;
                font-family: 'Inter', sans-serif !important;
            }}
            
            /* Force Streamlit's stubborn inner containers to be transparent */
            div[data-testid="stAppViewContainer"], 
            div[data-testid="stAppViewBlockContainer"] {{
                background: transparent !important;
                background-color: transparent !important;
            }}
            
            /* 3. Fix the Sidebar Background */
            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%) !important;
                border-right: 1px solid var(--border-color) !important;
            }}
            
            /* 4. Hide Streamlit's default sidebar text links (so we can use our custom buttons) */
            [data-testid="stSidebarNav"] {{ display: none !important; }}

            /* 5. Fix Custom Buttons */
            div[data-testid="stButton"] button {{
                background: var(--gradient-purple) !important;
                color: white !important; /* Keep button text white for contrast against purple */
                border: none !important;
                border-radius: 8px !important;
                padding: 0.5rem 1rem !important;
                box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3) !important;
                transition: all 0.3s ease !important;
            }}
            div[data-testid="stButton"] button:hover {{
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 25px rgba(139, 92, 246, 0.5) !important;
            }}
            div[data-testid="stButton"] button p {{
                color: white !important;
                font-weight: 600 !important;
            }}
            
            /* 6. Fix Typography */
            h1, h2, h3, h4, p, span {{ color: var(--text-primary); }}
            h1 {{
                background: var(--header-gradient) !important;
                -webkit-background-clip: text !important;
                -webkit-text-fill-color: transparent !important;
                background-clip: text !important;
            }}
            
            /* 7. Fix Upload Card Visibility */
            .glass-card {{
                background: var(--bg-card) !important;
                backdrop-filter: blur(10px) !important;
                border: 1px solid var(--border-color) !important;
                border-radius: var(--border-radius) !important;
                padding: 1.5rem !important;
            }}
            [data-testid="stFileUploader"] {{
                background: var(--bg-card) !important;
                border: 2px dashed rgba(139, 92, 246, 0.5) !important;
                border-radius: 12px !important;
            }}
            .metric-value {{ font-family: 'JetBrains Mono', monospace !important; color: var(--text-primary) !important; }}
            .metric-label {{ color: var(--text-secondary) !important; }}
            
            /* 8. Fix Tabs Visibility */
            .stTabs [data-baseweb="tab-list"] {{
                background: var(--bg-card) !important;
                border-radius: 12px !important;
                padding: 0.5rem !important;
            }}
            .stTabs [data-baseweb="tab"] {{ background: transparent !important; }}
            .stTabs [data-baseweb="tab"] p {{ color: var(--text-secondary) !important; }}
            .stTabs [aria-selected="true"] {{
                background: var(--gradient-purple) !important;
                border-radius: 8px !important;
            }}
            .stTabs [aria-selected="true"] p {{
                color: white !important;
                font-weight: 600 !important;
            }}
            .stTabs [data-baseweb="tab-highlight"] {{ display: none !important; }}
        </style>
        """, unsafe_allow_html=True)

        # 4. Sidebar Content
        st.markdown("""
        <div style="padding: 1rem 0;">
            <h2 style="margin: 0; font-size: 1.4rem;">📈 SME Analytics</h2>
            <p style="margin: 0.25rem 0 0 0; font-size: 0.7rem; color: var(--text-secondary);">Enterprise Analytics Platform</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Data Status Block
        if st.session_state.get('data') is not None:
            df = st.session_state['data']
            st.markdown('<div style="background: rgba(16, 185, 129, 0.15); color: #10b981; padding: 0.5rem 1rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; display: inline-block;">Data Loaded</div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="margin-top: 1rem; padding: 1rem; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border-color);">
                <div style="font-size: 1.5rem; font-weight: 700; color: var(--text-primary);">{len(df):,}</div>
                <div style="font-size: 0.75rem; color: var(--text-secondary);">Total Records</div>
                <div style="margin-top: 0.5rem; font-size: 0.7rem; color: var(--text-secondary);">
                    📅 {df['order_date'].min().strftime('%b %d')} → {df['order_date'].max().strftime('%b %d, %Y')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🗑️ Clear Data", use_container_width=True):
                for key in ['data', 'raw_df', 'basket_rules', 'model_results', 'pdf_buffer']:
                    st.session_state[key] = None
                st.switch_page("app.py")
        else:
            st.markdown("""
            <div style="padding: 1.5rem; background: var(--bg-card); border-radius: 12px; text-align: center; border: 1px solid var(--border-color);">
                <div style="font-size: 2rem;">📁</div>
                <div style="font-size: 0.8rem; color: var(--text-secondary);">No data loaded</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation Links
        st.markdown("""
        <div style="font-size: 0.7rem; color: var(--text-secondary);">
            <div style="margin-bottom: 0.5rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em;">Navigation</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🏠 Home (Upload)", use_container_width=True, key="nav_home"):
            st.switch_page("app.py")
        if st.button("📊 Dashboard", use_container_width=True, key="nav_dash"):
            st.switch_page("pages/Dashboard.py")
        if st.button("📦 Products", use_container_width=True, key="nav_prod"):
            st.switch_page("pages/Products.py")
        if st.button("📋 Product Analysis", use_container_width=True, key="nav_abc"):
            st.switch_page("pages/Product_Analysis.py")
        if st.button("🛒 Basket Analysis", use_container_width=True, key="nav_basket"):
            st.switch_page("pages/Basket_Analysis.py")
        if st.button("🤖 AI Forecast", use_container_width=True, key="nav_ai"):
            st.switch_page("pages/AI_Forecasting.py")
        if st.button("💬 AI Assistant", use_container_width=True, key="nav_chat"):
            st.switch_page("pages/AI_Assistant.py")
        if st.button("📄 Reports", use_container_width=True, key="nav_reports"):
            st.switch_page("pages/Reports.py")