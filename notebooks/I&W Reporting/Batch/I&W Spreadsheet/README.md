# I&W Spreadsheet Batch Processing Script

This directory contains a silent batch script to automate the execution of the I&W Spreadsheet notebook process.

## Available Script

### `run_iw_spreadsheet_silent.bat`
**Silent execution for automation**
- Runs the notebook without user interaction
- Suitable for scheduled tasks and automation
- Logs all output to timestamped log files
- Returns appropriate exit codes for automation
- Perfect for Task Scheduler integration

**Usage:**
```cmd
run_iw_spreadsheet_silent.bat
```

## Prerequisites

1. **Jupyter Notebook** must be installed and accessible via command line
2. **Python environment** with all required packages (pandas, openpyxl, etc.)
3. **Network access** to ThreatConnect API and data sources
4. **File permissions** to read from source directories and write to output directories

## File Paths

- **Notebook:** `C:\Users\jaskew\Documents\project_repository\notebooks\I&W Reporting\I&W_Spreadsheet.ipynb`
- **Output:** `Z:\HTOC\HTOC Reports\I&W Reports\5. I&W Staging\Spreadsheet`
- **Logs:** `C:\Users\jaskew\Documents\project_repository\notebooks\I&W Reporting\Batch\I&W Spreadsheet`

## Scheduling with Task Scheduler

To run these scripts automatically, use Windows Task Scheduler:

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Set action to start the silent batch script:
   ```
   Program: C:\Users\jaskew\Documents\project_repository\notebooks\I&W Reporting\Batch\I&W Spreadsheet\run_iw_spreadsheet_silent.bat
   ```

## Troubleshooting

### Common Issues:

1. **"Jupyter is not recognized"**
   - Ensure Jupyter is installed: `pip install jupyter`
   - Add Python/Scripts to PATH environment variable

2. **"Access denied" errors**
   - Verify file permissions for source and destination directories
   - Run as administrator if necessary

3. **Network connectivity issues**
   - Check VPN connection if required
   - Verify API credentials and endpoints

### Log Files

All scripts generate detailed log files with timestamps. Check these files for:
- Execution start/end times
- Error messages and stack traces
- File paths and operations
- Success/failure status

## Exit Codes

- `0`: Success
- `1`: General error
- `>1`: Specific error codes from Jupyter execution

## Notes

- The advanced script creates automatic backups of the notebook before execution
- All scripts change to the notebook directory before execution
- Log files are timestamped to prevent overwrites
- Silent script is recommended for automated/scheduled execution