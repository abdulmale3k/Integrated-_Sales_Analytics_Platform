"""
Silent Schema Mapper - Windows-Safe Version

This module wraps the original SchemaMapper and suppresses ALL console output
to prevent Unicode encoding errors on Windows terminals.

Perfect for:
- Streamlit applications (where console output isn't needed)
- Windows systems with encoding issues
- Production environments

Usage:
    from src.preprocessing.schema_mapper_silent import SchemaMapper
    
    mapper = SchemaMapper(df)  # No console output!
    mapping = mapper.auto_detect_mapping()  # Silent
    is_valid, errors = mapper.validate_mapping(mapping)  # Silent
    df_clean = mapper.apply_mapping(mapping)  # Silent
"""

import sys
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd

# ============================================================================
# IMPORT ORIGINAL MAPPER WITH SUPPRESSED OUTPUT
# ============================================================================

# Save original stdout
_original_stdout = sys.stdout
_original_stderr = sys.stderr

# Redirect to null during import
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

try:
    # Import the original SchemaMapper
    from src.preprocessing.schema_mapper import SchemaMapper as _OriginalSchemaMapper
finally:
    # Restore stdout/stderr
    sys.stdout.close()
    sys.stderr.close()
    sys.stdout = _original_stdout
    sys.stderr = _original_stderr

# ============================================================================
# SILENT WRAPPER CLASS
# ============================================================================

class SchemaMapper(_OriginalSchemaMapper):
    """
    Silent version of SchemaMapper - suppresses all print statements.
    
    This class inherits from the original SchemaMapper but overrides
    all methods to suppress their console output.
    
    All functionality remains identical - only the print statements
    are removed.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize SchemaMapper silently.
        
        Args:
            df (pd.DataFrame): The user's uploaded DataFrame
        """
        # Suppress output during initialization
        _old_stdout = sys.stdout
        _old_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        
        try:
            super().__init__(df)
        finally:
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = _old_stdout
            sys.stderr = _old_stderr
    
    def auto_detect_mapping(self) -> Dict[str, Optional[str]]:
        """
        Auto-detect column mappings silently.
        
        Returns:
            Dict[str, Optional[str]]: Mapping of canonical names to user columns
        """
        _old_stdout = sys.stdout
        _old_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        
        try:
            result = super().auto_detect_mapping()
        finally:
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = _old_stdout
            sys.stderr = _old_stderr
        
        return result
    
    def validate_mapping(self, mapping: Dict[str, Optional[str]]) -> Tuple[bool, List[str]]:
        """
        Validate mapping silently.
        
        Args:
            mapping (Dict[str, Optional[str]]): The proposed mapping
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        _old_stdout = sys.stdout
        _old_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        
        try:
            result = super().validate_mapping(mapping)
        finally:
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = _old_stdout
            sys.stderr = _old_stderr
        
        return result
    
    def apply_mapping(self, mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
        """
        Apply mapping transformation silently.
        
        Args:
            mapping (Dict[str, Optional[str]]): The column mapping
            
        Returns:
            pd.DataFrame: Transformed DataFrame
        """
        _old_stdout = sys.stdout
        _old_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        
        try:
            result = super().apply_mapping(mapping)
        finally:
            sys.stdout.close()
            sys.stderr.close()
            sys.stdout = _old_stdout
            sys.stderr = _old_stderr
        
        return result


# ============================================================================
# EXPOSE ALL OTHER ATTRIBUTES
# ============================================================================

# Make all class attributes available
CANONICAL_SCHEMA = _OriginalSchemaMapper.CANONICAL_SCHEMA

# Export the silent version
__all__ = ['SchemaMapper', 'CANONICAL_SCHEMA']