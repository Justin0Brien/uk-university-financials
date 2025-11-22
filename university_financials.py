"""
university_financials.py
========================

This module defines a simple agent that can be used to locate the latest
financial statements (audited accounts) for universities in the United
Kingdom.  Most English higher‑education institutions are **exempt
charities** regulated by the Office for Students (OfS).  Under the OfS
accounts direction, registered providers must publish their audited
financial statements on their website within two weeks of being signed
and keep at least six years of statements in an easily accessible
location【874841985887055†L1118-L1131】.  This script therefore takes
advantage of publicly available search engines to find the pages on
university websites where those statements are located.

The script does **not** download any reports itself – it only finds and
returns URLs that appear to host financial statements or annual reports.
Downloading the reports can then be performed separately once the
correct URLs have been identified.  To run the script you will need an
internet connection and (preferably) the ``duckduckgo_search`` package
installed.  If that package is unavailable, the script falls back to a
simple DuckDuckGo HTML scraper using ``requests`` and ``BeautifulSoup``.

Usage example::

    python university_financials.py

This will iterate over a predefined list of UK universities and attempt
to discover up to five candidate URLs per university where financial
statements might be located.  The results are printed to stdout.  You
may wish to redirect the output to a file for further processing.

Notes on the list of universities
---------------------------------

The list of institutions used here is based on the annex of exempt
charities published by the Office for Students【143294301069127†L704-L854】,
supplemented with universities in Scotland, Wales and Northern Ireland.
Scottish universities are not exempt charities – Scotland has no
exempt charities【70255884166863†L258-L281】 – but they are registered
charities and must still publish their accounts via the Scottish
Charity Regulator.  Welsh universities are also registered with the
Charity Commission and subject to similar disclosure obligations.  For
completeness, the major universities in those nations are included.
"""

from __future__ import annotations

import html
import logging
import re
import sys
import time
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
from datetime import datetime

try:
    # Preferred approach using the official duckduckgo_search package
    from duckduckgo_search import DDGS  # type: ignore
    _HAVE_DDG = True
except ImportError:
    _HAVE_DDG = False

try:
    from colorama import Fore, Style, init as colorama_init
    _HAVE_COLORAMA = True
except ImportError:
    _HAVE_COLORAMA = False
    # Fallback: define empty strings for color codes
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""
    class Style:
        BRIGHT = DIM = RESET_ALL = ""

try:
    from tqdm import tqdm
    _HAVE_TQDM = True
except ImportError:
    _HAVE_TQDM = False

import requests
from bs4 import BeautifulSoup  # type: ignore
from urllib.parse import quote_plus, urlparse


# Initialize colorama on Windows for colored output
if _HAVE_COLORAMA:
    colorama_init(autoreset=True)


# Configure logging
def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging with both file and console handlers.
    
    Parameters
    ----------
    log_file : Optional[str]
        Path to log file. If None, creates timestamped log in current directory.
    
    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    if log_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"university_financials_{timestamp}.log"
    
    logger = logging.getLogger("UniversityFinancials")
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler - detailed logs
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"{Fore.RED}Warning: Could not create log file: {e}{Style.RESET_ALL}")
    
    # Console handler - concise logs
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


# Global logger instance
logger = setup_logging()


@dataclass
class University:
    """Simple data class representing a university.

    Attributes
    ----------
    name: str
        The official name of the institution.
    country: str
        Country within the UK (England, Scotland, Wales or Northern Ireland).
    """

    name: str
    country: str

    def search_terms(self) -> List[str]:
        """Return a list of search terms for this university.

        These search terms are used by the search backend.  The
        combination of the university name and phrases like 'financial
        statements', 'annual report' and 'accounts' tends to yield
        relevant results.  The search will be performed in order, so
        terms earlier in the list have higher priority.
        """
        try:
            if not self.name or not isinstance(self.name, str):
                logger.error(f"Invalid university name: {self.name}")
                return []
            
            terms = [
                f"{self.name} financial statements",
                f"{self.name} annual report",
                f"{self.name} financial statements site:ac.uk",
                f"{self.name} accounts pdf",
            ]
            logger.debug(f"Generated {len(terms)} search terms for {self.name}")
            return terms
        except Exception as e:
            logger.error(f"Error generating search terms for {self.name}: {e}", exc_info=True)
            return []


