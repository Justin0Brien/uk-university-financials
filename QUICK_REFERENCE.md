# Quick Reference Guide

## 🚀 Setup (First Time)

```bash
# Clone the repository
git clone https://github.com/Justin0Brien/uk-university-financials.git
cd uk-university-financials

# Run the installation script
./install.sh
```

## 🏃 Running the Script

```bash
# Activate the virtual environment
source venv/bin/activate
# or use the helper:
./activate.sh

# Run the script (normal mode)
python university_financials.py

# Run with verbose debugging output
python university_financials.py -v
python university_financials.py --verbose

# When done
deactivate
```

## 🔍 Verbose Mode

Enable detailed debugging with `-v` or `--verbose`:

```bash
python university_financials.py --verbose
```

**Shows:**
- 🔎 All search terms for each university
- 📋 Every search result with title and URL
- ✅ Relevance checking with matched keywords
- 🔄 Duplicate detection
- 📊 Numbered progress for all operations
- 🎨 Color-coded DEBUG messages

## 📁 Project Structure

```
uk-university-financials/
├── university_financials.py    # Main script
├── requirements.txt            # Python dependencies
├── install.sh                  # Automated setup script
├── activate.sh                 # venv activation helper
├── .gitignore                  # Git ignore rules
├── README.md                   # Full documentation
├── ENHANCEMENTS.md            # Enhancement details
├── OUTPUT_PREVIEW.py          # Example output
└── venv/                      # Virtual environment (not in git)
```

## 🎨 Output Features

- ✅ **Green** = Success, URLs found
- ⚠️ **Yellow** = Warnings, no results
- ❌ **Red** = Errors
- 🔵 **Cyan** = Headers, university names
- 📊 Progress bars for all operations
- 📝 Detailed logs saved to timestamped files

## 🔧 Dependencies

- `beautifulsoup4` - HTML parsing
- `requests` - HTTP requests
- `ddgs` - Search API
- `colorama` - Colored output
- `tqdm` - Progress bars

## 🌐 GitHub Repository

**URL:** https://github.com/Justin0Brien/uk-university-financials

```bash
# Update from remote
git pull origin main

# Push local changes
git add .
git commit -m "Your message"
git push origin main
```

## 📊 What It Does

Searches for financial statement URLs for 180+ UK universities:
- 132 English universities
- 19 Scottish universities
- 8 Welsh universities
- 4 Northern Ireland universities

## ⚡ Performance

- ~5-10 seconds per university
- ~15-30 minutes total
- Respectful rate limiting (1s delays)
- Memory efficient (<50MB)

## 🐛 Troubleshooting

### Virtual environment not activating
```bash
# Recreate it
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Import errors
```bash
# Make sure venv is activated
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

### No results found
- Check internet connection
- Review logs in `university_financials_*.log`
- Search engines may rate-limit (wait and retry)

## 📝 Log Files

Log files are created automatically with timestamp:
- Format: `university_financials_YYYYMMDD_HHMMSS.log`
- Location: Same directory as script
- Contains: Full debug info, stack traces, all operations

## 🔐 Privacy & Ethics

- Only searches public information
- Respects robots.txt and rate limits
- Does not download documents
- Only identifies public URLs
- No authentication or scraping of restricted content
