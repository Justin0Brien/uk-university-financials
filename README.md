# UK University Financial Data Collection System

Automated system for collecting, extracting, and managing UK university financial documents. This coordinator-based system intelligently identifies data gaps and orchestrates document collection and text extraction.

## 🚀 Quick Start

```bash
# 1. Setup (one-time)
./install.sh
source venv/bin/activate

# 2. Verify iCloud directory exists (coordinator creates it automatically if needed)
ls ~/Library/Mobile\ Documents/com~apple~CloudDocs/Nexus/Resources/Reference\ Data/unimetrics/

# 3. Run coordinator to collect missing financial data
python run_coordinator.py --unis-per-iteration 10

# 4. Check iCloud for results (PDFs and extracted text)
ls ~/Library/Mobile\ Documents/com~apple~CloudDocs/Nexus/Resources/Reference\ Data/unimetrics/extracted_text/ | head -20
```

**Note**: All data files (PDFs, extracted text) are stored in iCloud Drive for automatic syncing across devices. The coordinator uses iCloud paths by default - no configuration needed!

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

# Show detailed summary for each university (what's found/missing)
python run_coordinator.py --summary

# Show all universities in summary (not just first 20)
python run_coordinator.py --summary --show-all-unis
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

The coordinator maintains `financial_data_tracker.csv` with 9 columns:
- **id** - Unique record ID
- **ukprn** - UK Provider Reference Number (from HESA registry)
- **university** - University name (canonical form from HESA, standardized)
- **year** - Financial year ending (e.g., "2024" means FY 2023-2024)
- **source_url** - URL where document was downloaded from (extracted from logs)
- **download_timestamp** - ISO timestamp when file was downloaded
- **pdf_path** - Path relative to iCloud base (e.g., `downloads/pdfs/file.pdf`)
- **txt_path** - Path relative to iCloud base (e.g., `extracted_text/file.txt`)
- **json_path** - Path relative to iCloud base (e.g., `extracted_text/file.json`)

**Data Quality Features:**
- **UKPRN Identification**: All universities identified by official UK Provider Reference Number
- **Canonical Names**: University names are standardized using official HESA provider names
- **Normalized Years**: All years use ending year format (2024 = FY 2023-2024) for consistency
- **iCloud-Relative Paths**: All file paths are relative to iCloud base directory for portability
- **Source URLs**: Extracted from download logs for audit trail (~32% of records)
- **Timestamps**: File download times captured for tracking (all downloaded files)

**Path Resolution**: Paths in CSV (e.g., `downloads/pdfs/file.pdf`) resolve to:
```
~/Library/Mobile Documents/com~apple~CloudDocs/Nexus/Resources/Reference Data/unimetrics/downloads/pdfs/file.pdf
```

This makes the CSV portable across machines - as long as iCloud Drive is set up, the coordinator automatically finds all files.

Missing data is tracked with placeholder rows (blank paths) so you know what's still needed.

### Single-Pass Operation

The coordinator uses a batch approach:
- Collects all search queries first
- Downloads everything in one phase
- Extracts everything in one phase
- Much more efficient than iterating

## 📂 Project Structure

```
University Financials/                 # Git repository (code + CSV only)
├── README.md                          # This file
├── run_coordinator.py                 # 🎯 MAIN SCRIPT - Run this!
├── step1_download_pdfs.py             # PDF downloader (uses DuckDuckGo search)
├── step2_extract_text.py              # Text extractor (used by coordinator)
├── verify_icloud.py                   # ✓ Verify iCloud setup (run on new machines)
├── migrate_csv_to_icloud_paths.py     # Migration script (already ran)
├── consolidate_downloads.py           # Consolidation script (already ran)
├── legacy_url_finder.py               # Old URL finder script (not used)
├── financial_data_tracker.csv         # 📊 CSV tracking all documents (iCloud-relative paths)
├── gemini_list.csv                    # University list
├── ProviderAllHESAEnhanced.csv        # HESA provider data with UKPRNs
├── requirements.txt                   # Python dependencies
├── docs/                              # Additional documentation
│   ├── README_COORDINATOR.md          # Detailed coordinator guide
│   ├── QUICK_START.md                 # Quick start guide
│   ├── IMPLEMENTATION_SUMMARY.md      # Technical details
│   └── ...                            # Other guides
├── logs/                              # Log files (auto-created, local only)
│   ├── coordinator_*.log
│   ├── extract_text_*.log
│   └── coordinator_progress_*.json
└── venv/                              # Virtual environment (local only)

~/Library/Mobile Documents/com~apple~CloudDocs/
└── Nexus/Resources/Reference Data/unimetrics/  # iCloud storage (data files)
    ├── downloads/                     # Downloaded files (3.3GB)
    │   └── pdfs/                      # All PDF downloads (894 files, 3.18GB)
    └── extracted_text/                # Extracted text files (895 files, 141MB)
        ├── *.txt                      # Plain text format
        └── *.json                     # JSON format (with metadata)
```