def get_universities() -> List[University]:
    """Return a list of UK universities to search for.

    The list is based on the Office for Students' annex of exempt
    charities【143294301069127†L704-L854】 and includes additional universities
    from Scotland, Wales and Northern Ireland.  Each entry specifies
    the university name and its country for informational purposes.
    """
    logger.info(f"{Fore.CYAN}Loading university list...{Style.RESET_ALL}")
    england = [
        "Anglia Ruskin University",
        "Arts University Bournemouth",
        "University of the Arts London",
        "Aston University",
        "University of Bath",
        "Bath Spa University",
        "University of Bedfordshire",
        "Birkbeck College",
        "University College Birmingham",
        "University of Birmingham",
        "Birmingham City University",
        "University of Bolton",
        "Bournemouth University",
        "University of Bradford",
        "University of Brighton",
        "University of Bristol",
        "The University College of Osteopathy",
        "Brunel University London",
        "Buckinghamshire New University",
        "University of Cambridge",
        "The Institute of Cancer Research: Royal Cancer Hospital",
        "University of Central Lancashire",
        "University of Chichester",
        "City, University of London",
        "Courtauld Institute of Art",
        "Coventry University",
        "Cranfield University",
        "University for the Creative Arts",
        "University of Cumbria",
        "De Montfort University",
        "University of Derby",
        "University of Durham",
        "University of East Anglia",
        "University of East London",
        "Edge Hill University",
        "University of Essex",
        "University of Exeter",
        "Falmouth University",
        "University of Gloucestershire",
        "Goldsmiths College",
        "University of Greenwich",
        "University of Hertfordshire",
        "University of Huddersfield",
        "University of Hull",
        "Imperial College of Science, Technology and Medicine",
        "University of Keele",
        "University of Kent",
        "King’s College London",
        "Kingston University",
        "University of Lancaster",
        "University of Leeds",
        "Leeds Arts University",
        "Leeds Beckett University",
        "The University of Leicester",
        "University of Lincoln",
        "University of Liverpool",
        "Liverpool John Moores University",
        "University College London",
        "University of London",
        "London Business School",
        "London School of Economics and Political Science",
        "London School of Hygiene and Tropical Medicine",
        "London Metropolitan University",
        "London South Bank University",
        "Loughborough University",
        "University of Manchester",
        "Manchester Metropolitan University",
        "Middlesex University",
        "University of Newcastle upon Tyne",
        "University of Northampton",
        "University of Northumbria at Newcastle",
        "Norwich University of the Arts",
        "The University of Nottingham",
        "Nottingham Trent University",
        "The Open University",
        "School of Oriental and African Studies",
        "University of Oxford",
        "Oxford Brookes University",
        "University of Plymouth",
        "Plymouth College of Art",
        "University of Portsmouth",
        "Queen Mary University of London",
        "Ravensbourne University London",
        "University of Reading",
        "Roehampton University",
        "The Royal Central School of Speech and Drama",
        "Royal College of Art",
        "Royal Holloway, University of London",
        "Royal Northern College of Music",
        "The Royal Veterinary College",
        "St George’s, University of London",
        "University of St Mark & St John",
        "The University of Salford",
        "The University of Sheffield",
        "Sheffield Hallam University",
        "University of Southampton",
        "Solent University",
        "Staffordshire University",
        "University of Suffolk",
        "University of Sunderland",
        "University of Surrey",
        "The University of Sussex",
        "Teesside University",
        "University of Warwick",
        "University of the West of England, Bristol",
        "The University of West London",
        "The University of Westminster",
        "University of Winchester",
        "The University of Wolverhampton",
        "University of Worcester",
        "Writtle University College",
        "University of York",
        "York St John University",
    ]

    scotland = [
        "Abertay University",
        "University of Aberdeen",
        "University of Dundee",
        "University of Edinburgh",
        "Edinburgh Napier University",
        "University of Glasgow",
        "Glasgow Caledonian University",
        "Glasgow School of Art",
        "Heriot-Watt University",
        "University of the Highlands and Islands",
        "Open University in Scotland",
        "Queen Margaret University, Edinburgh",
        "Robert Gordon University",
        "Royal Conservatoire of Scotland",
        "Scotland’s Rural College",
        "University of St Andrews",
        "University of Stirling",
        "University of Strathclyde",
        "University of the West of Scotland",
    ]

    wales = [
        "Aberystwyth University",
        "Bangor University",
        "Cardiff Metropolitan University",
        "Cardiff University",
        "Swansea University",
        "University of South Wales",
        "University of Wales Trinity Saint David",
        "Wrexham University",
    ]

    northern_ireland = [
        "Queen’s University Belfast",
        "Ulster University",
        "St Mary’s University College",
        "Stranmillis University College",
    ]

    try:
        universities = (
            [University(name, "England") for name in england] +
            [University(name, "Scotland") for name in scotland] +
            [University(name, "Wales") for name in wales] +
            [University(name, "Northern Ireland") for name in northern_ireland]
        )
        logger.info(f"{Fore.GREEN}Loaded {len(universities)} universities{Style.RESET_ALL}")
        logger.debug(f"England: {len(england)}, Scotland: {len(scotland)}, Wales: {len(wales)}, NI: {len(northern_ireland)}")
        return universities
    except Exception as e:
        logger.error(f"Error creating university list: {e}", exc_info=True)
        return []


