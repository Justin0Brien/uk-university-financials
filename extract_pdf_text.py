#!/usr/bin/env python3
"""
Extract text from PDF financial documents with multi-column layout support.

This script processes downloaded PDF files and extracts text while:
- Preserving multi-column layouts and reading order
- Handling tables and structured data
- Maintaining proper text flow and formatting
- Creating organized output with metadata
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import pdfplumber
except ImportError:
    print("ERROR: pdfplumber not installed. Install with: pip install pdfplumber")
    sys.exit(1)

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # Fallback: no colors
    class Fore:
        GREEN = YELLOW = RED = CYAN = BLUE = MAGENTA = ""
    class Style:
        RESET_ALL = BRIGHT = ""

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


# Configure logging
def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration with file and console handlers."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"extract_text_{timestamp}.log"
    
    # File handler - always DEBUG level
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler - INFO or DEBUG based on verbose flag
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"Logging initialized. Log file: {log_file}")


def colored_text(text: str, color: str) -> str:
    """Return colored text if colorama is available."""
    if COLORAMA_AVAILABLE:
        return f"{color}{text}{Style.RESET_ALL}"
    return text


def extract_text_from_pdf(pdf_path: Path, extract_tables: bool = True) -> Dict:
    """
    Extract text from a PDF file with multi-column layout support.
    
    Args:
        pdf_path: Path to the PDF file
        extract_tables: Whether to also extract tables
        
    Returns:
        Dictionary containing extracted text and metadata
    """
    result = {
        'file': str(pdf_path),
        'pages': [],
        'metadata': {},
        'total_pages': 0,
        'success': False,
        'error': None
    }
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            result['total_pages'] = len(pdf.pages)
            result['metadata'] = pdf.metadata or {}
            
            logging.debug(f"Processing {len(pdf.pages)} pages from {pdf_path.name}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_data = {
                    'page_number': page_num,
                    'text': '',
                    'tables': [],
                    'width': page.width,
                    'height': page.height
                }
                
                # Extract text - pdfplumber handles multi-column layouts well
                # by default, processing left-to-right, top-to-bottom
                try:
                    text = page.extract_text(layout=True, x_tolerance=3, y_tolerance=3)
                    if text:
                        page_data['text'] = text.strip()
                        logging.debug(f"Page {page_num}: Extracted {len(text)} characters")
                    else:
                        logging.debug(f"Page {page_num}: No text extracted")
                except Exception as e:
                    logging.warning(f"Page {page_num}: Text extraction error: {e}")
                
                # Extract tables if requested
                if extract_tables:
                    try:
                        tables = page.extract_tables()
                        if tables:
                            # Convert tables to list of lists and clean
                            for table_idx, table in enumerate(tables):
                                cleaned_table = []
                                for row in table:
                                    cleaned_row = [
                                        cell.strip() if cell else '' 
                                        for cell in row
                                    ]
                                    if any(cleaned_row):  # Skip empty rows
                                        cleaned_table.append(cleaned_row)
                                
                                if cleaned_table:
                                    page_data['tables'].append(cleaned_table)
                            
                            logging.debug(f"Page {page_num}: Extracted {len(tables)} tables")
                    except Exception as e:
                        logging.warning(f"Page {page_num}: Table extraction error: {e}")
                
                result['pages'].append(page_data)
            
            result['success'] = True
            
    except Exception as e:
        result['error'] = str(e)
        logging.error(f"Failed to process {pdf_path.name}: {e}")
    
    return result


def save_extracted_text(result: Dict, output_dir: Path, format: str = 'txt') -> Optional[Path]:
    """
    Save extracted text to file.
    
    Args:
        result: Extraction result dictionary
        output_dir: Directory to save output
        format: Output format ('txt', 'json', or 'both')
        
    Returns:
        Path to saved file(s) or None if failed
    """
    if not result['success']:
        return None
    
    pdf_path = Path(result['file'])
    base_name = pdf_path.stem
    
    saved_files = []
    
    try:
        # Save as TXT
        if format in ('txt', 'both'):
            txt_path = output_dir / f"{base_name}.txt"
            with open(txt_path, 'w', encoding='utf-8') as f:
                # Write metadata header
                f.write("=" * 80 + "\n")
                f.write(f"PDF: {pdf_path.name}\n")
                f.write(f"Pages: {result['total_pages']}\n")
                if result['metadata']:
                    f.write(f"Title: {result['metadata'].get('Title', 'N/A')}\n")
                    f.write(f"Author: {result['metadata'].get('Author', 'N/A')}\n")
                    f.write(f"Subject: {result['metadata'].get('Subject', 'N/A')}\n")
                f.write("=" * 80 + "\n\n")
                
                # Write page content
                for page in result['pages']:
                    f.write(f"\n{'='*80}\n")
                    f.write(f"PAGE {page['page_number']}\n")
                    f.write(f"{'='*80}\n\n")
                    
                    if page['text']:
                        f.write(page['text'])
                        f.write("\n\n")
                    
                    # Write tables
                    if page['tables']:
                        f.write(f"\n--- TABLES ON PAGE {page['page_number']} ---\n\n")
                        for table_idx, table in enumerate(page['tables'], 1):
                            f.write(f"Table {table_idx}:\n")
                            # Simple table formatting
                            for row in table:
                                f.write(" | ".join(row) + "\n")
                            f.write("\n")
            
            saved_files.append(txt_path)
            logging.debug(f"Saved TXT: {txt_path}")
        
        # Save as JSON
        if format in ('json', 'both'):
            json_path = output_dir / f"{base_name}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            saved_files.append(json_path)
            logging.debug(f"Saved JSON: {json_path}")
        
        return saved_files[0] if saved_files else None
        
    except Exception as e:
        logging.error(f"Failed to save extracted text for {base_name}: {e}")
        return None


def find_pdf_files(input_dir: Path, recursive: bool = True) -> List[Path]:
    """Find all PDF files in a directory."""
    if recursive:
        pdf_files = list(input_dir.rglob("*.pdf"))
    else:
        pdf_files = list(input_dir.glob("*.pdf"))
    
    return sorted(pdf_files)


def process_pdfs(
    input_dir: Path,
    output_dir: Path,
    extract_tables: bool = True,
    format: str = 'txt',
    recursive: bool = True,
    limit: Optional[int] = None,
    verbose: bool = False
) -> Dict:
    """
    Process all PDF files in a directory.
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Directory to save extracted text
        extract_tables: Whether to extract tables
        format: Output format ('txt', 'json', or 'both')
        recursive: Whether to search subdirectories
        limit: Maximum number of files to process (for testing)
        verbose: Enable verbose logging
        
    Returns:
        Dictionary with processing statistics
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find PDF files
    logging.info(f"Searching for PDF files in {input_dir}")
    pdf_files = find_pdf_files(input_dir, recursive=recursive)
    
    if not pdf_files:
        logging.warning(f"No PDF files found in {input_dir}")
        return {
            'total_files': 0,
            'successful': 0,
            'failed': 0,
            'total_pages': 0
        }
    
    if limit:
        pdf_files = pdf_files[:limit]
        logging.info(f"Limiting to {limit} files for testing")
    
    logging.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Statistics
    stats = {
        'total_files': len(pdf_files),
        'successful': 0,
        'failed': 0,
        'total_pages': 0,
        'failed_files': []
    }
    
    # Process files
    iterator = tqdm(pdf_files, desc="Extracting text", unit="file") if TQDM_AVAILABLE else pdf_files
    
    for pdf_path in iterator:
        if not TQDM_AVAILABLE:
            logging.info(f"Processing {pdf_path.name}")
        
        # Extract text
        result = extract_text_from_pdf(pdf_path, extract_tables=extract_tables)
        
        if result['success']:
            # Save extracted text
            saved_path = save_extracted_text(result, output_dir, format=format)
            if saved_path:
                stats['successful'] += 1
                stats['total_pages'] += result['total_pages']
                if verbose:
                    logging.info(colored_text(
                        f"✓ {pdf_path.name}: {result['total_pages']} pages",
                        Fore.GREEN
                    ))
            else:
                stats['failed'] += 1
                stats['failed_files'].append(str(pdf_path))
                logging.error(colored_text(
                    f"✗ {pdf_path.name}: Failed to save",
                    Fore.RED
                ))
        else:
            stats['failed'] += 1
            stats['failed_files'].append(str(pdf_path))
            logging.error(colored_text(
                f"✗ {pdf_path.name}: {result['error']}",
                Fore.RED
            ))
    
    return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract text from PDF financial documents with multi-column layout support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract text from all PDFs in downloads directory (TXT format)
  python extract_pdf_text.py downloads_20241122_194849 -o extracted_text
  
  # Extract with tables, save as both TXT and JSON
  python extract_pdf_text.py downloads_20241122_194849 -o extracted_text -f both
  
  # Test with first 5 files only, verbose output
  python extract_pdf_text.py downloads_20241122_194849 -o test_output --limit 5 -v
  
  # Extract without tables (faster)
  python extract_pdf_text.py downloads_20241122_194849 -o extracted_text --no-tables
        """
    )
    
    parser.add_argument(
        'input_dir',
        type=str,
        help='Directory containing PDF files to process'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='extracted_text',
        help='Output directory for extracted text (default: extracted_text)'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['txt', 'json', 'both'],
        default='txt',
        help='Output format (default: txt)'
    )
    
    parser.add_argument(
        '--no-tables',
        action='store_true',
        help='Skip table extraction (faster processing)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='Do not search subdirectories'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of files to process (for testing)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    
    # Validate input directory
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        logging.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    
    if not input_dir.is_dir():
        logging.error(f"Input path is not a directory: {input_dir}")
        sys.exit(1)
    
    output_dir = Path(args.output)
    
    # Print header
    print(colored_text("\n" + "=" * 80, Fore.CYAN))
    print(colored_text("PDF Text Extraction Tool", Fore.CYAN))
    print(colored_text("=" * 80 + "\n", Fore.CYAN))
    
    logging.info(f"Input directory: {input_dir}")
    logging.info(f"Output directory: {output_dir}")
    logging.info(f"Output format: {args.format}")
    logging.info(f"Extract tables: {not args.no_tables}")
    logging.info(f"Recursive search: {not args.no_recursive}")
    
    # Process PDFs
    stats = process_pdfs(
        input_dir=input_dir,
        output_dir=output_dir,
        extract_tables=not args.no_tables,
        format=args.format,
        recursive=not args.no_recursive,
        limit=args.limit,
        verbose=args.verbose
    )
    
    # Print summary
    print(colored_text("\n" + "=" * 80, Fore.CYAN))
    print(colored_text("Extraction Summary", Fore.CYAN))
    print(colored_text("=" * 80, Fore.CYAN))
    print(f"Total PDF files: {stats['total_files']}")
    print(colored_text(f"Successfully processed: {stats['successful']}", Fore.GREEN))
    print(colored_text(f"Failed: {stats['failed']}", Fore.RED if stats['failed'] > 0 else Fore.GREEN))
    print(f"Total pages extracted: {stats['total_pages']}")
    
    if stats['failed_files'] and args.verbose:
        print(colored_text("\nFailed files:", Fore.YELLOW))
        for failed_file in stats['failed_files']:
            print(f"  - {failed_file}")
    
    print(colored_text(f"\nExtracted text saved to: {output_dir}", Fore.CYAN))
    print(colored_text("=" * 80 + "\n", Fore.CYAN))
    
    logging.info("Text extraction completed successfully")


if __name__ == "__main__":
    main()
