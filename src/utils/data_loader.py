"""
UCI Online Retail II Dataset Loader

"""

import pandas as pd
import os
from pathlib import Path
import urllib.request
import zipfile
import sys

def download_uci_dataset():
    """
    Download UCI Online Retail II Dataset from the official repository.

    This function:
    1. Checks if dataset already exists (skip download if yes)
    2. Downloads ZIP file from UCI servers
    3. Extracts the Excel file
    4. Cleans up the ZIP file
    
    Returns:
        bool: True if successful, False if download failed
    """
    print("=" * 70)
    print(" " * 20 + "📥 DATASET DOWNLOADER")
    print("=" * 70)

    # The official UCI download URL
    url = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip" 

    # Create data directory structure
    data_dir = Path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)

    zip_path = data_dir / "online_retail_ii.zip"

        
    # Check if Excel file already exists (skip download if yes)
    excel_files = list(data_dir.glob("*.xlsx"))
    
    if excel_files:
        print(f"✅ Dataset already exists: {excel_files[0].name}")
        print(f"   Location: {excel_files[0].absolute()}")
        print(f"   Skipping download.")
        return True
    
    try:
        print(f"\n📡 Downloading from UCI repository...")
        print(f"    URL: {url}")
        print(f"    This may take 1-2 minutes depending on your connection...")

        #Actually download the file
        urllib.request.urlretrieve(url, zip_path)

        #Get file size for confirmation
        file_size_mb = zip_path.stat().st_size / (1024*1024)

        print(f"\n✅ Download complete!")
        print(f"   File size: {file_size_mb:.1f} MB")
        print(f"   Saved to: {zip_path.absolute()}")
            
    except Exception as e:
        print(f"\n❌ ERROR: Failed to download dataset")
        print(f"   Error details: {e}")
        print(f"\n📌 Manual download instructions:")
        print(f"   1. Open browser and go to:")
        print(f"      https://archive.ics.uci.edu/dataset/502/online+retail+ii")
        print(f"   2. Click the 'Download' button")
        print(f"   3. Save the ZIP file to:")
        print(f"      {zip_path.absolute()}")
        print(f"   4. Run this script again")
        return False
        
    # Extract the ZIP file
    try:
        print(f"\n📂 Extracting ZIP archive...")
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List what's inside the ZIP
            file_list = zip_ref.namelist()
            print(f"   Found {len(file_list)} file(s) in archive:")
            for filename in file_list:
                print(f"      - {filename}")
            
            # Extract everything
            zip_ref.extractall(data_dir)
        
        print(f"\n✅ Extraction complete!")
        
        # Verify the Excel file was extracted
        excel_files = list(data_dir.glob("*.xlsx"))
        if excel_files:
            print(f"   Extracted: {excel_files[0].name}")
            excel_size_mb = excel_files[0].stat().st_size / (1024 * 1024)
            print(f"   Size: {excel_size_mb:.1f} MB")
        
        # Clean up the ZIP file (optional - save disk space)
        zip_path.unlink()
        print(f"   Cleaned up ZIP file")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to extract ZIP file")
        print(f"   Error details: {e}")
        return False
    