def _ddg_search(query: str, max_results: int = 5) -> List[str]:
    """Search using the duckduckgo_search library if available.

    When the ``duckduckgo_search`` package is installed, this helper
    uses the official interface to perform a text search.  It returns
    a list of result URLs (strings) in the order returned by the
    search engine.  If the package is not available, the function
    falls back to ``None`` so that the caller can decide what to do.
    """
    if not _HAVE_DDG:
        logger.debug("duckduckgo_search package not available")
        return []
    
    if not query or not isinstance(query, str):
        logger.error(f"Invalid query parameter: {query}")
        return []
    
    results: List[str] = []
    try:
        logger.debug(f"Searching with duckduckgo_search: '{query}' (max_results={max_results})")
        with DDGS() as ddgs:
            for r in ddgs.text(query, region="uk-en", max_results=max_results):
                if not isinstance(r, dict):
                    logger.warning(f"Unexpected result type: {type(r)}")
                    continue
                href = r.get("href")
                if href and isinstance(href, str):
                    results.append(href)
                    logger.debug(f"Found result: {href}")
        logger.info(f"{Fore.GREEN}DDG search returned {len(results)} results{Style.RESET_ALL}")
    except Exception as e:
        logger.error(f"Error in _ddg_search for query '{query}': {e}", exc_info=True)
        return []
    return results


def _scrape_duckduckgo_html(query: str, max_results: int = 5) -> List[str]:
    """Fallback HTML scraper for DuckDuckGo.

    If ``duckduckgo_search`` is not available, this function builds a
    query URL for the DuckDuckGo HTML interface and scrapes the
    returned page for result links.  The HTML interface is simple and
    does not require JavaScript.  This method attempts to replicate
    human queries by including a User‑Agent header and respecting
    ``max_results``.  If an HTTP error occurs (for example, HTTP 403
    due to restrictions), the function returns an empty list.
    """
    if not query or not isinstance(query, str):
        logger.error(f"Invalid query parameter: {query}")
        return []
    
    try:
        params = quote_plus(query)
        url = f"https://duckduckgo.com/html/?q={params}"
        logger.debug(f"Scraping DuckDuckGo HTML: {url}")
        
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/105.0.0.0 Safari/537.36"
            )
        }
        
        resp = requests.get(url, headers=headers, timeout=20)
        
        if resp.status_code != 200:
            logger.warning(f"DuckDuckGo HTML returned status {resp.status_code} for query: '{query}'")
            return []
        
        logger.debug(f"Successfully retrieved HTML (length: {len(resp.text)} chars)")
        soup = BeautifulSoup(resp.text, "html.parser")
        links: List[str] = []
        
        for a in soup.select("a.result__a"):
            href = a.get("href")
            if href and isinstance(href, str):
                links.append(href)
                logger.debug(f"Found link: {href}")
                if len(links) >= max_results:
                    break
        
        logger.info(f"{Fore.GREEN}HTML scraping returned {len(links)} results{Style.RESET_ALL}")
        return links
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout while scraping DuckDuckGo for query: '{query}'")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during HTML scraping: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Unexpected error in _scrape_duckduckgo_html: {e}", exc_info=True)
        return []


