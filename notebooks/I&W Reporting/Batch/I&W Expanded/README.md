# I&W Document Expanded Processing Suite

This directory contains batch script versions of the Jupyter notebooks for I&W expanded processing.

## Files

### Spreadsheet Generator
- `I&W_Document_expanded_spreadsheet.py` - Main Python script that replicates the spreadsheet notebook functionality
- `run_iw_expanded_spreadsheet.bat` - Windows batch script to execute the spreadsheet script
- `requirements.txt` - Python package dependencies for spreadsheet generation

### Report Generator  
- `I&W_Document_expanded_generator.py` - Main Python script that replicates the report generator notebook functionality
- `run_iw_expanded_generator.bat` - Windows batch script to execute the report generator script
- `requirements_generator.txt` - Python package dependencies for report generation

### Documentation
- `README.md` - This file

## Prerequisites

1. **Python Environment**: Ensure Python is installed and accessible via the `python` command
2. **Dependencies**: Install required packages using:
   ```
   # For spreadsheet generation
   pip install -r requirements.txt
   
   # For report generation  
   pip install -r requirements_generator.txt
   ```
3. **ThreatConnect SDK**: Must be available at `Z:/HTOC/Data_Analytics/threatconnect`
4. **Config Loader**: Must be available at `C:\Users\jaskew\Documents\project_repository\scripts\Data Movement\ThrearConnect-api-pull\utils`
5. **Data Files**: Observed data files must be available at `Z:/HTOC/Data_Analytics/Data/OpDiv_Observations/`
6. **Output Directories**: 
   - Spreadsheet: `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Spreadsheet\Expanded`
   - Reports: `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Expanded Reports`
7. **Template**: Word template must be available at `C:\Users\jaskew\Documents\project_repository\notebooks\I&W Reporting\I&W Report Template.docx`

## Usage

### Option 1: Run the batch scripts (Recommended)
```
# Generate expanded indicators spreadsheet
run_iw_expanded_spreadsheet.bat

# Generate I&W reports from the spreadsheet
run_iw_expanded_generator.bat
```

### Option 2: Run Python scripts directly
```
# Generate spreadsheet
python I&W_Document_expanded_spreadsheet.py

# Generate reports
python I&W_Document_expanded_generator.py
```

## Workflow

The typical workflow is to run both scripts in sequence:

1. **First**: Run the spreadsheet generator to create the expanded indicators Excel file
2. **Second**: Run the report generator to create individual I&W reports from the spreadsheet

## What Each Script Does

### Spreadsheet Generator (`I&W_Document_expanded_spreadsheet.py`)
1. **Initialize ThreatConnect API**: Connects to ThreatConnect using configuration
2. **Fetch Indicators**: Queries ThreatConnect for indicators from the last 2 days
3. **Load Observed Data**: Reads observation data from CSV files for the last 3 days
4. **Process Tags**: Filters and processes tags, applying business logic for partner grouping
5. **Fetch Attributes**: Retrieves additional attributes for qualifying indicators
6. **Filter Reported**: Removes indicators that have already been reported
7. **Generate Output**: Saves the final dataset to an Excel file with today's date

### Report Generator (`I&W_Document_expanded_generator.py`)
1. **Load Spreadsheet**: Finds and loads the most recent expanded indicators spreadsheet
2. **Fetch Enrichment**: Queries VirusTotal and OTX APIs for additional indicator data
3. **Generate Reports**: Creates individual Word documents using the I&W report template
4. **Group Processing**: Handles both individual indicators and grouped indicators
5. **Update Tracking**: Adds processed indicators to the reported indicators list

## Output

### Spreadsheet Generator
- Excel file named `expanded_indicators_YYYYMMDD.xlsx` in the spreadsheet staging directory

### Report Generator  
- Individual Word documents in `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Expanded Reports\YYYY-MM-DD\`
- Format: `I&W_Report_{indicator}.docx` or `I&W_Report_Group_{group_id}.docx`
- Updated `indicators.csv` file with newly processed indicators

## Error Handling

- Both scripts include comprehensive error handling and logging
- If any critical step fails, the scripts will exit with an error message
- SSL warnings are suppressed for the ThreatConnect API connections
- API rate limiting and timeout handling for external services

## Configuration

Both scripts use the same configuration as the original notebooks:
- ThreatConnect API credentials from `config.json`
- Hardcoded API keys for VirusTotal and OTX (in report generator)
- Hardcoded paths for data sources and outputs
- Time windows: 2 days for indicators, 3 days for observed data

## Troubleshooting

1. **Import Errors**: Ensure all path dependencies are available and accessible
2. **API Errors**: Check ThreatConnect configuration and network connectivity
3. **File Access**: Verify permissions for input and output directories
4. **Memory Issues**: Large datasets may require adjusting pandas settings
5. **Template Issues**: Ensure Word template exists and is accessible
6. **External API Issues**: Check VirusTotal and OTX API connectivity

## Maintenance

These scripts should be kept in sync with any changes made to the original Jupyter notebooks. Key areas to monitor:
- API endpoints and query parameters
- Business logic for filtering and grouping
- Output format requirements
- Path configurations
- API keys and authentication