#!/usr/bin/env python3
"""
Consolidate PDFs from old timestamped download directories into the unified downloads/pdfs/ structure.
This ensures all PDFs are in one location for git syncing.
"""

import shutil
from pathlib import Path


def main():
    project_root = Path(__file__).parent
    old_dirs = sorted(project_root.glob('downloads_*'))
    
    if not old_dirs:
        print("✓ No old download directories found")
        return
    
    target_dir = project_root / 'downloads' / 'pdfs'
    target_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Found {len(old_dirs)} old download directories to consolidate")
    print(f"Target directory: {target_dir}\n")
    
    total_pdfs = 0
    moved_pdfs = 0
    skipped_pdfs = 0
    
    for old_dir in old_dirs:
        pdfs = list(old_dir.glob('*.pdf'))
        if not pdfs:
            continue
        
        print(f"Processing {old_dir.name}: {len(pdfs)} PDFs")
        total_pdfs += len(pdfs)
        
        for pdf in pdfs:
            target_file = target_dir / pdf.name
            
            # Check if file already exists
            if target_file.exists():
                # Check if they're the same file
                if target_file.stat().st_size == pdf.stat().st_size:
                    skipped_pdfs += 1
                    continue
                else:
                    # Different file with same name, keep both
                    base = pdf.stem
                    ext = pdf.suffix
                    counter = 1
                    while target_file.exists():
                        target_file = target_dir / f"{base}_{counter}{ext}"
                        counter += 1
            
            # Move the file
            shutil.copy2(pdf, target_file)
            moved_pdfs += 1
    
    print(f"\n✅ Consolidation complete!")
    print(f"   Total PDFs found: {total_pdfs}")
    print(f"   Moved: {moved_pdfs}")
    print(f"   Skipped (duplicates): {skipped_pdfs}")
    print(f"\n📁 All PDFs now in: {target_dir}")
    print(f"\n🗑️  You can now safely delete old directories with:")
    print(f"   rm -rf downloads_*/")


if __name__ == '__main__':
    main()