## ☁️ iCloud Storage & Multi-Machine Workflow

**All data files (PDFs and extracted text) are stored in iCloud Drive** for automatic syncing across machines. The Git repository contains only code and the CSV tracker (~5MB).

### Why iCloud Storage?
- **Large Dataset**: 3.3GB of data files (PDFs + extracted text) exceed GitHub free tier limits
- **Automatic Syncing**: iCloud automatically syncs files across your Mac devices
- **Clean Git Repo**: Repository stays small (<5MB) with just code and CSV tracker
- **Seamless Workflow**: Work on any machine, data is always in sync

### What's in Git ✅ (Code Repository)
- ✅ **`financial_data_tracker.csv`** - Tracking database with iCloud-relative paths
- ✅ **Python scripts** - All code and configuration files
- ✅ **Documentation** - README and docs/ folder
- ✅ **Configuration** - requirements.txt, .gitignore, etc.

**Git Repo Size**: ~5MB (just code and CSV)

### What's in iCloud ☁️ (Data Storage)
- ☁️ **`downloads/pdfs/`** - 894 PDF files (3.18GB)
- ☁️ **`extracted_text/`** - 895 text + JSON files (141MB)

**iCloud Data Size**: 3.3GB total

### What's Local Only 🖥️ (Not Synced)
- 🖥️ **`logs/`** - Log files (machine-specific, regenerated)
- 🖥️ **`venv/`** - Virtual environment (recreate on each machine)
- 🖥️ **`__pycache__/`** - Python cache

### First-Time Setup on New Machine

```bash
# 1. Clone the git repository (code + CSV only, ~5MB)
git clone <your-repo-url>
cd "University Financials"

# 2. Install Python environment
./install.sh
source venv/bin/activate

# 3. Verify iCloud setup (checks paths, directories, and data files)
python verify_icloud.py

# 4. Ready to use! Coordinator automatically uses iCloud paths
python run_coordinator.py --summary
```

**Expected output from verification script:**
```
✅ iCloud base path exists
✅ Downloads directory exists: 894 PDF files
✅ Extracted text directory exists: 866 .txt files, 29 .json files
✅ CSV tracker exists: 754 records
✅ SUCCESS: iCloud setup verified!
```

If verification fails, the script will provide specific instructions to fix the issue.

### Working Across Machines

```bash
# On Machine A: Do some work
python run_coordinator.py --unis-per-iteration 5
# → PDFs downloaded to iCloud: ~/Library/.../unimetrics/downloads/pdfs/
# → Text extracted to iCloud: ~/Library/.../unimetrics/extracted_text/
# → CSV updated with iCloud-relative paths: downloads/pdfs/file.pdf

git add financial_data_tracker.csv
git commit -m "Added 5 universities to tracking"
git push

# On Machine B: Continue where you left off
git pull  # Get updated CSV tracker
# → iCloud automatically syncs PDFs and extracted text in background
# → Wait for iCloud sync to complete (check Finder status)

source venv/bin/activate
python run_coordinator.py --unis-per-iteration 5  # Automatically skips completed work
git add financial_data_tracker.csv
git commit -m "Added 5 more universities"
git push

# Back on Machine A: Get the new tracking data
git pull  # Get CSV updates
# → iCloud automatically syncs new files from Machine B
# → You now have all PDFs and extracted text!
```

The coordinator automatically:
- Detects existing files in iCloud and skips re-downloading
- Uses iCloud paths by default (no configuration needed)
- Stores iCloud-relative paths in CSV for portability

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

# Show detailed summary for each university
python run_coordinator.py --summary

# Show all universities (not just first 20)
python run_coordinator.py --summary --show-all-unis

# Check the CSV tracker
head -20 financial_data_tracker.csv

# Count records by university
cut -d',' -f2 financial_data_tracker.csv | sort | uniq -c | sort -nr
```

### University Summary Report

The `--summary` flag shows detailed information for each university:

```bash
python run_coordinator.py --summary
```

Output example:
```
1. Anglia Ruskin University
----------------------------------------------------------------------
  ✓ Found: 3 years
    Range: 2021-22 to 2023-24
    Years: 2021-22, 2022-23, 2023-24
    Files: 3 documents
  ⚠ Missing: 2 years
    Years: 2019-20, 2020-21

