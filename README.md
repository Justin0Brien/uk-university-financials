# UK University Financial Data Collection System

Automated system for collecting, extracting, and managing UK university financial documents. This coordinator-based system intelligently identifies data gaps and orchestrates document collection and text extraction.

## 🚀 Quick Start

```bash
# 1. Setup (one-time)
./install.sh
source venv/bin/activate

# 2. Run coordinator to collect missing financial data
python run_coordinator.py --unis-per-iteration 10

# 3. Check extracted_text/ for results (.txt and .json files)
ls -la extracted_text/ | head -20
```

## 📋 Overview

The system consists of three main components:

1. **`run_coordinator.py`** - 🎯 **MAIN SCRIPT** - Orchestrates the entire workflow (use this!)
2. **`step1_download_pdfs.py`** - Downloads PDFs from university websites (called by coordinator)
3. **`step2_extract_text.py`** - Extracts text from PDFs with multi-column support (called by coordinator)

The coordinator automatically manages the entire workflow: analyzing what data you have, identifying missing years, downloading new documents, and extracting their content.

## 🎯 Main Command: The Coordinator

The coordinator is your primary interface. It handles everything automatically:

```bash
# Basic usage - process 5 universities (default)
python run_coordinator.py

# Process more universities per run
python run_coordinator.py --unis-per-iteration 10

# Preview what would be searched (no downloads)
python run_coordinator.py --dry-run

# Look further back in time (default: 5 years back, 2 forward)
python run_coordinator.py --max-lookback 10

# Verbose output for debugging
python run_coordinator.py -v
```

### What the Coordinator Does

1. **Loads** the CSV tracker (`financial_data_tracker.csv`) to see what's been collected
2. **Analyzes** your existing `extracted_text/` directory
3. **Identifies** missing financial years for each university
4. **Creates placeholders** in CSV for missing university/year combinations
5. **Searches** Google for missing documents
6. **Downloads** all found PDFs to `downloads_coordinator_YYYYMMDD_HHMMSS/`
7. **Extracts** all PDFs to both `.txt` and `.json` formats
8. **Updates** CSV tracker with all file paths and metadata
9. **Reports** final coverage summary

### CSV Tracking System

The coordinator maintains `financial_data_tracker.csv` with columns:
- **id** - Unique record ID
- **university** - University name
- **year** - Financial year (e.g., "2023-24" or "2023")
- **source_url** - URL where document was found (if available)
- **pdf_path** - Full path to downloaded PDF file
- **txt_path** - Full path to extracted .txt file
- **json_path** - Full path to extracted .json file

Missing data is tracked with placeholder rows (blank paths) so you know what's still needed.

### Single-Pass Operation

The coordinator uses a batch approach:
- Collects all search queries first
- Downloads everything in one phase
- Extracts everything in one phase
- Much more efficient than iterating

## 📂 Project Structure

```
University Financials/
├── README.md                          # This file
├── run_coordinator.py                 # 🎯 MAIN SCRIPT - Run this!
├── step1_download_pdfs.py             # PDF downloader (used by coordinator)
├── step2_extract_text.py              # Text extractor (used by coordinator)
├── legacy_url_finder.py               # Old URL finder script (not used)
├── financial_data_tracker.csv         # 📊 CSV tracking all documents
├── gemini_list.csv                    # University list
├── requirements.txt                   # Python dependencies
├── docs/                              # Additional documentation
│   ├── README_COORDINATOR.md          # Detailed coordinator guide
│   ├── QUICK_START.md                 # Quick start guide
│   ├── IMPLEMENTATION_SUMMARY.md      # Technical details
│   └── ...                            # Other guides
├── logs/                              # Log files (auto-created)
│   ├── coordinator_*.log
│   ├── extract_text_*.log
│   └── coordinator_progress_*.json
├── downloads_coordinator_*/           # Downloaded PDFs (timestamped)
└── extracted_text/                    # Extracted text files
    ├── *.txt                          # Plain text format
    └── *.json                         # JSON format (with metadata)
```

## 🔧 Installation

### Automated Setup (Recommended)

```bash
./install.sh
source venv/bin/activate
```

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or: source activate.sh

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

Core libraries:
- `pdfplumber` - PDF text extraction with multi-column support
- `requests` - HTTP requests for downloading
- `beautifulsoup4` - HTML parsing
- `playwright` - Browser automation (optional)
- `colorama` - Colored terminal output
- `tqdm` - Progress bars

## 📊 Output Formats

### Text Files (.txt)
Plain text extraction with page markers:
```
================================================================================
PDF: University_of_Cambridge_annual_report_2023.pdf
Pages: 156
...
================================================================================
PAGE 1
================================================================================

[Page content here]
```

### JSON Files (.json)
Structured format with metadata:
```json
{
  "metadata": {
    "pdf_file": "University_of_Cambridge_annual_report_2023.pdf",
    "pages": 156,
    "title": "Annual Report 2023",
    "author": "University of Cambridge"
  },
  "pages": [
    {
      "page": 1,
      "text": "..."
    }
  ]
}
```

## 🎓 Common Workflows

