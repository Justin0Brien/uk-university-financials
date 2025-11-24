#!/usr/bin/env python3
"""
Financial Data Coordinator - Intelligently fills gaps in university financial data.

This coordinator script:
1. Analyzes extracted_text folder to identify available financial years per university
2. Identifies missing years for each university
3. Searches for missing financial reports using targeted queries
4. Downloads newly found PDFs
5. Extracts text from new PDFs
6. Iteratively repeats until no more data can be found

The script works backward in time, attempting to find reports as far back as available.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    class Fore:
        GREEN = YELLOW = RED = CYAN = BLUE = MAGENTA = ""
    class Style:
        RESET_ALL = BRIGHT = ""


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"coordinator_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logging.info(f"Coordinator logging initialized. Log file: {log_file}")


# =============================================================================
# iCloud Storage Configuration
# =============================================================================

def get_icloud_base_path() -> Path:
    """
    Get the iCloud storage base path for university metrics data.
    All data files (PDFs, extracted text) are stored in iCloud to avoid GitHub size limits.
    """
    icloud_path = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Nexus" / "Resources" / "Reference Data" / "unimetrics"
    
    # Ensure directories exist
    (icloud_path / "downloads" / "pdfs").mkdir(parents=True, exist_ok=True)
    (icloud_path / "extracted_text").mkdir(parents=True, exist_ok=True)
    
    return icloud_path


def get_downloads_dir() -> Path:
    """Get the downloads directory in iCloud."""
    return get_icloud_base_path() / "downloads" / "pdfs"


def get_extracted_text_dir() -> Path:
    """Get the extracted text directory in iCloud."""
    return get_icloud_base_path() / "extracted_text"


# =============================================================================
# Path Management - Relative vs Absolute
# =============================================================================

def get_project_root() -> Path:
    """Get the project root directory (where this script is located)."""
    return Path(__file__).parent.resolve()


def to_relative_path(abs_path: str | Path) -> str:
    """
    Convert absolute path to path relative to iCloud base directory.
    If path is already relative, return as-is.
    Returns empty string if path is None or empty.
    
    Examples:
        /Users/justin/Library/.../unimetrics/downloads/pdfs/file.pdf -> downloads/pdfs/file.pdf
        /Users/justin/Library/.../unimetrics/extracted_text/file.txt -> extracted_text/file.txt
        downloads/pdfs/file.pdf -> downloads/pdfs/file.pdf (already relative)
    """
    if not abs_path:
        return ""
    
    abs_path = Path(abs_path)
    
    # If already relative, return as-is
    if not abs_path.is_absolute():
        return str(abs_path)
    
    icloud_base = get_icloud_base_path()
    
    try:
        # Get path relative to iCloud base
        rel_path = abs_path.relative_to(icloud_base)
        return str(rel_path)
    except ValueError:
        # Path is absolute but not within iCloud base
        logging.warning(f"Path {abs_path} is not within iCloud base {icloud_base}")
        return str(abs_path)


def to_absolute_path(rel_path: str | Path) -> Path:
    """
    Convert relative path to absolute path based on iCloud base directory.
    If path is already absolute, return as-is.
    Returns None if path is None or empty.
    
    Examples:
        downloads/pdfs/file.pdf -> /Users/justin/Library/.../unimetrics/downloads/pdfs/file.pdf
        extracted_text/file.txt -> /Users/justin/Library/.../unimetrics/extracted_text/file.txt
    """
    if not rel_path:
        return None
    
    rel_path = Path(rel_path)
    
    # If already absolute, return as-is
    if rel_path.is_absolute():
        return rel_path
    
    # Make relative to iCloud base
    icloud_base = get_icloud_base_path()
    return (icloud_base / rel_path).resolve()


# =============================================================================
# HESA Provider Data (UKPRN Lookup)
# =============================================================================

# Global cache for HESA provider data
_HESA_PROVIDERS = None

def load_hesa_providers(csv_path: str = "ProviderAllHESAEnhanced.csv") -> Dict:
    """
    Load HESA provider data with UKPRN and standardized names.
    
    Returns dict with:
        - 'ukprn_to_name': {ukprn -> official_name}
        - 'name_to_ukprn': {normalized_name -> ukprn}
        - 'all_providers': [{ukprn, name, ...}, ...]
    """
    global _HESA_PROVIDERS
    
    if _HESA_PROVIDERS is not None:
        return _HESA_PROVIDERS
    
    csv_file = Path(csv_path)
    if not csv_file.exists():
        logging.warning(f"HESA provider file not found: {csv_path}")
        _HESA_PROVIDERS = {
            'ukprn_to_name': {},
            'name_to_ukprn': {},
            'all_providers': []
        }
        return _HESA_PROVIDERS
    
    ukprn_to_name = {}
    name_to_ukprn = {}
    all_providers = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ukprn = row.get('UKPRN', '').strip()
                name = row.get('ProviderName', '').strip()
                
                # Skip if no UKPRN or name
                if not ukprn or not name:
                    continue
                
                # Store mappings
                ukprn_to_name[ukprn] = name
                
                # Create multiple name variants for matching
                normalized = normalize_name_for_matching(name)
                name_to_ukprn[normalized] = ukprn
                
                # Store provider record
                all_providers.append({
                    'ukprn': ukprn,
                    'name': name,
                    'instid': row.get('INSTID', ''),
                    'country': row.get('CountryCode', ''),
                    'category': row.get('CategoryName', '')
                })
        
        logging.info(f"Loaded {len(ukprn_to_name)} HESA providers with UKPRN")
        
    except Exception as e:
        logging.error(f"Error loading HESA providers: {e}")
        ukprn_to_name = {}
        name_to_ukprn = {}
        all_providers = []
    
    _HESA_PROVIDERS = {
        'ukprn_to_name': ukprn_to_name,
        'name_to_ukprn': name_to_ukprn,
        'all_providers': all_providers
    }
    
    return _HESA_PROVIDERS


def normalize_name_for_matching(name: str) -> str:
    """
    Normalize university name for matching.
    
    Removes common variations to help match filenames to HESA providers.
    """
    # Convert to lowercase
    name = name.lower()
    
    # Remove "the" prefix
    name = re.sub(r'^the\s+', '', name)
    
    # Normalize hyphens and apostrophes
    name = name.replace('-', ' ')
    name = name.replace("'", '')
    
    # Remove "university" suffix variations
    name = re.sub(r'\s+university$', '', name)
    name = re.sub(r'\s+uni$', '', name)
    name = re.sub(r'\s+univ$', '', name)
    
    # Remove "college" variations
    name = re.sub(r'\s+college$', '', name)
    name = re.sub(r'\s+coll$', '', name)
    
    # Remove "of" phrases that vary
    name = re.sub(r'\s+of\s+london$', '', name)
    name = re.sub(r'\s+london$', '', name)
    
    # Remove common trailing words
    name = re.sub(r'\s+bristol$', '', name)
    
    # Normalize whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def match_university_to_ukprn(extracted_name: str) -> Tuple[Optional[str], str]:
    """
    Match an extracted university name to UKPRN from HESA provider list.
    
    Returns:
        (ukprn, official_name) or (None, extracted_name)
    """
    if not extracted_name:
        return None, extracted_name
    
    providers = load_hesa_providers()
    name_to_ukprn = providers['name_to_ukprn']
    ukprn_to_name = providers['ukprn_to_name']
    
    # Manual aliases for common variations
    aliases = {
        'uwe bristol': '10007164',  # University of the West of England, Bristol
        'uwe': '10007164',
        'royal holloway': '10005553',  # Royal Holloway and Bedford New College
        'royal holloway univ': '10005553',
        'royal holloway univ of': '10005553',
        'royal holloway university': '10005553',
        'royal holloway university of': '10005553',
        'royal holloway and bedford': '10005553',
    }
    
    # Check aliases first
    normalized = normalize_name_for_matching(extracted_name)
    if normalized in aliases:
        ukprn = aliases[normalized]
        return ukprn, ukprn_to_name[ukprn]
    
    # Try exact match
    if normalized in name_to_ukprn:
        ukprn = name_to_ukprn[normalized]
        return ukprn, ukprn_to_name[ukprn]
    
    # Try fuzzy matching - check if extracted name contains any provider name
    for hesa_name, ukprn in name_to_ukprn.items():
        if hesa_name in normalized or normalized in hesa_name:
            return ukprn, ukprn_to_name[ukprn]
    
    # Try word-based matching for partial matches
    extracted_words = set(normalized.split())
    best_match = None
    best_score = 0
    
    for hesa_name, ukprn in name_to_ukprn.items():
        hesa_words = set(hesa_name.split())
        common_words = extracted_words & hesa_words
        
        # Score based on overlap
        if len(common_words) >= 2:  # At least 2 words in common
            score = len(common_words) / max(len(extracted_words), len(hesa_words))
            if score > best_score:
                best_score = score
                best_match = ukprn
    
    if best_match and best_score > 0.5:  # 50% word overlap
        return best_match, ukprn_to_name[best_match]
    
    # No match found
    logging.debug(f"No UKPRN match found for: {extracted_name}")
    return None, extracted_name


# =============================================================================
# CSV Tracking System
# =============================================================================

def canonicalize_university_name(name: str) -> str:
    """
    Convert university name to canonical form.
    
    Removes document-specific suffixes like "Infographic", "Annual-Report", etc.
    Standardizes spacing and capitalization.
    """
    # Remove file extensions first
    name = Path(name).stem if '.' in name else name
    
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    
    # Remove common document-type suffixes
    doc_suffixes = [
        'Infographic', 'Annual Report', 'Annual-Report', 'Financial Statements',
        'Financial-Statements', 'Accounts', 'Report', 'Document', 'FS',
        'Final', 'Draft', 'Consolidated', 'Statement', 'Summary'
    ]
    
    for suffix in doc_suffixes:
        # Remove suffix if it appears at the end (case-insensitive)
        if name.lower().endswith(suffix.lower()):
            name = name[:-(len(suffix))].strip()
        # Remove if appears after a space or hyphen
        pattern = rf'\s+{re.escape(suffix)}\b'
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
        pattern = rf'-{re.escape(suffix)}\b'
        name = re.sub(pattern, '', name, flags=re.IGNORECASE)
    
    # Remove year patterns from the name
    # This catches cases like "University Name 2023-24"
    name = re.sub(r'\s*\d{4}[-_]?\d{0,4}\s*$', '', name)
    name = re.sub(r'\s*\d{4}\s*$', '', name)
    
    # Clean up extra whitespace
    name = ' '.join(name.split())
    
    # Remove trailing/leading punctuation
    name = name.strip('-_.,;: ')
    
    # Standardize common abbreviations
    name = name.replace('Univ ', 'University ')
    name = name.replace('Coll ', 'College ')
    
    return name.strip()


def normalize_year_to_ending(year_str: str) -> str:
    """
    Normalize year to ending year format.
    
    Examples:
        "2023-24" -> "2024"
        "2023-2024" -> "2024"
        "2023" -> "2024" (assumes financial year ending in 2024)
        "202324" -> "2024"
    
    Returns the ending year as a 4-digit string.
    """
    if not year_str:
        return ""
    
    # Handle range formats: 2023-24, 2023-2024, 2023_24
    range_match = re.match(r'(\d{4})[-_](\d{2,4})', year_str)
    if range_match:
        start_year = range_match.group(1)
        end_part = range_match.group(2)
        
        if len(end_part) == 2:
            # 2023-24 format
            end_year = start_year[:2] + end_part
        else:
            # 2023-2024 format
            end_year = end_part
        
        return end_year
    
    # Single year: assume it's the starting year, add 1 for ending year
    single_match = re.match(r'(\d{4})$', year_str)
    if single_match:
        start_year = int(single_match.group(1))
        # Financial year starting 2023 ends in 2024
        return str(start_year + 1)
    
    # If we can't parse it, return as-is
    logging.warning(f"Could not normalize year: {year_str}")
    return year_str


def get_file_download_timestamp(file_path: Path) -> str:
    """
    Get the download timestamp for a file.
    
    Tries (in order):
    1. File modification time (mtime)
    2. File creation time (ctime/birthtime)
    
    Returns ISO format timestamp or empty string.
    """
    if not file_path.exists():
        return ""
    
    try:
        # Use modification time as best proxy for download time
        mtime = file_path.stat().st_mtime
        timestamp = datetime.fromtimestamp(mtime)
        return timestamp.isoformat()
    except Exception as e:
        logging.debug(f"Could not get timestamp for {file_path}: {e}")
        return ""


def extract_source_url_from_logs(pdf_filename: str, downloads_dir: Path = None) -> str:
    """
    Extract source URL for a PDF from download logs.
    
    Searches through log files in logs/ directory for download records.
    Looks for "Attempting direct download:" lines followed by the PDF filename.
    """
    logs_dir = Path('logs')
    if not logs_dir.exists():
        return ""
    
    # Search in download log files
    log_patterns = [
        'download_financials_*.log',
        'coordinator_*.log'
    ]
    
    pdf_name = Path(pdf_filename).name
    
    for pattern in log_patterns:
        for log_file in sorted(logs_dir.glob(pattern), reverse=True):
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    
                    # Look for lines mentioning this PDF
                    for i, line in enumerate(lines):
                        if pdf_name in line or pdf_filename in line:
                            # Look backwards for the most recent "Attempting direct download:" line
                            for j in range(i-1, max(0, i-10), -1):
                                if 'Attempting direct download:' in lines[j]:
                                    # Extract URL from this line
                                    url_match = re.search(r'https?://[^\s<>"\']+', lines[j])
                                    if url_match:
                                        url = url_match.group(0)
                                        # Filter out localhost and common non-source URLs
                                        if 'localhost' not in url and 'duckduckgo' not in url:
                                            return url.rstrip('.,;)')
                                    break
            except Exception as e:
                logging.debug(f"Error reading log file {log_file}: {e}")
                continue
    
    return ""


def load_csv_tracker(csv_path: Path) -> List[Dict]:
    """
    Load the CSV tracking file.
    
    Returns list of dicts with keys:
    - id, university, year, source_url, pdf_path, txt_path, json_path
    """
    if not csv_path.exists():
        logging.info(f"CSV tracker doesn't exist yet: {csv_path}")
        return []
    
    rows = []
    with open(csv_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    logging.info(f"Loaded {len(rows)} rows from CSV tracker")
    return rows


def save_csv_tracker(csv_path: Path, rows: List[Dict]) -> None:
    """
    Save the CSV tracking file with relative paths.
    
    Columns: id, ukprn, university, year, source_url, download_timestamp, pdf_path, txt_path, json_path
    Paths are stored as relative to project root (e.g., 'downloads/pdfs/file.pdf')
    """
    # Ensure directory exists
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ['id', 'ukprn', 'university', 'year', 'source_url', 'download_timestamp', 'pdf_path', 'txt_path', 'json_path']
    
    # Convert absolute paths to relative before saving
    rows_to_save = []
    for row in rows:
        row_copy = row.copy()
        if row_copy.get('pdf_path'):
            row_copy['pdf_path'] = to_relative_path(row_copy['pdf_path'])
        if row_copy.get('txt_path'):
            row_copy['txt_path'] = to_relative_path(row_copy['txt_path'])
        if row_copy.get('json_path'):
            row_copy['json_path'] = to_relative_path(row_copy['json_path'])
        rows_to_save.append(row_copy)
    
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_save)
    
    logging.info(f"Saved {len(rows)} rows to CSV tracker: {csv_path}")


def get_next_id(rows: List[Dict]) -> int:
    """Get the next available ID number."""
    if not rows:
        return 1
    
    max_id = max(int(row['id']) for row in rows)
    return max_id + 1


def find_csv_row(rows: List[Dict], university: str, year: str, pdf_path: str = None, ukprn: str = None) -> Optional[Dict]:
    """
    Find a row matching university/UKPRN, year, and optionally pdf_path.
    
    Prefers matching by UKPRN if provided, falls back to university name.
    Returns the matching row or None.
    """
    for row in rows:
        # Match by UKPRN if available
        if ukprn and row.get('ukprn') == ukprn and row['year'] == year:
            if pdf_path is None or row.get('pdf_path', '') == pdf_path:
                return row
        # Fall back to name matching
        elif not ukprn and row['university'] == university and row['year'] == year:
            if pdf_path is None or row.get('pdf_path', '') == pdf_path:
                return row
    return None


def add_placeholder_rows(rows: List[Dict], university: str, years: List[str], ukprn: str = None) -> List[Dict]:
    """
    Add placeholder rows for missing university/year combinations.
    
    Only adds if the combination doesn't already exist.
    Uses UKPRN for identification when available.
    """
    # Get UKPRN and official name if not provided
    if not ukprn:
        ukprn, official_name = match_university_to_ukprn(university)
        if not ukprn:
            # Fall back to canonical name if no UKPRN match
            official_name = canonicalize_university_name(university)
    else:
        providers = load_hesa_providers()
        official_name = providers['ukprn_to_name'].get(ukprn, university)
    
    next_id = get_next_id(rows)
    added_count = 0
    
    for year in years:
        # Normalize year to ending year format
        normalized_year = normalize_year_to_ending(year)
        
        # Check if any row exists for this UKPRN/year combo
        if ukprn:
            existing = [r for r in rows if r.get('ukprn') == ukprn and r['year'] == normalized_year]
        else:
            existing = [r for r in rows if r['university'] == official_name and r['year'] == normalized_year]
        
        if not existing:
            # Add placeholder row
            rows.append({
                'id': str(next_id),
                'ukprn': ukprn or '',
                'university': official_name,
                'year': normalized_year,
                'source_url': '',
                'download_timestamp': '',
                'pdf_path': '',
                'txt_path': '',
                'json_path': ''
            })
            next_id += 1
            added_count += 1
    
    if added_count > 0:
        logging.debug(f"Added {added_count} placeholder rows for {official_name}")
    
    return rows


def update_csv_with_extracted_files(rows: List[Dict], extracted_dir: Path) -> List[Dict]:
    """
    Scan extracted_text directory and update CSV with found files.
    
    Adds rows for any university/year combinations found in extracted files.
    Uses UKPRN for identification and official HESA names.
    """
    txt_files = list(extracted_dir.glob("*.txt"))
    json_files = list(extracted_dir.glob("*.json"))
    
    logging.info(f"Updating CSV with {len(txt_files)} txt files and {len(json_files)} json files")
    
    # Process txt files
    for txt_file in txt_files:
        uni_name_raw = extract_university_name(txt_file.name)
        year_raw = extract_year_from_filename(txt_file.name)
        
        if not uni_name_raw or not year_raw:
            continue
        
        # Match to UKPRN and get official name
        ukprn, official_name = match_university_to_ukprn(uni_name_raw)
        year = normalize_year_to_ending(year_raw)
        
        # Check for invalid years
        try:
            year_int = int(year)
            if year_int < 1990 or year_int > 2100:
                continue
        except (ValueError, IndexError):
            continue
        
        # Find corresponding json file
        json_file = extracted_dir / txt_file.name.replace('.txt', '.json')
        json_path = str(json_file.absolute()) if json_file.exists() else ''
        
        # Try to find matching PDF (look in all downloads_* directories)
        pdf_path = ''
        pdf_file_obj = None
        pdf_search_name = txt_file.stem  # Filename without .txt
        for downloads_dir in Path('.').glob('downloads_*'):
            possible_pdf = downloads_dir / f"{pdf_search_name}.pdf"
            if possible_pdf.exists():
                pdf_path = str(possible_pdf.absolute())
                pdf_file_obj = possible_pdf
                break
        
        # Extract metadata
        source_url = extract_source_url_from_logs(f"{pdf_search_name}.pdf") if pdf_file_obj else ''
        download_timestamp = get_file_download_timestamp(pdf_file_obj) if pdf_file_obj else ''
        
        # Check if row already exists for this file (match by UKPRN if available)
        existing_row = None
        for row in rows:
            # Match by UKPRN if available
            if ukprn and row.get('ukprn') == ukprn and row['year'] == year:
                if row.get('txt_path', '') == str(txt_file.absolute()):
                    existing_row = row
                    break
            # Fall back to name matching
            elif not ukprn and row['university'] == official_name and row['year'] == year:
                if row.get('txt_path', '') == str(txt_file.absolute()):
                    existing_row = row
                    break
        
        if existing_row:
            # Update existing row with metadata and UKPRN
            if ukprn and not existing_row.get('ukprn'):
                existing_row['ukprn'] = ukprn
            if official_name:
                existing_row['university'] = official_name
            existing_row['txt_path'] = str(txt_file.absolute())
            existing_row['json_path'] = json_path
            if pdf_path and not existing_row.get('pdf_path'):
                existing_row['pdf_path'] = pdf_path
            if source_url and not existing_row.get('source_url'):
                existing_row['source_url'] = source_url
            if download_timestamp and not existing_row.get('download_timestamp'):
                existing_row['download_timestamp'] = download_timestamp
        else:
            # Create new row
            next_id = get_next_id(rows)
            rows.append({
                'id': str(next_id),
                'ukprn': ukprn or '',
                'university': official_name,
                'year': year,
                'source_url': source_url,
                'download_timestamp': download_timestamp,
                'pdf_path': pdf_path,
                'txt_path': str(txt_file.absolute()),
                'json_path': json_path
            })
    
    return rows


def update_csv_with_downloads(rows: List[Dict], downloads_dir: Path) -> List[Dict]:
    """
    Scan downloads directory and update CSV with downloaded PDFs.
    
    Updates pdf_path for existing rows or creates new rows.
    Uses UKPRN for identification and official HESA names.
    Extracts source URLs and download timestamps.
    """
    pdf_files = list(downloads_dir.glob("*.pdf"))
    
    logging.info(f"Updating CSV with {len(pdf_files)} downloaded PDF files")
    
    for pdf_file in pdf_files:
        uni_name_raw = extract_university_name(pdf_file.name)
        year_raw = extract_year_from_filename(pdf_file.name)
        
        if not uni_name_raw or not year_raw:
            continue
        
        # Match to UKPRN and get official name
        ukprn, official_name = match_university_to_ukprn(uni_name_raw)
        year = normalize_year_to_ending(year_raw)
        
        if not official_name or not year:
            continue
        
        # Check for invalid years
        try:
            year_int = int(year)
            if year_int < 1990 or year_int > 2100:
                continue
        except (ValueError, IndexError):
            continue
        
        # Extract metadata
        source_url = extract_source_url_from_logs(pdf_file.name)
        download_timestamp = get_file_download_timestamp(pdf_file)
        
        # Look for corresponding txt/json files
        txt_file = Path('extracted_text') / f"{pdf_file.stem}.txt"
        json_file = Path('extracted_text') / f"{pdf_file.stem}.json"
        
        txt_path = str(txt_file.absolute()) if txt_file.exists() else ''
        json_path = str(json_file.absolute()) if json_file.exists() else ''
        
        # Find or create row (match by UKPRN if available)
        existing_row = None
        for row in rows:
            # Match by UKPRN if available
            if ukprn and row.get('ukprn') == ukprn and row['year'] == year and not row.get('pdf_path'):
                existing_row = row
                break
            # Fall back to name matching
            elif not ukprn and row['university'] == official_name and row['year'] == year and not row.get('pdf_path'):
                existing_row = row
                break
        
        if existing_row:
            # Update placeholder row with all metadata and UKPRN
            if ukprn and not existing_row.get('ukprn'):
                existing_row['ukprn'] = ukprn
            if official_name:
                existing_row['university'] = official_name
            existing_row['pdf_path'] = str(pdf_file.absolute())
            existing_row['txt_path'] = txt_path
            existing_row['json_path'] = json_path
            existing_row['source_url'] = source_url
            existing_row['download_timestamp'] = download_timestamp
        else:
            # Check if row exists with this exact PDF (match by UKPRN if available)
            pdf_exists = any(
                (row.get('ukprn') == ukprn if ukprn else row['university'] == official_name) and 
                row['year'] == year and 
                row.get('pdf_path') == str(pdf_file.absolute())
                for row in rows
            )
            
            if not pdf_exists:
                # Create new row with all metadata
                next_id = get_next_id(rows)
                rows.append({
                    'id': str(next_id),
                    'ukprn': ukprn or '',
                    'university': official_name,
                    'year': year,
                    'source_url': source_url,
                    'download_timestamp': download_timestamp,
                    'pdf_path': str(pdf_file.absolute()),
                    'txt_path': txt_path,
                    'json_path': json_path
                })
    
    return rows


# =============================================================================
# End CSV Tracking System
# =============================================================================


def colored_text(text: str, color: str) -> str:
    """Return colored text if colorama is available."""
    if COLORAMA_AVAILABLE:
        return f"{color}{text}{Style.RESET_ALL}"
    return text


def extract_year_from_filename(filename: str) -> Optional[str]:
    """
    Extract financial year from filename.
    
    Handles formats like:
    - 2023-24, 2023-2024
    - 2023_24, 2023_2024
    - 202324, 2023-24
    - FS2023, accounts-2023
    - accounts1920 (means 2019-20)
    
    Returns normalized format: "2023-24" or "2023" for single years
    Only returns years >= 1990 to avoid false matches
    """
    # Try various year patterns
    patterns = [
        # 2023-24, 2023-2024 format (standard range)
        r'(\d{4})[-_](\d{2,4})',
        # accounts1920, fs1920 format (compact range like 19-20 meaning 2019-2020)
        r'(?:accounts|fs|statements)(\d{2})(\d{2})',
        # Single year: 2023, FS2023, accounts-2023
        # Use word boundary to avoid matching "accounts1920" as year 1920
        r'(?:^|[^a-zA-Z0-9])(\d{4})(?:[^0-9]|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename, re.IGNORECASE)
        if match:
            year1 = match.group(1)
            
            # Handle compact format (e.g., "1920" from "accounts1920")
            if len(year1) == 2:
                # It's a 2-digit year, assume 20xx
                year1_full = "20" + year1
                year1_int = int(year1_full)
            else:
                year1_int = int(year1)
            
            # Filter out unreasonable years (financial reports before 1990 are unlikely)
            if year1_int < 1990:
                continue
            
            if len(match.groups()) > 1 and match.group(2):
                year2 = match.group(2)
                # Normalize second year
                if len(year2) == 2:
                    if len(year1) == 2:
                        # Both are 2-digit, make them 20xx
                        year1_full = "20" + year1
                        year2_full = "20" + year2
                    else:
                        year2_full = year1[:2] + year2
                else:
                    year2_full = year2
                return f"{year1_full if len(year1) == 2 else year1}-{year2_full[-2:]}"
            else:
                return year1_full if len(year1) == 2 else year1
    
    return None


def extract_university_name(filename: str) -> Optional[str]:
    """
    Extract university name from filename.
    
    Filename pattern: UniversityName_document-title.txt or UniversityName_Year_document.txt
    """
    # Remove extension
    name = Path(filename).stem
    
    # The filename pattern is: UniversityName_OptionalYear_DocumentTitle
    # We want to extract just the university name (first part before underscore)
    # But university names might have multiple words separated by underscores
    
    # Common pattern: Split on underscore and take parts that look like uni name
    parts = name.split('_')
    
    # Document keywords that indicate we've left the university name
    doc_keywords = ['annual', 'report', 'financial', 'statements', 'accounts', 
                    'fs', 'accounts', 'cu', 'document', 'final', 'aru']
    
    if len(parts) >= 1:
        # First part is typically the university name
        # Handle cases like "Anglia_Ruskin_University" or "University_of_Edinburgh"
        uni_parts = []
        for part in parts:
            # Stop when we hit a year pattern
            if re.match(r'^\d{4}', part):  # Starts with year
                break
            
            # Stop when we hit a document keyword (check hyphenated parts too)
            part_lower = part.lower()
            if any(keyword in part_lower for keyword in doc_keywords):
                break
            
            # Stop if part is very long or has many hyphens (likely a document title)
            if len(part) > 30 or part.count('-') > 2:
                break
            
            # Add to university name
            uni_parts.append(part)
            
            # Stop after getting a few parts (uni names are typically 2-4 words)
            if len(uni_parts) >= 4:
                break
        
        if uni_parts:
            return ' '.join(uni_parts)
    
    return None


def normalize_university_name(name: str) -> str:
    """
    Normalize university name for consistent matching.
    
    Removes 'University', 'of', etc. and creates canonical form.
    """
    # Convert to lowercase
    name = name.lower()
    
    # Remove common words
    for word in ['university', 'of', 'the', 'college']:
        name = name.replace(word, '')
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    return name.strip()


def analyze_extracted_text(extracted_dir: Path) -> Dict[str, Dict[str, any]]:
    """
    Analyze extracted text directory to find available years per university.
    
    Uses UKPRN for identification and official HESA names for consistency.
    
    Returns:
        Dict mapping UKPRN (or university name if no UKPRN) to:
            - 'ukprn': UKPRN identifier (if matched)
            - 'name': Official university name
            - 'years': Set of available years
            - 'min_year': Earliest year found
            - 'max_year': Latest year found
            - 'files': List of filenames
    """
    if not extracted_dir.exists():
        logging.warning(f"Extracted text directory does not exist: {extracted_dir}")
        return {}
    
    logging.info(f"Analyzing extracted text in: {extracted_dir}")
    
    university_data = defaultdict(lambda: {
        'ukprn': '',
        'name': '',
        'years': set(),
        'files': [],
        'min_year': None,
        'max_year': None
    })
    
    # Process all txt files
    txt_files = list(extracted_dir.glob("*.txt"))
    logging.info(f"Found {len(txt_files)} text files to analyze")
    
    for txt_file in txt_files:
        filename = txt_file.name
        
        # Extract university name and match to UKPRN
        uni_name_raw = extract_university_name(filename)
        if not uni_name_raw:
            continue
        
        ukprn, official_name = match_university_to_ukprn(uni_name_raw)
        
        # Extract year and normalize
        year = extract_year_from_filename(filename)
        if not year:
            continue
        year = normalize_year_to_ending(year)
        
        # Filter out invalid years (should be 1990-2100)
        try:
            year_int = int(year.split('-')[0]) if '-' in year else int(year)
            if not (1990 <= year_int <= 2100):
                continue
        except (ValueError, IndexError):
            continue
        
        # Use UKPRN as key if available, otherwise use name
        key = ukprn if ukprn else official_name
        
        # Store data
        university_data[key]['ukprn'] = ukprn or ''
        university_data[key]['name'] = official_name
        university_data[key]['years'].add(year)
        university_data[key]['files'].append(filename)
    
    # Calculate min/max years for each university
    for key, data in university_data.items():
        years = sorted(data['years'])
        if years:
            data['min_year'] = years[0]
            data['max_year'] = years[-1]
    
    return dict(university_data)


def identify_missing_years(
    university_data: Dict[str, Dict],
    current_year: int = None,
    max_lookback: int = 5,
    max_forward: int = 2
) -> Dict[str, List[str]]:
    """
    Identify missing years for each university.
    
    Strategy:
    1. Find gaps between earliest and latest years found (continuity)
    2. Look forward from latest year to current year (recent missing)
    3. Look back from earliest year (historical depth, limited to max_lookback)
    
    Args:
        university_data: Output from analyze_extracted_text
        current_year: Current year (default: current year)
        max_lookback: Maximum years to look back from earliest found year (default: 5)
        max_forward: How many years forward from current to consider (default: 2)
        
    Returns:
        Dict mapping university name to list of missing year strings
    """
    if current_year is None:
        current_year = datetime.now().year
    
    missing_data = {}
    
    for uni_name, data in university_data.items():
        if not data['years']:
            continue
        
        # Parse years and filter out invalid ones (should be 1900-2100)
        years_parsed = set()
        for year_str in data['years']:
            try:
                if '-' in year_str:
                    # Range like 2023-24
                    start = int(year_str.split('-')[0])
                else:
                    start = int(year_str)
                
                # Filter out garbage years (assume valid financial years are 1900-2100)
                if 1900 <= start <= 2100:
                    years_parsed.add(start)
            except (ValueError, IndexError):
                # Skip unparseable years
                continue
        
        if not years_parsed:
            continue
        
        min_year = min(years_parsed)
        max_year = max(years_parsed)
        
        missing_years = []
        
        # 1. Fill gaps between min and max (continuity)
        for year in range(min_year, max_year + 1):
            if year not in years_parsed:
                year_range = f"{year}-{str(year+1)[-2:]}"
                missing_years.append(year_range)
        
        # 2. Look forward from max to current year (recent missing)
        for year in range(max_year + 1, current_year + max_forward):
            year_range = f"{year}-{str(year+1)[-2:]}"
            missing_years.append(year_range)
        
        # 3. Look back from min (limited historical depth)
        # Only look back max_lookback years from the earliest found
        lookback_target = max(min_year - max_lookback, 2000)
        for year in range(lookback_target, min_year):
            year_range = f"{year}-{str(year+1)[-2:]}"
            missing_years.append(year_range)
        
        if missing_years:
            # Sort chronologically
            missing_data[uni_name] = sorted(missing_years)
    
    return missing_data


def generate_search_query(uni_name: str, year: str) -> str:
    """
    Generate search query for finding a specific year's financial report.
    
    Args:
        uni_name: University name
        year: Year string (e.g., "2020-21" or "2020")
        
    Returns:
        Search query string
    """
    # Clean university name
    clean_name = uni_name.replace('_', ' ')
    
    # Generate query with various terms
    terms = [
        f'"{clean_name}" {year} "annual report"',
        f'"{clean_name}" {year} "financial statements"',
        f'"{clean_name}" {year} "accounts"',
    ]
    
    # Use the first one as primary
    return terms[0]


def run_download_script(
    search_query: str,
    output_dir: Path,
    limit: int = 10,
    method: str = 'requests'
) -> bool:
    """
    Run the download script with a specific search query.
    
    Returns:
        True if download was successful, False otherwise
    """
    try:
        cmd = [
            sys.executable,
            'step1_download_pdfs.py',
            '--search', search_query,
            '--output', str(output_dir),
            '--limit', str(limit),
            '--method', method,
            '--no-scrape'  # Don't scrape, just search
        ]
        
        logging.info(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logging.info("Download script completed successfully")
            return True
        else:
            logging.warning(f"Download script failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error("Download script timed out")
        return False
    except Exception as e:
        logging.error(f"Error running download script: {e}")
        return False


def run_extraction_script(
    input_dir: Path,
    output_dir: Path,
    fast_mode: bool = True,
    workers: int = 4,
    output_format: str = 'both'
) -> bool:
    """
    Run the extraction script on newly downloaded PDFs.
    
    Args:
        input_dir: Directory containing PDF files
        output_dir: Directory for extracted text files
        fast_mode: Use fast extraction mode
        workers: Number of parallel workers
        output_format: Output format ('txt', 'json', or 'both')
    
    Returns:
        True if extraction was successful, False otherwise
    """
    try:
        cmd = [
            sys.executable,
            'step2_extract_text.py',
            str(input_dir),
            '--output', str(output_dir),
            '--workers', str(workers),
            '--format', output_format
        ]
        
        if fast_mode:
            cmd.append('--fast')
        
        logging.info(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode == 0:
            logging.info("Extraction script completed successfully")
            return True
        else:
            logging.warning(f"Extraction script failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logging.error("Extraction script timed out")
        return False
    except Exception as e:
        logging.error(f"Error running extraction script: {e}")
        return False


def save_progress(
    output_file: Path,
    university_data: Dict,
    missing_data: Dict,
    iteration: int
):
    """Save current progress to JSON file."""
    progress = {
        'timestamp': datetime.now().isoformat(),
        'iteration': iteration,
        'universities': {},
        'missing_data': {}
    }
    
    # Convert sets to lists for JSON serialization
    for uni_name, data in university_data.items():
        progress['universities'][uni_name] = {
            'years': sorted(list(data['years'])),
            'min_year': data['min_year'],
            'max_year': data['max_year'],
            'file_count': len(data['files'])
        }
    
    progress['missing_data'] = {
        uni: sorted(years) for uni, years in missing_data.items()
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Progress saved to: {output_file}")


def print_summary(university_data: Dict, missing_data: Dict):
    """Print summary of current data coverage."""
    print(colored_text("\n" + "="*80, Fore.CYAN))
    print(colored_text("Financial Data Coverage Summary", Fore.CYAN))
    print(colored_text("="*80, Fore.CYAN))
    
    print(f"\nTotal universities with data: {len(university_data)}")
    
    # Universities with complete recent coverage
    complete_recent = []
    incomplete = []
    
    current_year = datetime.now().year
    for uni_name, data in sorted(university_data.items()):
        if data['max_year']:
            max_year_int = int(data['max_year'].split('-')[0])
            if max_year_int >= current_year - 2:
                complete_recent.append(uni_name)
            else:
                incomplete.append(uni_name)
    
    print(colored_text(f"\nUniversities with recent data (last 2 years): {len(complete_recent)}", Fore.GREEN))
    print(colored_text(f"Universities missing recent data: {len(incomplete)}", Fore.YELLOW))
    
    # Show missing data summary
    if missing_data:
        print(colored_text(f"\nUniversities with gaps: {len(missing_data)}", Fore.YELLOW))
        
        # Show top 10 with most gaps (display names, not UKPRNs)
        top_gaps = sorted(missing_data.items(), key=lambda x: len(x[1]), reverse=True)[:10]
        print("\nTop 10 universities with most missing years:")
        for uni_key, years in top_gaps:
            # Get university name from university_data if available
            uni_info = university_data.get(uni_key, {})
            if isinstance(uni_info, dict) and uni_info.get('name'):
                display_name = uni_info['name']
                if uni_info.get('ukprn'):
                    display_name += f" (UKPRN: {uni_info['ukprn']})"
            else:
                display_name = uni_key
            
            print(f"  {display_name}: {len(years)} missing years")
            if len(years) <= 5:
                print(f"    Missing: {', '.join(years)}")
    
    print(colored_text("\n" + "="*80, Fore.CYAN))


def print_university_summary(
    university_data: Dict,
    missing_data: Dict,
    csv_rows: List[Dict] = None,
    show_all: bool = False,
    limit: int = 20
):
    """
    Print detailed summary for each university showing found and missing years.
    
    Args:
        university_data: Dict of university data from analyze_extracted_text (keyed by UKPRN or name)
        missing_data: Dict of missing years from identify_missing_years
        csv_rows: Optional CSV tracker rows for additional info
        show_all: If True, show all universities. If False, show only those with data
        limit: Maximum number of universities to show (default: 20)
    """
    print(colored_text("\n" + "="*80, Fore.CYAN))
    print(colored_text("University-by-University Summary", Fore.CYAN))
    print(colored_text("="*80, Fore.CYAN))
    
    # Get all universities (from both data and missing)
    all_unis = set(university_data.keys()) | set(missing_data.keys())
    
    if not all_unis:
        print(colored_text("\nNo university data available.", Fore.YELLOW))
        return
    
    # Sort by university name (get name from university_data if available)
    def sort_key(key):
        uni_info = university_data.get(key, {})
        return uni_info.get('name', key) if isinstance(uni_info, dict) else key
    
    sorted_unis = sorted(all_unis, key=sort_key)
    
    # Limit output if requested
    if not show_all and len(sorted_unis) > limit:
        print(f"\nShowing first {limit} universities (use --show-all-unis for complete list)")
        sorted_unis = sorted_unis[:limit]
    
    print(f"\nTotal universities: {len(all_unis)}\n")
    
    for idx, uni_key in enumerate(sorted_unis, 1):
        # Get data for this university
        uni_data = university_data.get(uni_key, {})
        missing_years = missing_data.get(uni_key, [])
        
        # Display name with UKPRN if available
        ukprn = uni_data.get('ukprn', '') if isinstance(uni_data, dict) else ''
        uni_name = uni_data.get('name', uni_key) if isinstance(uni_data, dict) else uni_key
        
        if ukprn:
            display_name = f"{uni_name} (UKPRN: {ukprn})"
        else:
            display_name = uni_name
        
        print(colored_text(f"\n{idx}. {display_name}", Fore.CYAN))
        print("-" * 70)
        
        # Found years
        if uni_data and uni_data.get('years'):
            years_list = sorted(list(uni_data['years']))
            year_ranges = format_year_ranges(years_list)
            
            print(colored_text(f"  ✓ Found: {len(years_list)} years", Fore.GREEN))
            print(f"    Range: {uni_data.get('min_year', 'N/A')} to {uni_data.get('max_year', 'N/A')}")
            print(f"    Years: {year_ranges}")
            print(f"    Files: {len(uni_data.get('files', []))} documents")
            
            # Count from CSV if available
            if csv_rows:
                csv_count = sum(1 for row in csv_rows 
                              if row['university'] == uni_name and row.get('txt_path'))
                if csv_count != len(uni_data.get('files', [])):
                    print(f"    CSV records: {csv_count} documents")
        else:
            print(colored_text("  ✗ No documents found yet", Fore.YELLOW))
        
        # Missing years
        if missing_years:
            # Group consecutive years
            missing_ranges = format_year_ranges(missing_years)
            print(colored_text(f"  ⚠ Missing: {len(missing_years)} years", Fore.YELLOW))
            print(f"    Years: {missing_ranges}")
            
            # Show placeholders in CSV if available
            if csv_rows:
                placeholder_count = sum(1 for row in csv_rows 
                                       if row['university'] == uni_name 
                                       and row['year'] in missing_years
                                       and not row.get('pdf_path'))
                if placeholder_count > 0:
                    print(f"    CSV placeholders: {placeholder_count} rows")
        else:
            if uni_data and uni_data.get('years'):
                print(colored_text("  ✓ No missing years in range", Fore.GREEN))
    
    print(colored_text("\n" + "="*80, Fore.CYAN))


def format_year_ranges(years: List[str]) -> str:
    """
    Format a list of years into readable ranges.
    
    Examples:
        ['2020-21', '2021-22', '2022-23'] -> '2020-21 to 2022-23'
        ['2020', '2021', '2022'] -> '2020 to 2022'
        ['2020-21', '2023-24'] -> '2020-21, 2023-24'
    """
    if not years:
        return "None"
    
    if len(years) <= 5:
        return ', '.join(years)
    
    # Extract start years for grouping
    year_ints = []
    for y in years:
        try:
            if '-' in y:
                year_ints.append(int(y.split('-')[0]))
            else:
                year_ints.append(int(y))
        except (ValueError, IndexError):
            continue
    
    if not year_ints:
        return ', '.join(years)
    
    year_ints.sort()
    
    # Find consecutive ranges
    ranges = []
    start = year_ints[0]
    end = year_ints[0]
    
    for year in year_ints[1:]:
        if year == end + 1:
            end = year
        else:
            # Add completed range
            if start == end:
                ranges.append(str(start))
            else:
                ranges.append(f"{start}-{end}")
            start = end = year
    
    # Add final range
    if start == end:
        ranges.append(str(start))
    else:
        ranges.append(f"{start}-{end}")
    
    # Format nicely
    if len(ranges) == 1:
        r = ranges[0]
        if '-' in r and len(r.split('-')) == 2:
            return f"{r} ({len(years)} years)"
        return r
    elif len(ranges) <= 3:
        return ', '.join(ranges) + f" ({len(years)} years)"
    else:
        return f"{ranges[0]} to {ranges[-1]} ({len(years)} years, {len(ranges)} ranges)"


def main():
    """Main coordinator function."""
    parser = argparse.ArgumentParser(
        description="Coordinate financial data collection to fill gaps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run coordinator with default settings
  python financial_data_coordinator.py
  
  # Run with specific directories
  python financial_data_coordinator.py --extracted extracted_text --downloads downloads_temp
  
  # Run for 5 iterations maximum
  python financial_data_coordinator.py --max-iterations 5
  
  # Dry run to see what would be searched
  python financial_data_coordinator.py --dry-run
        """
    )
    
    parser.add_argument(
        '--extracted',
        type=Path,
        default=None,
        help='Directory containing extracted text files (default: iCloud/unimetrics/extracted_text)'
    )
    
    parser.add_argument(
        '--downloads',
        type=Path,
        default=None,
        help='Directory for downloading new PDFs (default: iCloud/unimetrics/downloads/pdfs)'
    )
    
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=10,
        help='Maximum number of search iterations (default: 10)'
    )
    
    parser.add_argument(
        '--max-lookback',
        type=int,
        default=25,
        help='Maximum years to look back from latest found year (default: 25)'
    )
    
    parser.add_argument(
        '--unis-per-iteration',
        type=int,
        default=5,
        help='Number of universities to process per iteration (default: 5)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be searched without actually downloading'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show detailed university-by-university summary and exit'
    )
    
    parser.add_argument(
        '--show-all-unis',
        action='store_true',
        help='Show all universities in summary (not just first 20)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Print header
    print(colored_text("\n" + "="*80, Fore.CYAN))
    print(colored_text("Financial Data Collection Coordinator", Fore.CYAN))
    print(colored_text("="*80 + "\n", Fore.CYAN))
    
    # Set directories - use iCloud storage by default
    if args.downloads is None:
        args.downloads = get_downloads_dir()
    if args.extracted is None:
        args.extracted = get_extracted_text_dir()
    
    # Ensure directories exist
    args.downloads.mkdir(parents=True, exist_ok=True)
    args.extracted.mkdir(parents=True, exist_ok=True)
    
    logging.info(f"Downloads directory: {args.downloads}")
    logging.info(f"Extracted text directory: {args.extracted}")
    
    # CSV tracker setup (stays in project directory for git tracking)
    csv_tracker_path = Path('financial_data_tracker.csv')
    logging.info(f"CSV tracker: {csv_tracker_path}")
    
    # Track progress across iterations (in logs directory)
    progress_file = Path(f'logs/coordinator_progress_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    # Step 0: Load and initialize CSV tracker
    logging.info("\nStep 0: Loading CSV tracker...")
    csv_rows = load_csv_tracker(csv_tracker_path)
    
    # Update CSV with any existing extracted files
    csv_rows = update_csv_with_extracted_files(csv_rows, args.extracted)
    save_csv_tracker(csv_tracker_path, csv_rows)
    
    # Step 1: Analyze current data
    logging.info("\nStep 1: Analyzing extracted text files...")
    university_data = analyze_extracted_text(args.extracted)
    
    if not university_data:
        logging.warning("No extracted text found. Please run extraction first.")
        return
    
    logging.info(f"Found data for {len(university_data)} universities")
    
    # Step 2: Identify missing years
    logging.info("\nStep 2: Identifying missing years...")
    missing_data = identify_missing_years(
        university_data,
        max_lookback=args.max_lookback,
        max_forward=2  # Look up to 2 years ahead of current year
    )
    
    if not missing_data:
        logging.info(colored_text("\nNo missing data identified. Collection complete!", Fore.GREEN))
        return
    
    logging.info(f"Found gaps for {len(missing_data)} universities")
    
    # Add placeholder rows for missing years
    logging.info("\nAdding placeholders for missing years to CSV...")
    for uni_name, years in missing_data.items():
        csv_rows = add_placeholder_rows(csv_rows, uni_name, years)
    save_csv_tracker(csv_tracker_path, csv_rows)
    logging.info(f"CSV tracker now has {len(csv_rows)} total rows")
    
    # Step 3: Print initial summary
    print_summary(university_data, missing_data)
    
    # If --summary flag is set, show detailed per-university summary and exit
    if args.summary:
        print_university_summary(
            university_data,
            missing_data,
            csv_rows=csv_rows,
            show_all=args.show_all_unis,
            limit=20
        )
        print(colored_text(f"\n📊 CSV Tracker: {csv_tracker_path} ({len(csv_rows)} rows)", Fore.CYAN))
        return
    
    # Step 4: Save initial progress
    save_progress(progress_file, university_data, missing_data, 0)
    
    if args.dry_run:
        print(colored_text("\nDry run - showing what would be searched:", Fore.YELLOW))
        search_count = 0
        for uni_name, years in list(missing_data.items())[:args.unis_per_iteration]:
            for year in years[:3]:  # Show first 3 missing years per uni
                query = generate_search_query(uni_name, year)
                print(f"  Would search: {query}")
                search_count += 1
        print(colored_text(f"\nWould perform {search_count} searches", Fore.YELLOW))
        return
    
    # Step 5: Collect all search queries
    logging.info(f"\nStep 3: Preparing searches for {args.unis_per_iteration} universities...")
    all_queries = []
    
    for uni_name, years in list(missing_data.items())[:args.unis_per_iteration]:
        logging.info(colored_text(f"\nQueuing searches for: {uni_name}", Fore.CYAN))
        logging.info(f"Missing years: {', '.join(years[:5])}{'...' if len(years) > 5 else ''}")
        
        # Queue searches for earliest missing years
        for year in years[:3]:  # Try first 3 missing years
            query = generate_search_query(uni_name, year)
            all_queries.append((uni_name, year, query))
    
    logging.info(f"\nQueued {len(all_queries)} searches")
    
    # Step 6: Download ALL documents
    logging.info(f"\nStep 4: Downloading documents for all searches...")
    print(colored_text(f"\n{'='*80}", Fore.CYAN))
    print(colored_text("Downloading Phase", Fore.CYAN))
    print(colored_text(f"{'='*80}\n", Fore.CYAN))
    
    successful_downloads = 0
    for idx, (uni_name, year, query) in enumerate(all_queries, 1):
        print(colored_text(f"\n[{idx}/{len(all_queries)}] {uni_name} - {year}", Fore.CYAN))
        logging.info(f"Searching: {query}")
        
        if run_download_script(query, args.downloads, limit=5):
            successful_downloads += 1
    
    logging.info(f"\nDownloaded from {successful_downloads}/{len(all_queries)} searches")
    
    # Update CSV with downloaded PDFs
    if successful_downloads > 0:
        logging.info("\nUpdating CSV tracker with downloaded PDFs...")
        csv_rows = update_csv_with_downloads(csv_rows, args.downloads)
        save_csv_tracker(csv_tracker_path, csv_rows)
    
    # Step 7: Extract ALL PDFs at once
    if successful_downloads > 0:
        print(colored_text(f"\n{'='*80}", Fore.CYAN))
        print(colored_text("Extraction Phase", Fore.CYAN))
        print(colored_text(f"{'='*80}\n", Fore.CYAN))
        
        # Count PDFs to extract
        pdf_files = list(args.downloads.glob("*.pdf"))
        logging.info(f"Found {len(pdf_files)} PDF files to extract")
        
        if pdf_files:
            logging.info("\nExtracting text from all PDFs (format: both txt and json)...")
            run_extraction_script(
                args.downloads,
                args.extracted,
                fast_mode=True,
                workers=4,
                output_format='both'  # Extract both txt and json
            )
            
            # Update CSV with extracted files
            logging.info("\nUpdating CSV tracker with extracted files...")
            csv_rows = update_csv_with_extracted_files(csv_rows, args.extracted)
            save_csv_tracker(csv_tracker_path, csv_rows)
        else:
            logging.warning("No PDF files found in downloads directory")
    else:
        logging.warning("No successful downloads. Nothing to extract.")
    
    # Final summary
    print(colored_text("\n" + "="*80, Fore.CYAN))
    print(colored_text("Coordination Complete", Fore.CYAN))
    print(colored_text("="*80, Fore.CYAN))
    
    university_data = analyze_extracted_text(args.extracted)
    missing_data = identify_missing_years(university_data, max_lookback=args.max_lookback, max_forward=2)
    print_summary(university_data, missing_data)
    
    # Show detailed university summary
    print_university_summary(
        university_data,
        missing_data,
        csv_rows=csv_rows,
        show_all=False,
        limit=10
    )
    
    # Final CSV update
    logging.info("\nFinal CSV tracker update...")
    csv_rows = update_csv_with_extracted_files(csv_rows, args.extracted)
    save_csv_tracker(csv_tracker_path, csv_rows)
    
    print(colored_text(f"\n📊 CSV Tracker: {csv_tracker_path} ({len(csv_rows)} rows)", Fore.GREEN))
    print(colored_text(f"💡 Tip: Run with --summary to see detailed breakdown for all universities", Fore.CYAN))
    
    logging.info(f"\nProgress saved to: {progress_file}")
    print(colored_text("\nDone!", Fore.GREEN))


if __name__ == '__main__':
    main()
