#!/usr/bin/env python3
"""
Download financial documents from UK universities.

This script uses multiple strategies to download financial PDFs and other documents:
1. Direct download using requests (fastest, but may be blocked)
2. Headless browser with Playwright (bypasses basic protections)
3. Regular browser with manual intervention (for security checks)

The script also scrapes the financial pages to find additional documents
beyond those listed in the CSV files.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

# Optional imports with graceful fallbacks
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    _HAVE_COLORAMA = True
except ImportError:
    _HAVE_COLORAMA = False
    # Create dummy objects if colorama not available
    class _DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = _DummyColor()
    Style = _DummyColor()

try:
    from tqdm import tqdm
    _HAVE_TQDM = True
except ImportError:
    _HAVE_TQDM = False

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    _HAVE_REQUESTS = True
except ImportError:
    _HAVE_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    _HAVE_BS4 = True
except ImportError:
    _HAVE_BS4 = False

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    _HAVE_PLAYWRIGHT = True
except ImportError:
    _HAVE_PLAYWRIGHT = False


# Global logger
logger: logging.Logger = None


@dataclass
class FinancialDocument:
    """Represents a financial document to download."""
    university: str
    url: str
    year: Optional[str] = None
    domain: Optional[str] = None
    country: Optional[str] = None
    filename: Optional[str] = None
    file_type: Optional[str] = None
    source: str = "csv"  # csv, scraped, or manual
    
    def __post_init__(self):
        """Extract filename and file type from URL if not provided."""
        if not self.filename:
            parsed = urlparse(self.url)
            path = parsed.path
            if path:
                self.filename = os.path.basename(path)
            else:
                # Create filename from URL hash
                url_hash = hashlib.md5(self.url.encode()).hexdigest()[:8]
                self.filename = f"{url_hash}.pdf"
        
        if not self.file_type and self.filename:
            ext = os.path.splitext(self.filename)[1].lower()
            self.file_type = ext[1:] if ext else 'unknown'
    
    def get_safe_filename(self) -> str:
        """Generate a safe filename for saving."""
        # Sanitize university name
        safe_uni = re.sub(r'[^\w\s-]', '', self.university)
        safe_uni = re.sub(r'[-\s]+', '_', safe_uni).strip('_')
        
        # Add year if available
        year_part = f"_{self.year}" if self.year and self.year != 'N/A' else ""
        
        # Keep original filename if it has a reasonable extension
        if self.file_type in ['pdf', 'docx', 'xlsx', 'html', 'zip']:
            return f"{safe_uni}{year_part}_{self.filename}"
        else:
            return f"{safe_uni}{year_part}.pdf"


def search_for_documents(query: str, max_results: int = 10) -> List[FinancialDocument]:
    """
    Search for financial documents using Google search.
    
    Parameters
    ----------
    query : str
        Search query (e.g., "University of Edinburgh 2020-21 annual report")
    max_results : int
        Maximum number of results to return
        
    Returns
    -------
    List[FinancialDocument]
        List of documents found matching the query
    """
    if not _HAVE_REQUESTS:
        logger.warning("Requests library not available for searching")
        return []
    
    documents = []
    
    try:
        # Use Google search (simple scraping approach)
        # Note: For production, consider using official Google Custom Search API
        search_url = "https://www.google.com/search"
        params = {
            'q': query + ' filetype:pdf',
            'num': max_results
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        session = create_session()
        response = session.get(search_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200 and _HAVE_BS4:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract PDF links from search results
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                # Google search results have URLs in /url?q=ACTUAL_URL format
                if '/url?q=' in href:
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    
                    # Check if it's a PDF
                    if '.pdf' in actual_url.lower():
                        # Extract university name from query or URL
                        uni_name = query.split()[0:3]  # First few words usually contain uni name
                        uni_name = ' '.join(uni_name)
                        
                        doc = FinancialDocument(
                            university=uni_name,
                            url=actual_url,
                            source='search'
                        )
                        documents.append(doc)
                        
                        if len(documents) >= max_results:
                            break
        
        logger.info(f"Found {len(documents)} documents for query: {query}")
        return documents
        
    except Exception as e:
        logger.warning(f"Search failed: {e}")
        return []


def load_download_state(state_file: str = "download_state.json") -> dict:
    """Load the download state from a JSON file.
    
    Parameters
    ----------
    state_file : str
        Path to state file
    
    Returns
    -------
    dict
        Dictionary with 'downloaded_urls' set and 'downloaded_files' set
    """
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    'downloaded_urls': set(data.get('downloaded_urls', [])),
                    'downloaded_files': set(data.get('downloaded_files', []))
                }
        except Exception as e:
            logger.warning(f"Could not load state file: {e}")
    
    return {'downloaded_urls': set(), 'downloaded_files': set()}


def save_download_state(downloaded_urls: Set[str], downloaded_files: Set[str], 
                       state_file: str = "download_state.json") -> None:
    """Save the download state to a JSON file.
    
    Parameters
    ----------
    downloaded_urls : Set[str]
        Set of successfully downloaded URLs
    downloaded_files : Set[str]
        Set of successfully downloaded file paths
    state_file : str
        Path to state file
    """
    try:
        data = {
            'downloaded_urls': list(downloaded_urls),
            'downloaded_files': list(downloaded_files),
            'last_updated': datetime.now().isoformat()
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Could not save state file: {e}", exc_info=True)


def setup_logging(verbose: bool = False, log_dir: str = "logs") -> logging.Logger:
    """Configure logging with file and console handlers.
    
    Parameters
    ----------
    verbose : bool
        If True, set console logging to DEBUG level
    log_dir : str
        Directory to store log files
    
    Returns
    -------
    logging.Logger
        Configured logger instance
    """
    # Create logs directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"download_financials_{timestamp}.log")
    
    # Create logger
    logger = logging.getLogger("financial_downloader")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    
    # File handler (always DEBUG)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (INFO or DEBUG based on verbose)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"{Fore.GREEN}Logging initialized. Log file: {log_file}{Style.RESET_ALL}")
    
    return logger


def load_csv_documents(csv_path: str) -> List[FinancialDocument]:
    """Load documents from university financials CSV.
    
    Parameters
    ----------
    csv_path : str
        Path to CSV file
    
    Returns
    -------
    List[FinancialDocument]
        List of document objects
    """
    documents = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                doc = FinancialDocument(
                    university=row.get('University', '').strip(),
                    country=row.get('Country', '').strip(),
                    domain=row.get('Domain', '').strip(),
                    year=row.get('Year', 'N/A').strip(),
                    url=row.get('URL', '').strip(),
                    source='csv'
                )
                if doc.url:
                    documents.append(doc)
        
        logger.info(f"{Fore.GREEN}Loaded {len(documents)} documents from {csv_path}{Style.RESET_ALL}")
        return documents
    
    except Exception as e:
        logger.error(f"Error loading CSV {csv_path}: {e}", exc_info=True)
        return []


def load_gemini_documents(csv_path: str) -> List[FinancialDocument]:
    """Load documents from Gemini list CSV.
    
    Parameters
    ----------
    csv_path : str
        Path to Gemini CSV file
    
    Returns
    -------
    List[FinancialDocument]
        List of document objects
    """
    documents = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                uni_name = row.get('University Name', '').strip()
                
                # Add the financial data page
                data_page = row.get('Financial Data Page', '').strip()
                if data_page:
                    documents.append(FinancialDocument(
                        university=uni_name,
                        url=data_page,
                        domain=row.get('Root Domain', '').strip(),
                        source='gemini_page'
                    ))
                
                # Add the example PDF link
                pdf_link = row.get('Example Direct PDF Link', '').strip()
                if pdf_link:
                    documents.append(FinancialDocument(
                        university=uni_name,
                        url=pdf_link,
                        domain=row.get('Root Domain', '').strip(),
                        source='gemini_pdf'
                    ))
        
        logger.info(f"{Fore.GREEN}Loaded {len(documents)} documents from {csv_path}{Style.RESET_ALL}")
        return documents
    
    except Exception as e:
        logger.error(f"Error loading Gemini CSV {csv_path}: {e}", exc_info=True)
        return []


def create_session() -> Optional[requests.Session]:
    """Create a requests session with retry logic.
    
    Returns
    -------
    Optional[requests.Session]
        Configured session or None if requests not available
    """
    if not _HAVE_REQUESTS:
        return None
    
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set user agent to mimic a browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-GB,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    })
    
    return session


def download_with_requests(doc: FinancialDocument, output_dir: str, session: requests.Session) -> Tuple[bool, str]:
    """Attempt to download document using requests library.
    
    Parameters
    ----------
    doc : FinancialDocument
        Document to download
    output_dir : str
        Output directory
    session : requests.Session
        Requests session
    
    Returns
    -------
    Tuple[bool, str]
        (Success status, output path or error message)
    """
    try:
        logger.debug(f"Attempting direct download: {doc.url}")
        
        # Try to get the file
        response = session.get(doc.url, timeout=30, stream=True, allow_redirects=True)
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Determine file extension from content type if needed
        if 'pdf' in content_type and not doc.filename.endswith('.pdf'):
            doc.filename = f"{doc.filename}.pdf"
        elif 'word' in content_type or 'msword' in content_type:
            if not doc.filename.endswith('.docx'):
                doc.filename = f"{doc.filename}.docx"
        
        # Create output path
        safe_filename = doc.get_safe_filename()
        output_path = os.path.join(output_dir, safe_filename)
        
        # Download file
        total_size = int(response.headers.get('content-length', 0))
        
        with open(output_path, 'wb') as f:
            if total_size == 0:
                f.write(response.content)
            else:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
        
        file_size = os.path.getsize(output_path)
        logger.debug(f"Downloaded {file_size} bytes to {output_path}")
        
        return True, output_path
    
    except requests.exceptions.RequestException as e:
        logger.debug(f"Requests download failed: {e}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Unexpected error in direct download: {e}", exc_info=True)
        return False, str(e)


def scrape_financial_page(url: str, domain: str, session: requests.Session) -> List[str]:
    """Scrape a financial data page to find all document links.
    
    Parameters
    ----------
    url : str
        URL of the financial data page
    domain : str
        University domain to validate links
    session : requests.Session
        Requests session
    
    Returns
    -------
    List[str]
        List of document URLs found
    """
    if not _HAVE_BS4:
        logger.warning("BeautifulSoup not available, skipping page scraping")
        return []
    
    try:
        logger.debug(f"Scraping financial page: {url}")
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        document_urls = []
        seen_urls = set()
        
        for link in links:
            href = link['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(url, href)
            
            # Check if it's a document link
            if is_financial_document(absolute_url, link.get_text()):
                if absolute_url not in seen_urls:
                    seen_urls.add(absolute_url)
                    document_urls.append(absolute_url)
        
        logger.debug(f"Found {len(document_urls)} document links on page")
        return document_urls
    
    except Exception as e:
        logger.debug(f"Error scraping page: {e}")
        return []


def is_financial_document(url: str, link_text: str = "") -> bool:
    """Check if a URL appears to be a financial document.
    
    Parameters
    ----------
    url : str
        URL to check
    link_text : str
        Text of the link
    
    Returns
    -------
    bool
        True if appears to be a financial document
    """
    # File extensions to look for
    doc_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls']
    
    url_lower = url.lower()
    text_lower = link_text.lower()
    
    # Check if URL has document extension
    has_extension = any(url_lower.endswith(ext) for ext in doc_extensions)
    
    # Financial keywords
    financial_keywords = [
        'financial', 'statement', 'account', 'annual', 'report',
        'fiscal', 'budget', 'audit', 'finance'
    ]
    
    has_financial_keyword = any(kw in url_lower or kw in text_lower for kw in financial_keywords)
    
    # Exclude common false positives
    exclude_patterns = [
        'course', 'degree', 'student', 'module', 'prospectus',
        'login', 'portal', 'admissions', 'apply', 'news'
    ]
    
    has_exclude = any(pattern in url_lower for pattern in exclude_patterns)
    
    return has_extension and has_financial_keyword and not has_exclude


def download_with_playwright(doc: FinancialDocument, output_dir: str, headless: bool = True) -> Tuple[bool, str]:
    """Download document using Playwright browser automation.
    
    Parameters
    ----------
    doc : FinancialDocument
        Document to download
    output_dir : str
        Output directory
    headless : bool
        Whether to run in headless mode
    
    Returns
    -------
    Tuple[bool, str]
        (Success status, output path or error message)
    """
    if not _HAVE_PLAYWRIGHT:
        return False, "Playwright not installed"
    
    try:
        logger.debug(f"Attempting Playwright download (headless={headless}): {doc.url}")
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                accept_downloads=True
            )
            page = context.new_page()
            
            # Set up download handler
            download_info = {'path': None}
            
            def handle_download(download):
                safe_filename = doc.get_safe_filename()
                output_path = os.path.join(output_dir, safe_filename)
                download.save_as(output_path)
                download_info['path'] = output_path
            
            page.on('download', handle_download)
            
            # Navigate to URL
            try:
                page.goto(doc.url, wait_until='networkidle', timeout=60000)
            except PlaywrightTimeout:
                logger.debug("Page load timeout, proceeding anyway")
            
            # Check if it's a direct file download
            if doc.file_type in ['pdf', 'docx', 'xlsx']:
                # Wait a bit for download to trigger
                time.sleep(2)
            
            # If no download triggered, try to find and click download link
            if not download_info['path']:
                try:
                    # Look for download buttons/links
                    download_selectors = [
                        'a[download]',
                        'button:has-text("Download")',
                        'a:has-text("Download")',
                        'a:has-text("PDF")',
                    ]
                    
                    for selector in download_selectors:
                        try:
                            element = page.locator(selector).first
                            if element.is_visible():
                                element.click()
                                time.sleep(2)
                                break
                        except:
                            continue
                except Exception as e:
                    logger.debug(f"No download button found: {e}")
            
            browser.close()
            
            if download_info['path']:
                logger.debug(f"Playwright download successful: {download_info['path']}")
                return True, download_info['path']
            else:
                return False, "No download triggered"
    
    except Exception as e:
        logger.debug(f"Playwright download failed: {e}")
        return False, str(e)


def download_document(doc: FinancialDocument, output_dir: str, session: requests.Session, 
                     use_playwright: bool = True, headless: bool = True) -> Tuple[bool, str, str]:
    """Download a financial document using multiple strategies.
    
    Parameters
    ----------
    doc : FinancialDocument
        Document to download
    output_dir : str
        Output directory
    session : requests.Session
        Requests session
    use_playwright : bool
        Whether to try Playwright if requests fails
    headless : bool
        Whether to run Playwright in headless mode
    
    Returns
    -------
    Tuple[bool, str, str]
        (Success status, output path or error, download method used)
    """
    # Strategy 1: Try direct download with requests
    if _HAVE_REQUESTS and session:
        success, result = download_with_requests(doc, output_dir, session)
        if success:
            return True, result, "requests"
        logger.debug(f"Requests method failed: {result}")
    
    # Strategy 2: Try Playwright headless
    if use_playwright and _HAVE_PLAYWRIGHT and headless:
        success, result = download_with_playwright(doc, output_dir, headless=True)
        if success:
            return True, result, "playwright_headless"
        logger.debug(f"Playwright headless failed: {result}")
    
    # Strategy 3: Try Playwright with visible browser (manual intervention possible)
    if use_playwright and _HAVE_PLAYWRIGHT and not headless:
        success, result = download_with_playwright(doc, output_dir, headless=False)
        if success:
            return True, result, "playwright_visible"
        logger.debug(f"Playwright visible failed: {result}")
    
    return False, "All download methods failed", "none"


def process_documents(documents: List[FinancialDocument], output_dir: str, 
                     scrape_pages: bool = True, max_docs: Optional[int] = None,
                     use_playwright: bool = True, visible_browser: bool = False,
                     state_file: str = "download_state.json") -> dict:
    """Process and download all documents.
    
    Parameters
    ----------
    documents : List[FinancialDocument]
        List of documents to download
    output_dir : str
        Output directory
    scrape_pages : bool
        Whether to scrape financial pages for additional documents
    max_docs : Optional[int]
        Maximum number of documents to process (for testing)
    use_playwright : bool
        Whether to use Playwright as fallback
    visible_browser : bool
        Whether to use visible browser (for manual intervention)
    state_file : str
        Path to state file for tracking downloads
    
    Returns
    -------
    dict
        Statistics about the download process
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Create session
    session = create_session()
    
    # Load previous download state
    state = load_download_state(state_file)
    downloaded_urls = state['downloaded_urls']
    downloaded_files = state['downloaded_files']
    
    # Count previously downloaded
    previously_downloaded = len(downloaded_urls)
    if previously_downloaded > 0:
        logger.info(f"{Fore.CYAN}Loaded state: {previously_downloaded} URLs already downloaded{Style.RESET_ALL}")
    
    # Track statistics
    stats = {
        'total': len(documents),
        'processed': 0,
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'previously_downloaded': previously_downloaded,
        'scraped_additional': 0,
        'methods': {
            'requests': 0,
            'playwright_headless': 0,
            'playwright_visible': 0
        }
    }
    
    # Limit documents if specified
    if max_docs:
        documents = documents[:max_docs]
        stats['total'] = len(documents)
    
    # Progress bar
    doc_iterator = tqdm(documents, desc="Downloading documents", unit="doc") if _HAVE_TQDM else documents
    
    for doc in doc_iterator:
        try:
            stats['processed'] += 1
            
            # Skip already downloaded URLs
            if doc.url in downloaded_urls:
                logger.debug(f"Skipping already downloaded URL: {doc.url}")
                stats['skipped'] += 1
                continue
            
            logger.info(f"\n{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
            logger.info(f"{Fore.CYAN}{Style.BRIGHT}Processing: {doc.university}{Style.RESET_ALL}")
            logger.info(f"{Fore.WHITE}URL: {doc.url}{Style.RESET_ALL}")
            
            # Check if it's a page to scrape or a direct document
            is_page = doc.source.endswith('_page') or not doc.file_type or doc.file_type == 'unknown'
            
            if is_page and scrape_pages and session:
                # Scrape the page for document links
                logger.info(f"{Fore.YELLOW}Scraping financial page for documents...{Style.RESET_ALL}")
                doc_urls = scrape_financial_page(doc.url, doc.domain or '', session)
                
                if doc_urls:
                    logger.info(f"{Fore.GREEN}Found {len(doc_urls)} documents on page{Style.RESET_ALL}")
                    stats['scraped_additional'] += len(doc_urls)
                    
                    # Download each found document
                    for doc_url in doc_urls:
                        if doc_url in downloaded_urls:
                            continue
                        
                        scraped_doc = FinancialDocument(
                            university=doc.university,
                            url=doc_url,
                            domain=doc.domain,
                            country=doc.country,
                            source='scraped'
                        )
                        
                        success, result, method = download_document(
                            scraped_doc, output_dir, session, use_playwright, not visible_browser
                        )
                        
                        if success:
                            logger.info(f"{Fore.GREEN}✓ Downloaded via {method}: {result}{Style.RESET_ALL}")
                            stats['successful'] += 1
                            stats['methods'][method] += 1
                            downloaded_urls.add(doc_url)
                            downloaded_files.add(result)
                            # Save state after each successful download
                            save_download_state(downloaded_urls, downloaded_files, state_file)
                        else:
                            logger.warning(f"{Fore.YELLOW}✗ Failed: {result}{Style.RESET_ALL}")
                            stats['failed'] += 1
                        
                        time.sleep(1)  # Rate limiting
                else:
                    logger.warning(f"{Fore.YELLOW}No documents found on page{Style.RESET_ALL}")
            else:
                # Direct document download
                success, result, method = download_document(
                    doc, output_dir, session, use_playwright, not visible_browser
                )
                
                if success:
                    logger.info(f"{Fore.GREEN}✓ Downloaded via {method}: {result}{Style.RESET_ALL}")
                    stats['successful'] += 1
                    stats['methods'][method] += 1
                    downloaded_urls.add(doc.url)
                    downloaded_files.add(result)
                    # Save state after each successful download
                    save_download_state(downloaded_urls, downloaded_files, state_file)
                else:
                    logger.warning(f"{Fore.YELLOW}✗ Failed: {result}{Style.RESET_ALL}")
                    stats['failed'] += 1
            
            # Rate limiting
            time.sleep(0.5)
        
        except KeyboardInterrupt:
            logger.warning(f"\n{Fore.YELLOW}Process interrupted by user{Style.RESET_ALL}")
            break
        except Exception as e:
            logger.error(f"{Fore.RED}Error processing document: {e}{Style.RESET_ALL}", exc_info=True)
            stats['failed'] += 1
    
    return stats


def main(verbose: bool = False, max_docs: Optional[int] = None, scrape: bool = True,
         use_playwright: bool = True, visible_browser: bool = False,
         search_query: Optional[str] = None, output_dir: Optional[str] = None) -> None:
    """Main function to orchestrate document downloads.
    
    Parameters
    ----------
    verbose : bool
        Enable verbose logging
    max_docs : Optional[int]
        Maximum number of documents to process (for testing)
    scrape : bool
        Whether to scrape pages for additional documents
    use_playwright : bool
        Whether to use Playwright as fallback
    visible_browser : bool
        Whether to use visible browser for manual intervention
    search_query : Optional[str]
        Custom search query for targeted document search
    output_dir : Optional[str]
        Custom output directory (default: downloads_<timestamp>)
    """
    global logger
    
    try:
        # Setup logging
        logger = setup_logging(verbose=verbose)
        
        # Print header
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}UK University Financial Document Downloader{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}\n")
        
        logger.info(f"{Fore.GREEN}Starting document download process...{Style.RESET_ALL}")
        
        # Check dependencies
        if not _HAVE_REQUESTS:
            logger.error(f"{Fore.RED}requests library not installed. Cannot proceed.{Style.RESET_ALL}")
            sys.exit(1)
        
        if not _HAVE_BS4:
            logger.warning(f"{Fore.YELLOW}BeautifulSoup not installed. Page scraping disabled.{Style.RESET_ALL}")
            scrape = False
        
        if not _HAVE_PLAYWRIGHT and use_playwright:
            logger.warning(f"{Fore.YELLOW}Playwright not installed. Fallback method unavailable.{Style.RESET_ALL}")
            use_playwright = False
        
        # Handle custom search query
        if search_query:
            logger.info(f"{Fore.CYAN}Using custom search query: {search_query}{Style.RESET_ALL}")
            all_documents = search_for_documents(search_query)
            
            if not all_documents:
                logger.warning(f"{Fore.YELLOW}No documents found for query: {search_query}{Style.RESET_ALL}")
                return
        else:
            # Load documents from CSV files
            all_documents = []
            
            # Find CSV files
            results_files = list(Path('.').glob('university_financials_results_*.csv'))
            gemini_file = Path('gemini_list.csv')
        
        if not results_files and not gemini_file.exists():
            logger.error(f"{Fore.RED}No CSV files found. Please run university_financials.py first.{Style.RESET_ALL}")
            sys.exit(1)
        
        # Load from results files
        for csv_file in results_files:
            docs = load_csv_documents(str(csv_file))
            all_documents.extend(docs)
        
        # Load from Gemini list
        if gemini_file.exists():
            docs = load_gemini_documents(str(gemini_file))
            all_documents.extend(docs)
        
        if not all_documents:
            logger.error(f"{Fore.RED}No documents found in CSV files.{Style.RESET_ALL}")
            sys.exit(1)
        
        logger.info(f"{Fore.CYAN}Total documents to process: {len(all_documents)}{Style.RESET_ALL}")
        
        if max_docs:
            logger.info(f"{Fore.YELLOW}Limiting to {max_docs} documents for testing{Style.RESET_ALL}")
        
        # Create output directory
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"downloads_{timestamp}"
        
        logger.info(f"{Fore.CYAN}Output directory: {output_dir}{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}Scrape pages: {scrape}{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}Use Playwright: {use_playwright}{Style.RESET_ALL}")
        logger.info(f"{Fore.CYAN}Visible browser: {visible_browser}{Style.RESET_ALL}")
        
        # Process documents
        stats = process_documents(
            all_documents, output_dir, scrape_pages=scrape,
            max_docs=max_docs, use_playwright=use_playwright,
            visible_browser=visible_browser
        )
        
        # Print summary
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Download Summary{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")
        print(f"Documents processed: {Fore.GREEN}{stats['processed']}/{stats['total']}{Style.RESET_ALL}")
        print(f"Successful downloads: {Fore.GREEN}{stats['successful']}{Style.RESET_ALL}")
        print(f"Failed downloads: {Fore.RED}{stats['failed']}{Style.RESET_ALL}")
        print(f"Skipped (already downloaded): {Fore.YELLOW}{stats['skipped']}{Style.RESET_ALL}")
        if stats['previously_downloaded'] > 0:
            print(f"Previously downloaded (from state): {Fore.CYAN}{stats['previously_downloaded']}{Style.RESET_ALL}")
        print(f"Additional documents found: {Fore.CYAN}{stats['scraped_additional']}{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Download methods used:{Style.RESET_ALL}")
        for method, count in stats['methods'].items():
            if count > 0:
                print(f"  {method}: {Fore.GREEN}{count}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}{Style.BRIGHT}Downloads saved to: {output_dir}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}\n")
        
        logger.info(f"{Fore.GREEN}Download process completed successfully{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        logger.warning(f"\n{Fore.YELLOW}Program interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"{Fore.RED}Fatal error: {e}{Style.RESET_ALL}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Download financial documents from UK universities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python download_financial_documents.py                    # Normal mode
  python download_financial_documents.py -v                 # Verbose mode
  python download_financial_documents.py --test 10          # Test with 10 docs
  python download_financial_documents.py --no-scrape        # Skip page scraping
  python download_financial_documents.py --no-playwright    # Requests only
  python download_financial_documents.py --visible-browser  # Use visible browser

Download Strategies:
  1. Direct download with requests (fastest, may be blocked)
  2. Headless browser with Playwright (bypasses basic protections)
  3. Visible browser (allows manual security checks)

The script will automatically try methods in order until one succeeds.
        '''
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging (shows detailed debug info)'
    )
    
    parser.add_argument(
        '--test',
        type=int,
        metavar='N',
        help='Test mode: process only N documents'
    )
    
    parser.add_argument(
        '--no-scrape',
        action='store_true',
        help='Disable scraping of financial pages for additional documents'
    )
    
    parser.add_argument(
        '--no-playwright',
        action='store_true',
        help='Disable Playwright fallback (use requests only)'
    )
    
    parser.add_argument(
        '--visible-browser',
        action='store_true',
        help='Use visible browser (allows manual security checks)'
    )
    
    parser.add_argument(
        '--search',
        type=str,
        metavar='QUERY',
        help='Custom search query for targeted document search'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        metavar='DIR',
        help='Output directory for downloads (default: downloads_<timestamp>)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        metavar='N',
        help='Limit number of search results (used with --search)'
    )
    
    parser.add_argument(
        '--method',
        type=str,
        choices=['requests', 'playwright'],
        default='requests',
        help='Download method to use (default: requests)'
    )
    
    args = parser.parse_args()
    
    try:
        main(
            verbose=args.verbose,
            max_docs=args.test or args.limit,
            scrape=not args.no_scrape,
            use_playwright=not args.no_playwright and args.method != 'requests',
            visible_browser=args.visible_browser,
            search_query=args.search,
            output_dir=args.output
        )
    except Exception as e:
        print(f"{Fore.RED}Unhandled exception: {e}{Style.RESET_ALL}")
        if logger:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
