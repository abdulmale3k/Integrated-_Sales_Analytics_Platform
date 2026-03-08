"""
Data processing utilities for SME Analytics Platform.
"""

import pandas as pd
import streamlit as st


@st.cache_data(show_spinner=False)
def load_data(file):
    """Load CSV or Excel file with encoding fallbacks."""
    try:
        if file.name.endswith('.csv'):
            encodings = ['utf-8', 'ISO-8859-1', 'cp1252', 'latin1']
            for encoding in encodings:
                try:
                    file.seek(0)
                    return pd.read_csv(file, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode CSV")
        elif file.name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(file)
        return None
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


def auto_detect_columns(columns, aliases, required, optional):
    """Auto-detect column mappings based on aliases."""
    mapping = {}
    missing = []
    found_optional = []
    lower_cols = {c.lower().strip(): c for c in columns}
    
    for target in required:
        found = False
        for alias in aliases.get(target, []):
            if alias.lower() in lower_cols:
                mapping[target] = lower_cols[alias.lower()]
                found = True
                break
        if not found:
            missing.append(target)
    
    for target in optional:
        for alias in aliases.get(target, []):
            if alias.lower() in lower_cols:
                mapping[target] = lower_cols[alias.lower()]
                found_optional.append(target)
                break
    
    return mapping, missing, found_optional


def process_data(df_raw, mapping, required_columns):
    """Clean and process the raw dataframe."""
    try:
        # Rename columns
        rename_map = {v: k for k, v in mapping.items()}
        df = df_raw.rename(columns=rename_map)
        
        # Keep mapped columns
        cols_to_keep = [k for k in mapping.keys() if k in df.columns]
        df = df[cols_to_keep].copy()
        
        # Convert types
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
        df['total_value'] = df['quantity'] * df['unit_price']
        df['order_date'] = pd.to_datetime(df['order_date'], errors='coerce')
        
        # Clean
        df = df[df['quantity'] > 0]
        df = df[df['unit_price'] > 0]
        df = df.dropna(subset=['order_date', 'quantity', 'unit_price'])
        
        return df
    
    except Exception as e:
        st.error(f"Processing error: {e}")
        return None


def calculate_metrics(df):
    """Calculate key metrics from dataframe."""
    return {
        'total_rows': len(df),
        'date_range_days': (df['order_date'].max() - df['order_date'].min()).days,
        'unique_products': df['product_name'].nunique(),
        'total_revenue': df['total_value'].sum(),
        'avg_order_value': df['total_value'].mean(),
        'min_date': df['order_date'].min(),
        'max_date': df['order_date'].max(),
        'unique_transactions': df['transaction_id'].nunique() if 'transaction_id' in df.columns else None,
        'unique_customers': df['customer_id'].nunique() if 'customer_id' in df.columns else None
    }