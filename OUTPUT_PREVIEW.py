"""
Example Output Preview
======================

This file shows what the enhanced script output will look like.
"""

# Console Output Preview:

"""
================================================================================
UK University Financial Statements Finder
================================================================================

INFO: Loading university list...
INFO: Loaded 180 universities
INFO: England: 132, Scotland: 19, Wales: 8, NI: 4
INFO: Starting university financial statements search...

Processing universities: 100%|████████████████| 180/180 [25:30<00:00,  8.5s/uni]

University of Cambridge (England)
Searching: 100%|████████████████████████| 4/4 [00:08<00:00,  2.0s/it]
  ✓ https://www.cam.ac.uk/about-the-university/annual-reports
  ✓ https://www.admin.cam.ac.uk/reporter/financial-statements/
  ✓ https://www.governance.cam.ac.uk/governance/annual-report/
  ✓ https://www.cam.ac.uk/system/files/financial_statements_2023.pdf
  ✓ https://www.admin.cam.ac.uk/univ/accounts/

University of Oxford (England)
Searching: 100%|████████████████████████| 4/4 [00:09<00:00,  2.2s/it]
  ✓ https://www.ox.ac.uk/about/organisation/finance-and-funding
  ✓ https://www.ox.ac.uk/about/organisation/finance-and-funding/financial-statements
  ✓ https://governance.admin.ox.ac.uk/annual-report

Imperial College London (England)
Searching: 75%|███████████████          | 3/4 [00:07<00:02,  2.3s/it]
  ✓ https://www.imperial.ac.uk/about/governance/annual-report/
  ✓ https://www.imperial.ac.uk/media/imperial-college/administration/documents/financial-statements.pdf

Small University Example (England)
Searching: 100%|████████████████████████| 4/4 [00:12<00:00,  3.0s/it]
  ⚠ No obvious financial statement pages found

...

================================================================================
Summary
================================================================================
Universities processed: 180/180
Successful searches: 165
Total URLs found: 723
Success rate: 91.7%
Average URLs per university: 4.0
================================================================================

INFO: Search completed successfully
"""

# Log File Output Preview (university_financials_20251122_143022.log):

"""
2025-11-22 14:30:22,123 - UniversityFinancials - INFO - setup_logging:115 - Logging initialized
2025-11-22 14:30:22,124 - UniversityFinancials - INFO - get_universities:225 - Loading university list...
2025-11-22 14:30:22,125 - UniversityFinancials - INFO - get_universities:340 - Loaded 180 universities
2025-11-22 14:30:22,125 - UniversityFinancials - DEBUG - get_universities:341 - England: 132, Scotland: 19, Wales: 8, NI: 4
2025-11-22 14:30:22,126 - UniversityFinancials - INFO - main:538 - Starting university financial statements search...
2025-11-22 14:30:22,127 - UniversityFinancials - INFO - find_financial_statements:445 - Searching for: University of Cambridge
2025-11-22 14:30:22,128 - UniversityFinancials - DEBUG - search_terms:165 - Generated 4 search terms for University of Cambridge
2025-11-22 14:30:22,129 - UniversityFinancials - DEBUG - search_links:402 - Searching for: 'University of Cambridge financial statements'
2025-11-22 14:30:22,130 - UniversityFinancials - DEBUG - _ddg_search:361 - Searching with duckduckgo_search: 'University of Cambridge financial statements' (max_results=10)
2025-11-22 14:30:23,456 - UniversityFinancials - DEBUG - _ddg_search:370 - Found result: https://www.cam.ac.uk/about-the-university/annual-reports
2025-11-22 14:30:23,457 - UniversityFinancials - DEBUG - _ddg_search:370 - Found result: https://www.admin.cam.ac.uk/reporter/financial-statements/
2025-11-22 14:30:23,458 - UniversityFinancials - INFO - _ddg_search:371 - DDG search returned 10 results
2025-11-22 14:30:23,459 - UniversityFinancials - INFO - search_links:408 - Found 10 results using duckduckgo_search
2025-11-22 14:30:23,460 - UniversityFinancials - DEBUG - is_relevant_url:433 - Relevant URL found: https://www.cam.ac.uk/about-the-university/annual-reports
2025-11-22 14:30:23,461 - UniversityFinancials - INFO - find_financial_statements:472 - ✓ Found relevant link (1/5): https://www.cam.ac.uk/about-the-university/annual-reports
2025-11-22 14:30:23,462 - UniversityFinancials - DEBUG - is_relevant_url:433 - Relevant URL found: https://www.admin.cam.ac.uk/reporter/financial-statements/
2025-11-22 14:30:23,463 - UniversityFinancials - INFO - find_financial_statements:472 - ✓ Found relevant link (2/5): https://www.admin.cam.ac.uk/reporter/financial-statements/
...
2025-11-22 14:55:50,789 - UniversityFinancials - INFO - main:580 - Search completed successfully
"""

# Error Example in Log:

"""
2025-11-22 14:35:12,345 - UniversityFinancials - ERROR - _scrape_duckduckgo_html:392 - Network error during HTML scraping: HTTPConnectionPool(host='duckduckgo.com', port=80): Max retries exceeded with url: /html/?q=... (Caused by ConnectTimeoutError(<urllib3.connection.HTTPConnection object at 0x...>, 'Connection to duckduckgo.com timed out. (connect timeout=20)'))
Traceback (most recent call last):
  File "/Users/justin/code/University Financials/university_financials.py", line 385, in _scrape_duckduckgo_html
    resp = requests.get(url, headers=headers, timeout=20)
  ...
requests.exceptions.Timeout: ...
"""

# Warning Example:

"""
2025-11-22 14:40:25,678 - UniversityFinancials - WARNING - find_financial_statements:485 - No links found for Small Example University
2025-11-22 14:40:25,679 - UniversityFinancials - WARNING - is_relevant_url:425 - URL not from academic domain: https://www.example.com/page
"""
