#!/usr/bin/env python3
"""
Update financial_data_tracker.csv to use iCloud-relative paths.
All data is now stored in iCloud to avoid GitHub size limits.
"""

import csv
from pathlib import Path


def get_icloud_base_path() -> Path:
    """Get the iCloud storage base path."""
    return Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Nexus" / "Resources" / "Reference Data" / "unimetrics"


def to_icloud_relative_path(path_str: str) -> str:
    """
    Convert any path to path relative to iCloud base directory.
    Returns empty string if path is None or empty.
    """
    if not path_str:
        return ""
    
    path = Path(path_str)
    icloud_base = get_icloud_base_path()
    
    # If already relative and starts with downloads/ or extracted_text/, keep as-is
    if not path.is_absolute() and (str(path).startswith('downloads/') or str(path).startswith('extracted_text/')):
        return str(path)
    
    # If absolute, try to make relative to iCloud
    if path.is_absolute():
        try:
            rel_path = path.relative_to(icloud_base)
            return str(rel_path)
        except ValueError:
            pass
    
    # If it's a relative path from old project structure, convert it
    path_str = str(path)
    if path_str.startswith('downloads_'):
        # Old timestamped directory - extract filename and put in downloads/pdfs
        filename = Path(path_str).name
        return f"downloads/pdfs/{filename}"
    elif path_str.startswith('extracted_text/'):
        # Already correct relative path
        return path_str
    elif '/' in path_str:
        # Has subdirectories, try to extract meaningful part
        parts = Path(path_str).parts
        if 'downloads' in parts:
            idx = parts.index('downloads')
            return str(Path(*parts[idx:]))
        elif 'extracted_text' in parts:
            idx = parts.index('extracted_text')
            return str(Path(*parts[idx:]))
    
    # Fallback: return as-is
    return path_str


def main():
    csv_path = Path('financial_data_tracker.csv')
    backup_path = Path('financial_data_tracker_icloud_backup.csv')
    
    if not csv_path.exists():
        print(f"Error: {csv_path} not found")
        return
    
    # Create backup
    import shutil
    shutil.copy(csv_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    
    # Read CSV
    rows = []
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            rows.append(row)
    
    print(f"✓ Loaded {len(rows)} rows from CSV")
    
    # Convert paths
    converted_count = 0
    for row in rows:
        if row.get('pdf_path'):
            old_path = row['pdf_path']
            row['pdf_path'] = to_icloud_relative_path(old_path)
            if old_path != row['pdf_path']:
                converted_count += 1
        
        if row.get('txt_path'):
            old_path = row['txt_path']
            row['txt_path'] = to_icloud_relative_path(old_path)
            if old_path != row['txt_path']:
                converted_count += 1
        
        if row.get('json_path'):
            old_path = row['json_path']
            row['json_path'] = to_icloud_relative_path(old_path)
            if old_path != row['json_path']:
                converted_count += 1
    
    print(f"✓ Converted {converted_count} paths to iCloud-relative")
    
    # Write updated CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Saved updated CSV: {csv_path}")
    
    # Show examples
    print(f"\n📝 Sample paths (first 3 with PDF):")
    count = 0
    for row in rows:
        if row.get('pdf_path') and count < 3:
            print(f"   {row['pdf_path']}")
            count += 1
    
    print(f"\n✅ Migration complete!")
    print(f"   Paths now relative to: ~/Library/Mobile Documents/.../unimetrics/")
    print(f"   Original backed up to: {backup_path}")


if __name__ == '__main__':
    main()
