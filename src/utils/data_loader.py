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