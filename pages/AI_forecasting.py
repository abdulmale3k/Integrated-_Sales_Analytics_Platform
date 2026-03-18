"""
AI Forecasting Page
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import timedelta
from sidebar import create_sidebar  # <--- Importing your custom sidebar

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

st.set_page_config(page_title="AI Forecast", page_icon="🤖", layout="wide")

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
</style>
""", unsafe_allow_html=True)

CHART_THEME = {'paper_bgcolor': 'rgba(0,0,0,0)', 'plot_bgcolor': 'rgba(0,0,0,0)', 'font': {'color': '#a0a0a0'}, 'xaxis': {'gridcolor': 'rgba(255,255,255,0.1)'}, 'yaxis': {'gridcolor': 'rgba(255,255,255,0.1)'}}


def main():
    # === SIDEBAR ===
    create_sidebar()  # <--- Injecting the custom sidebar here
    
    st.markdown("<h1>🤖 AI-Powered Forecasting</h1>", unsafe_allow_html=True)
    st.caption("Predict future revenue with machine learning")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded.")
        st.stop()
    
    df = st.session_state['data']
    daily = df.groupby('order_date')['total_value'].sum().reset_index()
    daily = daily.set_index('order_date').resample('D').sum().reset_index().sort_values('order_date')
    
    if len(daily) < 14:
        st.warning(f"Need at least 14 days. You have {len(daily)}.")
        st.stop()
    
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📈 Forecast", "🏆 Model Arena"])
    
    with tab1:
        if st.session_state.get('model_results') is None:
            st.info("Train models in **Model Arena** tab first")
            if st.button("⚡ Quick Forecast", type="primary"):
                with st.spinner("Training..."):
                    results = train_models(daily)
                    st.session_state['model_results'] = results
                st.rerun()
        else:
            results = st.session_state['model_results']
            st.success(f"🏆 Using: **{results['champion_name']}**")
            
            forecast = generate_forecast(results['champion_model'], daily, results['feature_cols'], 30)
            
            fig = go.Figure()
            hist = daily.tail(60)
            fig.add_trace(go.Scatter(x=hist['order_date'], y=hist['total_value'], mode='lines', name='Historical', line=dict(color='#3b82f6', width=2)))
            fig.add_trace(go.Scatter(x=forecast['date'], y=forecast['value'], mode='lines', name='Forecast', line=dict(color='#10b981', width=2, dash='dash')))
            
            std = daily['total_value'].std() * 0.4
            fig.add_trace(go.Scatter(x=forecast['date'].tolist() + forecast['date'].tolist()[::-1], y=(forecast['value']+std).tolist() + (forecast['value']-std).clip(0).tolist()[::-1], fill='toself', fillcolor='rgba(16,185,129,0.1)', line=dict(color='rgba(0,0,0,0)'), name='Confidence'))
            
            fig.update_layout(**CHART_THEME, height=400, legend=dict(orientation='h', y=1.1), hovermode='x unified')
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            total = forecast['value'].sum()
            last30 = daily.tail(30)['total_value'].sum()
            growth = ((total - last30) / last30) * 100
            col1.metric("📈 30-Day Forecast", f"£{total:,.0f}")
            col2.metric("📊 Daily Avg", f"£{forecast['value'].mean():,.0f}")
            col3.metric("📉 vs Last 30 Days", f"{growth:+.1f}%")
    
    with tab2:
        if st.button("🏁 Train All Models", type="primary", use_container_width=True):
            progress = st.progress(0)
            with st.spinner("Training..."):
                results = train_models(daily, progress)
            progress.empty()
            st.session_state['model_results'] = results
            st.success("✅ Done!")
            st.rerun()
        
        if st.session_state.get('model_results'):
            results = st.session_state['model_results']
            st.markdown(f"### 🏆 Champion: **{results['champion_name']}**")
            
            display = results['results_df'].drop(columns=['predictions']).copy()
            display['R²'] = display['R² Score'].apply(lambda x: f"{x:.4f}")
            display['MAE'] = display['MAE'].apply(lambda x: f"£{x:,.0f}")
            display['RMSE'] = display['RMSE'].apply(lambda x: f"£{x:,.0f}")
            display['MAPE'] = display['MAPE'].apply(lambda x: f"{x:.1f}%")
            display['Time'] = display['Time'].apply(lambda x: f"{x:.2f}s")
            st.dataframe(display[['Model', 'R²', 'MAE', 'RMSE', 'MAPE', 'Time']], use_container_width=True, hide_index=True)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(y=results['y_test'].values, mode='lines', name='Actual', line=dict(color='white', width=3)))
            colors = ['#6366f1', '#ef4444', '#10b981', '#f59e0b']
            for i, row in results['results_df'].iterrows():
                fig.add_trace(go.Scatter(y=row['predictions'], mode='lines', name=row['Model'], line=dict(color=colors[i%4], width=2, dash='dash')))
            fig.update_layout(**CHART_THEME, height=350, legend=dict(orientation='h', y=1.1))
            st.plotly_chart(fig, use_container_width=True)