def load_uci_dataset(verbose=True):
    """
    Load the UCI Online Retail II dataset into a Pandas DataFrame.
    
    This function:
    1. Checks if the dataset exists in data/raw/
    2. If not found, automatically calls download_uci_dataset()
    3. Loads both Excel sheets (2009-2010 and 2010-2011)
    4. Combines them into a single DataFrame
    5. Returns the complete dataset
    
    Args:
        verbose (bool): If True, print detailed loading progress
                        If False, load silently
    
    Returns:
        pd.DataFrame: Combined dataset with all transactions
        
    Raises:
        FileNotFoundError: If dataset cannot be found or downloaded
        
    Example:
        >>> df = load_uci_dataset()
        📊 Loading dataset...
        ✅ Loaded 1,067,371 rows
        
        >>> df = load_uci_dataset(verbose=False)
        (loads silently, no output)
    """
    
    if verbose:
        print("\n" + "=" * 70)
        print(" " * 20 + "📊 DATASET LOADER")
        print("=" * 70)
    
    # Define path to look for Excel file
    data_dir = Path("data/raw")
    
    # Look for any Excel files in data/raw/
    excel_files = list(data_dir.glob("*.xlsx"))
    
    # If no Excel file found, try to download it
    if not excel_files:
        if verbose:
            print("\n⚠️  Dataset not found in data/raw/")
            print("   Attempting automatic download...\n")
        
        # Call the download function we built earlier
        success = download_uci_dataset()
        
        # If download failed, we can't continue
        if not success:
            raise FileNotFoundError(
                f"Dataset not found and download failed.\n"
                f"Please manually download from:\n"
                f"https://archive.ics.uci.edu/dataset/502/online+retail+ii\n"
                f"and save to: {data_dir.absolute()}"
            )
        
        # After successful download, look for Excel file again
        excel_files = list(data_dir.glob("*.xlsx"))
    
    # At this point, we should have the Excel file
    excel_path = excel_files[0]
    
    if verbose:
        print(f"\n📂 Loading file: {excel_path.name}")
        print(f"   Location: {excel_path.absolute()}")
        print(f"\n⏳ Reading Excel file...")
        print(f"   This takes 30-60 seconds (1M+ rows)...")
    
    try:
        # Load first sheet (Year 2009-2010)
        if verbose:
            print(f"\n   📄 Reading sheet: 'Year 2009-2010'...")
        
        df_2009_2010 = pd.read_excel(
            excel_path,
            sheet_name='Year 2009-2010',
            engine='openpyxl'
        )
        
        if verbose:
            print(f"      ✅ Loaded {len(df_2009_2010):,} rows")
        
        # Load second sheet (Year 2010-2011)
        if verbose:
            print(f"   📄 Reading sheet: 'Year 2010-2011'...")
        
        df_2010_2011 = pd.read_excel(
            excel_path,
            sheet_name='Year 2010-2011',
            engine='openpyxl'
        )
        
        if verbose:
            print(f"      ✅ Loaded {len(df_2010_2011):,} rows")
        
        # Combine both DataFrames into one
        if verbose:
            print(f"\n   🔗 Combining both years into single dataset...")
        
        df = pd.concat([df_2009_2010, df_2010_2011], ignore_index=True)
        
        if verbose:
            print(f"\n✅ Dataset loaded successfully!")
            print(f"   Total rows: {len(df):,}")
            print(f"   Total columns: {len(df.columns)}")
            print(f"   Date range: {df['InvoiceDate'].min()} to {df['InvoiceDate'].max()}")
            
            # Calculate memory usage
            memory_mb = df.memory_usage(deep=True).sum() / (1024 ** 2)
            print(f"   Memory usage: {memory_mb:.1f} MB")
        
        return df
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to load Excel file")
        print(f"   Error details: {e}")
        print(f"\n   Possible causes:")
        print(f"   - File is corrupted (try deleting and re-downloading)")
        print(f"   - Missing openpyxl package (run: pip install openpyxl)")
        print(f"   - Insufficient memory (dataset needs ~150 MB RAM)")
        raise


def display_dataset_info(df):
    """
    Display comprehensive information about the dataset.
    
    Shows:
    - Dataset dimensions (rows × columns)
    - Column names and data types
    - Missing value statistics
    - Sample rows
    
    Args:
        df (pd.DataFrame): The dataset to analyze
        
    Returns:
        None (prints information to console)
    """
    
    print("\n" + "=" * 70)
    print(" " * 22 + "📋 DATASET INFO")
    print("=" * 70)
    
    # Display shape
    print(f"\n📏 DIMENSIONS:")
    print(f"   Rows: {df.shape[0]:,}")
    print(f"   Columns: {df.shape[1]}")
    
    # Display column information
    print(f"\n📊 COLUMNS:")
    for i, col in enumerate(df.columns, 1):
        dtype = df[col].dtype
        non_null = df[col].count()
        null_count = len(df) - non_null
        print(f"   {i}. {col:<20} (type: {dtype}, missing: {null_count:,})")
    
    # Display data types summary
    print(f"\n🔍 DATA TYPES SUMMARY:")
    dtype_counts = df.dtypes.value_counts()
    for dtype, count in dtype_counts.items():
        print(f"   {dtype}: {count} columns")
    
    # Display missing values
    print(f"\n❓ MISSING VALUES:")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    
    missing_df = pd.DataFrame({
        'Column': missing.index,
        'Missing': missing.values,
        'Percentage': missing_pct.values
    })
    
    # Only show columns with missing values
    missing_df = missing_df[missing_df['Missing'] > 0]
    
    if len(missing_df) > 0:
        print(missing_df.to_string(index=False))
    else:
        print("   ✅ No missing values!")
    
    # Display sample data
    print(f"\n👀 SAMPLE DATA (first 3 rows):")
    print("-" * 70)
    
    # Set display options for better formatting
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_colwidth', 30)
    
    print(df.head(3).to_string(index=False))
    print("-" * 70)
    
    # Display basic statistics for numeric columns
    print(f"\n📈 NUMERIC COLUMN STATISTICS:")
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
    if len(numeric_cols) > 0:
        print(df[numeric_cols].describe().to_string())
    else:
        print("   No numeric columns found.")


