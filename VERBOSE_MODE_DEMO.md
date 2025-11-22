# Verbose Mode Demo

## Usage

```bash
python university_financials.py --verbose
# or
python university_financials.py -v
```

## What You'll See

### 1. Activation Message
```
🔍 VERBOSE MODE ENABLED - Detailed debugging output activated
```

### 2. Search Terms Generation
For each university, all search terms are displayed:
```
DEBUG [search_terms]: Generated 4 search terms for University of Cambridge:
DEBUG [search_terms]:   [1] 'University of Cambridge financial statements'
DEBUG [search_terms]:   [2] 'University of Cambridge annual report'
DEBUG [search_terms]:   [3] 'University of Cambridge financial statements site:ac.uk'
DEBUG [search_terms]:   [4] 'University of Cambridge accounts pdf'
```

### 3. Search Progress
Shows which term is being searched:
```
DEBUG [find_financial_statements]: 
[Term 1/4] Searching: 'University of Cambridge financial statements'
```

### 4. Search Execution
Shows the search backend being used:
```
DEBUG [search_links]: ══════ Searching for: 'University of Cambridge financial statements' ══════
DEBUG [_ddg_search]: → Searching with ddgs: 'University of Cambridge financial statements' (max_results=10)
```

### 5. Search Results
Every result with title and URL:
```
DEBUG [_ddg_search]:   [1] Financial Statements | University of Cambridge
DEBUG [_ddg_search]:       https://www.cam.ac.uk/about-the-university/annual-reports
DEBUG [_ddg_search]:   [2] Annual Report and Financial Statements
DEBUG [_ddg_search]:       https://www.admin.cam.ac.uk/reporter/financial-statements/
DEBUG [_ddg_search]:   [3] Governance and Financial Information
DEBUG [_ddg_search]:       https://www.governance.cam.ac.uk/governance/annual-report/
```

### 6. Link Retrieval Summary
```
DEBUG [find_financial_statements]: Retrieved 10 links from search
```

### 7. Relevance Checking
For each link, shows checking process:
```
DEBUG [find_financial_statements]:   [1] Checking relevance...
DEBUG [is_relevant_url]: ✓ Relevant URL (keywords: financial, statements): https://www.cam.ac.uk/about-the-university/annual-reports
INFO [find_financial_statements]: ✓ Found relevant link (1/5): https://www.cam.ac.uk/about-the-university/annual-reports
```

### 8. Duplicate Detection
Shows when links are skipped:
```
DEBUG [find_financial_statements]:   [3] ⊘ Duplicate (already seen): https://www.cam.ac.uk/about
```

### 9. Non-Relevant Links
Shows why links are rejected:
```
DEBUG [is_relevant_url]: ✗ URL lacks financial keywords: https://www.cam.ac.uk/about/history
```

### 10. Academic Domain Filtering
```
DEBUG [is_relevant_url]: URL not from academic domain: https://www.wikipedia.org/wiki/Cambridge
```

## Color Coding

In verbose mode, debug messages are color-coded:

- 🟣 **Magenta**: Search terms, term counters
- 🟡 **Yellow**: Search queries, warnings, duplicates
- 🔵 **Cyan**: Function names, URLs, progress indicators
- 🟢 **Green**: Success, found results, relevant URLs
- 🔴 **Red**: Errors

## Normal Mode vs Verbose Mode

### Normal Mode Output
```
INFO: Loading university list...
INFO: Loaded 180 universities
INFO: Searching for: University of Cambridge
✓ Found relevant link (1/5): https://www.cam.ac.uk/about-the-university/annual-reports
✓ Found relevant link (2/5): https://www.admin.cam.ac.uk/reporter/financial-statements/
```

### Verbose Mode Output
```
INFO: Loading university list...
INFO: Loaded 180 universities
DEBUG [get_universities]: England: 132, Scotland: 19, Wales: 8, NI: 4
🔍 VERBOSE MODE ENABLED - Detailed debugging output activated
================================================================================
DEBUG [find_financial_statements]: ================================================================================
INFO [find_financial_statements]: Searching for: University of Cambridge
DEBUG [find_financial_statements]: ================================================================================
DEBUG [search_terms]: Generated 4 search terms for University of Cambridge:
DEBUG [search_terms]:   [1] 'University of Cambridge financial statements'
DEBUG [search_terms]:   [2] 'University of Cambridge annual report'
DEBUG [search_terms]:   [3] 'University of Cambridge financial statements site:ac.uk'
DEBUG [search_terms]:   [4] 'University of Cambridge accounts pdf'
DEBUG [find_financial_statements]: Will search using 4 terms

DEBUG [find_financial_statements]: [Term 1/4] Searching: 'University of Cambridge financial statements'
DEBUG [search_links]: ══════ Searching for: 'University of Cambridge financial statements' ══════
DEBUG [_ddg_search]: → Searching with ddgs: 'University of Cambridge financial statements' (max_results=10)
DEBUG [_ddg_search]:   [1] Financial Statements | University of Cambridge
DEBUG [_ddg_search]:       https://www.cam.ac.uk/about-the-university/annual-reports
DEBUG [_ddg_search]:   [2] Annual Report and Financial Statements
DEBUG [_ddg_search]:       https://www.admin.cam.ac.uk/reporter/financial-statements/
INFO [search_links]: ✓ Found 10 results using ddgs
DEBUG [find_financial_statements]: Retrieved 10 links from search
DEBUG [find_financial_statements]:   [1] Checking relevance...
DEBUG [is_relevant_url]: ✓ Relevant URL (keywords: financial, statements): https://www.cam.ac.uk/about-the-university/annual-reports
INFO [find_financial_statements]: ✓ Found relevant link (1/5): https://www.cam.ac.uk/about-the-university/annual-reports
DEBUG [find_financial_statements]:   [2] Checking relevance...
DEBUG [is_relevant_url]: ✓ Relevant URL (keywords: financial, statements, report): https://www.admin.cam.ac.uk/reporter/financial-statements/
INFO [find_financial_statements]: ✓ Found relevant link (2/5): https://www.admin.cam.ac.uk/reporter/financial-statements/
```

## When to Use Verbose Mode

Use verbose mode (`-v` or `--verbose`) when:

1. **Debugging search issues** - See exactly what search terms are being used
2. **Understanding results** - See why certain URLs are included or excluded
3. **Verifying relevance** - Check which keywords are matching
4. **Development** - Testing changes to search logic
5. **Troubleshooting** - Investigating why a specific university returns no results
6. **Learning** - Understanding how the search algorithm works

## Performance Note

Verbose mode does not affect search performance - it only changes what's displayed in the console. All debug information is always written to the log file regardless of verbose mode.
