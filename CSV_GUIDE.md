# CSV Output Guide

## Overview

The script automatically exports all search results to a CSV file for easy data analysis and processing.

## File Format

### Filename
- Pattern: `university_financials_results_YYYYMMDD_HHMMSS.csv`
- Example: `university_financials_results_20251122_143022.csv`
- Automatically timestamped to avoid overwriting previous results

### Columns

| Column | Description | Example |
|--------|-------------|---------|
| University | Full name of the university | University of Cambridge |
| Country | Country within UK | England, Scotland, Wales, Northern Ireland |
| Domain | University's primary domain | cam.ac.uk |
| Year | Year extracted from URL (if available) | 2024, 2023, N/A |
| URL | Direct link to financial statement | https://www.cam.ac.uk/finances/annual-report-2024.pdf |

## Sample CSV Output

```csv
University,Country,Domain,Year,URL
University of Cambridge,England,cam.ac.uk,2024,https://www.cam.ac.uk/finances/annual-report-2024.pdf
University of Cambridge,England,cam.ac.uk,2023,https://www.cam.ac.uk/finances/annual-report-2023.pdf
University of Oxford,England,ox.ac.uk,2024,https://www.ox.ac.uk/about/finances/financial-statements-2024
University of Edinburgh,Scotland,ed.ac.uk,2023,https://www.ed.ac.uk/about/annual-report-2023
Imperial College London,England,imperial.ac.uk,N/A,https://www.imperial.ac.uk/about/governance/financial-statements
```

## Using the CSV File

### In Excel
1. Open Excel
2. File → Open → Select the CSV file
3. Data will be automatically parsed into columns
4. Use filters, sort, pivot tables for analysis

### In Python (pandas)
```python
import pandas as pd

# Read CSV
df = pd.read_csv('university_financials_results_20251122_143022.csv')

# View first few rows
print(df.head())

# Filter by year
recent_reports = df[df['Year'] == '2024']

# Group by country
by_country = df.groupby('Country').size()
print(by_country)

# Export specific universities
cambridge_reports = df[df['University'].str.contains('Cambridge')]
cambridge_reports.to_csv('cambridge_only.csv', index=False)
```

### In R
```r
# Read CSV
df <- read.csv('university_financials_results_20251122_143022.csv')

# View structure
str(df)

# Filter by country
england_unis <- df[df$Country == 'England', ]

# Count reports per university
reports_count <- table(df$University)

# Sort by year (descending)
df_sorted <- df[order(-as.numeric(df$Year)), ]
```

### In Google Sheets
1. Open Google Sheets
2. File → Import → Upload tab
3. Select the CSV file
4. Choose "Replace spreadsheet" or "Insert new sheet(s)"
5. Import data

## Data Analysis Examples

### Finding Universities with Multiple Years
```python
# Count URLs per university
url_counts = df.groupby('University').size().sort_values(ascending=False)
print("Universities with most financial statements found:")
print(url_counts.head(10))
```

### Analyzing Year Coverage
```python
# Exclude N/A years
valid_years = df[df['Year'] != 'N/A']

# Get year distribution
year_dist = valid_years['Year'].value_counts().sort_index()
print("Financial statements by year:")
print(year_dist)
```

### Domain Analysis
```python
# Check for universities missing domains
missing_domains = df[df['Domain'] == 'N/A']
print(f"Universities without detected domains: {len(missing_domains)}")
```

## Features

✅ **Automatic timestamping** - Never overwrites previous results  
✅ **UTF-8 encoding** - Handles special characters in university names  
✅ **Standard CSV format** - Compatible with all major tools  
✅ **Header row** - Column names included for easy import  
✅ **Year tagging** - Extracted years for chronological analysis  
✅ **Domain tracking** - Verify search accuracy per institution  

## Troubleshooting

### CSV file not created
- Check terminal output for "Results saved to:" message
- Verify write permissions in the script directory
- Check log file for error messages

### Empty CSV file
- Script may not have found any results
- Check console output for warnings
- Run with `-v` flag for debugging

### Special characters display incorrectly
- Ensure you're opening the file with UTF-8 encoding
- In Excel: Data → Get Data → From Text/CSV → Select UTF-8

## Combining Multiple Runs

If you run the script multiple times, you can combine CSV files:

### Python
```python
import pandas as pd
import glob

# Read all CSV files
csv_files = glob.glob('university_financials_results_*.csv')
dfs = [pd.read_csv(f) for f in csv_files]

# Combine and remove duplicates
combined = pd.concat(dfs, ignore_index=True)
combined_unique = combined.drop_duplicates(subset=['University', 'URL'])

# Save
combined_unique.to_csv('combined_results.csv', index=False)
print(f"Combined {len(csv_files)} files into {len(combined_unique)} unique records")
```

### Bash
```bash
# Combine all CSV files (skip headers from subsequent files)
head -n 1 university_financials_results_*.csv | head -n 1 > combined.csv
tail -n +2 -q university_financials_results_*.csv >> combined.csv
```

## Next Steps

After collecting the CSV file:
1. **Validate URLs** - Check if links are still active
2. **Download PDFs** - Automate downloading the actual documents
3. **Extract data** - Parse financial figures from PDFs
4. **Time series analysis** - Track changes over years
5. **Comparative analysis** - Compare universities by size, region, etc.
