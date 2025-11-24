#!/usr/bin/env python3
"""
Verify iCloud Drive setup for University Financials project.

This script checks that:
1. iCloud Drive path exists and is accessible
2. Required directories are present
3. Data files are synced and available
4. CSV tracker is properly configured

Run this script after cloning the repository on a new machine to ensure
everything is set up correctly.
"""

import sys
from pathlib import Path


def get_icloud_base_path():
    """Get the base iCloud path for the project."""
    return Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Nexus" / "Resources" / "Reference Data" / "unimetrics"


def check_icloud_path():
    """Check if iCloud Drive path exists."""
    icloud_base = get_icloud_base_path()
    print("\n🔍 Checking iCloud Drive Setup\n")
    print(f"📂 Expected path: {icloud_base}")
    
    if not icloud_base.exists():
        print("❌ ERROR: iCloud path does not exist")
        print("\nPossible solutions:")
        print("1. Ensure iCloud Drive is enabled in System Preferences")
        print("2. Create the directory manually:")
        print(f"   mkdir -p '{icloud_base}'")
        print("3. Check that the path matches your iCloud Drive location")
        return False
    
    print("✅ iCloud base path exists")
    return True


def check_directories():
    """Check if required data directories exist."""
    icloud_base = get_icloud_base_path()
    downloads_dir = icloud_base / "downloads" / "pdfs"
    extracted_dir = icloud_base / "extracted_text"
    
    print("\n📁 Checking Data Directories\n")
    
    all_exist = True
    
    if downloads_dir.exists():
        pdf_count = len(list(downloads_dir.glob("*.pdf")))
        print(f"✅ Downloads directory exists: {downloads_dir}")
        print(f"   Contains {pdf_count} PDF files")
    else:
        print(f"⚠️  Downloads directory missing: {downloads_dir}")
        print("   (Will be created automatically on first run)")
        all_exist = False
    
    if extracted_dir.exists():
        txt_count = len(list(extracted_dir.glob("*.txt")))
        json_count = len(list(extracted_dir.glob("*.json")))
        print(f"✅ Extracted text directory exists: {extracted_dir}")
        print(f"   Contains {txt_count} .txt files, {json_count} .json files")
    else:
        print(f"⚠️  Extracted text directory missing: {extracted_dir}")
        print("   (Will be created automatically on first run)")
        all_exist = False
    
    return all_exist


def check_csv_tracker():
    """Check CSV tracker file."""
    csv_path = Path(__file__).parent / "financial_data_tracker.csv"
    
    print("\n📊 Checking CSV Tracker\n")
    
    if not csv_path.exists():
        print(f"❌ CSV tracker not found: {csv_path}")
        print("   This file should be in the git repository")
        return False
    
    print(f"✅ CSV tracker exists: {csv_path}")
    
    # Read CSV and check for iCloud-relative paths
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            total_rows = len(lines) - 1  # Exclude header
            
            # Count rows with data
            rows_with_pdfs = sum(1 for line in lines[1:] if ',downloads/pdfs/' in line)
            rows_with_text = sum(1 for line in lines[1:] if ',extracted_text/' in line)
            
            print(f"   Total records: {total_rows}")
            print(f"   Records with PDFs: {rows_with_pdfs}")
            print(f"   Records with extracted text: {rows_with_text}")
            
            # Check path format
            if rows_with_pdfs > 0 or rows_with_text > 0:
                print(f"   ✓ Using iCloud-relative paths (downloads/pdfs/...)")
            
    except Exception as e:
        print(f"⚠️  Could not read CSV: {e}")
        return False
    
    return True


def check_icloud_sync_status():
    """Check if iCloud is actively syncing."""
    icloud_base = get_icloud_base_path()
    
    print("\n☁️  iCloud Sync Status\n")
    
    if not icloud_base.exists():
        print("⚠️  Cannot check sync status - iCloud path doesn't exist")
        return False
    
    print("To check sync status in Finder:")
    print("1. Open Finder")
    print("2. Navigate to: iCloud Drive → Nexus → Resources → Reference Data → unimetrics")
    print("3. Look for cloud icons next to files:")
    print("   ☁️  = Not downloaded (cloud)")
    print("   ⬇️  = Downloading (cloud with down arrow)")
    print("   ✓  = Downloaded and synced (checkmark)")
    print("\nNote: If you see cloud icons, wait for sync to complete before running the coordinator")
    
    return True


def main():
    """Run all verification checks."""
    print("=" * 70)
    print("University Financials - iCloud Setup Verification")
    print("=" * 70)
    
    # Run all checks
    icloud_ok = check_icloud_path()
    
    if not icloud_ok:
        print("\n" + "=" * 70)
        print("❌ FAILED: iCloud Drive is not properly configured")
        print("=" * 70)
        sys.exit(1)
    
    dirs_ok = check_directories()
    csv_ok = check_csv_tracker()
    check_icloud_sync_status()
    
    print("\n" + "=" * 70)
    
    if icloud_ok and csv_ok:
        print("✅ SUCCESS: iCloud setup verified!")
        
        if not dirs_ok:
            print("\nNote: Data directories will be created automatically on first run")
        
        print("\nYou can now run the coordinator:")
        print("  python run_coordinator.py --summary")
        print("=" * 70)
        sys.exit(0)
    else:
        print("⚠️  WARNING: Some checks failed")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