def save_sample_csv(df, output_path="data/raw/sample_sales.csv", n_rows=1000):
    """
    Save a sample of the dataset as CSV for testing.
    
    Creates a smaller CSV file (default 1000 rows) for quick testing
    without loading the entire 1M+ row dataset.
    
    Args:
        df (pd.DataFrame): The full dataset
        output_path (str): Where to save the sample CSV
        n_rows (int): Number of rows to include in sample (default: 1000)
        
    Returns:
        Path: Path object pointing to the saved CSV file
        
    Example:
        >>> df = load_uci_dataset()
        >>> sample_path = save_sample_csv(df, n_rows=500)
        💾 Saved 500 rows to data/raw/sample_sales.csv
    """
    
    # Take first n_rows from the dataset
    sample = df.head(n_rows).copy()
    
    # Convert to Path object
    output_path = Path(output_path)
    
    # Create parent directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    sample.to_csv(output_path, index=False)
    
    # Calculate file size
    file_size_kb = output_path.stat().st_size / 1024
    
    print(f"\n💾 SAVED SAMPLE CSV:")
    print(f"   Rows: {len(sample):,} (from {len(df):,} total)")
    print(f"   File: {output_path.name}")
    print(f"   Location: {output_path.absolute()}")
    print(f"   Size: {file_size_kb:.1f} KB")
    
    return output_path


# ============================================================================
# MAIN EXECUTION BLOCK
# ============================================================================

if __name__ == "__main__":
    """
    Test the data loader module independently.
    
    This code only runs when you execute this file directly:
        python src/utils/data_loader.py
    
    It does NOT run when you import this module in other files:
        from src.utils.data_loader import load_uci_dataset
    
    This allows the file to be both:
    - A reusable module (functions can be imported)
    - A standalone test script (verify it works)
    """
    
    print("\n" + "🎯" * 35)
    print(" " * 22 + "DATA LOADER TEST")
    print("🎯" * 35)
    
    try:
        # ====================================================================
        # TEST 1: Download Dataset
        # ====================================================================
        print("\n" + "=" * 70)
        print("TEST 1: Download Dataset")
        print("=" * 70)
        
        download_success = download_uci_dataset()
        
        if download_success:
            print("✅ Download test passed!")
        else:
            print("⚠️  Download skipped or failed (see messages above)")
        
        # ====================================================================
        # TEST 2: Load Dataset into Pandas
        # ====================================================================
        print("\n" + "=" * 70)
        print("TEST 2: Load Dataset into Pandas")
        print("=" * 70)
        
        df = load_uci_dataset(verbose=True)
        
        # Verify it loaded correctly
        assert df is not None, "DataFrame is None"
        assert len(df) > 0, "DataFrame is empty"
        assert len(df.columns) == 8, f"Expected 8 columns, got {len(df.columns)}"
        
        print("✅ Load test passed!")
        
        # ====================================================================
        # TEST 3: Display Dataset Information
        # ====================================================================
        print("\n" + "=" * 70)
        print("TEST 3: Display Dataset Information")
        print("=" * 70)
        
        display_dataset_info(df)
        
        print("✅ Info display test passed!")
        
        # ====================================================================
        # TEST 4: Save Sample CSV
        # ====================================================================
        print("\n" + "=" * 70)
        print("TEST 4: Save Sample CSV (1000 rows)")
        print("=" * 70)
        
        sample_path = save_sample_csv(df, n_rows=1000)
        
        # Verify file was created
        assert sample_path.exists(), "Sample CSV file was not created"
        
        print("✅ Sample CSV test passed!")
        
        # ====================================================================
        # ALL TESTS PASSED
        # ====================================================================
        print("\n" + "=" * 70)
        print("✅ " * 17 + "✅")
        print(" " * 20 + "ALL TESTS PASSED!")
        print("✅ " * 17 + "✅")
        print("=" * 70)
        
        print("\n📌 SUMMARY:")
        print(f"   Dataset location: data/raw/online_retail_II.xlsx")
        print(f"   Total rows: {len(df):,}")
        print(f"   Sample CSV: {sample_path}")
        
    except Exception as e:
        # ====================================================================
        # TEST FAILED
        # ====================================================================
        print("\n" + "=" * 70)
        print("❌ " * 17 + "❌")
        print(" " * 22 + "TEST FAILED")
        print("❌ " * 17 + "❌")
        print("=" * 70)
        
        print(f"\n💥 Error occurred:")
        print(f"   {type(e).__name__}: {e}")
        
        print(f"\n📌 Troubleshooting:")
        print(f"   1. Check error message above")
        print(f"   2. Verify internet connection (if download failed)")
        print(f"   3. Check disk space (needs ~50 MB free)")
        print(f"   4. Ensure openpyxl is installed: pip install openpyxl")
        
        # Exit with error code
        sys.exit(1)