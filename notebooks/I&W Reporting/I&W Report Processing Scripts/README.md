# I&W Document Generator

## Overview
The I&W Document Generator is a Python-based application that automates the process of fetching, processing, and reporting indicators from the ThreatConnect API. It streamlines workflows by integrating data from multiple sources into a comprehensive reporting tool.

## Project Structure
```
I&W_Document_Generator
├── scripts
│   ├── __init__.py
│   ├── config_loader.py
│   ├── data_processing.py
│   ├── api_integration.py
│   ├── report_generator.py
│   └── main.py
├── utils
│   ├── __init__.py
│   └── config.json
├── requirements.txt
├── README.md
```

## Data Sources and APIs
The application interacts with the following APIs to gather threat intelligence data:
- **ThreatConnect API**: Queries indicators (e.g., IPs, domains) and their metadata.
- **VirusTotal API**: Provides reputation, open ports, and network details for IPs and domains.
- **OTX (AlienVault) API**: Offers reputation and geolocation data for IPs, domains, and hostnames.

### API Keys
API keys for VirusTotal and OTX are securely loaded from configuration files.

## Filters and Conditions
The application applies several filters to ensure data relevance:
- **ThreatConnect Query Filters**:
   - Time Period: Indicators observed in the last 2 days.
   - Indicator Types: Includes IPs, email addresses, URLs, and file hashes.
   - Organization Scope: Data is scoped to the specified organization (e.g., HTOC Org).
- **Data Cleaning and Normalization**:
   - Removes duplicates and filters indicators observed in the last 48 hours.
   - Validates critical fields like `indicator` and `tags`.
- **Tag-Based Filtering**:
   - Excludes indicators with specific tags (e.g., "I&W").
   - Analyzes tags containing indications that an indicator has been observed by multiple partners.
- **Partner Filtering**:
   - Includes indicators observed by at least two unique partners.
- **Observation Limits**:
   - Excludes indicators with more than 15,000 observations.


## Data Processing
The application processes data as follows:
- **Merging Data**: Combines data from VirusTotal and OTX APIs for each indicator.
- **Consolidating Sources**: Links from both APIs are consolidated into a single field.
- **Grouping Partners**: Groups and lists partners observing the same indicator.

## Report Generation
The final step generates a Word document report:
- **Template-Based Report**: Uses a pre-defined Word template.
- **Table Population**: Adds key details (e.g., type, observation date, sources) to a table.
- **Source Consolidation**: Lists all sources outside the table for easy reference.

### Key Outputs
- **Filtered Indicators**: A refined list of I&W indicators.
- **Generated Report**: A Word document summarizing findings, saved with the current date as extension.

## Configuration
Before running the application, configure the `utils/config.json` file with your ThreatConnect API credentials:
- `api_secret_key`: Your API secret key.
- `api_access_id`: Your API access ID.
- `api_base_url`: The ThreatConnect API base URL.
- `api_default_org`: Your default organization name.

## Usage
To run the application, execute:
```
python scripts/main.py
```
This initiates configuration loading, data fetching, processing, and report generation.

## Functionality
- **Configuration Loader**: Loads API settings from a JSON file.
- **Data Processing**: Normalizes and filters data based on specified criteria.
- **API Integration**: Manages ThreatConnect API requests and session handling.
- **Report Generation**: Consolidates data and populates a Word document template.
