#!/usr/bin/env python3
"""
Migrate financial_data_tracker.csv to use relative paths instead of absolute paths.
This makes the CSV portable across different machines and git-syncable.
"""

import csv
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.resolve()


def to_relative_path(abs_path: str) -> str:
    """
    Convert absolute path to relative path from project root.
    Returns empty string if path is None or empty.
    """
    if not abs_path:
        return ""
    
    abs_path = Path(abs_path)
    project_root = get_project_root()
    
    try:
        rel_path = abs_path.relative_to(project_root)
        return str(rel_path)
    except ValueError:
        # Path is not relative to project root
        print(f"Warning: Path not within project root: {abs_path}")
        return str(abs_path)


def main():
    csv_path = Path('financial_data_tracker.csv')
    backup_path = Path('financial_data_tracker_backup.csv')
    
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
            row['pdf_path'] = to_relative_path(old_path)
            if old_path != row['pdf_path']:
                converted_count += 1
        
        if row.get('txt_path'):
            old_path = row['txt_path']
            row['txt_path'] = to_relative_path(old_path)
            if old_path != row['txt_path']:
                converted_count += 1
        
        if row.get('json_path'):
            old_path = row['json_path']
            row['json_path'] = to_relative_path(old_path)
            if old_path != row['json_path']:
                converted_count += 1
    
    print(f"✓ Converted {converted_count} paths to relative")
    
    # Write updated CSV
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"✓ Saved updated CSV: {csv_path}")
    print(f"\n✅ Migration complete!")
    print(f"   Original backed up to: {backup_path}")
    print(f"   If there are issues, restore with: cp {backup_path} {csv_path}")


if __name__ == '__main__':
    main()