def train_models(daily, progress=None):
    df = daily.copy()
    df['day_index'] = np.arange(len(df))
    df['dow'] = df['order_date'].dt.dayofweek
    df['month'] = df['order_date'].dt.month
    df['weekend'] = df['dow'].isin([5,6]).astype(int)
    df['roll7'] = df['total_value'].rolling(7, min_periods=1).mean()
    df['roll30'] = df['total_value'].rolling(30, min_periods=1).mean()
    df['lag1'] = df['total_value'].shift(1).fillna(df['total_value'].mean())
    df['lag7'] = df['total_value'].shift(7).fillna(df['total_value'].mean())
    
    features = ['day_index', 'dow', 'month', 'weekend', 'roll7', 'roll30', 'lag1', 'lag7']
    X, y = df[features].fillna(0), df['total_value']
    split = int(len(df) * 0.8)
    X_train, X_test, y_train, y_test = X.iloc[:split], X.iloc[split:], y.iloc[:split], y.iloc[split:]
    
    models = {"Linear Regression": LinearRegression(), "Random Forest": RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42), "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)}
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBRegressor(n_estimators=100, max_depth=5, verbosity=0, random_state=42)
    
    results, trained = [], {}
    for i, (name, model) in enumerate(models.items()):
        if progress: progress.progress((i+1)/len(models))
        t0 = time.time()
        model.fit(X_train, y_train)
        pred = np.maximum(model.predict(X_test), 0)
        results.append({'Model': name, 'R² Score': r2_score(y_test, pred), 'MAE': mean_absolute_error(y_test, pred), 'RMSE': np.sqrt(mean_squared_error(y_test, pred)), 'MAPE': np.mean(np.abs((y_test - pred)/(y_test+1e-8)))*100, 'Time': time.time()-t0, 'predictions': pred})
        trained[name] = model
    
    results_df = pd.DataFrame(results)
    champion = results_df.loc[results_df['R² Score'].idxmax(), 'Model']
    return {'results_df': results_df, 'trained_models': trained, 'champion_name': champion, 'champion_model': trained[champion], 'feature_cols': features, 'y_test': y_test}


def generate_forecast(model, daily, features, days=30):
    last_date, last_idx = daily['order_date'].max(), len(daily)-1
    recent = daily['total_value'].tail(30).tolist()
    preds = []
    for i in range(1, days+1):
        d = last_date + timedelta(days=i)
        X = pd.DataFrame([{'day_index': last_idx+i, 'dow': d.weekday(), 'month': d.month, 'weekend': 1 if d.weekday()>=5 else 0, 'roll7': np.mean(recent[-7:]), 'roll30': np.mean(recent), 'lag1': recent[-1], 'lag7': recent[-7] if len(recent)>=7 else recent[-1]}])[features]
        p = max(0, model.predict(X)[0])
        preds.append({'date': d, 'value': p})
        recent.append(p)
        recent = recent[-30:]
    return pd.DataFrame(preds)


if __name__ == "__main__":
    main()
