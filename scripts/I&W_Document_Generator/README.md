# I&W Document Generator

## Overview
The I&W Document Generator is a Python-based application designed to automate the process of fetching, processing, and reporting indicators from the ThreatConnect API. This project aims to streamline the workflow for security analysts by providing a comprehensive reporting tool that integrates data from various sources.

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
└── .gitignore
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd I&W_Document_Generator
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Configuration
Before running the application, ensure that the `utils/config.json` file is properly configured with your ThreatConnect API credentials. The configuration file should include the following fields:
- `api_secret_key`: Your API secret key.
- `api_access_id`: Your API access ID.
- `api_base_url`: The base URL for the ThreatConnect API.
- `api_default_org`: Your default organization name.

## Usage
To run the application, execute the following command:
```
python scripts/main.py
```

This will initiate the process of loading configurations, fetching data from the ThreatConnect API, processing the data, and generating reports.

## Functionality
- **Configuration Loader**: Loads API configuration settings from a JSON file.
- **Data Processing**: Processes and normalizes data retrieved from the API, filtering indicators based on specified criteria.
- **API Integration**: Manages the integration with the ThreatConnect API, including session initialization and request handling.
- **Report Generation**: Generates reports by consolidating data from different sources and populating a Word document template.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.