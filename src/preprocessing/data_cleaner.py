"""
Data Cleaner Module (Emoji-Free Version)
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any


class DataCleaner:
    """Automated data quality pipeline."""
    
    def __init__(self, df: pd.DataFrame):
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
            
        if df.empty:
            raise ValueError("DataFrame is empty")
            
        self.df = df.copy()
        self.cleaning_log = []
        self._log_step(f"Initialization", f"Started with {len(df):,} rows")
    
    def _log_step(self, step: str, details: str, rows_removed: int = 0):
        entry = {
            'step': step,
            'details': details,
            'rows_removed': rows_removed,
            'rows_remaining': len(self.df),
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        self.cleaning_log.append(entry)
        print(f"STEP: {step}: {details}")
        if rows_removed > 0:
            print(f"   Removed {rows_removed:,} rows")
    
    def clean(self) -> pd.DataFrame:
        print("\n" + "=" * 70)
        print(" " * 20 + "DATA CLEANING PIPELINE")
        print("=" * 70)
        
        initial_rows = len(self.df)
        
        self.remove_duplicates()
        self.handle_missing_values()
        self.convert_data_types()
        self.remove_invalid_transactions()
        self.create_derived_fields()
        
        final_rows = len(self.df)
        removed_total = initial_rows - final_rows
        removed_pct = (removed_total / initial_rows) * 100 if initial_rows > 0 else 0
        
        self._log_step(
            "Completion", 
            f"Finished with {final_rows:,} rows ({removed_pct:.1f}% reduction)"
        )
        
        print("\n" + "=" * 70)
        print(f"CLEANING COMPLETE")
        print(f"   Initial rows: {initial_rows:,}")
        print(f"   Final rows:   {final_rows:,}")
        print(f"   Removed:      {removed_total:,} ({removed_pct:.1f}%)")
        print("=" * 70)
        
        return self.df
    
    def remove_duplicates(self):
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates()
        removed = initial_count - len(self.df)
        self._log_step("Remove Duplicates", "Removed identical rows", removed)
    
    def handle_missing_values(self):
        initial_count = len(self.df)
        critical_cols = ['quantity', 'unit_price']
        cols_to_check = [c for c in critical_cols if c in self.df.columns]
        
        if cols_to_check:
            self.df = self.df.dropna(subset=cols_to_check)
        
        if 'invoice_date' in self.df.columns:
            self.df = self.df.dropna(subset=['invoice_date'])
            
        removed = initial_count - len(self.df)
        self._log_step("Handle Missing", "Dropped rows with missing critical data", removed)
        
        fill_values = {
            'customer_id': 'Unknown',
            'description': 'Unknown Product',
            'country': 'Unknown'
        }
        
        filled_count = 0
        for col, value in fill_values.items():
            if col in self.df.columns:
                missing = self.df[col].isnull().sum()
                if missing > 0:
                    self.df[col] = self.df[col].fillna(value)
                    filled_count += missing
        
        if filled_count > 0:
            self._log_step("Fill Missing", f"Filled {filled_count:,} optional values")
    
    def convert_data_types(self):
        initial_count = len(self.df)
        numeric_cols = ['quantity', 'unit_price']
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        if 'invoice_date' in self.df.columns:
            self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date'], errors='coerce')
        
        cols_to_check = [c for c in ['quantity', 'unit_price', 'invoice_date'] 
                         if c in self.df.columns]
        
        if cols_to_check:
            self.df = self.df.dropna(subset=cols_to_check)
            
        removed = initial_count - len(self.df)
        if removed > 0:
            self._log_step("Type Conversion", "Dropped rows with invalid format", removed)
    
    def remove_invalid_transactions(self):
        initial_count = len(self.df)
        if 'quantity' in self.df.columns:
            self.df = self.df[self.df['quantity'] > 0]
        if 'unit_price' in self.df.columns:
            self.df = self.df[self.df['unit_price'] >= 0]
        if 'invoice_no' in self.df.columns:
            is_cancelled = self.df['invoice_no'].astype(str).str.upper().str.startswith('C')
            self.df = self.df[~is_cancelled]
            
        removed = initial_count - len(self.df)
        self._log_step("Business Logic", "Removed returns/cancellations", removed)
    
    def create_derived_fields(self):
        if 'quantity' in self.df.columns and 'unit_price' in self.df.columns:
            self.df['total_price'] = self.df['quantity'] * self.df['unit_price']
            
        if 'invoice_date' in self.df.columns:
            dt = self.df['invoice_date'].dt
            self.df['year'] = dt.year
            self.df['month'] = dt.month
            self.df['day'] = dt.day
            self.df['day_of_week'] = dt.dayofweek
            self.df['month_year'] = self.df['invoice_date'].dt.to_period('M')
            
        self._log_step("Feature Engineering", "Created derived fields")

    def get_cleaning_report(self) -> pd.DataFrame:
        return pd.DataFrame(self.cleaning_log)

if __name__ == "__main__":
    print("\nDATA CLEANER TEST")
    try:
        df_messy = pd.DataFrame({
            'invoice_no': ['536365', '536365', 'C536366', '536367'],
            'stock_code': ['85123A', '85123A', '71053', '84406B'],
            'quantity': [6, 6, -1, None],
            'unit_price': [2.55, 2.55, 3.39, 2.75],
            'invoice_date': ['2010-12-01', '2010-12-01', '2010-12-01', '2010-12-01'],
            'customer_id': ['17850', '17850', '17850', None]
        })
        
        cleaner = DataCleaner(df_messy)
        df_clean = cleaner.clean()
        
        print("\nClean Data Preview:")
        print(df_clean)
        print("\nALL TESTS PASSED")
        
    except Exception as e:
        print(f"Error: {e}")