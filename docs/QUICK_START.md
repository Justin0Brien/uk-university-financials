# Quick Start Guide - Financial Data Collection

## 🚀 Getting Started (First Time)

```bash
# 1. Download initial documents (2-3 hours)
python download_financial_documents.py

# 2. Extract text from PDFs (2-3 hours with fast mode)
python extract_pdf_text.py downloads_YYYYMMDD_HHMMSS -o extracted_text --fast --workers 4

# 3. Start coordinator to fill gaps (runs iteratively)
python financial_data_coordinator.py --max-iterations 5
```

## 🔄 Daily Operations

### Check What You Have
```bash
# Dry run to see gaps
python financial_data_coordinator.py --dry-run

# Check progress files
cat coordinator_progress_*.json | jq '.universities | length'
```

### Continue Collection
```bash
# Resume coordinator (automatically skips processed files)
python financial_data_coordinator.py --max-iterations 10

# If interrupted, just run again - it resumes automatically
```

### Process New Downloads
```bash
# Extract text from new PDFs (skips existing automatically)
python extract_pdf_text.py downloads_NEW -o extracted_text --fast --workers 4
```

## 📊 Common Tasks

### Search for Specific University/Year
```bash
python download_financial_documents.py \
  --search "University of Cambridge 2019-20 annual report" \
  --output downloads_temp \
  --limit 5
```

### Extract Single PDF
```bash
python extract_pdf_text.py downloads_temp -o extracted_text --fast --limit 1
```

### Force Reprocess PDFs
```bash
# Delete existing extracted files
rm extracted_text/University_Name_2023*.txt
rm extracted_text/University_Name_2023*.json

# Run extraction again
python extract_pdf_text.py downloads_DIR -o extracted_text --fast --workers 4
```

### Check Logs
```bash
# Latest coordinator log
tail -f logs/coordinator_$(ls -t logs/coordinator_*.log | head -1 | xargs basename)

# Latest extraction log  
tail -f logs/extract_text_$(ls -t logs/extract_text_*.log | head -1 | xargs basename)
```

## 🛠️ Troubleshooting

### "No documents found"
```bash
# Check if search works
python download_financial_documents.py \
  --search "University test" \
  --limit 1 \
  -v
```

### "Extraction hanging"
```bash
# Check which file is causing issues
tail logs/extract_text_*.log

# Skip it by deleting the PDF
rm downloads_DIR/problematic_file.pdf
```

### "Too many warnings"
```bash
# Redirect stderr to null
python extract_pdf_text.py downloads_DIR -o extracted_text --fast --workers 4 2>/dev/null
```

### "Google blocking searches"
```bash
# Wait 30 minutes, then:
python financial_data_coordinator.py --unis-per-iteration 2 --max-iterations 5
```

## 📈 Monitor Progress

### Count Files
```bash
# Total PDFs downloaded
find downloads_* -name "*.pdf" | wc -l

# Total text files extracted  
ls extracted_text/*.txt | wc -l

# Universities with data
ls extracted_text/*.txt | cut -d_ -f1 | sort -u | wc -l
```

### Check Coverage
```bash
# Run analyzer
python financial_data_coordinator.py --dry-run --max-iterations 1

# View progress JSON
cat coordinator_progress_*.json | jq '.universities | length'
cat coordinator_progress_*.json | jq '.missing_data | length'
```

## ⚙️ Performance Tuning

### Fast Machine
```bash
# Use more workers
python extract_pdf_text.py downloads_DIR -o extracted_text --fast --workers 8

# Process more unis per iteration
python financial_data_coordinator.py --unis-per-iteration 10
```

### Slow Machine
```bash
# Use fewer workers
python extract_pdf_text.py downloads_DIR -o extracted_text --fast --workers 2

# Process fewer unis
python financial_data_coordinator.py --unis-per-iteration 3
```

### Rate Limiting
```bash
# Slow down coordinator
python financial_data_coordinator.py \
  --unis-per-iteration 2 \
  --max-iterations 3
  
# Wait between runs
# (Add sleep 1800 between iterations in your script)
```

## 🎯 Recommended Workflow

### Week 1: Initial Collection
```bash
# Monday: Download from CSV
python download_financial_documents.py

# Tuesday: Extract all (while monitoring)
python extract_pdf_text.py downloads_* -o extracted_text --fast --workers 4

# Wednesday: Start coordinator (5 iterations)
python financial_data_coordinator.py --max-iterations 5

# Thursday: Continue coordinator
python financial_data_coordinator.py --max-iterations 5

# Friday: Review progress, identify gaps
python financial_data_coordinator.py --dry-run
```

### Week 2+: Gap Filling
```bash
# Run daily (spread load across days)
python financial_data_coordinator.py --max-iterations 3 --unis-per-iteration 3
```

## 📝 Best Practices

1. **Always use --fast mode** (unless you need perfect column layout)
2. **Always use --workers 4** (or adjust for your CPU)
3. **Let coordinator run overnight** (it's designed for that)
4. **Check logs daily** (catch issues early)
5. **Back up extracted_text/** (it's your processed data)
6. **Delete downloads after extraction** (saves disk space)
7. **Run coordinator in screen/tmux** (survives disconnects)

## 🔐 Safety Features

- ✅ Coordinator saves progress after each iteration
- ✅ Extraction skips already-processed files
- ✅ Timeout on hanging PDFs (5 minutes)
- ✅ Logs everything for debugging
- ✅ Dry-run mode for testing
- ✅ Graceful handling of Ctrl+C

## 📦 Disk Space Management

```bash
# Check space used
du -sh downloads_*
du -sh extracted_text/

# Clean up old downloads (after extraction)
rm -rf downloads_2025*

# Keep only txt files (delete json)
rm extracted_text/*.json
```

## 🎓 Tips & Tricks

### Run in Background
```bash
# Using screen
screen -S coordinator
python financial_data_coordinator.py --max-iterations 10
# Ctrl+A, D to detach
# screen -r coordinator to reattach

# Using nohup
nohup python financial_data_coordinator.py --max-iterations 10 &
tail -f nohup.out
```

### Process Specific Universities
```bash
# Extract only specific uni
find downloads_* -name "Cambridge*.pdf" -exec python extract_pdf_text.py {} -o extracted_text --fast \;
```

### Parallel Extractions
```bash
# Split into batches
ls downloads_*/*.pdf | split -l 200 - batch_
for batch in batch_*; do
  python extract_pdf_text.py $(head -1 $batch | xargs dirname) -o extracted_text --fast --workers 4 &
done
wait
```

---

**Need Help?** Check:
- `README_COORDINATOR.md` - Full documentation
- `IMPLEMENTATION_SUMMARY.md` - Technical details
- `logs/` - Detailed error messages
- Run with `-v` flag for verbose output
