"""
SME Sales Analytics Platform
============================
A comprehensive analytics solution for small and medium enterprises.

Features:
- Auto-detection of column formats
- Data quality analysis
- Market basket analysis
- AI model comparison (Linear Regression, Random Forest, Gradient Boosting, XGBoost)
- Professional PDF reporting
- Interactive visualizations

Author: SME Analytics Team
Version: 2.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import time
from datetime import datetime, timedelta

# Machine Learning
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# XGBoost
try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

# Market Basket Analysis
try:
    from mlxtend.frequent_patterns import apriori, association_rules
    from mlxtend.preprocessing import TransactionEncoder
    MLXTEND_AVAILABLE = True
except ImportError:
    MLXTEND_AVAILABLE = False

# PDF Generation
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, Image, PageBreak, HRFlowable
)
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# Network visualization for basket analysis
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

# --- CONFIGURATION ---
st.set_page_config(
    page_title="SME Analytics Platform", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
</style>
""", unsafe_allow_html=True)


# --- COLUMN ALIASES ---
# The system looks for these names to auto-map columns
COLUMN_ALIASES = {
    "order_date": [
        "InvoiceDate", "invoice_date", "date", "Order Date", "order_date",
        "time", "Date", "TransactionDate", "transaction_date", "sale_date", "SaleDate"
    ],
    "product_name": [
        "Description", "description", "Product Name", "product_name", 
        "Item", "item", "ProductName", "product", "Product", "ItemName", "item_name"
    ],
    "quantity": [
        "Quantity", "quantity", "qty", "Qty", "Count", "count", 
        "Units", "units", "Amount", "amount"
    ],
    "unit_price": [
        "UnitPrice", "unit_price", "Price", "price", "Cost", "cost",
        "Unit Price", "ItemPrice", "item_price", "SalePrice", "sale_price"
    ],
    "transaction_id": [
        "InvoiceNo", "invoice_no", "Invoice", "invoice", "OrderID", "order_id",
        "TransactionID", "transaction_id", "Order ID", "Transaction ID",
        "InvoiceNumber", "invoice_number", "OrderNumber", "order_number"
    ],
    "customer_id": [
        "CustomerID", "customer_id", "Customer ID", "Customer", "customer",
        "ClientID", "client_id", "Client ID", "BuyerID", "buyer_id"
    ]
}

REQUIRED_COLUMNS = ["order_date", "product_name", "quantity", "unit_price"]
OPTIONAL_COLUMNS = ["transaction_id", "customer_id"]


# --- HELPER FUNCTIONS ---

def auto_detect_columns(columns):
    """
    Scans dataframe columns to automatically match them to system requirements.
    
    Args:
        columns: List of column names from the uploaded dataframe
        
    Returns:
        tuple: (mapping dict, list of missing required columns, list of found optional columns)
    """
    mapping = {}
    missing = []
    found_optional = []
    lower_cols = {c.lower().strip(): c for c in columns}
    
    # Check required columns
    for target in REQUIRED_COLUMNS:
        found = False
        possible_names = COLUMN_ALIASES[target]
        for alias in possible_names:
            if alias.lower() in lower_cols:
                mapping[target] = lower_cols[alias.lower()]
                found = True
                break
        if not found:
            missing.append(target)
    
    # Check optional columns
    for target in OPTIONAL_COLUMNS:
        possible_names = COLUMN_ALIASES[target]
        for alias in possible_names:
            if alias.lower() in lower_cols:
                mapping[target] = lower_cols[alias.lower()]
                found_optional.append(target)
                break
    
    return mapping, missing, found_optional


@st.cache_data(show_spinner=False)
def load_data(file):
    """
    Universal loader for CSV and Excel files with multiple encoding fallbacks.
    
    Args:
        file: Uploaded file object from Streamlit
        
    Returns:
        pd.DataFrame or None
    """
    try:
        if file.name.endswith('.csv'):
            # Try different encodings
            encodings = ['utf-8', 'ISO-8859-1', 'cp1252', 'latin1']
            for encoding in encodings:
                try:
                    file.seek(0)  # Reset file pointer
                    return pd.read_csv(file, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode CSV with any standard encoding")
        
        elif file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file)
        
        else:
            raise ValueError(f"Unsupported file type: {file.name}")
            
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def calculate_data_quality_metrics(df):
    """
    Calculate comprehensive data quality metrics.
    
    Args:
        df: Cleaned dataframe
        
    Returns:
        dict: Dictionary containing various quality metrics
    """
    metrics = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'date_range_days': (df['order_date'].max() - df['order_date'].min()).days,
        'unique_products': df['product_name'].nunique(),
        'total_revenue': df['total_value'].sum(),
        'avg_order_value': df['total_value'].mean(),
        'median_order_value': df['total_value'].median(),
        'min_date': df['order_date'].min(),
        'max_date': df['order_date'].max(),
    }
    
    # Check for transaction_id
    if 'transaction_id' in df.columns:
        metrics['unique_transactions'] = df['transaction_id'].nunique()
    
    # Check for customer_id
    if 'customer_id' in df.columns:
        metrics['unique_customers'] = df['customer_id'].nunique()
    
    return metrics


def detect_outliers(df, column='total_value'):
    """
    Detect outliers using IQR method.
    
    Args:
        df: Dataframe
        column: Column to check for outliers
        
    Returns:
        pd.DataFrame: Rows containing outliers
    """
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    return outliers


def perform_basket_analysis(df, min_support=0.02, min_threshold=1.0):
    """
    Perform market basket analysis using Apriori algorithm.
    
    Args:
        df: Dataframe with transaction_id and product_name columns
        min_support: Minimum support threshold for frequent itemsets
        min_threshold: Minimum lift threshold for association rules
        
    Returns:
        tuple: (frequent_itemsets DataFrame, association_rules DataFrame, basket DataFrame)
    """
    if 'transaction_id' not in df.columns:
        return None, None, None
    
    try:
        # Create basket format
        basket = df.groupby(['transaction_id', 'product_name'])['quantity'].sum().unstack().fillna(0)
        
        # Convert to binary (bought or not)
        basket_binary = basket.applymap(lambda x: 1 if x > 0 else 0)
        
        # Filter products that appear in at least 1% of transactions
        min_transactions = max(1, int(len(basket_binary) * 0.01))
        product_counts = basket_binary.sum()
        valid_products = product_counts[product_counts >= min_transactions].index
        basket_binary = basket_binary[valid_products]
        
        if len(basket_binary.columns) < 2:
            return None, None, None
        
        # Generate frequent itemsets
        frequent_items = apriori(
            basket_binary, 
            min_support=min_support, 
            use_colnames=True,
            max_len=3  # Limit to 3-item combinations for performance
        )
        
        if len(frequent_items) == 0:
            return frequent_items, None, basket_binary
        
        # Generate association rules
        rules = association_rules(
            frequent_items, 
            metric="lift", 
            min_threshold=min_threshold
        )
        rules = rules.sort_values('lift', ascending=False)
        
        return frequent_items, rules, basket_binary
        
    except Exception as e:
        st.error(f"Error in basket analysis: {str(e)}")
        return None, None, None


