# UK University Financial Statements Finder

This script automatically searches for and identifies financial statement URLs for UK universities.

## Features

- ✅ **Comprehensive Error Handling**: Robust error checking throughout the entire codebase
- 📝 **Detailed Logging**: Dual logging system (console + file) with timestamped log files
- 🎨 **Colored Terminal Output**: Easy-to-read colored console output using colorama
- 📊 **Progress Bars**: Visual progress tracking with tqdm
- 🔍 **Smart Search**: Uses DuckDuckGo with automatic fallback to HTML scraping
- 📈 **Statistics**: Detailed summary of search results and success rates

## Installation

### Option 1: Automated Setup (Recommended)

Run the installation script which will create a virtual environment and install all dependencies:

```bash
./install.sh
```

### Option 2: Manual Installation

1. Create a virtual environment:

```bash
python3 -m venv venv
```

2. Activate the virtual environment:

```bash
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Dependencies

- `beautifulsoup4` - HTML parsing for web scraping
- `requests` - HTTP requests
- `ddgs` - Official DuckDuckGo search API (optional but recommended)
- `colorama` - Cross-platform colored terminal output
- `tqdm` - Progress bars

## Usage

### Quick Start

1. Activate the virtual environment:

```bash
source venv/bin/activate
# or use the helper script: ./activate.sh
```

2. Run the script directly:

```bash
python university_financials.py
```

3. For verbose debugging output:

```bash
python university_financials.py -v
# or
python university_financials.py --verbose
```

4. Deactivate when done:

```bash
deactivate
```

### Verbose Mode

Use `-v` or `--verbose` flag for detailed debugging output that shows:
- All search terms generated for each university
- Each search result with title and URL
- Relevance checking details with matched keywords
- Link duplicate detection
- Full search progress with numbered items
- Color-coded DEBUG level messages

Example:
```bash
python university_financials.py --verbose
```

The script will:
1. Load a list of 180+ UK universities
2. Search for financial statement URLs for each university
3. Display results with colored output and progress bars
4. Generate a timestamped log file with detailed information

## Output

### Console Output
- Colored status messages (green for success, yellow for warnings, red for errors)
- Progress bars showing search progress
- Summary statistics at the end

### Log Files
- Timestamped log files (e.g., `university_financials_20251122_143022.log`)
- Detailed debug information
- Full error stack traces for troubleshooting

## Error Handling

The script includes comprehensive error handling for:
- Network timeouts and connection errors
- Invalid URLs and malformed data
- Missing dependencies with graceful fallbacks
- Search engine rate limiting
- Keyboard interrupts (Ctrl+C)

## Logging Levels

- **DEBUG**: Detailed diagnostic information (file only)
- **INFO**: General informational messages
- **WARNING**: Warning messages for non-critical issues
- **ERROR**: Error messages with full stack traces

## Customization

You can modify:
- `max_links`: Maximum URLs to find per university (default: 5)
- Search terms in the `search_terms()` method
- URL relevance heuristics in `is_relevant_url()`
- Logging configuration in `setup_logging()`

## Notes

- The script respects rate limits with 1-second delays between searches
- Only searches for URLs on academic domains (.ac.uk, .edu, .edu.uk)
- Does not download documents, only identifies URLs
- All UK nations included: England, Scotland, Wales, Northern Ireland