2. University of Cambridge
----------------------------------------------------------------------
  ✓ Found: 5 years
    Range: 2019-20 to 2023-24
    Years: 2019-20 to 2023-24 (5 years)
    Files: 5 documents
  ✓ No missing years in range
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

### iCloud Path Not Found
```bash
# Check if iCloud Drive is enabled
ls ~/Library/Mobile\ Documents/com~apple~CloudDocs/

# Verify unimetrics directory exists
ls ~/Library/Mobile\ Documents/com~apple~CloudDocs/Nexus/Resources/Reference\ Data/unimetrics/

# Check if data directories exist
ls ~/Library/Mobile\ Documents/com~apple~CloudDocs/Nexus/Resources/Reference\ Data/unimetrics/downloads/pdfs/ | head
ls ~/Library/Mobile\ Documents/com~apple~CloudDocs/Nexus/Resources/Reference\ Data/unimetrics/extracted_text/ | head
```

If directories don't exist, the coordinator will create them automatically on first run.

### iCloud Sync Status
Check Finder to see if iCloud is actively syncing:
1. Open Finder
2. Navigate to iCloud Drive → Nexus → Resources → Reference Data → unimetrics
3. Look for cloud icons next to filenames (downloading) or checkmarks (synced)
4. Wait for sync to complete before running coordinator

### No PDFs found
```bash
# Check download directory in iCloud
ls ~/Library/Mobile\ Documents/com~apple~CloudDocs/Nexus/Resources/Reference\ Data/unimetrics/downloads/pdfs/

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

### DuckDuckGo search rate limiting
- Built-in 2-second delay between searches
- Use `--unis-per-iteration 5` for smaller batches if needed
- System automatically retries failed searches

### Already processed files
The system automatically skips files that have been extracted. To force reprocessing:
```bash
# Delete specific extracted files
rm extracted_text/University_Name_2023*

# Then re-run extraction
python step2_extract_text.py downloads_dir -o extracted_text --fast --workers 4
```

## 🛡️ Storage Architecture

The system uses a **hybrid storage model** optimized for both size constraints and portability:

### Code Repository (Git)
**Location**: `/Users/justin/code/University Financials/`  
**Size**: ~5MB

**Included in Git (synced across machines):**
- ✅ All Python code and scripts
- ✅ `financial_data_tracker.csv` (with iCloud-relative paths)
- ✅ Documentation (README.md, docs/)
- ✅ Configuration files (requirements.txt, .gitignore)

**Excluded from Git:**
- ❌ Virtual environment (`venv/`)
- ❌ Log files (`logs/`, `*.log`)
- ❌ Python cache (`__pycache__/`, `*.pyc`)
- ❌ Data directories (`downloads/`, `extracted_text/`)
- ❌ Backup files (`*_backup.csv`, `*.bak`)

### Data Storage (iCloud)
**Location**: `~/Library/Mobile Documents/com~apple~CloudDocs/Nexus/Resources/Reference Data/unimetrics/`  
**Size**: 3.3GB

**Synced via iCloud:**
- ☁️ `downloads/pdfs/` - 894 PDF files (3.18GB)
- ☁️ `extracted_text/` - 895 .txt and .json files (141MB)

### Why This Architecture?

1. **GitHub Size Limits**: Free tier has 1GB soft limit; 3.3GB of data would exceed this
2. **Automatic Syncing**: iCloud handles file syncing across Mac devices automatically
3. **Clean Repository**: Git repo stays small and fast (<5MB)
4. **Portable CSV**: CSV uses iCloud-relative paths, works on any machine with iCloud
5. **No Manual File Management**: Download once, automatically available on all devices

### Cross-Machine Workflow

```bash
# Machine A: Do work
python run_coordinator.py --unis-per-iteration 5
# Files saved to iCloud automatically
git commit -am "Added 5 universities"
git push

# Machine B: Continue work
git pull  # Get CSV updates
# Wait for iCloud to sync data files (automatic)
python run_coordinator.py --summary  # See all data from Machine A
```

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

When contributing or collaborating:

1. **Commit CSV updates**: The `financial_data_tracker.csv` is the only file that needs to be in git
2. **Data syncs via iCloud**: PDFs and extracted text are automatically synced between machines
3. Use meaningful commit messages (e.g., "Added 10 universities: 2015-2024 financial reports")
4. Test changes with `--dry-run` first
5. Update documentation in `docs/` as needed
6. Ensure iCloud sync is complete before committing CSV changes

**Workflow:**
```bash
# Make changes
python run_coordinator.py --unis-per-iteration 10

# Verify iCloud has all files (check Finder for sync status)

# Commit only code and CSV
git add *.py financial_data_tracker.csv
git commit -m "Added 10 universities"
git push
```

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