def train_forecasting_models(daily_data, test_size=0.2):
    """
    Train multiple forecasting models and compare performance.
    
    Args:
        daily_data: DataFrame with daily aggregated sales
        test_size: Proportion of data to use for testing
        
    Returns:
        dict: Results containing model performances and predictions
    """
    # Feature engineering
    df = daily_data.copy()
    df['day_index'] = np.arange(len(df))
    df['day_of_week'] = df['order_date'].dt.dayofweek
    df['month'] = df['order_date'].dt.month
    df['day_of_month'] = df['order_date'].dt.day
    df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
    df['is_month_start'] = df['order_date'].dt.is_month_start.astype(int)
    df['is_month_end'] = df['order_date'].dt.is_month_end.astype(int)
    
    # Rolling features
    df['rolling_7d'] = df['total_value'].rolling(7, min_periods=1).mean()
    df['rolling_30d'] = df['total_value'].rolling(30, min_periods=1).mean()
    df['rolling_7d_std'] = df['total_value'].rolling(7, min_periods=1).std().fillna(0)
    
    # Lag features
    df['lag_1'] = df['total_value'].shift(1).fillna(df['total_value'].mean())
    df['lag_7'] = df['total_value'].shift(7).fillna(df['total_value'].mean())
    
    feature_cols = [
        'day_index', 'day_of_week', 'month', 'day_of_month',
        'is_weekend', 'is_month_start', 'is_month_end',
        'rolling_7d', 'rolling_30d', 'rolling_7d_std',
        'lag_1', 'lag_7'
    ]
    
    # Prepare data
    X = df[feature_cols].fillna(0)
    y = df['total_value']
    
    # Time-based split (not random!)
    split_idx = int(len(df) * (1 - test_size))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    
    # Define models
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(
            n_estimators=100, 
            max_depth=10, 
            random_state=42,
            n_jobs=-1
        ),
        "Gradient Boosting": GradientBoostingRegressor(
            n_estimators=100, 
            max_depth=5, 
            learning_rate=0.1,
            random_state=42
        )
    }
    
    if XGBOOST_AVAILABLE:
        models["XGBoost"] = XGBRegressor(
            n_estimators=100, 
            max_depth=5, 
            learning_rate=0.1,
            random_state=42,
            verbosity=0
        )
    
    results = []
    trained_models = {}
    
    for name, model in models.items():
        start_time = time.time()
        
        # Train
        model.fit(X_train, y_train)
        train_time = time.time() - start_time
        
        # Predict
        y_pred = model.predict(X_test)
        y_pred = np.maximum(y_pred, 0)  # No negative revenue
        
        # Metrics
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-8))) * 100
        
        results.append({
            'Model': name,
            'R² Score': r2,
            'MAE': mae,
            'RMSE': rmse,
            'MAPE (%)': mape,
            'Train Time (s)': train_time,
            'predictions': y_pred
        })
        
        trained_models[name] = model
    
    # Find champion
    results_df = pd.DataFrame(results)
    champion_idx = results_df['R² Score'].idxmax()
    champion_name = results_df.iloc[champion_idx]['Model']
    
    return {
        'results_df': results_df,
        'trained_models': trained_models,
        'champion_name': champion_name,
        'champion_model': trained_models[champion_name],
        'feature_cols': feature_cols,
        'X_test': X_test,
        'y_test': y_test,
        'test_dates': df.iloc[split_idx:]['order_date'].values
    }


def generate_future_forecast(model, daily_data, feature_cols, days=30):
    """
    Generate future forecasts using the trained model.
    
    Args:
        model: Trained model
        daily_data: Historical daily data
        feature_cols: List of feature column names
        days: Number of days to forecast
        
    Returns:
        pd.DataFrame: Future predictions with dates
    """
    last_date = daily_data['order_date'].max()
    last_idx = len(daily_data) - 1
    
    # Get recent values for rolling calculations
    recent_values = daily_data['total_value'].tail(30).values
    
    future_predictions = []
    
    for i in range(1, days + 1):
        future_date = last_date + timedelta(days=i)
        
        # Calculate features
        features = {
            'day_index': last_idx + i,
            'day_of_week': future_date.weekday(),
            'month': future_date.month,
            'day_of_month': future_date.day,
            'is_weekend': 1 if future_date.weekday() in [5, 6] else 0,
            'is_month_start': 1 if future_date.day == 1 else 0,
            'is_month_end': 1 if (future_date + timedelta(days=1)).day == 1 else 0,
            'rolling_7d': np.mean(recent_values[-7:]) if len(recent_values) >= 7 else np.mean(recent_values),
            'rolling_30d': np.mean(recent_values[-30:]) if len(recent_values) >= 30 else np.mean(recent_values),
            'rolling_7d_std': np.std(recent_values[-7:]) if len(recent_values) >= 7 else 0,
            'lag_1': recent_values[-1] if len(recent_values) > 0 else 0,
            'lag_7': recent_values[-7] if len(recent_values) >= 7 else recent_values[-1]
        }
        
        X_future = pd.DataFrame([features])[feature_cols]
        pred = max(0, model.predict(X_future)[0])
        
        future_predictions.append({
            'order_date': future_date,
            'total_value': pred,
            'Type': 'Forecast'
        })
        
        # Update recent values for next iteration
        recent_values = np.append(recent_values, pred)[-30:]
    
    return pd.DataFrame(future_predictions)


