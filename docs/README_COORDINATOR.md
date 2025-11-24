# Financial Data Collection System - README

## Overview

This system intelligently collects, extracts, and manages UK university financial documents. It consists of three coordinated scripts that work together to build a comprehensive dataset of financial annual reports going back as far as available.

## Components

### 1. `step1_download_pdfs.py` - Document Downloader
Downloads PDF financial documents from university websites.

**New Features:**
- **Custom Search**: Use `--search` to search for specific documents
- **Targeted Output**: Use `--output` to specify download directory
- **Method Selection**: Choose between `requests` or `playwright`
- **Result Limiting**: Use `--limit` to control number of results

**Usage Examples:**
```bash
# Search for specific university/year
python step1_download_pdfs.py --search "University of Edinburgh 2020-21 annual report" --output downloads_temp --limit 5

# Normal mode with CSV files
python step1_download_pdfs.py --no-scrape

# Test mode
python step1_download_pdfs.py --test 10
```

### 2. `step2_extract_text.py` - Text Extractor
Extracts structured text from PDF documents with resume capability.

**Key Features:**
- **Skip Already Processed**: Automatically skips PDFs that have already been extracted
- **Resume Capability**: Can be stopped and restarted - continues from where it left off
- **Suppressed Warnings**: Pdfminer warnings completely silenced for 30x speed improvement
- **Fast Mode**: Use `--fast` for 4-5x speedup
- **Parallel Processing**: Use `--workers 4` for additional 4x speedup

**Usage Examples:**
```bash
# Process new PDFs (automatically skips existing)
python step2_extract_text.py downloads_20251122_224411 -o extracted_text --fast --workers 4

# Force reprocess (delete existing txt/json files first)
rm extracted_text/University_Name_2023*.txt
python step2_extract_text.py downloads_20251122_224411 -o extracted_text --fast --workers 4
```

### 3. `run_coordinator.py` - Intelligent Coordinator (NEW)
Orchestrates the entire collection process to fill data gaps in a single efficient pass.

**What It Does:**
1. **Analyzes** existing extracted text to identify available years per university
2. **Identifies** missing financial years for each university
3. **Collects** all search queries for missing reports
4. **Downloads** ALL found PDFs in one batch to a timestamped directory
5. **Extracts** text from all downloads in parallel (both .txt and .json formats)

**Key Features:**
- Single-pass operation: downloads all, then extracts all (no interleaving)
- Works backward in time up to 25 years (configurable)
- Both .txt and .json output formats for maximum flexibility
- Timestamped download directories for easy tracking
- Comprehensive reporting
- Dry-run mode to preview searches

**Usage Examples:**
```bash
# Run with defaults (processes 5 universities, searches 3 years each)
python run_coordinator.py

# Dry run to see what would be searched
python run_coordinator.py --dry-run

# Process more universities
python run_coordinator.py --unis-per-iteration 10

# Use specific directories
python run_coordinator.py --extracted extracted_text --downloads downloads_custom

# Look further back in time
python run_coordinator.py --max-lookback 30

# Verbose output for debugging
python run_coordinator.py -v
```

## Complete Workflow

### Initial Setup
```bash
# 1. Download initial batch of documents
python step1_download_pdfs.py

# 2. Extract text from all PDFs
python step2_extract_text.py downloads_20251122_224411 -o extracted_text --fast --workers 4
```

### Iterative Gap Filling
```bash
# 3. Run coordinator to find and fill gaps (single pass)
python run_coordinator.py --unis-per-iteration 10

# The coordinator will:
# - Analyze what you have
# - Find missing years for 10 universities
# - Search for ALL missing documents
# - Download them ALL to downloads_coordinator_YYYYMMDD_HHMMSS/
# - Extract ALL PDFs to both .txt and .json formats
# - Show final summary
```

### Running Multiple Times
```bash
# Run coordinator multiple times to process different batches
# Each run creates a new timestamped download directory

# First run: process 5 universities
python run_coordinator.py --unis-per-iteration 5

# Second run: process next 10 universities  
python run_coordinator.py --unis-per-iteration 10

# The extraction script automatically skips already-processed files
# Downloads are organized in timestamped directories for easy tracking
```

## File Naming Convention

Extracted files follow this pattern:
```
UniversityName_DocumentTitle.txt
UniversityName_Year_DocumentTitle.txt
```