def search_links(query: str, max_results: int = 5) -> List[str]:
    """Search for a query and return a list of candidate URLs.

    This helper first tries the ``duckduckgo_search`` library; if that
    yields no results (or if the library is not installed), it falls
    back to scraping DuckDuckGo's HTML interface.  The returned list
    contains at most ``max_results`` unique URLs.
    """
    if not query:
        logger.error("Empty query provided to search_links")
        return []
    
    logger.debug(f"Searching for: '{query}'")
    
    # Try official DDG library first
    results = _ddg_search(query, max_results=max_results)
    if results:
        logger.info(f"{Fore.GREEN}Found {len(results)} results using duckduckgo_search{Style.RESET_ALL}")
        return results
    
    # Fallback to HTML scraping
    logger.info(f"{Fore.YELLOW}Falling back to HTML scraping...{Style.RESET_ALL}")
    results = _scrape_duckduckgo_html(query, max_results=max_results)
    
    if not results:
        logger.warning(f"{Fore.YELLOW}No results found for query: '{query}'{Style.RESET_ALL}")
    
    return results


def is_relevant_url(url: str, university: University) -> bool:
    """Heuristic to decide whether a URL is likely to contain financial statements.

    The function checks that the URL belongs to an academic domain (ends
    with ``.ac.uk``) or the university's own domain and contains
    keywords suggesting it hosts financial statements or annual
    reports.  This is a simple heuristic and may produce false
    positives or negatives; you may refine it according to your
    specific needs.
    """
    try:
        if not url or not isinstance(url, str):
            logger.warning(f"Invalid URL provided: {url}")
            return False
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        if not domain:
            logger.debug(f"No domain found in URL: {url}")
            return False
        
        # Check for academic domains
        academic_suffixes = (".ac.uk", ".edu", ".edu.uk")
        is_academic = any(domain.endswith(suffix) for suffix in academic_suffixes)
        
        if not is_academic:
            logger.debug(f"URL not from academic domain: {url}")
            return False
        
        # Check for financial keywords
        keywords = ["financial", "statements", "accounts", "annual", "report"]
        path = parsed.path.lower()
        query = parsed.query.lower()
        full_url_lower = f"{path} {query}"
        
        has_keyword = any(k in full_url_lower for k in keywords)
        
        if has_keyword:
            logger.debug(f"{Fore.GREEN}Relevant URL found: {url}{Style.RESET_ALL}")
        else:
            logger.debug(f"URL lacks financial keywords: {url}")
        
        return has_keyword
        
    except Exception as e:
        logger.error(f"Error checking URL relevance for '{url}': {e}", exc_info=True)
        return False


def find_financial_statements(university: University, max_links: int = 5) -> List[str]:
    """Attempt to locate URLs for a university's financial statements.

    The function iterates over a set of search terms for the given
    university and performs a DuckDuckGo search for each term.  It
    collects result URLs that appear relevant according to
    ``is_relevant_url`` and stops once ``max_links`` unique URLs have
    been found.  A short delay is inserted between queries to avoid
    overwhelming the search provider.

    Parameters
    ----------
    university: University
        The university for which to find financial statement pages.
    max_links: int, optional
        Maximum number of URLs to return per university.

    Returns
    -------
    List[str]
        A list of candidate URLs where financial statements may be
        published.
    """
    try:
        if not university or not isinstance(university, University):
            logger.error(f"Invalid university object: {university}")
            return []
        
        logger.info(f"{Fore.CYAN}Searching for: {university.name}{Style.RESET_ALL}")
        
        found: List[str] = []
        seen: set[str] = set()
        search_terms = university.search_terms()
        
        if not search_terms:
            logger.warning(f"No search terms generated for {university.name}")
            return []
        
        # Use tqdm progress bar if available
        term_iterator = tqdm(search_terms, desc=f"Searching", leave=False, disable=not _HAVE_TQDM) if _HAVE_TQDM else search_terms
        
        for term in term_iterator:
            try:
                logger.debug(f"Searching term: '{term}'")
                links = search_links(term, max_results=10)
                
                for link in links:
                    if link in seen:
                        logger.debug(f"Skipping duplicate link: {link}")
                        continue
                    
                    seen.add(link)
                    
                    if is_relevant_url(link, university):
                        found.append(link)
                        logger.info(f"{Fore.GREEN}✓ Found relevant link ({len(found)}/{max_links}): {link}{Style.RESET_ALL}")
                        
                        if len(found) >= max_links:
                            logger.info(f"{Fore.GREEN}Reached maximum links for {university.name}{Style.RESET_ALL}")
                            return found
                
                # Delay between searches to be respectful
                time.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error processing search term '{term}': {e}", exc_info=True)
                continue
        
        if found:
            logger.info(f"{Fore.GREEN}Found {len(found)} link(s) for {university.name}{Style.RESET_ALL}")
        else:
            logger.warning(f"{Fore.YELLOW}No links found for {university.name}{Style.RESET_ALL}")
        
        return found
        
    except Exception as e:
        logger.error(f"Error in find_financial_statements for {university.name}: {e}", exc_info=True)
        return []