### Collecting Missing Data for All Universities

```bash
# Run multiple times to process different batches
python run_coordinator.py --unis-per-iteration 10  # Batch 1
python run_coordinator.py --unis-per-iteration 10  # Batch 2
python run_coordinator.py --unis-per-iteration 10  # Batch 3

# The system automatically:
# - Skips already-extracted files
# - Creates new timestamped download directories
# - Tracks progress in logs/
```

### Checking Current Coverage

```bash
# See what data you have
ls -la extracted_text/ | wc -l

# Run dry-run to see what's missing
python run_coordinator.py --dry-run

# Check the CSV tracker
head -20 financial_data_tracker.csv

# Count records by university
cut -d',' -f2 financial_data_tracker.csv | sort | uniq -c | sort -nr
```

### Working with the CSV Tracker

```bash
# View all records for a specific university
grep "Cambridge" financial_data_tracker.csv

# Find missing data (rows with empty pdf_path)
awk -F',' '$5 == ""' financial_data_tracker.csv

# Count how many documents per year
cut -d',' -f3 financial_data_tracker.csv | sort | uniq -c

# Export to Excel or open in spreadsheet software
open financial_data_tracker.csv
```

### Manual Download and Extract

If you need more control:

```bash
# 1. Download from specific search
python step1_download_pdfs.py --search "University of Cambridge 2023 annual report" --output downloads_manual --limit 5

# 2. Extract from downloaded PDFs
python step2_extract_text.py downloads_manual -o extracted_text --fast --workers 4 --format both
```

## ⚡ Performance

- **Fast Mode**: 5-10x speedup over normal extraction
- **Parallel Processing**: 4 workers process multiple PDFs simultaneously
- **Combined**: ~10-15 seconds per PDF vs ~3-4 minutes
- **Warning Suppression**: Eliminates pdfminer warnings for 30x additional speedup on malformed PDFs
- **Resume Capability**: Automatically skips already-processed files

## 📖 Additional Documentation

For more detailed information, see the `docs/` folder:

- **`docs/README_COORDINATOR.md`** - Complete coordinator documentation
- **`docs/QUICK_START.md`** - Step-by-step getting started guide
- **`docs/IMPLEMENTATION_SUMMARY.md`** - Technical implementation details
- **`docs/WORKFLOW.md`** - Detailed workflow explanations
- **`docs/DOWNLOAD_GUIDE.md`** - Manual download instructions
- **`docs/CSV_GUIDE.md`** - Working with CSV files

## 🔍 Troubleshooting

### No PDFs found
```bash
# Check download directory
ls downloads_coordinator_*/

# Try manual search first
python step1_download_pdfs.py --search "University Name" --output test_download --limit 3
```

### Extraction errors
```bash
# Check logs
tail -f logs/extract_text_*.log

# Try single file
python step2_extract_text.py test_file.pdf -o test_output --fast
```

### Google search blocked
- Wait 15-30 minutes between runs
- Use `--unis-per-iteration 5` for smaller batches
- Consider spreading across multiple days

### Already processed files
The system automatically skips files that have been extracted. To force reprocessing:
```bash
# Delete specific extracted files
rm extracted_text/University_Name_2023*

# Then re-run extraction
python step2_extract_text.py downloads_dir -o extracted_text --fast --workers 4
```

## 🛡️ Git Configuration

The repository is configured to exclude:
- ✅ All PDF files (`*.pdf`, `downloads_*/`)
- ✅ Extracted text files (`extracted_text/`)
- ✅ Log files (`logs/`, `*.log`)
- ✅ Progress files (`coordinator_progress_*.json`)
- ✅ Virtual environment (`venv/`)
- ✅ Python cache (`__pycache__/`, `*.pyc`)

This keeps the repository clean and focused on code, not data.

## 📝 File Naming Convention

Extracted files follow this pattern:
```
UniversityName_DocumentTitle.txt
UniversityName_DocumentTitle.json
```

Examples:
- `University_of_Cambridge_annual-report-2023-24.txt`
- `University_of_Cambridge_annual-report-2023-24.json`
- `Anglia_Ruskin_University_financial-statements-2022-23.txt`

## 🚦 Exit Codes and Error Handling

The coordinator provides clear exit codes:
- `0` - Success
- `1` - Error (check logs)
- `130` - User interrupted (Ctrl+C)

All errors are logged to `logs/coordinator_*.log`

## 🤝 Contributing

When contributing:
1. Never commit PDF files, extracted text, or logs
2. Test changes with `--dry-run` first
3. Update documentation in `docs/` as needed
4. Keep the main README focused on the coordinator workflow

## 📄 License

This tool is for educational and research purposes. Always respect:
- Website terms of service
- robots.txt files  
- Rate limiting and fair use
- Copyright and data usage policies

## 🆘 Support

For issues:
1. Check `logs/` directory for error details
2. Run with `-v` flag for verbose output
3. Review `docs/README_COORDINATOR.md` for detailed information
4. Use `--dry-run` to preview operations without making changes

---

**Pro Tip**: Start with `--dry-run` to see what the coordinator would do, then run it for real once you're comfortable with the plan!
