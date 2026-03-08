"""
AI Forecasting Page
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import time
from datetime import timedelta

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

st.set_page_config(page_title="AI Forecast", page_icon="🤖", layout="wide")

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


def main():
    st.title("🤖 AI-Powered Forecasting")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please upload data from the Home page.")
        st.stop()
    
    df = st.session_state['data']
    
    # Prepare daily data
    daily = df.groupby('order_date')['total_value'].sum().reset_index()
    daily = daily.set_index('order_date').resample('D').sum().reset_index()
    daily = daily.sort_values('order_date')
    
    # Check minimum data
    if len(daily) < 14:
        st.warning(f"⚠️ Need at least 14 days of data for forecasting. You have {len(daily)} days.")
        st.stop()
    
    st.markdown("---")
    
    # === TABS ===
    tab1, tab2 = st.tabs(["📈 Forecast", "🏆 Model Comparison"])
    
    with tab1:
        display_forecast_tab(daily)
    
    with tab2:
        display_comparison_tab(daily)


def display_forecast_tab(daily):
    """Display the forecast visualization."""
    st.markdown("### 🔮 30-Day Revenue Forecast")
    
    # Check if model is trained
    if st.session_state.get('model_results') is None:
        st.info("💡 Train models first using the **Model Comparison** tab, or use Quick Forecast below.")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚡ Quick Forecast (Random Forest)", type="primary", use_container_width=True):
                with st.spinner("Training model..."):
                    results = train_models(daily)
                    st.session_state['model_results'] = results
                st.rerun()
        return
    
    results = st.session_state['model_results']
    
    st.success(f"🏆 Using champion model: **{results['champion_name']}**")
    
    # Generate forecast
    forecast = generate_forecast(
        results['champion_model'],
        daily,
        results['feature_cols'],
        days=30
    )
    
    # === VISUALIZATION ===
    fig = go.Figure()
    
    # Historical (last 60 days)
    hist = daily.tail(60)
    fig.add_trace(go.Scatter(
        x=hist['order_date'],
        y=hist['total_value'],
        mode='lines',
        name='Historical',
        line=dict(color='#3498db', width=2)
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast['date'],
        y=forecast['value'],
        mode='lines',
        name='Forecast',
        line=dict(color='#2ecc71', width=2, dash='dash')
    ))
    
    # Confidence band
    std = daily['total_value'].std() * 0.4
    upper = forecast['value'] + std
    lower = (forecast['value'] - std).clip(lower=0)
    
    fig.add_trace(go.Scatter(
        x=forecast['date'].tolist() + forecast['date'].tolist()[::-1],
        y=upper.tolist() + lower.tolist()[::-1],
        fill='toself',
        fillcolor='rgba(46, 204, 113, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Band',
        showlegend=True
    ))
    
    fig.update_layout(
        title=f"Revenue Forecast ({results['champion_name']})",
        xaxis_title="Date",
        yaxis_title="Revenue (£)",
        hovermode='x unified',
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # === METRICS ===
    st.markdown("### 📊 Forecast Summary")
    
    col1, col2, col3 = st.columns(3)
    
    total_forecast = forecast['value'].sum()
    last_30 = daily.tail(30)['total_value'].sum()
    growth = ((total_forecast - last_30) / last_30) * 100 if last_30 > 0 else 0
    
    with col1:
        st.metric("📈 Next 30 Days", f"£{total_forecast:,.0f}")
    
    with col2:
        st.metric("📊 Daily Average", f"£{forecast['value'].mean():,.0f}")
    
    with col3:
        delta_color = "normal" if growth >= 0 else "inverse"
        st.metric("📉 vs Last 30 Days", f"{growth:+.1f}%")
    
    # Download forecast
    st.markdown("---")
    st.download_button(
        "📥 Download Forecast Data (CSV)",
        forecast.to_csv(index=False),
        "revenue_forecast.csv",
        "text/csv"
    )


def display_comparison_tab(daily):
    """Display model comparison interface."""
    st.markdown("### 🥊 Model Comparison Arena")
    st.caption("Train multiple ML models and find the best one for your data")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🏁 Train All Models", type="primary", use_container_width=True):
            progress = st.progress(0, text="Initializing...")
            
            with st.spinner("Training models..."):
                results = train_models(daily, progress)
            
            progress.empty()
            st.session_state['model_results'] = results
            st.success("✅ Training complete!")
            st.rerun()
    
    # Display results if available
    if st.session_state.get('model_results'):
        results = st.session_state['model_results']
        
        st.markdown("---")
        st.markdown(f"### 🏆 Champion Model: **{results['champion_name']}**")
        
        # Results table
        st.markdown("#### 📊 Performance Comparison")
        
        display = results['results_df'].drop(columns=['predictions']).copy()
        display['R² Score'] = display['R² Score'].apply(lambda x: f"{x:.4f}")
        display['MAE'] = display['MAE'].apply(lambda x: f"£{x:,.0f}")
        display['RMSE'] = display['RMSE'].apply(lambda x: f"£{x:,.0f}")
        display['MAPE'] = display['MAPE'].apply(lambda x: f"{x:.1f}%")
        display['Time'] = display['Time'].apply(lambda x: f"{x:.2f}s")
        
        st.dataframe(display, use_container_width=True, hide_index=True)
        
        # Explanation
        with st.expander("ℹ️ Understanding the Metrics"):
            st.markdown("""
            | Metric | Description | Better |
            |--------|-------------|--------|
            | **R² Score** | How well model explains variance (0-1) | Higher |
            | **MAE** | Average prediction error | Lower |
            | **RMSE** | Root mean squared error (penalizes large errors) | Lower |
            | **MAPE** | Mean absolute percentage error | Lower |
            | **Time** | Training time | Lower |
            """)
        
        # Comparison chart
        st.markdown("#### 📈 Predictions vs Actual (Test Set)")
        
        fig = go.Figure()
        
        # Actual values
        fig.add_trace(go.Scatter(
            y=results['y_test'].values,
            mode='lines',
            name='Actual',
            line=dict(color='black', width=3)
        ))
        
        # Model predictions
        colors = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6']
        for idx, row in results['results_df'].iterrows():
            fig.add_trace(go.Scatter(
                y=row['predictions'],
                mode='lines',
                name=row['Model'],
                line=dict(color=colors[idx % len(colors)], width=2, dash='dash')
            ))
        
        fig.update_layout(
            height=350,
            xaxis_title="Day",
            yaxis_title="Revenue (£)",
            hovermode='x unified',
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)


def train_models(daily, progress=None):
    """Train all forecasting models."""
    # Feature engineering
    df = daily.copy()
    df['day_index'] = np.arange(len(df))
    df['day_of_week'] = df['order_date'].dt.dayofweek
    df['month'] = df['order_date'].dt.month
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['rolling_7d'] = df['total_value'].rolling(7, min_periods=1).mean()
    df['rolling_30d'] = df['total_value'].rolling(30, min_periods=1).mean()
    df['lag_1'] = df['total_value'].shift(1).fillna(df['total_value'].mean())
    df['lag_7'] = df['total_value'].shift(7).fillna(df['total_value'].mean())
    
    features = [
        'day_index', 'day_of_week', 'month', 'is_weekend',
        'rolling_7d', 'rolling_30d', 'lag_1', 'lag_7'
    ]
    
    X = df[features].fillna(0)
    y = df['total_value']
    
    # Time-based split (80/20)
    split = int(len(df) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = y.iloc[:split], y.iloc[split:]
    
    # Define models
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100, max_depth=5, random_state=42
        )
    }
    
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBRegressor(
            n_estimators=100, max_depth=5, verbosity=0, random_state=42
        )
    
    results = []
    trained = {}
    
    for idx, (name, model) in enumerate(models.items()):
        if progress:
            progress.progress((idx + 1) / len(models), text=f"Training {name}...")
        
        start = time.time()
        model.fit(X_train, y_train)
        train_time = time.time() - start
        
        pred = np.maximum(model.predict(X_test), 0)
        
        results.append({
            'Model': name,
            'R² Score': r2_score(y_test, pred),
            'MAE': mean_absolute_error(y_test, pred),
            'RMSE': np.sqrt(mean_squared_error(y_test, pred)),
            'MAPE': np.mean(np.abs((y_test - pred) / (y_test + 1e-8))) * 100,
            'Time': train_time,
            'predictions': pred
        })
        trained[name] = model
    
    results_df = pd.DataFrame(results)
    champion = results_df.loc[results_df['R² Score'].idxmax(), 'Model']
    
    return {
        'results_df': results_df,
        'trained_models': trained,
        'champion_name': champion,
        'champion_model': trained[champion],
        'feature_cols': features,
        'y_test': y_test
    }


def generate_forecast(model, daily, features, days=30):
    """Generate future forecast."""
    last_date = daily['order_date'].max()
    last_idx = len(daily) - 1
    recent = daily['total_value'].tail(30).values.tolist()
    
    predictions = []
    
    for i in range(1, days + 1):
        date = last_date + timedelta(days=i)
        
        X = pd.DataFrame([{
            'day_index': last_idx + i,
            'day_of_week': date.weekday(),
            'month': date.month,
            'is_weekend': 1 if date.weekday() >= 5 else 0,
            'rolling_7d': np.mean(recent[-7:]) if len(recent) >= 7 else np.mean(recent),
            'rolling_30d': np.mean(recent),
            'lag_1': recent[-1],
            'lag_7': recent[-7] if len(recent) >= 7 else recent[-1]
        }])[features]
        
        pred = max(0, model.predict(X)[0])
        predictions.append({'date': date, 'value': pred})
        
        # Update recent for next iteration
        recent.append(pred)
        if len(recent) > 30:
            recent = recent[-30:]
    
    return pd.DataFrame(predictions)


if __name__ == "__main__":
    main()
else:
    main()