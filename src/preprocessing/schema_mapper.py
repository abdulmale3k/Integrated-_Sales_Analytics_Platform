"""
Schema Mapper

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
    
    This class handles the transformation of user CSV files with arbitrary
    column names into a standardized schema that the platform expects.
    
    Attributes:
        df (pd.DataFrame): The user's uploaded DataFrame
        user_columns (List[str]): List of column names from user's CSV
        mapping (Dict[str, Optional[str]]): Current column mapping
        
    Example:
        >>> df_user = pd.read_csv("shopify_export.csv")
        >>> mapper = SchemaMapper(df_user)
        >>> auto_mapping = mapper.auto_detect_mapping()
        >>> is_valid, errors = mapper.validate_mapping(auto_mapping)
        >>> if is_valid:
        ...     df_clean = mapper.apply_mapping(auto_mapping)
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
        """
        Initialize the SchemaMapper with a user's DataFrame.
        
        Args:
            df (pd.DataFrame): The uploaded CSV data with original column names
            
        Raises:
            ValueError: If df is not a DataFrame or is empty
        """
        
        # Validate input
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Input must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        if len(df.columns) == 0:
            raise ValueError("DataFrame has no columns")
        
        # Store the original DataFrame
        self.df = df.copy()
        
        # Store user's column names
        self.user_columns = df.columns.tolist()
        
        # Initialize mapping dictionary
        self.mapping: Dict[str, Optional[str]] = {}
        
        print(f"✅ SchemaMapper initialized")
        print(f"   User columns: {len(self.user_columns)}")
        print(f"   Required fields: {self._count_required_fields()}")
    
    # ========================================================================
    # AUTO-DETECTION
    # ========================================================================
    
    def auto_detect_mapping(self) -> Dict[str, Optional[str]]:
        """
        Automatically detect column mappings based on common naming patterns.
        
        This method uses a multi-strategy approach:
        1. Exact match (case-insensitive, ignoring spaces/underscores)
        2. Keyword matching against known examples
        3. Partial string matching
        
        Returns:
            Dict[str, Optional[str]]: Mapping of canonical names to user columns
            
        Example:
            >>> mapping = mapper.auto_detect_mapping()
            >>> print(mapping)
            {
                'invoice_no': 'Order ID',
                'quantity': 'Qty',
                'unit_price': 'Price',
                'customer_id': None  # Not detected
            }
        """
        
        print("\n" + "=" * 70)
        print(" " * 20 + "🔍 AUTO-DETECTION")
        print("=" * 70)
        
        mapping = {}
        
        for canonical_name, schema_info in self.CANONICAL_SCHEMA.items():
            
            detected = None
            
            # ----------------------------------------------------------------
            # Strategy 1: Exact match (normalized)
            # ----------------------------------------------------------------
            
            for user_col in self.user_columns:
                # Normalize both strings: lowercase, no spaces/underscores
                normalized_user = user_col.lower().replace(' ', '').replace('_', '')
                normalized_canonical = canonical_name.lower().replace('_', '')
                
                if normalized_user == normalized_canonical:
                    detected = user_col
                    print(f"✅ {canonical_name:<15} → {user_col:<20} (exact match)")
                    break
            
            # ----------------------------------------------------------------
            # Strategy 2: Example keyword matching
            # ----------------------------------------------------------------
            
            if detected is None:
                for example in schema_info['examples']:
                    for user_col in self.user_columns:
                        
                        # Normalize for comparison
                        normalized_example = example.lower().replace(' ', '').replace('_', '')
                        normalized_user = user_col.lower().replace(' ', '').replace('_', '')
                        
                        # Check if example is contained in user column
                        if normalized_example in normalized_user or \
                           normalized_user in normalized_example:
                            detected = user_col
                            print(f"✅ {canonical_name:<15} → {user_col:<20} (matched '{example}')")
                            break
                    
                    if detected:
                        break
            
            # ----------------------------------------------------------------
            # Store result
            # ----------------------------------------------------------------
            
            if detected is None:
                print(f"⚠️  {canonical_name:<15} → NOT DETECTED")
            
            mapping[canonical_name] = detected
        
        # Print summary
        detected_count = sum(1 for v in mapping.values() if v is not None)
        total_count = len(mapping)
        required_count = self._count_required_fields()
        
        print("\n" + "-" * 70)
        print(f"📊 Detection Summary:")
        print(f"   Total fields: {total_count}")
        print(f"   Detected: {detected_count}")
        print(f"   Not detected: {total_count - detected_count}")
        print(f"   Required fields: {required_count}")
        print("=" * 70)
        
        return mapping
    
    # ========================================================================
    # VALIDATION
    # ========================================================================
    
    def validate_mapping(self, mapping: Dict[str, Optional[str]]) -> Tuple[bool, List[str]]:
        """
        Validate that the provided mapping satisfies all requirements.
        
        Checks:
        1. All required fields are mapped
        2. No duplicate mappings (same column mapped to multiple fields)
        3. Mapped columns actually exist in the DataFrame
        4. Data types are compatible (optional but recommended)
        
        Args:
            mapping (Dict[str, Optional[str]]): The proposed column mapping
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
            
        Example:
            >>> mapping = {'invoice_no': 'OrderID', 'quantity': None}
            >>> is_valid, errors = mapper.validate_mapping(mapping)
            >>> print(is_valid)
            False
            >>> print(errors)
            ['❌ Required field "quantity" is not mapped']
        """
        
        print("\n" + "=" * 70)
        print(" " * 20 + "✔️  VALIDATION")
        print("=" * 70)
        
        errors = []
        
        # ----------------------------------------------------------------
        # Check 1: Required fields must be mapped
        # ----------------------------------------------------------------
        
        print("\n🔍 Checking required fields...")
        
        for canonical_name, schema_info in self.CANONICAL_SCHEMA.items():
            if schema_info['required']:
                
                mapped_column = mapping.get(canonical_name)
                
                if mapped_column is None:
                    error_msg = f"❌ Required field '{canonical_name}' is not mapped"
                    errors.append(error_msg)
                    print(f"   {error_msg}")
                else:
                    print(f"   ✅ {canonical_name} → {mapped_column}")
        
        # ----------------------------------------------------------------
        # Check 2: No duplicate mappings
        # ----------------------------------------------------------------
        
        print("\n🔍 Checking for duplicate mappings...")
        
        # Get all mapped columns (excluding None)
        mapped_columns = [col for col in mapping.values() if col is not None]
        
        # Find duplicates
        seen = set()
        duplicates = set()
        
        for col in mapped_columns:
            if col in seen:
                duplicates.add(col)
            seen.add(col)
        
        if duplicates:
            for dup in duplicates:
                # Find which canonical fields this column is mapped to
                fields = [k for k, v in mapping.items() if v == dup]
                error_msg = f"❌ Column '{dup}' is mapped to multiple fields: {fields}"
                errors.append(error_msg)
                print(f"   {error_msg}")
        else:
            print("   ✅ No duplicate mappings")
        
        # ----------------------------------------------------------------
        # Check 3: Mapped columns exist in DataFrame
        # ----------------------------------------------------------------
        
        print("\n🔍 Checking column existence...")
        
        for canonical_name, user_column in mapping.items():
            if user_column is not None:
                if user_column not in self.df.columns:
                    error_msg = f"❌ Mapped column '{user_column}' does not exist in DataFrame"
                    errors.append(error_msg)
                    print(f"   {error_msg}")
        
        if not any("does not exist" in e for e in errors):
            print("   ✅ All mapped columns exist")
        
        # ----------------------------------------------------------------
        # Check 4: Data type compatibility (warnings, not errors)
        # ----------------------------------------------------------------
        
        print("\n🔍 Checking data types...")
        
        for canonical_name, user_column in mapping.items():
            if user_column is not None and user_column in self.df.columns:
                
                expected_type = self.CANONICAL_SCHEMA[canonical_name]['data_type']
                actual_dtype = self.df[user_column].dtype
                
                # Check numeric fields
                if expected_type == 'numeric':
                    if not pd.api.types.is_numeric_dtype(actual_dtype):
                        warning = f"⚠️  '{canonical_name}' expects numeric data, but '{user_column}' is {actual_dtype}"
                        print(f"   {warning}")
                        # Note: We don't add this to errors (just a warning)
                    else:
                        print(f"   ✅ {canonical_name} ({user_column}) is numeric")
        
        # ----------------------------------------------------------------
        # Final verdict
        # ----------------------------------------------------------------
        
        is_valid = len(errors) == 0
        
        print("\n" + "=" * 70)
        if is_valid:
            print("✅ " * 17 + "✅")
            print(" " * 22 + "VALIDATION PASSED")
            print("✅ " * 17 + "✅")
        else:
            print("❌ " * 17 + "❌")
            print(" " * 22 + "VALIDATION FAILED")
            print("❌ " * 17 + "❌")
            print(f"\n{len(errors)} error(s) found:")
            for error in errors:
                print(f"   {error}")
        print("=" * 70)
        
        return is_valid, errors
    
    # ========================================================================
    # TRANSFORMATION
    # ========================================================================
    
    def apply_mapping(self, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
        """
        Apply the mapping to transform the DataFrame to canonical schema.
        
        This method:
        1. Validates the mapping
        2. Selects only mapped columns from the original DataFrame
        3. Renames them to canonical names
        4. Returns the transformed DataFrame
        
        Args:
            mapping (Dict[str, Optional[str]]): The column mapping to apply
            
        Returns:
            pd.DataFrame: Transformed DataFrame with canonical column names
            
        Raises:
            ValueError: If mapping is invalid
            
        Example:
            >>> mapping = {
            ...     'invoice_no': 'Order ID',
            ...     'quantity': 'Qty',
            ...     'unit_price': 'Price'
            ... }
            >>> df_clean = mapper.apply_mapping(mapping)
            >>> print(df_clean.columns)
            Index(['invoice_no', 'quantity', 'unit_price'])
        """
        
        print("\n" + "=" * 70)
        print(" " * 20 + "🔄 APPLYING MAPPING")
        print("=" * 70)
        
        # ----------------------------------------------------------------
        # Step 1: Validate mapping first
        # ----------------------------------------------------------------
        
        is_valid, errors = self.validate_mapping(mapping)
        
        if not is_valid:
            raise ValueError(
                f"Cannot apply invalid mapping. Errors:\n" + 
                "\n".join(errors)
            )
        
        # ----------------------------------------------------------------
        # Step 2: Create reverse mapping (user_col -> canonical_name)
        # ----------------------------------------------------------------
        
        reverse_mapping = {}
        
        for canonical_name, user_column in mapping.items():
            if user_column is not None:
                reverse_mapping[user_column] = canonical_name
        
        print(f"\n📋 Mapping {len(reverse_mapping)} columns:")
        for user_col, canonical_name in reverse_mapping.items():
            print(f"   {user_col:<25} → {canonical_name}")
        
        # ----------------------------------------------------------------
        # Step 3: Select and rename columns
        # ----------------------------------------------------------------
        
        # Select only the columns that are mapped
        columns_to_keep = list(reverse_mapping.keys())
        df_selected = self.df[columns_to_keep].copy()
        
        # Rename to canonical names
        df_transformed = df_selected.rename(columns=reverse_mapping)
        
        print(f"\n✅ Transformation complete!")
        print(f"   Original columns: {len(self.df.columns)}")
        print(f"   Transformed columns: {len(df_transformed.columns)}")
        print(f"   Rows: {len(df_transformed):,}")
        
        # ----------------------------------------------------------------
        # Step 4: Display sample
        # ----------------------------------------------------------------
        
        print(f"\n👀 Sample of transformed data (first 3 rows):")
        print("-" * 70)
        pd.set_option('display.width', 1000)
        pd.set_option('display.max_columns', None)
        print(df_transformed.head(3).to_string(index=False))
        print("-" * 70)
        
        print("\n" + "=" * 70)
        
        return df_transformed
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _count_required_fields(self) -> int:
        """Count how many fields in the schema are required"""
        return sum(1 for info in self.CANONICAL_SCHEMA.values() if info['required'])
    
    def get_schema_info(self, canonical_name: str) -> Dict:
        """
        Get detailed information about a canonical field.
        
        Args:
            canonical_name (str): The canonical field name
            
        Returns:
            Dict: Schema information for that field
        """
        return self.CANONICAL_SCHEMA.get(canonical_name, {})
    
    def get_user_columns(self) -> List[str]:
        """
        Get the list of user's column names.
        
        Returns:
            List[str]: Column names from user's DataFrame
        """
        return self.user_columns.copy()
    
    def get_required_fields(self) -> List[str]:
        """
        Get list of required canonical field names.
        
        Returns:
            List[str]: Names of required fields
        """
        return [
            name for name, info in self.CANONICAL_SCHEMA.items()
            if info['required']
        ]
    
    def get_optional_fields(self) -> List[str]:
        """
        Get list of optional canonical field names.
        
        Returns:
            List[str]: Names of optional fields
        """
        return [
            name for name, info in self.CANONICAL_SCHEMA.items()
            if not info['required']
        ]


# ============================================================================
# MAIN EXECUTION BLOCK
# ============================================================================

if __name__ == "__main__":
    """
    Test the SchemaMapper with sample data.
    
    This demonstrates the complete workflow:
    1. Load a CSV with non-standard column names
    2. Auto-detect column mappings
    3. Validate the mapping
    4. Apply transformation
    """
    
    print("\n" + "🎯" * 35)
    print(" " * 20 + "SCHEMA MAPPER TEST")
    print("🎯" * 35)
    
    try:
        # ====================================================================
        # TEST 1: Load UCI Dataset
        # ====================================================================
        
        print("\n" + "=" * 70)
        print("TEST 1: Load UCI Dataset")
        print("=" * 70)
        
        from pathlib import Path
        import sys
        
        # Add parent directory to path to import data_loader
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        from src.utils.data_loader import load_uci_dataset
        
        df = load_uci_dataset(verbose=False)
        
        print(f"✅ Loaded {len(df):,} rows with {len(df.columns)} columns")
        print(f"   Columns: {df.columns.tolist()}")
        
        # ====================================================================
        # TEST 2: Initialize SchemaMapper
        # ====================================================================
        
        print("\n" + "=" * 70)
        print("TEST 2: Initialize SchemaMapper")
        print("=" * 70)
        
        mapper = SchemaMapper(df)
        
        # ====================================================================
        # TEST 3: Auto-detect Mapping
        # ====================================================================
        
        print("\n" + "=" * 70)
        print("TEST 3: Auto-detect Column Mapping")
        print("=" * 70)
        
        mapping = mapper.auto_detect_mapping()
        
        # ====================================================================
        # TEST 4: Validate Mapping
        # ====================================================================
        
        print("\n" + "=" * 70)
        print("TEST 4: Validate Mapping")
        print("=" * 70)
        
        is_valid, errors = mapper.validate_mapping(mapping)
        
        assert is_valid, f"Validation failed: {errors}"
        print("✅ Validation test passed!")
        
        # ====================================================================
        # TEST 5: Apply Mapping
        # ====================================================================
        
        print("\n" + "=" * 70)
        print("TEST 5: Apply Mapping Transformation")
        print("=" * 70)
        
        df_transformed = mapper.apply_mapping(mapping)
        
        # Verify transformation
        assert 'invoice_no' in df_transformed.columns
        assert 'quantity' in df_transformed.columns
        assert len(df_transformed) == len(df)
        
        print("✅ Transformation test passed!")
        
        # ====================================================================
        # ALL TESTS PASSED
        # ====================================================================
        
        print("\n" + "=" * 70)
        print("✅ " * 17 + "✅")
        print(" " * 20 + "ALL TESTS PASSED!")
        print("✅ " * 17 + "✅")
        print("=" * 70)
        
        print("\n📌 SUMMARY:")
        print(f"   Original columns: {len(df.columns)}")
        print(f"   Transformed columns: {len(df_transformed.columns)}")
        print(f"   Canonical names: {df_transformed.columns.tolist()}")
        
        print("\n📌 NEXT STEPS:")
        print("   1. ✅ Schema mapper is working correctly")
        print("   2. ➡️  Build data_cleaner.py next")
        print("   3. ➡️  Then integrate with Streamlit dashboard")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ " * 17 + "❌")
        print(" " * 22 + "TEST FAILED")
        print("❌ " * 17 + "❌")
        print("=" * 70)
        
        print(f"\n💥 Error occurred:")
        print(f"   {type(e).__name__}: {e}")
        
        import traceback
        print(f"\n📍 Traceback:")
        traceback.print_exc()
        
        sys.exit(1)