# I&W Master Listing

## Project Overview
The I&W Master Listing project is designed to extract data from PowerPoint presentations and write that data into an Excel spreadsheet. The project focuses on identifying specific patterns in the slides, such as HTOC-like and IP-like data, and organizing this information for further analysis.

## Project Structure
```
I&W_Master_Listing
├── src
│   ├── __init__.py
│   ├── extract_pptx.py
│   ├── excel_writer.py
│   └── main.py
├── requirements.txt
└── README.md
```

## Installation
To set up the project, ensure you have Python installed on your machine. Then, install the required packages using pip:

```bash
pip install -r requirements.txt
```

## Usage
1. Place your PowerPoint files in the designated directory.
2. Run the main script to extract data and write it to the Excel file:

```bash
python src/main.py
```

## Functions
- **extract_text_and_tables_from_pptx(pptx_path)**: Extracts text and tables from the specified PowerPoint file, identifying HTOC-like and IP-like data.
- **fill_excel_sheet(file_path, sheet_name)**: Reads from and writes to the specified Excel sheet, managing duplicates and adjusting column widths.

## Dependencies
The project requires the following Python packages:
- pandas
- openpyxl
- python-pptx

## Contributing
Contributions to the project are welcome. Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.