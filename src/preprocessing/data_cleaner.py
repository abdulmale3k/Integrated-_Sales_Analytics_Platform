"""
Data Cleaner Module

Purpose:
    Automated data cleaning pipeline for sales transaction data.
    Takes raw (but mapped) data and produces analysis-ready data.

Key Features:
    - Handles missing values (removes invalid rows, fills others)
    - Removes duplicate transactions
    - Validates data types (numeric conversion)
    - Filters invalid transactions (negative quantities, cancelled orders)
    - Creates derived fields (total_price, date components)
    - Generates cleaning report/audit trail

Author: [Your Name]
Date: February 2025
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any


class DataCleaner:
    """
    Automated data quality pipeline for sales transactions.
    
    This class transforms raw mapped data into clean, analysis-ready data
    by applying a sequence of cleaning operations and tracking the changes.
    
    Attributes:
        df (pd.DataFrame): The DataFrame being cleaned
        cleaning_log (List[Dict]): Audit log of cleaning operations
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the DataCleaner with a DataFrame.
        
        Args:
            df (pd.DataFrame): The DataFrame to clean (must have canonical column names)
        """
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
            
        if df.empty:
            raise ValueError("DataFrame is empty")
            
        self.df = df.copy()
        self.cleaning_log = []
        
        # Log initialization
        self._log_step(f"Initialization", f"Started with {len(df):,} rows")
    
    def _log_step(self, step: str, details: str, rows_removed: int = 0):
        """
        Record a cleaning step in the audit log.
        
        Args:
            step (str): Name of the cleaning operation
            details (str): Description of what happened
            rows_removed (int): Number of rows removed (optional)
        """
        entry = {
            'step': step,
            'details': details,
            'rows_removed': rows_removed,
            'rows_remaining': len(self.df),
            'timestamp': datetime.now().strftime("%H:%M:%S")
        }
        self.cleaning_log.append(entry)
        
        # Print for development visibility
        print(f"🧹 {step}: {details}")
        if rows_removed > 0:
            print(f"   ❌ Removed {rows_removed:,} rows")
    
    def clean(self) -> pd.DataFrame:
        """
        Execute the full cleaning pipeline.
        
        Sequence:
        1. Remove duplicates
        2. Handle missing values
        3. Convert data types
        4. Remove invalid transactions
        5. Create derived fields
        
        Returns:
            pd.DataFrame: Cleaned and enriched DataFrame
        """
        print("\n" + "=" * 70)
        print(" " * 20 + "🧼 DATA CLEANING PIPELINE")
        print("=" * 70)
        
        initial_rows = len(self.df)
        
        # Execute pipeline steps
        self.remove_duplicates()
        self.handle_missing_values()
        self.convert_data_types()
        self.remove_invalid_transactions()
        self.create_derived_fields()
        
        # Final summary
        final_rows = len(self.df)
        removed_total = initial_rows - final_rows
        removed_pct = (removed_total / initial_rows) * 100 if initial_rows > 0 else 0
        
        self._log_step(
            "Completion", 
            f"Finished with {final_rows:,} rows ({removed_pct:.1f}% reduction)"
        )
        
        print("\n" + "=" * 70)
        print(f"✅ CLEANING COMPLETE")
        print(f"   Initial rows: {initial_rows:,}")
        print(f"   Final rows:   {final_rows:,}")
        print(f"   Removed:      {removed_total:,} ({removed_pct:.1f}%)")
        print("=" * 70)
        
        return self.df
    
    # ========================================================================
    # CLEANING STEPS
    # ========================================================================
    
    def remove_duplicates(self):
        """Remove exact duplicate rows"""
        initial_count = len(self.df)
        self.df = self.df.drop_duplicates()
        removed = initial_count - len(self.df)
        
        self._log_step("Remove Duplicates", "Removed identical rows", removed)
    
    def handle_missing_values(self):
        """
        Handle missing values based on column importance.
        
        Rules:
        - Critical fields (Quantity, Price): Remove row
        - Important fields (Date): Remove row
        - Optional fields (Customer, Description): Fill with default
        """
        initial_count = len(self.df)
        
        # 1. Critical numeric fields
        critical_cols = ['quantity', 'unit_price']
        # Only check columns that exist
        cols_to_check = [c for c in critical_cols if c in self.df.columns]
        
        if cols_to_check:
            self.df = self.df.dropna(subset=cols_to_check)
        
        # 2. Critical date field
        if 'invoice_date' in self.df.columns:
            self.df = self.df.dropna(subset=['invoice_date'])
            
        removed = initial_count - len(self.df)
        self._log_step("Handle Missing", "Dropped rows with missing critical data", removed)
        
        # 3. Fill optional fields
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
                    print(f"   Filled {missing:,} missing values in '{col}'")
        
        if filled_count > 0:
            self._log_step("Fill Missing", f"Filled {filled_count:,} optional values")
    
    def convert_data_types(self):
        """Ensure columns have correct data types"""
        initial_count = len(self.df)
        
        # 1. Numeric conversions
        numeric_cols = ['quantity', 'unit_price']
        for col in numeric_cols:
            if col in self.df.columns:
                # Force numeric, turn errors into NaN
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
        
        # 2. Date conversions
        if 'invoice_date' in self.df.columns:
            self.df['invoice_date'] = pd.to_datetime(self.df['invoice_date'], errors='coerce')
        
        # 3. Drop rows where conversion failed (became NaN)
        cols_to_check = [c for c in ['quantity', 'unit_price', 'invoice_date'] 
                         if c in self.df.columns]
        
        if cols_to_check:
            self.df = self.df.dropna(subset=cols_to_check)
            
        removed = initial_count - len(self.df)
        
        if removed > 0:
            self._log_step("Type Conversion", "Dropped rows with invalid format", removed)
        else:
            self._log_step("Type Conversion", "All data types valid", 0)
    
    def remove_invalid_transactions(self):
        """
        Remove transactions that aren't valid sales.
        
        Rules:
        - Quantity must be > 0 (removes returns/cancellations)
        - Price must be >= 0
        - InvoiceNo shouldn't start with 'C' (cancelled)
        """
        initial_count = len(self.df)
        
        # 1. Positive quantity
        if 'quantity' in self.df.columns:
            self.df = self.df[self.df['quantity'] > 0]
            
        # 2. Non-negative price
        if 'unit_price' in self.df.columns:
            self.df = self.df[self.df['unit_price'] >= 0]
            
        # 3. Not cancelled (InvoiceNo starts with 'C')
        if 'invoice_no' in self.df.columns:
            # Convert to string first, then check
            is_cancelled = self.df['invoice_no'].astype(str).str.upper().str.startswith('C')
            self.df = self.df[~is_cancelled]
            
        removed = initial_count - len(self.df)
        self._log_step("Business Logic", "Removed returns/cancellations/invalid values", removed)
    
    def create_derived_fields(self):
        """Create useful calculated fields for analysis"""
        
        # 1. Total Price (Revenue)
        if 'quantity' in self.df.columns and 'unit_price' in self.df.columns:
            self.df['total_price'] = self.df['quantity'] * self.df['unit_price']
            
        # 2. Date Components
        if 'invoice_date' in self.df.columns:
            dt = self.df['invoice_date'].dt
            
            self.df['year'] = dt.year
            self.df['month'] = dt.month
            self.df['day'] = dt.day
            self.df['day_of_week'] = dt.dayofweek  # 0=Monday, 6=Sunday
            self.df['hour'] = dt.hour
            self.df['month_year'] = self.df['invoice_date'].dt.to_period('M')
            
        self._log_step("Feature Engineering", "Created derived fields (total_price, date parts)")
        
        # Print new columns
        new_cols = [c for c in ['total_price', 'year', 'month'] if c in self.df.columns]
        print(f"   Added columns: {', '.join(new_cols)}...")

    def get_cleaning_report(self) -> pd.DataFrame:
        """Return the cleaning log as a DataFrame"""
        return pd.DataFrame(self.cleaning_log)


# ============================================================================
# MAIN EXECUTION BLOCK (TESTING)
# ============================================================================

if __name__ == "__main__":
    """Test the DataCleaner with sample messy data"""
    
    print("\n" + "🎯" * 35)
    print(" " * 20 + "DATA CLEANER TEST")
    print("🎯" * 35)
    
    try:
        # 1. Create messy sample data
        print("\n" + "=" * 70)
        print("STEP 1: Create Messy Data")
        print("=" * 70)
        
        df_messy = pd.DataFrame({
            'invoice_no': ['536365', '536365', 'C536366', '536367', '536368', '536369'],
            'stock_code': ['85123A', '85123A', '71053', '84406B', '84029G', '85123A'],
            'quantity': [6, 6, -1, None, 6, 10],  # Duplicate, Negative, Missing
            'unit_price': [2.55, 2.55, 3.39, 2.75, 'Invalid', 2.55], # Duplicate, Invalid type
            'invoice_date': ['2010-12-01', '2010-12-01', '2010-12-01', '2010-12-01', '2010-12-01', '2010-12-02'],
            'customer_id': ['17850', '17850', '17850', None, '17850', '17850'] # Duplicate, Missing
        })
        
        print("\n📋 Messy Data Preview:")
        print(df_messy)
        print(f"\nIssues to fix:")
        print("- Row 1: Duplicate of Row 0")
        print("- Row 2: Cancelled order (C536366) + Negative quantity")
        print("- Row 3: Missing quantity")
        print("- Row 4: Invalid price ('Invalid')")
        print("- Row 3: Missing CustomerID (should handle gracefully)")
        
        # 2. Initialize Cleaner
        print("\n" + "=" * 70)
        print("STEP 2: Initialize Cleaner")
        print("=" * 70)
        
        cleaner = DataCleaner(df_messy)
        
        # 3. Run Cleaning Pipeline
        print("\n" + "=" * 70)
        print("STEP 3: Run Pipeline")
        print("=" * 70)
        
        df_clean = cleaner.clean()
        
        # 4. Verify Results
        print("\n" + "=" * 70)
        print("STEP 4: Verify Results")
        print("=" * 70)
        
        print("\n📋 Clean Data Preview:")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(df_clean)
        
        # Verification checks
        assert len(df_clean) == 2, f"Expected 2 rows, got {len(df_clean)}"
        # Row 0 (valid) and Row 5 (valid) should remain
        # Row 1 (duplicate) -> Removed
        # Row 2 (cancelled) -> Removed
        # Row 3 (missing qty) -> Removed
        # Row 4 (invalid price) -> Removed
        
        assert 'total_price' in df_clean.columns, "Derived field total_price missing"
        assert 'month' in df_clean.columns, "Derived field month missing"
        assert df_clean['customer_id'].isnull().sum() == 0, "Missing customer_id not filled"
        
        print("\n✅ Verification passed!")
        print("   - Duplicates removed")
        print("   - Cancelled orders removed")
        print("   - Missing values handled")
        print("   - Invalid types handled")
        print("   - Derived fields created")
        
        # 5. Show Report
        print("\n" + "=" * 70)
        print("STEP 5: Cleaning Report")
        print("=" * 70)
        
        report = cleaner.get_cleaning_report()
        print(report[['step', 'details', 'rows_removed', 'rows_remaining']].to_string(index=False))
        
        print("\n" + "=" * 70)
        print("✅ " * 17 + "✅")
        print(" " * 20 + "ALL TESTS PASSED!")
        print("✅ " * 17 + "✅")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()