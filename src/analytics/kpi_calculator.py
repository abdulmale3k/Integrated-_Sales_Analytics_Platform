"""
KPI Calculator Module

Purpose:
    Performs business logic calculations on cleaned sales data.
    Generates metrics for the dashboard (Revenue, Orders, Trends).

Key Features:
    - Calculates headline KPIs (Total Revenue, Avg Order Value, etc.)
    - Aggregates sales by time periods (Monthly/Weekly)
    - Identifies top-performing products and customers
    - Geographic analysis

Author: [Your Name]
Date: February 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple

class KPICalculator:
    """
    Business logic engine for calculating Sales KPIs.
    
    Attributes:
        df (pd.DataFrame): The cleaned sales dataset
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with cleaned data.
        
        Args:
            df (pd.DataFrame): Dataframe with standard columns 
                             (invoice_date, total_price, invoice_no, etc.)
        """
        self.df = df
        
        # Ensure date is datetime object
        if not pd.api.types.is_datetime64_any_dtype(self.df['invoice_date']):
            self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date'])
            
    def get_headline_metrics(self) -> Dict[str, float]:
        """
        Calculate top-level metrics for the dashboard header.
        
        Returns:
            Dict containing:
            - total_revenue
            - total_orders
            - avg_order_value
            - total_customers
            - total_items_sold
        """
        # Revenue
        total_revenue = self.df['total_price'].sum()
        
        # Orders (unique invoices)
        total_orders = self.df['invoice_no'].nunique()
        
        # Customers (unique IDs)
        if 'customer_id' in self.df.columns:
            # Exclude 'Unknown' from count
            valid_customers = self.df[self.df['customer_id'] != 'Unknown']
            total_customers = valid_customers['customer_id'].nunique()
        else:
            total_customers = 0
            
        # Average Order Value (AOV)
        if total_orders > 0:
            aov = total_revenue / total_orders
        else:
            aov = 0.0
            
        # Items sold
        total_items = self.df['quantity'].sum()
        
        return {
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'avg_order_value': aov,
            'total_customers': total_customers,
            'total_items_sold': total_items
        }
    
    def get_monthly_sales(self) -> pd.DataFrame:
        """
        Aggregate revenue by month for trend charts.
        
        Returns:
            DataFrame with columns ['Date', 'Revenue', 'Orders', 'Growth_Pct']
        """
        # Resample by Month ('M')
        monthly = self.df.set_index('invoice_date').resample('M').agg({
            'total_price': 'sum',
            'invoice_no': 'nunique'
        }).reset_index()
        
        # Rename columns
        monthly.columns = ['Date', 'Revenue', 'Orders']
        
        # Calculate Month-over-Month Growth
        monthly['Growth_Pct'] = monthly['Revenue'].pct_change() * 100
        
        # Format date for display (e.g., "Jan 2011")
        monthly['Month_Label'] = monthly['Date'].dt.strftime('%b %Y')
        
        return monthly
    
    def get_top_products(self, limit: int = 10, by: str = 'revenue') -> pd.DataFrame:
        """
        Identify top performing products.
        
        Args:
            limit (int): Number of products to return
            by (str): Metric to rank by ('revenue' or 'quantity')
            
        Returns:
            DataFrame with product details
        """
        # Group by description (product name)
        # We use description because stock_code isn't human readable
        
        if by == 'revenue':
            metric = 'total_price'
            col_name = 'Revenue'
        else:
            metric = 'quantity'
            col_name = 'Units Sold'
            
        top_products = self.df.groupby('description').agg({
            'total_price': 'sum',
            'quantity': 'sum',
            'invoice_no': 'nunique' # Number of orders containing this product
        }).reset_index()
        
        # Sort and take top N
        top_products = top_products.sort_values(metric, ascending=False).head(limit)
        
        # Rename for display
        top_products = top_products.rename(columns={
            'description': 'Product',
            'total_price': 'Revenue',
            'quantity': 'Units Sold',
            'invoice_no': 'Orders Count'
        })
        
        return top_products
    
    def get_sales_by_country(self) -> pd.DataFrame:
        """
        Aggregate sales by country for geographic analysis.
        """
        if 'country' not in self.df.columns:
            return pd.DataFrame()
            
        country_sales = self.df.groupby('country').agg({
            'total_price': 'sum',
            'invoice_no': 'nunique'
        }).reset_index()
        
        country_sales.columns = ['Country', 'Revenue', 'Orders']
        
        # Sort by revenue
        country_sales = country_sales.sort_values('Revenue', ascending=False)
        
        return country_sales

# ============================================================================
# MAIN EXECUTION BLOCK (TESTING)
# ============================================================================

# ============================================================================
# MAIN EXECUTION BLOCK (TESTING)
# ============================================================================

if __name__ == "__main__":
    """Test the KPI Calculator with the real pipeline"""
    
    print("\n" + "=" * 70)
    print("KPI CALCULATOR TEST")
    print("=" * 70)
    
    try:
        # 1. SETUP: Import previous modules
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        # Use silent mapper to avoid encoding issues
        from src.utils.data_loader import load_uci_dataset
        from src.preprocessing.schema_mapper_silent import SchemaMapper
        from src.preprocessing.data_cleaner import DataCleaner
        
        # 2. RUN PIPELINE (Loader -> Mapper -> Cleaner)
        print("\nRunning Data Pipeline (Loader -> Mapper -> Cleaner)...")
        
        # Load
        df_raw = load_uci_dataset(verbose=False)
        
        # Map (Silent mapper has no output, so this is safe)
        mapper = SchemaMapper(df_raw)
        mapping = mapper.auto_detect_mapping()
        df_mapped = mapper.apply_mapping(mapping)
        
        # Clean
        cleaner = DataCleaner(df_mapped)
        df_clean = cleaner.clean()
        
        print(f"Data Ready: {len(df_clean):,} rows")
        
        # 3. TEST CALCULATOR
        print("\n" + "=" * 70)
        print("TEST 1: Headline Metrics")
        print("=" * 70)
        
        calculator = KPICalculator(df_clean)
        metrics = calculator.get_headline_metrics()
        
        for key, value in metrics.items():
            if 'revenue' in key or 'value' in key:
                fmt = f"${value:,.2f}"
            else:
                fmt = f"{value:,.0f}"
            print(f"   {key:<20}: {fmt}")
            
        # 4. TEST MONTHLY SALES
        print("\n" + "=" * 70)
        print("TEST 2: Monthly Trends (First 5 months)")
        print("=" * 70)
        
        monthly = calculator.get_monthly_sales()
        print(monthly[['Month_Label', 'Revenue', 'Orders', 'Growth_Pct']].head())
        
        # 5. TEST TOP PRODUCTS
        print("\n" + "=" * 70)
        print("TEST 3: Top 5 Products by Revenue")
        print("=" * 70)
        
        top_products = calculator.get_top_products(limit=5)
        print(top_products[['Product', 'Revenue', 'Units Sold']].to_string(index=False))
        
        print("\n" + "=" * 70)
        print("ALL KPI TESTS PASSED!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()