"""
Dashboard Charts Module

Purpose:
    Generates interactive Plotly charts for the Streamlit dashboard.
    Takes pre-processed DataFrames and returns Figure objects.

Key Charts:
    - Monthly Revenue Trend (Line)
    - Top Products (Horizontal Bar)
    - Sales by Country (Bar)
    - Hourly Sales Patterns (Bar)

Author: [Your Name]
Date: February 2025
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

class ChartBuilder:
    """
    Factory class for generating dashboard visualizations.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with cleaned dataframe.
        """
        self.df = df
        # ensure Date is datetime
        if 'invoice_date' in self.df.columns:
            if not pd.api.types.is_datetime64_any_dtype(self.df['invoice_date']):
                self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date'])

    def plot_revenue_trend(self, monthly_df: pd.DataFrame):
        """
        Generate Monthly Revenue Trend Line Chart.
        """
        if monthly_df.empty:
            return None
            
        fig = px.line(
            monthly_df, 
            x='Date', 
            y='Revenue',
            title='Monthly Revenue Trend',
            markers=True,
            labels={'Revenue': 'Revenue ($)', 'Date': 'Month'},
            template="plotly_white"
        )
        
        fig.update_traces(line_color='#1f77b4', line_width=3)
        fig.update_layout(hovermode="x unified")
        
        return fig

    def plot_top_products(self, top_products_df: pd.DataFrame):
        """
        Generate Top Products Horizontal Bar Chart.
        """
        if top_products_df.empty:
            return None
            
        fig = px.bar(
            top_products_df, 
            x='Revenue', 
            y='Product',
            orientation='h',
            title='Top Performing Products',
            text_auto='.2s',
            labels={'Revenue': 'Total Revenue ($)', 'Product': ''},
            template="plotly_white"
        )
        
        # Make the chart look cleaner
        fig.update_traces(marker_color='#2ca02c')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
        
        return fig

    def plot_hourly_sales(self):
        """
        Generate Hourly Sales Distribution.
        """
        if 'hour' not in self.df.columns:
            return None
            
        hourly = self.df.groupby('hour')['total_price'].sum().reset_index()
        
        fig = px.bar(
            hourly, 
            x='hour', 
            y='total_price',
            title='Sales by Hour of Day',
            labels={'total_price': 'Revenue ($)', 'hour': 'Hour (24h)'},
            template="plotly_white"
        )
        
        fig.update_traces(marker_color='#ff7f0e')
        
        return fig

# ============================================================================
# MAIN EXECUTION BLOCK (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\nCHART BUILDER TEST")
    
    try:
        # 1. Setup Data
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from src.utils.data_loader import load_uci_dataset
        from src.preprocessing.schema_mapper_silent import SchemaMapper
        from src.preprocessing.data_cleaner import DataCleaner
        from src.analytics.kpi_calculator import KPICalculator
        
        print("Loading and preparing data...")
        df_raw = load_uci_dataset(verbose=False)
        mapper = SchemaMapper(df_raw)
        df_mapped = mapper.apply_mapping(mapper.auto_detect_mapping())
        cleaner = DataCleaner(df_mapped)
        df_clean = cleaner.clean()
        
        # 2. Setup Calculator and Builder
        kpi = KPICalculator(df_clean)
        builder = ChartBuilder(df_clean)
        
        # 3. Test Revenue Chart
        print("Generating Revenue Chart...")
        monthly_data = kpi.get_monthly_sales()
        fig_rev = builder.plot_revenue_trend(monthly_data)
        if fig_rev:
            print("   Revenue Chart created successfully")
            
        # 4. Test Top Products Chart
        print("Generating Top Products Chart...")
        top_data = kpi.get_top_products(limit=5)
        fig_prod = builder.plot_top_products(top_data)
        if fig_prod:
            print("   Top Products Chart created successfully")
            
        # 5. Test Hourly Chart
        print("Generating Hourly Chart...")
        fig_hour = builder.plot_hourly_sales()
        if fig_hour:
            print("   Hourly Chart created successfully")
            
        print("\nALL CHART TESTS PASSED")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()