def main() -> None:
    """Iterate over universities and print candidate financial statement URLs."""
    try:
        # Print header
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}UK University Financial Statements Finder{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}\n")
        
        logger.info(f"{Fore.GREEN}Starting university financial statements search...{Style.RESET_ALL}")
        
        # Check dependencies
        if not _HAVE_DDG:
            logger.warning(f"{Fore.YELLOW}duckduckgo_search package not installed. Using HTML scraping fallback.{Style.RESET_ALL}")
        if not _HAVE_COLORAMA:
            logger.warning(f"{Fore.YELLOW}colorama package not installed. Terminal output will not be colored.{Style.RESET_ALL}")
        if not _HAVE_TQDM:
            logger.warning(f"{Fore.YELLOW}tqdm package not installed. Progress bars will not be displayed.{Style.RESET_ALL}")
        
        # Get universities
        universities = get_universities()
        
        if not universities:
            logger.error(f"{Fore.RED}Failed to load university list. Exiting.{Style.RESET_ALL}")
            sys.exit(1)
        
        # Statistics
        total_unis = len(universities)
        processed = 0
        successful = 0
        total_urls = 0
        
        # Use tqdm progress bar if available
        uni_iterator = tqdm(universities, desc="Processing universities", unit="uni") if _HAVE_TQDM else universities
        
        for uni in uni_iterator:
            try:
                urls = find_financial_statements(uni, max_links=5)
                processed += 1
                
                # Print results
                print(f"\n{Fore.CYAN}{Style.BRIGHT}{uni.name}{Style.RESET_ALL} {Fore.WHITE}({uni.country}){Style.RESET_ALL}")
                
                if urls:
                    successful += 1
                    total_urls += len(urls)
                    for u in urls:
                        print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {u}")
                else:
                    print(f"  {Fore.YELLOW}⚠ No obvious financial statement pages found{Style.RESET_ALL}")
                
            except KeyboardInterrupt:
                logger.warning(f"\n{Fore.YELLOW}Search interrupted by user{Style.RESET_ALL}")
                break
            except Exception as e:
                logger.error(f"Error processing {uni.name}: {e}", exc_info=True)
                print(f"  {Fore.RED}✗ Error occurred during search{Style.RESET_ALL}")
                continue
        
        # Print summary
        print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}Summary{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}")
        print(f"Universities processed: {Fore.GREEN}{processed}/{total_unis}{Style.RESET_ALL}")
        print(f"Successful searches: {Fore.GREEN}{successful}{Style.RESET_ALL}")
        print(f"Total URLs found: {Fore.GREEN}{total_urls}{Style.RESET_ALL}")
        
        if processed > 0:
            success_rate = (successful / processed) * 100
            avg_urls = total_urls / processed if processed > 0 else 0
            print(f"Success rate: {Fore.GREEN}{success_rate:.1f}%{Style.RESET_ALL}")
            print(f"Average URLs per university: {Fore.GREEN}{avg_urls:.1f}{Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{Style.BRIGHT}{'='*80}{Style.RESET_ALL}\n")
        
        logger.info(f"{Fore.GREEN}Search completed successfully{Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        logger.warning(f"\n{Fore.YELLOW}Program interrupted by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"{Fore.RED}Fatal error in main: {e}{Style.RESET_ALL}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{Fore.RED}Unhandled exception: {e}{Style.RESET_ALL}")
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)