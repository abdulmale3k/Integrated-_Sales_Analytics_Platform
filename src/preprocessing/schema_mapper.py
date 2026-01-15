"""
Schema Mapper Module

Purpose:
    Maps user CSV columns to the platform's canonical schema.
    Handles varying column names from different e-commerce platforms
    (Shopify, WooCommerce, Etsy, etc.) and standardizes them.

Key Features:
    - Auto-detection of column mappings based on common patterns
    - Manual mapping interface for user confirmation
    - Validation to ensure all required fields are mapped
    - Transformation to standardized column names

Author: [Your Name]
Date: February 2025
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple


class SchemaMapper:
    """
    Intelligent column mapping system for standardizing diverse CSV formats.
    """
    
    # ========================================================================
    # CANONICAL SCHEMA DEFINITION
    # ========================================================================
    
    CANONICAL_SCHEMA = {
        'invoice_no': {
            'required': True,
            'description': 'Unique transaction/order identifier',
            'examples': ['Invoice', 'InvoiceNo', 'OrderID', 'Order Number', 
                        'TransactionID', 'Receipt', 'ReceiptID'],
            'data_type': 'string'
        },
        'stock_code': {
            'required': True,
            'description': 'Product/SKU identifier',
            'examples': ['StockCode', 'ProductID', 'SKU', 'ItemCode', 
                        'Product Code', 'Item ID', 'ASIN'],
            'data_type': 'string'
        },
        'description': {
            'required': False,
            'description': 'Product description/name',
            'examples': ['Description', 'ProductName', 'Product Title', 
                        'Item Name', 'Product', 'Item Description'],
            'data_type': 'string'
        },
        'quantity': {
            'required': True,
            'description': 'Quantity sold (must be numeric)',
            'examples': ['Quantity', 'Qty', 'Units', 'Amount', 'Count', 
                        'Quantity Sold', 'Items'],
            'data_type': 'numeric'
        },
        'invoice_date': {
            'required': True,
            'description': 'Transaction date/timestamp',
            'examples': ['InvoiceDate', 'Date', 'OrderDate', 'Transaction Date',
                        'Purchase Date', 'Created At', 'Order Time'],
            'data_type': 'datetime'
        },
        'unit_price': {
            'required': True,
            'description': 'Price per unit (must be numeric)',
            'examples': ['UnitPrice', 'Price', 'Unit Price', 'Cost', 
                        'Item Price', 'Rate', 'Amount'],
            'data_type': 'numeric'
        },
        'customer_id': {
            'required': False,
            'description': 'Customer identifier',
            'examples': ['CustomerID', 'Customer ID', 'Customer', 'ClientID',
                        'UserID', 'Account ID'],
            'data_type': 'string'
        },
        'country': {
            'required': False,
            'description': 'Country/region of transaction',
            'examples': ['Country', 'Region', 'Location', 'Territory',
                        'Shipping Country', 'Billing Country'],
            'data_type': 'string'
        }
    }
    
    # ========================================================================
    # INITIALIZATION
    # ========================================================================
    
    def __init__(self, df: pd.DataFrame):
        """Initialize the SchemaMapper with a user's DataFrame."""
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        if len(df.columns) == 0:
            raise ValueError("DataFrame has no columns")
        
        self.df = df.copy()
        self.user_columns = df.columns.tolist()
        self.mapping: Dict[str, Optional[str]] = {}
        
        print(f"SchemaMapper initialized")
        print(f"   User columns: {len(self.user_columns)}")
        print(f"   Required fields: {self._count_required_fields()}")
    
    # ========================================================================
    # AUTO-DETECTION
    # ========================================================================
    
    def auto_detect_mapping(self) -> Dict[str, Optional[str]]:
        """Automatically detect column mappings."""
        print("\n" + "=" * 70)
        print(" " * 20 + "AUTO-DETECTION")
        print("=" * 70)
        
        mapping = {}
        
        for canonical_name, schema_info in self.CANONICAL_SCHEMA.items():
            detected = None
            
            # Strategy 1: Exact match
            for user_col in self.user_columns:
                normalized_user = user_col.lower().replace(' ', '').replace('_', '')
                normalized_canonical = canonical_name.lower().replace('_', '')
                
                if normalized_user == normalized_canonical:
                    detected = user_col
                    print(f"MATCH: {canonical_name:<15} -> {user_col:<20} (exact match)")
                    break
            
            # Strategy 2: Keyword match
            if detected is None:
                for example in schema_info['examples']:
                    for user_col in self.user_columns:
                        normalized_example = example.lower().replace(' ', '').replace('_', '')
                        normalized_user = user_col.lower().replace(' ', '').replace('_', '')
                        
                        if normalized_example in normalized_user or \
                           normalized_user in normalized_example:
                            detected = user_col
                            print(f"MATCH: {canonical_name:<15} -> {user_col:<20} (matched '{example}')")
                            break
                    if detected:
                        break
            
            if detected is None:
                print(f"MISSING: {canonical_name:<15} -> NOT DETECTED")
            
            mapping[canonical_name] = detected
        
        return mapping
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate_mapping(self, mapping: Dict[str, Optional[str]]) -> Tuple[bool, List[str]]:
        """Validate mapping requirements."""
        print("\n" + "=" * 70)
        print(" " * 20 + "VALIDATION")
        print("=" * 70)
        
        errors = []
        
        print("\nChecking required fields...")
        for canonical_name, schema_info in self.CANONICAL_SCHEMA.items():
            if schema_info['required']:
                mapped_column = mapping.get(canonical_name)
                if mapped_column is None:
                    error_msg = f"ERROR: Required field '{canonical_name}' is not mapped"
                    errors.append(error_msg)
                    print(f"   {error_msg}")
                else:
                    print(f"   OK: {canonical_name} -> {mapped_column}")
        
        # Check duplicate mappings
        mapped_columns = [col for col in mapping.values() if col is not None]
        seen = set()
        duplicates = set()
        for col in mapped_columns:
            if col in seen:
                duplicates.add(col)
            seen.add(col)
            
        if duplicates:
            for dup in duplicates:
                fields = [k for k, v in mapping.items() if v == dup]
                print(f"   ERROR: Column '{dup}' mapped to multiple fields: {fields}")
        
        is_valid = len(errors) == 0
        
        print("\n" + "=" * 70)
        if is_valid:
            print("VALIDATION PASSED")
        else:
            print("VALIDATION FAILED")
        print("=" * 70)
        
        return is_valid, errors
    
    # ========================================================================
    # TRANSFORMATION
    # ========================================================================
    
    def apply_mapping(self, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
        """Transform DataFrame to canonical schema."""
        print("\n" + "=" * 70)
        print(" " * 20 + "APPLYING MAPPING")
        print("=" * 70)
        
        is_valid, errors = self.validate_mapping(mapping)
        if not is_valid:
            raise ValueError(f"Invalid mapping: {errors}")
        
        reverse_mapping = {}
        for canonical_name, user_column in mapping.items():
            if user_column is not None:
                reverse_mapping[user_column] = canonical_name
        
        columns_to_keep = list(reverse_mapping.keys())
        df_selected = self.df[columns_to_keep].copy()
        df_transformed = df_selected.rename(columns=reverse_mapping)
        
        print(f"\nTransformation complete!")
        print(f"   Original columns: {len(self.df.columns)}")
        print(f"   Transformed columns: {len(df_transformed.columns)}")
        print(f"   Rows: {len(df_transformed):,}")
        
        return df_transformed

    # Helper methods
    def _count_required_fields(self) -> int:
        return sum(1 for info in self.CANONICAL_SCHEMA.values() if info['required'])
        
    def get_required_fields(self) -> List[str]:
        return [n for n, i in self.CANONICAL_SCHEMA.items() if i['required']]
        
    def get_optional_fields(self) -> List[str]:
        return [n for n, i in self.CANONICAL_SCHEMA.items() if not i['required']]

# ============================================================================
# MAIN EXECUTION BLOCK
# ============================================================================

if __name__ == "__main__":
    print("\nSCHEMA MAPPER TEST")
    try:
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from src.utils.data_loader import load_uci_dataset
        
        df = load_uci_dataset(verbose=False)
        mapper = SchemaMapper(df)
        mapping = mapper.auto_detect_mapping()
        is_valid, errors = mapper.validate_mapping(mapping)
        
        if is_valid:
            df_transformed = mapper.apply_mapping(mapping)
            print("ALL TESTS PASSED")
        else:
            print("TEST FAILED")
            
    except Exception as e:
        print(f"Error: {e}")