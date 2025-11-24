# Financial Document Downloader

Automated download of financial statements and reports from UK university websites using multiple fallback strategies.

## Features

✅ **Multiple Download Strategies**
- Direct download with requests (fastest)
- Headless browser with Playwright (bypasses basic protections)
- Visible browser mode (allows manual security checks)

✅ **Intelligent Page Scraping**
- Automatically finds additional documents on financial pages
- Extracts all relevant PDFs, DOCX, XLSX files
- Filters out irrelevant links (courses, admissions, etc.)

✅ **Comprehensive Error Handling**
- Retries on failures with exponential backoff
- Graceful fallback between download methods
- Detailed logging of all operations

✅ **Progress Tracking**
- Colored terminal output with status indicators
- Progress bars for batch downloads
- Real-time statistics and summaries

✅ **Smart File Management**
- Automatic duplicate detection
- Safe filename generation
- Organized output with timestamps

## Installation

### 1. Install Python Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

After installing the Python package, you need to install the browser binaries:

```bash
playwright install chromium
```

This downloads the Chromium browser used for automated downloads.

## Usage

### Basic Usage

Download all financial documents:

```bash
python step1_download_pdfs.py
```

### With Verbose Logging

See detailed information about each download attempt:

```bash
python step1_download_pdfs.py -v
```

### Test Mode

Process only the first 10 documents (useful for testing):

```bash
python step1_download_pdfs.py --test 10
```

### Disable Page Scraping

Only download the specific URLs in CSV files (don't scrape pages for additional documents):

```bash
python step1_download_pdfs.py --no-scrape
```

### Requests Only Mode

Only use direct download method (faster but may miss some files):

```bash
python step1_download_pdfs.py --no-playwright
```

### Visible Browser Mode

Use a visible browser window (allows you to manually solve CAPTCHAs or security checks):

```bash
python step1_download_pdfs.py --visible-browser
```

### Combined Options

```bash
python step1_download_pdfs.py -v --test 5 --visible-browser
```

## How It Works

### 1. Document Discovery

The script loads documents from two sources:

- `university_financials_results_*.csv` - URLs found by the search script
- `gemini_list.csv` - Curated list of financial pages

### 2. Download Strategies

The script tries multiple methods in order:

**Strategy 1: Direct Download (requests)**
- Fastest method
- Works for direct PDF/DOCX links
- May be blocked by some sites

**Strategy 2: Headless Browser (Playwright)**
- Runs invisible browser automation
- Bypasses JavaScript protections
- Handles dynamic content

**Strategy 3: Visible Browser (Playwright)**
- Opens actual browser window
- Allows manual intervention
- For sites with CAPTCHA or security checks

### 3. Page Scraping

When enabled, the script:
1. Loads each financial page
2. Finds all links to PDFs, DOCX, XLSX files
3. Filters for financial keywords (statement, account, annual, etc.)
4. Excludes non-financial pages (courses, admissions, etc.)
5. Downloads all relevant documents

### 4. File Organization

Downloaded files are saved with structured names:

```
University_Name_2024_original_filename.pdf
University_Name_2023_financial_statements.pdf
```

All downloads go to a timestamped directory:
```
downloads_20251122_143022/
```

## Output

### Console Output

Colored status messages:
- 🟢 Green: Successful downloads
- 🟡 Yellow: Warnings or skipped files
- 🔴 Red: Errors
- 🔵 Cyan: Informational messages

### Log Files

Detailed logs saved to:
```
logs/download_financials_YYYYMMDD_HHMMSS.log
```

Contains:
- All download attempts
- Error messages with stack traces
- Timing information
- Method used for each download

### Download Directory

```
downloads_20251122_143022/
├── University_of_Cambridge_2024_financial_statements.pdf
├── University_of_Oxford_2023_annual_report.pdf
├── Imperial_College_London_2024_accounts.pdf
└── ...
```

## Download Statistics

At the end of each run, you'll see:

```
================================================================================
Download Summary
================================================================================
Documents processed: 150/200
Successful downloads: 120
Failed downloads: 25
Skipped (duplicates): 5
Additional documents found: 45

Download methods used:
  requests: 80
  playwright_headless: 35
  playwright_visible: 5

Downloads saved to: downloads_20251122_143022
================================================================================
```

## Troubleshooting

### "requests library not installed"

```bash
pip install requests
```

### "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### "BeautifulSoup not installed"

```bash
pip install beautifulsoup4
```

### Downloads failing with 403/403 errors

Try these options:
1. Use `--visible-browser` to allow manual security checks
2. Add delays between downloads (built-in 0.5-1s delays)
3. Run in smaller batches using `--test N`

### Browser not opening in visible mode

Make sure you have GUI access (won't work over SSH without X forwarding).

### No CSV files found

Run the search script first:
```bash
python university_financials.py
```

## Advanced Usage

### Processing Specific Universities

Edit the CSV files to include only the universities you want:

```python
import pandas as pd

df = pd.read_csv('university_financials_results_20251122_143022.csv')
cambridge = df[df['University'].str.contains('Cambridge')]
cambridge.to_csv('cambridge_only.csv', index=False)
```

Then modify the script to load your custom CSV.

### Customizing Scraping Logic

Edit the `is_financial_document()` function to customize what documents are downloaded:

```python
def is_financial_document(url: str, link_text: str = "") -> bool:
    # Add your custom logic here
    # Return True if the URL should be downloaded
    pass
```

### Adding New File Types

Edit the `doc_extensions` list in `is_financial_document()`:

```python
doc_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.html']
```

## Rate Limiting

The script includes built-in delays to respect website resources:

- 0.5 seconds between documents
- 1 second between scraped documents from same page
- Automatic retry with exponential backoff on failures

## Data Analysis

After downloading, analyze the documents:

### Count Downloads by University

```bash
ls -1 downloads_*/ | cut -d'_' -f1-3 | sort | uniq -c | sort -rn
```

### Find Most Recent Reports

```bash
find downloads_*/ -name "*2024*.pdf" | wc -l
```

### Check File Sizes

```bash
du -sh downloads_*/
find downloads_*/ -type f -exec du -h {} + | sort -rh | head -20
```

## Security Considerations

- The script mimics browser behavior but identifies itself honestly via User-Agent
- No attempts to circumvent legitimate security measures
- Respects robots.txt (via rate limiting and delays)
- Only downloads publicly accessible documents

## Performance

### Typical Performance

- Direct downloads: ~1-2 seconds per file
- Playwright downloads: ~5-10 seconds per file
- Page scraping: ~3-5 seconds per page

### Expected Runtime

- 200 documents with scraping: 30-60 minutes
- 200 documents without scraping: 10-20 minutes
- 50 documents (test mode): 5-10 minutes

## Next Steps

After downloading documents:

1. **Validate Downloads**
   ```bash
   python validate_downloads.py
   ```

2. **Extract Financial Data**
   - Use PDF parsing libraries (PyPDF2, pdfplumber)
   - Extract tables and figures
   - Build structured dataset

3. **Analyze Trends**
   - Compare year-over-year changes
   - Benchmark across institutions
   - Identify patterns

## Contributing

To add support for new file types or improve scraping logic:

1. Test with `--test 5 -v` to see detailed logs
2. Update the relevant function
3. Run full test to verify no regressions

## License

This script is for research and educational purposes. Respect website terms of service and copyright.