def generate_enhanced_pdf(df, metrics, fig_trend_bytes, top_products, basket_rules=None, model_results=None):
    """
    Generate a comprehensive, professional PDF report.
    
    Args:
        df: Cleaned dataframe
        metrics: Dictionary of calculated metrics
        fig_trend_bytes: Bytes of the trend chart image
        top_products: DataFrame of top products
        basket_rules: DataFrame of association rules (optional)
        model_results: Dictionary of model comparison results (optional)
        
    Returns:
        BytesIO: PDF file buffer
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4, 
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#1a5276'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#566573'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=13,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        leading=14
    )
    
    # === COVER PAGE ===
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("📈 Sales Analytics Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        subtitle_style
    ))
    story.append(Spacer(1, 0.3*inch))
    
    # Horizontal line
    story.append(HRFlowable(
        width="80%",
        thickness=2,
        color=colors.HexColor('#1a5276'),
        spaceBefore=10,
        spaceAfter=30
    ))
    
    story.append(Paragraph(
        f"Analysis Period: {metrics['min_date'].strftime('%B %d, %Y')} to {metrics['max_date'].strftime('%B %d, %Y')}",
        subtitle_style
    ))
    
    story.append(Spacer(1, 0.5*inch))
    
    # Executive summary box
    summary_text = f"""
    <b>Executive Summary</b><br/><br/>
    This report provides a comprehensive analysis of sales performance over {metrics['date_range_days']} days.
    Total revenue of <b>£{metrics['total_revenue']:,.2f}</b> was generated across 
    <b>{metrics['total_rows']:,}</b> transactions, with <b>{metrics['unique_products']:,}</b> unique products sold.
    """
    story.append(Paragraph(summary_text, body_style))
    
    story.append(PageBreak())
    
    # === PAGE 2: KEY METRICS ===
    story.append(Paragraph("Key Performance Indicators", heading_style))
    
    # Metrics table
    metrics_data = [
        ['Metric', 'Value', 'Description'],
        ['Total Revenue', f"£{metrics['total_revenue']:,.2f}", 'Sum of all transaction values'],
        ['Total Transactions', f"{metrics['total_rows']:,}", 'Number of individual sales'],
        ['Average Order Value', f"£{metrics['avg_order_value']:,.2f}", 'Mean transaction value'],
        ['Median Order Value', f"£{metrics['median_order_value']:,.2f}", 'Middle transaction value'],
        ['Unique Products', f"{metrics['unique_products']:,}", 'Distinct products sold'],
        ['Analysis Period', f"{metrics['date_range_days']} days", 'Date range coverage'],
    ]
    
    # Add optional metrics
    if 'unique_transactions' in metrics:
        metrics_data.append(['Unique Orders', f"{metrics['unique_transactions']:,}", 'Distinct order/invoice numbers'])
    if 'unique_customers' in metrics:
        metrics_data.append(['Unique Customers', f"{metrics['unique_customers']:,}", 'Distinct customer IDs'])
    
    metrics_table = Table(metrics_data, colWidths=[1.8*inch, 1.5*inch, 2.5*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8f9fa'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6'))
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 0.4*inch))
    
    # Sales trend chart
    story.append(Paragraph("Sales Trend Over Time", heading_style))
    
    if fig_trend_bytes:
        img = Image(io.BytesIO(fig_trend_bytes), width=6.5*inch, height=3.5*inch)
        story.append(img)
    
    story.append(PageBreak())
    
    # === PAGE 3: PRODUCT ANALYSIS ===
    story.append(Paragraph("Product Performance Analysis", heading_style))
    story.append(Paragraph(
        "Top performing products ranked by total revenue contribution:",
        body_style
    ))
    story.append(Spacer(1, 0.2*inch))
    
    product_data = [['Rank', 'Product Name', 'Revenue', '% of Total', 'Qty Sold']]
    
    for idx, row in top_products.head(15).iterrows():
        pct = (row['total_value'] / metrics['total_revenue']) * 100
        product_name = str(row['product_name'])[:45]  # Truncate long names
        if len(str(row['product_name'])) > 45:
            product_name += "..."
        
        qty = row.get('quantity', 'N/A')
        qty_str = f"{qty:,.0f}" if isinstance(qty, (int, float)) else str(qty)
        
        product_data.append([
            str(idx + 1),
            product_name,
            f"£{row['total_value']:,.2f}",
            f"{pct:.1f}%",
            qty_str
        ])
    
    product_table = Table(product_data, colWidths=[0.5*inch, 3*inch, 1*inch, 0.8*inch, 0.7*inch])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
    ]))
    
    story.append(product_table)
    
    # === PAGE 4: BASKET ANALYSIS (if available) ===
    if basket_rules is not None and len(basket_rules) > 0:
        story.append(PageBreak())
        story.append(Paragraph("Market Basket Analysis", heading_style))
        story.append(Paragraph(
            "Products frequently purchased together. Use these insights for bundling strategies and cross-promotions:",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        basket_data = [['If Customer Buys...', 'They Also Buy...', 'Confidence', 'Lift']]
        
        for _, row in basket_rules.head(12).iterrows():
            ant = ', '.join([str(x)[:25] for x in list(row['antecedents'])])
            cons = ', '.join([str(x)[:25] for x in list(row['consequents'])])
            
            basket_data.append([
                ant[:35] + ('...' if len(ant) > 35 else ''),
                cons[:35] + ('...' if len(cons) > 35 else ''),
                f"{row['confidence']:.0%}",
                f"{row['lift']:.2f}x"
            ])
        
        basket_table = Table(basket_data, colWidths=[2.2*inch, 2.2*inch, 0.9*inch, 0.7*inch])
        basket_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(basket_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        story.append(Paragraph("💡 Actionable Recommendations", subheading_style))
        
        for idx, row in basket_rules.head(3).iterrows():
            ant = ', '.join([str(x) for x in list(row['antecedents'])])
            cons = ', '.join([str(x) for x in list(row['consequents'])])
            rec_text = f"• <b>Bundle Opportunity:</b> Customers who buy <i>{ant[:50]}</i> are <b>{row['lift']:.1f}x</b> more likely to also purchase <i>{cons[:50]}</i>. Consider creating a promotional bundle."
            story.append(Paragraph(rec_text, body_style))
    
    # === PAGE 5: AI MODEL COMPARISON (if available) ===
    if model_results is not None:
        story.append(PageBreak())
        story.append(Paragraph("AI Forecasting Model Comparison", heading_style))
        story.append(Paragraph(
            "Multiple machine learning models were trained and evaluated to find the best forecasting approach:",
            body_style
        ))
        story.append(Spacer(1, 0.2*inch))
        
        results_df = model_results['results_df']
        
        model_data = [['Model', 'R² Score', 'MAE (£)', 'RMSE (£)', 'MAPE (%)']]
        
        for _, row in results_df.iterrows():
            model_data.append([
                row['Model'],
                f"{row['R² Score']:.3f}",
                f"£{row['MAE']:,.2f}",
                f"£{row['RMSE']:,.2f}",
                f"{row['MAPE (%)']:.1f}%"
            ])
        
        model_table = Table(model_data, colWidths=[1.5*inch, 1*inch, 1.2*inch, 1.2*inch, 1*inch])
        model_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(model_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Champion callout
        champion_text = f"<b>🏆 Champion Model: {model_results['champion_name']}</b> - Selected based on highest R² score, indicating best fit for this dataset."
        story.append(Paragraph(champion_text, body_style))
    
    # === FINAL PAGE: FOOTER ===
    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor('#bdc3c7'),
        spaceBefore=20,
        spaceAfter=10
    ))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Italic'],
        fontSize=9,
        textColor=colors.HexColor('#7f8c8d'),
        alignment=TA_CENTER
    )
    
    story.append(Paragraph(
        "This report was automatically generated by SME Analytics Platform.<br/>"
        "For questions or support, contact your analytics administrator.",
        footer_style
    ))
    story.append(Paragraph(
        "<b>Confidential</b> - For Internal Use Only",
        footer_style
    ))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


# --- MAIN APPLICATION ---

def main():
    """Main application entry point."""
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=80)
        st.title("SME Analytics")
        st.markdown("---")
        
        st.markdown("### 📁 Data Status")
        if st.session_state.get('data') is not None:
            df = st.session_state['data']
            st.success(f"✅ {len(df):,} records loaded")
            st.caption(f"Period: {df['order_date'].min().date()} to {df['order_date'].max().date()}")
        else:
            st.info("No data loaded")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.caption(
            "SME Analytics Platform v2.0\n\n"
            "Features:\n"
            "• Auto column detection\n"
            "• Market basket analysis\n"
            "• AI model comparison\n"
            "• Professional PDF reports"
        )
        
        # Library status
        st.markdown("---")
        st.markdown("### 🔧 Library Status")
        
        libs = {
            "XGBoost": XGBOOST_AVAILABLE,
            "MLxtend (Basket)": MLXTEND_AVAILABLE,
            "NetworkX": NETWORKX_AVAILABLE
        }
        
        for lib, available in libs.items():
            if available:
                st.caption(f"✅ {lib}")
            else:
                st.caption(f"❌ {lib}")
    
    # Main content
    st.markdown('<h1 class="main-header">📈 SME Sales Analytics Platform</h1>', unsafe_allow_html=True)
    
    # Initialize Session State
    if 'data' not in st.session_state:
        st.session_state['data'] = None
    if 'raw_df' not in st.session_state:
        st.session_state['raw_df'] = None
    if 'final_mapping' not in st.session_state:
        st.session_state['final_mapping'] = {}
    if 'basket_rules' not in st.session_state:
        st.session_state['basket_rules'] = None
    if 'model_results' not in st.session_state:
        st.session_state['model_results'] = None

    # --- STEP 1: DATA INGESTION ---
    st.markdown("## 📥 Step 1: Data Ingestion")
    
    col_upload, col_info = st.columns([2, 1])
    
    with col_upload:
        uploaded_file = st.file_uploader(
            "Upload your sales data file",
            type=['csv', 'xlsx', 'xls'],
            help="Supported formats: CSV, Excel (.xlsx, .xls)"
        )
    
    with col_info:
        with st.expander("ℹ️ Expected Columns"):
            st.markdown("""
            **Required:**
            - `order_date` - Transaction date
            - `product_name` - Item description
            - `quantity` - Units sold
            - `unit_price` - Price per unit
            
            **Optional (for advanced features):**
            - `transaction_id` - Invoice/Order number
            - `customer_id` - Customer identifier
            """)
    
    if uploaded_file is not None:
        try:
            # Load raw data
            with st.spinner('📂 Reading file...'):
                if st.session_state.get('last_file') != uploaded_file.name:
                    st.session_state['raw_df'] = load_data(uploaded_file)
                    st.session_state['last_file'] = uploaded_file.name
                    st.session_state['data'] = None  # Reset processed data
                    st.session_state['basket_rules'] = None
                    st.session_state['model_results'] = None
                
                df_raw = st.session_state['raw_df']
            
            if df_raw is None:
                st.error("Failed to load file. Please check the format.")
                return
            
            st.success(f"📄 Loaded {len(df_raw):,} rows × {len(df_raw.columns)} columns")
            
            # Auto-Detect Logic
            detected_map, missing_cols, found_optional = auto_detect_columns(df_raw.columns)
            final_mapping = {}
            
            # Show detection results
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔍 Column Detection Results")
                
                if len(missing_cols) == 0:
                    st.success("✅ All required columns auto-detected!")
                    final_mapping = detected_map
                else:
                    st.warning(f"⚠️ Could not auto-detect: **{', '.join(missing_cols)}**")
                
                if found_optional:
                    st.info(f"📋 Optional columns found: **{', '.join(found_optional)}**")
            
            with col2:
                st.markdown("#### 📊 Raw Data Preview")
                st.dataframe(df_raw.head(5), use_container_width=True)
            
            # Column mapping UI
            st.markdown("---")
            st.markdown("#### 🔧 Column Mapping")
            
            if len(missing_cols) == 0:
                # Show auto-detected mapping
                mapping_df = pd.DataFrame([
                    {"System Field": k, "Mapped To": v, "Status": "✅ Auto"}
                    for k, v in detected_map.items()
                ])
                st.dataframe(mapping_df, use_container_width=True, hide_index=True)
                
                process_button = st.button("🚀 Confirm & Process Data", type="primary", use_container_width=True)
            else:
                # Manual mapping required
                st.markdown("Please map the missing columns:")
                
                cols = st.columns(2)
                for i, target in enumerate(REQUIRED_COLUMNS):
                    options = ["-- Select --"] + list(df_raw.columns)
                    default_idx = 0
                    
                    if target in detected_map:
                        default_idx = options.index(detected_map[target])
                    
                    with cols[i % 2]:
                        selection = st.selectbox(
                            f"📌 {target.replace('_', ' ').title()}",
                            options,
                            index=default_idx,
                            key=f"map_{target}"
                        )
                        if selection != "-- Select --":
                            final_mapping[target] = selection
                
                # Optional columns
                st.markdown("**Optional columns:**")
                cols_opt = st.columns(2)
                for i, target in enumerate(OPTIONAL_COLUMNS):
                    options = ["-- Skip --"] + list(df_raw.columns)
                    default_idx = 0
                    
                    if target in detected_map:
                        default_idx = options.index(detected_map[target])
                    
                    with cols_opt[i % 2]:
                        selection = st.selectbox(
                            f"📌 {target.replace('_', ' ').title()} (optional)",
                            options,
                            index=default_idx,
                            key=f"map_{target}"
                        )
                        if selection != "-- Skip --":
                            final_mapping[target] = selection
                
                # Validate mapping
                all_required_mapped = all(col in final_mapping for col in REQUIRED_COLUMNS)
                
                if all_required_mapped:
                    process_button = st.button("🚀 Process Data", type="primary", use_container_width=True)
                else:
                    st.warning("Please map all required columns to continue.")
                    process_button = False

            # Processing Logic
            if process_button:
                with st.spinner('⚙️ Processing data...'):
                    progress = st.progress(0)
                    
                    # 1. Rename columns
                    progress.progress(10, "Renaming columns...")
                    rename_map = {v: k for k, v in final_mapping.items()}
                    df_clean = df_raw.rename(columns=rename_map)
                    
                    # Keep only mapped columns
                    cols_to_keep = [k for k in final_mapping.keys() if k in df_clean.columns]
                    df_clean = df_clean[cols_to_keep].copy()
                    
                    # 2. Convert numeric types
                    progress.progress(30, "Converting data types...")
                    df_clean['quantity'] = pd.to_numeric(df_clean['quantity'], errors='coerce')
                    df_clean['unit_price'] = pd.to_numeric(df_clean['unit_price'], errors='coerce')
                    
                    # 3. Calculate total value
                    progress.progress(50, "Calculating revenue...")
                    df_clean['total_value'] = df_clean['quantity'] * df_clean['unit_price']
                    
                    # 4. Convert dates
                    progress.progress(70, "Parsing dates...")
                    df_clean['order_date'] = pd.to_datetime(df_clean['order_date'], errors='coerce')
                    
                    # 5. Clean invalid data
                    progress.progress(85, "Removing invalid records...")
                    initial_count = len(df_clean)
                    
                    df_clean = df_clean[df_clean['quantity'] > 0]
                    df_clean = df_clean[df_clean['unit_price'] > 0]
                    df_clean = df_clean.dropna(subset=['order_date', 'quantity', 'unit_price'])
                    
                    removed_count = initial_count - len(df_clean)
                    
                    # 6. Save to session state
                    progress.progress(100, "Complete!")
                    st.session_state['data'] = df_clean
                    st.session_state['final_mapping'] = final_mapping
                    
                    # Clear previous analysis
                    st.session_state['basket_rules'] = None
                    st.session_state['model_results'] = None
                    
                    st.success(f"✅ Successfully processed **{len(df_clean):,}** valid transactions!")
                    
                    if removed_count > 0:
                        st.info(f"ℹ️ Removed {removed_count:,} invalid records (negative values, missing data, etc.)")
                    
                    time.sleep(0.5)
                    st.rerun()

        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            st.exception(e)

    # --- DASHBOARD (Only show when data is loaded) ---
    if st.session_state['data'] is not None:
        df = st.session_state['data']
        
        st.markdown("---")
        
        # === DATA QUALITY SUMMARY ===
        with st.expander("📋 Data Quality Summary", expanded=False):
            metrics = calculate_data_quality_metrics(df)
            
            # Top metrics row
            metric_cols = st.columns(5)
            
            metric_cols[0].metric("📊 Total Records", f"{metrics['total_rows']:,}")
            metric_cols[1].metric("📅 Date Range", f"{metrics['date_range_days']} days")
            metric_cols[2].metric("📦 Unique Products", f"{metrics['unique_products']:,}")
            metric_cols[3].metric("💰 Total Revenue", f"£{metrics['total_revenue']:,.2f}")
            metric_cols[4].metric("📈 Avg Order Value", f"£{metrics['avg_order_value']:,.2f}")
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("##### 📝 Column Information")
                col_info = pd.DataFrame({
                    'Column': df.columns,
                    'Data Type': df.dtypes.astype(str).values,
                    'Non-Null Count': df.count().values,
                    'Null Count': df.isnull().sum().values
                })
                st.dataframe(col_info, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("##### 📊 Numerical Statistics")
                st.dataframe(
                    df.describe().round(2),
                    use_container_width=True
                )
            
            # Outlier detection
            st.markdown("##### 🔍 Outlier Analysis")
            outliers = detect_outliers(df, 'total_value')
            
            if len(outliers) > 0:
                outlier_pct = (len(outliers) / len(df)) * 100
                st.warning(f"Found **{len(outliers):,}** potential outliers ({outlier_pct:.2f}% of data)")
                
                with st.expander("View outliers"):
                    st.dataframe(outliers.head(50), use_container_width=True)
            else:
                st.success("✅ No significant outliers detected")
            
            # Data preview
            st.markdown("##### 📄 Data Preview")
            st.dataframe(df.head(100), use_container_width=True)
        
        st.markdown("---")
        
        # === MAIN DASHBOARD TABS ===
        if 'transaction_id' in df.columns and MLXTEND_AVAILABLE:
            tabs = st.tabs(["📊 Overview", "📦 Products", "🛒 Basket Analysis", "🤖 AI Forecast"])
            has_basket_tab = True
        else:
            tabs = st.tabs(["📊 Overview", "📦 Products", "🤖 AI Forecast"])
            has_basket_tab = False
        
        # === TAB 1: OVERVIEW ===
        with tabs[0]:
            st.markdown("### 📊 Sales Overview")
            
            # Calculate metrics
            total_rev = df['total_value'].sum()
            total_orders = len(df)
            avg_order_value = df['total_value'].mean()
            
            # Top row metrics
            m1, m2, m3, m4 = st.columns(4)
            
            m1.metric(
                "💰 Total Revenue",
                f"£{total_rev:,.2f}"
            )
            m2.metric(
                "🧾 Transactions",
                f"{total_orders:,}"
            )
            m3.metric(
                "📊 Avg Order Value",
                f"£{avg_order_value:,.2f}"
            )
            m4.metric(
                "📦 Unique Products",
                f"{df['product_name'].nunique():,}"
            )
            
            st.markdown("---")
            
            # Sales trend chart
            st.markdown("#### 📈 Revenue Trend")
            
            daily = df.groupby('order_date')['total_value'].sum().reset_index()
            daily = daily.sort_values('order_date')
            
            # Add moving average
            daily['MA_7'] = daily['total_value'].rolling(7, min_periods=1).mean()
            daily['MA_30'] = daily['total_value'].rolling(30, min_periods=1).mean()
            
            fig_trend = go.Figure()
            
            fig_trend.add_trace(go.Scatter(
                x=daily['order_date'],
                y=daily['total_value'],
                mode='lines',
                name='Daily Revenue',
                line=dict(color='#3498db', width=1),
                opacity=0.6
            ))
            
            fig_trend.add_trace(go.Scatter(
                x=daily['order_date'],
                y=daily['MA_7'],
                mode='lines',
                name='7-Day Average',
                line=dict(color='#e74c3c', width=2)
            ))
            
            fig_trend.add_trace(go.Scatter(
                x=daily['order_date'],
                y=daily['MA_30'],
                mode='lines',
                name='30-Day Average',
                line=dict(color='#2ecc71', width=2)
            ))
            
            fig_trend.update_layout(
                title='Daily Revenue with Moving Averages',
                xaxis_title='Date',
                yaxis_title='Revenue (£)',
                hovermode='x unified',
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                height=400
            )
            
            st.plotly_chart(fig_trend, use_container_width=True)
            
            # Store for PDF
            st.session_state['fig_trend'] = fig_trend
            
            # Two column layout for additional charts
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📅 Revenue by Day of Week")
                df['day_of_week'] = df['order_date'].dt.day_name()
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                
                dow_sales = df.groupby('day_of_week')['total_value'].sum().reindex(day_order)
                
                fig_dow = px.bar(
                    x=dow_sales.index,
                    y=dow_sales.values,
                    labels={'x': 'Day', 'y': 'Revenue (£)'},
                    color=dow_sales.values,
                    color_continuous_scale='Blues'
                )
                fig_dow.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig_dow, use_container_width=True)
            
            with col2:
                st.markdown("#### 📆 Revenue by Month")
                df['month'] = df['order_date'].dt.to_period('M').astype(str)
                monthly = df.groupby('month')['total_value'].sum().reset_index()
                
                fig_monthly = px.bar(
                    monthly,
                    x='month',
                    y='total_value',
                    labels={'month': 'Month', 'total_value': 'Revenue (£)'},
                    color='total_value',
                    color_continuous_scale='Greens'
                )
                fig_monthly.update_layout(showlegend=False, height=300, xaxis_tickangle=-45)
                st.plotly_chart(fig_monthly, use_container_width=True)
            
            st.markdown("---")
            
            # PDF Generation
            st.markdown("#### 📄 Generate Report")
            
            col_pdf1, col_pdf2 = st.columns([1, 2])
            
            with col_pdf1:
                if st.button("📑 Generate Professional PDF Report", type="primary", use_container_width=True):
                    with st.spinner("📝 Creating comprehensive report..."):
                        try:
                            # Prepare data for PDF
                            metrics = calculate_data_quality_metrics(df)
                            
                            # Get trend chart as image
                            fig_trend_bytes = fig_trend.to_image(format='png', width=800, height=400)
                            
                            # Get top products
                            top_products = df.groupby('product_name').agg({
                                'total_value': 'sum',
                                'quantity': 'sum'
                            }).reset_index().sort_values('total_value', ascending=False)
                            
                            # Generate PDF
                            pdf_buffer = generate_enhanced_pdf(
                                df=df,
                                metrics=metrics,
                                fig_trend_bytes=fig_trend_bytes,
                                top_products=top_products,
                                basket_rules=st.session_state.get('basket_rules'),
                                model_results=st.session_state.get('model_results')
                            )
                            
                            st.session_state['pdf_ready'] = pdf_buffer
                            st.success("✅ Report generated successfully!")
                            
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
            
            with col_pdf2:
                if st.session_state.get('pdf_ready'):
                    st.download_button(
                        label="⬇️ Download Executive Report (PDF)",
                        data=st.session_state['pdf_ready'],
                        file_name=f"Sales_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        
        # === TAB 2: PRODUCTS ===
        with tabs[1]:
            st.markdown("### 📦 Product Analysis")
            
            # Product metrics
            prod_metrics = df.groupby('product_name').agg({
                'total_value': 'sum',
                'quantity': 'sum',
                'unit_price': 'mean'
            }).reset_index()
            
            prod_metrics.columns = ['Product', 'Total Revenue', 'Total Quantity', 'Avg Price']
            prod_metrics = prod_metrics.sort_values('Total Revenue', ascending=False)
            prod_metrics['Revenue %'] = (prod_metrics['Total Revenue'] / prod_metrics['Total Revenue'].sum() * 100).round(2)
            
            # Top metrics
            col1, col2, col3 = st.columns(3)
            
            col1.metric("🏆 Top Product", prod_metrics.iloc[0]['Product'][:30])
            col2.metric("💎 Top Revenue", f"£{prod_metrics.iloc[0]['Total Revenue']:,.2f}")
            col3.metric("📊 Revenue Share", f"{prod_metrics.iloc[0]['Revenue %']:.1f}%")
            
            st.markdown("---")
            
            # Visualization options
            chart_col, table_col = st.columns([1, 1])
            
            with chart_col:
                st.markdown("#### 📊 Top 15 Products by Revenue")
                
                top_n = prod_metrics.head(15).copy()
                top_n['Product_Short'] = top_n['Product'].str[:30]
                
                fig_products = px.bar(
                    top_n,
                    x='Total Revenue',
                    y='Product_Short',
                    orientation='h',
                    color='Total Revenue',
                    color_continuous_scale='Viridis',
                    labels={'Product_Short': 'Product', 'Total Revenue': 'Revenue (£)'}
                )
                
                fig_products.update_layout(
                    yaxis=dict(autorange="reversed"),
                    showlegend=False,
                    height=500
                )
                
                st.plotly_chart(fig_products, use_container_width=True)
            
            with table_col:
                st.markdown("#### 📋 Product Performance Table")
                
                display_df = prod_metrics.head(20).copy()
                display_df['Total Revenue'] = display_df['Total Revenue'].apply(lambda x: f"£{x:,.2f}")
                display_df['Total Quantity'] = display_df['Total Quantity'].apply(lambda x: f"{x:,.0f}")
                display_df['Avg Price'] = display_df['Avg Price'].apply(lambda x: f"£{x:.2f}")
                display_df['Revenue %'] = display_df['Revenue %'].apply(lambda x: f"{x:.1f}%")
                
                st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
            
            st.markdown("---")
            
            # Product distribution
            st.markdown("#### 📈 Revenue Distribution Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Pareto chart (80/20 rule)
                cumsum = prod_metrics['Total Revenue'].cumsum() / prod_metrics['Total Revenue'].sum() * 100
                n_products_80 = (cumsum <= 80).sum()
                
                st.info(f"📊 **Pareto Analysis:** {n_products_80} products ({n_products_80/len(prod_metrics)*100:.1f}%) generate 80% of revenue")
                
                fig_pareto = go.Figure()
                
                fig_pareto.add_trace(go.Bar(
                    x=list(range(len(prod_metrics))),
                    y=prod_metrics['Total Revenue'].values,
                    name='Revenue',
                    marker_color='steelblue'
                ))
                
                fig_pareto.add_trace(go.Scatter(
                    x=list(range(len(prod_metrics))),
                    y=cumsum.values,
                    mode='lines',
                    name='Cumulative %',
                    yaxis='y2',
                    line=dict(color='red', width=2)
                ))
                
                fig_pareto.update_layout(
                    title='Revenue Pareto Chart',
                    xaxis_title='Products (ranked)',
                    yaxis_title='Revenue (£)',
                    yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 100]),
                    height=350,
                    showlegend=True
                )
                
                st.plotly_chart(fig_pareto, use_container_width=True)
            
            with col2:
                # Price vs Quantity scatter
                st.markdown("##### Price vs. Quantity Sold")
                
                fig_scatter = px.scatter(
                    prod_metrics.head(50),
                    x='Avg Price',
                    y='Total Quantity',
                    size='Total Revenue',
                    color='Total Revenue',
                    hover_name='Product',
                    color_continuous_scale='Viridis',
                    labels={'Avg Price': 'Average Price (£)', 'Total Quantity': 'Quantity Sold'}
                )
                
                fig_scatter.update_layout(height=350)
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Download product data
            st.markdown("---")
            csv_products = prod_metrics.to_csv(index=False)
            st.download_button(
                "📥 Download Product Analysis (CSV)",
                csv_products,
                "product_analysis.csv",
                "text/csv",
                use_container_width=False
            )
        
        # === TAB 3: BASKET ANALYSIS (if available) ===
        if has_basket_tab:
            with tabs[2]:
                st.markdown("### 🛒 Market Basket Analysis")
                st.caption("Discover which products are frequently bought together")
                
                if not MLXTEND_AVAILABLE:
                    st.error("❌ MLxtend library not installed. Run: `pip install mlxtend`")
                elif 'transaction_id' not in df.columns:
                    st.warning("⚠️ Transaction ID column not found. Cannot perform basket analysis.")
                else:
                    # Parameters
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        min_support = st.slider(
                            "Minimum Support",
                            min_value=0.005,
                            max_value=0.1,
                            value=0.02,
                            step=0.005,
                            help="Minimum frequency of item combinations"
                        )
                    
                    with col2:
                        min_lift = st.slider(
                            "Minimum Lift",
                            min_value=1.0,
                            max_value=5.0,
                            value=1.2,
                            step=0.1,
                            help="Minimum lift value (>1 indicates positive association)"
                        )
                    
                    with col3:
                        max_rules = st.slider(
                            "Max Rules to Show",
                            min_value=10,
                            max_value=100,
                            value=30,
                            step=10
                        )
                    
                    if st.button("🔍 Run Basket Analysis", type="primary"):
                        with st.spinner("⚙️ Mining association patterns..."):
                            frequent_items, rules, basket = perform_basket_analysis(
                                df, 
                                min_support=min_support,
                                min_threshold=min_lift
                            )
                        
                        if rules is None or len(rules) == 0:
                            st.warning("⚠️ No significant patterns found. Try lowering the minimum support or lift values.")
                        else:
                            st.session_state['basket_rules'] = rules
                            
                            # Display metrics
                            st.success(f"✅ Found **{len(rules):,}** association rules!")
                            
                            m1, m2, m3, m4 = st.columns(4)
                            m1.metric("Patterns Found", len(rules))
                            m2.metric("Avg Confidence", f"{rules['confidence'].mean():.1%}")
                            m3.metric("Avg Lift", f"{rules['lift'].mean():.2f}x")
                            m4.metric("Max Lift", f"{rules['lift'].max():.2f}x")
                            
                            st.markdown("---")
                            
                            # Display rules
                            st.markdown("#### 🎯 Top Association Rules")
                            
                            rules_display = rules.head(max_rules).copy()
                            rules_display['antecedents'] = rules_display['antecedents'].apply(
                                lambda x: ', '.join([str(i)[:40] for i in list(x)])
                            )
                            rules_display['consequents'] = rules_display['consequents'].apply(
                                lambda x: ', '.join([str(i)[:40] for i in list(x)])
                            )
                            
                            rules_display = rules_display[[
                                'antecedents', 'consequents', 'support', 
                                'confidence', 'lift'
                            ]].copy()
                            
                            rules_display.columns = [
                                'If Customer Buys...', 'They Also Buy...', 
                                'Support', 'Confidence', 'Lift'
                            ]
                            
                            rules_display['Support'] = rules_display['Support'].apply(lambda x: f"{x:.3f}")
                            rules_display['Confidence'] = rules_display['Confidence'].apply(lambda x: f"{x:.1%}")
                            rules_display['Lift'] = rules_display['Lift'].apply(lambda x: f"{x:.2f}x")
                            
                            st.dataframe(rules_display, use_container_width=True, hide_index=True)
                            
                            st.markdown("---")
                            
                            # Network visualization
                            if NETWORKX_AVAILABLE and len(rules) >= 3:
                                st.markdown("#### 🕸️ Product Association Network")
                                
                                # Build network graph
                                G = nx.Graph()
                                
                                for _, row in rules.head(20).iterrows():
                                    for ant in row['antecedents']:
                                        for cons in row['consequents']:
                                            G.add_edge(
                                                str(ant)[:25], 
                                                str(cons)[:25], 
                                                weight=row['lift']
                                            )
                                
                                if len(G.nodes()) > 0:
                                    pos = nx.spring_layout(G, k=2, iterations=50, seed=42)
                                    
                                    # Create edges
                                    edge_x = []
                                    edge_y = []
                                    for edge in G.edges():
                                        x0, y0 = pos[edge[0]]
                                        x1, y1 = pos[edge[1]]
                                        edge_x.extend([x0, x1, None])
                                        edge_y.extend([y0, y1, None])
                                    
                                    edge_trace = go.Scatter(
                                        x=edge_x, y=edge_y,
                                        line=dict(width=1, color='#888'),
                                        hoverinfo='none',
                                        mode='lines'
                                    )
                                    
                                    # Create nodes
                                    node_x = [pos[node][0] for node in G.nodes()]
                                    node_y = [pos[node][1] for node in G.nodes()]
                                    
                                    node_trace = go.Scatter(
                                        x=node_x, y=node_y,
                                        mode='markers+text',
                                        hoverinfo='text',
                                        text=list(G.nodes()),
                                        textposition='top center',
                                        marker=dict(
                                            size=20,
                                            color='#1f77b4',
                                            line=dict(width=2, color='white')
                                        )
                                    )
                                    
                                    fig_network = go.Figure(
                                        data=[edge_trace, node_trace],
                                        layout=go.Layout(
                                            showlegend=False,
                                            hovermode='closest',
                                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                                            height=500
                                        )
                                    )
                                    
                                    st.plotly_chart(fig_network, use_container_width=True)
                            
                            st.markdown("---")
                            
                            # Actionable recommendations
                            st.markdown("#### 💡 Actionable Recommendations")
                            
                            for idx, row in rules.head(5).iterrows():
                                ant = ', '.join([str(x)[:40] for x in list(row['antecedents'])])
                                cons = ', '.join([str(x)[:40] for x in list(row['consequents'])])
                                
                                st.info(
                                    f"**Bundle Opportunity:** Customers who buy *{ant}* are "
                                    f"**{row['lift']:.1f}x** more likely to also buy *{cons}* "
                                    f"(Confidence: {row['confidence']:.0%}). "
                                    f"Consider creating a promotional bundle or cross-sell recommendation."
                                )
        
        # === TAB 4 (or 3): AI FORECAST ===
        forecast_tab_idx = 3 if has_basket_tab else 2
        
        with tabs[forecast_tab_idx]:
            st.markdown("### 🤖 AI-Powered Forecasting")
            
            forecast_subtabs = st.tabs(["📈 Revenue Forecast", "🏆 Model Comparison"])
            
            # Prepare daily data
            daily_data = df.groupby('order_date')['total_value'].sum().reset_index()
            daily_data = daily_data.set_index('order_date').resample('D').sum().reset_index()
            daily_data = daily_data.sort_values('order_date')
            
            with forecast_subtabs[0]:
                st.markdown("#### 🔮 30-Day Revenue Forecast")
                
                if len(daily_data) < 14:
                    st.warning("⚠️ Need at least 14 days of data for reliable forecasting.")
                else:
                    # Check if we have trained models
                    if st.session_state.get('model_results') is None:
                        st.info("💡 Run the Model Comparison first to see forecasts with the best model.")
                        
                        # Quick forecast with default model
                        if st.button("🚀 Quick Forecast (Linear Regression)"):
                            with st.spinner("Training model..."):
                                results = train_forecasting_models(daily_data)
                                st.session_state['model_results'] = results
                                st.rerun()
                    else:
                        results = st.session_state['model_results']
                        champion_model = results['champion_model']
                        champion_name = results['champion_name']
                        
                        st.success(f"🏆 Using champion model: **{champion_name}**")
                        
                        # Generate forecast
                        forecast_df = generate_future_forecast(
                            model=champion_model,
                            daily_data=daily_data,
                            feature_cols=results['feature_cols'],
                            days=30
                        )
                        
                        # Combine historical and forecast
                        daily_data_plot = daily_data.copy()
                        daily_data_plot['Type'] = 'Historical'
                        
                        combined = pd.concat([
                            daily_data_plot.tail(90)[['order_date', 'total_value', 'Type']],
                            forecast_df
                        ])
                        
                        # Create visualization
                        fig_forecast = go.Figure()
                        
                        historical = combined[combined['Type'] == 'Historical']
                        forecast = combined[combined['Type'] == 'Forecast']
                        
                        fig_forecast.add_trace(go.Scatter(
                            x=historical['order_date'],
                            y=historical['total_value'],
                            mode='lines',
                            name='Historical',
                            line=dict(color='#3498db', width=2)
                        ))
                        
                        fig_forecast.add_trace(go.Scatter(
                            x=forecast['order_date'],
                            y=forecast['total_value'],
                            mode='lines',
                            name='Forecast',
                            line=dict(color='#2ecc71', width=2, dash='dash')
                        ))
                        
                        # Add confidence band (simple approximation)
                        forecast_values = forecast['total_value'].values
                        std_dev = daily_data['total_value'].std() * 0.5
                        
                        fig_forecast.add_trace(go.Scatter(
                            x=forecast['order_date'].tolist() + forecast['order_date'].tolist()[::-1],
                            y=(forecast_values + std_dev).tolist() + (forecast_values - std_dev).tolist()[::-1],
                            fill='toself',
                            fillcolor='rgba(46, 204, 113, 0.2)',
                            line=dict(color='rgba(255,255,255,0)'),
                            name='Confidence Band'
                        ))
                        
                        fig_forecast.update_layout(
                            title=f'30-Day Revenue Forecast (Using {champion_name})',
                            xaxis_title='Date',
                            yaxis_title='Revenue (£)',
                            hovermode='x unified',
                            height=450
                        )
                        
                        st.plotly_chart(fig_forecast, use_container_width=True)
                        
                        # Forecast metrics
                        col1, col2, col3 = st.columns(3)
                        
                        total_forecast = forecast_df['total_value'].sum()
                        avg_forecast = forecast_df['total_value'].mean()
                        last_30_actual = daily_data.tail(30)['total_value'].sum()
                        
                        col1.metric(
                            "📈 Predicted Revenue (Next 30 Days)",
                            f"£{total_forecast:,.2f}"
                        )
                        col2.metric(
                            "📊 Daily Average Forecast",
                            f"£{avg_forecast:,.2f}"
                        )
                        
                        growth = ((total_forecast - last_30_actual) / last_30_actual) * 100
                        col3.metric(
                            "📉 vs Last 30 Days",
                            f"{growth:+.1f}%",
                            delta=f"£{total_forecast - last_30_actual:,.2f}"
                        )
                        
                        # Download forecast
                        csv_forecast = forecast_df.to_csv(index=False)
                        st.download_button(
                            "📥 Download Forecast Data (CSV)",
                            csv_forecast,
                            "revenue_forecast.csv",
                            "text/csv"
                        )
            
            with forecast_subtabs[1]:
                st.markdown("#### 🥊 AI Model Comparison Arena")
                st.caption("Compare multiple machine learning algorithms to find the best forecasting model")
                
                if len(daily_data) < 30:
                    st.warning("⚠️ Need at least 30 days of data for meaningful model comparison.")
                else:
                    if st.button("🏁 Start Model Training", type="primary", use_container_width=True):
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        status_text.text("Preparing features...")
                        progress_bar.progress(10)
                        
                        with st.spinner("Training models..."):
                            results = train_forecasting_models(daily_data)
                        
                        progress_bar.progress(100)
                        status_text.empty()
                        progress_bar.empty()
                        
                        st.session_state['model_results'] = results
                        st.success("✅ Model training complete!")
                        st.rerun()
                    
                    if st.session_state.get('model_results') is not None:
                        results = st.session_state['model_results']
                        results_df = results['results_df']
                        
                        st.markdown("---")
                        
                        # Champion announcement
                        st.markdown(f"### 🏆 Champion Model: **{results['champion_name']}**")
                        
                        # Results table with highlighting
                        st.markdown("#### 📊 Model Performance Comparison")
                        
                        display_results = results_df.drop(columns=['predictions']).copy()
                        display_results['R² Score'] = display_results['R² Score'].apply(lambda x: f"{x:.4f}")
                        display_results['MAE'] = display_results['MAE'].apply(lambda x: f"£{x:,.2f}")
                        display_results['RMSE'] = display_results['RMSE'].apply(lambda x: f"£{x:,.2f}")
                        display_results['MAPE (%)'] = display_results['MAPE (%)'].apply(lambda x: f"{x:.2f}%")
                        display_results['Train Time (s)'] = display_results['Train Time (s)'].apply(lambda x: f"{x:.3f}s")
                        
                        st.dataframe(display_results, use_container_width=True, hide_index=True)
                        
                        # Metric descriptions
                        with st.expander("📖 Understanding the Metrics"):
                            st.markdown("""
                            | Metric | Description | Better Value |
                            |--------|-------------|--------------|
                            | **R² Score** | How well the model explains variance in data (0-1) | Higher is better (closer to 1) |
                            | **MAE** | Mean Absolute Error - average prediction error | Lower is better |
                            | **RMSE** | Root Mean Squared Error - penalizes large errors more | Lower is better |
                            | **MAPE** | Mean Absolute Percentage Error | Lower is better |
                            | **Train Time** | Time to train the model | Lower is better (for production) |
                            """)
                        
                        st.markdown("---")
                        
                        # Visual comparison
                        st.markdown("#### 📈 Prediction Comparison on Test Set")
                        
                        fig_compare = go.Figure()
                        
                        # Actual values
                        fig_compare.add_trace(go.Scatter(
                            x=list(range(len(results['y_test']))),
                            y=results['y_test'].values,
                            mode='lines',
                            name='Actual',
                            line=dict(color='black', width=3)
                        ))
                        
                        # Model predictions
                        colors_list = ['#3498db', '#e74c3c', '#2ecc71', '#9b59b6']
                        
                        for idx, row in results_df.iterrows():
                            fig_compare.add_trace(go.Scatter(
                                x=list(range(len(row['predictions']))),
                                y=row['predictions'],
                                mode='lines',
                                name=row['Model'],
                                line=dict(color=colors_list[idx % len(colors_list)], width=2, dash='dash'),
                                opacity=0.8
                            ))
                        
                        fig_compare.update_layout(
                            title='Model Predictions vs Actual Values (Test Set)',
                            xaxis_title='Day',
                            yaxis_title='Revenue (£)',
                            hovermode='x unified',
                            height=450,
                            legend=dict(orientation='h', yanchor='bottom', y=1.02)
                        )
                        
                        st.plotly_chart(fig_compare, use_container_width=True)
                        
                        # Feature importance (for tree-based models)
                        if results['champion_name'] in ['Random Forest', 'Gradient Boosting', 'XGBoost']:
                            st.markdown("---")
                            st.markdown("#### 🎯 Feature Importance Analysis")
                            st.caption("Which factors most influence the predictions")
                            
                            champion_model = results['champion_model']
                            feature_cols = results['feature_cols']
                            
                            importances = pd.DataFrame({
                                'Feature': feature_cols,
                                'Importance': champion_model.feature_importances_
                            }).sort_values('Importance', ascending=True)
                            
                            fig_importance = px.bar(
                                importances,
                                x='Importance',
                                y='Feature',
                                orientation='h',
                                color='Importance',
                                color_continuous_scale='Viridis'
                            )
                            
                            fig_importance.update_layout(
                                title=f'Feature Importance ({results["champion_name"]})',
                                showlegend=False,
                                height=400
                            )
                            
                            st.plotly_chart(fig_importance, use_container_width=True)
                            
                            # Interpretation
                            top_feature = importances.iloc[-1]['Feature']
                            st.info(f"💡 **Key Insight:** The most important feature for predictions is **{top_feature}**")


# --- RUN APPLICATION --
if __name__ == "__main__":
    main()