Examples:
- `University_of_Cambridge_annual-report-2023-24.txt`
- `Anglia_Ruskin_University_annual-report-and-accounts-2022-23.txt`
- `SOAS_University_of_London_financial-statements-2021-22.txt`

## Progress Tracking

### Extraction Progress
The extraction script automatically tracks:
- Which PDFs have been processed (checks for existing .txt/.json files)
- Shows "Skipped (already processed): N" in summary
- Can restart any time without losing progress

### Coordinator Progress
The coordinator saves progress to JSON files:
- `coordinator_progress_YYYYMMDD_HHMMSS.json`

Contains:
```json
{
  "timestamp": "2025-11-23T15:14:12",
  "iteration": 3,
  "universities": {
    "University of Cambridge": {
      "years": ["2020-21", "2021-22", "2022-23", "2023-24"],
      "min_year": "2020-21",
      "max_year": "2023-24",
      "file_count": 4
    }
  },
  "missing_data": {
    "University of Cambridge": ["2018-19", "2019-20"]
  }
}
```

## Performance Optimizations

### Extraction Speed
- **Normal mode**: ~3-4 min per file
- **Fast mode**: ~40-60 sec per file (5-10x speedup)
- **Fast + 4 workers**: ~10-15 sec per file (15-20x speedup)
- **Pdfminer warning suppression**: 30x additional speedup on malformed PDFs
- **Both formats**: Coordinator extracts both .txt and .json simultaneously

### Coordinator Efficiency
- Single-pass operation: collects all queries, downloads all, then extracts all
- Processes N universities per run (default: 5)
- Searches for top 3 missing years per university
- Limits search results to avoid downloading duplicates
- Timestamped directories keep each run's downloads organized

## Handling Edge Cases

### Corrupt PDFs
The system handles corrupt PDFs gracefully:
- Timeout after 5 minutes per PDF
- Logs error and continues with next file
- Failed files listed in summary

### Already Downloaded
- Extraction checks output directory before processing
- Skips files that already have .txt (or .json if format=both)
- Shows count of skipped files in summary

### Missing University Data
If no data exists for a university:
- Coordinator won't search for it (needs at least one file to identify patterns)
- Add university manually by downloading one report first

### Search Limitations
Google search has rate limits:
- Coordinator includes delays between searches
- If blocked, wait 15-30 minutes and restart
- Consider spreading iterations across multiple days

## Directory Structure

```
University Financials/
├── step1_download_pdfs.py   # Downloader
├── step2_extract_text.py               # Text extractor
├── run_coordinator.py     # Coordinator (NEW)
├── gemini_list.csv                   # University list
├── downloads_YYYYMMDD_HHMMSS/        # Initial downloads
│   └── *.pdf
├── downloads_coordinator_YYYYMMDD_HHMMSS/  # Coordinator downloads
│   └── *.pdf
├── extracted_text/                   # Extracted text (all formats)
│   ├── *.txt                         # Plain text format
│   └── *.json                        # JSON format (metadata + text)
├── logs/                             # Log files
│   ├── extract_text_*.log
│   ├── coordinator_*.log
│   └── download_*.log
└── coordinator_progress_*.json       # Progress tracking
```

## Troubleshooting

### "No extracted text found"
```bash
# Make sure extraction ran first
python step2_extract_text.py downloads_DIR -o extracted_text --fast --workers 4
```

### "Warnings still appearing"
The stderr suppression should eliminate pdfminer warnings. If you still see them:
```bash
python step2_extract_text.py downloads_DIR -o extracted_text --fast --workers 4 2>/dev/null
```

### "Search not finding documents"
- Check search queries in dry-run mode
- Verify university names are correct
- Try adjusting search terms in coordinator
- Google may require CAPTCHA after many searches

### "Extraction hanging"
- Some PDFs are severely malformed
- 5-minute timeout will skip them automatically
- Check logs for specific files causing issues

## Future Enhancements

Potential improvements:
1. Use official Google Custom Search API (better rate limits)
2. Add support for multiple output formats (CSV, database)
3. Implement data quality checks (completeness, consistency)
4. Add visualization of data coverage over time
5. Support for international universities
6. Automated financial data extraction (not just text)

## License & Disclaimer

This tool is for educational and research purposes. Always respect:
- Website terms of service
- robots.txt files
- Rate limiting and fair use
- Copyright and data usage policies

## Support

For issues, questions, or contributions:
- Check logs/ directory for detailed error messages
- Run with `-v` or `--verbose` for debug output
- Use `--dry-run` to preview operations
- Review progress JSON files for state information
