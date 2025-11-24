# Quick Start: Download Financial Documents

## 🚀 Fast Setup (5 minutes)

### 1. Install Dependencies

```bash
cd "/Users/justin/code/University Financials"
source venv/bin/activate
pip install playwright
playwright install chromium
```

### 2. Run Your First Download

**Test with 5 universities:**
```bash
python step1_download_pdfs.py --test 5
```

**Download everything:**
```bash
python step1_download_pdfs.py
```

## 📊 What You'll Get

From just 3 test universities, we got **19 PDFs** including:
- Anglia Ruskin: 18 years of financial statements (2006-2024)
- University of Bedfordshire: Page had no documents
- University College Birmingham: 2016 annual accounts

The script automatically:
- Scraped financial pages for additional documents
- Downloaded all PDFs with proper names
- Organized everything in timestamped folder

## 🎯 Common Use Cases

### Full Download (All Universities)
```bash
python step1_download_pdfs.py -v
```
Expected: 30-60 minutes, 500+ documents

### Test Mode (Try First)
```bash
python step1_download_pdfs.py --test 10 -v
```
Expected: 5-10 minutes, ~50-100 documents

### Requests Only (Fastest)
```bash
python step1_download_pdfs.py --no-playwright
```
Expected: 10-20 minutes, may miss some files

### With Manual Intervention
```bash
python step1_download_pdfs.py --visible-browser
```
Use this if sites have CAPTCHAs or security checks

## 📁 Output Location

All downloads go to timestamped folders:
```
downloads_20251122_194849/
├── Anglia_Ruskin_University_annual-report-2023-24.pdf
├── Anglia_Ruskin_University_annual-report-2022-23.pdf
├── University_of_Oxford_2024_financial_statements.pdf
└── ...
```

## 📝 Logs

Detailed logs saved to:
```
logs/download_financials_20251122_194849.log
```

## 🎨 Console Output

You'll see colored progress:
- 🟢 Green = Downloaded successfully
- 🟡 Yellow = Warning or skipped
- 🔴 Red = Failed to download
- 🔵 Cyan = Information

## ⚙️ Options

| Flag | Description |
|------|-------------|
| `-v` | Verbose mode (detailed logs) |
| `--test N` | Process only N documents |
| `--no-scrape` | Skip page scraping |
| `--no-playwright` | Use requests only |
| `--visible-browser` | Show browser window |

## 🔧 Troubleshooting

### Browser not installed
```bash
playwright install chromium
```

### Permission denied
```bash
chmod +x step1_download_pdfs.py
```

### Module not found
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 📈 Performance

- Direct download: 1-2 seconds per file
- With scraping: 5-10 seconds per page
- Expected total time: 30-60 minutes for all universities

## 💡 Tips

1. **Start with test mode** to verify everything works
2. **Use verbose mode** (`-v`) to see what's happening
3. **Run overnight** for full download of all universities
4. **Check download folder** after to see what was collected

## 🎯 Success Criteria

After the test run, you should have:
- ✅ Downloads folder created
- ✅ Multiple PDFs downloaded
- ✅ Log file with details
- ✅ Summary statistics displayed

## Next Steps

After downloading:
1. Explore the downloads folder
2. Check file sizes and validate PDFs open correctly
3. Run full download for all universities
4. Analyze the collected financial data

## Support

Check these files for more details:
- `DOWNLOAD_GUIDE.md` - Comprehensive guide
- `logs/download_financials_*.log` - Detailed logs
- Run with `-v` flag for debugging

---

**Estimated Total Downloads:** 500-1000 documents  
**Estimated Total Size:** 5-15 GB  
**Estimated Time:** 30-60 minutes
